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
from omnidimensional.engine import (  # noqa: E402
    ComputeError, assemble_runs, compute, explore, ladder_view, name_run,
    omnifit, reverse,
)

st.set_page_config(page_title="Omnidimensional · O(1)", page_icon="∑", layout="wide")

st.title("Omnidimensional")
st.caption(
    f"v{__version__} · one exact, constant-time interface for the four progression "
    "families — arithmetic, geometric, harmonic, OmniFit"
)

(tab_calc, tab_fit, tab_shape, tab_lab, tab_speed, tab_mean,
 tab_verify) = st.tabs(
    ["Families", "Omni-Fit", "Explorer", "Sequence Lab", "O(1) vs O(n)",
     "Power mean", "Exact verifier"]
)


def _read_numbers(text):
    """Pull every number out of a free-form string."""
    import re
    return [float(x) for x in re.findall(r"-?\d+(?:\.\d+)?", text)]


def _show(value):
    """Result headline plus the three magnitude metrics."""
    st.code(value["text"], language="text")
    c1, c2, c3 = st.columns(3)
    c1.metric("digits", f"{value['digits']:,}")
    c2.metric("decimal", "overflows float" if value["decimal"] is None
              else f"{value['decimal']:.6g}")
    c3.metric("log10", "—" if value["log10"] is None else f"{value['log10']:.4f}")


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

# ---------------------------------------------------------------- Omni-Fit
with tab_fit:
    st.markdown(
        "Any count N is padded up to the nearest perfect **n^d** hypercube, the "
        "whole shape is solved in one O(1) call, and the synthetic padding is "
        "then clipped back off — exactly. Both halves are O(1), so the padding "
        "is free."
    )
    f1, f2 = st.columns([1, 2])
    with f1:
        fit_family = st.selectbox("family", ["arithmetic", "geometric", "harmonic"],
                                  key="fit_family")
        fit_n = st.number_input("N (your count)", 0, 10 ** 9, 50, step=10, key="fit_n")
        fit_d = st.number_input("dimension d", 1, 8, 3, key="fit_d")
        fit_F = st.number_input("first term F", value=7.0, key="fit_F")
        if fit_family == "geometric":
            fit_r = st.number_input("ratio r", value=3.0, key="fit_r")
            fit_h = 1.0
        else:
            fit_h = st.number_input("step h", value=2.0, key="fit_h")
            fit_r = 2.0
        fit_p = st.number_input("power p", 0, 64, 3, key="fit_p")
    with f2:
        try:
            fit = omnifit(fit_family, int(fit_n), int(fit_d), F=fit_F, h=fit_h,
                          r=fit_r, p=int(fit_p))
        except (ComputeError, ZeroDivisionError, OverflowError) as exc:
            st.error(str(exc))
        else:
            shape = fit["shape"]
            st.markdown(
                f"**Shape:** {fit['N']:,} real + {shape['pad']:,} pad = "
                f"`{shape['n']}^{shape['dimension']}` = {shape['total']:,} cells"
            )
            clip = "÷" if fit["operation"] == "divide" else "−"
            st.code(
                f"A  full shape ({shape['total']:,} cells) = {fit['full']['text']}\n"
                f"B  padding     ({shape['pad']:,} terms) = {fit['pad']['text']}\n"
                f"C  answer = full {clip} pad             = {fit['answer']['text']}",
                language="text",
            )
            _show(fit["answer"])
            if fit.get("exact_match") is True:
                st.success(
                    f"Matches the direct term-by-term result exactly — "
                    f"{fit['formula_operations']} formula operations against "
                    f"{fit['direct_operations']:,} direct ones."
                )
            elif fit.get("exact_match") is False:
                st.error("Does not match the direct result: "
                         f"{fit['direct']['text']}")
            if fit["approximate"]:
                note = ""
                if "relative_error" in fit:
                    note = (" Relative error against the exact sum: "
                            f"{fit['relative_error']:.2e}.")
                st.warning(
                    "Harmonic runs have no exact closed form; this is the O(1) "
                    "midpoint series." + note +
                    " The series sharpens as the run moves away from zero — a run "
                    "starting near 1 is its worst case."
                )
            if not fit["checked_directly"] and not fit["approximate"]:
                st.caption(
                    f"N = {fit['N']:,} is far too large to brute-force for "
                    "comparison, yet the closed form answered instantly."
                )
            if fit["best_dimension"]:
                best = fit["best_dimension"]
                st.caption(
                    f"Least-padding shape for N = {fit['N']:,} is "
                    f"d = {best['dimension']} ({best['n']}^{best['dimension']}, "
                    f"pad {best['pad']:,})."
                )

