# BGP Anomaly Detection System

A comprehensive machine learning system for real-time detection and localization of network failures using BGP routing updates and device logs.

## 🏗️ Project Structure

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
│   ├── design/                 # System design diagrams
│   ├── papers/                 # Research papers
│   └── development/            # Development documentation
├── docker-compose.yml          # Container orchestration
└── go.mod                       # Go module dependencies
```

## 🚀 Quick Start

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

## 🔬 Research Components

### Machine Learning Models

- **Matrix Profile**: Time-series anomaly detection for BGP streams
- **Isolation Forest**: Unsupervised anomaly detection for log patterns
- **LSTM Baseline**: Supervised learning approach for comparison

### Data Sources

- **BGP Updates**: Real-time routing change messages
- **Syslog**: Device logs and system events
- **Lab Traces**: Generated from virtual lab environment

### Evaluation Metrics

- Detection delay
- Precision/Recall/F1 scores
- Localization accuracy (Hit@k)
- Page reduction vs. traditional monitoring

## 📚 Documentation

- [Project Proposal](docs/project_proposal/) - LaTeX proposal documents
- [Testing Guide](TESTING_GUIDE.md) - Comprehensive testing instructions
- [Lab Documentation](lab/README.md) - Virtual lab setup and usage
- [Research Papers](docs/papers/) - Supporting research literature

## 🛠️ Development

### Code Organization

- **`src/`**: Python ML pipeline and analysis code
- **`cmd/bmp-collector/`**: Go-based BGP Monitoring Protocol collector
- **`lab/`**: Containerlab network environment with real FRR routers
- **`scripts/`**: Deployment and management automation

### Key Features

- Real-time BGP anomaly detection
- Multi-signal correlation (BGP + logs)
- Topology-aware localization
- Interactive dashboard for operators
- Comprehensive testing framework

## 📊 Project Status

This project is part of the IS 499 Information Systems Capstone at CUNY School of Professional Studies.

**Current Focus:**

- ✅ Project proposal completed
- ✅ Virtual lab environment established
- ✅ ML pipeline implementation
- 🔄 System integration and testing
- 📋 Final evaluation and documentation

## 🤝 Contributing

This is a capstone project. All code is a work in progress by Mike Hernandez.

## 📄 License

This project is for educational purposes as part of the CUNY SPS Information Systems Capstone.
