"""
Test script for CPU Matrix Profile detector - no GPU dependencies.
"""

import time
import numpy as np
import logging
from models.cpu_mp_detector import create_cpu_mp_detector
from utils.schema import FeatureBin

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_test_data(num_bins: int = 200, anomaly_bins: list = None) -> list:
    """Generate synthetic BGP feature data for testing."""
    if anomaly_bins is None:
        anomaly_bins = [50, 120, 180]  # Default anomaly locations

    feature_bins = []
    base_time = 1609459200  # 2021-01-01 00:00:00 UTC

    for i in range(num_bins):
        # Base values
        ann_total = np.random.poisson(10)
        wdr_total = np.random.poisson(5)
        as_path_churn = np.random.poisson(2)

        # Add anomalies
        if i in anomaly_bins:
            ann_total += np.random.poisson(50)  # Spike in announcements
            wdr_total += np.random.poisson(100)  # Spike in withdrawals
            as_path_churn += np.random.poisson(20)  # Spike in path churn

        # Create feature bin
        fb = FeatureBin(
            bin_start=base_time + (i * 30),
            bin_end=base_time + ((i + 1) * 30),
            totals={"ann_total": ann_total, "wdr_total": wdr_total, "as_path_churn": as_path_churn},
            peers={
                f"peer_{j}": {
                    "ann": np.random.poisson(2),
                    "wdr": np.random.poisson(1),
                    "as_path_churn": np.random.poisson(1),
                }
                for j in range(5)  # 5 peers
            },
        )
        feature_bins.append(fb)

    return feature_bins


def test_cpu_detector():
    """Test CPU detector performance and accuracy."""
    logger.info("Testing CPU Matrix Profile detector...")

    # Create detector
    detector = create_cpu_mp_detector(
        window_bins=32,
        series_keys=["wdr_total", "ann_total", "as_path_churn"],
        discord_threshold=2.0,
        mp_library="auto",  # Let it choose the best available library
    )

    # Generate test data
    test_data = generate_test_data(num_bins=500, anomaly_bins=[100, 200, 350, 450])

    # Test processing
    start_time = time.time()
    results = []

    for i, fb in enumerate(test_data):
        result = detector.update(fb)
        results.append(result)

        if result["is_anomaly"]:
            logger.info(
                f"Anomaly detected at bin {i}: "
                f"confidence={result['anomaly_confidence']:.2f}, "
                f"series={result['detected_series']}"
            )

    processing_time = time.time() - start_time

    # Analyze results
    anomalies_detected = sum(1 for r in results if r["is_anomaly"])
    true_anomalies = len([100, 200, 350, 450])  # Known anomaly positions

    logger.info("Performance Results:")
    logger.info(f"  Processing time: {processing_time:.2f} seconds")
    logger.info(f"  Bins processed: {len(test_data)}")
    logger.info(f"  Processing rate: {len(test_data)/processing_time:.1f} bins/sec")
    logger.info(f"  Anomalies detected: {anomalies_detected}")
    logger.info(f"  True anomalies: {true_anomalies}")

    # Get detector status
    status = detector.get_status()
    logger.info("Detector Status:")
    logger.info(f"  MP Library: {status['mp_library']}")
    logger.info(f"  Window bins: {status['window_bins']}")
    logger.info(f"  Series keys: {status['series_keys']}")
    logger.info(f"  Buffer sizes: {status['buffer_sizes']}")

    return {
        "processing_time": processing_time,
        "bins_processed": len(test_data),
        "processing_rate": len(test_data) / processing_time,
        "anomalies_detected": anomalies_detected,
        "mp_library": status["mp_library"],
    }


def test_different_libraries():
    """Test different Matrix Profile libraries."""
    logger.info("Testing different Matrix Profile libraries...")

    libraries = ["auto", "mpf", "stumpy", "fallback"]
    results = {}

    for lib in libraries:
        try:
            logger.info(f"Testing {lib} library...")
            detector = create_cpu_mp_detector(
                window_bins=16, mp_library=lib  # Smaller for faster testing
            )

            # Quick test with small dataset
            test_data = generate_test_data(num_bins=50, anomaly_bins=[20, 40])

            start_time = time.time()
            for fb in test_data:
                detector.update(fb)
            processing_time = time.time() - start_time

            status = detector.get_status()
            results[lib] = {
                "success": True,
                "processing_time": processing_time,
                "mp_library": status["mp_library"],
            }

            logger.info(f"  {lib}: {processing_time:.2f}s, library={status['mp_library']}")

        except Exception as e:
            logger.error(f"  {lib}: Failed - {e}")
            results[lib] = {"success": False, "error": str(e)}

    return results


def main():
    """Run all tests."""
    logger.info("Starting CPU Matrix Profile detector tests...")

    try:
        # Test 1: Library availability
        logger.info("=" * 50)
        logger.info("Test 1: Library Availability")
        logger.info("=" * 50)
        library_results = test_different_libraries()

        # Test 2: Performance test
        logger.info("=" * 50)
        logger.info("Test 2: Performance Test")
        logger.info("=" * 50)
        perf_results = test_cpu_detector()

        # Summary
        logger.info("=" * 50)
        logger.info("Test Summary")
        logger.info("=" * 50)
        logger.info(f"Best library: {perf_results['mp_library']}")
        logger.info(f"Processing rate: {perf_results['processing_rate']:.1f} bins/sec")
        logger.info(f"Anomalies detected: {perf_results['anomalies_detected']}")

        # Library status
        logger.info("Library Status:")
        for lib, result in library_results.items():
            if result["success"]:
                logger.info(f"  {lib}: ✓ ({result['mp_library']})")
            else:
                logger.info(f"  {lib}: ✗ ({result['error']})")

    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise


if __name__ == "__main__":
    main()
