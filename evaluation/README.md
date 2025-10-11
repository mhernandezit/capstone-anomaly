# Evaluation Framework

## Purpose

This directory contains the comprehensive evaluation suite for the multi-modal network anomaly detection system. It tests the **production pipeline** (`src/integrated_multimodal_pipeline.py`) with Matrix Profile and Isolation Forest detectors against realistic failure scenarios.

## Evaluation Approach

The evaluation uses realistic simulated data to test the **production pipeline**. The ML algorithms (Matrix Profile, Isolation Forest) process data format and patterns, making simulated BGP UPDATEs functionally equivalent to production data for algorithm validation. This approach provides controlled, reproducible test scenarios with fixed random seeds.

## Architecture

```
evaluation/
├─ scenarios/                    # 7 failure scenarios
│  ├─ 01_link_failure.py        # P1 Critical: Spine-ToR link down
│  ├─ 02_bgp_flapping.py        # P1 Critical: Route instability
│  ├─ 03_hardware_degradation.py # P2 Warning: Fan/temp issues
│  ├─ 04_server_failure.py      # P3 Info: Single host down
│  ├─ 05_route_leak.py          # P1 Critical: Prefix leak
│  ├─ 06_mass_withdrawal.py     # P1 Critical: Large outage
│  └─ 07_cascading_failure.py   # P1 Critical: Multi-device
│
├─ bgp_simulator.py             # Generates realistic BGP UPDATEs
├─ snmp_baseline.py             # Continuous SNMP noise (98%)
├─ run_evaluation.py            # Orchestrates all scenarios
├─ analyze_results.py           # Calculates F1, delay, Hit@k
└─ generate_paper_plots.py      # Creates figures for paper
```

## Key Features

1. **Production Pipeline**: Uses `src/integrated_multimodal_pipeline.py` with real Matrix Profile and Isolation Forest detectors
2. **Realistic Data**: BGP UPDATE messages match BMP format, SNMP metrics include 98% baseline noise
3. **Comprehensive Scenarios**: 7 failure types covering link, BGP, hardware, and cascading failures
4. **Quantitative Metrics**: F1, Precision, Recall, Detection Delay, Hit@k for paper
5. **Reproducible**: Fixed random seeds, documented parameters

## Prerequisites

Install the package in editable mode:

```bash
pip install -e .
```

This sets up all imports correctly without path hacks.

## Running Evaluation

```bash
# Start NATS
docker compose up -d nats

# Run full evaluation (7 scenarios)
python evaluation/run_evaluation.py

# Analyze results
python evaluation/analyze_results.py

# Generate paper plots (if available)
python evaluation/generate_paper_plots.py
```

## Expected Outputs

- `data/evaluation/alerts/` - Alert logs per scenario
- `data/evaluation/metrics/` - F1, delay, Hit@k per scenario
- `data/evaluation/plots/` - Figures for paper (precision-recall curves, delay histograms)

## Evaluation Framework Advantages

| Aspect | Benefit |
|--------|---------|
| ML Algorithm | Matrix Profile + Isolation Forest with production pipeline |
| Data Format | BMP-format BGP UPDATEs, realistic SNMP metrics |
| Noise Handling | 98% baseline noise + 2% anomalies |
| Topology Awareness | Simulated topology with device roles |
| Metrics Generation | F1, Detection Delay, Hit@k with controlled scenarios |
| Reproducibility | Fixed random seeds for consistent results |
| Platform Support | Cross-platform (Windows/Linux/Mac) |
| Algorithm Validation | Realistic data patterns for algorithm correctness |

**Key Benefit**: Controlled scenarios with reproducible metrics for academic evaluation and algorithm validation.
