"""
Demo: Complete User Experience for BGP Anomaly Detection

This script demonstrates what network operators would see when using
the dual-signal BGP anomaly detection system.
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from python.alerting.alert_manager import AlertManager, create_sample_alert

def print_banner(title):
    """Print a formatted banner."""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)

def print_alert(alert):
    """Print a formatted alert."""
    print(f"\n🚨 ALERT: {alert.title}")
    print(f"   ID: {alert.alert_id}")
    print(f"   Severity: {alert.severity}")
    print(f"   Time: {datetime.fromtimestamp(alert.timestamp).strftime('%H:%M:%S')}")
    print(f"   Impact: {alert.impact}")
    print(f"   Confidence: {alert.confidence:.2f}")
    print(f"   Roles: {', '.join(alert.roles_affected)}")
    print(f"   Status: {'✅ Acknowledged' if alert.acknowledged else '⚠️ Active'}")

def simulate_network_operations():
    """Simulate a network operations center experience."""
    print_banner("🌐 Network Operations Center - BGP Anomaly Detection System")
    
    # Initialize alert manager
    config = {
        'min_confidence_threshold': 0.5,
        'notifications': {
            'email': {'enabled': True, 'recipients': ['noc@company.com']},
            'slack': {'enabled': True, 'webhook_url': 'https://hooks.slack.com/...'},
            'webhook': {'enabled': True, 'url': 'https://monitoring.company.com/alerts'}
        }
    }
    
    alert_manager = AlertManager(config)
    
    print("System Status: 🟢 Online")
    print("Monitoring: 2,000+ network devices")
    print("BGP Sessions: 1,200+ active")
    print("Detection Mode: Dual-Signal (BGP + Syslog)")
    print("GPU Acceleration: ✅ Enabled")
    
    # Simulate normal operation
    print_banner("📊 Normal Operation (10:00 AM - 10:15 AM)")
    print("✅ System monitoring 2,000+ devices")
    print("✅ Processing 1,200+ BGP sessions")
    print("✅ Matrix Profile analysis running")
    print("✅ No anomalies detected")
    print("✅ All systems green")
    
    time.sleep(2)
    
    # Simulate first anomaly
    print_banner("🚨 ANOMALY DETECTED (10:15:23 AM)")
    
    # Create sample event for ToR-Spine link failure
    link_failure_event = {
        'timestamp': int(datetime.now().timestamp()),
        'is_anomaly': True,
        'anomaly_confidence': 0.92,
        'overall_score': 4.2,
        'impact_analysis': {
            'impact': 'NETWORK_IMPACTING',
            'roles': ['spine', 'tor'],
            'prefix_spread': 150
        },
        'bgp_analysis': {
            'detected_series': ['wdr_total', 'ann_total'],
            'series_results': {
                'wdr_total': {'discord_score': 4.8, 'is_discord': True},
                'ann_total': {'discord_score': 3.1, 'is_discord': True}
            }
        },
        'syslog_analysis': {
            'total_messages': 12,
            'has_errors': True,
            'severity_counts': {'error': 5, 'warning': 3, 'info': 4},
            'device_counts': {'spine-01': 7, 'tor-01': 5}
        },
        'correlation_analysis': {
            'bgp_anomaly': True,
            'syslog_anomaly': True,
            'correlation_strength': 0.89,
            'signal_agreement': True
        }
    }
    
    # Process alert
    alert1 = alert_manager.process_event(link_failure_event)
    print_alert(alert1)
    
    print("\n📧 Email Notification Sent:")
    print("   To: noc@company.com")
    print("   Subject: [CRITICAL] Network-Wide Anomaly Detected - spine, tor")
    print("   Body: Link failure detected between spine-01 and tor-01...")
    
    print("\n💬 Slack Notification Sent:")
    print("   Channel: #network-alerts")
    print("   Message: 🚨 Network Anomaly Alert - CRITICAL severity")
    
    print("\n🔗 Webhook Notification Sent:")
    print("   URL: https://monitoring.company.com/alerts")
    print("   Status: 200 OK")
    
    time.sleep(3)
    
    # Simulate operator response
    print_banner("👨‍💻 Operator Response (10:15:45 AM)")
    print("Operator: John Smith")
    print("Action: Investigating spine-01 to tor-01 link")
    print("Status: Checking interface status...")
    
    # Acknowledge alert
    alert_manager.acknowledge_alert(alert1.alert_id, "John Smith")
    print(f"✅ Alert {alert1.alert_id} acknowledged by John Smith")
    
    time.sleep(2)
    
    # Simulate second anomaly
    print_banner("🚨 SECOND ANOMALY DETECTED (10:16:12 AM)")
    
    # Create sample event for BGP session reset
    bgp_reset_event = {
        'timestamp': int(datetime.now().timestamp()),
        'is_anomaly': True,
        'anomaly_confidence': 0.78,
        'overall_score': 3.1,
        'impact_analysis': {
            'impact': 'EDGE_LOCAL',
            'roles': ['tor'],
            'prefix_spread': 25
        },
        'bgp_analysis': {
            'detected_series': ['wdr_total'],
            'series_results': {
                'wdr_total': {'discord_score': 3.5, 'is_discord': True}
            }
        },
        'syslog_analysis': {
            'total_messages': 3,
            'has_errors': False,
            'severity_counts': {'warning': 2, 'info': 1},
            'device_counts': {'tor-02': 3}
        },
        'correlation_analysis': {
            'bgp_anomaly': True,
            'syslog_anomaly': False,
            'correlation_strength': 0.45,
            'signal_agreement': False
        }
    }
    
    alert2 = alert_manager.process_event(bgp_reset_event)
    print_alert(alert2)
    
    print("\n📊 Analysis:")
    print("   - BGP shows withdrawal spike")
    print("   - Syslog shows only warnings (no errors)")
    print("   - Impact: Edge-local (ToR only)")
    print("   - Confidence: Medium (0.78)")
    print("   - Action: Monitor, no immediate intervention needed")
    
    time.sleep(2)
    
    # Simulate resolution
    print_banner("✅ INCIDENT RESOLVED (10:18:30 AM)")
    print("Root Cause: Physical link failure between spine-01 and tor-01")
    print("Resolution: Replaced faulty SFP module")
    print("Impact: 150 prefixes affected for 3 minutes")
    print("MTTR: 3 minutes 7 seconds")
    
    # Show final stats
    print_banner("📈 Session Summary")
    stats = alert_manager.get_alert_stats()
    print(f"Total Alerts: {stats['total_alerts']}")
    print(f"Active Alerts: {stats['active_alerts']}")
    print(f"Acknowledged Alerts: {stats['acknowledged_alerts']}")
    print(f"Severity Breakdown: {stats['severity_counts']}")
    
    print("\n🎯 Key Metrics:")
    print("   - Detection Time: 23 seconds")
    print("   - False Positive Rate: 0%")
    print("   - Signal Correlation: 89%")
    print("   - Operator Response Time: 22 seconds")
    print("   - Resolution Time: 3 minutes 7 seconds")
    
    print_banner("🏆 System Performance")
    print("✅ Dual-signal approach working effectively")
    print("✅ GPU acceleration providing real-time analysis")
    print("✅ Topology-aware impact classification accurate")
    print("✅ Alert correlation reducing false positives")
    print("✅ Network operators can respond quickly and effectively")

def show_dashboard_preview():
    """Show what the dashboard would look like."""
    print_banner("🖥️ Dashboard Preview")
    
    print("┌─────────────────────────────────────────────────────────────┐")
    print("│  🔍 BGP Anomaly Detection Dashboard                        │")
    print("├─────────────────────────────────────────────────────────────┤")
    print("│  System Status: 🟢 Online    Uptime: 2h 15m                │")
    print("│  Events Processed: 1,247    Anomalies Detected: 2          │")
    print("├─────────────────────────────────────────────────────────────┤")
    print("│  📊 Recent Events Timeline                                 │")
    print("│  ●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●●● │")
    print("│  Normal  Anomaly  Normal  Anomaly  Normal                  │")
    print("│  10:00   10:15    10:16   10:16    10:18                   │")
    print("├─────────────────────────────────────────────────────────────┤")
    print("│  🚨 Active Alerts                                          │")
    print("│  ┌─────────────────────────────────────────────────────────┐ │")
    print("│  │ CRITICAL: Network-Wide Anomaly - spine, tor            │ │")
    print("│  │ Confidence: 0.92  Impact: NETWORK_IMPACTING            │ │")
    print("│  │ Status: ✅ Acknowledged by John Smith                  │ │")
    print("│  └─────────────────────────────────────────────────────────┘ │")
    print("│  ┌─────────────────────────────────────────────────────────┐ │")
    print("│  │ MEDIUM: Edge-Local Anomaly - tor                       │ │")
    print("│  │ Confidence: 0.78  Impact: EDGE_LOCAL                   │ │")
    print("│  │ Status: ⚠️ Active                                      │ │")
    print("│  └─────────────────────────────────────────────────────────┘ │")
    print("├─────────────────────────────────────────────────────────────┤")
    print("│  📝 Real-Time Syslog Monitor                              │")
    print("│  10:15:23 [spine-01] Interface GigabitEthernet0/0/1 down  │")
    print("│  10:15:24 [spine-01] OSPF neighbor 10.0.2.1 Down          │")
    print("│  10:15:25 [tor-01] Interface GigabitEthernet0/0/1 down    │")
    print("│  10:16:12 [tor-02] BGP neighbor 10.0.1.2 Down             │")
    print("└─────────────────────────────────────────────────────────────┘")

def main():
    """Run the complete user experience demo."""
    print("🎬 BGP Anomaly Detection - Complete User Experience Demo")
    print("This demo shows what network operators see when using the system")
    
    # Show dashboard preview
    show_dashboard_preview()
    
    # Simulate network operations
    simulate_network_operations()
    
    print_banner("🎉 Demo Complete")
    print("This demonstrates the complete user experience for network operators")
    print("using the dual-signal BGP anomaly detection system.")
    print("\nKey Benefits Demonstrated:")
    print("✅ Real-time anomaly detection with GPU acceleration")
    print("✅ Dual-signal validation reducing false positives")
    print("✅ Topology-aware impact classification")
    print("✅ Comprehensive alerting and notification system")
    print("✅ Intuitive dashboard for network operators")
    print("✅ Fast incident response and resolution")

if __name__ == "__main__":
    main()
