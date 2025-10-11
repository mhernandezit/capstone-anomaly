"""Smoke tests for NATS connectivity."""

import asyncio

import pytest


@pytest.mark.smoke
@pytest.mark.asyncio
async def test_nats_server_running():
    """Test NATS server is accessible."""
    try:
        from nats.aio.client import Client as NATS

        nc = NATS()
        await asyncio.wait_for(nc.connect(servers=["nats://localhost:4222"]), timeout=5.0)
        await nc.close()
        assert True
    except asyncio.TimeoutError:
        pytest.fail("NATS server not responding within 5 seconds")
    except Exception as e:
        pytest.fail(f"NATS connection failed: {e}")


@pytest.mark.smoke
@pytest.mark.asyncio
async def test_publish_bgp_event():
    """Test publishing a BGP event to NATS."""
    try:
        import time

        from nats.aio.client import Client as NATS

        from anomaly_detection.utils.schema import BGPUpdate

        # Connect to NATS
        nc = NATS()
        await nc.connect(servers=["nats://localhost:4222"])

        # Create test event
        event = BGPUpdate(
            ts=int(time.time()),
            peer="10.0.1.1",
            type="UPDATE",
            announce=["192.168.1.0/24"],
            withdraw=None,
            attrs={"as_path": [65001, 65002]},
        )

        # Publish event
        await nc.publish("bgp.updates", event.model_dump_json().encode())
        await nc.flush()
        await nc.close()

        assert True
    except Exception as e:
        pytest.fail(f"Failed to publish BGP event: {e}")


@pytest.mark.smoke
def test_import_core_modules():
    """Test all core modules can be imported."""
    try:
        # Core detection modules
        # Correlation module
        from anomaly_detection.correlation.multimodal_correlator import (
            MultiModalCorrelator,  # noqa: F401
        )

        # Feature extraction
        from anomaly_detection.features.stream_features import FeatureAggregator  # noqa: F401
        from anomaly_detection.models.isolation_forest_detector import (
            IsolationForestDetector,  # noqa: F401
        )
        from anomaly_detection.models.matrix_profile_detector import (
            MatrixProfileDetector,  # noqa: F401
        )

        # Triage
        from anomaly_detection.triage.topology_triage import TopologyTriageSystem  # noqa: F401

        # Utils
        from anomaly_detection.utils.schema import BGPUpdate  # noqa: F401

        assert True
    except ImportError as e:
        pytest.fail(f"Failed to import core modules: {e}")


@pytest.mark.smoke
def test_stumpy_available():
    """Test Matrix Profile library is available."""
    try:
        import numpy as np
        import stumpy

        # Quick calculation to ensure it works
        test_data = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], dtype=np.float64)
        result = stumpy.stump(test_data, m=3)

        assert result is not None
        assert len(result) > 0
    except ImportError:
        pytest.fail("stumpy library not installed")
    except Exception as e:
        pytest.fail(f"stumpy calculation failed: {e}")


@pytest.mark.smoke
def test_sklearn_available():
    """Test scikit-learn is available."""
    try:
        import numpy as np
        from sklearn.ensemble import IsolationForest

        # Quick test
        X = np.random.rand(100, 10)
        clf = IsolationForest(n_estimators=10, random_state=42)
        clf.fit(X)
        predictions = clf.predict(X)

        assert len(predictions) == 100
    except ImportError:
        pytest.fail("scikit-learn not installed")
    except Exception as e:
        pytest.fail(f"IsolationForest test failed: {e}")
