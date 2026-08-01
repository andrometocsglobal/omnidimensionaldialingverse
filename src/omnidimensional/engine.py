"""One compute path, shared by the CLI, the API and the Streamlit app.

Keeping this in the package rather than in each front end is what stops the
three surfaces from disagreeing about limits, harmonic fallback, or how a
million-digit result should be rendered.
"""

from .families import Arithmetic, Geometric, Harmonic
from .faulhaber import power_sum_closed
from .limits import MAX_EXACT_HARMONIC, validate
from .render import log10_abs, to_decimal, to_exact_str
from .verify import verify

POWER_FORM = "S_n = sum k^p via Faulhaber, O(1) in n"
HARMONIC_APPROX_FORM = "(psi(a/d + n) - psi(a/d)) / d  — O(1) asymptotic"


class ComputeError(ValueError):
    """A request the limits module refused, with a human-readable reason."""


def compute(family, n, a=1.0, d=1.0, r=2.0, p=2, cross_check=True):
    """Evaluate one progression sum and describe the result.

    Raises :class:`ComputeError` for anything :func:`omnidimensional.validate`
    rejects, so every front end can turn that into its own kind of error
    message instead of a stack trace.
    """
    reason = validate(family, n, a=a, d=d, r=r, p=p)
    if reason:
        raise ComputeError(reason)

    n = int(n)
    approximate = False
    if family == "arithmetic":
        obj = Arithmetic(a, d)
        value, form = obj.sum(n), obj.closed_form
    elif family == "geometric":
        obj = Geometric(a, r)
        value, form = obj.sum(n), obj.closed_form
    elif family == "harmonic":
        obj = Harmonic(a, d)
        if n <= MAX_EXACT_HARMONIC:
            value, form = obj.sum(n), obj.closed_form
        else:
            # The exact HP sum is O(n); past the cap, use the O(1) stand-in and
            # say plainly that the answer is no longer exact.
            value, form, approximate = obj.sum_approx(n), HARMONIC_APPROX_FORM, True
    else:  # "power" — validate() already rejected anything else
        value, form = power_sum_closed(n, p), POWER_FORM

    text, truncated, digits = to_exact_str(value)
    out = {
        "family": family,
        "n": n,
        "params": {"a": a, "d": d, "r": r, "p": p},
        "result": text,
        "truncated": truncated,
        "digits": digits,
        "decimal": to_decimal(value),
        "log10": log10_abs(value),
        "closed_form": form,
        "approximate": approximate,
        "exact": not approximate,
    }
    if cross_check:
        report = verify(family, n, a=a, d=d, r=r, p=p)
        out["exact_match"] = report["exact_match"]
        out["verified_n"] = report["n_verified"]
        out["spot_checked"] = report["spot_checked"]
        out["verify_method"] = report["method"]
    return out
