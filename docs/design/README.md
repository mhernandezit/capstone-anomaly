# System Design Documentation

This directory contains comprehensive UML diagrams and design documentation for the BGP Failure Detection system.

## UML Diagrams

### 1. Structural UML - System Architecture

**File:** `bgp_anomaly_uml.gv.png`  
**Source:** `bgp_anomaly_uml.py`

**Purpose:** Shows the overall system flow, components, and data path from BGP collection through anomaly detection to dashboard visualization.

**Key Elements:**

- BGP Collector initialization and session management
- Feature aggregation and binning (30-second windows)
- Matrix Profile anomaly detection
- Topology-aware triage classification
- Dashboard updates and alerting flows

### 2. Action Specification UML - Behavioral Model

**File:** `bgp_action_specification.gv.png`  
**Source:** `bgp_action_specification.py`

**Purpose:** Defines actors, use cases, action specifications, decision logic, and system constraints.

**Key Elements:**

- **Actors:** Network Operator, BGP Router, Monitoring System, Management System
- **Use Cases:** Monitor BGP Stream, Detect Anomalies, Classify Impact, Generate Alerts
- **Actions:** Detailed pre/post conditions and exception handling
- **Constraints:** Performance requirements and system invariants

### 3. Use Case Details UML - Scenario Specifications

**File:** `bgp_usecase_details.gv.png`  
**Source:** `bgp_action_specification.py` (second diagram)

**Purpose:** Detailed use case flow for network failure detection scenario with alternative flows and exception handling.

**Key Elements:**

- Primary scenario: ToR-Spine link failure detection
- Alternative flows for edge cases
- Exception handling strategies
- Success/failure conditions

## 🔧 Generating Diagrams

To regenerate the diagrams after making changes:

```bash
# Ensure dependencies are installed
pip install graphviz
brew install graphviz

# Generate structural UML
python bgp_anomaly_uml.py

# Generate action specification UMLs
python bgp_action_specification.py
```

## Design Principles

### 1. Real-time Processing

- 30-second feature aggregation windows
- End-to-end detection latency < 60 seconds
- Streaming Matrix Profile for continuous analysis

### 2. Topology Awareness

- Role-based impact classification (ToR, Spine, Edge, RR, Server)
- Blast radius calculation using network topology
- Context-aware alerting (EDGE_LOCAL vs NETWORK_IMPACTING)

### 3. Fault Tolerance

- Graceful degradation when components fail
- Alternative data sources when BGP sessions are lost
- Exception handling at each processing stage

### 4. Scalability

- Containerized microservices architecture
- Message bus decoupling (NATS)
- Stateless processing components

## Use Case Scenarios

### Primary: Network Failure Detection

1. **Trigger:** Physical link failure (ToR ↔ Spine)
2. **Detection:** BGP withdrawal storm → feature spike → Matrix Profile discord
3. **Classification:** Role analysis → blast radius → impact determination
4. **Response:** Dashboard update + appropriate alerting level

### Secondary: Gradual Degradation

1. **Trigger:** Increasing BGP churn over time
2. **Detection:** Trending discord scores in Matrix Profile
3. **Classification:** Multi-role correlation analysis
4. **Response:** Predictive alerting before critical failure

## Performance Requirements

| Metric | Requirement | Rationale |
|--------|-------------|-----------|
| Detection Latency | < 60 seconds | Operator response time SLA |
| False Positive Rate | < 5% | Alert fatigue prevention |
| System Availability | > 99.5% | Critical infrastructure monitoring |
| BGP Update Processing | 1000+ updates/sec | Large network capacity |

## 🔍 Design Validation

The UML diagrams support validation through:

- **Traceability:** Requirements → Use Cases → Actions → Implementation
- **Completeness:** All system actors and interactions documented
- **Consistency:** Cross-referenced between structural and behavioral views
- **Testability:** Clear pre/post conditions enable unit testing

## Related Documentation

- **[System Requirements](../development/proposal.md)** - Functional and non-functional requirements
- **[Implementation Plan](../development/program_alignment.md)** - Development approach
- **[Research Foundation](../research/references.md)** - Academic literature supporting design choices

---

*These diagrams provide the architectural foundation for the network anomaly detection project, demonstrating systems analysis and design competencies while supporting the technical implementation.*
