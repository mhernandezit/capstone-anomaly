# Getting Started: Evaluation Framework

## What We're Testing

Your **production ML pipeline** from `src/integrated_multimodal_pipeline.py`:
- ✅ **Matrix Profile** (stumpy) for BGP time-series anomaly detection
- ✅ **Isolation Forest** (sklearn) for SNMP outlier detection  
- ✅ **Multi-modal fusion** to reduce false positives
- ✅ **Topology-aware triage** for failure localization

## Why Simulators?

Simulators provide controlled, reproducible test scenarios with fixed random seeds. The ML algorithms (Matrix Profile, Isolation Forest) process data format and patterns, making simulated BGP UPDATEs functionally equivalent to production data for algorithm validation.

## Installation

First, install the package in editable mode:

```bash
pip install -e .
```

This sets up all Python imports correctly.

## Quick Start (30 seconds)

```bash
# 1. Start NATS
docker compose up -d nats

# 2. Run quick validation
python evaluation/quick_validation.py

# 3. Check alerts (if generated)
cat data/alerts/alerts_log.jsonl
```

## Full Evaluation (5 minutes)

```bash
# Run all 7 scenarios
python evaluation/run_evaluation.py

# Calculate metrics for paper
python evaluation/analyze_results.py

# Generate plots
python evaluation/generate_paper_plots.py
```

## Expected Outputs

```
data/evaluation/
├─ alerts/
│  ├─ link_failure.jsonl
│  ├─ bgp_flapping.jsonl
│  ├─ hardware_degradation.jsonl
│  ├─ server_failure.jsonl
│  ├─ route_leak.jsonl
│  ├─ mass_withdrawal.jsonl
│  └─ cascading_failure.jsonl
│
├─ metrics/
│  ├─ summary.json          # F1, Precision, Recall per scenario
│  ├─ detection_delays.json  # Mean, median, p95, p99 delays
│  └─ localization.json      # Hit@1, Hit@3, Hit@5
│
└─ plots/
   ├─ precision_recall_curve.png
   ├─ detection_delay_histogram.png
   ├─ f1_by_scenario.png
   └─ confusion_matrix.png
```

## What Gets Validated

| Component | Test Coverage |
|-----------|---------------|
| Matrix Profile BGP detection | ✅ 7 scenarios with varying BGP patterns |
| Isolation Forest SNMP detection | ✅ 98% baseline noise + anomalies |
| Multi-modal fusion | ✅ Tests BGP-only, SNMP-only, and correlated |
| Topology triage | ✅ Severity by device role (spine/tor/edge) |
| Alert deduplication | ✅ Cooldown logic tested |
| Detection speed | ✅ Measured delay from injection to alert |
| Localization accuracy | ✅ Hit@k calculated against ground truth |

## Next Steps

1. **Today**: Create BGP simulator + wire production pipeline
2. **Today**: Implement 7 scenarios
3. **Today**: Run evaluation, get F1/delay/Hit@k
4. **Tomorrow**: Generate plots for paper
5. **Tomorrow**: Update paper Analysis section with metrics
6. **Presentation day**: Live demo with pre-generated results

## Time Estimate

- Simulator + pipeline wiring: **1 hour**
- 7 scenarios implementation: **2 hours**  
- Full evaluation run: **5 minutes**
- Metrics analysis: **15 minutes**
- Plot generation: **30 minutes**

**Total: ~4 hours to complete paper-ready results**
