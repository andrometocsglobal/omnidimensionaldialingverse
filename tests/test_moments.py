"""Midpoint/central-moment power sums and the hypercube fit-pad-clip pipeline."""

from fractions import Fraction

import pytest

from omnidimensional import (ap_power_sum, ap_power_sum_brute, best_dimension,
                             central_moment, coordinate, gp_power_product,
                             gp_power_product_brute, hp_power_sum_approx,
                             hp_power_sum_brute, integer_root_ceil, omnifit,
                             parse_shape, perfect_shape, power_sum_closed,
                             run_midpoint, solve_by_fit, ComputeError)


# --------------------------------------------------------------- moments

def test_central_moments_match_the_classical_closed_forms():
    for X in (2, 5, 7, 40):
        assert central_moment(0, X) == 1
        assert central_moment(1, X) == Fraction(X ** 2 - 1, 12)
        assert central_moment(2, X) == Fraction(3 * X ** 4 - 10 * X ** 2 + 7, 240)
        assert central_moment(3, X) == Fraction(
            3 * X ** 6 - 21 * X ** 4 + 49 * X ** 2 - 31, 1344)


def test_central_moments_stay_exact_past_a_lookup_table():
    """A hard-coded moment table stops at m=5; this is derived, so it does not."""
    X = 7
    for m in (6, 8):
        brute = sum((Fraction(i) - Fraction(X - 1, 2)) ** (2 * m)
                    for i in range(X)) / X
        assert central_moment(m, X) == brute


def test_odd_central_moments_vanish_by_symmetry():
    # only even moments appear in the formula; check the odd ones really are 0
    X = 9
    centre = Fraction(X - 1, 2)
    for odd in (1, 3, 5):
        assert sum((Fraction(i) - centre) ** odd for i in range(X)) == 0


# --------------------------------------------------------------- AP / GP / HP

def test_ap_power_sum_matches_brute_force_everywhere():
    for first in (7, -3, 1, 0):
        for step in (1, 2, Fraction(1, 2), -1):
            for count in (0, 1, 2, 5, 17):
                for power in range(0, 9):
                    assert (ap_power_sum(first, step, count, power)
                            == ap_power_sum_brute(first, step, count, power))


def test_ap_power_sum_known_value():
    assert ap_power_sum(7, 1, 4, 3) == 2584          # 7^3+8^3+9^3+10^3
    assert run_midpoint(7, 1, 4) == Fraction(17, 2)


def test_midpoint_form_agrees_with_faulhaber_at_enormous_n():
    """Two independent O(1) derivations must land on the same exact integer.

    ap_power_sum(1, 1, X, p) is sum_{k=1}^{X} k^p, which is exactly what
    power_sum_closed computes -- by a different route (Bernoulli, not moments).
    """
    for power in (1, 2, 3, 5):
        for count in (10, 1000, 10 ** 12):
            assert ap_power_sum(1, 1, count, power) == power_sum_closed(count, power)


def test_gp_power_product_matches_brute_force():
    for a in (2, 3, Fraction(1, 2)):
        for r in (2, 3, Fraction(1, 2)):
            for count in (0, 1, 6):
                for w in (1, 2, 3):
                    assert (gp_power_product(a, r, count, w)
                            == gp_power_product_brute(a, r, count, w))


def test_hp_series_is_sharp_away_from_zero_and_honest_near_it():
    far = abs(float(hp_power_sum_approx(1000, 1, 64, 1)
                    - hp_power_sum_brute(1000, 1, 64, 1)))
    assert far / float(hp_power_sum_brute(1000, 1, 64, 1)) < 1e-12

    # Its worst case: a run starting at 1, where the digamma path is far better.
    near = abs(float(hp_power_sum_approx(1, 1, 20, 1)
                     - hp_power_sum_brute(1, 1, 20, 1)))
    assert near / float(hp_power_sum_brute(1, 1, 20, 1)) > 1e-3


def test_hp_series_rejects_a_run_through_a_pole():
    with pytest.raises(ZeroDivisionError):
        hp_power_sum_approx(-2, 1, 5, 1)      # midpoint lands on zero


# --------------------------------------------------------------- hypercube

