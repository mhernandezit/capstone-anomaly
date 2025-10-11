# Multimodal Correlation Agent

## Overview

The Multimodal Correlation Agent is the intelligence layer that sits behind the BGP (Matrix Profile) and SNMP (Isolation Forest) anomaly detection pipelines. It correlates anomaly detections across both modalities, uses topology data to assess impact, and provides enriched alerts with actionable recommendations for network operators.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Network Data Sources                              │
├──────────────────────────────┬──────────────────────────────────────┤
│       BGP Updates            │         SNMP Metrics                 │
│   (BMP, Route Changes)       │   (Counters, Status, Errors)         │
└───────────────┬──────────────┴──────────────────┬───────────────────┘
                │                                  │
                v                                  v
         ┌──────────────┐                  ┌──────────────┐
         │Matrix Profile│                  │  Isolation   │
         │   Detector   │                  │    Forest    │
         │    (BGP)     │                  │   (SNMP)     │
         └──────┬───────┘                  └──────┬───────┘
                │                                  │
                │    BGP Anomaly                   │    SNMP Anomaly
                │    (confidence,                  │    (confidence,
                │     series,                      │     features,
                │     peer)                        │     device)
                │                                  │
                └──────────────┬───────────────────┘
                               │
                               v
                    ┌──────────────────────┐
                    │  Correlation Agent   │
                    │                      │
                    │  - Event correlation │
                    │  - Topology triage   │
                    │  - Impact assessment │
                    │  - Root cause        │
                    └──────────┬───────────┘
                               │
                               v
                    ┌──────────────────────┐
                    │   Enriched Alerts    │
                    │                      │
                    │  - Multi-modal       │
                    │  - Topology-aware    │
                    │  - Actionable        │
                    └──────────────────────┘
```

## Key Capabilities

### 1. Event Correlation

The correlation agent combines anomaly detections from both pipelines:

- **Temporal Correlation**: Events occurring close in time (within correlation window)
- **Spatial Correlation**: Events affecting the same device, interface, or BGP peer
- **Cross-Modal Validation**: Anomalies confirmed by both sources have higher confidence

Benefits:
- Reduces false positives (single-source anomalies may not alert)
- Increases confidence in real failures (multi-modal confirmation)
- Provides comprehensive view of network health

### 2. Topology-Aware Triage

Uses network topology data to assess:

- **Device Role**: Spine, edge, ToR, leaf (criticality varies by role)
- **Blast Radius**: Number of affected devices and services
- **Failure Domain**: Scope of impact (rack, datacenter, network-wide)
- **SPOF Detection**: Identifies single points of failure
- **Redundancy Status**: Determines if backup paths exist

### 3. Impact Assessment

Calculates criticality score (0-10) based on:

- Topology role (spine/edge = higher criticality)
- Blast radius (more affected devices = higher)
- Single point of failure (SPOF = critical)
- Service impact (connectivity vs. application)

Priority mapping:
- P1 (Critical): Score >= 8.0, immediate action required
- P2 (High): Score >= 5.0, urgent action needed
- P3 (Medium): Score < 5.0, monitor and investigate

### 4. Root Cause Inference

Infers probable root cause from correlated evidence:

- **Link Failure**: High interface errors (SNMP) + route withdrawals (BGP)
- **Hardware Failure**: Temperature/power issues (SNMP) + BGP session loss
- **Router Overload**: CPU/memory exhaustion (SNMP) + routing instability (BGP)
- **Optical Degradation**: Interface errors (SNMP) + packet loss
- **BGP Process Issue**: Resource exhaustion + AS path churn

### 5. Actionable Recommendations

Generates operator-friendly recommendations:

- Specific troubleshooting steps
- CLI commands to run
- Estimated resolution time
- Escalation guidance

## Components

### MultiModalCorrelator

Main correlation agent class.

**Key Methods:**

- `ingest_bgp_anomaly()`: Receives BGP anomaly from Matrix Profile
- `ingest_snmp_anomaly()`: Receives SNMP anomaly from Isolation Forest
- `get_statistics()`: Returns correlation metrics
- `print_statistics()`: Displays agent statistics

**Configuration:**

```python
correlator = MultiModalCorrelator(
    topology_path="evaluation/topology.yml",
    roles_config_path="config/configs/roles.yml",
    correlation_window=60.0,  # seconds
    min_correlation_confidence=0.6
)
```

### MultiModalSimulator

Generates realistic failure scenarios with correlated BGP and SNMP events.

**Failure Scenarios:**

1. `link_failure`: Physical link failure (both modalities)
2. `router_overload`: CPU/memory exhaustion (both modalities)
3. `optical_degradation`: Transceiver issues (primarily SNMP)
4. `hardware_failure`: Thermal/power failure (both modalities)
5. `route_leak`: Massive BGP announcements (primarily BGP)
6. `bgp_flapping`: Session instability (both modalities)

**Usage:**

```python
simulator = MultiModalSimulator(topology_path="evaluation/topology.yml")

