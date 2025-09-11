"""
Scaling Controller for Virtual Lab

This module controls the progressive scaling of data generation
to test the ML pipeline under increasing load conditions.
"""

import asyncio
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import yaml
import json

from ..data_generators.telemetry_generator import TelemetryGenerator
from ..message_bus.nats_publisher import MessageBusManager
from ..preprocessing.feature_extractor import PreprocessingPipeline

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ScalingPhase:
    """Represents a scaling phase with its configuration."""
    
    def __init__(self, name: str, duration_minutes: int, bgp_multiplier: float, syslog_multiplier: float):
        self.name = name
        self.duration_minutes = duration_minutes
        self.duration_seconds = duration_minutes * 60
        self.bgp_multiplier = bgp_multiplier
        self.syslog_multiplier = syslog_multiplier
        self.start_time = None
        self.end_time = None
        self.completed = False
    
    def start(self):
        """Start this scaling phase."""
        self.start_time = time.time()
        self.end_time = self.start_time + self.duration_seconds
        self.completed = False
        logger.info(f"Started scaling phase: {self.name} "
                   f"(BGP: {self.bgp_multiplier}x, Syslog: {self.syslog_multiplier}x)")
    
    def is_active(self) -> bool:
        """Check if this phase is currently active."""
        if self.start_time is None:
            return False
        return time.time() < self.end_time and not self.completed
    
    def is_completed(self) -> bool:
        """Check if this phase has completed."""
        if self.start_time is None:
            return False
        return time.time() >= self.end_time or self.completed
    
    def complete(self):
        """Mark this phase as completed."""
        self.completed = True
        logger.info(f"Completed scaling phase: {self.name}")
    
    def get_elapsed_time(self) -> float:
        """Get elapsed time in seconds."""
        if self.start_time is None:
            return 0.0
        return time.time() - self.start_time
    
    def get_remaining_time(self) -> float:
        """Get remaining time in seconds."""
        if self.start_time is None:
            return self.duration_seconds
        return max(0, self.end_time - time.time())


