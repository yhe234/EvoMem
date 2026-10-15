"""Beta-Bernoulli calibration tests (Eq. 6)."""

import pytest

from meta_memory.types import Rule


@pytest.mark.parametrize("c0,n0,S,F,expected", [
    (0.9, 2.0, 0, 0, 0.9),
    (0.9, 2.0, 1, 0, 0.9333),
    (0.9, 2.0, 3, 0, 0.96),
    (0.9, 2.0, 3, 1, 0.8889),
    (0.72, 2.0, 4, 0, 0.9067),
    (0.5, 2.0, 3, 0, 0.7143),
    (0.9, 5.0, 3, 0, 0.9474),
    (0.9, 10.0, 3, 0, 0.9231),
])
def test_beta_calibration(c0, n0, S, F, expected):
    rule = Rule(rule_id="r", phi="", psi="", initial_confidence=c0)
    alpha0 = n0 * c0
    beta0 = n0 * (1 - c0)
    rule.successes = S
    rule.failures = F
    assert abs(rule.posterior_confidence(alpha0, beta0) - expected) < 1e-3


def test_beta_calibration_via_confidence_prior():
    rule = Rule(rule_id="r", phi="", psi="", initial_confidence=0.9)
    rule.provenance["confidence_prior"] = {"alpha": 1.8, "beta": 0.2}
    rule.successes = 3
    rule.failures = 0
    assert abs(rule.confidence - 0.96) < 1e-3
