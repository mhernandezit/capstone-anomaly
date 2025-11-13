# IS499 Capstone Presentation - Version 2
## Machine Learning for Network Anomaly and Failure Detection

---

## SLIDE 1: Cover Slide

**Title:** Machine Learning for Network Anomaly and Failure Detection

**Content:**
- CUNY School of Professional Studies
- Michael Hernandez
- IS 499 Information Systems Capstone
- Professor John Bouma
- October 11, 2025

---

## SLIDE 2: Agenda Slide

**Title:** Agenda

**Content:**
- Introduction
- Topic Description
- Problem Description
- Solution Description
- Analysis
- References

---

## SLIDE 3: Introduction (Part 1)

**Title:** Introduction

**Content:**
This presentation examines machine learning techniques for detecting and localizing network anomalies and failures in large-scale environments, using data from BGP routing updates and SNMP metrics.

Traditional network monitoring relies on threshold-based alerts from SNMP, often producing many false positives and offering little context for locating failures. Recent research suggests that machine learning approaches applied to SNMP datasets may improve anomaly detection accuracy in operational environments.

---

## SLIDE 4: Introduction (Part 2)

**Title:** Introduction (continued)

**Content:**
The system integrates BGP monitoring and SNMP metrics for network anomaly detection. Using unsupervised learning techniques such as:
- Matrix Profile analysis for time-series routing data
- Isolation Forest for multi-dimensional hardware metrics

The approach aims to reduce alert noise while providing failure localization capabilities. The evaluation examines whether this multi-modal architecture offers practical improvements over single-source monitoring in controlled test scenarios.

---

## SLIDE 5: Topic Description - Network Monitoring Challenge

**Title:** Topic Description: The Network Monitoring Challenge

**Content:**
Large networks face a fundamental challenge: when something breaks, operators in network operations centers must quickly determine what failed and where. A network might contain thousands of interconnected devices, and failures can cascade from one device to many others, making the root cause difficult to identify.

This project addresses this challenge by using machine learning to automatically detect network problems and then apply topology awareness to pinpoint their source.

---

## SLIDE 6: Topic Description - Data Sources

**Title:** Topic Description: BGP and SNMP Data Sources

**Content:**
Network devices continuously generate health information through hardware and software metrics:

**BGP (Border Gateway Protocol):**
- Software metrics from routing systems
- Directs traffic across the Internet
- Routers send update messages when conditions change
- Creates continuous stream of information about traffic path evolution

**SNMP (Simple Network Management Protocol):**
- Hardware metrics from device performance data
- Reports processor utilization, memory consumption, temperature, interface error counts
- Provides complementary view of device health

Together, BGP and SNMP offer a combined view: routing updates show how traffic paths change over time, while hardware metrics reflect device health.

---

## SLIDE 7: Topic Description - Machine Learning Approach

**Title:** Topic Description: Machine Learning Detection Approach

**Content:**
The project employs a dual-pipeline architecture that processes routing updates and device metrics using specialized pattern recognition algorithms:

**BGP Pipeline:**
- Matrix Profile analysis for time-series sequences
- Computes distance between subsequences and nearest neighbors
- Highlights anomalous patterns (discords) without labeled training data

**SNMP Pipeline:**
- Isolation Forest for device telemetry
- Ensemble method that isolates outliers efficiently
- Enables detection without prior examples of failures

The system combines evidence from both sources. When routing behavior and hardware metrics simultaneously indicate problems, this cross-confirmation provides stronger evidence of genuine failure than either source independently.

---

## SLIDE 8: Problem Description - Core Problem

**Title:** Problem Description: The Core Problem

**Content:**
The core problem is that traditional monitoring systems generate alerts without sufficient context to understand:
- What failed
- Where it failed
- How serious the impact is

When a network problem occurs, operators receive numerous notifications but must manually investigate to determine root cause and scope. This manual correlation across multiple monitoring systems and many devices is time-consuming and delays resolution.

---

## SLIDE 9: Problem Description - Three Gaps

**Title:** Problem Description: Three Critical Gaps

**Content:**
This project addresses three gaps in current approaches:

**1. Isolated Monitoring Systems**
- Routing behavior and hardware performance are tracked separately
- Correlated problems across both sources provide stronger evidence of genuine failures, but systems don't leverage this

