"""omnidimensional — exact, constant-time closed forms for the four progression
families (arithmetic, geometric, harmonic, OmniFit), the generalized power mean,
a harmonic midpoint, and an exact verifier.

The classical mathematics (Nicomachus, Faulhaber, formalized by Knuth) is
presented as proven; the contribution here is unification, exact machine
verification, and a single scale-invariant interface. The harmonic case has no
elementary closed form and says so — it ships an O(1) digamma approximation
instead, which the verifier checks against the exact rational sum.
"""

from .families import (Arithmetic, Geometric, Harmonic, OmniFit, FAMILIES)
from .faulhaber import power_sum_closed, power_sum_brute, bernoulli
from .power_mean import power_mean, power_mean_spectrum
from .midpoint import omnidimensional_midpoint
from .approx import digamma, harmonic_sum_approx
from .render import to_exact_str, to_decimal, digit_count, log10_abs
from .limits import (validate, geometric_digits, FAMILY_NAMES,
                     MAX_EXACT_HARMONIC, MAX_POWER, MAX_N)
from .verify import verify
from .engine import compute, ComputeError

__version__ = "0.1.0"

__all__ = [
    "Arithmetic", "Geometric", "Harmonic", "OmniFit", "FAMILIES",
    "power_sum_closed", "power_sum_brute", "bernoulli",
    "power_mean", "power_mean_spectrum",
    "omnidimensional_midpoint",
    "digamma", "harmonic_sum_approx",
    "to_exact_str", "to_decimal", "digit_count", "log10_abs",
    "validate", "geometric_digits", "FAMILY_NAMES",
    "MAX_EXACT_HARMONIC", "MAX_POWER", "MAX_N",
    "verify", "compute", "ComputeError", "__version__",
]
