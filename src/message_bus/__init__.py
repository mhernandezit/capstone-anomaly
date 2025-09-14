"""
Message Bus Integration

This module provides message bus integration for the virtual lab,
including NATS publishers and consumers for data streaming.
"""

from .nats_publisher import NATSPublisher, NATSConsumer, MessageBusManager

__all__ = ["NATSPublisher", "NATSConsumer", "MessageBusManager"]
