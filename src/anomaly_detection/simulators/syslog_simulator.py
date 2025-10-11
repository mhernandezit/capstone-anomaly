"""
Syslog Message Simulator for Network Failure Detection

This module generates realistic syslog messages that correlate with BGP events
to simulate the dual-signal approach for network failure detection.
"""

import asyncio
import json
import logging
import random
import time
from datetime import datetime
from typing import Any, Dict, List

from nats.aio.client import Client as NATS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NetworkDevice:
    """Represents a network device with its role and characteristics."""

    def __init__(self, name: str, role: str, ip: str, interfaces: List[str] = None):
        self.name = name
        self.role = role
        self.ip = ip
        self.interfaces = interfaces or []
        self.status = "up"
        self.last_event_time = datetime.now()

    def get_interface(self) -> str:
        """Get a random interface for this device."""
        if self.interfaces:
            return random.choice(self.interfaces)
        return f"GigabitEthernet0/0/{random.randint(1, 4)}"


class SyslogSimulator:
    """
    Generates realistic syslog messages for network devices.

    Features:
    - Correlates with BGP events for realistic failure simulation
    - Generates device-specific messages based on role
    - Supports various failure scenarios
    - Publishes to NATS for integration with BGP pipeline
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the syslog simulator.

        Args:
            config: Configuration containing device mappings and NATS settings
        """
        self.config = config
        self.nats_url = config.get("nats_url", "nats://localhost:4222")
        self.devices = self._create_devices(config.get("devices", {}))
        self.failure_scenarios = self._create_failure_scenarios()

        # NATS client
        self.nc = None

        logger.info(f"Initialized syslog simulator with {len(self.devices)} devices")

    def _create_devices(self, device_config: Dict[str, Any]) -> Dict[str, NetworkDevice]:
        """Create network devices from configuration."""
        devices = {}

        # Default device configuration if none provided
        if not device_config:
            device_config = {
                "rr-01": {
                    "role": "rr",
                    "ip": "10.0.0.1",
                    "interfaces": ["GigabitEthernet0/0/1", "GigabitEthernet0/0/2"],
                },
                "rr-02": {
                    "role": "rr",
                    "ip": "10.0.0.2",
                    "interfaces": ["GigabitEthernet0/0/1", "GigabitEthernet0/0/2"],
                },
                "spine-01": {
                    "role": "spine",
                    "ip": "10.0.1.1",
                    "interfaces": [
                        "GigabitEthernet0/0/1",
                        "GigabitEthernet0/0/2",
                        "GigabitEthernet0/0/3",
                    ],
                },
                "spine-02": {
                    "role": "spine",
                    "ip": "10.0.1.2",
                    "interfaces": [
                        "GigabitEthernet0/0/1",
                        "GigabitEthernet0/0/2",
                        "GigabitEthernet0/0/3",
                    ],
                },
                "tor-01": {
                    "role": "tor",
                    "ip": "10.0.2.1",
                    "interfaces": [
                        "GigabitEthernet0/0/1",
                        "GigabitEthernet0/0/2",
                        "GigabitEthernet0/0/3",
                        "GigabitEthernet0/0/4",
                    ],
                },
                "tor-02": {
                    "role": "tor",
                    "ip": "10.0.2.2",
                    "interfaces": [
                        "GigabitEthernet0/0/1",
                        "GigabitEthernet0/0/2",
                        "GigabitEthernet0/0/3",
                        "GigabitEthernet0/0/4",
                    ],
                },
                "edge-01": {
                    "role": "edge",
                    "ip": "10.0.3.1",
                    "interfaces": ["GigabitEthernet0/0/1", "GigabitEthernet0/0/2"],
                },
                "edge-02": {
                    "role": "edge",
                    "ip": "10.0.3.2",
                    "interfaces": ["GigabitEthernet0/0/1", "GigabitEthernet0/0/2"],
                },
            }

        for name, device_info in device_config.items():
            devices[name] = NetworkDevice(
                name=name,
                role=device_info["role"],
                ip=device_info["ip"],
                interfaces=device_info.get("interfaces", []),
            )

        return devices

    def _create_failure_scenarios(self) -> Dict[str, List[str]]:
        """Create realistic failure scenarios with corresponding syslog messages."""
        return {
            "link_failure": [
                "Interface {interface} is down",
                "Interface {interface} changed state to down",
                "LINK-3-UPDOWN: Interface {interface}, changed state to down",
                "OSPF-5-ADJCHG: Process 1, Nbr {neighbor_ip} on {interface} from FULL to DOWN",
                "BGP-5-ADJCHG: neighbor {neighbor_ip} Down (Interface flap)",
            ],
            "router_crash": [
                "SYS-5-RESTART: System restarted",
                "SYS-6-BOOTTIME: Time taken to reboot after reload = {reboot_time} seconds",
                "BGP-5-ADJCHG: neighbor {neighbor_ip} Down (Peer closed the session)",
                "OSPF-5-ADJCHG: Process 1, Nbr {neighbor_ip} on {interface} from FULL to DOWN",
            ],
            "bgp_session_reset": [
                "BGP-5-ADJCHG: neighbor {neighbor_ip} Down (Peer closed the session)",
                "BGP-5-ADJCHG: neighbor {neighbor_ip} Down (Hold timer expired)",
                "BGP-5-ADJCHG: neighbor {neighbor_ip} Down (Connection reset by peer)",
                "BGP-3-BACKWARD_TRANSITION: neighbor {neighbor_ip} FSM changed from Established to Idle",
            ],
            "interface_flap": [
                "Interface {interface} is up",
                "Interface {interface} is down",
                "Interface {interface} changed state to up",
                "Interface {interface} changed state to down",
                "LINK-3-UPDOWN: Interface {interface}, changed state to up",
            ],
            "normal_operation": [
                "BGP-5-ADJCHG: neighbor {neighbor_ip} Up",
                "OSPF-5-ADJCHG: Process 1, Nbr {neighbor_ip} on {interface} from LOADING to FULL",
                "Interface {interface} is up",
                "BGP-6-NEXTHOP_CREATE: Next hop {next_hop} in VRF {vrf} created",
                "BGP-6-NEXTHOP_DELETE: Next hop {next_hop} in VRF {vrf} deleted",
            ],
        }

    async def start(self):
        """Start the syslog simulator and connect to NATS."""
        self.nc = NATS()
        await self.nc.connect(servers=[self.nats_url])
        logger.info("Syslog simulator started, connected to NATS")

    async def stop(self):
        """Stop the simulator and disconnect from NATS."""
        if self.nc:
            await self.nc.drain()
        logger.info("Syslog simulator stopped")

    def generate_syslog_message(
        self, device: NetworkDevice, scenario: str = "normal_operation", **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a realistic syslog message for a device.

        Args:
            device: Network device
            scenario: Failure scenario type
            **kwargs: Additional parameters for message formatting

        Returns:
            Dictionary containing syslog message data
        """
        # Get message template
        templates = self.failure_scenarios.get(scenario, self.failure_scenarios["normal_operation"])
        template = random.choice(templates)

        # Fill in template variables
        message = template.format(
            interface=device.get_interface(),
            neighbor_ip=kwargs.get("neighbor_ip", "10.0.0.100"),
            next_hop=kwargs.get("next_hop", "10.0.0.1"),
            vrf=kwargs.get("vrf", "default"),
            reboot_time=random.randint(30, 120),
        )

        # Create syslog message
        timestamp = datetime.now()
        syslog_msg = {
            "timestamp": int(timestamp.timestamp()),
            "device": device.name,
            "role": device.role,
            "ip": device.ip,
            "facility": "local0",
            "severity": random.choice(["info", "warning", "error"]),
            "message": message,
            "scenario": scenario,
            "raw_syslog": f"<{random.randint(16, 23)}> {timestamp.strftime('%b %d %H:%M:%S')} {device.name} : {message}",
        }

        return syslog_msg

    async def simulate_normal_operation(self, duration_seconds: int = 60):
        """Simulate normal network operation with occasional syslog messages."""
        logger.info(f"Simulating normal operation for {duration_seconds} seconds...")

        start_time = time.time()
        while time.time() - start_time < duration_seconds:
            # Randomly select a device
            device = random.choice(list(self.devices.values()))

            # Generate normal operation message
            syslog_msg = self.generate_syslog_message(device, "normal_operation")

            # Publish to NATS
            await self._publish_syslog(syslog_msg)

            # Wait random interval (1-10 seconds)
            await asyncio.sleep(random.uniform(1, 10))

    async def simulate_failure_scenario(
        self, scenario: str, affected_devices: List[str] = None, duration_seconds: int = 30
    ):
        """
        Simulate a specific failure scenario.

        Args:
            scenario: Type of failure scenario
            affected_devices: List of device names to affect
            duration_seconds: How long to simulate the failure
        """
        if affected_devices is None:
            # Select random devices based on scenario
            if scenario == "link_failure":
                affected_devices = random.sample(list(self.devices.keys()), 2)
            elif scenario == "router_crash":
                affected_devices = [random.choice(list(self.devices.keys()))]
            else:
                affected_devices = random.sample(list(self.devices.keys()), random.randint(1, 3))

        logger.info(f"Simulating {scenario} affecting devices: {affected_devices}")

        start_time = time.time()
        while time.time() - start_time < duration_seconds:
            for device_name in affected_devices:
                if device_name in self.devices:
                    device = self.devices[device_name]

                    # Generate failure message
                    syslog_msg = self.generate_syslog_message(device, scenario)

                    # Publish to NATS
                    await self._publish_syslog(syslog_msg)

            # Wait between messages (0.1-2 seconds for failure scenarios)
            await asyncio.sleep(random.uniform(0.1, 2))

    async def simulate_correlated_failure(
        self, bgp_event: Dict[str, Any], delay_seconds: float = 0.5
    ):
        """
        Simulate syslog events that correlate with BGP events.

        Args:
            bgp_event: BGP event data to correlate with
            delay_seconds: Delay between BGP and syslog events
        """
        await asyncio.sleep(delay_seconds)

        # Determine failure type based on BGP event
        if "withdraw" in str(bgp_event).lower():
            scenario = "link_failure"
        elif "notification" in str(bgp_event).lower():
            scenario = "bgp_session_reset"
        else:
            scenario = "interface_flap"

        # Get affected device (try to match BGP peer)
        peer_ip = bgp_event.get("peer", "10.0.0.100")
        affected_device = None

        for device in self.devices.values():
            if device.ip == peer_ip or peer_ip in device.ip:
                affected_device = device
                break

        if not affected_device:
            affected_device = random.choice(list(self.devices.values()))

        # Generate correlated syslog message
        syslog_msg = self.generate_syslog_message(affected_device, scenario, neighbor_ip=peer_ip)

        # Add correlation metadata
        syslog_msg["correlated_bgp_event"] = {
            "timestamp": bgp_event.get("timestamp"),
            "peer": bgp_event.get("peer"),
            "type": bgp_event.get("type"),
        }

        await self._publish_syslog(syslog_msg)
        logger.info(f"Generated correlated syslog for BGP event: {scenario}")

    async def _publish_syslog(self, syslog_msg: Dict[str, Any]):
        """Publish syslog message to NATS."""
        try:
            message_json = json.dumps(syslog_msg, default=str)
            await self.nc.publish("syslog.messages", message_json.encode())
            logger.debug(f"Published syslog: {syslog_msg['device']} - {syslog_msg['message']}")
        except Exception as e:
            logger.error(f"Error publishing syslog: {e}")


async def main():
    """Main function to run the syslog simulator."""
    config = {
        "nats_url": "nats://localhost:4222",
        "devices": {
            "rr-01": {
                "role": "rr",
                "ip": "10.0.0.1",
                "interfaces": ["GigabitEthernet0/0/1", "GigabitEthernet0/0/2"],
            },
            "spine-01": {
                "role": "spine",
                "ip": "10.0.1.1",
                "interfaces": ["GigabitEthernet0/0/1", "GigabitEthernet0/0/2"],
            },
            "tor-01": {
                "role": "tor",
                "ip": "10.0.2.1",
                "interfaces": ["GigabitEthernet0/0/1", "GigabitEthernet0/0/2"],
            },
            "edge-01": {
                "role": "edge",
                "ip": "10.0.3.1",
                "interfaces": ["GigabitEthernet0/0/1", "GigabitEthernet0/0/2"],
            },
        },
    }

    simulator = SyslogSimulator(config)

    try:
        await simulator.start()

        # Simulate normal operation
        await simulator.simulate_normal_operation(30)

        # Simulate a link failure
        await simulator.simulate_failure_scenario("link_failure", ["spine-01", "tor-01"], 20)

        # Simulate normal operation again
        await simulator.simulate_normal_operation(30)

    except KeyboardInterrupt:
        logger.info("Shutting down syslog simulator...")
    finally:
        await simulator.stop()


if __name__ == "__main__":
    asyncio.run(main())
