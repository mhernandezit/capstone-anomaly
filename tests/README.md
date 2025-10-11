# Test Suite

This directory contains the test suite for the network anomaly detection system, organized using pytest conventions.

## Directory Structure

```
tests/
├── conftest.py           # Pytest configuration and shared fixtures
├── unit/                 # Unit tests for individual components
├── integration/          # Integration tests for pipelines
├── fixtures/             # Test data and fixtures
└── smoke/               # Quick smoke tests for validation
```

## Prerequisites

Install the package in editable mode (required for tests to work):

```bash
pip install -e .
```

Or install with dev dependencies:

```bash
pip install -e ".[dev]"
```

## Running Tests

### All Tests

```bash
# Run entire test suite
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

### By Category

```bash
# Unit tests (fast, < 10 seconds)
pytest tests/unit/ -v

# Integration tests (slower, < 60 seconds)
pytest tests/integration/ -v

# Smoke tests (quick validation)
pytest tests/smoke/ -v
```

### By Marker

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run smoke tests
pytest -m smoke

# Skip slow tests
pytest -m "not slow"
```

### Specific Tests

```bash
# Test specific file
pytest tests/unit/test_isolation_forest.py -v

# Test specific class
pytest tests/unit/test_isolation_forest.py::TestIsolationForestDetector -v

# Test specific function
pytest tests/unit/test_matrix_profile.py::TestStumpyBasic::test_stumpy_basic_calculation -v
```

## Test Categories

### Unit Tests (`unit/`)

Fast, isolated tests for individual components:

- `test_isolation_forest.py` - Isolation Forest detector tests
- `test_matrix_profile.py` - Matrix Profile/stumpy tests

**Characteristics:**
- Run in < 10 seconds total
- No external dependencies (NATS, files, etc.)
- Test single functions/classes
- Use mocked data

### Integration Tests (`integration/`)

End-to-end pipeline tests:

- `test_multimodal.py` - Full multimodal correlation pipeline

**Characteristics:**
- Run in < 60 seconds total
- May use temporary files
- Test component interactions
- Validate full workflows

### Smoke Tests (`smoke/`)

Quick validation tests:

- `test_nats_connection.py` - NATS connectivity and basic operations
- `test_imports.py` - Core module imports

**Characteristics:**
- Run in < 5 seconds total
- Check basic functionality
- Validate environment setup
- Useful for CI/CD pipelines

### Fixtures (`fixtures/`)

Reusable test data:

- `bgp_updates.jsonl` - Sample BGP updates
- `snmp_metrics.csv` - Sample SNMP metrics
- `syslog_messages.jsonl` - Sample syslog messages

## Writing New Tests

### Unit Test Template

```python
"""Unit tests for [Component]."""
import pytest
from src.models.your_module import YourClass


@pytest.mark.unit
class TestYourClass:
    """Test suite for YourClass."""
    
    def test_initialization(self):
        """Test component initializes correctly."""
        obj = YourClass(param=value)
        assert obj.param == value
    
    def test_normal_operation(self, sample_fixture):
        """Test normal operation."""
        result = obj.process(sample_fixture)
        assert result is not None
```

### Integration Test Template

```python
"""Integration tests for [Pipeline]."""
import pytest


@pytest.mark.integration
class TestYourPipeline:
    """Test suite for pipeline integration."""
    
    def test_end_to_end(self):
        """Test complete pipeline flow."""
        # Setup
        pipeline = YourPipeline()
        
        # Execute
        result = pipeline.run(test_data)
        
        # Verify
        assert result.success
```

## Available Fixtures

Defined in `conftest.py`:

- `sample_bgp_update` - Normal BGP update
- `sample_bgp_anomaly` - BGP update with anomaly
- `sample_snmp_metrics` - Normal SNMP metrics
- `sample_snmp_anomaly` - SNMP metrics with anomaly
- `sample_topology` - Network topology for testing
- `sample_roles_config` - Device roles configuration
- `fixtures_dir` - Path to fixtures directory

Example usage:

```python
def test_with_fixture(sample_bgp_update):
    """Test using a fixture."""
    assert sample_bgp_update["peer"] == "10.0.1.1"
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run smoke tests
        run: pytest tests/smoke/ -v
      - name: Run unit tests
        run: pytest tests/unit/ -v --cov=src
      - name: Run integration tests
        run: pytest tests/integration/ -v
```

## Pytest Configuration

### Markers

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.smoke` - Smoke tests
- `@pytest.mark.slow` - Tests that take longer to run
- `@pytest.mark.asyncio` - Async tests

### Command Line Options

```bash
# Show print statements
pytest -s

# Stop on first failure
pytest -x

# Run last failed tests
pytest --lf

# Run tests matching pattern
pytest -k "test_isolation"

# Parallel execution (requires pytest-xdist)
pytest -n auto
```

## Troubleshooting

### Import Errors

Ensure you're running pytest from the project root:

```bash
cd /path/to/capstone-anomaly
pytest tests/
```

### NATS Connection Errors

For smoke tests requiring NATS:

```bash
# Start NATS server
docker compose up -d nats

# Or use Docker directly
docker run -p 4222:4222 nats:latest
```

### Missing Dependencies

```bash
# Install test dependencies
pip install -r requirements.txt

# Install pytest plugins
pip install pytest pytest-asyncio pytest-cov
```

### GPU Tests Failing

GPU tests (Matrix Profile acceleration) require CUDA:

```bash
# Skip GPU tests if CUDA not available
pytest -m "not slow"
```

## Coverage Reports

```bash
# Generate HTML coverage report
pytest tests/ --cov=src --cov-report=html

# Open report
open htmlcov/index.html  # macOS
start htmlcov/index.html # Windows
xdg-open htmlcov/index.html # Linux
```

## Comparison: Tests vs Evaluation

| Directory | Purpose | Focus | Runtime |
|-----------|---------|-------|---------|
| `tests/` | Verify code correctness | Algorithm logic | < 2 min |
| `evaluation/` | Measure system performance | Metrics (F1, delay, Hit@k) | 5-30 min |

**Use tests/** for:
- Verifying bug fixes
- Testing new features
- CI/CD pipelines
- Development workflow

**Use evaluation/** for:
- Academic paper metrics
- Performance benchmarks
- Scenario-based validation
- System evaluation

## Best Practices

1. **Keep tests fast** - Unit tests should run in seconds
2. **Use fixtures** - Avoid duplicating test data setup
3. **Test one thing** - Each test should verify one behavior
4. **Clear names** - Test names should describe what they test
5. **Arrange-Act-Assert** - Follow the AAA pattern
6. **No external deps** - Unit tests should not require NATS, files, etc.
7. **Mark appropriately** - Use pytest markers for organization

## Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Testing Best Practices](https://docs.pytest.org/en/latest/goodpractices.html)
- Project evaluation framework: `evaluation/README.md`

## Quick Reference

```bash
# Common commands
pytest tests/                     # All tests
pytest tests/unit/ -v             # Unit tests, verbose
pytest tests/smoke/               # Quick validation
pytest -m "unit and not slow"     # Fast unit tests only
pytest --lf                       # Re-run failed tests
pytest -k "isolation"             # Tests matching pattern
pytest --cov=src                  # With coverage
```
