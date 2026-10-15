"""Conflict arbitration strategy comparison."""

from __future__ import annotations

import json
import os
import random
from typing import Any, Mapping, Sequence

from meta_memory import Rule, RuleTier

from .metrics import arbitration_success, sscv_accept, vsv_retain


def _make_stable_rule(rule_id: str, success_rate: float, rng: random.Random) -> Rule:
    rule = Rule(
        rule_id=rule_id,
        phi=f"stable-context-{rule_id}",
        psi=f"stable-action-{rule_id}",
        omega="success",
        initial_confidence=0.9,
        tier=RuleTier.STABLE,
    )
    rule.successes = int(success_rate * 10)
    rule.failures = 10 - rule.successes
    return rule


def _make_volatile_rule(rule_id: str, success_rate: float, rng: random.Random) -> Rule:
    rule = Rule(
        rule_id=rule_id,
        phi=f"volatile-context-{rule_id}",
        psi=f"volatile-action-{rule_id}",
        omega="pending",
        initial_confidence=0.7,
        tier=RuleTier.VOLATILE,
    )
    rule.successes = int(success_rate * 10)
    rule.failures = 10 - rule.successes
    return rule


def _arbitrate(strategy: str, stable: Rule, volatile: Rule, rng: random.Random) -> dict[str, Any]:
    if strategy == "stable_precedence":
        chosen = "stable"
    elif strategy == "confidence_gap":
        chosen = "volatile" if volatile.confidence > stable.confidence + 0.05 else "stable"
    elif strategy == "recency":
        chosen = "volatile"
    elif strategy == "local_validation_hit":
        chosen = "volatile" if volatile.successes >= 5 else "stable"
    elif strategy == "similarity":
        chosen = "volatile" if rng.random() > 0.5 else "stable"
    elif strategy == "hybrid":
        score_v = volatile.confidence + 0.1 * (volatile.successes >= 5)
        score_s = stable.confidence + 0.1
        chosen = "volatile" if score_v > score_s else "stable"
    else:
        raise ValueError(f"unknown strategy {strategy}")
    return {"chosen": chosen, "stable": stable, "volatile": volatile}


def _build_conflict_pairs(
    n_sscv: int,
    n_vsv: int,
    seed: int = 0,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """SSCV: stale stable vs correct volatile. VSV: valid stable vs noisy volatile."""
    rng = random.Random(seed)
    sscv = []
    for i in range(n_sscv):
        stable = _make_stable_rule(f"s-sscv-{i}", success_rate=0.35, rng=rng)
        volatile = _make_volatile_rule(f"v-sscv-{i}", success_rate=0.85, rng=rng)
        sscv.append({"stable": stable, "volatile": volatile, "ground_truth": "volatile"})
    vsv = []
    for i in range(n_vsv):
        stable = _make_stable_rule(f"s-vsv-{i}", success_rate=0.9, rng=rng)
        volatile = _make_volatile_rule(f"v-vsv-{i}", success_rate=0.2, rng=rng)
        vsv.append({"stable": stable, "volatile": volatile, "ground_truth": "stable"})
    return sscv, vsv


def run_arbitration(
    strategy: str,
    sscv: Sequence[Mapping[str, Any]],
    vsv: Sequence[Mapping[str, Any]],
    seed: int = 0,
) -> dict[str, float]:
    rng = random.Random(seed)
    sscv_results = []
    for pair in sscv:
        decision = _arbitrate(strategy, pair["stable"], pair["volatile"], rng)
        correct = decision["chosen"] == pair["ground_truth"]
        sscv_results.append({
            "accepted_volatile": decision["chosen"] == "volatile",
            "retained_stable": decision["chosen"] == "stable",
            "correct": correct,
        })
    vsv_results = []
    for pair in vsv:
        decision = _arbitrate(strategy, pair["stable"], pair["volatile"], rng)
        correct = decision["chosen"] == pair["ground_truth"]
        vsv_results.append({
            "accepted_volatile": decision["chosen"] == "volatile",
            "retained_stable": decision["chosen"] == "stable",
            "correct": correct,
        })
    all_results = sscv_results + vsv_results
    return {
        "SSCV Accept": sscv_accept(sscv_results),
        "VSV Retain": vsv_retain(vsv_results),
        "Success": arbitration_success(all_results),
        "Regress": 1.0 - arbitration_success(all_results),
        "Conflict": 0.0,
    }


def run_conflict_arbitration(output_dir: str = "reports/results") -> dict[str, Any]:
    sscv, vsv = _build_conflict_pairs(n_sscv=600, n_vsv=600, seed=0)
    strategies = [
        "stable_precedence",
        "confidence_gap",
        "recency",
        "local_validation_hit",
        "similarity",
        "hybrid",
    ]
    results: dict[str, Any] = {}
    for s in strategies:
        results[s] = run_arbitration(s, sscv, vsv, seed=0)

    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "arbitration.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, sort_keys=True)
    return results


if __name__ == "__main__":
    out = run_conflict_arbitration()
    print(json.dumps(out, indent=2, sort_keys=True))
