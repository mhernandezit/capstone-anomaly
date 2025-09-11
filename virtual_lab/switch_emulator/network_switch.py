"""
Network Switch Emulator for Virtual Lab

This module emulates a network switch that generates realistic BGP updates
and syslog messages for testing the anomaly detection pipeline.
"""

import asyncio
import random
import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import yaml

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DeviceRole(Enum):
    SPINE = "spine"
    TOR = "tor"
    LEAF = "leaf"


class BGPUpdateType(Enum):
    ANNOUNCEMENT = "announcement"
    WITHDRAWAL = "withdrawal"
    NOTIFICATION = "notification"
    KEEPALIVE = "keepalive"


class SyslogSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class NetworkInterface:
    """Represents a network interface on the switch."""
    name: str
    status: str  # "up" or "down"
    speed: str
    duplex: str
    last_change: datetime


@dataclass
class BGPPeer:
    """Represents a BGP peer connection."""
    peer_ip: str
    remote_as: int
    state: str  # "established", "idle", "active", "connect"
    uptime: datetime
    prefixes_received: int
    prefixes_advertised: int


@dataclass
class Prefix:
    """Represents a BGP prefix."""
    network: str
    as_path: List[int]
    next_hop: str
    origin: str
    communities: List[str]
    last_seen: datetime