# ---------------------------------------------------------------- Explorer
with tab_shape:
    st.markdown("Lay a run over a dimensional arrangement and inspect every cell.")
    e1, e2 = st.columns([1, 2])
    with e1:
        ex_family = st.selectbox("family", ["arithmetic", "geometric", "harmonic"],
                                 key="ex_family")
        ex_shape = st.text_input("dimensional arrangement", "2 x 3 x 2",
                                 key="ex_shape")
        ex_start = st.number_input("start", value=7.0, key="ex_start")
        ex_step = st.number_input(
            "ratio" if ex_family == "geometric" else "spacing",
            value=2.0 if ex_family == "geometric" else 1.0, key="ex_step")
        ex_power = st.slider("power p", 0, 10, 3, key="ex_power")
    with e2:
        try:
            shaped = explore(ex_shape, ex_family, ex_start, ex_step, int(ex_power))
        except (ComputeError, ZeroDivisionError, OverflowError) as exc:
            st.error(str(exc))
        else:
            st.markdown(f"**{shaped['label']}** over `{shaped['shape']['label']}`")
            _show(shaped["value"])
            s1, s2, s3, s4 = st.columns(4)
            s1.metric("cells X", f"{shaped['count']:,}")
            s2.metric("midpoint M", shaped["midpoint"] or "—")
            s3.metric("last term", shaped["last"])
            s4.metric("dimensions", f"{shaped['dimensions']}-D")
            st.dataframe([
                {"#": t["index"], "coordinate": str(t["coordinate"]),
                 "base term": t["base"], "contribution": t["contribution"]}
                for t in shaped["terms"]
            ])
            if shaped["terms_truncated"]:
                st.caption(f"Showing the first {len(shaped['terms']):,} of "
                           f"{shaped['count']:,} cells.")

# ---------------------------------------------------------------- Lab
with tab_lab:
    st.markdown(
        "Throw in any numbers. The difference ladder names them — arithmetic, "
        "geometric, harmonic, or honestly unstructured — and whatever law fits "
        "supplies the O(1) aggregate."
    )
    raw = st.text_input("numbers (comma or space separated)", "1, 3, 7, 14, 25",
                        key="lab_raw")
    numbers = _read_numbers(raw)
    if len(numbers) < 3:
        st.warning("Enter at least 3 numbers.")
    else:
        try:
            named = name_run(numbers)
            ladder = ladder_view(numbers)
        except ComputeError as exc:
            st.error(str(exc))
        else:
            badge = ("HYBRID " if named["kind"] == "hybrid" else "") + named["family"].upper()
            (st.success if named["structured"] else st.warning)(
                f"{badge} · depth {named['depth']} — {named['reason']}")
            st.code("\n".join(
                f"{level['label']:>24}: " + ",  ".join(level["values"])
                + (" …" if level["truncated"] else "")
                for level in ladder["levels"]), language="text")
            st.markdown(f"**{named['label']}** (closed form, O(1))")
            _show(named["closed"])
            st.caption(
                f"direct term-by-term = {named['direct']['text']} · "
                + ("exact match ✓" if named["match"] else "MISMATCH")
                + f" · ~{named['operations']} operations vs {named['terms']} direct"
            )
            if not named["structured"]:
                st.info(
                    "No ladder flattened early, so there is no structure to "
                    "exploit. The aggregate is still exact — it is just honest "
                    "O(N) work, and the predicted next term "
                    f"({named['next_term']['text']}) is extrapolation, not insight."
                )

        if len(numbers) >= 4:
            st.divider()
            st.markdown("#### Reverse-engineer the closest law")
            try:
                ranked = reverse(numbers)
            except ComputeError as exc:
                st.error(str(exc))
            else:
                st.dataframe([
                    {"candidate law": m["name"], "R²": round(m["r2"], 4),
                     "adjusted R²": round(m["adjusted_r2"], 4),
                     "params": m["params"]}
                    for m in ranked["models"]
                ])
                st.markdown(
                    f"**Best fit:** `{ranked['best']['formula']}` · "
                    f"R² = {ranked['best']['r2']:.4f} ({ranked['quality']}) · "
                    f"residual RMS {ranked['residual_rms']:.3g} "
                    f"({ranked['relative_residual'] * 100:.1f}% of signal)"
                )

        st.divider()
        st.markdown("#### Split → solve each block → recombine")
        a1, a2 = st.columns(2)
        sort_first = a1.checkbox("sort first", key="lab_sort")
        block_count = a2.slider("blocks", 1, max(1, len(numbers) // 2), 1,
                                key="lab_blocks")
        try:
            built = assemble_runs(numbers, int(block_count), bool(sort_first))
        except ComputeError as exc:
            st.error(str(exc))
        else:
            st.dataframe([
                {"block": b["block"], "terms": b["terms"],
                 "range": f"{b['low']} … {b['high']}", "law": b["law"],
                 "how": b["note"], "Σ": b["sum"]["text"]}
                for b in built["blocks"]
            ])
            (st.success if built["match"] else st.error)(
                f"Σ assembled = {built['total']['text']}"
                + (" — equals the direct total ✓" if built["match"]
                   else f" — direct total is {built['direct']['text']}")
            )
            st.caption(
                f"{built['operations']} operations vs {built['direct_operations']} "
                "direct" + (" · every block solved in O(1)"
                            if built["all_constant_time"]
                            else " · some blocks had no structure and were summed directly")
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
    raw_values = st.text_input("values (comma-separated)", "3, 5, 11, 2")
    try:
        vals = [float(x) for x in raw_values.split(",") if x.strip()]
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

    st.divider()
    st.markdown("**OmniFit warp** — irregular sample positions onto an even grid.")
    xs_raw = st.text_input("sample positions (strictly increasing)",
                           "0, 1, 4, 9, 16, 25")
    try:
        xs = [float(x) for x in xs_raw.split(",") if x.strip()]
        warp = OmniFit(xs)
        st.dataframe([{"position x": x, "grid index": warp.warp(x),
                       "unwarp(warp(x))": warp.unwarp(warp.warp(x))} for x in xs])
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
