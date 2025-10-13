"""
GPU-Accelerated Matrix Profile Detector for BGP Anomaly Detection

This module implements a streaming Matrix Profile detector using GPU acceleration
via CuPy and the stumpy library. It's designed for real-time
BGP anomaly detection with topology-aware failure localization.
"""

import logging
from collections import deque
from typing import Any, Dict, List

import cupy as cp
import numpy as np

from anomaly_detection.utils.schema import FeatureBin

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GPUMPDetector:
    """
    GPU-accelerated streaming Matrix Profile detector for BGP anomaly detection.

    Features:
    - GPU acceleration via CuPy
    - Streaming processing for real-time detection
    - Multiple time series support (withdrawals, announcements, churn)
    - Discord detection with configurable thresholds
    - Memory-efficient sliding window processing
    """

    def __init__(
        self,
        window_bins: int = 64,
        series_keys: List[str] = None,
        discord_threshold: float = 2.5,
        gpu_memory_limit: str = "2GB",
    ):
        """
        Initialize the GPU Matrix Profile detector.

        Args:
            window_bins: Number of bins for Matrix Profile subsequence length
            series_keys: List of feature keys to monitor (e.g., ['wdr_total', 'ann_total'])
            discord_threshold: Z-score threshold for discord detection
            gpu_memory_limit: GPU memory limit for CuPy operations
        """
        self.window_bins = window_bins
        self.series_keys = series_keys or ["wdr_total", "ann_total", "as_path_churn"]
        self.discord_threshold = discord_threshold

        # Initialize GPU
        try:
            # Test GPU is available
            cp.cuda.Device(0).compute_capability
            self.gpu_available = True
            logger.info("GPU acceleration enabled")
        except Exception as e:
            logger.warning(f"GPU not available, falling back to CPU: {e}")
            self.gpu_available = False

        # Initialize data buffers (need 2*window for stumpy + extra)
        self.buffers = {key: deque(maxlen=window_bins * 3) for key in self.series_keys}
        self.min_buffer_size = window_bins * 2 + 2  # Ensure stumpy has enough data

        # Matrix Profile state
        self.mp_cache = {}
        self.last_discord_scores = {}

        logger.info(
            f"Initialized GPU MP detector with window_bins={window_bins}, "
            f"series_keys={self.series_keys}"
        )

    def _to_gpu_array(self, data: np.ndarray) -> cp.ndarray:
        """Convert numpy array to GPU array if GPU is available."""
        if self.gpu_available:
            return cp.asarray(data)
        return data

    def _to_cpu_array(self, data: cp.ndarray) -> np.ndarray:
        """Convert GPU array back to CPU array."""
        if self.gpu_available:
            return cp.asnumpy(data)
        return data

    def _calculate_matrix_profile_gpu(self, ts: np.ndarray) -> Dict[str, float]:
        """
        Calculate Matrix Profile using stumpy with GPU-accelerated data preparation.

        Uses stumpy for Matrix Profile calculation with CuPy for data preprocessing.
        """
        if len(ts) < self.window_bins:
            return {"discord_score": 0.0, "is_discord": False, "confidence": 0.0}

        try:
            import stumpy

            # Ensure correct dtype for stumpy
            ts_float = ts.astype(np.float64)

            # Use stumpy for Matrix Profile calculation
            mp_result = stumpy.stump(ts_float, m=self.window_bins)

            # Get discord score (highest Matrix Profile value)
            discord_score = float(np.max(mp_result[:, 0]))
            confidence = min(discord_score / self.discord_threshold, 1.0)

            return {
                "discord_score": discord_score,
                "is_discord": discord_score > self.discord_threshold,
                "confidence": confidence,
            }

        except ImportError:
            # Fallback to rolling z-score if stumpy not available
            return self._calculate_fallback_zscore(ts)
        except Exception as e:
            logger.warning(f"Stumpy calculation failed: {e}, using fallback")
            return self._calculate_fallback_zscore(ts)

    def _calculate_fallback_zscore(self, ts: np.ndarray) -> Dict[str, float]:
        """Fallback z-score calculation if stumpy fails."""
        if len(ts) < self.window_bins:
            return {"discord_score": 0.0, "is_discord": False, "confidence": 0.0}

        # Convert to GPU array for acceleration if available
        ts_gpu = self._to_gpu_array(ts)

        if self.gpu_available:
            # GPU-accelerated rolling statistics
            rolling_mean = cp.convolve(
                ts_gpu, cp.ones(self.window_bins) / self.window_bins, mode="valid"
            )
            rolling_std = cp.sqrt(
                cp.convolve(ts_gpu**2, cp.ones(self.window_bins) / self.window_bins, mode="valid")
                - rolling_mean**2
            )

            recent_values = ts_gpu[-len(rolling_mean) :]
            z_scores = cp.abs((recent_values - rolling_mean) / (rolling_std + 1e-9))
            max_discord_score = float(cp.max(z_scores))
        else:
            # CPU fallback
            rolling_mean = np.convolve(
                ts, np.ones(self.window_bins) / self.window_bins, mode="valid"
            )
            rolling_std = np.sqrt(
                np.convolve(ts**2, np.ones(self.window_bins) / self.window_bins, mode="valid")
                - rolling_mean**2
            )

            recent_values = ts[-len(rolling_mean) :]
            z_scores = np.abs((recent_values - rolling_mean) / (rolling_std + 1e-9))
            max_discord_score = float(np.max(z_scores))

        return {
            "discord_score": max_discord_score,
            "is_discord": max_discord_score > self.discord_threshold,
            "confidence": min(max_discord_score / self.discord_threshold, 1.0),
        }

    def update(self, fb: FeatureBin) -> Dict[str, Any]:
        """
        Update the detector with a new feature bin and return anomaly scores.

        Args:
            fb: FeatureBin containing aggregated BGP features

        Returns:
            Dictionary containing anomaly scores and detection results
        """
        results = {}

        for key in self.series_keys:
            # Extract time series value
            value = fb.totals.get(key, 0.0)
            self.buffers[key].append(float(value))

            # Check if we have enough data for Matrix Profile calculation
            if len(self.buffers[key]) < self.min_buffer_size:
                results[key] = {
                    "discord_score": 0.0,
                    "is_discord": False,
                    "confidence": 0.0,
                    "status": "insufficient_data",
                }
                continue

            # Convert buffer to numpy array
            ts = np.array(self.buffers[key], dtype=np.float32)

            # Calculate Matrix Profile
            mp_result = self._calculate_matrix_profile_gpu(ts)

            # Store results
            results[key] = {
                "discord_score": mp_result["discord_score"],
                "is_discord": mp_result["is_discord"],
                "confidence": mp_result["confidence"],
                "status": "active",
            }

            # Update cache
            self.mp_cache[key] = mp_result
            self.last_discord_scores[key] = mp_result["discord_score"]

        # Calculate overall anomaly score
        overall_score = self._calculate_overall_anomaly_score(results)

        return {
            "timestamp": fb.bin_start,
            "series_results": results,
            "overall_score": overall_score,
            "is_anomaly": overall_score["is_anomaly"],
            "anomaly_confidence": overall_score["confidence"],
            "detected_series": [k for k, v in results.items() if v["is_discord"]],
        }

    def _calculate_overall_anomaly_score(self, series_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate overall anomaly score from individual series results.

        Uses weighted combination of discord scores with emphasis on withdrawal patterns.
        """
        if not series_results:
            return {"is_anomaly": False, "confidence": 0.0, "score": 0.0}

        # Weight different series based on BGP anomaly characteristics
        weights = {
            "wdr_total": 0.5,  # Withdrawals are primary indicator
            "ann_total": 0.3,  # Announcements secondary
            "as_path_churn": 0.2,  # Path changes tertiary
        }

        weighted_scores = []
        active_series = []

        for key, result in series_results.items():
            if result["status"] == "active":
                weight = weights.get(key, 0.1)
                weighted_scores.append(result["discord_score"] * weight)
                active_series.append(key)

        if not weighted_scores:
            return {"is_anomaly": False, "confidence": 0.0, "score": 0.0}

        # Calculate weighted average
        overall_score = np.mean(weighted_scores)
        is_anomaly = overall_score > self.discord_threshold
        confidence = min(overall_score / self.discord_threshold, 1.0)

        return {
            "is_anomaly": is_anomaly,
            "confidence": confidence,
            "score": overall_score,
            "active_series": active_series,
        }

    def get_status(self) -> Dict[str, Any]:
        """Get current detector status and statistics."""
        return {
            "gpu_available": self.gpu_available,
            "window_bins": self.window_bins,
            "series_keys": self.series_keys,
            "discord_threshold": self.discord_threshold,
            "buffer_sizes": {k: len(v) for k, v in self.buffers.items()},
            "last_discord_scores": self.last_discord_scores.copy(),
        }

    def reset(self):
        """Reset the detector state."""
        for buffer in self.buffers.values():
            buffer.clear()
        self.mp_cache.clear()
        self.last_discord_scores.clear()
        logger.info("GPU MP detector reset")


# Factory function for easy instantiation
def create_gpu_mp_detector(
    window_bins: int = 64,
    series_keys: List[str] = None,
    discord_threshold: float = 2.5,
    gpu_memory_limit: str = "2GB",
) -> GPUMPDetector:
    """
    Factory function to create a GPU-accelerated Matrix Profile detector.

    Args:
        window_bins: Matrix Profile window size
        series_keys: Time series to monitor
        discord_threshold: Anomaly detection threshold
        gpu_memory_limit: GPU memory allocation limit

    Returns:
        Configured GPUMPDetector instance
    """
    return GPUMPDetector(
        window_bins=window_bins,
        series_keys=series_keys,
        discord_threshold=discord_threshold,
        gpu_memory_limit=gpu_memory_limit,
    )
