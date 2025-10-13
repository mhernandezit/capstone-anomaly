#!/usr/bin/env python3
"""
Integration tests for topology triage system with ML detection pipeline.

Tests the integration between ML detectors, multimodal correlator,
and topology triage system to ensure end-to-end functionality.
"""

import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock

from anomaly_detection.triage.topology_triage import TopologyTriageSystem
from anomaly_detection.topology import DeviceRole, FailureDomain


class TestMLPipelineIntegration:
    """Integration tests for ML pipeline with topology triage."""

    @pytest.fixture
    def sample_topology_config(self):
        """Sample topology configuration for integration testing."""
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
    def sample_roles_config(self):
        """Sample roles configuration for integration testing."""
        return {
            "roles": {
                "spine-01": "spine",
                "spine-02": "spine",
                "tor-01": "tor",
                "tor-02": "tor",
                "edge-01": "edge",
                "server-01": "server",
                "server-02": "server",
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
        """Create a triage system instance for integration testing."""
        return TopologyTriageSystem(temp_roles_file, temp_topology_file)

    def test_bgp_pipeline_integration(self, triage_system):
        """Test integration with BGP Matrix Profile detector."""
        # Simulate Matrix Profile detector output
        bgp_detection = {
            "timestamp": 1234567890,
            "detector": "matrix_profile",
            "anomaly_type": "bgp_flapping",
            "confidence": 0.85,
            "anomaly_score": 0.92,
            "detected_location": {
                "device": "spine-01",
                "interface": "eth0",
                "bgp_peer": "tor-01",
                "confidence": 0.75,
            },
            "features": {
                "announcement_rate": 150.0,
                "withdrawal_rate": 25.0,
                "as_path_changes": 8,
                "prefix_churn": 0.15,
            },
            "raw_data": {
                "bgp_updates": [
                    {"prefix": "192.168.1.0/24", "action": "withdraw"},
                    {"prefix": "192.168.2.0/24", "action": "withdraw"},
                ]
            },
        }
        
        result = triage_system.analyze(bgp_detection, bgp_detection["detected_location"])
        
        # Verify BGP-specific analysis
        assert result.location.device == "spine-01"
        assert result.location.interface == "eth0"
        assert result.location.bgp_peer == "tor-01"
        assert result.location.topology_role == DeviceRole.SPINE
        
        # Verify high-priority classification for spine failure
        assert result.criticality.priority.value in ["P1", "P2"]
        assert result.blast_radius.failure_domain == FailureDomain.DATACENTER_DOMAIN
        assert "east_west_traffic" in result.blast_radius.affected_services

    def test_snmp_pipeline_integration(self, triage_system):
        """Test integration with SNMP Isolation Forest detector."""
        # Simulate Isolation Forest detector output
        snmp_detection = {
            "timestamp": 1234567890,
            "detector": "isolation_forest",
            "anomaly_type": "hardware_degradation",
            "confidence": 0.78,
            "anomaly_score": 0.82,
            "detected_location": {
                "device": "tor-01",
                "interface": "eth0",
                "confidence": 0.70,
            },
            "features": {
                "cpu_utilization": 95.2,
                "memory_utilization": 88.5,
                "temperature": 85.3,
                "interface_error_rate": 12.5,
                "fan_status": 0,  # Fan failure
            },
            "raw_data": {
                "snmp_metrics": {
                    "cpu": 95.2,
                    "memory": 88.5,
                    "temp": 85.3,
                    "errors": 1250,
                }
            },
        }
        
        result = triage_system.analyze(snmp_detection, snmp_detection["detected_location"])
        
        # Verify SNMP-specific analysis
        assert result.location.device == "tor-01"
        assert result.location.interface == "eth0"
        assert result.location.topology_role == DeviceRole.TOR
        
        # Verify medium-priority classification for ToR failure
        assert result.criticality.priority.value in ["P2", "P3"]
        assert result.blast_radius.failure_domain == FailureDomain.RACK_DOMAIN
        assert "rack_connectivity" in result.blast_radius.affected_services

    def test_multimodal_correlation_integration(self, triage_system):
        """Test integration with multimodal correlator."""
        # Simulate correlator output
        correlator_data = {
            "correlation_id": "corr_12345",
            "timestamp": 1234567890,
            "correlation_strength": 0.92,
            "temporal_proximity": 0.95,
            "spatial_correlation": 0.88,
            "is_multi_modal": True,
            "modalities": ["bgp", "snmp"],
            "affected_devices": ["tor-01", "server-01"],
            "affected_services": ["rack_connectivity", "application"],
            "correlated_events": [
                {
                    "source": "bgp",
                    "device": "tor-01",
                    "confidence": 0.85,
                },
                {
                    "source": "snmp",
                    "device": "tor-01",
                    "confidence": 0.78,
                },
            ],
        }
        
        # Simulate combined anomaly data
        anomaly_data = {
            "alert_type": "multimodal_correlated",
            "confidence": 0.90,
            "sources": ["bgp", "snmp"],
            "correlation_data": correlator_data,
        }
        
        detected_location = {
            "device": "tor-01",
            "interface": "eth0",
            "confidence": 0.80,
        }
        
        result = triage_system.analyze(anomaly_data, detected_location, correlator_data)
        
        # Verify multimodal analysis
        assert result.location.device == "tor-01"
        assert result.blast_radius.affected_devices >= 2  # Should include correlator data
        assert "rack_connectivity" in result.blast_radius.affected_services
        assert "application" in result.blast_radius.affected_services
        
        # Verify enhanced criticality due to multimodal correlation
        assert result.criticality.score >= 5.0  # Should be P2 or higher

    def test_end_to_end_pipeline_simulation(self, triage_system):
        """Test complete end-to-end pipeline simulation."""
        # Simulate complete pipeline flow
        
        # Step 1: BGP Matrix Profile Detection
        bgp_result = {
            "timestamp": 1234567890,
            "detector": "matrix_profile",
            "anomaly_type": "bgp_flapping",
            "confidence": 0.88,
            "detected_location": {
                "device": "spine-01",
                "interface": "eth0",
                "bgp_peer": "tor-01",
                "confidence": 0.82,
            },
        }
        
        # Step 2: SNMP Isolation Forest Detection
        snmp_result = {
            "timestamp": 1234567895,  # 5 seconds later
            "detector": "isolation_forest",
            "anomaly_type": "hardware_degradation",
            "confidence": 0.75,
            "detected_location": {
                "device": "spine-01",
                "interface": "eth0",
                "confidence": 0.70,
            },
        }
        
        # Step 3: Multimodal Correlation
        correlator_data = {
            "correlation_strength": 0.90,
            "temporal_proximity": 0.95,
            "spatial_correlation": 0.95,
            "affected_devices": ["spine-01", "tor-01", "tor-02"],
            "affected_services": ["east_west_traffic", "rack_connectivity"],
        }
        
        # Step 4: Topology Triage Analysis
        anomaly_data = {
            "alert_type": "multimodal_correlated",
            "confidence": 0.90,
            "sources": ["bgp", "snmp"],
        }
        
        detected_location = {
            "device": "spine-01",
            "interface": "eth0",
            "bgp_peer": "tor-01",
            "confidence": 0.85,
        }
        
        result = triage_system.analyze(anomaly_data, detected_location, correlator_data)
        
        # Verify end-to-end results
        assert result.location.device == "spine-01"
        assert result.location.interface == "eth0"
        assert result.location.bgp_peer == "tor-01"
        assert result.location.topology_role == DeviceRole.SPINE
        
        # Verify high-priority classification
        assert result.criticality.priority.value in ["P1", "P2"]
        assert result.criticality.sla_breach_likely is True
        
        # Verify SPOF detection
        assert result.blast_radius.spof is True
        assert result.blast_radius.failure_domain == FailureDomain.DATACENTER_DOMAIN
        
        # Verify impact assessment
        assert result.blast_radius.affected_devices >= 3
        assert "east_west_traffic" in result.blast_radius.affected_services
        assert "rack_connectivity" in result.blast_radius.affected_services
        
        # Verify ranked predictions include related devices
        prediction_devices = [p.device for p in result.ranked_predictions]
        assert "tor-01" in prediction_devices or "tor-02" in prediction_devices

    def test_alert_manager_integration_format(self, triage_system):
        """Test integration with alert manager data format."""
        # Simulate alert manager expected format
        anomaly_data = {
            "alert_id": "alert_12345",
            "timestamp": 1234567890,
            "alert_type": "bgp_flapping",
            "confidence": 0.85,
            "severity": "high",
            "sources": ["bgp"],
            "detected_location": {
                "device": "edge-01",
                "interface": "eth0",
                "confidence": 0.80,
            },
        }
        
        result = triage_system.analyze(anomaly_data, anomaly_data["detected_location"])
        
        # Verify alert manager compatible output
        assert result.location.device == "edge-01"
        assert result.location.interface == "eth0"
        assert result.location.topology_role == DeviceRole.EDGE
        
        # Verify SPOF detection for edge device
        assert result.blast_radius.spof is True
        assert result.blast_radius.failure_domain == FailureDomain.EDGE_DOMAIN
        
        # Verify critical priority for edge failure
        assert result.criticality.priority.value in ["P1", "P2"]
        assert result.severity.value in ["critical", "error"]

    def test_dashboard_integration_format(self, triage_system):
        """Test integration with dashboard data format."""
        # Simulate dashboard expected format
        anomaly_data = {
            "timestamp": 1234567890,
            "anomaly_type": "interface_failure",
            "confidence": 0.75,
            "detected_location": {
                "device": "tor-01",
                "interface": "eth2",
                "confidence": 0.70,
            },
        }
        
        result = triage_system.analyze(anomaly_data, anomaly_data["detected_location"])
        
        # Verify dashboard compatible output
        assert result.location.device == "tor-01"
        assert result.location.interface == "eth2"
        assert result.location.topology_role == DeviceRole.TOR
        
        # Verify impact visualization data
        assert result.blast_radius.affected_devices >= 1
        assert result.blast_radius.downstream_devices is not None
        assert result.blast_radius.failure_domain == FailureDomain.RACK_DOMAIN
        
        # Verify severity for dashboard display
        assert result.severity.value in ["critical", "error", "warning", "info"]
        assert result.criticality.score >= 0.0
        assert result.criticality.score <= 10.0

    def test_performance_under_load(self, triage_system):
        """Test performance under simulated load."""
        # Simulate multiple concurrent analyses
        scenarios = [
            {"device": "spine-01", "type": "bgp_flapping", "priority": "P1"},
            {"device": "spine-02", "type": "bgp_flapping", "priority": "P1"},
            {"device": "tor-01", "type": "interface_failure", "priority": "P2"},
            {"device": "tor-02", "type": "interface_failure", "priority": "P2"},
            {"device": "server-01", "type": "hardware_degradation", "priority": "P3"},
            {"device": "server-02", "type": "hardware_degradation", "priority": "P3"},
        ]
        
        results = []
        for scenario in scenarios:
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
        
        # Verify all analyses completed successfully
        assert len(results) == 6
        assert all(r.location.device == scenarios[i]["device"] for i, r in enumerate(results))
        
        # Verify priority classifications
        p1_results = [r for r in results if r.criticality.priority.value == "P1"]
        p2_results = [r for r in results if r.criticality.priority.value == "P2"]
        p3_results = [r for r in results if r.criticality.priority.value == "P3"]
        
        assert len(p1_results) == 2  # Both spine devices
        assert len(p2_results) == 2  # Both ToR devices
        assert len(p3_results) == 2  # Both server devices

    def test_error_handling_and_recovery(self, triage_system):
        """Test error handling and recovery scenarios."""
        # Test with malformed data
        malformed_data = {
            "alert_type": None,
            "confidence": "invalid",
            "detected_location": {},
        }
        
        result = triage_system.analyze(malformed_data)
        
        # Should handle gracefully
        assert result.location.device == "unknown"
        assert result.location.topology_role == DeviceRole.UNKNOWN
        assert result.criticality.priority.value == "P3"
        
        # Test with missing topology data
        anomaly_data = {
            "alert_type": "bgp_flapping",
            "confidence": 0.85,
        }
        
        detected_location = {
            "device": "nonexistent-device",
            "confidence": 0.75,
        }
        
        result = triage_system.analyze(anomaly_data, detected_location)
        
        # Should handle unknown devices gracefully
        assert result.location.device == "nonexistent-device"
        assert result.location.topology_role == DeviceRole.UNKNOWN
        assert result.blast_radius.failure_domain == FailureDomain.UNKNOWN_DOMAIN
