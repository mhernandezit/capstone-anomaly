#!/usr/bin/env python3
"""
SNMP Simulator for Hardware Failure Events

This module uses snmpsim to generate realistic SNMP data including:
- Normal baseline metrics (interface stats, system health)
- Hardware failure scenarios (bad optics, cable issues, component failures)
- Environmental anomalies (temperature, power, vibration)
- Progressive degradation patterns

Integrates with the existing NATS message bus architecture.
"""

import asyncio
import logging
import json
import time
import random
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta

import nats
from pysnmp.hlapi import *
from pysnmp.entity.rfc3413.oneliner import cmdgen

logger = logging.getLogger(__name__)


@dataclass
class SNMPMetric:
    """Represents a single SNMP metric measurement."""
    timestamp: float
    device_id: str
    oid: str
    value: Any
    metric_type: str  # 'interface', 'environmental', 'system', 'optical'
    severity: str = 'info'  # 'info', 'warning', 'error', 'critical'


@dataclass
class HardwareFailureScenario:
    """Defines a hardware failure scenario."""
    name: str
    description: str
    affected_oids: List[str]
    failure_pattern: str  # 'instant', 'gradual', 'intermittent'
    duration_minutes: int
    severity_progression: List[str]
    

class SNMPFailureSimulator:
    """
    Simulates various hardware failures through SNMP data.
    
    This class generates realistic SNMP data patterns that represent:
    - Normal operational baselines
    - Hardware component failures
    - Environmental issues
    - Progressive degradation scenarios
    """
    
    def __init__(self, config_path: str = "configs/snmp_config.yml"):
        """Initialize the SNMP failure simulator."""
        self.config = self._load_config(config_path)
        self.running = False
        self.nats_client = None
        
        # Failure scenario definitions
        self.failure_scenarios = self._initialize_failure_scenarios()
        
        # Current active scenarios
        self.active_scenarios: Dict[str, Dict] = {}
        
        # Baseline metrics storage
        self.baseline_metrics: Dict[str, float] = {}
        
        # Statistics
        self.stats = {
            'metrics_generated': 0,
            'failures_injected': 0,
            'scenarios_active': 0,
            'start_time': time.time()
        }
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load SNMP simulation configuration."""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning(f"Config file {config_path} not found, using defaults")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for SNMP simulation."""
        return {
            'devices': [
                {'id': 'spine-01', 'type': 'spine', 'interfaces': 48},
                {'id': 'spine-02', 'type': 'spine', 'interfaces': 48},
                {'id': 'tor-01', 'type': 'tor', 'interfaces': 32},
                {'id': 'tor-02', 'type': 'tor', 'interfaces': 32},
                {'id': 'edge-01', 'type': 'edge', 'interfaces': 16},
                {'id': 'edge-02', 'type': 'edge', 'interfaces': 16},
            ],
            'polling_interval': 30,  # seconds
            'nats_subject': 'snmp.metrics',
            'failure_injection': {
                'enabled': True,
                'scenario_probability': 0.1,  # 10% chance per polling cycle
                'max_concurrent_scenarios': 3
            }
        }
    
    def _initialize_failure_scenarios(self) -> List[HardwareFailureScenario]:
        """Initialize predefined hardware failure scenarios."""
        return [
            # Optical Transceiver Failures
            HardwareFailureScenario(
                name="optical_degradation",
                description="Gradual optical power loss in SFP/QSFP",
                affected_oids=[
                    "1.3.6.1.2.1.2.2.1.10",  # ifInOctets
                    "1.3.6.1.2.1.2.2.1.16",  # ifOutOctets
                    "1.3.6.1.2.1.2.2.1.14",  # ifInErrors
                ],
                failure_pattern="gradual",
                duration_minutes=15,
                severity_progression=["info", "warning", "error", "critical"]
            ),
            
            # Cable/Physical Layer Issues
            HardwareFailureScenario(
                name="cable_intermittent",
                description="Intermittent cable connection causing packet loss",
                affected_oids=[
                    "1.3.6.1.2.1.2.2.1.14",  # ifInErrors
                    "1.3.6.1.2.1.2.2.1.20",  # ifOutErrors
                    "1.3.6.1.2.1.2.2.1.8",   # ifOperStatus
                ],
                failure_pattern="intermittent",
                duration_minutes=8,
                severity_progression=["warning", "error", "warning", "error"]
            ),
            
            # Memory Issues
            HardwareFailureScenario(
                name="memory_pressure",
                description="Increasing memory utilization leading to performance degradation",
                affected_oids=[
                    "1.3.6.1.4.1.9.9.48.1.1.1.5",  # Cisco memory utilization
                    "1.3.6.1.4.1.9.9.109.1.1.1.1.7",  # CPU utilization
                ],
                failure_pattern="gradual",
                duration_minutes=20,
                severity_progression=["info", "warning", "error"]
            ),
            
            # Temperature Issues
            HardwareFailureScenario(
                name="thermal_runaway",
                description="Overheating due to fan failure or blocked airflow",
                affected_oids=[
                    "1.3.6.1.4.1.9.9.13.1.3.1.3",  # Temperature sensors
                    "1.3.6.1.4.1.9.9.13.1.4.1.3",  # Fan status
                ],
                failure_pattern="gradual",
                duration_minutes=12,
                severity_progression=["warning", "error", "critical"]
            ),
            
            # Power Supply Issues
            HardwareFailureScenario(
                name="power_supply_degradation",
                description="Power supply voltage instability",
                affected_oids=[
                    "1.3.6.1.4.1.9.9.13.1.5.1.3",  # Power supply status
                    "1.3.6.1.4.1.9.9.13.1.5.1.4",  # Power consumption
                ],
                failure_pattern="intermittent",
                duration_minutes=10,
                severity_progression=["warning", "error", "warning"]
            )
        ]
    
    async def connect_nats(self):
        """Connect to NATS message bus."""
        try:
            self.nats_client = await nats.connect("nats://127.0.0.1:4222")
            logger.info("Connected to NATS message bus")
        except Exception as e:
            logger.error(f"Failed to connect to NATS: {e}")
            raise
    
    async def disconnect_nats(self):
        """Disconnect from NATS message bus."""
        if self.nats_client:
            await self.nats_client.close()
            logger.info("Disconnected from NATS message bus")
    
    def generate_baseline_metrics(self, device: Dict[str, Any]) -> List[SNMPMetric]:
        """Generate normal baseline SNMP metrics for a device."""
        metrics = []
        current_time = time.time()
        
        # Interface metrics
        for interface_id in range(1, device['interfaces'] + 1):
            # Normal traffic patterns
            base_traffic = random.randint(1000000, 10000000)  # 1-10 MB/s baseline
            
            metrics.extend([
                SNMPMetric(
                    timestamp=current_time,
                    device_id=device['id'],
                    oid=f"1.3.6.1.2.1.2.2.1.10.{interface_id}",  # ifInOctets
                    value=base_traffic + random.randint(-100000, 100000),
                    metric_type="interface",
                    severity="info"
                ),
                SNMPMetric(
                    timestamp=current_time,
                    device_id=device['id'],
                    oid=f"1.3.6.1.2.1.2.2.1.16.{interface_id}",  # ifOutOctets
                    value=base_traffic + random.randint(-100000, 100000),
                    metric_type="interface",
                    severity="info"
                ),
                SNMPMetric(
                    timestamp=current_time,
                    device_id=device['id'],
                    oid=f"1.3.6.1.2.1.2.2.1.8.{interface_id}",   # ifOperStatus
                    value=1,  # up
                    metric_type="interface",
                    severity="info"
                )
            ])
        
        # System metrics
        metrics.extend([
            SNMPMetric(
                timestamp=current_time,
                device_id=device['id'],
                oid="1.3.6.1.4.1.9.9.109.1.1.1.1.7.1",  # CPU utilization
                value=random.randint(10, 30),  # 10-30% normal CPU
                metric_type="system",
                severity="info"
            ),
            SNMPMetric(
                timestamp=current_time,
                device_id=device['id'],
                oid="1.3.6.1.4.1.9.9.48.1.1.1.5.1",  # Memory utilization
                value=random.randint(20, 40),  # 20-40% normal memory
                metric_type="system",
                severity="info"
            )
        ])
        
        # Environmental metrics
        metrics.extend([
            SNMPMetric(
                timestamp=current_time,
                device_id=device['id'],
                oid="1.3.6.1.4.1.9.9.13.1.3.1.3.1",  # Temperature
                value=random.randint(35, 45),  # 35-45°C normal
                metric_type="environmental",
                severity="info"
            )
        ])
        
        return metrics
    
    def inject_failure_scenario(self, scenario: HardwareFailureScenario, 
                              device: Dict[str, Any]) -> List[SNMPMetric]:
        """Inject a specific failure scenario into SNMP metrics."""
        metrics = []
        current_time = time.time()
        scenario_key = f"{device['id']}_{scenario.name}"
        
        # Initialize scenario if not active
        if scenario_key not in self.active_scenarios:
            self.active_scenarios[scenario_key] = {
                'scenario': scenario,
                'device': device,
                'start_time': current_time,
                'phase': 0,
                'last_update': current_time
            }
            self.stats['failures_injected'] += 1
            logger.info(f"Injecting failure scenario '{scenario.name}' on device '{device['id']}'")
        
        scenario_state = self.active_scenarios[scenario_key]
        elapsed_minutes = (current_time - scenario_state['start_time']) / 60
        
        # Check if scenario should end
        if elapsed_minutes >= scenario.duration_minutes:
            del self.active_scenarios[scenario_key]
            logger.info(f"Completed failure scenario '{scenario.name}' on device '{device['id']}'")
            return self.generate_baseline_metrics(device)
        
        # Generate failure-specific metrics
        severity_index = min(
            int(elapsed_minutes / (scenario.duration_minutes / len(scenario.severity_progression))),
            len(scenario.severity_progression) - 1
        )
        current_severity = scenario.severity_progression[severity_index]
        
        # Apply failure patterns based on scenario type
        if scenario.name == "optical_degradation":
            metrics.extend(self._generate_optical_failure_metrics(
                device, scenario, current_severity, elapsed_minutes
            ))
        elif scenario.name == "cable_intermittent":
            metrics.extend(self._generate_cable_failure_metrics(
                device, scenario, current_severity, elapsed_minutes
            ))
        elif scenario.name == "memory_pressure":
            metrics.extend(self._generate_memory_failure_metrics(
                device, scenario, current_severity, elapsed_minutes
            ))
        elif scenario.name == "thermal_runaway":
            metrics.extend(self._generate_thermal_failure_metrics(
                device, scenario, current_severity, elapsed_minutes
            ))
        elif scenario.name == "power_supply_degradation":
            metrics.extend(self._generate_power_failure_metrics(
                device, scenario, current_severity, elapsed_minutes
            ))
        
        return metrics
    
    def _generate_optical_failure_metrics(self, device: Dict[str, Any], 
                                        scenario: HardwareFailureScenario,
                                        severity: str, elapsed_minutes: float) -> List[SNMPMetric]:
        """Generate metrics for optical transceiver degradation."""
        metrics = []
        current_time = time.time()
        
        # Simulate gradual signal degradation
        degradation_factor = min(elapsed_minutes / scenario.duration_minutes, 1.0)
        
        # Interface 1 experiencing optical issues
        interface_id = 1
        
        # Decreasing throughput due to retransmissions
        normal_traffic = 5000000
        degraded_traffic = int(normal_traffic * (1 - degradation_factor * 0.8))
        
        # Increasing error rates
        error_rate = int(degradation_factor * 1000)
        
        metrics.extend([
            SNMPMetric(
                timestamp=current_time,
                device_id=device['id'],
                oid=f"1.3.6.1.2.1.2.2.1.10.{interface_id}",
                value=degraded_traffic,
                metric_type="interface",
                severity=severity
            ),
            SNMPMetric(
                timestamp=current_time,
                device_id=device['id'],
                oid=f"1.3.6.1.2.1.2.2.1.14.{interface_id}",  # ifInErrors
                value=error_rate,
                metric_type="interface",
                severity=severity
            )
        ])
        
        return metrics
    
    def _generate_cable_failure_metrics(self, device: Dict[str, Any], 
                                      scenario: HardwareFailureScenario,
                                      severity: str, elapsed_minutes: float) -> List[SNMPMetric]:
        """Generate metrics for intermittent cable issues."""
        metrics = []
        current_time = time.time()
        
        # Intermittent pattern - errors spike periodically
        cycle_position = (elapsed_minutes * 4) % 2  # 4 cycles per minute
        is_error_phase = cycle_position < 1
        
        interface_id = 2
        error_count = 500 if is_error_phase else 10
        
        # Intermittent link status changes
        link_status = 2 if is_error_phase and severity in ['error', 'critical'] else 1
        
        metrics.extend([
            SNMPMetric(
                timestamp=current_time,
                device_id=device['id'],
                oid=f"1.3.6.1.2.1.2.2.1.14.{interface_id}",
                value=error_count,
                metric_type="interface",
                severity=severity
            ),
            SNMPMetric(
                timestamp=current_time,
                device_id=device['id'],
                oid=f"1.3.6.1.2.1.2.2.1.8.{interface_id}",
                value=link_status,
                metric_type="interface",
                severity=severity
            )
        ])
        
        return metrics
    
    def _generate_memory_failure_metrics(self, device: Dict[str, Any], 
                                       scenario: HardwareFailureScenario,
                                       severity: str, elapsed_minutes: float) -> List[SNMPMetric]:
        """Generate metrics for memory pressure scenarios."""
        current_time = time.time()
        
        # Gradual memory increase
        progress = elapsed_minutes / scenario.duration_minutes
        base_memory = 30
        memory_utilization = int(base_memory + (progress * 60))  # Up to 90%
        
        # CPU also increases due to memory pressure
        cpu_utilization = int(20 + (progress * 50))  # Up to 70%
        
        return [
            SNMPMetric(
                timestamp=current_time,
                device_id=device['id'],
                oid="1.3.6.1.4.1.9.9.48.1.1.1.5.1",
                value=memory_utilization,
                metric_type="system",
                severity=severity
            ),
            SNMPMetric(
                timestamp=current_time,
                device_id=device['id'],
                oid="1.3.6.1.4.1.9.9.109.1.1.1.1.7.1",
                value=cpu_utilization,
                metric_type="system",
                severity=severity
            )
        ]
    
    def _generate_thermal_failure_metrics(self, device: Dict[str, Any], 
                                        scenario: HardwareFailureScenario,
                                        severity: str, elapsed_minutes: float) -> List[SNMPMetric]:
        """Generate metrics for thermal runaway scenarios."""
        current_time = time.time()
        
        # Temperature rises gradually
        progress = elapsed_minutes / scenario.duration_minutes
        base_temp = 40
        current_temp = int(base_temp + (progress * 35))  # Up to 75°C
        
        # Fan speed increases to compensate
        fan_speed = int(3000 + (progress * 2000))  # Up to 5000 RPM
        
        return [
            SNMPMetric(
                timestamp=current_time,
                device_id=device['id'],
                oid="1.3.6.1.4.1.9.9.13.1.3.1.3.1",
                value=current_temp,
                metric_type="environmental",
                severity=severity
            ),
            SNMPMetric(
                timestamp=current_time,
                device_id=device['id'],
                oid="1.3.6.1.4.1.9.9.13.1.4.1.3.1",
                value=fan_speed,
                metric_type="environmental",
                severity=severity
            )
        ]
    
    def _generate_power_failure_metrics(self, device: Dict[str, Any], 
                                      scenario: HardwareFailureScenario,
                                      severity: str, elapsed_minutes: float) -> List[SNMPMetric]:
        """Generate metrics for power supply issues."""
        current_time = time.time()
        
        # Intermittent power fluctuations
        cycle_position = (elapsed_minutes * 6) % 3  # 6 cycles per minute
        is_fluctuation = cycle_position < 1
        
        # Power supply status: 1=normal, 2=warning, 3=critical
        power_status = 3 if is_fluctuation and severity == 'critical' else 2
        
        # Power consumption varies
        base_power = 150  # watts
        power_variation = 20 if is_fluctuation else 5
        current_power = base_power + random.randint(-power_variation, power_variation)
        
        return [
            SNMPMetric(
                timestamp=current_time,
                device_id=device['id'],
                oid="1.3.6.1.4.1.9.9.13.1.5.1.3.1",
                value=power_status,
                metric_type="environmental",
                severity=severity
            ),
            SNMPMetric(
                timestamp=current_time,
                device_id=device['id'],
                oid="1.3.6.1.4.1.9.9.13.1.5.1.4.1",
                value=current_power,
                metric_type="environmental",
                severity=severity
            )
        ]
    
    async def generate_metrics_cycle(self) -> List[SNMPMetric]:
        """Generate one cycle of SNMP metrics for all devices."""
        all_metrics = []
        
        for device in self.config['devices']:
            # Check if we should inject a failure
            should_inject_failure = (
                self.config['failure_injection']['enabled'] and
                random.random() < self.config['failure_injection']['scenario_probability'] and
                len(self.active_scenarios) < self.config['failure_injection']['max_concurrent_scenarios']
            )
            
            # Generate metrics (baseline or with failures)
            device_has_active_scenario = any(
                device['id'] in key for key in self.active_scenarios.keys()
            )
            
            if device_has_active_scenario:
                # Continue existing failure scenarios
                device_metrics = []
                for scenario_key in list(self.active_scenarios.keys()):
                    if device['id'] in scenario_key:
                        scenario_state = self.active_scenarios[scenario_key]
                        device_metrics.extend(
                            self.inject_failure_scenario(
                                scenario_state['scenario'], device
                            )
                        )
                if not device_metrics:
                    device_metrics = self.generate_baseline_metrics(device)
            elif should_inject_failure:
                # Start a new failure scenario
                scenario = random.choice(self.failure_scenarios)
                device_metrics = self.inject_failure_scenario(scenario, device)
            else:
                # Generate normal baseline metrics
                device_metrics = self.generate_baseline_metrics(device)
            
            all_metrics.extend(device_metrics)
        
        self.stats['metrics_generated'] += len(all_metrics)
        self.stats['scenarios_active'] = len(self.active_scenarios)
        
        return all_metrics
    
    async def publish_metrics(self, metrics: List[SNMPMetric]):
        """Publish SNMP metrics to NATS message bus."""
        if not self.nats_client:
            logger.warning("NATS client not connected, cannot publish metrics")
            return
        
        for metric in metrics:
            message = json.dumps(asdict(metric))
            await self.nats_client.publish(
                self.config['nats_subject'], 
                message.encode()
            )
    
    async def run_simulation(self):
        """Run the main simulation loop."""
        logger.info("Starting SNMP failure simulation")
        self.running = True
        
        await self.connect_nats()
        
        try:
            while self.running:
                # Generate metrics for this cycle
                metrics = await self.generate_metrics_cycle()
                
                # Publish to NATS
                await self.publish_metrics(metrics)
                
                # Log statistics periodically
                if self.stats['metrics_generated'] % 1000 == 0:
                    logger.info(
                        f"SNMP Simulator Stats: "
                        f"metrics={self.stats['metrics_generated']}, "
                        f"failures={self.stats['failures_injected']}, "
                        f"active_scenarios={self.stats['scenarios_active']}"
                    )
                
                # Wait for next polling cycle
                await asyncio.sleep(self.config['polling_interval'])
                
        except KeyboardInterrupt:
            logger.info("Received interrupt signal, stopping simulation")
        except Exception as e:
            logger.error(f"Error in simulation loop: {e}")
        finally:
            await self.disconnect_nats()
            self.running = False
    
    def stop_simulation(self):
        """Stop the simulation."""
        self.running = False
    
    def get_simulation_stats(self) -> Dict[str, Any]:
        """Get current simulation statistics."""
        runtime = time.time() - self.stats['start_time']
        return {
            **self.stats,
            'runtime_minutes': runtime / 60,
            'metrics_per_minute': self.stats['metrics_generated'] / max(runtime / 60, 1),
            'active_scenarios': len(self.active_scenarios),
            'scenario_details': {
                key: {
                    'scenario_name': state['scenario'].name,
                    'device_id': state['device']['id'],
                    'elapsed_minutes': (time.time() - state['start_time']) / 60
                }
                for key, state in self.active_scenarios.items()
            }
        }


async def main():
    """Main entry point for SNMP simulation."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    simulator = SNMPFailureSimulator()
    
    try:
        await simulator.run_simulation()
    except KeyboardInterrupt:
        logger.info("Shutting down SNMP simulator")
    finally:
        simulator.stop_simulation()


if __name__ == "__main__":
    asyncio.run(main())
