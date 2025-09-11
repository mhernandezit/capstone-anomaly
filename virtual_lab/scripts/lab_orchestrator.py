"""
Virtual Lab Orchestrator

This is the main entry point for the virtual lab environment.
It coordinates all components and provides a unified interface
for running the complete lab environment.
"""

import asyncio
import argparse
import logging
import signal
import sys
from datetime import datetime
from typing import Dict, Any, Optional
import yaml
import json

from ..data_generators.telemetry_generator import TelemetryGenerator
from ..message_bus.nats_publisher import MessageBusManager
from ..preprocessing.feature_extractor import PreprocessingPipeline
from .scaling_controller import ScalingController, ScalingMonitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('virtual_lab/logs/lab.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class VirtualLabOrchestrator:
    """
    Main orchestrator for the virtual lab environment.
    
    This class coordinates all components of the virtual lab:
    - Data generation (BGP, syslog, telemetry)
    - Message bus communication
    - Feature extraction and preprocessing
    - Scaling control
    - Monitoring and alerting
    """
    
    def __init__(self, config_path: str):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.config_path = config_path
        self.running = False
        
        # Initialize components
        self.telemetry_generator = TelemetryGenerator(config_path)
        self.message_bus_manager = MessageBusManager(config_path)
        self.preprocessing_pipeline = PreprocessingPipeline(config_path)
        self.scaling_controller = ScalingController(config_path)
        
        # Monitoring
        self.monitor = ScalingMonitor(self.scaling_controller)
        
        # Statistics
        self.stats = {
            'start_time': None,
            'end_time': None,
            'total_runtime': 0,
            'components_started': 0,
            'components_stopped': 0,
            'errors': 0
        }
        
        logger.info("Virtual lab orchestrator initialized")
    
    async def start(self):
        """Start the virtual lab environment."""
        try:
            logger.info("Starting virtual lab environment...")
            self.stats['start_time'] = datetime.now()
            self.running = True
            
            # Start message bus manager
            await self.message_bus_manager.start()
            self.stats['components_started'] += 1
            logger.info("Message bus manager started")
            
            # Start scaling controller
            await self.scaling_controller.start()
            self.stats['components_started'] += 1
            logger.info("Scaling controller started")
            
            logger.info("Virtual lab environment started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start virtual lab environment: {e}")
            self.stats['errors'] += 1
            raise
    
    async def stop(self):
        """Stop the virtual lab environment."""
        try:
            logger.info("Stopping virtual lab environment...")
            self.running = False
            
            # Stop scaling controller
            await self.scaling_controller.stop()
            self.stats['components_stopped'] += 1
            logger.info("Scaling controller stopped")
            
            # Stop message bus manager
            await self.message_bus_manager.stop()
            self.stats['components_stopped'] += 1
            logger.info("Message bus manager stopped")
            
            self.stats['end_time'] = datetime.now()
            if self.stats['start_time']:
                self.stats['total_runtime'] = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
            
            logger.info("Virtual lab environment stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping virtual lab environment: {e}")
            self.stats['errors'] += 1
    
    async def run(self, duration_minutes: Optional[int] = None):
        """Run the virtual lab for a specified duration or until completion."""
        try:
            logger.info(f"Running virtual lab for {duration_minutes} minutes" if duration_minutes else "Running until completion")
            
            # Start monitoring in background
            monitor_task = asyncio.create_task(self.monitor.start_monitoring())
            
            # Run scaling cycles
            start_time = asyncio.get_event_loop().time()
            cycle_count = 0
            
            while self.running:
                # Run one scaling cycle
                await self.scaling_controller.run_scaling_cycle()
                cycle_count += 1
                
                # Check if duration limit reached
                if duration_minutes:
                    elapsed_minutes = (asyncio.get_event_loop().time() - start_time) / 60
                    if elapsed_minutes >= duration_minutes:
                        logger.info(f"Duration limit of {duration_minutes} minutes reached")
                        break
                
                # Check if all phases completed
                status = self.scaling_controller.get_current_status()
                if status['phases_completed'] >= status['total_phases']:
                    logger.info("All scaling phases completed")
                    break
                
                # Wait before next cycle
                await asyncio.sleep(1.0)
            
            # Wait for monitoring to complete
            await monitor_task
            
            logger.info(f"Virtual lab completed after {cycle_count} cycles")
            
        except Exception as e:
            logger.error(f"Error running virtual lab: {e}")
            self.stats['errors'] += 1
            raise
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of the virtual lab."""
        status = {
            'running': self.running,
            'start_time': self.stats['start_time'].isoformat() if self.stats['start_time'] else None,
            'end_time': self.stats['end_time'].isoformat() if self.stats['end_time'] else None,
            'total_runtime_seconds': self.stats['total_runtime'],
            'components_started': self.stats['components_started'],
            'components_stopped': self.stats['components_stopped'],
            'errors': self.stats['errors']
        }
        
        # Add component statuses
        if hasattr(self, 'scaling_controller'):
            status['scaling_status'] = self.scaling_controller.get_current_status()
        
        if hasattr(self, 'message_bus_manager'):
            status['message_bus_stats'] = self.message_bus_manager.get_stats()
        
        if hasattr(self, 'telemetry_generator'):
            status['telemetry_stats'] = self.telemetry_generator.get_generation_stats()
        
        if hasattr(self, 'preprocessing_pipeline'):
            status['preprocessing_stats'] = self.preprocessing_pipeline.get_processing_stats()
        
        return status
    
    def get_phase_history(self) -> list:
        """Get history of completed scaling phases."""
        if hasattr(self, 'scaling_controller'):
            return self.scaling_controller.get_phase_history()
        return []
    
    def export_results(self, output_path: str):
        """Export lab results to a file."""
        try:
            results = {
                'lab_config': self.config,
                'status': self.get_status(),
                'phase_history': self.get_phase_history(),
                'export_timestamp': datetime.now().isoformat()
            }
            
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            logger.info(f"Results exported to {output_path}")
            
        except Exception as e:
            logger.error(f"Failed to export results: {e}")
            self.stats['errors'] += 1


def setup_signal_handlers(orchestrator: VirtualLabOrchestrator):
    """Setup signal handlers for graceful shutdown."""
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        asyncio.create_task(orchestrator.stop())
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


async def main():
    """Main function for running the virtual lab."""
    parser = argparse.ArgumentParser(description='Virtual Lab for BGP Anomaly Detection')
    parser.add_argument('--config', default='virtual_lab/configs/lab_config.yml',
                       help='Path to lab configuration file')
    parser.add_argument('--duration', type=int, default=None,
                       help='Duration to run the lab in minutes (default: run until completion)')
    parser.add_argument('--export-results', default=None,
                       help='Path to export results JSON file')
    parser.add_argument('--log-level', default='INFO',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Logging level')
    
    args = parser.parse_args()
    
    # Set logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Initialize orchestrator
    orchestrator = VirtualLabOrchestrator(args.config)
    
    # Setup signal handlers
    setup_signal_handlers(orchestrator)
    
    try:
        # Start the lab
        await orchestrator.start()
        
        # Run the lab
        await orchestrator.run(args.duration)
        
        # Export results if requested
        if args.export_results:
            orchestrator.export_results(args.export_results)
        
        # Print final status
        status = orchestrator.get_status()
        logger.info("Virtual lab completed successfully")
        logger.info(f"Final status: {json.dumps(status, indent=2, default=str)}")
        
    except KeyboardInterrupt:
        logger.info("Virtual lab interrupted by user")
    except Exception as e:
        logger.error(f"Virtual lab failed: {e}")
        sys.exit(1)
    finally:
        # Ensure cleanup
        if orchestrator.running:
            await orchestrator.stop()


if __name__ == "__main__":
    asyncio.run(main())