class NetworkSwitch:
    """
    Emulates a network switch that generates BGP updates and syslog messages.
    
    This class simulates the behavior of a real network switch including:
    - BGP peer relationships and updates
    - Interface status changes
    - System events and errors
    - Realistic timing and patterns
    """
    
    def __init__(self, device_id: str, role: DeviceRole, config: Dict[str, Any]):
        self.device_id = device_id
        self.role = role
        self.config = config
        
        # Network state
        self.interfaces: Dict[str, NetworkInterface] = {}
        self.bgp_peers: Dict[str, BGPPeer] = {}
        self.prefixes: Dict[str, Prefix] = {}
        
        # Data generation state
        self.base_announcement_rate = config.get('base_announcements_per_second', 10)
        self.base_withdrawal_rate = config.get('base_withdrawals_per_second', 2)
        self.syslog_rate = config.get('base_messages_per_second', 5)
        
        # Anomaly injection
        self.anomaly_enabled = config.get('anomaly_injection', {}).get('enabled', False)
        self.anomaly_frequency = config.get('anomaly_injection', {}).get('frequency', 0.1)
        self.anomaly_types = config.get('anomaly_injection', {}).get('types', [])
        
        # Initialize network state
        self._initialize_interfaces()
        self._initialize_bgp_peers()
        self._initialize_prefixes()
        
        logger.info(f"Initialized {role.value} switch {device_id}")
    
    def _initialize_interfaces(self):
        """Initialize network interfaces based on device role."""
        interface_count = self.config.get('interfaces', 24)
        
        for i in range(interface_count):
            if_name = f"GigabitEthernet0/0/{i+1}"
            self.interfaces[if_name] = NetworkInterface(
                name=if_name,
                status="up" if random.random() > 0.1 else "down",
                speed="1000",
                duplex="full",
                last_change=datetime.now()
            )
    
    def _initialize_bgp_peers(self):
        """Initialize BGP peer relationships."""
        peer_configs = self.config.get('bgp_peers', [])
        
        for peer_config in peer_configs:
            peer_ip = peer_config['ip']
            remote_as = peer_config['as']
            
            self.bgp_peers[peer_ip] = BGPPeer(
                peer_ip=peer_ip,
                remote_as=remote_as,
                state="established" if random.random() > 0.05 else "idle",
                uptime=datetime.now() - timedelta(hours=random.randint(1, 72)),
                prefixes_received=random.randint(100, 1000),
                prefixes_advertised=random.randint(50, 500)
            )
    
    def _initialize_prefixes(self):
        """Initialize BGP prefixes."""
        prefix_pools = self.config.get('prefix_pools', [])
        
        for pool in prefix_pools:
            network = pool['network']
            count = pool['count']
            
            # Generate random prefixes from the pool
            for _ in range(min(count, 100)):  # Limit for performance
                prefix = self._generate_prefix_from_pool(network)
                self.prefixes[prefix] = Prefix(
                    network=prefix,
                    as_path=self._generate_as_path(),
                    next_hop=self._generate_next_hop(),
                    origin="igp",
                    communities=self._generate_communities(),
                    last_seen=datetime.now()
                )
    
    def _generate_prefix_from_pool(self, network: str) -> str:
        """Generate a random prefix from a network pool."""
        # Simple implementation - in reality would need proper CIDR math
        base_parts = network.split('.')
        if len(base_parts) == 4:
            # IPv4 prefix
            return f"{base_parts[0]}.{base_parts[1]}.{random.randint(0, 255)}.{random.randint(0, 255)}/24"
        return network
    
    def _generate_as_path(self) -> List[int]:
        """Generate a realistic AS path."""
        path_length = random.randint(2, 6)
        as_path = []
        
        # Start with our AS
        our_as = self.config.get('local_as', 65000)
        as_path.append(our_as)
        
        # Add transit ASes
        for _ in range(path_length - 1):
            as_path.append(random.randint(1, 65535))
        
        return as_path
    
    def _generate_next_hop(self) -> str:
        """Generate a next hop IP."""
        return f"10.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"
    
    def _generate_communities(self) -> List[str]:
        """Generate BGP communities."""
        communities = []
        if random.random() > 0.5:
            communities.append(f"{self.config.get('local_as', 65000)}:100")
        if random.random() > 0.7:
            communities.append(f"{self.config.get('local_as', 65000)}:200")
        return communities
    
    async def generate_bgp_update(self) -> Optional[Dict[str, Any]]:
        """Generate a BGP update message."""
        if not self.bgp_peers:
            return None
        
        # Select random peer
        peer_ip = random.choice(list(self.bgp_peers.keys()))
        peer = self.bgp_peers[peer_ip]
        
        if peer.state != "established":
            return None
        
        # Determine update type
        if random.random() < 0.8:  # 80% announcements
            update_type = BGPUpdateType.ANNOUNCEMENT
        else:  # 20% withdrawals
            update_type = BGPUpdateType.WITHDRAWAL
        
        # Generate update content
        if update_type == BGPUpdateType.ANNOUNCEMENT:
            # Announce new or existing prefix
            if self.prefixes and random.random() > 0.3:
                prefix = random.choice(list(self.prefixes.keys()))
            else:
                prefix = self._generate_prefix_from_pool("10.0.0.0/8")
            
            return {
                "timestamp": int(time.time()),
                "device_id": self.device_id,
                "peer": peer_ip,
                "type": "UPDATE",
                "announce": [prefix],
                "withdraw": None,
                "attrs": {
                    "as_path": self._generate_as_path(),
                    "next_hop": self._generate_next_hop(),
                    "origin": "igp",
                    "communities": self._generate_communities(),
                    "as_path_len": len(self._generate_as_path())
                }
            }
        
        elif update_type == BGPUpdateType.WITHDRAWAL:
            # Withdraw existing prefix
            if self.prefixes:
                prefix = random.choice(list(self.prefixes.keys()))
                # Remove from our prefix table
                del self.prefixes[prefix]
                
                return {
                    "timestamp": int(time.time()),
                    "device_id": self.device_id,
                    "peer": peer_ip,
                    "type": "UPDATE",
                    "announce": None,
                    "withdraw": [prefix],
                    "attrs": {
                        "as_path_len": 0
                    }
                }
        
        return None
    
    async def generate_syslog_message(self) -> Optional[Dict[str, Any]]:
        """Generate a syslog message."""
        # Determine message type and severity
        message_types = [
            "interface_up_down", "bgp_neighbor_changes", "ospf_events",
            "system_events", "security_events"
        ]
        
        msg_type = random.choice(message_types)
        severity = self._select_severity()
        
        # Generate message content based on type
        message_content = self._generate_message_content(msg_type, severity)
        
        return {
            "timestamp": int(time.time()),
            "device_id": self.device_id,
            "facility": "local0",
            "severity": severity.value,
            "message_type": msg_type,
            "message": message_content,
            "source_ip": self._get_device_ip()
        }
    
    def _select_severity(self) -> SyslogSeverity:
        """Select syslog severity based on configured distribution."""
        distribution = self.config.get('severity_distribution', {
            'info': 0.6, 'warning': 0.25, 'error': 0.1, 'critical': 0.05
        })
        
        rand = random.random()
        cumulative = 0
        
        for severity, prob in distribution.items():
            cumulative += prob
            if rand <= cumulative:
                return SyslogSeverity(severity)
        
        return SyslogSeverity.INFO
    
    def _generate_message_content(self, msg_type: str, severity: SyslogSeverity) -> str:
        """Generate realistic syslog message content."""
        templates = {
            "interface_up_down": [
                f"Interface {random.choice(list(self.interfaces.keys()))} is up",
                f"Interface {random.choice(list(self.interfaces.keys()))} is down",
                f"Line protocol on Interface {random.choice(list(self.interfaces.keys()))}, changed state to up",
                f"Line protocol on Interface {random.choice(list(self.interfaces.keys()))}, changed state to down"
            ],
            "bgp_neighbor_changes": [
                f"BGP: {random.choice(list(self.bgp_peers.keys()))} went from Established to Idle",
                f"BGP: {random.choice(list(self.bgp_peers.keys()))} went from Idle to Established",
                f"BGP: {random.choice(list(self.bgp_peers.keys()))} neighbor {random.choice(list(self.bgp_peers.keys()))} Up",
                f"BGP: {random.choice(list(self.bgp_peers.keys()))} neighbor {random.choice(list(self.bgp_peers.keys()))} Down"
            ],
            "ospf_events": [
                "OSPF: Interface GigabitEthernet0/0/1 going Up",
                "OSPF: Interface GigabitEthernet0/0/1 going Down",
                "OSPF: Neighbor 10.0.1.1 on GigabitEthernet0/0/1 from LOADING to FULL",
                "OSPF: Neighbor 10.0.1.1 on GigabitEthernet0/0/1 from FULL to DOWN"
            ],
            "system_events": [
                "System: CPU utilization is 45%",
                "System: Memory utilization is 78%",
                "System: Temperature is 45C",
                "System: Fan speed is 2500 RPM"
            ],
            "security_events": [
                "Security: Failed login attempt from 192.168.1.100",
                "Security: SSH connection established from 10.0.1.5",
                "Security: Access list denied packet from 172.16.1.50",
                "Security: User admin logged in via console"
            ]
        }
        
        return random.choice(templates.get(msg_type, ["System event occurred"]))
    
    def _get_device_ip(self) -> str:
        """Get the device's IP address."""
        return f"10.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"
    
    async def inject_anomaly(self) -> Optional[Dict[str, Any]]:
        """Inject an anomaly event."""
        if not self.anomaly_enabled or random.random() > self.anomaly_frequency:
            return None
        
        anomaly_type = random.choice(self.anomaly_types)
        
        if anomaly_type == "link_failure":
            return await self._simulate_link_failure()
        elif anomaly_type == "bgp_reset":
            return await self._simulate_bgp_reset()
        elif anomaly_type == "prefix_hijack":
            return await self._simulate_prefix_hijack()
        elif anomaly_type == "route_flap":
            return await self._simulate_route_flap()
        
        return None
    
    async def _simulate_link_failure(self) -> Dict[str, Any]:
        """Simulate a link failure event."""
        interface = random.choice(list(self.interfaces.keys()))
        self.interfaces[interface].status = "down"
        
        # Generate multiple related events
        events = []
        
        # Interface down event
        events.append({
            "timestamp": int(time.time()),
            "device_id": self.device_id,
            "type": "syslog",
            "severity": "error",
            "message": f"Interface {interface} is down"
        })
        
        # BGP neighbor down events
        for peer_ip in list(self.bgp_peers.keys())[:2]:  # Affect 2 peers
            events.append({
                "timestamp": int(time.time()),
                "device_id": self.device_id,
                "type": "bgp",
                "peer": peer_ip,
                "event": "neighbor_down"
            })
        
        return {
            "anomaly_type": "link_failure",
            "events": events,
            "impact": "high"
        }
    
    async def _simulate_bgp_reset(self) -> Dict[str, Any]:
        """Simulate a BGP session reset."""
        peer_ip = random.choice(list(self.bgp_peers.keys()))
        peer = self.bgp_peers[peer_ip]
        
        # Reset the peer
        peer.state = "idle"
        peer.uptime = datetime.now()
        
        return {
            "anomaly_type": "bgp_reset",
            "peer": peer_ip,
            "timestamp": int(time.time()),
            "device_id": self.device_id
        }
    
    async def _simulate_prefix_hijack(self) -> Dict[str, Any]:
        """Simulate a prefix hijack event."""
        # Generate suspicious prefix announcements
        suspicious_prefixes = []
        for _ in range(random.randint(5, 20)):
            prefix = self._generate_prefix_from_pool("10.0.0.0/8")
            suspicious_prefixes.append(prefix)
        
        return {
            "anomaly_type": "prefix_hijack",
            "prefixes": suspicious_prefixes,
            "timestamp": int(time.time()),
            "device_id": self.device_id
        }
    
    async def _simulate_route_flap(self) -> Dict[str, Any]:
        """Simulate route flapping."""
        prefix = random.choice(list(self.prefixes.keys())) if self.prefixes else "10.0.0.0/24"
        
        # Generate rapid announce/withdraw cycles
        events = []
        for _ in range(random.randint(3, 8)):
            events.append({
                "timestamp": int(time.time()),
                "type": "announcement",
                "prefix": prefix
            })
            events.append({
                "timestamp": int(time.time()) + 1,
                "type": "withdrawal",
                "prefix": prefix
            })
        
        return {
            "anomaly_type": "route_flap",
            "prefix": prefix,
            "events": events,
            "timestamp": int(time.time()),
            "device_id": self.device_id
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get current switch status."""
        return {
            "device_id": self.device_id,
            "role": self.role.value,
            "interfaces_up": sum(1 for iface in self.interfaces.values() if iface.status == "up"),
            "interfaces_down": sum(1 for iface in self.interfaces.values() if iface.status == "down"),
            "bgp_peers_established": sum(1 for peer in self.bgp_peers.values() if peer.state == "established"),
            "bgp_peers_idle": sum(1 for peer in self.bgp_peers.values() if peer.state == "idle"),
            "prefixes_learned": len(self.prefixes),
            "anomaly_enabled": self.anomaly_enabled
        }


class VirtualLabNetwork:
    """
    Manages a collection of network switches for the virtual lab.
    """
    
    def __init__(self, config_path: str):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.switches: Dict[str, NetworkSwitch] = {}
        self._initialize_network()
    
    def _initialize_network(self):
        """Initialize the virtual network with switches."""
        topology = self.config.get('topology', {})
        devices = topology.get('devices', {})
        
        # Create spine switches
        for i in range(devices.get('spine_switches', {}).get('count', 2)):
            device_id = f"spine-{i+1:02d}"
            switch_config = self._create_switch_config(DeviceRole.SPINE, i)
            self.switches[device_id] = NetworkSwitch(device_id, DeviceRole.SPINE, switch_config)
        
        # Create TOR switches
        for i in range(devices.get('tor_switches', {}).get('count', 4)):
            device_id = f"tor-{i+1:02d}"
            switch_config = self._create_switch_config(DeviceRole.TOR, i)
            self.switches[device_id] = NetworkSwitch(device_id, DeviceRole.TOR, switch_config)
        
        # Create leaf switches
        for i in range(devices.get('leaf_switches', {}).get('count', 8)):
            device_id = f"leaf-{i+1:02d}"
            switch_config = self._create_switch_config(DeviceRole.LEAF, i)
            self.switches[device_id] = NetworkSwitch(device_id, DeviceRole.LEAF, switch_config)
        
        logger.info(f"Initialized virtual network with {len(self.switches)} switches")
    
    def _create_switch_config(self, role: DeviceRole, index: int) -> Dict[str, Any]:
        """Create configuration for a switch based on its role."""
        base_config = self.config.get('data_generation', {})
        
        # Role-specific configuration
        if role == DeviceRole.SPINE:
            local_as = 65001
            peer_ips = [f"10.0.{i}.1" for i in range(2, 6)]  # TOR switches
        elif role == DeviceRole.TOR:
            local_as = 65002
            peer_ips = [f"10.0.1.{index+1}"]  # Spine switch
            peer_ips.extend([f"10.0.{index+2}.{i}" for i in range(1, 3)])  # Leaf switches
        else:  # LEAF
            local_as = 65003
            peer_ips = [f"10.0.{index//2+2}.{index%2+1}"]  # TOR switch
        
        return {
            'local_as': local_as,
            'interfaces': 24 if role != DeviceRole.LEAF else 12,
            'bgp_peers': [{'ip': ip, 'as': 65002 if role == DeviceRole.SPINE else 65001} for ip in peer_ips],
            'prefix_pools': self.config.get('topology', {}).get('bgp', {}).get('prefix_pools', []),
            **base_config.get('bgp_telemetry', {}),
            **base_config.get('syslog', {})
        }
    
    async def generate_network_events(self) -> List[Dict[str, Any]]:
        """Generate events from all switches in the network."""
        events = []
        
        for switch in self.switches.values():
            # Generate BGP updates
            bgp_update = await switch.generate_bgp_update()
            if bgp_update:
                events.append(bgp_update)
            
            # Generate syslog messages
            syslog_msg = await switch.generate_syslog_message()
            if syslog_msg:
                events.append(syslog_msg)
            
            # Inject anomalies
            anomaly = await switch.inject_anomaly()
            if anomaly:
                events.extend(anomaly.get('events', [anomaly]))
        
        return events
    
    def get_network_status(self) -> Dict[str, Any]:
        """Get status of all switches in the network."""
        return {
            switch_id: switch.get_status()
            for switch_id, switch in self.switches.items()
        }
