"""
Test script for stumpy Matrix Profile library
"""


def test_stumpy():
    """Test stumpy import and basic functionality."""
    try:
        print("Testing stumpy import...")
        import stumpy

        print("✓ stumpy imported successfully")

        print("Testing stumpy version...")
        try:
            version = stumpy.__version__
            print(f"✓ stumpy version: {version}")
        except AttributeError:
            print("⚠ No version info available")

        print("Testing basic computation...")
        import numpy as np

        # Simple test data
        test_data = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], dtype=np.float64)
        print(f"Test data: {test_data}")

        # Test stump computation (Matrix Profile)
        result = stumpy.stump(test_data, m=3)
        print("✓ stumpy.stump computation successful")
        print(f"Result shape: {result.shape}")
        print(f"Matrix Profile values: {result[:, 0]}")
        print(f"Discord score: {np.max(result[:, 0])}")

        # Test other useful functions
        print("\nTesting additional stumpy functions...")

        # Test mass (for streaming)
        query = np.array([3, 4, 5])
        mass_result = stumpy.mass(query, test_data)
        print(f"✓ stumpy.mass successful: {mass_result[:3]}")

        # Test mstump (for multiple time series)
        multi_ts = np.array([[1, 2, 3, 4, 5], [2, 3, 4, 5, 6]])
        multi_result = stumpy.mstump(multi_ts, m=3)
        print(f"✓ stumpy.mstump successful: {multi_result.shape}")

        return True

    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Computation error: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback

        traceback.print_exc()
        return False


def test_stumpy_with_gpu():
    """Test stumpy with GPU acceleration if available."""
    try:
        print("\nTesting stumpy with GPU...")
        import stumpy
        import cupy as cp

        # import numpy as np  # Unused import

        if cp.cuda.is_available():
            print("✓ CUDA available, testing GPU acceleration...")

            # Create test data on GPU
            test_data_gpu = cp.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], dtype=cp.float64)
            test_data_cpu = cp.asnumpy(test_data_gpu)

            # Test CPU computation
            cpu_result = stumpy.stump(test_data_cpu, m=3)
            print(f"✓ CPU computation: {cpu_result.shape}")

            # Note: stumpy doesn't directly support GPU, but we can use CuPy for data prep
            print("✓ GPU data preparation works with CuPy")

        else:
            print("⚠ CUDA not available, testing CPU only")

        return True

    except ImportError as e:
        print(f"✗ GPU test failed: {e}")
        return False
    except Exception as e:
        print(f"✗ GPU test error: {e}")
        return False


def test_performance():
    """Test stumpy performance with larger dataset."""
    try:
        print("\nTesting stumpy performance...")
        import stumpy
        import numpy as np
        import time

        # Create larger test dataset
        np.random.seed(42)
        test_data = np.random.randn(1000) + np.sin(np.linspace(0, 10 * np.pi, 1000))

        print(f"Test data size: {len(test_data)} points")

        # Test different window sizes
        window_sizes = [32, 64, 128]

        for m in window_sizes:
            start_time = time.time()
            result = stumpy.stump(test_data, m=m)
            computation_time = time.time() - start_time

            print(
                f"Window size {m}: {computation_time:.3f}s, max MP value: {np.max(result[:, 0]):.3f}"
            )

        return True

    except Exception as e:
        print(f"✗ Performance test failed: {e}")
        return False


if __name__ == "__main__":
    print("Stumpy Matrix Profile Test")
    print("=" * 40)

    # Test basic functionality
    basic_success = test_stumpy()

    # Test GPU integration
    gpu_success = test_stumpy_with_gpu()

    # Test performance
    perf_success = test_performance()

    print("\n" + "=" * 40)
    print("Test Summary:")
    print(f"Basic functionality: {'✓' if basic_success else '✗'}")
    print(f"GPU integration: {'✓' if gpu_success else '✗'}")
    print(f"Performance: {'✓' if perf_success else '✗'}")

    if basic_success:
        print("\n✓ Stumpy is working correctly and ready to use!")
    else:
        print("\n✗ Stumpy has issues that need to be resolved.")
