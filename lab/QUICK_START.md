# 🚀 Quick Start Guide - BGP Anomaly Detection Lab

## What You've Got

A complete containerlab-based virtual lab with:
- **10 real FRR routers** (2 spines, 2 ToRs, 2 edges, 4 servers)
- **Authentic BGP sessions** between all devices
- **Real syslog messages** from FRR daemons
- **Failure injection capabilities** for testing
- **ML pipeline integration** with your existing code

## 🎯 3-Step Quick Start

### 1. Deploy the Lab
```bash
cd lab
./scripts/deploy.sh
```

### 2. Check Everything is Working
```bash
./scripts/check-bgp.sh
```

### 3. Connect to Your ML Pipeline
```bash
python scripts/integrate-with-ml.py
```

## 🔥 What Happens Next

1. **Real BGP Updates** flow from the lab routers
2. **Your ML pipeline** processes them in real-time
3. **Matrix Profile detection** identifies anomalies
4. **Impact scoring** classifies the severity
5. **Alerts** are generated for detected anomalies

## 💥 Test with Failures

```bash
# Interactive failure injection
./scripts/inject-failures.sh

# Choose from:
# 1. Link failures
# 2. Router crashes  
# 3. BGP session resets
# 4. Interface down events
```

## 📊 Monitor Everything

```bash
# Watch logs in real-time
./scripts/monitor-logs.sh

# Check BGP status
./scripts/check-bgp.sh

# Follow specific logs
docker exec clab-bgp-anomaly-lab-spine-01 tail -f /var/log/frr/frr.log
```

## 🎓 Perfect for Research

- **Algorithm Testing** - Real BGP data for ML models
- **Performance Benchmarking** - Measure detection accuracy
- **Feature Validation** - Test feature extraction approaches
- **Failure Analysis** - Study BGP behavior under failures
- **Scalability Studies** - Test under various load conditions

## 🛠️ Customize for Your Needs

- **Edit `topo.clab.yml`** - Modify network topology
- **Edit `configs/*/frr.conf`** - Change BGP configurations
- **Edit `scripts/inject-failures.sh`** - Add custom failure scenarios
- **Edit `scripts/integrate-with-ml.py`** - Modify ML integration

## 🧹 Clean Up

```bash
./scripts/destroy.sh
```

## 🆘 Need Help?

- **Check logs**: `./scripts/monitor-logs.sh`
- **Debug BGP**: `./scripts/check-bgp.sh`
- **Check containers**: `docker ps --filter "name=clab-bgp-anomaly-lab"`
- **Read full docs**: `README.md`

---

**This lab gives you everything you need to test and validate your BGP anomaly detection research with real network protocols and authentic data patterns!** 🎉
