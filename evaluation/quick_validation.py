#!/usr/bin/env python3
"""
QUICK VALIDATION - Tests Matrix Profile + Isolation Forest in 60 seconds.
"""

import logging
import time
from pathlib import Path

import numpy as np

from anomaly_detection.models import IsolationForestDetector
from anomaly_detection.models.matrix_profile_detector import MatrixProfileDetector
from anomaly_detection.utils import FeatureBin

logging.basicConfig(level=logging.WARNING)  # Quiet

print("=" * 80)
print("QUICK VALIDATION - Real ML Algorithms")
print("=" * 80)

# Test 1: Matrix Profile
print("\n[TEST 1] Matrix Profile with BGP spike...")
mp_detector = MatrixProfileDetector(
    window_bins=8, series_keys=["wdr_total"], discord_threshold=1.5, mp_library="stumpy"
)

# Send baseline
for i in range(18):
    fb = FeatureBin(
        bin_start=int(time.time()),
        bin_end=int(time.time() + 10),
        totals={"wdr_total": 2.0 + (i % 3), "ann_total": 5.0},
        peers={},
    )
    mp_detector.update(fb)

# Send spike
fb_spike = FeatureBin(
    bin_start=int(time.time()),
    bin_end=int(time.time() + 10),
    totals={"wdr_total": 50.0, "ann_total": 5.0},  # HUGE spike
    peers={},
)
result = mp_detector.update(fb_spike)

mp_detected = result.get("is_anomaly", False)
mp_discord = result.get("series_results", {}).get("wdr_total", {}).get("discord_score", 0)

if mp_detected:
    print(f"  [OK] Matrix Profile DETECTED (discord={mp_discord:.2f})")
else:
    print(f"  [FAIL] Matrix Profile missed (discord={mp_discord:.2f})")

# Test 2: Isolation Forest
print("\n[TEST 2] Isolation Forest with SNMP anomaly...")

# Load pre-trained model
model_path = Path("data/evaluation/models/isolation_forest_trained.pkl")
if model_path.exists():
    import joblib

    model_data = joblib.load(model_path)

    if_detector = IsolationForestDetector(n_estimators=200, contamination=0.02)
    if_detector.model = model_data["model"]
    if_detector.scaler = model_data["scaler"]  # Load scaler
    if_detector.feature_names = model_data["feature_names"]
    if_detector.is_trained = True

    # Create anomalous feature vector (high temp, high errors)
    anomalous_features = np.array(
        [
            [
                100.0,  # interface_error_rate (HIGH)
                0.8,  # interface_utilization_mean
                0.1,  # interface_utilization_std
                5.0,  # interface_flap_count
                90.0,  # cpu_utilization_mean (HIGH)
                5.0,  # cpu_utilization_std
                95.0,  # memory_utilization_mean (HIGH)
                2.0,  # memory_utilization_std
                85.0,  # temperature_mean (HIGH)
                5.0,  # temperature_std
                6000.0,  # fan_speed_mean (MAX)
                100.0,  # fan_speed_std
                0.8,  # power_supply_voltage_mean
                0.05,  # power_supply_voltage_std
                3.0,  # threshold_violation_count
                5.0,  # severity_escalation_count
                2.0,  # multi_device_correlation_score
                0.9,  # environmental_stress_score
                0.8,  # syslog_correlation_score
            ]
        ]
    )

    result = if_detector.predict(
        anomalous_features[0], timestamp=time.time(), feature_names=if_detector.feature_names
    )

    if result.is_anomaly:
        print(f"  [OK] Isolation Forest DETECTED (confidence={result.confidence:.2f})")
    else:
        print(f"  [FAIL] Isolation Forest missed (score={result.anomaly_score:.2f})")
else:
    print("  [SKIP] No pre-trained model found")

# Summary
print("\n" + "=" * 80)
if mp_detected:
    print("[OK] MATRIX PROFILE WORKING")
else:
    print("[FAIL] Matrix Profile needs tuning")

print("=" * 80)
