#!/usr/bin/env python3
"""
Multimodal Network Event Simulator

Generates realistic network events for both BGP and SNMP monitoring, simulating
various failure scenarios that trigger both pipelines.

This simulator creates correlated events that should be detected by:
- Matrix Profile (BGP): Route withdrawals, AS path churn, routing instability
- Isolation Forest (SNMP): Interface errors, CPU/memory spikes, temperature issues

Failure Scenarios:
1. Link Failure: High interface errors (SNMP) + route withdrawals (BGP)
2. Router Overload: High CPU/memory (SNMP) + routing instability (BGP)
3. Optical Degradation: Interface errors (SNMP) + packet loss affecting BGP
4. Hardware Failure: Temperature/power issues (SNMP) + BGP session flaps
5. Route Leak: Normal SNMP + massive BGP route announcements
6. BGP Flapping: Peer flapping + interface instability
"""

import random
import time
from dataclasses import dataclass
from typing import Any, Dict, List

import numpy as np
import yaml


@dataclass
class NetworkEvent:
    """Represents a network event affecting one or more modalities."""

    timestamp: float
    event_type: str
    device: str
    duration: float  # seconds
    severity: str

    # Expected detections
    should_trigger_bgp: bool
    should_trigger_snmp: bool

    # Event parameters
    parameters: Dict[str, Any]


