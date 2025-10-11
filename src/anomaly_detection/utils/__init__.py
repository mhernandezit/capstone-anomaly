"""Shared utilities and schemas."""

from .schema import BGPUpdate, FeatureBin

# SNMPMetrics may not be in schema, check if it exists
try:
    from .schema import SNMPMetrics

    __all__ = ["BGPUpdate", "FeatureBin", "SNMPMetrics"]
except ImportError:
    __all__ = ["BGPUpdate", "FeatureBin"]
