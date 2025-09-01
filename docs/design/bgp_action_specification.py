from graphviz import Digraph

def create_action_specification_uml():
    """
    Create an Action Specification UML for BGP Failure Detection System
    Focuses on use cases, actor interactions, and detailed behavioral specifications
    """
    
    # Create the main diagram
    dot = Digraph('BGP_Action_Specification', filename='docs/design/bgp_action_specification.gv', format='png')
    dot.attr(rankdir='LR', splines='ortho', size='16,12')
    dot.attr('node', fontname='Arial', fontsize='10')
    dot.attr('edge', fontname='Arial', fontsize='8')
    
    # Define actors
    with dot.subgraph(name='cluster_actors') as actors:
        actors.attr(label='System Actors', style='filled', fillcolor='lightblue')
        actors.node('network_operator', 'Network Operator\n(Primary User)', shape='box', style='filled', fillcolor='lightgreen')
        actors.node('bgp_router', 'BGP Router\n(Data Source)', shape='box', style='filled', fillcolor='lightcoral')
        actors.node('monitoring_system', 'Existing Monitoring\n(Integration)', shape='box', style='filled', fillcolor='lightyellow')
        actors.node('management_system', 'Network Management\n(Consumer)', shape='box', style='filled', fillcolor='lightgray')
    
    # Define main use cases
    with dot.subgraph(name='cluster_use_cases') as uc:
        uc.attr(label='Primary Use Cases', style='filled', fillcolor='lightcyan')
        uc.node('uc_monitor', 'Monitor BGP Stream\n[Real-time]', shape='ellipse')
        uc.node('uc_detect', 'Detect Anomalies\n[Matrix Profile]', shape='ellipse')
        uc.node('uc_classify', 'Classify Impact\n[Topology-Aware]', shape='ellipse')
        uc.node('uc_alert', 'Generate Alerts\n[Contextual]', shape='ellipse')
        uc.node('uc_visualize', 'Visualize Events\n[Dashboard]', shape='ellipse')
        uc.node('uc_investigate', 'Investigate Failures\n[Root Cause]', shape='ellipse')
    
    # Define detailed action specifications
    with dot.subgraph(name='cluster_actions') as actions:
        actions.attr(label='Action Specifications', style='filled', fillcolor='mistyrose')
        
        # BGP Monitoring Actions
        actions.node('action_connect', 'Action: EstablishBGPSessions\nPre: Config loaded, NATS ready\nPost: Active BGP sessions\nException: SessionFailure', shape='note')
        actions.node('action_parse', 'Action: ParseBGPUpdate\nPre: Raw BGP message received\nPost: Structured update object\nException: MalformedMessage', shape='note')
        actions.node('action_publish', 'Action: PublishToMessageBus\nPre: Valid update object\nPost: Message in NATS stream\nException: PublishFailure', shape='note')
        
        # Feature Processing Actions
        actions.node('action_aggregate', 'Action: AggregateFeatures\nPre: BGP updates in time window\nPost: Feature vector computed\nException: InsufficientData', shape='note')
        actions.node('action_bin', 'Action: CreateTimeBin\nPre: 30-second window elapsed\nPost: Closed feature bin\nException: TimingError', shape='note')
        
        # Anomaly Detection Actions
        actions.node('action_mp', 'Action: ComputeMatrixProfile\nPre: Sufficient historical data\nPost: Anomaly score calculated\nException: ComputationError', shape='note')
        actions.node('action_threshold', 'Action: EvaluateThreshold\nPre: Anomaly score available\nPost: Boolean anomaly decision\nException: ThresholdError', shape='note')
        
        # Triage Actions
        actions.node('action_role', 'Action: AnalyzeRoleImpact\nPre: Anomaly detected\nPost: Affected roles identified\nException: TopologyError', shape='note')
        actions.node('action_blast', 'Action: CalculateBlastRadius\nPre: Role analysis complete\nPost: Impact classification\nException: ClassificationError', shape='note')
        
        # Response Actions
        actions.node('action_dashboard', 'Action: UpdateDashboard\nPre: Event classified\nPost: UI updated with event\nException: DisplayError', shape='note')
        actions.node('action_alert', 'Action: TriggerAlert\nPre: Network impact detected\nPost: Alert sent to operators\nException: AlertFailure', shape='note')
    
    # Define decision points and conditions
    with dot.subgraph(name='cluster_decisions') as decisions:
        decisions.attr(label='Decision Logic', style='filled', fillcolor='lavender')
        decisions.node('decision_session', 'BGP Session\nHealth Check\n[Every 30s]', shape='diamond', style='filled', fillcolor='yellow')
        decisions.node('decision_anomaly', 'Anomaly Score\n> Threshold\n[Configurable]', shape='diamond', style='filled', fillcolor='orange')
        decisions.node('decision_impact', 'Impact Scope\nClassification\n[Rule-based]', shape='diamond', style='filled', fillcolor='red')
        decisions.node('decision_alert', 'Alert Severity\nDetermination\n[Policy-driven]', shape='diamond', style='filled', fillcolor='purple')
    
    # Define data flows and constraints
    with dot.subgraph(name='cluster_constraints') as constraints:
        constraints.attr(label='System Constraints & Invariants', style='filled', fillcolor='honeydew')
        constraints.node('constraint_latency', 'Constraint: DetectionLatency\n< 60 seconds end-to-end', shape='box', style='filled', fillcolor='lightsteelblue')
        constraints.node('constraint_accuracy', 'Constraint: FalsePositiveRate\n< 5% for network impact events', shape='box', style='filled', fillcolor='lightsteelblue')
        constraints.node('constraint_availability', 'Constraint: SystemAvailability\n> 99.5% uptime', shape='box', style='filled', fillcolor='lightsteelblue')
        constraints.node('invariant_data', 'Invariant: DataIntegrity\nAll BGP updates processed in order', shape='box', style='filled', fillcolor='lightpink')
        constraints.node('invariant_session', 'Invariant: SessionState\nBGP sessions monitored continuously', shape='box', style='filled', fillcolor='lightpink')
    
    # Connect actors to use cases
    dot.edge('network_operator', 'uc_monitor', label='initiates')
    dot.edge('network_operator', 'uc_investigate', label='performs')
    dot.edge('network_operator', 'uc_visualize', label='views')
    dot.edge('bgp_router', 'uc_monitor', label='provides data to')
    dot.edge('monitoring_system', 'uc_alert', label='receives from')
    dot.edge('management_system', 'uc_alert', label='consumes')
    
    # Connect use cases to actions
    dot.edge('uc_monitor', 'action_connect', label='realizes')
    dot.edge('uc_monitor', 'action_parse', label='includes')
    dot.edge('uc_monitor', 'action_publish', label='includes')
    
    dot.edge('uc_detect', 'action_aggregate', label='requires')
    dot.edge('uc_detect', 'action_mp', label='performs')
    dot.edge('uc_detect', 'action_threshold', label='evaluates')
    
    dot.edge('uc_classify', 'action_role', label='executes')
    dot.edge('uc_classify', 'action_blast', label='calculates')
    
    dot.edge('uc_alert', 'action_alert', label='triggers')
    dot.edge('uc_visualize', 'action_dashboard', label='updates')
    
    # Connect actions to decisions
    dot.edge('action_connect', 'decision_session', label='validates')
    dot.edge('action_threshold', 'decision_anomaly', label='determines')
    dot.edge('action_blast', 'decision_impact', label='classifies')
    dot.edge('decision_impact', 'decision_alert', label='influences')
    
    # Connect to constraints
    dot.edge('action_mp', 'constraint_latency', label='bounded by', style='dashed')
    dot.edge('decision_anomaly', 'constraint_accuracy', label='measured by', style='dashed')
    dot.edge('uc_monitor', 'constraint_availability', label='requires', style='dashed')
    dot.edge('action_publish', 'invariant_data', label='maintains', style='dashed')
    dot.edge('decision_session', 'invariant_session', label='enforces', style='dashed')
    
    # Add temporal sequences
    with dot.subgraph(name='cluster_sequence') as seq:
        seq.attr(label='Temporal Sequence', style='filled', fillcolor='aliceblue')
        seq.node('seq_1', '1. BGP Update\nReceived', shape='box', style='filled', fillcolor='wheat')
        seq.node('seq_2', '2. Features\nAggregated', shape='box', style='filled', fillcolor='wheat')
        seq.node('seq_3', '3. Anomaly\nDetected', shape='box', style='filled', fillcolor='wheat')
        seq.node('seq_4', '4. Impact\nClassified', shape='box', style='filled', fillcolor='wheat')
        seq.node('seq_5', '5. Response\nTriggered', shape='box', style='filled', fillcolor='wheat')
        
        seq.edge('seq_1', 'seq_2', label='30s window')
        seq.edge('seq_2', 'seq_3', label='real-time')
        seq.edge('seq_3', 'seq_4', label='<1s')
        seq.edge('seq_4', 'seq_5', label='immediate')
    
    return dot

