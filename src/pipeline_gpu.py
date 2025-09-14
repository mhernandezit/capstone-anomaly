"""
GPU-Accelerated BGP Anomaly Detection Pipeline

This pipeline integrates the GPU Matrix Profile detector with the existing
BGP collection and feature aggregation system for real-time anomaly detection.
"""

import asyncio
import json
import logging
from typing import Dict, Any
from nats.aio.client import Client as NATS

from src.features.stream_features import FeatureAggregator
from src.models.gpu_mp_detector import create_gpu_mp_detector
from src.triage.impact import ImpactScorer
from src.utils.schema import BGPUpdate, FeatureBin

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GPUAnomalyPipeline:
    """
    GPU-accelerated BGP anomaly detection pipeline.

    Components:
    1. Feature aggregation (30-second bins)
    2. GPU Matrix Profile detection
    3. Topology-aware impact scoring
    4. Event publishing to dashboard
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the GPU anomaly detection pipeline.

        Args:
            config: Configuration dictionary containing:
                - nats_url: NATS server URL
                - roles_config: Device role mapping
                - mp_config: Matrix Profile configuration
        """
        self.config = config
        self.nats_url = config.get("nats_url", "nats://localhost:4222")

        # Initialize components
        self.feature_aggregator = FeatureAggregator(bin_seconds=config.get("bin_seconds", 30))

        self.mp_detector = create_gpu_mp_detector(
            window_bins=config.get("mp_window_bins", 64),
            series_keys=config.get("mp_series_keys", ["wdr_total", "ann_total", "as_path_churn"]),
            discord_threshold=config.get("mp_discord_threshold", 2.5),
            gpu_memory_limit=config.get("gpu_memory_limit", "2GB"),
        )

        self.impact_scorer = ImpactScorer(cfg_roles=config.get("roles_config", {}))

        # NATS client
        self.nc = None

        logger.info("GPU anomaly detection pipeline initialized")

    async def start(self):
        """Start the pipeline and connect to NATS."""
        self.nc = NATS()
        await self.nc.connect(servers=[self.nats_url])

        # Subscribe to BGP updates
        await self.nc.subscribe("bgp.updates", cb=self._handle_bgp_update)

        logger.info("Pipeline started, listening for BGP updates...")

    async def stop(self):
        """Stop the pipeline and disconnect from NATS."""
        if self.nc:
            await self.nc.drain()
        logger.info("Pipeline stopped")

    async def _handle_bgp_update(self, msg):
        """Handle incoming BGP update message."""
        try:
            # Parse BGP update
            data = json.loads(msg.data.decode())
            bgp_update = BGPUpdate(**data)

            # Add to feature aggregator
            self.feature_aggregator.add_update(bgp_update)

            # Process any closed bins
            while self.feature_aggregator.has_closed_bin():
                await self._process_feature_bin(self.feature_aggregator.pop_closed_bin())

        except Exception as e:
            logger.error(f"Error processing BGP update: {e}")

    async def _process_feature_bin(self, fb: FeatureBin):
        """
        Process a completed feature bin through the anomaly detection pipeline.

        Args:
            fb: FeatureBin containing aggregated BGP features
        """
        try:
            # Step 1: Matrix Profile anomaly detection
            mp_results = self.mp_detector.update(fb)

            # Step 2: Topology-aware impact scoring
            impact_results = self.impact_scorer.classify(fb, mp_results["overall_score"]["score"])

            # Step 3: Create comprehensive event
            event = self._create_anomaly_event(fb, mp_results, impact_results)

            # Step 4: Publish event to dashboard
            await self._publish_event(event)

            # Log significant events
            if event["is_anomaly"]:
                logger.info(
                    f"Anomaly detected: {event['impact']} - "
                    f"Confidence: {event['anomaly_confidence']:.2f} - "
                    f"Roles: {event['impact_analysis']['roles']}"
                )

        except Exception as e:
            logger.error(f"Error processing feature bin: {e}")

    def _create_anomaly_event(
        self, fb: FeatureBin, mp_results: Dict[str, Any], impact_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a comprehensive anomaly event from all pipeline results.

        Args:
            fb: Feature bin
            mp_results: Matrix Profile detection results
            impact_results: Impact scoring results

        Returns:
            Comprehensive anomaly event dictionary
        """
        return {
            "timestamp": fb.bin_start,
            "bin_duration": fb.bin_end - fb.bin_start,
            "is_anomaly": mp_results["is_anomaly"],
            "anomaly_confidence": mp_results["anomaly_confidence"],
            "overall_score": mp_results["overall_score"]["score"],
            "detected_series": mp_results["detected_series"],
            # Matrix Profile details
            "mp_analysis": {
                "series_results": mp_results["series_results"],
                "active_series": mp_results["overall_score"]["active_series"],
            },
            # Impact analysis
            "impact_analysis": {
                "impact": impact_results["impact"],
                "roles": impact_results["roles"],
                "prefix_spread": impact_results["prefix_spread"],
            },
            # Feature details
            "feature_summary": {
                "total_announcements": fb.totals.get("ann_total", 0),
                "total_withdrawals": fb.totals.get("wdr_total", 0),
                "as_path_churn": fb.totals.get("as_path_churn", 0),
                "active_peers": len(fb.peers),
            },
            # Peer details
            "peer_activity": {
                peer: {
                    "announcements": data.get("ann", 0),
                    "withdrawals": data.get("wdr", 0),
                    "as_path_churn": data.get("as_path_churn", 0),
                }
                for peer, data in fb.peers.items()
            },
        }

    async def _publish_event(self, event: Dict[str, Any]):
        """Publish anomaly event to NATS for dashboard consumption."""
        try:
            event_json = json.dumps(event, default=str)
            await self.nc.publish("bgp.events", event_json.encode())
            logger.debug(f"Published event: {event['timestamp']}")
        except Exception as e:
            logger.error(f"Error publishing event: {e}")

    def get_pipeline_status(self) -> Dict[str, Any]:
        """Get current pipeline status and statistics."""
        return {
            "mp_detector_status": self.mp_detector.get_status(),
            "feature_aggregator": {
                "current_bin_start": self.feature_aggregator.current_bin_start,
                "closed_bins_count": len(self.feature_aggregator.closed),
                "bin_seconds": self.feature_aggregator.bin_seconds,
            },
            "nats_connected": self.nc is not None,
        }


async def main():
    """Main function to run the GPU anomaly detection pipeline."""
    # Load configuration
    config = {
        "nats_url": "nats://localhost:4222",
        "bin_seconds": 30,
        "mp_window_bins": 64,
        "mp_series_keys": ["wdr_total", "ann_total", "as_path_churn"],
        "mp_discord_threshold": 2.5,
        "gpu_memory_limit": "2GB",
        "roles_config": {
            "roles": {
                "10.0.0.1": "rr",
                "10.0.0.2": "rr",
                "10.0.1.1": "spine",
                "10.0.1.2": "spine",
                "10.0.2.1": "tor",
                "10.0.2.2": "tor",
                "10.0.3.1": "edge",
                "10.0.3.2": "edge",
                "10.0.10.11": "server",
                "10.0.10.12": "server",
            },
            "thresholds": {
                "edge_local_prefix_max": 100,
                "edge_local_pct_table_max": 0.01,
                "correlation_window_secs": 60,
            },
        },
    }

    # Create and start pipeline
    pipeline = GPUAnomalyPipeline(config)

    try:
        await pipeline.start()

        # Keep running
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        logger.info("Shutting down pipeline...")
    finally:
        await pipeline.stop()


if __name__ == "__main__":
    asyncio.run(main())
