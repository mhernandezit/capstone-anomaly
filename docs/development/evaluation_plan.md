# Evaluation Plan

## Overview

This document outlines the evaluation methodology for the multi-modal network anomaly detection system. The evaluation focuses on three key dimensions: detection accuracy, operational efficiency, and system performance.

## Evaluation Metrics

### 1. Detection Accuracy (F1 Score)

**Definition**: Harmonic mean of precision and recall for anomaly detection.

**Formula**:

```
Precision = TP / (TP + FP)
Recall = TP / (TP + FN)
F1 = 2 * (Precision * Recall) / (Precision + Recall)
```

**Ground Truth**:

- Failure injection timestamps from simulated scenarios
- Labeled failures in test scenarios (link failures, route flaps, hardware issues)
- Manual verification logs from test runs

**Computation Method**:

1. Parse alert logs from `data/alerts/` directory
2. Match detected anomalies against ground truth failure timestamps
3. Apply time window (±30 seconds) for matching detected events to actual failures
4. Calculate TP, FP, FN for each failure scenario
5. Aggregate metrics across all test scenarios

**Target Thresholds**:

- Precision: ≥ 90% (minimize false positives)
- Recall: ≥ 85% (catch most failures)
- F1 Score: ≥ 87.5%

**Implementation**:

```python
# src/evaluation/metrics.py
def calculate_f1(alerts_csv, ground_truth_csv, time_window_sec=30):
    """Calculate F1 score with time-windowed matching"""
    # Parse alerts and ground truth
    # Match within time window
    # Return precision, recall, F1
    pass
```

---

### 2. Detection Delay (Latency)

**Definition**: Time elapsed from failure occurrence to alert generation.

**Measurement Points**:

1. **Failure injection timestamp** (t₀): Recorded when test scenario triggers failure
2. **First data observation** (t₁): When failure-related data enters NATS message bus
3. **Anomaly detection** (t₂): When ML model identifies anomaly
4. **Alert generation** (t₃): When confirmed alert is published

**Computation Method**:

```text
Detection Delay = t₃ - t₀
Pipeline Latency = t₃ - t₁
```

**Target Thresholds**:

- **Detection Delay**: ≤ 60 seconds (real-time requirement)
- **Pipeline Latency**: ≤ 30 seconds (processing efficiency)
- **P95 Detection Delay**: ≤ 90 seconds

**Implementation**:

1. Log failure injection timestamps in `data/evaluation/ground_truth.json`
2. Extract alert timestamps from alert logs
3. Calculate per-failure delays
4. Aggregate statistics (mean, median, P95, P99)

**Output Format**:

```json
{
  "scenario": "link_failure_tor1_tor2",
  "failure_time": "2024-10-09T15:30:00Z",
  "first_observation": "2024-10-09T15:30:05Z",
  "detection_time": "2024-10-09T15:30:22Z",
  "alert_time": "2024-10-09T15:30:25Z",
  "detection_delay_sec": 25,
  "pipeline_latency_sec": 20
}
```

---

### 3. Hit@k (Localization Accuracy)

**Definition**: Whether the true failure location appears in the top-k predicted locations from topology-aware triage.

**Variants**:

- **Hit@1**: True location is the #1 prediction (exact match)
- **Hit@3**: True location is in top-3 predictions
- **Hit@5**: True location is in top-5 predictions

**Computation Method**:

1. Parse triage output with ranked device/link predictions
2. Extract ground truth failure location from test scenario metadata
3. Check if ground truth appears in top-k predictions
4. Calculate Hit@k rate across all test scenarios

**Formula**:

```text
Hit@k = (Number of scenarios where true location ∈ top-k predictions) / (Total scenarios)
```

**Target Thresholds**:

- Hit@1: ≥ 70% (accurate pinpointing)
- Hit@3: ≥ 90% (narrow down to few candidates)
- Hit@5: ≥ 95% (comprehensive coverage)

**Implementation**:

```python
# src/evaluation/localization.py
def calculate_hitk(triage_results_csv, ground_truth_csv, k_values=[1, 3, 5]):
    """Calculate Hit@k metrics for failure localization"""
    # Parse triage predictions (ranked list of devices/links)
    # Match against ground truth failure location
    # Return Hit@1, Hit@3, Hit@5 percentages
    pass
```

**Triage Output Format**:

