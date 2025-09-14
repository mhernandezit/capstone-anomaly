# Quick Start Guide - BGP Anomaly Detection Lab

## Lab Overview

A complete containerlab-based lab environment with:

- **Multiple FRR routers** (spines, ToRs, edges, servers, ISPs)
- **Authentic BGP sessions** between all devices
- **Real syslog messages** from FRR daemons
- **BGP collector** for data collection
- **Failure injection capabilities** for testing
- **ML pipeline integration** with machine learning models

## Quick Start Options

### Option 1: Standard Topology (Recommended for beginners)

#### 3-Step Quick Start

1. **Deploy the Lab**
2. **Check Everything is Working**
3. **Connect to ML Pipeline**

### Option 2: Expanded Topology (For advanced users)

#### 3-Step Quick Start with More Devices

1. **Deploy the Expanded Lab**
2. **Check Everything is Working**
3. **Connect to ML Pipeline**

#### Topology Comparison

| Feature | Standard Topology | Expanded Topology |
|---------|------------------|-------------------|
| **Devices** | ~10 FRR routers | ~20+ FRR routers |
| **Complexity** | Simple, focused | Complex, realistic |
| **Use Case** | Learning, basic testing | Research, production-like |
| **Resource Usage** | Lower | Higher |
| **BGP Sessions** | ~15-20 sessions | ~40+ sessions |
| **File** | `topo.clab.yml` | `topo-dc-expanded.clab.yml` |

#### 1. Deploy the Lab

```bash
cd lab
./scripts/deploy.sh
```

#### 2. Check Standard Lab Status

```bash
./scripts/check-bgp.sh
```

#### 3. Connect ML Pipeline to Standard Lab

```bash
python scripts/integrate-with-ml.py
```

### Option 2: Expanded Topology

#### 1. Deploy the Expanded Lab

```bash
cd lab
clab deploy -t topo-dc-expanded.clab.yml
```

#### 2. Check Expanded Lab Status

```bash
./scripts/check-bgp.sh
```

#### 3. Connect ML Pipeline to Expanded Lab

```bash
python scripts/integrate-with-ml.py
```

## Prerequisites

Before starting, ensure you have:

- **Docker** installed and running
- **Containerlab** installed ([install guide](https://containerlab.dev/install/))
- **Python 3.8+** for ML integration
- **Git** to clone the repository

## Process Overview

1. **BGP Updates** flow from the lab routers
2. **BGP Collector** captures and processes the updates
3. **ML pipeline** processes them in real-time
4. **Matrix Profile detection** identifies anomalies
5. **Impact scoring** classifies the severity
6. **Alerts** are generated for detected anomalies

## Failure Testing

```bash
# Interactive failure injection
./scripts/inject-failures.sh

# Choose from:
# 1. Link failures
# 2. Router crashes  
# 3. BGP session resets
# 4. Interface down events
# 5. Prefix hijacking
# 6. Route flapping
```

## Monitoring

```bash
# Watch logs in real-time
./scripts/monitor-logs.sh

# Check BGP status
./scripts/check-bgp.sh

# Start BGP collector
./scripts/collector.sh

# Follow specific logs
docker exec clab-bgp-anomaly-lab-spine-01 tail -f /var/log/frr/frr.log

# Check BGP neighbors
docker exec clab-bgp-anomaly-lab-spine-01 vtysh -c "show bgp summary"
```

## Research Applications

- **Algorithm Testing** - BGP data for ML models
- **Performance Benchmarking** - Measure detection accuracy
- **Feature Validation** - Test feature extraction approaches
- **Failure Analysis** - Study BGP behavior under failures
- **Scalability Studies** - Test under various load conditions
- **Protocol Validation** - Test with authentic BGP message formats

## Customization

- **Edit `topo.clab.yml`** - Modify network topology
- **Edit `topo-dc-expanded.clab.yml`** - Use expanded topology with more devices
- **Edit `configs/*/frr.conf`** - Change BGP configurations
- **Edit `scripts/inject-failures.sh`** - Add custom failure scenarios
- **Edit `scripts/integrate-with-ml.py`** - Modify ML integration
- **Edit `monitoring/fluent-bit.conf`** - Configure log collection

## Cleanup

```bash
# Stop and remove all lab containers
./scripts/destroy.sh

# Clean up logs (optional)
rm -rf logs/*
```

## Troubleshooting

- **Check logs**: `./scripts/monitor-logs.sh`
- **Debug BGP**: `./scripts/check-bgp.sh`
- **Check containers**: `docker ps --filter "name=clab-bgp-anomaly-lab"`
- **Check BGP neighbors**: `docker exec clab-bgp-anomaly-lab-spine-01 vtysh -c "show bgp summary"`
- **Check network connectivity**: `docker exec clab-bgp-anomaly-lab-spine-01 ping 10.0.2.2`
- **Read full docs**: `README.md`
- **View topology**: `clab graph -t topo.clab.yml`

## Advanced Usage

### Use Expanded Topology

```bash
# Deploy with more devices
clab deploy -t topo-dc-expanded.clab.yml
```

### Run Specific Tests

```bash
# Test specific failure scenarios
./scripts/inject-failures.sh --scenario link_failure

# Monitor specific devices
./scripts/monitor-logs.sh --device spine-01
```

### Integration Examples

```bash
# Run ML integration with custom parameters
python scripts/integrate-with-ml.py --duration 10 --threshold 2.5

# Run collector only
./scripts/collector.sh --output bgp_updates.json
```

---

This lab provides a complete testing environment for BGP anomaly detection research using real network protocols and authentic data patterns.
