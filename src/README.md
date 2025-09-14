# BGP Anomaly Detection ML Pipeline

This Python-based ML pipeline provides real-time BGP anomaly detection using streaming data from a containerlab network environment. It processes BGP updates via NATS messaging, extracts features, and performs anomaly detection using Matrix Profile and other ML techniques.

## 🏗️ Architecture

The ML pipeline consists of several key components:

### 1. Data Ingestion (`ingest/`)

- **Purpose**: Receives BGP data from the containerlab environment
- **Technology**: NATS message bus integration
- **Sources**:
  - BGP updates from Go BMP collector
  - Syslog messages from Fluent Bit
  - Real-time streaming data

### 2. Feature Extraction (`features/`)

- **Purpose**: Extracts and aggregates features from BGP data
- **Technology**: `FeatureAggregator` class
- **Features**:
  - BGP announcement/withdrawal rates
  - AS path analysis and churn
  - Peer diversity metrics
  - Temporal feature bins

### 3. Message Bus (`message_bus/`)

- **Purpose**: Handles data streaming between components
- **Technology**: NATS message bus
- **Subjects**:
  - `bgp.updates` - BGP update messages from BMP collector
  - `syslog.messages` - Syslog messages from Fluent Bit
  - `bgp.events` - Anomaly detection events
  - `anomaly.alerts` - Alert notifications

### 4. ML Models (`models/`)

- **Purpose**: Anomaly detection using various ML techniques
- **Technologies**:
  - Matrix Profile (GPU-accelerated)
  - LSTM networks
  - Isolation Forest
- **Features**:
  - Real-time streaming detection
  - GPU acceleration support
  - Multiple detection algorithms

### 5. Dual-Signal Pipeline (`dual_signal_pipeline.py`)

- **Purpose**: Combines BGP and syslog data for enhanced detection
- **Features**:
  - Correlates BGP updates with syslog messages
  - Enhanced failure detection accuracy
  - Improved localization capabilities

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

2. **Run the dual-signal pipeline**:

   ```bash
   python dual_signal_pipeline.py
   ```

3. **Run with lab integration**:

   ```bash
   cd ../lab
   python scripts/integrate-with-ml.py
   ```

4. **Access the dashboard**:

   ```bash
   # Start the dashboard
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

```
virtual_lab/
├── configs/
│   └── lab_config.yml          # Main configuration
├── switch_emulator/
│   └── (removed - using real FRR routers instead)
├── message_bus/
│   └── nats_publisher.py       # Message bus integration
├── preprocessing/
│   └── feature_extractor.py    # Feature extraction pipeline
├── scripts/
│   ├── (removed - using real FRR routers instead)
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

### Debug Mode

Run with debug logging:

```bash
# Use real FRR routers with Containerlab instead
```

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
