#!/usr/bin/env python3
"""
Realistic ML Detection Test
Tests ML detection with gradual failures and novel anomaly patterns NOT in training data.
No SNMP traps - pure ML detection only.
"""

import asyncio
import json
import random
import time
from pathlib import Path

from nats.aio.client import Client as NATS

from pipeline_runner import ProductionPipelineRunner


class RealisticAnomalySimulator:
    """Simulates realistic, gradual failures that require ML to detect."""

    def __init__(self, num_devices: int = 100):
        self.num_devices = num_devices
        self.devices = [f"device-{i:04d}" for i in range(1, num_devices + 1)]
        
        # Device state
        self.device_state = {}
        for device in self.devices:
            self.device_state[device] = {
                "temperature": random.uniform(45, 55),
                "cpu": random.uniform(20, 35),
                "memory": random.uniform(30, 45),
                "fan_speed": random.uniform(3000, 4000),
                "if_errors": 0,
                "if_discards": 0,
            }
        
        print(f"[Simulator] Initialized with {num_devices} devices")

    async def connect(self, nats_url: str = "nats://localhost:4222"):
        """Connect to NATS."""
        self.nc = NATS()
        await self.nc.connect(nats_url)
        print(f"[Simulator] Connected to NATS")

    async def generate_baseline(self, duration: int = 60):
        """Generate normal baseline traffic."""
        print(f"[Baseline] Generating normal traffic for {duration}s...")
        start = time.time()
        count = 0

        while time.time() - start < duration:
            # Sample random devices
            sample = random.sample(self.devices, min(50, len(self.devices)))
            
            for device in sample:
                state = self.device_state[device]
                
                # Normal drift
                state["temperature"] += random.gauss(0, 0.3)
                state["temperature"] = max(40, min(70, state["temperature"]))
                
                state["cpu"] += random.gauss(0, 1.5)
                state["cpu"] = max(5, min(85, state["cpu"]))
                
                # Send SNMP metrics (NO TRAPS)
                metrics = {
                    "timestamp": time.time(),
                    "device": device,
                    "metrics": {
                        "temperature": round(state["temperature"], 1),
                        "cpu_usage_percent": round(state["cpu"], 1),
                        "memory_usage_percent": round(state["memory"], 1),
                        "fan_speed_rpm": int(state["fan_speed"]),
                        "if_errors": state["if_errors"],
                        "if_discards": state["if_discards"],
                    },
                }
                await self.nc.publish("snmp.metrics", json.dumps(metrics).encode())
                
                # Sparse BGP updates
                if random.random() < 0.05:
                    bgp = {
                        "timestamp": time.time(),
                        "peer": f"10.0.{random.randint(1,255)}.{random.randint(1,255)}",
                        "type": "UPDATE",
                        "update_type": random.choice(["announce", "withdraw"]),
                        "prefixes": [f"192.168.{random.randint(0,255)}.0/24"],
                        "as_path": [65000, 65001],
                    }
                    await self.nc.publish("bgp.updates", json.dumps(bgp).encode())
                
                count += 1
            
            await asyncio.sleep(0.2)
        
        print(f"[Baseline] Complete: {count} samples")

    async def inject_gradual_failure(self, device: str, failure_type: str) -> float:
        """
        Inject REALISTIC production failure scenarios.
        These are actual failure modes encountered in production networks:
        - BFD withdrawals (fast failure detection protocol)
        - Unidirectional link failures (peering up, data path down)
        - Layer 2 loops (broadcast storm causing CPU starvation and BGP flaps)
        - Gradual optical degradation (bit errors causing packet loss and retransmits)
        """
        failure_start = time.time()
        state = self.device_state[device]
        
        # Device-specific BGP peer
        device_num = int(device.split("-")[1])
        peer_ip = f"10.0.{(device_num >> 8) & 255}.{device_num & 255}"
        
        if failure_type == "bfd_failure":
            # BFD detects link failure faster than BGP keepalives
            # Results in rapid BGP session teardown with mass withdrawals
            # SNMP shows interface down but otherwise normal metrics
            print(f"[Inject] BFD-detected link failure on {device}")
            
            # Interface goes down
            state["if_errors"] = 0  # No errors - clean shutdown
            state["if_discards"] = 0
            
            # Send metrics showing interface down (no gradual degradation)
            for i in range(10):
                metrics = {
                    "timestamp": time.time(),
                    "device": device,
                    "metrics": {
                        "temperature": state["temperature"],  # Normal
                        "cpu_usage_percent": state["cpu"],     # Normal
                        "memory_usage_percent": state["memory"], # Normal
                        "fan_speed_rpm": int(state["fan_speed"]),
                        "if_errors": 0,  # Clean shutdown
                        "if_discards": 0,
                        "interface_status": "down",  # New field
                    },
                }
                await self.nc.publish("snmp.metrics", json.dumps(metrics).encode())
                await asyncio.sleep(0.2)
            
            # BGP: Immediate mass withdrawal (BFD triggers fast failover)
            # All prefixes withdrawn rapidly
            for i in range(15):
                bgp = {
                    "timestamp": time.time(),
                    "peer": peer_ip,
                    "type": "UPDATE",
                    "update_type": "withdraw",
                    "prefixes": [f"192.168.{(device_num + i) & 255}.0/24"],
                    "as_path": [],
                }
                await self.nc.publish("bgp.updates", json.dumps(bgp).encode())
                await asyncio.sleep(0.05)  # Rapid withdrawal
        
        elif failure_type == "unidirectional_link_failure":
            # One-way traffic loss: BGP keepalives work in one direction (peering stays up)
            # but data plane is broken (packets dropped), causing asymmetric routing issues
            # SNMP shows increasing discards and errors, BGP shows instability but no session down
            print(f"[Inject] Unidirectional link failure on {device} (data plane broken, control plane up)")
            
            for step in range(20):
                # SNMP: Increasing packet drops and errors (data plane issue)
                state["if_errors"] += random.randint(100, 300)  # Rapid error accumulation
                state["if_discards"] += random.randint(50, 150)  # Packet drops
                
                metrics = {
                    "timestamp": time.time(),
                    "device": device,
                    "metrics": {
                        "temperature": state["temperature"],
                        "cpu_usage_percent": state["cpu"],
                        "memory_usage_percent": state["memory"],
                        "fan_speed_rpm": int(state["fan_speed"]),
                        "if_errors": state["if_errors"],
                        "if_discards": state["if_discards"],
                    },
                }
                await self.nc.publish("snmp.metrics", json.dumps(metrics).encode())
                
                # BGP: Session stays up but routes become unstable
                # Asymmetric routing causes some prefixes to flip
                if step % 3 == 0:  # Periodic instability
                    for i in range(2):
                        # Withdraw then re-announce (routing instability from asymmetry)
                        bgp_withdraw = {
                            "timestamp": time.time(),
                            "peer": peer_ip,
                            "type": "UPDATE",
                            "update_type": "withdraw",
                            "prefixes": [f"192.168.{(device_num + i * 5) & 255}.0/24"],
                            "as_path": [],
                        }
                        await self.nc.publish("bgp.updates", json.dumps(bgp_withdraw).encode())
                        await asyncio.sleep(0.3)
                        
                        bgp_announce = {
                            "timestamp": time.time(),
                            "peer": peer_ip,
                            "type": "UPDATE",
                            "update_type": "announce",
                            "prefixes": [f"192.168.{(device_num + i * 5) & 255}.0/24"],
                            "as_path": [65000, 65001],
                        }
                        await self.nc.publish("bgp.updates", json.dumps(bgp_announce).encode())
                
                await asyncio.sleep(0.4)
        
        elif failure_type == "layer2_loop":
            # Layer 2 switching loop causes broadcast storm
            # CPU maxes out at 100% handling broadcast traffic
            # BGP processes get starved of CPU time and start flapping
            # Temperature rises from CPU load
            print(f"[Inject] Layer 2 loop on {device} (broadcast storm -> CPU starvation -> BGP flaps)")
            
            for step in range(25):
                # SNMP: CPU ramps to 100% quickly, temperature rises
                if step < 5:
                    state["cpu"] = 60 + (step * 8)  # Rapid CPU increase
                else:
                    state["cpu"] = 98 + random.uniform(-2, 2)  # Maxed out with jitter
                
                state["temperature"] += 1.5  # Rising from CPU load
                state["if_discards"] += random.randint(500, 1500)  # Massive discards from loop
                
                metrics = {
                    "timestamp": time.time(),
                    "device": device,
                    "metrics": {
                        "temperature": round(min(state["temperature"], 85), 1),
                        "cpu_usage_percent": round(state["cpu"], 1),
                        "memory_usage_percent": state["memory"],  # Memory stable
                        "fan_speed_rpm": int(min(state["fan_speed"] + (step * 50), 5500)),  # Fans speed up
                        "if_errors": state["if_errors"],
                        "if_discards": state["if_discards"],
                    },
                }
                await self.nc.publish("snmp.metrics", json.dumps(metrics).encode())
                
                # BGP: Processes starved of CPU -> missed keepalives -> session flapping
                # Irregular pattern of withdrawals and re-announcements
                if step > 3 and step % 4 == 0:  # After CPU maxes out
                    # BGP process gets CPU slice, sends withdrawal
                    for i in range(3):
                        bgp = {
                            "timestamp": time.time(),
                            "peer": peer_ip,
                            "type": "UPDATE",
                            "update_type": "withdraw",
                            "prefixes": [f"192.168.{(device_num + i) & 255}.0/24"],
                            "as_path": [],
                        }
                        await self.nc.publish("bgp.updates", json.dumps(bgp).encode())
                        await asyncio.sleep(0.05)
                    
                    # Brief recovery, re-announces
                    await asyncio.sleep(0.5)
                    for i in range(3):
                        bgp = {
                            "timestamp": time.time(),
                            "peer": peer_ip,
                            "type": "UPDATE",
                            "update_type": "announce",
                            "prefixes": [f"192.168.{(device_num + i) & 255}.0/24"],
                            "as_path": [65000, 65001],
                        }
                        await self.nc.publish("bgp.updates", json.dumps(bgp).encode())
                        await asyncio.sleep(0.05)
                
                await asyncio.sleep(0.3)
        
        elif failure_type == "optical_degradation":
            # Gradual optical signal degradation causes bit errors
            # Results in increasing packet loss, retransmits, and BGP instability
            # This is gradual degradation, not sudden failure - harder to detect
            print(f"[Inject] Optical degradation on {device} (bit errors -> packet loss -> BGP instability)")
            
            for step in range(30):
                # SNMP: Gradually increasing error rates as optics degrade
                # Bit errors cause CRC failures
                error_increase = step * step * 5  # Quadratic growth (degradation accelerates)
                state["if_errors"] += error_increase
                state["if_discards"] += error_increase // 2
                
                # CPU increases slightly from retransmit overhead
                state["cpu"] += 0.5
                
                metrics = {
                    "timestamp": time.time(),
                    "device": device,
                    "metrics": {
                        "temperature": state["temperature"],  # Normal - not heat related
                        "cpu_usage_percent": round(min(state["cpu"], 75), 1),
                        "memory_usage_percent": state["memory"],
                        "fan_speed_rpm": int(state["fan_speed"]),
                        "if_errors": state["if_errors"],
                        "if_discards": state["if_discards"],
                        "rx_errors": state["if_errors"],  # RX specific
                        "crc_errors": error_increase,  # CRC errors from bit flips
                    },
                }
                await self.nc.publish("snmp.metrics", json.dumps(metrics).encode())
                
                # BGP: Keepalive packets get corrupted, causing session instability
                # As degradation worsens, more BGP updates fail/retry
                if step > 10:  # Starts affecting BGP after some degradation
                    # Probabilistic failures based on degradation level
                    if random.random() < (step / 30):  # Increasing probability
                        # BGP update failures cause route flapping
                        for i in range(2):
                            bgp = {
                                "timestamp": time.time(),
                                "peer": peer_ip,
                                "type": "UPDATE",
                                "update_type": "withdraw",
                                "prefixes": [f"192.168.{(device_num + i) & 255}.0/24"],
                                "as_path": [],
                            }
                            await self.nc.publish("bgp.updates", json.dumps(bgp).encode())
                            await asyncio.sleep(0.2)
                            
                            # Retry/recovery
                            bgp = {
                                "timestamp": time.time(),
                                "peer": peer_ip,
                                "type": "UPDATE",
                                "update_type": "announce",
                                "prefixes": [f"192.168.{(device_num + i) & 255}.0/24"],
                                "as_path": [65000, 65001],
                            }
                            await self.nc.publish("bgp.updates", json.dumps(bgp).encode())
                
                await asyncio.sleep(0.25)
        
        return failure_start


