"""
Network Anomaly Detection Dashboard
Comprehensive dashboard with topology visualization, live BGP/SNMP stats, and data graphs
"""

import streamlit as st
import asyncio
import json
import time
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import networkx as nx
import nats
from collections import defaultdict, deque
import queue

# Configure Streamlit page
st.set_page_config(
    page_title="Network Anomaly Detection Dashboard",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .topology-container {
        background-color: white;
        border: 1px solid #ddd;
        border-radius: 0.5rem;
        padding: 1rem;
    }
    .alert-banner {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .alert-critical {
        background-color: #ffebee;
        border-left: 4px solid #f44336;
        color: #c62828;
    }
    .alert-warning {
        background-color: #fff3e0;
        border-left: 4px solid #ff9800;
        color: #e65100;
    }
    .alert-info {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
        color: #1565c0;
    }
</style>
""", unsafe_allow_html=True)

class NetworkDataCollector:
    """Collects and processes network data from NATS"""
    
    def __init__(self):
        self.bgp_data = deque(maxlen=1000)
        self.snmp_data = deque(maxlen=1000)
        self.syslog_data = deque(maxlen=1000)
        self.anomalies = deque(maxlen=100)
        self.peer_stats = defaultdict(lambda: {
            'updates': 0, 'notifications': 0, 'keepalives': 0,
            'last_seen': None, 'status': 'active'
        })
        self.data_queue = queue.Queue()
        self.running = False
        
    async def start_collection(self):
        """Start collecting data from NATS"""
        self.running = True
        try:
            nc = await nats.connect('nats://localhost:4222')
            print("Connected to NATS for dashboard data collection")
            
            # Subscribe to BGP updates
            await nc.subscribe('bgp.updates', cb=self.handle_bgp_message)
            
            # Subscribe to SNMP data (if available)
            await nc.subscribe('snmp.metrics', cb=self.handle_snmp_message)
            
            # Subscribe to syslog data (if available)
            await nc.subscribe('syslog.messages', cb=self.handle_syslog_message)
            
            # Subscribe to anomalies
            await nc.subscribe('anomalies.detected', cb=self.handle_anomaly_message)
            
            # Keep running
            while self.running:
                await asyncio.sleep(0.1)
                
        except Exception as e:
            st.error(f"Error connecting to NATS: {e}")
            
    async def handle_bgp_message(self, msg):
        """Handle incoming BGP messages"""
        try:
            data = json.loads(msg.data.decode())
            timestamp = datetime.now()
            
            # Add to BGP data
            self.bgp_data.append({
                'timestamp': timestamp,
                'peer': data.get('peer', 'unknown'),
                'type': data.get('type', 'unknown'),
                'as_path': data.get('as_path', 'unknown'),
                'announce': data.get('announce', []),
                'withdraw': data.get('withdraw', []),
                'local_pref': data.get('local_pref', 0),
                'med': data.get('med', 0)
            })
            
            # Update peer statistics
            peer = data.get('peer', 'unknown')
            msg_type = data.get('type', 'unknown')
            if peer in self.peer_stats:
                self.peer_stats[peer]['last_seen'] = timestamp
                if msg_type in self.peer_stats[peer]:
                    self.peer_stats[peer][msg_type.lower()] += 1
                    
        except Exception as e:
            print(f"Error processing BGP message: {e}")
            
    async def handle_snmp_message(self, msg):
        """Handle incoming SNMP messages"""
        try:
            data = json.loads(msg.data.decode())
            self.snmp_data.append({
                'timestamp': datetime.now(),
                'device': data.get('device_id', 'unknown'),
                'metric': data.get('oid', 'unknown'),
                'value': data.get('value', 0),
                'metric_type': data.get('metric_type', 'unknown'),
                'severity': data.get('severity', 'info')
            })
        except Exception as e:
            print(f"Error processing SNMP message: {e}")
            
    async def handle_syslog_message(self, msg):
        """Handle incoming syslog messages"""
        try:
            data = json.loads(msg.data.decode())
            self.syslog_data.append({
                'timestamp': datetime.now(),
                'device': data.get('device', 'unknown'),
                'message': data.get('message', 'unknown'),
                'severity': data.get('severity', 'info'),
                'scenario': data.get('scenario', 'normal_operation')
            })
        except Exception as e:
            print(f"Error processing syslog message: {e}")
            
    async def handle_anomaly_message(self, msg):
        """Handle detected anomalies"""
        try:
            data = json.loads(msg.data.decode())
            self.anomalies.append({
                'timestamp': datetime.now(),
                'type': data.get('type', 'unknown'),
                'severity': data.get('severity', 'medium'),
                'peer': data.get('peer', 'unknown'),
                'description': data.get('description', 'Anomaly detected'),
                'confidence': data.get('confidence', 0.5)
            })
        except Exception as e:
            print(f"Error processing anomaly message: {e}")
            
    def stop_collection(self):
        """Stop data collection"""
        self.running = False

# Initialize data collector
if 'data_collector' not in st.session_state:
    st.session_state.data_collector = NetworkDataCollector()

# Main dashboard header
st.markdown('<h1 class="main-header">🌐 Network Anomaly Detection Dashboard</h1>', unsafe_allow_html=True)

# Sidebar controls
st.sidebar.header("Dashboard Controls")
auto_refresh = st.sidebar.checkbox("Auto Refresh", value=True)
refresh_interval = st.sidebar.slider("Refresh Interval (seconds)", 1, 30, 5)
show_topology = st.sidebar.checkbox("Show Network Topology", value=True)
show_alerts = st.sidebar.checkbox("Show Alerts", value=True)

# Start data collection if not running
if not st.session_state.data_collector.running:
    if st.sidebar.button("Start Data Collection"):
        asyncio.create_task(st.session_state.data_collector.start_collection())
        st.sidebar.success("Data collection started!")

# Main dashboard layout
col1, col2, col3, col4 = st.columns(4)

# Key metrics
with col1:
    st.metric(
        label="Active BGP Peers",
        value=len([p for p in st.session_state.data_collector.peer_stats.values() 
                  if p['last_seen'] and (datetime.now() - p['last_seen']).seconds < 60]),
        delta=None
    )

with col2:
    st.metric(
        label="BGP Updates/min",
        value=len([m for m in st.session_state.data_collector.bgp_data 
                  if (datetime.now() - m['timestamp']).seconds < 60]),
        delta=None
    )

with col3:
    st.metric(
        label="Anomalies Detected",
        value=len(st.session_state.data_collector.anomalies),
        delta=None
    )

with col4:
    st.metric(
        label="Network Devices",
        value=len(st.session_state.data_collector.snmp_data) if st.session_state.data_collector.snmp_data else 0,
        delta=None
    )

# Alerts section
if show_alerts and st.session_state.data_collector.anomalies:
    st.markdown("## 🚨 Recent Anomalies")
    
    for anomaly in list(st.session_state.data_collector.anomalies)[-5:]:
        severity_class = f"alert-{anomaly['severity']}"
        st.markdown(f"""
        <div class="alert-banner {severity_class}">
            <strong>{anomaly['type'].upper()}</strong> - {anomaly['description']}<br>
            <small>Peer: {anomaly['peer']} | Confidence: {anomaly['confidence']:.2f} | {anomaly['timestamp'].strftime('%H:%M:%S')}</small>
        </div>
        """, unsafe_allow_html=True)

# Network Topology Visualization
if show_topology:
    st.markdown("## 🗺️ Network Topology")
    
    # Create network graph
    G = nx.Graph()
    
    # Add nodes (peers)
    for peer, stats in st.session_state.data_collector.peer_stats.items():
        if stats['last_seen'] and (datetime.now() - stats['last_seen']).seconds < 300:
            status = 'active'
            color = '#4CAF50'  # Green for active
        else:
            status = 'inactive'
            color = '#F44336'  # Red for inactive
            
        G.add_node(peer, 
                  updates=stats['updates'],
                  notifications=stats['notifications'],
                  keepalives=stats['keepalives'],
                  status=status,
                  color=color)
    
    # Add edges (connections)
    for i, peer1 in enumerate(list(G.nodes())):
        for j, peer2 in enumerate(list(G.nodes())[i+1:], i+1):
            G.add_edge(peer1, peer2)
    
    # Create Plotly network visualization
    if G.nodes():
        pos = nx.spring_layout(G, k=3, iterations=50)
        
        edge_x = []
        edge_y = []
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
        
        edge_trace = go.Scatter(x=edge_x, y=edge_y,
                               line=dict(width=0.5, color='#888'),
                               hoverinfo='none',
                               mode='lines')
        
        node_x = []
        node_y = []
        node_text = []
        node_colors = []
        
        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_text.append(f"{node}<br>Updates: {G.nodes[node]['updates']}<br>Notifications: {G.nodes[node]['notifications']}")
            node_colors.append(G.nodes[node]['color'])
        
        node_trace = go.Scatter(x=node_x, y=node_y,
                               mode='markers+text',
                               hoverinfo='text',
                               text=[node.split('.')[-1] for node in G.nodes()],
                               textposition="middle center",
                               hovertext=node_text,
                               marker=dict(size=20,
                                         color=node_colors,
                                         line=dict(width=2)))
        
        fig = go.Figure(data=[edge_trace, node_trace],
                       layout=go.Layout(title='BGP Network Topology',
                                      titlefont_size=16,
                                      showlegend=False,
                                      hovermode='closest',
                                      margin=dict(b=20,l=5,r=5,t=40),
                                      annotations=[ dict(
                                          text="Active peers shown in green, inactive in red",
                                          showarrow=False,
                                          xref="paper", yref="paper",
                                          x=0.005, y=-0.002,
                                          xanchor='left', yanchor='bottom',
                                          font=dict(color="gray", size=12)
                                      )],
                                      xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                                      yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)))
        
        st.plotly_chart(fig, use_container_width=True)

# Data visualization section
st.markdown("## 📊 Network Statistics")

# Create tabs for different views
tab1, tab2, tab3, tab4, tab5 = st.tabs(["BGP Activity", "SNMP Metrics", "Syslog Messages", "Peer Details", "Anomaly Analysis"])

with tab1:
    st.markdown("### BGP Message Activity")
    
    if st.session_state.data_collector.bgp_data:
        # Create BGP activity chart
        bgp_df = pd.DataFrame(list(st.session_state.data_collector.bgp_data))
        bgp_df['time'] = bgp_df['timestamp'].dt.strftime('%H:%M:%S')
        
        # Count messages by type
        message_counts = bgp_df['type'].value_counts()
        
        fig = px.pie(values=message_counts.values, 
                    names=message_counts.index,
                    title="BGP Message Types Distribution")
        st.plotly_chart(fig, use_container_width=True)
        
        # Timeline chart
        timeline_data = bgp_df.groupby(['time', 'type']).size().reset_index(name='count')
        fig = px.line(timeline_data, x='time', y='count', color='type',
                     title="BGP Messages Over Time")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No BGP data available. Make sure data collection is running.")

with tab2:
    st.markdown("### SNMP Network Metrics")
    
    if st.session_state.data_collector.snmp_data:
        snmp_df = pd.DataFrame(list(st.session_state.data_collector.snmp_data))
        
        # Create SNMP metrics chart
        fig = px.bar(snmp_df, x='device', y='value', color='metric_type',
                    title="SNMP Metrics by Device")
        st.plotly_chart(fig, use_container_width=True)
        
        # Severity distribution
        severity_counts = snmp_df['severity'].value_counts()
        fig = px.pie(values=severity_counts.values, names=severity_counts.index,
                    title="SNMP Metric Severity Distribution")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No SNMP data available. Start the SNMP simulator to see metrics.")

with tab3:
    st.markdown("### Syslog Messages")
    
    if st.session_state.data_collector.syslog_data:
        syslog_df = pd.DataFrame(list(st.session_state.data_collector.syslog_data))
        
        # Recent syslog messages
        recent_syslog = syslog_df.tail(20)[['timestamp', 'device', 'severity', 'scenario', 'message']]
        st.dataframe(recent_syslog, use_container_width=True)
        
        # Severity distribution
        severity_counts = syslog_df['severity'].value_counts()
        fig = px.pie(values=severity_counts.values, names=severity_counts.index,
                    title="Syslog Severity Distribution")
        st.plotly_chart(fig, use_container_width=True)
        
        # Scenario distribution
        scenario_counts = syslog_df['scenario'].value_counts()
        fig = px.bar(x=scenario_counts.index, y=scenario_counts.values,
                    title="Syslog Scenarios")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No syslog data available. Start the syslog simulator to see messages.")

with tab4:
    st.markdown("### BGP Peer Details")
    
    if st.session_state.data_collector.peer_stats:
        peer_data = []
        for peer, stats in st.session_state.data_collector.peer_stats.items():
            peer_data.append({
                'Peer': peer,
                'Status': 'Active' if stats['last_seen'] and (datetime.now() - stats['last_seen']).seconds < 60 else 'Inactive',
                'Updates': stats['updates'],
                'Notifications': stats['notifications'],
                'Keepalives': stats['keepalives'],
                'Last Seen': stats['last_seen'].strftime('%H:%M:%S') if stats['last_seen'] else 'Never'
            })
        
        peer_df = pd.DataFrame(peer_data)
        st.dataframe(peer_df, use_container_width=True)
    else:
        st.info("No peer data available.")

with tab4:
    st.markdown("### Anomaly Analysis")
    
    if st.session_state.data_collector.anomalies:
        anomaly_df = pd.DataFrame(list(st.session_state.data_collector.anomalies))
        
        # Anomaly severity distribution
        severity_counts = anomaly_df['severity'].value_counts()
        fig = px.bar(x=severity_counts.index, y=severity_counts.values,
                    title="Anomaly Severity Distribution")
        st.plotly_chart(fig, use_container_width=True)
        
        # Confidence distribution
        fig = px.histogram(anomaly_df, x='confidence', bins=20,
                          title="Anomaly Detection Confidence Distribution")
        st.plotly_chart(fig, use_container_width=True)
        
        # Recent anomalies table
        st.markdown("### Recent Anomalies")
        recent_anomalies = anomaly_df.tail(10)[['timestamp', 'type', 'severity', 'peer', 'confidence', 'description']]
        st.dataframe(recent_anomalies, use_container_width=True)
    else:
        st.info("No anomalies detected yet.")

# Auto-refresh functionality
if auto_refresh:
    time.sleep(refresh_interval)
    st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.8rem;">
    Network Anomaly Detection Dashboard | Real-time BGP/SNMP Monitoring | Powered by Streamlit
</div>
""", unsafe_allow_html=True)