class MultiModalSimulator:
    """
    Simulates realistic network events across BGP and SNMP modalities.
    
    Generates synthetic feature vectors for both BGP and SNMP data sources.
    """

    def __init__(
        self,
        topology_path: str = "evaluation/topology.yml",
        bin_seconds: int = 30,
        random_seed: int = None,
    ):
        """
        Initialize the multimodal simulator.

        Args:
            topology_path: Path to topology YAML
            bin_seconds: Time bin size for aggregation
            random_seed: Random seed for reproducibility
        """
        if random_seed is not None:
            random.seed(random_seed)
            np.random.seed(random_seed)

        self.bin_seconds = bin_seconds

        # Load topology
        with open(topology_path) as f:
            self.topology = yaml.safe_load(f)

        self.devices = list(self.topology.get("devices", {}).keys())
        self.bgp_peers = self.topology.get("bgp_peers", [])

        # Baseline values for normal operation
        self.snmp_baseline = self._create_snmp_baseline()
        self.bgp_baseline = self._create_bgp_baseline()

        # Current event (if any)
        self.active_event: NetworkEvent = None
        self.event_start_time = None

    def _create_snmp_baseline(self) -> Dict[str, float]:
        """Create baseline SNMP values for normal operation."""
        return {
            "interface_error_rate": 0.02,
            "interface_utilization_mean": 0.35,
            "interface_utilization_std": 0.05,
            "interface_flap_count": 0,
            "cpu_utilization_mean": 0.30,
            "cpu_utilization_max": 0.45,
            "memory_utilization_mean": 0.40,
            "memory_utilization_max": 0.55,
            "temperature_mean": 42.0,
            "temperature_max": 48.0,
            "temperature_variance": 2.0,
            "fan_speed_variance": 120.0,
            "power_stability_score": 0.90,
            "threshold_violations": 0,
            "severity_escalations": 0,
            "multi_device_correlation": 0.05,
            "environmental_stress_score": 0.08,
            "bgp_correlation": 0.04,
            "syslog_correlation": 0.05,
        }

    def _create_bgp_baseline(self) -> Dict[str, float]:
        """Create baseline BGP values for normal operation."""
        return {
            "wdr_total": 5.0,
            "ann_total": 8.0,
            "as_path_churn": 2.0,
        }


    def generate_normal_snmp_data(self, device: str) -> Dict[str, float]:
        """
        Generate normal SNMP metrics with natural variance.

        Args:
            device: Device identifier

        Returns:
            SNMP feature vector
        """
        baseline = self.snmp_baseline.copy()

        # Add natural variance
        data = {}
        for key, value in baseline.items():
            if key in ["interface_flap_count", "threshold_violations", "severity_escalations"]:
                # Discrete counts with Poisson distribution
                data[key] = max(0, np.random.poisson(value))
            elif key in [
                "interface_error_rate",
                "multi_device_correlation",
                "environmental_stress_score",
                "bgp_correlation",
                "syslog_correlation",
            ]:
                # Rates with exponential distribution
                data[key] = np.clip(np.random.exponential(value), 0.0, 0.1)
            elif "utilization" in key:
                # Utilization with time-of-day variance
                time_factor = 1.0 + 0.2 * np.sin(2 * np.pi * time.time() / 86400)
                data[key] = np.clip(np.random.beta(2, 3) * value * time_factor, 0.05, 0.95)
            elif "temperature" in key:
                # Temperature with normal distribution
                data[key] = np.clip(np.random.normal(value, 3), 25, 70)
            elif "fan_speed" in key:
                # Fan speed variance
                data[key] = np.clip(np.random.gamma(3, value / 3), 50, 500)
            elif key == "power_stability_score":
                # Power stability (high is good)
                data[key] = np.clip(np.random.beta(8, 2), 0.80, 1.0)
            else:
                data[key] = value

        return data

    def generate_normal_bgp_data(self, peer: str) -> Dict[str, float]:
        """
        Generate normal BGP metrics with natural variance.

        Args:
            peer: BGP peer identifier

        Returns:
            BGP feature values
        """
        baseline = self.bgp_baseline.copy()

        data = {}
        for key, value in baseline.items():
            # BGP updates follow Poisson-like distribution
            data[key] = max(0, np.random.poisson(value))

        return data

    def inject_failure(
        self, event_type: str, device: str = None, duration: float = 60.0, severity: str = "high"
    ) -> NetworkEvent:
        """
        Inject a failure event into the simulation (synchronous version).

        Args:
            event_type: Type of failure (link_failure, router_overload, etc.)
            device: Target device (random if None)
            duration: Event duration in seconds
            severity: Event severity (low, medium, high, critical)

        Returns:
            NetworkEvent object describing the injected failure

        Note:
            This is the legacy synchronous API for backward compatibility.
            For real BGP simulator support, use inject_failure_async().
        """
        if device is None:
            # Prefer important devices (spine, edge)
            important_devices = [
                d
                for d, info in self.topology["devices"].items()
                if info.get("role") in ["spine", "edge"]
            ]
            device = random.choice(important_devices if important_devices else self.devices)

        # Create event based on type
        if event_type == "link_failure":
            event = self._create_link_failure_event(device, duration, severity)
        elif event_type == "router_overload":
            event = self._create_router_overload_event(device, duration, severity)
        elif event_type == "optical_degradation":
            event = self._create_optical_degradation_event(device, duration, severity)
        elif event_type == "hardware_failure":
            event = self._create_hardware_failure_event(device, duration, severity)
        elif event_type == "route_leak":
            event = self._create_route_leak_event(device, duration, severity)
        elif event_type == "bgp_flapping":
            event = self._create_bgp_flapping_event(device, duration, severity)
        else:
            raise ValueError(f"Unknown event type: {event_type}")

        self.active_event = event
        self.event_start_time = time.time()

        return event


    def _create_link_failure_event(
        self, device: str, duration: float, severity: str
    ) -> NetworkEvent:
        """Create link failure event (affects both SNMP and BGP)."""
        return NetworkEvent(
            timestamp=time.time(),
            event_type="link_failure",
            device=device,
            duration=duration,
            severity=severity,
            should_trigger_bgp=True,
            should_trigger_snmp=True,
            parameters={
                "interface_error_multiplier": 20.0,  # 20x normal
                "bgp_withdrawal_rate": 50.0,  # Heavy withdrawals
                "interface_flaps": 10,
            },
        )

    def _create_router_overload_event(
        self, device: str, duration: float, severity: str
    ) -> NetworkEvent:
        """Create router overload event (CPU/memory + BGP instability)."""
        return NetworkEvent(
            timestamp=time.time(),
            event_type="router_overload",
            device=device,
            duration=duration,
            severity=severity,
            should_trigger_bgp=True,
            should_trigger_snmp=True,
            parameters={
                "cpu_multiplier": 2.5,  # 2.5x normal CPU
                "memory_multiplier": 2.0,  # 2x normal memory
                "bgp_churn_rate": 30.0,  # High AS path churn
            },
        )

    def _create_optical_degradation_event(
        self, device: str, duration: float, severity: str
    ) -> NetworkEvent:
        """Create optical degradation event (interface errors + packet loss)."""
        return NetworkEvent(
            timestamp=time.time(),
            event_type="optical_degradation",
            device=device,
            duration=duration,
            severity=severity,
            should_trigger_bgp=False,  # May not immediately affect BGP
            should_trigger_snmp=True,
            parameters={
                "interface_error_multiplier": 15.0,  # High error rate
                "optical_power_degradation": 0.6,  # 60% of normal
            },
        )

    def _create_hardware_failure_event(
        self, device: str, duration: float, severity: str
    ) -> NetworkEvent:
        """Create hardware failure event (thermal/power + BGP session loss)."""
        return NetworkEvent(
            timestamp=time.time(),
            event_type="hardware_failure",
            device=device,
            duration=duration,
            severity=severity,
            should_trigger_bgp=True,
            should_trigger_snmp=True,
            parameters={
                "temperature_increase": 35.0,  # +35C
                "power_stability": 0.45,  # Very unstable
                "bgp_session_loss": True,
            },
        )

    def _create_route_leak_event(self, device: str, duration: float, severity: str) -> NetworkEvent:
        """Create route leak event (massive BGP announcements, normal SNMP)."""
        return NetworkEvent(
            timestamp=time.time(),
            event_type="route_leak",
            device=device,
            duration=duration,
            severity=severity,
            should_trigger_bgp=True,
            should_trigger_snmp=False,  # SNMP may be normal
            parameters={
                "announcement_multiplier": 50.0,  # 50x normal announcements
            },
        )

    def _create_bgp_flapping_event(
        self, device: str, duration: float, severity: str
    ) -> NetworkEvent:
        """Create BGP flapping event (rapid session up/down)."""
        return NetworkEvent(
            timestamp=time.time(),
            event_type="bgp_flapping",
            device=device,
            duration=duration,
            severity=severity,
            should_trigger_bgp=True,
            should_trigger_snmp=True,  # May show interface flaps
            parameters={
                "session_flap_rate": 5,  # Flaps per minute
                "interface_flaps": 8,
            },
        )

    def generate_snmp_data_with_event(self, device: str) -> Dict[str, float]:
        """
        Generate SNMP data considering active event.

        Args:
            device: Device identifier

        Returns:
            SNMP feature vector (potentially anomalous if event is active)
        """
        # Start with normal data
        data = self.generate_normal_snmp_data(device)

        # Apply event effects if active and affects this device
        if self.active_event and self._is_event_active():
            if device == self.active_event.device or self._is_device_affected(device):
                data = self._apply_event_to_snmp(data, self.active_event)

        return data

    def generate_bgp_data_with_event(self, peer: str) -> Dict[str, float]:
        """
        Generate BGP data considering active event.

        Args:
            peer: BGP peer identifier

        Returns:
            BGP feature values (potentially anomalous if event is active)
        """
        # Start with normal data
        data = self.generate_normal_bgp_data(peer)

        # Apply event effects if active and affects this peer
        if self.active_event and self._is_event_active():
            if peer == self.active_event.device or self._is_peer_affected(peer):
                data = self._apply_event_to_bgp(data, self.active_event)

        return data

    def _is_event_active(self) -> bool:
        """Check if the current event is still active."""
        if not self.active_event or not self.event_start_time:
            return False

        elapsed = time.time() - self.event_start_time
        return elapsed < self.active_event.duration

    def _is_device_affected(self, device: str) -> bool:
        """Check if a device is affected by the current event."""
        if not self.active_event:
            return False

        # Event device is always affected
        if device == self.active_event.device:
            return True

        # Check if device is BGP neighbor
        for peer_pair in self.bgp_peers:
            if self.active_event.device in peer_pair and device in peer_pair:
                return True

        return False

    def _is_peer_affected(self, peer: str) -> bool:
        """Check if a BGP peer is affected by the current event."""
        return self._is_device_affected(peer)

    def _apply_event_to_snmp(self, data: Dict[str, float], event: NetworkEvent) -> Dict[str, float]:
        """Apply event effects to SNMP data."""
        params = event.parameters

        # Link failure effects
        if "interface_error_multiplier" in params:
            data["interface_error_rate"] *= params["interface_error_multiplier"]
            data["interface_error_rate"] = min(data["interface_error_rate"], 0.95)

        if "interface_flaps" in params:
            data["interface_flap_count"] += params["interface_flaps"]

        # Router overload effects
        if "cpu_multiplier" in params:
            data["cpu_utilization_mean"] = min(
                data["cpu_utilization_mean"] * params["cpu_multiplier"], 0.98
            )
            data["cpu_utilization_max"] = min(
                data["cpu_utilization_max"] * params["cpu_multiplier"], 0.99
            )

        if "memory_multiplier" in params:
            data["memory_utilization_mean"] = min(
                data["memory_utilization_mean"] * params["memory_multiplier"], 0.95
            )
            data["memory_utilization_max"] = min(
                data["memory_utilization_max"] * params["memory_multiplier"], 0.98
            )

        # Hardware failure effects
        if "temperature_increase" in params:
            data["temperature_mean"] += params["temperature_increase"]
            data["temperature_max"] += params["temperature_increase"] + 5
            data["temperature_variance"] *= 3.0

        if "power_stability" in params:
            data["power_stability_score"] = params["power_stability"]

        # Update threshold violations
        violations = 0
        if data["interface_error_rate"] > 0.1:
            violations += 1
        if data["cpu_utilization_max"] > 0.85:
            violations += 1
        if data["memory_utilization_max"] > 0.90:
            violations += 1
        if data["temperature_max"] > 65:
            violations += 1

        data["threshold_violations"] += violations

        if violations > 2:
            data["severity_escalations"] += 1

        return data

    def _apply_event_to_bgp(self, data: Dict[str, float], event: NetworkEvent) -> Dict[str, float]:
        """Apply event effects to BGP data."""
        params = event.parameters

        # Route withdrawals
        if "bgp_withdrawal_rate" in params:
            data["wdr_total"] += params["bgp_withdrawal_rate"]

        # Route announcements
        if "announcement_multiplier" in params:
            data["ann_total"] *= params["announcement_multiplier"]

        # AS path churn
        if "bgp_churn_rate" in params:
            data["as_path_churn"] += params["bgp_churn_rate"]

        # BGP session loss (massive withdrawals)
        if params.get("bgp_session_loss"):
            data["wdr_total"] += 100.0
            data["as_path_churn"] += 50.0

        # Session flapping
        if "session_flap_rate" in params:
            data["wdr_total"] += 20.0 * params["session_flap_rate"]
            data["ann_total"] += 20.0 * params["session_flap_rate"]
            data["as_path_churn"] += 15.0 * params["session_flap_rate"]

        return data

    def clear_event(self):
        """Clear the active event."""
        self.active_event = None
        self.event_start_time = None

    def get_available_scenarios(self) -> List[str]:
        """Get list of available failure scenarios."""
        return [
            "link_failure",
            "router_overload",
            "optical_degradation",
            "hardware_failure",
            "route_leak",
            "bgp_flapping",
        ]

    def get_event_info(self) -> Dict[str, Any]:
        """Get information about the active event."""
        if not self.active_event:
            return {"active": False}

        elapsed = time.time() - self.event_start_time if self.event_start_time else 0
        remaining = max(0, self.active_event.duration - elapsed)

        return {
            "active": self._is_event_active(),
            "event_type": self.active_event.event_type,
            "device": self.active_event.device,
            "severity": self.active_event.severity,
            "elapsed_seconds": elapsed,
            "remaining_seconds": remaining,
            "progress_percent": (elapsed / self.active_event.duration) * 100,
            "should_trigger_bgp": self.active_event.should_trigger_bgp,
            "should_trigger_snmp": self.active_event.should_trigger_snmp,
        }
