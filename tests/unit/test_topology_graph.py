#!/usr/bin/env python3
"""
Unit tests for NetworkTopologyGraph class.

Tests the topology graph functionality including device loading,
graph traversal, blast radius calculation, and SPOF detection.
"""

import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch, mock_open

from anomaly_detection.topology import (
    NetworkTopologyGraph,
    DeviceRole,
    FailureDomain,
    DeviceMetadata,
    BGPPeer,
)


class TestNetworkTopologyGraph:
    """Test cases for NetworkTopologyGraph class."""

    @pytest.fixture
    def sample_topology_config(self):
        """Sample topology configuration for testing."""
        return {
            "devices": {
                "spine-01": {
                    "role": "spine",
                    "asn": 65001,
                    "router_id": "10.0.0.1",
                    "rack": "R01",
                    "datacenter": "DC1",
                    "interfaces": [
                        {"name": "eth0", "ip": "10.1.1.1/30", "peer": "tor-01"},
                        {"name": "eth1", "ip": "10.1.1.5/30", "peer": "tor-02"},
                    ],
                },
                "spine-02": {
                    "role": "spine",
                    "asn": 65002,
                    "router_id": "10.0.0.2",
                    "interfaces": [
                        {"name": "eth0", "ip": "10.1.2.1/30", "peer": "tor-01"},
                        {"name": "eth1", "ip": "10.1.2.5/30", "peer": "tor-02"},
                    ],
                },
                "tor-01": {
                    "role": "tor",
                    "asn": 65101,
                    "router_id": "10.0.1.1",
                    "interfaces": [
                        {"name": "eth0", "ip": "10.1.1.2/30", "peer": "spine-01"},
                        {"name": "eth1", "ip": "10.1.2.2/30", "peer": "spine-02"},
                        {"name": "eth2", "ip": "10.2.1.1/30", "peer": "server-01"},
                    ],
                },
                "tor-02": {
                    "role": "tor",
                    "asn": 65102,
                    "router_id": "10.0.1.2",
                    "interfaces": [
                        {"name": "eth0", "ip": "10.1.1.6/30", "peer": "spine-01"},
                        {"name": "eth1", "ip": "10.1.2.6/30", "peer": "spine-02"},
                        {"name": "eth2", "ip": "10.2.2.1/30", "peer": "server-02"},
                    ],
                },
                "edge-01": {
                    "role": "edge",
                    "asn": 65200,
                    "router_id": "10.0.2.1",
                    "interfaces": [
                        {"name": "eth0", "ip": "10.1.1.10/30", "peer": "spine-01"},
                        {"name": "eth1", "ip": "10.1.2.10/30", "peer": "spine-02"},
                    ],
                },
                "server-01": {
                    "role": "server",
                    "asn": 65301,
                    "router_id": "10.0.3.1",
                    "interfaces": [
                        {"name": "eth0", "ip": "10.2.1.2/30", "peer": "tor-01"},
                    ],
                },
                "server-02": {
                    "role": "server",
                    "asn": 65302,
                    "router_id": "10.0.3.2",
                    "interfaces": [
                        {"name": "eth0", "ip": "10.2.2.2/30", "peer": "tor-02"},
                    ],
                },
            },
            "bgp_peers": [
                {
                    "local_device": "spine-01",
                    "local_asn": 65001,
                    "local_ip": "10.1.1.1",
                    "remote_device": "tor-01",
                    "remote_asn": 65101,
                    "remote_ip": "10.1.1.2",
                    "session_type": "eBGP",
                },
                {
                    "local_device": "spine-01",
                    "local_asn": 65001,
                    "local_ip": "10.1.1.5",
                    "remote_device": "tor-02",
                    "remote_asn": 65102,
                    "remote_ip": "10.1.1.6",
                    "session_type": "eBGP",
                },
                {
                    "local_device": "spine-02",
                    "local_asn": 65002,
                    "local_ip": "10.1.2.1",
                    "remote_device": "tor-01",
                    "remote_asn": 65101,
                    "remote_ip": "10.1.2.2",
                    "session_type": "eBGP",
                },
                {
                    "local_device": "spine-02",
                    "local_asn": 65002,
                    "local_ip": "10.1.2.5",
                    "remote_device": "tor-02",
                    "remote_asn": 65102,
                    "remote_ip": "10.1.2.6",
                    "session_type": "eBGP",
                },
                {
                    "local_device": "tor-01",
                    "local_asn": 65101,
                    "local_ip": "10.2.1.1",
                    "remote_device": "server-01",
                    "remote_asn": 65301,
                    "remote_ip": "10.2.1.2",
                    "session_type": "eBGP",
                },
                {
                    "local_device": "tor-02",
                    "local_asn": 65102,
                    "local_ip": "10.2.2.1",
                    "remote_device": "server-02",
                    "remote_asn": 65302,
                    "remote_ip": "10.2.2.2",
                    "session_type": "eBGP",
                },
                {
                    "local_device": "spine-01",
                    "local_asn": 65001,
                    "local_ip": "10.1.1.9",
                    "remote_device": "edge-01",
                    "remote_asn": 65200,
                    "remote_ip": "10.1.1.10",
                    "session_type": "eBGP",
                },
                {
                    "local_device": "spine-02",
                    "local_asn": 65002,
                    "local_ip": "10.1.2.9",
                    "remote_device": "edge-01",
                    "remote_asn": 65200,
                    "remote_ip": "10.1.2.10",
                    "session_type": "eBGP",
                },
            ],
            "prefixes": {
                "spine-01": ["10.0.0.0/24"],
                "spine-02": ["10.0.0.0/24"],
                "tor-01": ["10.10.1.0/24", "192.168.100.0/24"],
                "tor-02": ["10.10.2.0/24", "192.168.101.0/24"],
                "edge-01": ["0.0.0.0/0", "203.0.113.0/24"],
                "server-01": ["10.10.1.1/32"],
                "server-02": ["10.10.2.1/32"],
            },
        }

    @pytest.fixture
    def temp_topology_file(self, sample_topology_config):
        """Create a temporary topology file for testing."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            yaml.dump(sample_topology_config, f)
            return f.name

    def test_init_with_valid_config(self, temp_topology_file):
        """Test initialization with valid topology configuration."""
        graph = NetworkTopologyGraph(temp_topology_file)
        
        assert len(graph.devices) == 7
        assert len(graph.bgp_peers) == 8
        assert len(graph.prefixes) == 7
        assert len(graph.adjacency_list) == 7
        
        # Verify device loading
        assert "spine-01" in graph.devices
        assert graph.devices["spine-01"].role == DeviceRole.SPINE
        assert graph.devices["spine-01"].asn == 65001
        assert graph.devices["spine-01"].rack == "R01"
        assert graph.devices["spine-01"].datacenter == "DC1"

    def test_init_with_missing_file(self):
        """Test initialization with missing topology file."""
        with patch("anomaly_detection.topology.network_graph.logger") as mock_logger:
            graph = NetworkTopologyGraph("nonexistent.yml")
            
            assert len(graph.devices) == 0
            assert len(graph.bgp_peers) == 0
            assert len(graph.prefixes) == 0
            mock_logger.warning.assert_called_once()

    def test_init_with_invalid_yaml(self):
        """Test initialization with invalid YAML file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write("invalid: yaml: content: [")
            f.flush()
            
            with patch("anomaly_detection.topology.network_graph.logger") as mock_logger:
                graph = NetworkTopologyGraph(f.name)
                
                assert len(graph.devices) == 0
                mock_logger.error.assert_called_once()

    def test_get_device_role(self, temp_topology_file):
        """Test device role retrieval."""
        graph = NetworkTopologyGraph(temp_topology_file)
        
        assert graph.get_device_role("spine-01") == DeviceRole.SPINE
        assert graph.get_device_role("tor-01") == DeviceRole.TOR
        assert graph.get_device_role("edge-01") == DeviceRole.EDGE
        assert graph.get_device_role("server-01") == DeviceRole.SERVER
        assert graph.get_device_role("nonexistent") == DeviceRole.UNKNOWN

    def test_get_device_metadata(self, temp_topology_file):
        """Test device metadata retrieval."""
        graph = NetworkTopologyGraph(temp_topology_file)
        
        metadata = graph.get_device_metadata("spine-01")
        assert metadata is not None
        assert metadata.name == "spine-01"
        assert metadata.role == DeviceRole.SPINE
        assert metadata.asn == 65001
        assert metadata.rack == "R01"
        assert metadata.datacenter == "DC1"
        
        assert graph.get_device_metadata("nonexistent") is None

    def test_get_downstream_devices(self, temp_topology_file):
        """Test downstream device discovery."""
        graph = NetworkTopologyGraph(temp_topology_file)
        
        # Test spine-01 downstream (should include tor-01, tor-02, edge-01)
        downstream = graph.get_downstream_devices("spine-01")
        assert len(downstream) == 5  # tor-01, tor-02, edge-01, server-01, server-02
        assert "tor-01" in downstream
        assert "tor-02" in downstream
        assert "edge-01" in downstream
        
        # Test tor-01 downstream (should include server-01)
        downstream = graph.get_downstream_devices("tor-01")
        assert len(downstream) == 1
        assert "server-01" in downstream
        
        # Test server-01 downstream (should be empty)
        downstream = graph.get_downstream_devices("server-01")
        assert len(downstream) == 0
        
        # Test nonexistent device
        downstream = graph.get_downstream_devices("nonexistent")
        assert len(downstream) == 0

    def test_calculate_blast_radius(self, temp_topology_file):
        """Test blast radius calculation."""
        graph = NetworkTopologyGraph(temp_topology_file)
        
        # Test spine device (high impact)
        affected_count, services, has_redundancy = graph.calculate_blast_radius("spine-01")
        assert affected_count >= 6  # spine + downstream devices
        assert "east_west_traffic" in services
        assert has_redundancy  # spine has multiple peers
        
        # Test tor device (medium impact)
        affected_count, services, has_redundancy = graph.calculate_blast_radius("tor-01")
        assert affected_count >= 2  # tor + server
        assert "rack_connectivity" in services
        
        # Test server device (low impact)
        affected_count, services, has_redundancy = graph.calculate_blast_radius("server-01")
        assert affected_count == 1  # just the server
        assert "application" in services
        assert has_redundancy  # servers have redundancy
        
        # Test nonexistent device
        affected_count, services, has_redundancy = graph.calculate_blast_radius("nonexistent")
        assert affected_count == 1
        assert "unknown" in services
        assert not has_redundancy

    def test_get_peer_devices(self, temp_topology_file):
        """Test peer device retrieval."""
        graph = NetworkTopologyGraph(temp_topology_file)
        
        # Test spine-01 peers
        peers = graph.get_peer_devices("spine-01")
        assert len(peers) == 3
        assert "tor-01" in peers
        assert "tor-02" in peers
        assert "edge-01" in peers
        
        # Test tor-01 peers
        peers = graph.get_peer_devices("tor-01")
        assert len(peers) == 3
        assert "spine-01" in peers
        assert "spine-02" in peers
        assert "server-01" in peers
        
        # Test server-01 peers
        peers = graph.get_peer_devices("server-01")
        assert len(peers) == 1
        assert "tor-01" in peers
        
        # Test nonexistent device
        peers = graph.get_peer_devices("nonexistent")
        assert len(peers) == 0

    def test_is_spof(self, temp_topology_file):
        """Test SPOF detection."""
        graph = NetworkTopologyGraph(temp_topology_file)
        
        # Edge devices with few peers should be SPOFs
        assert graph.is_spof("edge-01") is True
        
        # Spine devices with multiple peers should not be SPOFs
        assert graph.is_spof("spine-01") is False
        
        # ToR devices with multiple peers should not be SPOFs
        assert graph.is_spof("tor-01") is False
        
        # Server devices should not be SPOFs
        assert graph.is_spof("server-01") is False
        
        # Nonexistent device should not be SPOF
        assert graph.is_spof("nonexistent") is False

    def test_get_failure_domain(self, temp_topology_file):
        """Test failure domain classification."""
        graph = NetworkTopologyGraph(temp_topology_file)
        
        assert graph.get_failure_domain("spine-01") == FailureDomain.DATACENTER_DOMAIN
        assert graph.get_failure_domain("edge-01") == FailureDomain.EDGE_DOMAIN
        assert graph.get_failure_domain("tor-01") == FailureDomain.RACK_DOMAIN
        assert graph.get_failure_domain("server-01") == FailureDomain.LOCAL_DOMAIN
        assert graph.get_failure_domain("nonexistent") == FailureDomain.UNKNOWN_DOMAIN

    def test_get_devices_by_role(self, temp_topology_file):
        """Test device filtering by role."""
        graph = NetworkTopologyGraph(temp_topology_file)
        
        spine_devices = graph.get_devices_by_role(DeviceRole.SPINE)
        assert len(spine_devices) == 2
        assert "spine-01" in spine_devices
        assert "spine-02" in spine_devices
        
        tor_devices = graph.get_devices_by_role(DeviceRole.TOR)
        assert len(tor_devices) == 2
        assert "tor-01" in tor_devices
        assert "tor-02" in tor_devices
        
        server_devices = graph.get_devices_by_role(DeviceRole.SERVER)
        assert len(server_devices) == 2
        assert "server-01" in server_devices
        assert "server-02" in server_devices

    def test_get_topology_summary(self, temp_topology_file):
        """Test topology summary generation."""
        graph = NetworkTopologyGraph(temp_topology_file)
        
        summary = graph.get_topology_summary()
        
        assert summary["spine"] == 2
        assert summary["tor"] == 2
        assert summary["edge"] == 1
        assert summary["server"] == 2
        assert summary["unknown"] == 0

    def test_adjacency_list_construction(self, temp_topology_file):
        """Test adjacency list construction from BGP peers."""
        graph = NetworkTopologyGraph(temp_topology_file)
        
        # Verify bidirectional connections
        assert "tor-01" in graph.adjacency_list["spine-01"]
        assert "spine-01" in graph.adjacency_list["tor-01"]
        
        assert "tor-02" in graph.adjacency_list["spine-01"]
        assert "spine-01" in graph.adjacency_list["tor-02"]
        
        assert "edge-01" in graph.adjacency_list["spine-01"]
        assert "spine-01" in graph.adjacency_list["edge-01"]
        
        # Verify server connections
        assert "server-01" in graph.adjacency_list["tor-01"]
        assert "tor-01" in graph.adjacency_list["server-01"]

    def test_device_metadata_creation(self, temp_topology_file):
        """Test device metadata object creation."""
        graph = NetworkTopologyGraph(temp_topology_file)
        
        metadata = graph.get_device_metadata("spine-01")
        assert isinstance(metadata, DeviceMetadata)
        assert metadata.name == "spine-01"
        assert metadata.role == DeviceRole.SPINE
        assert metadata.asn == 65001
        assert metadata.router_id == "10.0.0.1"
        assert metadata.rack == "R01"
        assert metadata.datacenter == "DC1"
        assert len(metadata.interfaces) == 2

    def test_bgp_peer_creation(self, temp_topology_file):
        """Test BGP peer object creation."""
        graph = NetworkTopologyGraph(temp_topology_file)
        
        peer = graph.bgp_peers[0]
        assert isinstance(peer, BGPPeer)
        assert peer.local_device == "spine-01"
        assert peer.local_asn == 65001
        assert peer.local_ip == "10.1.1.1"
        assert peer.remote_device == "tor-01"
        assert peer.remote_asn == 65101
        assert peer.remote_ip == "10.1.1.2"
        assert peer.session_type == "eBGP"

    def test_unknown_role_handling(self, temp_topology_file):
        """Test handling of unknown device roles."""
        # Create a config with unknown role
        config = {
            "devices": {
                "unknown-device": {
                    "role": "unknown_role",
                    "asn": 99999,
                }
            },
            "bgp_peers": [],
            "prefixes": {},
        }
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            yaml.dump(config, f)
            
            graph = NetworkTopologyGraph(f.name)
            assert graph.get_device_role("unknown-device") == DeviceRole.UNKNOWN

    def test_empty_config_handling(self):
        """Test handling of empty configuration."""
        config = {"devices": {}, "bgp_peers": [], "prefixes": {}}
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            yaml.dump(config, f)
            
            graph = NetworkTopologyGraph(f.name)
            assert len(graph.devices) == 0
            assert len(graph.bgp_peers) == 0
            assert len(graph.prefixes) == 0
            assert len(graph.adjacency_list) == 0

    def test_max_depth_parameter(self, temp_topology_file):
        """Test max_depth parameter in downstream device discovery."""
        graph = NetworkTopologyGraph(temp_topology_file)
        
        # Test with max_depth=1 (only direct peers)
        downstream = graph.get_downstream_devices("spine-01", max_depth=1)
        assert len(downstream) == 3  # tor-01, tor-02, edge-01
        
        # Test with max_depth=2 (peers and their peers)
        downstream = graph.get_downstream_devices("spine-01", max_depth=2)
        assert len(downstream) == 5  # tor-01, tor-02, edge-01, server-01, server-02
        
        # Test with max_depth=0 (no downstream)
        downstream = graph.get_downstream_devices("spine-01", max_depth=0)
        assert len(downstream) == 0
