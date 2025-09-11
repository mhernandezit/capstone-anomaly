#!/usr/bin/env python3
"""
Run Virtual Lab with ML Analysis

This script demonstrates how to use the virtual lab to generate events
and analyze them with the existing ML models.
"""

import asyncio
import sys
import os
import logging
import time
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import virtual lab components
from virtual_lab.switch_emulator.network_switch import VirtualLabNetwork
from virtual_lab.data_generators.telemetry_generator import TelemetryGenerator
from virtual_lab.preprocessing.feature_extractor import PreprocessingPipeline

# Import existing ML components
try:
    from python.models.gpu_mp_detector import GPUMPDetector
    from python.utils.schema import FeatureBin
    logger.info("✅ Successfully imported existing ML components")
except ImportError as e:
    logger.warning(f"Could not import ML components: {e}")
    logger.warning("Running in simulation mode")

# Import existing feature aggregator
try:
    from python.features.stream_features import FeatureAggregator
    logger.info("✅ Successfully imported FeatureAggregator")
except ImportError as e:
    logger.warning(f"Could not import FeatureAggregator: {e}")


class LabMLIntegration:
    """
    Integrates virtual lab data generation with existing ML models.
    """
    
    def __init__(self):
        self.config_path = "virtual_lab/configs/lab_config.yml"
        
        # Initialize virtual lab components
        self.network = VirtualLabNetwork(self.config_path)
        self.telemetry_generator = TelemetryGenerator(self.config_path)
        self.preprocessing_pipeline = PreprocessingPipeline(self.config_path)
        
        # Initialize ML components
        self.mp_detector = None
        self.feature_aggregator = None
        self._initialize_ml_components()
        
        # Statistics
        self.stats = {
            'events_generated': 0,
            'features_extracted': 0,
            'anomalies_detected': 0,
            'start_time': time.time()
        }
    
    def _initialize_ml_components(self):
        """Initialize ML components."""
        try:
            # Initialize Matrix Profile detector
            self.mp_detector = GPUMPDetector(
                window_bins=64,
                series_keys=['wdr_total', 'ann_total', 'as_path_churn'],
                discord_threshold=2.5
            )
            logger.info("✅ Matrix Profile detector initialized")
            
            # Initialize feature aggregator
            self.feature_aggregator = FeatureAggregator(bin_seconds=30)
            logger.info("✅ Feature aggregator initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize ML components: {e}")
    
    def convert_lab_data_to_bgp_updates(self, lab_events):
        """Convert lab events to BGP update format for existing ML pipeline."""
        bgp_updates = []
        
        for event in lab_events:
            if event.get('type') == 'UPDATE' or 'peer' in event:
                # Convert to BGPUpdate format
                bgp_update = {
                    'ts': event.get('timestamp', int(time.time())),
                    'peer': event.get('peer', 'unknown'),
                    'type': event.get('type', 'UPDATE'),
                    'announce': event.get('announce'),
                    'withdraw': event.get('withdraw'),
                    'attrs': event.get('attrs', {})
                }
                bgp_updates.append(bgp_update)
        
        return bgp_updates
    
    async def generate_and_analyze_events(self, duration_minutes=5):
        """Generate events and analyze them with ML models."""
        logger.info(f"🚀 Starting lab event generation and ML analysis for {duration_minutes} minutes")
        
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        cycle_count = 0
        
        while time.time() < end_time:
            cycle_count += 1
            logger.info(f"📊 Cycle {cycle_count} - Generating events...")
            
            # Generate events from virtual lab
            lab_events = await self.network.generate_network_events()
            self.stats['events_generated'] += len(lab_events)
            
            # Convert to BGP updates for ML pipeline
            bgp_updates = self.convert_lab_data_to_bgp_updates(lab_events)
            
            if bgp_updates:
                logger.info(f"  Generated {len(bgp_updates)} BGP updates")
                
                # Process through existing feature aggregator
                if self.feature_aggregator:
                    for update_data in bgp_updates:
                        # Convert to BGPUpdate object
                        from python.utils.schema import BGPUpdate
                        bgp_update = BGPUpdate(**update_data)
                        self.feature_aggregator.add_update(bgp_update)
                    
                    # Check for closed bins
                    while self.feature_aggregator.has_closed_bin():
                        feature_bin = self.feature_aggregator.pop_closed_bin()
                        logger.info(f"  Processing feature bin: {feature_bin.bin_start} - {feature_bin.bin_end}")
                        
                        # Analyze with Matrix Profile detector
                        if self.mp_detector:
                            mp_result = self.mp_detector.update(feature_bin)
                            
                            if mp_result.get('is_anomaly', False):
                                logger.warning(f"🚨 ANOMALY DETECTED!")
                                logger.warning(f"  Confidence: {mp_result.get('anomaly_confidence', 0):.2f}")
                                logger.warning(f"  Detected series: {mp_result.get('detected_series', [])}")
                                logger.warning(f"  Overall score: {mp_result.get('overall_score', {}).get('score', 0):.2f}")
                                self.stats['anomalies_detected'] += 1
                            else:
                                logger.info(f"  Normal operation - Score: {mp_result.get('overall_score', {}).get('score', 0):.2f}")
                        
                        self.stats['features_extracted'] += 1
            
            # Also process through virtual lab preprocessing
            self.preprocessing_pipeline.add_data('bgp', bgp_updates)
            
            # Extract features using virtual lab pipeline
            extracted_features = self.preprocessing_pipeline.extract_features()
            if extracted_features:
                logger.info(f"  Virtual lab features: {len(extracted_features.bgp_features)} BGP features")
            
            # Wait before next cycle
            await asyncio.sleep(2.0)
        
        # Print final statistics
        elapsed_time = time.time() - start_time
        logger.info(f"\n📈 Final Statistics:")
        logger.info(f"  Duration: {elapsed_time:.1f} seconds")
        logger.info(f"  Events generated: {self.stats['events_generated']}")
        logger.info(f"  Features extracted: {self.stats['features_extracted']}")
        logger.info(f"  Anomalies detected: {self.stats['anomalies_detected']}")
        logger.info(f"  Event rate: {self.stats['events_generated'] / elapsed_time:.1f} events/sec")
        logger.info(f"  Feature rate: {self.stats['features_extracted'] / elapsed_time:.1f} features/sec")


async def main():
    """Main function."""
    logger.info("🔬 Virtual Lab + ML Analysis Demo")
    logger.info("=" * 50)
    
    # Initialize integration
    integration = LabMLIntegration()
    
    try:
        # Run for 2 minutes by default
        await integration.generate_and_analyze_events(duration_minutes=2)
        
        logger.info("\n✅ Demo completed successfully!")
        logger.info("This shows how the virtual lab generates realistic events")
        logger.info("and processes them through your existing ML pipeline.")
        
    except KeyboardInterrupt:
        logger.info("\n⏹️ Demo interrupted by user")
    except Exception as e:
        logger.error(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
