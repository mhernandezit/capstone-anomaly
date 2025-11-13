# Machine Learning for Network Anomaly and Failure Detection

- **Institution:** CUNY School of Professional Studies  
- **Presenter:** Michael Hernandez  
- **Date:** November 9, 2025  

---

## Agenda

- Introduction  
- Topic  
- Problem  
- Solution  
- Analysis  
- References  

---

## Introduction / Topic Description

### Why this matters

- Outages waste time  
- Alerts are noisy  
- People need clarity  

### Goal

- Spot issues early  
- Show where it started  
- Reduce false alarms  

### Signals we use

- Routing changes (paths shift)  
- Device health (errors & load)  
- Timing that lines up  

### Patterns vs. surprises

- Normal steady rhythm  
- Breaks leave fingerprints  
- Across sources = real  

### Why this topic

- Alert fatigue is real  
- Better triage beats more alerts  
- Small changes, big impact  

---

## Problem Description

### What’s broken today

- Tools don’t talk  
- No blast-radius sense  
- Thresholds miss context  

### Impact

- Slow hunts  
- Missed patterns  
- Fixes take longer  

### What we need

- Combine signals  
- Understand the map  
- Prioritize what matters  

---

## Solution Description

### How it works

- Stream the data  
- Find surprises  
- Fuse and score  
- Show likely cause  

### Two key views

- Path shifts  
- Device health nearby  
- Same time = stronger signal  

### Triage that knows the map

- Core vs. edge matters  
- Bigger blast radius → higher priority  
- Fewer, better alerts  

---

## Analysis

### How we tested

- Lab network  
- Mostly normal traffic  
- Injected real faults  

### What we found

- Found issues in under a minute  
- Cut noisy alerts  
- Faster triage  

### Limits & next steps

- Lab ≠ live  
- More fault types  
- Scale up tests  

### Lab Topology

- Core, leaf, servers  
- Edge to internet  
- Collector for signals  

### Data Flow

- Paths + health  
- Fuse and score  
- Triage and alert  

### Figure (from draft)

- High-level view  
- Use as visual anchor  
- Speak to impact  

---

## References

### References (1/3)

1. Cheng, M., Li, Q., Lv, J., Liu, W., & Wang, J. (2021). Multi-Scale LSTM Model for BGP Anomaly Classification. *IEEE Transactions on Services Computing, 14*(3), 765–778. https://doi.org/10.1109/TSC.2018.2824809  
2. Mohammed, S. A., Mohammed, A. R., Côté, D., & Shirmohammadi, S. (2021). A machine-learning-based action recommender for Network Operation Centers. *IEEE Transactions on Network and Service Management, 18*(3), 2702–2713. https://doi.org/10.1109/TNSM.2021.3095463  
3. Mueen, A., & Keogh, E. (2017). Matrix Profile I: All Pairs Similarity Joins for Time Series: A Unifying View that Includes Motifs, Discords and Shapelets. *2016 IEEE 16th International Conference on Data Mining (ICDM)*, 1317–1322. https://doi.org/10.1109/ICDM.2016.0179  
4. Scott, B., Johnstone, M. N., Szewczyk, P., & Richardson, S. (2024). Matrix Profile data mining for BGP anomaly detection. *Computer Networks, 242*, 110257.  
5. Tan, Y., Huang, W., You, Y., Su, S., & Lu, H. (2024). Recognizing BGP Communities Based on Graph Neural Network. *IEEE Network, 38*(6), 232–238. https://doi.org/10.1109/MNET.2024.3414113  
6. Allagi, S., & Rachh, R. (2019). Analysis of Network log data using Machine Learning. *2019 IEEE 5th International Conference for Convergence in Technology (I2CT)*, 1–3. https://doi.org/10.1109/I2CT45611.2019.9033528  
7. Skazin, A. (2021). Detection of network anomalies in log files. *IOP Conference Series: Materials Science and Engineering, 1069*(1), 012021. https://doi.org/10.1088/1757-899X/1069/1/012021  
8. Feltin, T., Cordero Fuertes, J. A., Brockners, F., & Clausen, T. H. (2023). Understanding Semantics in Feature Selection for Fault Diagnosis in Network Telemetry Data. *NOMS 2023-2023 IEEE/IFIP Network Operations and Management Symposium*, 1–9. https://doi.org/10.1109/NOMS56928.2023.10154455  

### References (2/3)

9. Wang, H. (2020). Improvement and implementation of Wireless Network Topology System based on SNMP protocol for router equipment. *Computer Communications, 151*, 10–18. https://doi.org/10.1016/j.comcom.2020.01.001  
10. Manna, A., & Alkasassbeh, M. (2019). Detecting network anomalies using machine learning and SNMP-MIB dataset with IP group. *arXiv preprint* arXiv:1906.00863. https://arxiv.org/abs/1906.00863  
11. Liu, F. T., Ting, K. M., & Zhou, Z.-H. (2008). Isolation Forest. *2008 Eighth IEEE International Conference on Data Mining*, 413–422. https://doi.org/10.1109/ICDM.2008.17  
12. Liu, T., Zhu, Y., Xu, Q., Kong, X., & Yu, P. S. (2024). A layered isolation forest algorithm for outlier detection in imbalanced dataset. *Neurocomputing, 578*, 127381. https://doi.org/10.1016/j.neucom.2024.127381  
13. Powers, D. M. W. (2011). Evaluation: From Precision, Recall and F-Measure to ROC, Informedness, Markedness & Correlation. *Journal of Machine Learning Technologies, 2*(1), 37–63.  
14. Järvelin, K., & Kekäläinen, J. (2002). Cumulated Gain-Based Evaluation of IR Techniques. *ACM Transactions on Information Systems, 20*(4), 422–446. https://doi.org/10.1145/582415.582418  
15. Benzekki, K., El Fergougui, A., & Elbelrhiti Elalaoui, A.
