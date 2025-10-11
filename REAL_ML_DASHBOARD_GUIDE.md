# Real ML Dashboard Guide

## Overview

This dashboard uses **ACTUAL** Matrix Profile and Isolation Forest algorithms, not simulated data.

## Two Dashboard Versions

### 1. **Simulated Dashboard** (Fast, Demo-Friendly)
**File**: `src/anomaly_detection/dash/modern_dashboard.py`  
**Launcher**: `python launch_dashboard.py`

**Characteristics**:
- ⚡ Instant results (no processing delay)
- 🎭 Mock data generated with random numbers
- 📊 Visualizations show concept, not real ML
- 🎯 Perfect for presentations and quick demos
- ✅ Always available, no model loading needed

**Use When**:
- Giving live presentations
- Quick demonstrations
- Showing UI/UX features
- Explaining the concept

### 2. **Real ML Dashboard** (Authentic, Slower) ⭐ NEW
**File**: `src/anomaly_detection/dash/real_ml_dashboard.py`  
**Launcher**: `python launch_real_ml_dashboard.py`

**Characteristics**:
- 🔬 Real Matrix Profile discord detection
- 🌲 Real Isolation Forest with 150 decision trees
- ⏱️ Authentic 30-60 second processing times
- 📈 Genuine confidence scores from algorithms
- 🎓 Educational - shows actual ML behavior

**Use When**:
- Validating ML algorithm performance
- Demonstrating real system capabilities
- Educational purposes (showing actual ML)
- Building trust with technical audiences

## Quick Start - Real ML Dashboard

### Launch

```powershell
python launch_real_ml_dashboard.py
```

Or directly:
```powershell
streamlit run src/anomaly_detection/dash/real_ml_dashboard.py
```

### First Run

**Initialization (30 seconds)**:
1. Loading Matrix Profile detector
2. Loading Isolation Forest detector
3. Attempting to load trained model from `data/models/isolation_forest_model_tuned.pkl`
4. If model not found, training new model with 250 synthetic samples

You'll see:
```
✅ Matrix Profile: Loaded
✅ Isolation Forest: Loaded
📊 Bins Processed: 0
```

### Running a Scenario

1. **Select Scenario**: Choose from dropdown (e.g., "Link Failure (Multimodal)")
2. **Click "Start"**: Dashboard begins processing
3. **Wait 30-60 seconds**: Real ML algorithms are computing
4. **Observe**: 
   - Matrix Profile graph updates with REAL distance calculations
   - Isolation Forest shows TRUE outlier positions
   - Detections appear with GENUINE confidence scores

## What's Different?

### Matrix Profile (BGP)

**Simulated Version**:
```python
# Mock data with random distance
"distance": np.random.uniform(1, 4) if is_anomaly else np.random.uniform(0.5, 1.5)
"is_anomaly": scenario == "BGP" and i < 2  # Hardcoded
```

**Real ML Version**:
```python
# Actual Matrix Profile computation
bgp_result = bgp_detector.update(feature_bin)  # Real algorithm!
"distance": bgp_result.get("min_distance", 0)  # Computed distance
"is_anomaly": bgp_result["is_anomaly"]  # Algorithm decision
"confidence": bgp_result["anomaly_confidence"]  # Real confidence
```

### Isolation Forest (SNMP)

**Simulated Version**:
```python
# Mock feature space position
"feature_1": np.random.normal(0, 1)
"is_anomaly": scenario == "Hardware" and i > 7  # Hardcoded
```

**Real ML Version**:
```python
# Actual Isolation Forest prediction
snmp_result = snmp_detector.predict(feature_vector, timestamp, feature_names)  # Real!
"is_anomaly": snmp_result.is_anomaly  # Algorithm decision
"confidence": snmp_result.confidence  # Real confidence
"anomaly_score": snmp_result.anomaly_score  # Tree-based score
```

## Technical Details

### Matrix Profile Processing

**Algorithm**: STUMPY library implementation  
**Window Size**: 64 bins (32 minutes of data)  
**Discord Threshold**: 2.5 standard deviations  
**Features**: withdrawals, announcements, AS-path churn

**How it works**:
1. Maintains sliding window of BGP features
2. Computes pairwise distances between subsequences
3. Identifies discords (unusual patterns)
4. Returns min distance and anomaly flag

**Typical Output**:
```python
{
    "is_anomaly": True,
    "anomaly_confidence": 0.87,
    "detected_series": ["wdr_total", "as_path_churn"],
    "min_distance": 3.2,  # Exceeds 2.5 threshold
}
```

### Isolation Forest Processing

**Algorithm**: scikit-learn IsolationForest  
**Trees**: 150 estimators  
**Features**: 8 SNMP metrics (CPU, memory, temp, interface)  
**Contamination**: 2% expected anomaly rate

**How it works**:
1. Builds 150 isolation trees
2. Isolates each data point
3. Computes anomaly score (average path length)
4. Identifies outliers in high-dimensional space

