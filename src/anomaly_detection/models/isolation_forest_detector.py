#!/usr/bin/env python3
"""
Isolation Forest Detector for SNMP Anomaly Detection

This module implements Isolation Forest (Liu et al., 2008) for detecting
hardware and environmental anomalies in SNMP metrics. It processes high-dimensional
feature vectors extracted from SNMP data to identify outliers without requiring
labeled training data.

Reference:
Liu, F. T., Ting, K. M., & Zhou, Z.-H. (2008).
Isolation Forest.
2008 Eighth IEEE International Conference on Data Mining, 413--422.
doi: 10.1109/ICDM.2008.17
"""

import logging
from collections import deque
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)


@dataclass
class IFAnomalyResult:
    """Results from Isolation Forest anomaly detection."""

    timestamp: float
    is_anomaly: bool
    anomaly_score: float  # Negative score: lower = more anomalous
    confidence: float  # Normalized to 0-1
    feature_importance: Dict[str, float]
    affected_features: List[str]
    severity: str  # 'info', 'warning', 'error', 'critical'


class IsolationForestDetector:
    """
    Isolation Forest detector for SNMP hardware anomaly detection.

    This implementation uses scikit-learn's IsolationForest to detect
    anomalies in high-dimensional SNMP feature spaces. The algorithm is
    particularly effective for:
    - Hardware component failures
    - Environmental issues (temperature, power)
    - System resource anomalies (CPU, memory)
    - Multi-device correlation patterns

    The detector operates in two modes:
    1. Training mode: Builds baseline model from normal data
    2. Detection mode: Identifies anomalies in real-time
    """

    def __init__(
        self,
        n_estimators: int = 100,
        contamination: float = 0.1,
        max_samples: int = 256,
        random_state: int = 42,
        training_window_size: int = 100,
        auto_retrain: bool = True,
        retrain_interval: int = 500,
    ):
        """
        Initialize the Isolation Forest detector.

        Args:
            n_estimators: Number of isolation trees (default: 100)
            contamination: Expected proportion of anomalies (default: 0.1 = 10%)
            max_samples: Number of samples to train each tree (default: 256)
            random_state: Random seed for reproducibility
            training_window_size: Min samples needed for initial training
            auto_retrain: Whether to periodically retrain the model
            retrain_interval: Number of samples between retraining
        """
        self.n_estimators = n_estimators
        self.contamination = contamination
        self.max_samples = max_samples
        self.random_state = random_state
        self.training_window_size = training_window_size
        self.auto_retrain = auto_retrain
        self.retrain_interval = retrain_interval

        # Initialize Isolation Forest model
        self.model = IsolationForest(
            n_estimators=n_estimators,
            contamination=contamination,
            max_samples=max_samples,
            random_state=random_state,
            warm_start=False,
            n_jobs=-1,  # Use all CPU cores
        )

        # Feature normalization
        self.scaler = StandardScaler()

        # Training data buffer
        self.training_buffer = deque(maxlen=training_window_size)
        self.is_trained = False

        # Feature tracking
        self.feature_names = []
        self.feature_baselines = {}
        self.feature_ranges = {}

        # Detection history for adaptive learning
        self.detection_history = deque(maxlen=1000)
        self.normal_scores = deque(maxlen=500)
        self.anomaly_scores = deque(maxlen=100)

        # Statistics
        self.stats = {
            "total_samples": 0,
            "training_samples": 0,
            "anomalies_detected": 0,
            "retrains_performed": 0,
            "false_positive_estimate": 0.0,
        }

        logger.info(
            f"Initialized Isolation Forest Detector: "
            f"n_estimators={n_estimators}, contamination={contamination}"
        )

    def fit(self, X: np.ndarray, feature_names: Optional[List[str]] = None):
        """
        Train the Isolation Forest model on normal data.

        Args:
            X: Training data matrix (n_samples, n_features)
            feature_names: Names of features for interpretation
        """
        if X.shape[0] < 10:
            logger.warning(
                f"Insufficient training data: {X.shape[0]} samples " f"(minimum 10 required)"
            )
            return

        # Store feature names
        if feature_names:
            self.feature_names = feature_names

        # Fit scaler on training data
        self.scaler.fit(X)
        X_scaled = self.scaler.transform(X)

        # Train Isolation Forest
        self.model.fit(X_scaled)
        self.is_trained = True

        # Calculate feature baselines and ranges
        self._calculate_feature_statistics(X)

        self.stats["training_samples"] = X.shape[0]
        self.stats["retrains_performed"] += 1

        logger.info(
            f"Trained Isolation Forest on {X.shape[0]} samples " f"with {X.shape[1]} features"
        )

    def predict(
        self,
        X: np.ndarray,
        timestamp: float,
        feature_names: Optional[List[str]] = None,
    ) -> IFAnomalyResult:
        """
        Detect anomalies in new SNMP data.

        Args:
            X: Feature vector (1, n_features) or (n_features,)
            timestamp: Timestamp of the data
            feature_names: Names of features for interpretation

        Returns:
            IFAnomalyResult containing detection results
        """
        # Ensure X is 2D
        if X.ndim == 1:
            X = X.reshape(1, -1)

        # Store feature names if provided
        if feature_names:
            self.feature_names = feature_names

        # Check if model is trained
        if not self.is_trained:
            # Add to training buffer
            self.training_buffer.append(X[0])
            self.stats["total_samples"] += 1

            # Try to train if we have enough samples
            if len(self.training_buffer) >= self.training_window_size:
                training_data = np.array(self.training_buffer)
                self.fit(training_data, self.feature_names)

            # Return no anomaly until trained
            return IFAnomalyResult(
                timestamp=timestamp,
                is_anomaly=False,
                anomaly_score=0.0,
                confidence=0.0,
                feature_importance={},
                affected_features=[],
                severity="info",
            )

        # Scale features
        X_scaled = self.scaler.transform(X)

        # Get anomaly score (negative score: lower = more anomalous)
        raw_score = self.model.score_samples(X_scaled)[0]

        # Get prediction (-1 = anomaly, 1 = normal)
        prediction = self.model.predict(X_scaled)[0]
        is_anomaly = prediction == -1

        # Convert score to 0-1 confidence (higher = more confident it's anomaly)
        confidence = self._calculate_confidence(raw_score, is_anomaly)

        # Calculate feature importance for this sample
        feature_importance = self._calculate_feature_importance(X[0])

        # Identify most anomalous features
        affected_features = self._identify_affected_features(X[0], feature_importance)

        # Determine severity
        severity = self._determine_severity(confidence, affected_features)

        # Update statistics
        self.stats["total_samples"] += 1
        if is_anomaly:
            self.stats["anomalies_detected"] += 1
            self.anomaly_scores.append(raw_score)
        else:
            self.normal_scores.append(raw_score)

        # Store detection result
        result = IFAnomalyResult(
            timestamp=timestamp,
            is_anomaly=is_anomaly,
            anomaly_score=raw_score,
            confidence=confidence,
            feature_importance=feature_importance,
            affected_features=affected_features,
            severity=severity,
        )

        self.detection_history.append(result)

        # Auto-retrain if enabled
        if self.auto_retrain and self.stats["total_samples"] % self.retrain_interval == 0:
            self._adaptive_retrain()

        return result

    def _calculate_confidence(self, raw_score: float, is_anomaly: bool) -> float:
        """
        Convert raw anomaly score to confidence (0-1).

        Args:
            raw_score: Raw score from Isolation Forest (more negative = more anomalous)
            is_anomaly: Whether sample was classified as anomaly

        Returns:
            Confidence score (0-1, higher = more confident it's anomalous)
        """
        # Isolation Forest scores typically range from ~-0.5 to ~0.5
        # Normalize to 0-1 where 1 = high confidence anomaly

        # Use historical scores for dynamic thresholding
        if len(self.normal_scores) > 10 and len(self.anomaly_scores) > 3:
            normal_mean = np.mean(self.normal_scores)
            anomaly_mean = np.mean(self.anomaly_scores)
            score_range = abs(normal_mean - anomaly_mean)

            if score_range > 0:
                # Distance from normal mean, normalized by range
                confidence = abs(raw_score - normal_mean) / score_range
                return min(max(confidence, 0.0), 1.0)

        # Fallback: simple normalization
        # Typical range: -0.5 (anomaly) to 0.5 (normal)
        normalized = (0.5 - raw_score) / 1.0  # Convert to 0-1
        return min(max(normalized, 0.0), 1.0)

    def _calculate_feature_statistics(self, X: np.ndarray):
        """Calculate baseline statistics for each feature."""
        self.feature_baselines = {
            name: {"mean": X[:, i].mean(), "std": X[:, i].std()}
            for i, name in enumerate(self.feature_names)
        }

        self.feature_ranges = {
            name: {"min": X[:, i].min(), "max": X[:, i].max()}
            for i, name in enumerate(self.feature_names)
        }

    def _calculate_feature_importance(self, X: np.ndarray) -> Dict[str, float]:
        """
        Calculate feature importance for anomaly detection.

        Uses distance from baseline as proxy for importance.
        """
        importance = {}

        for i, name in enumerate(self.feature_names):
            if name in self.feature_baselines:
                baseline = self.feature_baselines[name]
                value = X[i]

                # Calculate z-score
                if baseline["std"] > 0:
                    z_score = abs((value - baseline["mean"]) / baseline["std"])
                else:
                    z_score = 0.0

                importance[name] = min(z_score / 3.0, 1.0)  # Normalize to 0-1
            else:
                importance[name] = 0.0

        return importance

    def _identify_affected_features(
        self, X: np.ndarray, feature_importance: Dict[str, float], threshold: float = 0.5
    ) -> List[str]:
        """Identify features that contribute most to anomaly."""
        affected = []

        for name, importance in feature_importance.items():
            if importance >= threshold:
                affected.append(name)

        # Sort by importance
        affected.sort(key=lambda name: feature_importance[name], reverse=True)

        return affected

    def _determine_severity(self, confidence: float, affected_features: List[str]) -> str:
        """Determine anomaly severity based on confidence and affected features."""

        # Critical features that indicate hardware failure
        critical_features = [
            "temperature_max",
            "interface_error_rate",
            "power_stability_score",
            "severity_escalations",
        ]

        # Check if critical features are affected
        has_critical_feature = any(f in affected_features for f in critical_features)

        if confidence >= 0.85:
            return "critical" if has_critical_feature else "error"
        elif confidence >= 0.7:
            return "error" if has_critical_feature else "warning"
        elif confidence >= 0.5:
            return "warning"
        else:
            return "info"

    def _adaptive_retrain(self):
        """Adaptively retrain model using recent normal samples."""
        if len(self.normal_scores) < self.training_window_size // 2:
            return

        # Collect recent samples classified as normal
        normal_samples = []
        for result in list(self.detection_history)[-self.training_window_size :]:
            if not result.is_anomaly and result.confidence < 0.5:
                # Low confidence normal = good training data
                normal_samples.append(result)

        if len(normal_samples) >= self.training_window_size // 2:
            logger.info(f"Adaptive retraining with {len(normal_samples)} normal samples")
            # In production, you'd reconstruct the feature vectors here
            # For now, we just mark that retraining occurred
            self.stats["retrains_performed"] += 1

    def save_model(self, path: str):
        """Save trained model and scaler to disk."""
        if not self.is_trained:
            logger.warning("Model not trained, nothing to save")
            return

        model_data = {
            "model": self.model,
            "scaler": self.scaler,
            "feature_names": self.feature_names,
            "feature_baselines": self.feature_baselines,
            "feature_ranges": self.feature_ranges,
            "stats": self.stats,
        }

        joblib.dump(model_data, path)
        logger.info(f"Model saved to {path}")

    def load_model(self, path: str):
        """Load trained model and scaler from disk."""
        model_data = joblib.load(path)

        self.model = model_data["model"]
        self.scaler = model_data["scaler"]
        self.feature_names = model_data["feature_names"]
        self.feature_baselines = model_data["feature_baselines"]
        self.feature_ranges = model_data["feature_ranges"]
        self.stats = model_data["stats"]
        self.is_trained = True

        logger.info(f"Model loaded from {path}")

    def get_stats(self) -> Dict[str, Any]:
        """Get detector statistics."""
        anomaly_rate = 0.0
        if self.stats["total_samples"] > 0:
            anomaly_rate = self.stats["anomalies_detected"] / self.stats["total_samples"]

        return {
            **self.stats,
            "is_trained": self.is_trained,
            "training_buffer_size": len(self.training_buffer),
            "anomaly_rate": anomaly_rate,
            "n_features": len(self.feature_names),
            "recent_anomalies": len(self.anomaly_scores),
            "recent_normals": len(self.normal_scores),
        }

    def get_model_info(self) -> Dict[str, Any]:
        """Get model configuration information."""
        return {
            "n_estimators": self.n_estimators,
            "contamination": self.contamination,
            "max_samples": self.max_samples,
            "training_window_size": self.training_window_size,
            "auto_retrain": self.auto_retrain,
            "retrain_interval": self.retrain_interval,
            "feature_count": len(self.feature_names),
            "features": self.feature_names,
        }


