#!/usr/bin/env python3
"""
Unit tests for TopologyTriageSystem class.

Tests the triage system functionality including failure analysis,
blast radius calculation, criticality assessment, and SPOF detection.
"""

import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock

from anomaly_detection.triage.topology_triage import (
    TopologyTriageSystem,
    TopologyLocation,
    BlastRadius,
    CriticalityAssessment,
    TriageResult,
    Priority,
    Severity,
)
from anomaly_detection.topology import DeviceRole, FailureDomain


class TestTopologyTriageSystem:
    """Test cases for TopologyTriageSystem class."""

    @pytest.fixture
    def sample_topology_config(self):
        """Sample topology configuration for testing."""
        return {
            "devices": {
                "spine-01": {
                    "role": "spine",
                    "asn": 65001,
                    "router_id": "10.0.0.1",
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
                    "local_device": "tor-01",
                    "local_asn": 65101,
                    "local_ip": "10.2.1.1",
                    "remote_device": "server-01",
                    "remote_asn": 65301,
                    "remote_ip": "10.2.1.2",
                    "session_type": "eBGP",
                },
            ],
            "prefixes": {
                "spine-01": ["10.0.0.0/24"],
                "tor-01": ["10.10.1.0/24"],
                "server-01": ["10.10.1.1/32"],
            },
        }

    @pytest.fixture
    def sample_roles_config(self):
        """Sample roles configuration for testing."""
        return {
            "roles": {
                "spine-01": "spine",
                "spine-02": "spine",
                "tor-01": "tor",
                "tor-02": "tor",
                "edge-01": "edge",
                "server-01": "server",
            }
        }

    @pytest.fixture
    def temp_topology_file(self, sample_topology_config):
        """Create a temporary topology file for testing."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            yaml.dump(sample_topology_config, f)
            return f.name

    @pytest.fixture
    def temp_roles_file(self, sample_roles_config):
        """Create a temporary roles file for testing."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            yaml.dump(sample_roles_config, f)
            return f.name

    @pytest.fixture
    def triage_system(self, temp_roles_file, temp_topology_file):
        """Create a triage system instance for testing."""
        return TopologyTriageSystem(temp_roles_file, temp_topology_file)

    def test_init_with_valid_configs(self, temp_roles_file, temp_topology_file):
        """Test initialization with valid configuration files."""
        triage = TopologyTriageSystem(temp_roles_file, temp_topology_file)
        
        assert triage.roles_config_path == Path(temp_roles_file)
        assert triage.topology_config_path == Path(temp_topology_file)
        assert len(triage.roles) == 6
        assert triage.topology_graph is not None
        assert len(triage.topology_graph.devices) == 6

    def test_init_with_missing_files(self):
        """Test initialization with missing configuration files."""
        with patch("anomaly_detection.triage.topology_triage.logger") as mock_logger:
            triage = TopologyTriageSystem("nonexistent_roles.yml", "nonexistent_topology.yml")
            
            assert len(triage.roles) == 0
            assert triage.topology_graph is not None
            mock_logger.warning.assert_called()

    def test_role_priorities(self, triage_system):
        """Test role priority mapping."""
        assert triage_system.role_priorities[DeviceRole.EDGE] == 4.0
        assert triage_system.role_priorities[DeviceRole.SPINE] == 4.0
        assert triage_system.role_priorities[DeviceRole.TOR] == 3.5
        assert triage_system.role_priorities[DeviceRole.SERVER] == 1.0
        assert triage_system.role_priorities[DeviceRole.UNKNOWN] == 0.5

    def test_analyze_basic_anomaly(self, triage_system):
        """Test basic anomaly analysis."""
        anomaly_data = {
            "alert_type": "bgp_flapping",
            "confidence": 0.85,
            "sources": ["bgp"],
        }
        
        detected_location = {
            "device": "spine-01",
            "interface": "eth0",
            "confidence": 0.75,
        }
        
        result = triage_system.analyze(anomaly_data, detected_location)
        
        assert isinstance(result, TriageResult)
        assert result.location.device == "spine-01"
        assert result.location.interface == "eth0"
        assert result.location.topology_role == DeviceRole.SPINE
        assert result.location.confidence == 0.75
        assert len(result.ranked_predictions) >= 1
        assert isinstance(result.blast_radius, BlastRadius)
        assert isinstance(result.criticality, CriticalityAssessment)
        assert isinstance(result.severity, Severity)

    def test_analyze_with_correlator_data(self, triage_system):
        """Test analysis with multimodal correlator data."""
        anomaly_data = {
            "alert_type": "multimodal_correlated",
            "confidence": 0.90,
            "sources": ["bgp", "snmp"],
        }
        
        detected_location = {
            "device": "tor-01",
            "interface": "eth0",
            "confidence": 0.80,
        }
        
        correlator_data = {
            "affected_devices": ["server-01", "server-02"],
            "affected_services": ["rack_connectivity", "application"],
        }
        
        result = triage_system.analyze(anomaly_data, detected_location, correlator_data)
        
        assert result.location.device == "tor-01"
        assert result.blast_radius.affected_devices >= 2  # Should include correlator data
        assert "rack_connectivity" in result.blast_radius.affected_services

    def test_determine_location(self, triage_system):
        """Test location determination."""
        detected_location = {
            "device": "spine-01",
            "interface": "eth0",
            "bgp_peer": "tor-01",
            "confidence": 0.85,
        }
        
        location = triage_system._determine_location(detected_location)
        
        assert isinstance(location, TopologyLocation)
        assert location.device == "spine-01"
        assert location.interface == "eth0"
        assert location.bgp_peer == "tor-01"
        assert location.topology_role == DeviceRole.SPINE
        assert location.confidence == 0.85

    def test_determine_location_unknown_device(self, triage_system):
        """Test location determination with unknown device."""
        detected_location = {
            "device": "unknown-device",
            "confidence": 0.50,
        }
        
        location = triage_system._determine_location(detected_location)
        
        assert location.device == "unknown-device"
        assert location.topology_role == DeviceRole.UNKNOWN
        assert location.confidence == 0.50

    def test_rank_predictions(self, triage_system):
        """Test prediction ranking."""
        anomaly_data = {"alert_type": "bgp_flapping"}
        primary = TopologyLocation(
            device="spine-01",
            topology_role=DeviceRole.SPINE,
            confidence=0.80,
        )
        
        predictions = triage_system._rank_predictions(anomaly_data, primary)
        
        assert len(predictions) >= 1
        assert predictions[0] == primary
        
        # Should include peer devices
        peer_devices = [p.device for p in predictions[1:]]
        assert "tor-01" in peer_devices or "tor-02" in peer_devices

    def test_calculate_blast_radius(self, triage_system):
        """Test blast radius calculation."""
        location = TopologyLocation(
            device="spine-01",
            topology_role=DeviceRole.SPINE,
            confidence=0.80,
        )
        
        anomaly_data = {"alert_type": "bgp_flapping"}
        correlator_data = {
            "affected_devices": ["tor-01", "tor-02"],
            "affected_services": ["east_west_traffic"],
        }
        
        blast_radius = triage_system._calculate_blast_radius(location, anomaly_data, correlator_data)
        
        assert isinstance(blast_radius, BlastRadius)
        assert blast_radius.affected_devices >= 3  # spine + downstream
        assert "east_west_traffic" in blast_radius.affected_services
        assert blast_radius.failure_domain == FailureDomain.DATACENTER_DOMAIN
        assert blast_radius.impact_score > 0

    def test_calculate_blast_radius_spof(self, triage_system):
        """Test blast radius calculation for SPOF."""
        location = TopologyLocation(
            device="edge-01",
            topology_role=DeviceRole.EDGE,
            confidence=0.90,
        )
        
        anomaly_data = {"alert_type": "link_failure"}
        
        blast_radius = triage_system._calculate_blast_radius(location, anomaly_data)
        
        assert blast_radius.spof is True
        assert blast_radius.failure_domain == FailureDomain.EDGE_DOMAIN
        assert "external_connectivity" in blast_radius.affected_services

    def test_assess_criticality_high_priority(self, triage_system):
        """Test criticality assessment for high-priority failure."""
        location = TopologyLocation(
            device="spine-01",
            topology_role=DeviceRole.SPINE,
            confidence=0.90,
        )
        
        blast_radius = BlastRadius(
            affected_devices=15,
            affected_services=["east_west_traffic"],
            downstream_devices=["tor-01", "tor-02"],
            redundancy_available=False,
            spof=True,
            failure_domain=FailureDomain.DATACENTER_DOMAIN,
            impact_score=8.5,
        )
        
        anomaly_data = {"alert_type": "bgp_flapping"}
        
        criticality = triage_system._assess_criticality(location, blast_radius, anomaly_data)
        
        assert isinstance(criticality, CriticalityAssessment)
        assert criticality.score >= 8.0
        assert criticality.priority == Priority.P1
        assert criticality.sla_breach_likely is True
        assert criticality.time_to_breach_min == 15
        assert "topology_role" in criticality.factors
        assert "blast_radius" in criticality.factors

    def test_assess_criticality_medium_priority(self, triage_system):
        """Test criticality assessment for medium-priority failure."""
        location = TopologyLocation(
            device="tor-01",
            topology_role=DeviceRole.TOR,
            confidence=0.70,
        )
        
        blast_radius = BlastRadius(
            affected_devices=8,
            affected_services=["rack_connectivity"],
            downstream_devices=["server-01"],
            redundancy_available=True,
            spof=False,
            failure_domain=FailureDomain.RACK_DOMAIN,
            impact_score=5.5,
        )
        
        anomaly_data = {"alert_type": "interface_failure"}
        
        criticality = triage_system._assess_criticality(location, blast_radius, anomaly_data)
        
        assert criticality.score >= 5.0
        assert criticality.priority == Priority.P2
        assert criticality.sla_breach_likely is True
        assert criticality.time_to_breach_min == 60

    def test_assess_criticality_low_priority(self, triage_system):
        """Test criticality assessment for low-priority failure."""
        location = TopologyLocation(
            device="server-01",
            topology_role=DeviceRole.SERVER,
            confidence=0.60,
        )
        
        blast_radius = BlastRadius(
            affected_devices=1,
            affected_services=["application"],
            downstream_devices=[],
            redundancy_available=True,
            spof=False,
            failure_domain=FailureDomain.LOCAL_DOMAIN,
            impact_score=2.0,
        )
        
        anomaly_data = {"alert_type": "hardware_degradation"}
        
        criticality = triage_system._assess_criticality(location, blast_radius, anomaly_data)
        
        assert criticality.score < 5.0
        assert criticality.priority == Priority.P3
        assert criticality.sla_breach_likely is False
        assert criticality.time_to_breach_min is None

    def test_determine_severity(self, triage_system):
        """Test severity determination."""
        assert triage_system._determine_severity(9.0) == Severity.CRITICAL
        assert triage_system._determine_severity(7.0) == Severity.CRITICAL
        assert triage_system._determine_severity(6.0) == Severity.ERROR
        assert triage_system._determine_severity(4.0) == Severity.ERROR
        assert triage_system._determine_severity(3.5) == Severity.WARNING
        assert triage_system._determine_severity(2.0) == Severity.WARNING
        assert triage_system._determine_severity(1.0) == Severity.INFO

    def test_criticality_scoring_factors(self, triage_system):
        """Test criticality scoring factor breakdown."""
        location = TopologyLocation(
            device="spine-01",
            topology_role=DeviceRole.SPINE,
            confidence=0.85,
        )
        
        blast_radius = BlastRadius(
            affected_devices=20,
            affected_services=["east_west_traffic"],
            downstream_devices=["tor-01", "tor-02", "edge-01"],
            redundancy_available=False,
            spof=True,
            failure_domain=FailureDomain.DATACENTER_DOMAIN,
            impact_score=9.0,
        )
        
        anomaly_data = {"alert_type": "bgp_flapping"}
        
        criticality = triage_system._assess_criticality(location, blast_radius, anomaly_data)
        
        # Check scoring factors
        assert "topology_role" in criticality.factors
        assert "blast_radius" in criticality.factors
        assert "redundancy" in criticality.factors
        assert "service_impact" in criticality.factors
        
        # Verify factor descriptions
        assert "spine" in criticality.factors["topology_role"]
        assert "20 devices" in criticality.factors["blast_radius"]
        assert "SPOF" in criticality.factors["redundancy"]
        assert "Connectivity affected" in criticality.factors["service_impact"]

    def test_score_capping(self, triage_system):
        """Test that criticality scores are capped at 10.0."""
        location = TopologyLocation(
            device="spine-01",
            topology_role=DeviceRole.SPINE,
            confidence=0.95,
        )
        
        blast_radius = BlastRadius(
            affected_devices=50,  # Very high impact
            affected_services=["east_west_traffic", "external_connectivity"],
            downstream_devices=["tor-01", "tor-02", "edge-01"],
            redundancy_available=False,
            spof=True,
            failure_domain=FailureDomain.DATACENTER_DOMAIN,
            impact_score=15.0,  # Very high impact score
        )
        
        anomaly_data = {"alert_type": "critical_failure"}
        
        criticality = triage_system._assess_criticality(location, blast_radius, anomaly_data)
        
        assert criticality.score <= 10.0

    def test_unknown_device_handling(self, triage_system):
        """Test handling of unknown devices."""
        anomaly_data = {
            "alert_type": "unknown_failure",
            "confidence": 0.50,
        }
        
        detected_location = {
            "device": "unknown-device",
            "confidence": 0.30,
        }
        
        result = triage_system.analyze(anomaly_data, detected_location)
        
        assert result.location.device == "unknown-device"
        assert result.location.topology_role == DeviceRole.UNKNOWN
        assert result.blast_radius.failure_domain == FailureDomain.UNKNOWN_DOMAIN
        assert result.criticality.priority == Priority.P3  # Low priority for unknown

    def test_empty_anomaly_data(self, triage_system):
        """Test handling of empty anomaly data."""
        result = triage_system.analyze({})
        
        assert result.location.device == "unknown"
        assert result.location.topology_role == DeviceRole.UNKNOWN
        assert result.criticality.priority == Priority.P3

    def test_singleton_functionality(self, temp_roles_file, temp_topology_file):
        """Test singleton triage system functionality."""
        from anomaly_detection.triage.topology_triage import get_triage_system
        
        # Get first instance
        triage1 = get_triage_system(temp_roles_file, temp_topology_file)
        
        # Get second instance (should be same object)
        triage2 = get_triage_system(temp_roles_file, temp_topology_file)
        
        assert triage1 is triage2

    def test_integration_with_ml_pipeline(self, triage_system):
        """Test integration with ML pipeline data structures."""
        # Simulate ML pipeline output
        ml_detection = {
            "timestamp": 1234567890,
            "anomaly_type": "bgp_flapping",
            "confidence": 0.85,
            "detected_location": {
                "device": "spine-01",
                "interface": "eth0",
                "confidence": 0.75,
            },
            "features": {
                "announcement_rate": 150.0,
                "withdrawal_rate": 25.0,
                "as_path_changes": 8,
            },
        }
        
        # Simulate correlator data
        correlator_data = {
            "correlation_strength": 0.90,
            "affected_devices": ["tor-01", "tor-02"],
            "affected_services": ["east_west_traffic"],
            "temporal_proximity": 0.95,
        }
        
        result = triage_system.analyze(
            ml_detection,
            ml_detection["detected_location"],
            correlator_data
        )
        
        assert result.location.device == "spine-01"
        assert result.location.interface == "eth0"
        assert result.blast_radius.affected_devices >= 3
        assert result.criticality.priority in [Priority.P1, Priority.P2]
        assert result.severity in [Severity.CRITICAL, Severity.ERROR]

    def test_performance_with_large_topology(self, triage_system):
        """Test performance with larger topology scenarios."""
        # Test multiple analyses in sequence
        anomaly_scenarios = [
            {"device": "spine-01", "type": "bgp_flapping"},
            {"device": "tor-01", "type": "interface_failure"},
            {"device": "server-01", "type": "hardware_degradation"},
        ]
        
        results = []
        for scenario in anomaly_scenarios:
            anomaly_data = {
                "alert_type": scenario["type"],
                "confidence": 0.80,
            }
            
            detected_location = {
                "device": scenario["device"],
                "confidence": 0.75,
            }
            
            result = triage_system.analyze(anomaly_data, detected_location)
            results.append(result)
        
        assert len(results) == 3
        assert all(isinstance(r, TriageResult) for r in results)
        assert results[0].location.device == "spine-01"
        assert results[1].location.device == "tor-01"
        assert results[2].location.device == "server-01"
