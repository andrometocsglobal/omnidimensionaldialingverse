# The Four Progression Families: A Unified, Exact, Constant-Time Treatment

*A generalized note on arithmetic, geometric, harmonic, and OmniFit progressions
— what each closes in constant time, where the boundary honestly lies, and why a
single power-mean interface ties them together.*

## 1. Motivation

A great deal of quantitative work reduces to the same question: given a rule that
generates a sequence, what is the sum (or the mean, or the midpoint) of its first
`n` terms? Computed naively this costs O(n) — one operation per term. For the
*structured* sequences that dominate practice, the answer instead has a **closed
form** evaluated in a fixed number of operations, independent of `n`. This note
collects the four families the `omnidimensional` package implements under one
interface, states each closed form, verifies it in exact arithmetic, and draws
the boundary where a closed form stops existing.

The mathematics is classical. The lineage runs from **Nicomachus (c. 100 AD)**
through **Faulhaber (1631)**, formalized by **Knuth (1993)**. The contribution
here is *unification, exact machine-verification, and a single scale-invariant
interface* — not a new theorem. Framing it that way is what makes it credible and
still useful.

## 2. The four families

### 2.1 Arithmetic (AP)
Terms `a, a+d, a+2d, …`. The sum of the first `n` terms is
`S_n = n/2 · (2a + (n−1)d)` — two multiplications and a division, O(1) in `n`.
Raising each term to a power `p` produces a **power sum** `Σ kᵖ`, which Faulhaber
closes with Bernoulli numbers: `Σ_{k=1}^{n} kᵖ` is a degree-`(p+1)` polynomial in
`n`, again O(1) in `n` (and O(p²) in the power). This is the engine behind
"any power" — raising a depth-`D` difference ladder to power `p` yields another
finite ladder of depth `D·p`, still closed by one pass.

### 2.2 Geometric (GP)
Terms `a, ar, ar², …`. The sum is `S_n = a(rⁿ − 1)/(r − 1)` for `r ≠ 1`, and
`a·n` for `r = 1`. The midpoint analogue is multiplicative: the geometric mean
`√(a·b)` replaces the arithmetic `(a+b)/2`.

### 2.3 Harmonic (HP) — the honest boundary
Terms `1/a, 1/(a+d), 1/(a+2d), …` — reciprocals of an AP. Here the method
**states its own limit**: reciprocal-power sums admit *no elementary closed form*;
they require special functions (digamma / generalized harmonic numbers). The
package therefore returns an **exact rational** obtained by summation, and says
so. Naming this boundary is part of the result, not a footnote — a tool that
claims a closed form it does not have is worse than one that abstains.

### 2.4 OmniFit — regularizing irregular spacing
Real data is rarely evenly spaced. OmniFit **warps** strictly-increasing sample
positions onto a uniform index grid (the cumulative-rank map), so that a
progression closed form applies to data that was not uniform to begin with, and
an inverse `unwarp` returns to the original coordinate. It is not a new
progression so much as an *adapter* that lets the other three apply more widely —
the practical bridge from clean theory to messy inputs.

## 3. One operator over all of them: the generalized power mean

The families of *means* collapse into a single operator, the **power mean**
`M_p(x) = ( (Σ wᵢ xᵢᵖ) / Σwᵢ )^{1/p}`. As `p` sweeps it becomes, in order,
min (`p→−∞`), harmonic (`p=−1`), geometric (`p=0`), arithmetic (`p=1`),
quadratic (`p=2`), and max (`p→+∞`). `M_p` is monotonically non-decreasing in
`p` and bounded by the min and max of its inputs. Two consequences matter in
applications:

- **Tail-awareness.** Low `p` is pulled toward the smallest input, which is the
  prudent bias whenever a single weak component should not be averaged away.
- **One knob, identifiable from data.** Choosing `p` on held-out data is a
  one-line, overfitting-resistant way to select the *correct* summary for a
  bounded quantity, rather than defaulting to the arithmetic mean.

The `omnidimensional_midpoint(a, b, family)` call is the two-point special case:
harmonic `2ab/(a+b)`, arithmetic `(a+b)/2`, geometric `√(ab)`, quadratic
`√((a²+b²)/2)`.

## 4. Exactness and verification

Every closed form in the package is checked against a term-by-term sum in **exact
rational arithmetic** (`fractions.Fraction`), so a passing check is a proof of
equality for those inputs, not a floating-point coincidence. `verify(family, n,
…)` returns both values and a PASS/FAIL verdict; the test suite exercises AP, GP,
HP, and power sums across several sizes and powers. Because the outputs are
re-derivable and exact, any downstream decision built on them is auditable rather
than estimated.

## 5. The complexity claim, scoped honestly

"O(1)" here means **constant in the number of terms `n`**: the closed form does a
fixed handful of arithmetic operations whether `n` is a thousand or a
quindecillion. It does **not** mean infinitely fast, and it applies only to the
*structured* case — the four families above. Unstructured data, general
computation, and the harmonic closed form are explicitly outside the regime. The
value is therefore precise: for the structured part of a problem, cost stops
scaling with size, freeing compute and attention for the part that genuinely is
not structured.

## 6. Where it is useful

Anywhere the structured part of a workload is a progression or a bounded
aggregate: fast exact partial sums in analytics, closed-form feature generation
over ordered signals (a curve sampled along depth, time, or position),
power-mean pooling and ensembling, and any setting that benefits from an
auditable, re-derivable primitive beneath a heavier model. The same operators
port across modalities because they describe *structure*, not a domain.

## 7. Summary

Four families, one interface: arithmetic and geometric close in constant time;
power sums close via Faulhaber; harmonic is summed exactly and its lack of an
elementary closed form is stated plainly; OmniFit extends all three to
irregularly-spaced data. The generalized power mean unifies their means under a
single tunable operator, and an exact verifier keeps every claim honest.

## References
- Nicomachus of Gerasa, *Introduction to Arithmetic* (c. 100 AD).
- J. Faulhaber, *Academia Algebrae* (1631).
- D. E. Knuth, "Johann Faulhaber and Sums of Powers," *Math. Comp.* 61 (1993).
- G. H. Hardy, J. E. Littlewood, G. Pólya, *Inequalities* (1934) — power means.
