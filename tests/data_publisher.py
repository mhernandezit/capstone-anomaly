#!/usr/bin/env python3
"""
BGP Event Data Publisher for Testing

This module provides utilities to publish test BGP events to NATS for testing
the anomaly detection pipeline and dashboard.
"""

import asyncio
import json
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import random
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nats.aio.client import Client as NATS
from src.utils.schema import BGPUpdate


@dataclass
class TestScenario:
    """Configuration for a test scenario"""
    name: str
    description: str
    duration_seconds: int
    event_rate_per_second: float
    peers: List[str]
    prefixes: List[str]
    anomaly_type: Optional[str] = None


class BGPEventGenerator:
    """Generates realistic BGP events for testing"""
    
    def __init__(self):
        # Common BGP peers based on roles.yml structure
        self.default_peers = [
            "10.0.1.1",    # ToR switches
            "10.0.1.2", 
            "10.0.2.1",    # Spine switches  
            "10.0.2.2",
            "10.0.3.1",    # Edge routers
            "10.0.3.2",
            "10.0.4.1",    # Route reflectors
            "10.0.4.2"
        ]
        
        # Common prefixes for testing
        self.default_prefixes = [
            "192.168.1.0/24",
            "192.168.2.0/24", 
            "10.10.0.0/16",
            "172.16.0.0/16",
            "203.0.113.0/24",
            "198.51.100.0/24"
        ]
        
        # AS paths for realistic routing
        self.as_paths = [
            [65001, 65002],
            [65001, 65003, 65004], 
            [65002, 65005],
            [65003, 65006, 65007]
        ]

    def generate_normal_update(self, peer: str, prefixes: List[str]) -> BGPUpdate:
        """Generate a normal BGP UPDATE message"""
        prefix = random.choice(prefixes)
        as_path = random.choice(self.as_paths)
        
        # 80% announcements, 20% withdrawals for normal traffic
        if random.random() < 0.8:
            return BGPUpdate(
                ts=int(time.time()),
                peer=peer,
                type="UPDATE",
                announce=[prefix],
                withdraw=None,
                attrs={
                    "as_path": as_path,
                    "next_hop": peer,
                    "origin": "IGP",
                    "med": random.randint(0, 100)
                }
            )
        else:
            return BGPUpdate(
                ts=int(time.time()),
                peer=peer,
                type="UPDATE", 
                announce=None,
                withdraw=[prefix],
                attrs={}
            )

    def generate_route_leak(self, peer: str, prefixes: List[str]) -> List[BGPUpdate]:
        """Generate a route leak anomaly - peer announces many prefixes at once"""
        events = []
        leak_prefixes = random.sample(prefixes, min(len(prefixes), 3))
        
        for prefix in leak_prefixes:
            events.append(BGPUpdate(
                ts=int(time.time()),
                peer=peer,
                type="UPDATE",
                announce=[prefix],
                withdraw=None,
                attrs={
                    "as_path": [65999] + random.choice(self.as_paths),  # Suspicious AS
                    "next_hop": peer,
                    "origin": "INCOMPLETE"  # Suspicious origin
                }
            ))
        return events

    def generate_prefix_hijack(self, peer: str, target_prefix: str) -> BGPUpdate:
        """Generate a prefix hijack - peer announces prefix with suspicious AS path"""
        return BGPUpdate(
            ts=int(time.time()),
            peer=peer,
            type="UPDATE",
            announce=[target_prefix],
            withdraw=None,
            attrs={
                "as_path": [65666],  # Suspicious single AS  
                "next_hop": peer,
                "origin": "IGP"
            }
        )

    def generate_massive_withdrawal(self, peer: str, prefixes: List[str]) -> List[BGPUpdate]:
        """Generate massive withdrawal anomaly"""
        events = []
        withdraw_prefixes = random.sample(prefixes, min(len(prefixes), 4))
        
        # Single update with multiple withdrawals
        events.append(BGPUpdate(
            ts=int(time.time()),
            peer=peer,
            type="UPDATE",
            announce=None,
            withdraw=withdraw_prefixes,
            attrs={}
        ))
        return events