```json
{
  "alert_id": "a123",
  "timestamp": "2024-10-09T15:30:25Z",
  "ranked_predictions": [
    {"device": "tor-01", "link": "eth1", "confidence": 0.92},
    {"device": "spine-01", "link": "eth3", "confidence": 0.78},
    {"device": "tor-02", "link": "eth1", "confidence": 0.65}
  ],
  "ground_truth": {"device": "tor-01", "link": "eth1"}
}
```

---

## Test Scenarios

### Simulated Failure Scenarios

1. **Link Failure**: Simulated link down between ToR and Spine
2. **Route Flapping**: Intermittent BGP session instability
3. **Hardware Degradation**: Simulated interface errors (SNMP counters)
4. **Route Leak**: Unexpected prefix advertisements
5. **Prefix Hijack**: Malicious route announcement
6. **Multi-Device Correlation**: Cascading failures affecting multiple devices
7. **False Positive Test**: Normal network variations (BGP churn, maintenance)

### Data Collection

**During Each Test Scenario**:
1. Record failure injection metadata in `data/evaluation/ground_truth.json`
2. Collect raw telemetry data (BGP updates, SNMP metrics, syslog)
3. Capture ML pipeline logs with timestamps
4. Export alerts to `data/alerts/alerts_log.jsonl`
5. Save triage outputs to `data/triage/triage_results.jsonl`

**Post-Test Analysis**:

```bash
# Run evaluation scripts
python evaluation/analyze_results.py \
  --alerts data/alerts/alerts_log.jsonl \
  --ground-truth data/evaluation/ground_truth.json \
  --triage data/triage/triage_results.jsonl \
  --output data/evaluation/evaluation_report.json
```

---

## Evaluation Timeline

1. **Baseline Collection** (1 hour): Collect normal traffic data with no failures
2. **Individual Failures** (3 hours): Test each scenario independently (7 scenarios × 3 runs)
3. **Multi-Modal Fusion** (1 hour): Test with BGP+SNMP+Syslog vs. single sources
4. **Stress Testing** (1 hour): High-frequency failures, concurrent events
5. **Analysis & Reporting** (2 hours): Generate charts, statistical analysis, write-up

**Total Estimated Time**: 8 hours

---

## Output Artifacts

### 1. Evaluation Report (`results/evaluation_report.json`)

```json
{
  "summary": {
    "f1_score": 0.89,
    "precision": 0.92,
    "recall": 0.87,
    "mean_detection_delay_sec": 28.5,
    "p95_detection_delay_sec": 52.0,
    "hit_at_1": 0.73,
    "hit_at_3": 0.91,
    "hit_at_5": 0.96
  },
  "per_scenario_results": [...]
}
```

### 2. Visualizations

- F1 scores by scenario (bar chart)
- Detection delay distribution (histogram + CDF)
- Hit@k rates comparison (stacked bar)
- ROC curves for anomaly detection
- Confusion matrix for localization

### 3. Statistical Analysis

- Confidence intervals for each metric
- Comparison with baseline (threshold-based monitoring)
- Ablation study: multi-modal vs. single-modal detection

---

## Comparison Baselines

### Traditional Monitoring

- Threshold-based SNMP alerting
- Syslog keyword matching
- BGP route count deviation

### Single-Modal ML

- BGP-only (Matrix Profile alone)
- SNMP-only (Isolation Forest alone)
- Syslog-only (DeepSyslog baseline)

### Multi-Modal (This System)

- BGP + SNMP + Syslog fusion
- Topology-aware triage

**Expected Result**: Multi-modal should improve precision (reduce false positives) while maintaining high recall.

---

## Implementation Checklist

- [ ] Create `src/evaluation/metrics.py` with F1/precision/recall functions
- [ ] Create `src/evaluation/localization.py` with Hit@k functions
- [ ] Add timestamp logging to all pipeline components
- [ ] Implement failure injection metadata logging
- [ ] Create visualization scripts in `src/evaluation/visualize.py`
- [ ] Write end-to-end evaluation script `src/evaluation/calculate_metrics.py`
- [ ] Generate sample ground truth data for validation
- [ ] Document output formats in this file

---

## References

- Mohammed et al. (2021) - NOC operational metrics
- Scott et al. (2024) - BGP anomaly detection evaluation methodology
- Zhou et al. (2022) - DeepSyslog evaluation metrics (precision/recall on log data)
