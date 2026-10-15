"""Promotion dynamics on a synthetic non-stationary stream."""

from __future__ import annotations

import json
import os
from typing import Any

from meta_memory import PatchOperation, RuleTier

from .config import ExperimentConfig
from .synthetic_tasks import SyntheticTask, generate_task_stream, inject_distribution_shift
from .utils import build_engine, build_store, make_evidence, make_patch, make_rule, stable_count, volatile_count


def _task_to_patch(task: SyntheticTask, round_id: int) -> tuple[Any, Any]:
    """Convert a synthetic task into one atomic ADD patch + validation evidence."""
    rule = make_rule(
        f"rule-{task.task_id}",
        phi=f"context for {task.category}",
        psi=f"handle {task.category}",
        c0=0.85,
    )
    patch = make_patch(
        f"patch-{task.task_id}",
        PatchOperation.ADD,
        result_rules=(rule,),
        context=rule.phi,
        judge_confidence=0.85,
        provenance={"failure_case": task.task_id} if task.failure_injected else {},
    )
    evidence = make_evidence(
        patch.patch_id,
        success=not task.failure_injected,
        subset_id=task.subset_id,
        round_id=round_id,
        recovered=not task.failure_injected,
    )
    return patch, evidence


def record_round(store, engine, round_id: int, cycle_result: dict[str, Any]) -> dict[str, Any]:
    volatile_rules = store.list_rules(RuleTier.VOLATILE)
    stable_rules = store.list_rules(RuleTier.STABLE)
    avg_conf = (
        sum(r.confidence for r in volatile_rules + stable_rules)
        / max(1, len(volatile_rules) + len(stable_rules))
    )
    avg_age = (
        sum(r.elapsed_age for r in volatile_rules + stable_rules)
        / max(1, len(volatile_rules) + len(stable_rules))
    )
    avg_lifespan = (
        sum(r.successful_lifespan for r in volatile_rules + stable_rules)
        / max(1, len(volatile_rules) + len(stable_rules))
    )
    avg_subsets = (
        sum(len(r.independent_subsets) for r in volatile_rules + stable_rules)
        / max(1, len(volatile_rules) + len(stable_rules))
    )
    return {
        "round": round_id,
        "volatile_count": len(volatile_rules),
        "stable_count": len(stable_rules),
        "promoted": len(cycle_result.get("promoted", [])),
        "resolved": len(cycle_result.get("resolved", [])),
        "staged": len(cycle_result.get("staged", [])),
        "rolled_back": sum(
            1 for p in cycle_result.get("resolved", [])
            if p.status.value == "rolled_back"
        ),
        "rejected": sum(
            1 for p in cycle_result.get("staged", [])
            if p.status.value == "rejected"
        ),
        "avg_confidence": avg_conf,
        "avg_age": avg_age,
        "avg_lifespan": avg_lifespan,
        "avg_subsets": avg_subsets,
    }


def run_dynamics(config: ExperimentConfig) -> list[dict[str, Any]]:
    store = build_store()
    engine = build_engine(store, config)
    try:
        stream = generate_task_stream(
            config.rounds,
            config.tasks_per_round,
            seed=config.seed,
            failure_rate=0.3,
        )
        if config.rounds >= 5:
            stream = inject_distribution_shift(stream, shift_round=max(3, config.rounds // 2))

        history: list[dict[str, Any]] = []
        for round_id, tasks in enumerate(stream, start=1):
            patches = []
            evidences = []
            for task in tasks:
                p, e = _task_to_patch(task, round_id)
                patches.append(p)
                evidences.append(e)
            cycle = engine.update_cycle(patches, round_id, evidences)
            history.append(record_round(store, engine, round_id, cycle))
        return history
    finally:
        store.close()


def run_promotion_dynamics(
    config: ExperimentConfig | None = None,
    output_dir: str = "reports/results",
) -> dict[str, Any]:
    config = config or ExperimentConfig()
    history = run_dynamics(config)
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, f"dynamics_{config.name}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, sort_keys=True)
    return {"history": history, "path": path}


if __name__ == "__main__":
    out = run_promotion_dynamics()
    print(json.dumps(out["history"], indent=2, sort_keys=True))
