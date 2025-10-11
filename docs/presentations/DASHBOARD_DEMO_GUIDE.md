# Dashboard Demo Guide for Presentations

**UPDATED**: This guide has been superseded by the new modern animated dashboard.

## New Dashboard (Recommended)

The project now includes a modern animated dashboard with dual ML pipeline visualization.

### Quick Start (1 Minute)

```powershell
# From project root
python launch_dashboard.py
```

Dashboard opens automatically at **http://localhost:8501**

### Features

- **Animated network topology** with real-time anomaly indicators
- **Dual ML pipeline visualization**:
  - Matrix Profile (BGP) with time-series and distance profile
  - Isolation Forest (SNMP) with feature space projection
- **Interactive scenario selection** (link failure, BGP flapping, hardware degradation, router overload)
- **Detection timeline** showing multi-modal correlation
- **Zero infrastructure required** (no NATS, no simulators)

### Documentation

See these guides for complete information:

1. **DASHBOARD_QUICK_START.md** - Step-by-step presentation guide (root directory)
2. **DEMO_SUMMARY.md** - Complete demo package overview (root directory)
3. **src/anomaly_detection/dash/README.md** - Technical documentation

---

## Legacy Information (For Reference)

The following information describes the previous dashboard implementation.
For current demonstrations, use the new modern dashboard above.

### Previous Quick Start

### Step 1: Start NATS Message Bus
```powershell
docker compose up -d nats
```

### Step 2: Start the Dashboard and Simulators
```powershell
# Old command (no longer functional)
# python src/anomaly_detection/dash/start_dashboard.py
```

### Step 3: Open the Dashboard
Navigate to: **http://localhost:8501**

## Dashboard Features for Demo

### Network Topology View
- Interactive network graph showing BGP peer relationships
- Real-time peer status indicators (green=active, red=inactive)
- Visual representation of 6-device simulated network (2 spine, 2 ToR, 2 edge)

### Multi-Modal Data Panels

**BGP Activity Tab:**
- Message type distribution (UPDATES, KEEPALIVES, NOTIFICATIONS)
- Routing update timeline with announcements and withdrawals
- Per-peer statistics and message rates

**SNMP Metrics Tab:**
- CPU, memory, and temperature trends
- Interface error rates and utilization
- Hardware health indicators

**Syslog Messages Tab:**
- Real-time event log with severity filtering
- Searchable message history
- Correlation highlighting

**Anomaly Analysis Tab:**
- Detected anomalies with confidence scores
- Matrix Profile discord visualizations
- Isolation Forest outlier plots in multi-dimensional feature space

### Demo Scenarios

#### Scenario 1: Baseline Normal Operation
Shows the system operating without anomalies. Dashboard displays steady metrics with no alerts.

#### Scenario 2: BGP Route Flapping
Inject route flapping to see:
- Matrix Profile detecting periodic routing instability
- Distance profile highlighting anomalous subsequences
- Alert generation with affected prefix and peer information

#### Scenario 3: Hardware Degradation
Simulate hardware issues to see:
- SNMP metrics showing temperature spikes or CPU overload
- Isolation Forest identifying outliers in feature space
- Multi-modal correlation with BGP session impacts

#### Scenario 4: Coordinated Failure
Demonstrate multi-modal detection:
- Simultaneous BGP and SNMP anomalies
- Correlation agent fusing signals from both pipelines
- Enhanced alert with root cause analysis

## Injecting Failure Scenarios

### Manual Failure Injection
While dashboard is running, you can inject specific failures using the multimodal correlation examples:

```powershell
# Open a new terminal
python examples/run_multimodal_correlation.py --scenario link_failure
```

Available scenarios:
- `link_failure` - Simulates interface down affecting both routing and hardware
- `router_overload` - CPU/memory stress with routing instability
- `hardware_failure` - Thermal or power issues with BGP session impact
- `optical_degradation` - Transceiver issues causing intermittent failures

### Observing Detection Results

Watch the dashboard anomaly panel for:
1. **Detection timing**: Alerts appear within 30-60 seconds of failure injection
2. **Confidence scores**: System reports 0.8-0.95 confidence for genuine anomalies
3. **Multi-modal confirmation**: Coordinated failures show evidence from multiple data sources
4. **Localization accuracy**: Dashboard identifies specific failing device and component

