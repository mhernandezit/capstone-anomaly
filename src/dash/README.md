# Network Anomaly Detection Dashboard

A comprehensive Streamlit-based dashboard for visualizing network anomaly detection in real-time, featuring topology diagrams, live BGP/SNMP/syslog statistics, and data graphs.

## Features

### 🗺️ Network Topology Visualization
- Interactive network graph showing BGP peer relationships
- Real-time peer status (active/inactive)
- Visual indicators for peer health and connectivity

### 📊 Multi-Modal Data Visualization
- **BGP Activity**: Message type distribution, timeline charts, peer statistics
- **SNMP Metrics**: Device performance metrics, severity analysis
- **Syslog Messages**: Network events, failure scenarios, correlation analysis
- **Anomaly Analysis**: Detected anomalies, severity distribution, confidence metrics

### 🚨 Real-Time Monitoring
- Live data streaming from NATS message bus
- Auto-refresh capabilities
- Alert banners for critical anomalies
- Peer status tracking

## Quick Start

### 1. Start Background Components
```bash
# Start all simulators and data collectors
python src/dash/start_dashboard.py
```

This will start:
- SNMP Data Simulator (from `src/simulators/snmp_simulator.py`)
- Syslog Message Simulator (from `src/simulators/syslog_simulator.py`)
- BGP data collection (from lab environment)

### 2. Start the Dashboard
```bash
# Start the Streamlit dashboard
streamlit run src/dash/network_dashboard.py
```

The dashboard will be available at: http://localhost:8501

## Data Sources

The dashboard integrates with multiple data sources via NATS message bus:

| Source | Subject | Description |
|--------|---------|-------------|
| BGP Updates | `bgp.updates` | Real-time BGP message data |
| SNMP Metrics | `snmp.metrics` | Network device performance metrics |
| Syslog Messages | `syslog.messages` | Network event logs |
| Anomalies | `anomalies.detected` | ML-detected anomalies |

## Dashboard Components

### Main Dashboard (`network_dashboard.py`)
- **NetworkDataCollector**: Collects and processes data from NATS
- **Real-time Metrics**: Active peers, message rates, anomaly counts
- **Interactive Tabs**: BGP, SNMP, Syslog, Peer Details, Anomaly Analysis
- **Topology Visualization**: Network graph with peer relationships

### Startup Manager (`start_dashboard.py`)
- Manages all background components
- Graceful startup/shutdown
- Process monitoring and restart capabilities

## Configuration

### Dashboard Settings
- Auto-refresh interval (1-30 seconds)
- Topology display options
- Alert notification preferences

### Data Collection
- Message buffer sizes (default: 1000 messages)
- Peer timeout thresholds (default: 60 seconds)
- Anomaly confidence thresholds

## Integration with Existing Simulators

The dashboard automatically integrates with your existing simulators:

- **SNMP Simulator**: Provides realistic hardware failure scenarios
- **Syslog Simulator**: Generates correlated network events
- **BGP Data Collector**: Streams live BGP updates from lab environment

## Troubleshooting

### Common Issues

1. **No data appearing**
   - Ensure NATS server is running (`nats-server --jetstream`)
   - Check that simulators are started via `start_dashboard.py`
   - Verify BGP data collector is running in lab environment

2. **Dashboard not loading**
   - Check Streamlit installation: `pip install streamlit`
   - Verify port 8501 is available
   - Check for Python dependency issues

3. **Simulators not starting**
   - Ensure all dependencies are installed
   - Check NATS connectivity
   - Verify file paths in startup script

### Dependencies
```bash
pip install streamlit plotly networkx pandas nats-py
```

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   BGP Lab       │    │  SNMP Simulator │    │ Syslog Simulator│
│   Environment   │    │                 │    │                 │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │      NATS Message Bus     │
                    │   (bgp.updates, snmp.     │
                    │    metrics, syslog.       │
                    │    messages, anomalies)   │
                    └─────────────┬─────────────┘
                                  │
                    ┌─────────────▼─────────────┐
                    │   Streamlit Dashboard     │
                    │   (network_dashboard.py)  │
                    └───────────────────────────┘
```

## Next Steps

1. **Start the lab environment** to get real BGP data
2. **Run the dashboard startup script** to begin data collection
3. **Launch the Streamlit dashboard** for visualization
4. **Monitor network topology** and anomaly detection in real-time


