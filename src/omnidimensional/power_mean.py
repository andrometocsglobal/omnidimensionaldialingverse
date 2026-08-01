"""The generalized power mean M_p — the single operator that unifies the family
of means (min, harmonic, geometric, arithmetic, quadratic, max) as p sweeps."""

import math


def power_mean(values, p, weights=None, eps=1e-12):
    """Weighted generalized power mean of non-negative values.

    p -> -inf : min ; p = -1 : harmonic ; p = 0 : geometric ;
    p = 1 : arithmetic ; p = 2 : quadratic ; p -> +inf : max.
    """
    xs = [max(eps, float(v)) for v in values]
    if not xs:
        return 0.0
    ws = [1.0] * len(xs) if weights is None else [float(w) for w in weights]
    W = sum(ws)
    if W <= 0:
        return 0.0
    if abs(p) < 1e-12:
        return math.exp(sum(w * math.log(x) for x, w in zip(xs, ws)) / W)
    return (sum(w * x ** p for x, w in zip(xs, ws)) / W) ** (1.0 / p)


def power_mean_spectrum(values, ps=(-4, -2, -1, 0, 1, 2, 4)):
    """M_p across several exponents — a compact multi-scale fingerprint."""
    return {float(p): power_mean(values, p) for p in ps}
