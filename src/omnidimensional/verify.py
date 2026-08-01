"""Exact verifier: prove a closed form equals brute force, in exact arithmetic."""

from fractions import Fraction

from .families import Arithmetic, Geometric, Harmonic
from .faulhaber import power_sum_closed, power_sum_brute
from .limits import MAX_BRUTE, MAX_VERIFY_HARMONIC, geometric_brute_cap
from .render import to_exact_str

# The harmonic check compares a float approximation to an exact rational, so it
# is the one family whose verdict is a tolerance rather than an equality.
HARMONIC_TOL = 1e-9


def verify(family, n, max_brute=MAX_BRUTE, **params):
    """Compare the fast method against a slow reference.

    The closed forms are O(1), so ``n`` may be far larger than anything worth
    summing term by term. When that happens the cross-check runs at a capped
    ``n_verified`` and the report says so via ``spot_checked``, rather than
    claiming to have verified the full request.

    family: 'arithmetic' | 'geometric' | 'power' | 'harmonic'
    """
    n = int(n)
    if n < 0:
        raise ValueError("n must be >= 0")
    n_check = min(n, int(max_brute))
    method = "closed form vs term-by-term sum, exact rational arithmetic"

    if family == "arithmetic":
        fam = Arithmetic(params.get("a", 1), params.get("d", 1))
        closed = fam.sum(n_check)
        brute = sum((fam.term(k) for k in range(n_check)), Fraction(0))
        ok = closed == brute
    elif family == "geometric":
        a, r = params.get("a", 1), params.get("r", 2)
        # GP terms grow geometrically, so the reference is capped by result
        # size rather than by term count.
        n_check = min(n_check, geometric_brute_cap(a, r))
        fam = Geometric(a, r)
        closed = fam.sum(n_check)
        brute = sum((fam.term(k) for k in range(n_check)), Fraction(0))
        ok = closed == brute
    elif family == "power":
        p = int(params.get("p", 2))
        closed = power_sum_closed(n_check, p)
        brute = power_sum_brute(n_check, p)
        ok = closed == brute
    elif family == "harmonic":
        # HP has no elementary closed form, so comparing "the closed form" to a
        # brute-force sum would be a tautology. The meaningful check is the O(1)
        # digamma approximation against the exact rational sum.
        n_check = min(n_check, MAX_VERIFY_HARMONIC)
        fam = Harmonic(params.get("a", 1), params.get("d", 1))
        brute = fam.sum(n_check)
        closed = fam.sum_approx(n_check)
        ok = abs(closed - float(brute)) <= HARMONIC_TOL * max(1.0, abs(float(brute)))
        method = ("O(1) digamma approximation vs exact rational sum, tolerance %g"
                  % HARMONIC_TOL)
    else:
        raise ValueError("unknown family: %s" % family)

    closed_text, closed_cut, _ = to_exact_str(closed)
    brute_text, brute_cut, _ = to_exact_str(brute)
    return {
        "family": family,
        "n": n,
        "n_verified": n_check,
        "spot_checked": n_check < n,
        "params": dict(params),
        "method": method,
        "closed_form": closed_text,
        "brute_force": brute_text,
        "truncated": bool(closed_cut or brute_cut),
        "exact_match": bool(ok),
        "verdict": "PASS" if ok else "FAIL",
    }
