"""
Network Dashboard Startup Script
Starts the comprehensive network anomaly detection dashboard with all simulators
"""

import subprocess
import sys
import time
import signal
from pathlib import Path

class DashboardManager:
    """Manages all dashboard components"""
    
    def __init__(self):
        self.processes = []
        self.base_dir = Path(__file__).parent
        self.project_root = self.base_dir.parent.parent
        
    def start_component(self, script_name, description, cwd=None):
        """Start a dashboard component"""
        if cwd:
            script_path = cwd / script_name
        else:
            script_path = self.base_dir / script_name
        
        if not script_path.exists():
            print(f"❌ {description} script not found: {script_path}")
            return None
        
        try:
            print(f"🚀 Starting {description}...")
            process = subprocess.Popen([
                sys.executable, str(script_path)
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd)
            
            self.processes.append({
                'process': process,
                'name': description,
                'script': script_name,
                'cwd': cwd
            })
            
            print(f"✅ {description} started (PID: {process.pid})")
            return process
            
        except Exception as e:
            print(f"❌ Failed to start {description}: {e}")
            return None
    
    def start_all_components(self):
        """Start all dashboard components"""
        print("🌐 Starting Network Anomaly Detection Dashboard Components")
        print("=" * 70)
        
        # Start existing SNMP simulator
        snmp_sim_path = self.project_root / "src" / "simulators"
        self.start_component('snmp_simulator.py', 'SNMP Data Simulator', snmp_sim_path)
        time.sleep(2)
        
        # Start existing syslog simulator
        self.start_component('syslog_simulator.py', 'Syslog Message Simulator', snmp_sim_path)
        time.sleep(2)
        
        print("\n" + "=" * 70)
        print("🎯 All background components started!")
        print("\n📊 To start the main dashboard, run:")
        print("   streamlit run src/dash/network_dashboard.py")
        print("\n🔗 Dashboard will be available at: http://localhost:8501")
        print("\n📋 Available Data Sources:")
        print("   • BGP Updates: bgp.updates (from lab BGP data collector)")
        print("   • SNMP Metrics: snmp.metrics (from SNMP simulator)")
        print("   • Syslog Messages: syslog.messages (from syslog simulator)")
        print("   • Anomalies: anomalies.detected (from ML pipeline)")
        print("\n⏹️  Press Ctrl+C to stop all components")
        
    def stop_all_components(self):
        """Stop all dashboard components"""
        print("\n🛑 Stopping all dashboard components...")
        
        for component in self.processes:
            try:
                process = component['process']
                if process.poll() is None:  # Process is still running
                    process.terminate()
                    process.wait(timeout=5)
                    print(f"✅ Stopped {component['name']}")
                else:
                    print(f"⚠️  {component['name']} was already stopped")
            except subprocess.TimeoutExpired:
                process.kill()
                print(f"🔨 Force killed {component['name']}")
            except Exception as e:
                print(f"❌ Error stopping {component['name']}: {e}")
        
        self.processes.clear()
        print("🏁 All components stopped")

def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    print("\n\n🛑 Received interrupt signal...")
    manager.stop_all_components()
    sys.exit(0)

if __name__ == "__main__":
    manager = DashboardManager()
    
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        manager.start_all_components()
        
        # Keep the script running
        while True:
            # Check if any processes have died
            for component in manager.processes[:]:
                process = component['process']
                if process.poll() is not None:
                    print(f"⚠️  {component['name']} has stopped unexpectedly")
                    manager.processes.remove(component)
            
            if not manager.processes:
                print("⚠️  All background components have stopped")
                break
                
            time.sleep(5)
            
    except KeyboardInterrupt:
        pass
    finally:
        manager.stop_all_components()


