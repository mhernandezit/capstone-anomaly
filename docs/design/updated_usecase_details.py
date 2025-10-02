from graphviz import Digraph


def create_updated_usecase_details():
    """
    Create a simplified use case details diagram for presentation
    Focuses on a clear failure detection scenario
    """

    dot = Digraph(
        "Updated_UseCase_Details", filename="docs/design/updated_usecase_details.gv", format="png"
    )
    dot.attr(rankdir="TB", splines="ortho", size="10,14")
    dot.attr("node", fontname="Arial", fontsize="10")
    dot.attr("edge", fontname="Arial", fontsize="9")

    # Title
    dot.node(
        "title",
        "Use Case: Network Failure Detection & Response\nMulti-Modal Anomaly Detection Scenario",
        shape="box",
        style="filled",
        fillcolor="lightblue",
        fontsize="14",
    )

    # Main Scenario
    with dot.subgraph(name="cluster_main_scenario") as scenario:
        scenario.attr(
            label="Primary Scenario: ToR-Spine Link Failure",
            style="filled",
            fillcolor="lightcyan",
            fontsize="12",
        )

        scenario.node(
            "preconditions",
            "Preconditions:\n• Multi-modal monitoring active\n• Baseline patterns learned\n• All systems operational",
            shape="box",
            style="filled",
            fillcolor="lightgreen",
        )

        scenario.node(
            "trigger",
            "Trigger Event:\nPhysical Link Failure\n(ToR ↔ Spine)",
            shape="box",
            style="filled",
            fillcolor="orange",
        )

        # Main flow steps
        scenario.node(
            "step1",
            "Step 1: Data Collection\nBGP withdrawals detected\nSNMP interface down alerts\nSyslog link failure messages",
            shape="box",
            style="filled",
            fillcolor="wheat",
        )

        scenario.node(
            "step2",
            "Step 2: Feature Correlation\nMulti-modal feature extraction\nCross-source correlation\nTemporal pattern analysis",
            shape="box",
            style="filled",
            fillcolor="wheat",
        )

        scenario.node(
            "step3",
            "Step 3: Anomaly Detection\nMatrix Profile analysis\nML-based anomaly scoring\nThreshold evaluation",
            shape="box",
            style="filled",
            fillcolor="orange",
        )

        scenario.node(
            "step4",
            "Step 4: Impact Classification\nTopology-aware analysis\nRole-based impact assessment\nBlast radius calculation",
            shape="box",
            style="filled",
            fillcolor="yellow",
        )

        scenario.node(
            "step5",
            "Step 5: Response Generation\nDashboard visualization\nContext-aware alerting\nOperator notification",
            shape="box",
            style="filled",
            fillcolor="lightpink",
        )

        scenario.node(
            "success",
            "Success Outcome:\nFailure identified within 60s\nRoot cause localized\nAppropriate response triggered",
            shape="box",
            style="filled",
            fillcolor="lightgreen",
        )

    # Alternative Flows
    with dot.subgraph(name="cluster_alternatives") as alt:
        alt.attr(label="Alternative Flows", style="filled", fillcolor="mistyrose", fontsize="12")

        alt.node(
            "alt1",
            "Alternative 1: Partial Data\nMissing BGP session\n→ Infer from SNMP/Syslog\n→ Reduced confidence alert",
            shape="box",
            style="filled",
            fillcolor="lightyellow",
        )

        alt.node(
            "alt2",
            "Alternative 2: Gradual Degradation\nSlow performance decline\n→ Trending analysis\n→ Predictive alerting",
            shape="box",
            style="filled",
            fillcolor="lightyellow",
        )

        alt.node(
            "alt3",
            "Alternative 3: False Positive\nNormal operational change\n→ Enhanced verification\n→ No alert sent",
            shape="box",
            style="filled",
            fillcolor="lightyellow",
        )

    # Exception Handling
    with dot.subgraph(name="cluster_exceptions") as exc:
        exc.attr(
            label="Exception Handling", style="filled", fillcolor="lavenderblush", fontsize="12"
        )

        exc.node(
            "exc1",
            "Exception: Data Source Failure\nBGP collector down\n→ SNMP/Syslog only mode\n→ Degraded monitoring",
            shape="box",
            style="filled",
            fillcolor="lightcoral",
        )

        exc.node(
            "exc2",
            "Exception: ML Model Failure\nMatrix Profile computation error\n→ Fallback to thresholding\n→ Reduced accuracy",
            shape="box",
            style="filled",
            fillcolor="lightcoral",
        )

        exc.node(
            "exc3",
            "Exception: Dashboard Failure\nUI unavailable\n→ Direct alert notifications\n→ Emergency mode",
            shape="box",
            style="filled",
            fillcolor="lightcoral",
        )

    # Performance Metrics
    with dot.subgraph(name="cluster_metrics") as metrics:
        metrics.attr(label="Success Metrics", style="filled", fillcolor="honeydew", fontsize="12")

        metrics.node(
            "metric_detection",
            "Detection Time:\n< 60 seconds",
            shape="note",
            style="filled",
            fillcolor="lightsteelblue",
        )

        metrics.node(
            "metric_accuracy",
            "Accuracy Rate:\n> 95%",
            shape="note",
            style="filled",
            fillcolor="lightsteelblue",
        )

        metrics.node(
            "metric_coverage",
            "Coverage:\nMulti-modal correlation",
            shape="note",
            style="filled",
            fillcolor="lightsteelblue",
        )

    # Connect main flow
    dot.edge("preconditions", "trigger")
    dot.edge("trigger", "step1")
    dot.edge("step1", "step2")
    dot.edge("step2", "step3")
    dot.edge("step3", "step4")
    dot.edge("step4", "step5")
    dot.edge("step5", "success")

    # Connect alternatives
    dot.edge("step1", "alt1", label="if partial data", style="dotted", color="blue")
    dot.edge("step3", "alt2", label="if gradual change", style="dotted", color="blue")
    dot.edge("step4", "alt3", label="if false positive", style="dotted", color="blue")

    # Connect exceptions
    dot.edge("step1", "exc1", label="data source fails", style="dashed", color="red")
    dot.edge("step3", "exc2", label="ML computation fails", style="dashed", color="red")
    dot.edge("step5", "exc3", label="dashboard fails", style="dashed", color="red")

    # Connect metrics
    dot.edge("step3", "metric_detection", label="measured by", style="dashed", color="green")
    dot.edge("step4", "metric_accuracy", label="validated by", style="dashed", color="green")
    dot.edge("step2", "metric_coverage", label="ensured by", style="dashed", color="green")

    # Alternative outcomes
    dot.edge("alt1", "step4", label="continue with reduced data")
    dot.edge("alt2", "step5", label="predictive alert")
    dot.edge("alt3", "success", label="no action needed")

    # Exception recovery
    dot.edge("exc1", "step2", label="degraded mode")
    dot.edge("exc2", "step4", label="fallback detection")
    dot.edge("exc3", "success", label="direct notification")

    return dot


if __name__ == "__main__":
    # Generate the updated use case details
    details = create_updated_usecase_details()
    details.render(view=False)

    print("Updated Use Case Details diagram created:")
    print("docs/design/updated_usecase_details.gv.png")
    print(
        "\nThis diagram shows a simplified failure detection scenario with alternatives and exceptions."
    )
