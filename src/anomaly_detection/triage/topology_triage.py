#!/usr/bin/env python3
"""
Topology-Aware Triage System

This module provides focused failure analysis and triage capabilities for network
anomaly detection. It combines topology-aware impact assessment with multimodal
correlation data to deliver precise failure localization and SPOF detection.

Key Features:
    - Topology-aware failure localization using graph traversal
    - Blast radius calculation based on actual network topology
    - Criticality scoring (0-10) with priority classification (P1/P2/P3)
    - Integration with multimodal correlator for impact data
    - SPOF (Single Point of Failure) detection
    - SLA breach likelihood assessment

Architecture:
    The triage system operates as the core analysis layer, consuming:
    - Raw anomaly detections from ML pipelines
    - Topology graph data for network structure
    - Multimodal correlation data for impact assessment
    - Device role mappings for criticality weighting

    It produces focused triage results with:
    - Ranked failure location predictions
    - Impact assessment with affected devices
    - Criticality assessment with scoring factors
    - Severity classification

Example:
    >>> triage = TopologyTriageSystem()
    >>> result = triage.analyze(anomaly_data, detected_location)
    >>> print(f"Priority: {result.criticality.priority}")
    >>> print(f"SPOF: {result.blast_radius.spof}")
    >>> print(f"Affected devices: {result.blast_radius.affected_devices}")
"""

import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from anomaly_detection.topology import DeviceRole, FailureDomain, NetworkTopologyGraph

logger = logging.getLogger(__name__)


class Priority(Enum):
    """Alert priority levels based on criticality scoring."""
    
    P1 = "P1"  # Critical (score >= 8.0) - SLA breach imminent
    P2 = "P2"  # High (score >= 5.0) - SLA breach likely
    P3 = "P3"  # Medium (score < 5.0) - Monitor and investigate


class Severity(Enum):
    """Alert severity levels mapped from criticality scores."""
    
    CRITICAL = "critical"  # Score >= 8.0
    ERROR = "error"       # Score >= 5.0
    WARNING = "warning"    # Score >= 3.0
    INFO = "info"         # Score < 3.0


@dataclass
class TopologyLocation:
    """
    Predicted failure location with essential topology context.
    
    This class represents a specific location in the network topology where
    a failure has been detected or predicted. It focuses on core attributes
    needed for failure analysis while remaining extensible.
    
    Attributes:
        device: Primary device identifier (hostname or IP)
        interface: Specific interface name if applicable
        bgp_peer: BGP peer device if BGP-related failure
        topology_role: Network role (spine, tor, edge, etc.)
        confidence: Detection confidence score (0.0-1.0)
        
    Example:
        >>> location = TopologyLocation(
        ...     device="spine-01",
        ...     interface="eth0",
        ...     topology_role=DeviceRole.SPINE,
        ...     confidence=0.85
        ... )
    """

    device: str
    interface: Optional[str] = None
    bgp_peer: Optional[str] = None
    topology_role: Optional[DeviceRole] = None
    confidence: float = 0.0


@dataclass
class BlastRadius:
    """
    Comprehensive impact assessment of a network failure.
    
    This class quantifies the scope and impact of a network failure,
    including the number of affected devices, services, and the
    availability of redundancy mechanisms.
    
    Attributes:
        affected_devices: Total number of devices impacted
        affected_services: List of service types affected
        downstream_devices: Devices downstream from failure point
        redundancy_available: Whether redundancy exists for this failure
        spof: Whether this represents a Single Point of Failure
        failure_domain: Network domain affected (edge, datacenter, etc.)
        impact_score: Calculated impact score (0-10)
        
    Example:
        >>> blast = BlastRadius(
        ...     affected_devices=15,
        ...     affected_services=["east_west_traffic"],
        ...     downstream_devices=["tor-01", "tor-02"],
        ...     redundancy_available=False,
        ...     spof=True,
        ...     failure_domain="datacenter"
        ... )
    """

    affected_devices: int
    affected_services: List[str]
    downstream_devices: List[str]
    redundancy_available: bool
    spof: bool  # Single Point of Failure
    failure_domain: FailureDomain
    impact_score: float = 0.0


