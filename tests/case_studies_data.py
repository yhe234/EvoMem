"""Case study data from the paper, used by case study experiments."""

from __future__ import annotations

S2D_CASE = {
    "case_id": "s2d-duodenal-ulcer",
    "description": "Duodenal ulcer misclassified as Gastritis",
    "query": "burning epigastric pain, 2-3 hours after meals, at night, relieved by food; nausea",
    "expected": "Peptic ulcer disease",
    "wrong": "Gastritis",
    "subset_id": "gastro",
    "cross_subsets": ["dermatology", "vascular"],
    "patches": [
        {
            "patch_id": "patch-s2d-1",
            "operation": "ADD",
            "rule_id": "s2d-contrastive-verify",
            "phi": "top 3 labels agree but confidence < 0.85 and rare disease absent",
            "psi": "retrieve challenger diagnoses and re-query",
            "c0": 0.75,
        }
    ],
}

LAWBENCH_CASE = {
    "case_id": "lawbench-noncompete",
    "description": "Non-compete clause misclassified as Confidentiality",
    "query": "Employment agreement clause with post-departure competition restriction, monthly non-compete compensation, territory scope",
    "expected": "Non-compete",
    "wrong": "Confidentiality",
    "subset_id": "legal",
    "cross_subsets": ["labor", "contract"],
    "patches": [
        {
            "patch_id": "patch-lawbench-1",
            "operation": "ADD",
            "rule_id": "lawbench-noncompete-rule",
            "phi": "post-departure restriction with non-compete compensation and territory/duration",
            "psi": "Classify as Non-compete; check compensation, duration, territory",
            "c0": 0.72,
        }
    ],
}

USPTO_CASE = {
    "case_id": "uspto-heterocycle",
    "description": "Heterocycle formation misclassified as amide coupling",
    "query": "2-aminophenol + aldehyde in ethanol under reflux, cyclization and dehydration to benzoxazole",
    "expected": "heterocycle formation",
    "wrong": "amide coupling",
    "subset_id": "reaction",
    "cross_subsets": ["organic", "medicinal"],
    "patches": [
        {
            "patch_id": "patch-uspto-refine",
            "operation": "REFINE",
            "target_rule_ids": ("rule-amide-012",),
            "rule_id": "uspto-amide-refined",
            "phi": "amino-carbonyl condensation without cyclization/dehydration",
            "psi": "Classify as amide coupling only when acyclic amide forms",
            "c0": 0.78,
        },
        {
            "patch_id": "patch-uspto-add",
            "operation": "ADD",
            "rule_id": "uspto-heterocycle-rule",
            "phi": "aminophenol + aldehyde forms benzoxazole/oxazole ring",
            "psi": "Classify as heterocycle formation",
            "c0": 0.78,
        },
    ],
}

SWE_CASE = {
    "case_id": "swe-env-fallback",
    "description": "Missing APP_MODE env var raises KeyError; wrong file edited",
    "query": "When APP_MODE is not set, load_config raises KeyError; expected fallback to development with warning",
    "expected": "app/config/parser.py uses os.environ.get('APP_MODE', 'development')",
    "wrong": "Add APP_MODE: development to config.yaml",
    "subset_id": "swe",
    "cross_subsets": ["db", "logging"],
    "patches": [
        {
            "patch_id": "patch-swe-1",
            "operation": "ADD",
            "rule_id": "swe-env-fallback-rule",
            "phi": "KeyError for env var during config loading, expected fallback behavior",
            "psi": "Localize fix to parser/loader; use os.environ.get with default; emit warning",
            "c0": 0.80,
        }
    ],
}


ALL_CASES = [S2D_CASE, LAWBENCH_CASE, USPTO_CASE, SWE_CASE]


__all__ = ["S2D_CASE", "LAWBENCH_CASE", "USPTO_CASE", "SWE_CASE", "ALL_CASES"]
