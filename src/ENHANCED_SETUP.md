# Enhanced Multi-Modal Pipeline Setup Guide

This guide helps you set up and run the enhanced network failure detection pipeline that addresses the professor's feedback to expand beyond BGP-only events.

## 🎯 What's New

The enhanced pipeline now detects:

- **Hardware failures** (bad parts, memory issues, CPU problems)
- **Cable/optics issues** (fiber breaks, transceiver degradation) 
- **Environmental problems** (thermal runaway, power instability)
- **Broader routing events** (OSPF, IS-IS, policy issues)

## 🚀 Quick Setup

### 1. Install Dependencies

```bash
# Install enhanced requirements (includes SNMP libraries)
pip install -r requirements.txt

# Verify SNMP simulation library
python -c "import snmpsim; print('snmpsim installed successfully')"
```

### 2. Start NATS Message Bus

```bash
# Using Docker (recommended)
docker run -d --name nats-server -p 4222:4222 nats:latest

# Or install locally
# See: https://docs.nats.io/running-a-nats-service/introduction/installation
```

### 3. Run the Enhanced Pipeline

#### Option A: Demo Mode (Recommended for Testing)
```bash
python src/run_enhanced_pipeline.py --demo-mode
```

This will:
- Show detailed capability overview
- Display failure scenarios being simulated
- Provide real-time statistics and alerts
- Demonstrate multi-modal correlation

#### Option B: Production Mode
```bash
python src/run_enhanced_pipeline.py
```

#### Option C: Individual Components
```bash
# Just SNMP hardware failure simulation
python src/simulators/snmp_simulator.py

# Multi-modal integration
python src/integration/multi_modal_pipeline.py
```

## 📊 What You'll See

### Console Output
```
🌟 Enhanced Network Failure Detection System
============================================================

Addressing Professor's Feedback:
✅ Expanded beyond BGP-only events
✅ Added hardware failure detection  
✅ Included cable/optics monitoring
✅ Environmental anomaly detection
✅ Multi-modal data correlation

🎯 Enhanced Failure Detection Capabilities
============================================================

📡 Data Sources:
  • BGP Updates (existing)
  • Syslog Messages (existing)  
  • SNMP Metrics (NEW)
  • Environmental Sensors (NEW)

🔍 Failure Types Detected:
  Hardware Layer (NEW):
    - Optical transceiver failures
    - Memory pressure and leaks
    - CPU thermal throttling
    - Storage subsystem issues

  Physical Layer (NEW):
    - Cable degradation/breaks
    - Connector contamination
    - Signal attenuation
    - Intermittent connections

  Environmental (NEW):
    - Thermal runaway
    - Power supply instability
    - Cooling system failures
    - Humidity/dust issues
```

### Real-Time Alerts
```
📊 Pipeline Statistics (Runtime: 2.3 min)
   BGP Events: 1,245
   SNMP Metrics: 3,678
   Syslog Messages: 892
   Alerts Generated: 7
   Multi-Modal Detections: 3

🚨 ALERT: Multi-Modal Detection
   Failure Type: hardware/optical_degradation
   Confidence: 0.82
   Affected Devices: ['dc1-tor-01']
   Contributing Signals:
     - SNMP interface errors (0.75)
     - BGP convergence delay (0.45)
     - Syslog optical warnings (0.63)
   Recommended Actions:
     - Check optical power levels
     - Inspect fiber connections
     - Consider transceiver replacement
```

## 🔧 Configuration

### Main Configuration
Edit `src/configs/multi_modal_config.yml` to customize:

```yaml
# Alert thresholds
alert_thresholds:
  bgp_only: 0.7
  hardware_only: 0.6
  multi_modal: 0.5

# Failure scenarios to simulate
failure_taxonomy:
  hardware:
    optical:
      - transceiver_degradation
      - laser_failure
      - wavelength_drift
    memory:
      - memory_pressure
      - ecc_errors
      - module_failure
```

### SNMP Simulation
Edit `src/configs/snmp_config.yml` to customize hardware failure scenarios:

```yaml
failure_injection:
  enabled: true
  scenario_probability: 0.08
  max_concurrent_scenarios: 4
  
  scenario_weights:
    optical_degradation: 0.25
    memory_pressure: 0.15
    thermal_runaway: 0.15
    power_supply_degradation: 0.10
```

## 🧪 Testing Different Failure Types

### Test Optical Degradation
The system will simulate gradual optical power loss:
- Interface error rates increase
- Traffic throughput decreases
- BGP convergence may be affected
- Expected detection: 2-3 minutes

### Test Memory Pressure
Simulates memory exhaustion affecting routing:
- Memory utilization climbs to 90%+
- CPU usage increases due to swapping
- BGP route processing delays
- Expected detection: 1-2 minutes

### Test Thermal Issues
Simulates overheating scenarios:
- Temperature sensors show climbing values
- Fan speeds increase to compensate
- CPU thermal throttling may occur
- Expected detection: 3-4 minutes

### Test Cable Issues
Simulates intermittent cable connections:
- Periodic interface flapping
- Burst error patterns
- Link status oscillations
- Expected detection: 1-2 minutes

## 📈 Monitoring and Validation

### View Real-Time Statistics
The pipeline logs comprehensive statistics every 30 seconds:
- Events processed per data source
- Multi-modal correlation detections
- Alert generation rates
- Simulation scenario status

### Validate Multi-Modal Detection
Look for alerts that show:
- **Multiple contributing signals** (BGP + SNMP + Syslog)
- **Temporal correlation** (events happening close in time)
- **Spatial correlation** (related devices affected)
- **Root cause classification** (specific failure type identified)

## 🎓 Academic Value

This enhanced system demonstrates:

1. **Comprehensive Failure Coverage**: Beyond just BGP routing issues
2. **Multi-Modal Data Fusion**: Correlation across different data types
3. **Realistic Simulation**: Hardware failures that containerlab can't directly simulate
4. **Practical Applicability**: Real-world network operation scenarios
5. **Advanced ML Techniques**: Cross-modal correlation and anomaly detection

## 🚨 Troubleshooting

### NATS Connection Issues
```bash
# Check if NATS is running
docker ps | grep nats

# View NATS logs
docker logs nats-server
```

### SNMP Simulation Not Starting
```bash
# Test SNMP libraries
python -c "from pysnmp.hlapi import *; print('SNMP OK')"
python -c "import snmpsim; print('snmpsim OK')"
```

### No Multi-Modal Alerts
- Check that all data sources are generating events
- Verify correlation time windows in configuration
- Ensure alert thresholds are appropriate for your scenario

### Performance Issues
- Reduce `scenario_probability` in SNMP config
- Increase `bin_seconds` for less frequent processing
- Limit `max_concurrent_scenarios`

## 📚 Next Steps

1. **Run the demo** to see all capabilities
2. **Customize failure scenarios** for your specific use case
3. **Integrate with your containerlab topology**
4. **Extend the feature extraction** for additional data sources
5. **Tune alert thresholds** based on your environment

This enhanced pipeline provides a comprehensive foundation for network failure detection that goes far beyond BGP-only monitoring, directly addressing your professor's feedback while maintaining practical applicability.
