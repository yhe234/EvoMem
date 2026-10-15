```markdown
# EvoRule Harness

Provider-neutral, training-free implementation of **EvoRule Harness** — a two-tier memory of validated causal rules for lifelong harness adaptation. Volatile edits are isolated, re-tested, and promoted to stable memory only after evidence-gated validation. Stable memory is never directly overwritten.

---

## Features

- **Two-tier rule memory**: `volatile` scratchpad + `stable` validated knowledge.
- **Atomic edit operations**: `ADD`, `DELETE`, `REFINE`, `SPLIT`, `MERGE`.
- **Beta-Bernoulli calibration** (Eq. 6): `alpha0 = n0*c0`, `beta0 = n0*(1-c0)`.
- **Evidence-gated promotion** (Eq. 5): `c_t >= 0.8`, `age >= 3`.
- **Stable protection**: stable rules only permit `MERGE` / `DELETE` after repeated cross-subset failures.
- **Conflict resolution**: stable rules take precedence over volatile edits.
- **Provider-neutral**: works with any frozen LLM harness, no gradients or weight updates.
- **Plug-and-play**: drop-in integration with existing harness optimizers.
- **Transactional SQLite persistence** with full audit trail.

---

## Installation

```bash
git clone https://github.com/yhe234/EvoMem.git
cd EvoMem
pip install -e .
```

Optional extras:

```bash
pip install openai>=1.0                # OpenAI-compatible embeddings
pip install sentence-transformers      # Local embedding models
pip install matplotlib pytest          # Experiments and tests
```

### Environment Files

The repository ships with the following dependency manifests:

| File | Purpose |
|---|---|
| `pyproject.toml` | Package metadata, core dependencies, optional extras. |
| `requirements.txt` | Pinned core runtime requirements. |
| `requirements-dev.txt` | Pinned development and experiment requirements. |
| `environment.yml` | Conda environment for full reproducibility. |

Install with pins:

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

Or with Conda:

```bash
conda env create -f environment.yml
conda activate evorule
```

---

## Repository Layout

```
evorule_harness/          # Core package (provider-neutral)
  __init__.py             # Public exports
  types.py                # Rule, Patch, ValidationEvidence, EvoRuleConfig
  engine.py               # Algorithm 1 lifecycle
  store.py                # Transactional SQLite persistence
  embeddings.py           # Embedding engines (hash / openai / sentence-transformers)
  adapters.py             # Response validators and prompt templates
  demo.py                 # Teaching walkthrough

experiments/              # Method-focused experiment suite
  __init__.py
  config.py               # ExperimentConfig and sweep generators
  utils.py                # Builders and ablation hooks
  metrics.py              # Method-level metrics
  plotting.py             # Figure helpers
  synthetic_tasks.py      # Non-stationary task streams
  run_mechanism_tests.py  # Beta calibration, promotion lifecycle, rollback
  run_promotion_dynamics.py
  run_ablation.py
  run_sensitivity.py
  run_conflict_arbitration.py
  run_retrieval_robustness.py
  run_case_studies.py
  run_all.py              # Full suite entry point

integrations/             # Plug-and-play integrations with base harnesses
  tthe/                   # EvoRule Harness + TTHE
  meta_harness/           # EvoRule Harness + Meta-Harness

tests/                    # Unit and lifecycle tests
  test_beta_calibration.py
  test_promotion_lifecycle.py
  test_rollback_stable_protection.py
  test_evidence_uniqueness_aging.py

data/                     # Case study data and data preparation notes
  case_studies_data.py    # S2D, LawBench, USPTO-50k, SWE-bench case data
  README.md               # Benchmark download and layout instructions

reports/                  # Table and figure generators
  generate_tables.py
  generate_figures.py
```

> **Note**: `experiments/`, `integrations/`, and `tests/` are not part of the installable package. Run all experiment and integration commands from the repository root so that `python -m experiments.*` and `python -m integrations.*` resolve correctly.

---

## Quick Start

```python
from evorule_harness import (
    EvoRuleConfig, EvoRuleEngine, Patch, PatchOperation,
    Rule, SQLiteStore, ValidationEvidence,
)

