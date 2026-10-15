"""Hyperparameter sensitivity for MMH promotion."""

from __future__ import annotations

import json
import os
from typing import Any

from .config import (
    ExperimentConfig,
    iter_influence_configs,
    iter_sensitivity_configs,
    iter_stable_failure_configs,
    iter_subset_configs,
)
from .run_promotion_dynamics import run_dynamics


def _summarize(history: list[dict[str, Any]]) -> dict[str, float]:
    if not history:
        return {"final_stable": 0.0, "total_promoted": 0.0, "avg_confidence": 0.0}
    return {
        "final_stable": float(history[-1]["stable_count"]),
        "final_volatile": float(history[-1]["volatile_count"]),
        "total_promoted": float(sum(h["promoted"] for h in history)),
        "total_rolled_back": float(sum(h["rolled_back"] for h in history)),
        "avg_confidence": float(sum(h["avg_confidence"] for h in history) / len(history)),
    }


def _run_configs(configs: list[ExperimentConfig], label: str, output_dir: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for config in configs:
        history = run_dynamics(config)
        summary = _summarize(history)
        rows.append({
            "name": config.name,
            "promotion_confidence": config.promotion_confidence,
            "promotion_age": config.promotion_age,
            "prior_strength": config.prior_strength,
            "influence_threshold": config.influence_threshold,
            "promotion_subsets": config.promotion_subsets,
            "stable_failure_rounds": config.stable_failure_rounds,
            **summary,
        })
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, f"sensitivity_{label}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2, sort_keys=True)
    return rows


def run_sensitivity(output_dir: str = "reports/results") -> dict[str, Any]:
    base = ExperimentConfig(rounds=6, tasks_per_round=6)
    results = {
        "promotion": _run_configs(iter_sensitivity_configs(), "promotion", output_dir),
        "influence": _run_configs(iter_influence_configs(), "influence", output_dir),
        "subsets": _run_configs(iter_subset_configs(), "subsets", output_dir),
        "stable_failure": _run_configs(iter_stable_failure_configs(), "stable_failure", output_dir),
    }
    return results


if __name__ == "__main__":
    out = run_sensitivity()
    print(json.dumps(out, indent=2, sort_keys=True))
