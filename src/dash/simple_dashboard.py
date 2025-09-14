"""
Simple Web Dashboard for BGP Anomaly Detection

A lightweight dashboard that shows the user experience without requiring
complex setup or external dependencies.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import json

# Configure Streamlit
st.set_page_config(
    page_title="BGP Anomaly Detection",
    page_icon="🔍",
    layout="wide"
)

def create_sample_data():
    """Create sample data for demonstration."""
    # Sample events
    events = [
        {
            'timestamp': datetime.now() - timedelta(minutes=30),
            'type': 'Normal',
            'confidence': 0.2,
            'impact': 'None',
            'roles': [],
            'bgp_score': 0.8,
            'syslog_messages': 2
        },
        {
            'timestamp': datetime.now() - timedelta(minutes=25),
            'type': 'Normal',
            'confidence': 0.3,
            'impact': 'None',
            'roles': [],
            'bgp_score': 1.1,
            'syslog_messages': 1
        },
        {
            'timestamp': datetime.now() - timedelta(minutes=20),
            'type': 'Normal',
            'confidence': 0.1,
            'impact': 'None',
            'roles': [],
            'bgp_score': 0.6,
            'syslog_messages': 3
        },
        {
            'timestamp': datetime.now() - timedelta(minutes=15),
            'type': 'Anomaly',
            'confidence': 0.92,
            'impact': 'NETWORK_IMPACTING',
            'roles': ['spine', 'tor'],
            'bgp_score': 4.2,
            'syslog_messages': 12
        },
        {
            'timestamp': datetime.now() - timedelta(minutes=10),
            'type': 'Anomaly',
            'confidence': 0.78,
            'impact': 'EDGE_LOCAL',
            'roles': ['tor'],
            'bgp_score': 3.1,
            'syslog_messages': 5
        },
        {
            'timestamp': datetime.now() - timedelta(minutes=5),
            'type': 'Normal',
            'confidence': 0.2,
            'impact': 'None',
            'roles': [],
            'bgp_score': 0.9,
            'syslog_messages': 2
        }
    ]
    
    # Sample syslog messages
    syslog_messages = [
        {
            'timestamp': datetime.now() - timedelta(minutes=15, seconds=30),
            'device': 'spine-01',
            'severity': 'error',
            'message': 'Interface GigabitEthernet0/0/1 is down'
        },
        {
            'timestamp': datetime.now() - timedelta(minutes=15, seconds=25),
            'device': 'spine-01',
            'severity': 'error',
            'message': 'OSPF neighbor 10.0.2.1 Down'
        },
        {
            'timestamp': datetime.now() - timedelta(minutes=15, seconds=20),
            'device': 'tor-01',
            'severity': 'error',
            'message': 'Interface GigabitEthernet0/0/1 is down'
        },
        {
            'timestamp': datetime.now() - timedelta(minutes=10, seconds=45),
            'device': 'tor-02',
            'severity': 'warning',
            'message': 'BGP neighbor 10.0.1.2 Down'
        },
        {
            'timestamp': datetime.now() - timedelta(minutes=5, seconds=30),
            'device': 'spine-01',
            'severity': 'info',
            'message': 'Interface GigabitEthernet0/0/1 is up'
        }
    ]
    
    return events, syslog_messages

def render_header():
    """Render the dashboard header."""
    st.title("🔍 BGP Anomaly Detection Dashboard")
    st.markdown("**Dual-Signal Network Failure Detection & Localization**")
    
    # Status indicators
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("System Status", " Online")
    
    with col2:
        st.metric("Uptime", "2h 15m")
    
    with col3:
        st.metric("Events Processed", "1,247")
    
    with col4:
        st.metric("Anomalies Detected", "2")

def render_metrics_overview():
    """Render key metrics overview."""
    st.subheader(" System Metrics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Anomaly Rate", "0.16%", delta="+0.02%")
    
    with col2:
        st.metric("Detection Accuracy", "94.2%", delta="+2.1%")
    
    with col3:
        st.metric("Avg Detection Time", "23.4s", delta="-5.2s")

def render_events_timeline(events):
    """Render events timeline."""
    st.subheader(" Recent Events Timeline")
    
    df = pd.DataFrame(events)
    
    # Timeline chart
    fig = px.scatter(
        df, 
        x='timestamp', 
        y='confidence',
        color='type',
        size='bgp_score',
        hover_data=['impact', 'roles', 'syslog_messages'],
        title="Event Timeline (Last 30 Minutes)"
    )
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

def render_anomaly_details(events):
    """Render anomaly details."""
    st.subheader(" Recent Anomalies")
    
    anomalies = [e for e in events if e['type'] == 'Anomaly']
    
    if not anomalies:
        st.info("No anomalies detected.")
        return
    
    for i, anomaly in enumerate(anomalies):
        with st.expander(f"Alert #{len(anomalies)-i} - {anomaly['timestamp'].strftime('%H:%M:%S')}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**BGP Analysis:**")
                st.write(f"- Confidence: {anomaly['confidence']:.2f}")
                st.write(f"- BGP Score: {anomaly['bgp_score']:.2f}")
                st.write(f"- Impact: {anomaly['impact']}")
                st.write(f"- Roles: {', '.join(anomaly['roles'])}")
            
            with col2:
                st.write("**Syslog Analysis:**")
                st.write(f"- Total Messages: {anomaly['syslog_messages']}")
                st.write(f"- Error Messages: 3")
                st.write(f"- Warning Messages: 2")
                st.write(f"- Devices Affected: spine-01, tor-01")
            
            # Correlation analysis
            st.write("**Signal Correlation:**")
            st.write(f"- BGP Anomaly: ✓ True")
            st.write(f"- Syslog Anomaly: ✓ True")
            st.write(f"- Correlation Strength: 0.89")
            st.write(f"- Signal Agreement: ✓ True")

def render_syslog_monitor(syslog_messages):
    """Render syslog monitor."""
    st.subheader("📝 Real-Time Syslog Monitor")
    
    for msg in reversed(syslog_messages[-10:]):  # Last 10 messages
        timestamp = msg['timestamp'].strftime('%H:%M:%S')
        device = msg['device']
        severity = msg['severity']
        message = msg['message']
        
        # Color code by severity
        if severity == 'error':
            st.error(f"**{timestamp}** [{device}] {message}")
        elif severity == 'warning':
            st.warning(f"**{timestamp}** [{device}] {message}")
        else:
            st.info(f"**{timestamp}** [{device}] {message}")

def render_system_status():
    """Render system status."""
    st.subheader("⚙️ System Status")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Component Status:**")
        st.write(" BGP Collector: Running")
        st.write(" Syslog Simulator: Running")
        st.write(" Matrix Profile Detector: Running")
        st.write(" GPU Acceleration: Active")
        st.write(" Dashboard: Active")
    
    with col2:
        st.write("**Performance Metrics:**")
        st.write("- Events/min: 42")
        st.write("- Memory Usage: 245 MB")
        st.write("- CPU Usage: 12%")
        st.write("- GPU Usage: 8%")
        st.write("- Detection Latency: 23.4s avg")

def render_alert_management():
    """Render alert management."""
    st.subheader("🔔 Alert Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Alert Settings:**")
        confidence_threshold = st.slider("Confidence Threshold", 0.0, 1.0, 0.7, 0.1)
        impact_filter = st.selectbox("Impact Filter", ["All", "EDGE_LOCAL", "NETWORK_IMPACTING"])
        
        if st.button("Test Alert"):
            st.success("Test alert sent!")
    
    with col2:
        st.write("**Notification Channels:**")
        email_enabled = st.checkbox("Email Notifications", value=True)
        slack_enabled = st.checkbox("Slack Notifications", value=False)
        webhook_enabled = st.checkbox("Webhook Notifications", value=False)
        
        if st.button("Save Settings"):
            st.success("Alert settings saved!")

def main():
    """Main dashboard function."""
    # Create sample data
    events, syslog_messages = create_sample_data()
    
    # Render dashboard
    render_header()
    st.divider()
    
    render_metrics_overview()
    st.divider()
    
    render_events_timeline(events)
    st.divider()
    
    render_anomaly_details(events)
    st.divider()
    
    render_syslog_monitor(syslog_messages)
    st.divider()
    
    render_system_status()
    st.divider()
    
    render_alert_management()
    
    # Auto-refresh
    time.sleep(5)
    st.rerun()

if __name__ == "__main__":
    main()
