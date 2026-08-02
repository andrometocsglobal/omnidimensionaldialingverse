"""One compute path, shared by the CLI, the API and the Streamlit app.

Keeping this in the package rather than in each front end is what stops the
three surfaces from disagreeing about limits, harmonic fallback, or how a
million-digit result should be rendered.
"""

from fractions import Fraction

from .families import Arithmetic, Geometric, Harmonic
from .faulhaber import power_sum_closed
from .fit import assemble, reverse_engineer
from .hypercube import (best_dimension, coordinate, parse_shape, perfect_shape,
                        solve_by_fit)
from .ladder import aggregate
from .limits import (FIT_FAMILY_NAMES, MAX_CELLS, MAX_EXACT_HARMONIC,
                     MAX_FIT_N, MAX_RESULT_DIGITS, MAX_VALUES,
                     geometric_digits, non_finite, validate)
from .moments import (ap_power_sum, gp_power_product, hp_power_sum_approx,
                      hp_power_sum_brute, run_midpoint)
from .render import describe, exact, log10_abs, to_decimal, to_exact_str
from .verify import verify

POWER_FORM = "S_n = sum_{k=1}^{n} k^p via Faulhaber, O(1) in n"
POWER_FROM_FORM = ("S = sum_{k=a}^{a+n-1} k^p via central moments about the "
                   "midpoint, O(1) in n")
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
        start = exact(a)
        if start == 1:
            value, form = power_sum_closed(n, p), POWER_FORM
        else:
            # k runs from `a`, so this is the midpoint/central-moment form.
            value, form = ap_power_sum(start, 1, n, p), POWER_FROM_FORM

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


# --------------------------------------------------------------- fit / pad / clip

def _check_values(values, minimum=3):
    values = list(values)
    if len(values) < minimum:
        raise ComputeError("need at least %d numbers (got %d)"
                           % (minimum, len(values)))
    if len(values) > MAX_VALUES:
        raise ComputeError("at most %d numbers per request" % MAX_VALUES)
    return values


def omnifit(family, N, dimension=3, F=1, h=1, r=2, p=1, order=3):
    """Fit N terms onto a perfect hypercube, solve it, and clip the padding.

    The headline pipeline: both the full-shape solve and the padding solve are
    O(1), so the whole thing is O(1) and the padding is free.
    """
    if family not in FIT_FAMILY_NAMES:
        raise ComputeError("family must be one of %s"
                           % ", ".join(FIT_FAMILY_NAMES))
    N = int(N)
    if not 0 <= N <= MAX_FIT_N:
        raise ComputeError("N must be between 0 and %d" % MAX_FIT_N)
    if not 1 <= int(dimension) <= 8:
        raise ComputeError("dimension must be between 1 and 8")
    if not 0 <= int(p) <= 64:
        raise ComputeError("power must be between 0 and 64")
    unusable = non_finite(F=F, h=h, r=r)
    if unusable:
        raise ComputeError(unusable)

    shape = perfect_shape(N, dimension)
    if family == "geometric":
        # The padded shape, not N, is what actually gets built.
        digits = geometric_digits(F, r, shape["total"])
        if digits > MAX_RESULT_DIGITS:
            raise ComputeError(
                "the padded shape %d^%d = %s terms gives a product of about %s "
                "digits; the limit is %s. Reduce N, the dimension, or |r|."
                % (shape["n"], shape["dimension"], format(shape["total"], ","),
                   format(digits, ","), format(MAX_RESULT_DIGITS, ",")))
    if family == "harmonic":
        step = exact(h)
        if step == 0 and exact(F) == 0:
            raise ComputeError("harmonic undefined for F = 0, h = 0")
        if step != 0:
            k = -exact(F) / step
            if k.denominator == 1 and 0 <= k < shape["total"]:
                raise ComputeError(
                    "harmonic term undefined: F + k*h = 0 at k = %d" % k)

    try:
        result = solve_by_fit(family, N, dimension, F=F, h=h, r=r, p=p,
                              order=order)
    except (ValueError, ZeroDivisionError) as exc:
        raise ComputeError(str(exc))

    direct = None
    if N <= 4000:
        direct = _direct_fit_reference(family, N, F, h, r, p)

    out = {
        "family": family,
        "N": N,
        "shape": result["shape"],
        "operation": result["operation"],
        "full": describe(result["full"]),
        "pad": describe(result["pad"]),
        "answer": describe(result["answer"]),
        "exact": result["exact"],
        "approximate": not result["exact"],
        "params": {"F": float(F), "h": float(h), "r": float(r), "p": int(p)},
        "best_dimension": best_dimension(N) if N else None,
        "formula_operations": int(p) // 2 + 2,
        "direct_operations": N,
    }
    if result["midpoint"] is not None:
        out["midpoint"] = str(result["midpoint"])
    if direct is not None:
        out["direct"] = describe(direct)
        if result["exact"]:
            out["exact_match"] = result["answer"] == direct
        else:
            reference = float(direct)
            out["exact_match"] = None
            out["relative_error"] = (
                abs(float(result["answer"]) - reference) / abs(reference)
                if reference else 0.0)
        out["checked_directly"] = True
    else:
        out["checked_directly"] = False
    return out


def _direct_fit_reference(family, N, F, h, r, p):
    if family == "arithmetic":
        start, step = exact(F), exact(h)
        return sum(((start + i * step) ** int(p) for i in range(N)), Fraction(0))
    if family == "geometric":
        first, ratio, out = exact(F), exact(r), Fraction(1)
        for i in range(N):
            out *= (first * ratio ** i) ** int(p)
        return out
    return hp_power_sum_brute(F, h, N, p)


