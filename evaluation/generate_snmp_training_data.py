#!/usr/bin/env python3
"""
SNMP Training Data Generator
Creates large dataset of realistic SNMP metrics for Isolation Forest training.
"""

import json
import os
import random
from datetime import datetime
from pathlib import Path

import yaml


class SNMPTrainingDataGenerator:
    """Generates realistic SNMP training data with anomalies."""

    def __init__(self, topology_file: str = None):
        if topology_file is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            topology_file = os.path.join(base_dir, "topology.yml")

        with open(topology_file) as f:
            topology = yaml.safe_load(f)

        self.devices = list(topology["devices"].keys())
        self.device_roles = {name: info["role"] for name, info in topology["devices"].items()}

        # Initialize device states
        self.device_states = {}
        for device in self.devices:
            self.device_states[device] = self._init_device_state()

    def _init_device_state(self):
        """Initialize normal operating state for a device."""
        return {
            "temperature": random.uniform(45, 55),
            "cpu": random.uniform(15, 35),
            "memory": random.uniform(30, 50),
            "fan_speed": random.uniform(3000, 4000),
            "if_errors": 0,
            "if_discards": 0,
            "uptime": random.randint(86400, 2592000),
        }

    def generate_normal_sample(self, device: str, timestamp: float):
        """Generate one normal SNMP sample."""
        state = self.device_states[device]

        # Normal drift with brownian motion
        state["temperature"] += random.gauss(0, 0.3)
        state["temperature"] += (50 - state["temperature"]) * 0.1  # Mean reversion
        state["temperature"] = max(40, min(70, state["temperature"]))

        state["cpu"] += random.gauss(0, 1.5)
        state["cpu"] += (25 - state["cpu"]) * 0.12
        state["cpu"] = max(5, min(85, state["cpu"]))

        state["memory"] += random.uniform(0, 0.1)
        if random.random() < 0.02:  # Occasional GC
            state["memory"] -= random.uniform(5, 10)
        state["memory"] = max(20, min(80, state["memory"]))

        state["fan_speed"] += random.gauss(0, 50)
        state["fan_speed"] = max(2500, min(5000, state["fan_speed"]))

        # Rare errors (0.1% chance)
        if random.random() < 0.001:
            state["if_errors"] += random.randint(1, 3)

        state["uptime"] += 5

        return {
            "timestamp": timestamp,
            "device": device,
            "metrics": {
                "temperature": round(state["temperature"], 1),
                "cpu_usage_percent": round(state["cpu"], 1),
                "memory_usage_percent": round(state["memory"], 1),
                "fan_speed_rpm": int(state["fan_speed"]),
                "if_errors": state["if_errors"],
                "if_discards": state["if_discards"],
                "uptime_seconds": state["uptime"],
            },
        }

    def inject_anomaly(self, device: str, anomaly_type: str):
        """Inject specific anomaly into device state."""
        state = self.device_states[device]

        if anomaly_type == "thermal_runaway":
            state["temperature"] = random.uniform(75, 90)
            state["fan_speed"] = random.uniform(5500, 6000)

        elif anomaly_type == "cpu_spike":
            state["cpu"] = random.uniform(85, 98)

        elif anomaly_type == "memory_leak":
            state["memory"] = random.uniform(85, 95)

        elif anomaly_type == "interface_errors":
            state["if_errors"] += random.randint(50, 200)
            state["if_discards"] += random.randint(20, 100)

        elif anomaly_type == "fan_failure":
            state["fan_speed"] = random.uniform(500, 1500)  # Too slow
            state["temperature"] += random.uniform(10, 20)  # Heat up

    def generate_dataset(
        self,
        num_samples: int = 100000,
        anomaly_ratio: float = 0.02,
        output_file: str = "data/evaluation/training/snmp_training_data.jsonl",
    ):
        """Generate complete training dataset."""

        print(f"Generating {num_samples} SNMP samples...")
        print(f"  Devices: {len(self.devices)}")
        print(f"  Anomaly ratio: {anomaly_ratio*100:.1f}%")

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        samples = []
        anomaly_count = 0
        start_time = datetime.now().timestamp()

        for i in range(num_samples):
            timestamp = start_time + (i * 5)  # 5 second intervals

            # Pick random device
            device = random.choice(self.devices)

            # Decide if this should be anomalous
            if random.random() < anomaly_ratio:
                anomaly_type = random.choice(
                    [
                        "thermal_runaway",
                        "cpu_spike",
                        "memory_leak",
                        "interface_errors",
                        "fan_failure",
                    ]
                )
                self.inject_anomaly(device, anomaly_type)
                anomaly_count += 1

            sample = self.generate_normal_sample(device, timestamp)
            sample["is_anomaly"] = random.random() < anomaly_ratio  # Label for validation

            samples.append(sample)

            # Progress
            if (i + 1) % 1000 == 0:
                print(f"  Generated {i+1}/{num_samples} samples ({anomaly_count} anomalies)")

        # Save to file
        with open(output_path, "w") as f:
            for sample in samples:
                f.write(json.dumps(sample) + "\n")

        print(f"\n[OK] Training data saved to: {output_path}")
        print(f"     Total samples: {num_samples}")
        print(f"     Anomalies: {anomaly_count} ({anomaly_count/num_samples*100:.1f}%)")
        print(f"     File size: {output_path.stat().st_size / 1024 / 1024:.2f} MB")

        return str(output_path)


def main():
    """Generate SNMP training dataset."""
    generator = SNMPTrainingDataGenerator()

    # Generate VERY LARGE training set for 100MB+ file
    # 500,000 samples = ~700 hours of data at 5s intervals
    # Expected file size: ~150MB
    generator.generate_dataset(
        num_samples=500000,
        anomaly_ratio=0.02,  # 2% anomalies
        output_file="data/evaluation/training/snmp_training_data.jsonl",
    )


if __name__ == "__main__":
    main()
