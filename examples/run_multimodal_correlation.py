#!/usr/bin/env python3
"""
Multimodal Correlation System - Full Integration

This script demonstrates the complete multimodal anomaly detection and correlation system:

1. Multimodal Simulator - Generates realistic BGP and SNMP events
2. Matrix Profile Pipeline - Detects BGP anomalies
3. Isolation Forest Pipeline - Detects SNMP anomalies
4. Correlation Agent - Correlates events and provides enriched context

The system shows how raw anomaly detections from individual pipelines are transformed
into actionable operational intelligence through correlation and topology awareness.
"""

import argparse
import logging
import time

import numpy as np

from anomaly_detection.correlation import MultiModalCorrelator
from anomaly_detection.models import IsolationForestDetector, MatrixProfileDetector
from anomaly_detection.simulators.multimodal_simulator import MultiModalSimulator
from anomaly_detection.utils import FeatureBin

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class MultiModalCorrelationSystem:
    """
    Complete multimodal correlation system integrating:
    - BGP Matrix Profile detection
    - SNMP Isolation Forest detection
    - Multimodal correlation agent
    """

    def __init__(
        self,
        topology_path: str = "evaluation/topology.yml",
        roles_config_path: str = "config/configs/roles.yml",
        use_pretrained_if: bool = True,
    ):
        """Initialize the complete system."""
        logger.info("=" * 80)
        logger.info("  Multimodal Correlation System - Initializing")
        logger.info("=" * 80)

        # Initialize simulator
        logger.info("[1/4] Initializing multimodal simulator...")
        self.simulator = MultiModalSimulator(topology_path=topology_path, bin_seconds=30)
        logger.info(f"  [OK] Loaded topology with {len(self.simulator.devices)} devices")

        # Initialize Matrix Profile detector (BGP)
        logger.info("[2/4] Initializing Matrix Profile detector (BGP)...")
        self.bgp_detector = MatrixProfileDetector(
            window_bins=64,
            series_keys=["wdr_total", "ann_total", "as_path_churn"],
            discord_threshold=2.5,
        )
        logger.info("  [OK] Matrix Profile detector ready")

        # Initialize Isolation Forest detector (SNMP)
        logger.info("[3/4] Initializing Isolation Forest detector (SNMP)...")
        self.snmp_detector = IsolationForestDetector(n_estimators=150, contamination=0.02)

        # Load pretrained model or train quickly
        if use_pretrained_if:
            try:
                self.snmp_detector.load_model("data/isolation_forest_model_tuned.pkl")
                logger.info("  [OK] Loaded pre-trained Isolation Forest model")
            except Exception:
                logger.info("  [INFO] Pre-trained model not found, training new model...")
                self._quick_train_isolation_forest()
        else:
            self._quick_train_isolation_forest()

        # Initialize correlation agent
        logger.info("[4/4] Initializing multimodal correlation agent...")
        self.correlator = MultiModalCorrelator(
            topology_path=topology_path,
            roles_config_path=roles_config_path,
            correlation_window=60.0,
            min_correlation_confidence=0.5,
        )
        logger.info("  [OK] Correlation agent ready")

        # Statistics
        self.stats = {
            "bins_processed": 0,
            "bgp_anomalies": 0,
            "snmp_anomalies": 0,
            "correlated_alerts": 0,
            "start_time": time.time(),
        }

        logger.info("=" * 80)
        logger.info("  System Ready")
        logger.info("=" * 80)
        print()

    def _quick_train_isolation_forest(self):
        """Quickly train Isolation Forest with synthetic normal data."""
        logger.info("  [INFO] Generating training data...")

        # Generate 250 samples of normal SNMP data
        training_data = []
        for i in range(250):
            snmp_data = self.simulator.generate_normal_snmp_data("training-device")
            # Convert to feature vector (ordered by feature names)
            feature_vector = self._snmp_dict_to_vector(snmp_data)
            training_data.append(feature_vector)

        training_data = np.array(training_data)
        feature_names = list(self.simulator.snmp_baseline.keys())

        logger.info(f"  [INFO] Training on {len(training_data)} normal samples...")
        self.snmp_detector.fit(training_data, feature_names)
        logger.info("  [OK] Isolation Forest trained")

    def _snmp_dict_to_vector(self, snmp_data: dict) -> np.ndarray:
        """Convert SNMP dict to ordered feature vector."""
        # Ensure consistent ordering
        feature_names = sorted(snmp_data.keys())
        return np.array([snmp_data[key] for key in feature_names])

    def run_scenario(
        self, scenario_type: str, device: str = None, duration: float = 60.0, num_bins: int = 10
    ):
        """
        Run a failure scenario through the complete system.

        Args:
            scenario_type: Type of failure (link_failure, router_overload, etc.)
            device: Target device (random if None)
            duration: Failure duration in seconds
            num_bins: Number of time bins to process
        """
        logger.info("=" * 80)
        logger.info(f"  Running Scenario: {scenario_type}")
        logger.info("=" * 80)

        # Inject failure
        event = self.simulator.inject_failure(
            event_type=scenario_type, device=device, duration=duration, severity="high"
        )

        logger.info("Injected Failure:")
        logger.info(f"  Type: {event.event_type}")
        logger.info(f"  Device: {event.device}")
        logger.info(f"  Duration: {duration}s")
        logger.info(f"  Should trigger BGP: {event.should_trigger_bgp}")
        logger.info(f"  Should trigger SNMP: {event.should_trigger_snmp}")
        print()

        # Process time bins
        logger.info(f"Processing {num_bins} time bins (30s each)...")
        print()

        for bin_idx in range(num_bins):
            current_time = time.time()
            bin_start = current_time - 30
            bin_end = current_time

            logger.info(f"[BIN {bin_idx + 1}/{num_bins}] Time: {bin_start:.0f} - {bin_end:.0f}")

            # Generate and process BGP data
            bgp_data = self.simulator.generate_bgp_data_with_event(event.device)
            self._process_bgp_bin(
                device=event.device, bin_start=bin_start, bin_end=bin_end, data=bgp_data
            )

            # Generate and process SNMP data
            snmp_data = self.simulator.generate_snmp_data_with_event(event.device)
            self._process_snmp_bin(
                device=event.device, timestamp=current_time, data=snmp_data
            )

            # Check for correlation
            self._check_correlation(bin_idx + 1)

            print()

            # Update stats
            self.stats["bins_processed"] += 1

            # Sleep to simulate real-time (optional)
            # time.sleep(1)

        # Final statistics
        self._print_final_stats()

        # Clear event
        self.simulator.clear_event()

    def _process_bgp_bin(self, device: str, bin_start: float, bin_end: float, data: dict) -> dict:
        """Process BGP data through Matrix Profile detector."""
        # Create feature bin
        feature_bin = FeatureBin(
            bin_start=bin_start, bin_end=bin_end, totals=data, by_peer={}, by_prefix={}
        )

        # Run through Matrix Profile
        mp_result = self.bgp_detector.update(feature_bin)

        # Check for anomaly
        if mp_result["is_anomaly"]:
            self.stats["bgp_anomalies"] += 1

            logger.info("  [BGP] Anomaly detected!")
            logger.info(f"    Confidence: {mp_result['anomaly_confidence']:.2f}")
            logger.info(f"    Detected series: {', '.join(mp_result['detected_series'])}")

            # Ingest into correlator
            alert = self.correlator.ingest_bgp_anomaly(
                timestamp=bin_start,
                confidence=mp_result["anomaly_confidence"],
                detected_series=mp_result["detected_series"],
                peer=device,
                raw_data=mp_result,
            )

            if alert:
                self.stats["correlated_alerts"] += 1
                self._print_enriched_alert(alert)
        else:
            logger.info("  [BGP] Normal operation")

        return mp_result

    def _process_snmp_bin(self, device: str, timestamp: float, data: dict) -> dict:
        """Process SNMP data through Isolation Forest detector."""
        # Convert to feature vector
        feature_vector = self._snmp_dict_to_vector(data)
        feature_vector = feature_vector.reshape(1, -1)
        feature_names = sorted(data.keys())

        # Run through Isolation Forest
        if_result = self.snmp_detector.predict(
            feature_vector, timestamp=timestamp, feature_names=feature_names
        )

        # Check for anomaly
        if if_result.is_anomaly:
            self.stats["snmp_anomalies"] += 1

            logger.info("  [SNMP] Anomaly detected!")
            logger.info(f"    Confidence: {if_result.confidence:.2f}")
            logger.info(f"    Severity: {if_result.severity}")
            logger.info(f"    Top features: {', '.join(if_result.affected_features[:3])}")

            # Ingest into correlator
            alert = self.correlator.ingest_snmp_anomaly(
                timestamp=timestamp,
                confidence=if_result.confidence,
                severity=if_result.severity,
                device=device,
                affected_features=if_result.affected_features,
                raw_data={
                    "anomaly_score": if_result.anomaly_score,
                    "feature_importance": if_result.feature_importance,
                },
            )

            if alert:
                self.stats["correlated_alerts"] += 1
                self._print_enriched_alert(alert)
        else:
            logger.info("  [SNMP] Normal operation")

        return if_result

    def _check_correlation(self, bin_number: int):
        """Check correlation status."""
        stats = self.correlator.get_statistics()

        if stats["recent_bgp_events"] > 0 or stats["recent_snmp_events"] > 0:
            logger.info("  [CORRELATION] Active events in window:")
            logger.info(
                f"    BGP: {stats['recent_bgp_events']}, SNMP: {stats['recent_snmp_events']}"
            )
            logger.info(f"    Correlation rate: {stats['correlation_rate']:.1%}")

    def _print_enriched_alert(self, alert):
        """Print enriched alert with full details."""
        print()
        print("=" * 80)
        print("  [ENRICHED ALERT] Multimodal Correlation Detected")
        print("=" * 80)
        print(f"Alert ID: {alert.alert_id}")
        print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(alert.timestamp))}")
        print(f"Type: {alert.alert_type}")
        print(f"Severity: {alert.severity.upper()} | Priority: {alert.priority}")
        print(f"Confidence: {alert.confidence:.2f}")
        print()

        print("Correlation:")
        print(f"  Multi-modal: {alert.correlated_event.is_multi_modal}")
        print(f"  Sources: {', '.join(alert.correlated_event.modalities)}")
        print(f"  Correlation strength: {alert.correlated_event.correlation_strength:.2f}")
        print()

        print("Topology Analysis:")
        print(f"  Device: {alert.triage_result.location.device}")
        print(f"  Role: {alert.triage_result.location.topology_role}")
        print(f"  Criticality: {alert.triage_result.criticality.score:.1f}/10")
        print()

        print("Impact Assessment:")
        print(f"  Affected devices: {alert.blast_radius}")
        print(f"  Affected services: {', '.join(alert.affected_services)}")
        print(f"  SPOF: {'YES - CRITICAL!' if alert.is_spof else 'No'}")
        print(f"  Failure domain: {alert.triage_result.blast_radius.failure_domain}")
        print()

        print("Root Cause Analysis:")
        print(f"  Probable cause: {alert.probable_root_cause}")
        print("  Supporting evidence:")
        for evidence in alert.supporting_evidence:
            print(f"    - {evidence}")
        print()

        print("Recommended Actions:")
        for i, action in enumerate(alert.recommended_actions, 1):
            print(f"  {i}. {action.get('action', 'N/A')}")
            if "command" in action:
                print(f"     Command: {action['command']}")
            if "estimated_time" in action:
                print(f"     Time: {action['estimated_time']}")
        print()

        if alert.escalation_required:
            print("[ESCALATION REQUIRED] Contact on-call engineer immediately!")
            print()

        print(f"Estimated resolution time: {alert.estimated_resolution_time}")
        print("=" * 80)
        print()

    def _print_final_stats(self):
        """Print final statistics."""
        runtime = time.time() - self.stats["start_time"]

        print()
        print("=" * 80)
        print("  Final Statistics")
        print("=" * 80)
        print(f"Runtime: {runtime:.1f}s")
        print(f"Bins processed: {self.stats['bins_processed']}")
        print(f"BGP anomalies: {self.stats['bgp_anomalies']}")
        print(f"SNMP anomalies: {self.stats['snmp_anomalies']}")
        print(f"Correlated alerts: {self.stats['correlated_alerts']}")
        print()

        # Correlation agent stats
        self.correlator.print_statistics()
        print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run multimodal correlation system demo")
    parser.add_argument(
        "--scenario",
        type=str,
        default="link_failure",
        choices=[
            "link_failure",
            "router_overload",
            "optical_degradation",
            "hardware_failure",
            "route_leak",
            "bgp_flapping",
        ],
        help="Failure scenario to simulate",
    )
    parser.add_argument(
        "--device", type=str, default=None, help="Target device (random if not specified)"
    )
    parser.add_argument("--duration", type=float, default=60.0, help="Failure duration in seconds")
    parser.add_argument("--bins", type=int, default=10, help="Number of time bins to process")

    args = parser.parse_args()

    # Initialize system
    system = MultiModalCorrelationSystem()

    # Run scenario
    system.run_scenario(
        scenario_type=args.scenario, device=args.device, duration=args.duration, num_bins=args.bins
    )


if __name__ == "__main__":
    main()
