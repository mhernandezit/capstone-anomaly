# Evaluation Directory Organization

**Last Updated**: October 10, 2025

## Purpose

This directory contains all evaluation and testing infrastructure for the network anomaly detection system. It provides tools for training models, running evaluations, generating test data, and analyzing results.

## Directory Structure

```
evaluation/
├── README.md                          # Main documentation
├── GETTING_STARTED.md                 # Quick start guide
├── ORGANIZATION.md                    # This file
│
├── Core Runners
│   ├── run_evaluation.py              # Full evaluation suite
│   ├── pipeline_runner.py             # Pipeline execution
│   ├── run_with_real_pipeline.py      # Pipeline evaluation
│   └── quick_validation.py            # Quick validation checks
│
├── Data Generation & Training
│   ├── generate_snmp_training_data.py # Training data generator
│   └── train_isolation_forest.py      # Train SNMP detector
│
├── Analysis Tools
│   ├── analyze_results.py             # Result analysis
│   └── analyze_real_results.py        # Real pipeline analysis
│
└── data/
    └── evaluation/                     # Evaluation results
        ├── alerts/                     # Alert logs
        ├── metrics/                    # Performance metrics
        ├── models/                     # Trained models
        ├── plots/                      # Visualizations
        └── training/                   # Training data
```

## File Descriptions

### Core Runners

**`run_evaluation.py`**

- Purpose: Run complete evaluation suite
- Usage: `python evaluation/run_evaluation.py`
- Output: Comprehensive metrics (F1, delay, Hit@k)
- Duration: 5-30 minutes

**`pipeline_runner.py`**
- Purpose: Execute ML pipeline with scenario data
- Usage: `python evaluation/pipeline_runner.py`
- Features: Real-time anomaly detection, correlation
- Output: Alert logs, ground truth comparison

**`quick_validation.py`**
- Purpose: Quick smoke test of pipeline
- Usage: `python evaluation/quick_validation.py`
- Duration: < 1 minute
- Use case: Verify everything works after changes

### Simulators

Simulators have been moved to `src/anomaly_detection/simulators/` for better organization.

**`src/anomaly_detection/simulators/bgp_simulator.py`**
- Purpose: Generate realistic BGP UPDATE messages
- Features: Multiple failure scenarios, timing control
- Output: BGP updates to NATS or files

**`src/anomaly_detection/simulators/snmp_baseline.py`**
- Purpose: Generate baseline SNMP metrics
- Features: Normal operation simulation, noise injection
- Output: SNMP metrics for training/testing

**`generate_snmp_training_data.py`**
- Purpose: Create labeled training data for Isolation Forest
- Usage: `python evaluation/generate_snmp_training_data.py`
- Output: `data/evaluation/training/snmp_training_data.jsonl`

### Model Training

**`train_isolation_forest.py`**
- Purpose: Train SNMP anomaly detector
- Input: Training data from generate_snmp_training_data.py
- Output: `data/models/isolation_forest_model.pkl`
- Features: Hyperparameter tuning, validation

### Analysis Tools

**`analyze_results.py`**
- Purpose: Analyze evaluation results
- Metrics: F1, Precision, Recall, Detection Delay, Hit@k
- Input: Alert logs + ground truth
- Output: `data/evaluation/metrics/summary.json`

**`analyze_real_results.py`**
- Purpose: Analyze results from real pipeline runs
- Similar to analyze_results.py but for production data

### Diagnostic Tools

**`debug_pipeline.py`**
- Purpose: Debug pipeline execution
- Features: Verbose logging, step-by-step execution
- Use case: Troubleshooting issues

**`diagnose_isolation_forest.py`**
- Purpose: Diagnose Isolation Forest model
- Features: Model inspection, feature importance
- Use case: Understanding model behavior

**`test_feature_extraction.py`**
- Purpose: Test SNMP feature extraction
- Use case: Verify feature extraction works correctly

**`test_gpu.py`**
- Purpose: Test GPU availability for Matrix Profile
- Use case: Verify CUDA/CuPy setup

**`test_stumpy_directly.py`**
- Purpose: Test stumpy Matrix Profile library
- Use case: Verify stumpy installation

## Usage Examples

### Run Full Evaluation

```bash
# 1. Start NATS server
docker compose up -d nats

# 2. Generate training data (if needed)
python evaluation/generate_snmp_training_data.py

# 3. Train models (if needed)
python evaluation/train_isolation_forest.py

# 4. Run evaluation
python evaluation/run_evaluation.py

# 5. Analyze results
python evaluation/analyze_results.py
```

### Quick Validation

```bash
# Just check if everything works
python evaluation/quick_validation.py
```

### Debug Pipeline Issues

```bash
# Run with verbose logging
python evaluation/debug_pipeline.py
```

## Import Conventions

All files use consistent imports:

```python
# Correct imports (consistent)
from src.models import MatrixProfileDetector, IsolationForestDetector
from src.features import SNMPFeatureExtractor
from src.utils import FeatureBin
from src.correlation import MultiModalCorrelator
```

## Data Flow

```
1. Simulators → Generate test data
   ├── bgp_simulator.py → BGP updates
   └── snmp_baseline.py → SNMP metrics

2. Training → Create models
   ├── generate_snmp_training_data.py → Training data
   └── train_isolation_forest.py → Trained model

3. Evaluation → Test system
   ├── run_evaluation.py → Run scenarios
   └── pipeline_runner.py → Execute pipeline

4. Analysis → Measure performance
   ├── analyze_results.py → Calculate metrics
   └── Visualizations in data/evaluation/plots/
```

## Recent Changes (October 2025)

### Import Fixes ✅
- All imports now use `from src.` prefix
- Fixed 6 files with inconsistent imports
- More reliable, works from any location

### Cleanup ✅
- Removed empty `scenarios/` directory
- Consolidated evaluation data structure

## Adding New Evaluation Scenarios

1. Create scenario script in evaluation/
2. Use simulators to generate test data
3. Run via pipeline_runner.py or run_evaluation.py
4. Analyze with analyze_results.py
5. Document results

Example:

```python
# evaluation/my_scenario.py
from src.anomaly_detection.simulators import BGPSimulator, SNMPBaseline

def run_my_scenario():
    # 1. Generate data
    bgp_sim = BGPSimulator()
    bgp_sim.generate_failure_scenario("my_failure")
    
    # 2. Run pipeline (handled by pipeline_runner.py)
    
    # 3. Analyze (handled by analyze_results.py)
    pass
```

## Troubleshooting

### Import Errors

Ensure you're running from project root:

```bash
cd /path/to/capstone-anomaly
python evaluation/run_evaluation.py
```

### NATS Connection Errors

Start NATS server:

```bash
docker compose up -d nats
```

### Model Not Found

Train the model first:

```bash
python evaluation/train_isolation_forest.py
```

## Related Documentation

- Main README: `README.md`
- Data directory: `data/README.md`
- Test suite: `tests/README.md`
- Src organization: `src/ORGANIZATION.md`

## Questions?

See:
- `evaluation/README.md` - Comprehensive evaluation guide
- `evaluation/GETTING_STARTED.md` - Quick start
- Analysis document: `REORGANIZATION_ANALYSIS_DIRS.md`
