"""
CPU-Optimized Matrix Profile Detector for BGP Anomaly Detection

This module implements a high-performance CPU-based Matrix Profile detector
using the Matrix Profile Foundation library. It's designed for real-time
BGP anomaly detection with topology-aware failure localization.
"""

import numpy as np
from collections import deque
from typing import Optional, Dict, Any, List
import logging
from python.utils.schema import FeatureBin

# Try to import Matrix Profile Foundation, fall back to stumpy if not available
try:
    import matrixprofile as mp
    MP_AVAILABLE = True
    logger = logging.getLogger(__name__)
    logger.info("Using Matrix Profile Foundation library")
except ImportError:
    try:
        import stumpy
        MP_AVAILABLE = False
        logger = logging.getLogger(__name__)
        logger.info("Using stumpy library (Matrix Profile Foundation not available)")
    except ImportError:
        MP_AVAILABLE = False
        logger = logging.getLogger(__name__)
        logger.warning("No Matrix Profile library available, using simplified z-score method")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CPUMPDetector:
    """
    CPU-optimized streaming Matrix Profile detector for BGP anomaly detection.
    
    Features:
    - High-performance CPU implementation
    - Streaming processing for real-time detection
    - Multiple time series support (withdrawals, announcements, churn)
    - Multiple Matrix Profile library support (MPF, stumpy, or fallback)
    - Memory-efficient sliding window processing
    """
    
    def __init__(
        self,
        window_bins: int = 64,
        series_keys: List[str] = None,
        discord_threshold: float = 2.5,
        mp_library: str = "auto"
    ):
        """
        Initialize the CPU Matrix Profile detector.
        
        Args:
            window_bins: Number of bins for Matrix Profile subsequence length
            series_keys: List of feature keys to monitor
            discord_threshold: Z-score threshold for discord detection
            mp_library: Matrix Profile library to use ("mpf", "stumpy", "auto", "fallback")
        """
        self.window_bins = window_bins
        self.series_keys = series_keys or ['wdr_total', 'ann_total', 'as_path_churn']
        self.discord_threshold = discord_threshold
        
        # Determine which library to use
        self.mp_library = self._determine_library(mp_library)
        
        # Initialize data buffers
        self.buffers = {key: deque(maxlen=window_bins * 2) for key in self.series_keys}
        self.min_buffer_size = window_bins + 10
        
        # Matrix Profile state
        self.mp_cache = {}
        self.last_discord_scores = {}
        
        logger.info(f"Initialized CPU MP detector with {self.mp_library} library, "
                   f"window_bins={window_bins}, series_keys={self.series_keys}")
    
    def _determine_library(self, mp_library: str) -> str:
        """Determine which Matrix Profile library to use."""
        if mp_library == "auto":
            if MP_AVAILABLE:
                return "mpf"
            else:
                try:
                    import stumpy
                    return "stumpy"
                except ImportError:
                    return "fallback"
        elif mp_library == "mpf" and MP_AVAILABLE:
            return "mpf"
        elif mp_library == "stumpy":
            try:
                import stumpy
                return "stumpy"
            except ImportError:
                logger.warning("stumpy not available, falling back to simplified method")
                return "fallback"
        else:
            return "fallback"
    
    def _calculate_matrix_profile_mpf(self, ts: np.ndarray) -> Dict[str, float]:
        """Calculate Matrix Profile using Matrix Profile Foundation library."""
        try:
            # Calculate Matrix Profile
            profile = mp.compute(ts, windows=self.window_bins)
            
            # Get discord score (highest Matrix Profile value)
            discord_score = float(np.max(profile['mp']))
            
            # Calculate confidence based on how much it exceeds threshold
            confidence = min(discord_score / self.discord_threshold, 1.0)
            
            return {
                'discord_score': discord_score,
                'is_discord': discord_score > self.discord_threshold,
                'confidence': confidence
            }
        except Exception as e:
            logger.error(f"MPF calculation error: {e}")
            return self._calculate_fallback(ts)
    
    def _calculate_matrix_profile_stumpy(self, ts: np.ndarray) -> Dict[str, float]:
        """Calculate Matrix Profile using stumpy library."""
        try:
            import stumpy
            
            # Ensure correct dtype for stumpy (requires float64)
            ts_float = ts.astype(np.float64)
            
            # Calculate Matrix Profile
            mp_values = stumpy.stump(ts_float, m=self.window_bins)
            
            # Get discord score (highest Matrix Profile value)
            discord_score = float(np.max(mp_values[:, 0]))
            
            # Calculate confidence
            confidence = min(discord_score / self.discord_threshold, 1.0)
            
            return {
                'discord_score': discord_score,
                'is_discord': discord_score > self.discord_threshold,
                'confidence': confidence
            }
        except Exception as e:
            logger.error(f"Stumpy calculation error: {e}")
            return self._calculate_fallback(ts)
    
    def _calculate_fallback(self, ts: np.ndarray) -> Dict[str, float]:
        """Fallback calculation using rolling z-score method."""
        if len(ts) < self.window_bins:
            return {'discord_score': 0.0, 'is_discord': False, 'confidence': 0.0}
        
        # Calculate rolling statistics
        rolling_mean = np.convolve(ts, np.ones(self.window_bins) / self.window_bins, mode='valid')
        rolling_std = np.sqrt(np.convolve(ts**2, np.ones(self.window_bins) / self.window_bins, mode='valid') - rolling_mean**2)
        
        # Calculate z-scores for recent values
        recent_values = ts[-len(rolling_mean):]
        z_scores = np.abs((recent_values - rolling_mean) / (rolling_std + 1e-9))
        
        discord_score = float(np.max(z_scores))
        confidence = min(discord_score / self.discord_threshold, 1.0)
        
        return {
            'discord_score': discord_score,
            'is_discord': discord_score > self.discord_threshold,
            'confidence': confidence
        }
    
    def _calculate_matrix_profile(self, ts: np.ndarray) -> Dict[str, float]:
        """Calculate Matrix Profile using the selected library."""
        if self.mp_library == "mpf":
            return self._calculate_matrix_profile_mpf(ts)
        elif self.mp_library == "stumpy":
            return self._calculate_matrix_profile_stumpy(ts)
        else:
            return self._calculate_fallback(ts)
    
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
                    'discord_score': 0.0,
                    'is_discord': False,
                    'confidence': 0.0,
                    'status': 'insufficient_data'
                }
                continue
            
            # Convert buffer to numpy array
            ts = np.array(self.buffers[key], dtype=np.float32)
            
            # Calculate Matrix Profile
            mp_result = self._calculate_matrix_profile(ts)
            
            # Store results
            results[key] = {
                'discord_score': mp_result['discord_score'],
                'is_discord': mp_result['is_discord'],
                'confidence': mp_result['confidence'],
                'status': 'active'
            }
            
            # Update cache
            self.mp_cache[key] = mp_result
            self.last_discord_scores[key] = mp_result['discord_score']
        
        # Calculate overall anomaly score
        overall_score = self._calculate_overall_anomaly_score(results)
        
        return {
            'timestamp': fb.bin_start,
            'series_results': results,
            'overall_score': overall_score,
            'is_anomaly': overall_score['is_anomaly'],
            'anomaly_confidence': overall_score['confidence'],
            'detected_series': [k for k, v in results.items() if v['is_discord']]
        }
    
    def _calculate_overall_anomaly_score(self, series_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall anomaly score from individual series results."""
        if not series_results:
            return {'is_anomaly': False, 'confidence': 0.0, 'score': 0.0}
        
        # Weight different series based on BGP anomaly characteristics
        weights = {
            'wdr_total': 0.5,      # Withdrawals are primary indicator
            'ann_total': 0.3,      # Announcements secondary
            'as_path_churn': 0.2   # Path changes tertiary
        }
        
        weighted_scores = []
        active_series = []
        
        for key, result in series_results.items():
            if result['status'] == 'active':
                weight = weights.get(key, 0.1)
                weighted_scores.append(result['discord_score'] * weight)
                active_series.append(key)
        
        if not weighted_scores:
            return {'is_anomaly': False, 'confidence': 0.0, 'score': 0.0}
        
        # Calculate weighted average
        overall_score = np.mean(weighted_scores)
        is_anomaly = overall_score > self.discord_threshold
        confidence = min(overall_score / self.discord_threshold, 1.0)
        
        return {
            'is_anomaly': is_anomaly,
            'confidence': confidence,
            'score': overall_score,
            'active_series': active_series
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get current detector status and statistics."""
        return {
            'mp_library': self.mp_library,
            'window_bins': self.window_bins,
            'series_keys': self.series_keys,
            'discord_threshold': self.discord_threshold,
            'buffer_sizes': {k: len(v) for k, v in self.buffers.items()},
            'last_discord_scores': self.last_discord_scores.copy()
        }
    
    def reset(self):
        """Reset the detector state."""
        for buffer in self.buffers.values():
            buffer.clear()
        self.mp_cache.clear()
        self.last_discord_scores.clear()
        logger.info("CPU MP detector reset")


# Factory function for easy instantiation
def create_cpu_mp_detector(
    window_bins: int = 64,
    series_keys: List[str] = None,
    discord_threshold: float = 2.5,
    mp_library: str = "auto"
) -> CPUMPDetector:
    """
    Factory function to create a CPU-optimized Matrix Profile detector.
    
    Args:
        window_bins: Matrix Profile window size
        series_keys: Time series to monitor
        discord_threshold: Anomaly detection threshold
        mp_library: Matrix Profile library to use
        
    Returns:
        Configured CPUMPDetector instance
    """
    return CPUMPDetector(
        window_bins=window_bins,
        series_keys=series_keys,
        discord_threshold=discord_threshold,
        mp_library=mp_library
    )
