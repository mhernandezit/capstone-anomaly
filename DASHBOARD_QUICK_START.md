# Dashboard Quick Start Guide

## Overview

This guide shows you how to launch and use the new modern network anomaly detection dashboard with animated dual ML pipeline visualization.

## What You'll See

### 1. Network Topology (Top Panel)
- **6-device Clos fabric** visualization
- **Real-time status** indicators on each device
- **Animated anomaly** highlighting (devices turn red)
- **Device roles** shown by shape:
  - Squares: Spine routers
  - Diamonds: ToR switches
  - Circles: Edge routers

### 2. Dual ML Pipelines (Middle Panels)

**Left: Matrix Profile (BGP Pipeline)**
- Time-series of BGP update volume
- Distance profile showing anomaly detection
- Red threshold line at 2.5
- Animated X markers for detected anomalies
- Shows routing instability patterns

**Right: Isolation Forest (SNMP Pipeline)**
- 2D projection of 19-dimensional feature space
- Blue dots: Normal operation
- Red X markers: Anomalous outliers
- Shows hardware degradation patterns

### 3. Detection Timeline (Bottom Panel)
- Pink line: BGP detections over time
- Blue line: SNMP detections over time
- Y-axis: Confidence scores (0-1)
- Shows multi-modal correlation

### 4. Active Anomalies Section
- Real-time alert cards
- Device name, source, confidence, timestamp
- Critical alerts pulse in red

## Launch Instructions

### Step 1: Open Dashboard

```powershell
# Option A: Use launcher script
python launch_dashboard.py

# Option B: Direct Streamlit command
streamlit run src/anomaly_detection/dash/modern_dashboard.py
```

Your browser will automatically open to `http://localhost:8501`

### Step 2: Select a Scenario

In the left sidebar, choose from:
- **Link Failure (Multimodal)** - Both pipelines detect
- **BGP Route Flapping** - BGP-only
- **Hardware Degradation** - SNMP-only
- **Router Overload** - Both pipelines
- **Normal Operation** - No anomalies

### Step 3: Start Simulation

Click the **"Start Simulation"** button in the sidebar.

Watch as the dashboard animates:
1. Topology updates with red anomaly indicators
2. Matrix Profile shows BGP discords
3. Isolation Forest displays SNMP outliers
4. Timeline tracks both pipelines
5. Alerts appear in the bottom section

### Step 4: Observe Multi-Modal Correlation

For "Link Failure (Multimodal)" scenario, you'll see:

**T+0s to T+20s**
- BGP pipeline starts processing
- Matrix Profile distance increases
- Green light turns red on "BGP" indicator

**T+20s to T+35s**
- SNMP pipeline detects outlier
- Isolation Forest shows red X marker
- Green light turns red on "SNMP" indicator

**T+35s+**
- Both pipelines correlated
- spine-01 node turns red on topology
- Alert appears: "CRITICAL: Anomaly detected"
- Confidence scores shown from both sources

## Sidebar Controls

### Simulation Controls
- **Select Failure Scenario**: Choose what to simulate
- **▶️ Start Simulation**: Begin animation
- **⏹️ Stop Simulation**: Pause current scenario
- **🔄 Reset Dashboard**: Clear all data

### Display Options
- **Auto-refresh**: Toggle automatic updates
- **Refresh Rate**: 1-10 seconds (controls animation speed)

### Pipeline Status Indicators
- ⚪ Idle (not processing)
- 🔴 Active (processing/detecting)

## Scenario Details

### Link Failure (Multimodal) [RECOMMENDED FOR DEMO]

**What happens**: Physical link failure on spine-01 interface eth1

**BGP Impact**:
- 47 route withdrawals
- Peer session goes IDLE
- Matrix Profile distance: 3.2 (exceeds 2.5 threshold)

**SNMP Impact**:
- Interface error rate: 0.02% → 45%
- Link state: UP → DOWN
- Isolation Forest outlier score: -0.45

**Expected Detection**:
- BGP detection: ~20 seconds
- SNMP detection: ~30 seconds
- Correlation: ~35 seconds
- Alert generated with multi-modal evidence

### BGP Route Flapping

**What happens**: Periodic route announcements/withdrawals on tor-01

**BGP Impact**:
- Repeating pattern of UPDATE messages
- Matrix Profile detects periodic discord

**SNMP Impact**: None (routing-only issue)

**Expected Detection**:
- BGP detection: ~25 seconds
- Shows power of time-series pattern detection

### Hardware Degradation

**What happens**: Temperature spike and CPU overload on spine-02

**BGP Impact**: None initially

**SNMP Impact**:
- Temperature: 42°C → 78°C
- CPU utilization: 30% → 95%
- Multi-dimensional outlier in feature space

**Expected Detection**:
- SNMP detection: ~30 seconds
- Shows unsupervised outlier detection

