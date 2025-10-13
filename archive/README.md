# Archive - Scope Creep Items

This directory contains files that were moved out of the main codebase to reduce scope creep and focus on the core requirements.

## Archived Items

### Duplicate ML Models (`models/`)
- `mp_detector.py` - Duplicate Matrix Profile implementation
- `gpu_mp_detector.py` - GPU-accelerated Matrix Profile (not needed for capstone)

**Kept**: `matrix_profile_detector.py` and `isolation_forest_detector.py` (core requirements)

### Complex Dashboard (`dashboards/`)
- `modern_dashboard.py` - Over-engineered dashboard with 300+ lines
- `README.md` - Complex dashboard documentation

**Kept**: `real_ml_dashboard.py` (simple, focused dashboard)

### Excess Example Scripts (`examples/`)
- `comprehensive_dashboard_demo.py` - Complex demo script
- `ml_pipeline_integration.py` - Redundant integration example
- `run_complete_system.py` - Duplicate system runner
- `run_multimodal_correlation.py` - Redundant correlation demo

**Kept**: `demo_multimodal_correlation.py` (core demo functionality)

### Complex Topology System (`topology/`)
- `network_graph.py` - Over-engineered topology with 400+ lines
- `__init__.py` - Complex topology module
- `__pycache__/` - Compiled Python files

**Replaced with**: Simple role-based topology in triage system

## Rationale

The original proposal called for:
1. Dual ML pipelines (Matrix Profile + Isolation Forest) 
2. Multi-modal correlation 
3. Topology-aware localization 
4. Simple dashboard for demo 
5. Basic example scripts 

The archived items represent scope creep that added complexity without contributing to the core capstone objectives. The simplified codebase now focuses on the essential functionality required by the proposal.

## Restoration

If any archived functionality is needed later, files can be restored from this archive. However, the current simplified implementation meets all requirements and is more maintainable.

## Archive Date

October 13, 2025 - Before final cleanup and project finalization
