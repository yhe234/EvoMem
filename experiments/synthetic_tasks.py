"""Synthetic non-stationary task streams for method-level evaluation."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any, Iterable


@dataclass
class SyntheticTask:
    task_id: str
    round_id: int
    subset_id: str
    query: str
    expected: str
    failure_injected: bool = False
    category: str = "general"


_CATEGORIES = [
    "compilation",
    "api_call",
    "env_fallback",
    "legal_clause",
    "symptom_diag",
    "reaction_type",
]


def _make_query(category: str, rng: random.Random) -> str:
    if category == "compilation":
        return f"Compilation error in module {rng.randint(0, 999)}"
    if category == "api_call":
        return f"API call returns 500 for endpoint /v{rng.randint(1, 3)}/items"
    if category == "env_fallback":
        return f"Missing env var VAR_{rng.randint(0, 99)} raises KeyError"
    if category == "legal_clause":
        return f"Employment clause #{rng.randint(0, 999)}"
    if category == "symptom_diag":
        return f"Patient reports symptom #{rng.randint(0, 999)}"
    if category == "reaction_type":
        return f"Reaction SMILES C{rng.randint(1, 9)}H{rng.randint(4, 12)}O"
    return f"Generic task {rng.randint(0, 9999)}"


def generate_task_stream(
    rounds: int,
    tasks_per_round: int,
    *,
    seed: int = 0,
    failure_rate: float = 0.3,
) -> list[list[SyntheticTask]]:
    """Return ``rounds`` lists, each containing ``tasks_per_round`` tasks."""
    rng = random.Random(seed)
    stream: list[list[SyntheticTask]] = []
    for round_id in range(1, rounds + 1):
        round_tasks: list[SyntheticTask] = []
        for i in range(tasks_per_round):
            category = rng.choice(_CATEGORIES)
            subset = f"subset-{round_id % 3}"
            task = SyntheticTask(
                task_id=f"task-{round_id}-{i}",
                round_id=round_id,
                subset_id=subset,
                query=_make_query(category, rng),
                expected=category,
                failure_injected=rng.random() < failure_rate,
                category=category,
            )
            round_tasks.append(task)
        stream.append(round_tasks)
    return stream


def inject_distribution_shift(stream: list[list[SyntheticTask]], shift_round: int = 5) -> list[list[SyntheticTask]]:
    """Introduce new categories after ``shift_round`` to simulate drift."""
    shifted: list[list[SyntheticTask]] = []
    for round_id, tasks in enumerate(stream, start=1):
        if round_id < shift_round:
            shifted.append(tasks)
            continue
        new_tasks = []
        for task in tasks:
            new_tasks.append(SyntheticTask(
                task_id=task.task_id,
                round_id=task.round_id,
                subset_id=f"shifted-{task.subset_id}",
                query=f"[DRIFT] {task.query}",
                expected=task.expected,
                failure_injected=True,
                category=task.category,
            ))
        shifted.append(new_tasks)
    return shifted


def flatten(stream: Iterable[Iterable[SyntheticTask]]) -> list[SyntheticTask]:
    return [task for round_tasks in stream for task in round_tasks]


__all__ = [
    "SyntheticTask",
    "generate_task_stream",
    "inject_distribution_shift",
    "flatten",
]
