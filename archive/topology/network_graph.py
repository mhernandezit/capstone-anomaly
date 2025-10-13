#!/usr/bin/env python3
"""
Network Topology Graph Module

This module provides a comprehensive network topology representation and analysis
capabilities for the anomaly detection system. It loads topology data from YAML
configuration files and provides methods for graph traversal, impact analysis,
and failure localization.

Key Features:
    - YAML-based topology configuration loading
    - Graph traversal for downstream device discovery
    - Blast radius calculation using actual topology
    - Device role and metadata management
    - SPOF (Single Point of Failure) detection
    - BGP peering relationship analysis

Architecture:
    The topology graph operates as a foundational component that:
    - Loads topology data from YAML configuration files
    - Builds adjacency lists for efficient graph traversal
    - Provides device metadata and role information
    - Enables impact analysis through graph algorithms

Example:
    >>> graph = NetworkTopologyGraph("evaluation/topology.yml")
    >>> downstream = graph.get_downstream_devices("spine-01")
    >>> affected_count, services, has_redundancy = graph.calculate_blast_radius("tor-01")
    >>> role = graph.get_device_role("edge-01")
"""

import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import yaml

logger = logging.getLogger(__name__)


class DeviceRole(Enum):
    """Network device roles with criticality weighting."""
    
    EDGE = "edge"           # External connectivity (highest criticality)
    SPINE = "spine"         # Core switching (highest criticality)
    ROUTE_REFLECTOR = "rr"  # BGP route reflector (highest criticality)
    TOR = "tor"             # Top-of-Rack switch (high criticality)
    LEAF = "leaf"           # Leaf switch (medium criticality)
    ACCESS = "access"       # Access switch (low criticality)
    SERVER = "server"       # Endpoint server (lowest criticality)
    UNKNOWN = "unknown"     # Unknown role (minimal criticality)


class FailureDomain(Enum):
    """Network failure domains for blast radius classification."""
    
    EDGE_DOMAIN = "edge"           # External connectivity impact
    DATACENTER_DOMAIN = "datacenter"  # East-west traffic impact
    NETWORK_DOMAIN = "network"     # BGP convergence impact
    RACK_DOMAIN = "rack"          # Rack-level connectivity
    POD_DOMAIN = "pod"             # Pod-level services
    FLOOR_DOMAIN = "floor"         # Floor-level access
    LOCAL_DOMAIN = "local"         # Device-local impact
    UNKNOWN_DOMAIN = "unknown"     # Unknown scope


@dataclass
class DeviceMetadata:
    """Comprehensive device metadata from topology configuration."""
    
    name: str
    role: DeviceRole
    asn: Optional[int] = None
    router_id: Optional[str] = None
    rack: Optional[str] = None
    datacenter: Optional[str] = None
    interfaces: List[Dict] = None
    
    def __post_init__(self):
        if self.interfaces is None:
            self.interfaces = []


@dataclass
class BGPPeer:
    """BGP peering relationship representation."""
    
    local_device: str
    local_asn: int
    local_ip: str
    remote_device: str
    remote_asn: int
    remote_ip: str
    session_type: str = "eBGP"