class DataPublisher:
    """Publishes test data to NATS"""
    
    def __init__(self, nats_url: str = "nats://localhost:4222"):
        self.nats_url = nats_url
        self.nc: Optional[NATS] = None
        self.generator = BGPEventGenerator()

    async def connect(self):
        """Connect to NATS"""
        self.nc = NATS()
        await self.nc.connect(servers=[self.nats_url])
        print(f"Connected to NATS at {self.nats_url}")

    async def disconnect(self):
        """Disconnect from NATS"""
        if self.nc:
            await self.nc.drain()
            print("Disconnected from NATS")

    async def publish_event(self, event: BGPUpdate, subject: str = "bgp.updates"):
        """Publish a single BGP event"""
        if not self.nc:
            raise RuntimeError("Not connected to NATS. Call connect() first.")
        
        event_json = event.model_dump_json()
        await self.nc.publish(subject, event_json.encode())

    async def publish_events(self, events: List[BGPUpdate], subject: str = "bgp.updates"):
        """Publish multiple BGP events"""
        for event in events:
            await self.publish_event(event, subject)

    async def run_scenario(self, scenario: TestScenario):
        """Run a complete test scenario"""
        print(f"\nStarting scenario: {scenario.name}")
        print(f"📄 Description: {scenario.description}")
        print(f"⏱️  Duration: {scenario.duration_seconds}s")
        print(f"Event rate: {scenario.event_rate_per_second}/s")
        
        start_time = time.time()
        event_count = 0
        
        while time.time() - start_time < scenario.duration_seconds:
            # Generate events based on scenario type
            if scenario.anomaly_type == "route_leak":
                # Inject route leak every 10 seconds
                if event_count % int(10 * scenario.event_rate_per_second) == 0:
                    peer = random.choice(scenario.peers)
                    events = self.generator.generate_route_leak(peer, scenario.prefixes)
                    await self.publish_events(events)
                    print(f" Injected route leak from {peer}")
                else:
                    # Normal traffic
                    peer = random.choice(scenario.peers)
                    event = self.generator.generate_normal_update(peer, scenario.prefixes)
                    await self.publish_event(event)
                    
            elif scenario.anomaly_type == "prefix_hijack":
                # Inject hijack every 15 seconds
                if event_count % int(15 * scenario.event_rate_per_second) == 0:
                    peer = random.choice(scenario.peers)
                    prefix = random.choice(scenario.prefixes)
                    event = self.generator.generate_prefix_hijack(peer, prefix)
                    await self.publish_event(event)
                    print(f" Injected prefix hijack: {peer} -> {prefix}")
                else:
                    # Normal traffic
                    peer = random.choice(scenario.peers)
                    event = self.generator.generate_normal_update(peer, scenario.prefixes)
                    await self.publish_event(event)
                    
            elif scenario.anomaly_type == "massive_withdrawal":
                # Inject massive withdrawal every 20 seconds
                if event_count % int(20 * scenario.event_rate_per_second) == 0:
                    peer = random.choice(scenario.peers)
                    events = self.generator.generate_massive_withdrawal(peer, scenario.prefixes)
                    await self.publish_events(events)
                    print(f" Injected massive withdrawal from {peer}")
                else:
                    # Normal traffic
                    peer = random.choice(scenario.peers)
                    event = self.generator.generate_normal_update(peer, scenario.prefixes)
                    await self.publish_event(event)
            else:
                # Normal traffic only
                peer = random.choice(scenario.peers)
                event = self.generator.generate_normal_update(peer, scenario.prefixes)
                await self.publish_event(event)
                
            event_count += 1
            
            # Control event rate
            await asyncio.sleep(1.0 / scenario.event_rate_per_second)
            
            # Progress indicator
            if event_count % int(scenario.event_rate_per_second * 10) == 0:
                elapsed = time.time() - start_time
                print(f" Published {event_count} events in {elapsed:.1f}s")
        
        print(f"Completed scenario: {scenario.name} ({event_count} events)")


