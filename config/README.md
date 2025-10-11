# Config Directory Organization

**Last Updated**: October 10, 2025

## Purpose

This directory contains system-level configuration files for the network anomaly detection system.

## Directory Structure

```
config/
├── README.md           # This file
└── roles.yml           # Device role mapping
```

**Note**: Pipeline-specific configs are in `src/configs/`:
- `src/configs/multi_modal_config.yml` - Multimodal correlation settings
- `src/configs/snmp_config.yml` - SNMP simulator settings

## Configuration Files

### roles.yml

**Purpose**: Map device identifiers to network roles

**Contents**:

```yaml
roles:
  10.0.0.1: rr        # Route reflector
  10.0.0.2: rr
  10.0.1.1: spine     # Spine switches
  10.0.1.2: spine
  10.0.2.1: tor       # Top-of-rack
  10.0.2.2: tor
  10.0.3.1: edge      # Edge routers
  10.0.3.2: edge
  10.0.10.11: server  # Servers
  10.0.10.12: server

thresholds:
  edge_local_prefix_max: 100
  edge_local_pct_table_max: 0.01
  correlation_window_secs: 60

binning:
  bin_seconds: 30
  window_bins: 64
```

**Usage**:
- Topology triage system (`src/triage/topology_triage.py`)
- Impact scoring (`src/triage/impact.py`)
- Multimodal correlator (`src/correlation/multimodal_correlator.py`)

**Loading**:

```python
from src.triage import TopologyTriage

triage = TopologyTriage(roles_config_path="config/roles.yml")
```

## Configuration Hierarchy

### System-Level (config/)

**Purpose**: Deployment and infrastructure
- Device role mappings
- System thresholds

**Who uses**: System operators, deployment scripts

### Pipeline-Level (src/configs/)

**Purpose**: ML pipeline behavior
- Multimodal correlation parameters
- SNMP simulation settings
- Feature extraction configuration

**Who uses**: Data scientists, researchers

## Role Mapping Details

### Device Roles

| Role | Description | Criticality | Blast Radius |
|------|-------------|-------------|--------------|
| `rr` | Route Reflector | Critical | Very High |
| `spine` | Spine Switch | Critical | High |
| `edge` | Edge Router | Critical | Very High |
| `tor` | Top-of-Rack | High | Medium |
| `server` | Server/Endpoint | Low | Low |

### Adding New Devices

Edit `config/roles.yml`:

```yaml
roles:
  10.0.5.1: spine  # Add new spine switch
  10.0.6.1: tor    # Add new ToR
```

Criticality is automatically assigned based on role.

## Threshold Configuration

### Edge Prefix Thresholds

```yaml
thresholds:
  edge_local_prefix_max: 100           # Max prefixes for edge-local classification
  edge_local_pct_table_max: 0.01       # Or <1% of total routing table
  correlation_window_secs: 60          # Time window for event correlation
```

**Purpose**: Classify route announcements as edge-local vs transit

**Impact**: Affects alert priority and severity scoring

### Binning Configuration

```yaml
binning:
  bin_seconds: 30       # Feature aggregation window
  window_bins: 64       # Matrix Profile subsequence length
```

**Purpose**: Control time-series analysis granularity

**Impact**:
- `bin_seconds`: Trade-off between responsiveness and noise
- `window_bins`: Matrix Profile sensitivity to patterns

## Configuration Best Practices

### 1. Version Control

- ✅ **Track**: config files in git
- ✅ **Document**: Changes in CHANGELOG.md
- ❌ **Don't commit**: Secrets, credentials, local overrides

### 2. Environment-Specific Configs

```bash
# Development
config/roles.yml

# Production (not in repo)
config/roles.prod.yml

# Load based on environment
CONFIG_FILE=${ENV:-dev}
python app.py --config config/roles.$CONFIG_FILE.yml
```

### 3. Validation

Validate YAML before deployment:

```bash
# Check YAML syntax
python -c "import yaml; yaml.safe_load(open('config/roles.yml'))"
```

## Recent Changes (October 2025)

### Structure Cleanup ✅
- Flattened `config/configs/` → `config/`
- Removed redundant nesting
- Clearer file organization

### Documentation ✅
- Added comprehensive README
- Documented all configuration options
- Provided usage examples

## Examples

### Load Roles Configuration

```python
import yaml

with open("config/roles.yml") as f:
    config = yaml.safe_load(f)

roles = config["roles"]
thresholds = config["thresholds"]

print(f"Loaded {len(roles)} device mappings")
```

### Update Correlation Window

```yaml
# Edit config/roles.yml
thresholds:
  correlation_window_secs: 120  # Increase from 60 to 120
```

Then restart the correlation agent for changes to take effect.

### Add New Device Role

```yaml
# Add to config/roles.yml
roles:
  10.0.7.1: spine   # New spine switch
```

The triage system will automatically assign:
- Criticality: 9.0/10 (spine role)
- Blast radius: 15 (based on topology)
- Priority: P1 (critical)

## Configuration Schema

### roles.yml Schema

```yaml
roles:                        # Required
  <device_id>: <role>        # device_id: IP or hostname, role: rr|spine|tor|edge|server

thresholds:                   # Optional
  edge_local_prefix_max: int
  edge_local_pct_table_max: float
  correlation_window_secs: int

binning:                      # Optional
  bin_seconds: int
  window_bins: int
```

## Troubleshooting

### YAML Parsing Errors

```bash
# Validate YAML
python -c "import yaml; print(yaml.safe_load(open('config/roles.yml')))"

# Check for common issues:
# - Tabs instead of spaces (YAML requires spaces)
# - Missing colons
# - Incorrect indentation
```

### Role Not Found

If device role is not found:
1. Check device ID format (IP vs hostname)
2. Add missing device to `config/roles.yml`
3. Restart services

## Related Files

**System Configs** (this directory):
- `config/roles.yml` - Device roles

**Pipeline Configs** (src/configs/):
- `src/configs/multi_modal_config.yml` - Correlation settings
- `src/configs/snmp_config.yml` - SNMP simulator

**See Also**:
- Src configs: `src/configs/` directory
- Evaluation configs: Used inline in `evaluation/` scripts
- Test configs: `tests/conftest.py` for test fixtures

## Quick Reference

```bash
# View current roles
cat config/roles.yml

# Validate YAML
python -c "import yaml; yaml.safe_load(open('config/roles.yml'))"

# Count configured devices
grep -c ":" config/roles.yml
```
