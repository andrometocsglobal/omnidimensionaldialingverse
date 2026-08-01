"""The four omnidimensional progression families.

Each family exposes the same tiny interface: a ``term(k)`` for the k-th term
(0-indexed) and a ``sum(n)`` for the first n terms. Sums are exact (Fraction)
and closed-form where an elementary closed form exists; the harmonic family
honestly reports that it has none and returns an exact rational instead.

Families
--------
Arithmetic (AP)  term a + k*d           sum n/2 (2a + (n-1)d)
Geometric  (GP)  term a * r**k          sum a (r**n - 1)/(r - 1), or a*n if r==1
Harmonic   (HP)  term 1/(a + k*d)       exact rational (no elementary closed form)
OmniFit          warps irregular sample positions onto an even grid so a closed
                 form applies to otherwise unevenly-spaced data.
"""

from fractions import Fraction

from .approx import harmonic_sum_approx
from .faulhaber import power_sum_closed


def _F(x):
    return x if isinstance(x, Fraction) else Fraction(str(x)) if isinstance(x, float) else Fraction(x)


class Arithmetic:
    name = "arithmetic"
    closed_form = "S_n = n/2 * (2a + (n-1)d)"

    def __init__(self, a=0, d=1):
        self.a, self.d = _F(a), _F(d)

    def term(self, k):
        return self.a + k * self.d

    def sum(self, n):
        n = int(n)
        if n <= 0:
            return Fraction(0)
        return Fraction(n, 1) * (2 * self.a + (n - 1) * self.d) / 2

    def power_sum(self, n, p):
        """Closed-form sum of the p-th powers when a=0,d=1 (pure k**p)."""
        if self.a == 0 and self.d == 1:
            return power_sum_closed(n, p)
        return sum(self.term(k) ** int(p) for k in range(int(n)))


class Geometric:
    name = "geometric"
    closed_form = "S_n = a (r^n - 1)/(r - 1),  or a*n if r == 1"

    def __init__(self, a=1, r=2):
        self.a, self.r = _F(a), _F(r)

    def term(self, k):
        return self.a * self.r ** k

    def sum(self, n):
        n = int(n)
        if n <= 0:
            return Fraction(0)
        if self.r == 1:
            return self.a * n
        return self.a * (self.r ** n - 1) / (self.r - 1)


class Harmonic:
    name = "harmonic"
    closed_form = "no elementary closed form (exact rational sum)"

    def __init__(self, a=1, d=1):
        self.a, self.d = _F(a), _F(d)

    def term(self, k):
        denom = self.a + k * self.d
        if denom == 0:
            raise ZeroDivisionError("harmonic term undefined (a + k*d == 0)")
        return Fraction(1) / denom

    def sum(self, n):
        # Exact, but summed term by term — HP has no elementary closed form.
        return sum((self.term(k) for k in range(int(n))), Fraction(0))

    def sum_approx(self, n):
        """O(1) floating-point approximation via digamma.

        The exact :meth:`sum` is O(n); this is the constant-time stand-in for
        large n. :func:`omnidimensional.verify` checks one against the other.
        """
        return harmonic_sum_approx(n, float(self.a), float(self.d))


class OmniFit:
    """Warp irregular sample positions onto an even grid.

    Given strictly increasing positions ``xs`` and values ``ys``, OmniFit maps
    the positions to a uniform index grid (0..n-1) so that a progression closed
    form can be applied to data that was not evenly spaced to begin with. The
    warp is the cumulative-rank map; ``unwarp`` inverts it.
    """

    name = "omnifit"
    closed_form = "reindex irregular x -> uniform grid, then apply a family"

    def __init__(self, xs):
        xs = [float(x) for x in xs]
        if any(b <= a for a, b in zip(xs, xs[1:])):
            raise ValueError("OmniFit positions must be strictly increasing")
        self.xs = xs
        self.n = len(xs)

    def warp(self, x):
        """Map a real position to fractional grid index via linear interpolation."""
        xs = self.xs
        if x <= xs[0]:
            return 0.0
        if x >= xs[-1]:
            return float(self.n - 1)
        for i in range(self.n - 1):
            if xs[i] <= x <= xs[i + 1]:
                frac = (x - xs[i]) / (xs[i + 1] - xs[i])
                return i + frac
        return float(self.n - 1)

    def unwarp(self, idx):
        """Inverse: fractional grid index back to a real position."""
        idx = max(0.0, min(float(self.n - 1), float(idx)))
        lo = int(idx)
        hi = min(lo + 1, self.n - 1)
        frac = idx - lo
        return self.xs[lo] + frac * (self.xs[hi] - self.xs[lo])


FAMILIES = {
    "arithmetic": Arithmetic,
    "geometric": Geometric,
    "harmonic": Harmonic,
    "omnifit": OmniFit,
}
