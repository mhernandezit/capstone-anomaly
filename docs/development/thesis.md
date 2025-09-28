# Machine Learning for Real-Time Detection and Localization of Network Failures

## 1–2 sentence description

I’m building an unsupervised, dual-signal system that fuses streaming **BGP updates** and **device logs** to detect **failure-induced** incidents in near real time and **localize** where they originate (ToR, spine, route-reflector, edge). A lightweight topology-aware triage suppresses benign ToR↔server flaps while escalating fabric/egress faults.

## Description of the problem you are trying to solve

Traditional alerting (SNMP/syslog thresholds) often over-pages on edge-local noise and under-explains fabric/egress issues, forcing manual correlation across a very large environment (≈2,000 switches and 1,200+ server peers, anycast services, global VXLAN). This project aims to **reduce detection delay**, **cut noisy pages**, and provide a first-guess **“what and where”** to accelerate triage.
**Demo failures:** one-way loss of signal, route-reflector crash, edge/provider outage, server crash.
**Baseline for comparison:** manual triage using SNMP/syslog alerts.
**Metrics reported:** **F1**, **detection delay**, **Hit\@k** localization accuracy, and **page reduction**.

## Explanation as to why you chose the topic

As a network engineering manager responsible for SRE in a large, BGP-routed production environment, I’ve seen how varied failures and anycast/VXLAN complexity slow root-cause isolation. Applying ML to streaming control-plane and log data can narrow the search **at or near the time of failure**, lowering MTTR and even catching issues proactively. Deliverables will include a **live dashboard** on a small-scale lab plus a **proof-of-concept path** toward an enterprise-grade deployment.
