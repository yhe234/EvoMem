"""Core component ablations for MMH."""

from __future__ import annotations

import json
import os
from dataclasses import replace
from typing import Any

from .config import ExperimentConfig
from .run_promotion_dynamics import run_dynamics


def _summarize(history: list[dict[str, Any]]) -> dict[str, float]:
    if not history:
        return {"final_stable": 0.0, "final_volatile": 0.0, "total_promoted": 0.0,
                "total_rolled_back": 0.0, "avg_confidence": 0.0}
    return {
        "final_stable": float(history[-1]["stable_count"]),
        "final_volatile": float(history[-1]["volatile_count"]),
        "total_promoted": float(sum(h["promoted"] for h in history)),
        "total_rolled_back": float(sum(h["rolled_back"] for h in history)),
        "avg_confidence": float(
            sum(h["avg_confidence"] for h in history) / len(history)
        ),
    }


def _variants(base: ExperimentConfig) -> dict[str, ExperimentConfig]:
    return {
        "full": replace(base, name="full"),
        "w/o_promotion": replace(base, name="w_o_promotion", disable_promotion=True),
        "w/o_volatile": replace(base, name="w_o_volatile", disable_volatile=True),
        "w/o_stable": replace(base, name="w_o_stable", disable_stable=True),
        "w/o_credit_assignment": replace(base, name="w_o_credit", disable_credit_assignment=True),
        "w/o_atomic_ops": replace(
            base, name="w_o_atomic",
            disable_atomic_ops=True,
            allowed_operations=("ADD", "DELETE"),
        ),
        "w/o_precedent_gate": replace(base, name="w_o_precedent", disable_precedent_gate=True),
        "w/o_conflict_arbitration": replace(
            base, name="w_o_arbitration", disable_conflict_arbitration=True,
        ),
        "w/o_context_matcher": replace(
            base, name="w_o_matcher", disable_context_matcher=True,
        ),
        "stable_refine_allowed": replace(
            base, name="stable_refine_allowed",
            allowed_operations=("ADD", "DELETE", "REFINE", "SPLIT", "MERGE"),
        ),
    }


def run_ablation(
    base_config: ExperimentConfig | None = None,
    output_dir: str = "reports/results",
) -> dict[str, Any]:
    base = base_config or ExperimentConfig(rounds=8, tasks_per_round=8)
    variants = _variants(base)
    results: dict[str, Any] = {}
    for name, config in variants.items():
        history = run_dynamics(config)
        results[name] = _summarize(history)

    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "ablation.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, sort_keys=True)
    return results


if __name__ == "__main__":
    out = run_ablation()
    print(json.dumps(out, indent=2, sort_keys=True))
