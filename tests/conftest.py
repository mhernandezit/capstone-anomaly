"""Pytest configuration and fixtures for the test suite."""

from pathlib import Path

import pytest

# Package is now properly installed, no need for path manipulation


@pytest.fixture
def sample_bgp_update():
    """Sample BGP update for testing."""
    return {
        "ts": 1234567890,
        "peer": "10.0.1.1",
        "type": "UPDATE",
        "announce": ["192.168.1.0/24"],
        "withdraw": None,
        "attrs": {"as_path": "65001 65002"},
    }


@pytest.fixture
def sample_bgp_anomaly():
    """Sample BGP update with anomaly characteristics."""
    return {
        "ts": 1234567900,
        "peer": "10.0.1.1",
        "type": "UPDATE",
        "announce": None,
        "withdraw": ["192.168.1.0/24", "192.168.2.0/24", "192.168.3.0/24"],
        "attrs": {"as_path": "65001"},
    }


@pytest.fixture
def sample_snmp_metrics():
    """Sample SNMP metrics for testing."""
    return {
        "timestamp": 1234567890,
        "device": "spine-01",
        "cpu_utilization": 45.2,
        "memory_utilization": 62.1,
        "temperature": 58.3,
        "interface_error_rate": 0.01,
        "bandwidth_utilization": 75.5,
        "packet_loss_rate": 0.001,
        "fan_status": 1,
        "power_status": 1,
    }


@pytest.fixture
def sample_snmp_anomaly():
    """Sample SNMP metrics with anomaly characteristics."""
    return {
        "timestamp": 1234567900,
        "device": "spine-01",
        "cpu_utilization": 98.5,
        "memory_utilization": 95.3,
        "temperature": 88.7,
        "interface_error_rate": 15.2,
        "bandwidth_utilization": 12.3,
        "packet_loss_rate": 25.8,
        "fan_status": 0,
        "power_status": 1,
    }


@pytest.fixture
def fixtures_dir():
    """Path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_topology():
    """Sample network topology for testing."""
    return {
        "devices": {
            "spine-01": {"role": "spine", "asn": 65001, "priority": "critical", "blast_radius": 15},
            "tor-01": {
                "role": "tor",
                "asn": 65002,
                "priority": "high",
                "blast_radius": 8,
                "uplinks": ["spine-01"],
            },
            "edge-01": {
                "role": "edge",
                "asn": 65100,
                "priority": "critical",
                "blast_radius": 20,
                "uplinks": ["spine-01"],
            },
        },
        "bgp_peers": [["spine-01", "tor-01"], ["spine-01", "edge-01"]],
    }


@pytest.fixture
def sample_roles_config():
    """Sample roles configuration for testing."""
    return {
        "roles": {
            "spine-01": "spine",
            "spine-02": "spine",
            "tor-01": "tor",
            "tor-02": "tor",
            "edge-01": "edge",
            "edge-02": "edge",
        }
    }


# Pytest configuration
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests for individual components")
    config.addinivalue_line("markers", "integration: Integration tests for pipelines")
    config.addinivalue_line("markers", "smoke: Quick smoke tests")
    config.addinivalue_line("markers", "slow: Tests that take longer to run")
