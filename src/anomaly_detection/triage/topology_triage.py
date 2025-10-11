#!/usr/bin/env python3
"""
Topology-Aware Triage System

Provides criticality assessment, blast radius calculation, and failure localization
based on network topology and device roles.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)


@dataclass
class TopologyLocation:
    """Predicted failure location with topology context."""

    device: str
    interface: Optional[str] = None
    bgp_peer: Optional[str] = None
    rack: Optional[str] = None
    datacenter: Optional[str] = None
    topology_role: Optional[str] = None
    confidence: float = 0.0


@dataclass
class BlastRadius:
    """Impact assessment of a failure."""

    affected_devices: int
    affected_services: List[str]
    downstream_devices: List[str]
    redundancy_available: bool
    spof: bool  # Single Point of Failure
    failure_domain: str


@dataclass
class CriticalityAssessment:
    """Criticality scoring for a failure."""

    score: float  # 0-10 scale
    priority: str  # P1, P2, P3
    factors: Dict[str, str]
    sla_breach_likely: bool
    time_to_breach_min: Optional[int]


@dataclass
class TriageResult:
    """Complete triage analysis result."""

    location: TopologyLocation
    ranked_predictions: List[TopologyLocation]
    blast_radius: BlastRadius
    criticality: CriticalityAssessment
    recommended_actions: List[Dict[str, str]]
    severity: str  # info, warning, error, critical


class TopologyTriageSystem:
    """
    Topology-aware triage system for network anomaly localization and impact assessment.
    """

    def __init__(self, roles_config_path: str = "config/configs/roles.yml"):
        """Initialize triage system with topology configuration."""
        self.roles_config_path = Path(roles_config_path)
        self.roles = {}
        self.device_metadata = {}
        self.role_priorities = {
            "edge": 4.0,
            "spine": 4.0,
            "rr": 4.0,  # Route reflector
            "tor": 3.5,
            "leaf": 2.5,
            "access": 1.5,
            "server": 1.0,
            "unknown": 0.5,
        }

        self._load_topology_config()

    def _load_topology_config(self):
        """Load topology configuration from YAML."""
        if not self.roles_config_path.exists():
            logger.warning(f"Roles config not found: {self.roles_config_path}")
            return

        try:
            with open(self.roles_config_path) as f:
                config = yaml.safe_load(f)
                self.roles = config.get("roles", {})
                logger.info(f"Loaded {len(self.roles)} device role mappings")
        except Exception as e:
            logger.error(f"Failed to load roles config: {e}")

    def analyze(self, anomaly_data: Dict, detected_location: Optional[Dict] = None) -> TriageResult:
        """
        Perform complete triage analysis for an anomaly.

        Args:
            anomaly_data: Detected anomaly information (type, confidence, sources)
            detected_location: Predicted failure location (device, interface, peer)

        Returns:
            TriageResult with full topology-aware analysis
        """
        # Step 1: Determine primary location
        primary_location = self._determine_location(detected_location or {})

        # Step 2: Generate ranked location predictions
        ranked_predictions = self._rank_predictions(anomaly_data, primary_location)

        # Step 3: Calculate blast radius
        blast_radius = self._calculate_blast_radius(primary_location, anomaly_data)

        # Step 4: Assess criticality
        criticality = self._assess_criticality(primary_location, blast_radius, anomaly_data)

        # Step 5: Determine severity
        severity = self._determine_severity(criticality.score)

        # Step 6: Generate recommended actions
        actions = self._recommend_actions(
            anomaly_data.get("alert_type", "unknown"), primary_location, criticality.priority
        )

        return TriageResult(
            location=primary_location,
            ranked_predictions=ranked_predictions,
            blast_radius=blast_radius,
            criticality=criticality,
            recommended_actions=actions,
            severity=severity,
        )

    def _determine_location(self, detected_location: Dict) -> TopologyLocation:
        """Determine primary failure location with topology context."""
        device = detected_location.get("device", "unknown")
        interface = detected_location.get("interface")
        bgp_peer = detected_location.get("bgp_peer") or detected_location.get("peer")

        # Get topology role
        role = self.roles.get(device) or self.roles.get(bgp_peer, "unknown")

        return TopologyLocation(
            device=device,
            interface=interface,
            bgp_peer=bgp_peer,
            topology_role=role,
            confidence=detected_location.get("confidence", 0.0),
        )

    def _rank_predictions(
        self, anomaly_data: Dict, primary: TopologyLocation
    ) -> List[TopologyLocation]:
        """Generate ranked list of possible failure locations."""
        predictions = [primary]

        # Add nearby devices based on topology (simplified - would use graph traversal)
        if primary.bgp_peer:
            # Find other devices in same role
            peer_role = self.roles.get(primary.bgp_peer)
            if peer_role:
                for device, role in self.roles.items():
                    if role == peer_role and device != primary.bgp_peer:
                        predictions.append(
                            TopologyLocation(
                                device=device,
                                topology_role=role,
                                confidence=primary.confidence
                                * 0.5,  # Lower confidence for inferred locations
                            )
                        )
                        if len(predictions) >= 5:
                            break

        return predictions[:5]  # Return top 5

    def _calculate_blast_radius(
        self, location: TopologyLocation, anomaly_data: Dict
    ) -> BlastRadius:
        """Calculate impact blast radius for a failure."""
        role = location.topology_role or "unknown"

        # Estimate based on role (simplified - would use topology graph)
        blast_estimates = {
            "edge": (20, ["external_connectivity"], False, True, "edge"),
            "spine": (15, ["east_west_traffic"], False, True, "datacenter"),
            "rr": (30, ["bgp_convergence"], False, True, "network"),
            "tor": (12, ["rack_connectivity"], False, True, "rack"),
            "leaf": (8, ["server_connectivity"], True, False, "pod"),
            "access": (2, ["user_connectivity"], True, False, "floor"),
            "server": (1, ["application"], True, False, "local"),
            "unknown": (5, ["unknown"], False, False, "unknown"),
        }

        affected_count, services, redundancy, is_spof, domain = blast_estimates.get(
            role, blast_estimates["unknown"]
        )

        # Get downstream devices (simplified - would traverse topology)
        downstream = []
        if location.device and location.device in self.roles:
            # Would normally find all devices downstream in topology
            downstream = [
                f"{location.device}-downstream-{i}" for i in range(min(affected_count, 5))
            ]

        return BlastRadius(
            affected_devices=affected_count,
            affected_services=services,
            downstream_devices=downstream,
            redundancy_available=redundancy,
            spof=is_spof,
            failure_domain=domain,
        )

    def _assess_criticality(
        self, location: TopologyLocation, blast_radius: BlastRadius, anomaly_data: Dict
    ) -> CriticalityAssessment:
        """Assess criticality score and priority."""
        score = 0.0
        factors = {}

        # Factor 1: Topology role (0-4 points)
        role = location.topology_role or "unknown"
        role_score = self.role_priorities.get(role, 0.5)
        score += role_score
        factors["topology_role"] = f"{role} ({role_score:.1f} pts)"

        # Factor 2: Blast radius (0-3 points)
        if blast_radius.affected_devices > 15:
            blast_score = 3.0
        elif blast_radius.affected_devices > 10:
            blast_score = 2.5
        elif blast_radius.affected_devices > 5:
            blast_score = 2.0
        else:
            blast_score = 1.0
        score += blast_score
        factors["blast_radius"] = f"{blast_radius.affected_devices} devices ({blast_score:.1f} pts)"

        # Factor 3: SPOF (0-2 points)
        if blast_radius.spof:
            spof_score = 2.0
            factors["redundancy"] = "SPOF - no redundancy (2.0 pts)"
        else:
            spof_score = 0.0
            factors["redundancy"] = "Redundancy available (0.0 pts)"
        score += spof_score

        # Factor 4: Service impact (0-1 point)
        if "connectivity" in str(blast_radius.affected_services).lower():
            service_score = 1.0
            factors["service_impact"] = "Connectivity affected (1.0 pt)"
        else:
            service_score = 0.5
            factors["service_impact"] = "Limited impact (0.5 pt)"
        score += service_score

        # Cap at 10.0
        score = min(score, 10.0)

        # Determine priority
        if score >= 8.0:
            priority = "P1"
            sla_breach = True
            time_to_breach = 15
        elif score >= 5.0:
            priority = "P2"
            sla_breach = True
            time_to_breach = 60
        else:
            priority = "P3"
            sla_breach = False
            time_to_breach = None

        return CriticalityAssessment(
            score=score,
            priority=priority,
            factors=factors,
            sla_breach_likely=sla_breach,
            time_to_breach_min=time_to_breach,
        )

    def _determine_severity(self, criticality_score: float) -> str:
        """Map criticality score to severity level."""
        if criticality_score >= 8.0:
            return "critical"
        elif criticality_score >= 5.0:
            return "error"
        elif criticality_score >= 3.0:
            return "warning"
        else:
            return "info"

    def _recommend_actions(
        self, failure_type: str, location: TopologyLocation, priority: str
    ) -> List[Dict[str, str]]:
        """Generate recommended troubleshooting actions."""
        actions = []

        # Action templates based on failure type
        if "link" in failure_type.lower() or "interface" in failure_type.lower():
            actions.append(
                {
                    "priority": "1",
                    "action": f"Check physical link status on {location.device}",
                    "command": f"show interface {location.interface or 'all'} status",
                    "estimated_time": "2 minutes",
                }
            )

        if "bgp" in failure_type.lower() or "flapping" in failure_type.lower():
            actions.append(
                {
                    "priority": "2",
                    "action": "Verify BGP session health",
                    "command": f"show bgp neighbor {location.bgp_peer or 'all'}",
                    "estimated_time": "1 minute",
                }
            )

        if "multimodal" in failure_type.lower():
            actions.append(
                {
                    "priority": "3",
                    "action": "Check SNMP interface counters for errors",
                    "command": f"show snmp interface {location.device}",
                    "estimated_time": "1 minute",
                }
            )

        # Always add escalation for P1
        if priority == "P1":
            actions.append(
                {
                    "priority": "4",
                    "action": "Escalate to on-call network engineer",
                    "contact": "NOC hotline",
                    "estimated_time": "Immediate",
                }
            )

        return actions


# Singleton instance
_triage_system = None


def get_triage_system(roles_config_path: str = "config/configs/roles.yml") -> TopologyTriageSystem:
    """Get or create singleton triage system instance."""
    global _triage_system
    if _triage_system is None:
        _triage_system = TopologyTriageSystem(roles_config_path)
    return _triage_system
