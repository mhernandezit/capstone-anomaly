"""
Anomaly Detection - Machine Learning for Network Anomaly and Failure Detection

A comprehensive ML system for detecting and localizing network anomalies using
multi-modal data sources (BGP, SNMP, syslog) and intelligent correlation.
"""

__version__ = "1.0.0"
__author__ = "Michael Hernandez"

# Core ML Models
# Correlation System
from .correlation import MultiModalCorrelator

# Feature Extraction
from .features import (
    FeatureAggregator,
    SNMPFeatureExtractor,
)
from .models import (
    GPUMPDetector,
    IsolationForestDetector,
    MatrixProfileDetector,
)

# Topology Triage
from .triage import (
    ImpactScorer,
    TopologyTriage,
    TopologyTriageSystem,
)

# Data Schemas
from .utils import (
    BGPUpdate,
    FeatureBin,
)

__all__ = [
    # Models
    "MatrixProfileDetector",
    "IsolationForestDetector",
    "GPUMPDetector",
    # Correlation
    "MultiModalCorrelator",
    # Features
    "FeatureAggregator",
    "SNMPFeatureExtractor",
    # Triage
    "TopologyTriage",
    "TopologyTriageSystem",
    "ImpactScorer",
    # Utils
    "BGPUpdate",
    "FeatureBin",
]
