# Machine Learning for Network Anomaly and Failure Detection

A comprehensive machine learning system for real-time detection and localization of network failures using multi-modal data sources including BGP routing updates, SNMP metrics, and syslog messages.

## Project Structure

```text
capstone-anomaly/
├── src/                          # Python ML pipeline source code
│   ├── models/                   # ML models (Matrix Profile, LSTM, etc.)
│   ├── features/                 # Feature extraction and aggregation
│   ├── ingest/                   # Data ingestion from NATS
│   ├── dash/                     # Streamlit dashboards
│   ├── alerting/                 # Alert management
│   ├── triage/                   # Impact classification
│   ├── preprocessing/            # Data preprocessing
│   ├── integration/              # ML pipeline integration
│   ├── message_bus/              # NATS message bus integration
│   └── utils/                    # Utility functions and schemas
├── cmd/                          # Go-based components
│   └── bmp-collector/            # BGP Monitoring Protocol collector
├── lab/                         # Containerlab network environment
│   ├── topo.clab.yml           # Basic lab topology
│   ├── topo-dc-expanded.clab.yml # Expanded datacenter topology
│   ├── configs/                # FRR router configurations
│   ├── scripts/                # Lab management scripts
│   └── monitoring/             # Fluent Bit log collection
├── config/                      # Configuration files
│   └── configs/                # System configurations
├── tests/                       # Test files and test data
├── data/                        # Data storage
│   ├── lab_traces/             # Lab-generated traces
│   └── public_traces/          # Public BGP traces
├── docs/                        # Documentation
│   ├── project_proposal/       # LaTeX proposal documents
│   ├── presentations/          # Final project presentation
│   ├── design/                 # System design diagrams
│   ├── papers/                 # Research papers
│   └── development/            # Development documentation
├── docker-compose.yml          # Container orchestration
└── go.mod                       # Go module dependencies
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.8+
- Go 1.21+ (for BMP collector)
- Containerlab (for network lab)
- NATS server

### Running the System

1. **Start the lab environment:**

   ```bash
   cd lab
   ./scripts/deploy.sh
   ```

2. **Build and run the BMP collector:**

   ```bash
   # Build the Go BMP collector
   docker build -t capstone-bmp-collector:latest -f cmd/bmp-collector/Dockerfile .
   
   # The collector is automatically started with the lab
   ```

3. **Run the ML pipeline:**

   ```bash
   cd src
   python dual_signal_pipeline.py
   ```

4. **Access the dashboard:**
   - Open `http://localhost:8501` in your browser

### Testing

```bash
# Quick test
make test-quick

# Full test suite
make test-scenarios
```

## Research Components

### Machine Learning Models

- **Matrix Profile**: Time-series anomaly detection for BGP streams
- **Isolation Forest**: Unsupervised anomaly detection for log patterns
- **LSTM Baseline**: Supervised learning approach for comparison

### Data Sources

- **BGP Updates**: Real-time routing change messages via BGP Monitoring Protocol (BMP)
- **SNMP Metrics**: Hardware health indicators and interface performance data
- **Syslog**: Device logs and system events
- **Lab Traces**: Generated from virtual lab environment with Containerlab and FRR routers

### Evaluation Metrics

- Operational efficiency improvements
- Precision/Recall/F1 scores for anomaly detection
- Context-aware anomaly localization accuracy
- Alert noise reduction vs. traditional threshold-based monitoring

## Documentation

- [Project Proposal](docs/project_proposal/) - LaTeX proposal documents
- [Final Project Presentation](docs/presentations/) - Final project presentation
- [Testing Guide](TESTING_GUIDE.md) - Comprehensive testing instructions
- [Lab Documentation](lab/README.md) - Virtual lab setup and usage
- [Research Papers](docs/papers/) - Supporting research literature

## Development

### Code Organization

- **`src/`**: Python ML pipeline and analysis code
- **`cmd/bmp-collector/`**: Go-based BGP Monitoring Protocol collector
- **`lab/`**: Containerlab network environment with real FRR routers
- **`scripts/`**: Deployment and management automation

### Key Features

- Multi-modal network anomaly detection (BGP, SNMP, syslog)
- Real-time streaming analytics with NATS message bus
- Matrix Profile and Isolation Forest ML algorithms
- Topology-aware failure localization
- Context-aware correlation analysis
- Interactive dashboard for Network Operation Centers

## Project Status

This project is part of the Information Systems Capstone program.

**Current Focus:**

- Project proposal completed
- Virtual lab environment established with Containerlab and FRR routers
- ML pipeline implementation with multi-modal data processing
- Go-based BMP collector for BGP data ingestion
- Final project presentation completed
- System integration and comprehensive testing
- Performance evaluation and validation

## Contributing

This is a research project. All code is a work in progress by Mike Hernandez.

## License

This project is for educational purposes as part of the Information Systems Capstone program.