async def main():
    print("=" * 80)
    print("REALISTIC PRODUCTION FAILURE SCENARIOS")
    print("Testing ML detection on real network failure modes:")
    print("  - BFD-detected link failures")
    print("  - Unidirectional link failures (data plane down, control up)")
    print("  - Layer 2 loops (broadcast storm -> CPU starvation -> BGP flaps)")
    print("  - Optical degradation (bit errors -> packet loss -> BGP instability)")
    print("No SNMP traps - Pure ML detection required")
    print("=" * 80)
    print()

    # Configuration
    num_devices = int(input("Number of devices (default 100): ") or "100")
    
    simulator = RealisticAnomalySimulator(num_devices=num_devices)
    await simulator.connect()

    pipeline = ProductionPipelineRunner()
    await pipeline.connect()

    # Longer baseline for proper Matrix Profile training
    # Matrix Profile needs 2*window_bins + 2 = 26 bins minimum
    # With 10-second bins, need 260+ seconds
    baseline_duration = 270  # 270 seconds = 27 bins (enough for 12-bin window)
    print(f"\n[1/3] Baseline Period ({baseline_duration}s) - Training ML models...")
    print(f"    (Matrix Profile requires {baseline_duration}s for 12-bin window)")
    baseline_task = asyncio.create_task(simulator.generate_baseline(duration=baseline_duration))
    await asyncio.sleep(baseline_duration)
    await baseline_task
    print("[OK] Baseline complete\n")

    # Start monitoring
    print(f"[2/3] Starting ML detection pipeline...")
    pipeline_task = asyncio.create_task(pipeline.run(duration=150))
    await asyncio.sleep(3)

    # Inject GRADUAL failures with novel patterns
    print(f"\n[3/3] Injecting GRADUAL failures (novel patterns)...")
    failure_times = {}
    failure_types = {}
    
    # Test 4 realistic production failure scenarios
    test_scenarios = [
        ("device-0023", "bfd_failure"),                    # BFD-detected link failure
        ("device-0047", "unidirectional_link_failure"),    # One-way traffic loss
        ("device-0065", "layer2_loop"),                    # Broadcast storm -> CPU starvation -> BGP flaps
        ("device-0081", "optical_degradation"),            # Gradual fiber/optic degradation
    ]
    
    for i, (device, failure_type) in enumerate(test_scenarios, 1):
        print(f"\n  [{i}/{len(test_scenarios)}] {failure_type} on {device}")
        failure_time = await simulator.inject_gradual_failure(device, failure_type)
        failure_times[device] = failure_time
        failure_types[device] = failure_type
        await asyncio.sleep(10)  # 10s between failure injections

    # Continue normal traffic
    print("\n[Monitor] Continuing normal traffic (40s) while ML detects...")
    monitor_task = asyncio.create_task(simulator.generate_baseline(duration=40))
    await asyncio.sleep(40)
    await monitor_task

    # Get results
    print("\n[Wait] Collecting ML detection results...")
    alerts = await pipeline_task

    # Filter to ONLY Isolation Forest detections (no rule-based traps)
    ml_alerts = [a for a in alerts if a.get("detector") == "isolation_forest"]

    # Calculate detection delays
    print("\n" + "=" * 80)
    print("ML DETECTION RESULTS (Isolation Forest only)")
    print("=" * 80)
    print(f"\nConfiguration:")
    print(f"  Total Devices:           {num_devices}")
    print(f"  Failures Injected:       {len(failure_times)}")
    print(f"  Total Alerts (all):      {len(alerts)}")
    print(f"  ML Alerts (IF only):     {len(ml_alerts)}")

    detection_delays = []
    detected_devices = set()
    
    print(f"\nDetection Results by Failure Type:")
    for device, failure_time in failure_times.items():
        failure_type = failure_types[device]
        
        # Find ML alerts for this device
        device_ml_alerts = [a for a in ml_alerts if device in str(a.get("source", "")) or device in str(a.get("details", {}))]
        
        if device_ml_alerts:
            first_alert_time = device_ml_alerts[0]["timestamp"]
            delay = first_alert_time - failure_time
            detection_delays.append(delay)
            detected_devices.add(device)
            print(f"\n  {device:15s} ({failure_type})")
            print(f"    Status:           [DETECTED by ML]")
            print(f"    Detection Time:   {delay:6.2f}s")
            print(f"    ML Alerts:        {len(device_ml_alerts)}")
        else:
            print(f"\n  {device:15s} ({failure_type})")
            print(f"    Status:           [MISSED - Not detected by ML]")
            print(f"    ML Alerts:        0")

    # Statistics
    if detection_delays:
        mean_delay = sum(detection_delays) / len(detection_delays)
        min_delay = min(detection_delays)
        max_delay = max(detection_delays)
        detection_rate = len(detection_delays) / len(failure_times)
        
        print(f"\n{'-' * 80}")
        print(f"Performance Metrics (ML Detection Only):")
        print(f"  Mean Detection Time:  {mean_delay:6.2f}s")
        print(f"  Min Detection Time:   {min_delay:6.2f}s")
        print(f"  Max Detection Time:   {max_delay:6.2f}s")
        print(f"  Detection Rate:       {len(detection_delays)}/{len(failure_times)} ({detection_rate*100:.1f}%)")
        print(f"\n  Note: These are REALISTIC times for ML anomaly detection")
        print(f"        with gradual failures and novel patterns.")
    else:
        print("\n[WARNING] No ML detections! The Isolation Forest did not detect these novel patterns.")
        print("This indicates the model needs more diverse training data or different features.")

    # Detector breakdown
    by_detector = {}
    for alert in alerts:
        detector = alert.get("detector", "unknown")
        if detector not in by_detector:
            by_detector[detector] = []
        by_detector[detector].append(alert)

    print(f"\n{'-' * 80}")
    print(f"All Alerts by Detector:")
    for detector, detector_alerts in sorted(by_detector.items()):
        print(f"  {detector:30s}: {len(detector_alerts)} alerts")

    # Save results
    results = {
        "config": {
            "num_devices": num_devices,
            "num_failures": len(failure_times),
            "test_type": "realistic_ml_detection",
            "novel_patterns": True,
            "no_traps": True,
        },
        "performance": {
            "mean_detection_time_sec": mean_delay if detection_delays else None,
            "min_detection_time_sec": min_delay if detection_delays else None,
            "max_detection_time_sec": max_delay if detection_delays else None,
            "detection_rate": detection_rate if detection_delays else 0,
            "total_alerts": len(alerts),
            "ml_alerts_only": len(ml_alerts),
        },
        "failure_scenarios": {device: failure_types[device] for device in failure_times.keys()},
        "failures": {device: time for device, time in failure_times.items()},
        "detection_delays": {device: delay for device, delay in zip(detected_devices, detection_delays)},
        "alerts_sample": alerts[:20],  # Save first 20 alerts
    }

    results_file = Path(f"data/evaluation/realistic_ml_detection_{num_devices}_devices.json")
    results_file.parent.mkdir(parents=True, exist_ok=True)
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n[OK] Results saved to: {results_file}")
    print("=" * 80)

    # Cleanup
    await simulator.nc.close()
    await pipeline.nc.close()


if __name__ == "__main__":
    asyncio.run(main())

