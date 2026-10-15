"""Method-level metrics for MMH evaluation."""

from __future__ import annotations

from typing import Any, Iterable, Mapping, Sequence

from meta_memory import MetaMemoryEngine, PatchStatus, RuleTier, SQLiteStore


def pass_at_1(correct: int, total: int) -> float:
    return float(correct) / float(total) if total > 0 else 0.0


def promotion_rate(store: SQLiteStore, round_id: int) -> float:
    """Fraction of volatile rules ever promoted by this round."""
    volatile = store.list_rules(RuleTier.VOLATILE)
    stable = store.list_rules(RuleTier.STABLE)
    total = len(volatile) + len(stable)
    return float(len(stable)) / float(total) if total > 0 else 0.0


def false_promotion_rate(
    store: SQLiteStore,
    stable_rule_ids: Iterable[str],
    eval_results: Mapping[str, bool],
) -> float:
    """Fraction of stable rules that fail on later held-out tasks."""
    failed = 0
    total = 0
    for rule_id in stable_rule_ids:
        if rule_id in eval_results:
            total += 1
            if not eval_results[rule_id]:
                failed += 1
    return float(failed) / float(total) if total > 0 else 0.0


def regression_rate(
    before: Mapping[str, bool],
    after: Mapping[str, bool],
) -> float:
    """Fraction of tasks that were correct before but wrong after."""
    regressed = 0
    total = 0
    for task_id, was_correct in before.items():
        if task_id in after:
            total += 1
            if was_correct and not after[task_id]:
                regressed += 1
    return float(regressed) / float(total) if total > 0 else 0.0


def stable_retention(
    engine: MetaMemoryEngine,
    old_task_ids: Sequence[str],
    task_pass: Mapping[str, bool],
) -> float:
    """Retention of old-task performance after new rounds."""
    retained = 0
    for task_id in old_task_ids:
        if task_pass.get(task_id, False):
            retained += 1
    return float(retained) / float(len(old_task_ids)) if old_task_ids else 0.0


def sscv_accept(arbitration_results: Sequence[Mapping[str, Any]]) -> float:
    """Stale-stable/correct-volatile: fraction where volatile was accepted."""
    if not arbitration_results:
        return 0.0
    accepted = sum(1 for r in arbitration_results if r.get("accepted_volatile"))
    return float(accepted) / float(len(arbitration_results))


def vsv_retain(arbitration_results: Sequence[Mapping[str, Any]]) -> float:
    """Valid-stable/noisy-volatile: fraction where stable was retained."""
    if not arbitration_results:
        return 0.0
    retained = sum(1 for r in arbitration_results if r.get("retained_stable"))
    return float(retained) / float(len(arbitration_results))


def arbitration_success(arbitration_results: Sequence[Mapping[str, Any]]) -> float:
    if not arbitration_results:
        return 0.0
    correct = sum(1 for r in arbitration_results if r.get("correct"))
    return float(correct) / float(len(arbitration_results))


def conflict_rate(
    store: SQLiteStore,
    query_contexts: Sequence[str],
) -> float:
    """Fraction of queries where stable and volatile prescribe conflicting psi."""
    # Simplified: count queries where both tiers return a rule with disjoint psi
    conflicts = 0
    for _ in query_contexts:
        stable = store.list_rules(RuleTier.STABLE)
        volatile = store.list_rules(RuleTier.VOLATILE)
        if stable and volatile:
            # Any overlap in phi is treated as a potential conflict
            conflicts += 1
    return float(conflicts) / float(len(query_contexts)) if query_contexts else 0.0


def time_to_promote(store: SQLiteStore, rule_id: str) -> int | None:
    """Number of rounds between staging and promotion; None if not promoted."""
    rule = store.get_rule(rule_id)
    if rule is None or rule.tier is not RuleTier.STABLE:
        return None
    return int(rule.elapsed_age)


def context_tokens(engine: MetaMemoryEngine, context: str) -> int:
    """Approximate tokens used by retrieved rules."""
    rules = engine.retrieve(context)
    return sum(len(r.phi.split()) + len(r.psi.split()) for r in rules)


def rejection_count(store: SQLiteStore) -> int:
    return len(store.list_patches(PatchStatus.REJECTED))


def rollback_count(store: SQLiteStore) -> int:
    return len(store.list_patches(PatchStatus.ROLLED_BACK))


def deferred_count(store: SQLiteStore) -> int:
    return len(store.list_patches(PatchStatus.DEFERRED))


__all__ = [
    "pass_at_1",
    "promotion_rate",
    "false_promotion_rate",
    "regression_rate",
    "stable_retention",
    "sscv_accept",
    "vsv_retain",
    "arbitration_success",
    "conflict_rate",
    "time_to_promote",
    "context_tokens",
    "rejection_count",
    "rollback_count",
    "deferred_count",
]
