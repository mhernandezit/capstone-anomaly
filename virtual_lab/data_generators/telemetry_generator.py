"""
Telemetry Data Generator for Virtual Lab

This module generates realistic network telemetry data including BGP updates
and system metrics for testing the anomaly detection pipeline.
"""

import asyncio
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import yaml
import random
import numpy as np

from ..switch_emulator.network_switch import VirtualLabNetwork

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TelemetryGenerator:
    """
    Generates realistic network telemetry data for the virtual lab.
    
    This class coordinates data generation from multiple network switches
    and applies scaling factors based on the current lab phase.
    """
    
    def __init__(self, config_path: str):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Initialize virtual network
        self.network = VirtualLabNetwork(config_path)
        
        # Scaling configuration
        self.scaling_config = self.config.get('scaling', {})
        self.current_phase = 0
        self.phase_start_time = time.time()
        
        # Data generation rates
        self.bgp_multiplier = 1.0
        self.syslog_multiplier = 1.0
        
        # Statistics
        self.stats = {
            'bgp_updates_generated': 0,
            'syslog_messages_generated': 0,
            'anomalies_injected': 0,
            'start_time': time.time()
        }
        
        logger.info("Telemetry generator initialized")
    
    def _update_scaling_phase(self):
        """Update the current scaling phase based on elapsed time."""
        phases = self.scaling_config.get('phases', [])
        if not phases:
            return
        
        elapsed_minutes = (time.time() - self.phase_start_time) / 60
        
        for i, phase in enumerate(phases):
            phase_duration = phase.get('duration_minutes', 0)
            if elapsed_minutes <= phase_duration:
                if i != self.current_phase:
                    self.current_phase = i
                    self.bgp_multiplier = phase.get('bgp_multiplier', 1.0)
                    self.syslog_multiplier = phase.get('syslog_multiplier', 1.0)
                    logger.info(f"Switched to scaling phase: {phase.get('name', f'phase_{i}')} "
                              f"(BGP: {self.bgp_multiplier}x, Syslog: {self.syslog_multiplier}x)")
                break
        else:
            # Use the last phase if we've exceeded all durations
            if self.current_phase < len(phases) - 1:
                self.current_phase = len(phases) - 1
                last_phase = phases[-1]
                self.bgp_multiplier = last_phase.get('bgp_multiplier', 1.0)
                self.syslog_multiplier = last_phase.get('syslog_multiplier', 1.0)
    
    async def generate_bgp_telemetry(self) -> List[Dict[str, Any]]:
        """Generate BGP telemetry data from all switches."""
        self._update_scaling_phase()
        
        # Get base rate from config
        base_rate = self.config.get('data_generation', {}).get('bgp_telemetry', {}).get('update_frequency', 1.0)
        adjusted_rate = base_rate / self.bgp_multiplier
        
        # Generate events from network
        events = await self.network.generate_network_events()
        
        # Filter BGP events
        bgp_events = [event for event in events if event.get('type') == 'UPDATE' or 'peer' in event]
        
        # Apply scaling
        scaled_events = []
        for event in bgp_events:
            # Duplicate events based on multiplier
            for _ in range(int(self.bgp_multiplier)):
                scaled_event = event.copy()
                scaled_event['timestamp'] = int(time.time() * 1000)  # Use milliseconds
                scaled_events.append(scaled_event)
        
        self.stats['bgp_updates_generated'] += len(scaled_events)
        return scaled_events
    
    async def generate_syslog_telemetry(self) -> List[Dict[str, Any]]:
        """Generate syslog telemetry data from all switches."""
        self._update_scaling_phase()
        
        # Get base rate from config
        base_rate = self.config.get('data_generation', {}).get('syslog', {}).get('base_messages_per_second', 5)
        adjusted_rate = base_rate * self.syslog_multiplier
        
        # Generate events from network
        events = await self.network.generate_network_events()
        
        # Filter syslog events
        syslog_events = [event for event in events if event.get('type') == 'syslog' or 'severity' in event]
        
        # Apply scaling
        scaled_events = []
        for event in syslog_events:
            # Duplicate events based on multiplier
            for _ in range(int(self.syslog_multiplier)):
                scaled_event = event.copy()
                scaled_event['timestamp'] = int(time.time() * 1000)  # Use milliseconds
                scaled_events.append(scaled_event)
        
        self.stats['syslog_messages_generated'] += len(scaled_events)
        return scaled_events
    
    async def generate_system_metrics(self) -> List[Dict[str, Any]]:
        """Generate system metrics for each switch."""
        metrics = []
        current_time = int(time.time() * 1000)
        
        for switch_id, switch in self.network.switches.items():
            # Generate realistic system metrics
            cpu_usage = max(0, min(100, random.gauss(45, 15)))
            memory_usage = max(0, min(100, random.gauss(60, 20)))
            temperature = max(30, min(80, random.gauss(45, 10)))
            
            # Add some correlation between metrics
            if cpu_usage > 80:
                memory_usage = min(100, memory_usage + random.uniform(5, 15))
                temperature = min(80, temperature + random.uniform(2, 8))
            
            metrics.append({
                'timestamp': current_time,
                'device_id': switch_id,
                'metric_type': 'system',
                'metrics': {
                    'cpu_usage_percent': round(cpu_usage, 2),
                    'memory_usage_percent': round(memory_usage, 2),
                    'temperature_celsius': round(temperature, 1),
                    'fan_speed_rpm': random.randint(2000, 4000),
                    'power_consumption_watts': random.randint(150, 300)
                }
            })
        
        return metrics
    
    async def generate_interface_metrics(self) -> List[Dict[str, Any]]:
        """Generate interface-level metrics for each switch."""
        metrics = []
        current_time = int(time.time() * 1000)
        
        for switch_id, switch in self.network.switches.items():
            for if_name, interface in switch.interfaces.items():
                # Generate interface metrics
                if interface.status == "up":
                    bytes_in = random.randint(1000, 1000000)
                    bytes_out = random.randint(1000, 1000000)
                    packets_in = random.randint(100, 100000)
                    packets_out = random.randint(100, 100000)
                    errors_in = random.randint(0, 10)
                    errors_out = random.randint(0, 10)
                else:
                    bytes_in = bytes_out = packets_in = packets_out = 0
                    errors_in = errors_out = 0
                
                metrics.append({
                    'timestamp': current_time,
                    'device_id': switch_id,
                    'interface': if_name,
                    'metric_type': 'interface',
                    'metrics': {
                        'status': interface.status,
                        'bytes_in': bytes_in,
                        'bytes_out': bytes_out,
                        'packets_in': packets_in,
                        'packets_out': packets_out,
                        'errors_in': errors_in,
                        'errors_out': errors_out,
                        'utilization_percent': random.randint(0, 100)
                    }
                })
        
        return metrics
    
    async def generate_bgp_metrics(self) -> List[Dict[str, Any]]:
        """Generate BGP-specific metrics for each switch."""
        metrics = []
        current_time = int(time.time() * 1000)
        
        for switch_id, switch in self.network.switches.items():
            # Count BGP peers by state
            peers_established = sum(1 for peer in switch.bgp_peers.values() if peer.state == "established")
            peers_idle = sum(1 for peer in switch.bgp_peers.values() if peer.state == "idle")
            
            # Calculate prefix counts
            total_prefixes = len(switch.prefixes)
            
            # Generate BGP metrics
            metrics.append({
                'timestamp': current_time,
                'device_id': switch_id,
                'metric_type': 'bgp',
                'metrics': {
                    'peers_established': peers_established,
                    'peers_idle': peers_idle,
                    'peers_total': len(switch.bgp_peers),
                    'prefixes_learned': total_prefixes,
                    'prefixes_advertised': random.randint(50, 500),
                    'updates_received': random.randint(0, 100),
                    'updates_sent': random.randint(0, 100),
                    'withdrawals_received': random.randint(0, 20),
                    'withdrawals_sent': random.randint(0, 20)
                }
            })
        
        return metrics
    
    def get_generation_stats(self) -> Dict[str, Any]:
        """Get statistics about data generation."""
        elapsed_time = time.time() - self.stats['start_time']
        
        return {
            'elapsed_time_seconds': elapsed_time,
            'current_phase': self.current_phase,
            'bgp_multiplier': self.bgp_multiplier,
            'syslog_multiplier': self.syslog_multiplier,
            'bgp_updates_generated': self.stats['bgp_updates_generated'],
            'syslog_messages_generated': self.stats['syslog_messages_generated'],
            'anomalies_injected': self.stats['anomalies_injected'],
            'bgp_rate_per_second': self.stats['bgp_updates_generated'] / elapsed_time if elapsed_time > 0 else 0,
            'syslog_rate_per_second': self.stats['syslog_messages_generated'] / elapsed_time if elapsed_time > 0 else 0
        }
    
    def reset_stats(self):
        """Reset generation statistics."""
        self.stats = {
            'bgp_updates_generated': 0,
            'syslog_messages_generated': 0,
            'anomalies_injected': 0,
            'start_time': time.time()
        }
        self.phase_start_time = time.time()
        self.current_phase = 0


