# Multi-Modal Network Anomaly Detection ML Pipeline

This Python-based ML pipeline provides comprehensive real-time network anomaly detection using streaming data from multiple sources. It processes BGP updates, SNMP metrics, and syslog messages via NATS messaging, extracts multi-modal features, and performs anomaly detection using Matrix Profile and other ML techniques to identify network failures and provide correlation analysis for Network Operation Centers.

## Architecture

The ML pipeline consists of several key components:

### 1. Data Ingestion (`ingest/`)

- **Purpose**: Receives multi-modal network data from simulated and production sources
- **Technology**: NATS message bus integration
- **Sources**:
  - BGP updates from data generators
  - Syslog messages from network devices
  - **SNMP metrics from hardware simulation**
  - **Environmental sensor data**
  - Real-time streaming data

### 2. Feature Extraction (`features/`)

- **Purpose**: Extracts and aggregates features from multi-modal network data
- **Technology**: `FeatureAggregator` and `SNMPFeatureExtractor` classes
- **BGP Features**:
  - BGP announcement/withdrawal rates
  - AS path analysis and churn
  - Peer diversity metrics
  - Temporal feature bins
- **SNMP Features**:
  - Hardware health indicators (CPU, memory, temperature)
  - Interface performance metrics (errors, utilization)
  - Environmental anomaly patterns (thermal, power, fan status)
  - Multi-device correlation analysis

### 3. Message Bus (`message_bus/`)

- **Purpose**: Handles data streaming between components
- **Technology**: NATS message bus
- **Subjects**:
  - `bgp.updates` - BGP update messages from simulators
  - `syslog.messages` - Syslog messages from simulators
  - `snmp.metrics` - **SNMP hardware metrics (NEW)**
  - `bgp.events` - Anomaly detection events
  - `anomaly.alerts` - Alert notifications
  - `alerts.multi_modal` - **Multi-modal failure alerts (NEW)**

### 4. ML Models (`models/`)

- **Purpose**: Multi-modal anomaly detection using various ML techniques
- **Technologies**:
  - Matrix Profile (GPU-accelerated) for BGP time series
  - **Isolation Forest for SNMP hardware anomalies**
  - LSTM networks for temporal patterns
  - **Multi-modal fusion algorithms**
- **Features**:
  - Real-time streaming detection
  - GPU acceleration support
  - Multiple detection algorithms
  - **Cross-modal correlation analysis (NEW)**

### 5. Multi-Modal Pipeline (`integration/multi_modal_pipeline.py`) **NEW**

- **Purpose**: Combines BGP, syslog, and SNMP data for comprehensive failure detection
- **Features**:
  - Correlates BGP updates with syslog messages and SNMP metrics
  - **Hardware failure detection and classification**
  - **Environmental anomaly monitoring**
  - Enhanced failure detection accuracy
  - Improved localization capabilities
  - **Multi-modal alert generation**

### 6. SNMP Simulation (`simulators/snmp_simulator.py`)

- **Purpose**: Simulates hardware failures and environmental issues using snmpsim
- **Features**:
  - **Optical transceiver degradation simulation**
  - **Memory pressure and thermal runaway scenarios**
  - **Cable intermittent connection patterns**
  - **Power supply instability modeling**
  - Realistic SNMP metric generation

## Multi-Modal Analytics Framework

This system extends beyond traditional BGP monitoring to provide comprehensive network analytics:

### **Network Anomaly Detection**

- **Routing Anomalies**: BGP update patterns, AS path changes, convergence issues
- **Hardware Issues**: SNMP metrics for device health and interface performance
- **System Events**: Syslog message patterns and error correlation
- **Environmental Factors**: Thermal, power, and performance degradation indicators

### **Multi-Modal Data Sources**

- **BGP Updates**: Route announcements, withdrawals, AS path changes
- **SNMP Metrics**: Hardware health, interface statistics, environmental sensors
- **Syslog Messages**: System events, error patterns, device correlations

### **Advanced Analytics**

- **Temporal Correlation**: Cross-time analysis of events across data sources
- **Multi-Modal Fusion**: Integration of BGP, SNMP, and syslog signals
- **Context-Aware Localization**: Topology-aware anomaly identification
- **Operational Efficiency**: Alert noise reduction and correlation analysis

## Quick Start

### Prerequisites

1. **Python 3.8+** with required packages:

   ```bash
   pip install -r requirements.txt
   ```

2. **NATS Server** (optional, for message bus):

   ```bash
   # Using Docker
   docker run -p 4222:4222 nats:latest
   
   # Or install locally
   # See: https://docs.nats.io/running-a-nats-service/introduction/installation
   ```

