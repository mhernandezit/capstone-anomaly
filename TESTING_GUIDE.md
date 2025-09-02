# BGP Event Testing - Quick Start Guide

## 🚀 Publishing Data to Your BGP Anomaly Detection System

Your system is now set up with a comprehensive testing framework. Here's how to start publishing BGP events to test your anomaly detection pipeline.

## Current System Status

✅ **NATS Message Broker**: Running on `localhost:4222`  
✅ **Streamlit Dashboard**: Available at `http://localhost:8501`  
✅ **Test Framework**: Ready in `tests/` directory  
✅ **Make Commands**: Available for easy testing  

## Quick Test (Start Here)

To verify everything is working and see immediate results:

```bash
# 1. Make sure your system is running
make up

# 2. Send test events immediately  
make test-quick
```

This publishes 3 sample BGP events that should appear in your dashboard at `http://localhost:8501`.

## Test Scenarios (Comprehensive Testing)

For more thorough testing with different anomaly types:

```bash
make test-scenarios
```

This opens an interactive menu with 5 scenarios:

1. **Normal Traffic** (60s) - Baseline BGP activity
2. **Route Leak Attack** (90s) - Route leak anomalies every 10s
3. **Prefix Hijack** (75s) - Hijack attempts every 15s  
4. **Massive Withdrawal** (60s) - Network outages every 20s
5. **High Volume Traffic** (120s) - Performance testing at 10 events/sec

## NATS Subjects

The testing framework publishes to:

- `bgp.updates` - Main processing pipeline (consumed by `python.ingest.nats_consumer`)
- `bgp.events` - Direct dashboard display (consumed by Streamlit app)

## Data Format

All events follow the BGP schema in `python/utils/schema.py`:

```python
{
  "ts": 1693526401,              # Unix timestamp
  "peer": "10.0.1.1",           # BGP peer IP
  "type": "UPDATE",             # Message type
  "announce": ["192.168.1.0/24"], # Announced prefixes (optional)
  "withdraw": ["192.168.2.0/24"], # Withdrawn prefixes (optional)  
  "attrs": {                    # BGP attributes (optional)
    "as_path": [65001, 65002],
    "next_hop": "10.0.1.1",
    "origin": "IGP"
  }
}
```

## Integration with Your Pipeline

```
Test Publisher → NATS → Python Pipeline → Dashboard
                   ↓
               bgp.updates
                   ↓
            Feature Aggregation
                   ↓
          Matrix Profile Detection
                   ↓
           Impact Classification  
                   ↓ 
           bgp.events (results)
                   ↓
              Dashboard Display
```

## Running the Full Pipeline

To test the complete processing chain:

```bash
# Terminal 1: Start infrastructure
make up

# Terminal 2: Start the Python processing pipeline
make pipeline

# Terminal 3: Send test data
make test-quick
# or
make test-scenarios
```

You should see:
1. **Test Publisher**: Confirmation messages about published events
2. **Pipeline Logs**: Processing output with anomaly scores and triage results
3. **Dashboard**: Real-time display of events and analysis results

## Monitoring Results

- **Dashboard**: `http://localhost:8501` - Real-time event display
- **Pipeline Output**: Console output showing feature aggregation and anomaly detection
- **NATS Logs**: `docker logs capstone-anomaly-nats-1`
- **Dashboard Logs**: `docker logs capstone-anomaly-dash-1`

## Custom Testing

### Manual Event Publishing

You can create custom events programmatically:

```python
import asyncio
from nats.aio.client import Client as NATS

async def publish_custom_event():
    nc = NATS()
    await nc.connect(servers=["nats://localhost:4222"])
    
    event = {
        "ts": int(time.time()),
        "peer": "10.0.1.1", 
        "type": "UPDATE",
        "announce": ["192.168.100.0/24"],
        "attrs": {"as_path": [65001], "next_hop": "10.0.1.1"}
    }
    
    await nc.publish("bgp.updates", json.dumps(event).encode())
    await nc.drain()

asyncio.run(publish_custom_event())
```

### Command Line Testing

Using the NATS CLI (if installed):

```bash
# Install NATS CLI
go install github.com/nats-io/natscli/nats@latest

# Publish a test event
echo '{"ts":1693526401,"peer":"10.0.1.1","type":"UPDATE","announce":["192.168.1.0/24"]}' | nats pub bgp.updates
```

## Troubleshooting

### Connection Issues
```bash
# Check NATS is running
docker ps | grep nats

# Test NATS connectivity
telnet localhost 4222
```

### Dashboard Not Updating
```bash
# Check dashboard logs
docker logs capstone-anomaly-dash-1

# Restart services
make down && make up
```

### Import/Path Issues
```bash
# Make sure you're in the project root
pwd  # Should show: /Users/mike/Documents/IS499/capstone-anomaly

# Check virtual environment
ls -la venv/bin/python
```

## Next Steps

1. ✅ **Start with quick test**: `make test-quick`
2. 🧪 **Try scenarios**: `make test-scenarios` 
3. 🔄 **Run pipeline**: `make pipeline` (in separate terminal)
4. 📊 **Monitor dashboard**: `http://localhost:8501`
5. 🎯 **Customize tests**: Edit files in `tests/` directory for your specific needs

Your BGP anomaly detection system is ready for comprehensive testing! 🎉
