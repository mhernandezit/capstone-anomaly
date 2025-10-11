#!/usr/bin/env python3
"""
Real ML Dashboard Launcher

Launches the dashboard that uses ACTUAL Matrix Profile and Isolation Forest algorithms.
"""

import subprocess
import sys
from pathlib import Path

def main():
    """Launch the real ML dashboard"""
    dashboard_path = Path("src/anomaly_detection/dash/real_ml_dashboard.py")
    
    if not dashboard_path.exists():
        print(f"[ERROR] Dashboard not found at: {dashboard_path}")
        sys.exit(1)
    
    print("=" * 80)
    print("  Real ML Network Anomaly Detection Dashboard")
    print("=" * 80)
    print()
    print("[INFO] This dashboard uses REAL machine learning algorithms:")
    print("  - Matrix Profile: Actual time-series discord detection")
    print("  - Isolation Forest: Real 150-tree outlier detection")
    print("  - Authentic processing times (30-60 seconds)")
    print("  - Genuine confidence scores from algorithms")
    print()
    print("[INFO] Dashboard will open at: http://localhost:8501")
    print("[INFO] Processing will be slower than simulated version")
    print("[INFO] First run will initialize ML models (takes ~30 seconds)")
    print()
    print("=" * 80)
    print()
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run",
            str(dashboard_path),
            "--server.headless", "true",
        ])
    except KeyboardInterrupt:
        print("\n\n[INFO] Dashboard stopped by user")
    except Exception as e:
        print(f"\n[ERROR] Failed to launch dashboard: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

