"""Difference ladders, run classification, and reverse-engineering noisy data."""

from fractions import Fraction

import pytest

from omnidimensional import (aggregate, assemble, assemble_runs, classify,
                             difference_ladder, name_run, newton_sum,
                             newton_term, ratio_ladder, reverse,
                             reverse_engineer, segment, ComputeError)


# --------------------------------------------------------------- ladders

def test_difference_ladder_flattens_at_the_polynomial_degree():
    squares = [k * k for k in range(1, 8)]
    built = difference_ladder(squares)
    assert built["depth"] == 2 and built["flat"]
    assert built["heads"][:3] == [Fraction(1), Fraction(3), Fraction(2)]


def test_ratio_ladder_finds_a_geometric_run():
    built = ratio_ladder([3, 6, 12, 24, 48])
    assert built["flat"] and built["depth"] == 1 and built["ratio"] == 2


def test_ratio_ladder_declines_when_a_term_is_zero():
    assert ratio_ladder([1, 0, 3, 4]) is None


def test_newton_sum_is_exact_and_independent_of_n():
    """Sum k^2 for k in 1..N straight from a ladder built on 8 samples."""
    heads = difference_ladder([k * k for k in range(1, 9)])["heads"]
    for N in (5, 50, 10 ** 6):
        assert newton_sum(heads, N) == N * (N + 1) * (2 * N + 1) // 6


def test_newton_term_reconstructs_the_run():
    values = [1, 3, 7, 14, 25]
    heads = difference_ladder(values)["heads"]
    assert [newton_term(heads, i) for i in range(len(values))] == \
        [Fraction(v) for v in values]


# --------------------------------------------------------------- classify

@pytest.mark.parametrize("values, family, kind", [
    ([2, 4, 6, 8], "arithmetic", "plain"),
    ([2, 4, 8, 16], "geometric", "plain"),
    ([60, 30, 20, 15], "harmonic", "plain"),
    ([1, 3, 7, 14, 25], "arithmetic", "hybrid"),
])
def test_classify_names_each_family(values, family, kind):
    detected = classify(values)
    assert detected["family"] == family and detected["kind"] == kind


def test_classify_admits_when_there_is_no_structure():
    detected = classify([5, -2, 88, 3, -41])
    assert detected["family"] == "unstructured"
    assert "not a pattern" in detected["reason"]


def test_classify_needs_enough_evidence():
    with pytest.raises(ValueError):
        classify([1, 2])


def test_aggregate_closed_form_equals_the_direct_result():
    for values in ([2, 4, 6, 8, 10], [3, 6, 12, 24], [60, 30, 20, 15, 12],
                   [1, 3, 7, 14, 25], [5, -2, 88, 3, -41]):
        summary = aggregate(values)
        assert summary["match"], values
        assert summary["closed"] == summary["direct"]


def test_aggregate_picks_the_right_operation_per_family():
    assert aggregate([3, 6, 12, 24])["label"] == "product of terms"
    assert aggregate([60, 30, 20, 15])["label"] == "sum of reciprocals"
    assert aggregate([2, 4, 6, 8])["label"] == "sum of terms"


# --------------------------------------------------------------- reverse fit

def test_reverse_engineer_recovers_an_exact_linear_law():
    ranked = reverse_engineer([2, 4, 6, 8, 10, 12])
    assert ranked["best"]["name"] == "arithmetic (linear)"
    assert ranked["quality"] == "exact" and ranked["best"]["r2"] > 0.9999


def test_reverse_engineer_recovers_a_geometric_law():
    ranked = reverse_engineer([3, 6, 12, 24, 48, 96])
    assert ranked["best"]["kind"] == "geometric"
    assert ranked["best"]["r2"] > 0.9999


def test_reverse_engineer_prefers_simple_models_on_noise():
    """Adjusted R-squared should stop a degree-3 fit from winning on junk."""
    ranked = reverse_engineer([5, -20, 88, 3, -41, 60, 7])
    assert ranked["quality"] in ("poor", "weak")
    assert ranked["relative_residual"] > 0.1


def test_reverse_engineer_needs_four_points():
    with pytest.raises(ValueError):
        reverse_engineer([1, 2, 3])


# --------------------------------------------------------------- assemble

def test_segment_splits_evenly_and_loses_nothing():
    values = list(range(10))
    for blocks in (1, 3, 4, 10):
        parts = segment(values, blocks)
        assert len(parts) == blocks
        assert [v for part in parts for v in part] == values


def test_assemble_recombines_blocks_into_the_exact_total():
    values = [3, 5, 7, 9, 2, 4, 8, 16, 45, 50, 55, 60]
    built = assemble(values, blocks=3)
    assert built["match"] and built["total"] == sum(values)
    assert [row["law"] for row in built["blocks"]] == \
        ["arithmetic", "geometric", "arithmetic"]
    assert built["operations"] < built["direct_operations"]


def test_assemble_handles_a_harmonic_block_without_lying():
    """The ladder describes the reciprocals, so the term sum has no closed form."""
    built = assemble([60, 30, 20, 15, 5, 10, 15, 20], blocks=2)
    assert built["match"]
    harmonic = [row for row in built["blocks"] if row["law"] == "harmonic"]
    assert harmonic and not built["all_constant_time"]
    assert "no closed form" in harmonic[0]["note"]


def test_assemble_can_sort_first():
    values = [50, 3, 9, 5, 55, 7, 45, 60]
    built = assemble(values, blocks=2, sort_first=True)
    assert built["match"] and built["sorted"] is True
    assert built["total"] == sum(values)


# --------------------------------------------------------------- engine wrappers

def test_name_run_is_json_safe():
    out = name_run([1, 3, 7, 14, 25])
    assert out["closed"]["text"] == "50" and out["match"] is True
    assert isinstance(out["values"], list) and out["structured"] is True


def test_lab_wrappers_refuse_bad_input():
    with pytest.raises(ComputeError):
        name_run([1, 2])
    with pytest.raises(ComputeError):
        reverse([1, 2, 3])
    with pytest.raises(ComputeError):
        assemble_runs([1, 2, 3, 4], blocks=99)
    with pytest.raises(ComputeError):
        name_run(list(range(1000)))          # over the per-request value cap
