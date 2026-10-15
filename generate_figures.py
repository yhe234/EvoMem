"""Generate figures from experiment results."""

from __future__ import annotations

import json
import os
from typing import Any

from experiments.plotting import (
    plot_ablation_bar,
    plot_conflict_arbitration,
    plot_promotion_curve,
    plot_sensitivity_heatmap,
)


def _load(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_figures(results_dir: str = "reports/results", figure_dir: str = "reports/figures") -> dict[str, str]:
    os.makedirs(figure_dir, exist_ok=True)
    out: dict[str, str] = {}

    dyn_path = os.path.join(results_dir, "dynamics_main.json")
    if os.path.exists(dyn_path):
        history = _load(dyn_path)
        path = os.path.join(figure_dir, "promotion_curve.png")
        plot_promotion_curve(history, path)
        out["promotion_curve"] = path

    ab_path = os.path.join(results_dir, "ablation.json")
    if os.path.exists(ab_path):
        data = _load(ab_path)
        flat = {name: row["final_stable"] for name, row in data.items()}
        path = os.path.join(figure_dir, "ablation.png")
        plot_ablation_bar(flat, path)
        out["ablation"] = path

    arb_path = os.path.join(results_dir, "arbitration.json")
    if os.path.exists(arb_path):
        data = _load(arb_path)
        path = os.path.join(figure_dir, "arbitration.png")
        plot_conflict_arbitration(data, path)
        out["arbitration"] = path

    sens_path = os.path.join(results_dir, "sensitivity_promotion.json")
    if os.path.exists(sens_path):
        data = _load(sens_path)
        path = os.path.join(figure_dir, "sensitivity_promotion.png")
        plot_sensitivity_heatmap(data, "promotion_confidence", "promotion_age", "final_stable", path)
        out["sensitivity_promotion"] = path

    return out


if __name__ == "__main__":
    figs = generate_figures()
    for name, path in figs.items():
        print(f"{name}: {path}")