class TelemetryPublisher:
    """
    Publishes telemetry data to the message bus.
    """
    
    def __init__(self, message_bus_config: Dict[str, Any]):
        self.config = message_bus_config
        self.subjects = message_bus_config.get('subjects', {})
        
    async def publish_bgp_updates(self, updates: List[Dict[str, Any]]):
        """Publish BGP updates to the message bus."""
        # This would integrate with NATS or other message bus
        # For now, just log the updates
        logger.info(f"Publishing {len(updates)} BGP updates")
        for update in updates[:5]:  # Log first 5 for debugging
            logger.debug(f"BGP Update: {update}")
    
    async def publish_syslog_messages(self, messages: List[Dict[str, Any]]):
        """Publish syslog messages to the message bus."""
        logger.info(f"Publishing {len(messages)} syslog messages")
        for message in messages[:5]:  # Log first 5 for debugging
            logger.debug(f"Syslog: {message}")
    
    async def publish_telemetry_data(self, metrics: List[Dict[str, Any]]):
        """Publish telemetry metrics to the message bus."""
        logger.info(f"Publishing {len(metrics)} telemetry metrics")
        for metric in metrics[:3]:  # Log first 3 for debugging
            logger.debug(f"Telemetry: {metric}")


async def main():
    """Main function for testing the telemetry generator."""
    config_path = "virtual_lab/configs/lab_config.yml"
    
    # Initialize generator
    generator = TelemetryGenerator(config_path)
    publisher = TelemetryPublisher(generator.config.get('message_bus', {}))
    
    logger.info("Starting telemetry data generation...")
    
    try:
        while True:
            # Generate different types of telemetry data
            bgp_updates = await generator.generate_bgp_telemetry()
            syslog_messages = await generator.generate_syslog_telemetry()
            system_metrics = await generator.generate_system_metrics()
            interface_metrics = await generator.generate_interface_metrics()
            bgp_metrics = await generator.generate_bgp_metrics()
            
            # Publish to message bus
            await publisher.publish_bgp_updates(bgp_updates)
            await publisher.publish_syslog_messages(syslog_messages)
            await publisher.publish_telemetry_data(system_metrics + interface_metrics + bgp_metrics)
            
            # Print stats every 10 seconds
            if int(time.time()) % 10 == 0:
                stats = generator.get_generation_stats()
                logger.info(f"Generation stats: {stats}")
            
            # Wait before next generation cycle
            await asyncio.sleep(1.0)
            
    except KeyboardInterrupt:
        logger.info("Stopping telemetry generation...")
        final_stats = generator.get_generation_stats()
        logger.info(f"Final stats: {final_stats}")


if __name__ == "__main__":
    asyncio.run(main())
