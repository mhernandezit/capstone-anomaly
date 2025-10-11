#!/usr/bin/env python3
"""
Multimodal Correlation Agent

This agent sits behind the Isolation Forest (SNMP) and Matrix Profile (BGP) pipelines.
It receives anomaly detections from both sources, correlates events, and uses topology
data to provide enriched context including:
- Event correlation across modalities
- Topology-aware impact assessment
- Severity classification
- Root cause localization
- Actionable recommendations

Architecture:
    BGP Pipeline (Matrix Profile) ----\
                                       +--> Correlation Agent --> Enriched Alerts
    SNMP Pipeline (Isolation Forest) -/

The correlation agent provides the "intelligence" layer that transforms raw anomaly
detections into actionable operational insights.
"""

import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import yaml

from anomaly_detection.triage.topology_triage import TopologyTriageSystem, TriageResult

logger = logging.getLogger(__name__)


@dataclass
class AnomalyEvent:
    """Represents an anomaly detection event from a single pipeline."""

    timestamp: float
    source: str  # 'bgp' or 'snmp'
    confidence: float
    severity: str

    # Source-specific data
    device: Optional[str] = None
    interface: Optional[str] = None
    peer: Optional[str] = None

    # Anomaly characteristics
    anomaly_score: float = 0.0
    affected_features: List[str] = None

    # Raw detection data
    raw_data: Dict[str, Any] = None

    def __post_init__(self):
        if self.affected_features is None:
            self.affected_features = []
        if self.raw_data is None:
            self.raw_data = {}


@dataclass
class CorrelatedEvent:
    """Represents a correlated event from multiple sources."""

    correlation_id: str
    timestamp: float

    # Source events
    bgp_event: Optional[AnomalyEvent] = None
    snmp_event: Optional[AnomalyEvent] = None

    # Correlation metrics
    correlation_strength: float = 0.0
    temporal_proximity: float = 0.0  # How close in time (0-1, 1=same time)
    spatial_correlation: float = 0.0  # Same device/interface/peer (0-1)

    # Multi-modal assessment
    is_multi_modal: bool = False
    modalities: List[str] = None

    def __post_init__(self):
        if self.modalities is None:
            self.modalities = []


@dataclass
class EnrichedAlert:
    """Final enriched alert with full context and recommendations."""

    alert_id: str
    timestamp: float

    # Correlation data
    correlated_event: CorrelatedEvent

    # Topology-aware analysis
    triage_result: TriageResult

    # Classification
    alert_type: str
    severity: str
    priority: str
    confidence: float

    # Impact
    affected_devices: List[str]
    affected_services: List[str]
    blast_radius: int
    is_spof: bool

    # Root cause
    probable_root_cause: str
    supporting_evidence: List[str]

    # Operator guidance
    recommended_actions: List[Dict[str, str]]
    escalation_required: bool
    estimated_resolution_time: str


