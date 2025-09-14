"""
ML Pipeline Integration for Virtual Lab

This module integrates the virtual lab with the existing ML pipeline
for BGP anomaly detection, allowing seamless testing and validation.
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add the parent directory to the path so we can import existing modules
sys.path.append(str(Path(__file__).parent.parent.parent))

# Removed telemetry_generator - using real FRR data instead
from preprocessing.feature_extractor import PreprocessingPipeline
from message_bus.nats_publisher import MessageBusManager

# Import existing ML pipeline components
try:
    from models.gpu_mp_detector import GPUMPDetector
    from triage.impact import ImpactScorer
    from alerting.alert_manager import AlertManager
    from utils.schema import FeatureBin
except ImportError as e:
    logging.warning(f"Could not import existing ML pipeline components: {e}")
    logging.warning("Some features may not be available")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MLPipelineIntegration:
    """
    Integrates the virtual lab with the existing ML pipeline.
    
    This class bridges the gap between the virtual lab's data generation
    and the existing BGP anomaly detection ML pipeline.
    """
    
    def __init__(self, config_path: str):
        self.config_path = config_path
        
        # Initialize virtual lab components
        self.telemetry_generator = TelemetryGenerator(config_path)
        self.preprocessing_pipeline = PreprocessingPipeline(config_path)
        self.message_bus_manager = MessageBusManager(config_path)
        
        # Initialize ML pipeline components
        self.mp_detector = None
        self.impact_scorer = None
        self.alert_manager = None
        
        self._initialize_ml_components()
        
        # Statistics
        self.stats = {
            'features_processed': 0,
            'anomalies_detected': 0,
            'alerts_generated': 0,
            'false_positives': 0,
            'true_positives': 0
        }
        
        logger.info("ML pipeline integration initialized")
    
    def _initialize_ml_components(self):
        """Initialize ML pipeline components."""
        try:
            # Initialize Matrix Profile detector
            self.mp_detector = GPUMPDetector(
                window_bins=64,
                series_keys=['wdr_total', 'ann_total', 'as_path_churn'],
                discord_threshold=2.5
            )
            logger.info("Matrix Profile detector initialized")
            
            # Initialize impact scorer
            # Note: This would need the roles configuration
            try:
                import yaml
                with open('configs/roles.yml', 'r') as f:
                    roles_config = yaml.safe_load(f)
                self.impact_scorer = ImpactScorer(roles_config)
                logger.info("Impact scorer initialized")
            except Exception as e:
                logger.warning(f"Could not initialize impact scorer: {e}")
            
            # Initialize alert manager
            self.alert_manager = AlertManager()
            logger.info("Alert manager initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize ML components: {e}")
            logger.warning("Running in simulation mode")
    
    async def start(self):
        """Start the integrated ML pipeline."""
        await self.message_bus_manager.start()
        logger.info("ML pipeline integration started")
    
    async def stop(self):
        """Stop the integrated ML pipeline."""
        await self.message_bus_manager.stop()
        logger.info("ML pipeline integration stopped")
    
    def convert_features_to_feature_bin(self, extracted_features) -> Optional[FeatureBin]:
        """Convert extracted features to FeatureBin format for ML pipeline."""
        try:
            # Combine all features
            all_features = {}
            all_features.update(extracted_features.bgp_features)
            all_features.update(extracted_features.syslog_features)
            all_features.update(extracted_features.system_features)
            all_features.update(extracted_features.interface_features)
            all_features.update(extracted_features.correlation_features)
            all_features.update(extracted_features.semantic_features)
            
            # Create FeatureBin
            feature_bin = FeatureBin(
                bin_start=int(extracted_features.window_start.timestamp()),
                bin_end=int(extracted_features.window_end.timestamp()),
                totals=all_features,
                peers={}  # Simplified for demo
            )
            
            return feature_bin
            
        except Exception as e:
            logger.error(f"Failed to convert features to FeatureBin: {e}")
            return None
    
    async def process_features_with_ml(self, extracted_features) -> Optional[Dict[str, Any]]:
        """Process extracted features through the ML pipeline."""
        if not self.mp_detector:
            logger.warning("ML pipeline not available, skipping processing")
            return None
        
        try:
            # Convert to FeatureBin format
            feature_bin = self.convert_features_to_feature_bin(extracted_features)
            if not feature_bin:
                return None
            
            # Run Matrix Profile detection
            mp_result = self.mp_detector.update(feature_bin)
            
            # Run impact scoring if available
            impact_result = None
            if self.impact_scorer:
                try:
                    impact_result = self.impact_scorer.classify(feature_bin, mp_result)
                except Exception as e:
                    logger.warning(f"Impact scoring failed: {e}")
            
            # Create comprehensive result
            result = {
                'timestamp': feature_bin.bin_end,
                'is_anomaly': mp_result.get('is_anomaly', False),
                'anomaly_confidence': mp_result.get('anomaly_confidence', 0.0),
                'overall_score': mp_result.get('overall_score', {}).get('score', 0.0),
                'detected_series': mp_result.get('detected_series', []),
                'series_results': mp_result.get('series_results', {}),
                'impact_analysis': impact_result,
                'features_used': list(feature_bin.totals.keys())
            }
            
            # Update statistics
            self.stats['features_processed'] += 1
            if result['is_anomaly']:
                self.stats['anomalies_detected'] += 1
            
            return result
            
        except Exception as e:
            logger.error(f"ML processing failed: {e}")
            return None
    
    async def generate_alert_if_needed(self, ml_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate alert if anomaly is detected."""
        if not ml_result or not ml_result.get('is_anomaly', False):
            return None
        
        try:
            # Create alert data
            alert_data = {
                'alert_id': f"VL_ALERT_{int(ml_result['timestamp'])}",
                'timestamp': ml_result['timestamp'],
                'severity': self._determine_severity(ml_result),
                'title': self._generate_alert_title(ml_result),
                'description': self._generate_alert_description(ml_result),
                'confidence': ml_result['anomaly_confidence'],
                'impact': ml_result.get('impact_analysis', {}),
                'detected_series': ml_result.get('detected_series', []),
                'source': 'virtual_lab_ml_pipeline'
            }
            
            # Send alert if alert manager is available
            if self.alert_manager:
                try:
                    await self.alert_manager.send_alert(alert_data)
                except Exception as e:
                    logger.warning(f"Failed to send alert: {e}")
            
            # Publish to message bus
            await self.message_bus_manager.publish_alert(alert_data)
            
            self.stats['alerts_generated'] += 1
            logger.info(f"Alert generated: {alert_data['alert_id']}")
            
            return alert_data
            
        except Exception as e:
            logger.error(f"Failed to generate alert: {e}")
            return None
    
    def _determine_severity(self, ml_result: Dict[str, Any]) -> str:
        """Determine alert severity based on ML result."""
        confidence = ml_result.get('anomaly_confidence', 0.0)
        impact = ml_result.get('impact_analysis', {})
        
        if confidence > 0.9 and impact.get('impact') == 'NETWORK_IMPACTING':
            return 'CRITICAL'
        elif confidence > 0.7 and impact.get('impact') == 'NETWORK_IMPACTING':
            return 'HIGH'
        elif confidence > 0.5 or impact.get('impact') == 'EDGE_LOCAL':
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _generate_alert_title(self, ml_result: Dict[str, Any]) -> str:
        """Generate alert title based on ML result."""
        detected_series = ml_result.get('detected_series', [])
        impact = ml_result.get('impact_analysis', {})
        
        if 'wdr_total' in detected_series:
            return "BGP Withdrawal Anomaly Detected"
        elif 'ann_total' in detected_series:
            return "BGP Announcement Anomaly Detected"
        elif 'as_path_churn' in detected_series:
            return "BGP Path Churn Anomaly Detected"
        else:
            return "Network Anomaly Detected"
    
    def _generate_alert_description(self, ml_result: Dict[str, Any]) -> str:
        """Generate alert description based on ML result."""
        confidence = ml_result.get('anomaly_confidence', 0.0)
        detected_series = ml_result.get('detected_series', [])
        impact = ml_result.get('impact_analysis', {})
        
        description = f"Anomaly detected with confidence {confidence:.2f}. "
        
        if detected_series:
            description += f"Affected metrics: {', '.join(detected_series)}. "
        
        if impact:
            description += f"Impact: {impact.get('impact', 'Unknown')}. "
        
        return description.strip()
    
    async def run_integrated_cycle(self):
        """Run one cycle of the integrated ML pipeline."""
        try:
            # Generate telemetry data
            bgp_updates = await self.telemetry_generator.generate_bgp_telemetry()
            syslog_messages = await self.telemetry_generator.generate_syslog_telemetry()
            system_metrics = await self.telemetry_generator.generate_system_metrics()
            interface_metrics = await self.telemetry_generator.generate_interface_metrics()
            
            # Add to preprocessing pipeline
            self.preprocessing_pipeline.add_data('bgp', bgp_updates)
            self.preprocessing_pipeline.add_data('syslog', syslog_messages)
            self.preprocessing_pipeline.add_data('system', system_metrics)
            self.preprocessing_pipeline.add_data('interface', interface_metrics)
            
            # Extract features
            extracted_features = self.preprocessing_pipeline.extract_features()
            if not extracted_features:
                return
            
            # Process with ML pipeline
            ml_result = await self.process_features_with_ml(extracted_features)
            if not ml_result:
                return
            
            # Generate alert if needed
            alert = await self.generate_alert_if_needed(ml_result)
            
            # Log results
            if ml_result['is_anomaly']:
                logger.info(f"Anomaly detected: confidence={ml_result['anomaly_confidence']:.2f}, "
                           f"series={ml_result['detected_series']}")
            
        except Exception as e:
            logger.error(f"Error in integrated cycle: {e}")
    
    def get_integration_stats(self) -> Dict[str, Any]:
        """Get integration statistics."""
        return {
            'features_processed': self.stats['features_processed'],
            'anomalies_detected': self.stats['anomalies_detected'],
            'alerts_generated': self.stats['alerts_generated'],
            'false_positives': self.stats['false_positives'],
            'true_positives': self.stats['true_positives'],
            'detection_rate': self.stats['anomalies_detected'] / max(self.stats['features_processed'], 1),
            'alert_rate': self.stats['alerts_generated'] / max(self.stats['features_processed'], 1)
        }


async def main():
    """Main function for testing the ML pipeline integration."""
    config_path = "virtual_lab/configs/lab_config.yml"
    
    # Initialize integration
    integration = MLPipelineIntegration(config_path)
    
    try:
        # Start the integration
        await integration.start()
        
        logger.info("Running integrated ML pipeline for 2 minutes...")
        
        # Run for 2 minutes
        start_time = asyncio.get_event_loop().time()
        cycle_count = 0
        
        while (asyncio.get_event_loop().time() - start_time) < 120:  # 2 minutes
            await integration.run_integrated_cycle()
            cycle_count += 1
            
            # Wait before next cycle
            await asyncio.sleep(5.0)
        
        # Print final statistics
        stats = integration.get_integration_stats()
        logger.info(f"Integration completed after {cycle_count} cycles")
        logger.info(f"Final stats: {stats}")
        
    except KeyboardInterrupt:
        logger.info("Integration interrupted by user")
    except Exception as e:
        logger.error(f"Integration failed: {e}")
    finally:
        await integration.stop()


if __name__ == "__main__":
    asyncio.run(main())
