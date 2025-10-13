"""
Simplified Topology System

This module provides minimal topology support for the triage system,
replacing the complex NetworkTopologyGraph with simple role-based mappings.
"""

from enum import Enum
from typing import Dict, List, Optional


class DeviceRole(Enum):
    """Device roles in the network topology."""
    SPINE = "spine"
    TOR = "tor"  # Top-of-Rack
    EDGE = "edge"
    SERVER = "server"
    LEAF = "leaf"
    ROUTE_REFLECTOR = "route_reflector"
    ACCESS = "access"
    UNKNOWN = "unknown"


class FailureDomain(Enum):
    """Failure domain classifications."""
    RACK = "rack"
    POD = "pod"
    DATACENTER = "datacenter"
    REGION = "region"


class DeviceMetadata:
    """Simple device metadata."""
    def __init__(self, name: str, role: DeviceRole, ip: str = ""):
        self.name = name
        self.role = role
        self.ip = ip


class BGPPeer:
    """Simple BGP peer representation."""
    def __init__(self, name: str, ip: str, asn: int = 0):
        self.name = name
        self.ip = ip
        self.asn = asn


class NetworkTopologyGraph:
    """
    Simplified topology graph that provides basic role-based functionality
    without the complexity of the archived version.
    """
    
    def __init__(self, topology_config_path: str = None):
        self.devices: Dict[str, DeviceMetadata] = {}
        self.peers: Dict[str, BGPPeer] = {}
        self.connections: List[tuple] = []
        
        if topology_config_path:
            self._load_from_config(topology_config_path)
    
    def _load_from_config(self, config_path: str):
        """Load topology from YAML configuration file."""
        import yaml
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Load devices
            for device_name, device_info in config.get('devices', {}).items():
                role_str = device_info.get('role', 'unknown')
                role = DeviceRole(role_str) if role_str in [r.value for r in DeviceRole] else DeviceRole.UNKNOWN
                ip = device_info.get('ip', '')
                self.add_device(device_name, role, ip)
            
            # Load BGP peers
            for peer_name, peer_info in config.get('bgp_peers', {}).items():
                ip = peer_info.get('ip', '')
                asn = peer_info.get('asn', 0)
                self.add_peer(peer_name, ip, asn)
                
        except Exception as e:
            print(f"[WARNING] Could not load topology config: {e}")
            # Continue with empty topology
    
    def add_device(self, name: str, role: DeviceRole, ip: str = ""):
        """Add a device to the topology."""
        self.devices[name] = DeviceMetadata(name, role, ip)
    
    def add_peer(self, name: str, ip: str, asn: int = 0):
        """Add a BGP peer to the topology."""
        self.peers[name] = BGPPeer(name, ip, asn)
    
    def get_device_role(self, device_name: str) -> Optional[DeviceRole]:
        """Get the role of a device."""
        device = self.devices.get(device_name)
        return device.role if device else None
    
    def get_downstream_devices(self, device_name: str) -> List[str]:
        """Get devices that depend on this device (simplified)."""
        device = self.devices.get(device_name)
        if not device:
            return []
        
        # Simple role-based dependency mapping
        if device.role == DeviceRole.SPINE:
            # Spines affect all ToRs and servers
            return [name for name, dev in self.devices.items() 
                   if dev.role in [DeviceRole.TOR, DeviceRole.SERVER]]
        elif device.role == DeviceRole.TOR:
            # ToRs affect servers in their rack
            return [name for name, dev in self.devices.items() 
                   if dev.role == DeviceRole.SERVER]
        else:
            # Servers/leafs have minimal impact
            return []
    
    def get_blast_radius(self, device_name: str) -> int:
        """Calculate blast radius (number of affected devices)."""
        return len(self.get_downstream_devices(device_name))
    
    def is_spof(self, device_name: str) -> bool:
        """Check if device is a Single Point of Failure (simplified)."""
        device = self.devices.get(device_name)
        if not device:
            return False
        
        # Simple SPOF logic: spines and edges are SPOFs
        return device.role in [DeviceRole.SPINE, DeviceRole.EDGE]
    
    def get_failure_domain(self, device_name: str) -> FailureDomain:
        """Get the failure domain for a device (simplified)."""
        device = self.devices.get(device_name)
        if not device:
            return FailureDomain.RACK
        
        # Simple role-based failure domain mapping
        if device.role in [DeviceRole.SPINE, DeviceRole.EDGE]:
            return FailureDomain.DATACENTER
        elif device.role == DeviceRole.TOR:
            return FailureDomain.RACK
        else:
            return FailureDomain.RACK
    
    def calculate_blast_radius(self, device_name: str) -> tuple:
        """Calculate blast radius and return (affected_count, affected_services, has_redundancy)."""
        affected_devices = self.get_downstream_devices(device_name)
        affected_count = len(affected_devices)
        affected_services = affected_devices  # Simplified - devices are services
        has_redundancy = affected_count < len(self.devices)  # Simplified redundancy check
        return affected_count, affected_services, has_redundancy
    
    def get_devices_by_role(self, role: DeviceRole) -> List[str]:
        """Get all devices with a specific role."""
        return [name for name, device in self.devices.items() if device.role == role]
    
    def get_peer_devices(self, device_name: str) -> List[str]:
        """Get BGP peer devices for a given device (simplified)."""
        # For simplicity, return empty list - peer relationships not critical for basic functionality
        return []
    
    def is_critical_device(self, device_name: str) -> bool:
        """Check if device is critical based on role."""
        device = self.devices.get(device_name)
        if not device:
            return False
        
        return device.role in [DeviceRole.SPINE, DeviceRole.TOR]