def test_integer_root_ceil_is_exact_at_the_boundaries():
    assert integer_root_ceil(1000, 3) == 10
    assert integer_root_ceil(1001, 3) == 11
    assert integer_root_ceil(1024, 10) == 2
    assert integer_root_ceil(1025, 10) == 3
    # a float cube root would round this one the wrong way
    big = 10 ** 18
    assert integer_root_ceil(big, 3) == 10 ** 6
    assert integer_root_ceil(big + 1, 3) == 10 ** 6 + 1


def test_perfect_shape_is_the_smallest_cube_that_fits():
    for N in (0, 1, 7, 50, 64, 65, 1000):
        for d in (1, 2, 3, 4):
            shape = perfect_shape(N, d)
            assert shape["total"] == shape["n"] ** d
            assert shape["total"] >= N
            assert shape["pad"] == shape["total"] - N
            if shape["n"] > 0:
                assert (shape["n"] - 1) ** d < N or shape["n"] <= 1


def test_best_dimension_minimises_padding():
    best = best_dimension(50)
    for d in range(2, 7):
        assert best["pad"] <= perfect_shape(50, d)["pad"]


def test_fit_pad_clip_reproduces_the_direct_sum_exactly():
    """The padding is removed by exact arithmetic, not estimated away."""
    for N in (0, 1, 7, 50, 101):
        for d in (1, 2, 3, 4):
            fitted = solve_by_fit("arithmetic", N, d, F=7, h=2, p=3)
            assert fitted["answer"] == ap_power_sum_brute(7, 2, N, 3)
            product = solve_by_fit("geometric", N, d, F=2, r=3, p=2)
            assert product["answer"] == gp_power_product_brute(2, 3, N, 2)


def test_parse_shape_accepts_the_usual_separators():
    for text in ("2 x 3 x 2", "2 × 3 × 2", "2*3*2", "2,3,2"):
        assert parse_shape(text)["dims"] == [2, 3, 2]
        assert parse_shape(text)["count"] == 12
    for bad in ("", "2 x zero", "0 x 3", "99 x 2"):
        with pytest.raises(ValueError):
            parse_shape(bad)


def test_coordinate_walks_the_arrangement_in_order():
    dims = [2, 3, 2]
    assert coordinate(0, dims) == [1, 1, 1]
    assert coordinate(1, dims) == [1, 1, 2]
    assert coordinate(2, dims) == [1, 2, 1]
    assert coordinate(11, dims) == [2, 3, 2]


# --------------------------------------------------------------- engine wrapper

def test_omnifit_reports_the_pipeline_and_verifies_it():
    out = omnifit("arithmetic", 50, 3, F=7, h=2, p=3)
    assert out["shape"] == {"n": 4, "dimension": 3, "total": 64, "pad": 14}
    assert out["operation"] == "subtract"
    assert out["exact_match"] is True
    assert out["answer"]["text"] == str(ap_power_sum_brute(7, 2, 50, 3))


def test_omnifit_is_constant_time_for_an_enormous_count():
    out = omnifit("arithmetic", 10 ** 9, 3, F=1, h=1, p=2)
    assert out["checked_directly"] is False
    assert out["answer"]["digits"] == 27


@pytest.mark.parametrize("dimension", [2, 3, 4, 5])
def test_the_answer_is_invariant_across_dimensions(dimension):
    """2D, 3D, 4D and 5D pad by different amounts and still agree exactly.

    That is the point of the clip: the shape is scaffolding, not part of the sum.
    """
    fitted = omnifit("arithmetic", 50, dimension, F=7, h=2, p=3)
    assert fitted["shape"]["dimension"] == dimension
    assert fitted["shape"]["total"] == fitted["shape"]["n"] ** dimension
    assert fitted["exact_match"] is True
    assert fitted["answer"]["text"] == str(ap_power_sum_brute(7, 2, 50, 3))


def test_dimensions_really_do_differ_in_padding():
    pads = {d: omnifit("arithmetic", 50, d, F=7, h=2, p=3)["shape"]["pad"]
            for d in (2, 3, 4, 5)}
    assert pads[4] != pads[3] and pads[5] > pads[2]   # not all the same scaffold


def test_omnifit_refuses_a_shape_it_cannot_build():
    with pytest.raises(ComputeError):
        omnifit("geometric", 10 ** 7, 6, F=1, r=2, p=1)
    with pytest.raises(ComputeError):
        omnifit("bogus", 10)
    with pytest.raises(ComputeError):
        omnifit("harmonic", 10, 2, F=-2, h=1)      # padded shape crosses the pole