class ScalingController:
    """
    Controls the progressive scaling of the virtual lab.
    
    This class manages the scaling phases and coordinates between
    data generation, preprocessing, and ML pipeline components.
    """
    
    def __init__(self, config_path: str):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.scaling_config = self.config.get('scaling', {})
        self.phases = self._initialize_phases()
        self.current_phase_index = 0
        self.current_phase = None
        
        # Components
        self.telemetry_generator = TelemetryGenerator(config_path)
        self.message_bus_manager = MessageBusManager(config_path)
        self.preprocessing_pipeline = PreprocessingPipeline(config_path)
        
        # Statistics
        self.stats = {
            'phases_completed': 0,
            'total_data_generated': 0,
            'total_features_extracted': 0,
            'total_alerts_generated': 0,
            'start_time': None,
            'phase_history': []
        }
        
        logger.info("Scaling controller initialized")
    
    def _initialize_phases(self) -> List[ScalingPhase]:
        """Initialize scaling phases from configuration."""
        phases = []
        phase_configs = self.scaling_config.get('phases', [])
        
        for phase_config in phase_configs:
            phase = ScalingPhase(
                name=phase_config.get('name', 'unknown'),
                duration_minutes=phase_config.get('duration_minutes', 5),
                bgp_multiplier=phase_config.get('bgp_multiplier', 1.0),
                syslog_multiplier=phase_config.get('syslog_multiplier', 1.0)
            )
            phases.append(phase)
        
        logger.info(f"Initialized {len(phases)} scaling phases")
        return phases
    
    async def start(self):
        """Start the scaling controller."""
        # Start message bus manager
        await self.message_bus_manager.start()
        
        # Start first phase
        if self.phases:
            self.current_phase = self.phases[0]
            self.current_phase.start()
        
        self.stats['start_time'] = time.time()
        logger.info("Scaling controller started")
    
    async def stop(self):
        """Stop the scaling controller."""
        await self.message_bus_manager.stop()
        logger.info("Scaling controller stopped")
    
    async def run_scaling_cycle(self):
        """Run one cycle of the scaling process."""
        if not self.current_phase:
            logger.warning("No active scaling phase")
            return
        
        # Check if current phase is completed
        if self.current_phase.is_completed():
            await self._complete_current_phase()
            await self._start_next_phase()
            return
        
        # Generate telemetry data
        try:
            # Generate BGP updates
            bgp_updates = await self.telemetry_generator.generate_bgp_telemetry()
            if bgp_updates:
                await self.message_bus_manager.publish_data('bgp', bgp_updates)
                self.stats['total_data_generated'] += len(bgp_updates)
            
            # Generate syslog messages
            syslog_messages = await self.telemetry_generator.generate_syslog_telemetry()
            if syslog_messages:
                await self.message_bus_manager.publish_data('syslog', syslog_messages)
                self.stats['total_data_generated'] += len(syslog_messages)
            
            # Generate system metrics
            system_metrics = await self.telemetry_generator.generate_system_metrics()
            if system_metrics:
                await self.message_bus_manager.publish_data('telemetry', system_metrics)
                self.stats['total_data_generated'] += len(system_metrics)
            
            # Generate interface metrics
            interface_metrics = await self.telemetry_generator.generate_interface_metrics()
            if interface_metrics:
                await self.message_bus_manager.publish_data('telemetry', interface_metrics)
                self.stats['total_data_generated'] += len(interface_metrics)
            
            # Generate BGP metrics
            bgp_metrics = await self.telemetry_generator.generate_bgp_metrics()
            if bgp_metrics:
                await self.message_bus_manager.publish_data('telemetry', bgp_metrics)
                self.stats['total_data_generated'] += len(bgp_metrics)
            
            # Add data to preprocessing pipeline
            self.preprocessing_pipeline.add_data('bgp', bgp_updates)
            self.preprocessing_pipeline.add_data('syslog', syslog_messages)
            self.preprocessing_pipeline.add_data('system', system_metrics)
            self.preprocessing_pipeline.add_data('interface', interface_metrics)
            
            # Extract features
            extracted_features = self.preprocessing_pipeline.extract_features()
            if extracted_features:
                # Convert to dictionary for publishing
                features_dict = {
                    'timestamp': int(time.time() * 1000),
                    'window_start': extracted_features.window_start.isoformat(),
                    'window_end': extracted_features.window_end.isoformat(),
                    'bgp_features': extracted_features.bgp_features,
                    'syslog_features': extracted_features.syslog_features,
                    'system_features': extracted_features.system_features,
                    'interface_features': extracted_features.interface_features,
                    'correlation_features': extracted_features.correlation_features,
                    'semantic_features': extracted_features.semantic_features
                }
                
                await self.message_bus_manager.publish_features(features_dict)
                self.stats['total_features_extracted'] += 1
                
                # Check for anomalies (simplified)
                if self._detect_anomaly(features_dict):
                    alert = self._create_anomaly_alert(features_dict)
                    await self.message_bus_manager.publish_alert(alert)
                    self.stats['total_alerts_generated'] += 1
        
        except Exception as e:
            logger.error(f"Error in scaling cycle: {e}")
    
    async def _complete_current_phase(self):
        """Complete the current scaling phase."""
        if not self.current_phase:
            return
        
        self.current_phase.complete()
        self.stats['phases_completed'] += 1
        
        # Record phase history
        phase_stats = {
            'name': self.current_phase.name,
            'duration_minutes': self.current_phase.duration_minutes,
            'bgp_multiplier': self.current_phase.bgp_multiplier,
            'syslog_multiplier': self.current_phase.syslog_multiplier,
            'actual_duration': self.current_phase.get_elapsed_time(),
            'data_generated': self.stats['total_data_generated'],
            'features_extracted': self.stats['total_features_extracted'],
            'alerts_generated': self.stats['total_alerts_generated']
        }
        self.stats['phase_history'].append(phase_stats)
        
        logger.info(f"Completed phase: {self.current_phase.name}")
        logger.info(f"Phase stats: {phase_stats}")
    
    async def _start_next_phase(self):
        """Start the next scaling phase."""
        self.current_phase_index += 1
        
        if self.current_phase_index >= len(self.phases):
            logger.info("All scaling phases completed")
            self.current_phase = None
            return
        
        self.current_phase = self.phases[self.current_phase_index]
        self.current_phase.start()
    
    def _detect_anomaly(self, features: Dict[str, Any]) -> bool:
        """Simple anomaly detection based on feature values."""
        # This is a simplified example - in practice would use the ML pipeline
        
        # Check BGP features
        bgp_features = features.get('bgp_features', {})
        if bgp_features.get('withdrawal_rate', 0) > 10:  # High withdrawal rate
            return True
        
        if bgp_features.get('update_burstiness', 0) > 5:  # High burstiness
            return True
        
        # Check syslog features
        syslog_features = features.get('syslog_features', {})
        if syslog_features.get('error_rate', 0) > 0.5:  # High error rate
            return True
        
        # Check system features
        system_features = features.get('system_features', {})
        if system_features.get('cpu_max', 0) > 90:  # High CPU usage
            return True
        
        if system_features.get('memory_max', 0) > 95:  # High memory usage
            return True
        
        return False
    
    def _create_anomaly_alert(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Create an anomaly alert."""
        return {
            'alert_id': f"ALERT_{int(time.time())}",
            'timestamp': int(time.time() * 1000),
            'severity': 'HIGH',
            'title': 'Anomaly Detected in Virtual Lab',
            'description': 'Anomalous patterns detected in network telemetry data',
            'features': features,
            'confidence': 0.85,
            'source': 'virtual_lab_scaling_controller'
        }
    
    def get_current_status(self) -> Dict[str, Any]:
        """Get current status of the scaling controller."""
        status = {
            'current_phase': self.current_phase.name if self.current_phase else None,
            'phase_index': self.current_phase_index,
            'total_phases': len(self.phases),
            'phases_completed': self.stats['phases_completed'],
            'elapsed_time': time.time() - self.stats['start_time'] if self.stats['start_time'] else 0,
            'total_data_generated': self.stats['total_data_generated'],
            'total_features_extracted': self.stats['total_features_extracted'],
            'total_alerts_generated': self.stats['total_alerts_generated']
        }
        
        if self.current_phase:
            status.update({
                'phase_elapsed_time': self.current_phase.get_elapsed_time(),
                'phase_remaining_time': self.current_phase.get_remaining_time(),
                'bgp_multiplier': self.current_phase.bgp_multiplier,
                'syslog_multiplier': self.current_phase.syslog_multiplier
            })
        
        return status
    
    def get_phase_history(self) -> List[Dict[str, Any]]:
        """Get history of completed phases."""
        return self.stats['phase_history'].copy()
    
    def get_telemetry_stats(self) -> Dict[str, Any]:
        """Get telemetry generation statistics."""
        return self.telemetry_generator.get_generation_stats()
    
    def get_message_bus_stats(self) -> Dict[str, Any]:
        """Get message bus statistics."""
        return self.message_bus_manager.get_stats()
    
    def get_preprocessing_stats(self) -> Dict[str, Any]:
        """Get preprocessing pipeline statistics."""
        return self.preprocessing_pipeline.get_processing_stats()


class ScalingMonitor:
    """
    Monitors the scaling process and provides real-time feedback.
    """
    
    def __init__(self, controller: ScalingController):
        self.controller = controller
        self.monitoring = True
    
    async def start_monitoring(self, interval_seconds: int = 10):
        """Start monitoring the scaling process."""
        logger.info("Starting scaling monitor")
        
        while self.monitoring:
            try:
                # Get current status
                status = self.controller.get_current_status()
                
                # Log status
                logger.info(f"Scaling Status: {status}")
                
                # Check if all phases are completed
                if status['phases_completed'] >= status['total_phases']:
                    logger.info("All scaling phases completed")
                    break
                
                # Wait for next check
                await asyncio.sleep(interval_seconds)
                
            except Exception as e:
                logger.error(f"Error in monitoring: {e}")
                await asyncio.sleep(interval_seconds)
    
    def stop_monitoring(self):
        """Stop monitoring."""
        self.monitoring = False
        logger.info("Scaling monitor stopped")


async def main():
    """Main function for running the scaling controller."""
    config_path = "virtual_lab/configs/lab_config.yml"
    
    # Initialize scaling controller
    controller = ScalingController(config_path)
    monitor = ScalingMonitor(controller)
    
    try:
        # Start the controller
        await controller.start()
        
        # Start monitoring in background
        monitor_task = asyncio.create_task(monitor.start_monitoring())
        
        # Run scaling cycles
        while True:
            await controller.run_scaling_cycle()
            
            # Check if all phases are completed
            status = controller.get_current_status()
            if status['phases_completed'] >= status['total_phases']:
                break
            
            # Wait before next cycle
            await asyncio.sleep(1.0)
        
        # Wait for monitoring to complete
        await monitor_task
        
        # Print final statistics
        logger.info("Scaling process completed")
        logger.info(f"Final stats: {controller.get_current_status()}")
        logger.info(f"Phase history: {controller.get_phase_history()}")
        
    except KeyboardInterrupt:
        logger.info("Scaling process interrupted by user")
    except Exception as e:
        logger.error(f"Error in scaling process: {e}")
    finally:
        await controller.stop()
        monitor.stop_monitoring()


if __name__ == "__main__":
    asyncio.run(main())
