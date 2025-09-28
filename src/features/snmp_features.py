#!/usr/bin/env python3
"""
SNMP Feature Extraction Module

This module extracts features from SNMP metrics to detect hardware failures,
environmental issues, and system degradation. It integrates with the existing
BGP and syslog feature extraction pipeline.

Features extracted:
- Hardware health indicators (CPU, memory, temperature)
- Interface performance metrics (errors, utilization, stability)
- Environmental anomaly patterns (thermal, power, fan status)
- Multi-modal correlation features (SNMP + BGP + syslog)
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict, deque
import json
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class SNMPFeatureBin:
    """Represents aggregated SNMP features for a time bin."""
    bin_start: float
    bin_end: float
    device_count: int
    
    # Interface health features
    interface_error_rate: float
    interface_utilization_mean: float
    interface_utilization_std: float
    interface_flap_count: int
    
    # System health features  
    cpu_utilization_mean: float
    cpu_utilization_max: float
    memory_utilization_mean: float
    memory_utilization_max: float
    
    # Environmental features
    temperature_mean: float
    temperature_max: float
    temperature_variance: float
    fan_speed_variance: float
    power_stability_score: float
    
    # Anomaly indicators
    threshold_violations: int
    severity_escalations: int
    multi_device_correlation: float
    environmental_stress_score: float
    
    # Correlation with other signals
    bgp_correlation: float = 0.0
    syslog_correlation: float = 0.0


class SNMPFeatureExtractor:
    """
    Extracts features from SNMP metrics for anomaly detection.
    
    This class processes streaming SNMP metrics and aggregates them into
    time-binned features that can be used by ML models for detecting
    hardware failures, environmental issues, and system degradation.
    """
    
    def __init__(self, bin_seconds: int = 60, history_bins: int = 100):
        """
        Initialize the SNMP feature extractor.
        
        Args:
            bin_seconds: Duration of each time bin in seconds
            history_bins: Number of historical bins to maintain
        """
        self.bin_seconds = bin_seconds
        self.history_bins = history_bins
        
        # Current bin data
        self.current_bin_start = None
        self.current_metrics: List[Dict[str, Any]] = []
        
        # Historical data
        self.completed_bins: deque = deque(maxlen=history_bins)
        self.device_baselines: Dict[str, Dict[str, float]] = defaultdict(dict)
        
        # Correlation data from other sources
        self.bgp_events: deque = deque(maxlen=1000)
        self.syslog_events: deque = deque(maxlen=1000)
        
        # Statistics
        self.stats = {
            'metrics_processed': 0,
            'bins_completed': 0,
            'anomalies_detected': 0,
            'devices_monitored': set()
        }
    
    def add_snmp_metric(self, metric: Dict[str, Any]):
        """
        Add an SNMP metric to the current bin.
        
        Args:
            metric: Dictionary containing SNMP metric data
        """
        current_time = metric.get('timestamp', datetime.now().timestamp())
        
        # Initialize first bin if needed
        if self.current_bin_start is None:
            self.current_bin_start = self._bin_start_time(current_time)
        
        # Check if metric belongs to current bin
        bin_start = self._bin_start_time(current_time)
        if bin_start > self.current_bin_start:
            # Complete current bin and start new one
            if self.current_metrics:
                completed_bin = self._complete_current_bin()
                self.completed_bins.append(completed_bin)
                self.stats['bins_completed'] += 1
            
            self.current_bin_start = bin_start
            self.current_metrics = []
        
        # Add metric to current bin
        self.current_metrics.append(metric)
        self.stats['metrics_processed'] += 1
        self.stats['devices_monitored'].add(metric.get('device_id', 'unknown'))
    
    def add_bgp_event(self, event: Dict[str, Any]):
        """Add BGP event for correlation analysis."""
        self.bgp_events.append({
            'timestamp': event.get('timestamp', datetime.now().timestamp()),
            'type': event.get('type', 'unknown'),
            'device_id': event.get('device_id'),
            'severity': event.get('severity', 'info')
        })
    
    def add_syslog_event(self, event: Dict[str, Any]):
        """Add syslog event for correlation analysis."""
        self.syslog_events.append({
            'timestamp': event.get('timestamp', datetime.now().timestamp()),
            'severity': event.get('severity', 'info'),
            'device_id': event.get('device_id'),
            'message': event.get('message', '')
        })
    
    def _bin_start_time(self, timestamp: float) -> float:
        """Calculate the start time of the bin containing the given timestamp."""
        return int(timestamp // self.bin_seconds) * self.bin_seconds
    
    def _complete_current_bin(self) -> SNMPFeatureBin:
        """Complete the current bin and extract features."""
        if not self.current_metrics:
            return None
        
        bin_end = self.current_bin_start + self.bin_seconds
        
        # Group metrics by device and type
        device_metrics = defaultdict(lambda: defaultdict(list))
        for metric in self.current_metrics:
            device_id = metric.get('device_id', 'unknown')
            metric_type = metric.get('metric_type', 'unknown')
            device_metrics[device_id][metric_type].append(metric)
        
        # Extract features
        features = self._extract_bin_features(device_metrics, self.current_bin_start, bin_end)
        
        # Update baselines
        self._update_device_baselines(device_metrics)
        
        return features
    
    def _extract_bin_features(self, device_metrics: Dict[str, Dict[str, List]], 
                            bin_start: float, bin_end: float) -> SNMPFeatureBin:
        """Extract features from metrics in a single bin."""
        
        # Initialize feature values
        interface_errors = []
        interface_utilizations = []
        interface_flaps = 0
        cpu_utilizations = []
        memory_utilizations = []
        temperatures = []
        fan_speeds = []
        power_values = []
        threshold_violations = 0
        severity_escalations = 0
        
        device_count = len(device_metrics)
        
        # Process each device's metrics
        for device_id, metric_types in device_metrics.items():
            
            # Interface metrics
            if 'interface' in metric_types:
                device_interface_errors, device_utilizations, device_flaps = \
                    self._extract_interface_features(metric_types['interface'], device_id)
                interface_errors.extend(device_interface_errors)
                interface_utilizations.extend(device_utilizations)
                interface_flaps += device_flaps
            
            # System metrics
            if 'system' in metric_types:
                device_cpu, device_memory = self._extract_system_features(
                    metric_types['system'], device_id
                )
                cpu_utilizations.extend(device_cpu)
                memory_utilizations.extend(device_memory)
            
            # Environmental metrics
            if 'environmental' in metric_types:
                device_temps, device_fans, device_power = \
                    self._extract_environmental_features(metric_types['environmental'], device_id)
                temperatures.extend(device_temps)
                fan_speeds.extend(device_fans)
                power_values.extend(device_power)
            
            # Count threshold violations and severity escalations
            device_violations, device_escalations = self._analyze_device_anomalies(
                metric_types, device_id
            )
            threshold_violations += device_violations
            severity_escalations += device_escalations
        
        # Calculate aggregate features
        interface_error_rate = np.mean(interface_errors) if interface_errors else 0.0
        interface_util_mean = np.mean(interface_utilizations) if interface_utilizations else 0.0
        interface_util_std = np.std(interface_utilizations) if len(interface_utilizations) > 1 else 0.0
        
        cpu_mean = np.mean(cpu_utilizations) if cpu_utilizations else 0.0
        cpu_max = np.max(cpu_utilizations) if cpu_utilizations else 0.0
        memory_mean = np.mean(memory_utilizations) if memory_utilizations else 0.0
        memory_max = np.max(memory_utilizations) if memory_utilizations else 0.0
        
        temp_mean = np.mean(temperatures) if temperatures else 0.0
        temp_max = np.max(temperatures) if temperatures else 0.0
        temp_variance = np.var(temperatures) if len(temperatures) > 1 else 0.0
        fan_variance = np.var(fan_speeds) if len(fan_speeds) > 1 else 0.0
        power_stability = self._calculate_power_stability(power_values)
        
        # Multi-device correlation
        multi_device_corr = self._calculate_multi_device_correlation(device_metrics)
        
        # Environmental stress score
        env_stress = self._calculate_environmental_stress(temperatures, fan_speeds, power_values)
        
        # Correlation with BGP and syslog
        bgp_corr = self._calculate_bgp_correlation(bin_start, bin_end)
        syslog_corr = self._calculate_syslog_correlation(bin_start, bin_end)
        
        return SNMPFeatureBin(
            bin_start=bin_start,
            bin_end=bin_end,
            device_count=device_count,
            interface_error_rate=interface_error_rate,
            interface_utilization_mean=interface_util_mean,
            interface_utilization_std=interface_util_std,
            interface_flap_count=interface_flaps,
            cpu_utilization_mean=cpu_mean,
            cpu_utilization_max=cpu_max,
            memory_utilization_mean=memory_mean,
            memory_utilization_max=memory_max,
            temperature_mean=temp_mean,
            temperature_max=temp_max,
            temperature_variance=temp_variance,
            fan_speed_variance=fan_variance,
            power_stability_score=power_stability,
            threshold_violations=threshold_violations,
            severity_escalations=severity_escalations,
            multi_device_correlation=multi_device_corr,
            environmental_stress_score=env_stress,
            bgp_correlation=bgp_corr,
            syslog_correlation=syslog_corr
        )
    
    def _extract_interface_features(self, interface_metrics: List[Dict], 
                                  device_id: str) -> Tuple[List[float], List[float], int]:
        """Extract interface-specific features."""
        errors = []
        utilizations = []
        flap_count = 0
        
        # Group by interface
        interface_data = defaultdict(list)
        for metric in interface_metrics:
            oid = metric.get('oid', '')
            interface_id = self._extract_interface_id(oid)
            interface_data[interface_id].append(metric)
        
        # Process each interface
        for interface_id, metrics in interface_data.items():
            # Calculate error rates
            error_metrics = [m for m in metrics if 'Error' in m.get('oid', '')]
            if error_metrics:
                error_rate = sum(m.get('value', 0) for m in error_metrics) / len(error_metrics)
                errors.append(error_rate)
            
            # Calculate utilization (simplified)
            traffic_metrics = [m for m in metrics if 'Octets' in m.get('oid', '')]
            if traffic_metrics:
                # Simplified utilization calculation
                total_octets = sum(m.get('value', 0) for m in traffic_metrics)
                # Normalize to percentage (assuming 1Gbps interface)
                utilization = min((total_octets * 8) / (1e9 * self.bin_seconds) * 100, 100)
                utilizations.append(utilization)
            
            # Detect interface flaps
            status_changes = [m for m in metrics if 'OperStatus' in m.get('oid', '')]
            if len(status_changes) > 2:  # Multiple status changes indicate flapping
                flap_count += 1
        
        return errors, utilizations, flap_count
    
    def _extract_system_features(self, system_metrics: List[Dict], 
                               device_id: str) -> Tuple[List[float], List[float]]:
        """Extract system-specific features."""
        cpu_values = []
        memory_values = []
        
        for metric in system_metrics:
            oid = metric.get('oid', '')
            value = metric.get('value', 0)
            
            if 'cpu' in oid.lower() or '109.1.1.1.1.7' in oid:
                cpu_values.append(float(value))
            elif 'memory' in oid.lower() or '48.1.1.1.5' in oid:
                memory_values.append(float(value))
        
        return cpu_values, memory_values
    
    def _extract_environmental_features(self, env_metrics: List[Dict], 
                                      device_id: str) -> Tuple[List[float], List[float], List[float]]:
        """Extract environmental-specific features."""
        temperatures = []
        fan_speeds = []
        power_values = []
        
        for metric in env_metrics:
            oid = metric.get('oid', '')
            value = metric.get('value', 0)
            
            if 'temperature' in oid.lower() or '13.1.3.1.3' in oid:
                temperatures.append(float(value))
            elif 'fan' in oid.lower() or '13.1.4.1' in oid:
                fan_speeds.append(float(value))
            elif 'power' in oid.lower() or '13.1.5.1' in oid:
                power_values.append(float(value))
        
        return temperatures, fan_speeds, power_values
    
    def _extract_interface_id(self, oid: str) -> str:
        """Extract interface ID from SNMP OID."""
        # Simple extraction - get the last number after the last dot
        parts = oid.split('.')
        return parts[-1] if parts else 'unknown'
    
    def _analyze_device_anomalies(self, metric_types: Dict[str, List], 
                                device_id: str) -> Tuple[int, int]:
        """Analyze device metrics for anomalies."""
        violations = 0
        escalations = 0
        
        # Count metrics with error/critical severity
        for metrics_list in metric_types.values():
            for metric in metrics_list:
                severity = metric.get('severity', 'info')
                if severity in ['error', 'critical']:
                    violations += 1
                if severity == 'critical':
                    escalations += 1
        
        return violations, escalations
    
    def _calculate_power_stability(self, power_values: List[float]) -> float:
        """Calculate power stability score (0-1, higher is more stable)."""
        if len(power_values) < 2:
            return 1.0
        
        # Calculate coefficient of variation
        mean_power = np.mean(power_values)
        if mean_power == 0:
            return 1.0
        
        cv = np.std(power_values) / mean_power
        # Convert to stability score (inverse of coefficient of variation)
        stability = 1.0 / (1.0 + cv)
        return stability
    
    def _calculate_multi_device_correlation(self, device_metrics: Dict[str, Dict]) -> float:
        """Calculate correlation of anomalies across multiple devices."""
        if len(device_metrics) < 2:
            return 0.0
        
        # Count devices with anomalies
        devices_with_anomalies = 0
        for device_id, metric_types in device_metrics.items():
            has_anomaly = False
            for metrics_list in metric_types.values():
                for metric in metrics_list:
                    if metric.get('severity') in ['error', 'critical']:
                        has_anomaly = True
                        break
                if has_anomaly:
                    break
            if has_anomaly:
                devices_with_anomalies += 1
        
        # Return correlation score
        return devices_with_anomalies / len(device_metrics)
    
    def _calculate_environmental_stress(self, temperatures: List[float], 
                                      fan_speeds: List[float], 
                                      power_values: List[float]) -> float:
        """Calculate environmental stress score."""
        stress_factors = []
        
        # Temperature stress
        if temperatures:
            max_temp = max(temperatures)
            if max_temp > 60:  # Above normal range
                temp_stress = min((max_temp - 60) / 20, 1.0)  # Normalize to 0-1
                stress_factors.append(temp_stress)
        
        # Fan stress (high fan speeds indicate stress)
        if fan_speeds:
            max_fan = max(fan_speeds)
            if max_fan > 4000:  # Above normal range
                fan_stress = min((max_fan - 4000) / 2000, 1.0)
                stress_factors.append(fan_stress)
        
        # Power instability
        if power_values and len(power_values) > 1:
            power_cv = np.std(power_values) / np.mean(power_values)
            if power_cv > 0.05:  # More than 5% variation
                power_stress = min(power_cv / 0.2, 1.0)
                stress_factors.append(power_stress)
        
        return np.mean(stress_factors) if stress_factors else 0.0
    
    def _calculate_bgp_correlation(self, bin_start: float, bin_end: float) -> float:
        """Calculate correlation with BGP events in the same time window."""
        bgp_events_in_window = [
            event for event in self.bgp_events
            if bin_start <= event['timestamp'] <= bin_end
        ]
        
        # Simple correlation: presence of BGP events during SNMP anomalies
        return min(len(bgp_events_in_window) / 10.0, 1.0)  # Normalize to 0-1
    
    def _calculate_syslog_correlation(self, bin_start: float, bin_end: float) -> float:
        """Calculate correlation with syslog events in the same time window."""
        syslog_events_in_window = [
            event for event in self.syslog_events
            if bin_start <= event['timestamp'] <= bin_end
            and event['severity'] in ['error', 'critical']
        ]
        
        return min(len(syslog_events_in_window) / 5.0, 1.0)  # Normalize to 0-1
    
    def _update_device_baselines(self, device_metrics: Dict[str, Dict]):
        """Update baseline metrics for each device."""
        for device_id, metric_types in device_metrics.items():
            if device_id not in self.device_baselines:
                self.device_baselines[device_id] = {}
            
            # Update baselines with exponential moving average
            alpha = 0.1  # Learning rate
            
            for metric_type, metrics in metric_types.items():
                for metric in metrics:
                    if metric.get('severity') == 'info':  # Only use normal metrics for baseline
                        oid = metric.get('oid', '')
                        value = float(metric.get('value', 0))
                        
                        if oid in self.device_baselines[device_id]:
                            # Update existing baseline
                            current_baseline = self.device_baselines[device_id][oid]
                            self.device_baselines[device_id][oid] = \
                                (1 - alpha) * current_baseline + alpha * value
                        else:
                            # Initialize baseline
                            self.device_baselines[device_id][oid] = value
    
    def get_current_bin_features(self) -> Optional[SNMPFeatureBin]:
        """Get features for the current (incomplete) bin."""
        if not self.current_metrics:
            return None
        
        # Create temporary bin
        current_time = datetime.now().timestamp()
        device_metrics = defaultdict(lambda: defaultdict(list))
        
        for metric in self.current_metrics:
            device_id = metric.get('device_id', 'unknown')
            metric_type = metric.get('metric_type', 'unknown')
            device_metrics[device_id][metric_type].append(metric)
        
        return self._extract_bin_features(
            device_metrics, 
            self.current_bin_start, 
            current_time
        )
    
    def get_completed_bins(self) -> List[SNMPFeatureBin]:
        """Get all completed feature bins."""
        return list(self.completed_bins)
    
    def get_latest_completed_bin(self) -> Optional[SNMPFeatureBin]:
        """Get the most recent completed feature bin."""
        return self.completed_bins[-1] if self.completed_bins else None
    
    def has_completed_bin(self) -> bool:
        """Check if there are any completed bins available."""
        return len(self.completed_bins) > 0
    
    def pop_completed_bin(self) -> Optional[SNMPFeatureBin]:
        """Pop and return the oldest completed bin."""
        return self.completed_bins.popleft() if self.completed_bins else None
    
    def get_device_baseline(self, device_id: str, oid: str) -> Optional[float]:
        """Get baseline value for a specific device and OID."""
        return self.device_baselines.get(device_id, {}).get(oid)
    
    def get_feature_vector(self, bin_data: SNMPFeatureBin) -> np.ndarray:
        """Convert feature bin to numpy array for ML processing."""
        return np.array([
            bin_data.interface_error_rate,
            bin_data.interface_utilization_mean,
            bin_data.interface_utilization_std,
            bin_data.interface_flap_count,
            bin_data.cpu_utilization_mean,
            bin_data.cpu_utilization_max,
            bin_data.memory_utilization_mean,
            bin_data.memory_utilization_max,
            bin_data.temperature_mean,
            bin_data.temperature_max,
            bin_data.temperature_variance,
            bin_data.fan_speed_variance,
            bin_data.power_stability_score,
            bin_data.threshold_violations,
            bin_data.severity_escalations,
            bin_data.multi_device_correlation,
            bin_data.environmental_stress_score,
            bin_data.bgp_correlation,
            bin_data.syslog_correlation
        ])
    
    def get_feature_names(self) -> List[str]:
        """Get names of all features in the feature vector."""
        return [
            'interface_error_rate',
            'interface_utilization_mean',
            'interface_utilization_std',
            'interface_flap_count',
            'cpu_utilization_mean',
            'cpu_utilization_max',
            'memory_utilization_mean',
            'memory_utilization_max',
            'temperature_mean',
            'temperature_max',
            'temperature_variance',
            'fan_speed_variance',
            'power_stability_score',
            'threshold_violations',
            'severity_escalations',
            'multi_device_correlation',
            'environmental_stress_score',
            'bgp_correlation',
            'syslog_correlation'
        ]
    
    def get_extraction_stats(self) -> Dict[str, Any]:
        """Get feature extraction statistics."""
        return {
            **self.stats,
            'devices_monitored': len(self.stats['devices_monitored']),
            'completed_bins': len(self.completed_bins),
            'current_bin_metrics': len(self.current_metrics),
            'baseline_devices': len(self.device_baselines)
        }


# Utility functions for integration with existing pipeline

def create_unified_feature_vector(bgp_features: np.ndarray, 
                                syslog_features: np.ndarray,
                                snmp_features: np.ndarray) -> np.ndarray:
    """Create a unified feature vector from all three data sources."""
    return np.concatenate([bgp_features, syslog_features, snmp_features])


async def main():
    """Example usage of SNMP feature extraction."""
    logging.basicConfig(level=logging.INFO)
    
    extractor = SNMPFeatureExtractor(bin_seconds=60)
    
    # Simulate some SNMP metrics
    sample_metrics = [
        {
            'timestamp': datetime.now().timestamp(),
            'device_id': 'spine-01',
            'oid': '1.3.6.1.2.1.2.2.1.14.1',
            'value': 100,
            'metric_type': 'interface',
            'severity': 'warning'
        },
        {
            'timestamp': datetime.now().timestamp(),
            'device_id': 'spine-01',
            'oid': '1.3.6.1.4.1.9.9.109.1.1.1.1.7.1',
            'value': 75,
            'metric_type': 'system',
            'severity': 'error'
        }
    ]
    
    for metric in sample_metrics:
        extractor.add_snmp_metric(metric)
    
    # Wait for bin completion
    await asyncio.sleep(2)
    
    current_features = extractor.get_current_bin_features()
    if current_features:
        print(f"Extracted features: {asdict(current_features)}")
        
        feature_vector = extractor.get_feature_vector(current_features)
        print(f"Feature vector shape: {feature_vector.shape}")
        print(f"Feature names: {extractor.get_feature_names()}")
    
    stats = extractor.get_extraction_stats()
    print(f"Extraction stats: {stats}")


if __name__ == "__main__":
    asyncio.run(main())
