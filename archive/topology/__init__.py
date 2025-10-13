#!/usr/bin/env python3
"""
Topology Module

This module provides network topology representation and analysis capabilities
for the anomaly detection system.

Key Components:
    - NetworkTopologyGraph: Main topology graph class
    - DeviceRole: Network device role enumeration
    - FailureDomain: Network failure domain classification
    - DeviceMetadata: Device metadata representation
    - BGPPeer: BGP peering relationship representation
"""

from .network_graph import (
    BGPPeer,
    DeviceMetadata,
    DeviceRole,
    FailureDomain,
    NetworkTopologyGraph,
)

__all__ = [
    "NetworkTopologyGraph",
    "DeviceRole", 
    "FailureDomain",
    "DeviceMetadata",
    "BGPPeer",
]
