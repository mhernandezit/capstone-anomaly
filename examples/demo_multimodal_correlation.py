#!/usr/bin/env python3
"""
Multimodal Correlation Demo - Interactive Demonstration

A simplified, visual demonstration of the multimodal correlation agent.
This shows how the system:
1. Detects anomalies in both BGP and SNMP data
2. Correlates events across modalities
3. Provides enriched context with topology awareness
4. Generates actionable recommendations

Usage:
    python examples/demo_multimodal_correlation.py
    python examples/demo_multimodal_correlation.py --scenario hardware_failure
"""

import time

import numpy as np

from anomaly_detection.correlation import MultiModalCorrelator
from anomaly_detection.models import IsolationForestDetector, MatrixProfileDetector
from anomaly_detection.simulators.multimodal_simulator import MultiModalSimulator
from anomaly_detection.utils import FeatureBin

print("=" * 80)
print("  Multimodal Correlation Agent - Interactive Demo")
print("=" * 80)
print()
print("This demo shows how the correlation agent combines detections from:")
print("  [1] Matrix Profile (BGP anomaly detection)")
print("  [2] Isolation Forest (SNMP anomaly detection)")
print("  [3] Topology-aware triage (impact assessment)")
print()
print("Result: Enriched alerts with root cause, impact, and recommendations")
print("=" * 80)
print()

# Initialize components
print("[INIT] Initializing system components...")

# Simulator
simulator = MultiModalSimulator(topology_path="evaluation/topology.yml", bin_seconds=30)
print(f"  [OK] Simulator ready ({len(simulator.devices)} devices)")

# BGP detector
bgp_detector = MatrixProfileDetector(
    window_bins=64, series_keys=["wdr_total", "ann_total", "as_path_churn"], discord_threshold=2.5
)
print("  [OK] BGP Matrix Profile detector ready")

# SNMP detector
snmp_detector = IsolationForestDetector(n_estimators=150, contamination=0.02)
try:
    snmp_detector.load_model("data/isolation_forest_model_tuned.pkl")
    print("  [OK] SNMP Isolation Forest detector ready (pre-trained)")
except Exception:
    # Quick train
    print("  [INFO] Training Isolation Forest...")
    training_data = []
    for i in range(250):
        snmp_data = simulator.generate_normal_snmp_data("training")
        feature_names = sorted(snmp_data.keys())
        feature_vector = np.array([snmp_data[k] for k in feature_names])
        training_data.append(feature_vector)

    snmp_detector.fit(np.array(training_data), feature_names)
    print("  [OK] SNMP Isolation Forest detector ready (trained)")

# Correlator
correlator = MultiModalCorrelator(
    topology_path="evaluation/topology.yml",
    roles_config_path="config/roles.yml",
    correlation_window=60.0,
)
print("  [OK] Correlation agent ready")
print()

# Demonstration scenarios
scenarios = [
    {
        "name": "Link Failure on Spine",
        "type": "link_failure",
        "device": "spine-01",
        "description": "Physical link failure causing interface errors and route withdrawals",
        "expected": "Both BGP and SNMP should detect; High severity due to spine role",
    },
    {
        "name": "Router Overload on Edge",
        "type": "router_overload",
        "device": "edge-01",
        "description": "CPU/memory exhaustion causing routing instability",
        "expected": "Both pipelines detect; Critical due to edge router role",
    },
    {
        "name": "Hardware Failure on ToR",
        "type": "hardware_failure",
        "device": "tor-01",
        "description": "Thermal/power issue leading to device instability",
        "expected": "Strong SNMP signal; Moderate BGP impact",
    },
]

print("=" * 80)
print("  Available Scenarios")
print("=" * 80)
for i, scenario in enumerate(scenarios, 1):
    print(f"{i}. {scenario['name']}")
    print(f"   {scenario['description']}")
    print(f"   Expected: {scenario['expected']}")
    print()

# Run first scenario
selected_scenario = scenarios[0]

print("=" * 80)
print(f"  Running: {selected_scenario['name']}")
print("=" * 80)
print()

# Inject failure
event = simulator.inject_failure(
    event_type=selected_scenario["type"],
    device=selected_scenario["device"],
    duration=90.0,
    severity="high",
)

print("[FAILURE INJECTED]")
print(f"  Type: {event.event_type}")
print(f"  Device: {event.device}")
print(f"  Expected BGP anomaly: {event.should_trigger_bgp}")
print(f"  Expected SNMP anomaly: {event.should_trigger_snmp}")
print()

# Process multiple time bins
print("=" * 80)
print("  Processing Time Bins")
print("=" * 80)
print()

alerts_generated = []

