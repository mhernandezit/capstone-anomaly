#!/usr/bin/env python3
"""
Full Evaluation with REAL ML Pipeline
Runs Matrix Profile + Isolation Forest on realistic data.
"""

import asyncio
import json
import time
from pathlib import Path

from pipeline_runner import ProductionPipelineRunner

from src.anomaly_detection.simulators.bgp_simulator import BGPSimulator
from src.anomaly_detection.simulators.snmp_baseline import SNMPBaseline


async def main():
    print("=" * 80)
    print("REAL ML PIPELINE EVALUATION")
    print("Matrix Profile + Isolation Forest on Realistic Data")
    print("=" * 80)
    print()

    # Start components
    print("[1/4] Starting BGP simulator...")
    bgp_sim = BGPSimulator()
    await bgp_sim.connect()

    print("[2/4] Starting SNMP baseline...")
    snmp_base = SNMPBaseline()
    await snmp_base.connect()

    print("[3/4] Starting REAL ML pipeline...")
    pipeline = ProductionPipelineRunner()
    await pipeline.connect()

    print("[4/4] Running evaluation...")
    print()

    # Start baseline traffic
    baseline_task = asyncio.create_task(snmp_base.run(duration=300))
    pipeline_task = asyncio.create_task(pipeline.run(duration=240))

    # Baseline period (train detectors) - MUCH LONGER for Matrix Profile
    print("[Baseline] Normal operation (120s) - Training Matrix Profile...")
    asyncio.create_task(bgp_sim.baseline_traffic(duration=120))
    await asyncio.sleep(120)  # Wait for full baseline
    print("[OK] Baseline complete - Matrix Profile should have 12 bins")

    # Inject failures
    print("\n[INJECT] Link failure: tor-01")
    ground_truth_start = time.time()
    await snmp_base.inject_interface_errors("tor-01", "eth1")
    await asyncio.sleep(0.5)
    await bgp_sim.inject_link_failure("tor-01", "eth1", "10.0.1.1")
    await asyncio.sleep(15)

    print("\n[INJECT] BGP flapping: spine-01")
    await bgp_sim.inject_bgp_flapping("spine-01", "10.1.0.0/16", "10.0.1.2", count=20)
    await asyncio.sleep(15)

    print("\n[INJECT] Hardware degradation: spine-02")
    await snmp_base.inject_hardware_issue("spine-02")
    await asyncio.sleep(15)

    print("\n[INJECT] Server failure: server-01")
    await bgp_sim.inject_server_failure("server-01", "10.0.2.1")
    await asyncio.sleep(15)

    # Wait for pipeline to finish
    alerts = await pipeline_task

    # Analyze results
    print("\n" + "=" * 80)
    print("REAL ALGORITHM RESULTS")
    print("=" * 80)

    print(f"\nTotal alerts from REAL detectors: {len(alerts)}")

    # Group by detector
    by_detector = {}
    for alert in alerts:
        detector = alert["detector"]
        if detector not in by_detector:
            by_detector[detector] = []
        by_detector[detector].append(alert)

    print("\nBy Detector:")
    for detector, detector_alerts in by_detector.items():
        print(f"  {detector:20s}: {len(detector_alerts)} alerts")

    # Show detection timeline
    print("\nDetection Timeline:")
    for i, alert in enumerate(alerts[:10], 1):  # First 10
        rel_time = alert["timestamp"] - ground_truth_start
        print(
            f"  {i:2d}. T+{rel_time:5.1f}s | {alert['source']:10s} | {alert['detector']:20s} | conf={alert['confidence']:.2f}"
        )

    if len(alerts) > 10:
        print(f"  ... and {len(alerts) - 10} more")

    # Save results
    results = {
        "total_alerts": len(alerts),
        "by_detector": {k: len(v) for k, v in by_detector.items()},
        "alerts": alerts,
    }

    results_file = Path("data/evaluation/real_pipeline_results.json")
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n[OK] Results saved to: {results_file}")
    print("\n[NEXT] Run: python evaluation/analyze_real_results.py")

    await baseline_task
    await bgp_sim.nc.close()
    await snmp_base.nc.close()
    await pipeline.nc.close()


if __name__ == "__main__":
    asyncio.run(main())
