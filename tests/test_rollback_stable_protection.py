"""Rollback and stable-protection tests."""

from meta_memory import (
    MMHConfig, MetaMemoryEngine, PatchOperation, PatchStatus, Rule, RuleTier,
    SQLiteStore, ValidationEvidence,
)
from meta_memory.types import Patch


def _make_rule(rule_id, c0=0.9):
    return Rule(rule_id=rule_id, phi=f"phi-{rule_id}", psi=f"psi-{rule_id}",
                initial_confidence=c0, omega="pending")


def _add_patch(patch_id, rule_id):
    return Patch(
        patch_id=patch_id, operation=PatchOperation.ADD,
        result_rules=(_make_rule(rule_id),), context=f"phi-{rule_id}",
        judge_confidence=0.9, provenance={"failure_case": "case"},
    )


def _evidence(patch_id, success, subset, round_id, recovered=None):
    return ValidationEvidence(
        patch_id=patch_id, success=success, subset_id=subset,
        round_id=round_id, original_failure_recovered=recovered,
    )


def test_failing_patch_rolls_back():
    store = SQLiteStore(":memory:")
    engine = MetaMemoryEngine(store, config=MMHConfig())
    patch = _add_patch("p-bad", "r-bad")
    engine.update_cycle([patch], 1, [_evidence("p-bad", False, "s1", 1)])
    p = store.get_patch("p-bad")
    assert p.status is PatchStatus.ROLLED_BACK
    assert store.get_rule("r-bad") is None
    store.close()


def test_refine_on_stable_rejected():
    store = SQLiteStore(":memory:")
    engine = MetaMemoryEngine(store, config=MMHConfig(prior_strength=2.0, promotion_age=3))
    # Promote a stable rule
    patch = _add_patch("p-stable", "r-stable")
    engine.update_cycle([patch], 1, [_evidence("p-stable", True, "s1", 1, recovered=True)])
    engine.update_cycle([], 2, [_evidence("p-stable", True, "s2", 2)])
    engine.update_cycle([], 3, [_evidence("p-stable", True, "s3", 3)])
    engine.update_cycle([], 4)
    r = store.get_rule("r-stable")
    assert r.tier is RuleTier.STABLE

    # Attempt direct REFINE
    refine = Patch(
        patch_id="p-refine",
        operation=PatchOperation.REFINE,
        target_rule_ids=("r-stable",),
        result_rules=(_make_rule("r-stable-refined"),),
        context="phi-r-stable",
    )
    accepted = engine.filter_and_resolve([refine])
    assert len(accepted) == 0
    store.close()


def test_stable_delete_requires_repeated_failures():
    store = SQLiteStore(":memory:")
    engine = MetaMemoryEngine(store, config=MMHConfig(stable_failure_rounds=5))
    patch = _add_patch("p-stable", "r-stable")
    engine.update_cycle([patch], 1, [_evidence("p-stable", True, "s1", 1, recovered=True)])
    engine.update_cycle([], 2, [_evidence("p-stable", True, "s2", 2)])
    engine.update_cycle([], 3, [_evidence("p-stable", True, "s3", 3)])
    engine.update_cycle([], 4)

    # Only 2 failures recorded; DELETE must be rejected
    for i, subset in enumerate(["a", "b"], start=5):
        engine.record_rule_observation("r-stable", False, subset, i)
    delete = Patch(
        patch_id="p-delete", operation=PatchOperation.DELETE,
        target_rule_ids=("r-stable",),
    )
    accepted = engine.filter_and_resolve([delete])
    assert len(accepted) == 0
    store.close()
