#!/usr/bin/env python3
"""
Production Pipeline Runner
Wires the REAL Matrix Profile + Isolation Forest detectors to evaluation data.
"""

import asyncio
import json
import logging
import time
from pathlib import Path

from nats.aio.client import Client as NATS

from anomaly_detection.features import SNMPFeatureExtractor
from anomaly_detection.models import IsolationForestDetector, MatrixProfileDetector
from anomaly_detection.utils import FeatureBin

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProductionPipelineRunner:
    """Runs REAL ML detectors on evaluation data."""

    def __init__(self):
        # Initialize REAL detectors with GPU
        logger.info("Initializing Matrix Profile detector with GPU acceleration...")

        # Try GPU first (stumpy + cupy)
        try:
            import cupy as cp  # noqa: F401

            # Use GPU Matrix Profile detector
            from models.gpu_mp_detector import GPUMPDetector

            self.bgp_detector = GPUMPDetector(
                window_bins=8, series_keys=["wdr_total", "ann_total"], discord_threshold=1.5
            )
            logger.info("[OK] Using GPU Matrix Profile (stumpy + CuPy)")
        except ImportError:
            # Fall back to CPU
            self.bgp_detector = MatrixProfileDetector(
                window_bins=12,  # Increased from 8 to 12 (120s window for better pattern detection)
                series_keys=["wdr_total", "ann_total"],
                discord_threshold=1.2,  # Lowered from 1.5 to 1.2 (more sensitive)
                mp_library="stumpy",
            )
            logger.info("[OK] Using CPU Matrix Profile (stumpy) - Enhanced sensitivity: window=12, threshold=1.2")

        # Try to load pre-trained Isolation Forest
        logger.info("Initializing Isolation Forest detector...")
        pretrained_path = Path("data/evaluation/models/isolation_forest_trained.pkl")

        if pretrained_path.exists():
            logger.info(f"Loading pre-trained model from {pretrained_path}")
            import joblib

            model_data = joblib.load(pretrained_path)

            # Create detector with pre-trained model
            self.snmp_detector = IsolationForestDetector(n_estimators=200, contamination=0.02)
            # Inject pre-trained model AND scaler
            self.snmp_detector.model = model_data["model"]
            self.snmp_detector.scaler = model_data.get("scaler")  # Load scaler too
            self.snmp_detector.feature_names = model_data["feature_names"]
            self.snmp_detector.is_trained = True
            self.snmp_trained = True
            logger.info("[OK] Using pre-trained Isolation Forest model with scaler")
        else:
            logger.warning("No pre-trained model found - will train online")
            self.snmp_detector = IsolationForestDetector(
                n_estimators=150,  # More trees for better detection
                contamination=0.05  # More sensitive (5% instead of 10%)
            )
            self.snmp_trained = False
            self.training_samples = []

        self.snmp_extractor = SNMPFeatureExtractor(bin_seconds=10)

        # Track data for binning
        self.bgp_bin_data = {"wdr_total": 0, "ann_total": 0}
        self.bin_start = time.time()
        self.bin_duration = 10  # 10 second bins for faster response

        self.alerts = []

    async def connect(self):
        """Connect to NATS."""
        self.nc = NATS()
        await self.nc.connect("nats://localhost:4222")

        # Subscribe to data streams
        await self.nc.subscribe("bgp.updates", cb=self._handle_bgp)
        await self.nc.subscribe("snmp.metrics", cb=self._handle_snmp)
        await self.nc.subscribe("snmp.traps", cb=self._handle_snmp_trap)

        logger.info("[OK] Connected to NATS and subscribed to streams")

    async def _handle_bgp(self, msg):
        """Process BGP through Matrix Profile."""
        try:
            data = json.loads(msg.data.decode())

            # Accumulate into bins
            if data.get("update_type") == "withdraw":
                self.bgp_bin_data["wdr_total"] += len(data.get("prefixes", []))
            elif data.get("update_type") == "announce":
                self.bgp_bin_data["ann_total"] += len(data.get("prefixes", []))

            # Check if bin complete
            if time.time() - self.bin_start >= self.bin_duration:
                await self._process_bgp_bin()

        except Exception as e:
            logger.error(f"BGP handler error: {e}")

    async def _process_bgp_bin(self):
        """Process completed BGP bin through Matrix Profile."""
        # Create feature bin (convert to int timestamps)
        fb = FeatureBin(
            bin_start=int(self.bin_start),
            bin_end=int(time.time()),
            totals=self.bgp_bin_data.copy(),
            peers={},  # Required field
        )

        logger.info(f"[BGP Bin] wdr={fb.totals['wdr_total']}, ann={fb.totals.get('ann_total', 0)}")

        # Run through REAL Matrix Profile detector
        result = self.bgp_detector.update(fb)

        logger.info(
            f"[MP Result] discord={result.get('series_results', {}).get('wdr_total', {}).get('discord_score', 0):.2f}, anomaly={result.get('is_anomaly')}"
        )

        if result.get("is_anomaly"):
            # Extract confidence properly (overall_score is a dict)
            if isinstance(result.get("anomaly_confidence"), dict):
                confidence = float(result["anomaly_confidence"].get("confidence", 1.0))
                overall_score_val = float(result["anomaly_confidence"].get("score", 0.0))
            else:
                confidence = float(result.get("anomaly_confidence", 1.0))
                overall_score_val = float(result.get("overall_score", {}).get("score", 0.0)) if isinstance(result.get("overall_score"), dict) else float(result.get("overall_score", 0.0))
            
            alert = {
                "timestamp": time.time(),
                "source": "bgp",
                "detector": "matrix_profile",
                "confidence": confidence,
                "details": {
                    "series": [str(s) for s in result["detected_series"]] if isinstance(result["detected_series"], list) else str(result["detected_series"]),
                    "overall_score": overall_score_val,
                    "withdrawals": int(self.bgp_bin_data["wdr_total"]),
                    "announcements": int(self.bgp_bin_data["ann_total"]),
                },
            }
            self.alerts.append(alert)
            logger.warning(
                f"[BGP ANOMALY] Matrix Profile detected! Confidence: {confidence:.2f}"
            )
            logger.warning(
                f"  Withdrawals: {self.bgp_bin_data['wdr_total']}, Announcements: {self.bgp_bin_data['ann_total']}"
            )

        # Reset for next bin
        self.bgp_bin_data = {"wdr_total": 0, "ann_total": 0}
        self.bin_start = time.time()

    async def _handle_snmp(self, msg):
        """Process SNMP through Isolation Forest."""
        try:
            data = json.loads(msg.data.decode())

            # Add to extractor
            self.snmp_extractor.add_snmp_metric(data)

            # Check for completed bin
            if self.snmp_extractor.has_completed_bin():
                bin_data = self.snmp_extractor.pop_completed_bin()
                feature_vector = self.snmp_extractor.get_feature_vector(bin_data)
                feature_names = self.snmp_extractor.get_feature_names()

                # Training phase (first 5 samples - faster training)
                if not self.snmp_trained:
                    self.training_samples.append(feature_vector)
                    if len(self.training_samples) >= 5:
                        import numpy as np

                        training_data = np.array(self.training_samples)
                        self.snmp_detector.fit(training_data, feature_names)
                        self.snmp_trained = True
                        logger.info(
                            f"[OK] Isolation Forest trained on {len(self.training_samples)} samples"
                        )
                    return

                # Detection phase - run through REAL Isolation Forest
                result = self.snmp_detector.predict(
                    feature_vector, timestamp=bin_data.bin_start, feature_names=feature_names
                )

                if result.is_anomaly:
                    alert = {
                        "timestamp": time.time(),
                        "source": "snmp",
                        "detector": "isolation_forest",
                        "confidence": float(result.confidence),  # Convert to native Python float
                        "severity": str(result.severity),
                        "details": {
                            "affected_features": [str(f) for f in result.affected_features[:3]],
                            "anomaly_score": float(result.anomaly_score),
                        },
                    }
                    self.alerts.append(alert)
                    logger.warning(
                        f"[SNMP ANOMALY] Isolation Forest detected! Confidence: {result.confidence:.2f}"
                    )
                    logger.warning(f"  Affected: {', '.join(result.affected_features[:3])}")

        except Exception as e:
            logger.error(f"SNMP handler error: {e}")

    async def _handle_snmp_trap(self, msg):
        """Handle SNMP traps as high-confidence signals."""
        try:
            data = json.loads(msg.data.decode())

            # Traps are immediate anomalies
            alert = {
                "timestamp": time.time(),
                "source": "snmp_trap",
                "detector": "rule_based",
                "confidence": 0.95,
                "severity": data.get("severity", "warning"),
                "details": {"trap_type": data.get("trap_type"), "device": data.get("device")},
            }
            self.alerts.append(alert)
            logger.warning(f"[SNMP TRAP] {data.get('trap_type')} from {data.get('device')}")

        except Exception as e:
            logger.error(f"SNMP trap handler error: {e}")

    async def run(self, duration: int = 120):
        """Run pipeline for specified duration."""
        logger.info(f"[Pipeline] Running for {duration}s...")
        await asyncio.sleep(duration)

        # Save alerts
        alerts_file = Path("data/evaluation/alerts/pipeline_alerts.jsonl")
        alerts_file.parent.mkdir(parents=True, exist_ok=True)

        with open(alerts_file, "w") as f:
            for alert in self.alerts:
                f.write(json.dumps(alert) + "\n")

        logger.info(f"[OK] Pipeline complete. {len(self.alerts)} alerts generated")
        logger.info(f"     Alerts saved to: {alerts_file}")

        return self.alerts


async def main():
    """Test production pipeline."""
    pipeline = ProductionPipelineRunner()
    await pipeline.connect()

    # Run for 2 minutes
    alerts = await pipeline.run(duration=120)

    print(f"\n[SUMMARY] {len(alerts)} total alerts:")
    for i, alert in enumerate(alerts, 1):
        print(
            f"  {i}. {alert['source']:10s} | {alert['detector']:20s} | conf={alert['confidence']:.2f}"
        )

    await pipeline.nc.close()


if __name__ == "__main__":
    asyncio.run(main())
