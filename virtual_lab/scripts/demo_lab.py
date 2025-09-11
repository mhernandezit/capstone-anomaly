#!/usr/bin/env python3
"""
Demo script for the virtual lab environment.

This script demonstrates the key capabilities of the virtual lab
without requiring a full setup or external dependencies.
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
from virtual_lab.preprocessing.feature_extractor import PreprocessingPipeline

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def demo_network_switch():
    """Demonstrate network switch emulation."""
    logger.info("🌐 Network Switch Emulation Demo")
    logger.info("=" * 50)
    
    # Create a simple config for demo
    config = {
        'topology': {
            'devices': {
                'spine_switches': {'count': 1, 'interfaces': 24},
                'tor_switches': {'count': 2, 'interfaces': 12},
                'leaf_switches': {'count': 4, 'interfaces': 8}
            },
            'bgp': {
                'prefix_pools': [
                    {'network': '10.0.0.0/8', 'count': 100},
                    {'network': '172.16.0.0/12', 'count': 50}
                ]
            }
        },
        'data_generation': {
            'bgp_telemetry': {
                'update_frequency': 2.0,
                'base_announcements_per_second': 5,
                'base_withdrawals_per_second': 1
            },
            'syslog': {
                'base_messages_per_second': 3,
                'severity_distribution': {
                    'info': 0.6, 'warning': 0.25, 'error': 0.1, 'critical': 0.05
                }
            }
        }
    }
    
    # Create temporary config file
    import yaml
    config_path = "virtual_lab/configs/demo_config.yml"
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    
    with open(config_path, 'w') as f:
        yaml.dump(config, f)
    
    try:
        # Initialize network
        network = VirtualLabNetwork(config_path)
        
        # Show network status
        status = network.get_network_status()
        logger.info(f"Created virtual network with {len(status)} switches:")
        for switch_id, switch_status in status.items():
            logger.info(f"  - {switch_id}: {switch_status['role']} "
                       f"({switch_status['interfaces_up']} up, {switch_status['bgp_peers_established']} BGP peers)")
        
        # Generate some events
        logger.info("\nGenerating network events...")
        events = await network.generate_network_events()
        
        # Categorize events
        bgp_events = [e for e in events if e.get('type') == 'UPDATE' or 'peer' in e]
        syslog_events = [e for e in events if e.get('type') == 'syslog' or 'severity' in e]
        
        logger.info(f"Generated {len(events)} total events:")
        logger.info(f"  - BGP updates: {len(bgp_events)}")
        logger.info(f"  - Syslog messages: {len(syslog_events)}")
        
        # Show sample events
        if bgp_events:
            logger.info(f"\nSample BGP update:")
            logger.info(f"  {bgp_events[0]}")
        
        if syslog_events:
            logger.info(f"\nSample syslog message:")
            logger.info(f"  {syslog_events[0]}")
        
        return True
        
    except Exception as e:
        logger.error(f"Network switch demo failed: {e}")
        return False
    finally:
        # Clean up
        if os.path.exists(config_path):
            os.remove(config_path)


async def demo_telemetry_generation():
    """Demonstrate telemetry data generation."""
    logger.info("\n📊 Telemetry Generation Demo")
    logger.info("=" * 50)
    
    # Create a simple config for demo
    config = {
        'topology': {
            'devices': {
                'spine_switches': {'count': 1, 'interfaces': 24},
                'tor_switches': {'count': 2, 'interfaces': 12}
            },
            'bgp': {
                'prefix_pools': [{'network': '10.0.0.0/8', 'count': 50}]
            }
        },
        'data_generation': {
            'bgp_telemetry': {
                'update_frequency': 1.0,
                'base_announcements_per_second': 3,
                'base_withdrawals_per_second': 1
            },
            'syslog': {
                'base_messages_per_second': 2,
                'severity_distribution': {
                    'info': 0.7, 'warning': 0.2, 'error': 0.1, 'critical': 0.0
                }
            }
        },
        'scaling': {
            'phases': [
                {'name': 'demo', 'duration_minutes': 1, 'bgp_multiplier': 1.0, 'syslog_multiplier': 1.0}
            ]
        }
    }
    
    # Create temporary config file
    import yaml
    config_path = "virtual_lab/configs/demo_config.yml"
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    
    with open(config_path, 'w') as f:
        yaml.dump(config, f)
    
    try:
        # Initialize generator
        generator = TelemetryGenerator(config_path)
        
        # Generate different types of telemetry
        logger.info("Generating BGP telemetry...")
        bgp_updates = await generator.generate_bgp_telemetry()
        logger.info(f"Generated {len(bgp_updates)} BGP updates")
        
        logger.info("Generating syslog telemetry...")
        syslog_messages = await generator.generate_syslog_telemetry()
        logger.info(f"Generated {len(syslog_messages)} syslog messages")
        
        logger.info("Generating system metrics...")
        system_metrics = await generator.generate_system_metrics()
        logger.info(f"Generated {len(system_metrics)} system metrics")
        
        logger.info("Generating interface metrics...")
        interface_metrics = await generator.generate_interface_metrics()
        logger.info(f"Generated {len(interface_metrics)} interface metrics")
        
        # Show sample data
        if bgp_updates:
            logger.info(f"\nSample BGP update:")
            logger.info(f"  Device: {bgp_updates[0].get('device_id')}")
            logger.info(f"  Peer: {bgp_updates[0].get('peer')}")
            logger.info(f"  Type: {bgp_updates[0].get('type')}")
            if bgp_updates[0].get('announce'):
                logger.info(f"  Announce: {bgp_updates[0]['announce'][0]}")
        
        if syslog_messages:
            logger.info(f"\nSample syslog message:")
            logger.info(f"  Device: {syslog_messages[0].get('device_id')}")
            logger.info(f"  Severity: {syslog_messages[0].get('severity')}")
            logger.info(f"  Message: {syslog_messages[0].get('message')}")
        
        # Show generation stats
        stats = generator.get_generation_stats()
        logger.info(f"\nGeneration statistics:")
        logger.info(f"  BGP updates: {stats['bgp_updates_generated']}")
        logger.info(f"  Syslog messages: {stats['syslog_messages_generated']}")
        logger.info(f"  BGP rate: {stats['bgp_rate_per_second']:.2f}/sec")
        logger.info(f"  Syslog rate: {stats['syslog_rate_per_second']:.2f}/sec")
        
        return True
        
    except Exception as e:
        logger.error(f"Telemetry generation demo failed: {e}")
        return False
    finally:
        # Clean up
        if os.path.exists(config_path):
            os.remove(config_path)


async def demo_feature_extraction():
    """Demonstrate feature extraction."""
    logger.info("\n🔬 Feature Extraction Demo")
    logger.info("=" * 50)
    
    # Create sample data
    sample_bgp_data = [
        {
            "timestamp": 1234567890,
            "device_id": "spine-01",
            "peer": "10.0.1.1",
            "type": "UPDATE",
            "announce": ["10.0.0.0/24"],
            "withdraw": None,
            "attrs": {"as_path_len": 3}
        },
        {
            "timestamp": 1234567891,
            "device_id": "spine-01",
            "peer": "10.0.1.2",
            "type": "UPDATE",
            "announce": None,
            "withdraw": ["10.0.1.0/24"],
            "attrs": {"as_path_len": 2}
        }
    ]
    
    sample_syslog_data = [
        {
            "timestamp": 1234567890,
            "device_id": "spine-01",
            "severity": "info",
            "message": "Interface GigabitEthernet0/0/1 is up"
        },
        {
            "timestamp": 1234567891,
            "device_id": "spine-01",
            "severity": "warning",
            "message": "BGP neighbor 10.0.1.1 went from Established to Idle"
        },
        {
            "timestamp": 1234567892,
            "device_id": "spine-01",
            "severity": "error",
            "message": "Interface GigabitEthernet0/0/2 is down"
        }
    ]
    
    sample_system_data = [
        {
            "timestamp": 1234567890,
            "device_id": "spine-01",
            "metric_type": "system",
            "metrics": {
                "cpu_usage_percent": 45.2,
                "memory_usage_percent": 67.8,
                "temperature_celsius": 42.1
            }
        }
    ]
    
    # Create a simple config for demo
    config = {
        'preprocessing': {
            'feature_extraction': {
                'time_windows': [30, 60],
                'features': {
                    'bgp': ['announcement_rate', 'withdrawal_rate', 'as_path_churn'],
                    'syslog': ['error_rate', 'warning_rate', 'message_frequency'],
                    'system': ['cpu_mean', 'memory_mean', 'temperature_mean']
                }
            },
            'feature_selection': {
                'method': 'mutual_information',
                'max_features': 10,
                'correlation_threshold': 0.8
            }
        }
    }
    
    # Create temporary config file
    import yaml
    config_path = "virtual_lab/configs/demo_config.yml"
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    
    with open(config_path, 'w') as f:
        yaml.dump(config, f)
    
    try:
        # Initialize preprocessing pipeline
        pipeline = PreprocessingPipeline(config_path)
        
        # Add sample data
        pipeline.add_data('bgp', sample_bgp_data)
        pipeline.add_data('syslog', sample_syslog_data)
        pipeline.add_data('system', sample_system_data)
        
        # Extract features
        logger.info("Extracting features from sample data...")
        features = pipeline.extract_features()
        
        if features:
            logger.info("✅ Features extracted successfully!")
            logger.info(f"  Window: {features.window_start} to {features.window_end}")
            logger.info(f"  BGP features: {len(features.bgp_features)}")
            logger.info(f"  Syslog features: {len(features.syslog_features)}")
            logger.info(f"  System features: {len(features.system_features)}")
            logger.info(f"  Correlation features: {len(features.correlation_features)}")
            logger.info(f"  Semantic features: {len(features.semantic_features)}")
            
            # Show some sample features
            logger.info(f"\nSample BGP features:")
            for key, value in list(features.bgp_features.items())[:3]:
                logger.info(f"  {key}: {value:.4f}")
            
            logger.info(f"\nSample syslog features:")
            for key, value in list(features.syslog_features.items())[:3]:
                logger.info(f"  {key}: {value:.4f}")
            
            logger.info(f"\nSample system features:")
            for key, value in list(features.system_features.items())[:3]:
                logger.info(f"  {key}: {value:.4f}")
        else:
            logger.warning("No features extracted (may need more data)")
        
        # Show processing stats
        stats = pipeline.get_processing_stats()
        logger.info(f"\nProcessing statistics:")
        logger.info(f"  Data buffer sizes: {stats['data_buffer_sizes']}")
        logger.info(f"  Feature history size: {stats['feature_history_size']}")
        
        return True
        
    except Exception as e:
        logger.error(f"Feature extraction demo failed: {e}")
        return False
    finally:
        # Clean up
        if os.path.exists(config_path):
            os.remove(config_path)


async def main():
    """Run all demos."""
    logger.info("🚀 Virtual Lab Demo")
    logger.info("=" * 60)
    logger.info("This demo shows the key capabilities of the virtual lab")
    logger.info("without requiring external dependencies or full setup.")
    logger.info("=" * 60)
    
    demos = [
        ("Network Switch Emulation", demo_network_switch),
        ("Telemetry Data Generation", demo_telemetry_generation),
        ("Feature Extraction", demo_feature_extraction)
    ]
    
    results = []
    for demo_name, demo_func in demos:
        logger.info(f"\n🎯 Running: {demo_name}")
        try:
            result = await demo_func()
            results.append(result)
            if result:
                logger.info(f"✅ {demo_name} completed successfully")
            else:
                logger.error(f"❌ {demo_name} failed")
        except Exception as e:
            logger.error(f"❌ {demo_name} failed with exception: {e}")
            results.append(False)
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("Demo Summary")
    logger.info("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    for i, (demo_name, _) in enumerate(demos):
        status = "✅ PASSED" if results[i] else "❌ FAILED"
        logger.info(f"{demo_name}: {status}")
    
    logger.info(f"\nOverall: {passed}/{total} demos passed")
    
    if passed == total:
        logger.info("🎉 All demos completed successfully!")
        logger.info("The virtual lab is ready for use.")
        logger.info("\nNext steps:")
        logger.info("1. Run: python virtual_lab/scripts/setup_lab.py")
        logger.info("2. Run: python virtual_lab/scripts/start_lab.py")
    else:
        logger.error("❌ Some demos failed. Please check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
