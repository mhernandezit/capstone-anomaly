#!/usr/bin/env python3
"""
Test script for virtual lab components.

This script tests individual components of the virtual lab
to ensure they work correctly before running the full lab.
"""

import asyncio
import sys
import os
import logging
from pathlib import Path

# Add the parent directory to the path so we can import our modules
sys.path.append(str(Path(__file__).parent.parent.parent))

from virtual_lab.switch_emulator.network_switch import VirtualLabNetwork
from virtual_lab.data_generators.telemetry_generator import TelemetryGenerator
from virtual_lab.message_bus.nats_publisher import MessageBusManager
from virtual_lab.preprocessing.feature_extractor import PreprocessingPipeline

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_network_switch():
    """Test the network switch emulator."""
    logger.info("Testing network switch emulator...")
    
    try:
        config_path = "virtual_lab/configs/lab_config.yml"
        network = VirtualLabNetwork(config_path)
        
        # Test generating events
        events = await network.generate_network_events()
        logger.info(f"Generated {len(events)} network events")
        
        # Test network status
        status = network.get_network_status()
        logger.info(f"Network status: {len(status)} switches")
        
        logger.info("✅ Network switch emulator test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Network switch emulator test failed: {e}")
        return False


async def test_telemetry_generator():
    """Test the telemetry generator."""
    logger.info("Testing telemetry generator...")
    
    try:
        config_path = "virtual_lab/configs/lab_config.yml"
        generator = TelemetryGenerator(config_path)
        
        # Test generating different types of telemetry
        bgp_updates = await generator.generate_bgp_telemetry()
        logger.info(f"Generated {len(bgp_updates)} BGP updates")
        
        syslog_messages = await generator.generate_syslog_telemetry()
        logger.info(f"Generated {len(syslog_messages)} syslog messages")
        
        system_metrics = await generator.generate_system_metrics()
        logger.info(f"Generated {len(system_metrics)} system metrics")
        
        interface_metrics = await generator.generate_interface_metrics()
        logger.info(f"Generated {len(interface_metrics)} interface metrics")
        
        bgp_metrics = await generator.generate_bgp_metrics()
        logger.info(f"Generated {len(bgp_metrics)} BGP metrics")
        
        # Test statistics
        stats = generator.get_generation_stats()
        logger.info(f"Generation stats: {stats}")
        
        logger.info("✅ Telemetry generator test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Telemetry generator test failed: {e}")
        return False


async def test_message_bus():
    """Test the message bus (without actual NATS connection)."""
    logger.info("Testing message bus manager...")
    
    try:
        config_path = "virtual_lab/configs/lab_config.yml"
        manager = MessageBusManager(config_path)
        
        # Test configuration loading
        logger.info(f"Message bus config: {manager.message_bus_config}")
        
        # Test statistics
        stats = manager.get_stats()
        logger.info(f"Message bus stats: {stats}")
        
        logger.info("✅ Message bus manager test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Message bus manager test failed: {e}")
        return False


async def test_preprocessing_pipeline():
    """Test the preprocessing pipeline."""
    logger.info("Testing preprocessing pipeline...")
    
    try:
        config_path = "virtual_lab/configs/lab_config.yml"
        pipeline = PreprocessingPipeline(config_path)
        
        # Test adding data
        test_bgp_data = [
            {
                "timestamp": 1234567890,
                "device_id": "spine-01",
                "peer": "10.0.1.1",
                "type": "UPDATE",
                "announce": ["10.0.0.0/24"],
                "withdraw": None,
                "attrs": {"as_path_len": 3}
            }
        ]
        
        test_syslog_data = [
            {
                "timestamp": 1234567890,
                "device_id": "spine-01",
                "severity": "info",
                "message": "Interface GigabitEthernet0/0/1 is up"
            }
        ]
        
        pipeline.add_data('bgp', test_bgp_data)
        pipeline.add_data('syslog', test_syslog_data)
        
        # Test feature extraction
        features = pipeline.extract_features()
        if features:
            logger.info(f"Extracted features: {len(features.bgp_features)} BGP, {len(features.syslog_features)} syslog")
        else:
            logger.warning("No features extracted (may need more data)")
        
        # Test statistics
        stats = pipeline.get_processing_stats()
        logger.info(f"Processing stats: {stats}")
        
        logger.info("✅ Preprocessing pipeline test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Preprocessing pipeline test failed: {e}")
        return False


async def run_all_tests():
    """Run all component tests."""
    logger.info("Running virtual lab component tests...")
    
    tests = [
        test_network_switch,
        test_telemetry_generator,
        test_message_bus,
        test_preprocessing_pipeline
    ]
    
    results = []
    for test in tests:
        result = await test()
        results.append(result)
        logger.info("")  # Add spacing between tests
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    logger.info("=" * 50)
    logger.info(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Virtual lab components are ready.")
        return True
    else:
        logger.error(f"❌ {total - passed} tests failed. Please fix issues before running the lab.")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
