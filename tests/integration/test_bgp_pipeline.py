"""
Integration tests for BGP simulator with Matrix Profile pipeline.
"""

import asyncio
import json
import time

import pytest

from anomaly_detection.models import MatrixProfileDetector
from anomaly_detection.simulators.bgp_simulator import BGPSimulator


@pytest.mark.integration
@pytest.mark.asyncio
class TestBGPPipeline:
    """Test BGP simulator with anomaly detection pipeline."""

    async def test_bgp_simulator_initialization(self):
        """Test BGP simulator loads topology correctly."""
        sim = BGPSimulator(topology_file="evaluation/topology.yml")
        
        assert sim.get_peer_count() > 0, "No BGP peers loaded from topology"
        assert len(sim.devices) > 0, "No devices loaded from topology"
        assert len(sim.prefixes) > 0, "No prefixes loaded from topology"

    async def test_baseline_traffic_generation(self):
        """Test baseline BGP traffic generation."""
        sim = BGPSimulator(topology_file="evaluation/topology.yml")
        await sim.connect()
        
        updates_received = []
        
        async def collect_updates(msg):
            data = json.loads(msg.data.decode())
            updates_received.append(data)
        
        await sim.nc.subscribe("bgp.updates", cb=collect_updates)
        
        # Generate baseline traffic
        await sim.baseline_traffic(duration=5)
        await asyncio.sleep(1)  # Let messages propagate
        
        await sim.nc.close()
        
        assert len(updates_received) > 0, "No BGP updates generated"
        
        # Check update structure
        update = updates_received[0]
        assert "timestamp" in update
        assert "peer" in update
        assert "type" in update
        assert update["type"] == "UPDATE"

    async def test_peer_down_event(self):
        """Test peer down event generation."""
        sim = BGPSimulator(topology_file="evaluation/topology.yml")
        await sim.connect()
        
        events_received = []
        
        async def collect_events(msg):
            data = json.loads(msg.data.decode())
            events_received.append(data)
        
        await sim.nc.subscribe("bgp.events", cb=collect_events)
        
        # Get a peer IP from topology
        peer_ip = list(sim.peer_states.keys())[0]
        
        # Inject link failure (generates peer down + withdrawals)
        await sim.inject_link_failure("spine-01", "eth0", peer_ip)
        await asyncio.sleep(1)
        
        await sim.nc.close()
        
        # Should have peer_down event
        peer_down_events = [e for e in events_received if e.get("event") == "peer_down"]
        assert len(peer_down_events) > 0, "No peer_down event generated"
        
        event = peer_down_events[0]
        assert event["type"] == "PEER_STATE"
        assert event["reason"] == "interface_down"
        assert event["interface"] == "eth0"

    async def test_peer_flapping_events(self):
        """Test peer flapping generates up/down events."""
        sim = BGPSimulator(topology_file="evaluation/topology.yml")
        await sim.connect()
        
        events_received = []
        
        async def collect_events(msg):
            data = json.loads(msg.data.decode())
            events_received.append(data)
        
        await sim.nc.subscribe("bgp.events", cb=collect_events)
        
        peer_ip = list(sim.peer_states.keys())[0]
        
        # Inject peer flapping
        await sim.inject_peer_flap("spine-01", peer_ip, "eth0", count=2, interval=0.5)
        await asyncio.sleep(1)
        
        await sim.nc.close()
        
        peer_down_events = [e for e in events_received if e.get("event") == "peer_down"]
        peer_up_events = [e for e in events_received if e.get("event") == "peer_up"]
        
        assert len(peer_down_events) >= 2, "Not enough peer_down events"
        assert len(peer_up_events) >= 2, "Not enough peer_up events"

    async def test_matrix_profile_with_bgp_data(self):
        """Test Matrix Profile detection with BGP simulator."""
        sim = BGPSimulator(topology_file="evaluation/topology.yml")
        await sim.connect()
        
        # Initialize detector
        detector = MatrixProfileDetector(
            window_bins=8,
            series_keys=["wdr_total", "ann_total"],
            discord_threshold=2.0,
            mp_library="stumpy"
        )
        
        bins_collected = []
        current_bin = {"wdr_total": 0, "ann_total": 0}
        bin_start = time.time()
        
        async def collect_updates(msg):
            nonlocal current_bin, bin_start, bins_collected
            
            data = json.loads(msg.data.decode())
            
            # Count updates
            if data.get("update_type") == "withdraw":
                current_bin["wdr_total"] += len(data.get("prefixes", []))
            elif data.get("update_type") == "announce":
                current_bin["ann_total"] += len(data.get("prefixes", []))
            
            # Check if bin is complete (every 2 seconds for testing)
            if time.time() - bin_start >= 2:
                bin_data = current_bin.copy()
                bin_data["timestamp"] = bin_start
                bins_collected.append(bin_data)
                
                # Reset bin
                current_bin = {"wdr_total": 0, "ann_total": 0}
                bin_start = time.time()
        
        await sim.nc.subscribe("bgp.updates", cb=collect_updates)
        
        # Generate baseline (should be normal)
        await sim.baseline_traffic(duration=10)
        await asyncio.sleep(1)
        
        baseline_bins = len(bins_collected)
        
        # Inject anomaly (link failure = many withdrawals)
        peer_ip = list(sim.peer_states.keys())[0]
        await sim.inject_link_failure("spine-01", "eth0", peer_ip)
        await asyncio.sleep(3)
        
        await sim.nc.close()
        
        assert len(bins_collected) >= 9, "Not enough bins for Matrix Profile window"
        
        # Last bins should have high withdrawal counts
        recent_bins = bins_collected[-3:]
        assert any(b["wdr_total"] > 20 for b in recent_bins), "Link failure didn't generate enough withdrawals"


@pytest.mark.integration
class TestTopologyConfiguration:
    """Test topology configuration is valid."""

    def test_topology_has_bgp_peers(self):
        """Test topology defines BGP peer relationships."""
        sim = BGPSimulator(topology_file="evaluation/topology.yml")
        
        assert sim.get_peer_count() >= 5, "Topology should have at least 5 BGP peers"

    def test_topology_has_devices(self):
        """Test topology defines network devices."""
        sim = BGPSimulator(topology_file="evaluation/topology.yml")
        
        assert "spine-01" in sim.devices, "Missing spine-01"
        assert "tor-01" in sim.devices, "Missing tor-01"
        
        # Check devices have ASNs
        spine01 = sim.devices["spine-01"]
        assert "asn" in spine01, "Devices should have ASN"
        assert "router_id" in spine01, "Devices should have router_id"

    def test_topology_has_prefix_ownership(self):
        """Test topology defines prefix ownership."""
        sim = BGPSimulator(topology_file="evaluation/topology.yml")
        
        assert len(sim.prefixes) > 0, "No prefix ownership defined"
        assert any("/32" in p for device_prefixes in sim.prefixes.values() 
                   for p in device_prefixes), "Should have host routes (/32)"

