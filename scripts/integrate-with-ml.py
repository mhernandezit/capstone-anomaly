#!/usr/bin/env python3
"""
Integration script to connect the containerlab environment with the ML pipeline.

This script:
1. Monitors BGP updates from the lab environment
2. Converts them to the format expected by the ML pipeline
3. Feeds them into the feature aggregator and Matrix Profile detector
"""

import asyncio
import json
import logging
import subprocess
import time
from pathlib import Path
import sys

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Import ML components
try:
    from src.utils.schema import BGPUpdate
    from src.features.stream_features import FeatureAggregator
    from src.models.gpu_mp_detector import GPUMPDetector
    from src.triage.impact import ImpactScorer

    logger.info("Successfully imported ML components")
except ImportError as e:
    logger.error(f"Failed to import ML components: {e}")
    sys.exit(1)


class LabMLIntegration:
    """
    Integrates the containerlab environment with the existing ML pipeline.

    This class connects to the NATS message bus to receive BGP updates from the
    Go-based BMP collector, processes them through the feature aggregator,
    and runs anomaly detection using Matrix Profile analysis.

    Attributes:
        feature_aggregator (FeatureAggregator): Aggregates BGP updates into time bins
        mp_detector (GPUMPDetector): Detects anomalies using Matrix Profile
        impact_scorer (ImpactScorer, optional): Scores the impact of detected anomalies
        stats (dict): Statistics tracking for monitoring and debugging
    """

    def __init__(self):
        """
        Initialize the ML integration components.

        Sets up the feature aggregator with 30-second bins, configures the
        GPU-based Matrix Profile detector, and loads the impact scoring system.
        """
        self.feature_aggregator = FeatureAggregator(bin_seconds=30)
        self.mp_detector = GPUMPDetector(
            window_bins=64,
            series_keys=["wdr_total", "ann_total", "as_path_churn"],
            discord_threshold=2.5,
        )

        # Load roles configuration for impact scoring
        try:
            import yaml

            with open("configs/roles.yml", "r") as f:
                roles_config = yaml.safe_load(f)
            self.impact_scorer = ImpactScorer(roles_config)
            logger.info("✓ Impact scorer initialized")
        except Exception as e:
            logger.warning(f" Could not initialize impact scorer: {e}")
            self.impact_scorer = None

        # Statistics
        self.stats = {
            "updates_processed": 0,
            "features_extracted": 0,
            "anomalies_detected": 0,
            "start_time": time.time(),
        }

    def parse_bgp_output(self, line):
        """
        Parse BGP monitoring output and convert to BGPUpdate format.

        This method is deprecated and kept for compatibility. The current
        implementation uses NATS messages from the BMP collector instead.

        Args:
            line (str): JSON-formatted BGP monitoring output line

        Returns:
            BGPUpdate or None: Parsed BGP update object, or None if parsing fails
        """
        try:
            # Parse JSON output from BGP monitoring
            data = json.loads(line.strip())

            # Extract BGP update information
            if "path" in data and "nlri" in data["path"]:
                nlri = data["path"]["nlri"]
                attrs = data["path"].get("attrs", {})

                # Determine update type
                if "withdrawn" in data["path"] and data["path"]["withdrawn"]:
                    update_type = "WITHDRAWAL"
                    prefixes = data["path"]["withdrawn"]
                else:
                    update_type = "ANNOUNCEMENT"
                    prefixes = [nlri.get("prefix", "")]

                # Create BGPUpdate object
                bgp_update = BGPUpdate(
                    ts=int(time.time()),
                    peer=data.get("neighbor", {}).get("address", "unknown"),
                    type=update_type,
                    announce=prefixes if update_type == "ANNOUNCEMENT" else None,
                    withdraw=prefixes if update_type == "WITHDRAWAL" else None,
                    attrs={
                        "as_path_len": len(attrs.get("as_paths", [{}])[0].get("segments", [])),
                        "origin": attrs.get("origin", "unknown"),
                        "next_hop": attrs.get("next_hop", "unknown"),
                    },
                )

                return bgp_update

        except Exception as e:
            logger.debug(f"Failed to parse BGP output: {e}")
            return None

    async def process_bgp_updates(self):
        """
        Process BGP updates from the lab environment via NATS.

        Connects to the NATS message bus to receive BGP updates published by the
        Go-based BMP collector. Processes each update through the feature aggregator
        and runs anomaly detection on completed time bins.

        The method runs indefinitely until interrupted, continuously:
        1. Receiving BGP updates from NATS
        2. Converting them to BGPUpdate objects
        3. Feeding them to the feature aggregator
        4. Running Matrix Profile analysis on completed bins
        5. Logging anomalies and statistics

        Raises:
            Exception: If NATS connection fails or processing errors occur
        """
        logger.info("🔄 Starting BGP update processing...")

        # Start BGP monitoring process
        # Note: This would need to be replaced with actual BGP monitoring
        # For now, we'll simulate with a placeholder
        logger.warning("BGP monitoring not implemented - using placeholder")
        process = None

        try:
            # Connect to NATS to receive BGP updates from BMP collector
            try:
                import nats

                nc = await nats.connect("nats://localhost:4222")
                logger.info("Connected to NATS for BGP updates from BMP collector")
            except Exception as e:
                logger.error(f"Failed to connect to NATS: {e}")
                return

            try:
                # Subscribe to BGP updates from BMP collector
                logger.info("Subscribing to BGP updates from BMP collector...")

                async def message_handler(msg):
                    """
                    Handle incoming BGP update messages from NATS.

                    Processes each BGP update message by:
                    1. Parsing the JSON data from the message
                    2. Creating a BGPUpdate object
                    3. Adding it to the feature aggregator
                    4. Running anomaly detection on completed bins
                    5. Logging statistics and anomalies

                    Args:
                        msg: NATS message object containing BGP update data
                    """
                    try:
                        # Parse BGP update from NATS message
                        bgp_data = json.loads(msg.data.decode())

                        # Create BGP update object
                        bgp_update = BGPUpdate(
                            timestamp=bgp_data["timestamp"],
                            peer=bgp_data["peer"],
                            type=bgp_data["type"],
                            announce=bgp_data.get("announce"),
                            withdraw=bgp_data.get("withdraw"),
                            as_path=bgp_data.get("as_path"),
                            next_hop=bgp_data.get("next_hop"),
                        )

                        # Add to feature aggregator
                        self.feature_aggregator.add_update(bgp_update)
                        self.stats["updates_processed"] += 1

                        logger.debug(
                            f"Processed BGP update: {bgp_update.type} from {bgp_update.peer}"
                        )

                        # Check for closed bins and run anomaly detection
                        while self.feature_aggregator.has_closed_bin():
                            feature_bin = self.feature_aggregator.pop_closed_bin()
                            logger.info(
                                f"Processing feature bin: {feature_bin.bin_start} - {feature_bin.bin_end}"
                            )

                            # Run Matrix Profile detection
                            mp_result = self.mp_detector.update(feature_bin)

                            if mp_result.get("is_anomaly", False):
                                logger.warning("🚨 ANOMALY DETECTED!")
                                logger.warning(
                                    f"  Confidence: {mp_result.get('anomaly_confidence', 0):.2f}"
                                )
                                logger.warning(
                                    f"  Detected series: {mp_result.get('detected_series', [])}"
                                )
                                logger.warning(
                                    f"  Overall score: {mp_result.get('overall_score', {}).get('score', 0):.2f}"
                                )

                                # Run impact scoring if available
                                if self.impact_scorer:
                                    try:
                                        impact_result = self.impact_scorer.classify(
                                            feature_bin, mp_result
                                        )
                                        logger.warning(f"  Impact: {impact_result}")
                                    except Exception as e:
                                        logger.warning(f"  Impact scoring failed: {e}")

                                self.stats["anomalies_detected"] += 1
                            else:
                                logger.info(
                                    f"  Normal operation - Score: {mp_result.get('overall_score', {}).get('score', 0):.2f}"
                                )

                            self.stats["features_extracted"] += 1

                        # Print statistics every 100 updates
                        if self.stats["updates_processed"] % 100 == 0:
                            elapsed_time = time.time() - self.stats["start_time"]
                            logger.info(
                                f"Stats: {self.stats['updates_processed']} updates, "
                                f"{self.stats['features_extracted']} features, "
                                f"{self.stats['anomalies_detected']} anomalies, "
                                f"{self.stats['updates_processed']/elapsed_time:.1f} updates/sec"
                            )

                    except Exception as e:
                        logger.error(f"Error processing BGP update: {e}")

                # Subscribe to BGP updates
                await nc.subscribe("bgp.updates", cb=message_handler)
                logger.info("Subscribed to bgp.updates channel")

                # Keep the connection alive
                while True:
                    await asyncio.sleep(1)

            except KeyboardInterrupt:
                logger.info("Processing interrupted by user")
            except Exception as e:
                logger.error(f"Error processing BGP updates: {e}")

        except KeyboardInterrupt:
            logger.info(" Processing interrupted by user")
        except Exception as e:
            logger.error(f"✗ Error processing BGP updates: {e}")
        finally:
            process.terminate()
            process.wait()

    def get_stats(self):
        """
        Get current processing statistics.

        Returns:
            dict: Dictionary containing:
                - updates_processed (int): Total BGP updates processed
                - features_extracted (int): Total feature bins processed
                - anomalies_detected (int): Total anomalies detected
                - elapsed_time (float): Time elapsed since start (seconds)
                - update_rate (float): Average updates per second
        """
        elapsed_time = time.time() - self.stats["start_time"]
        return {
            "updates_processed": self.stats["updates_processed"],
            "features_extracted": self.stats["features_extracted"],
            "anomalies_detected": self.stats["anomalies_detected"],
            "elapsed_time": elapsed_time,
            "update_rate": (
                self.stats["updates_processed"] / elapsed_time if elapsed_time > 0 else 0
            ),
        }


