"""Shared safety limits, so every front end refuses the same runaway inputs.

The closed forms are O(1) in the number of terms, but that does not make every
request safe: ``Geometric(1, 2).sum(10**9)`` is a well-defined exact integer
with ~300 million digits, and building it will exhaust memory long before it
returns. Streamlit, the API and the CLI all validate through :func:`validate`
so they agree on what is answerable.
"""

import math

MAX_N = 10 ** 12            # closed forms are O(1) in n, so n itself can be huge
MAX_POWER = 100             # Faulhaber cost is O(p^2) in exact rationals
MAX_RESULT_DIGITS = 200_000  # refuse results too large to build and ship
MAX_EXACT_HARMONIC = 100_000  # HP exact sum is O(n); above this, approximate
MAX_BRUTE = 50_000          # ceiling on the verifier's term-by-term reference
MAX_VERIFY_HARMONIC = 20_000  # exact HP reference used by the verifier
MAX_VERIFY_DIGITS = 2_000   # keep the verifier's GP reference cheap

FAMILY_NAMES = ("arithmetic", "geometric", "harmonic", "power")


def geometric_digits(a, r, n):
    """Estimated decimal size of ``Geometric(a, r).sum(n)``, computed in logs.

    Both |r| > 1 and |r| < 1 blow up — the first in the numerator, the second
    in the denominator — so the magnitude of log10|r| is what matters.
    """
    n = int(n)
    if n <= 0:
        return 1
    abs_a, abs_r = abs(float(a)), abs(float(r))
    if abs_a == 0.0 or abs_r == 0.0:
        return 1
    base = math.log10(abs_a)
    if abs(abs_r - 1.0) < 1e-15:          # sum is a*n
        return max(1, int(base + math.log10(n)) + 1)
    return max(1, int(base + n * abs(math.log10(abs_r))) + 1)


def geometric_brute_cap(a, r, max_digits=MAX_VERIFY_DIGITS):
    """Largest n whose term-by-term GP sum is still cheap to compute."""
    abs_r = abs(float(r))
    if abs_r == 0.0 or abs(abs_r - 1.0) < 1e-15:
        return MAX_BRUTE
    return max(1, min(MAX_BRUTE, int(max_digits / abs(math.log10(abs_r)))))


def validate(family, n, a=1.0, d=1.0, r=2.0, p=2):
    """Return None if the request is answerable, else a human-readable reason."""
    if family not in FAMILY_NAMES:
        return "unknown family: %r (expected one of %s)" % (
            family, ", ".join(FAMILY_NAMES))
    try:
        n = int(n)
    except (TypeError, ValueError):
        return "n must be an integer"
    if n < 0:
        return "n must be >= 0"
    if n > MAX_N:
        return "n must be <= %d" % MAX_N

    if family == "power":
        p = int(p)
        if not 0 <= p <= MAX_POWER:
            return "p must be between 0 and %d" % MAX_POWER

    if family == "geometric":
        digits = geometric_digits(a, r, n)
        if digits > MAX_RESULT_DIGITS:
            # Plain ASCII: this string reaches Windows consoles via the CLI.
            return ("geometric sum with r=%s and n=%d has about %s digits; "
                    "the limit is %s. Reduce n, or bring |r| closer to 1."
                    % (r, n, format(digits, ","), format(MAX_RESULT_DIGITS, ",")))

    if family == "harmonic":
        a_f, d_f = float(a), float(d)
        if d_f == 0.0:
            return None if a_f != 0.0 else "harmonic undefined for a = 0, d = 0"
        # a term is undefined wherever a + k*d == 0 for an integer k in range
        k = -a_f / d_f
        if abs(k - round(k)) < 1e-12 and 0 <= round(k) < n:
            return "harmonic term undefined: a + k*d = 0 at k = %d" % int(round(k))

    return None
