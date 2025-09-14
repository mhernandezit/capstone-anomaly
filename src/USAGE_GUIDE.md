# BGP Anomaly Detection Lab Usage Guide

This guide describes how to use the containerlab-based lab environment to generate BGP events and analyze them with machine learning models.

## Lab Usage Methods

### 1. Quick Demo

```bash
cd lab
./scripts/deploy.sh
./scripts/check-bgp.sh
```

This deploys the containerlab environment with real FRR routers.

### 2. Lab + ML Integration

```bash
cd lab
./scripts/deploy.sh
python scripts/integrate-with-ml.py
```

This integrates the lab with ML pipeline components.

### 3. Full Lab with Failure Testing

```bash
cd lab
./scripts/deploy.sh
./scripts/inject-failures.sh
```

This runs the full lab with failure injection capabilities.

## Method 2: Lab + ML Integration (Recommended)

This is the most practical way to use the lab with machine learning models.

### How it works

1. **Deploy Lab**: Containerlab creates real FRR routers with authentic BGP sessions
2. **Collect Data**: BGP collector captures real BGP updates and syslog messages
3. **Convert Format**: Events are converted to BGPUpdate format
4. **Process with ML**: Events flow through FeatureAggregator and GPUMPDetector
5. **Analyze Results**: Matrix Profile analysis detects anomalies in real-time

### Example Output

```text
🚀 Starting lab event generation and ML analysis for 2 minutes
📊 Cycle 1 - Collecting BGP updates...
  Generated 15 BGP updates from real FRR routers
  Processing feature bin: 1234567890 - 1234567920
  Normal operation - Score: 1.2
📊 Cycle 2 - Collecting BGP updates...
  Generated 12 BGP updates from real FRR routers
  Processing feature bin: 1234567920 - 1234567950
🚨 ANOMALY DETECTED!
  Confidence: 0.85
  Detected series: ['wdr_total']
  Overall score: 3.2
```

## Lab Customization

### Modify Network Topology

Edit `lab/topo.clab.yml` to add more devices:

```yaml
name: bgp-anomaly-lab
topology:
  nodes:
    spine-03:  # Add more spine switches
      kind: linux
      image: frrouting/frr:v8.4.0
    tor-03:    # Add more ToR switches
      kind: linux
      image: frrouting/frr:v8.4.0
```

### Customize BGP Configuration

Edit `lab/configs/*/frr.conf` to modify BGP behavior:

```bash
# Example: Add more prefixes to advertise
router bgp 65001
  network 192.168.100.0/24
  network 192.168.101.0/24
  neighbor 10.0.1.2 remote-as 65002
```

### Add Custom Failure Scenarios

Edit `lab/scripts/inject-failures.sh` to add new failure types:

```bash
# Example: Add prefix hijacking scenario
inject_prefix_hijack() {
    echo "Injecting prefix hijack..."
    docker exec clab-bgp-anomaly-lab-server-01 vtysh -c "conf t" -c "router bgp 65010" -c "network 10.0.0.0/8"
}

## Data Flow

```text
Containerlab Environment
        ↓
   Real FRR Routers (BGP sessions)
        ↓
   BGP Collector (GoBGP)
        ↓
   Format Conversion (BGPUpdate)
        ↓
   Feature Aggregator
        ↓
   Matrix Profile Detector
        ↓
   Anomaly Detection Results
