# BGP Failure Detection using Topology-Aware Machine Learning

> **IS499 Capstone Project** | Real-time BGP anomaly detection with topology-aware failure localization

This system detects **failure‑induced** BGP anomalies on live streams and triages edge‑local (ToR↔server) vs. network‑impacting events using Matrix Profile analysis and lightweight topology‑aware blast‑radius scoring.

## 📚 Project Documentation

**👉 [Complete Documentation](docs/)** | **[References](docs/research/references.md)** | **[System Design](docs/design/)**

- **Research Foundation:** [9 peer-reviewed sources](docs/research/references.md) on BGP anomaly detection
- **Technical Design:** [UML diagrams](docs/design/) and system architecture  
- **Academic Integration:** [Program alignment](docs/development/program_alignment.md) mapping to IS curriculum
- **Project Planning:** [Proposal](docs/development/proposal.md) and [evaluation plan](docs/development/evaulation_plan.md)

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

## 🎓 Academic Context

**Thesis:** Traditional BGP monitoring suffers from high false positives and lacks failure localization context. This system combines Matrix Profile discord detection with network topology analysis to reduce alert fatigue and enable faster failure resolution.

**Novel Contributions:**
- Real-time topology-aware failure localization (EDGE_LOCAL vs NETWORK_IMPACTING)
- Streaming Matrix Profile implementation for BGP time series analysis
- Multi-language integration (Go collector + Python ML pipeline)
- Production-ready architecture with Docker containerization

**Program Integration:** Demonstrates competencies across 12 IS courses including networking, databases, security, software development, and enterprise architecture.

---

**Author:** Mike Hernandez  
**Institution:** [Your University] - Information Systems Program  
**Advisor:** [Advisor Name]  
**Repository:** https://github.com/mhernandezit/capstone-anomaly