# Pre-defined test scenarios
TEST_SCENARIOS = {
    "normal_traffic": TestScenario(
        name="Normal Traffic",
        description="Baseline BGP traffic with normal announcements and withdrawals",
        duration_seconds=60,
        event_rate_per_second=2.0,
        peers=["10.0.1.1", "10.0.1.2", "10.0.2.1"],
        prefixes=["192.168.1.0/24", "192.168.2.0/24", "10.10.0.0/16"]
    ),
    
    "route_leak_attack": TestScenario(
        name="Route Leak Attack",
        description="Simulates a route leak where a peer announces prefixes it shouldn't",
        duration_seconds=90,
        event_rate_per_second=3.0,
        peers=["10.0.1.1", "10.0.2.1", "10.0.3.1"],
        prefixes=["192.168.1.0/24", "192.168.2.0/24", "203.0.113.0/24"],
        anomaly_type="route_leak"
    ),
    
    "prefix_hijack": TestScenario(
        name="Prefix Hijack",
        description="Simulates prefix hijacking with suspicious AS paths",
        duration_seconds=75,
        event_rate_per_second=2.5,
        peers=["10.0.1.2", "10.0.2.2", "10.0.4.1"],
        prefixes=["198.51.100.0/24", "172.16.0.0/16"],
        anomaly_type="prefix_hijack"
    ),
    
    "massive_withdrawal": TestScenario(
        name="Massive Withdrawal",
        description="Simulates massive route withdrawals indicating network problems",
        duration_seconds=60,
        event_rate_per_second=4.0,
        peers=["10.0.3.1", "10.0.4.1", "10.0.4.2"],
        prefixes=["192.168.1.0/24", "192.168.2.0/24", "10.10.0.0/16", "203.0.113.0/24"],
        anomaly_type="massive_withdrawal"
    ),
    
    "high_volume": TestScenario(
        name="High Volume Traffic",
        description="High volume normal traffic to test system performance",
        duration_seconds=120,
        event_rate_per_second=10.0,
        peers=["10.0.1.1", "10.0.1.2", "10.0.2.1", "10.0.2.2", "10.0.3.1", "10.0.3.2"],
        prefixes=["192.168.1.0/24", "192.168.2.0/24", "10.10.0.0/16", "172.16.0.0/16", "203.0.113.0/24", "198.51.100.0/24"]
    )
}


async def main():
    """Interactive test runner"""
    publisher = DataPublisher()
    
    try:
        await publisher.connect()
        
        print("\n🧪 BGP Event Test Publisher")
        print("=" * 50)
        print("Available test scenarios:")
        
        for i, (key, scenario) in enumerate(TEST_SCENARIOS.items(), 1):
            print(f"{i}. {scenario.name}")
            print(f"   {scenario.description}")
            print(f"   Duration: {scenario.duration_seconds}s, Rate: {scenario.event_rate_per_second}/s")
            print()
        
        while True:
            try:
                choice = input("Enter scenario number (1-5) or 'q' to quit: ").strip()
                
                if choice.lower() == 'q':
                    break
                    
                choice_num = int(choice)
                if 1 <= choice_num <= len(TEST_SCENARIOS):
                    scenario_key = list(TEST_SCENARIOS.keys())[choice_num - 1]
                    scenario = TEST_SCENARIOS[scenario_key]
                    
                    confirm = input(f"Run '{scenario.name}'? (y/n): ").strip().lower()
                    if confirm == 'y':
                        await publisher.run_scenario(scenario)
                        print("\n" + "="*50)
                else:
                    print("Invalid choice. Please try again.")
                    
            except (ValueError, KeyboardInterrupt):
                print("\nExiting...")
                break
                
    finally:
        await publisher.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