# Inject failure
event = simulator.inject_failure(
    event_type='link_failure',
    device='spine-01',
    duration=60.0,
    severity='high'
)

# Generate data with failure effects
bgp_data = simulator.generate_bgp_data_with_event(device)
snmp_data = simulator.generate_snmp_data_with_event(device)
```

### EnrichedAlert

Final alert structure with full context.

**Fields:**

- `alert_id`: Unique identifier
- `timestamp`: Alert timestamp
- `alert_type`: Classified failure type
- `severity`: info, warning, error, critical
- `priority`: P1, P2, P3
- `confidence`: Combined confidence (0-1)
- `correlated_event`: Source events and correlation metrics
- `triage_result`: Topology analysis results
- `probable_root_cause`: Inferred root cause
- `supporting_evidence`: List of evidence
- `recommended_actions`: Operator actions
- `blast_radius`: Number of affected devices
- `is_spof`: Single point of failure flag
- `escalation_required`: Boolean flag
- `estimated_resolution_time`: Time estimate

## Usage

### Running the Demo

Quick demonstration of the correlation agent:

```bash
python examples/demo_multimodal_correlation.py
```

This runs a pre-configured scenario and shows:
- Anomaly detection in both pipelines
- Event correlation
- Enriched alert generation
- Impact assessment

### Running Full Integration

Complete system with custom scenarios:

```bash
# Link failure on spine-01
python examples/run_multimodal_correlation.py --scenario link_failure --device spine-01

# Router overload with 15 time bins
python examples/run_multimodal_correlation.py --scenario router_overload --bins 15

# Hardware failure with custom duration
python examples/run_multimodal_correlation.py --scenario hardware_failure --duration 120
```

### Integrating with Existing Pipelines

To integrate the correlation agent with your pipelines:

```python
from correlation.multimodal_correlator import MultiModalCorrelator

# Initialize
correlator = MultiModalCorrelator(
    topology_path="evaluation/topology.yml",
    roles_config_path="config/configs/roles.yml"
)

# In your BGP pipeline (Matrix Profile detection):
if bgp_anomaly_detected:
    alert = correlator.ingest_bgp_anomaly(
        timestamp=current_time,
        confidence=mp_result['anomaly_confidence'],
        detected_series=mp_result['detected_series'],
        peer=peer_identifier,
        raw_data=mp_result
    )
    
    if alert:
        # Process enriched alert
        handle_alert(alert)

# In your SNMP pipeline (Isolation Forest detection):
if snmp_anomaly_detected:
    alert = correlator.ingest_snmp_anomaly(
        timestamp=current_time,
        confidence=if_result.confidence,
        severity=if_result.severity,
        device=device_id,
        affected_features=if_result.affected_features,
        raw_data={'anomaly_score': if_result.anomaly_score}
    )
    
    if alert:
        # Process enriched alert
        handle_alert(alert)
```

## Configuration

### Topology Configuration

Define your network topology in YAML:

```yaml
# evaluation/topology.yml
devices:
  spine-01:
    role: spine
    asn: 65001
    priority: critical
    blast_radius: 15
    
  tor-01:
    role: tor
    asn: 65002
    priority: high
    blast_radius: 8
    uplinks: [spine-01, spine-02]

bgp_peers:
  - [spine-01, tor-01]
  - [spine-01, edge-01]
```

### Role Configuration

Map devices to roles:

```yaml
# config/configs/roles.yml
roles:
  10.0.0.1: rr
  10.0.1.1: spine
  10.0.2.1: tor
  spine-01: spine
  edge-01: edge
```

### Correlation Parameters

Tune correlation behavior:

- `correlation_window`: Time window for correlating events (default: 60s)
- `min_correlation_confidence`: Minimum confidence threshold (default: 0.6)

Smaller window = stricter temporal correlation
Higher confidence = fewer but higher-quality alerts

## Alert Example

Example of an enriched alert:

```
[ENRICHED ALERT] Multimodal Correlation Detected
================================================================================
Alert ID: alert-1728583920-critical
Timestamp: 2025-10-10 14:32:00
Type: link_failure
Severity: CRITICAL | Priority: P1
Confidence: 0.92

Correlation:
  Multi-modal: True
  Sources: BGP, SNMP
  Correlation strength: 0.87

