"""Evidence uniqueness and aging tests."""

from meta_memory import (
    MMHConfig, MetaMemoryEngine, PatchOperation, Rule, SQLiteStore, ValidationEvidence,
)
from meta_memory.types import Patch


def _rule(rule_id, c0=0.9):
    return Rule(rule_id=rule_id, phi=f"phi-{rule_id}", psi=f"psi-{rule_id}",
                initial_confidence=c0, omega="pending")


def _patch(patch_id, rule_id):
    return Patch(
        patch_id=patch_id, operation=PatchOperation.ADD,
        result_rules=(_rule(rule_id),), context=f"phi-{rule_id}",
        judge_confidence=0.9, provenance={"failure_case": "case"},
    )


def _evidence(patch_id, success, subset, round_id, recovered=None):
    return ValidationEvidence(
        patch_id=patch_id, success=success, subset_id=subset,
        round_id=round_id, original_failure_recovered=recovered,
    )


def test_duplicate_evidence_is_ignored():
    store = SQLiteStore(":memory:")
    engine = MetaMemoryEngine(store, config=MMHConfig())
    patch = _patch("p1", "r1")
    engine.update_cycle([patch], 1, [_evidence("p1", True, "s1", 1, recovered=True)])
    r = store.get_rule("r1")
    initial_successes = r.successes

    # Duplicate evidence with same (patch_id, subset_id, round_id)
    engine.update_cycle([], 1, [_evidence("p1", True, "s1", 1)])
    r = store.get_rule("r1")
    assert r.successes == initial_successes
    store.close()


def test_advance_round_aging():
    store = SQLiteStore(":memory:")
    engine = MetaMemoryEngine(store, config=MMHConfig())
    patch = _patch("p1", "r1")
    engine.update_cycle([patch], 1, [_evidence("p1", True, "s1", 1, recovered=True)])
    r = store.get_rule("r1")
    assert r.elapsed_age == 0

    engine.advance_round(2)
    r = store.get_rule("r1")
    assert r.elapsed_age >= 1

    engine.advance_round(3)
    r = store.get_rule("r1")
    assert r.elapsed_age >= 2
    store.close()


def test_same_round_multiple_subsets_counts_once_for_lifespan():
    store = SQLiteStore(":memory:")
    engine = MetaMemoryEngine(store, config=MMHConfig())
    patch = _patch("p1", "r1")
    engine.update_cycle([patch], 1, [
        _evidence("p1", True, "s1", 1, recovered=True),
        _evidence("p1", True, "s2", 1),
        _evidence("p1", True, "s3", 1),
    ])
    r = store.get_rule("r1")
    assert r.successes == 3
    assert r.successful_lifespan == 1
    assert len(r.independent_subsets) == 3
    store.close()
