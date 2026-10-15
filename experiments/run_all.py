"""Run the full method-focused experiment suite."""

from __future__ import annotations

import json
import os
from typing import Any

from .config import ExperimentConfig, load_config
from .run_ablation import run_ablation
from .run_case_studies import run_case_studies
from .run_conflict_arbitration import run_conflict_arbitration
from .run_mechanism_tests import run_mechanism_tests
from .run_promotion_dynamics import run_promotion_dynamics
from .run_retrieval_robustness import run_retrieval_robustness
from .run_sensitivity import run_sensitivity


def main() -> dict[str, Any]:
    config = load_config(rounds=6, tasks_per_round=6, name="main")
    results: dict[str, Any] = {}

    print("[1/7] mechanism tests")
    results["mechanism"] = run_mechanism_tests(config.output_dir)

    print("[2/7] promotion dynamics")
    results["dynamics"] = run_promotion_dynamics(config, config.output_dir)

    print("[3/7] ablation")
    results["ablation"] = run_ablation(config, config.output_dir)

    print("[4/7] sensitivity")
    results["sensitivity"] = run_sensitivity(config.output_dir)

    print("[5/7] conflict arbitration")
    results["arbitration"] = run_conflict_arbitration(config.output_dir)

    print("[6/7] retrieval robustness")
    results["retrieval"] = run_retrieval_robustness(config.output_dir)

    print("[7/7] case studies")
    results["case_studies"] = run_case_studies(output_dir=config.output_dir)

    summary_path = os.path.join(config.output_dir, "summary.json")
    os.makedirs(config.output_dir, exist_ok=True)
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump({k: str(type(v).__name__) for k, v in results.items()}, f, indent=2)
    return results


if __name__ == "__main__":
    main()
