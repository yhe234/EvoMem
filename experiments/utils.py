"""Utilities for building MMH engines, rules, patches, and evidence."""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Callable, Mapping, Sequence

from meta_memory import (
    MMHConfig,
    MetaMemoryEngine,
    Patch,
    PatchOperation,
    Rule,
    RuleTier,
    SQLiteStore,
    ValidationEvidence,
)

from .config import ExperimentConfig


# ---------------------------------------------------------------------------
# Store / engine construction
# ---------------------------------------------------------------------------

def build_store(path: str = ":memory:") -> SQLiteStore:
    return SQLiteStore(path)


def build_engine(
    store: SQLiteStore,
    config: ExperimentConfig | None = None,
    *,
    embedding_provider: Callable[[str], Sequence[float]] | None = None,
) -> MetaMemoryEngine:
    """Build an engine and apply ablation hooks without touching the core package."""
    config = config or ExperimentConfig()
    mmh_config = MMHConfig(
        prior_strength=config.prior_strength,
        promotion_confidence=config.promotion_confidence,
        promotion_age=config.promotion_age,
        promotion_subsets=config.promotion_subsets,
        influence_threshold=config.influence_threshold,
        stable_failure_rounds=config.stable_failure_rounds,
        stable_failure_subsets=config.stable_failure_subsets,
        gaussian_bandwidth=config.gaussian_bandwidth,
        minimum_comparable_precedents=config.minimum_comparable_precedents,
        context_match_confidence=config.context_match_confidence,
    )
    engine = MetaMemoryEngine(
        store,
        embedding_provider=embedding_provider,
        config=mmh_config,
    )
    _apply_ablations(engine, config)
    return engine


def _apply_ablations(engine: MetaMemoryEngine, config: ExperimentConfig) -> None:
    if config.disable_promotion:
        engine._eligible_for_promotion = lambda rule: False  # type: ignore[assignment]

    if config.disable_stable:
        engine.promote_eligible = lambda round_id: []  # type: ignore[assignment]

    if config.disable_credit_assignment:
        engine._rule_ids_receiving_evidence = lambda patch: ()  # type: ignore[assignment]

    if config.disable_precedent_gate:
        engine.config.influence_threshold = 0.0

    if config.disable_volatile:
        # Direct-to-stable ablation: rules enter stable tier immediately.
        original_stage = engine.stage_patch

        def stage_direct(patch, round_id):
            staged = original_stage(patch, round_id)
            for rule in staged.result_rules:
                stored = engine.store.get_rule(rule.rule_id)
                if stored is not None:
                    stored.tier = RuleTier.STABLE
                    stored.status = PatchStatus.VALIDATED
                    engine.store.put_rule(stored)
            return staged

        engine.stage_patch = stage_direct  # type: ignore[assignment]

    if config.disable_conflict_arbitration:
        original_filter = engine.filter_and_resolve

        def filter_without_conflict(patches):
            winners = original_filter(patches)
            return winners

        engine.filter_and_resolve = filter_without_conflict  # type: ignore[assignment]

    if config.disable_context_matcher:
        # Disable the second-stage matcher: rely on embedding similarity only.
        pass  # engine.retrieve already does pure embedding retrieval

    if config.disable_atomic_ops:
        allowed = set(config.allowed_operations or ("ADD", "DELETE"))
        original_validate = engine._validate_patch_shape

        def validate_restricted(patch):
            original_validate(patch)
            if patch.operation.value not in allowed:
                raise ValueError(f"operation {patch.operation.value} disabled by ablation")

        engine._validate_patch_shape = validate_restricted  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Rule / patch / evidence builders
# ---------------------------------------------------------------------------

def make_rule(
    rule_id: str,
    phi: str,
    psi: str,
    *,
    c0: float = 0.9,
    omega: str = "pending",
    tier: RuleTier = RuleTier.VOLATILE,
    provenance: Mapping[str, Any] | None = None,
) -> Rule:
    return Rule(
        rule_id=rule_id,
        phi=phi,
        psi=psi,
        omega=omega,
        initial_confidence=float(c0),
        tier=tier,
        provenance=dict(provenance or {}),
    )


def make_patch(
    patch_id: str,
    operation: PatchOperation,
    *,
    target_rule_ids: Sequence[str] = (),
    result_rules: Sequence[Rule] = (),
    context: str = "",
    judge_confidence: float = 0.9,
    provenance: Mapping[str, Any] | None = None,
) -> Patch:
    return Patch(
        patch_id=patch_id,
        operation=operation,
        target_rule_ids=tuple(target_rule_ids),
        result_rules=tuple(result_rules),
        context=context,
        judge_confidence=float(judge_confidence),
        provenance=dict(provenance or {}),
    )


def make_evidence(
    patch_id: str,
    *,
    success: bool,
    subset_id: str,
    round_id: int,
    recovered: bool | None = None,
    applicable: bool = True,
    details: Mapping[str, Any] | None = None,
) -> ValidationEvidence:
    return ValidationEvidence(
        patch_id=patch_id,
        success=bool(success),
        subset_id=subset_id,
        round_id=int(round_id),
        original_failure_recovered=recovered,
        applicable=applicable,
        details=dict(details or {}),
    )


# ---------------------------------------------------------------------------
# Introspection helpers
# ---------------------------------------------------------------------------

def rule_snapshot(store: SQLiteStore, rule_id: str) -> dict[str, Any]:
    rule = store.get_rule(rule_id)
    if rule is None:
        return {"rule_id": rule_id, "present": False}
    return {
        "rule_id": rule.rule_id,
        "present": True,
        "tier": rule.tier.value,
        "status": rule.status.value,
        "phi": rule.phi,
        "psi": rule.psi,
        "confidence": rule.confidence,
        "successes": rule.successes,
        "failures": rule.failures,
        "elapsed_age": rule.elapsed_age,
        "successful_lifespan": rule.successful_lifespan,
        "independent_subsets": sorted(rule.independent_subsets),
        "original_failure_required": rule.original_failure_required,
        "original_failure_recovered": rule.original_failure_recovered,
        "confidence_prior": rule.provenance.get("confidence_prior"),
        "successful_rounds": rule.provenance.get("successful_rounds", []),
    }


def stable_count(store: SQLiteStore) -> int:
    return len(store.list_rules(RuleTier.STABLE))


def volatile_count(store: SQLiteStore) -> int:
    return len(store.list_rules(RuleTier.VOLATILE))


__all__ = [
    "build_store",
    "build_engine",
    "make_rule",
    "make_patch",
    "make_evidence",
    "rule_snapshot",
    "stable_count",
    "volatile_count",
]
