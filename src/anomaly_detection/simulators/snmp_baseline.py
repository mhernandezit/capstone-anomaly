#!/usr/bin/env python3
"""SNMP Baseline Generator - 98% normal traffic, 2% anomalies"""

import asyncio
import json
import random
import time

import yaml
from nats.aio.client import Client as NATS


class SNMPBaseline:
    """Generates realistic SNMP baseline with occasional anomalies."""

    def __init__(self, topology_file: str = None):
        if topology_file is None:
            import os

            base_dir = os.path.dirname(os.path.abspath(__file__))
            topology_file = os.path.join(base_dir, "topology.yml")

        with open(topology_file) as f:
            topology = yaml.safe_load(f)
        self.devices = list(topology["devices"].keys())

        # Initialize device state
        self.state = {}
        for device in self.devices:
            self.state[device] = {
                "temperature": random.uniform(45, 55),
                "cpu": random.uniform(15, 35),
                "memory": random.uniform(30, 50),
                "fan_speed": random.uniform(3000, 4000),
                "if_errors": 0,
            }

    async def connect(self, nats_url: str = "nats://localhost:4222"):
        self.nc = NATS()
        await self.nc.connect(nats_url)
        print("[SNMP Baseline] Connected to NATS")

    async def run(self, duration: int = 60):
        """Generate baseline SNMP metrics."""
        print(f"[SNMP Baseline] Running for {duration}s...")
        start = time.time()

        while time.time() - start < duration:
            for device in self.devices:
                await self._send_metrics(device)
            await asyncio.sleep(5)  # 5s polling interval

    async def _send_metrics(self, device: str):
        """Send one polling cycle for a device."""
        state = self.state[device]

        # Normal drift
        state["temperature"] += random.gauss(0, 0.5)
        state["temperature"] = max(40, min(75, state["temperature"]))

        state["cpu"] += random.gauss(0, 2)
        state["cpu"] = max(5, min(90, state["cpu"]))

        metrics = {
            "timestamp": time.time(),
            "device": device,
            "metrics": {
                "temperature": round(state["temperature"], 1),
                "cpu_usage_percent": round(state["cpu"], 1),
                "memory_usage_percent": round(state["memory"], 1),
                "fan_speed_rpm": int(state["fan_speed"]),
                "if_errors": state["if_errors"],
            },
        }

        await self.nc.publish("snmp.metrics", json.dumps(metrics).encode())

    async def inject_hardware_issue(self, device: str):
        """Inject hardware anomaly."""
        print(f"[SNMP Baseline] Hardware issue: {device}")
        self.state[device]["temperature"] = 85  # Overheat
        self.state[device]["fan_speed"] = 6000  # Fan maxed

        # Send immediate trap
        trap = {
            "timestamp": time.time(),
            "device": device,
            "trap_type": "temperatureHigh",
            "severity": "critical",
            "value": 85,
        }
        await self.nc.publish("snmp.traps", json.dumps(trap).encode())

    async def inject_interface_errors(self, device: str, interface: str):
        """Inject interface errors."""
        print(f"[SNMP Baseline] Interface errors: {device} {interface}")
        self.state[device]["if_errors"] = 1000

        trap = {
            "timestamp": time.time(),
            "device": device,
            "interface": interface,
            "trap_type": "linkDown",
            "severity": "critical",
        }
        await self.nc.publish("snmp.traps", json.dumps(trap).encode())
