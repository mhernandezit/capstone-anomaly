# BGP Anomaly Detection Lab

A complete containerlab-based virtual lab environment for testing BGP anomaly detection systems with real FRR routers, authentic BGP sessions, and realistic failure scenarios.

## 🏗️ Lab Architecture

```text
┌─────────────┐    ┌─────────────┐
│   Spine-01  │────│   Spine-02  │
│   (AS65001) │    │   (AS65001) │
└─────┬───────┘    └─────┬───────┘
      │                  │
      │                  │
┌─────▼───────┐    ┌─────▼───────┐
│    ToR-01   │    │    ToR-02   │
│   (AS65002) │    │   (AS65002) │
└─────┬───────┘    └─────┬───────┘
      │                  │
      │                  │
┌─────▼───────┐    ┌─────▼───────┐
│   Edge-01   │    │   Edge-02   │
│   (AS65003) │    │   (AS65003) │
└─────┬───────┘    └─────┬───────┘
      │                  │
┌─────▼───────┐    ┌─────▼───────┐
│  Server-01  │    │  Server-03  │
│  (AS65010)  │    │  (AS65012)  │
└─────────────┘    └─────────────┘
┌─────▼───────┐    ┌─────▼───────┐
│  Server-02  │    │  Server-04  │
│  (AS65011)  │    │  (AS65013)  │
└─────────────┘    └─────────────┘
```

## 🚀 Quick Start

### Prerequisites

