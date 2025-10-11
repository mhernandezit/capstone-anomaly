"""ML models for anomaly detection."""

from .gpu_mp_detector import GPUMPDetector
from .isolation_forest_detector import IsolationForestDetector
from .matrix_profile_detector import MatrixProfileDetector

# Legacy support (deprecated)
from .mp_detector import MPDetector

__all__ = [
    "MatrixProfileDetector",
    "IsolationForestDetector",
    "GPUMPDetector",
    "MPDetector",  # Deprecated - use MatrixProfileDetector
]
