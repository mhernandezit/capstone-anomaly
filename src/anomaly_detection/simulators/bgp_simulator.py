#!/usr/bin/env python3
"""
Simple BGP UPDATE Message Generator

Generates BGP UPDATE messages (announcements/withdrawals) and peer state events
for testing the anomaly detection pipeline. Does not implement full BGP FSM or
routing tables - just emits realistic messages.

For realistic BGP testing, use containerlab + FRRouting + BMP collector.
"""

import asyncio
import json
import random
import time
from typing import Dict, List, Optional

import yaml
from nats.aio.client import Client as NATS


class BGPSimulator:
    """
    Simple BGP message simulator for testing.
    
    Generates:
    - BGP UPDATE messages (announces/withdrawals)
    - Peer state change events (peer down/up with reason)
    - Various failure scenarios
    """

    def __init__(self, topology_file: str = None):
        if topology_file is None:
            import os
            # Try multiple locations
            possible_paths = [
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "evaluation", "topology.yml"),
                "evaluation/topology.yml",
                "../../../evaluation/topology.yml"
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    topology_file = path
                    break
            else:
                raise FileNotFoundError(f"topology.yml not found. Tried: {possible_paths}")

        with open(topology_file) as f:
            self.topology = yaml.safe_load(f)

        self.devices = self.topology.get("devices", {})
        self.bgp_peers = self.topology.get("bgp_peers", [])
        self.prefixes = self.topology.get("prefixes", {})
        
        # Track peer states (up/down)
        self.peer_states = {}  # peer_ip -> True (up) / False (down)
        self._initialize_peers()

    def _initialize_peers(self):
        """Initialize peer state tracking from topology."""
        for peer_config in self.bgp_peers:
            local_ip = peer_config.get("local_ip")
            remote_ip = peer_config.get("remote_ip")
            
            # Track both directions
            if local_ip:
                self.peer_states[local_ip] = True  # Start in up state
            if remote_ip:
                self.peer_states[remote_ip] = True

    async def connect(self, nats_url: str = "nats://localhost:4222"):
        """Connect to NATS."""
        self.nc = NATS()
        await self.nc.connect(nats_url)
        print(f"[BGP Simulator] Connected to NATS at {nats_url}")

    async def send_update(
        self, 
        peer: str, 
        update_type: str, 
        prefixes: List[str], 
        as_path: Optional[List[int]] = None
    ):
        """
        Send a BGP UPDATE message.
        
        Args:
            peer: Peer IP address
            update_type: "announce" or "withdraw"
            prefixes: List of prefixes affected
            as_path: AS path (for announcements)
        """
        msg = {
            "timestamp": time.time(),
            "peer": peer,
            "type": "UPDATE",
            "update_type": update_type,
            "prefixes": prefixes,
            "as_path": as_path or [],
        }

        await self.nc.publish("bgp.updates", json.dumps(msg).encode())

    async def send_peer_event(
        self,
        peer: str,
        event_type: str,
        reason: Optional[str] = None,
        interface: Optional[str] = None
    ):
        """
        Send a BGP peer state change event.
        
        Args:
            peer: Peer IP address
            event_type: "peer_down" or "peer_up"
            reason: Reason for state change (e.g., "interface_down", "hold_timer_expired")
            interface: Interface name (e.g., "eth0")
        """
        msg = {
            "timestamp": time.time(),
            "peer": peer,
            "type": "PEER_STATE",
            "event": event_type,
            "reason": reason,
            "interface": interface
        }

        await self.nc.publish("bgp.events", json.dumps(msg).encode())
        
        # Update internal state
        self.peer_states[peer] = (event_type == "peer_up")

    async def baseline_traffic(self, duration: int = 30):
        """
        Generate baseline BGP traffic (normal operation).
        
        Args:
            duration: Duration in seconds
        """
        print(f"[BGP Simulator] Baseline traffic for {duration}s...")
        start = time.time()
        count = 0

        while time.time() - start < duration:
            # Random announcements (70%) and withdrawals (30%)
            if random.random() < 0.7:
                device = random.choice(list(self.prefixes.keys()))
                prefix = random.choice(self.prefixes[device])
                peer_ip = self._get_random_peer_ip()
                
                # Generate AS path (2-4 hops)
                as_path = [65000 + random.randint(1, 10) for _ in range(random.randint(2, 4))]
                
                await self.send_update(peer_ip, "announce", [prefix], as_path)
            else:
                device = random.choice(list(self.prefixes.keys()))
                prefix = random.choice(self.prefixes[device])
                peer_ip = self._get_random_peer_ip()
                await self.send_update(peer_ip, "withdraw", [prefix])

            count += 1
            await asyncio.sleep(random.uniform(0.2, 0.8))

        print(f"[BGP Simulator] Baseline complete: {count} updates sent")

    async def inject_link_failure(self, device: str, interface: str, peer_ip: str):
        """
        Simulate link failure.
        
        Generates:
        1. Peer down event with reason "interface_down"
        2. Withdrawal of all prefixes from that peer
        
        Args:
            device: Device name
            interface: Interface name (e.g., "eth0")
            peer_ip: Peer IP address
        """
        print(f"[BGP Simulator] Link failure: {device} {interface} -> {peer_ip}")

        # Send peer down event
        await self.send_peer_event(
            peer=peer_ip,
            event_type="peer_down",
            reason="interface_down",
            interface=interface
        )
        
        await asyncio.sleep(0.1)

        # Withdraw MANY prefixes rapidly (simulate full routing table loss)
        synthetic_prefixes = [f"192.168.{i}.0/24" for i in range(50)]

        for prefix in synthetic_prefixes:
            await self.send_update(peer_ip, "withdraw", [prefix])
            await asyncio.sleep(0.01)

    async def inject_peer_flap(
        self, 
        device: str, 
        peer_ip: str, 
        interface: str,
        count: int = 5,
        interval: float = 2.0
    ):
        """
        Simulate BGP peer flapping (rapid up/down).
        
        Args:
            device: Device name
            peer_ip: Peer IP address
            interface: Interface name
            count: Number of flap cycles
            interval: Time between flaps
        """
        print(f"[BGP Simulator] Peer flapping: {device} <-> {peer_ip} (x{count})")

        for i in range(count):
            # Peer goes down
            await self.send_peer_event(
                peer=peer_ip,
                event_type="peer_down",
                reason="hold_timer_expired" if i % 2 == 0 else "connection_reset",
                interface=interface
            )
            
            # Withdrawals
            if device in self.prefixes:
                await self.send_update(peer_ip, "withdraw", self.prefixes[device])
            
            await asyncio.sleep(interval / 2)
            
            # Peer comes back up
            await self.send_peer_event(
                peer=peer_ip,
                event_type="peer_up",
                interface=interface
            )
            
            # Re-announce prefixes
            if device in self.prefixes:
                await self.send_update(
                    peer_ip, 
                    "announce", 
                    self.prefixes[device],
                    as_path=[65000, 65001]
                )
            
            await asyncio.sleep(interval / 2)

    async def inject_bgp_flapping(self, device: str, prefix: str, peer: str, count: int = 30):
        """
        Simulate BGP route flapping (specific prefix).
        
        Args:
            device: Device name
            prefix: Prefix to flap
            peer: Peer IP
            count: Number of announce/withdraw cycles
        """
        print(f"[BGP Simulator] BGP route flapping: {device} {prefix} (x{count})")

        for i in range(count):
            # Alternate announce/withdraw rapidly
            if i % 2 == 0:
                await self.send_update(peer, "announce", [prefix], [65000, 65001])
            else:
                await self.send_update(peer, "withdraw", [prefix])
            await asyncio.sleep(0.3)

    async def inject_route_leak(self, device: str, leaked_prefixes: List[str], peer: str):
        """
        Simulate route leak with suspicious AS path.
        
        Args:
            device: Device name
            leaked_prefixes: Prefixes being leaked
            peer: Peer IP
        """
        print(f"[BGP Simulator] Route leak: {device} leaking {len(leaked_prefixes)} prefixes")

        # Announce with long/suspicious AS path (AS path prepending)
        bad_as_path = [65000] * 10 + [65001, 65002]

        for prefix in leaked_prefixes:
            await self.send_update(peer, "announce", [prefix], bad_as_path)
            await asyncio.sleep(0.1)

    async def inject_mass_withdrawal(self, device: str, peer: str):
        """
        Simulate massive withdrawal event.
        
        Args:
            device: Device name
            peer: Peer IP
        """
        print(f"[BGP Simulator] Mass withdrawal: {device}")

        if device in self.prefixes:
            prefixes = self.prefixes[device]
            await self.send_update(peer, "withdraw", prefixes)

    async def inject_server_failure(self, server: str, peer: str):
        """
        Simulate single server failure (single /32 withdrawal).
        
        Args:
            server: Server name
            peer: Peer IP
        """
        print(f"[BGP Simulator] Server failure: {server}")

        if server in self.prefixes:
            # Only withdraw the /32
            host_routes = [p for p in self.prefixes[server] if "/32" in p]
            if host_routes:
                await self.send_update(peer, "withdraw", host_routes)

    def _get_random_peer_ip(self) -> str:
        """Get a random peer IP from the topology."""
        if self.bgp_peers:
            peer = random.choice(self.bgp_peers)
            return peer.get("local_ip") or peer.get("remote_ip", "10.0.1.1")
        return "10.0.1.1"

    def _get_peer_for_device(self, device: str) -> Optional[str]:
        """Get peer IP for a specific device."""
        for peer_config in self.bgp_peers:
            if peer_config.get("local_device") == device:
                return peer_config.get("remote_ip")
            if peer_config.get("remote_device") == device:
                return peer_config.get("local_ip")
        return None

    def get_peer_count(self) -> int:
        """Get number of BGP peers."""
        return len(self.bgp_peers)

    def get_peer_states(self) -> Dict[str, bool]:
        """Get current state of all peers."""
        return self.peer_states.copy()


