"""O(1) asymptotic approximations for the sum that has no closed form.

The harmonic family is the honest gap in the set: HP has no elementary closed
form, so its exact sum costs O(n). It does have an O(1) *approximation* in
terms of the digamma function, which is what this module supplies:

    sum_{k=0}^{n-1} 1/(a + k*d)  =  (psi(a/d + n) - psi(a/d)) / d

The exact rational sum remains available and is what the verifier checks this
approximation against.
"""

import math

EULER_GAMMA = 0.57721566490153286060


def digamma(x):
    """psi(x) for x > 0, via recurrence shift plus the asymptotic series.

    Accurate to roughly 1e-13 relative across the useful range.
    """
    x = float(x)
    if x <= 0:
        raise ValueError("digamma requires x > 0")
    shift = 0.0
    while x < 10.0:          # push the argument into the series' good range
        shift -= 1.0 / x
        x += 1.0
    f = 1.0 / (x * x)
    series = (
        (-1.0 / 12.0) * f
        + (1.0 / 120.0) * f ** 2
        + (-1.0 / 252.0) * f ** 3
        + (1.0 / 240.0) * f ** 4
        + (-1.0 / 132.0) * f ** 5
    )
    return shift + math.log(x) - 0.5 / x + series


def harmonic_sum_approx(n, a=1.0, d=1.0):
    """O(1) approximation of sum_{k=0}^{n-1} 1/(a + k*d).

    Falls back to direct summation when the digamma identity does not apply
    (d <= 0, or a non-positive start), because the terms may then straddle a
    pole or change sign.
    """
    n = int(n)
    if n <= 0:
        return 0.0
    a, d = float(a), float(d)
    if d == 0.0:
        if a == 0.0:
            raise ZeroDivisionError("harmonic undefined for a = 0, d = 0")
        return n / a
    if d < 0.0 or a <= 0.0:
        return sum(1.0 / (a + k * d) for k in range(n))
    z = a / d
    return (digamma(z + n) - digamma(z)) / d
