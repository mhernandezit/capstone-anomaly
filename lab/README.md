# Lab Environment

This directory contains the containerlab network topology and testing environment for the anomaly detection pipeline.

## Directory Structure

### `containerlab/`
Containerlab topology configurations:
- `frr-bgp-topology.clab.yml` - **Working topology** (5 devices: spine-01, spine-02, tor-01, tor-02, edge-01)
- `frr-bgp-topology-expanded.clab.yml` - Expanded topology (20 devices)
- `clab-frr-bgp-topology/` - Runtime topology data

### `configs/`
Network device configurations:
- `frr/` - FRR router configurations for working topology
  - `spine-01/`, `spine-02/` - Spine router configs
  - `tor-01/`, `tor-02/` - ToR switch configs  
  - `edge-01/` - Edge router config

### `scripts/`
Organized scripts for lab management and testing:
- `lab-management/` - Deploy/destroy lab topologies
- `bgp-monitoring/` - BGP monitoring and data collection
- `snmp-simulation/` - SNMP metric generation
- `failure-injection/` - Failure scenario testing
- `configuration/` - Network configuration utilities

### `data/`
Generated data files:
- `bgp_updates.jsonl` - BGP update messages
- `failure_events.jsonl` - Failure injection events
- `gobmp_pipeline_messages.jsonl` - goBMP collector data
- `snmp_metrics.jsonl` - SNMP simulation data

### `tools/`
Additional tools and utilities:
- `bgp-simulator.py` - BGP update simulator
- `bmp/` - goBMP collector and integration tools

## Quick Start

1. **Deploy the lab:**
   ```bash
   cd scripts/lab-management
   ./deploy-lab.sh
   ```

2. **Configure BGP monitoring:**
   ```bash
   cd scripts/bgp-monitoring  
   ./configure-bmp-sessions.sh
   ```

3. **Start SNMP simulation:**
   ```bash
   cd scripts/snmp-simulation
   python3 snmp_simulator.py
   ```

4. **Test failure scenarios:**
   ```bash
   cd scripts/failure-injection
   python3 test-failure-injection.py
   ```

## Working Configuration

The main working topology is `containerlab/frr-bgp-topology.clab.yml` which uses:
- FRR (Free Range Routing) for BGP
- 5 devices: spine-01, spine-02, tor-01, tor-02, edge-01
- Proper FRR configuration files in `configs/frr/`

**Deploy command:**
```bash
wsl -e bash -c "cd /mnt/c/Users/PC/Documents/GitHub/capstone-anomaly/lab && clab deploy --reconfigure --topo containerlab/frr-bgp-topology.clab.yml"
```

## Verification

Check that the lab is running:
```bash
docker ps | grep clab-frr-bgp-topology
docker exec clab-frr-bgp-topology-spine-01 vtysh -c "show bgp summary"
```

## Integration with Existing Pipeline

The lab integrates with your existing anomaly detection pipeline:

```
Containerlab Network → BMP Collector → NATS → Your Existing Pipeline
                    → SNMP Simulator → NATS → Your Existing Pipeline
```

### Key Integration Points

1. **BGP Updates**: goBMP collector sends BGP updates to your existing NATS message bus
2. **SNMP Metrics**: SNMP simulator generates metrics compatible with your existing SNMP pipeline  
3. **Topology Awareness**: Uses your existing topology configuration
4. **Matrix Profile**: BGP updates flow through your existing Matrix Profile detector
5. **Isolation Forest**: SNMP metrics flow through your existing Isolation Forest detector
6. **Multimodal Correlation**: Your existing correlation agent processes both data streams

## Network Topology

Based on your topology configuration:

- **2 Spine Routers**: Core infrastructure (ASN 65001, 65002)
- **2 ToR Switches**: Distribution layer (ASN 65101, 65102)  
- **1 Edge Router**: External connectivity (ASN 65200)
- **goBMP Collector**: Production-ready BMP collector
- **SNMP Simulator**: Generates device metrics

## Failure Scenarios

The lab supports coordinated failure scenarios:

- **BGP Flapping**: Triggers Matrix Profile detection
- **Link Failures**: Triggers both BGP and SNMP alerts
- **Hardware Degradation**: Triggers Isolation Forest detection
- **Route Leaks**: Triggers BGP anomaly detection
- **Multimodal Failures**: Coordinated BGP and SNMP failures

## Benefits

1. **Real Network Traffic**: Containerlab provides realistic network behavior
2. **Existing Pipeline**: No changes needed to your ML algorithms
3. **Coordinated Failures**: Can inject failures that affect both BGP and SNMP
4. **Topology Awareness**: Uses your existing topology configuration
5. **Production-Ready**: Tests your pipeline with realistic network conditions