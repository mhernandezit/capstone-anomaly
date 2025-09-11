#!/usr/bin/env python3
"""
Quick start script for the virtual lab environment.

This script provides a simple way to start the virtual lab
with common configurations.
"""

import asyncio
import sys
import os
import logging
from pathlib import Path

# Add the parent directory to the path so we can import our modules
sys.path.append(str(Path(__file__).parent.parent.parent))

from virtual_lab.scripts.lab_orchestrator import VirtualLabOrchestrator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def quick_start():
    """Quick start the virtual lab with default settings."""
    config_path = "virtual_lab/configs/lab_config.yml"
    
    # Check if config file exists
    if not os.path.exists(config_path):
        logger.error(f"Configuration file not found: {config_path}")
        logger.error("Please run this script from the project root directory")
        sys.exit(1)
    
    # Initialize orchestrator
    orchestrator = VirtualLabOrchestrator(config_path)
    
    try:
        logger.info("Starting virtual lab environment...")
        
        # Start the lab
        await orchestrator.start()
        
        # Run for 5 minutes by default
        logger.info("Running virtual lab for 5 minutes...")
        await orchestrator.run(duration_minutes=5)
        
        # Export results
        results_path = "virtual_lab/logs/lab_results.json"
        orchestrator.export_results(results_path)
        logger.info(f"Results exported to {results_path}")
        
        # Print summary
        status = orchestrator.get_status()
        logger.info("Virtual lab completed successfully!")
        logger.info(f"Total runtime: {status['total_runtime_seconds']:.2f} seconds")
        logger.info(f"Data generated: {status.get('telemetry_stats', {}).get('bgp_updates_generated', 0)} BGP updates")
        logger.info(f"Features extracted: {status.get('preprocessing_stats', {}).get('feature_history_size', 0)}")
        
    except KeyboardInterrupt:
        logger.info("Virtual lab interrupted by user")
    except Exception as e:
        logger.error(f"Virtual lab failed: {e}")
        sys.exit(1)
    finally:
        if orchestrator.running:
            await orchestrator.stop()


if __name__ == "__main__":
    asyncio.run(quick_start())
