"""
Message Bus Integration

This module provides message bus integration for network telemetry,
including NATS publishers and consumers for data streaming.
"""

from .nats_publisher import MessageBusManager, NATSConsumer, NATSPublisher

__all__ = ["NATSPublisher", "NATSConsumer", "MessageBusManager"]
