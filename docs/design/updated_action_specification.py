from graphviz import Digraph


def create_updated_action_specification():
    """
    Create a simplified action specification UML for presentation
    Focuses on key actors, use cases, and decision logic
    """

    dot = Digraph(
        "Updated_Action_Specification",
        filename="docs/design/updated_action_specification.gv",
        format="png",
    )
    dot.attr(rankdir="LR", splines="ortho", size="12,10")
    dot.attr("node", fontname="Arial", fontsize="10")
    dot.attr("edge", fontname="Arial", fontsize="8")

    # Title
    dot.node(
        "title",
        "Multi-Modal Network Anomaly Detection\nAction Specification",
        shape="box",
        style="filled",
        fillcolor="lightblue",
        fontsize="14",
    )

    # Actors (simplified)
    with dot.subgraph(name="cluster_actors") as actors:
        actors.attr(label="System Actors", style="filled", fillcolor="lightcyan", fontsize="12")
        actors.node(
            "operator",
            "Network Operator\n(Primary User)",
            shape="box",
            style="filled",
            fillcolor="lightgreen",
        )
        actors.node(
            "network",
            "Network Devices\n(BGP, SNMP, Syslog)",
            shape="box",
            style="filled",
            fillcolor="lightcoral",
        )
        actors.node(
            "system",
            "Detection System\n(ML Pipeline)",
            shape="box",
            style="filled",
            fillcolor="lightyellow",
        )

    # Core Use Cases
    with dot.subgraph(name="cluster_use_cases") as uc:
        uc.attr(label="Primary Use Cases", style="filled", fillcolor="mistyrose", fontsize="12")
        uc.node(
            "uc_monitor",
            "Monitor Multi-Modal\nNetwork Data",
            shape="ellipse",
            style="filled",
            fillcolor="wheat",
        )
        uc.node(
            "uc_detect",
            "Detect Anomalies\n(ML Analysis)",
            shape="ellipse",
            style="filled",
            fillcolor="orange",
        )
        uc.node(
            "uc_classify",
            "Classify Impact\n(Topology Analysis)",
            shape="ellipse",
            style="filled",
            fillcolor="yellow",
        )
        uc.node(
            "uc_respond",
            "Respond to Failures\n(Alerts & Actions)",
            shape="ellipse",
            style="filled",
            fillcolor="lightpink",
        )

    # Key Actions (simplified)
    with dot.subgraph(name="cluster_actions") as actions:
        actions.attr(label="Key Actions", style="filled", fillcolor="lavender", fontsize="12")

        # Data Processing Actions
        actions.node(
            "action_collect",
            "Collect Multi-Modal Data\n(BGP + SNMP + Syslog)",
            shape="note",
            style="filled",
            fillcolor="lightsteelblue",
        )
        actions.node(
            "action_extract",
            "Extract Features\n(Multi-Source Correlation)",
            shape="note",
            style="filled",
            fillcolor="lightsteelblue",
        )

        # ML Actions
        actions.node(
            "action_analyze",
            "Analyze with ML\n(Matrix Profile + Others)",
            shape="note",
            style="filled",
            fillcolor="lightsteelblue",
        )
        actions.node(
            "action_classify",
            "Classify Impact Scope\n(Edge vs Network-wide)",
            shape="note",
            style="filled",
            fillcolor="lightsteelblue",
        )

        # Response Actions
        actions.node(
            "action_alert",
            "Generate Smart Alerts\n(Context-Aware)",
            shape="note",
            style="filled",
            fillcolor="lightsteelblue",
        )
        actions.node(
            "action_visualize",
            "Update Dashboard\n(Real-time Visualization)",
            shape="note",
            style="filled",
            fillcolor="lightsteelblue",
        )

    # Decision Points
    with dot.subgraph(name="cluster_decisions") as decisions:
        decisions.attr(label="Decision Logic", style="filled", fillcolor="honeydew", fontsize="12")
        decisions.node(
            "decision_anomaly",
            "Anomaly Detected?\n(ML Threshold)",
            shape="diamond",
            style="filled",
            fillcolor="orange",
        )
        decisions.node(
            "decision_impact",
            "Impact Level?\n(Edge vs Network)",
            shape="diamond",
            style="filled",
            fillcolor="red",
        )
        decisions.node(
            "decision_response",
            "Alert Required?\n(Severity Check)",
            shape="diamond",
            style="filled",
            fillcolor="purple",
        )

    # Performance Constraints
    with dot.subgraph(name="cluster_constraints") as constraints:
        constraints.attr(
            label="Performance Constraints", style="filled", fillcolor="aliceblue", fontsize="12"
        )
        constraints.node(
            "constraint_speed",
            "Real-time Processing\n< 60s Detection",
            shape="box",
            style="filled",
            fillcolor="lightsteelblue",
        )
        constraints.node(
            "constraint_accuracy",
            "High Accuracy\n< 5% False Positives",
            shape="box",
            style="filled",
            fillcolor="lightsteelblue",
        )
        constraints.node(
            "constraint_coverage",
            "Multi-Modal Coverage\nAll Data Sources",
            shape="box",
            style="filled",
            fillcolor="lightsteelblue",
        )

    # Connect actors to use cases
    dot.edge("operator", "uc_monitor", label="initiates")
    dot.edge("operator", "uc_respond", label="performs")
    dot.edge("network", "uc_monitor", label="provides data")
    dot.edge("system", "uc_detect", label="executes")
    dot.edge("system", "uc_classify", label="performs")

    # Connect use cases to actions
    dot.edge("uc_monitor", "action_collect", label="includes")
    dot.edge("uc_monitor", "action_extract", label="requires")
    dot.edge("uc_detect", "action_analyze", label="performs")
    dot.edge("uc_classify", "action_classify", label="executes")
    dot.edge("uc_respond", "action_alert", label="triggers")
    dot.edge("uc_respond", "action_visualize", label="updates")

    # Connect actions to decisions
    dot.edge("action_analyze", "decision_anomaly", label="determines")
    dot.edge("action_classify", "decision_impact", label="evaluates")
    dot.edge("decision_impact", "decision_response", label="influences")

    # Connect to constraints
    dot.edge("action_analyze", "constraint_speed", label="bounded by", style="dashed")
    dot.edge("decision_anomaly", "constraint_accuracy", label="measured by", style="dashed")
    dot.edge("action_collect", "constraint_coverage", label="ensures", style="dashed")

    # Decision outcomes
    dot.edge("decision_anomaly", "action_classify", label="Yes", color="green")
    dot.edge("decision_impact", "action_alert", label="Network Impact", color="red")
    dot.edge("decision_impact", "action_visualize", label="Edge Local", color="orange")
    dot.edge("decision_response", "operator", label="Alert Sent", color="purple")

    return dot


if __name__ == "__main__":
    # Generate the updated action specification
    spec = create_updated_action_specification()
    spec.render(view=False)

    print("Updated Action Specification diagram created:")
    print("docs/design/updated_action_specification.gv.png")
    print("\nThis diagram shows simplified actors, use cases, and decision logic for presentation.")