### Running the Pipeline

1. **Run the multi-modal pipeline**:

   ```bash
   # Multi-modal detection with BGP, SNMP, and syslog
   python examples/run_multimodal_correlation.py
   
   # Or run a quick demonstration
   python examples/demo_multimodal_correlation.py
   ```

2. **Run individual components**:

   ```bash
   # SNMP simulation for hardware failure testing
   python src/simulators/snmp_simulator.py
   
   # BGP anomaly detection only
   python src/models/matrix_profile_bgp.py
   ```

3. **Access the dashboard** (optional):

   ```bash
   # Start the dashboard
   streamlit run src/dash/simple_dashboard.py
   ```

## Configuration

The system is configured via YAML files in the `configs/` directory. Key configuration sections:

### Network Topology

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

### Data Generation

The simulation configuration can be customized in the individual test scripts:

```python
# BGP update generation
bgp_config = {
    'update_frequency': 1.0,  # seconds
    'announcements_per_second': 10,
    'withdrawals_per_second': 2
}

# SNMP metric generation
snmp_config = {
    'sample_rate': 5,  # seconds
    'baseline_noise': 0.98  # 98% normal metrics
}
```

## Feature Extraction

The preprocessing pipeline implements the approach from the Feltin 2023 paper:

### BGP Features

- Announcement/withdrawal rates
- AS path analysis (length, variance, churn)
- Peer diversity and update patterns
- Temporal burstiness analysis

### Syslog Features

- Severity distribution analysis
- Message type diversity
- Temporal patterns and burstiness
- Semantic event pattern detection

### System Features

- CPU, memory, temperature trends
- Resource utilization patterns
- Performance degradation indicators

### Correlation Features

- Cross-correlation between BGP and syslog
- Temporal alignment analysis
- Event sequence scoring

## Monitoring and Metrics

The lab provides comprehensive monitoring:

### Real-time Metrics

- Data generation rates
- Feature extraction throughput
- Message bus performance
- Scaling phase progress

### Exportable Results

- Complete phase history
- Performance statistics
- Feature importance scores
- Anomaly detection results

## Testing

### Component Tests

```bash
# Run quick validation
python evaluation/quick_validation.py

# Test specific scenarios
python tests/run_test_scenarios.py
```

### Integration Tests

```bash
# Run complete evaluation suite
python evaluation/run_evaluation.py

# Analyze results
python evaluation/analyze_results.py
```

### Custom Test Scenarios

Create custom test scenarios by modifying the scenario scripts in `evaluation/scenarios/`:

- Different network topologies
- Varying data generation rates
- Custom failure injection patterns
- Multi-device coordinated failures

## Directory Structure

``` text
src/
├── correlation/
│   └── multimodal_correlator.py  # Cross-modal event correlation
├── models/
│   ├── cpu_mp_detector.py        # Matrix Profile BGP detector
│   └── isolation_forest_detector.py  # SNMP detector
├── features/
│   └── feature_extractor.py      # Feature extraction pipeline
├── simulators/
│   ├── bgp_simulator.py          # BGP data generation
│   └── snmp_simulator.py         # SNMP metric simulation
├── triage/
│   └── topology_triage.py        # Topology-aware analysis
├── alerting/
│   └── alert_manager.py          # Alert generation
└── README.md                     # This file
```

## Troubleshooting

### Common Issues

1. **NATS Connection Failed**
   - Ensure NATS server is running: `docker compose up -d nats`
   - Check connection configuration in your scripts

2. **Import Errors**
   - Run from project root directory
   - Ensure all dependencies are installed: `pip install -r requirements.txt`

3. **Configuration Errors**
   - Validate YAML syntax
   - Check file paths are correct

4. **Performance Issues**
   - Reduce data generation rates in test scenarios
   - Decrease the number of simulated devices
   - Adjust detection sensitivity thresholds

## References

- **Feltin, T., et al. (2023)**: "Understanding Semantics in Feature Selection for Fault Diagnosis in Network Telemetry Data"
- **Matrix Profile**: For time series anomaly detection
- **NATS**: High-performance messaging system
- **BGP**: Border Gateway Protocol specifications

## Contributing

To extend the system:

1. **Add New Data Sources**: Extend simulators in `simulators/`
2. **New Feature Types**: Modify `FeatureExtractor` classes
3. **Custom Anomalies**: Add new scenario scripts in `evaluation/scenarios/`
4. **New Detection Algorithms**: Extend models in `models/`

## License

This project is licensed under the MIT License. See the LICENSE file in the project root for details.