1. **Docker** - Running and accessible
2. **Containerlab** - Install from [containerlab.dev](https://containerlab.dev/install/)
3. **Python 3.8+** - For ML integration

### Deploy the Lab

```bash
# 1. Deploy the lab
cd lab
./scripts/deploy.sh

# 2. Check BGP status
./scripts/check-bgp.sh

# 3. Monitor logs
./scripts/monitor-logs.sh
```

### Connect to Your ML Pipeline

```bash
# Build BMP collector Docker image
./scripts/build-bmp-collector.sh

# Deploy the lab (includes BMP collector)
./scripts/deploy.sh

# Run the integration script
python scripts/integrate-with-ml.py
```

## 🔧 Lab Components

### Network Devices

- **2x Spine Switches** (AS 65001) - Core layer with iBGP
- **2x ToR Switches** (AS 65002) - Aggregation layer
- **2x Edge Routers** (AS 65003) - Edge layer
- **4x Servers** (AS 65010-65013) - Host layer with test prefixes

### Monitoring & Collection

- **BMP Collector** - Go-based BGP Monitoring Protocol collector for real-time BGP updates
- **Fluent Bit** - Log collection and forwarding
- **Log Aggregation** - Centralized logging for all devices

## 📊 What You Get

### Real BGP Data

- **Authentic BGP sessions** between real FRR instances
- **Real-time BGP updates** via BMP (BGP Monitoring Protocol)
- **Actual routing tables** and path information
- **True BGP timers** and session management
- **Live BGP monitoring** with Go-based BMP collector

### Realistic Syslog

- **FRR daemon logs** with authentic message formats
- **Interface status changes** and BGP neighbor events
- **System events** and error conditions
- **Proper severity levels** and timestamps

### Failure Scenarios

- **Link failures** - Interface down/up events
- **Router crashes** - Complete device failures
- **BGP session resets** - Neighbor relationship issues
- **Interface instability** - Flapping conditions

## 🎯 Usage Scenarios

### 1. **Algorithm Testing**

Test your ML models with real BGP data:

```bash
# Deploy lab
./scripts/deploy.sh

# Run your ML pipeline
python scripts/integrate-with-ml.py

# Inject failures while monitoring
./scripts/inject-failures.sh
```

### 2. **Performance Benchmarking**

Measure detection accuracy and speed:

```bash
# Monitor performance metrics
./scripts/monitor-logs.sh

# Check BGP convergence times
./scripts/check-bgp.sh
```

### 3. **Feature Validation**

Validate feature extraction approaches:

```bash
# Monitor specific BGP events
grep "BGP" logs/*/frr.log

# Analyze interface events
grep "interface" logs/*/frr.log
```

### 4. **Anomaly Injection**

Test with known failure patterns:

```bash
# Interactive failure injection
./scripts/inject-failures.sh

# Automated failure sequences
# (Customize scripts/inject-failures.sh)
```

## 🔍 Monitoring & Debugging

### Check Lab Status

```bash
# BGP neighbor status
./scripts/check-bgp.sh

# Container status
docker ps --filter "name=clab-bgp-anomaly-lab"

# Interface status
docker exec clab-bgp-anomaly-lab-spine-01 ip link show
```

### Monitor Logs

```bash
# All logs in real-time
./scripts/monitor-logs.sh

# Specific device logs
docker exec clab-bgp-anomaly-lab-spine-01 tail -f /var/log/frr/frr.log

# BGP events only
grep "BGP" logs/*/frr.log
```

### Debug BGP Sessions

```bash
# Check BGP neighbors
docker exec clab-bgp-anomaly-lab-spine-01 vtysh -c "show bgp summary"

# Check BGP routes
docker exec clab-bgp-anomaly-lab-spine-01 vtysh -c "show bgp ipv4 unicast"

# Check BGP configuration
docker exec clab-bgp-anomaly-lab-spine-01 vtysh -c "show running-config"
```

## 🛠️ Customization

### Modify Network Topology

Edit `topo.clab.yml` to:

- Add more devices
- Change AS numbers
- Modify network addressing
- Add additional links

### Customize BGP Configuration

Edit `configs/*/frr.conf` to:

- Change BGP policies
- Modify route advertisements
- Adjust BGP timers
- Add route filters

### Add Custom Failure Scenarios

Edit `scripts/inject-failures.sh` to:

- Add new failure types
- Create automated sequences
- Implement custom test scenarios

## 📁 Directory Structure

```text
lab/
├── topo.clab.yml              # Containerlab topology
├── configs/                   # FRR configurations
│   ├── spine-01/frr.conf
│   ├── spine-02/frr.conf
│   ├── tor-01/frr.conf
│   ├── tor-02/frr.conf
│   ├── edge-01/frr.conf
│   ├── edge-02/frr.conf
│   ├── server-01/frr.conf
│   ├── server-02/frr.conf
│   ├── server-03/frr.conf
│   ├── server-04/frr.conf
│   └── common/                # Common FRR configs
├── scripts/                   # Management scripts
│   ├── deploy.sh
│   ├── destroy.sh
│   ├── check-bgp.sh
│   ├── inject-failures.sh
│   ├── monitor-logs.sh
│   ├── bgp_collector.py
│   ├── build-bmp-collector.sh
│   └── integrate-with-ml.py
├── monitoring/                # Monitoring configs
│   └── fluent-bit.conf
├── logs/                      # Log files
└── README.md
```

## 🔧 Troubleshooting

### Common Issues

1. **Lab won't start**
   - Check Docker is running
   - Verify containerlab is installed
   - Check port conflicts

2. **BGP sessions not established**
   - Check interface configurations
   - Verify AS numbers match
   - Check network connectivity

3. **ML integration fails**
   - Verify Python dependencies
   - Check import paths
   - Ensure lab is running

### Debug Commands

```bash
# Check container logs
docker logs clab-bgp-anomaly-lab-spine-01

# Check network connectivity
docker exec clab-bgp-anomaly-lab-spine-01 ping 10.0.2.2

# Check BGP configuration
docker exec clab-bgp-anomaly-lab-spine-01 vtysh -c "show running-config"
```

## 🎓 Research Applications

This lab is perfect for:

1. **Algorithm Validation** - Test ML models with real data
2. **Performance Testing** - Measure detection accuracy and speed
3. **Feature Analysis** - Validate feature extraction approaches
4. **Scalability Studies** - Test under various load conditions
5. **Failure Analysis** - Study BGP behavior under failures

## 📚 Next Steps

1. **Deploy the lab** and verify BGP sessions are established
2. **Run the ML integration** to see real-time anomaly detection
3. **Inject failures** to test your detection algorithms
4. **Customize the lab** for your specific research needs
5. **Integrate with your existing pipeline** for comprehensive testing

## 🤝 Contributing

To extend the lab:

1. **Add new devices** - Modify `topo.clab.yml`
2. **Create new failure scenarios** - Edit `scripts/inject-failures.sh`
3. **Add monitoring** - Extend `monitoring/` directory
4. **Improve integration** - Enhance `scripts/integrate-with-ml.py`

This lab provides a complete, realistic environment for testing and validating BGP anomaly detection systems with real network protocols and authentic data patterns.
