"""Exact power sums (Faulhaber) and Bernoulli numbers — constant-time in n."""

import math
from fractions import Fraction
from functools import lru_cache


@lru_cache(maxsize=None)
def _bernoulli_cached(n):
    """B_0..B_n as an immutable tuple. Central moments hammer this."""
    B = [Fraction(0)] * (n + 1)
    B[0] = Fraction(1)
    for m in range(1, n + 1):
        s = Fraction(0)
        for k in range(m):
            s += math.comb(m + 1, k) * B[k]
        B[m] = -s / (m + 1)
    return tuple(B)


def bernoulli(n):
    """Bernoulli numbers B_0..B_n as exact Fractions (B_1 = -1/2 convention)."""
    return list(_bernoulli_cached(int(n)))


def power_sum_closed(n, p):
    """Exact 1**p + 2**p + ... + n**p for integer p >= 0, via Faulhaber.

    O(p**2) in the power and O(1) in the number of terms n.
    """
    n, p = int(n), int(p)
    if n <= 0:
        return Fraction(0)
    if p < 0:
        raise ValueError("power_sum_closed requires integer p >= 0")
    if p == 0:
        return Fraction(n)
    B = _bernoulli_cached(p)
    total = Fraction(0)
    for j in range(p + 1):
        total += math.comb(p + 1, j) * B[j] * Fraction(n) ** (p + 1 - j)
    return total / (p + 1) + Fraction(n) ** p


def power_sum_brute(n, p):
    """Reference O(n) term-by-term sum, for verification."""
    return sum((Fraction(k) ** int(p) for k in range(1, int(n) + 1)), Fraction(0))
