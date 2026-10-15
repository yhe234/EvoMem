"""Mechanism correctness tests for MMH (method-focused)."""

from __future__ import annotations

import json
import os
from typing import Any

from meta_memory import MMHConfig, MetaMemoryEngine, PatchOperation, Rule, RuleTier, SQLiteStore

from .utils import build_engine, build_store, make_evidence, make_patch, make_rule, rule_snapshot


def run_beta_calibration() -> list[dict[str, Any]]:
    """Verify Eq. 6: alpha0 = n0*c0, beta0 = n0*(1-c0), c_t = (a0+S)/(a0+b0+S+F)."""
    cases = [
        (0.9, 2.0, 0, 0, 0.9),
        (0.9, 2.0, 1, 0, 0.9333),
        (0.9, 2.0, 3, 0, 0.96),
        (0.9, 2.0, 3, 1, 0.8889),
        (0.72, 2.0, 4, 0, 0.9067),
        (0.5, 2.0, 3, 0, 0.7143),
        (0.9, 5.0, 3, 0, 0.9474),
        (0.9, 10.0, 3, 0, 0.9231),
    ]
    results = []
    for c0, n0, S, F, expected in cases:
        rule = Rule(rule_id="r", phi="phi", psi="psi", initial_confidence=c0)
        alpha0 = n0 * c0
        beta0 = n0 * (1 - c0)
        rule.successes = S
        rule.failures = F
        actual = rule.posterior_confidence(alpha0, beta0)
        results.append({
            "c0": c0, "n0": n0, "S": S, "F": F,
            "alpha0": alpha0, "beta0": beta0,
            "expected": expected, "actual": actual,
            "abs_error": abs(actual - expected),
            "ok": abs(actual - expected) < 1e-3,
        })
    return results


def run_promotion_lifecycle() -> dict[str, Any]:
    """Track one volatile rule from staging to stable promotion."""
    store = build_store()
    engine = build_engine(store)
    try:
        rule = make_rule("r-lifecycle", "phi-lifecycle", "psi-lifecycle", c0=0.9)
        patch = make_patch(
            "p-lifecycle",
            PatchOperation.ADD,
            result_rules=(rule,),
            context=rule.phi,
            judge_confidence=0.9,
            provenance={"failure_case": "case-lifecycle"},
        )
        trace: list[dict[str, Any]] = []

        engine.update_cycle(
            [patch], 1,
            [make_evidence("p-lifecycle", success=True, subset_id="s1", round_id=1, recovered=True)],
        )
        trace.append({"stage": "after_round_1", **rule_snapshot(store, "r-lifecycle")})

        engine.update_cycle(
            [], 2,
            [make_evidence("p-lifecycle", success=True, subset_id="s2", round_id=2)],
        )
        trace.append({"stage": "after_round_2", **rule_snapshot(store, "r-lifecycle")})

        engine.update_cycle(
            [], 3,
            [make_evidence("p-lifecycle", success=True, subset_id="s3", round_id=3)],
        )
        trace.append({"stage": "after_round_3", **rule_snapshot(store, "r-lifecycle")})

        result = engine.update_cycle([], 4)
        trace.append({"stage": "after_round_4", **rule_snapshot(store, "r-lifecycle")})

        promoted_ids = [r.rule_id for r in result["promoted"]]
        return {
            "trace": trace,
            "promoted": promoted_ids,
            "final_tier": rule_snapshot(store, "r-lifecycle")["tier"],
        }
    finally:
        store.close()


def run_rollback_protection() -> dict[str, Any]:
    """Volatile patch fails -> rolled back; stable is protected."""
    store = build_store()
    engine = build_engine(store)
    try:
        # Step 1: promote a stable rule
        rule = make_rule("r-stable", "stable-phi", "stable-psi", c0=0.95)
        patch = make_patch(
            "p-stable", PatchOperation.ADD,
            result_rules=(rule,), context=rule.phi,
            provenance={"failure_case": "case-stable"},
        )
        engine.update_cycle([patch], 1, [make_evidence("p-stable", True, "s1", 1, recovered=True)])
        engine.update_cycle([], 2, [make_evidence("p-stable", True, "s2", 2)])
        engine.update_cycle([], 3, [make_evidence("p-stable", True, "s3", 3)])
        engine.update_cycle([], 4)
        stable_snapshot = rule_snapshot(store, "r-stable")

        # Step 2: direct REFINE on stable must be rejected
        refine_patch = make_patch(
            "p-refine-stable", PatchOperation.REFINE,
            target_rule_ids=("r-stable",),
            result_rules=(make_rule("r-stable-refined", "new-phi", "new-psi"),),
            context="stable-phi",
        )
        accepted = engine.filter_and_resolve([refine_patch])
        refine_rejected = len(accepted) == 0

        # Step 3: failing volatile patch rolled back
        bad_rule = make_rule("r-bad", "bad-phi", "bad-psi", c0=0.9)
        bad_patch = make_patch(
            "p-bad", PatchOperation.ADD,
            result_rules=(bad_rule,), context=bad_rule.phi,
            provenance={"failure_case": "case-bad"},
        )
        engine.update_cycle([bad_patch], 5, [make_evidence("p-bad", False, "s-bad", 5)])
        bad_snapshot = rule_snapshot(store, "r-bad")
        bad_patch_obj = store.get_patch("p-bad")

        return {
            "stable_snapshot": stable_snapshot,
            "refine_rejected": refine_rejected,
            "bad_rule_present": bad_snapshot["present"],
            "bad_patch_status": bad_patch_obj.status.value if bad_patch_obj else None,
        }
    finally:
        store.close()


def run_mechanism_tests(output_dir: str = "reports/results") -> dict[str, Any]:
    os.makedirs(output_dir, exist_ok=True)
    results = {
        "beta_calibration": run_beta_calibration(),
        "promotion_lifecycle": run_promotion_lifecycle(),
        "rollback_protection": run_rollback_protection(),
    }
    path = os.path.join(output_dir, "mechanism.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, sort_keys=True)
    return results


if __name__ == "__main__":
    out = run_mechanism_tests()
    print(json.dumps(out, indent=2, sort_keys=True))
