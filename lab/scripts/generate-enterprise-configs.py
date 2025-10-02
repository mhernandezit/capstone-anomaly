#!/usr/bin/env python3
"""
Enterprise Lab Configuration Generator

This script generates FRR configurations for all devices in the enterprise-scale lab.
Creates a realistic enterprise network topology with proper BGP configurations.
"""

import os
import yaml
from pathlib import Path

def create_directory_structure():
    """Create directory structure for enterprise configurations"""
    base_path = Path("configs/enterprise")
    
    devices = [
        "core-01", "core-02", "core-03", "core-04",
        "dist-01", "dist-02", "dist-03", "dist-04", 
        "dist-05", "dist-06", "dist-07", "dist-08",
        "access-01", "access-02", "access-03", "access-04",
        "access-05", "access-06", "access-07", "access-08",
        "access-09", "access-10", "access-11", "access-12",
        "access-13", "access-14", "access-15", "access-16",
        "access-17", "access-18", "access-19", "access-20",
        "edge-01", "edge-02", "edge-03", "edge-04",
        "server-01", "server-02", "server-03", "server-04",
        "server-05", "server-06", "server-07", "server-08",
        "server-09", "server-10"
    ]
    
    # Create directories
    for device in devices:
        (base_path / device).mkdir(parents=True, exist_ok=True)
    
    return devices

def generate_core_config(device_name, device_num):
    """Generate core router configuration"""
    router_id = f"{device_num}.{device_num}.{device_num}.{device_num}"
    asn = 65000
    
    config = f"""! {device_name.upper()} Core Router Configuration
hostname {device_name}
password zebra
enable password zebra
!
! Logging configuration
log stdout
log file /var/log/frr/frr.log
!
! Interface configuration
interface eth1
 description "Core-to-Core"
 ip address 10.{device_num}.1.{device_num}/30
!
interface eth2
 description "Core-to-Core"
 ip address 10.{device_num}.2.{device_num}/30
!
interface eth3
 description "Core-to-Core"
 ip address 10.{device_num}.3.{device_num}/30
!
interface eth4
 description "Core-to-Distribution"
 ip address 10.{device_num}.4.{device_num}/30
!
interface eth5
 description "Core-to-Distribution"
 ip address 10.{device_num}.5.{device_num}/30
!
interface eth6
 description "Core-to-Edge"
 ip address 10.{device_num}.6.{device_num}/30
!
interface eth7
 description "Monitoring"
 ip address 10.{device_num}.7.{device_num}/30
!
! BGP configuration
router bgp {asn}
 bgp router-id {router_id}
 no bgp default ipv4-unicast
!
 ! iBGP to other cores
"""
    
    # Add iBGP neighbors to other cores
    for i in range(1, 5):
        if i != device_num:
            config += f" neighbor 10.{i}.1.{i} remote-as {asn}\n"
            config += f" neighbor 10.{i}.1.{i} update-source eth1\n"
            config += f" neighbor 10.{i}.1.{i} next-hop-self\n"
    
    # Add eBGP to distribution layer
    dist_asn = 65100
    for i in range(1, 9):
        config += f" neighbor 10.{device_num}.4.{i} remote-as {dist_asn}\n"
        config += f" neighbor 10.{device_num}.4.{i} description \"DIST-{i:02d}\"\n"
    
    config += """!
 ! Address families
 address-family ipv4 unicast
"""
    
    # Activate all neighbors
    for i in range(1, 5):
        if i != device_num:
            config += f"  neighbor 10.{i}.1.{i} activate\n"
    
    for i in range(1, 9):
        config += f"  neighbor 10.{device_num}.4.{i} activate\n"
    
    config += f"""  network 10.{device_num}.0.0/16
!
! Loopback interface
interface lo
 ip address {router_id}/32
!
! Static routes for loopbacks
"""
    
    for i in range(1, 5):
        if i != device_num:
            config += f"ip route {i}.{i}.{i}.{i}/32 10.{i}.1.{i}\n"
    
    config += "!\n"
    
    return config

def generate_distribution_config(device_name, device_num):
    """Generate distribution switch configuration"""
    router_id = f"10.1.{device_num}.{device_num}"
    asn = 65100
    
    config = f"""! {device_name.upper()} Distribution Switch Configuration
hostname {device_name}
password zebra
enable password zebra
!
! Logging configuration
log stdout
log file /var/log/frr/frr.log
!
! Interface configuration
interface eth1
 description "Distribution-to-Core"
 ip address 10.{((device_num-1)//2)+1}.4.{device_num}/30
!
interface eth2
 description "Distribution-to-Access"
 ip address 10.10.{device_num}.1/30
!
interface eth3
 description "Distribution-to-Access"
 ip address 10.10.{device_num}.2/30
!
! BGP configuration
router bgp {asn}
 bgp router-id {router_id}
 no bgp default ipv4-unicast
!
 ! eBGP to core
 neighbor 10.{((device_num-1)//2)+1}.4.{((device_num-1)//2)+1} remote-as 65000
 neighbor 10.{((device_num-1)//2)+1}.4.{((device_num-1)//2)+1} description "CORE-{((device_num-1)//2)+1:02d}"
!
 ! eBGP to access layer
 neighbor 10.10.{device_num}.2 remote-as 65200
 neighbor 10.10.{device_num}.2 description "ACCESS-{(device_num-1)*2+1:02d}"
!
 neighbor 10.10.{device_num}.3 remote-as 65200
 neighbor 10.10.{device_num}.3 description "ACCESS-{(device_num-1)*2+2:02d}"
!
 ! Address families
 address-family ipv4 unicast
  neighbor 10.{((device_num-1)//2)+1}.4.{((device_num-1)//2)+1} activate
  neighbor 10.10.{device_num}.2 activate
  neighbor 10.10.{device_num}.3 activate
  network 10.10.{device_num}.0/24
!
! Loopback interface
interface lo
 ip address {router_id}/32
!
!
"""
    
    return config

