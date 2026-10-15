"""Experiment configuration for Meta-Memory Harness method evaluation."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Iterable


@dataclass
class ExperimentConfig:
    # Stream
    seed: int = 0
    rounds: int = 10
    tasks_per_round: int = 10

    # MMH hyperparameters (paper-aligned defaults)
    promotion_confidence: float = 0.8
    promotion_age: int = 3
    prior_strength: float = 2.0
    promotion_subsets: int = 1
    influence_threshold: float = 0.6
    stable_failure_rounds: int = 5
    stable_failure_subsets: int = 2
    gaussian_bandwidth: float = 1.0
    minimum_comparable_precedents: int = 3
    context_match_confidence: float = 0.7

    # Ablation toggles
    disable_promotion: bool = False
    disable_volatile: bool = False
    disable_stable: bool = False
    disable_credit_assignment: bool = False
    disable_atomic_ops: bool = False
    disable_precedent_gate: bool = False
    disable_conflict_arbitration: bool = False
    disable_context_matcher: bool = False

    # Operation set restriction (used by disable_atomic_ops)
    allowed_operations: tuple[str, ...] | None = None

    # Output
    output_dir: str = "reports/results"
    figure_dir: str = "reports/figures"
    table_dir: str = "reports/tables"

    # Label
    name: str = "full"


def load_config(**overrides: Any) -> ExperimentConfig:
    return ExperimentConfig(**overrides)


def with_overrides(config: ExperimentConfig, **overrides: Any) -> ExperimentConfig:
    return replace(config, **overrides)


def iter_sensitivity_configs(
    thetas_c: Iterable[float] = (0.7, 0.75, 0.8, 0.85, 0.9),
    thetas_age: Iterable[int] = (1, 2, 3, 4, 5),
    n0s: Iterable[float] = (1.0, 2.0, 5.0, 10.0),
) -> list[ExperimentConfig]:
    configs: list[ExperimentConfig] = []
    for theta_c in thetas_c:
        for theta_age in thetas_age:
            for n0 in n0s:
                configs.append(ExperimentConfig(
                    promotion_confidence=float(theta_c),
                    promotion_age=int(theta_age),
                    prior_strength=float(n0),
                    name=f"sens_c{theta_c}_a{theta_age}_n{n0}",
                ))
    return configs


def iter_influence_configs(
    epsilons: Iterable[float] = (0.4, 0.5, 0.6, 0.7, 0.8),
) -> list[ExperimentConfig]:
    return [
        ExperimentConfig(influence_threshold=float(eps), name=f"inf_{eps}")
        for eps in epsilons
    ]


def iter_subset_configs(
    subsets: Iterable[int] = (1, 2, 3),
) -> list[ExperimentConfig]:
    return [
        ExperimentConfig(promotion_subsets=int(s), name=f"sub_{s}")
        for s in subsets
    ]


def iter_stable_failure_configs(
    rounds: Iterable[int] = (3, 5, 7),
) -> list[ExperimentConfig]:
    return [
        ExperimentConfig(stable_failure_rounds=int(r), name=f"sfr_{r}")
        for r in rounds
    ]


__all__ = [
    "ExperimentConfig",
    "load_config",
    "with_overrides",
    "iter_sensitivity_configs",
    "iter_influence_configs",
    "iter_subset_configs",
    "iter_stable_failure_configs",
]
