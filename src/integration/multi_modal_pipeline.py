#!/usr/bin/env python3
"""
Multi-Modal Network Failure Detection Pipeline

This module integrates BGP, syslog, and SNMP data sources for comprehensive
network failure detection. It addresses the professor's feedback to expand
beyond just BGP events to include hardware failures, cable issues, and
broader routing events.

Key Features:
- Multi-modal data fusion (BGP + Syslog + SNMP)
- Hardware failure detection and simulation
- Environmental anomaly detection
- Comprehensive failure taxonomy
- Real-time streaming analysis
"""

import asyncio
import logging
import json
import time
import yaml
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import numpy as np

# Import existing components
from src.features.stream_features import FeatureAggregator
from src.features.snmp_features import SNMPFeatureExtractor
from src.models.mp_detector import MPDetector
from src.triage.impact import ImpactScorer
from src.simulators.snmp_simulator import SNMPFailureSimulator
from src.alerting.alert_manager import AlertManager

# Import NATS client
import nats

logger = logging.getLogger(__name__)


@dataclass
class MultiModalAlert:
    """Represents a multi-modal network failure alert."""

    timestamp: float
    alert_id: str
    severity: str
    confidence: float

    # Failure classification
    failure_type: str  # 'bgp', 'hardware', 'environmental', 'multi_modal'
    failure_subtype: str  # 'optical_degradation', 'memory_pressure', etc.

    # Location information
    affected_devices: List[str]
    suspected_location: str  # 'spine', 'tor', 'edge', 'server'

    # Contributing signals
    bgp_contribution: float
    syslog_contribution: float
    snmp_contribution: float

    # Feature importance
    top_features: List[Dict[str, float]]

    # Correlation analysis
    temporal_correlation: float
    spatial_correlation: float

    # Recommended actions
    recommended_actions: List[str]

    # Raw data references
    bgp_events: List[Dict[str, Any]]
    syslog_events: List[Dict[str, Any]]
    snmp_metrics: List[Dict[str, Any]]


