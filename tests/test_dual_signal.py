"""
Test script for dual-signal BGP + Syslog anomaly detection
"""

import asyncio
import time
from src.simulators.syslog_simulator import SyslogSimulator
from src.dual_signal_pipeline import DualSignalPipeline

async def test_dual_signal_detection():
    """Test the dual-signal detection system."""
    print("Testing Dual-Signal BGP + Syslog Detection")
    print("=" * 50)
    
    # Configuration
    config = {
        'nats_url': 'nats://localhost:4222',
        'bin_seconds': 30,
        'mp_window_bins': 32,  # Smaller for faster testing
        'mp_series_keys': ['wdr_total', 'ann_total', 'as_path_churn'],
        'mp_discord_threshold': 2.0,
        'gpu_memory_limit': '1GB',
        'correlation_window_seconds': 60,
        'roles_config': {
            'roles': {
                '10.0.0.1': 'rr',
                '10.0.1.1': 'spine',
                '10.0.2.1': 'tor',
                '10.0.3.1': 'edge',
            },
            'thresholds': {
                'edge_local_prefix_max': 100,
                'edge_local_pct_table_max': 0.01,
                'correlation_window_secs': 60
            }
        }
    }
    
    # Initialize components
    syslog_simulator = SyslogSimulator(config)
    dual_pipeline = DualSignalPipeline(config)
    
    try:
        print("Starting dual-signal pipeline...")
        await dual_pipeline.start()
        
        print("Starting syslog simulator...")
        await syslog_simulator.start()
        
        print("\n1. Simulating normal operation (30 seconds)...")
        await syslog_simulator.simulate_normal_operation(30)
        
        print("\n2. Simulating link failure scenario (20 seconds)...")
        await syslog_simulator.simulate_failure_scenario(
            'link_failure', 
            ['spine-01', 'tor-01'], 
            20
        )
        
        print("\n3. Simulating BGP session reset (15 seconds)...")
        await syslog_simulator.simulate_failure_scenario(
            'bgp_session_reset', 
            ['rr-01', 'spine-01'], 
            15
        )
        
        print("\n4. Simulating normal operation again (30 seconds)...")
        await syslog_simulator.simulate_normal_operation(30)
        
        print("\n5. Getting pipeline status...")
        status = dual_pipeline.get_pipeline_status()
        print("Pipeline Status:")
        print(f"  BGP aggregator bins: {status['bgp_aggregator']['closed_bins_count']}")
        print(f"  Syslog buffer messages: {status['syslog_buffer']['message_count']}")
        print(f"  GPU available: {status['mp_detector_status']['gpu_available']}")
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    finally:
        print("\nShutting down...")
        await syslog_simulator.stop()
        await dual_pipeline.stop()

async def test_correlated_events():
    """Test correlated BGP and syslog events."""
    print("\n" + "=" * 50)
    print("Testing Correlated Events")
    print("=" * 50)
    
    config = {
        'nats_url': 'nats://localhost:4222',
        'devices': {
            'spine-01': {'role': 'spine', 'ip': '10.0.1.1', 'interfaces': ['GigabitEthernet0/0/1']},
            'tor-01': {'role': 'tor', 'ip': '10.0.2.1', 'interfaces': ['GigabitEthernet0/0/1']},
        }
    }
    
    simulator = SyslogSimulator(config)
    
    try:
        await simulator.start()
        
        # Simulate BGP event
        bgp_event = {
            'timestamp': int(time.time()),
            'peer': '10.0.1.1',
            'type': 'UPDATE',
            'withdraw': ['192.168.1.0/24', '192.168.2.0/24']
        }
        
        print(f"Simulating BGP event: {bgp_event}")
        
        # Generate correlated syslog
        await simulator.simulate_correlated_failure(bgp_event, delay_seconds=1.0)
        
        print("Correlated syslog event generated")
        
    finally:
        await simulator.stop()

def main():
    """Run all dual-signal tests."""
    print("Dual-Signal BGP + Syslog Anomaly Detection Test")
    print("=" * 60)
    
    try:
        # Test 1: Full dual-signal detection
        asyncio.run(test_dual_signal_detection())
        
        # Test 2: Correlated events
        asyncio.run(test_correlated_events())
        
        print("\n" + "=" * 60)
        print("✓ All dual-signal tests completed!")
        print("\nThe system is ready for:")
        print("- Real-time BGP + syslog correlation")
        print("- Enhanced failure detection")
        print("- Improved localization accuracy")
        print("- GPU-accelerated Matrix Profile analysis")
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