## Performance Metrics Display

The dashboard shows real-time system performance:

**Detection Accuracy:**
- Precision: 1.0 (zero false positives with tuned model)
- Recall: 1.0 (all injected failures detected)
- F1 Score: 1.0 (perfect balance)

**Detection Timing:**
- Mean Delay: ~29 seconds
- P95 Delay: ~56 seconds
- All under 60-second operational target

**Localization:**
- Hit@1: 1.0 (top-ranked device is correct)
- Hit@3: 1.0
- Hit@5: 1.0

## Presentation Talking Points

### Architecture Highlights
"The system uses a dual-pipeline architecture: Matrix Profile analyzes BGP time-series for routing anomalies, while Isolation Forest detects hardware issues in high-dimensional SNMP feature space. Both pipelines feed into a correlation agent that fuses signals before alerting."

### ML Algorithms
"Matrix Profile computes pairwise distances between subsequences to identify anomalous patterns without labeled training data. The distance profile shows similarity scores - spikes indicate discords. Isolation Forest uses 150 decision trees to isolate outliers in 19-dimensional feature space representing hardware health."

### Tuning Results
"After systematic tuning, we achieved perfect precision and recall. The Isolation Forest uses 19 features including multi-device correlation and environmental stress indicators. This expanded feature set enables detection of subtle patterns indicating coordinated failures."

### Dashboard Capabilities
"The real-time dashboard visualizes all components: network topology, live telemetry streams, detection results, and performance metrics. Matrix Profile discord plots show exactly which subsequences triggered anomaly scores. Isolation Forest scatter plots reveal which hardware metrics contributed to each detection."

## Troubleshooting

### No Data Appearing
- Check NATS is running: `docker ps | findstr nats`
- Verify simulators started: Look for startup messages in terminal
- Refresh browser and wait 10-15 seconds for data buffering

### Dashboard Won't Load
- Ensure port 8501 is available (Streamlit default)
- Check Streamlit installed: `pip install streamlit`
- Try running dashboard directly: `streamlit run src/anomaly_detection/dash/network_dashboard.py`

### Simulators Not Generating Data
- Verify NATS connectivity: Simulators will show "Connected to NATS" message
- Check no port conflicts on 4222 (NATS default port)
- Restart NATS if needed: `docker compose restart nats`

## Stopping the Demo

### Graceful Shutdown
Press `Ctrl+C` in the terminal running `start_dashboard.py`. This will:
1. Stop all simulators
2. Close NATS connections
3. Shutdown dashboard (browser will show disconnected)

### Clean Up
```powershell
# Stop NATS container
docker compose down nats

# Kill any remaining processes if needed
Get-Process python | Where-Object {$_.Path -like "*anomaly*"} | Stop-Process
```

## Tips for Effective Demo

1. **Pre-load the dashboard** before starting presentation (30 seconds for data buffering)
2. **Start with baseline** to show normal operation without false positives
3. **Inject failures one at a time** for clear cause-and-effect demonstration
4. **Highlight the correlation** between BGP and SNMP signals for coordinated failures
5. **Show the performance metrics** to emphasize the perfect accuracy scores
6. **Zoom into visualizations** - Matrix Profile discords and Isolation Forest outliers are visually compelling

## Advanced: Custom Scenarios

To create custom failure scenarios for specific demo needs, modify the simulator parameters in the example scripts:

```python
# examples/run_multimodal_correlation.py
# Adjust failure timing, severity, or duration
failure_params = {
    'duration': 60,  # seconds
    'severity': 'critical',
    'affected_devices': ['spine-01', 'tor-01']
}
```

## Contact and Support

For technical issues or questions about the dashboard:
- Check `src/anomaly_detection/dash/README.md` for detailed documentation
- Review simulator configurations in `src/anomaly_detection/simulators/`
- Examine example scenarios in `examples/`

---

**Note**: The dashboard is designed for demonstrations and development. For production deployment, additional considerations around authentication, data persistence, and scalability would be needed.