class NetworkTopologyGraph:
    """
    Network topology graph for failure impact analysis.
    
    This class represents the network topology as a graph structure,
    enabling efficient traversal for blast radius calculation and
    failure impact assessment. It loads topology data from YAML
    configuration files and provides methods for graph traversal.
    
    Attributes:
        devices: Dictionary mapping device names to device metadata
        bgp_peers: List of BGP peering relationships
        prefixes: Dictionary mapping devices to advertised prefixes
        adjacency_list: Graph adjacency list for efficient traversal
        
    Example:
        >>> graph = NetworkTopologyGraph("evaluation/topology.yml")
        >>> downstream = graph.get_downstream_devices("spine-01")
        >>> affected = graph.calculate_blast_radius("tor-01")
    """
    
    def __init__(self, topology_config_path: str):
        """
        Initialize topology graph from configuration file.
        
        Args:
            topology_config_path: Path to topology YAML configuration
        """
        self.topology_path = Path(topology_config_path)
        self.devices: Dict[str, DeviceMetadata] = {}
        self.bgp_peers: List[BGPPeer] = []
        self.prefixes: Dict[str, List[str]] = {}
        self.adjacency_list: Dict[str, Set[str]] = {}
        
        self._load_topology_config()
        self._build_adjacency_list()
    
    def _load_topology_config(self):
        """Load topology configuration from YAML file."""
        if not self.topology_path.exists():
            logger.warning(f"Topology config not found: {self.topology_path}")
            return
        
        try:
            with open(self.topology_path) as f:
                config = yaml.safe_load(f)
                
                # Load devices
                devices_config = config.get("devices", {})
                for device_name, device_info in devices_config.items():
                    role_str = device_info.get("role", "unknown")
                    try:
                        role = DeviceRole(role_str)
                    except ValueError:
                        role = DeviceRole.UNKNOWN
                    
                    self.devices[device_name] = DeviceMetadata(
                        name=device_name,
                        role=role,
                        asn=device_info.get("asn"),
                        router_id=device_info.get("router_id"),
                        rack=device_info.get("rack"),
                        datacenter=device_info.get("datacenter"),
                        interfaces=device_info.get("interfaces", [])
                    )
                
                # Load BGP peers
                bgp_config = config.get("bgp_peers", [])
                for peer_info in bgp_config:
                    self.bgp_peers.append(BGPPeer(
                        local_device=peer_info["local_device"],
                        local_asn=peer_info["local_asn"],
                        local_ip=peer_info["local_ip"],
                        remote_device=peer_info["remote_device"],
                        remote_asn=peer_info["remote_asn"],
                        remote_ip=peer_info["remote_ip"],
                        session_type=peer_info.get("session_type", "eBGP")
                    ))
                
                # Load prefixes
                self.prefixes = config.get("prefixes", {})
                
                logger.info(f"Loaded topology with {len(self.devices)} devices and {len(self.bgp_peers)} BGP sessions")
        except Exception as e:
            logger.error(f"Failed to load topology config: {e}")
    
    def _build_adjacency_list(self):
        """Build adjacency list from BGP peering relationships."""
        for peer in self.bgp_peers:
            local_device = peer.local_device
            remote_device = peer.remote_device
            
            if local_device not in self.adjacency_list:
                self.adjacency_list[local_device] = set()
            if remote_device not in self.adjacency_list:
                self.adjacency_list[remote_device] = set()
                
            self.adjacency_list[local_device].add(remote_device)
            self.adjacency_list[remote_device].add(local_device)
    
    def get_device_role(self, device: str) -> DeviceRole:
        """
        Get the network role of a device.
        
        Args:
            device: Device identifier
            
        Returns:
            DeviceRole enum value
        """
        device_metadata = self.devices.get(device)
        if device_metadata:
            return device_metadata.role
        return DeviceRole.UNKNOWN
    
    def get_device_metadata(self, device: str) -> Optional[DeviceMetadata]:
        """
        Get comprehensive metadata for a device.
        
        Args:
            device: Device identifier
            
        Returns:
            DeviceMetadata object or None if not found
        """
        return self.devices.get(device)
    
    def get_downstream_devices(self, device: str, max_depth: int = 3) -> List[str]:
        """
        Get devices downstream from a given device using BFS traversal.
        
        This method performs breadth-first search to find all devices
        that would be affected by a failure at the given device.
        
        Args:
            device: Source device identifier
            max_depth: Maximum traversal depth
            
        Returns:
            List of downstream device identifiers
        """
        if device not in self.adjacency_list:
            return []
        
        visited = set()
        queue = [(device, 0)]
        downstream = []
        
        while queue:
            current_device, depth = queue.pop(0)
            
            if depth >= max_depth or current_device in visited:
                continue
                
            visited.add(current_device)
            
            if depth > 0:  # Don't include the source device
                downstream.append(current_device)
            
            # Add neighbors to queue
            for neighbor in self.adjacency_list.get(current_device, []):
                if neighbor not in visited:
                    queue.append((neighbor, depth + 1))
        
        return downstream
    
    def calculate_blast_radius(self, device: str) -> Tuple[int, List[str], bool]:
        """
        Calculate blast radius for a device failure.
        
        This method determines the impact of a device failure by analyzing
        the topology graph and device roles to estimate affected devices,
        services, and redundancy availability.
        
        Args:
            device: Device identifier
            
        Returns:
            Tuple of (affected_device_count, affected_services, has_redundancy)
        """
        downstream = self.get_downstream_devices(device)
        device_metadata = self.get_device_metadata(device)
        
        if not device_metadata:
            return 1, ["unknown"], False
        
        role = device_metadata.role
        
        # Count affected devices
        affected_count = len(downstream) + 1  # Include the failed device
        
        # Determine affected services based on role
        affected_services = []
        if role == DeviceRole.EDGE:
            affected_services = ["external_connectivity"]
        elif role == DeviceRole.SPINE:
            affected_services = ["east_west_traffic"]
        elif role == DeviceRole.ROUTE_REFLECTOR:
            affected_services = ["bgp_convergence"]
        elif role == DeviceRole.TOR:
            affected_services = ["rack_connectivity"]
        elif role == DeviceRole.LEAF:
            affected_services = ["server_connectivity"]
        elif role == DeviceRole.ACCESS:
            affected_services = ["user_connectivity"]
        elif role == DeviceRole.SERVER:
            affected_services = ["application"]
        else:
            affected_services = ["unknown"]
        
        # Check for redundancy (simplified - would need more sophisticated logic)
        has_redundancy = len(downstream) > 1 or role in [DeviceRole.LEAF, DeviceRole.ACCESS, DeviceRole.SERVER]
        
        return affected_count, affected_services, has_redundancy
    
    def get_peer_devices(self, device: str) -> List[str]:
        """
        Get devices that peer with the given device.
        
        Args:
            device: Device identifier
            
        Returns:
            List of peer device identifiers
        """
        return list(self.adjacency_list.get(device, []))
    
    def is_spof(self, device: str) -> bool:
        """
        Determine if a device represents a Single Point of Failure.
        
        This method analyzes the device's role and connectivity to determine
        if it represents a critical failure point in the network topology.
        
        Args:
            device: Device identifier
            
        Returns:
            True if device is a SPOF
        """
        device_metadata = self.get_device_metadata(device)
        if not device_metadata:
            return False
        
        role = device_metadata.role
        peers = self.get_peer_devices(device)
        
        # High-criticality devices with few peers are likely SPOFs
        if role in [DeviceRole.EDGE, DeviceRole.SPINE, DeviceRole.ROUTE_REFLECTOR]:
            return len(peers) <= 1  # Only 1 peer = SPOF
        
        return False
    
    def get_failure_domain(self, device: str) -> FailureDomain:
        """
        Get the failure domain for a device based on its role.
        
        Args:
            device: Device identifier
            
        Returns:
            FailureDomain enum value
        """
        role = self.get_device_role(device)
        
        failure_domain_map = {
            DeviceRole.EDGE: FailureDomain.EDGE_DOMAIN,
            DeviceRole.SPINE: FailureDomain.DATACENTER_DOMAIN,
            DeviceRole.ROUTE_REFLECTOR: FailureDomain.NETWORK_DOMAIN,
            DeviceRole.TOR: FailureDomain.RACK_DOMAIN,
            DeviceRole.LEAF: FailureDomain.POD_DOMAIN,
            DeviceRole.ACCESS: FailureDomain.FLOOR_DOMAIN,
            DeviceRole.SERVER: FailureDomain.LOCAL_DOMAIN,
            DeviceRole.UNKNOWN: FailureDomain.UNKNOWN_DOMAIN,
        }
        
        return failure_domain_map.get(role, FailureDomain.UNKNOWN_DOMAIN)
    
    def get_devices_by_role(self, role: DeviceRole) -> List[str]:
        """
        Get all devices with a specific role.
        
        Args:
            role: Device role to filter by
            
        Returns:
            List of device identifiers with the specified role
        """
        return [name for name, metadata in self.devices.items() if metadata.role == role]
    
    def get_topology_summary(self) -> Dict[str, int]:
        """
        Get a summary of the topology by device role counts.
        
        Returns:
            Dictionary mapping device roles to counts
        """
        summary = {}
        for role in DeviceRole:
            summary[role.value] = len(self.get_devices_by_role(role))
        return summary