@dataclass
class CriticalityAssessment:
    """
    Comprehensive criticality assessment with scoring and priority classification.
    
    This class provides a detailed analysis of failure criticality based on
    multiple factors including topology role, blast radius, redundancy status,
    and service impact. The scoring system uses a 0-10 scale with automatic
    priority classification.
    
    Attributes:
        score: Criticality score (0.0-10.0)
        priority: Priority level (P1/P2/P3)
        factors: Detailed scoring breakdown by factor
        sla_breach_likely: Whether SLA breach is likely
        time_to_breach_min: Estimated time to SLA breach (minutes)
        
    Scoring Factors:
        - Topology Role (0-4 points): Device criticality based on role
        - Blast Radius (0-3 points): Number of affected devices
        - SPOF Status (0-2 points): Single Point of Failure penalty
        - Service Impact (0-1 point): Connectivity vs. limited impact
        
    Priority Mapping:
        - P1 (Critical): Score >= 8.0, SLA breach imminent
        - P2 (High): Score >= 5.0, SLA breach likely
        - P3 (Medium): Score < 5.0, monitor and investigate
        
    Example:
        >>> assessment = CriticalityAssessment(
        ...     score=8.5,
        ...     priority="P1",
        ...     factors={"topology_role": "spine (4.0 pts)"},
        ...     sla_breach_likely=True,
        ...     time_to_breach_min=15
        ... )
    """

    score: float  # 0-10 scale
    priority: Priority
    factors: Dict[str, str]
    sla_breach_likely: bool
    time_to_breach_min: Optional[int]


@dataclass
class TriageResult:
    """
    Core triage analysis result focused on failure location and impact.
    
    This class represents the essential output of the topology-aware triage system,
    focusing on failure localization and SPOF detection while remaining extensible.
    
    Attributes:
        location: Primary predicted failure location
        ranked_predictions: Ranked list of possible failure locations
        blast_radius: Impact assessment including affected devices
        criticality: Criticality scoring and priority classification
        severity: Overall severity level
        
    Example:
        >>> result = TriageResult(
        ...     location=primary_location,
        ...     ranked_predictions=[location1, location2],
        ...     blast_radius=blast_assessment,
        ...     criticality=criticality_assessment,
        ...     severity=Severity.CRITICAL
        ... )
    """

    location: TopologyLocation
    ranked_predictions: List[TopologyLocation]
    blast_radius: BlastRadius
    criticality: CriticalityAssessment
    severity: Severity


