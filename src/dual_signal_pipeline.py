"""
Dual-Signal BGP + Syslog Anomaly Detection Pipeline

This pipeline combines BGP updates and syslog messages for enhanced
failure detection and localization using the dual-signal approach.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from collections import defaultdict, deque
from nats.aio.client import Client as NATS

from python.features.stream_features import FeatureAggregator
from python.models.gpu_mp_detector import create_gpu_mp_detector
from python.triage.impact import ImpactScorer
from python.utils.schema import BGPUpdate, FeatureBin

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DualSignalPipeline:
    """
    Dual-signal anomaly detection pipeline combining BGP and syslog data.
    
    Features:
    - Correlates BGP updates with syslog messages
    - Enhanced failure detection using both signals
    - Improved localization accuracy
    - Real-time processing with GPU acceleration
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the dual-signal pipeline.
        
        Args:
            config: Configuration containing all pipeline settings
        """
        self.config = config
        self.nats_url = config.get('nats_url', 'nats://localhost:4222')
        
        # Initialize components
        self.bgp_aggregator = FeatureAggregator(
            bin_seconds=config.get('bin_seconds', 30)
        )
        
        self.mp_detector = create_gpu_mp_detector(
            window_bins=config.get('mp_window_bins', 64),
            series_keys=config.get('mp_series_keys', ['wdr_total', 'ann_total', 'as_path_churn']),
            discord_threshold=config.get('mp_discord_threshold', 2.5),
            gpu_memory_limit=config.get('gpu_memory_limit', '2GB')
        )
        
        self.impact_scorer = ImpactScorer(
            cfg_roles=config.get('roles_config', {})
        )
        
        # Syslog correlation
        self.syslog_buffer = deque(maxlen=1000)  # Keep last 1000 syslog messages
        self.correlation_window = config.get('correlation_window_seconds', 60)
        
        # NATS client
        self.nc = None
        
        logger.info("Dual-signal pipeline initialized")
    
    async def start(self):
        """Start the pipeline and connect to NATS."""
        self.nc = NATS()
        await self.nc.connect(servers=[self.nats_url])
        
        # Subscribe to both BGP and syslog messages
        await self.nc.subscribe("bgp.updates", cb=self._handle_bgp_update)
        await self.nc.subscribe("syslog.messages", cb=self._handle_syslog_message)
        
        logger.info("Dual-signal pipeline started, listening for BGP and syslog messages...")
    
    async def stop(self):
        """Stop the pipeline and disconnect from NATS."""
        if self.nc:
            await self.nc.drain()
        logger.info("Dual-signal pipeline stopped")
    
    async def _handle_bgp_update(self, msg):
        """Handle incoming BGP update message."""
        try:
            data = json.loads(msg.data.decode())
            bgp_update = BGPUpdate(**data)
            
            # Add to BGP aggregator
            self.bgp_aggregator.add_update(bgp_update)
            
            # Process any closed bins
            while self.bgp_aggregator.has_closed_bin():
                await self._process_dual_signal_bin(self.bgp_aggregator.pop_closed_bin())
                
        except Exception as e:
            logger.error(f"Error processing BGP update: {e}")
    
    async def _handle_syslog_message(self, msg):
        """Handle incoming syslog message."""
        try:
            data = json.loads(msg.data.decode())
            
            # Add to syslog buffer
            self.syslog_buffer.append(data)
            
            logger.debug(f"Received syslog: {data.get('device')} - {data.get('message')}")
            
        except Exception as e:
            logger.error(f"Error processing syslog message: {e}")
    
    async def _process_dual_signal_bin(self, fb: FeatureBin):
        """
        Process a feature bin with both BGP and syslog correlation.
        
        Args:
            fb: FeatureBin containing aggregated BGP features
        """
        try:
            # Step 1: Matrix Profile anomaly detection on BGP data
            mp_results = self.mp_detector.update(fb)
            
            # Step 2: Correlate with syslog messages
            correlated_syslog = self._correlate_syslog_messages(fb, mp_results)
            
            # Step 3: Enhanced impact scoring with syslog context
            impact_results = self._enhanced_impact_scoring(fb, mp_results, correlated_syslog)
            
            # Step 4: Create comprehensive event
            event = self._create_dual_signal_event(fb, mp_results, correlated_syslog, impact_results)
            
            # Step 5: Publish event
            await self._publish_event(event)
            
            # Log significant events
            if event['is_anomaly']:
                logger.info(f"Dual-signal anomaly detected: {event['impact_analysis']['impact']} - "
                          f"Confidence: {event['anomaly_confidence']:.2f} - "
                          f"BGP: {len(event['bgp_analysis']['detected_series'])} series - "
                          f"Syslog: {len(event['syslog_analysis']['correlated_messages'])} messages")
                
        except Exception as e:
            logger.error(f"Error processing dual-signal bin: {e}")
    
    def _correlate_syslog_messages(self, fb: FeatureBin, mp_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Correlate syslog messages with BGP feature bin.
        
        Args:
            fb: Feature bin
            mp_results: Matrix Profile results
            
        Returns:
            Dictionary containing correlated syslog analysis
        """
        bin_start = fb.bin_start
        bin_end = fb.bin_end
        
        # Find syslog messages within the time window
        correlated_messages = []
        for syslog_msg in self.syslog_buffer:
            msg_time = syslog_msg.get('timestamp', 0)
            if bin_start <= msg_time <= bin_end:
                correlated_messages.append(syslog_msg)
        
        # Analyze syslog patterns
        device_counts = defaultdict(int)
        severity_counts = defaultdict(int)
        scenario_counts = defaultdict(int)
        
        for msg in correlated_messages:
            device_counts[msg.get('device', 'unknown')] += 1
            severity_counts[msg.get('severity', 'info')] += 1
            scenario_counts[msg.get('scenario', 'normal_operation')] += 1
        
        # Calculate syslog anomaly score
        total_messages = len(correlated_messages)
        error_messages = severity_counts.get('error', 0)
        warning_messages = severity_counts.get('warning', 0)
        
        # Higher score for more error/warning messages
        syslog_anomaly_score = (error_messages * 2 + warning_messages) / max(total_messages, 1)
        
        return {
            'correlated_messages': correlated_messages,
            'total_messages': total_messages,
            'device_counts': dict(device_counts),
            'severity_counts': dict(severity_counts),
            'scenario_counts': dict(scenario_counts),
            'syslog_anomaly_score': syslog_anomaly_score,
            'has_errors': error_messages > 0,
            'has_warnings': warning_messages > 0
        }
    
    def _enhanced_impact_scoring(
        self, 
        fb: FeatureBin, 
        mp_results: Dict[str, Any], 
        syslog_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Enhanced impact scoring using both BGP and syslog signals.
        
        Args:
            fb: Feature bin
            mp_results: Matrix Profile results
            syslog_analysis: Correlated syslog analysis
            
        Returns:
            Enhanced impact scoring results
        """
        # Get base impact scoring
        base_impact = self.impact_scorer.classify(fb, mp_results['overall_score']['score'])
        
        # Enhance with syslog context
        syslog_anomaly_score = syslog_analysis['syslog_anomaly_score']
        has_errors = syslog_analysis['has_errors']
        has_warnings = syslog_analysis['has_warnings']
        
        # Adjust impact based on syslog signals
        if has_errors:
            # Errors in syslog suggest more severe impact
            if base_impact['impact'] == 'EDGE_LOCAL':
                base_impact['impact'] = 'NETWORK_IMPACTING'
            base_impact['confidence'] = min(base_impact.get('confidence', 0) + 0.3, 1.0)
        elif has_warnings:
            # Warnings suggest potential issues
            base_impact['confidence'] = min(base_impact.get('confidence', 0) + 0.1, 1.0)
        
        # Add syslog context
        base_impact['syslog_context'] = {
            'anomaly_score': syslog_anomaly_score,
            'has_errors': has_errors,
            'has_warnings': has_warnings,
            'message_count': syslog_analysis['total_messages']
        }
        
        return base_impact
    
    def _create_dual_signal_event(
        self,
        fb: FeatureBin,
        mp_results: Dict[str, Any],
        syslog_analysis: Dict[str, Any],
        impact_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create comprehensive dual-signal anomaly event.
        
        Args:
            fb: Feature bin
            mp_results: Matrix Profile results
            syslog_analysis: Correlated syslog analysis
            impact_results: Enhanced impact scoring
            
        Returns:
            Comprehensive dual-signal event
        """
        return {
            'timestamp': fb.bin_start,
            'bin_duration': fb.bin_end - fb.bin_start,
            'is_anomaly': mp_results['is_anomaly'],
            'anomaly_confidence': mp_results['anomaly_confidence'],
            'overall_score': mp_results['overall_score']['score'],
            
            # BGP analysis
            'bgp_analysis': {
                'detected_series': mp_results['detected_series'],
                'series_results': mp_results['series_results'],
                'active_series': mp_results['overall_score']['active_series']
            },
            
            # Syslog analysis
            'syslog_analysis': {
                'correlated_messages': syslog_analysis['correlated_messages'],
                'total_messages': syslog_analysis['total_messages'],
                'device_counts': syslog_analysis['device_counts'],
                'severity_counts': syslog_analysis['severity_counts'],
                'scenario_counts': syslog_analysis['scenario_counts'],
                'anomaly_score': syslog_analysis['syslog_anomaly_score'],
                'has_errors': syslog_analysis['has_errors'],
                'has_warnings': syslog_analysis['has_warnings']
            },
            
            # Enhanced impact analysis
            'impact_analysis': {
                'impact': impact_results['impact'],
                'roles': impact_results['roles'],
                'prefix_spread': impact_results['prefix_spread'],
                'syslog_context': impact_results.get('syslog_context', {})
            },
            
            # Feature summary
            'feature_summary': {
                'total_announcements': fb.totals.get('ann_total', 0),
                'total_withdrawals': fb.totals.get('wdr_total', 0),
                'as_path_churn': fb.totals.get('as_path_churn', 0),
                'active_peers': len(fb.peers)
            },
            
            # Dual-signal correlation
            'correlation_analysis': {
                'bgp_anomaly': mp_results['is_anomaly'],
                'syslog_anomaly': syslog_analysis['syslog_anomaly_score'] > 0.5,
                'correlation_strength': self._calculate_correlation_strength(mp_results, syslog_analysis),
                'signal_agreement': self._calculate_signal_agreement(mp_results, syslog_analysis)
            }
        }
    
    def _calculate_correlation_strength(
        self, 
        mp_results: Dict[str, Any], 
        syslog_analysis: Dict[str, Any]
    ) -> float:
        """Calculate correlation strength between BGP and syslog signals."""
        bgp_score = mp_results['overall_score']['score']
        syslog_score = syslog_analysis['syslog_anomaly_score']
        
        # Simple correlation: both signals should be elevated for strong correlation
        if bgp_score > 0 and syslog_score > 0:
            return min(bgp_score * syslog_score, 1.0)
        return 0.0
    
    def _calculate_signal_agreement(
        self, 
        mp_results: Dict[str, Any], 
        syslog_analysis: Dict[str, Any]
    ) -> bool:
        """Calculate if BGP and syslog signals agree on anomaly presence."""
        bgp_anomaly = mp_results['is_anomaly']
        syslog_anomaly = syslog_analysis['syslog_anomaly_score'] > 0.5
        
        return bgp_anomaly == syslog_anomaly
    
    async def _publish_event(self, event: Dict[str, Any]):
        """Publish dual-signal event to NATS."""
        try:
            event_json = json.dumps(event, default=str)
            await self.nc.publish("bgp.events", event_json.encode())
            logger.debug(f"Published dual-signal event: {event['timestamp']}")
        except Exception as e:
            logger.error(f"Error publishing event: {e}")
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """Get current pipeline status and statistics."""
        return {
            'mp_detector_status': self.mp_detector.get_status(),
            'bgp_aggregator': {
                'current_bin_start': self.bgp_aggregator.current_bin_start,
                'closed_bins_count': len(self.bgp_aggregator.closed),
                'bin_seconds': self.bgp_aggregator.bin_seconds
            },
            'syslog_buffer': {
                'message_count': len(self.syslog_buffer),
                'correlation_window': self.correlation_window
            },
            'nats_connected': self.nc is not None
        }


async def main():
    """Main function to run the dual-signal pipeline."""
    config = {
        'nats_url': 'nats://localhost:4222',
        'bin_seconds': 30,
        'mp_window_bins': 64,
        'mp_series_keys': ['wdr_total', 'ann_total', 'as_path_churn'],
        'mp_discord_threshold': 2.5,
        'gpu_memory_limit': '2GB',
        'correlation_window_seconds': 60,
        'roles_config': {
            'roles': {
                '10.0.0.1': 'rr',
                '10.0.0.2': 'rr',
                '10.0.1.1': 'spine',
                '10.0.1.2': 'spine',
                '10.0.2.1': 'tor',
                '10.0.2.2': 'tor',
                '10.0.3.1': 'edge',
                '10.0.3.2': 'edge',
                '10.0.10.11': 'server',
                '10.0.10.12': 'server'
            },
            'thresholds': {
                'edge_local_prefix_max': 100,
                'edge_local_pct_table_max': 0.01,
                'correlation_window_secs': 60
            }
        }
    }
    
    pipeline = DualSignalPipeline(config)
    
    try:
        await pipeline.start()
        
        # Keep running
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Shutting down dual-signal pipeline...")
    finally:
        await pipeline.stop()


if __name__ == "__main__":
    asyncio.run(main())