**Typical Output**:
```python
IFAnomalyResult(
    is_anomaly=True,
    confidence=0.91,
    anomaly_score=-0.45,  # Negative = more anomalous
    affected_features=["cpu_utilization_max", "temperature_mean"],
    severity="critical"
)
```

## Performance Expectations

### Processing Time

**Bin Processing**: 2-5 seconds per time bin
- Data generation: ~0.1s
- Matrix Profile computation: ~1-2s (depends on buffer size)
- Isolation Forest prediction: ~0.1s
- UI update: ~0.5s

**Detection Delay**: 30-60 seconds
- Matrix Profile needs 128+ bins to build profile
- First detections appear after sufficient data accumulated
- Matches evaluation framework timing

### Resource Usage

**CPU**: Moderate
- Matrix Profile: Single-core computation
- Isolation Forest: Multi-core (n_jobs=-1)
- Peak usage during detection: 40-60%

**Memory**: Light
- BGP buffer: ~200 bins × 3 features = negligible
- SNMP buffer: ~200 samples × 8 features = ~12KB
- ML models: ~5MB (Isolation Forest), minimal (Matrix Profile)

## Comparison Table

| Feature | Simulated Dashboard | Real ML Dashboard |
|---------|-------------------|------------------|
| **Speed** | Instant | 30-60s delays |
| **Algorithm** | Mock random data | Actual ML |
| **Confidence** | Fake (random) | Real (computed) |
| **Detection** | Hardcoded | Algorithm decision |
| **Model Loading** | Not needed | Required |
| **CPU Usage** | Minimal | Moderate |
| **Educational Value** | Low | High |
| **Demo-Friendly** | Very | Moderate |
| **Accuracy** | N/A | 1.00 (from eval) |
| **Use Case** | Presentations | Validation/education |

## Troubleshooting

### Model Not Loading

```
⚠️ Could not load model: [Errno 2] No such file or directory: 
'data/models/isolation_forest_model_tuned.pkl'
Training new model...
```

**Solution**: Model will be trained automatically with 250 synthetic samples. Takes ~10 seconds.

**Alternative**: Run evaluation framework first to generate trained model:
```powershell
python evaluation/train_isolation_forest.py
```

### Slow Processing

**Symptom**: Each bin takes >10 seconds

**Causes**:
- Large buffer size (Matrix Profile scales with buffer length)
- CPU throttling
- Other processes using CPU

**Solutions**:
- Close other applications
- Reduce buffer size in code (line 76: `maxlen=100` instead of 200)
- Wait for Matrix Profile's initial warmup period

### No Detections Appearing

**Symptom**: Simulation runs but no detections shown

**Causes**:
- Matrix Profile needs minimum buffer (128 bins)
- Anomaly not severe enough for thresholds
- Random data generation happened to be normal

**Solutions**:
- Wait longer (2-3 minutes)
- Check "Bins Processed" counter (should be >128 for MP)
- Try different scenario
- Lower discord threshold in code (line 28: `discord_threshold=2.0`)

## Validation

### Verify Real ML is Running

1. **Check processing delay**: Should take 2-5 seconds per bin
2. **Watch distance values**: Should vary smoothly, not jump randomly
3. **Observe anomaly scores**: Should be negative for Isolation Forest
4. **Count bins**: Matrix Profile won't detect until 128+ bins processed

### Compare with Evaluation Results

The real ML dashboard should match evaluation framework performance:

**From `data/evaluation/metrics/summary.json`**:
```json
{
  "f1": {"precision": 1.0, "recall": 1.0, "f1": 1.0},
  "delay": {"mean": 29.4, "median": 40.91, "p95": 55.94},
  "localization": {"hit@1": 1.0}
}
```

Run same scenarios and verify similar timing and detection accuracy.

## Development

### Adding New Features

To add new SNMP features:

1. **Update feature generation** (line 134):
```python
snmp_features = {
    "cpu_utilization_mean": ...,
    "new_feature_name": ...,  # Add here
}
```

2. **Update training data** (line 103):
```python
features = {
    # ... existing features
    "new_feature_name": np.random.uniform(...),
}
```

3. **Retrain model** or clear cache to reload

### Adjusting Detection Sensitivity

**Matrix Profile** (line 28):
```python
discord_threshold=2.5  # Lower = more sensitive (e.g., 2.0)
```

**Isolation Forest** (line 33):
```python
contamination=0.02  # Higher = expect more anomalies (e.g., 0.05)
```

## Summary

The real ML dashboard provides an **authentic** view of the anomaly detection system's capabilities:

- ✅ Uses actual Matrix Profile and Isolation Forest algorithms
- ✅ Shows genuine detection delays (30-60s like production)
- ✅ Displays real confidence scores from ML models
- ✅ Demonstrates true algorithm behavior
- ✅ Validates system performance claims

**Use the simulated dashboard for presentations, the real ML dashboard for validation.**

---

**Questions?**
- Compare: Run both dashboards side-by-side to see differences
- Validate: Check against evaluation framework results
- Learn: Read algorithm papers (Matrix Profile: Yeh et al. 2016, Isolation Forest: Liu et al. 2008)

