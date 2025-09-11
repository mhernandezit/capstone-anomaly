# Virtual Lab Usage Guide

This guide shows you how to use the virtual lab to generate events and analyze them with your ML models.

## 🎯 Three Ways to Use the Lab

### 1. **Quick Demo** - See the lab in action
```bash
python virtual_lab/scripts/demo_lab.py
```
This runs a standalone demo without external dependencies.

### 2. **Lab + ML Integration** - Generate events and analyze with your ML models
```bash
python virtual_lab/scripts/run_lab_with_ml.py
```
This integrates the lab with your existing ML pipeline.

### 3. **Full Lab Environment** - Complete testing environment
```bash
python virtual_lab/scripts/setup_lab.py
python virtual_lab/scripts/start_lab.py
```
This runs the full lab with message bus and scaling.

## 🔬 Method 2: Lab + ML Integration (Recommended)

This is the most practical way to use the lab with your existing ML models.

### How it works:

1. **Generate Events**: Virtual lab creates realistic BGP updates, syslog messages, and system metrics
2. **Convert Format**: Events are converted to your existing BGPUpdate format
3. **Process with ML**: Events flow through your FeatureAggregator and GPUMPDetector
4. **Analyze Results**: Matrix Profile analysis detects anomalies in real-time

### Example Output:
```
🚀 Starting lab event generation and ML analysis for 2 minutes
📊 Cycle 1 - Generating events...
  Generated 15 BGP updates
  Processing feature bin: 1234567890 - 1234567920
  Normal operation - Score: 1.2
📊 Cycle 2 - Generating events...
  Generated 12 BGP updates
  Processing feature bin: 1234567920 - 1234567950
🚨 ANOMALY DETECTED!
  Confidence: 0.85
  Detected series: ['wdr_total']
  Overall score: 3.2
```

## 🛠️ Customizing the Lab

### Modify Data Generation
Edit `virtual_lab/configs/lab_config.yml`:

```yaml
data_generation:
  bgp_telemetry:
    update_frequency: 0.5  # More frequent updates
    base_announcements_per_second: 20  # Higher rate
    base_withdrawals_per_second: 5
  syslog:
    base_messages_per_second: 10  # More syslog messages
```

### Add More Anomalies
```yaml
data_generation:
  bgp_telemetry:
    anomaly_injection:
      enabled: true
      frequency: 0.2  # 20% chance of anomaly
      types: ["link_failure", "bgp_reset", "prefix_hijack", "route_flap"]
```

### Scale Up the Load
```yaml
scaling:
  phases:
    - name: "baseline"
      duration_minutes: 2
      bgp_multiplier: 1.0
    - name: "stress_test"
      duration_minutes: 3
      bgp_multiplier: 10.0  # 10x load
```

## 📊 Understanding the Data Flow

```
Virtual Lab Network
        ↓
   Event Generation
        ↓
   Format Conversion
        ↓
   Feature Aggregator (your existing code)
        ↓
   Matrix Profile Detector (your existing code)
        ↓
   Anomaly Detection Results
```

## 🔍 What Events Are Generated

### BGP Updates
- **Announcements**: New prefix advertisements
- **Withdrawals**: Prefix withdrawals
- **Session Events**: BGP neighbor up/down
- **Path Changes**: AS path modifications

### Syslog Messages
- **Interface Events**: Up/down status changes
- **BGP Events**: Neighbor state changes
- **System Events**: CPU, memory, temperature
- **Security Events**: Login attempts, access denials

### System Metrics
- **CPU Usage**: Realistic utilization patterns
- **Memory Usage**: Memory consumption trends
- **Temperature**: Thermal monitoring
- **Interface Stats**: Traffic, errors, utilization

## 🎛️ Advanced Usage

### Custom Network Topology
```yaml
topology:
  devices:
    spine_switches:
      count: 4  # More spine switches
    tor_switches:
      count: 8  # More TOR switches
    leaf_switches:
      count: 16  # More leaf switches
```

### Custom Feature Extraction
The lab uses the Feltin 2023 approach for feature extraction:
- Multi-scale temporal analysis
- Semantic event understanding
- Correlation between data sources
- Feature selection using mutual information

### Integration with Your Code
```python
# In your existing code, you can now do:
from virtual_lab.data_generators.telemetry_generator import TelemetryGenerator

generator = TelemetryGenerator("virtual_lab/configs/lab_config.yml")
bgp_events = await generator.generate_bgp_telemetry()
# Process bgp_events with your existing ML pipeline
```

## 📈 Monitoring and Statistics

The lab provides comprehensive statistics:
- Events generated per second
- Features extracted per second
- Anomalies detected
- ML pipeline performance
- Resource utilization

## 🚨 Troubleshooting

### Common Issues

1. **Import Errors**
   - Make sure you're running from the project root directory
   - Check that all dependencies are installed

2. **No Events Generated**
   - Check the configuration file
   - Verify the network topology settings

3. **ML Pipeline Not Working**
   - Ensure your existing ML components are available
   - Check the import paths in the integration script

### Debug Mode
```bash
python virtual_lab/scripts/run_lab_with_ml.py --log-level DEBUG
```

## 🎓 Research Applications

This virtual lab is perfect for:

1. **Algorithm Testing**: Test your ML models with realistic data
2. **Performance Benchmarking**: Measure detection accuracy and speed
3. **Scalability Testing**: Test under increasing load conditions
4. **Feature Validation**: Validate feature extraction approaches
5. **Anomaly Injection**: Test with known anomaly patterns

## 📚 Next Steps

1. **Start Simple**: Run the demo to understand the capabilities
2. **Integrate**: Use the lab + ML integration script
3. **Customize**: Modify the configuration for your needs
4. **Scale Up**: Test with higher loads and more complex scenarios
5. **Research**: Use the lab for your capstone research

The virtual lab provides a complete testing environment that generates realistic network telemetry data and integrates seamlessly with your existing ML pipeline. This allows you to test, validate, and improve your BGP anomaly detection system under controlled conditions.
