"""Omnidimensional — interactive O(1) explorer (Streamlit, flagship deploy).

Run locally:   streamlit run streamlit_app.py
Deploy:        push to GitHub, then Streamlit Community Cloud -> New app ->
               main file = streamlit_app.py
"""

import sys
import time
from pathlib import Path

import streamlit as st

# make the src/ package importable whether installed or run from the repo
sys.path.insert(0, str(Path(__file__).parent / "src"))

from omnidimensional import (  # noqa: E402
    MAX_N, MAX_POWER, OmniFit, omnidimensional_midpoint, power_mean_spectrum,
    power_sum_brute, power_sum_closed, to_exact_str, verify, __version__,
)
from omnidimensional.engine import ComputeError, compute  # noqa: E402

st.set_page_config(page_title="Omnidimensional · O(1)", page_icon="∑", layout="wide")

st.title("Omnidimensional")
st.caption(
    f"v{__version__} · one exact, constant-time interface for the four progression "
    "families — arithmetic, geometric, harmonic, OmniFit"
)

tab_calc, tab_speed, tab_mean, tab_fit, tab_verify = st.tabs(
    ["Families", "O(1) vs O(n)", "Power mean", "OmniFit", "Exact verifier"]
)

# ---------------------------------------------------------------- Families
with tab_calc:
    c1, c2 = st.columns([1, 2])
    with c1:
        label = st.selectbox(
            "Family", ["arithmetic", "geometric", "harmonic", "power (k^p)"])
        family = "power" if label.startswith("power") else label
        n = st.number_input("n (terms)", 0, MAX_N, 100, step=10)
        kw = {}
        if family == "arithmetic":
            kw["a"] = st.number_input("a (first term)", value=1.0)
            kw["d"] = st.number_input("d (common difference)", value=1.0)
        elif family == "geometric":
            kw["a"] = st.number_input("a (first term)", value=1.0)
            kw["r"] = st.number_input("r (ratio)", value=2.0)
        elif family == "harmonic":
            kw["a"] = st.number_input("a", value=1.0)
            kw["d"] = st.number_input("d", value=1.0)
        else:
            kw["p"] = st.number_input("p (power)", 0, MAX_POWER, 2)

    with c2:
        st.markdown("#### Result")
        try:
            out = compute(family, int(n), **kw)
        except (ComputeError, ZeroDivisionError, OverflowError) as exc:
            st.error(str(exc))
        else:
            st.code(out["result"], language="text")
            st.markdown(f"**Closed form:** `{out['closed_form']}`")

            m1, m2, m3 = st.columns(3)
            m1.metric("digits", f"{out['digits']:,}")
            m2.metric("decimal",
                      "overflows float" if out["decimal"] is None
                      else f"{out['decimal']:.6g}")
            m3.metric("cross-check", "exact ✓" if out["exact_match"] else "FAIL")

            if out["truncated"]:
                st.info(
                    f"The exact value has {out['digits']:,} digits — shown in "
                    "scientific notation. Nothing was rounded in the computation "
                    "itself; only the display is bounded."
                )
            if out["approximate"]:
                st.warning(
                    "Harmonic sums have no elementary closed form. Past "
                    f"n = {out['verified_n']:,} this is the O(1) digamma "
                    "approximation, not an exact rational."
                )
            if out["spot_checked"]:
                st.caption(
                    f"Cross-checked term-by-term at n = {out['verified_n']:,} "
                    f"(the request was n = {out['n']:,}; summing that many terms "
                    "would defeat the point of a closed form)."
                )

# ---------------------------------------------------------------- O(1) vs O(n)
with tab_speed:
    st.markdown("Compare the closed form (constant work) to the term-by-term sum "
                "(work grows with n). Same exact answer; very different cost.")
    p = st.slider("power p", 1, 5, 2)
    rows = []
    for nn in (1_000, 10_000, 100_000, 1_000_000):
        t0 = time.perf_counter()
        closed = power_sum_closed(nn, p)
        t_closed = time.perf_counter() - t0
        if nn <= 100_000:
            t0 = time.perf_counter()
            brute = power_sum_brute(nn, p)
            t_brute = time.perf_counter() - t0
            match = "exact match" if closed == brute else "MISMATCH"
        else:
            t_brute, match = None, "skipped (too slow)"
        # Keep brute_force_s numeric — mixing floats with a placeholder string
        # makes the column type `object` and Arrow serialization fails.
        rows.append({"n": nn,
                     "closed_form_s": round(t_closed, 6),
                     "brute_force_s": None if t_brute is None else round(t_brute, 6),
                     "result": match})
    st.dataframe(rows)
    st.caption("Closed-form time stays flat; brute-force time scales with n.")

