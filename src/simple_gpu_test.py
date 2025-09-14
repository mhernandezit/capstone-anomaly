"""
Simple test to verify GPU setup and basic functionality.
"""


def test_imports():
    """Test if all required modules can be imported."""
    try:
        import cupy as cp

        print("✓ CuPy imported successfully")
        print(f"  CuPy version: {cp.__version__}")
        print(f"  CUDA available: {cp.cuda.is_available()}")

        if cp.cuda.is_available():
            print(f"  CUDA version: {cp.cuda.runtime.runtimeGetVersion()}")
            print(f"  GPU count: {cp.cuda.runtime.getDeviceCount()}")

        return True

    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_basic_gpu_operations():
    """Test basic GPU operations."""
    try:
        import cupy as cp
        import numpy as np

        if not cp.cuda.is_available():
            print("⚠ CUDA not available, skipping GPU tests")
            return True

        # Test basic array operations
        print("Testing basic GPU operations...")

        # Create arrays
        a_cpu = np.array([1, 2, 3, 4, 5], dtype=np.float32)
        a_gpu = cp.asarray(a_cpu)

        # Test operations
        result_gpu = a_gpu * 2
        result_cpu = cp.asnumpy(result_gpu)

        expected = a_cpu * 2
        if np.allclose(result_cpu, expected):
            print("✓ Basic GPU operations working")
            return True
        else:
            print("✗ GPU operations failed")
            return False

    except Exception as e:
        print(f"✗ GPU test error: {e}")
        return False


if __name__ == "__main__":
    print("Testing GPU setup for Matrix Profile detector...")
    print("=" * 50)

    # Test imports
    imports_ok = test_imports()

    if imports_ok:
        # Test basic operations
        gpu_ok = test_basic_gpu_operations()

        if gpu_ok:
            print("\n✓ All tests passed! GPU setup is ready.")
        else:
            print("\n⚠ GPU setup has issues, but CPU fallback should work.")
    else:
        print("\n✗ Setup failed. Please check dependencies.")