```

## Generated Events

### Real BGP Updates (from FRR routers)

- **Announcements**: Real prefix advertisements from FRR
- **Withdrawals**: Actual prefix withdrawals from FRR
- **Session Events**: Authentic BGP neighbor up/down events
- **Path Changes**: Real AS path modifications
- **Route Updates**: Actual routing table changes

### Real Syslog Messages (from FRR daemons)

- **BGP Daemon Logs**: Authentic FRR BGP daemon messages
- **Interface Events**: Real interface up/down status changes
- **BGP Events**: Actual neighbor state changes
- **System Events**: Real system and daemon events
- **Error Conditions**: Authentic error and warning messages

### Network Topology

- **10 Real FRR Routers**: 2 spines, 2 ToRs, 2 edges, 4 servers
- **Authentic BGP Sessions**: Real iBGP and eBGP relationships
- **Real Network Interfaces**: Actual Linux network interfaces
- **True BGP Timers**: Real BGP keepalive and hold timers

## Advanced Usage

### Custom Network Topology

Edit `lab/topo.clab.yml` to add more devices:

```yaml
name: bgp-anomaly-lab
topology:
  nodes:
    spine-03:  # Add more spine switches
      kind: linux
      image: frrouting/frr:v8.4.0
    tor-03:    # Add more ToR switches
      kind: linux
      image: frrouting/frr:v8.4.0
  links:
    - endpoints: ["spine-03:eth1", "tor-03:eth1"]
```

### Custom BGP Configuration

Edit `lab/configs/*/frr.conf` to modify BGP behavior:

```bash
# Example: Add more prefixes and modify policies
router bgp 65001
  network 192.168.100.0/24
  neighbor 10.0.1.2 remote-as 65002
  neighbor 10.0.1.2 route-map OUT out
route-map OUT permit 10
  set community 65001:100
```

### Code Integration

```python
# The lab provides BGP data through the collector
# ML pipeline processes BGP updates

from lab.scripts.integrate_with_ml import LabMLIntegration

integration = LabMLIntegration()
await integration.run_analysis()
# Process BGP events with ML pipeline
```

## Monitoring and Statistics

The lab provides comprehensive monitoring:

- **BGP Updates**: Actual BGP messages from FRR routers
- **BGP Session Status**: Live neighbor relationship monitoring
- **Interface Statistics**: Network interface metrics
- **ML Pipeline Performance**: Detection accuracy and speed
- **Failure Injection**: Controlled anomaly testing
- **Log Aggregation**: Centralized logging from all devices

## Troubleshooting

### Common Issues

1. **Lab Won't Start**
   - Check Docker is running: `docker ps`
   - Verify containerlab is installed: `clab version`
   - Check port conflicts

2. **BGP Sessions Not Established**
   - Check BGP status: `./scripts/check-bgp.sh`
   - Verify interface configurations
   - Check AS numbers match in configs

3. **ML Pipeline Not Working**
   - Ensure ML components are available
   - Check the import paths in the integration script
   - Verify the lab is running: `docker ps --filter "name=clab-bgp-anomaly-lab"`

### Debug Commands

```bash
# Check BGP status
./scripts/check-bgp.sh

# Monitor logs in real-time
./scripts/monitor-logs.sh

# Check specific router logs
docker exec clab-bgp-anomaly-lab-spine-01 tail -f /var/log/frr/frr.log

# Check BGP neighbors
docker exec clab-bgp-anomaly-lab-spine-01 vtysh -c "show bgp summary"
```

## Research Applications

This containerlab-based lab is perfect for:

1. **Algorithm Testing**: Test ML models with BGP data from FRR routers
2. **Performance Benchmarking**: Measure detection accuracy and speed with authentic data
3. **Scalability Testing**: Test under increasing load conditions with real network protocols
4. **Feature Validation**: Validate feature extraction approaches with real BGP updates
5. **Failure Analysis**: Study BGP behavior under controlled failure scenarios
6. **Protocol Validation**: Test with authentic BGP message formats and timers

## Next Steps

1. **Deploy the Lab**: Run `cd lab && ./scripts/deploy.sh` to start the containerlab environment
2. **Verify BGP**: Check `./scripts/check-bgp.sh` to ensure BGP sessions are established
3. **Integrate ML**: Use `python scripts/integrate-with-ml.py` to connect with ML pipeline
4. **Test Failures**: Run `./scripts/inject-failures.sh` to test with controlled anomalies
5. **Customize**: Modify `topo.clab.yml` and `configs/*/frr.conf` for research needs
6. **Research**: Use the lab for capstone research with BGP data

The containerlab-based lab provides a complete testing environment with FRR routers, BGP sessions, and network telemetry data. This allows testing, validation, and improvement of BGP anomaly detection systems under controlled conditions with network protocols.
