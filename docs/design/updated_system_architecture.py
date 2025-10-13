from graphviz import Digraph


def create_updated_system_architecture():
    """
    Create a simplified, clearer system architecture diagram for presentation
    Focuses on multi-modal data flow and key components
    """

    dot = Digraph(
        "Multi_Modal_System_Architecture",
        filename="docs/design/updated_system_architecture.gv",
        format="png",
    )
    dot.attr(rankdir="TB", splines="polyline", size="10,12")
    dot.attr("node", fontname="Arial", fontsize="11", width="2.5", height="1")
    dot.attr("edge", fontname="Arial", fontsize="9")

    # Title
    dot.node(
        "title",
        "Multi-Modal Network Anomaly Detection System\nBGP + SNMP + Syslog Integration",
        shape="box",
        style="filled",
        fillcolor="lightblue",
        fontsize="14",
    )

    # Data Sources Layer
    with dot.subgraph(name="cluster_data_sources") as sources:
        sources.attr(label="Data Sources", style="filled", fillcolor="lightcyan", fontsize="12")
        sources.node(
            "bgp_source",
            "BGP Updates\n(BMP Collector)",
            shape="box",
            style="filled",
            fillcolor="lightgreen",
        )
        sources.node(
            "snmp_source",
            "SNMP Metrics\n(Hardware Health)",
            shape="box",
            style="filled",
            fillcolor="lightyellow",
        )
        sources.node(
            "syslog_source",
            "Syslog Messages\n(Device Events)",
            shape="box",
            style="filled",
            fillcolor="lightcoral",
        )

    # Message Bus
    dot.node(
        "nats_bus",
        "NATS Message Bus\n(Real-time Streaming)",
        shape="ellipse",
        style="filled",
        fillcolor="lightsteelblue",
        fontsize="12",
    )

    # Processing Layer
    with dot.subgraph(name="cluster_processing") as processing:
        processing.attr(
            label="ML Processing Pipeline", style="filled", fillcolor="mistyrose", fontsize="12"
        )
        processing.node(
            "feature_extraction",
            "Multi-Modal\nFeature Extraction",
            shape="box",
            style="filled",
            fillcolor="wheat",
        )
        processing.node(
            "anomaly_detection",
            "Anomaly Detection\n(Matrix Profile +\nIsolation Forest)",
            shape="box",
            style="filled",
            fillcolor="orange",
        )
        processing.node(
            "multimodal_fusion",
            "Multi-Modal Fusion\n(Correlation Engine)",
            shape="box",
            style="filled",
            fillcolor="gold",
        )
        processing.node(
            "topology_triage",
            "Topology-Aware Triage\n(Impact Assessment)",
            shape="box",
            style="filled",
            fillcolor="lightgreen",
        )

    # Output Layer
    with dot.subgraph(name="cluster_output") as output:
        output.attr(label="Output & Response", style="filled", fillcolor="lavender", fontsize="12")
        output.node(
            "alerts",
            "Enriched Alerts\n(Root Cause +\nRecommendations)",
            shape="box",
            style="filled",
            fillcolor="lightcoral",
        )
        output.node(
            "operator",
            "Network Operator\n(Decision Maker)",
            shape="box",
            style="filled",
            fillcolor="lightskyblue",
        )

    # Data flow connections
    dot.edge("title", "bgp_source", style="invis")

    # Sources to message bus
    dot.edge("bgp_source", "nats_bus", label="bgp.updates")
    dot.edge("snmp_source", "nats_bus", label="snmp.metrics")
    dot.edge("syslog_source", "nats_bus", label="syslog.messages")

    # Message bus to processing
    dot.edge("nats_bus", "feature_extraction", label="Multi-Modal Data")

    # Processing pipeline
    dot.edge("feature_extraction", "anomaly_detection", label="Feature Vectors")
    dot.edge("anomaly_detection", "multimodal_fusion", label="Anomaly Scores\n(BGP + SNMP)")
    dot.edge("multimodal_fusion", "topology_triage", label="Correlated\nDetections")
    
    # Processing to output
    dot.edge("topology_triage", "alerts", label="Enriched Context\n(Impact + Root Cause)")
    dot.edge("alerts", "operator", label="Actionable Intelligence")

    # Key metrics annotation
    with dot.subgraph(name="cluster_metrics") as metrics:
        metrics.attr(
            label="Performance Targets", style="filled", fillcolor="honeydew", fontsize="11"
        )
        metrics.node(
            "latency",
            "Detection Latency\n< 60 seconds",
            shape="note",
            style="filled",
            fillcolor="lightsteelblue",
        )
        metrics.node(
            "accuracy",
            "False Positive Rate\n< 5%",
            shape="note",
            style="filled",
            fillcolor="lightsteelblue",
        )
        metrics.node(
            "coverage",
            "Multi-Modal Coverage\nBGP + SNMP + Syslog",
            shape="note",
            style="filled",
            fillcolor="lightsteelblue",
        )

    # Connect metrics to main flow
    dot.edge("multimodal_fusion", "latency", style="dashed", color="blue")
    dot.edge("topology_triage", "accuracy", style="dashed", color="blue")
    dot.edge("feature_extraction", "coverage", style="dashed", color="blue")

    return dot


if __name__ == "__main__":
    # Generate the updated system architecture
    arch = create_updated_system_architecture()
    arch.render(view=False)

    print("Updated System Architecture diagram created:")
    print("docs/design/updated_system_architecture.gv.png")
    print("\nThis diagram shows the simplified multi-modal architecture for presentation.")
