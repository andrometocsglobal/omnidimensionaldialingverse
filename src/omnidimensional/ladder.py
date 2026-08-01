"""Difference ladders — name an arbitrary run, then sum it in O(1).

Every finite sequence is a polynomial in its index, so its difference ladder
always flattens eventually. What matters is *how fast*: a run that flattens at
depth k is a degree-k polynomial, and its sum collapses to Newton's identity

    sum_{i=0}^{N-1} f(i) = sum_k  D^k f(0) * C(N, k+1)

which costs k+1 terms regardless of N. A run that only flattens at depth N-1
has no structure to exploit -- it is noise wearing a polynomial's clothes, and
this module says so rather than pretending otherwise.

Three ladders name the three families:
    differences of the terms          -> arithmetic (depth 1 = a plain AP)
    ratios of the terms               -> geometric
    differences of the reciprocals    -> harmonic
"""

import math
from fractions import Fraction

from .render import exact

# A ladder that only flattens at the very bottom carries no usable structure.
MIN_FLAT_RUN = 2


def _flat(row):
    return len(row) >= MIN_FLAT_RUN and all(v == row[0] for v in row)


def difference_ladder(values):
    """Successive differences until a level goes flat.

    Returns ``{'levels', 'heads', 'depth', 'flat'}``. ``heads`` are the
    left-edge entries D^k f(0) that Newton's identity needs.
    """
    levels = [[exact(v) for v in values]]
    while len(levels[-1]) > 1:
        row = levels[-1]
        levels.append([row[i + 1] - row[i] for i in range(len(row) - 1)])
        if _flat(levels[-1]):
            break
    return {
        "levels": levels,
        "heads": [row[0] for row in levels if row],
        "depth": len(levels) - 1,
        "flat": _flat(levels[-1]),
    }


def ratio_ladder(values):
    """Successive ratios until a level goes flat. None if any term is zero."""
    row = [exact(v) for v in values]
    if any(v == 0 for v in row):
        return None
    levels = [row]
    while len(levels[-1]) > 1:
        row = levels[-1]
        if any(v == 0 for v in row[:-1]):
            return None
        levels.append([row[i + 1] / row[i] for i in range(len(row) - 1)])
        if _flat(levels[-1]):
            break
    return {
        "levels": levels,
        "heads": [r[0] for r in levels if r],
        "depth": len(levels) - 1,
        "flat": _flat(levels[-1]),
        "ratio": levels[1][0] if len(levels) > 1 else None,
    }


def newton_sum(heads, N):
    """sum_{i=0}^{N-1} f(i) from the ladder heads, via the hockey-stick identity.

    Exact and O(len(heads)) -- independent of N.
    """
    N = int(N)
    total = Fraction(0)
    for k, head in enumerate(heads):
        total += head * math.comb(N, k + 1)
    return total


def newton_term(heads, i):
    """The i-th term f(i) reconstructed from the ladder heads."""
    i = int(i)
    total = Fraction(0)
    for k, head in enumerate(heads):
        total += head * math.comb(i, k)
    return total


def classify(values):
    """Name a run: arithmetic, geometric, harmonic, or unstructured.

    Picks whichever ladder flattens shallowest, tie-breaking toward the more
    specific family (geometric, then harmonic, then arithmetic).
    """
    values = list(values)
    n = len(values)
    if n < 3:
        raise ValueError("need at least 3 values to classify")

    limit = n - 2          # flattening only at depth n-1 proves nothing
    candidates = []

    additive = difference_ladder(values)
    if additive["flat"] and additive["depth"] <= limit:
        candidates.append(("arithmetic", additive["depth"], additive, 2))

    if all(exact(v) != 0 for v in values):
        multiplicative = ratio_ladder(values)
        if (multiplicative and multiplicative["flat"]
                and multiplicative["depth"] <= limit):
            candidates.append(("geometric", multiplicative["depth"],
                               multiplicative, 0))
        reciprocals = [Fraction(1) / exact(v) for v in values]
        harmonic = difference_ladder(reciprocals)
        if harmonic["flat"] and harmonic["depth"] <= limit:
            harmonic["reciprocals"] = reciprocals
            candidates.append(("harmonic", harmonic["depth"], harmonic, 1))

    if not candidates:
        return {
            "family": "unstructured",
            "depth": additive["depth"],
            "ladder": additive,
            "kind": "unstructured",
            "reason": ("no ladder flattened above depth %d; a degree-%d Newton "
                       "fit still reproduces the run exactly, but it is a "
                       "restatement of the data, not a pattern"
                       % (limit, additive["depth"])),
        }

    candidates.sort(key=lambda c: (c[1], c[3]))
    family, depth, ladder, _ = candidates[0]
    return {
        "family": family,
        "depth": depth,
        "ladder": ladder,
        "kind": "plain" if depth <= 1 else "hybrid",
        "reason": "the %s ladder went flat at level %d" % (
            {"arithmetic": "difference", "geometric": "ratio",
             "harmonic": "reciprocal-difference"}[family], depth),
    }


def aggregate(values):
    """The natural O(1) aggregate for whatever family the run turns out to be.

    Arithmetic -> sum, geometric -> product, harmonic -> reciprocal sum. Each
    is cross-checked against the term-by-term result.
    """
    values = list(values)
    N = len(values)
    detected = classify(values)
    family = detected["family"]

    if family == "geometric":
        first, ratio = exact(values[0]), detected["ladder"]["ratio"]
        closed = first ** N * ratio ** (N * (N - 1) // 2)
        direct = Fraction(1)
        for v in values:
            direct *= exact(v)
        label, operations = "product of terms", 3
    elif family == "harmonic":
        heads = detected["ladder"]["heads"]
        closed = newton_sum(heads, N)
        direct = sum((Fraction(1) / exact(v) for v in values), Fraction(0))
        label, operations = "sum of reciprocals", len(heads)
    else:
        heads = detected["ladder"]["heads"]
        closed = newton_sum(heads, N)
        direct = sum((exact(v) for v in values), Fraction(0))
        label, operations = "sum of terms", len(heads)

    return {
        "family": family,
        "kind": detected["kind"],
        "depth": detected["depth"],
        "reason": detected["reason"],
        "label": label,
        "closed": closed,
        "direct": direct,
        "match": closed == direct,
        "operations": operations,
        "terms": N,
        "next_term": newton_term(detected["ladder"]["heads"], N),
        "structured": family != "unstructured",
    }
