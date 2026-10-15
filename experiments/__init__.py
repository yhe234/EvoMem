"""Experiment suite for the Meta-Memory Harness (EvoRule Harness).

Method-focused experiments only:
- mechanism correctness (Beta calibration, promotion lifecycle, rollback)
- promotion dynamics
- core component ablations
- hyperparameter sensitivity
- conflict arbitration strategies
- retrieval robustness
- case studies
"""

from .config import ExperimentConfig, iter_sensitivity_configs, load_config
from .utils import build_engine, build_store, make_evidence, make_patch, make_rule

__all__ = [
    "ExperimentConfig",
    "load_config",
    "iter_sensitivity_configs",
    "build_store",
    "build_engine",
    "make_rule",
    "make_patch",
    "make_evidence",
]
