#!/usr/bin/env python3
"""
Simple BGP Data Collector for Enterprise Lab

This script simulates BGP data collection from the enterprise network
and publishes updates to NATS for the ML pipeline.
"""

import asyncio
import json
import nats
import random
import time
from datetime import datetime

async def publish_bgp_data():
    try:
        # Connect to NATS
        nc = await nats.connect("nats://localhost:4222")
        print("Connected to NATS server")
        
        # Simulate enterprise network peers
        peers = [
            "172.20.20.2",   # spine-01
            "172.20.20.3",   # spine-02  
            "172.20.20.4",   # tor-01
            "172.20.20.5",   # tor-02
            "172.20.20.6",   # edge-01
            "172.20.20.7",   # edge-02
            "172.20.20.8",   # server-01
            "172.20.20.9",   # server-02
            "172.20.20.10",  # server-03
            "172.20.20.11",  # server-04
        ]
        
        # Simulate route prefixes
        routes = [
            "10.1.0.0/16", "10.2.0.0/16", "10.3.0.0/16", "10.4.0.0/16",
            "10.10.0.0/16", "10.11.0.0/16", "10.12.0.0/16", "10.13.0.0/16",
            "172.16.0.0/16", "172.17.0.0/16", "172.18.0.0/16", "172.19.0.0/16",
            "192.168.1.0/24", "192.168.2.0/24", "192.168.3.0/24", "192.168.4.0/24",
            "203.0.1.0/24", "203.0.2.0/24", "203.0.3.0/24", "203.0.4.0/24",
        ]
        
        # ASNs for different network tiers
        asns = [65000, 65100, 65200, 65300, 65400]
        
        print(f"Starting BGP data collection for {len(peers)} peers...")
        
        while True:
            # Generate 1-5 updates per second to simulate realistic traffic
            num_updates = random.randint(1, 5)
            for _ in range(num_updates):
                # Generate random BGP update
                data = {
                    "timestamp": datetime.now().isoformat(),
                    "peer": random.choice(peers),
                    "type": random.choice(["UPDATE", "KEEPALIVE", "NOTIFICATION"]),
                    "as_path": str(random.choice(asns)),
                    "next_hop": random.choice(peers),
                    "origin": "IGP",
                    "local_pref": random.randint(50, 150),
                    "med": random.randint(0, 100)
                }
                
                # Add announce/withdraw based on message type
                if data["type"] == "UPDATE":
                    if random.random() < 0.7:  # 70% chance of announcement
                        data["announce"] = [random.choice(routes)]
                    else:  # 30% chance of withdrawal
                        data["withdraw"] = [random.choice(routes)]
                
                # Publish to NATS
                await nc.publish("bgp.updates", json.dumps(data).encode())
                print(f"Published: {data['type']} from {data['peer']} (AS{data['as_path']})")
            
            # Wait 1 second before next batch
            await asyncio.sleep(1)
            
    except Exception as e:
        print(f"Error in BGP data collector: {e}")
        time.sleep(5)

if __name__ == "__main__":
    print("BGP Data Collector Starting...")
    asyncio.run(publish_bgp_data())
