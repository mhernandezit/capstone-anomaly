"""
NATS Message Bus Publisher for Virtual Lab

This module handles publishing telemetry data to NATS message bus
for consumption by the ML pipeline.
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
import nats
from nats.aio.client import Client as NATS
from nats.aio.msg import Msg
import yaml

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NATSPublisher:
    """
    Publishes telemetry data to NATS message bus.
    
    This class handles the connection to NATS and publishes different
    types of telemetry data to appropriate subjects.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.servers = config.get('servers', ['nats://localhost:4222'])
        self.subjects = config.get('subjects', {})
        
        self.nc: Optional[NATS] = None
        self.connected = False
        
        logger.info("NATS publisher initialized")
    
    async def connect(self):
        """Connect to NATS server."""
        try:
            self.nc = await nats.connect(servers=self.servers)
            self.connected = True
            logger.info(f"Connected to NATS at {self.servers}")
        except Exception as e:
            logger.error(f"Failed to connect to NATS: {e}")
            self.connected = False
            raise
    
    async def disconnect(self):
        """Disconnect from NATS server."""
        if self.nc and self.connected:
            await self.nc.close()
            self.connected = False
            logger.info("Disconnected from NATS")
    
    async def publish_bgp_updates(self, updates: List[Dict[str, Any]]):
        """Publish BGP updates to NATS."""
        if not self.connected or not self.nc:
            logger.warning("Not connected to NATS, skipping BGP updates")
            return
        
        subject = self.subjects.get('bgp_updates', 'bgp.updates')
        
        try:
            for update in updates:
                message = json.dumps(update).encode('utf-8')
                await self.nc.publish(subject, message)
            
            logger.debug(f"Published {len(updates)} BGP updates to {subject}")
        except Exception as e:
            logger.error(f"Failed to publish BGP updates: {e}")
    
    async def publish_syslog_messages(self, messages: List[Dict[str, Any]]):
        """Publish syslog messages to NATS."""
        if not self.connected or not self.nc:
            logger.warning("Not connected to NATS, skipping syslog messages")
            return
        
        subject = self.subjects.get('syslog_messages', 'syslog.messages')
        
        try:
            for message in messages:
                message_data = json.dumps(message).encode('utf-8')
                await self.nc.publish(subject, message_data)
            
            logger.debug(f"Published {len(messages)} syslog messages to {subject}")
        except Exception as e:
            logger.error(f"Failed to publish syslog messages: {e}")
    
    async def publish_telemetry_data(self, metrics: List[Dict[str, Any]]):
        """Publish telemetry metrics to NATS."""
        if not self.connected or not self.nc:
            logger.warning("Not connected to NATS, skipping telemetry data")
            return
        
        subject = self.subjects.get('telemetry_data', 'telemetry.data')
        
        try:
            for metric in metrics:
                message_data = json.dumps(metric).encode('utf-8')
                await self.nc.publish(subject, message_data)
            
            logger.debug(f"Published {len(metrics)} telemetry metrics to {subject}")
        except Exception as e:
            logger.error(f"Failed to publish telemetry data: {e}")
    
    async def publish_processed_features(self, features: Dict[str, Any]):
        """Publish processed features to NATS."""
        if not self.connected or not self.nc:
            logger.warning("Not connected to NATS, skipping processed features")
            return
        
        subject = self.subjects.get('processed_features', 'features.processed')
        
        try:
            message_data = json.dumps(features).encode('utf-8')
            await self.nc.publish(subject, message_data)
            logger.debug(f"Published processed features to {subject}")
        except Exception as e:
            logger.error(f"Failed to publish processed features: {e}")
    
    async def publish_anomaly_alert(self, alert: Dict[str, Any]):
        """Publish anomaly alert to NATS."""
        if not self.connected or not self.nc:
            logger.warning("Not connected to NATS, skipping anomaly alert")
            return
        
        subject = self.subjects.get('anomaly_alerts', 'anomaly.alerts')
        
        try:
            message_data = json.dumps(alert).encode('utf-8')
            await self.nc.publish(subject, message_data)
            logger.info(f"Published anomaly alert to {subject}")
        except Exception as e:
            logger.error(f"Failed to publish anomaly alert: {e}")
    
    async def publish_batch(self, data_type: str, data: List[Dict[str, Any]]):
        """Publish a batch of data to the appropriate subject."""
        if data_type == 'bgp':
            await self.publish_bgp_updates(data)
        elif data_type == 'syslog':
            await self.publish_syslog_messages(data)
        elif data_type == 'telemetry':
            await self.publish_telemetry_data(data)
        else:
            logger.warning(f"Unknown data type: {data_type}")