async def main():
    """
    Main function to run the BGP anomaly detection integration.

    Performs the following steps:
    1. Checks if the containerlab environment is running
    2. Initializes the ML integration components
    3. Starts processing BGP updates from NATS
    4. Handles graceful shutdown and statistics reporting

    Exits with code 1 if the lab environment is not running or if
    initialization fails.
    """
    logger.info("🔬 BGP Anomaly Detection Lab - ML Integration")
    logger.info("=" * 50)

    # Check if lab is running
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=clab-bgp-anomaly-lab", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
        )
        if not result.stdout.strip():
            logger.error("✗ Lab is not running. Please deploy it first:")
            logger.error("   cd lab && ./scripts/deploy.sh")
            sys.exit(1)

        logger.info("✓ Lab is running")
        logger.info(f"Running containers: {result.stdout.strip()}")

    except Exception as e:
        logger.error(f"✗ Failed to check lab status: {e}")
        sys.exit(1)

    # Initialize integration
    integration = LabMLIntegration()

    try:
        # Start processing
        await integration.process_bgp_updates()

    except KeyboardInterrupt:
        logger.info(" Integration stopped by user")
    except Exception as e:
        logger.error(f"✗ Integration failed: {e}")
    finally:
        # Print final statistics
        stats = integration.get_stats()
        logger.info(" Final Statistics:")
        logger.info(f"  Updates processed: {stats['updates_processed']}")
        logger.info(f"  Features extracted: {stats['features_extracted']}")
        logger.info(f"  Anomalies detected: {stats['anomalies_detected']}")
        logger.info(f"  Update rate: {stats['update_rate']:.1f} updates/sec")


if __name__ == "__main__":
    asyncio.run(main())