class TopologyTriageSystem:
    """
    Topology-aware triage system for network anomaly localization and impact assessment.
    
    This system provides comprehensive failure analysis by combining:
    - Topology graph traversal for accurate blast radius calculation
    - Multimodal correlation data for impact assessment
    - Device role-based criticality scoring
    - Actionable troubleshooting recommendations
    
    The system operates as the final analysis layer in the anomaly detection
    pipeline, consuming raw anomaly detections and producing enriched triage
    results with operational context.
    
    Key Capabilities:
        - Failure localization with confidence scoring
        - Topology-aware blast radius calculation
        - Criticality assessment with priority classification
        - SPOF detection and redundancy analysis
        - Actionable troubleshooting recommendations
        - Integration with multimodal correlation data
    
    Architecture:
        The system integrates with:
        - NetworkTopologyGraph for topology traversal
        - MultimodalCorrelator for impact data
        - Device role mappings for criticality weighting
        
    Example:
        >>> triage = TopologyTriageSystem(
        ...     roles_config_path="config/roles.yml",
        ...     topology_config_path="evaluation/topology.yml"
        ... )
        >>> result = triage.analyze(anomaly_data, detected_location)
        >>> print(f"Priority: {result.criticality.priority.value}")
        >>> print(f"Affected devices: {result.blast_radius.affected_devices}")
    """

    def __init__(self, roles_config_path: str = "config/roles.yml", topology_config_path: str = "evaluation/topology.yml"):
        """
        Initialize triage system with topology and role configurations.
        
        Args:
            roles_config_path: Path to device role mapping configuration
            topology_config_path: Path to network topology configuration
        """
        self.roles_config_path = Path(roles_config_path)
        self.topology_config_path = Path(topology_config_path)
        self.roles = {}
        self.device_metadata = {}
        
        # Role priority mapping for criticality scoring
        self.role_priorities = {
            DeviceRole.EDGE: 4.0,
            DeviceRole.SPINE: 4.0,
            DeviceRole.ROUTE_REFLECTOR: 4.0,
            DeviceRole.TOR: 3.5,
            DeviceRole.LEAF: 2.5,
            DeviceRole.ACCESS: 1.5,
            DeviceRole.SERVER: 1.0,
            DeviceRole.UNKNOWN: 0.5,
        }
        
        # Initialize topology graph
        self.topology_graph = NetworkTopologyGraph(topology_config_path)
        
        self._load_topology_config()

    def _load_topology_config(self):
        """
        Load topology configuration from YAML files.
        
        This method loads both device role mappings and topology configuration
        to enable accurate failure analysis and impact assessment.
        """
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

    def analyze(self, anomaly_data: Dict, detected_location: Optional[Dict] = None, correlator_data: Optional[Dict] = None) -> TriageResult:
        """
        Perform core triage analysis focused on failure location and SPOF detection.
        
        This method orchestrates the essential triage analysis pipeline,
        focusing on failure localization and impact assessment.
        
        Args:
            anomaly_data: Detected anomaly information including type, confidence, and sources
            detected_location: Predicted failure location from ML pipeline
            correlator_data: Additional impact data from multimodal correlator
            
        Returns:
            TriageResult containing core analysis:
            - Primary and ranked failure locations
            - Impact assessment with affected devices
            - Criticality scoring and priority classification
            - Overall severity level
            
        Example:
            >>> anomaly_data = {
            ...     "alert_type": "bgp_flapping",
            ...     "confidence": 0.85,
            ...     "sources": ["bgp", "snmp"]
            ... }
            >>> detected_location = {
            ...     "device": "spine-01",
            ...     "interface": "eth0",
            ...     "confidence": 0.75
            ... }
            >>> result = triage.analyze(anomaly_data, detected_location)
        """
        # Step 1: Determine primary location with topology context
        primary_location = self._determine_location(detected_location or {})

        # Step 2: Generate ranked location predictions
        ranked_predictions = self._rank_predictions(anomaly_data, primary_location)

        # Step 3: Calculate blast radius using topology graph
        blast_radius = self._calculate_blast_radius(primary_location, anomaly_data, correlator_data)

        # Step 4: Assess criticality with comprehensive scoring
        criticality = self._assess_criticality(primary_location, blast_radius, anomaly_data)

        # Step 5: Determine severity level
        severity = self._determine_severity(criticality.score)

        return TriageResult(
            location=primary_location,
            ranked_predictions=ranked_predictions,
            blast_radius=blast_radius,
            criticality=criticality,
            severity=severity,
        )

    def _determine_location(self, detected_location: Dict) -> TopologyLocation:
        """
        Determine primary failure location with essential topology context.
        
        This method processes the detected location from ML pipelines and
        enriches it with essential topology information including device roles
        and confidence scoring.
        
        Args:
            detected_location: Raw location data from ML pipeline
            
        Returns:
            TopologyLocation with essential topology context
        """
        device = detected_location.get("device", "unknown")
        interface = detected_location.get("interface")
        bgp_peer = detected_location.get("bgp_peer") or detected_location.get("peer")

        # Get topology role from graph
        role = self.topology_graph.get_device_role(device)

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
        """
        Generate ranked list of possible failure locations using topology analysis.
        
        This method uses topology graph traversal to identify alternative
        failure locations based on network connectivity and device roles.
        
        Args:
            anomaly_data: Anomaly detection data for context
            primary: Primary predicted location
            
        Returns:
            List of TopologyLocation objects ranked by likelihood
        """
        predictions = [primary]

        # Add peer devices as potential failure locations
        if primary.device and primary.device != "unknown":
            peer_devices = self.topology_graph.get_peer_devices(primary.device)
            
            for peer_device in peer_devices[:4]:  # Limit to top 4 peers
                peer_role = self.topology_graph.get_device_role(peer_device)
                predictions.append(
                    TopologyLocation(
                        device=peer_device,
                        topology_role=peer_role,
                        confidence=primary.confidence * 0.6,  # Lower confidence for peers
                    )
                )

        # Add devices with same role as potential locations
        if primary.topology_role:
            for device_name in self.topology_graph.get_devices_by_role(primary.topology_role):
                if device_name != primary.device and len(predictions) < 5:
                    predictions.append(
                        TopologyLocation(
                            device=device_name,
                            topology_role=primary.topology_role,
                            confidence=primary.confidence * 0.4,  # Lower confidence for role-based
                        )
                    )

        return predictions[:5]  # Return top 5

    def _calculate_blast_radius(
        self, location: TopologyLocation, anomaly_data: Dict, correlator_data: Optional[Dict] = None
    ) -> BlastRadius:
        """
        Calculate comprehensive blast radius using topology graph and correlator data.
        
        This method combines topology graph traversal with multimodal correlator
        data to provide accurate impact assessment including affected devices,
        services, and redundancy status.
        
        Args:
            location: Primary failure location
            anomaly_data: Anomaly detection data
            correlator_data: Additional impact data from multimodal correlator
            
        Returns:
            BlastRadius with comprehensive impact assessment
        """
        device = location.device
        
        # Get topology-based impact data
        affected_count, affected_services, has_redundancy = self.topology_graph.calculate_blast_radius(device)
        downstream_devices = self.topology_graph.get_downstream_devices(device)
        
        # Enhance with correlator data if available
        if correlator_data:
            correlator_affected = correlator_data.get("affected_devices", [])
            correlator_services = correlator_data.get("affected_services", [])
            
            # Merge correlator data with topology data
            if correlator_affected:
                affected_count = max(affected_count, len(correlator_affected))
            if correlator_services:
                affected_services.extend(correlator_services)
        
        # Determine failure domain based on role
        failure_domain = self.topology_graph.get_failure_domain(device)
        
        # Determine SPOF status
        is_spof = self.topology_graph.is_spof(device)
        
        # Calculate impact score (0-10)
        impact_score = min(10.0, affected_count * 0.5 + (3.0 if is_spof else 0.0))

        return BlastRadius(
            affected_devices=affected_count,
            affected_services=list(set(affected_services)),  # Remove duplicates
            downstream_devices=downstream_devices,
            redundancy_available=has_redundancy,
            spof=is_spof,
            failure_domain=failure_domain,
            impact_score=impact_score,
        )

    def _assess_criticality(
        self, location: TopologyLocation, blast_radius: BlastRadius, anomaly_data: Dict
    ) -> CriticalityAssessment:
        """
        Assess criticality score and priority using comprehensive scoring factors.
        
        This method calculates a criticality score (0-10) based on multiple factors:
        - Topology role criticality (0-4 points)
        - Blast radius impact (0-3 points)
        - SPOF status (0-2 points)
        - Service impact (0-1 point)
        
        Args:
            location: Primary failure location
            blast_radius: Impact assessment
            anomaly_data: Anomaly detection data
            
        Returns:
            CriticalityAssessment with score, priority, and detailed factors
        """
        score = 0.0
        factors = {}

        # Factor 1: Topology role (0-4 points)
        role = location.topology_role or DeviceRole.UNKNOWN
        role_score = self.role_priorities.get(role, 0.5)
        score += role_score
        factors["topology_role"] = f"{role.value} ({role_score:.1f} pts)"

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
            priority = Priority.P1
            sla_breach = True
            time_to_breach = 15
        elif score >= 5.0:
            priority = Priority.P2
            sla_breach = True
            time_to_breach = 60
        else:
            priority = Priority.P3
            sla_breach = False
            time_to_breach = None

        return CriticalityAssessment(
            score=score,
            priority=priority,
            factors=factors,
            sla_breach_likely=sla_breach,
            time_to_breach_min=time_to_breach,
        )

    def _determine_severity(self, criticality_score: float) -> Severity:
        """
        Map criticality score to severity level using standardized thresholds.
        
        Args:
            criticality_score: Calculated criticality score (0-10)
            
        Returns:
            Severity enum value
        """
        if criticality_score >= 8.0:
            return Severity.CRITICAL
        elif criticality_score >= 5.0:
            return Severity.ERROR
        elif criticality_score >= 3.0:
            return Severity.WARNING
        else:
            return Severity.INFO

# Singleton instance
_triage_system = None


def get_triage_system(roles_config_path: str = "config/roles.yml", topology_config_path: str = "evaluation/topology.yml") -> TopologyTriageSystem:
    """Get or create singleton triage system instance."""
    global _triage_system
    if _triage_system is None:
        _triage_system = TopologyTriageSystem(roles_config_path, topology_config_path)
    return _triage_system