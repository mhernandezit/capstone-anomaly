#!/usr/bin/env python3
"""
Enhanced Multi-Modal Network Failure Detection Pipeline

This script demonstrates the expanded capabilities addressing the professor's feedback
to move beyond just BGP events to include hardware failures, environmental issues,
and comprehensive network failure detection.

Key Enhancements:
1. SNMP simulation for hardware failures (bad parts, cables, optics)
2. Multi-modal data fusion (BGP + Syslog + SNMP)
3. Comprehensive failure taxonomy
4. Environmental monitoring
5. Real-time correlation analysis

Usage:
    python src/run_enhanced_pipeline.py [--demo-mode] [--config CONFIG_FILE]
"""

import asyncio
import argparse
import logging
import signal
import sys
from pathlib import Path
from src.integration.multi_modal_pipeline import MultiModalPipeline

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class EnhancedPipelineDemo:
    """
    Demonstration of the enhanced multi-modal pipeline capabilities.

    This class showcases how the expanded system can detect and correlate
    various types of network failures beyond just BGP events.
    """

    def __init__(self, config_path: str = None):
        """Initialize the enhanced pipeline demo."""
        self.config_path = config_path or "src/configs/multi_modal_config.yml"
        self.pipeline = None
        self.demo_scenarios = [
            {
                "name": "Optical Transceiver Degradation",
                "description": "Simulates gradual optical power loss in SFP/QSFP modules",
                "expected_signals": ["SNMP error rates", "Interface flapping", "Syslog alerts"],
                "detection_time": "2-3 minutes",
            },
            {
                "name": "Memory Pressure with BGP Impact",
                "description": "Memory exhaustion affecting BGP route processing",
                "expected_signals": [
                    "SNMP memory metrics",
                    "BGP convergence delays",
                    "System logs",
                ],
                "detection_time": "1-2 minutes",
            },
            {
                "name": "Thermal Runaway",
                "description": "Overheating causing system instability",
                "expected_signals": ["Temperature sensors", "Fan speed changes", "CPU throttling"],
                "detection_time": "3-4 minutes",
            },
            {
                "name": "Cable Intermittent Connection",
                "description": "Loose cable causing intermittent packet loss",
                "expected_signals": ["Interface errors", "Link flapping", "Traffic drops"],
                "detection_time": "1-2 minutes",
            },
            {
                "name": "Power Supply Instability",
                "description": "Voltage fluctuations affecting multiple components",
                "expected_signals": [
                    "Power metrics",
                    "Multiple device correlation",
                    "Environmental alerts",
                ],
                "detection_time": "2-3 minutes",
            },
        ]

    async def initialize_pipeline(self):
        """Initialize the multi-modal pipeline."""
        print("🚀 Initializing Enhanced Multi-Modal Pipeline")
        print("=" * 60)

        self.pipeline = MultiModalPipeline(self.config_path)
        await self.pipeline.initialize()

        print("✅ Pipeline initialized successfully")
        print(f"📊 Configuration loaded from: {self.config_path}")
        print()

    def display_capabilities(self):
        """Display the enhanced capabilities of the system."""
        print("🎯 Enhanced Failure Detection Capabilities")
        print("=" * 60)
        print()

        print("📡 Data Sources:")
        print("  • BGP Updates (existing)")
        print("  • Syslog Messages (existing)")
        print("  • SNMP Metrics (NEW)")
        print("  • Environmental Sensors (NEW)")
        print()

        print("🔍 Failure Types Detected:")
        print("  Network Layer:")
        print("    - BGP routing anomalies")
        print("    - OSPF/IS-IS convergence issues")
        print("    - Route leaks and hijacks")
        print()
        print("  Hardware Layer (NEW):")
        print("    - Optical transceiver failures")
        print("    - Memory pressure and leaks")
        print("    - CPU thermal throttling")
        print("    - Storage subsystem issues")
        print()
        print("  Physical Layer (NEW):")
        print("    - Cable degradation/breaks")
        print("    - Connector contamination")
        print("    - Signal attenuation")
        print("    - Intermittent connections")
        print()
        print("  Environmental (NEW):")
        print("    - Thermal runaway")
        print("    - Power supply instability")
        print("    - Cooling system failures")
        print("    - Humidity/dust issues")
        print()

        print("🧠 Analysis Techniques:")
        print("  • Multi-modal data fusion")
        print("  • Temporal correlation analysis")
        print("  • Spatial failure propagation")
        print("  • Machine learning anomaly detection")
        print("  • Topology-aware impact assessment")
        print()

    def display_demo_scenarios(self):
        """Display the demonstration scenarios."""
        print("🎭 Demonstration Scenarios")
        print("=" * 60)
        print()

        for i, scenario in enumerate(self.demo_scenarios, 1):
            print(f"{i}. {scenario['name']}")
            print(f"   Description: {scenario['description']}")
            print(f"   Expected Signals: {', '.join(scenario['expected_signals'])}")
            print(f"   Detection Time: {scenario['detection_time']}")
            print()

    async def run_demo_mode(self):
        """Run the pipeline in demonstration mode."""
        print("🎪 Starting Demo Mode")
        print("=" * 60)
        print()

        print("The system will now:")
        print("1. Start SNMP simulation with hardware failures")
        print("2. Generate realistic BGP and syslog data")
        print("3. Inject various failure scenarios")
        print("4. Demonstrate multi-modal correlation")
        print("5. Show real-time alerts and analysis")
        print()

        print("📈 Watch for alerts showing:")
        print("  • Failure type classification")
        print("  • Multi-modal correlation scores")
        print("  • Affected device identification")
        print("  • Recommended remediation actions")
        print()

        # Start the pipeline
        pipeline_task = asyncio.create_task(self.pipeline.run_pipeline())

        # Monitor and display statistics
        try:
            while True:
                await asyncio.sleep(30)  # Update every 30 seconds
                stats = self.pipeline.get_pipeline_stats()

                print(f"📊 Pipeline Statistics (Runtime: {stats['runtime_minutes']:.1f} min)")
                print(f"   BGP Events: {stats['bgp_events_processed']}")
                print(f"   SNMP Metrics: {stats['snmp_metrics_processed']}")
                print(f"   Syslog Messages: {stats['syslog_events_processed']}")
                print(f"   Alerts Generated: {stats['alerts_generated']}")
                print(f"   Multi-Modal Detections: {stats['multi_modal_detections']}")
                print()

        except KeyboardInterrupt:
            print("\n🛑 Demo interrupted by user")
            pipeline_task.cancel()
            await self.pipeline.shutdown()

    async def run_production_mode(self):
        """Run the pipeline in production mode."""
        print("🏭 Starting Production Mode")
        print("=" * 60)
        print()

        print("Pipeline is running in production mode...")
        print("Press Ctrl+C to stop")
        print()

        # Set up signal handlers
        def signal_handler(signum, frame):
            print(f"\n📡 Received signal {signum}, shutting down...")
            raise KeyboardInterrupt

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        try:
            await self.pipeline.run_pipeline()
        except KeyboardInterrupt:
            print("🛑 Pipeline stopped")
        finally:
            await self.pipeline.shutdown()


