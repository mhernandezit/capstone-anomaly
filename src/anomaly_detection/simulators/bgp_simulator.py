#!/usr/bin/env python3
"""
BGP UPDATE Simulator
Generates realistic BGP UPDATE messages in BMP format for evaluation.
"""

import asyncio
import json
import random
import time
from typing import List, Optional

import yaml
from nats.aio.client import Client as NATS


class BGPSimulator:
    """Simulates BGP UPDATE messages for testing."""

    def __init__(self, topology_file: str = None):
        if topology_file is None:
            import os

            base_dir = os.path.dirname(os.path.abspath(__file__))
            topology_file = os.path.join(base_dir, "topology.yml")

        with open(topology_file) as f:
            self.topology = yaml.safe_load(f)

        self.devices = self.topology["devices"]
        self.bgp_peers = self.topology["bgp_peers"]
        self.prefixes = self.topology["prefixes"]

    async def connect(self, nats_url: str = "nats://localhost:4222"):
        """Connect to NATS."""
        self.nc = NATS()
        await self.nc.connect(nats_url)
        print(f"[BGP Simulator] Connected to NATS at {nats_url}")

    async def send_update(
        self, peer: str, update_type: str, prefixes: List[str], as_path: Optional[List[int]] = None
    ):
        """Send a BGP UPDATE message."""
        msg = {
            "timestamp": time.time(),
            "peer": peer,
            "type": "UPDATE",
            "update_type": update_type,  # "announce" or "withdraw"
            "prefixes": prefixes,
            "as_path": as_path or [],
        }

        await self.nc.publish("bgp.updates", json.dumps(msg).encode())

    async def baseline_traffic(self, duration: int = 30):
        """Generate baseline BGP traffic (normal operation)."""
        print(f"[BGP Simulator] Baseline traffic for {duration}s...")
        start = time.time()
        count = 0

        while time.time() - start < duration:
            # More frequent updates for better Matrix Profile baseline
            # Random announcements (70%) and withdrawals (30%)
            if random.random() < 0.7:
                device = random.choice(list(self.prefixes.keys()))
                prefix = random.choice(self.prefixes[device])
                peer_ip = f"10.0.{random.randint(1,10)}.{random.randint(1,254)}"
                await self.send_update(peer_ip, "announce", [prefix], [65000, 65001])
            else:
                device = random.choice(list(self.prefixes.keys()))
                prefix = random.choice(self.prefixes[device])
                peer_ip = f"10.0.{random.randint(1,10)}.{random.randint(1,254)}"
                await self.send_update(peer_ip, "withdraw", [prefix])

            count += 1
            await asyncio.sleep(random.uniform(0.2, 0.8))  # FASTER for more data

        print(f"[BGP Simulator] Baseline complete: {count} updates sent")

    async def inject_link_failure(self, device: str, interface: str, peer: str):
        """Simulate link failure with mass withdrawals."""
        print(f"[BGP Simulator] Link failure: {device} {interface} -> {peer}")

        # Withdraw MANY prefixes rapidly (simulate full routing table loss)
        # Generate 50 synthetic prefixes to make anomaly stand out
        synthetic_prefixes = [f"192.168.{i}.0/24" for i in range(50)]

        # Send all withdrawals rapidly (within same bin)
        for prefix in synthetic_prefixes:
            await self.send_update(peer, "withdraw", [prefix])
            await asyncio.sleep(0.01)  # Very fast

    async def inject_bgp_flapping(self, device: str, prefix: str, peer: str, count: int = 30):
        """Simulate BGP route flapping."""
        print(f"[BGP Simulator] BGP flapping: {device} {prefix} (x{count})")

        for i in range(count):
            # Alternate announce/withdraw rapidly
            if i % 2 == 0:
                await self.send_update(peer, "announce", [prefix], [65000, 65001])
            else:
                await self.send_update(peer, "withdraw", [prefix])
            await asyncio.sleep(0.3)  # Faster flapping

    async def inject_route_leak(self, device: str, leaked_prefixes: List[str], peer: str):
        """Simulate route leak with suspicious AS path."""
        print(f"[BGP Simulator] Route leak: {device} leaking {len(leaked_prefixes)} prefixes")

        # Announce with long/suspicious AS path
        bad_as_path = [65000] * 10 + [65001, 65002]

        for prefix in leaked_prefixes:
            await self.send_update(peer, "announce", [prefix], bad_as_path)
            await asyncio.sleep(0.1)

    async def inject_mass_withdrawal(self, device: str, peer: str):
        """Simulate massive withdrawal event."""
        print(f"[BGP Simulator] Mass withdrawal: {device}")

        if device in self.prefixes:
            prefixes = self.prefixes[device]
            # Withdraw everything rapidly
            await self.send_update(peer, "withdraw", prefixes)

    async def inject_server_failure(self, server: str, peer: str):
        """Simulate single server failure (single /32 withdrawal)."""
        print(f"[BGP Simulator] Server failure: {server}")

        if server in self.prefixes:
            # Only withdraw the /32
            host_routes = [p for p in self.prefixes[server] if "/32" in p]
            if host_routes:
                await self.send_update(peer, "withdraw", host_routes)


async def main():
    """Test BGP simulator."""
    sim = BGPSimulator()
    await sim.connect()

    # Baseline
    await sim.baseline_traffic(10)

    # Test failures
    await sim.inject_link_failure("tor-01", "eth1", "10.0.1.1")
    await asyncio.sleep(5)

    await sim.inject_bgp_flapping("spine-01", "10.1.0.0/16", "10.0.1.2", count=10)
    await asyncio.sleep(5)

    await sim.inject_server_failure("server-01", "10.0.2.1")

    await sim.nc.close()
    print("[BGP Simulator] Done")


if __name__ == "__main__":
    asyncio.run(main())
