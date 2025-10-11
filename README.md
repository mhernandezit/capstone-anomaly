# Machine Learning for Network Anomaly and Failure Detection

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A capstone project implementing a multimodal machine learning system for network anomaly detection and failure localization using BGP routing data and SNMP metrics.

## Overview

This project addresses the challenges of network monitoring in large-scale environments where traditional threshold-based alerting produces excessive false positives and lacks context for failure localization. The system uses unsupervised machine learning techniques to detect anomalies across multiple data sources and an intelligent correlation agent to provide enriched, actionable alerts.

### Key Features

- **Dual-Pipeline Anomaly Detection**
  - Matrix Profile analysis for BGP time-series anomalies
  - Isolation Forest for SNMP hardware and environmental anomalies
  
- **Multimodal Correlation Agent**
  - Temporal and spatial event correlation
  - Cross-modal validation to reduce false positives
  - Topology-aware impact assessment
  
- **Enriched Alerting**
  - Root cause inference from multi-modal evidence
  - Blast radius calculation and SPOF detection
  - Criticality scoring (0-10) and priority classification (P1/P2/P3)
  - Actionable recommendations with CLI commands

- **Comprehensive Failure Coverage**
  - Link failures
  - Router overload
  - Optical degradation
  - Hardware failures
  - Route leaks
  - BGP flapping

## Architecture

```
Network Events (BGP, SNMP)
         |
         v
  [Data Collection]
    BGP: Simulators (Python)
    SNMP: Simulators (Python)
         |
         +------------------+
         |                  |
    BGP Updates        SNMP Metrics
         |                  |
         v                  v
  [Matrix Profile]   [Isolation Forest]
   (BGP Pipeline)     (SNMP Pipeline)
         |                  |
    BGP Anomaly        SNMP Anomaly
         |                  |
         +--------+---------+
                  |
                  v
       [Correlation Agent]
          - Correlates events
          - Topology triage
          - Impact assessment
                  |
                  v
         [Enriched Alerts]
       - Root cause
       - Impact details
       - Actions
```

## Quick Start

### Prerequisites

- Python 3.8+
- pip (Python package manager)

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/your-username/capstone-anomaly.git
   cd capstone-anomaly
   ```

2. Install the package in editable mode (recommended):
  
```bash
   pip install -e .
   ```
  
   This installs all dependencies and sets up the package for development.
  
   Alternatively, install just the dependencies:
  
```bash
   pip install -r requirements.txt
   ```

1. Run the quick demonstration:
  
   ```bash
python examples/demo_multimodal_correlation.py

   ```

**Note**: The editable install (`pip install -e .`) is recommended as it allows you to import from `src` anywhere in the project without path manipulation.

### Running Scenarios

Test different failure scenarios:

```bash
# Link failure (both BGP and SNMP affected)
python examples/run_multimodal_correlation.py --scenario link_failure

# Router overload (CPU/memory + routing issues)
python examples/run_multimodal_correlation.py --scenario router_overload

# Hardware failure (thermal/power + BGP session loss)
python examples/run_multimodal_correlation.py --scenario hardware_failure
```

See [QUICK_START_MULTIMODAL.md](QUICK_START_MULTIMODAL.md) for detailed usage instructions.

## Project Structure

```
capstone-anomaly/
├── src/                          # Core source code
│   ├── correlation/              # Multimodal correlation agent
│   ├── models/                   # ML detectors (Matrix Profile, Isolation Forest)
│   ├── features/                 # Feature extraction (BGP, SNMP)
│   ├── simulators/               # Failure scenario simulators
│   ├── triage/                   # Topology-aware triage system
│   ├── alerting/                 # Alert generation and logging
│   └── utils/                    # Shared utilities and schemas
├── examples/                     # Demo and integration scripts
├── tests/                        # Test suite
├── docs/                         # Documentation
│   ├── MULTIMODAL_CORRELATION.md  # Comprehensive architecture guide
│   ├── presentations/            # Academic presentation materials
│   └── papers/                   # Research papers
├── config/                       # Configuration files
├── data/                         # Models and results
└── evaluation/                   # Topology and evaluation scripts
```

## Core Components

### 1. Matrix Profile Detector (BGP)
- Detects anomalies in BGP update streams
- Uses time-series discord detection
- Identifies route withdrawals, announcements, and AS path churn
- Location: `src/models/cpu_mp_detector.py`

### 2. Isolation Forest Detector (SNMP)
- Detects anomalies in SNMP metrics
- 19-dimensional feature space (interface, CPU, memory, temperature, etc.)
- Pre-trained model with 5% false positive rate, 100% detection rate
- Location: `src/models/isolation_forest_detector.py`

### 3. Multimodal Correlation Agent
- Correlates anomalies across BGP and SNMP pipelines
- Temporal correlation (60-second window)
- Spatial correlation (same device/interface/peer)
- Multi-modal validation (higher confidence when both sources agree)
- Location: `src/correlation/multimodal_correlator.py`

### 4. Topology Triage System
- Maps devices to roles (spine, edge, ToR, etc.)
- Calculates blast radius
- Detects single points of failure (SPOF)
- Assigns criticality scores and priorities
- Location: `src/triage/topology_triage.py`

## Documentation

- **[QUICK_START_MULTIMODAL.md](QUICK_START_MULTIMODAL.md)** - Quick start guide for the correlation system
- **[README_MULTIMODAL.md](README_MULTIMODAL.md)** - Overview of the multimodal system
- **[docs/MULTIMODAL_CORRELATION.md](docs/MULTIMODAL_CORRELATION.md)** - Comprehensive architecture and API documentation
- **[MULTIMODAL_SYSTEM_SUMMARY.md](MULTIMODAL_SYSTEM_SUMMARY.md)** - Implementation summary
- **[CHANGELOG.md](CHANGELOG.md)** - Project changelog

## Performance Metrics

Based on realistic failure scenario testing:

- **Correlation Rate**: 60-80% (events successfully correlated)
- **Multi-modal Confirmation**: 40-60% (events confirmed by both sources)
- **False Positive Suppression**: 30-50% (reduction through cross-validation)
- **Alert Confidence**: 0.75-0.95 (combined confidence scores)

## Example Output

When both pipelines detect anomalies, the system generates enriched alerts:

```
[ENRICHED ALERT] Multimodal Correlation Detected
Alert Type: link_failure
Severity: CRITICAL | Priority: P1
Confidence: 92%

