"""omnidimensional — exact, constant-time closed forms for the four progression
families (arithmetic, geometric, harmonic, OmniFit), the generalized power mean,
a harmonic midpoint, and an exact verifier.

The classical mathematics (Nicomachus, Faulhaber, formalized by Knuth) is
presented as proven; the contribution here is unification, exact machine
verification, and a single scale-invariant interface. The harmonic case has no
elementary closed form and says so — it ships O(1) approximations instead,
which the verifier checks against the exact rational sum.

Two ways in:

* **closed forms** — ``Geometric(1, 2).sum(64)``, ``power_sum_closed``,
  ``ap_power_sum`` (midpoint/central-moment form), ``gp_power_product``.
* **arbitrary data** — ``classify`` and ``aggregate`` name a run from its
  difference ladder, ``reverse_engineer`` fits the closest law to noisy data,
  and ``omnifit`` pads any count onto a perfect hypercube, solves it in O(1),
  then clips the padding back off.
"""

from .families import (Arithmetic, Geometric, Harmonic, OmniFit, FAMILIES)
from .faulhaber import power_sum_closed, power_sum_brute, bernoulli
from .power_mean import power_mean, power_mean_spectrum
from .midpoint import omnidimensional_midpoint
from .approx import digamma, harmonic_sum_approx
from .moments import (central_moment, run_midpoint, ap_power_sum,
                      ap_power_sum_brute, hp_power_sum_approx,
                      hp_power_sum_brute, gp_power_product,
                      gp_power_product_brute)
from .hypercube import (perfect_shape, best_dimension, solve_by_fit,
                        integer_root_ceil, parse_shape, coordinate)
from .ladder import (difference_ladder, ratio_ladder, newton_sum, newton_term,
                     classify, aggregate)
from .fit import reverse_engineer, segment, assemble, polynomial_fit
from .render import (to_exact_str, to_decimal, digit_count, log10_abs, describe,
                     exact)
from .limits import (validate, geometric_digits, FAMILY_NAMES,
                     FIT_FAMILY_NAMES, MAX_EXACT_HARMONIC, MAX_POWER, MAX_N)
from .verify import verify
from .engine import (compute, omnifit, name_run, ladder_view, reverse,
                     assemble_runs, explore, ComputeError)

__version__ = "0.2.0"

__all__ = [
    "Arithmetic", "Geometric", "Harmonic", "OmniFit", "FAMILIES",
    "power_sum_closed", "power_sum_brute", "bernoulli",
    "power_mean", "power_mean_spectrum",
    "omnidimensional_midpoint",
    "digamma", "harmonic_sum_approx",
    "central_moment", "run_midpoint", "ap_power_sum", "ap_power_sum_brute",
    "hp_power_sum_approx", "hp_power_sum_brute",
    "gp_power_product", "gp_power_product_brute",
    "perfect_shape", "best_dimension", "solve_by_fit", "integer_root_ceil",
    "parse_shape", "coordinate",
    "difference_ladder", "ratio_ladder", "newton_sum", "newton_term",
    "classify", "aggregate",
    "reverse_engineer", "segment", "assemble", "polynomial_fit",
    "to_exact_str", "to_decimal", "digit_count", "log10_abs", "describe",
    "exact",
    "validate", "geometric_digits", "FAMILY_NAMES", "FIT_FAMILY_NAMES",
    "MAX_EXACT_HARMONIC", "MAX_POWER", "MAX_N",
    "verify", "compute", "omnifit", "name_run", "ladder_view", "reverse",
    "assemble_runs", "explore", "ComputeError", "__version__",
]
