"""Generate Markdown tables from experiment results."""

from __future__ import annotations

import json
import os
from typing import Any


def _load(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def table_ablation(results_path: str) -> str:
    data = _load(results_path)
    lines = ["| Variant | Stable | Volatile | Promoted | Rolled back | Avg conf |",
             "|---|---:|---:|---:|---:|---:|"]
    for name, row in data.items():
        lines.append(
            f"| {name} | {row['final_stable']:.1f} | {row['final_volatile']:.1f} | "
            f"{row['total_promoted']:.0f} | {row['total_rolled_back']:.0f} | "
            f"{row['avg_confidence']:.3f} |"
        )
    return "\n".join(lines)


def table_arbitration(results_path: str) -> str:
    data = _load(results_path)
    lines = ["| Strategy | SSCV Accept | VSV Retain | Success | Regress | Conflict |",
             "|---|---:|---:|---:|---:|---:|"]
    for name, row in data.items():
        lines.append(
            f"| {name} | {row['SSCV Accept']:.3f} | {row['VSV Retain']:.3f} | "
            f"{row['Success']:.3f} | {row['Regress']:.3f} | {row['Conflict']:.3f} |"
        )
    return "\n".join(lines)


def table_beta_calibration(results_path: str) -> str:
    data = _load(results_path)["beta_calibration"]
    lines = ["| c0 | n0 | S | F | Expected | Actual | OK |",
             "|---|---:|---:|---:|---:|---:|---|"]
    for row in data:
        lines.append(
            f"| {row['c0']} | {row['n0']} | {row['S']} | {row['F']} | "
            f"{row['expected']:.4f} | {row['actual']:.4f} | {row['ok']} |"
        )
    return "\n".join(lines)


def generate_tables(results_dir: str = "reports/results", table_dir: str = "reports/tables") -> dict[str, str]:
    os.makedirs(table_dir, exist_ok=True)
    out: dict[str, str] = {}

    mech_path = os.path.join(results_dir, "mechanism.json")
    if os.path.exists(mech_path):
        out["beta_calibration"] = table_beta_calibration(mech_path)
        with open(os.path.join(table_dir, "beta_calibration.md"), "w", encoding="utf-8") as f:
            f.write(out["beta_calibration"])

    ab_path = os.path.join(results_dir, "ablation.json")
    if os.path.exists(ab_path):
        out["ablation"] = table_ablation(ab_path)
        with open(os.path.join(table_dir, "ablation.md"), "w", encoding="utf-8") as f:
            f.write(out["ablation"])

    arb_path = os.path.join(results_dir, "arbitration.json")
    if os.path.exists(arb_path):
        out["arbitration"] = table_arbitration(arb_path)
        with open(os.path.join(table_dir, "arbitration.md"), "w", encoding="utf-8") as f:
            f.write(out["arbitration"])

    return out


if __name__ == "__main__":
    tables = generate_tables()
    for name, content in tables.items():
        print(f"=== {name} ===")
        print(content)
        print()