# --------------------------------------------------------------- the lab

def name_run(values):
    """Name an arbitrary run and aggregate it with whatever law fits."""
    values = _check_values(values, minimum=3)
    try:
        summary = aggregate(values)
    except (ValueError, ZeroDivisionError) as exc:
        raise ComputeError(str(exc))
    ladder = summary.pop("ladder", None)
    out = dict(summary)
    out["closed"] = describe(summary["closed"])
    out["direct"] = describe(summary["direct"])
    out["next_term"] = describe(summary["next_term"])
    out["values"] = [str(exact(v)) for v in values]
    del ladder
    return out


def ladder_view(values, max_levels=8, max_width=12):
    """The difference (or ratio) ladder, trimmed for display."""
    from .ladder import classify, difference_ladder, ratio_ladder
    values = _check_values(values, minimum=3)
    detected = classify(values)
    if detected["family"] == "geometric":
        built, kind = ratio_ladder(values), "ratio"
    elif detected["family"] == "harmonic":
        built = difference_ladder([Fraction(1) / exact(v) for v in values])
        kind = "reciprocal difference"
    else:
        built, kind = difference_ladder(values), "difference"
    rows = []
    for index, level in enumerate(built["levels"][:max_levels]):
        rows.append({
            "level": index,
            "label": "terms" if index == 0 else "%s %d" % (kind, index),
            "values": [str(v) for v in level[:max_width]],
            "truncated": len(level) > max_width,
        })
    return {
        "kind": kind, "family": detected["family"], "depth": detected["depth"],
        "reason": detected["reason"], "levels": rows,
        "heads": [str(v) for v in built["heads"]],
        "flat": built["flat"],
    }


def reverse(values):
    """Rank candidate AP / GP / HP / hybrid laws for noisy data."""
    values = _check_values(values, minimum=4)
    try:
        return reverse_engineer(values)
    except (ValueError, ZeroDivisionError) as exc:
        raise ComputeError(str(exc))


def assemble_runs(values, blocks=1, sort_first=False):
    """Split into blocks, solve each with its own law, recombine."""
    values = _check_values(values, minimum=3)
    if not 1 <= int(blocks) <= len(values):
        raise ComputeError("blocks must be between 1 and %d" % len(values))
    try:
        result = assemble(values, blocks, sort_first)
    except (ValueError, ZeroDivisionError) as exc:
        raise ComputeError(str(exc))
    out = dict(result)
    out["total"] = describe(result["total"])
    out["direct"] = describe(result["direct"])
    out["blocks"] = [dict(row, sum=describe(row["sum"])) for row in result["blocks"]]
    return out


# --------------------------------------------------------------- shape explorer

def explore(shape="2 x 2", family="arithmetic", start=7, step=1, power=3,
            max_terms=256):
    """Lay a run out over a dimensional arrangement and inspect every cell."""
    if family not in FIT_FAMILY_NAMES:
        raise ComputeError("family must be one of %s"
                           % ", ".join(FIT_FAMILY_NAMES))
    try:
        parsed = parse_shape(shape)
    except ValueError as exc:
        raise ComputeError(str(exc))
    count = parsed["count"]
    if count > MAX_CELLS:
        raise ComputeError("%s cells exceeds the %s-cell limit"
                           % (format(count, ","), format(MAX_CELLS, ",")))
    power = int(power)
    if not 0 <= power <= 32:
        raise ComputeError("power must be between 0 and 32")
    unusable = non_finite(start=start, step=step)
    if unusable:
        raise ComputeError(unusable)

    first, delta = exact(start), exact(step)
    if family == "geometric":
        if first == 0 or delta == 0:
            raise ComputeError("geometric start and ratio must be non-zero")
        digits = geometric_digits(start, step, count)
        if digits > MAX_RESULT_DIGITS:
            raise ComputeError("product would have about %s digits"
                               % format(digits, ","))
        terms = [first * delta ** i for i in range(count)]
        value = gp_power_product(start, step, count, power)
        label, approximate = "product of powered terms", False
    elif family == "harmonic":
        terms = [first + i * delta for i in range(count)]
        if any(t == 0 for t in terms):
            raise ComputeError("a harmonic denominator is zero")
        value = sum((Fraction(1) / t ** power for t in terms), Fraction(0))
        label, approximate = "sum of reciprocal powers", False
    else:
        terms = [first + i * delta for i in range(count)]
        value = ap_power_sum(start, step, count, power)
        label, approximate = "sum of powered terms", False

    rows = []
    for index in range(min(count, int(max_terms))):
        term = terms[index]
        contribution = (term ** power if family != "harmonic"
                        else Fraction(1) / term ** power)
        rows.append({
            "index": index + 1,
            "coordinate": coordinate(index, parsed["dims"]),
            "base": str(term),
            "contribution": describe(contribution)["text"],
        })

    last = terms[-1] if terms else first
    centre = (run_midpoint(start, step, count) if family != "geometric"
              else None)
    return {
        "family": family, "label": label, "approximate": approximate,
        "shape": parsed, "count": count, "dimensions": len(parsed["dims"]),
        "value": describe(value),
        "first": str(first), "last": str(last),
        "midpoint": str(centre) if centre is not None else None,
        "terms": rows, "terms_truncated": count > len(rows),
        "power": power,
    }
