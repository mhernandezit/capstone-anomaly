#!/usr/bin/env python3
"""
BGP Collector for Containerlab Environment
Monitors BGP updates from FRR routers using vtysh commands
"""

import asyncio
import json
import logging
import subprocess
import time
from datetime import datetime
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BGPCollector:
    """Collects BGP updates from FRR routers in the lab environment."""
    
    def __init__(self, lab_name: str = "bgp-anomaly-lab"):
        self.lab_name = lab_name
        self.devices = [
            "spine-01", "spine-02", "tor-01", "tor-02", 
            "edge-01", "edge-02", "server-01", "server-02", 
            "server-03", "server-04"
        ]
        self.running = False
        
    def get_container_name(self, device: str) -> str:
        """Get the Docker container name for a device."""
        return f"clab-{self.lab_name}-{device}"
    
    def check_device_available(self, device: str) -> bool:
        """Check if a device container is running and accessible."""
        try:
            container_name = self.get_container_name(device)
            result = subprocess.run(
                ["docker", "exec", container_name, "vtysh", "-c", "show version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def get_bgp_neighbors(self, device: str) -> List[Dict]:
        """Get BGP neighbor information from a device."""
        try:
            container_name = self.get_container_name(device)
            result = subprocess.run(
                ["docker", "exec", container_name, "vtysh", "-c", "show bgp summary json"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                logger.warning(f"Failed to get BGP summary from {device}: {result.stderr}")
                return []
            
            data = json.loads(result.stdout)
            neighbors = []
            
            # Parse BGP summary data
            if 'ipv4Unicast' in data and 'peers' in data['ipv4Unicast']:
                for peer_ip, peer_data in data['ipv4Unicast']['peers'].items():
                    neighbor = {
                        'device': device,
                        'peer_ip': peer_ip,
                        'asn': peer_data.get('remoteAs', 0),
                        'state': peer_data.get('state', 'Unknown'),
                        'uptime': peer_data.get('uptime', 0),
                        'prefixes_received': peer_data.get('pfxRcd', 0),
                        'prefixes_sent': peer_data.get('pfxSnt', 0),
                        'timestamp': datetime.now().isoformat()
                    }
                    neighbors.append(neighbor)
            
            return neighbors
            
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, json.JSONDecodeError) as e:
            logger.error(f"Error getting BGP neighbors from {device}: {e}")
            return []
    
    def get_bgp_routes(self, device: str) -> List[Dict]:
        """Get BGP route information from a device."""
        try:
            container_name = self.get_container_name(device)
            result = subprocess.run(
                ["docker", "exec", container_name, "vtysh", "-c", "show bgp ipv4 unicast json"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                logger.warning(f"Failed to get BGP routes from {device}: {result.stderr}")
                return []
            
            data = json.loads(result.stdout)
            routes = []
            
            # Parse BGP routes data
            if 'routes' in data:
                for prefix, route_data in data['routes'].items():
                    for route_info in route_data:
                        route = {
                            'device': device,
                            'prefix': prefix,
                            'as_path': route_info.get('path', ''),
                            'next_hop': route_info.get('nexthops', [{}])[0].get('ip', ''),
                            'origin': route_info.get('origin', 'Unknown'),
                            'local_pref': route_info.get('localpref', 0),
                            'med': route_info.get('med', 0),
                            'timestamp': datetime.now().isoformat()
                        }
                        routes.append(route)
            
            return routes
            
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, json.JSONDecodeError) as e:
            logger.error(f"Error getting BGP routes from {device}: {e}")
            return []
    
    def monitor_bgp_logs(self, device: str) -> List[Dict]:
        """Monitor BGP-related log entries from a device."""
        try:
            container_name = self.get_container_name(device)
            result = subprocess.run(
                ["docker", "exec", container_name, "tail", "-n", "50", "/var/log/frr/bgpd.log"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                return []
            
            log_entries = []
            for line in result.stdout.strip().split('\n'):
                if line and ('BGP' in line or 'neighbor' in line.lower()):
                    log_entry = {
                        'device': device,
                        'log_line': line,
                        'timestamp': datetime.now().isoformat()
                    }
                    log_entries.append(log_entry)
            
            return log_entries
            
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
            logger.error(f"Error monitoring BGP logs from {device}: {e}")
            return []
    
    async def collect_bgp_data(self) -> Dict:
        """Collect BGP data from all available devices."""
        logger.info("Collecting BGP data from lab devices...")
        
        data = {
            'neighbors': [],
            'routes': [],
            'logs': [],
            'timestamp': datetime.now().isoformat(),
            'devices_available': 0,
            'devices_total': len(self.devices)
        }
        
        for device in self.devices:
            if not self.check_device_available(device):
                logger.warning(f"Device {device} is not available")
                continue
            
            data['devices_available'] += 1
            logger.debug(f"Collecting data from {device}")
            
            # Collect BGP neighbors
            neighbors = self.get_bgp_neighbors(device)
            data['neighbors'].extend(neighbors)
            
            # Collect BGP routes
            routes = self.get_bgp_routes(device)
            data['routes'].extend(routes)
            
            # Collect BGP logs
            logs = self.monitor_bgp_logs(device)
            data['logs'].extend(logs)
        
        logger.info(f"Collected data from {data['devices_available']}/{data['devices_total']} devices")
        logger.info(f"Found {len(data['neighbors'])} neighbors, {len(data['routes'])} routes, {len(data['logs'])} log entries")
        
        return data
    
    async def start_monitoring(self, interval: int = 30):
        """Start continuous BGP monitoring."""
        logger.info(f"Starting BGP monitoring with {interval}s interval")
        self.running = True
        
        try:
            while self.running:
                data = await self.collect_bgp_data()
                
                # Log summary
                logger.info(f"BGP Status: {data['devices_available']} devices, "
                          f"{len(data['neighbors'])} neighbors, "
                          f"{len(data['routes'])} routes")
                
                # Here you could send data to NATS, save to file, etc.
                # For now, just log the data
                if data['neighbors']:
                    active_neighbors = [n for n in data['neighbors'] if n['state'] == 'Established']
                    logger.info(f"Active BGP sessions: {len(active_neighbors)}")
                
                await asyncio.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info("BGP monitoring stopped by user")
        except Exception as e:
            logger.error(f"Error in BGP monitoring: {e}")
        finally:
            self.running = False
    
    def stop_monitoring(self):
        """Stop BGP monitoring."""
        self.running = False


async def main():
    """Main function for testing the BGP collector."""
    collector = BGPCollector()
    
    # Test single collection
    logger.info("Testing BGP data collection...")
    data = await collector.collect_bgp_data()
    
    # Print summary
    print(f"\nBGP Collection Summary:")
    print(f"Devices available: {data['devices_available']}/{data['devices_total']}")
    print(f"BGP neighbors: {len(data['neighbors'])}")
    print(f"BGP routes: {len(data['routes'])}")
    print(f"Log entries: {len(data['logs'])}")
    
    if data['neighbors']:
        print(f"\nActive BGP Sessions:")
        for neighbor in data['neighbors']:
            if neighbor['state'] == 'Established':
                print(f"  {neighbor['device']} -> {neighbor['peer_ip']} (AS{neighbor['asn']})")


if __name__ == "__main__":
    asyncio.run(main())
