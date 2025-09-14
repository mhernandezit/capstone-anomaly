#!/usr/bin/env python3
"""
Quick BGP Event Publisher

A simple script to publish a few test BGP events immediately.
Suitable for testing if the dashboard is receiving data.
"""

import asyncio
import time
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nats.aio.client import Client as NATS
from src.utils.schema import BGPUpdate


async def publish_test_events():
    """Publish a few test BGP events to verify the pipeline works"""
    
    # Connect to NATS
    nc = NATS()
    await nc.connect(servers=["nats://localhost:4222"])
    print("Connected to NATS")
    
    # Create some test BGP events
    test_events = [
        BGPUpdate(
            ts=int(time.time()),
            peer="10.0.1.1",
            type="UPDATE",
            announce=["192.168.1.0/24"],
            withdraw=None,
            attrs={
                "as_path": [65001, 65002],
                "next_hop": "10.0.1.1",
                "origin": "IGP"
            }
        ),
        BGPUpdate(
            ts=int(time.time()) + 1,
            peer="10.0.2.1", 
            type="UPDATE",
            announce=None,
            withdraw=["192.168.2.0/24"],
            attrs={}
        ),
        BGPUpdate(
            ts=int(time.time()) + 2,
            peer="10.0.3.1",
            type="UPDATE", 
            announce=["203.0.113.0/24"],
            withdraw=None,
            attrs={
                "as_path": [65003, 65004, 65005],
                "next_hop": "10.0.3.1", 
                "origin": "IGP",
                "med": 50
            }
        )
    ]
    
    # Publish events to both subjects the system expects
    for i, event in enumerate(test_events, 1):
        # Publish to the subject the pipeline consumes
        await nc.publish("bgp.updates", event.model_dump_json().encode())
        
        # Also publish directly to dashboard subject for immediate display
        await nc.publish("bgp.events", event.model_dump_json().encode())
        
        print(f"📤 Published test event {i}: {event.peer} -> {event.announce or event.withdraw}")
        await asyncio.sleep(1)  # Space out the events
    
    # Wait a moment then disconnect
    await asyncio.sleep(2)
    await nc.drain()
    print("Test events published successfully!")
    print("Check dashboard at http://localhost:8501")


if __name__ == "__main__":
    asyncio.run(publish_test_events())
