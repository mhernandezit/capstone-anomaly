"""
Simple stumpy test that works from project root
"""


def test_stumpy_basic():
    """Test basic stumpy functionality."""
    try:
        print("Testing stumpy...")
        import stumpy
        import numpy as np

        # Create test data with correct dtype
        test_data = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], dtype=np.float64)
        print(f"Test data: {test_data}")

        # Test Matrix Profile calculation
        result = stumpy.stump(test_data, m=3)
        print(f"✓ Stumpy works! Result shape: {result.shape}")
        print(f"Matrix Profile values: {result[:, 0]}")
        print(f"Max discord score: {np.max(result[:, 0]):.3f}")

        return True

    except Exception as e:
        print(f"✗ Stumpy test failed: {e}")
        return False


def test_gpu_availability():
    """Test GPU availability."""
    try:
        print("\nTesting GPU...")
        import cupy as cp

        if cp.cuda.is_available():
            print("✓ CUDA available")
            print(f"GPU count: {cp.cuda.runtime.getDeviceCount()}")

            # Test basic GPU operation
            test_array = cp.array([1, 2, 3, 4, 5], dtype=cp.float64)
            result = test_array * 2
            print(f"✓ GPU operations work: {cp.asnumpy(result)}")
            return True
        else:
            print("⚠ CUDA not available")
            return False

    except Exception as e:
        print(f"✗ GPU test failed: {e}")
        return False


if __name__ == "__main__":
    print("Simple Stumpy + GPU Test")
    print("=" * 30)

    stumpy_ok = test_stumpy_basic()
    gpu_ok = test_gpu_availability()

    print("\n" + "=" * 30)
    print("Results:")
    print(f"Stumpy: {'✓' if stumpy_ok else '✗'}")
    print(f"GPU: {'✓' if gpu_ok else '✗'}")

    if stumpy_ok:
        print("\n✓ Ready to use stumpy for Matrix Profile!")
    else:
        print("\n✗ Need to fix stumpy issues")
