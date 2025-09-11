"""
Network Switch Emulator

This module provides network switch emulation for generating realistic
BGP updates and syslog messages in the virtual lab environment.
"""

from .network_switch import NetworkSwitch, VirtualLabNetwork, DeviceRole

__all__ = ['NetworkSwitch', 'VirtualLabNetwork', 'DeviceRole']