store = SQLiteStore(":memory:")
engine = EvoRuleEngine(store, config=EvoRuleConfig(
    prior_strength=2.0,        # n0 for Eq. 6
    promotion_confidence=0.8,  # theta_c
    promotion_age=3,           # theta_age
))

rule = Rule(
    rule_id="contrastive-verify",
    phi="identical retrieved labels and low confidence",
    psi="retrieve counterexamples and ask for comparative verification",
    omega="pending",
    initial_confidence=0.9,
)
patch = Patch(
    patch_id="repair-contrastive",
    operation=PatchOperation.ADD,
    result_rules=(rule,),
    context=rule.phi,
    judge_confidence=0.9,
    provenance={"failure_case": "rare-class-retrieval"},
)

# Round 1: stage + first successful retest
engine.update_cycle([patch], 1, [
    ValidationEvidence(
        patch_id=patch.patch_id, success=True,
        subset_id="gastro", round_id=1,
        original_failure_recovered=True,
    )
])

# Rounds 2-3: cross-subset validation
engine.update_cycle([], 2, [
    ValidationEvidence(patch_id=patch.patch_id, success=True,
                       subset_id="dermatology", round_id=2)
])
engine.update_cycle([], 3, [
    ValidationEvidence(patch_id=patch.patch_id, success=True,
                       subset_id="vascular", round_id=3)
])

# Round 4: promotion
result = engine.update_cycle([], 4)
print(result["promoted"])          # [contrastive-verify]
print(store.get_rule("contrastive-verify").tier)  # RuleTier.STABLE
store.close()
```

Run the deterministic demo:

```bash
python -m evorule_harness.demo
```

---

## Core Concepts

### Causal Rule

| Field | Symbol | Meaning |
|---|---|---|
| Applicability context | `phi` | When the rule fires. |
| Intervention | `psi` | Action to execute. |
| Feedback | `omega` | `success` / `fail` / `pending`. |
| Confidence | `c` | Calibrated trust in `[0,1]`. |
| Lifespan | `tau` | Rounds survived. |

### Promotion

A volatile rule is promoted when:

```
c_t >= theta_c   AND   age >= theta_age
```

Default: `theta_c = 0.8`, `theta_age = 3`, `n0 = 2.0`.

Promotion is atomic and one-way. Stable memory is never directly modified by volatile edits.

### Stable Protection

- Stable rules only allow `MERGE` or `DELETE`.
- `DELETE` requires repeated cross-subset underperformance.
- Direct `REFINE` / `SPLIT` on stable rules is rejected.
- Conflicts resolve in favor of the stable tier.

---

## Integrations

EvoRule Harness is designed as a **plug-and-play memory layer**: it attaches to a frozen backbone and an existing harness optimizer without modifying either. The `integrations/` directory contains working examples:

- `integrations/tthe/` — EvoRule Harness + TTHE.
- `integrations/meta_harness/` — EvoRule Harness + Meta-Harness.

**More integrations are welcome and straightforward to add.** The core requirement is to connect EvoRule Harness to three components of the base harness:

1. **Proposer** — where candidate edits or harness updates are generated.
2. **Judger** — where failures are diagnosed and reflections are produced.
3. **Executor** — where candidate edits are applied and re-tested.

EvoRule Harness sits between these three: it converts the judger's reflections into atomic patches, stages them in the volatile tier, and promotes them to the stable tier only after evidence-gated validation. Any base harness that exposes these three roles can be integrated by implementing a thin adapter under `integrations/`.

---

## Experiments

Method-focused verification, no full benchmark re-run required.

```bash
# Mechanism correctness (Eq. 6, promotion lifecycle, rollback)
python -m experiments.run_mechanism_tests

# Promotion dynamics on a synthetic non-stationary stream
python -m experiments.run_promotion_dynamics --seed 0 --rounds 10

