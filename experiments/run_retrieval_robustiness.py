"""Retrieval robustness: Top-K and threshold sensitivity."""

from __future__ import annotations

import json
import os
from typing import Any

from meta_memory import MMHConfig, MetaMemoryEngine, PatchOperation, Rule, RuleTier

from .config import ExperimentConfig
from .utils import build_engine, build_store, make_evidence, make_patch, make_rule


def _populate_rules(engine: MetaMemoryEngine, count: int = 20) -> None:
    for i in range(count):
        rule = make_rule(
            f"rule-{i}",
            phi=f"context-{i}",
            psi=f"action-{i}",
            c0=0.9,
        )
        patch = make_patch(
            f"patch-{i}", PatchOperation.ADD,
            result_rules=(rule,), context=rule.phi,
            provenance={"failure_case": f"case-{i}"},
        )
        engine.update_cycle([patch], i + 1, [make_evidence(patch.patch_id, True, f"s-{i}", i + 1, recovered=True)])


def _evaluate_retrieval(
    engine: MetaMemoryEngine,
    top_k: int,
    threshold: float,
    queries: list[str],
) -> dict[str, float]:
    hits = 0
    for q in queries:
        rules = engine.retrieve(q, min_similarity=threshold)
        rules = rules[:top_k]
        if rules:
            hits += 1
    return {
        "pass_at_1": hits / max(1, len(queries)),
        "recall_at_k": hits / max(1, len(queries)),
    }


def run_retrieval_robustness(output_dir: str = "reports/results") -> dict[str, Any]:
    providers = ["hash"]  # extend with "openai", "sentence-transformers", "bge-m3"
    top_k_values = [1, 3, 5, 10, 20]
    thresholds = [0.5, 0.6, 0.7, 0.8, 0.9]
    queries = [f"context-{i}" for i in range(10)]

    results: list[dict[str, Any]] = []
    for provider in providers:
        for top_k in top_k_values:
            for threshold in thresholds:
                store = build_store()
                engine = build_engine(store, ExperimentConfig())
                _populate_rules(engine, count=20)
                metrics = _evaluate_retrieval(engine, top_k, threshold, queries)
                results.append({
                    "provider": provider,
                    "top_k": top_k,
                    "threshold": threshold,
                    **metrics,
                })
                store.close()

    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "retrieval_robustness.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, sort_keys=True)
    return {"results": results, "path": path}


if __name__ == "__main__":
    out = run_retrieval_robustness()
    print(json.dumps(out["results"], indent=2, sort_keys=True))
