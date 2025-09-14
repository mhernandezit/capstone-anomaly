from graphviz import Digraph

dot = Digraph('BGP_Anomaly_Detection', filename='bgp_anomaly_uml.gv', format='png')
dot.attr(rankdir='TB', splines='ortho')  # Top-to-bottom layout with orthogonal edges

# Define nodes for the BGP anomaly detection system

# Start and Infrastructure
dot.node('start', '', shape='circle', style='filled', fillcolor='black')
dot.node('load_configs', 'Load Configurations:\nroles.yml & collector.yml', shape='box')
dot.node('start_nats', 'Start NATS Message Broker', shape='box')
dot.node('start_collector', 'Start BGP Collector (Go)', shape='box')
dot.node('start_pipeline', 'Start Python Pipeline', shape='box')
dot.node('start_dashboard', 'Start Streamlit Dashboard', shape='box')

# BGP Collector Flow
dot.node('init_gobgp', 'Initialize GoBGP Server', shape='box')
dot.node('add_peers', 'Add BGP Peers\n(ToR, Spine, Edge, RR)', shape='box')
dot.node('establish_sessions', 'Establish BGP Sessions', shape='box')
dot.node('session_check', 'BGP Sessions\nEstablished?', shape='diamond')
dot.node('session_fail', 'Session Establishment Failed\nRetry or Alert', shape='box', style='filled', fillcolor='orange')
dot.node('listen_updates', 'Listen for BGP Updates\n(Announcements/Withdrawals)', shape='box')
dot.node('parse_update', 'Parse BGP Update:\nPrefix, AS-Path, Peer', shape='box')
dot.node('publish_nats', 'Publish Parsed Update\nto NATS (bgp.updates)', shape='box')

# Feature Processing Flow
dot.node('consume_nats', 'Consume BGP Updates\nfrom NATS', shape='box')
dot.node('aggregate_features', 'Aggregate Features in Bins\n(30s windows)', shape='box')
dot.node('bin_ready', 'Feature Bin\nComplete?', shape='diamond')
dot.node('extract_features', 'Extract Features:\n• Announcements/Withdrawals\n• AS-Path Changes\n• Peer Activity', shape='box')

# Anomaly Detection Flow
dot.node('mp_detection', 'Matrix Profile Detection:\nCompute Discord Score', shape='box')
dot.node('anomaly_check', 'Anomaly Score >\nThreshold?', shape='diamond')
dot.node('normal_activity', 'Normal BGP Activity\nContinue Monitoring', shape='box', style='filled', fillcolor='lightgreen')

# Triage and Impact Assessment
dot.node('triage_analysis', 'Triage Analysis:\nClassify Impact Scope', shape='box')
dot.node('role_analysis', 'Analyze Affected Roles:\nToR, Spine, Edge, RR, Server', shape='box')
dot.node('prefix_analysis', 'Analyze Prefix Spread\n& Table Impact', shape='box')
dot.node('impact_decision', 'Impact Classification', shape='diamond')
dot.node('edge_local', 'EDGE_LOCAL:\nToR ↔ Server Issue\nLimited Blast Radius', shape='box', style='filled', fillcolor='yellow')
dot.node('network_impact', 'NETWORK_IMPACTING:\nWide-scale Failure\nMultiple Roles Affected', shape='box', style='filled', fillcolor='red')

# Dashboard and Alerting
dot.node('publish_event', 'Publish Event to\nDashboard Channel', shape='box')
dot.node('update_dashboard', 'Update Streamlit Dashboard:\n• Live Anomaly Score\n• Affected Prefixes/Roles\n• Explanation', shape='box')
dot.node('alert_check', 'Network Impact\nRequires Alert?', shape='diamond')
dot.node('send_alert', 'Send Network Alert\n(Critical)', shape='box', style='filled', fillcolor='red')
dot.node('log_event', 'Log Event\n(Informational)', shape='box')

# Continuous Operation
dot.node('continue_monitoring', 'Continue Monitoring\nfor Next Updates', shape='box')
dot.node('end', '', shape='circle', style='filled', fillcolor='black')

# Define edges for the main flow

# Initialization Flow
dot.edge('start', 'load_configs')
dot.edge('load_configs', 'start_nats')
dot.edge('start_nats', 'start_collector')
dot.edge('start_collector', 'start_pipeline')
dot.edge('start_pipeline', 'start_dashboard')

# BGP Collector Setup
dot.edge('start_dashboard', 'init_gobgp')
dot.edge('init_gobgp', 'add_peers')
dot.edge('add_peers', 'establish_sessions')
dot.edge('establish_sessions', 'session_check')
dot.edge('session_check', 'session_fail', label='No')
dot.edge('session_fail', 'establish_sessions', label='Retry')
dot.edge('session_check', 'listen_updates', label='Yes')

# BGP Update Processing
dot.edge('listen_updates', 'parse_update')
dot.edge('parse_update', 'publish_nats')
dot.edge('publish_nats', 'consume_nats')

# Feature Aggregation
dot.edge('consume_nats', 'aggregate_features')
dot.edge('aggregate_features', 'bin_ready')
dot.edge('bin_ready', 'aggregate_features', label='No\n(Continue)')
dot.edge('bin_ready', 'extract_features', label='Yes')

# Anomaly Detection
dot.edge('extract_features', 'mp_detection')
dot.edge('mp_detection', 'anomaly_check')
dot.edge('anomaly_check', 'normal_activity', label='No')
dot.edge('normal_activity', 'continue_monitoring')

# Triage Flow (when anomaly detected)
dot.edge('anomaly_check', 'triage_analysis', label='Yes')
dot.edge('triage_analysis', 'role_analysis')
dot.edge('role_analysis', 'prefix_analysis')
dot.edge('prefix_analysis', 'impact_decision')

# Impact Classification
dot.edge('impact_decision', 'edge_local', label='ToR/Server Only\n<100 Prefixes')
dot.edge('impact_decision', 'network_impact', label='Multiple Roles\n>100 Prefixes')

# Event Publishing and Alerting
dot.edge('edge_local', 'publish_event')
dot.edge('network_impact', 'publish_event')
dot.edge('publish_event', 'update_dashboard')
dot.edge('update_dashboard', 'alert_check')
dot.edge('alert_check', 'send_alert', label='Yes\n(Network Impact)')
dot.edge('alert_check', 'log_event', label='No\n(Edge Local)')
dot.edge('send_alert', 'continue_monitoring')
dot.edge('log_event', 'continue_monitoring')

# Continuous Loop
dot.edge('continue_monitoring', 'listen_updates', label='Next Update')

# End (for diagram completeness, though system runs continuously)
dot.edge('continue_monitoring', 'end', label='Shutdown', constraint='false', style='dashed')

# Add some styling for better visual organization
dot.attr('node', fontsize='10')
dot.attr('edge', fontsize='9')

# Render the diagram and view the result
dot.render(view=True)
print("BGP Anomaly Detection UML diagram created: bgp_anomaly_uml.gv.png")