**2. Lack of Topology Awareness**
- Systems don't understand how devices connect or which are critical
- Cannot assess failure impact or prioritize response
- Operators must determine priorities manually

**3. Uniform Threshold-Based Alerting**
- All devices and metrics treated uniformly
- Doesn't apply detection methods suited to different types of data
- Time-series methods work better for routing; multi-dimensional outlier detection works better for hardware metrics

---

## SLIDE 10: Problem Description - Why Current Systems Are Insufficient

**Title:** Problem Description: Why Current Systems Are Insufficient

**Content:**
Current network monitoring systems have fundamental limitations:

- Hardware monitoring can detect hard failures but produces excessive alerts for harmless events
- Lacks context for assessing failure scope or impact
- Operations teams face false positives while missing critical anomalies

**Architectural Limitations:**
- Different monitoring systems operate independently
- No understanding of network structure and device importance
- Threshold-based approaches apply same logic to all data types despite different behaviors

Combining specialized approaches with correlation across sources can improve detection accuracy over single-source methods.

---

## SLIDE 11: Solution Description - Architecture Overview

**Title:** Solution Description: Implementation Architecture

**Content:**
The system processes network data through two specialized detection pipelines before combining their results:

**BGP Pipeline:**
- Analyzes routing update patterns over time using Matrix Profile
- Compares recent activity against historical patterns
- Identifies unusual routing behavior

**SNMP Pipeline:**
- Examines device health metrics using Isolation Forest
- Learns normal operating ranges
- Flags devices showing abnormal performance

**Correlation Stage:**
- Combines alerts from both pipelines
- Checks if routing problems and hardware issues occur simultaneously
- Cross-validation helps distinguish genuine failures from routine variations
- Incorporates network topology information to assess impact scope

---

## SLIDE 12: Solution Description - Key Implementation Details

**Title:** Solution Description: Key Implementation Details

**Content:**
**Matrix Profile Implementation:**
- Processes data in real-time using sliding windows
- Maintains recent history of routing updates (12 time periods)
- Continuously compares new patterns against baseline
- Enables real-time detection as problems occur

**Isolation Forest Training:**
- Trained on 500,000 samples of simulated device metrics
- Learned to identify the 5% most unusual combinations of metrics
- Validated using controlled failure scenarios
- Identifies novel failure types without requiring examples of every possible problem

**Topology Configuration:**
- Defined using configuration files specifying device roles and connections
- System knows which devices are core routers, top-of-rack switches, and leaf devices
- Calculates how many downstream devices might be affected by failures

---

## SLIDE 13: Solution Description - Testing Approach

**Title:** Solution Description: Testing Approach

**Content:**
To test the system without access to production networks, simulators were built that generate realistic network data:

- Simulators create normal network traffic 98% of the time
- Inject specific failure scenarios 2% of the time
- Controlled approach allows measurement of exactly when failures occur and how quickly the system detects them

**Test Scenarios:**
- Unstable routing connections (route flapping)
- Broken network links
- Device restarts
- Gradual hardware degradation

**Test Network:**
- 20-device topology with 4 core routers, 8 rack switches, and 8 servers
- Simulates realistic enterprise environment
- Enables testing of both individual device failures and problems affecting multiple devices simultaneously

---

## SLIDE 14: Analysis - Evaluation Setup and Results

**Title:** Analysis: Evaluation Setup and Results

**Content:**
Four common types of network failures were tested:

**Route Flapping:**
- Generated strong routing alerts but minimal hardware signals
- System correctly identified as routing-only problems
- Assigned appropriate priority levels

**Link Failures:**
- Produced alerts from both routing and hardware systems simultaneously
- Correlation system recognized pattern and generated high-priority multi-modal alerts
- Correctly identified scope of problem

**Device Restarts:**
- Created brief routing anomalies appropriately deprioritized
- Avoided false alarms for routine maintenance

**Gradual Hardware Degradation:**
- Detected by hardware monitoring system
- Received higher priority when accompanied by unusual routing activity

---

## SLIDE 15: Analysis - Performance Metrics

**Title:** Analysis: Performance Metrics

**Content:**
**Detection Accuracy (Controlled Scenarios):**
- Precision: 1.0
- Recall: 1.0
- F1 Score: 1.0

