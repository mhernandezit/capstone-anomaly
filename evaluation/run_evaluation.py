#!/usr/bin/env python3
"""
Evaluation Framework - Tests production ML pipeline with realistic scenarios.
Generates F1, Detection Delay, and Hit@k metrics for paper.
"""

import asyncio
import json
import time
from pathlib import Path

from src.anomaly_detection.simulators.bgp_simulator import BGPSimulator
from src.anomaly_detection.simulators.snmp_baseline import SNMPBaseline


class EvaluationRunner:
    """Runs evaluation scenarios and collects metrics."""

    def __init__(self):
        self.scenarios = []
        self.ground_truth = []
        self.alerts_dir = Path("data/evaluation/alerts")
        self.alerts_dir.mkdir(parents=True, exist_ok=True)

    async def setup(self):
        """Initialize simulators."""
        print("=" * 80)
        print("EVALUATION FRAMEWORK - Production ML Pipeline Test")
        print("=" * 80)
        print()

        self.bgp_sim = BGPSimulator()
        await self.bgp_sim.connect()

        self.snmp_base = SNMPBaseline()
        await self.snmp_base.connect()

        print("[OK] Simulators connected")

    async def run_scenario_01_link_failure(self):
        """Scenario 1: Link failure (P1 Critical)"""
        print("\n[SCENARIO 1] Link Failure: tor-01 -> spine-01")

        start_time = time.time()

        # Record ground truth
        self.ground_truth.append(
            {
                "scenario": "link_failure",
                "timestamp": start_time,
                "device": "tor-01",
                "interface": "eth1",
                "severity": "critical",
                "expected_sources": ["bgp", "snmp"],
            }
        )

        # Inject coordinated failure
        await self.snmp_base.inject_interface_errors("tor-01", "eth1")
        await asyncio.sleep(0.5)
        await self.bgp_sim.inject_link_failure("tor-01", "eth1", "10.0.1.1")

        await asyncio.sleep(10)  # Allow detection
        print(f"[OK] Scenario 1 complete ({time.time() - start_time:.1f}s)")

    async def run_scenario_02_bgp_flapping(self):
        """Scenario 2: BGP Flapping (P1 Critical)"""
        print("\n[SCENARIO 2] BGP Flapping: spine-01")

        start_time = time.time()

        self.ground_truth.append(
            {
                "scenario": "bgp_flapping",
                "timestamp": start_time,
                "device": "spine-01",
                "severity": "critical",
                "expected_sources": ["bgp"],
            }
        )

        await self.bgp_sim.inject_bgp_flapping("spine-01", "10.1.0.0/16", "10.0.1.2", count=15)

        await asyncio.sleep(10)
        print(f"[OK] Scenario 2 complete ({time.time() - start_time:.1f}s)")

    async def run_scenario_03_hardware(self):
        """Scenario 3: Hardware degradation (P2 Warning)"""
        print("\n[SCENARIO 3] Hardware Degradation: spine-02")

        start_time = time.time()

        self.ground_truth.append(
            {
                "scenario": "hardware_degradation",
                "timestamp": start_time,
                "device": "spine-02",
                "severity": "warning",
                "expected_sources": ["snmp"],
            }
        )

        await self.snmp_base.inject_hardware_issue("spine-02")

        await asyncio.sleep(10)
        print(f"[OK] Scenario 3 complete ({time.time() - start_time:.1f}s)")

    async def run_scenario_04_server_failure(self):
        """Scenario 4: Server failure (P3 Info) - single /32"""
        print("\n[SCENARIO 4] Server Failure: server-01 (single /32)")

        start_time = time.time()

        self.ground_truth.append(
            {
                "scenario": "server_failure",
                "timestamp": start_time,
                "device": "server-01",
                "severity": "info",
                "expected_sources": ["bgp"],
            }
        )

        await self.bgp_sim.inject_server_failure("server-01", "10.0.2.1")

        await asyncio.sleep(10)
        print(f"[OK] Scenario 4 complete ({time.time() - start_time:.1f}s)")

    async def run_all_scenarios(self):
        """Run all evaluation scenarios."""
        # Start baseline traffic
        baseline_task = asyncio.create_task(self.snmp_base.run(duration=200))

        # Baseline period
        print("\n[Baseline] Normal operation (30s)")
        await asyncio.sleep(30)

        # Run scenarios
        await self.run_scenario_01_link_failure()
        await asyncio.sleep(5)

        await self.run_scenario_02_bgp_flapping()
        await asyncio.sleep(5)

        await self.run_scenario_03_hardware()
        await asyncio.sleep(5)

        await self.run_scenario_04_server_failure()

        # Wait for baseline to finish
        await baseline_task

        # Save ground truth
        gt_file = Path("data/evaluation/ground_truth.json")
        gt_file.parent.mkdir(parents=True, exist_ok=True)
        with open(gt_file, "w") as f:
            json.dump(self.ground_truth, f, indent=2)

        print("\n" + "=" * 80)
        print("[OK] All scenarios complete")
        print(f"     Ground truth: {gt_file}")
        print("=" * 80)


async def main():
    runner = EvaluationRunner()
    await runner.setup()
    await runner.run_all_scenarios()

    print("\n[NEXT] Run: python evaluation/analyze_results.py")


if __name__ == "__main__":
    asyncio.run(main())
