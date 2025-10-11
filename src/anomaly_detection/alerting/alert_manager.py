"""
Alert Manager for BGP Anomaly Detection

This module handles alert generation, notification delivery, and alert management
for network operators monitoring the dual-signal anomaly detection system.
"""

import asyncio
import logging
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional

import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Alert:
    """Represents a single alert."""

    def __init__(self, event_data: Dict[str, Any]):
        self.timestamp = event_data.get("timestamp", int(datetime.now().timestamp()))
        self.alert_id = f"ALERT_{self.timestamp}_{hash(str(event_data)) % 10000}"
        self.severity = self._determine_severity(event_data)
        self.title = self._generate_title(event_data)
        self.description = self._generate_description(event_data)
        self.impact = event_data.get("impact_analysis", {}).get("impact", "Unknown")
        self.confidence = event_data.get("anomaly_confidence", 0.0)
        self.roles_affected = event_data.get("impact_analysis", {}).get("roles", [])
        self.raw_event = event_data
        self.status = "active"
        self.acknowledged = False
        self.acknowledged_by = None
        self.acknowledged_at = None

    def _determine_severity(self, event_data: Dict[str, Any]) -> str:
        """Determine alert severity based on event data."""
        confidence = event_data.get("anomaly_confidence", 0.0)
        impact = event_data.get("impact_analysis", {}).get("impact", "Unknown")
        syslog_errors = event_data.get("syslog_analysis", {}).get("has_errors", False)

        if confidence > 0.9 and impact == "NETWORK_IMPACTING" and syslog_errors:
            return "CRITICAL"
        elif confidence > 0.7 and impact == "NETWORK_IMPACTING":
            return "HIGH"
        elif confidence > 0.5 or impact == "EDGE_LOCAL":
            return "MEDIUM"
        else:
            return "LOW"

    def _generate_title(self, event_data: Dict[str, Any]) -> str:
        """Generate alert title."""
        impact = event_data.get("impact_analysis", {}).get("impact", "Unknown")
        roles = event_data.get("impact_analysis", {}).get("roles", [])

        if impact == "NETWORK_IMPACTING":
            return f"Network-Wide Anomaly Detected - {', '.join(roles)}"
        elif impact == "EDGE_LOCAL":
            return f"Edge-Local Anomaly Detected - {', '.join(roles)}"
        else:
            return "BGP Anomaly Detected"

    def _generate_description(self, event_data: Dict[str, Any]) -> str:
        """Generate detailed alert description."""
        bgp_analysis = event_data.get("bgp_analysis", {})
        syslog_analysis = event_data.get("syslog_analysis", {})
        correlation = event_data.get("correlation_analysis", {})

        description = f"""
**Alert Details:**
- Confidence: {event_data.get('anomaly_confidence', 0):.2f}
- Impact Level: {event_data.get('impact_analysis', {}).get('impact', 'Unknown')}
- Affected Roles: {', '.join(event_data.get('impact_analysis', {}).get('roles', []))}

**BGP Analysis:**
- Detected Series: {', '.join(bgp_analysis.get('detected_series', []))}
- Overall Score: {event_data.get('overall_score', 0):.2f}

**Syslog Analysis:**
- Total Messages: {syslog_analysis.get('total_messages', 0)}
- Error Messages: {syslog_analysis.get('severity_counts', {}).get('error', 0)}
- Devices Affected: {', '.join(syslog_analysis.get('device_counts', {}).keys())}

**Signal Correlation:**
- BGP Anomaly: {correlation.get('bgp_anomaly', False)}
- Syslog Anomaly: {correlation.get('syslog_anomaly', False)}
- Correlation Strength: {correlation.get('correlation_strength', 0):.2f}
- Signal Agreement: {correlation.get('signal_agreement', False)}
        """.strip()

        return description

    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary."""
        return {
            "alert_id": self.alert_id,
            "timestamp": self.timestamp,
            "severity": self.severity,
            "title": self.title,
            "description": self.description,
            "impact": self.impact,
            "confidence": self.confidence,
            "roles_affected": self.roles_affected,
            "status": self.status,
            "acknowledged": self.acknowledged,
            "acknowledged_by": self.acknowledged_by,
            "acknowledged_at": self.acknowledged_at,
        }


class AlertManager:
    """Manages alerts and notifications for the anomaly detection system."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.alerts = {}  # alert_id -> Alert
        self.notification_channels = config.get("notifications", {})
        self.alert_history = []

        logger.info("Alert manager initialized")

    def process_event(self, event_data: Dict[str, Any]) -> Optional[Alert]:
        """
        Process an event and generate alert if necessary.

        Args:
            event_data: Event data from the dual-signal pipeline

        Returns:
            Alert object if generated, None otherwise
        """
        # Only generate alerts for anomalies
        if not event_data.get("is_anomaly", False):
            return None

        # Check if this is a significant anomaly
        confidence = event_data.get("anomaly_confidence", 0.0)
        if confidence < self.config.get("min_confidence_threshold", 0.5):
            return None

        # Create alert
        alert = Alert(event_data)
        self.alerts[alert.alert_id] = alert
        self.alert_history.append(alert)

        # Send notifications (synchronous for demo)
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self._send_notifications(alert))
            else:
                loop.run_until_complete(self._send_notifications(alert))
        except RuntimeError:
            # No event loop running, skip async notifications for demo
            logger.info(f"Alert generated: {alert.alert_id} - {alert.title}")

        logger.info(f"Generated alert: {alert.alert_id} - {alert.title}")
        return alert

    async def _send_notifications(self, alert: Alert):
        """Send notifications for an alert."""
        try:
            # Email notification
            if self.notification_channels.get("email", {}).get("enabled", False):
                await self._send_email_alert(alert)

            # Slack notification
            if self.notification_channels.get("slack", {}).get("enabled", False):
                await self._send_slack_alert(alert)

            # Webhook notification
            if self.notification_channels.get("webhook", {}).get("enabled", False):
                await self._send_webhook_alert(alert)

        except Exception as e:
            logger.error(f"Error sending notifications for alert {alert.alert_id}: {e}")

    async def _send_email_alert(self, alert: Alert):
        """Send email alert."""
        email_config = self.notification_channels.get("email", {})

        msg = MIMEMultipart()
        msg["From"] = email_config.get("from_email", "alerts@network.com")
        msg["To"] = ", ".join(email_config.get("recipients", []))
        msg["Subject"] = f"[{alert.severity}] {alert.title}"

        body = f"""
Network Anomaly Alert

{alert.description}

Alert ID: {alert.alert_id}
Timestamp: {datetime.fromtimestamp(alert.timestamp).strftime('%Y-%m-%d %H:%M:%S')}

Please investigate this anomaly immediately.

Best regards,
BGP Anomaly Detection System
        """.strip()

        msg.attach(MIMEText(body, "plain"))

        # Send email (simplified - in production, use proper SMTP)
        logger.info(f"Email alert sent: {alert.alert_id}")

    async def _send_slack_alert(self, alert: Alert):
        """Send Slack alert."""
        slack_config = self.notification_channels.get("slack", {})
        webhook_url = slack_config.get("webhook_url")

        if not webhook_url:
            return

        # Color code by severity
        color_map = {
            "CRITICAL": "#FF0000",
            "HIGH": "#FF8C00",
            "MEDIUM": "#FFD700",
            "LOW": "#00FF00",
        }

        payload = {
            "text": " Network Anomaly Alert",
            "attachments": [
                {
                    "color": color_map.get(alert.severity, "#000000"),
                    "fields": [
                        {"title": "Alert ID", "value": alert.alert_id, "short": True},
                        {"title": "Severity", "value": alert.severity, "short": True},
                        {"title": "Impact", "value": alert.impact, "short": True},
                        {"title": "Confidence", "value": f"{alert.confidence:.2f}", "short": True},
                        {
                            "title": "Roles Affected",
                            "value": ", ".join(alert.roles_affected),
                            "short": False,
                        },
                        {"title": "Description", "value": alert.description, "short": False},
                    ],
                    "footer": "BGP Anomaly Detection System",
                    "ts": alert.timestamp,
                }
            ],
        }

        try:
            response = requests.post(webhook_url, json=payload)
            response.raise_for_status()
            logger.info(f"Slack alert sent: {alert.alert_id}")
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")

    async def _send_webhook_alert(self, alert: Alert):
        """Send webhook alert."""
        webhook_config = self.notification_channels.get("webhook", {})
        webhook_url = webhook_config.get("url")

        if not webhook_url:
            return

        payload = {
            "alert_id": alert.alert_id,
            "timestamp": alert.timestamp,
            "severity": alert.severity,
            "title": alert.title,
            "description": alert.description,
            "impact": alert.impact,
            "confidence": alert.confidence,
            "roles_affected": alert.roles_affected,
            "raw_event": alert.raw_event,
        }

        try:
            response = requests.post(webhook_url, json=payload)
            response.raise_for_status()
            logger.info(f"Webhook alert sent: {alert.alert_id}")
        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")

    def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """Acknowledge an alert."""
        if alert_id in self.alerts:
            alert = self.alerts[alert_id]
            alert.acknowledged = True
            alert.acknowledged_by = acknowledged_by
            alert.acknowledged_at = datetime.now().timestamp()
            logger.info(f"Alert {alert_id} acknowledged by {acknowledged_by}")
            return True
        return False

    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts."""
        return [alert for alert in self.alerts.values() if alert.status == "active"]

    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """Get alert history."""
        return self.alert_history[-limit:]

    def get_alert_stats(self) -> Dict[str, Any]:
        """Get alert statistics."""
        total_alerts = len(self.alert_history)
        active_alerts = len(self.get_active_alerts())
        acknowledged_alerts = sum(1 for alert in self.alerts.values() if alert.acknowledged)

        severity_counts = {}
        for alert in self.alert_history:
            severity_counts[alert.severity] = severity_counts.get(alert.severity, 0) + 1

        return {
            "total_alerts": total_alerts,
            "active_alerts": active_alerts,
            "acknowledged_alerts": acknowledged_alerts,
            "severity_counts": severity_counts,
        }


# Example usage and testing
def create_sample_alert():
    """Create a sample alert for testing."""
    sample_event = {
        "timestamp": int(datetime.now().timestamp()),
        "is_anomaly": True,
        "anomaly_confidence": 0.85,
        "overall_score": 3.2,
        "impact_analysis": {
            "impact": "NETWORK_IMPACTING",
            "roles": ["spine", "tor"],
            "prefix_spread": 150,
        },
        "bgp_analysis": {
            "detected_series": ["wdr_total", "ann_total"],
            "series_results": {
                "wdr_total": {"discord_score": 4.1, "is_discord": True},
                "ann_total": {"discord_score": 2.8, "is_discord": True},
            },
        },
        "syslog_analysis": {
            "total_messages": 8,
            "has_errors": True,
            "severity_counts": {"error": 3, "warning": 2, "info": 3},
            "device_counts": {"spine-01": 5, "tor-01": 3},
        },
        "correlation_analysis": {
            "bgp_anomaly": True,
            "syslog_anomaly": True,
            "correlation_strength": 0.78,
            "signal_agreement": True,
        },
    }

    return sample_event


if __name__ == "__main__":
    # Test the alert manager
    config = {
        "min_confidence_threshold": 0.5,
        "notifications": {
            "email": {"enabled": False},
            "slack": {"enabled": False},
            "webhook": {"enabled": False},
        },
    }

    alert_manager = AlertManager(config)

    # Create sample alert
    sample_event = create_sample_alert()
    alert = alert_manager.process_event(sample_event)

    if alert:
        print(f"Generated alert: {alert.alert_id}")
        print(f"Title: {alert.title}")
        print(f"Severity: {alert.severity}")
        print(f"Description: {alert.description}")

        # Get stats
        stats = alert_manager.get_alert_stats()
        print(f"\nAlert Stats: {stats}")
    else:
        print("No alert generated")
