"""Promotion lifecycle tests."""

from meta_memory import (
    MMHConfig, MetaMemoryEngine, PatchOperation, PatchStatus, Rule, RuleTier,
    SQLiteStore, ValidationEvidence,
)


def _make_rule(rule_id, c0=0.9):
    return Rule(rule_id=rule_id, phi=f"phi-{rule_id}", psi=f"psi-{rule_id}",
                initial_confidence=c0, omega="pending")


def _make_patch(patch_id, rule_id):
    from meta_memory.types import Patch
    return Patch(
        patch_id=patch_id,
        operation=PatchOperation.ADD,
        result_rules=(_make_rule(rule_id),),
        context=f"phi-{rule_id}",
        judge_confidence=0.9,
        provenance={"failure_case": "case-1"},
    )


def _evidence(patch_id, success, subset, round_id, recovered=None):
    return ValidationEvidence(
        patch_id=patch_id, success=success, subset_id=subset,
        round_id=round_id, original_failure_recovered=recovered,
    )


def test_promotion_lifecycle_full():
    store = SQLiteStore(":memory:")
    engine = MetaMemoryEngine(store, config=MMHConfig(prior_strength=2.0, promotion_age=3))
    patch = _make_patch("p1", "r1")

    engine.update_cycle([patch], 1, [_evidence("p1", True, "s1", 1, recovered=True)])
    r = store.get_rule("r1")
    assert r.tier is RuleTier.VOLATILE
    assert r.status is PatchStatus.VALIDATED
    assert r.original_failure_recovered is True

    engine.update_cycle([], 2, [_evidence("p1", True, "s2", 2)])
    engine.update_cycle([], 3, [_evidence("p1", True, "s3", 3)])
    result = engine.update_cycle([], 4)

    r = store.get_rule("r1")
    assert r.tier is RuleTier.STABLE
    assert "r1" in [x.rule_id for x in result["promoted"]]
    assert abs(r.confidence - 0.96) < 1e-3
    store.close()


def test_promotion_requires_age():
    store = SQLiteStore(":memory:")
    engine = MetaMemoryEngine(store, config=MMHConfig(promotion_age=3))
    patch = _make_patch("p1", "r1")
    engine.update_cycle([patch], 1, [_evidence("p1", True, "s1", 1, recovered=True)])
    r = store.get_rule("r1")
    assert r.tier is RuleTier.VOLATILE
    engine.update_cycle([], 2)
    r = store.get_rule("r1")
    assert r.tier is RuleTier.VOLATILE
    store.close()
