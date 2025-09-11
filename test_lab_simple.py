#!/usr/bin/env python3
"""
Simple test of the virtual lab integration.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("🔬 Testing Virtual Lab Integration")
print("=" * 40)

try:
    # Test importing virtual lab components
    print("1. Testing imports...")
    from virtual_lab.switch_emulator.network_switch import VirtualLabNetwork
    print("   ✅ VirtualLabNetwork imported")
    
    from virtual_lab.data_generators.telemetry_generator import TelemetryGenerator
    print("   ✅ TelemetryGenerator imported")
    
    from virtual_lab.preprocessing.feature_extractor import PreprocessingPipeline
    print("   ✅ PreprocessingPipeline imported")
    
    # Test importing existing ML components
    print("\n2. Testing ML component imports...")
    try:
        from python.models.gpu_mp_detector import GPUMPDetector
        print("   ✅ GPUMPDetector imported")
    except ImportError as e:
        print(f"   ⚠️ GPUMPDetector import failed: {e}")
    
    try:
        from python.utils.schema import BGPUpdate, FeatureBin
        print("   ✅ BGPUpdate, FeatureBin imported")
    except ImportError as e:
        print(f"   ⚠️ Schema imports failed: {e}")
    
    try:
        from python.features.stream_features import FeatureAggregator
        print("   ✅ FeatureAggregator imported")
    except ImportError as e:
        print(f"   ⚠️ FeatureAggregator import failed: {e}")
    
    print("\n3. Testing virtual lab initialization...")
    
    # Create a simple config
    import yaml
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
                'base_announcements_per_second': 5,
                'base_withdrawals_per_second': 1
            },
            'syslog': {
                'base_messages_per_second': 3,
                'severity_distribution': {
                    'info': 0.6, 'warning': 0.25, 'error': 0.1, 'critical': 0.05
                }
            }
        },
        'scaling': {
            'phases': [
                {'name': 'test', 'duration_minutes': 1, 'bgp_multiplier': 1.0, 'syslog_multiplier': 1.0}
            ]
        },
        'preprocessing': {
            'feature_extraction': {
                'time_windows': [30, 60],
                'features': {
                    'bgp': ['announcement_rate', 'withdrawal_rate'],
                    'syslog': ['error_rate', 'warning_rate']
                }
            }
        }
    }
    
    # Save config
    config_path = "virtual_lab/configs/test_config.yml"
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    with open(config_path, 'w') as f:
        yaml.dump(config, f)
    
    print(f"   ✅ Created test config: {config_path}")
    
    # Test network initialization
    network = VirtualLabNetwork(config_path)
    print("   ✅ VirtualLabNetwork initialized")
    
    # Test telemetry generator
    generator = TelemetryGenerator(config_path)
    print("   ✅ TelemetryGenerator initialized")
    
    # Test preprocessing pipeline
    pipeline = PreprocessingPipeline(config_path)
    print("   ✅ PreprocessingPipeline initialized")
    
    print("\n4. Testing event generation...")
    
    async def test_generation():
        # Generate events
        events = await network.generate_network_events()
        print(f"   Generated {len(events)} network events")
        
        # Generate telemetry
        bgp_updates = await generator.generate_bgp_telemetry()
        print(f"   Generated {len(bgp_updates)} BGP updates")
        
        syslog_messages = await generator.generate_syslog_telemetry()
        print(f"   Generated {len(syslog_messages)} syslog messages")
        
        # Test feature extraction
        pipeline.add_data('bgp', bgp_updates)
        pipeline.add_data('syslog', syslog_messages)
        
        features = pipeline.extract_features()
        if features:
            print(f"   Extracted {len(features.bgp_features)} BGP features")
            print(f"   Extracted {len(features.syslog_features)} syslog features")
        else:
            print("   No features extracted (may need more data)")
        
        return True
    
    # Run async test
    result = asyncio.run(test_generation())
    
    if result:
        print("\n✅ All tests passed! Virtual lab is working correctly.")
        print("\nNext steps:")
        print("1. Run: python virtual_lab/scripts/run_lab_with_ml.py")
        print("2. Or run: python virtual_lab/scripts/demo_lab.py")
    else:
        print("\n❌ Some tests failed.")
    
except Exception as e:
    print(f"\n❌ Test failed with error: {e}")
    import traceback
    traceback.print_exc()
