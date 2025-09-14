"""
Debug script to test stumpy Matrix Profile functionality
"""

def test_stumpy():
    """Test stumpy import and basic functionality."""
    try:
        print("Testing stumpy import...")
        import stumpy as mp
        print("✓ stumpy imported successfully")
        
        print("Testing stumpy version...")
        try:
            version = mp.__version__
            print(f"✓ stumpy version: {version}")
        except AttributeError:
            print("⚠ No version info available")
        
        print("Testing basic computation...")
        import numpy as np
        
        # Simple test data
        test_data = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], dtype=np.float64)
        print(f"Test data: {test_data}")
        
        # Test computation
        result = mp.compute(test_data, windows=3)
        print("✓ stumpy computation successful")
        print(f"Matrix Profile values: {result['mp']}")
        print(f"Discord score: {np.max(result['mp'])}")
        
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

def test_alternatives():
    """Test alternative Matrix Profile libraries."""
    print("\nTesting alternative libraries...")
    
    # Test stumpy
    try:
        import stumpy
        print("✓ stumpy imported successfully")
        
        import numpy as np
        test_data = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        result = stumpy.stump(test_data, m=3)
        print("✓ stumpy computation successful")
        print(f"Stumpy result shape: {result.shape}")
        
    except ImportError as e:
        print(f"✗ stumpy import error: {e}")
    except Exception as e:
        print(f"✗ stumpy computation error: {e}")

if __name__ == "__main__":
    print("Stumpy Matrix Profile Debug Test")
    print("=" * 40)
    
    success = test_stumpy()
    test_alternatives()
    
    if success:
        print("\n✓ Stumpy Matrix Profile is working correctly!")
    else:
        print("\n✗ Stumpy Matrix Profile has issues, but alternatives are available.")