### Router Overload

**What happens**: CPU/memory exhaustion affecting routing

**BGP Impact**:
- Routing delays and instability
- Increased UPDATE churn

**SNMP Impact**:
- CPU utilization spike
- Memory pressure increase

**Expected Detection**:
- SNMP detection: ~25 seconds
- BGP detection: ~35 seconds
- Shows cascading failure pattern

## Understanding the Visualizations

### Matrix Profile Graph

**Top panel (Time Series)**:
- Shows BGP update volume over time
- Normal: ~20 updates per window
- Anomalous: Spikes to 100+ or drops to 0

**Bottom panel (Distance Profile)**:
- Y-axis: Distance to nearest neighbor
- Red dashed line: Threshold (2.5)
- Spikes above threshold = anomalies (discords)
- Shows how different current pattern is from historical

### Isolation Forest Graph

**2D Feature Space**:
- X-axis: Aggregated CPU/Memory metrics
- Y-axis: Aggregated Interface/Temperature metrics
- Clustering: Normal points cluster together
- Outliers: Anomalous points far from cluster
- Shows high-dimensional anomaly detection in 2D

### Network Topology

**Colors**:
- Default: Device role color (red/teal/green)
- Anomaly: Bright red with larger size
- Edge connections: Gray (normal) or red (affected)

**Real-time Updates**:
- Nodes pulse when anomalies detected
- Size increases for active anomalies
- Connected edges highlight affected paths

## Performance Metrics

Based on evaluation framework results:

```
F1 METRICS:
  Precision: 1.000 (0% false positives)
  Recall:    1.000 (100% detection rate)
  F1 Score:  1.000 (perfect balance)

DETECTION DELAY:
  Mean:   29.40 seconds
  Median: 40.91 seconds
  P95:    55.94 seconds
  [OK] All under 60-second SLA

LOCALIZATION:
  Hit@1: 1.000 (top device always correct)
  Hit@3: 1.000
  Hit@5: 1.000
```

## Tips for Presentations

1. **Start with topology**: Show the clean 6-device network
2. **Explain dual pipelines**: Point out BGP (routing) vs SNMP (hardware)
3. **Run multimodal scenario**: Best demonstrates correlation
4. **Highlight animations**: Watch for pipeline status lights and node colors
5. **Show timeline**: Demonstrates temporal correlation
6. **Explain confidence**: Both pipelines contribute to final score
7. **Point out metrics**: Perfect precision/recall in bottom section

## Troubleshooting

### Dashboard won't start
```powershell
# Install missing dependencies
pip install streamlit plotly networkx pandas numpy
```

### No animations visible
- Ensure "Auto-refresh" is checked
- Verify refresh rate is reasonable (3-5 seconds)
- Try clicking "Start Simulation" again

### Browser doesn't open
- Manually navigate to: `http://localhost:8501`
- Check firewall settings
- Try different port: `streamlit run ... --server.port 8502`

### Performance issues
- Reduce refresh rate to 5-10 seconds
- Close other browser tabs
- Stop simulation when not actively demoing

## Next Steps

### View Real Evaluation Results

```powershell
# Run full evaluation with simulators
docker compose up -d nats
python evaluation/run_evaluation.py
python evaluation/analyze_results.py
```

### See Comprehensive Demo

```powershell
# Text-based walkthrough (no dependencies)
python examples/comprehensive_dashboard_demo.py
```

### Read Documentation

- Dashboard README: `src/anomaly_detection/dash/README.md`
- Evaluation Framework: `evaluation/README.md`
- Project Overview: `README.md`

## What Makes This Dashboard Unique

1. **Dual ML Visualization**: See both algorithms working simultaneously
2. **Real-time Correlation**: Watch multi-modal detection unfold
3. **Topology Integration**: Anomalies shown on network map
4. **Animated Processing**: Pipeline status indicators show live analysis
5. **Educational**: Perfect for understanding how the system works
6. **No Dependencies**: Runs standalone without external services
7. **Interactive**: Full control over scenarios and timing

## Architecture Overview

```
User selects scenario
        ↓
Dashboard generates mock data matching failure pattern
        ↓
    ┌───────────────┐       ┌───────────────┐
    │ Matrix Profile│       │Isolation Forest│
    │   (BGP Data)  │       │  (SNMP Data)   │
    └───────┬───────┘       └───────┬────────┘
            │                       │
            └───────┬───────────────┘
                    ↓
            Correlation Agent
                    ↓
            Topology Update
                    ↓
            Alert Generation
                    ↓
         Dashboard Displays Results
```

## Contact

For questions or issues:
- Check `src/anomaly_detection/dash/README.md` for detailed documentation
- Review evaluation results in `data/evaluation/`
- See examples in `examples/` directory

---

**Enjoy exploring the dual ML pipeline dashboard!**

