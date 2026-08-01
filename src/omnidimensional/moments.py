"""Midpoint-centred power sums via exact central moments.

An alternative to Faulhaber that centres on the run's midpoint instead of its
origin:

    sum_{i=0}^{X-1} (F + i*h)^p
        = X * sum_{m=0}^{floor(p/2)} C(p, 2m) * M^(p-2m) * h^(2m) * mu_m(X)

where ``M = F + (X-1)h/2`` is the midpoint and ``mu_m(X)`` is the (2m)-th
central moment of the uniform run. Odd central moments vanish by symmetry,
which is why only even powers survive: the sum collapses to floor(p/2)+1 terms
no matter how many terms the run actually has. That is the O(1).

The same moments drive an O(1) approximation for reciprocal (harmonic) power
sums, which have no elementary closed form.

Unlike a hard-coded moment table, ``central_moment`` is derived from the
existing Faulhaber machinery, so it is exact for every m rather than silently
degrading past a fixed cutoff.
"""

import math
from fractions import Fraction
from functools import lru_cache

from .faulhaber import power_sum_closed
from .render import exact


@lru_cache(maxsize=512)
def central_moment(m, X):
    """The (2m)-th central moment of {0, 1, ..., X-1}, exactly.

    mu_m(X) = (1/X) * sum_{i=0}^{X-1} (i - (X-1)/2)^(2m)

    Computed in closed form from Faulhaber power sums, so it costs O(m^2) and
    nothing in X. mu_0 = 1, mu_1 = (X^2-1)/12, and so on.
    """
    m, X = int(m), int(X)
    if X <= 0:
        return Fraction(0)
    if m == 0:
        return Fraction(1)
    c = Fraction(X - 1, 2)
    total = Fraction(0)
    for j in range(2 * m + 1):
        # sum_{i=0}^{X-1} i^j  --  the i=0 term is 0 for j >= 1
        power_sum = Fraction(X) if j == 0 else power_sum_closed(X - 1, j)
        total += math.comb(2 * m, j) * (-c) ** (2 * m - j) * power_sum
    return total / X


def run_midpoint(F, h, X):
    """The midpoint of an arithmetic run: M = F + (X-1)h/2."""
    return exact(F) + Fraction(int(X) - 1, 2) * exact(h)


def ap_power_sum(F, h, X, p):
    """Exact sum_{i=0}^{X-1} (F + i*h)^p, midpoint form, O(1) in X.

    Agrees with the term-by-term sum for every integer p >= 0; the verifier
    checks this against brute force.
    """
    X, p = int(X), int(p)
    if X <= 0:
        return Fraction(0)
    if p < 0:
        raise ValueError("ap_power_sum requires integer p >= 0")
    M, hh = run_midpoint(F, h, X), exact(h)
    total = Fraction(0)
    for m in range(p // 2 + 1):
        total += (math.comb(p, 2 * m) * M ** (p - 2 * m)
                  * hh ** (2 * m) * central_moment(m, X))
    return Fraction(X) * total


def ap_power_sum_brute(F, h, X, p):
    """O(X) reference for :func:`ap_power_sum`."""
    F, h = exact(F), exact(h)
    return sum(((F + i * h) ** int(p) for i in range(int(X))), Fraction(0))


def _rising(p, k):
    """Rising factorial p(p+1)...(p+k-1)."""
    out = 1
    for t in range(k):
        out *= p + t
    return out


def hp_power_sum_approx(F, h, X, p=1, order=3):
    """O(1) approximation of sum_{i=0}^{X-1} 1/(F + i*h)^p.

    The Taylor/Euler-Maclaurin expansion of x^-p about the midpoint M:

        sum ~ X * sum_{m=0}^{order} (p)_{2m}/(2m)! * h^(2m) * mu_m(X) / M^(p+2m)

    Sharp when the run sits far from zero relative to its width, and it
    degrades gracefully rather than silently: pair it with
    :func:`omnidimensional.verify` to see the actual error.

    Returns an exact Fraction (the *series* is exact; it is the truncation that
    approximates).
    """
    X, p = int(X), int(p)
    if X <= 0:
        return Fraction(0)
    if p < 1:
        raise ValueError("hp_power_sum_approx requires integer p >= 1")
    M, hh = run_midpoint(F, h, X), exact(h)
    if M == 0:
        raise ZeroDivisionError("midpoint is zero; the run straddles a pole")
    total = Fraction(0)
    for m in range(int(order) + 1):
        coefficient = Fraction(_rising(p, 2 * m), math.factorial(2 * m))
        total += (coefficient * hh ** (2 * m) * central_moment(m, X)
                  / M ** (p + 2 * m))
    return Fraction(X) * total


def hp_power_sum_brute(F, h, X, p=1):
    """O(X) exact reference for :func:`hp_power_sum_approx`."""
    F, h = exact(F), exact(h)
    total = Fraction(0)
    for i in range(int(X)):
        denominator = F + i * h
        if denominator == 0:
            raise ZeroDivisionError("harmonic term undefined at i=%d" % i)
        total += Fraction(1) / denominator ** int(p)
    return total


def gp_power_product(a, r, X, w=1):
    """Exact prod_{i=0}^{X-1} (a * r^i)^w = a^(wX) * r^(w*X(X-1)/2), O(1) in X."""
    X, w = int(X), int(w)
    if X <= 0:
        return Fraction(1)
    return exact(a) ** (w * X) * exact(r) ** (w * X * (X - 1) // 2)


def gp_power_product_brute(a, r, X, w=1):
    """O(X) reference for :func:`gp_power_product`."""
    a, r = exact(a), exact(r)
    out = Fraction(1)
    for i in range(int(X)):
        out *= (a * r ** i) ** int(w)
    return out