def create_use_case_detail_diagram():
    """
    Create detailed use case specifications for key scenarios
    """
    
    detail = Digraph('BGP_UseCase_Details', filename='docs/design/bgp_usecase_details.gv', format='png')
    detail.attr(rankdir='TB', splines='ortho', size='12,16')
    detail.attr('node', fontname='Arial', fontsize='9')
    
    # Network Failure Scenario Use Case
    with detail.subgraph(name='cluster_failure_scenario') as scenario:
        scenario.attr(label='Use Case: Network Failure Detection & Response', style='filled', fillcolor='lightcyan')
        
        scenario.node('uc_title', 'Use Case: Detect ToR-Spine Link Failure\nActor: Network Operator\nGoal: Rapid failure localization', 
                     shape='note', style='filled', fillcolor='lightyellow')
        
        scenario.node('precond', 'Preconditions:\n• BGP sessions established\n• Baseline traffic pattern learned\n• Dashboard accessible', 
                     shape='box')
        scenario.node('trigger', 'Trigger:\nToR-Spine link fails\n→ BGP withdrawals', 
                     shape='box', style='filled', fillcolor='orange')
        
        scenario.node('step1', 'Step 1:\nBGP collector receives\nwithdrawal storm from ToR', shape='box')
        scenario.node('step2', 'Step 2:\nFeature aggregator detects\nhigh withdrawal rate', shape='box')
        scenario.node('step3', 'Step 3:\nMatrix Profile identifies\ndiscord in time series', shape='box')
        scenario.node('step4', 'Step 4:\nTriage analysis determines\nEDGE_LOCAL impact', shape='box')
        scenario.node('step5', 'Step 5:\nDashboard shows localized\nfailure with affected prefixes', shape='box')
        
        scenario.node('success', 'Success Condition:\nOperator identifies failed link\nwithin 60 seconds', 
                     shape='box', style='filled', fillcolor='lightgreen')
        scenario.node('failure', 'Failure Condition:\nFalse positive or\nmissed detection', 
                     shape='box', style='filled', fillcolor='lightcoral')
        
        # Connect the flow
        detail.edge('precond', 'trigger')
        detail.edge('trigger', 'step1')
        detail.edge('step1', 'step2')
        detail.edge('step2', 'step3')
        detail.edge('step3', 'step4')
        detail.edge('step4', 'step5')
        detail.edge('step5', 'success', label='normal flow')
        detail.edge('step3', 'failure', label='detection fails', style='dashed', color='red')
    
    # Alternative flows
    with detail.subgraph(name='cluster_alternatives') as alt:
        alt.attr(label='Alternative Flows', style='filled', fillcolor='mistyrose')
        
        alt.node('alt1', 'Alternative 1:\nNo BGP session to affected ToR\n→ Infer from neighbor behavior', 
                shape='box', style='filled', fillcolor='yellow')
        alt.node('alt2', 'Alternative 2:\nHigh noise in baseline\n→ Adaptive threshold adjustment', 
                shape='box', style='filled', fillcolor='yellow')
        alt.node('alt3', 'Alternative 3:\nDashboard unavailable\n→ Direct NATS subscription for alerts', 
                shape='box', style='filled', fillcolor='yellow')
        
        detail.edge('step1', 'alt1', label='if no direct session', style='dotted')
        detail.edge('step3', 'alt2', label='if high baseline noise', style='dotted')
        detail.edge('step5', 'alt3', label='if dashboard down', style='dotted')
    
    # Exception handling
    with detail.subgraph(name='cluster_exceptions') as exc:
        exc.attr(label='Exception Handling', style='filled', fillcolor='lavenderblush')
        
        exc.node('exc1', 'Exception: BGP Session Loss\nAction: Attempt reconnection\nFallback: Monitor via neighbors', 
                shape='box', style='filled', fillcolor='red')
        exc.node('exc2', 'Exception: NATS Connection Loss\nAction: Local buffering\nFallback: Direct dashboard update', 
                shape='box', style='filled', fillcolor='red')
        exc.node('exc3', 'Exception: Matrix Profile Computation Failure\nAction: Fallback to simple thresholding\nAlert: Degraded mode active', 
                shape='box', style='filled', fillcolor='red')
        
        detail.edge('step1', 'exc1', label='BGP session fails', style='dashed', color='red')
        detail.edge('step2', 'exc2', label='NATS fails', style='dashed', color='red')
        detail.edge('step3', 'exc3', label='MP computation fails', style='dashed', color='red')
    
    return detail

if __name__ == "__main__":
    # Generate both diagrams
    action_spec = create_action_specification_uml()
    use_case_detail = create_use_case_detail_diagram()
    
    # Render the diagrams
    action_spec.render(view=False)
    use_case_detail.render(view=False)
    
    print("Action Specification UML diagrams created:")
    print("1. docs/design/bgp_action_specification.gv.png - Main action specification")
    print("2. docs/design/bgp_usecase_details.gv.png - Detailed use case flows")
    print("\nThese complement the existing structural UML with behavioral specifications.")