CORRELATION:
  Multi-modal: YES
  Sources: BGP, SNMP
  Strength: 0.87

TOPOLOGY ANALYSIS:
  Device: spine-01
  Role: spine
  Criticality: 9.0/10

IMPACT ASSESSMENT:
  Affected devices: 15
  Services: east_west_traffic
  SPOF: YES - CRITICAL!

ROOT CAUSE:
  Physical link failure on spine-01
  Evidence:
    - BGP: wdr_total, as_path_churn (0.89)
    - SNMP: interface_error_rate (0.95)

RECOMMENDED ACTIONS:
  1. Check physical link status
  2. Verify BGP session health
  3. Escalate immediately
```

## Academic Context

This is a capstone project for the CUNY School of Professional Studies IS 499 Information Systems Capstone course. The work builds on research in:

- Matrix Profile data mining for BGP anomaly detection (Scott et al., 2024)
- Machine learning for SNMP-MIB anomaly detection (Manna & Alkasassbeh, 2019)
- ML-based action recommenders for Network Operation Centers (Mohammed et al., 2021)
- Semantic feature selection in network telemetry (Feltin et al., 2023)

See [docs/presentations/final_project_draft.pdf](docs/presentations/final_project_draft.pdf) for the complete academic paper.

## Integration with Existing Infrastructure

The correlation agent can be integrated with production monitoring systems:

```python
from src.correlation.multimodal_correlator import MultiModalCorrelator

# Initialize
correlator = MultiModalCorrelator(
    topology_path="path/to/topology.yml",
    roles_config_path="path/to/roles.yml"
)

# In your BGP monitoring pipeline:
if bgp_anomaly_detected:
    alert = correlator.ingest_bgp_anomaly(
        timestamp=current_time,
        confidence=detection_confidence,
        detected_series=['wdr_total', 'as_path_churn'],
        peer='spine-01'
    )
    if alert:
        send_to_operations(alert)

# In your SNMP monitoring pipeline:
if snmp_anomaly_detected:
    alert = correlator.ingest_snmp_anomaly(
        timestamp=current_time,
        confidence=detection_confidence,
        severity='critical',
        device='spine-01',
        affected_features=['interface_error_rate']
    )
    if alert:
        send_to_operations(alert)
```

## Configuration

### Topology Configuration
Define your network topology in YAML format:

```yaml
devices:
  spine-01:
    role: spine
    asn: 65001
    priority: critical
    blast_radius: 15

bgp_peers:
  - [spine-01, tor-01]
  - [spine-01, edge-01]
```

### Role Mapping
Map device identifiers to roles in `config/configs/roles.yml`:

```yaml
roles:
  spine-01: spine
  edge-01: edge
  tor-01: tor
```

## Testing

Run the test suite:

```bash
# Run all tests
python -m pytest tests/

# Run specific test categories
python -m pytest tests/test_isolation_forest.py
python -m pytest tests/test_correlation.py
```

## Contributing

This is an academic project completed for CUNY SPS. For questions or collaboration:

- **Author**: Michael Hernandez
- **Course**: IS 499 Information Systems Capstone
- **Institution**: CUNY School of Professional Studies
- **Professor**: John Bouma

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Citation

If you use this work in your research, please cite:

```bibtex
@mastersthesis{hernandez2025multimodal,
  author = {Hernandez, Michael},
  title = {Machine Learning for Network Anomaly and Failure Detection},
  school = {CUNY School of Professional Studies},
  year = {2025},
  type = {Capstone Project}
}
```

## Acknowledgments

- Professor John Bouma for guidance and feedback
- CUNY School of Professional Studies for academic support
- Research community for foundational work in network anomaly detection
- Open source projects: stumpy (Matrix Profile), scikit-learn (Isolation Forest), NATS

## References

Key references that informed this work:

1. Scott, B., Johnstone, M. N., Szewczyk, P., & Richardson, S. (2024). Matrix Profile data mining for BGP anomaly detection. *Computer Networks*, 242, 110257.

2. Manna, A., & Alkasassbeh, M. (2019). Detecting network anomalies using machine learning and SNMP-MIB IP group data. *arXiv preprint arXiv:1906.00863*.

3. Mohammed, S. A., Mohammed, A. R., Côté, D., & Shirmohammadi, S. (2021). A machine-learning-based action recommender for Network Operation Centers. *IEEE Transactions on Network and Service Management*, 18(3), 2702-2713.

4. Feltin, T., Cordero Fuertes, J. A., Brockners, F., & Clausen, T. H. (2023). Understanding Semantics in Feature Selection for Fault Diagnosis in Network Telemetry Data. *NOMS 2023-2023 IEEE/IFIP Network Operations and Management Symposium*, 1-9.

For the complete list of references, see [docs/presentations/final_project_draft.pdf](docs/presentations/final_project_draft.pdf).

---

**Project Status**: ✅ Complete (October 2025)

For detailed technical documentation, see [docs/MULTIMODAL_CORRELATION.md](docs/MULTIMODAL_CORRELATION.md).