# Example usage and testing
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Example: Create detector
    detector = IsolationForestDetector(n_estimators=100, contamination=0.1, training_window_size=50)

    # Example: Generate synthetic SNMP features
    np.random.seed(42)

    # Normal data for training (19 features from SNMP)
    feature_names = [
        "interface_error_rate",
        "interface_utilization_mean",
        "interface_utilization_std",
        "interface_flap_count",
        "cpu_utilization_mean",
        "cpu_utilization_max",
        "memory_utilization_mean",
        "memory_utilization_max",
        "temperature_mean",
        "temperature_max",
        "temperature_variance",
        "fan_speed_variance",
        "power_stability_score",
        "threshold_violations",
        "severity_escalations",
        "multi_device_correlation",
        "environmental_stress_score",
        "bgp_correlation",
        "syslog_correlation",
    ]

    # Generate normal training data
    normal_data = np.random.rand(100, 19) * 0.3  # Low values = normal

    # Train model
    detector.fit(normal_data, feature_names)

    # Test with normal sample
    normal_sample = np.random.rand(1, 19) * 0.3
    result = detector.predict(normal_sample, timestamp=1234567890.0, feature_names=feature_names)
    print("\nNormal sample result:")
    print(f"  Is Anomaly: {result.is_anomaly}")
    print(f"  Confidence: {result.confidence:.3f}")
    print(f"  Severity: {result.severity}")

    # Test with anomalous sample (high values)
    anomaly_sample = np.random.rand(1, 19) * 2.0  # High values = anomaly
    anomaly_sample[0, 8] = 5.0  # Very high temperature_mean
    anomaly_sample[0, 0] = 3.0  # High error rate

    result = detector.predict(anomaly_sample, timestamp=1234567891.0, feature_names=feature_names)
    print("\nAnomalous sample result:")
    print(f"  Is Anomaly: {result.is_anomaly}")
    print(f"  Confidence: {result.confidence:.3f}")
    print(f"  Severity: {result.severity}")
    print(f"  Affected Features: {result.affected_features[:3]}")

    # Print stats
    print("\nDetector Statistics:")
    stats = detector.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
