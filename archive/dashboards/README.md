# Modern Network Anomaly Detection Dashboard

Real-time visualization of dual ML pipelines with animated topology and detection indicators.

## Features

### Dual ML Pipeline Visualization

**Matrix Profile Pipeline (BGP)**
- Real-time time-series analysis of BGP routing data
- Discord detection showing anomalous subsequences
- Visual distance profile with threshold indicators
- Animated processing indicators

**Isolation Forest Pipeline (SNMP)**
- Multi-dimensional feature space visualization
- Outlier detection in 19-feature space
- 2D projection showing normal vs anomalous points
- Real-time anomaly markers

### Interactive Network Topology

- Live 6-device Clos fabric visualization
- Color-coded device status (normal vs anomaly)
- Device role indicators (spine/tor/edge)
- Animated anomaly highlighting
- Impact assessment with connected devices

### Detection Timeline

- Multi-modal correlation timeline
- BGP and SNMP detection events
- Confidence scores over time
- Source attribution for each detection

### Active Alerts Dashboard

- Real-time anomaly notifications
- Device-specific alerts with confidence scores
- Source pipeline attribution
- Timestamp tracking

## Quick Start

### 1. Launch Dashboard

```powershell
# From project root
streamlit run src/anomaly_detection/dash/modern_dashboard.py
```

The dashboard will open in your browser at `http://localhost:8501`

### 2. Select Failure Scenario

Use the sidebar to select from:
- **Normal Operation** - Baseline with no anomalies
- **Link Failure (Multimodal)** - Both BGP and SNMP detect
- **BGP Route Flapping** - BGP-only detection
- **Hardware Degradation** - SNMP-only detection
- **Router Overload** - Both pipelines with different signatures

### 3. Start Simulation

Click "Start Simulation" in the sidebar to begin the animated visualization.

Watch as:
1. Network topology updates with anomaly indicators
2. Matrix Profile shows BGP time-series discords
3. Isolation Forest displays SNMP outliers
4. Timeline tracks correlation events
5. Alerts appear for detected anomalies

## Dashboard Components

### Network Topology (Top)

- **Nodes**: Colored by device role
  - Red squares: Spine routers
  - Teal diamonds: ToR switches
  - Green circles: Edge routers
- **Status**: Nodes turn red when anomalies detected
- **Size**: Nodes enlarge during active anomalies
- **Connections**: Edges show network connectivity

### ML Pipelines (Middle Row)

**Left Panel - Matrix Profile (BGP)**
- Top graph: BGP update volume time-series
- Bottom graph: Distance profile with anomaly threshold
- Red X markers: Detected anomalies exceeding threshold 2.5
- Shows routing instability patterns

**Right Panel - Isolation Forest (SNMP)**
- 2D feature space projection
- Blue dots: Normal operation points
- Red X markers: Detected outliers
- Axes represent aggregated metrics (CPU/memory, interface/temp)

### Detection Timeline (Lower)

- Time-series plot of all detections
- Pink line: BGP pipeline detections
- Blue line: SNMP pipeline detections
- Y-axis: Confidence scores (0-1)
- Shows multi-modal correlation patterns

### Active Anomalies (Bottom)

- Real-time alert cards
- Device name, source pipeline, confidence, timestamp
- Critical alerts highlighted in red
- Updates as scenarios progress

## Simulation Scenarios

### Link Failure (Multimodal)

**Simulates**: Physical link failure on spine-01
**BGP Impact**: Route withdrawals, peer session down
**SNMP Impact**: Interface errors, link state change
**Expected**: Both pipelines detect within 30 seconds

### BGP Route Flapping

**Simulates**: Routing instability on tor-01
**BGP Impact**: Periodic announcements/withdrawals
**SNMP Impact**: None (routing-only issue)
**Expected**: Matrix Profile detects periodic pattern

### Hardware Degradation

**Simulates**: Temperature spike on spine-02
**BGP Impact**: None initially
**SNMP Impact**: Temperature, CPU metrics abnormal
**Expected**: Isolation Forest detects outlier

### Router Overload

**Simulates**: CPU/memory exhaustion on edge-01
**BGP Impact**: Routing delays, instability
**SNMP Impact**: Resource utilization spikes
**Expected**: Both pipelines with different timing

## Controls

### Sidebar Options

- **Select Failure Scenario**: Choose what to simulate
- **Start Simulation**: Begin animated visualization
- **Stop Simulation**: Pause current scenario
- **Reset Dashboard**: Clear all data and restart
- **Auto-refresh**: Toggle automatic updates
- **Refresh Rate**: Control update frequency (1-10 seconds)

### ML Pipeline Status

