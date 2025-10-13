#!/usr/bin/env python3
"""
Complete Multi-Modal System Example

This script demonstrates the complete integration of:
1. SNMP Simulator → generates realistic hardware metrics
2. Isolation Forest → detects hardware anomalies
3. Multi-Modal Pipeline → fuses signals for comprehensive detection

Run this to see the complete system in action!
"""

import asyncio
import logging

from anomaly_detection.simulators.snmp_simulator import SNMPFailureSimulator

# Note: IntegratedMultiModalPipeline may need to be implemented or this script may be outdated

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


async def run_snmp_simulator():
    """Run SNMP simulator in background."""
    logger.info("🔧 Starting SNMP Simulator...")
    simulator = SNMPFailureSimulator("src/configs/snmp_config.yml")

    try:
        await simulator.run_simulation()
    except asyncio.CancelledError:
        logger.info("SNMP Simulator stopped")
        simulator.stop_simulation()


async def run_pipeline():
    """Run the integrated multi-modal pipeline."""
    logger.info("[INFO] Starting Integrated Multi-Modal Pipeline...")
    # TODO: IntegratedMultiModalPipeline not yet implemented
    # Use run_multimodal_correlation.py instead for full system demo
    logger.warning("  [WARN] IntegratedMultiModalPipeline not implemented")
    logger.info("  [INFO] Use 'python examples/run_multimodal_correlation.py' instead")

    try:
        await asyncio.sleep(1)  # Placeholder
    except asyncio.CancelledError:
        logger.info("Pipeline stopped")


async def main():
    """Run complete system."""
    print("=" * 70)
    print("  Multi-Modal Network Anomaly Detection System")
    print("  BGP (Matrix Profile) + SNMP (Isolation Forest) + Syslog")
    print("=" * 70)
    print()
    print("📋 Components:")
    print("  ✅ SNMP Simulator - Generating realistic hardware metrics")
    print("  ✅ Isolation Forest - Detecting hardware anomalies")
    print("  ✅ Multi-Modal Fusion - Combining signals")
    print()
    print("🎯 What to expect:")
    print("  • Normal operation for ~2 minutes (building baseline)")
    print("  • Random hardware failures injected (~8% probability)")
    print("  • Real-time anomaly detection with confidence scores")
    print("  • Multi-modal alerts when confirmed by multiple sources")
    print()
    print("📊 Watch for:")
    print("  🔴 SNMP Anomaly detected! - Single source detection")
    print("  🚨 MULTI-MODAL ALERT - Confirmed failure (high confidence)")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 70)
    print()

    # Wait for user to be ready
    await asyncio.sleep(2)

    # Create tasks
    simulator_task = asyncio.create_task(run_snmp_simulator())
    pipeline_task = asyncio.create_task(run_pipeline())

    # Wait for both tasks
    try:
        await asyncio.gather(simulator_task, pipeline_task)
    except KeyboardInterrupt:
        print()
        print("=" * 70)
        print("  Shutting down system...")
        print("=" * 70)

        # Cancel tasks
        simulator_task.cancel()
        pipeline_task.cancel()

        # Wait for cleanup
        await asyncio.gather(simulator_task, pipeline_task, return_exceptions=True)

        print()
        print("✅ System stopped cleanly")


if __name__ == "__main__":
    # Check if NATS is running
    print("\n🔍 Checking prerequisites...")
    print("  • NATS message bus should be running on localhost:4222")
    print("    If not running, start with: docker run -p 4222:4222 nats:latest")
    print()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n✅ Stopped")