# Core component ablations
python -m experiments.run_ablation --seed 0

# Hyperparameter sensitivity
python -m experiments.run_sensitivity --seed 0

# Conflict arbitration strategies
python -m experiments.run_conflict_arbitration --seed 0

# Retrieval robustness (Top-K, thresholds)
python -m experiments.run_retrieval_robustness --seed 0

# Paper case studies (S2D, LawBench, USPTO-50k, SWE-bench)
python -m experiments.run_case_studies

# Everything
python -m experiments.run_all --seed 0 --rounds 10
```

Generate reports:

```bash
python -m reports.generate_tables
python -m reports.generate_figures
```

Results are written to `reports/results/`, tables to `reports/tables/`, figures to `reports/figures/`.

### Reproducibility

All experiment entry points accept `--seed` and `--rounds`. To reproduce a specific table or figure, use the same seed and round count reported alongside it. Example:

```bash
python -m experiments.run_promotion_dynamics --seed 0 --rounds 10
```

### Outputs and Gitignore

The following directories are **gitignored** because they contain large intermediate artifacts:

- `reports/results/`
- `reports/tables/`
- `reports/figures/`
- `integrations/*/results/`
- `integrations/*/reports/`

Only small, human-readable summaries are committed. Regenerate the rest with the commands above.

---

## Data Preparation

Benchmark data is **not** shipped with this repository. See [`data/README.md`](data/README.md) for:

- Where to download Tau-Bench, Terminal-Bench-2, SWE-bench Verified, LawBench, S2D, and USPTO-50k.
- The expected on-disk layout.
- How to point the experiments at the local data directory via environment variables such as `EVORULE_DATA_DIR`.

The only data bundled in the repository is `data/case_studies_data.py`, which contains the four paper case studies (S2D duodenal ulcer, LawBench non-compete, USPTO-50k heterocycle, SWE-bench Verified env fallback).

---

## Hardware and Runtime

The core package is CPU-only and has no GPU requirement. The experiments require a frozen LLM backbone; runtimes below assume a locally served or API-accessed backbone.

| Component | Hardware | Approx. runtime |
|---|---|---|
| Core unit tests | CPU, 2 cores | < 1 minute |
| `experiments.run_mechanism_tests` | CPU, 2 cores | < 1 minute |
| `experiments.run_promotion_dynamics` | CPU, 4 cores | 5–15 minutes |
| `experiments.run_ablation` | CPU, 4 cores | 20–40 minutes |
| `experiments.run_sensitivity` | CPU, 4 cores | 30–60 minutes |
| `experiments.run_conflict_arbitration` | CPU, 2 cores | < 5 minutes |
| `experiments.run_retrieval_robustness` | CPU, 4 cores | 5–15 minutes |
| `experiments.run_case_studies` | CPU, 2 cores | < 5 minutes |

Memory footprint is dominated by the SQLite rule store and is typically well under 1 GB.

---

## Testing

```bash
pytest tests/ -v
```

Coverage:

- Beta-Bernoulli calibration (Eq. 6)
- Promotion lifecycle (`PENDING → VALIDATED → STABLE`)
- Rollback and stable protection
- Evidence uniqueness and aging

---

## Configuration

All hyperparameters live in `EvoRuleConfig`:

| Parameter | Default | Paper |
|---|---|---|
| `prior_strength` (`n0`) | `2.0` | Eq. 6 |
| `promotion_confidence` (`theta_c`) | `0.8` | Eq. 5 |
| `promotion_age` (`theta_age`) | `3` | Eq. 5 |
| `influence_threshold` (`epsilon`) | `0.6` | Sec. 3.1 |
| `context_match_confidence` | `0.7` | Appendix A.4 |
| `stable_failure_rounds` | `5` | Sec. 3.2 |
| `stable_failure_subsets` | `2` | Sec. 3.2 |
| `promotion_subsets` | `1` | Eq. 5 |

Set `promotion_subsets >= 2` to enable the stricter multi-subset gate.
```