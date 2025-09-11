# Virtual Lab for BGP Anomaly Detection

This virtual lab environment provides a comprehensive testing platform for BGP anomaly detection systems. It generates realistic network telemetry data, processes it through a feature extraction pipeline, and tests the ML pipeline under progressively increasing load conditions.

## 🏗️ Architecture

The virtual lab consists of several key components:

### 1. Network Switch Emulator (`switch_emulator/`)
- **Purpose**: Emulates realistic network switches (spine, TOR, leaf)
- **Features**: 
  - BGP peer relationships and updates
  - Interface status changes
  - System events and errors
  - Anomaly injection capabilities

### 2. Data Generators (`data_generators/`)
- **Purpose**: Generates realistic telemetry data streams
- **Types**:
  - BGP updates and withdrawals
  - Syslog messages with various severities
  - System metrics (CPU, memory, temperature)
  - Interface statistics
  - BGP-specific metrics

### 3. Message Bus (`message_bus/`)
- **Purpose**: Handles data streaming between components
- **Technology**: NATS message bus
- **Subjects**:
  - `bgp.updates` - BGP update messages
  - `syslog.messages` - Syslog messages
  - `telemetry.data` - System and interface metrics
  - `features.processed` - Extracted features
  - `anomaly.alerts` - Anomaly alerts

### 4. Preprocessing Pipeline (`preprocessing/`)
- **Purpose**: Feature extraction and data preprocessing
- **Based on**: Feltin 2023 paper on feature selection for network telemetry
- **Features**:
  - Multi-scale temporal feature extraction
  - Semantic understanding of network events
  - Correlation analysis between data sources
  - Feature selection using mutual information

### 5. Scaling Controller (`scripts/`)
- **Purpose**: Manages progressive scaling of data generation
- **Phases**:
  - Baseline (1x load)
  - Light load (2x BGP, 1.5x syslog)
  - Medium load (5x BGP, 3x syslog)
  - Heavy load (10x BGP, 5x syslog)
  - Stress test (20x BGP, 10x syslog)

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

### Running the Lab

1. **Test Components** (recommended first):
   ```bash
   python virtual_lab/scripts/test_components.py
   ```

2. **Quick Start** (5-minute test run):
   ```bash
   python virtual_lab/scripts/start_lab.py
   ```

3. **Full Lab Run**:
   ```bash
   python virtual_lab/scripts/lab_orchestrator.py --duration 30 --export-results results.json
   ```

4. **Custom Configuration**:
   ```bash
   python virtual_lab/scripts/lab_orchestrator.py --config custom_config.yml --duration 60
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
python virtual_lab/scripts/lab_orchestrator.py --duration 5
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
│   └── network_switch.py       # Network switch emulation
├── data_generators/
│   └── telemetry_generator.py  # Data generation
├── message_bus/
│   └── nats_publisher.py       # Message bus integration
├── preprocessing/
│   └── feature_extractor.py    # Feature extraction pipeline
├── scripts/
│   ├── lab_orchestrator.py     # Main orchestrator
│   ├── scaling_controller.py   # Scaling management
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
python virtual_lab/scripts/lab_orchestrator.py --log-level DEBUG
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