class MultiModalPipeline:
    """
    Comprehensive multi-modal network failure detection pipeline.

    This pipeline integrates BGP updates, syslog messages, and SNMP metrics
    to detect a wide range of network failures including:
    - BGP routing anomalies
    - Hardware component failures
    - Environmental issues
    - Cable/optical problems
    - System performance degradation
    """

    def __init__(self, config_path: str = "configs/multi_modal_config.yml"):
        """Initialize the multi-modal pipeline."""
        self.config = self._load_config(config_path)
        self.running = False

        # Data processors
        self.bgp_aggregator = FeatureAggregator(bin_seconds=self.config.get("bin_seconds", 60))
        self.snmp_extractor = SNMPFeatureExtractor(bin_seconds=self.config.get("bin_seconds", 60))

        # ML models
        self.bgp_detector = MPDetector(window_bins=self.config.get("window_bins", 64))

        # Impact assessment
        roles_config = self.config.get("roles", {})
        self.impact_scorer = ImpactScorer(roles_config)

        # SNMP simulator for hardware failures
        self.snmp_simulator = SNMPFailureSimulator(
            config_path=self.config.get("snmp_config_path", "configs/snmp_config.yml")
        )

        # Communication
        self.nats_client = None
        self.alert_manager = AlertManager()

        # State tracking
        self.recent_alerts: List[MultiModalAlert] = []
        self.correlation_window = self.config.get("correlation_window_seconds", 120)

        # Statistics
        self.stats = {
            "bgp_events_processed": 0,
            "syslog_events_processed": 0,
            "snmp_metrics_processed": 0,
            "alerts_generated": 0,
            "multi_modal_detections": 0,
            "start_time": time.time(),
        }

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load pipeline configuration."""
        try:
            with open(config_path, "r") as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning(f"Config file {config_path} not found, using defaults")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "bin_seconds": 60,
            "window_bins": 64,
            "correlation_window_seconds": 120,
            "nats_url": "nats://127.0.0.1:4222",
            "alert_thresholds": {"bgp_only": 0.7, "hardware_only": 0.6, "multi_modal": 0.5},
            "failure_taxonomy": {
                "bgp": ["route_leak", "hijack", "convergence_delay"],
                "hardware": ["optical_degradation", "memory_pressure", "thermal_runaway"],
                "environmental": ["power_instability", "cooling_failure"],
                "cable": ["intermittent_connection", "signal_degradation"],
            },
        }

    async def initialize(self):
        """Initialize the pipeline components."""
        logger.info("Initializing multi-modal pipeline")

        # Connect to NATS
        self.nats_client = await nats.connect(self.config.get("nats_url", "nats://127.0.0.1:4222"))

        # Initialize SNMP simulator
        await self.snmp_simulator.connect_nats()

        # Set up subscriptions
        await self._setup_subscriptions()

        logger.info("Multi-modal pipeline initialized successfully")

    async def _setup_subscriptions(self):
        """Set up NATS subscriptions for different data sources."""

        # BGP updates subscription
        await self.nats_client.subscribe("bgp.updates", cb=self._handle_bgp_update)

        # Syslog messages subscription
        await self.nats_client.subscribe("syslog.messages", cb=self._handle_syslog_message)

        # SNMP metrics subscription
        await self.nats_client.subscribe("snmp.metrics", cb=self._handle_snmp_metric)

        logger.info("Subscribed to all data source channels")

    async def _handle_bgp_update(self, msg):
        """Handle incoming BGP update messages."""
        try:
            bgp_data = json.loads(msg.data.decode())

            # Add to BGP aggregator
            self.bgp_aggregator.add_update(bgp_data)

            # Also add to SNMP extractor for correlation
            self.snmp_extractor.add_bgp_event(bgp_data)

            self.stats["bgp_events_processed"] += 1

            # Check for completed bins
            await self._process_completed_bins()

        except Exception as e:
            logger.error(f"Error processing BGP update: {e}")

    async def _handle_syslog_message(self, msg):
        """Handle incoming syslog messages."""
        try:
            syslog_data = json.loads(msg.data.decode())

            # Add to SNMP extractor for correlation
            self.snmp_extractor.add_syslog_event(syslog_data)

            self.stats["syslog_events_processed"] += 1

        except Exception as e:
            logger.error(f"Error processing syslog message: {e}")

    async def _handle_snmp_metric(self, msg):
        """Handle incoming SNMP metrics."""
        try:
            snmp_data = json.loads(msg.data.decode())

            # Add to SNMP extractor
            self.snmp_extractor.add_snmp_metric(snmp_data)

            self.stats["snmp_metrics_processed"] += 1

            # Check for completed bins
            await self._process_completed_bins()

        except Exception as e:
            logger.error(f"Error processing SNMP metric: {e}")

    async def _process_completed_bins(self):
        """Process completed feature bins from all sources."""

        # Check BGP bins
        while self.bgp_aggregator.has_closed_bin():
            bgp_bin = self.bgp_aggregator.pop_closed_bin()
            await self._analyze_multi_modal_features(bgp_bin=bgp_bin)

        # Check SNMP bins
        while self.snmp_extractor.has_completed_bin():
            snmp_bin = self.snmp_extractor.pop_completed_bin()
            await self._analyze_multi_modal_features(snmp_bin=snmp_bin)

    async def _analyze_multi_modal_features(self, bgp_bin=None, snmp_bin=None):
        """Analyze features from multiple modalities."""

        current_time = time.time()

        # Collect features from all available sources
        feature_sources = {}

        if bgp_bin:
            # Run BGP anomaly detection
            bgp_score = self.bgp_detector.update(bgp_bin)
            feature_sources["bgp"] = {
                "bin": bgp_bin,
                "anomaly_score": bgp_score,
                "features": self._extract_bgp_features(bgp_bin),
            }

        if snmp_bin:
            # Run SNMP anomaly analysis
            snmp_score = self._calculate_snmp_anomaly_score(snmp_bin)
            feature_sources["snmp"] = {
                "bin": snmp_bin,
                "anomaly_score": snmp_score,
                "features": self.snmp_extractor.get_feature_vector(snmp_bin),
            }

        # Multi-modal fusion and analysis
        if len(feature_sources) >= 1:  # At least one source has data
            await self._perform_multi_modal_analysis(feature_sources, current_time)

    def _extract_bgp_features(self, bgp_bin) -> np.ndarray:
        """Extract feature vector from BGP bin."""
        # Convert BGP bin to feature vector (simplified)
        return np.array(
            [
                bgp_bin.wdr_total,
                bgp_bin.ann_total,
                bgp_bin.as_path_churn,
                bgp_bin.peer_diversity,
                getattr(bgp_bin, "burstiness", 0.0),
            ]
        )

    def _calculate_snmp_anomaly_score(self, snmp_bin) -> float:
        """Calculate anomaly score for SNMP bin."""
        # Simple anomaly scoring based on threshold violations and severity
        base_score = 0.0

        # Threshold violations contribute to score
        if snmp_bin.threshold_violations > 0:
            base_score += min(snmp_bin.threshold_violations * 0.1, 0.5)

        # Severity escalations are more serious
        if snmp_bin.severity_escalations > 0:
            base_score += min(snmp_bin.severity_escalations * 0.2, 0.7)

        # Environmental stress
        base_score += snmp_bin.environmental_stress_score * 0.3

        # Multi-device correlation indicates widespread issues
        base_score += snmp_bin.multi_device_correlation * 0.4

        return min(base_score, 1.0)

    async def _perform_multi_modal_analysis(
        self, feature_sources: Dict[str, Any], current_time: float
    ):
        """Perform comprehensive multi-modal analysis."""

        # Calculate overall anomaly confidence
        anomaly_scores = [source["anomaly_score"] for source in feature_sources.values()]
        max_score = max(anomaly_scores)
        mean_score = np.mean(anomaly_scores)

        # Determine if this constitutes an alert
        alert_thresholds = self.config.get("alert_thresholds", {})

        should_alert = False
        alert_type = "info"

        if len(feature_sources) > 1 and mean_score > alert_thresholds.get("multi_modal", 0.5):
            should_alert = True
            alert_type = "multi_modal"
            self.stats["multi_modal_detections"] += 1
        elif "bgp" in feature_sources and feature_sources["bgp"][
            "anomaly_score"
        ] > alert_thresholds.get("bgp_only", 0.7):
            should_alert = True
            alert_type = "bgp"
        elif "snmp" in feature_sources and feature_sources["snmp"][
            "anomaly_score"
        ] > alert_thresholds.get("hardware_only", 0.6):
            should_alert = True
            alert_type = "hardware"

        if should_alert:
            alert = await self._generate_multi_modal_alert(
                feature_sources, alert_type, max_score, current_time
            )

            if alert:
                await self._publish_alert(alert)
                self.recent_alerts.append(alert)
                self.stats["alerts_generated"] += 1

                logger.info(
                    f"Generated {alert_type} alert: "
                    f"confidence={alert.confidence:.2f}, "
                    f"devices={alert.affected_devices}, "
                    f"failure_type={alert.failure_subtype}"
                )

    async def _generate_multi_modal_alert(
        self, feature_sources: Dict[str, Any], alert_type: str, confidence: float, timestamp: float
    ) -> Optional[MultiModalAlert]:
        """Generate a comprehensive multi-modal alert."""

        # Analyze failure type and subtype
        failure_type, failure_subtype = self._classify_failure(feature_sources)

        # Determine affected devices
        affected_devices = self._identify_affected_devices(feature_sources)

        # Localize the failure
        suspected_location = self._localize_failure(feature_sources, affected_devices)

        # Calculate signal contributions
        bgp_contrib = feature_sources.get("bgp", {}).get("anomaly_score", 0.0)
        snmp_contrib = feature_sources.get("snmp", {}).get("anomaly_score", 0.0)
        syslog_contrib = 0.0  # TODO: Add syslog-specific analysis

        # Identify top contributing features
        top_features = self._identify_top_features(feature_sources)

        # Calculate correlations
        temporal_corr = self._calculate_temporal_correlation(feature_sources, timestamp)
        spatial_corr = self._calculate_spatial_correlation(affected_devices)

        # Generate recommended actions
        recommended_actions = self._generate_recommendations(
            failure_type, failure_subtype, affected_devices
        )

        # Determine severity
        severity = self._determine_severity(confidence, len(affected_devices), failure_type)

        alert = MultiModalAlert(
            timestamp=timestamp,
            alert_id=f"alert_{int(timestamp)}_{len(self.recent_alerts)}",
            severity=severity,
            confidence=confidence,
            failure_type=failure_type,
            failure_subtype=failure_subtype,
            affected_devices=affected_devices,
            suspected_location=suspected_location,
            bgp_contribution=bgp_contrib,
            syslog_contribution=syslog_contrib,
            snmp_contribution=snmp_contrib,
            top_features=top_features,
            temporal_correlation=temporal_corr,
            spatial_correlation=spatial_corr,
            recommended_actions=recommended_actions,
            bgp_events=self._extract_bgp_events(feature_sources),
            syslog_events=[],  # TODO: Extract syslog events
            snmp_metrics=self._extract_snmp_metrics(feature_sources),
        )

        return alert

    def _classify_failure(self, feature_sources: Dict[str, Any]) -> tuple[str, str]:
        """Classify the type and subtype of failure."""

        # Multi-modal classification logic
        if "snmp" in feature_sources:
            snmp_bin = feature_sources["snmp"]["bin"]

            # Hardware-specific failures
            if snmp_bin.temperature_max > 65:
                return "hardware", "thermal_runaway"
            elif snmp_bin.memory_utilization_max > 85:
                return "hardware", "memory_pressure"
            elif snmp_bin.interface_error_rate > 100:
                return "hardware", "optical_degradation"
            elif snmp_bin.power_stability_score < 0.7:
                return "environmental", "power_instability"
            elif snmp_bin.interface_flap_count > 2:
                return "cable", "intermittent_connection"

        if "bgp" in feature_sources:
            bgp_bin = feature_sources["bgp"]["bin"]

            # BGP-specific failures
            if bgp_bin.wdr_total > bgp_bin.ann_total * 2:
                return "bgp", "route_withdrawal_storm"
            elif bgp_bin.as_path_churn > 50:
                return "bgp", "convergence_delay"

        # Default classification
        return "unknown", "unclassified"

    def _identify_affected_devices(self, feature_sources: Dict[str, Any]) -> List[str]:
        """Identify devices affected by the failure."""
        affected = set()

        if "snmp" in feature_sources:
            snmp_bin = feature_sources["snmp"]["bin"]
            # Extract device IDs from SNMP data (simplified)
            affected.add(f"device_count_{snmp_bin.device_count}")

        if "bgp" in feature_sources:
            bgp_bin = feature_sources["bgp"]["bin"]
            # Extract peer information (simplified)
            affected.add(f"bgp_peers_{bgp_bin.peer_diversity}")

        return list(affected)

    def _localize_failure(
        self, feature_sources: Dict[str, Any], affected_devices: List[str]
    ) -> str:
        """Localize the failure to a network tier."""

        # Simple localization logic
        if "snmp" in feature_sources:
            snmp_bin = feature_sources["snmp"]["bin"]
            if snmp_bin.multi_device_correlation > 0.7:
                return "spine"  # Widespread impact suggests spine issue
            elif snmp_bin.device_count > 2:
                return "tor"  # Multiple devices suggests ToR issue
            else:
                return "edge"  # Single device suggests edge issue

        return "unknown"

    def _identify_top_features(self, feature_sources: Dict[str, Any]) -> List[Dict[str, float]]:
        """Identify the top contributing features."""
        top_features = []

        if "snmp" in feature_sources:
            snmp_bin = feature_sources["snmp"]["bin"]
            features = {
                "temperature_max": snmp_bin.temperature_max,
                "cpu_utilization_max": snmp_bin.cpu_utilization_max,
                "interface_error_rate": snmp_bin.interface_error_rate,
                "threshold_violations": snmp_bin.threshold_violations,
                "environmental_stress": snmp_bin.environmental_stress_score,
            }

            # Sort by value and take top 3
            sorted_features = sorted(features.items(), key=lambda x: x[1], reverse=True)
            top_features.extend([{"feature": k, "value": v} for k, v in sorted_features[:3]])

        return top_features

    def _calculate_temporal_correlation(
        self, feature_sources: Dict[str, Any], timestamp: float
    ) -> float:
        """Calculate temporal correlation with recent events."""
        # Look for recent alerts within correlation window
        recent_threshold = timestamp - self.correlation_window
        recent_alerts = [
            alert for alert in self.recent_alerts if alert.timestamp > recent_threshold
        ]

        # Simple correlation based on recent alert count
        return min(len(recent_alerts) / 5.0, 1.0)

    def _calculate_spatial_correlation(self, affected_devices: List[str]) -> float:
        """Calculate spatial correlation across devices."""
        # Simple correlation based on number of affected devices
        return min(len(affected_devices) / 10.0, 1.0)

    def _generate_recommendations(
        self, failure_type: str, failure_subtype: str, affected_devices: List[str]
    ) -> List[str]:
        """Generate recommended actions based on failure analysis."""
        recommendations = []

        if failure_type == "hardware":
            if failure_subtype == "thermal_runaway":
                recommendations.extend(
                    [
                        "Check cooling system and airflow",
                        "Verify fan operation and speeds",
                        "Inspect for blocked air vents",
                    ]
                )
            elif failure_subtype == "memory_pressure":
                recommendations.extend(
                    [
                        "Check memory utilization trends",
                        "Look for memory leaks in processes",
                        "Consider memory upgrade if persistent",
                    ]
                )
            elif failure_subtype == "optical_degradation":
                recommendations.extend(
                    [
                        "Check optical power levels",
                        "Inspect fiber connections",
                        "Consider transceiver replacement",
                    ]
                )

        elif failure_type == "environmental":
            recommendations.extend(
                [
                    "Check power supply status",
                    "Verify environmental conditions",
                    "Inspect power distribution",
                ]
            )

        elif failure_type == "cable":
            recommendations.extend(
                ["Check cable connections", "Test cable integrity", "Look for physical damage"]
            )

        elif failure_type == "bgp":
            recommendations.extend(
                ["Check BGP session status", "Verify routing policies", "Look for route flaps"]
            )

        if not recommendations:
            recommendations.append("Investigate affected devices for anomalies")

        return recommendations

    def _determine_severity(self, confidence: float, device_count: int, failure_type: str) -> str:
        """Determine alert severity."""
        if confidence > 0.8 and device_count > 3:
            return "critical"
        elif confidence > 0.6 and device_count > 1:
            return "error"
        elif confidence > 0.4:
            return "warning"
        else:
            return "info"

    def _extract_bgp_events(self, feature_sources: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract BGP events from feature sources."""
        if "bgp" not in feature_sources:
            return []

        bgp_bin = feature_sources["bgp"]["bin"]
        return [
            {
                "bin_start": bgp_bin.bin_start,
                "bin_end": bgp_bin.bin_end,
                "withdrawals": bgp_bin.wdr_total,
                "announcements": bgp_bin.ann_total,
                "as_path_churn": bgp_bin.as_path_churn,
            }
        ]

    def _extract_snmp_metrics(self, feature_sources: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract SNMP metrics from feature sources."""
        if "snmp" not in feature_sources:
            return []

        snmp_bin = feature_sources["snmp"]["bin"]
        return [
            {
                "bin_start": snmp_bin.bin_start,
                "bin_end": snmp_bin.bin_end,
                "device_count": snmp_bin.device_count,
                "temperature_max": snmp_bin.temperature_max,
                "cpu_max": snmp_bin.cpu_utilization_max,
                "threshold_violations": snmp_bin.threshold_violations,
            }
        ]

    async def _publish_alert(self, alert: MultiModalAlert):
        """Publish alert to NATS and alert manager."""
        try:
            # Publish to NATS
            alert_message = json.dumps(asdict(alert), default=str)
            await self.nats_client.publish("alerts.multi_modal", alert_message.encode())

            # Send to alert manager
            await self.alert_manager.process_alert(alert)

        except Exception as e:
            logger.error(f"Error publishing alert: {e}")

    async def start_simulation(self):
        """Start the SNMP failure simulation."""
        logger.info("Starting SNMP failure simulation")

        # Start SNMP simulator in background
        simulation_task = asyncio.create_task(self.snmp_simulator.run_simulation())
        return simulation_task

    async def run_pipeline(self):
        """Run the main pipeline."""
        logger.info("Starting multi-modal pipeline")
        self.running = True

        try:
            await self.initialize()

            # Start SNMP simulation
            await self.start_simulation()

            # Main processing loop
            while self.running:
                # Log statistics periodically
                if (
                    self.stats["bgp_events_processed"] % 100 == 0
                    and self.stats["bgp_events_processed"] > 0
                ):
                    logger.info(f"Pipeline stats: {self.get_pipeline_stats()}")

                await asyncio.sleep(1)

        except KeyboardInterrupt:
            logger.info("Received interrupt, shutting down pipeline")
        except Exception as e:
            logger.error(f"Error in pipeline: {e}")
        finally:
            await self.shutdown()

    async def shutdown(self):
        """Shutdown the pipeline."""
        logger.info("Shutting down multi-modal pipeline")
        self.running = False

        # Stop SNMP simulator
        self.snmp_simulator.stop_simulation()
        await self.snmp_simulator.disconnect_nats()

        # Close NATS connection
        if self.nats_client:
            await self.nats_client.close()

    def get_pipeline_stats(self) -> Dict[str, Any]:
        """Get comprehensive pipeline statistics."""
        runtime = time.time() - self.stats["start_time"]

        return {
            **self.stats,
            "runtime_minutes": runtime / 60,
            "events_per_minute": {
                "bgp": self.stats["bgp_events_processed"] / max(runtime / 60, 1),
                "syslog": self.stats["syslog_events_processed"] / max(runtime / 60, 1),
                "snmp": self.stats["snmp_metrics_processed"] / max(runtime / 60, 1),
            },
            "recent_alerts": len(self.recent_alerts),
            "snmp_simulator_stats": self.snmp_simulator.get_simulation_stats(),
        }


async def main():
    """Main entry point for the multi-modal pipeline."""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    pipeline = MultiModalPipeline()

    try:
        await pipeline.run_pipeline()
    except KeyboardInterrupt:
        logger.info("Shutting down multi-modal pipeline")
    finally:
        await pipeline.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
