#!/usr/bin/env python3
"""
Example integration of topology triage system with ML detection pipeline.

This script demonstrates how to integrate the topology triage system
with the existing ML detection pipeline components.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any

from anomaly_detection.triage import TopologyTriageSystem
from anomaly_detection.topology import DeviceRole, FailureDomain

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MLPipelineIntegration:
    """
    Example integration class showing how to integrate topology triage
    with the ML detection pipeline.
    """

    def __init__(self, roles_config: str = "config/roles.yml", topology_config: str = "evaluation/topology.yml"):
        """
        Initialize the integrated pipeline.
        
        Args:
            roles_config: Path to device roles configuration
            topology_config: Path to network topology configuration
        """
        self.triage_system = TopologyTriageSystem(roles_config, topology_config)
        logger.info("ML Pipeline Integration initialized")

    def process_bgp_detection(self, bgp_detection: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process BGP Matrix Profile detection through topology triage.
        
        Args:
            bgp_detection: BGP anomaly detection result
            
        Returns:
            Enriched detection result with topology analysis
        """
        logger.info(f"Processing BGP detection for device: {bgp_detection.get('device', 'unknown')}")
        
        # Extract detection data
        anomaly_data = {
            "alert_type": bgp_detection.get("anomaly_type", "bgp_flapping"),
            "confidence": bgp_detection.get("confidence", 0.0),
            "sources": ["bgp"],
        }
        
        detected_location = bgp_detection.get("detected_location", {})
        
        # Perform topology triage analysis
        triage_result = self.triage_system.analyze(anomaly_data, detected_location)
        
        # Enrich the detection result
        enriched_result = {
            **bgp_detection,
            "triage_analysis": {
                "primary_location": {
                    "device": triage_result.location.device,
                    "interface": triage_result.location.interface,
                    "bgp_peer": triage_result.location.bgp_peer,
                    "topology_role": triage_result.location.topology_role.value if triage_result.location.topology_role else None,
                    "confidence": triage_result.location.confidence,
                },
                "ranked_predictions": [
                    {
                        "device": pred.device,
                        "topology_role": pred.topology_role.value if pred.topology_role else None,
                        "confidence": pred.confidence,
                    }
                    for pred in triage_result.ranked_predictions
                ],
                "blast_radius": {
                    "affected_devices": triage_result.blast_radius.affected_devices,
                    "affected_services": triage_result.blast_radius.affected_services,
                    "downstream_devices": triage_result.blast_radius.downstream_devices,
                    "redundancy_available": triage_result.blast_radius.redundancy_available,
                    "spof": triage_result.blast_radius.spof,
                    "failure_domain": triage_result.blast_radius.failure_domain.value,
                    "impact_score": triage_result.blast_radius.impact_score,
                },
                "criticality": {
                    "score": triage_result.criticality.score,
                    "priority": triage_result.criticality.priority.value,
                    "factors": triage_result.criticality.factors,
                    "sla_breach_likely": triage_result.criticality.sla_breach_likely,
                    "time_to_breach_min": triage_result.criticality.time_to_breach_min,
                },
                "severity": triage_result.severity.value,
            },
        }
        
        return enriched_result

    def process_snmp_detection(self, snmp_detection: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process SNMP Isolation Forest detection through topology triage.
        
        Args:
            snmp_detection: SNMP anomaly detection result
            
        Returns:
            Enriched detection result with topology analysis
        """
        logger.info(f"Processing SNMP detection for device: {snmp_detection.get('device', 'unknown')}")
        
        # Extract detection data
        anomaly_data = {
            "alert_type": snmp_detection.get("anomaly_type", "hardware_degradation"),
            "confidence": snmp_detection.get("confidence", 0.0),
            "sources": ["snmp"],
        }
        
        detected_location = snmp_detection.get("detected_location", {})
        
        # Perform topology triage analysis
        triage_result = self.triage_system.analyze(anomaly_data, detected_location)
        
        # Enrich the detection result (same structure as BGP)
        enriched_result = {
            **snmp_detection,
            "triage_analysis": {
                "primary_location": {
                    "device": triage_result.location.device,
                    "interface": triage_result.location.interface,
                    "topology_role": triage_result.location.topology_role.value if triage_result.location.topology_role else None,
                    "confidence": triage_result.location.confidence,
                },
                "blast_radius": {
                    "affected_devices": triage_result.blast_radius.affected_devices,
                    "affected_services": triage_result.blast_radius.affected_services,
                    "downstream_devices": triage_result.blast_radius.downstream_devices,
                    "redundancy_available": triage_result.blast_radius.redundancy_available,
                    "spof": triage_result.blast_radius.spof,
                    "failure_domain": triage_result.blast_radius.failure_domain.value,
                    "impact_score": triage_result.blast_radius.impact_score,
                },
                "criticality": {
                    "score": triage_result.criticality.score,
                    "priority": triage_result.criticality.priority.value,
                    "factors": triage_result.criticality.factors,
                    "sla_breach_likely": triage_result.criticality.sla_breach_likely,
                    "time_to_breach_min": triage_result.criticality.time_to_breach_min,
                },
                "severity": triage_result.severity.value,
            },
        }
        
        return enriched_result

    def process_multimodal_detection(self, bgp_detection: Dict[str, Any], snmp_detection: Dict[str, Any], correlator_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process multimodal correlated detection through topology triage.
        
        Args:
            bgp_detection: BGP anomaly detection result
            snmp_detection: SNMP anomaly detection result
            correlator_data: Multimodal correlator analysis
            
        Returns:
            Enriched multimodal detection result with topology analysis
        """
        logger.info("Processing multimodal correlated detection")
        
        # Extract detection data
        anomaly_data = {
            "alert_type": "multimodal_correlated",
            "confidence": max(
                bgp_detection.get("confidence", 0.0),
                snmp_detection.get("confidence", 0.0)
            ),
            "sources": ["bgp", "snmp"],
        }
        
        # Use the higher confidence location
        bgp_location = bgp_detection.get("detected_location", {})
        snmp_location = snmp_detection.get("detected_location", {})
        
        if bgp_detection.get("confidence", 0.0) >= snmp_detection.get("confidence", 0.0):
            detected_location = bgp_location
        else:
            detected_location = snmp_location
        
        # Perform topology triage analysis with correlator data
        triage_result = self.triage_system.analyze(anomaly_data, detected_location, correlator_data)
        
        # Enrich the multimodal detection result
        enriched_result = {
            "correlation_id": correlator_data.get("correlation_id", "unknown"),
            "timestamp": correlator_data.get("timestamp", 0),
            "bgp_detection": bgp_detection,
            "snmp_detection": snmp_detection,
            "correlator_data": correlator_data,
            "triage_analysis": {
                "primary_location": {
                    "device": triage_result.location.device,
                    "interface": triage_result.location.interface,
                    "bgp_peer": triage_result.location.bgp_peer,
                    "topology_role": triage_result.location.topology_role.value if triage_result.location.topology_role else None,
                    "confidence": triage_result.location.confidence,
                },
                "ranked_predictions": [
                    {
                        "device": pred.device,
                        "topology_role": pred.topology_role.value if pred.topology_role else None,
                        "confidence": pred.confidence,
                    }
                    for pred in triage_result.ranked_predictions
                ],
                "blast_radius": {
                    "affected_devices": triage_result.blast_radius.affected_devices,
                    "affected_services": triage_result.blast_radius.affected_services,
                    "downstream_devices": triage_result.blast_radius.downstream_devices,
                    "redundancy_available": triage_result.blast_radius.redundancy_available,
                    "spof": triage_result.blast_radius.spof,
                    "failure_domain": triage_result.blast_radius.failure_domain.value,
                    "impact_score": triage_result.blast_radius.impact_score,
                },
                "criticality": {
                    "score": triage_result.criticality.score,
                    "priority": triage_result.criticality.priority.value,
                    "factors": triage_result.criticality.factors,
                    "sla_breach_likely": triage_result.criticality.sla_breach_likely,
                    "time_to_breach_min": triage_result.criticality.time_to_breach_min,
                },
                "severity": triage_result.severity.value,
            },
        }
        
        return enriched_result

    def generate_alert_summary(self, enriched_detection: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a concise alert summary for operational teams.
        
        Args:
            enriched_detection: Enriched detection result with triage analysis
            
        Returns:
            Concise alert summary
        """
        triage = enriched_detection.get("triage_analysis", {})
        location = triage.get("primary_location", {})
        blast_radius = triage.get("blast_radius", {})
        criticality = triage.get("criticality", {})
        
        summary = {
            "alert_id": enriched_detection.get("alert_id", "unknown"),
            "timestamp": enriched_detection.get("timestamp", 0),
            "severity": triage.get("severity", "unknown"),
            "priority": criticality.get("priority", "P3"),
            "device": location.get("device", "unknown"),
            "interface": location.get("interface"),
            "topology_role": location.get("topology_role"),
            "spof": blast_radius.get("spof", False),
            "affected_devices": blast_radius.get("affected_devices", 0),
            "failure_domain": blast_radius.get("failure_domain", "unknown"),
            "sla_breach_likely": criticality.get("sla_breach_likely", False),
            "time_to_breach_min": criticality.get("time_to_breach_min"),
            "criticality_score": criticality.get("score", 0.0),
        }
        
        return summary


def main():
    """Example usage of the ML pipeline integration."""
    
    # Initialize the integration
    pipeline = MLPipelineIntegration()
    
    # Example BGP detection
    bgp_detection = {
        "alert_id": "bgp_001",
        "timestamp": 1234567890,
        "anomaly_type": "bgp_flapping",
        "confidence": 0.85,
        "detected_location": {
            "device": "spine-01",
            "interface": "eth0",
            "bgp_peer": "tor-01",
            "confidence": 0.75,
        },
        "features": {
            "announcement_rate": 150.0,
            "withdrawal_rate": 25.0,
        },
    }
    
    # Process BGP detection
    enriched_bgp = pipeline.process_bgp_detection(bgp_detection)
    bgp_summary = pipeline.generate_alert_summary(enriched_bgp)
    
    print("BGP Detection Analysis:")
    print(json.dumps(bgp_summary, indent=2))
    
    # Example SNMP detection
    snmp_detection = {
        "alert_id": "snmp_001",
        "timestamp": 1234567895,
        "anomaly_type": "hardware_degradation",
        "confidence": 0.78,
        "detected_location": {
            "device": "tor-01",
            "interface": "eth0",
            "confidence": 0.70,
        },
        "features": {
            "cpu_utilization": 95.2,
            "temperature": 85.3,
        },
    }
    
    # Process SNMP detection
    enriched_snmp = pipeline.process_snmp_detection(snmp_detection)
    snmp_summary = pipeline.generate_alert_summary(enriched_snmp)
    
    print("\nSNMP Detection Analysis:")
    print(json.dumps(snmp_summary, indent=2))
    
    # Example multimodal correlation
    correlator_data = {
        "correlation_id": "corr_001",
        "timestamp": 1234567900,
        "correlation_strength": 0.90,
        "affected_devices": ["spine-01", "tor-01"],
        "affected_services": ["east_west_traffic", "rack_connectivity"],
    }
    
    # Process multimodal detection
    enriched_multimodal = pipeline.process_multimodal_detection(
        bgp_detection, snmp_detection, correlator_data
    )
    multimodal_summary = pipeline.generate_alert_summary(enriched_multimodal)
    
    print("\nMultimodal Detection Analysis:")
    print(json.dumps(multimodal_summary, indent=2))


if __name__ == "__main__":
    main()
