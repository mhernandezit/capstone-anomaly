# BGP Anomaly Detection System

A comprehensive machine learning system for real-time detection and localization of network failures using BGP routing updates and device logs.

## 🏗️ Project Structure

```text
capstone-anomaly/
├── src/                          # Source code
│   ├── models/                   # ML models (Matrix Profile, LSTM, etc.)
│   ├── features/                 # Feature extraction
│   ├── ingest/                   # Data ingestion (NATS, BGP)
│   ├── dash/                     # Streamlit dashboards
│   ├── alerting/                 # Alert management
│   ├── triage/                   # Impact classification
│   ├── preprocessing/            # Data preprocessing
│   ├── integration/              # ML pipeline integration
│   └── scripts/                  # Utility scripts
├── lab/                         # Containerlab virtual lab environment
│   ├── topo.clab.yml           # Lab topology definition
│   ├── configs/                # FRR router configurations
│   └── scripts/                # Lab management scripts
├── scripts/                     # Management and deployment scripts
├── config/                      # Configuration files
│   └── configs/                # System configurations
├── tests/                       # Test files and test data
├── data/                        # Data storage
│   ├── lab_traces/             # Lab-generated traces
│   └── public_traces/          # Public BGP traces
├── results/                     # Analysis results and outputs
├── docs/                        # Documentation
│   ├── project_proposal/       # LaTeX proposal documents
│   ├── design/                 # System design diagrams
│   ├── papers/                 # Research papers
│   └── development/            # Development documentation
└── docker-compose.yml          # Container orchestration
```

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.8+
- Containerlab (for virtual lab)

### Running the System

1. **Start the lab environment:**

   ```bash
   cd lab
   ./scripts/deploy.sh
   ```

2. **Run the ML pipeline:**

   ```bash
   cd src/python
   python dual_signal_pipeline.py
   ```

3. **Access the dashboard:**
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

- **`src/python/`**: Main ML pipeline and analysis code
- **`src/cmd/`**: Go-based BGP collector and utilities
- **`lab/`**: Virtual lab environment for testing
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
