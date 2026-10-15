"""Case studies from the paper, replayed against the fixed MMH implementation."""

from __future__ import annotations

import json
import os
from typing import Any

from meta_memory import PatchOperation, RuleTier

from .utils import build_engine, build_store, make_evidence, make_patch, make_rule, rule_snapshot


def _run_generic_case(case: dict[str, Any]) -> dict[str, Any]:
    store = build_store()
    engine = build_engine(store)
    try:
        trace: list[dict[str, Any]] = []

        # 1. Failure case
        trace.append({"stage": "failure_case", "case": case})

        # 2. Atomic patch (ADD or REFINE + ADD)
        patches = []
        for i, p in enumerate(case["patches"]):
            rule = make_rule(
                p["rule_id"], p["phi"], p["psi"],
                c0=p.get("c0", 0.75),
            )
            patch = make_patch(
                p["patch_id"],
                PatchOperation(p["operation"]),
                target_rule_ids=tuple(p.get("target_rule_ids", ())),
                result_rules=(rule,),
                context=rule.phi,
                judge_confidence=p.get("c0", 0.75),
                provenance={"failure_case": case["case_id"]},
            )
            patches.append(patch)

        # 3. Volatile staging
        cycle = engine.update_cycle(patches, 1)
        for patch in cycle["staged"]:
            trace.append({
                "stage": "staged",
                "patch_id": patch.patch_id,
                "status": patch.status.value,
                "result_rules": [rule_snapshot(store, r.rule_id) for r in patch.result_rules],
            })

        # 4. Retest on same failure case
        evidence = []
        for patch in cycle["staged"]:
            evidence.append(make_evidence(
                patch.patch_id, True, case["subset_id"], 1, recovered=True,
            ))
        engine.update_cycle([], 1, evidence)
        for patch in cycle["staged"]:
            trace.append({
                "stage": "validated",
                "patch_id": patch.patch_id,
                "result_rules": [rule_snapshot(store, r.rule_id) for r in patch.result_rules],
            })

        # 5. Cross-subset validation
        for round_id, subset in enumerate(case["cross_subsets"], start=2):
            evidence = []
            for patch in cycle["staged"]:
                evidence.append(make_evidence(
                    patch.patch_id, True, subset, round_id,
                ))
            engine.update_cycle([], round_id, evidence)

        # 6. Promotion
        promotion_round = len(case["cross_subsets"]) + 2
        result = engine.update_cycle([], promotion_round)
        trace.append({
            "stage": "promoted",
            "promoted_ids": [r.rule_id for r in result["promoted"]],
            "rules": [
                rule_snapshot(store, r.rule_id)
                for r in result["promoted"]
            ],
        })

        # 7. Stable protection: attempt direct REFINE on stable rule
        if result["promoted"]:
            stable_id = result["promoted"][0].rule_id
            refine_patch = make_patch(
                f"refine-{stable_id}",
                PatchOperation.REFINE,
                target_rule_ids=(stable_id,),
                result_rules=(make_rule(f"{stable_id}-refined", "new-phi", "new-psi"),),
                context="new-phi",
            )
            accepted = engine.filter_and_resolve([refine_patch])
            trace.append({
                "stage": "stable_protection",
                "refine_accepted": len(accepted) > 0,
                "expected": False,
            })

        return {
            "case_id": case["case_id"],
            "trace": trace,
            "final_state": {
                "stable_rules": [r.rule_id for r in store.list_rules(RuleTier.STABLE)],
                "volatile_rules": [r.rule_id for r in store.list_rules(RuleTier.VOLATILE)],
            },
        }
    finally:
        store.close()


def run_case_studies(
    cases: list[dict[str, Any]] | None = None,
    output_dir: str = "reports/results",
) -> dict[str, Any]:
    from data.case_studies_data import ALL_CASES
    cases = cases or ALL_CASES
    results = {}
    for case in cases:
        results[case["case_id"]] = _run_generic_case(case)

    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "case_studies.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, sort_keys=True)
    return results


if __name__ == "__main__":
    out = run_case_studies()
    print(json.dumps(out, indent=2, sort_keys=True))
