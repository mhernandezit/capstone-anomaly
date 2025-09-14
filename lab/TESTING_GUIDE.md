# BGP Anomaly Detection System - Testing Guide

This guide covers comprehensive testing of the BGP anomaly detection system with all components.

## 🚀 Quick Test

Run the complete system test:

```bash
cd lab
./scripts/test-full-system.sh
```

This will:

- Build and deploy all components
- Start the Streamlit dashboard
- Run ML integration
- Inject realistic failures
- Monitor the system
- Generate a test report

## 🔧 Individual Component Tests

### 1. Validate System Components

```bash
./scripts/validate-system.sh
```

Checks:

- All containers are running
- NATS connectivity
- BMP collector status
- BGP sessions
- Dashboard accessibility
- ML integration

### 2. Test BMP Collector

```bash
./scripts/test-bmp-collector.sh
```

### 3. Check BGP Status

```bash
./scripts/check-bgp.sh
```

### 4. Inject Test Failures

```bash
./scripts/inject-test-failures.sh
```

## 📊 Monitoring

### Dashboard

- **URL**: http://localhost:8501
- **Features**: Real-time BGP monitoring, anomaly detection, topology view

### Manual Monitoring

```bash
# Monitor all logs
./scripts/monitor-logs.sh

# Check specific container logs
docker logs -f clab-bgp-anomaly-lab-bmp-collector
docker logs -f clab-bgp-anomaly-lab-nats

# Check BGP status
./scripts/check-bgp.sh
```

## 🧪 Test Scenarios

The system includes these automated test scenarios:

1. **Interface Flapping** - Bring interfaces up/down
2. **BGP Session Resets** - Clear BGP sessions
3. **Route Withdrawals** - Withdraw and re-advertise routes
4. **Container Restarts** - Restart network devices
5. **CPU Load** - Simulate high CPU usage
6. **Multiple Failures** - Simultaneous failures

## 📈 Expected Results

### Normal Operation

- All BGP sessions established
- BMP collector receiving updates
- NATS messages flowing
- Dashboard showing live data
- No false positive alerts

### During Failures

- BGP sessions go down/up
- Route withdrawals/advertisements
- Anomaly detection triggers
- Dashboard shows alerts
- ML pipeline processes events

## 🐛 Troubleshooting

### Common Issues

1. **Containers not starting**

   ```bash

   docker ps -a
   docker logs <container_name>
   ```

2. **BGP sessions not established**

   ```bash

   ./scripts/check-bgp.sh
   docker exec clab-bgp-anomaly-lab-spine-01 vtysh -c "show bgp summary"
   ```

3. **BMP collector not receiving data**

   ```bash

   docker logs clab-bgp-anomaly-lab-bmp-collector
   docker exec clab-bgp-anomaly-lab-spine-01 vtysh -c "show bmp targets"
   ```

4. **Dashboard not accessible**

```bash

   # Check if Streamlit is running
   ps aux | grep streamlit
   
   # Start manually
   cd ../src
   streamlit run dash/enhanced_dashboard.py
   ```

### Clean Restart

```bash
# Stop everything
./scripts/destroy.sh

# Clean up
docker system prune -f

# Restart
./scripts/test-full-system.sh
```

## 📋 Test Report

After running tests, check the generated report:

- `test-report-YYYYMMDD-HHMMSS.txt`
- Contains system status, logs, and results

## 🔄 Continuous Testing

For ongoing testing:

```bash
# Run validation every 5 minutes
while true; do
    ./scripts/validate-system.sh
    sleep 300
done
```

## 📚 Additional Resources

- [Containerlab Documentation](https://containerlab.dev/)
- [FRR BGP Configuration](https://docs.frrouting.org/)
- [NATS Documentation](https://docs.nats.io/)
- [Streamlit Documentation](https://docs.streamlit.io/)
