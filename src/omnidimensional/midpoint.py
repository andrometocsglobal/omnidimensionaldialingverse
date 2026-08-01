"""The flagship midpoint operator — one call spanning the classical means."""

import math
from fractions import Fraction


def omnidimensional_midpoint(a, b, family="harmonic"):
    """Midpoint of a and b under the chosen family.

    harmonic  : 2ab/(a+b)        (exact Fraction)
    arithmetic: (a+b)/2          (exact Fraction)
    geometric : sqrt(a*b)
    quadratic : sqrt((a^2+b^2)/2)
    """
    if family == "harmonic":
        A, B = Fraction(a), Fraction(b)
        if A + B == 0:
            raise ZeroDivisionError("harmonic midpoint undefined for a + b == 0")
        return 2 * A * B / (A + B)
    if family == "arithmetic":
        return (Fraction(a) + Fraction(b)) / 2
    if family == "geometric":
        return math.sqrt(float(a) * float(b))
    if family == "quadratic":
        return math.sqrt((float(a) ** 2 + float(b) ** 2) / 2.0)
    raise ValueError("unknown family: %s" % family)
