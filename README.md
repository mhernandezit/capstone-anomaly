# Failure‑Focused Live BGP Failure Detection (Topology‑Aware)

This repo detects **failure‑induced** BGP anomalies on live streams and triages edge‑local (ToR↔server) vs. network‑impacting events using a lightweight topology‑aware blast‑radius score.

## Quick Start
1. **Edit configs**
   - `configs/roles.yml` — map device name/IP → role: [server, tor, spine, rr, edge]
   - `configs/collector.yml` — GoBGP passive eBGP collector (no routes advertised)
2. **Bring up infra**
   ```bash
   make up      # starts NATS + dashboard; run collector separately if you prefer bare-metal
   ```
3. **Run collector** (Go)
   ```bash
   make collector
   ```
4. **Run pipeline** (Python)
   ```bash
   make pipeline  # feature aggregation + MP detector + triage + push to dashboard
   ```
5. **Open dashboard**
   * Streamlit at [http://localhost:8501](http://localhost:8501)

## Components

* **Collector (Go):** peers eBGP with ToRs/Spines/Edge as a passive neighbor, publishes parsed updates to NATS (`bgp.updates`).
* **Features (Python):** aggregates 15–30s bins (withdrawals, announcements, prefix/peer churn, AS‑path edit distance, etc.).
* **Detector (Python):** Matrix Profile discords (streaming) over selected series.
* **Triage (Python):** topology‑aware blast radius → `EDGE_LOCAL` or `NETWORK_IMPACTING`.
* **Dashboard:** live anomaly score + impacted roles/prefixes + explanation.

## Lab Tips

* If physical lab isn't ready, use `cmd/failure-injector/exabgp.conf` to simulate withdraw storms and session resets.

## Make Targets

```bash
make up         # NATS + Streamlit in Docker
make down       # stop
make collector  # build/run Go collector (reads configs/collector.yml)
make pipeline   # run python pipeline (env from requirements.txt)
```
