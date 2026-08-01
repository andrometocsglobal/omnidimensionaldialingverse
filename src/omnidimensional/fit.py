"""Reverse-engineer the closest AP / GP / HP / hybrid law for noisy data.

:mod:`omnidimensional.ladder` answers "is this run *exactly* one of the three
families?". This module answers the softer question: "which law does it most
nearly follow?" -- least-squares fits ranked by adjusted R-squared, so extra
parameters have to earn their place.

The polynomial fits solve the normal equations in exact rational arithmetic, so
they do not inherit the conditioning problems that make float normal equations
unreliable at higher degrees. The geometric fit needs logarithms and is
therefore floating point by nature.
"""

import math
from fractions import Fraction

from .ladder import classify, newton_sum
from .render import exact

MAX_FIT_DEGREE = 3


def solve_exact(matrix, vector):
    """Gauss-Jordan over Fractions. Returns None when the system is singular."""
    n = len(vector)
    A = [row[:] for row in matrix]
    b = vector[:]
    for col in range(n):
        pivot = next((r for r in range(col, n) if A[r][col] != 0), None)
        if pivot is None:
            return None
        A[col], A[pivot] = A[pivot], A[col]
        b[col], b[pivot] = b[pivot], b[col]
        scale = A[col][col]
        A[col] = [v / scale for v in A[col]]
        b[col] = b[col] / scale
        for r in range(n):
            if r == col or A[r][col] == 0:
                continue
            factor = A[r][col]
            A[r] = [A[r][c] - factor * A[col][c] for c in range(n)]
            b[r] = b[r] - factor * b[col]
    return b


def polynomial_fit(xs, ys, degree):
    """Exact least-squares polynomial coefficients, lowest order first."""
    size = degree + 1
    xs = [exact(x) for x in xs]
    ys = [exact(y) for y in ys]
    matrix = [[sum((x ** (r + c) for x in xs), Fraction(0)) for c in range(size)]
              for r in range(size)]
    vector = [sum((y * x ** r for x, y in zip(xs, ys)), Fraction(0))
              for r in range(size)]
    return solve_exact(matrix, vector)


def polynomial_value(coefficients, x):
    return sum((c * exact(x) ** i for i, c in enumerate(coefficients)),
               Fraction(0))


def r_squared(ys, predictions):
    ys = [float(y) for y in ys]
    predictions = [float(p) for p in predictions]
    mean = sum(ys) / len(ys)
    residual = sum((y - p) ** 2 for y, p in zip(ys, predictions))
    total = sum((y - mean) ** 2 for y in ys)
    if total < 1e-15:
        return 1.0 if residual < 1e-15 else 0.0
    return 1.0 - residual / total


def _adjusted(r2, n, params):
    if n - params - 1 <= 0:
        return r2
    return 1.0 - (1.0 - r2) * (n - 1) / (n - params - 1)


def reverse_engineer(values):
    """Rank candidate laws for ``values`` by adjusted R-squared."""
    values = list(values)
    n = len(values)
    if n < 4:
        raise ValueError("need at least 4 values to reverse-engineer a trend")
    xs = list(range(n))
    ys = [exact(v) for v in values]
    models = []

    names = {1: "arithmetic (linear)", 2: "hybrid degree 2",
             3: "hybrid degree 3"}
    for degree in range(1, min(MAX_FIT_DEGREE, n - 2) + 1):
        coefficients = polynomial_fit(xs, ys, degree)
        if coefficients is None:
            continue
        predictions = [polynomial_value(coefficients, x) for x in xs]
        models.append({
            "name": names[degree], "kind": "polynomial", "params": degree,
            "r2": r_squared(ys, predictions),
            "predictions": predictions,
            "coefficients": [str(c) for c in coefficients],
            "formula": _polynomial_formula(coefficients),
            "next": float(polynomial_value(coefficients, n)),
        })

    floats = [float(y) for y in ys]
    if all(v != 0 for v in floats) and (all(v > 0 for v in floats)
                                        or all(v < 0 for v in floats)):
        sign = 1.0 if floats[0] > 0 else -1.0
        logs = [math.log(abs(v)) for v in floats]
        coefficients = polynomial_fit(xs, logs, 1)
        if coefficients is not None:
            intercept, slope = float(coefficients[0]), float(coefficients[1])
            ratio, first = math.exp(slope), sign * math.exp(intercept)
            predictions = [first * ratio ** x for x in xs]
            models.append({
                "name": "geometric (x ratio)", "kind": "geometric", "params": 1,
                "r2": r_squared(ys, predictions), "predictions": predictions,
                "formula": "a(n) = %.6g * %.6g^n" % (first, ratio),
                "next": first * ratio ** n,
            })

    if all(y != 0 for y in ys):
        coefficients = polynomial_fit(xs, [Fraction(1) / y for y in ys], 1)
        if coefficients is not None and any(c != 0 for c in coefficients):
            denominators = [polynomial_value(coefficients, x) for x in xs]
            if all(d != 0 for d in denominators):
                predictions = [Fraction(1) / d for d in denominators]
                tail = polynomial_value(coefficients, n)
                models.append({
                    "name": "harmonic (1/x linear)", "kind": "harmonic",
                    "params": 1, "r2": r_squared(ys, predictions),
                    "predictions": predictions,
                    "formula": "a(n) = 1 / (%s + %s*n)" % (
                        _short(coefficients[0]), _short(coefficients[1])),
                    "next": float(Fraction(1) / tail) if tail != 0 else None,
                })

    if not models:
        raise ValueError("no candidate law could be fitted to these values")

    for model in models:
        model["adjusted_r2"] = _adjusted(model["r2"], n, model["params"])
    models.sort(key=lambda m: (-m["adjusted_r2"], m["params"]))

    best = models[0]
    residual = math.sqrt(sum((float(y) - float(p)) ** 2
                             for y, p in zip(ys, best["predictions"])) / n)
    signal = math.sqrt(sum(float(y) ** 2 for y in ys) / n)
    for model in models:
        model.pop("predictions")
    return {
        "models": models,
        "best": best,
        "residual_rms": residual,
        "relative_residual": residual / signal if signal else 0.0,
        "quality": _quality(best["r2"]),
        "terms": n,
    }


