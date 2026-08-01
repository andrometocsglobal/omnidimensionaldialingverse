"""Fit an arbitrary range onto a perfect hypercube, then clip the padding.

The closed forms want a tidy shape. An arbitrary count N rarely is one, so:

    1. fit    -- find the smallest n with n^d >= N
    2. pad    -- borrow q = n^d - N synthetic terms that continue the spacing
    3. solve  -- evaluate the full n^d shape in one O(1) call
    4. clip   -- evaluate the q padding terms (also O(1)) and remove them

Both evaluations are O(1), so the whole pipeline is O(1) and the padding never
costs anything. The result is exact: the synthetic terms are removed by exact
arithmetic, not estimated away.

For sums the clip is a subtraction; for products it is a division.
"""

from fractions import Fraction

from .moments import (ap_power_sum, gp_power_product, hp_power_sum_approx,
                      run_midpoint)
from .render import exact

MAX_DIMENSION = 8


def integer_root_ceil(N, d):
    """Smallest integer n with n**d >= N, exactly (no floating point)."""
    N, d = int(N), int(d)
    if d < 1:
        raise ValueError("dimension must be >= 1")
    if N <= 1:
        return max(0, N)
    n = 1 << ((N.bit_length() + d - 1) // d)   # comfortably above the answer
    while n > 1 and (n - 1) ** d >= N:         # walk down to the smallest
        n -= 1
    while n ** d < N:                          # ...and up, if we undershot
        n += 1
    return n


def perfect_shape(N, d):
    """The smallest d-dimensional cube that holds N terms.

    Returns ``{'n', 'dimension', 'total', 'pad'}`` where total = n**d and
    pad = total - N.
    """
    N, d = int(N), int(d)
    if N < 0:
        raise ValueError("N must be >= 0")
    if not 1 <= d <= MAX_DIMENSION:
        raise ValueError("dimension must be between 1 and %d" % MAX_DIMENSION)
    n = integer_root_ceil(N, d)
    total = n ** d
    return {"n": n, "dimension": d, "total": total, "pad": total - N}


def best_dimension(N, lo=2, hi=6):
    """The dimension in [lo, hi] that needs the least padding.

    d = 1 is excluded by default because a line always fits exactly, which
    makes it a trivial winner and hides the interesting shapes.
    """
    best = None
    for d in range(int(lo), int(hi) + 1):
        shape = perfect_shape(N, d)
        if best is None or shape["pad"] < best["pad"]:
            best = shape
    return best


def solve_by_fit(family, N, d=3, F=1, h=1, r=2, p=1, order=3):
    """Run the fit -> pad -> solve -> clip pipeline over N terms.

    ``family`` is 'arithmetic', 'geometric' or 'harmonic'. Returns the shape,
    the full-shape value, the padding value, and the clipped answer.
    """
    N = int(N)
    if N < 0:
        raise ValueError("N must be >= 0")
    shape = perfect_shape(N, d)
    total, q = shape["total"], shape["pad"]

    if family == "arithmetic":
        full = ap_power_sum(F, h, total, p)
        # the padding continues the same run, starting at index N
        pad = ap_power_sum(exact(F) + N * exact(h), h, q, p)
        answer, operation = full - pad, "subtract"
    elif family == "geometric":
        full = gp_power_product(F, r, total, p)
        # prod_{i=N}^{N+q-1} (F r^i)^p = F^(pq) * r^(p*(qN + q(q-1)/2))
        pad = (exact(F) ** (p * q)
               * exact(r) ** (p * (q * N + q * (q - 1) // 2))) if q else Fraction(1)
        answer, operation = (full / pad if q else full), "divide"
    elif family == "harmonic":
        full = hp_power_sum_approx(F, h, total, p, order)
        pad = (hp_power_sum_approx(exact(F) + N * exact(h), h, q, p, order)
               if q else Fraction(0))
        answer, operation = full - pad, "subtract"
    else:
        raise ValueError("unknown family: %s" % family)

    return {
        "family": family,
        "N": N,
        "shape": shape,
        "operation": operation,
        "full": full,
        "pad": pad,
        "answer": answer,
        "midpoint": run_midpoint(F, h, total) if family != "geometric" else None,
        "exact": family != "harmonic",
    }


def parse_shape(text):
    """Parse a dimensional arrangement like '2 x 3 x 2' or '2 × 2 × 2'.

    Accepts x, X, *, the multiplication sign, and commas as separators.
    Returns ``{'dims', 'count', 'label'}``.
    """
    cleaned = (str(text).strip().lower()
               .replace("×", "x").replace("*", "x").replace(",", "x"))
    parts = [part.strip() for part in cleaned.split("x") if part.strip()]
    if not parts:
        raise ValueError("enter an arrangement such as 2 x 3 x 2")
    dims = []
    for part in parts:
        if not part.isdigit():
            raise ValueError("dimensions must be positive whole numbers "
                             "separated by x")
        value = int(part)
        if not 1 <= value <= 64:
            raise ValueError("each dimension must be between 1 and 64")
        dims.append(value)
    if len(dims) > MAX_DIMENSION:
        raise ValueError("use at most %d dimensions" % MAX_DIMENSION)
    count = 1
    for value in dims:
        count *= value
    return {"dims": dims, "count": count, "label": " x ".join(map(str, dims))}


def coordinate(index, dims):
    """Map a flat index onto its 1-based cell coordinate in ``dims``."""
    coords = [0] * len(dims)
    for axis in range(len(dims) - 1, -1, -1):
        coords[axis] = index % dims[axis] + 1
        index //= dims[axis]
    return coords