- Green indicators show active processing
- Red pulsing indicates anomaly detection
- Updates in real-time during simulation

## Performance Metrics

Based on evaluation framework results (`data/evaluation/metrics/summary.json`):

- **Precision**: 1.00 (zero false positives)
- **Recall**: 1.00 (100% detection rate)
- **F1 Score**: 1.00 (perfect balance)
- **Mean Detection Delay**: 29.4 seconds
- **P95 Detection Delay**: 55.9 seconds
- **Hit@1**: 1.00 (perfect localization)

## Technical Details

### ML Algorithms

**Matrix Profile**
- Window size: 64 bins (32 minutes)
- Discord threshold: 2.5 standard deviations
- Features: withdrawals, announcements, AS-path churn

**Isolation Forest**
- Trees: 150 estimators
- Features: 19 multi-device correlation metrics
- Contamination: 2% expected anomaly rate

### Data Flow

1. Scenario selection triggers simulation mode
2. Mock data generated matching failure patterns
3. ML pipelines process data every refresh cycle
4. Topology updated with detection results
5. Alerts generated for threshold exceedances
6. Timeline tracks multi-modal correlation

### Visualization Technology

- **Streamlit**: Web dashboard framework
- **Plotly**: Interactive charts and graphs
- **NetworkX**: Topology graph layout
- **Pandas**: Time-series data handling

## Integration with Live Data

To connect with real evaluation framework:

1. Start NATS message bus:
   ```powershell
   docker compose up -d nats
   ```

2. Run evaluation scenarios:
   ```powershell
   python evaluation/run_evaluation.py
   ```

3. Modify dashboard to subscribe to NATS topics:
   - `bgp.updates`: BGP routing messages
   - `snmp.metrics`: Hardware telemetry
   - `anomalies.detected`: ML pipeline alerts

4. Update data loading functions to read from message queue instead of simulation

## Customization

### Adding New Scenarios

Edit `modern_dashboard.py`:

```python
scenario = st.sidebar.selectbox(
    "Select Failure Scenario",
    [
        "Normal Operation",
        "Your New Scenario",  # Add here
        # ... existing scenarios
    ],
)
```

Then add scenario logic in simulation section.

### Adjusting Topology

Modify `DashboardState._create_topology()`:

```python
devices = {
    "new-device": {"role": "spine", "pos": (x, y), "color": "#color"},
    # ... define your devices
}

connections = [
    ("device-1", "device-2"),
    # ... define connections
]
```

### Changing Visualization Style

Update CSS in the `st.markdown()` section at top of file:

```css
.pipeline-box {
    background: your-gradient;
    /* ... your styles */
}
```

## Troubleshooting

### Dashboard Won't Start

```powershell
# Install dependencies
pip install streamlit plotly networkx pandas numpy

# Try running directly
python -m streamlit run src/anomaly_detection/dash/modern_dashboard.py
```

### Port Already in Use

```powershell
# Change default port
streamlit run src/anomaly_detection/dash/modern_dashboard.py --server.port 8502
```

### No Data Showing

1. Ensure you've clicked "Start Simulation"
2. Check auto-refresh is enabled
3. Verify scenario selection is not "Normal Operation"
4. Try "Reset Dashboard" and start again

### Animations Not Smooth

1. Reduce refresh rate in sidebar
2. Close other browser tabs
3. Check CPU usage
4. Reduce data history size in code

## Future Enhancements

- [ ] Real-time NATS integration for live data
- [ ] Historical playback of evaluation scenarios
- [ ] Alert export to JSON/CSV
- [ ] Custom threshold configuration
- [ ] Multi-scenario comparison view
- [ ] Performance profiling dashboard
- [ ] Zoom/pan on topology graph
- [ ] Alert acknowledgment system

## Development

### Project Structure

```
src/anomaly_detection/dash/
├── modern_dashboard.py      # Main dashboard application
├── README.md                 # This file
└── __init__.py              # Module init
```

### Dependencies

- streamlit >= 1.20.0
- plotly >= 5.13.0
- networkx >= 3.0
- pandas >= 1.5.0
- numpy >= 1.24.0

### Testing

Run dashboard in development mode:

```powershell
streamlit run src/anomaly_detection/dash/modern_dashboard.py --server.runOnSave true
```

Code will auto-reload on changes.

## References

- [Evaluation Framework](../../../evaluation/README.md)
- [ML Models](../../models/README.md)
- [Simulators](../../simulators/README.md)
- [Project Documentation](../../../../docs/README.md)

---

**Note**: This dashboard uses simulated data for demonstration. For production use with live network data, integrate with the evaluation framework's NATS message bus and update data loading functions accordingly.