def generate_access_config(device_name, device_num):
    """Generate access switch configuration"""
    router_id = f"10.11.{device_num}.{device_num}"
    asn = 65200
    
    config = f"""! {device_name.upper()} Access Switch Configuration
hostname {device_name}
password zebra
enable password zebra
!
! Logging configuration
log stdout
log file /var/log/frr/frr.log
!
! Interface configuration
interface eth1
 description "Access-to-Distribution"
 ip address 10.10.{((device_num-1)//2)+1}.{2 if device_num % 2 == 0 else 3}/30
!
interface eth2
 description "Access-to-Server"
 ip address 10.12.{device_num}.1/30
!
! BGP configuration
router bgp {asn}
 bgp router-id {router_id}
 no bgp default ipv4-unicast
!
 ! eBGP to distribution
 neighbor 10.10.{((device_num-1)//2)+1}.{1 if device_num % 2 == 0 else 1} remote-as 65100
 neighbor 10.10.{((device_num-1)//2)+1}.{1 if device_num % 2 == 0 else 1} description "DIST-{((device_num-1)//2)+1:02d}"
!
 ! eBGP to servers
 neighbor 10.12.{device_num}.2 remote-as 65400
 neighbor 10.12.{device_num}.2 description "SERVER-{device_num:02d}"
!
 ! Address families
 address-family ipv4 unicast
  neighbor 10.10.{((device_num-1)//2)+1}.{1 if device_num % 2 == 0 else 1} activate
  neighbor 10.12.{device_num}.2 activate
  network 10.12.{device_num}.0/24
!
! Loopback interface
interface lo
 ip address {router_id}/32
!
!
"""
    
    return config

def generate_edge_config(device_name, device_num):
    """Generate edge router configuration"""
    router_id = f"10.20.{device_num}.{device_num}"
    asn = 65300
    
    config = f"""! {device_name.upper()} Edge Router Configuration
hostname {device_name}
password zebra
enable password zebra
!
! Logging configuration
log stdout
log file /var/log/frr/frr.log
!
! Interface configuration
interface eth1
 description "Edge-to-Core"
 ip address 10.{device_num}.6.{device_num}/30
!
interface eth2
 description "External-ISP"
 ip address 203.0.{device_num}.1/30
!
! BGP configuration
router bgp {asn}
 bgp router-id {router_id}
 no bgp default ipv4-unicast
!
 ! eBGP to core
 neighbor 10.{device_num}.6.{device_num} remote-as 65000
 neighbor 10.{device_num}.6.{device_num} description "CORE-{device_num:02d}"
!
 ! eBGP to ISP
 neighbor 203.0.{device_num}.2 remote-as 64500
 neighbor 203.0.{device_num}.2 description "ISP-{device_num:02d}"
!
 ! Address families
 address-family ipv4 unicast
  neighbor 10.{device_num}.6.{device_num} activate
  neighbor 203.0.{device_num}.2 activate
  network 10.20.{device_num}.0/24
!
! Loopback interface
interface lo
 ip address {router_id}/32
!
!
"""
    
    return config

def generate_server_config(device_name, device_num):
    """Generate server configuration"""
    router_id = f"10.12.{device_num}.{device_num}"
    asn = 65400
    
    config = f"""! {device_name.upper()} Server Configuration
hostname {device_name}
password zebra
enable password zebra
!
! Logging configuration
log stdout
log file /var/log/frr/frr.log
!
! Interface configuration
interface eth1
 description "Server-to-Access"
 ip address 10.12.{device_num}.2/30
!
! BGP configuration
router bgp {asn}
 bgp router-id {router_id}
 no bgp default ipv4-unicast
!
 ! eBGP to access
 neighbor 10.12.{device_num}.1 remote-as 65200
 neighbor 10.12.{device_num}.1 description "ACCESS-{device_num:02d}"
!
 ! Address families
 address-family ipv4 unicast
  neighbor 10.12.{device_num}.1 activate
  network 10.12.{device_num}.0/24
!
! Loopback interface
interface lo
 ip address {router_id}/32
!
!
"""
    
    return config

def main():
    """Main function to generate all configurations"""
    print("Generating enterprise lab configurations...")
    
    devices = create_directory_structure()
    base_path = Path("configs/enterprise")
    
    for device in devices:
        device_type = device.split('-')[0]
        device_num = int(device.split('-')[1])
        
        if device_type == "core":
            config = generate_core_config(device, device_num)
        elif device_type == "dist":
            config = generate_distribution_config(device, device_num)
        elif device_type == "access":
            config = generate_access_config(device, device_num)
        elif device_type == "edge":
            config = generate_edge_config(device, device_num)
        elif device_type == "server":
            config = generate_server_config(device, device_num)
        else:
            continue
        
        # Write configuration file
        config_file = base_path / device / "frr.conf"
        with open(config_file, 'w') as f:
            f.write(config)
        
        print(f"Generated configuration for {device}")
    
    # Create log directories
    log_base = Path("logs")
    for device in devices:
        (log_base / device).mkdir(parents=True, exist_ok=True)
    
    print(f"Generated configurations for {len(devices)} devices")
    print("Enterprise lab configuration generation complete!")

if __name__ == "__main__":
    main()