async def main():
    """Test BGP simulator."""
    print("=" * 70)
    print("Simple BGP Simulator Test")
    print("=" * 70)
    
    sim = BGPSimulator()
    await sim.connect()

    print(f"\n[INFO] Loaded topology with {sim.get_peer_count()} BGP peers")
    print(f"[INFO] Peer IPs: {list(sim.peer_states.keys())}")

    # Baseline
    print("\n[TEST 1] Baseline traffic")
    await sim.baseline_traffic(10)

    # Test peer down event
    print("\n[TEST 2] Link failure with peer down")
    peer_ip = list(sim.peer_states.keys())[0] if sim.peer_states else "10.0.1.1"
    await sim.inject_link_failure("tor-01", "eth1", peer_ip)
    await asyncio.sleep(3)

    # Test peer flapping
    print("\n[TEST 3] Peer flapping")
    await sim.inject_peer_flap("spine-01", peer_ip, "eth0", count=3, interval=1.5)
    await asyncio.sleep(3)

    # Test route flapping
    print("\n[TEST 4] Route flapping")
    await sim.inject_bgp_flapping("spine-01", "10.1.0.0/16", peer_ip, count=10)
    await asyncio.sleep(3)

    # Test route leak
    print("\n[TEST 5] Route leak")
    leaked_prefixes = [f"198.51.{i}.0/24" for i in range(1, 11)]
    await sim.inject_route_leak("edge-01", leaked_prefixes, peer_ip)

    await sim.nc.close()
    print("\n[BGP Simulator] Done")


if __name__ == "__main__":
    asyncio.run(main())
