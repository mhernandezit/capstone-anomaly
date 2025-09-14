"""
Preprocessing Pipeline

This module provides feature extraction and preprocessing capabilities
based on the Feltin 2023 paper on feature selection for network telemetry.
"""

from .feature_extractor import (
    SemanticFeatureExtractor, 
    FeatureSelector, 
    PreprocessingPipeline,
    ExtractedFeatures,
    FeatureWindow
)

__all__ = [
    'SemanticFeatureExtractor',
    'FeatureSelector', 
    'PreprocessingPipeline',
    'ExtractedFeatures',
    'FeatureWindow'
]
