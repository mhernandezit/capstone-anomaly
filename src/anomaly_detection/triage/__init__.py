"""Topology-aware triage components."""

from .impact import ImpactScorer
from .topology_triage import TopologyTriageSystem, TopologyLocation, BlastRadius, CriticalityAssessment, TriageResult

# Alias for backward compatibility
TopologyTriage = TopologyTriageSystem

__all__ = [
    "TopologyTriageSystem", 
    "TopologyTriage", 
    "ImpactScorer",
    "TopologyLocation",
    "BlastRadius", 
    "CriticalityAssessment",
    "TriageResult",
]