def _short(value):
    return str(value) if len(str(value)) <= 12 else "%.6g" % float(value)


def _polynomial_formula(coefficients):
    pieces = []
    for power, c in enumerate(coefficients):
        if c == 0 and power:
            continue
        term = _short(c) if not power else "%s*n%s" % (
            _short(c), "" if power == 1 else "^%d" % power)
        pieces.append(term)
    return "a(n) = " + " + ".join(pieces or ["0"])


def _quality(r2):
    if r2 > 0.9999:
        return "exact"
    if r2 > 0.99:
        return "excellent"
    if r2 > 0.9:
        return "good"
    if r2 > 0.6:
        return "weak"
    return "poor"


def segment(values, blocks):
    """Split into ``blocks`` contiguous, near-equal parts."""
    values = list(values)
    blocks = max(1, int(blocks))
    if blocks > len(values):
        blocks = len(values)
    base, extra = divmod(len(values), blocks)
    out, index = [], 0
    for i in range(blocks):
        size = base + (1 if i < extra else 0)
        out.append(values[index:index + size])
        index += size
    return out


def assemble(values, blocks=1, sort_first=False):
    """Split, solve each block with its own O(1) law, then recombine.

    Sorting first often turns wild data into locally-regular stretches, which
    is the honest way to make a closed form apply to something that was never
    a progression to begin with.
    """
    values = sorted(values) if sort_first else list(values)
    parts = segment(values, blocks)
    total, operations, rows, all_constant_time = Fraction(0), 0, [], True

    for index, part in enumerate(parts):
        if len(part) < 3:
            block_sum = sum((exact(v) for v in part), Fraction(0))
            law, note, cost, constant = "direct", "too short to name", len(part), False
        else:
            detected = classify(part)
            law = detected["family"]
            if law == "unstructured":
                block_sum = sum((exact(v) for v in part), Fraction(0))
                note, cost, constant = "no structure; summed directly", len(part), False
            elif law == "geometric":
                # Assembly adds blocks up, so a geometric block needs its
                # series sum here, not the product `aggregate` would return.
                ratio, first, m = (detected["ladder"]["ratio"],
                                   exact(part[0]), len(part))
                block_sum = (first * m if ratio == 1
                             else first * (ratio ** m - 1) / (ratio - 1))
                note, cost, constant = "geometric series", 4, True
            elif law == "harmonic":
                # The ladder describes the reciprocals; the sum of the terms
                # themselves is exactly the case with no elementary closed form.
                block_sum = sum((exact(v) for v in part), Fraction(0))
                note, cost, constant = ("harmonic: term sum has no closed form",
                                        len(part), False)
            else:
                heads = detected["ladder"]["heads"]
                block_sum = newton_sum(heads, len(part))
                note = "%s ladder depth %d" % (law, detected["depth"])
                cost, constant = len(heads), True
        total += block_sum
        operations += cost
        all_constant_time = all_constant_time and constant
        rows.append({
            "block": index + 1, "terms": len(part),
            "low": min(part) if part else None,
            "high": max(part) if part else None,
            "law": law, "note": note, "sum": block_sum, "operations": cost,
        })

    direct = sum((exact(v) for v in values), Fraction(0))
    return {
        "blocks": rows,
        "total": total,
        "direct": direct,
        "match": total == direct,
        "operations": operations,
        "direct_operations": len(values),
        "all_constant_time": all_constant_time,
        "sorted": bool(sort_first),
    }
