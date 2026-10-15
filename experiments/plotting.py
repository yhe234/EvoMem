"""Plotting helpers for MMH experiment reports."""

from __future__ import annotations

import os
from typing import Any, Mapping, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


def _ensure_dir(path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)


def plot_promotion_curve(history: Sequence[Mapping[str, Any]], path: str) -> None:
    rounds = [h["round"] for h in history]
    volatile = [h.get("volatile_count", 0) for h in history]
    stable = [h.get("stable_count", 0) for h in history]
    promoted = [h.get("promoted", 0) for h in history]
    rolled_back = [h.get("rolled_back", 0) for h in history]

    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    axes[0].plot(rounds, volatile, label="volatile", marker="o")
    axes[0].plot(rounds, stable, label="stable", marker="s")
    axes[0].set_xlabel("Round")
    axes[0].set_ylabel("Rule count")
    axes[0].set_title("Rule inventory")
    axes[0].legend()

    axes[1].plot(rounds, promoted, label="promoted", marker="o")
    axes[1].plot(rounds, rolled_back, label="rolled_back", marker="x")
    axes[1].set_xlabel("Round")
    axes[1].set_ylabel("Count")
    axes[1].set_title("Per-round events")
    axes[1].legend()

    fig.tight_layout()
    _ensure_dir(path)
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_sensitivity_heatmap(
    results: Sequence[Mapping[str, Any]],
    x_key: str,
    y_key: str,
    value_key: str,
    path: str,
) -> None:
    xs = sorted({r[x_key] for r in results})
    ys = sorted({r[y_key] for r in results})
    grid = [[float("nan")] * len(xs) for _ in ys]
    for r in results:
        i = ys.index(r[y_key])
        j = xs.index(r[x_key])
        grid[i][j] = r[value_key]

    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(grid, cmap="viridis", aspect="auto")
    ax.set_xticks(range(len(xs)))
    ax.set_xticklabels(xs)
    ax.set_yticks(range(len(ys)))
    ax.set_yticklabels(ys)
    ax.set_xlabel(x_key)
    ax.set_ylabel(y_key)
    ax.set_title(value_key)
    fig.colorbar(im, ax=ax)
    fig.tight_layout()
    _ensure_dir(path)
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_ablation_bar(results: Mapping[str, float], path: str) -> None:
    names = list(results.keys())
    values = [results[n] for n in names]
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.bar(range(len(names)), values, color="steelblue")
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, rotation=30, ha="right")
    ax.set_ylabel("Pass@1")
    ax.set_title("Ablation study")
    fig.tight_layout()
    _ensure_dir(path)
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_conflict_arbitration(results: Mapping[str, Mapping[str, float]], path: str) -> None:
    strategies = list(results.keys())
    metrics = ["SSCV Accept", "VSV Retain", "Success", "Regress", "Conflict"]
    fig, ax = plt.subplots(figsize=(10, 5))
    width = 0.15
    for i, m in enumerate(metrics):
        values = [results[s].get(m, 0.0) for s in strategies]
        ax.bar([x + i * width for x in range(len(strategies))], values, width=width, label=m)
    ax.set_xticks([x + 2 * width for x in range(len(strategies))])
    ax.set_xticklabels(strategies, rotation=20, ha="right")
    ax.set_ylabel("Score")
    ax.set_title("Conflict arbitration strategies")
    ax.legend()
    fig.tight_layout()
    _ensure_dir(path)
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_retrieval_robustness(results: Sequence[Mapping[str, Any]], path: str) -> None:
    providers = sorted({r["provider"] for r in results})
    fig, ax = plt.subplots(figsize=(8, 5))
    for provider in providers:
        subset = [r for r in results if r["provider"] == provider]
        subset.sort(key=lambda r: r["top_k"])
        xs = [r["top_k"] for r in subset]
        ys = [r["pass_at_1"] for r in subset]
        ax.plot(xs, ys, marker="o", label=provider)
    ax.set_xlabel("Top-K")
    ax.set_ylabel("Pass@1")
    ax.set_title("Retrieval robustness")
    ax.legend()
    fig.tight_layout()
    _ensure_dir(path)
    fig.savefig(path, dpi=150)
    plt.close(fig)


__all__ = [
    "plot_promotion_curve",
    "plot_sensitivity_heatmap",
    "plot_ablation_bar",
    "plot_conflict_arbitration",
    "plot_retrieval_robustness",
]