class MultiModalCorrelator:
    """
    Multimodal correlation agent that combines BGP and SNMP anomaly detections.

    This is the "intelligent" layer that sits behind both pipelines and provides:
    - Temporal correlation (events close in time)
    - Spatial correlation (same device/location)
    - Cross-modal validation (confirming anomalies across sources)
    - Topology-aware impact assessment
    - Root cause localization
    - Actionable recommendations
    """

    def __init__(
        self,
        topology_path: str = "evaluation/topology.yml",
        roles_config_path: str = "config/configs/roles.yml",
        correlation_window: float = 60.0,  # seconds
        min_correlation_confidence: float = 0.6,
    ):
        """
        Initialize the multimodal correlation agent.

        Args:
            topology_path: Path to topology YAML file
            roles_config_path: Path to device roles configuration
            correlation_window: Time window for correlating events (seconds)
            min_correlation_confidence: Minimum confidence for correlation
        """
        self.correlation_window = correlation_window
        self.min_correlation_confidence = min_correlation_confidence

        # Load topology
        self.topology = self._load_topology(topology_path)

        # Initialize topology triage system
        self.triage_system = TopologyTriageSystem(roles_config_path)

        # Event buffers (recent events from each pipeline)
        self.recent_bgp_events: List[AnomalyEvent] = []
        self.recent_snmp_events: List[AnomalyEvent] = []

        # Correlated events (to avoid duplicate processing)
        self.processed_correlations: Dict[str, float] = {}  # correlation_id -> timestamp

        # Statistics
        self.stats = {
            "bgp_events": 0,
            "snmp_events": 0,
            "correlated_events": 0,
            "multi_modal_confirmations": 0,
            "false_positives_suppressed": 0,
            "alerts_generated": 0,
        }

        logger.info("[OK] Multimodal Correlation Agent initialized")
        logger.info(f"  Correlation window: {correlation_window}s")
        logger.info(f"  Min correlation confidence: {min_correlation_confidence}")
        logger.info(f"  Topology devices: {len(self.topology.get('devices', {}))}")

    def _load_topology(self, path: str) -> Dict:
        """Load topology configuration from YAML."""
        try:
            with open(path) as f:
                topology = yaml.safe_load(f)
                logger.info(f"[OK] Loaded topology from {path}")
                return topology
        except Exception as e:
            logger.warning(f"Failed to load topology from {path}: {e}")
            return {"devices": {}, "bgp_peers": []}

    def ingest_bgp_anomaly(
        self,
        timestamp: float,
        confidence: float,
        detected_series: List[str],
        peer: str = None,
        raw_data: Dict = None,
    ) -> Optional[EnrichedAlert]:
        """
        Ingest a BGP anomaly from the Matrix Profile pipeline.

        Args:
            timestamp: Event timestamp
            confidence: Detection confidence (0-1)
            detected_series: List of anomalous series (e.g., ['wdr_total', 'as_path_churn'])
            peer: BGP peer identifier
            raw_data: Raw detection data from Matrix Profile

        Returns:
            EnrichedAlert if correlation produces actionable alert, None otherwise
        """
        # Create BGP event
        event = AnomalyEvent(
            timestamp=timestamp,
            source="bgp",
            confidence=confidence,
            severity=self._classify_bgp_severity(confidence, detected_series),
            peer=peer,
            affected_features=detected_series,
            raw_data=raw_data or {},
        )

        self.recent_bgp_events.append(event)
        self.stats["bgp_events"] += 1

        # Clean old events
        self._cleanup_old_events()

        # Attempt correlation
        return self._correlate_and_enrich(event)

    def ingest_snmp_anomaly(
        self,
        timestamp: float,
        confidence: float,
        severity: str,
        device: str = None,
        interface: str = None,
        affected_features: List[str] = None,
        raw_data: Dict = None,
    ) -> Optional[EnrichedAlert]:
        """
        Ingest an SNMP anomaly from the Isolation Forest pipeline.

        Args:
            timestamp: Event timestamp
            confidence: Detection confidence (0-1)
            severity: Severity from Isolation Forest (info/warning/error/critical)
            device: Device identifier
            interface: Interface identifier
            affected_features: List of anomalous SNMP features
            raw_data: Raw detection data from Isolation Forest

        Returns:
            EnrichedAlert if correlation produces actionable alert, None otherwise
        """
        # Create SNMP event
        event = AnomalyEvent(
            timestamp=timestamp,
            source="snmp",
            confidence=confidence,
            severity=severity,
            device=device,
            interface=interface,
            affected_features=affected_features or [],
            raw_data=raw_data or {},
        )

        self.recent_snmp_events.append(event)
        self.stats["snmp_events"] += 1

        # Clean old events
        self._cleanup_old_events()

        # Attempt correlation
        return self._correlate_and_enrich(event)

    def _cleanup_old_events(self):
        """Remove events outside the correlation window."""
        current_time = time.time()
        cutoff = current_time - self.correlation_window

        self.recent_bgp_events = [e for e in self.recent_bgp_events if e.timestamp > cutoff]
        self.recent_snmp_events = [e for e in self.recent_snmp_events if e.timestamp > cutoff]

        # Clean processed correlations (older than 5 minutes)
        correlation_cutoff = current_time - 300
        self.processed_correlations = {
            k: v for k, v in self.processed_correlations.items() if v > correlation_cutoff
        }

    def _correlate_and_enrich(self, new_event: AnomalyEvent) -> Optional[EnrichedAlert]:
        """
        Correlate a new event with recent events from other sources and enrich with context.

        This is the core correlation logic that:
        1. Finds temporally and spatially correlated events
        2. Calculates correlation strength
        3. Performs topology-aware triage
        4. Generates enriched alerts

        Args:
            new_event: Newly ingested event

        Returns:
            EnrichedAlert if correlation succeeds and confidence is sufficient
        """
        # Find best correlated event from other source
        if new_event.source == "bgp":
            correlated_event = self._find_best_correlation(new_event, self.recent_snmp_events)
        else:  # snmp
            correlated_event = self._find_best_correlation(new_event, self.recent_bgp_events)

        # Build correlated event object
        if new_event.source == "bgp":
            bgp_event = new_event
            snmp_event = correlated_event
        else:
            bgp_event = correlated_event
            snmp_event = new_event

        # Calculate correlation metrics
        correlation = self._build_correlation(bgp_event, snmp_event)

        # Check if we've already processed this correlation
        correlation_key = self._get_correlation_key(correlation)
        if correlation_key in self.processed_correlations:
            logger.debug(f"Skipping duplicate correlation: {correlation_key}")
            return None

        # Decide if this correlation is strong enough to process
        if correlation.correlation_strength < self.min_correlation_confidence:
            logger.debug(
                f"Correlation strength too low: {correlation.correlation_strength:.2f} "
                f"< {self.min_correlation_confidence}"
            )

            # Single-source anomaly - might be false positive
            if new_event.confidence > 0.85:
                # High confidence single source - might still alert
                pass
            else:
                self.stats["false_positives_suppressed"] += 1
                return None

        # Mark as processed
        self.processed_correlations[correlation_key] = time.time()
        self.stats["correlated_events"] += 1

        if correlation.is_multi_modal:
            self.stats["multi_modal_confirmations"] += 1

        # Perform topology-aware triage
        triage_result = self._perform_triage(correlation)

        # Generate enriched alert
        alert = self._generate_enriched_alert(correlation, triage_result)

        self.stats["alerts_generated"] += 1

        return alert

    def _find_best_correlation(
        self, event: AnomalyEvent, candidates: List[AnomalyEvent]
    ) -> Optional[AnomalyEvent]:
        """Find the best correlated event from candidate list."""
        if not candidates:
            return None

        best_candidate = None
        best_score = 0.0

        for candidate in candidates:
            # Calculate correlation score based on temporal and spatial proximity
            temporal_score = self._calculate_temporal_proximity(event, candidate)
            spatial_score = self._calculate_spatial_correlation(event, candidate)

            # Combined score (weighted)
            combined_score = 0.6 * temporal_score + 0.4 * spatial_score

            if combined_score > best_score:
                best_score = combined_score
                best_candidate = candidate

        return best_candidate

    def _calculate_temporal_proximity(self, event1: AnomalyEvent, event2: AnomalyEvent) -> float:
        """Calculate temporal proximity score (0-1, 1=same time)."""
        time_diff = abs(event1.timestamp - event2.timestamp)

        # Exponential decay within correlation window
        proximity = max(0.0, 1.0 - (time_diff / self.correlation_window))

        return proximity

    def _calculate_spatial_correlation(self, event1: AnomalyEvent, event2: AnomalyEvent) -> float:
        """Calculate spatial correlation score (0-1, 1=same location)."""
        score = 0.0

        # Check device match
        if event1.device and event2.device:
            if event1.device == event2.device:
                score += 0.5

        # Check interface match
        if event1.interface and event2.interface:
            if event1.interface == event2.interface:
                score += 0.3

        # Check peer relationship
        if event1.peer and event2.device:
            if event1.peer == event2.device or self._are_bgp_neighbors(event1.peer, event2.device):
                score += 0.2

        if event2.peer and event1.device:
            if event2.peer == event1.device or self._are_bgp_neighbors(event2.peer, event1.device):
                score += 0.2

        return min(score, 1.0)

    def _are_bgp_neighbors(self, device1: str, device2: str) -> bool:
        """Check if two devices are BGP neighbors."""
        peers = self.topology.get("bgp_peers", [])
        for peer_pair in peers:
            if set(peer_pair) == {device1, device2}:
                return True
        return False

    def _build_correlation(
        self, bgp_event: Optional[AnomalyEvent], snmp_event: Optional[AnomalyEvent]
    ) -> CorrelatedEvent:
        """Build a correlated event from BGP and SNMP events."""
        # Determine timestamp (use the one that exists, or average if both)
        if bgp_event and snmp_event:
            timestamp = (bgp_event.timestamp + snmp_event.timestamp) / 2
        elif bgp_event:
            timestamp = bgp_event.timestamp
        elif snmp_event:
            timestamp = snmp_event.timestamp
        else:
            timestamp = time.time()

        # Calculate correlation metrics
        temporal_proximity = 0.0
        spatial_correlation = 0.0

        if bgp_event and snmp_event:
            temporal_proximity = self._calculate_temporal_proximity(bgp_event, snmp_event)
            spatial_correlation = self._calculate_spatial_correlation(bgp_event, snmp_event)

        # Overall correlation strength
        correlation_strength = (temporal_proximity + spatial_correlation) / 2

        # Determine modalities
        modalities = []
        if bgp_event:
            modalities.append("bgp")
        if snmp_event:
            modalities.append("snmp")

        is_multi_modal = len(modalities) > 1

        # Generate correlation ID
        correlation_id = self._generate_correlation_id(bgp_event, snmp_event)

        return CorrelatedEvent(
            correlation_id=correlation_id,
            timestamp=timestamp,
            bgp_event=bgp_event,
            snmp_event=snmp_event,
            correlation_strength=correlation_strength,
            temporal_proximity=temporal_proximity,
            spatial_correlation=spatial_correlation,
            is_multi_modal=is_multi_modal,
            modalities=modalities,
        )

    def _generate_correlation_id(
        self, bgp_event: Optional[AnomalyEvent], snmp_event: Optional[AnomalyEvent]
    ) -> str:
        """Generate unique correlation ID."""
        components = []

        if bgp_event:
            components.append(f"bgp-{int(bgp_event.timestamp)}")
        if snmp_event:
            components.append(f"snmp-{int(snmp_event.timestamp)}")

        return "-".join(components)

    def _get_correlation_key(self, correlation: CorrelatedEvent) -> str:
        """Get key for tracking processed correlations."""
        return correlation.correlation_id

    def _perform_triage(self, correlation: CorrelatedEvent) -> TriageResult:
        """Perform topology-aware triage using the triage system."""
        # Extract location information
        location = {}

        if correlation.snmp_event:
            location["device"] = correlation.snmp_event.device
            location["interface"] = correlation.snmp_event.interface
            location["confidence"] = correlation.snmp_event.confidence

        if correlation.bgp_event:
            location["peer"] = correlation.bgp_event.peer
            if not location.get("device"):
                location["device"] = correlation.bgp_event.peer

        # Build anomaly data for triage
        anomaly_data = {
            "alert_type": self._classify_failure_type(correlation),
            "confidence": self._calculate_combined_confidence(correlation),
            "sources": correlation.modalities,
        }

        # Perform triage
        triage_result = self.triage_system.analyze(
            anomaly_data=anomaly_data, detected_location=location
        )

        return triage_result

    def _classify_failure_type(self, correlation: CorrelatedEvent) -> str:
        """Classify the type of failure based on correlated events."""
        failure_types = []

        # Check SNMP features
        if correlation.snmp_event:
            features = correlation.snmp_event.affected_features
            if any("error" in f.lower() for f in features):
                failure_types.append("link_degradation")
            if any("temperature" in f.lower() for f in features):
                failure_types.append("thermal_issue")
            if any("power" in f.lower() for f in features):
                failure_types.append("power_issue")
            if any("cpu" in f.lower() or "memory" in f.lower() for f in features):
                failure_types.append("resource_exhaustion")

        # Check BGP patterns
        if correlation.bgp_event:
            features = correlation.bgp_event.affected_features
            if "wdr_total" in features:
                failure_types.append("route_withdrawal")
            if "as_path_churn" in features:
                failure_types.append("routing_instability")

        # Multi-modal patterns
        if correlation.is_multi_modal:
            if "link_degradation" in failure_types and "route_withdrawal" in failure_types:
                return "link_failure"
            if "thermal_issue" in failure_types or "power_issue" in failure_types:
                return "hardware_failure"
            if "resource_exhaustion" in failure_types and "routing_instability" in failure_types:
                return "bgp_process_issue"

        # Default classification
        if failure_types:
            return failure_types[0]

        return "unknown_anomaly"

    def _calculate_combined_confidence(self, correlation: CorrelatedEvent) -> float:
        """Calculate combined confidence from both sources."""
        confidences = []

        if correlation.bgp_event:
            confidences.append(correlation.bgp_event.confidence)

        if correlation.snmp_event:
            confidences.append(correlation.snmp_event.confidence)

        if not confidences:
            return 0.0

        # If multi-modal, boost confidence
        avg_confidence = sum(confidences) / len(confidences)

        if correlation.is_multi_modal:
            # Multi-modal confirmation increases confidence
            avg_confidence = min(avg_confidence * 1.3, 1.0)

        # Factor in correlation strength
        combined = avg_confidence * (0.7 + 0.3 * correlation.correlation_strength)

        return min(combined, 1.0)

    def _classify_bgp_severity(self, confidence: float, detected_series: List[str]) -> str:
        """Classify severity of BGP anomaly."""
        if confidence > 0.85:
            return "critical"
        elif confidence > 0.7:
            return "error"
        elif confidence > 0.5:
            return "warning"
        else:
            return "info"

    def _generate_enriched_alert(
        self, correlation: CorrelatedEvent, triage_result: TriageResult
    ) -> EnrichedAlert:
        """Generate final enriched alert with all context."""
        # Classify alert type and root cause
        alert_type = self._classify_failure_type(correlation)
        probable_cause = self._infer_root_cause(correlation, triage_result)

        # Gather supporting evidence
        evidence = self._gather_supporting_evidence(correlation)

        # Calculate combined confidence
        confidence = self._calculate_combined_confidence(correlation)

        # Generate alert ID
        alert_id = f"alert-{int(correlation.timestamp)}-{triage_result.severity}"

        # Determine escalation need
        escalation_required = triage_result.criticality.priority in ["P1", "P2"]

        # Estimate resolution time
        resolution_time = self._estimate_resolution_time(
            alert_type, triage_result.criticality.priority
        )

        return EnrichedAlert(
            alert_id=alert_id,
            timestamp=correlation.timestamp,
            correlated_event=correlation,
            triage_result=triage_result,
            alert_type=alert_type,
            severity=triage_result.severity,
            priority=triage_result.criticality.priority,
            confidence=confidence,
            affected_devices=[triage_result.location.device]
            + triage_result.blast_radius.downstream_devices[:3],
            affected_services=triage_result.blast_radius.affected_services,
            blast_radius=triage_result.blast_radius.affected_devices,
            is_spof=triage_result.blast_radius.spof,
            probable_root_cause=probable_cause,
            supporting_evidence=evidence,
            recommended_actions=triage_result.recommended_actions,
            escalation_required=escalation_required,
            estimated_resolution_time=resolution_time,
        )

    def _infer_root_cause(self, correlation: CorrelatedEvent, triage_result: TriageResult) -> str:
        """Infer probable root cause from correlated evidence."""
        failure_type = self._classify_failure_type(correlation)

        root_causes = {
            "link_failure": f"Physical link failure on {triage_result.location.device}",
            "hardware_failure": f"Hardware failure on {triage_result.location.device}",
            "bgp_process_issue": f"BGP process issue on {triage_result.location.device}",
            "link_degradation": f"Link degradation on {triage_result.location.interface or 'unknown interface'}",
            "thermal_issue": f"Thermal shutdown imminent on {triage_result.location.device}",
            "power_issue": f"Power supply failure on {triage_result.location.device}",
            "resource_exhaustion": f"Resource exhaustion on {triage_result.location.device}",
            "route_withdrawal": f"Route withdrawal from {triage_result.location.bgp_peer or 'peer'}",
            "routing_instability": f"Routing instability at {triage_result.location.device}",
        }

        return root_causes.get(failure_type, f"Anomaly detected at {triage_result.location.device}")

    def _gather_supporting_evidence(self, correlation: CorrelatedEvent) -> List[str]:
        """Gather supporting evidence from correlated events."""
        evidence = []

        if correlation.bgp_event:
            evidence.append(
                f"BGP: {', '.join(correlation.bgp_event.affected_features)} "
                f"(confidence: {correlation.bgp_event.confidence:.2f})"
            )

        if correlation.snmp_event:
            top_features = correlation.snmp_event.affected_features[:3]
            evidence.append(
                f"SNMP: {', '.join(top_features)} "
                f"(confidence: {correlation.snmp_event.confidence:.2f})"
            )

        if correlation.is_multi_modal:
            evidence.append(
                f"Multi-modal confirmation (correlation: {correlation.correlation_strength:.2f})"
            )

        return evidence

    def _estimate_resolution_time(self, alert_type: str, priority: str) -> str:
        """Estimate resolution time based on alert type and priority."""
        base_times = {
            "link_failure": "30-60 minutes",
            "hardware_failure": "1-4 hours",
            "bgp_process_issue": "15-30 minutes",
            "link_degradation": "30-60 minutes",
            "thermal_issue": "1-2 hours",
            "power_issue": "2-4 hours",
            "resource_exhaustion": "15-30 minutes",
        }

        base_time = base_times.get(alert_type, "30-60 minutes")

        if priority == "P1":
            return f"{base_time} (URGENT)"
        else:
            return base_time

    def get_statistics(self) -> Dict[str, Any]:
        """Get correlation statistics."""
        return {
            **self.stats,
            "recent_bgp_events": len(self.recent_bgp_events),
            "recent_snmp_events": len(self.recent_snmp_events),
            "pending_correlations": len(self.processed_correlations),
            "correlation_rate": (
                self.stats["correlated_events"]
                / max(1, self.stats["bgp_events"] + self.stats["snmp_events"])
            ),
            "multi_modal_rate": (
                self.stats["multi_modal_confirmations"] / max(1, self.stats["correlated_events"])
            ),
        }

    def print_statistics(self):
        """Print correlation statistics."""
        stats = self.get_statistics()

        print("=" * 80)
        print("  Multimodal Correlation Agent Statistics")
        print("=" * 80)
        print(f"BGP Events:                 {stats['bgp_events']}")
        print(f"SNMP Events:                {stats['snmp_events']}")
        print(f"Correlated Events:          {stats['correlated_events']}")
        print(f"Multi-modal Confirmations:  {stats['multi_modal_confirmations']}")
        print(f"False Positives Suppressed: {stats['false_positives_suppressed']}")
        print(f"Alerts Generated:           {stats['alerts_generated']}")
        print()
        print(f"Correlation Rate:           {stats['correlation_rate']:.1%}")
        print(f"Multi-modal Rate:           {stats['multi_modal_rate']:.1%}")
        print()
        print(f"Recent BGP Events:          {stats['recent_bgp_events']}")
        print(f"Recent SNMP Events:         {stats['recent_snmp_events']}")
        print("=" * 80)