**Detection Latency:**
- Mean detection delay: 29.4 seconds
- Median: 40.9 seconds
- P95: 55.9 seconds
- All below the 60-second operational target

**Scalability:**
- Memory usage: approximately linear (2.52 MB at 20 devices, 3.50 MB at 1,000 devices)
- Throughput: scaled from 184 to 921 samples/second
- Pre-trained Isolation Forest model: 2.5 MB (trained on 500,000 SNMP samples, 122 MB)

---

## SLIDE 16: Analysis - Limitations and Trade-offs

**Title:** Analysis: Limitations and Trade-offs

**Content:**
**Scale and Scope Limitations:**
- Evaluation used 20-device topology, orders of magnitude smaller than production networks
- Limited to four representative failure types
- Most failure domains known prior to testing

**Data Quality and Realism:**
- Used simulated BGP updates and SNMP metrics rather than production data
- 98% baseline traffic with 2% injected anomalies represents idealized scenario
- May not reflect actual network conditions

**Algorithmic Trade-offs:**
- Aggregation supports scaling but reduces device-level attribution
- Sliding windows introduce latency versus precision trade-offs
- Fusion approach assumes temporal correlation between BGP and SNMP anomalies

**Generalization Concerns:**
- Results represent controlled laboratory conditions rather than production validation
- High accuracy metrics may not translate to real-world performance
- Evaluation on live networks with production data remains necessary

---

## SLIDE 17: References (Part 1)

**Title:** References

**Content:**
- Allagi, S., & Rachh, R. (2019). Analysis of Network log data using Machine Learning. 2019 IEEE 5th International Conference for Convergence in Technology (I2CT), 1-3.

- Cheng, M., Li, Q., Lv, J., Liu, W., & Wang, J. (2021). Multi-Scale LSTM Model for BGP Anomaly Classification. IEEE Transactions on Services Computing, 14(3), 765-778.

- Cisco Systems. (2006). Understanding Simple Network Management Protocol (SNMP) Traps. Cisco Technical Documentation.

- Feltin, T., Cordero Fuertes, J. A., Brockners, F., & Clausen, T. H. (2023). Understanding Semantics in Feature Selection for Fault Diagnosis in Network Telemetry Data. NOMS 2023-2023 IEEE/IFIP Network Operations and Management Symposium, 1-9.

- Liu, F. T., Ting, K. M., & Zhou, Z.-H. (2008). Isolation Forest. 2008 Eighth IEEE International Conference on Data Mining, 413-422.

- Liu, T., Zhu, Y., Xu, Q., Kong, X., & Yu, P. S. (2024). A layered isolation forest algorithm for outlier detection in imbalanced dataset. Neurocomputing, 578, 127381.

---

## SLIDE 18: References (Part 2)

**Title:** References (continued)

**Content:**
- Manna, A., & Alkasassbeh, M. (2019). Detecting network anomalies using machine learning and SNMP-MIB dataset with IP group. arXiv preprint arXiv:1906.00863.

- Mohammed, S. A., Mohammed, A. R., Côté, D., & Shirmohammadi, S. (2021). A machine-learning-based action recommender for Network Operation Centers. IEEE Transactions on Network and Service Management, 18(3), 2702-2713.

- Mueen, A., & Keogh, E. (2017). Matrix Profile I: All Pairs Similarity Joins for Time Series: A Unifying View that Includes Motifs, Discords and Shapelets. 2016 IEEE 16th International Conference on Data Mining (ICDM), 1317-1322.

- Rekhter, Y., Li, T., & Hares, S. (2006). A Border Gateway Protocol 4 (BGP-4). RFC 4271, Internet Engineering Task Force (IETF).

- Scott, B., Johnstone, M. N., Szewczyk, P., & Richardson, S. (2024). Matrix Profile data mining for BGP anomaly detection. Computer Networks, 242, 110257.

- Skazin, A. (2021). Detection of network anomalies in log files. IOP Conference Series: Materials Science and Engineering, 1069(1), 012021.

- Tan, Y., Huang, W., You, Y., Su, S., & Lu, H. (2024). Recognizing BGP Communities Based on Graph Neural Network. IEEE Network, 38(6), 232-238.

- Wang, H. (2020). Improvement and implementation of Wireless Network Topology System based on SNMP protocol for router equipment. Computer Communications, 151, 10-18.