# ---------------------------------------------------------------- Power mean
with tab_mean:
    st.markdown("The generalized power mean M_p unifies min → harmonic → geometric "
                "→ arithmetic → quadratic → max as p sweeps.")
    raw = st.text_input("values (comma-separated)", "3, 5, 11, 2")
    try:
        vals = [float(x) for x in raw.split(",") if x.strip()]
        if not vals:
            raise ValueError("enter at least one number")
        spec = power_mean_spectrum(vals)
        st.line_chart({"M_p": list(spec.values())})
        st.write({f"p={int(pp)}": round(v, 4) for pp, v in spec.items()})
    except ValueError as exc:
        st.error(str(exc))

    st.divider()
    mc1, mc2, mc3 = st.columns(3)
    ma = mc1.number_input("midpoint a", value=2.0)
    mb = mc2.number_input("midpoint b", value=3.0)
    mf = mc3.selectbox("midpoint family",
                       ["harmonic", "arithmetic", "geometric", "quadratic"])
    try:
        mid = omnidimensional_midpoint(ma, mb, mf)
        st.metric(f"{mf} midpoint", f"{float(mid):.6g}")
        if mf in ("harmonic", "arithmetic"):
            st.caption(f"exact: {to_exact_str(mid)[0]}")
    except (ValueError, ZeroDivisionError) as exc:
        st.error(str(exc))

# ---------------------------------------------------------------- OmniFit
with tab_fit:
    st.markdown(
        "OmniFit warps irregular sample positions onto an even grid, so a "
        "progression closed form applies to data that was never evenly spaced."
    )
    xs_raw = st.text_input("sample positions (strictly increasing)",
                           "0, 1, 4, 9, 16, 25")
    try:
        xs = [float(x) for x in xs_raw.split(",") if x.strip()]
        fit = OmniFit(xs)
        st.dataframe([{"position x": x, "grid index": fit.warp(x),
                       "unwarp(warp(x))": fit.unwarp(fit.warp(x))} for x in xs])
        q = st.slider("query a position", float(min(xs)), float(max(xs)),
                      float(xs[len(xs) // 2]))
        w = fit.warp(q)
        q1, q2 = st.columns(2)
        q1.metric("warped grid index", f"{w:.4f}")
        q2.metric("round-trip back", f"{fit.unwarp(w):.6g}")
        st.caption("The warp is the cumulative-rank map; unwarp inverts it, so "
                   "positions survive the round trip.")
    except ValueError as exc:
        st.error(str(exc))

# ---------------------------------------------------------------- Verifier
with tab_verify:
    st.markdown("Every closed form is checked against a term-by-term sum in exact "
                "arithmetic (Python `Fraction`).")
    vf = st.selectbox("family", ["arithmetic", "geometric", "power", "harmonic"],
                      key="vf")
    vn = st.number_input("n", 0, MAX_N, 500, key="vn")
    vkw = {}
    if vf in ("arithmetic", "harmonic"):
        vkw["a"] = st.number_input("a", value=1.0, key="va")
        vkw["d"] = st.number_input("d", value=1.0, key="vd")
    elif vf == "geometric":
        vkw["a"] = st.number_input("a", value=1.0, key="va2")
        vkw["r"] = st.number_input("r", value=2.0, key="vr")
    else:
        vkw["p"] = st.number_input("p", 0, MAX_POWER, 2, key="vp")
    try:
        report = verify(vf, int(vn), **vkw)
    except (ValueError, ZeroDivisionError) as exc:
        st.error(str(exc))
    else:
        (st.success if report["exact_match"] else st.error)(report["verdict"])
        st.caption(report["method"])
        if report["spot_checked"]:
            st.info(f"Verified term-by-term at n = {report['n_verified']:,} of the "
                    f"requested n = {report['n']:,}.")
        st.json(report)