async def main():
    """Main entry point for the enhanced pipeline."""
    parser = argparse.ArgumentParser(
        description="Enhanced Multi-Modal Network Failure Detection Pipeline"
    )
    parser.add_argument(
        "--demo-mode", action="store_true", help="Run in demonstration mode with detailed output"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="src/configs/multi_modal_config.yml",
        help="Path to configuration file",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level",
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Create and run demo
    demo = EnhancedPipelineDemo(args.config)

    try:
        # Display system information
        print("🌟 Enhanced Network Failure Detection System")
        print("=" * 60)
        print()
        print("Addressing Professor's Feedback:")
        print("✅ Expanded beyond BGP-only events")
        print("✅ Added hardware failure detection")
        print("✅ Included cable/optics monitoring")
        print("✅ Environmental anomaly detection")
        print("✅ Multi-modal data correlation")
        print()

        demo.display_capabilities()

        if args.demo_mode:
            demo.display_demo_scenarios()

        # Initialize pipeline
        await demo.initialize_pipeline()

        # Run appropriate mode
        if args.demo_mode:
            await demo.run_demo_mode()
        else:
            await demo.run_production_mode()

    except KeyboardInterrupt:
        print("\n👋 Shutting down enhanced pipeline")
    except Exception as e:
        print(f"\n❌ Error running pipeline: {e}")
        logging.exception("Pipeline error")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
