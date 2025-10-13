# Matrix Profile Algorithm Comparison

## Scott et al. (2024) - Batch/Offline Approach

**Algorithm 1: MPBGP Anomaly Detection**

```
procedure MPBGPDetect(T, windowsize, k):
    dataset ← np.dataload(D)                    # Load complete historical data
    profile ← mp.compute(dataset, windowsize)   # Compute MP on entire dataset
    discords ← mp.discover.discords(            # Find top-k discords globally
        profile, k=k, 
        exclusionzone=windowsize
    )
    # Visualization of top-k anomalies
    for each discord: plot(discord_window)
end procedure
```

**Characteristics**:
- **Batch processing**: Loads complete dataset from file
- **Global discord discovery**: Finds top-k anomalies across entire time series
- **Retrospective analysis**: Analyzes historical data after collection
- **Visualization-focused**: Plots discords for human analysis
- **Research-oriented**: Designed for exploratory data analysis

**Use Case**: Post-hoc analysis of BGP routing anomalies in collected telemetry

---

## Our Implementation - Streaming/Online Approach

**Our Algorithm: Real-time Streaming Detection**

```
procedure StreamingMPDetect(window_bins, threshold):
    buffers ← {series: deque(maxlen=window_bins*3)}  # Sliding windows
    
    for each incoming_bin in stream:
        for each series in [withdrawals, announcements]:
            buffers[series].append(bin.value)       # Add to sliding window
            
            if len(buffer) < 2*window_bins:
                continue  # Need minimum data
            
            ts ← array(buffers[series])
            mp ← stumpy.stump(ts, m=window_bins)    # MP on current window
            discord_score ← max(mp[:, 0])           # Highest discord in window
            
            if discord_score > threshold:
                emit_alert(series, discord_score, confidence)
        
        overall ← weighted_average(all_series_discords)
        if overall > threshold:
            emit_multivariate_alert(overall, confidence, detected_series)
end procedure
```

**Characteristics**:
- **Streaming processing**: Processes data as it arrives via message bus
- **Sliding window**: Maintains fixed-size recent history (memory-bounded)
- **Real-time detection**: Emits alerts immediately when discord exceeds threshold
- **Threshold-based**: Binary decision (anomaly or not) rather than ranking
- **Multi-variate**: Processes multiple time series (withdrawals, announcements)
- **Production-oriented**: Designed for operational deployment

**Use Case**: Real-time network monitoring with sub-minute alerting

---

## Key Differences

| Aspect | Scott (2024) | Our Implementation |
|--------|--------------|-------------------|
| **Processing Mode** | Batch/Offline | Streaming/Online |
| **Data Source** | File (np.dataload) | Message bus (NATS) |
| **Memory** | Full dataset in memory | Fixed sliding window (bounded) |
| **Discord Discovery** | Top-k globally | Threshold-based locally |
| **Latency** | Minutes to hours | 10-30 seconds |
| **Use Case** | Research analysis | Production monitoring |
| **Scalability** | Limited by dataset size | Continuous operation |
| **Multi-Series** | Single time series | Multiple series weighted |

## Architectural Trade-offs

### Scott's Advantages
1. **Global optimality**: Finds truly most anomalous periods across all history
2. **Comparative ranking**: Can say "3rd most anomalous event"
3. **Full context**: Can analyze patterns over months/years

### Scott's Limitations
1. **Not real-time**: Requires complete dataset before analysis
2. **Memory intensive**: Must load entire time series
3. **No online detection**: Cannot alert as anomalies occur
4. **Single series**: Analyzes one metric at a time

### Our Advantages
1. **Real-time alerting**: Detects anomalies as they happen
2. **Memory efficient**: Fixed-size sliding window (configurable)
3. **Production-ready**: Continuous operation without restarts
4. **Multi-modal**: Combines multiple time series (withdrawals, announcements)
5. **Scalable**: Works with streaming data indefinitely

### Our Limitations
1. **Local context only**: Cannot compare against events outside window
2. **No global ranking**: Cannot say "this is the worst anomaly ever"
3. **Window dependency**: Detection quality depends on window size tuning
4. **Threshold tuning**: Requires setting appropriate thresholds

## Implementation Details Comparison

### Scott's matrixprofile-ts Library
```python
import matrixprofile as mp

# One-shot computation on complete dataset
profile = mp.compute(data, windows=window_size)
discords = mp.discover.discords(profile, k=5)
```

### Our stumpy Library (Streaming)
```python
import stumpy

# Incremental computation on sliding window
for new_bin in stream:
    buffer.append(new_bin)
    if len(buffer) >= 2*window_size:
        mp = stumpy.stump(buffer, m=window_size)
        discord = np.max(mp[:, 0])
        if discord > threshold:
            emit_alert()
```

## Why We Made This Choice

1. **Operational Requirements**: Network operations need real-time alerts, not retrospective analysis
2. **Scalability**: Sliding windows prevent unbounded memory growth
3. **Multi-modal Fusion**: Need to correlate BGP + SNMP in real-time
4. **Topology Integration**: Real-time alerts enable topology-aware localization

## Contribution to Field

**Scott et al.** demonstrated that Matrix Profile **can** detect BGP anomalies effectively.

**Our work** extends this by:
1. Adapting Matrix Profile for **streaming operation**
2. Combining **multiple time series** (withdrawals + announcements)
3. Integrating with **SNMP pipeline** for multi-modal detection
4. Adding **topology-aware localization**
5. Deploying in **real-time operational architecture**

This represents a transition from "proof of concept" (Scott) to "production system" (ours).

## Citation Strategy for Paper

In the paper, we should:
1. **Acknowledge Scott**: "Building on the work of Scott et al. (2024), who demonstrated Matrix Profile's effectiveness for BGP anomaly detection..."
2. **Highlight difference**: "However, their batch-processing approach required complete datasets, while operational networks need real-time detection..."
3. **Explain adaptation**: "We adapted the Matrix Profile algorithm for streaming operation using sliding windows and threshold-based detection..."
4. **Show contribution**: "This enables real-time alerting with bounded memory consumption, suitable for production deployment."

