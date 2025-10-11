#!/usr/bin/env python3
"""
Modern Network Anomaly Detection Dashboard

Real-time visualization of dual ML pipelines with animated topology and detection indicators.
Shows Matrix Profile (BGP) and Isolation Forest (SNMP) processing with network impact visualization.
"""

import json
import time
from collections import deque
from datetime import datetime, timedelta
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

# Page configuration
st.set_page_config(
    page_title="Network Anomaly Detection - Dual ML Pipeline",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .pipeline-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 0.5rem 0;
    }
    .bgp-pipeline {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    }
    .snmp-pipeline {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    }
    .alert-critical {
        background-color: #ff4444;
        color: white;
        padding: 1rem;
        border-radius: 5px;
        font-weight: bold;
        animation: pulse 2s infinite;
    }
    .alert-warning {
        background-color: #ffaa00;
        color: white;
        padding: 1rem;
        border-radius: 5px;
        font-weight: bold;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #1f77b4;
    }
    .processing {
        color: #00ff00;
        font-weight: bold;
        animation: blink 1s infinite;
    }
    @keyframes blink {
        0%, 50%, 100% { opacity: 1; }
        25%, 75% { opacity: 0.3; }
    }
</style>
""", unsafe_allow_html=True)


class DashboardState:
    """Manages dashboard state and data"""
    
    def __init__(self):
        # Network topology
        self.topology = self._create_topology()
        
        # ML Pipeline states
        self.bgp_processing = False
        self.snmp_processing = False
        
        # Detection history
        self.bgp_history = deque(maxlen=100)
        self.snmp_history = deque(maxlen=100)
        self.alerts = deque(maxlen=50)
        
        # Current anomalies
        self.current_anomalies = {}
        
        # Timeline data
        self.timeline_data = deque(maxlen=200)
        
    def _create_topology(self):
        """Create network topology graph with leaf-spine fabric plus servers"""
        G = nx.Graph()
        
        # Define devices with positions for visualization (4 spine, 6 ToR, 6 leaf, 12 servers)
        devices = {
            # Spine layer (top)
            "spine-01": {"role": "spine", "pos": (1.5, 6), "color": "#ff6b6b"},
            "spine-02": {"role": "spine", "pos": (3, 6), "color": "#ff6b6b"},
            "spine-03": {"role": "spine", "pos": (4.5, 6), "color": "#ff6b6b"},
            "spine-04": {"role": "spine", "pos": (6, 6), "color": "#ff6b6b"},
            
            # ToR layer (middle-upper)
            "tor-01": {"role": "tor", "pos": (0.5, 4), "color": "#4ecdc4"},
            "tor-02": {"role": "tor", "pos": (2, 4), "color": "#4ecdc4"},
            "tor-03": {"role": "tor", "pos": (3.5, 4), "color": "#4ecdc4"},
            "tor-04": {"role": "tor", "pos": (5, 4), "color": "#4ecdc4"},
            "tor-05": {"role": "tor", "pos": (6.5, 4), "color": "#4ecdc4"},
            "tor-06": {"role": "tor", "pos": (8, 4), "color": "#4ecdc4"},
            
            # Leaf layer (middle-lower)
            "leaf-01": {"role": "leaf", "pos": (0, 2), "color": "#95e1d3"},
            "leaf-02": {"role": "leaf", "pos": (1.5, 2), "color": "#95e1d3"},
            "leaf-03": {"role": "leaf", "pos": (3, 2), "color": "#95e1d3"},
            "leaf-04": {"role": "leaf", "pos": (4.5, 2), "color": "#95e1d3"},
            "leaf-05": {"role": "leaf", "pos": (6, 2), "color": "#95e1d3"},
            "leaf-06": {"role": "leaf", "pos": (7.5, 2), "color": "#95e1d3"},
            
            # Server layer (bottom) - 2 servers per leaf
            "server-01": {"role": "server", "pos": (-0.3, 0.3), "color": "#b8b8b8"},
            "server-02": {"role": "server", "pos": (0.3, 0.3), "color": "#b8b8b8"},
            "server-03": {"role": "server", "pos": (1.2, 0.3), "color": "#b8b8b8"},
            "server-04": {"role": "server", "pos": (1.8, 0.3), "color": "#b8b8b8"},
            "server-05": {"role": "server", "pos": (2.7, 0.3), "color": "#b8b8b8"},
            "server-06": {"role": "server", "pos": (3.3, 0.3), "color": "#b8b8b8"},
            "server-07": {"role": "server", "pos": (4.2, 0.3), "color": "#b8b8b8"},
            "server-08": {"role": "server", "pos": (4.8, 0.3), "color": "#b8b8b8"},
            "server-09": {"role": "server", "pos": (5.7, 0.3), "color": "#b8b8b8"},
            "server-10": {"role": "server", "pos": (6.3, 0.3), "color": "#b8b8b8"},
            "server-11": {"role": "server", "pos": (7.2, 0.3), "color": "#b8b8b8"},
            "server-12": {"role": "server", "pos": (7.8, 0.3), "color": "#b8b8b8"},
        }
        
        # Add nodes
        for device, attrs in devices.items():
            G.add_node(device, **attrs, status="normal", anomaly_score=0, 
                      blast_radius=0, affected_services=[])
        
        # Add connections
        connections = []
        
        # Spine to all ToR connections (full mesh)
        for spine in ["spine-01", "spine-02", "spine-03", "spine-04"]:
            for tor in ["tor-01", "tor-02", "tor-03", "tor-04", "tor-05", "tor-06"]:
                connections.append((spine, tor))
        
        # ToR to leaf connections (2 leafs per ToR)
        connections.extend([
            ("tor-01", "leaf-01"),
            ("tor-02", "leaf-01"),
            ("tor-02", "leaf-02"),
            ("tor-03", "leaf-02"),
            ("tor-03", "leaf-03"),
            ("tor-04", "leaf-03"),
            ("tor-04", "leaf-04"),
            ("tor-05", "leaf-04"),
            ("tor-05", "leaf-05"),
            ("tor-06", "leaf-05"),
            ("tor-06", "leaf-06"),
        ])
        
        # Leaf to server connections (2 servers per leaf)
        connections.extend([
            ("leaf-01", "server-01"),
            ("leaf-01", "server-02"),
            ("leaf-02", "server-03"),
            ("leaf-02", "server-04"),
            ("leaf-03", "server-05"),
            ("leaf-03", "server-06"),
            ("leaf-04", "server-07"),
            ("leaf-04", "server-08"),
            ("leaf-05", "server-09"),
            ("leaf-05", "server-10"),
            ("leaf-06", "server-11"),
            ("leaf-06", "server-12"),
        ])
        
        for src, dst in connections:
            G.add_edge(src, dst, status="normal")
        
        return G
    
    def mark_anomaly(self, device, source, confidence, blast_radius=0, affected_services=None):
        """Mark a device as having an anomaly with impact details"""
        if device in self.topology.nodes:
            self.topology.nodes[device]["status"] = "anomaly"
            self.topology.nodes[device]["anomaly_score"] = confidence
            self.topology.nodes[device]["blast_radius"] = blast_radius
            self.topology.nodes[device]["affected_services"] = affected_services or []
            
            # Calculate actual blast radius from topology
            if blast_radius == 0:
                blast_radius = self._calculate_blast_radius(device)
            
            self.current_anomalies[device] = {
                "source": source,
                "confidence": confidence,
                "timestamp": datetime.now(),
                "blast_radius": blast_radius,
                "affected_services": affected_services or ["routing", "transit"],
                "role": self.topology.nodes[device]["role"],
                "is_multimodal": False,  # Will be updated if both sources detect
            }
    
    def _calculate_blast_radius(self, device):
        """Calculate number of affected downstream devices"""
        # Count all devices reachable from this node
        if device not in self.topology.nodes:
            return 0
        
        role = self.topology.nodes[device]["role"]
        
        # Spine affects all ToR, leaf, and server devices
        if role == "spine":
            return len([n for n in self.topology.nodes 
                       if self.topology.nodes[n]["role"] in ["tor", "leaf", "server"]])
        
        # ToR affects connected leaf and server devices
        elif role == "tor":
            affected = 0
            for neighbor in self.topology.neighbors(device):
                if self.topology.nodes[neighbor]["role"] == "leaf":
                    affected += 1
                    # Count servers connected to this leaf
                    affected += len([n for n in self.topology.neighbors(neighbor)
                                   if self.topology.nodes[n]["role"] == "server"])
            return affected
        
        # Leaf affects connected servers
        elif role == "leaf":
            return len([n for n in self.topology.neighbors(device) 
                       if self.topology.nodes[n]["role"] == "server"])
        
        # Server affects only itself
        else:
            return 1
    
    def clear_anomalies(self):
        """Clear all anomaly markers"""
        for node in self.topology.nodes:
            self.topology.nodes[node]["status"] = "normal"
            self.topology.nodes[node]["anomaly_score"] = 0
        self.current_anomalies.clear()
    
    @staticmethod
    def get_layer_name(role):
        """Get human-readable layer name for device role"""
        layer_map = {
            "spine": "Layer 1 - Spine",
            "tor": "Layer 2 - Top-of-Rack",
            "leaf": "Layer 3 - Leaf",
            "server": "Layer 4 - Compute",
        }
        return layer_map.get(role, "Unknown Layer")


def create_topology_figure(state: DashboardState):
    """Create interactive topology visualization with anomaly indicators"""
    G = state.topology
    
    # Create edge traces
    edge_x = []
    edge_y = []
    edge_colors = []
    
    for edge in G.edges():
        x0, y0 = G.nodes[edge[0]]["pos"]
        x1, y1 = G.nodes[edge[1]]["pos"]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
        
        # Color edges based on connected nodes' status
        if (G.nodes[edge[0]]["status"] == "anomaly" or 
            G.nodes[edge[1]]["status"] == "anomaly"):
            edge_colors.extend(["#ff4444", "#ff4444", None])
        else:
            edge_colors.extend(["#888", "#888", None])
    
    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=3, color="#888"),
        hoverinfo="none",
        mode="lines",
        showlegend=False,
    )
    
    # Create node traces
    node_x = []
    node_y = []
    node_text = []
    node_colors = []
    node_sizes = []
    node_symbols = []
    
    for node in G.nodes():
        x, y = G.nodes[node]["pos"]
        node_x.append(x)
        node_y.append(y)
        
        role = G.nodes[node]["role"]
        status = G.nodes[node]["status"]
        anomaly_score = G.nodes[node]["anomaly_score"]
        
        # Node text
        if status == "anomaly":
            node_text.append(
                f"<b>{node}</b><br>"
                f"Role: {role}<br>"
                f"Status: ANOMALY<br>"
                f"Score: {anomaly_score:.2f}"
            )
        else:
            node_text.append(f"<b>{node}</b><br>Role: {role}<br>Status: Normal")
        
        # Node color based on status
        if status == "anomaly":
            node_colors.append("#ff4444")  # Red for anomaly
            node_sizes.append(60)  # Larger for anomaly
        else:
            node_colors.append(G.nodes[node]["color"])
            node_sizes.append(40)
        
        # Node symbol and size based on role
        if role == "spine":
            node_symbols.append("square")
        elif role == "tor":
            node_symbols.append("diamond")
        elif role == "leaf":
            node_symbols.append("circle")
        else:  # server
            node_symbols.append("circle")
            # Make servers smaller
            if status != "anomaly":
                node_sizes[-1] = 20
    
    # Create text labels (hide for servers to reduce clutter)
    node_labels = []
    for node in G.nodes():
        if G.nodes[node]["role"] == "server":
            node_labels.append("")  # No label for servers
        else:
            node_labels.append(node.split("-")[0])
    
    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode="markers+text",
        hoverinfo="text",
        hovertext=node_text,
        text=node_labels,
        textposition="middle center",
        textfont=dict(size=10, color="white", family="Arial Black"),
        marker=dict(
            size=node_sizes,
            color=node_colors,
            symbol=node_symbols,
            line=dict(width=2, color="white"),
        ),
        showlegend=False,
    )
    
    # Create figure
    fig = go.Figure(data=[edge_trace, node_trace])
    
    fig.update_layout(
        title={
            "text": "Network Topology - Real-time Anomaly Detection",
            "x": 0.5,
            "xanchor": "center",
            "font": {"size": 18, "color": "#333"},
        },
        showlegend=False,
        hovermode="closest",
        margin=dict(b=20, l=5, r=5, t=40),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor="rgba(240,240,240,0.5)",
        height=500,
    )
    
    return fig


def create_matrix_profile_visualization(history_data):
    """Create Matrix Profile (BGP) visualization"""
    if not history_data:
        # Create empty placeholder
        fig = go.Figure()
        fig.add_annotation(
            text="Waiting for BGP data...",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, color="gray"),
        )
        fig.update_layout(
            title="Matrix Profile - BGP Time Series Analysis",
            xaxis=dict(showgrid=False, showticklabels=False),
            yaxis=dict(showgrid=False, showticklabels=False),
            height=250,
        )
        return fig
    
    # Convert to dataframe
    df = pd.DataFrame(history_data)
    
    # Create subplot with time series and distance profile
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=("BGP Update Volume", "Matrix Profile Distance"),
        vertical_spacing=0.15,
        row_heights=[0.5, 0.5],
    )
    
    # Time series
    fig.add_trace(
        go.Scatter(
            x=df["timestamp"],
            y=df["value"],
            mode="lines",
            name="BGP Updates",
            line=dict(color="#f5576c", width=2),
        ),
        row=1, col=1,
    )
    
    # Distance profile
    fig.add_trace(
        go.Scatter(
            x=df["timestamp"],
            y=df["distance"],
            mode="lines",
            name="Distance",
            line=dict(color="#667eea", width=2),
            fill="tozeroy",
        ),
        row=2, col=1,
    )
    
    # Add threshold line
    fig.add_hline(
        y=2.5, line_dash="dash", line_color="red",
        annotation_text="Threshold",
        row=2, col=1,
    )
    
    # Highlight anomalies
    anomalies = df[df["is_anomaly"]]
    if not anomalies.empty:
        fig.add_trace(
            go.Scatter(
                x=anomalies["timestamp"],
                y=anomalies["distance"],
                mode="markers",
                name="Anomaly",
                marker=dict(size=12, color="red", symbol="x"),
            ),
            row=2, col=1,
        )
    
    fig.update_layout(
        height=300,
        showlegend=True,
        title_text="Matrix Profile - BGP Anomaly Detection",
    )
    
    return fig


def create_isolation_forest_visualization(history_data):
    """Create Isolation Forest (SNMP) visualization"""
    if not history_data:
        fig = go.Figure()
        fig.add_annotation(
            text="Waiting for SNMP data...",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, color="gray"),
        )
        fig.update_layout(
            title="Isolation Forest - SNMP Feature Space",
            xaxis=dict(showgrid=False, showticklabels=False),
            yaxis=dict(showgrid=False, showticklabels=False),
            height=250,
        )
        return fig
    
    df = pd.DataFrame(history_data)
    
    # Create 2D projection of feature space (PCA-like visualization)
    fig = go.Figure()
    
    # Normal points
    normal = df[~df["is_anomaly"]]
    if not normal.empty:
        fig.add_trace(go.Scatter(
            x=normal["feature_1"],
            y=normal["feature_2"],
            mode="markers",
            name="Normal",
            marker=dict(size=8, color="#4facfe", opacity=0.6),
        ))
    
    # Anomalies
    anomalies = df[df["is_anomaly"]]
    if not anomalies.empty:
        fig.add_trace(go.Scatter(
            x=anomalies["feature_1"],
            y=anomalies["feature_2"],
            mode="markers",
            name="Anomaly",
            marker=dict(
                size=15,
                color="#ff4444",
                symbol="x",
                line=dict(width=2, color="darkred"),
            ),
        ))
    
    fig.update_layout(
        title="Isolation Forest - SNMP Feature Space (2D Projection)",
        xaxis_title="CPU/Memory Metrics",
        yaxis_title="Interface/Temperature Metrics",
        height=300,
        showlegend=True,
        hovermode="closest",
    )
    
    return fig


def create_timeline_chart(timeline_data):
    """Create detection timeline chart"""
    if not timeline_data:
        return go.Figure()
    
    df = pd.DataFrame(timeline_data)
    
    fig = go.Figure()
    
    # BGP detections
    bgp_data = df[df["source"] == "BGP"]
    if not bgp_data.empty:
        fig.add_trace(go.Scatter(
            x=bgp_data["timestamp"],
            y=bgp_data["confidence"],
            mode="markers+lines",
            name="BGP Detections",
            marker=dict(size=10, color="#f5576c"),
            line=dict(width=2),
        ))
    
    # SNMP detections
    snmp_data = df[df["source"] == "SNMP"]
    if not snmp_data.empty:
        fig.add_trace(go.Scatter(
            x=snmp_data["timestamp"],
            y=snmp_data["confidence"],
            mode="markers+lines",
            name="SNMP Detections",
            marker=dict(size=10, color="#4facfe"),
            line=dict(width=2),
        ))
    
    fig.update_layout(
        title="Detection Timeline - Multi-Modal Correlation",
        xaxis_title="Time",
        yaxis_title="Confidence Score",
        height=250,
        showlegend=True,
        yaxis_range=[0, 1],
    )
    
    return fig


def load_evaluation_data():
    """Load data from evaluation framework results"""
    data_dir = Path("data/evaluation")
    
    # Load alerts
    alerts_file = data_dir / "alerts" / "alerts_log.jsonl"
    alerts = []
    
    if alerts_file.exists():
        with open(alerts_file) as f:
            for line in f:
                try:
                    alerts.append(json.loads(line))
                except:
                    pass
    
    return alerts


# Initialize session state
if "state" not in st.session_state:
    st.session_state.state = DashboardState()
    st.session_state.simulation_running = False
    st.session_state.current_scenario = None

# Main header
st.markdown('<h1 class="main-header">🔍 Network Anomaly Detection - Dual ML Pipeline</h1>', unsafe_allow_html=True)

# Sidebar controls
st.sidebar.header("Dashboard Controls")

# Scenario selection
scenario = st.sidebar.selectbox(
    "Select Failure Scenario",
    [
        "Normal Operation",
        "Link Failure (Multimodal)",
        "BGP Route Flapping",
        "Hardware Degradation",
        "Router Overload",
        "Server Failure",
    ],
)

# Start simulation
if st.sidebar.button("▶️ Start Simulation"):
    st.session_state.simulation_running = True
    st.session_state.current_scenario = scenario
    st.session_state.state.clear_anomalies()

if st.sidebar.button("⏹️ Stop Simulation"):
    st.session_state.simulation_running = False
    st.session_state.state.clear_anomalies()

if st.sidebar.button("🔄 Reset Dashboard"):
    st.session_state.state = DashboardState()
    st.session_state.simulation_running = False

# Auto-refresh toggle
auto_refresh = st.sidebar.checkbox("Auto-refresh", value=True)
refresh_rate = st.sidebar.slider("Refresh Rate (seconds)", 1, 10, 3)

st.sidebar.markdown("---")
st.sidebar.markdown("### ML Pipeline Status")

# Pipeline status indicators
col1, col2 = st.sidebar.columns(2)
with col1:
    if st.session_state.state.bgp_processing:
        st.markdown('<div class="processing">🔴 BGP</div>', unsafe_allow_html=True)
    else:
        st.markdown("⚪ BGP")

with col2:
    if st.session_state.state.snmp_processing:
        st.markdown('<div class="processing">🔴 SNMP</div>', unsafe_allow_html=True)
    else:
        st.markdown("⚪ SNMP")

# Main dashboard layout
# Row 1: Network Topology
st.markdown("## 🗺️ Network Topology - Leaf-Spine Fabric (28 Devices)")
st.caption("4 Spine Routers (red squares) | 6 ToR Switches (teal diamonds) | 6 Leaf Switches (green circles) | 12 Servers (gray)")
topology_fig = create_topology_figure(st.session_state.state)
st.plotly_chart(topology_fig, use_container_width=True, key="topology")

# Row 2: ML Pipelines
col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="pipeline-box bgp-pipeline"><h3>🔄 Matrix Profile Pipeline (BGP)</h3><p>Time-series discord detection for routing anomalies</p></div>', unsafe_allow_html=True)
    
    # Simulate BGP data if running
    if st.session_state.simulation_running and scenario != "Normal Operation":
        st.session_state.state.bgp_processing = True
        
        # Generate mock BGP data
        current_time = datetime.now()
        for i in range(5):
            st.session_state.state.bgp_history.append({
                "timestamp": current_time - timedelta(seconds=i*30),
                "value": np.random.normal(50, 10) if "BGP" in scenario or "Multimodal" in scenario else np.random.normal(20, 5),
                "distance": np.random.uniform(1, 4) if "BGP" in scenario or "Multimodal" in scenario else np.random.uniform(0.5, 1.5),
                "is_anomaly": ("BGP" in scenario or "Multimodal" in scenario) and i < 2,
            })
    
    bgp_fig = create_matrix_profile_visualization(list(st.session_state.state.bgp_history))
    st.plotly_chart(bgp_fig, use_container_width=True, key="bgp")

with col2:
    st.markdown('<div class="pipeline-box snmp-pipeline"><h3>🔄 Isolation Forest Pipeline (SNMP)</h3><p>Multi-dimensional outlier detection for hardware metrics</p></div>', unsafe_allow_html=True)
    
    # Simulate SNMP data if running
    if st.session_state.simulation_running and scenario != "Normal Operation":
        st.session_state.state.snmp_processing = True
        
        # Generate mock SNMP data
        for i in range(10):
            st.session_state.state.snmp_history.append({
                "feature_1": np.random.normal(0, 1),
                "feature_2": np.random.normal(0, 1) if "Hardware" not in scenario and "Multimodal" not in scenario else np.random.normal(3, 0.5),
                "is_anomaly": ("Hardware" in scenario or "Multimodal" in scenario) and i > 7,
            })
    
    snmp_fig = create_isolation_forest_visualization(list(st.session_state.state.snmp_history))
    st.plotly_chart(snmp_fig, use_container_width=True, key="snmp")

# Row 3: Timeline
st.markdown("## 📊 Detection Timeline")

# Simulate detections and store ground truth
if st.session_state.simulation_running and scenario != "Normal Operation":
    current_time = datetime.now()
    
    # Define scenario details with ground truth
    scenario_config = {
        "Link Failure (Multimodal)": {
            "device": "spine-01",
            "actual_failure": "Physical link failure on interface eth1",
            "failure_type": "Hardware - Link Down",
            "detectable_by": ["BGP", "SNMP"],
            "bgp_signature": "47 route withdrawals, peer session IDLE",
            "snmp_signature": "Interface error rate 0.02% → 45%, link state DOWN",
        },
        "BGP Route Flapping": {
            "device": "tor-01",
            "actual_failure": "BGP session instability causing route flapping",
            "failure_type": "Protocol - Routing Instability",
            "detectable_by": ["BGP"],
            "bgp_signature": "Periodic announcements/withdrawals every 30s",
            "snmp_signature": None,
        },
        "Hardware Degradation": {
            "device": "spine-02",
            "actual_failure": "Temperature spike and CPU overload",
            "failure_type": "Hardware - Environmental",
            "detectable_by": ["SNMP"],
            "bgp_signature": None,
            "snmp_signature": "Temperature 42°C → 78°C, CPU 30% → 95%",
        },
        "Router Overload": {
            "device": "leaf-01",
            "actual_failure": "CPU/memory exhaustion affecting routing",
            "failure_type": "Hardware - Resource Exhaustion",
            "detectable_by": ["BGP", "SNMP"],
            "bgp_signature": "Routing delays, increased UPDATE churn",
            "snmp_signature": "CPU 35% → 98%, Memory 45% → 92%",
        },
        "Server Failure": {
            "device": "server-05",
            "actual_failure": "Server crash - application unresponsive",
            "failure_type": "Compute - Service Failure",
            "detectable_by": [],  # Network devices don't directly detect server failures
            "bgp_signature": None,
            "snmp_signature": None,
        },
    }
    
    config = scenario_config.get(scenario, {})
    target_device = config.get("device", "tor-01")
    
    # Store ground truth in session state for display
    if "ground_truth" not in st.session_state:
        st.session_state.ground_truth = {}
    st.session_state.ground_truth = config
    
    # Add BGP detection
    if "BGP" in config.get("detectable_by", []):
        st.session_state.state.timeline_data.append({
            "timestamp": current_time,
            "source": "BGP",
            "confidence": np.random.uniform(0.7, 0.95),
            "device": target_device,
        })
        st.session_state.state.mark_anomaly(target_device, "BGP", 0.87)
    
    # Add SNMP detection
    if "SNMP" in config.get("detectable_by", []):
        st.session_state.state.timeline_data.append({
            "timestamp": current_time,
            "source": "SNMP",
            "confidence": np.random.uniform(0.75, 0.98),
            "device": target_device,
        })
        st.session_state.state.mark_anomaly(target_device, "SNMP", 0.91)
    
    # Mark as multimodal if both detected
    if len(config.get("detectable_by", [])) > 1 and target_device in st.session_state.state.current_anomalies:
        st.session_state.state.current_anomalies[target_device]["is_multimodal"] = True
        st.session_state.state.current_anomalies[target_device]["source"] = "BGP + SNMP"

timeline_fig = create_timeline_chart(list(st.session_state.state.timeline_data))
st.plotly_chart(timeline_fig, use_container_width=True, key="timeline")

# Row 4: Active Alerts with Detailed Information
st.markdown("## 🚨 Active Anomalies & Impact Assessment")

# Check if simulation is running but no detections (e.g., server failure)
if st.session_state.simulation_running and scenario != "Normal Operation" and not st.session_state.state.current_anomalies:
    st.warning("⚠️ No network-level anomalies detected")
    if hasattr(st.session_state, 'ground_truth') and st.session_state.ground_truth:
        gt = st.session_state.ground_truth
        st.info(f"""
        **Ground Truth**: {gt.get('failure_type', 'Unknown')}  
        **Device**: {gt.get('device', 'Unknown')}  
        **Description**: {gt.get('actual_failure', 'Unknown')}
        
        **Why no detection?** This failure type ({gt.get('failure_type', 'Unknown')}) is not observable through 
        network telemetry (BGP/SNMP). Server failures require application-level monitoring or health checks.
        """)

if st.session_state.state.current_anomalies:
    for device, info in st.session_state.state.current_anomalies.items():
        # Create alert card with detailed information
        with st.container():
            # Header row
            col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
            
            with col1:
                role_emoji = {"spine": "🔴", "tor": "🔷", "leaf": "🟢", "server": "⚪"}.get(info['role'], "⚪")
                st.markdown(f"### {role_emoji} {device}")
                st.caption(f"Role: {info['role'].upper()}")
            
            with col2:
                if info.get('is_multimodal', False):
                    st.markdown("**🔀 MULTIMODAL ALERT**")
                    st.caption("Both BGP + SNMP detected")
                else:
                    st.markdown(f"**Source:** {info['source']}")
                    st.caption("Single-source detection")
            
            with col3:
                st.metric("Confidence", f"{info['confidence']:.1%}", 
                         delta="High" if info['confidence'] > 0.85 else "Medium")
            
            with col4:
                st.markdown(f"**Detected:** {info['timestamp'].strftime('%H:%M:%S')}")
                elapsed = (datetime.now() - info['timestamp']).total_seconds()
                st.caption(f"{elapsed:.0f}s ago")
            
            # Impact details row
            st.markdown("---")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**📍 Impact Radius**")
                blast_radius = info.get('blast_radius', 0)
                if info['role'] == "spine":
                    st.error(f"⚠️ CRITICAL: {blast_radius} devices affected")
                    st.caption("Spine failure impacts entire fabric")
                elif info['role'] == "tor":
                    st.warning(f"⚠️ MODERATE: {blast_radius} leaf+server devices affected")
                    st.caption("ToR failure impacts connected leafs")
                elif info['role'] == "leaf":
                    st.warning(f"⚠️ LOW-MODERATE: {blast_radius} server(s) affected")
                    st.caption("Leaf failure impacts connected servers")
                else:
                    st.info(f"ℹ️ LOW: {blast_radius} server affected")
                    st.caption("Server failure localized")
            
            with col2:
                st.markdown("**🔧 Affected Services**")
                services = info.get('affected_services', ['routing', 'transit'])
                for service in services:
                    st.markdown(f"- {service.title()}")
            
            with col3:
                st.markdown("**🎯 Recommended Actions**")
                if info.get('is_multimodal', False):
                    st.markdown("1. Check physical link")
                    st.markdown("2. Verify interface status")
                    st.markdown("3. Review BGP sessions")
                elif info['source'] == "BGP":
                    st.markdown("1. Check BGP sessions")
                    st.markdown("2. Review route changes")
                else:
                    st.markdown("1. Check hardware metrics")
                    st.markdown("2. Review system logs")
            
            # Detailed evidence (expandable)
            with st.expander("🔍 View Detailed Evidence & Root Cause Analysis"):
                # Ground truth vs detected
                if hasattr(st.session_state, 'ground_truth') and st.session_state.ground_truth:
                    gt = st.session_state.ground_truth
                    st.markdown("### 📋 Ground Truth vs Detection")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**🎯 Actual Failure (Ground Truth)**")
                        st.markdown(f"- **Type**: {gt.get('failure_type', 'Unknown')}")
                        st.markdown(f"- **Description**: {gt.get('actual_failure', 'Unknown')}")
                        st.markdown(f"- **Target Device**: {gt.get('device', 'Unknown')}")
                        st.markdown(f"- **Detectable By**: {', '.join(gt.get('detectable_by', ['None']))}")
                    
                    with col2:
                        st.markdown("**🔍 Detected By ML Pipelines**")
                        detected_by = []
                        if info.get('is_multimodal', False):
                            detected_by = ["BGP (Matrix Profile)", "SNMP (Isolation Forest)"]
                        elif info['source'] == "BGP":
                            detected_by = ["BGP (Matrix Profile)"]
                        elif info['source'] == "SNMP":
                            detected_by = ["SNMP (Isolation Forest)"]
                        
                        for detector in detected_by:
                            st.markdown(f"- ✅ {detector}")
                        
                        if not detected_by:
                            st.markdown("- ⚠️ No ML detection (out of scope)")
                        
                        # Show expected vs actual
                        expected = set(gt.get('detectable_by', []))
                        actual = set(['BGP' if 'BGP' in info['source'] else None, 
                                     'SNMP' if 'SNMP' in info['source'] else None]) - {None}
                        
                        if expected == actual and expected:
                            st.success("✅ Detection matches ground truth")
                        elif not expected:
                            st.info("ℹ️ Failure not in detection scope")
                        else:
                            st.warning(f"⚠️ Partial detection: Expected {expected}, Got {actual}")
                    
                    st.markdown("---")
                    st.markdown("### 📊 Detection Signatures")
                    
                    if gt.get('bgp_signature'):
                        st.markdown(f"**BGP Signature**: {gt['bgp_signature']}")
                    if gt.get('snmp_signature'):
                        st.markdown(f"**SNMP Signature**: {gt['snmp_signature']}")
                    
                    st.markdown("---")
                
                # Detection evidence
                st.markdown("### 🔬 ML Detection Evidence")
                
                if info.get('is_multimodal', False):
                    st.markdown("**Multi-Modal Correlation Evidence:**")
                    st.markdown("- **BGP Signal**: Route withdrawals detected, peer session instability")
                    st.markdown("- **SNMP Signal**: Interface error rate spike, link state change")
                    st.markdown("- **Correlation**: Both signals within 15-second window")
                    st.markdown("- **Probable Root Cause**: Physical link failure (fiber cut or transceiver failure)")
                    st.markdown("- **Confidence Level**: HIGH (multi-modal confirmation)")
                elif info['source'] == "BGP":
                    st.markdown("**BGP-Only Detection Evidence:**")
                    st.markdown("- Route announcement/withdrawal pattern detected")
                    st.markdown("- Matrix Profile distance exceeded threshold (2.5σ)")
                    st.markdown("- **Probable Root Cause**: Routing protocol instability or configuration issue")
                elif "SNMP" in info['source']:
                    st.markdown("**SNMP-Only Detection Evidence:**")
                    st.markdown("- Hardware metrics outlier in 19-dimensional feature space")
                    st.markdown("- Isolation Forest anomaly score exceeded threshold")
                    st.markdown("- **Probable Root Cause**: Hardware degradation or environmental issue")
                
                st.markdown("---")
                st.markdown("### 🗺️ Topology & Impact Assessment")
                
                # Get topology info
                G = st.session_state.state.topology
                
                # Show device location in topology
                if device in G.nodes:
                    node = G.nodes[device]
                    neighbors = list(G.neighbors(device))
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**Device Information**")
                        st.markdown(f"- **Role**: {info['role'].upper()}")
                        st.markdown(f"- **Layer**: {st.session_state.state.get_layer_name(info['role'])}")
                        st.markdown(f"- **Connections**: {len(neighbors)} direct neighbors")
                        
                        # Show connected devices by role
                        neighbor_roles = {}
                        for n in neighbors:
                            n_role = G.nodes[n]['role']
                            neighbor_roles[n_role] = neighbor_roles.get(n_role, 0) + 1
                        
                        if neighbor_roles:
                            st.markdown("- **Connected to**:")
                            for role, count in neighbor_roles.items():
                                st.markdown(f"  - {count} {role}(s)")
                    
                    with col2:
                        st.markdown("**Impact Analysis**")
                        st.markdown(f"- **Blast Radius**: {info.get('blast_radius', 0)} devices")
                        priority = {"spine": "P1 CRITICAL", "tor": "P2 HIGH", "leaf": "P3 MEDIUM", "server": "P4 LOW"}.get(info['role'], "P4 LOW")
                        st.markdown(f"- **Priority**: {priority}")
                        
                        # Calculate and show affected roles
                        if info['role'] == 'spine':
                            st.markdown("- **Affected Layers**: All downstream (ToR, Leaf, Servers)")
                        elif info['role'] == 'tor':
                            st.markdown("- **Affected Layers**: Leaf switches and Servers")
                        elif info['role'] == 'leaf':
                            st.markdown("- **Affected Layers**: Connected Servers only")
                        else:
                            st.markdown("- **Affected Layers**: Local services only")
                        
                        # Redundancy check
                        if info['role'] in ['spine', 'tor']:
                            st.markdown(f"- **Redundancy**: Available (multiple {info['role']}s)")
                        else:
                            st.markdown("- **Redundancy**: Limited or none")
            
            # Critical alert banner
            if info['role'] == "spine" or info.get('is_multimodal', False):
                st.markdown(
                    '<div class="alert-critical">⚠️ CRITICAL ALERT: Immediate escalation required - '
                    f'Contact Network Operations Team</div>',
                    unsafe_allow_html=True
                )
            
            st.markdown("---")
else:
    st.success("✅ No active anomalies detected. System operating normally.")
    st.info("All devices healthy. Network topology stable.")

# Row 5: Metrics
st.markdown("## 📈 System Performance")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("BGP Detections", len([d for d in st.session_state.state.timeline_data if d.get("source") == "BGP"]))

with col2:
    st.metric("SNMP Detections", len([d for d in st.session_state.state.timeline_data if d.get("source") == "SNMP"]))

with col3:
    st.metric("Active Anomalies", len(st.session_state.state.current_anomalies))

with col4:
    st.metric("Correlation Rate", "100%" if len(st.session_state.state.current_anomalies) > 1 else "N/A")

# Auto-refresh
if auto_refresh and st.session_state.simulation_running:
    time.sleep(refresh_rate)
    st.rerun()

# Footer
st.markdown("---")
st.markdown(
    '<div style="text-align: center; color: #666; font-size: 0.9rem;">'
    'Network Anomaly Detection System | Matrix Profile + Isolation Forest | Real-time Multi-Modal Correlation'
    '</div>',
    unsafe_allow_html=True,
)

