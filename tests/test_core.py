"""Exact self-tests. Run: pytest -q"""

from fractions import Fraction

import pytest

from omnidimensional import (Arithmetic, Geometric, Harmonic, OmniFit,
                             power_sum_closed, power_sum_brute,
                             power_mean, omnidimensional_midpoint, verify,
                             harmonic_sum_approx, digamma, to_exact_str,
                             to_decimal, digit_count, validate, compute,
                             ComputeError)


def test_arithmetic_closed_matches_brute():
    fam = Arithmetic(3, 5)
    for n in (0, 1, 10, 100, 1000):
        assert fam.sum(n) == sum(fam.term(k) for k in range(n))


def test_geometric_closed_matches_brute():
    fam = Geometric(1, 2)
    for n in (1, 10, 64):
        assert fam.sum(n) == sum(fam.term(k) for k in range(n))
    assert Geometric(1, 2).sum(64) == 2 ** 64 - 1


def test_power_sums_faulhaber():
    for n in (10, 100, 1000):
        for p in (0, 1, 2, 3, 4, 5):
            assert power_sum_closed(n, p) == power_sum_brute(n, p)
    assert power_sum_closed(100, 2) == 338350


def test_harmonic_exact():
    fam = Harmonic(1, 1)
    assert fam.sum(4) == Fraction(1) + Fraction(1, 2) + Fraction(1, 3) + Fraction(1, 4)
    assert fam.sum(0) == Fraction(0)


def test_power_mean_identities():
    assert abs(power_mean([2, 8], 1) - 5) < 1e-9
    assert abs(power_mean([2, 8], 0) - 4) < 1e-9
    assert abs(power_mean([2, 8], -1) - 3.2) < 1e-9
    seq = [power_mean([3, 5, 11], p) for p in (-5, -1, 0, 1, 5)]
    assert all(seq[i] <= seq[i + 1] + 1e-9 for i in range(len(seq) - 1))


def test_midpoint():
    assert omnidimensional_midpoint(2, 3, "harmonic") == Fraction(12, 5)
    assert omnidimensional_midpoint(2, 8, "arithmetic") == 5


def test_omnifit_roundtrip():
    of = OmniFit([0.0, 1.0, 4.0, 9.0])
    for x in (0.0, 2.0, 4.0, 7.5, 9.0):
        assert abs(of.unwarp(of.warp(x)) - x) < 1e-9


def test_verifier():
    for fam, kw in [("arithmetic", {"a": 2, "d": 3}), ("geometric", {"a": 1, "r": 3}),
                    ("power", {"p": 4})]:
        assert verify(fam, 200, **kw)["exact_match"]


# --------------------------------------------------------------- digamma / HP

def test_digamma_matches_known_values():
    # psi(1) = -gamma, and psi(n+1) = -gamma + H_n
    gamma = 0.57721566490153286
    assert abs(digamma(1.0) + gamma) < 1e-12
    for n in (1, 2, 5, 20):
        h_n = float(sum(Fraction(1, k) for k in range(1, n + 1)))
        assert abs(digamma(n + 1.0) - (-gamma + h_n)) < 1e-11


def test_harmonic_approx_tracks_exact_sum():
    for a, d, n in [(1, 1, 1), (1, 1, 10), (1, 1, 10_000),
                    (2, 3, 500), (0.5, 0.25, 1000), (7, 1, 3000)]:
        exact = float(Harmonic(a, d).sum(n))
        assert abs(harmonic_sum_approx(n, a, d) - exact) <= 1e-9 * abs(exact)


def test_harmonic_verify_compares_approx_against_exact():
    report = verify("harmonic", 5_000_000, a=1, d=1)
    assert report["exact_match"] and report["spot_checked"]
    assert report["n_verified"] < report["n"]


# --------------------------------------------------------------- rendering

def test_render_survives_a_million_digit_result():
    """The bug this guards: str() and float() both blow up on huge exact values."""
    value = Geometric(1, 2).sum(1_000_000)
    assert value == 2 ** 1_000_000 - 1          # still exact in memory
    text, truncated, digits = to_exact_str(value)
    assert truncated and digits == 301_030
    assert text.startswith("9.900656") and text.endswith("e+301029")
    assert to_decimal(value) is None            # genuinely overflows a float


def test_render_leaves_small_values_exact():
    assert to_exact_str(Fraction(12, 5)) == ("12/5", False, 2)
    assert to_exact_str(Fraction(338350)) == ("338350", False, 6)
    assert to_exact_str(Fraction(-7, 2))[0] == "-7/2"
    assert digit_count(Fraction(10 ** 50)) == 51


def test_render_handles_tiny_rationals():
    text, truncated, _ = to_exact_str(Geometric(1, Fraction(1, 2)).sum(100_000))
    assert truncated and "e" in text


# --------------------------------------------------------------- limits

def test_validate_rejects_runaway_requests():
    assert validate("geometric", 10 ** 9, a=1, r=2) is not None
    assert validate("bogus", 10) is not None
    assert validate("arithmetic", -1) is not None
    assert validate("power", 10, p=10 ** 6) is not None
    assert validate("harmonic", 10, a=-2, d=1) is not None   # pole at k = 2
    assert validate("geometric", 64, a=1, r=2) is None
    assert validate("harmonic", 10, a=1, d=1) is None


# --------------------------------------------------------------- engine

def test_compute_matches_the_families_directly():
    out = compute("geometric", 64, a=1, r=2)
    assert out["result"] == str(2 ** 64 - 1)
    assert out["exact_match"] and out["exact"] and not out["truncated"]

    out = compute("power", 100, p=2)
    assert out["result"] == "338350"

    out = compute("arithmetic", 1000, a=3, d=5)
    assert out["result"] == str(Arithmetic(3, 5).sum(1000))


def test_compute_falls_back_to_approximation_for_huge_harmonic():
    out = compute("harmonic", 5_000_000, a=1, d=1)
    assert out["approximate"] and not out["exact"]
    # H_n = ln n + gamma + 1/(2n) - ... ; H_5e6 = 16.0021642353
    assert abs(float(out["result"]) - 16.0021642353) < 1e-9


def test_compute_refuses_what_it_cannot_build():
    with pytest.raises(ComputeError):
        compute("geometric", 10 ** 9, a=1, r=2)
    with pytest.raises(ComputeError):
        compute("bogus", 10)


def test_compute_is_constant_time_in_n():
    """n = 10**12 must return promptly — that is the whole claim."""
    out = compute("power", 10 ** 12, p=3)
    assert out["exact_match"] and out["spot_checked"]
    assert out["result"] == str(power_sum_closed(10 ** 12, 3))