Topology Analysis:
  Device: spine-01
  Role: spine
  Criticality: 9.0/10

Impact Assessment:
  Affected devices: 15
  Affected services: east_west_traffic
  SPOF: YES - CRITICAL!
  Failure domain: datacenter

Root Cause Analysis:
  Probable cause: Physical link failure on spine-01
  Supporting evidence:
    - BGP: wdr_total, as_path_churn (confidence: 0.89)
    - SNMP: interface_error_rate, interface_flap_count (confidence: 0.95)
    - Multi-modal confirmation (correlation: 0.87)

Recommended Actions:
  1. Check physical link status on spine-01
     Command: show interface eth1 status
     Time: 2 minutes
  2. Verify BGP session health
     Command: show bgp neighbor all
     Time: 1 minute
  3. Escalate to on-call network engineer
     Contact: NOC hotline
     Time: Immediate

[ESCALATION REQUIRED] Contact on-call engineer immediately!

Estimated resolution time: 30-60 minutes (URGENT)
================================================================================
```

## Performance

### Correlation Metrics

Track agent performance:

```python
stats = correlator.get_statistics()

# Key metrics:
- bgp_events: Total BGP anomalies received
- snmp_events: Total SNMP anomalies received
- correlated_events: Events successfully correlated
- multi_modal_confirmations: Events confirmed by both sources
- false_positives_suppressed: Single-source anomalies filtered
- alerts_generated: Final enriched alerts produced

# Rates:
- correlation_rate: Percentage of events correlated
- multi_modal_rate: Percentage of correlations that are multi-modal
```

### Typical Results

With properly tuned detectors:

- Correlation rate: 60-80% (most anomalies find correlated events)
- Multi-modal rate: 40-60% (many failures affect both BGP and SNMP)
- False positive suppression: 30-50% (significant reduction)
- Alert confidence: 0.75-0.95 (high confidence in correlated alerts)

## Best Practices

### 1. Tune Individual Pipelines First

Ensure Matrix Profile and Isolation Forest are well-tuned before enabling correlation:

- BGP: Adjust discord threshold (typically 2.0-3.0)
- SNMP: Tune contamination parameter (typically 0.01-0.05)

### 2. Set Appropriate Correlation Window

- Too short: Miss related events
- Too long: False correlations
- Recommended: 30-90 seconds for most networks

### 3. Configure Topology Accurately

Accurate topology is critical for impact assessment:

- Keep device roles updated
- Map all BGP peering relationships
- Define uplink relationships
- Set realistic blast radius estimates

### 4. Monitor Correlation Metrics

Track correlation statistics to identify issues:

- Low correlation rate: Widen correlation window
- High false positive suppression: May be too conservative
- Low multi-modal rate: Check if both pipelines are working

### 5. Customize Actions for Your Environment

Update recommended actions to match your operational procedures:

- Add your specific CLI commands
- Include your contact information
- Adjust estimated resolution times
- Add runbook links

## Troubleshooting

### No Alerts Generated

Possible causes:

1. Correlation confidence too high: Lower `min_correlation_confidence`
2. Individual detectors not triggering: Check detector thresholds
3. Correlation window too narrow: Increase `correlation_window`
4. Events not temporally aligned: Check simulator timing

### Too Many Alerts

Possible causes:

1. Correlation confidence too low: Raise `min_correlation_confidence`
2. Individual detectors too sensitive: Tune detector parameters
3. Correlation window too wide: Decrease `correlation_window`

### Incorrect Impact Assessment

Possible causes:

1. Topology configuration outdated: Update topology.yml
2. Role mappings incorrect: Update roles.yml
3. Blast radius estimates wrong: Adjust device configurations

## Future Enhancements

Potential improvements:

1. **Graph-Based Correlation**: Use topology graph for better spatial correlation
2. **Temporal Patterns**: Learn temporal patterns of failures
3. **Confidence Calibration**: Calibrate confidence scores with ground truth
4. **Automated Actions**: Trigger automated remediation for known failures
5. **Historical Context**: Use past failures to improve root cause inference
6. **Multi-Site Correlation**: Correlate events across data centers
7. **Feedback Loop**: Incorporate operator feedback to improve classifications

## References

- Isolation Forest implementation: `src/models/isolation_forest_detector.py`
- Matrix Profile implementation: `src/models/cpu_mp_detector.py`
- Topology triage system: `src/triage/topology_triage.py`
- Feature extraction: `src/features/snmp_features.py`, `src/features/bgp_features.py`

## Support

For questions or issues:

1. Check logs for error messages
2. Verify topology and role configurations
3. Test individual pipelines separately
4. Run demo script to validate setup
5. Check correlation statistics for anomalies
