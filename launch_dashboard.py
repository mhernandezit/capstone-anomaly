#!/usr/bin/env python3
"""
Dashboard Launcher

Starts the modern network anomaly detection dashboard with dual ML pipeline visualization.
"""

import subprocess
import sys
from pathlib import Path

def main():
    """Launch the Streamlit dashboard"""
    dashboard_path = Path("src/anomaly_detection/dash/modern_dashboard.py")
    
    if not dashboard_path.exists():
        print(f"[ERROR] Dashboard not found at: {dashboard_path}")
        sys.exit(1)
    
    print("=" * 80)
    print("  Network Anomaly Detection Dashboard")
    print("=" * 80)
    print()
    print("[INFO] Launching Streamlit dashboard...")
    print("[INFO] Dashboard features:")
    print("  - Animated network topology with anomaly indicators")
    print("  - Matrix Profile pipeline visualization (BGP)")
    print("  - Isolation Forest pipeline visualization (SNMP)")
    print("  - Real-time detection timeline")
    print("  - Active alerts dashboard")
    print()
    print("[INFO] Dashboard will open in your browser at: http://localhost:8501")
    print("[INFO] Press Ctrl+C to stop the dashboard")
    print()
    print("=" * 80)
    print()
    
    try:
        # Launch Streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run",
            str(dashboard_path),
            "--server.headless", "true",
        ])
    except KeyboardInterrupt:
        print("\n\n[INFO] Dashboard stopped by user")
    except Exception as e:
        print(f"\n[ERROR] Failed to launch dashboard: {e}")
        print("\n[INFO] Try installing Streamlit:")
        print("  pip install streamlit plotly networkx")
        sys.exit(1)


if __name__ == "__main__":
    main()

