#!/usr/bin/env python3
"""
Alert Logger - Logs detection alerts for evaluation and monitoring
"""

import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)


@dataclass
class Alert:
    """Structured alert with full context."""

    timestamp: float
    datetime_iso: str
    alert_id: str
    alert_type: str
    confidence: float

    # Detection details
    detection_sources: list  # ["bgp", "snmp", "syslog"]
    bgp_score: float
    snmp_score: float
    syslog_score: float

    # Location
    predicted_location: Dict
    ranked_predictions: list
    topology_role: str

    # Impact
    severity: str
    blast_radius: Dict
    criticality: Dict

    # Actions
    recommended_actions: list


class AlertLogger:
    """Logs alerts to JSONL file for evaluation and operations."""

    def __init__(self, log_file="data/alerts/alerts_log.jsonl"):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.alert_count = 0
        logger.info(f"AlertLogger initialized: {self.log_file}")

    def log_alert(self, alert_data: Dict[str, Any]) -> str:
        """
        Log an alert to JSONL file.

        Args:
            alert_data: Alert information dictionary

        Returns:
            alert_id: Generated alert ID
        """
        self.alert_count += 1
        alert_id = f"alert_{self.alert_count:04d}"

        # Create log entry
        log_entry = {
            "timestamp": time.time(),
            "datetime": datetime.now().isoformat(),
            "alert_id": alert_id,
            **alert_data,
        }

        # Write to JSONL
        with open(self.log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

        logger.info(f"Alert logged: {alert_id} - {alert_data.get('alert_type')}")

        return alert_id

    def clear_logs(self):
        """Clear alert logs (for testing)."""
        if self.log_file.exists():
            self.log_file.unlink()
        self.alert_count = 0
        logger.info("Alert logs cleared")
