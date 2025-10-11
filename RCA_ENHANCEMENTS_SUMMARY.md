# Root Cause Analysis Enhancements - Summary

## Changes Completed

### 1. Added Server Failure Scenario ✅

**New Scenario**: Server Failure
- **Device**: server-05
- **Type**: Compute - Service Failure
- **Description**: Server crash - application unresponsive
- **Detectable By**: None (out of scope for network monitoring)
- **Purpose**: Demonstrates system boundaries and scope limitations

### 2. Ground Truth vs Detection Comparison ✅

#### New RCA Structure

When you expand the "View Detailed Evidence & Root Cause Analysis" section, you now see:

```
🔍 View Detailed Evidence & Root Cause Analysis [▼]

├── 📋 Ground Truth vs Detection
│   ├── 🎯 Actual Failure (Ground Truth)
│   │   ├── Type: Hardware - Link Down
│   │   ├── Description: Physical link failure on interface eth1
│   │   ├── Target Device: spine-01
│   │   └── Detectable By: BGP, SNMP
│   │
│   └── 🔍 Detected By ML Pipelines
│       ├── ✅ BGP (Matrix Profile)
│       ├── ✅ SNMP (Isolation Forest)
│       └── ✅ Detection matches ground truth
│
├── 📊 Detection Signatures
│   ├── BGP Signature: 47 route withdrawals, peer session IDLE
│   └── SNMP Signature: Interface error rate 0.02% → 45%, link state DOWN
│
├── 🔬 ML Detection Evidence
│   ├── Multi-Modal Correlation Evidence
│   ├── BGP Signal: Route withdrawals detected...
│   ├── SNMP Signal: Interface error rate spike...
│   ├── Correlation: Both signals within 15-second window
│   ├── Probable Root Cause: Physical link failure
│   └── Confidence Level: HIGH
│
└── 🗺️ Topology & Impact Assessment
    ├── Device Information
    │   ├── Role: SPINE
    │   ├── Layer: Layer 1 - Spine
    │   ├── Connections: 6 direct neighbors
    │   └── Connected to: 6 tor(s)
    │
    └── Impact Analysis
        ├── Blast Radius: 24 devices
        ├── Priority: P1 CRITICAL
        ├── Affected Layers: All downstream (ToR, Leaf, Servers)
        └── Redundancy: Available (multiple spines)
```

### 3. Scenario Configurations

Each scenario now includes detailed ground truth:

#### Link Failure (Multimodal)
```python
{
    "device": "spine-01",
    "actual_failure": "Physical link failure on interface eth1",
    "failure_type": "Hardware - Link Down",
    "detectable_by": ["BGP", "SNMP"],
    "bgp_signature": "47 route withdrawals, peer session IDLE",
    "snmp_signature": "Interface error rate 0.02% → 45%, link state DOWN",
}
```

#### BGP Route Flapping
```python
{
    "device": "tor-01",
    "actual_failure": "BGP session instability causing route flapping",
    "failure_type": "Protocol - Routing Instability",
    "detectable_by": ["BGP"],
    "bgp_signature": "Periodic announcements/withdrawals every 30s",
    "snmp_signature": None,
}
```

#### Hardware Degradation
```python
{
    "device": "spine-02",
    "actual_failure": "Temperature spike and CPU overload",
    "failure_type": "Hardware - Environmental",
    "detectable_by": ["SNMP"],
    "bgp_signature": None,
    "snmp_signature": "Temperature 42°C → 78°C, CPU 30% → 95%",
}
```

#### Router Overload
```python
{
    "device": "leaf-01",
    "actual_failure": "CPU/memory exhaustion affecting routing",
    "failure_type": "Hardware - Resource Exhaustion",
    "detectable_by": ["BGP", "SNMP"],
    "bgp_signature": "Routing delays, increased UPDATE churn",
    "snmp_signature": "CPU 35% → 98%, Memory 45% → 92%",
}
```

#### Server Failure (New)
```python
{
    "device": "server-05",
    "actual_failure": "Server crash - application unresponsive",
    "failure_type": "Compute - Service Failure",
    "detectable_by": [],  # Out of scope
    "bgp_signature": None,
    "snmp_signature": None,
}
```

### 4. Detection Validation

System now validates ML detections against ground truth:

**Perfect Match**:
```
✅ Detection matches ground truth
Expected: {BGP, SNMP}
Detected: {BGP, SNMP}
```

**Partial Detection**:
```
⚠️ Partial detection
Expected: {BGP, SNMP}
Detected: {BGP}
```

**Out of Scope**:
```
ℹ️ Failure not in detection scope
Expected: {}
Detected: {}
Why: Server failures require application-level monitoring
```

### 5. Topology Integration

New topology section shows:

#### Device Information
- **Role**: Device's network role (SPINE, TOR, LEAF, SERVER)
- **Layer**: Network layer (Layer 1-4 with description)
- **Connections**: Count of direct neighbors
- **Connected to**: Breakdown by neighbor role
  - Example: "6 tor(s)" or "2 leaf(s), 4 server(s)"

#### Impact Analysis
- **Blast Radius**: Number of affected downstream devices
- **Priority**: P1-P4 based on role and impact
- **Affected Layers**: Which network layers impacted
  - Spine: "All downstream (ToR, Leaf, Servers)"
  - ToR: "Leaf switches and Servers"
  - Leaf: "Connected Servers only"
  - Server: "Local services only"
- **Redundancy**: Availability status
  - Spine/ToR: "Available (multiple X)"
  - Leaf/Server: "Limited or none"

### 6. Server Failure Educational Message

When server failure scenario is selected:

```
⚠️ No network-level anomalies detected

ℹ️ Ground Truth: Compute - Service Failure
   Device: server-05
   Description: Server crash - application unresponsive
   
   Why no detection? This failure type (Compute - Service Failure) 
   is not observable through network telemetry (BGP/SNMP). 
   Server failures require application-level monitoring or health checks.
```

## Visual Example

### BGP-Only Detection (Route Flapping)

Expanded RCA shows:

```
📋 Ground Truth vs Detection
┌─────────────────────────────┬─────────────────────────────┐
│ 🎯 Actual Failure           │ 🔍 Detected By ML Pipelines │
│                             │                             │
│ Type: Protocol - Routing    │ ✅ BGP (Matrix Profile)     │
│ Instability                 │                             │
│                             │ ✅ Detection matches        │
│ Description: BGP session    │    ground truth            │
│ instability causing route   │                             │
│ flapping                    │                             │
│                             │                             │
│ Target Device: tor-01       │                             │
│ Detectable By: BGP          │                             │
└─────────────────────────────┴─────────────────────────────┘

📊 Detection Signatures
BGP Signature: Periodic announcements/withdrawals every 30s

🔬 ML Detection Evidence
BGP-Only Detection Evidence:
- Route announcement/withdrawal pattern detected
- Matrix Profile distance exceeded threshold (2.5σ)
- Probable Root Cause: Routing protocol instability or configuration issue

🗺️ Topology & Impact Assessment
┌─────────────────────────────┬─────────────────────────────┐
│ Device Information          │ Impact Analysis             │
│                             │                             │
│ Role: TOR                   │ Blast Radius: 5 devices     │
│ Layer: Layer 2 - Top-of-Rack│ Priority: P2 HIGH           │
│ Connections: 6 direct       │                             │
│ neighbors                   │ Affected Layers:            │
│                             │ Leaf switches and Servers   │
│ Connected to:               │                             │
│ - 4 spine(s)                │ Redundancy: Available       │
│ - 2 leaf(s)                 │ (multiple tors)             │
└─────────────────────────────┴─────────────────────────────┘
```

## Benefits

### Educational Value
1. **Shows what was actually injected** vs what was detected
2. **Demonstrates system scope** - not all failures are detectable
3. **Validates ML accuracy** - expected vs actual detection comparison
4. **Explains detection mechanisms** - BGP and SNMP signatures

### Operational Value
1. **Topology context** - shows device's network position
2. **Impact clarity** - which layers and devices affected
3. **Redundancy awareness** - helps assess urgency
4. **Neighbor visibility** - understand connectivity

### Demonstration Value
1. **Perfect for presentations** - clear ground truth comparison
2. **Algorithm transparency** - shows what each detector found
3. **Failure diversity** - 5 different scenario types
4. **Scope limitations** - honest about what's not covered

## Usage

### View Ground Truth Comparison

1. Launch dashboard: `python launch_dashboard.py`
2. Select any scenario (e.g., "Link Failure (Multimodal)")
3. Click "Start Simulation"
4. Wait for alert to appear
5. Click "View Detailed Evidence & Root Cause Analysis"
6. See three-section RCA:
   - Ground Truth vs Detection
   - ML Detection Evidence
   - Topology & Impact Assessment

### Test Detection Validation

**Perfect Match** (Link Failure):
- Ground Truth: Detectable by BGP + SNMP
- Result: ✅ Detection matches ground truth

**Single Source** (BGP Flapping):
- Ground Truth: Detectable by BGP only
- Result: ✅ Detection matches ground truth

**Out of Scope** (Server Failure):
- Ground Truth: Not detectable by network monitoring
- Result: ℹ️ Failure not in detection scope
- Shows educational message explaining why

### Examine Topology Details

Look at topology section for any alert:
- Device role and layer position
- Number and types of neighbors
- Blast radius calculation
- Affected downstream layers
- Redundancy availability

## Technical Implementation

### Ground Truth Storage

```python
# Stored in session state
st.session_state.ground_truth = {
    "device": "spine-01",
    "actual_failure": "Physical link failure...",
    "failure_type": "Hardware - Link Down",
    "detectable_by": ["BGP", "SNMP"],
    "bgp_signature": "47 route withdrawals...",
    "snmp_signature": "Interface error rate...",
}
```

### Detection Validation Logic

```python
expected = set(ground_truth.get('detectable_by', []))
actual = set(['BGP', 'SNMP']) & detected_sources

if expected == actual and expected:
    st.success("✅ Detection matches ground truth")
elif not expected:
    st.info("ℹ️ Failure not in detection scope")
else:
    st.warning(f"⚠️ Partial detection: Expected {expected}, Got {actual}")
```

### Layer Name Mapping

```python
layer_map = {
    "spine": "Layer 1 - Spine",
    "tor": "Layer 2 - Top-of-Rack",
    "leaf": "Layer 3 - Leaf",
    "server": "Layer 4 - Compute",
}
```

## Summary

Successfully enhanced the Root Cause Analysis section with:

1. ✅ **Server failure scenario** demonstrating scope boundaries
2. ✅ **Ground truth comparison** showing actual vs detected failures
3. ✅ **Detection validation** with success/partial/out-of-scope indicators
4. ✅ **Topology integration** showing device context and connectivity
5. ✅ **Structured RCA** with three clear sections
6. ✅ **Educational messages** explaining detection limitations
7. ✅ **Layer information** showing network hierarchy
8. ✅ **Neighbor breakdown** by role type
9. ✅ **Blast radius context** with affected layers
10. ✅ **Redundancy status** for operational awareness

The dashboard now provides a comprehensive, educational, and operationally-relevant root cause analysis that clearly demonstrates the system's capabilities and limitations while providing rich topology context for every alert.