for bin_idx in range(5):
    print(f"[BIN {bin_idx + 1}/5] Time: T+{bin_idx * 30}s")
    print("-" * 40)

    current_time = time.time()
    bin_start = current_time - 30
    bin_end = current_time

    # Generate BGP data
    bgp_data = simulator.generate_bgp_data_with_event(event.device)

    # Process through Matrix Profile
    feature_bin = FeatureBin(
        bin_start=int(bin_start), bin_end=int(bin_end), totals=bgp_data, peers={}
    )
    bgp_result = bgp_detector.update(feature_bin)

    # Display BGP result
    if bgp_result["is_anomaly"]:
        print("  [BGP] ANOMALY DETECTED")
        print(f"    Confidence: {bgp_result['anomaly_confidence']:.2f}")
        print(f"    Series: {', '.join(bgp_result['detected_series'])}")

        # Ingest to correlator
        alert = correlator.ingest_bgp_anomaly(
            timestamp=bin_start,
            confidence=bgp_result["anomaly_confidence"],
            detected_series=bgp_result["detected_series"],
            peer=event.device,
            raw_data=bgp_result,
        )
        if alert:
            alerts_generated.append(alert)
    else:
        print("  [BGP] Normal")

    # Generate SNMP data
    snmp_data = simulator.generate_snmp_data_with_event(event.device)
    feature_names = sorted(snmp_data.keys())
    feature_vector = np.array([snmp_data[k] for k in feature_names]).reshape(1, -1)

    # Process through Isolation Forest
    snmp_result = snmp_detector.predict(
        feature_vector, timestamp=current_time, feature_names=feature_names
    )

    # Display SNMP result
    if snmp_result.is_anomaly:
        print("  [SNMP] ANOMALY DETECTED")
        print(f"    Confidence: {snmp_result.confidence:.2f}")
        print(f"    Severity: {snmp_result.severity}")
        print(f"    Features: {', '.join(snmp_result.affected_features[:3])}")

        # Ingest to correlator
        alert = correlator.ingest_snmp_anomaly(
            timestamp=current_time,
            confidence=snmp_result.confidence,
            severity=snmp_result.severity,
            device=event.device,
            affected_features=snmp_result.affected_features,
        )
        if alert:
            alerts_generated.append(alert)
    else:
        print("  [SNMP] Normal")

    print()

# Display enriched alerts
print("=" * 80)
print("  Enriched Alerts Generated")
print("=" * 80)
print()

if not alerts_generated:
    print("[INFO] No correlated alerts generated (anomalies may be below threshold)")
    print()
else:
    for i, alert in enumerate(alerts_generated, 1):
        print(f"[ALERT {i}/{len(alerts_generated)}] {alert.alert_id}")
        print("-" * 80)
        print()

        # Header
        print(f"Alert Type: {alert.alert_type}")
        print(f"Severity: {alert.severity.upper()} | Priority: {alert.priority}")
        print(f"Confidence: {alert.confidence:.2%}")
        print()

        # Correlation
        print("CORRELATION:")
        print(f"  Multi-modal: {'YES' if alert.correlated_event.is_multi_modal else 'No'}")
        print(f"  Sources: {', '.join([s.upper() for s in alert.correlated_event.modalities])}")
        print(f"  Strength: {alert.correlated_event.correlation_strength:.2f}")
        print()

        # Topology
        print("TOPOLOGY ANALYSIS:")
        print(f"  Device: {alert.triage_result.location.device}")
        print(f"  Role: {alert.triage_result.location.topology_role}")
        if alert.triage_result.location.interface:
            print(f"  Interface: {alert.triage_result.location.interface}")
        print(f"  Criticality: {alert.triage_result.criticality.score:.1f}/10")
        print()

        # Impact
        print("IMPACT ASSESSMENT:")
        print(f"  Affected devices: {alert.blast_radius}")
        print(f"  Services: {', '.join(alert.affected_services)}")
        print(f"  Failure domain: {alert.triage_result.blast_radius.failure_domain}")
        if alert.is_spof:
            print("  [WARNING] Single Point of Failure - No redundancy!")
        else:
            print("  Redundancy: Available")
        print()

        # Root cause
        print("ROOT CAUSE:")
        print(f"  {alert.probable_root_cause}")
        print()
        print("  Evidence:")
        for evidence in alert.supporting_evidence:
            print(f"    - {evidence}")
        print()

        # Actions
        print("RECOMMENDED ACTIONS:")
        for j, action in enumerate(alert.recommended_actions, 1):
            print(f"  [{j}] {action.get('action', 'N/A')}")
            if "command" in action:
                print(f"      $ {action['command']}")
            if "estimated_time" in action:
                print(f"      Time: {action['estimated_time']}")
        print()

        # Escalation
        if alert.escalation_required:
            print("[ESCALATION] Contact on-call engineer immediately")
            print()

        print(f"Estimated resolution: {alert.estimated_resolution_time}")
        print()
        print("=" * 80)
        print()

# Final statistics
print("=" * 80)
print("  Correlation Agent Statistics")
print("=" * 80)
print()
correlator.print_statistics()

print()
print("=" * 80)
print("  Demo Complete")
print("=" * 80)
print()
print("Key Takeaways:")
print("  [1] Individual pipelines detect anomalies in their domain (BGP or SNMP)")
print("  [2] Correlation agent combines signals for higher confidence")
print("  [3] Topology awareness provides impact and blast radius assessment")
print("  [4] Enriched alerts include root cause and actionable recommendations")
print()
print("This transforms raw anomaly detections into operational intelligence.")
print("=" * 80)
