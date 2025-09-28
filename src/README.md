# Multi-Modal Network Failure Detection ML Pipeline

This Python-based ML pipeline provides comprehensive real-time network failure detection using streaming data from multiple sources. It processes BGP updates, SNMP metrics, and syslog messages via NATS messaging, extracts multi-modal features, and performs anomaly detection using Matrix Profile and other ML techniques to detect hardware failures, environmental issues, and routing anomalies.

## 🏗️ Architecture

The ML pipeline consists of several key components:

### 1. Data Ingestion (`ingest/`)

- **Purpose**: Receives multi-modal network data from the containerlab environment
- **Technology**: NATS message bus integration
- **Sources**:
  - BGP updates from Go BMP collector
  - Syslog messages from Fluent Bit
  - **SNMP metrics from hardware simulation (NEW)**
  - **Environmental sensor data (NEW)**
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
  - `bgp.updates` - BGP update messages from BMP collector
  - `syslog.messages` - Syslog messages from Fluent Bit
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

## 🌟 Enhanced Capabilities (Addressing Professor Feedback)

This enhanced version expands beyond BGP-only events to include comprehensive network failure detection:

### **Expanded Failure Detection**

- **Hardware Failures**: Bad parts, memory issues, CPU problems, storage failures
- **Cable/Optics Issues**: Fiber breaks, transceiver degradation, connector problems
- **Environmental Problems**: Thermal runaway, power instability, cooling failures
- **Routing Events**: BGP, OSPF, IS-IS convergence issues and policy problems

### **Multi-Modal Data Sources**

- **BGP Updates**: Route announcements, withdrawals, AS path changes
- **SNMP Metrics**: Hardware health, interface statistics, environmental sensors
- **Syslog Messages**: System events, error patterns, device correlations

### **Advanced Analysis**

- **Temporal Correlation**: Cross-time analysis of events across data sources
- **Spatial Correlation**: Multi-device failure propagation analysis
- **Root Cause Analysis**: Automated failure classification and localization
- **Impact Assessment**: Topology-aware blast radius calculation

## 🚀 Quick Start

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

1. **Start the containerlab environment**:

   ```bash
   cd ../lab
   ./scripts/deploy.sh
   ```

2. **Run the enhanced multi-modal pipeline**:

   ```bash
   # Full multi-modal detection with SNMP simulation
   python src/run_enhanced_pipeline.py --demo-mode
   
   # Or production mode
   python src/run_enhanced_pipeline.py
   ```

3. **Run individual components**:

   ```bash
   # SNMP hardware failure simulation only
   python src/simulators/snmp_simulator.py
   
   # Legacy dual-signal pipeline (BGP + syslog)
   python dual_signal_pipeline.py
   
   # Lab integration
   cd ../lab
   python scripts/integrate-with-ml.py
   ```

4. **Access the dashboard**:

   ```bash
   # Start the enhanced dashboard
   streamlit run dash/simple_dashboard.py
   ```

## 📊 Configuration

The lab is configured via `configs/lab_config.yml`. Key configuration sections:

### Network Topology

```yaml
topology:
  devices:
    spine_switches:
      count: 2
      model: "Cisco Nexus 9000"
    tor_switches:
      count: 4
      model: "Cisco Nexus 3000"
    leaf_switches:
      count: 8
      model: "Cisco Catalyst 9300"
```

### Data Generation

```yaml
data_generation:
  bgp_telemetry:
    update_frequency: 1.0  # seconds
    base_announcements_per_second: 10
    base_withdrawals_per_second: 2
  syslog:
    base_messages_per_second: 5
    severity_distribution:
      info: 0.6
      warning: 0.25
      error: 0.1
      critical: 0.05
```

### Scaling Phases

```yaml
scaling:
  phases:
    - name: "baseline"
      duration_minutes: 5
      bgp_multiplier: 1.0
      syslog_multiplier: 1.0
    - name: "stress_test"
      duration_minutes: 10
      bgp_multiplier: 20.0
      syslog_multiplier: 10.0
```

## 🔬 Feature Extraction

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

## 📈 Monitoring and Metrics

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

## 🧪 Testing

### Component Tests

```bash
python virtual_lab/scripts/test_components.py
```

### Integration Tests

```bash
# Use real FRR routers with Containerlab instead
```

### Custom Test Scenarios

Modify `configs/lab_config.yml` to create custom test scenarios:

- Different network topologies
- Varying data generation rates
- Custom scaling phases
- Specific anomaly injection patterns

## 📁 Directory Structure

``` text

virtual_lab/
├── configs/
│   └── lab_config.yml          # Main configuration
├── message_bus/
│   └── nats_publisher.py       # Message bus integration
├── preprocessing/
│   └── feature_extractor.py    # Feature extraction pipeline
├── scripts/
│   ├── start_lab.py           # Quick start script
│   └── test_components.py     # Component testing
├── logs/
│   └── lab.log                # Lab execution logs
└── README.md                  # This file
```

## 🔧 Troubleshooting

### Common Issues

1. **NATS Connection Failed**
   - Ensure NATS server is running
   - Check connection configuration in `lab_config.yml`

2. **Import Errors**
   - Run from project root directory
   - Ensure all dependencies are installed

3. **Configuration Errors**
   - Validate YAML syntax
   - Check file paths are correct

4. **Performance Issues**
   - Reduce scaling multipliers
   - Decrease data generation rates
   - Use smaller network topologies

## 📚 References

- **Feltin, T., et al. (2023)**: "Understanding Semantics in Feature Selection for Fault Diagnosis in Network Telemetry Data"
- **Matrix Profile**: For time series anomaly detection
- **NATS**: High-performance messaging system
- **BGP**: Border Gateway Protocol specifications

## 🤝 Contributing

To extend the virtual lab:

1. **Add New Data Sources**: Extend `TelemetryGenerator`
2. **New Feature Types**: Modify `SemanticFeatureExtractor`
3. **Custom Anomalies**: Extend `NetworkSwitch` anomaly injection
4. **Additional Scaling**: Modify `ScalingController` phases

## 📄 License

This virtual lab is part of the BGP Anomaly Detection project and follows the same licensing terms.