class NATSConsumer:
    """
    Consumes messages from NATS for processing.
    
    This class can be used to consume messages from NATS subjects
    for further processing by the ML pipeline.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.servers = config.get('servers', ['nats://localhost:4222'])
        self.subjects = config.get('subjects', {})
        
        self.nc: Optional[NATS] = None
        self.connected = False
        self.subscriptions = {}
        
        logger.info("NATS consumer initialized")
    
    async def connect(self):
        """Connect to NATS server."""
        try:
            self.nc = await nats.connect(servers=self.servers)
            self.connected = True
            logger.info(f"Connected to NATS at {self.servers}")
        except Exception as e:
            logger.error(f"Failed to connect to NATS: {e}")
            self.connected = False
            raise
    
    async def disconnect(self):
        """Disconnect from NATS server."""
        if self.nc and self.connected:
            await self.nc.close()
            self.connected = False
            logger.info("Disconnected from NATS")
    
    async def subscribe_to_bgp_updates(self, callback):
        """Subscribe to BGP updates."""
        if not self.connected or not self.nc:
            logger.warning("Not connected to NATS, cannot subscribe")
            return
        
        subject = self.subjects.get('bgp_updates', 'bgp.updates')
        
        try:
            subscription = await self.nc.subscribe(subject, cb=callback)
            self.subscriptions['bgp_updates'] = subscription
            logger.info(f"Subscribed to BGP updates on {subject}")
        except Exception as e:
            logger.error(f"Failed to subscribe to BGP updates: {e}")
    
    async def subscribe_to_syslog_messages(self, callback):
        """Subscribe to syslog messages."""
        if not self.connected or not self.nc:
            logger.warning("Not connected to NATS, cannot subscribe")
            return
        
        subject = self.subjects.get('syslog_messages', 'syslog.messages')
        
        try:
            subscription = await self.nc.subscribe(subject, cb=callback)
            self.subscriptions['syslog_messages'] = subscription
            logger.info(f"Subscribed to syslog messages on {subject}")
        except Exception as e:
            logger.error(f"Failed to subscribe to syslog messages: {e}")
    
    async def subscribe_to_telemetry_data(self, callback):
        """Subscribe to telemetry data."""
        if not self.connected or not self.nc:
            logger.warning("Not connected to NATS, cannot subscribe")
            return
        
        subject = self.subjects.get('telemetry_data', 'telemetry.data')
        
        try:
            subscription = await self.nc.subscribe(subject, cb=callback)
            self.subscriptions['telemetry_data'] = subscription
            logger.info(f"Subscribed to telemetry data on {subject}")
        except Exception as e:
            logger.error(f"Failed to subscribe to telemetry data: {e}")
    
    async def subscribe_to_processed_features(self, callback):
        """Subscribe to processed features."""
        if not self.connected or not self.nc:
            logger.warning("Not connected to NATS, cannot subscribe")
            return
        
        subject = self.subjects.get('processed_features', 'features.processed')
        
        try:
            subscription = await self.nc.subscribe(subject, cb=callback)
            self.subscriptions['processed_features'] = subscription
            logger.info(f"Subscribed to processed features on {subject}")
        except Exception as e:
            logger.error(f"Failed to subscribe to processed features: {e}")
    
    async def subscribe_to_anomaly_alerts(self, callback):
        """Subscribe to anomaly alerts."""
        if not self.connected or not self.nc:
            logger.warning("Not connected to NATS, cannot subscribe")
            return
        
        subject = self.subjects.get('anomaly_alerts', 'anomaly.alerts')
        
        try:
            subscription = await self.nc.subscribe(subject, cb=callback)
            self.subscriptions['anomaly_alerts'] = subscription
            logger.info(f"Subscribed to anomaly alerts on {subject}")
        except Exception as e:
            logger.error(f"Failed to subscribe to anomaly alerts: {e}")


class MessageBusManager:
    """
    Manages the message bus for the virtual lab.
    
    This class coordinates between publishers and consumers
    and provides a unified interface for message bus operations.
    """
    
    def __init__(self, config_path: str):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.message_bus_config = self.config.get('message_bus', {})
        self.publisher = NATSPublisher(self.message_bus_config)
        self.consumer = NATSConsumer(self.message_bus_config)
        
        # Statistics
        self.stats = {
            'messages_published': 0,
            'messages_consumed': 0,
            'errors': 0,
            'start_time': None
        }
        
        logger.info("Message bus manager initialized")
    
    async def start(self):
        """Start the message bus manager."""
        await self.publisher.connect()
        await self.consumer.connect()
        self.stats['start_time'] = asyncio.get_event_loop().time()
        logger.info("Message bus manager started")
    
    async def stop(self):
        """Stop the message bus manager."""
        await self.publisher.disconnect()
        await self.consumer.disconnect()
        logger.info("Message bus manager stopped")
    
    async def publish_data(self, data_type: str, data: List[Dict[str, Any]]):
        """Publish data to the message bus."""
        try:
            await self.publisher.publish_batch(data_type, data)
            self.stats['messages_published'] += len(data)
        except Exception as e:
            logger.error(f"Failed to publish {data_type} data: {e}")
            self.stats['errors'] += 1
    
    async def publish_features(self, features: Dict[str, Any]):
        """Publish processed features."""
        try:
            await self.publisher.publish_processed_features(features)
            self.stats['messages_published'] += 1
        except Exception as e:
            logger.error(f"Failed to publish features: {e}")
            self.stats['errors'] += 1
    
    async def publish_alert(self, alert: Dict[str, Any]):
        """Publish anomaly alert."""
        try:
            await self.publisher.publish_anomaly_alert(alert)
            self.stats['messages_published'] += 1
        except Exception as e:
            logger.error(f"Failed to publish alert: {e}")
            self.stats['errors'] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get message bus statistics."""
        elapsed_time = asyncio.get_event_loop().time() - self.stats['start_time'] if self.stats['start_time'] else 0
        
        return {
            'messages_published': self.stats['messages_published'],
            'messages_consumed': self.stats['messages_consumed'],
            'errors': self.stats['errors'],
            'elapsed_time': elapsed_time,
            'publish_rate': self.stats['messages_published'] / elapsed_time if elapsed_time > 0 else 0,
            'error_rate': self.stats['errors'] / max(self.stats['messages_published'], 1)
        }


# Example usage and testing
async def test_message_bus():
    """Test the message bus functionality."""
    config_path = "virtual_lab/configs/lab_config.yml"
    
    # Initialize message bus manager
    manager = MessageBusManager(config_path)
    
    try:
        # Start the manager
        await manager.start()
        
        # Test data
        test_bgp_updates = [
            {
                "timestamp": 1234567890,
                "device_id": "spine-01",
                "peer": "10.0.1.1",
                "type": "UPDATE",
                "announce": ["10.0.0.0/24"],
                "withdraw": None,
                "attrs": {"as_path_len": 3}
            }
        ]
        
        test_syslog_messages = [
            {
                "timestamp": 1234567890,
                "device_id": "spine-01",
                "severity": "info",
                "message": "Interface GigabitEthernet0/0/1 is up"
            }
        ]
        
        # Publish test data
        await manager.publish_data('bgp', test_bgp_updates)
        await manager.publish_data('syslog', test_syslog_messages)
        
        # Wait a bit
        await asyncio.sleep(1)
        
        # Print stats
        stats = manager.get_stats()
        logger.info(f"Message bus stats: {stats}")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
    finally:
        await manager.stop()


if __name__ == "__main__":
    asyncio.run(test_message_bus())
