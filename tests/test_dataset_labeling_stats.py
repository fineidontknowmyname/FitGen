import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.dataset_labeling_stats import (
    class_balance,
    fleiss_kappa,
    interpret_kappa,
    majority_vote,
)


def test_fleiss_kappa_matches_hand_computed_reference_case():
    rows = [
        ["A", "A", "A"],
        ["A", "A", "B"],
        ["B", "B", "B"],
    ]
    kappa = fleiss_kappa(rows)
    assert kappa == pytest.approx(0.55, abs=1e-9)


def test_fleiss_kappa_perfect_agreement_is_one():
    rows = [
        ["low", "low", "low"],
        ["very_high", "very_high", "very_high"],
        ["moderate", "moderate", "moderate"],
    ]
    assert fleiss_kappa(rows) == pytest.approx(1.0, abs=1e-9)


def test_fleiss_kappa_requires_at_least_two_raters():
    with pytest.raises(ValueError):
        fleiss_kappa([["low"]])


def test_fleiss_kappa_requires_consistent_rater_count():
    with pytest.raises(ValueError):
        fleiss_kappa([["low", "high"], ["low", "high", "moderate"]])


def test_interpret_kappa_bands():
    assert interpret_kappa(-0.1) == "poor (worse than chance)"
    assert interpret_kappa(0.1) == "slight"
    assert interpret_kappa(0.3) == "fair"
    assert interpret_kappa(0.5) == "moderate"
    assert interpret_kappa(0.7) == "substantial"
    assert interpret_kappa(0.9) == "almost perfect"


def test_majority_vote_returns_winner():
    assert majority_vote(["high", "high", "moderate"]) == "high"


def test_majority_vote_returns_none_on_tie():
    assert majority_vote(["high", "moderate"]) is None


def test_class_balance_counts_majority_labels_and_ties_separately():
    rows = [
        ["high", "high", "moderate"],
        ["low", "low", "low"],
        ["high", "moderate"],
    ]
    balance = class_balance(rows)
    assert balance["high"] == 1
    assert balance["low"] == 1
    assert balance["__no_majority__"] == 1
