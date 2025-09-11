"""
Test script for GPU Matrix Profile detector performance and functionality.

This script tests the GPU acceleration and compares performance with CPU baseline.
"""

import time
import numpy as np
import logging
from python.models.gpu_mp_detector import create_gpu_mp_detector
from python.utils.schema import FeatureBin

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_test_data(num_bins: int = 200, anomaly_bins: list = None) -> list:
    """
    Generate synthetic BGP feature data for testing.
    
    Args:
        num_bins: Number of feature bins to generate
        anomaly_bins: List of bin indices where anomalies should occur
        
    Returns:
        List of FeatureBin objects
    """
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
            totals={
                'ann_total': ann_total,
                'wdr_total': wdr_total,
                'as_path_churn': as_path_churn
            },
            peers={
                f'peer_{j}': {
                    'ann': np.random.poisson(2),
                    'wdr': np.random.poisson(1),
                    'as_path_churn': np.random.poisson(1)
                }
                for j in range(5)  # 5 peers
            }
        )
        feature_bins.append(fb)
    
    return feature_bins


def test_gpu_detector_performance():
    """Test GPU detector performance and accuracy."""
    logger.info("Testing GPU Matrix Profile detector...")
    
    # Create detector
    detector = create_gpu_mp_detector(
        window_bins=32,
        series_keys=['wdr_total', 'ann_total', 'as_path_churn'],
        discord_threshold=2.0,
        gpu_memory_limit='1GB'
    )
    
    # Generate test data
    test_data = generate_test_data(num_bins=500, anomaly_bins=[100, 200, 350, 450])
    
    # Test processing
    start_time = time.time()
    results = []
    
    for i, fb in enumerate(test_data):
        result = detector.update(fb)
        results.append(result)
        
        if result['is_anomaly']:
            logger.info(f"Anomaly detected at bin {i}: "
                       f"confidence={result['anomaly_confidence']:.2f}, "
                       f"series={result['detected_series']}")
    
    processing_time = time.time() - start_time
    
    # Analyze results
    anomalies_detected = sum(1 for r in results if r['is_anomaly'])
    true_anomalies = len([100, 200, 350, 450])  # Known anomaly positions
    
    logger.info(f"Performance Results:")
    logger.info(f"  Processing time: {processing_time:.2f} seconds")
    logger.info(f"  Bins processed: {len(test_data)}")
    logger.info(f"  Processing rate: {len(test_data)/processing_time:.1f} bins/sec")
    logger.info(f"  Anomalies detected: {anomalies_detected}")
    logger.info(f"  True anomalies: {true_anomalies}")
    
    # Get detector status
    status = detector.get_status()
    logger.info(f"Detector Status:")
    logger.info(f"  GPU available: {status['gpu_available']}")
    logger.info(f"  Window bins: {status['window_bins']}")
    logger.info(f"  Series keys: {status['series_keys']}")
    logger.info(f"  Buffer sizes: {status['buffer_sizes']}")
    
    return {
        'processing_time': processing_time,
        'bins_processed': len(test_data),
        'processing_rate': len(test_data) / processing_time,
        'anomalies_detected': anomalies_detected,
        'gpu_available': status['gpu_available']
    }


def test_cpu_fallback():
    """Test CPU fallback when GPU is not available."""
    logger.info("Testing CPU fallback...")
    
    # Force CPU mode by setting GPU memory to 0
    detector = create_gpu_mp_detector(
        window_bins=32,
        series_keys=['wdr_total', 'ann_total', 'as_path_churn'],
        discord_threshold=2.0,
        gpu_memory_limit='0MB'  # Force CPU mode
    )
    
    # Generate smaller test dataset
    test_data = generate_test_data(num_bins=100, anomaly_bins=[30, 70])
    
    start_time = time.time()
    results = []
    
    for fb in test_data:
        result = detector.update(fb)
        results.append(result)
    
    processing_time = time.time() - start_time
    
    logger.info(f"CPU Fallback Results:")
    logger.info(f"  Processing time: {processing_time:.2f} seconds")
    logger.info(f"  Bins processed: {len(test_data)}")
    logger.info(f"  Processing rate: {len(test_data)/processing_time:.1f} bins/sec")
    
    return {
        'processing_time': processing_time,
        'bins_processed': len(test_data),
        'processing_rate': len(test_data) / processing_time
    }


def benchmark_gpu_vs_cpu():
    """Benchmark GPU vs CPU performance."""
    logger.info("Benchmarking GPU vs CPU performance...")
    
    # Test data
    test_data = generate_test_data(num_bins=1000, anomaly_bins=[200, 500, 800])
    
    # GPU test
    logger.info("Testing GPU performance...")
    gpu_detector = create_gpu_mp_detector(
        window_bins=64,
        gpu_memory_limit='2GB'
    )
    
    gpu_start = time.time()
    for fb in test_data:
        gpu_detector.update(fb)
    gpu_time = time.time() - gpu_start
    
    # CPU test
    logger.info("Testing CPU performance...")
    cpu_detector = create_gpu_mp_detector(
        window_bins=64,
        gpu_memory_limit='0MB'  # Force CPU
    )
    
    cpu_start = time.time()
    for fb in test_data:
        cpu_detector.update(fb)
    cpu_time = time.time() - cpu_start
    
    # Results
    speedup = cpu_time / gpu_time if gpu_time > 0 else 0
    
    logger.info(f"Benchmark Results:")
    logger.info(f"  GPU time: {gpu_time:.2f} seconds")
    logger.info(f"  CPU time: {cpu_time:.2f} seconds")
    logger.info(f"  Speedup: {speedup:.2f}x")
    logger.info(f"  GPU available: {gpu_detector.gpu_available}")
    
    return {
        'gpu_time': gpu_time,
        'cpu_time': cpu_time,
        'speedup': speedup,
        'gpu_available': gpu_detector.gpu_available
    }


def main():
    """Run all tests."""
    logger.info("Starting GPU Matrix Profile detector tests...")
    
    try:
        # Test 1: Basic functionality
        logger.info("=" * 50)
        logger.info("Test 1: Basic GPU Detector Performance")
        logger.info("=" * 50)
        gpu_results = test_gpu_detector_performance()
        
        # Test 2: CPU fallback
        logger.info("=" * 50)
        logger.info("Test 2: CPU Fallback")
        logger.info("=" * 50)
        cpu_results = test_cpu_fallback()
        
        # Test 3: Benchmark comparison
        logger.info("=" * 50)
        logger.info("Test 3: GPU vs CPU Benchmark")
        logger.info("=" * 50)
        benchmark_results = benchmark_gpu_vs_cpu()
        
        # Summary
        logger.info("=" * 50)
        logger.info("Test Summary")
        logger.info("=" * 50)
        logger.info(f"GPU available: {gpu_results['gpu_available']}")
        if gpu_results['gpu_available']:
            logger.info(f"GPU speedup: {benchmark_results['speedup']:.2f}x")
        logger.info(f"GPU processing rate: {gpu_results['processing_rate']:.1f} bins/sec")
        logger.info(f"CPU processing rate: {cpu_results['processing_rate']:.1f} bins/sec")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise


if __name__ == "__main__":
    main()
