# BGP Event Testing Suite

This directory contains tools for testing the BGP anomaly detection system by publishing synthetic BGP events to NATS.

## Quick Start

### 1. Test Dashboard Connection (Immediate)

```bash
# Make sure your application is running first
make up

# Publish a few test events immediately
python tests/quick_test.py
```

This will send 3 test BGP events and you should see them appear in your Streamlit dashboard at `http://localhost:8501`.

### 2. Run Full Test Scenarios (Comprehensive)

```bash
# Interactive test runner with multiple scenarios
python tests/data_publisher.py
```

This provides 5 different test scenarios:
1. **Normal Traffic** - Baseline BGP activity
2. **Route Leak Attack** - Simulates route leak anomalies  
3. **Prefix Hijack** - Simulates prefix hijacking
4. **Massive Withdrawal** - Simulates network outages
5. **High Volume Traffic** - Performance testing

## Test Scenarios Explained

### Normal Traffic
- **Purpose**: Establish baseline behavior
- **Events**: 80% announcements, 20% withdrawals
- **Duration**: 60 seconds at 2 events/sec
- **Use Case**: Verify system handles normal BGP operations

### Route Leak Attack
- **Purpose**: Test detection of route leaks
- **Anomaly**: Peer announces prefixes with suspicious AS paths
- **Pattern**: Normal traffic + periodic route leaks every 10s
- **Use Case**: Validate route leak detection algorithms

### Prefix Hijack
- **Purpose**: Test prefix hijacking detection
- **Anomaly**: Single AS announces prefixes it shouldn't own
- **Pattern**: Normal traffic + hijack attempts every 15s
- **Use Case**: Validate prefix hijack detection

### Massive Withdrawal  
- **Purpose**: Test outage detection
- **Anomaly**: Large numbers of routes withdrawn simultaneously
- **Pattern**: Normal traffic + mass withdrawals every 20s
- **Use Case**: Validate network outage detection

### High Volume Traffic
- **Purpose**: Performance and stress testing
- **Events**: 10 events/sec from multiple peers
- **Duration**: 2 minutes
- **Use Case**: Ensure system scales under load

## Data Format

All test events follow the `BGPUpdate` schema defined in `python/utils/schema.py`:

```python
class BGPUpdate(BaseModel):
    ts: int                           # Unix timestamp
    peer: str                         # BGP peer IP address  
    type: str                         # "UPDATE" | "NOTIFICATION"
    announce: Optional[List[str]]     # Announced prefixes
    withdraw: Optional[List[str]]     # Withdrawn prefixes  
    attrs: Optional[Dict[str, Any]]   # BGP attributes (AS path, etc.)
```

## NATS Subjects

The test suite publishes to these NATS subjects:

- `bgp.updates` - Consumed by the Python pipeline for processing
- `bgp.events` - Consumed directly by the dashboard for display

## System Integration

```
Test Publisher → NATS → [Pipeline] → Dashboard
                   ↓
               Processing Chain:
               1. Feature Aggregation
               2. Matrix Profile Detection  
               3. Impact Classification
               4. Alert Generation
```

## Monitoring Test Results

1. **Dashboard**: Real-time event display at `http://localhost:8501`
2. **Pipeline Logs**: Check console output of `make pipeline`
3. **NATS Logs**: Monitor NATS server activity
4. **Container Logs**: `docker logs capstone-anomaly-dash-1`

## Customizing Tests

### Add New Scenarios

Edit `tests/data_publisher.py` and add to `TEST_SCENARIOS`:

```python
"my_scenario": TestScenario(
    name="My Custom Scenario",
    description="Description of what this tests",
    duration_seconds=120,
    event_rate_per_second=5.0,
    peers=["10.0.1.1", "10.0.2.1"],
    prefixes=["192.168.100.0/24"],
    anomaly_type="custom"  # or None for normal
)
```

### Modify Event Generation

Edit the `BGPEventGenerator` class methods:
- `generate_normal_update()` - Normal BGP traffic patterns
- `generate_route_leak()` - Route leak anomaly patterns
- `generate_prefix_hijack()` - Hijack anomaly patterns
- `generate_massive_withdrawal()` - Withdrawal anomaly patterns

## Troubleshooting

### Connection Issues
```bash
# Check NATS is running
docker ps | grep nats

# Check NATS connectivity  
telnet localhost 4222
```

### Dashboard Not Updating
```bash
# Check dashboard logs
docker logs capstone-anomaly-dash-1

# Restart dashboard
make down && make up
```

### Pipeline Not Processing
```bash
# Run pipeline manually to see errors
make pipeline
```

## Next Steps

1. Run `quick_test.py` to verify basic connectivity
2. Use `data_publisher.py` scenarios to test anomaly detection
3. Monitor results in dashboard and pipeline logs
4. Customize scenarios for your specific testing needs
