# Quick Start Guide

**For new users and team members**

## Installation (2 minutes)

```bash
# 1. Clone the repository
git clone https://github.com/your-username/capstone-anomaly.git
cd capstone-anomaly

# 2. Install the package
pip install -e .

# This installs all dependencies and sets up clean imports
```

That's it! You're ready to use the system.

## Verify Installation

```bash
# Test imports work
python -c "from src.models import MatrixProfileDetector; print('OK')"

# Run quick validation
python evaluation/quick_validation.py

# Run tests
pytest tests/smoke/ -v
```

## Common Tasks

### Run Demo

```bash
python examples/demo_multimodal_correlation.py
```

### Run Full Evaluation

```bash
# Start NATS (if not running)
docker compose up -d nats

# Run evaluation
python evaluation/run_evaluation.py

# Analyze results
python evaluation/analyze_results.py
```

### Run Tests

```bash
# All tests
pytest tests/

# Just unit tests (fast)
pytest tests/unit/

# With coverage
pytest tests/ --cov=src --cov-report=html
```

### Use in Code

```python
# Import components
from src.models import MatrixProfileDetector, IsolationForestDetector
from src.correlation import MultiModalCorrelator
from src.features import FeatureAggregator

# Create detector
detector = MatrixProfileDetector(window_bins=64)

# Use it
result = detector.update(feature_bin)
```

## Project Structure

```
capstone-anomaly/
├── src/           # Python package (import from here)
├── tests/         # Test suite (pytest)
├── evaluation/    # Evaluation scripts
├── examples/      # Demo scripts
├── data/          # Data artifacts
├── config/        # Configuration
└── docs/          # Documentation
```

## Key Commands

```bash
# Installation
pip install -e .                    # Editable install
pip install -e ".[dev]"             # With dev tools
pip install -e ".[all]"             # With all extras

# Testing
pytest tests/                       # All tests
pytest tests/unit/ -v               # Unit tests only

# Evaluation
python evaluation/quick_validation.py  # Quick check
python evaluation/run_evaluation.py    # Full evaluation

# Examples
python examples/demo_multimodal_correlation.py  # Interactive demo

# Development
black src/                          # Format code
ruff check src/                     # Lint code
```

## Documentation

- **README.md** - Project overview
- **tests/README.md** - Test suite guide
- **evaluation/README.md** - Evaluation framework
- **src/ORGANIZATION.md** - Src directory structure
- **FINAL_PROJECT_STATUS.md** - Complete project status

## Troubleshooting

### Import Errors

Make sure you installed the package:

```bash
pip install -e .
```

### NATS Connection Errors

Start NATS server:

```bash
docker compose up -d nats
```

### Test Failures

Reinstall with dev dependencies:

```bash
pip install -e ".[dev]"
```

## Next Steps

1. Read `README.md` for project overview
2. Run `pytest tests/` to verify everything works
3. Try `python examples/demo_multimodal_correlation.py`
4. Explore the code in `src/` directory

---

**That's it!** You're ready to use the network anomaly detection system.

For more details, see:
- Full documentation: `docs/`
- API reference: Code docstrings in `src/`
- Academic paper: `docs/presentations/`
