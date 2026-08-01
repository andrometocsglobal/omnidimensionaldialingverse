"""Streamlit app tests — the script is actually executed, not just imported.

`streamlit run` only fails at request time, so a broken widget or a bad
dataframe column would otherwise reach the deployed app unnoticed.
"""

import pytest

pytest.importorskip("streamlit")

from streamlit.testing.v1 import AppTest  # noqa: E402

APP = "streamlit_app.py"


@pytest.fixture(scope="module")
def app():
    return AppTest.from_file(APP, default_timeout=180).run()


def test_app_runs_without_raising(app):
    assert not app.exception, [e.value for e in app.exception]
    assert not app.error, [e.value for e in app.error]


def test_every_tab_renders(app):
    assert len(app.tabs) == 7
    assert app.title[0].value == "Omnidimensional"


def test_omnifit_and_lab_tabs_produce_results(app):
    """The fit pipeline and the sequence lab must actually run in the app."""
    blocks = [c.value for c in app.code]
    assert any("full shape" in b and "answer = full" in b for b in blocks)
    assert any("difference 1" in b for b in blocks)   # the lab's ladder


def test_default_view_shows_an_exact_result(app):
    # defaults are arithmetic, n = 100, a = 1, d = 1  ->  sum = 5050
    assert any("5050" in block.value for block in app.code)
    assert any(m.value == "exact ✓" for m in app.metric)


def test_speed_table_columns_stay_numeric(app):
    """Mixing floats with a placeholder string used to break Arrow encoding."""
    # Several tabs render tables now, so pick the one by its columns.
    speed = next((f.value for f in app.dataframe
                  if "closed_form_s" in getattr(f.value, "columns", [])), None)
    assert speed is not None, "expected the O(1) vs O(n) table to render"
    for column in ("closed_form_s", "brute_force_s"):
        series = speed[column].dropna()
        assert all(isinstance(v, float) for v in series), column


def test_geometric_selection_recomputes(app):
    at = AppTest.from_file(APP, default_timeout=180).run()
    at.selectbox[0].select("geometric").run()
    at.number_input[0].set_value(64).run()
    assert not at.exception, [e.value for e in at.exception]
    assert any(str(2 ** 64 - 1) in block.value for block in at.code)


def test_runaway_input_is_refused_not_crashed(app):
    at = AppTest.from_file(APP, default_timeout=180).run()
    at.selectbox[0].select("geometric").run()
    at.number_input[0].set_value(10 ** 9).run()
    assert not at.exception, [e.value for e in at.exception]
    assert any("digits" in e.value for e in at.error)
