# omnidimensional

Exact, constant-time closed forms for the **four progression families** —
arithmetic (AP), geometric (GP), harmonic (HP), and **OmniFit** — plus the
generalized **power mean**, a harmonic **midpoint**, and an **exact verifier**.
Ships a **Streamlit** app (flagship), a **FastAPI** server, and a zero-build
**React** client that stay in sync in real time.

> The math is classical (Nicomachus → Faulhaber → Knuth). The contribution is
> unification, exact machine-verification, and one scale-invariant interface.
> See [`RESEARCH.md`](RESEARCH.md).

## Install

Requires Python **3.10+** (the Streamlit and FastAPI extras set the floor; the
core itself is pure standard library).

```bash
pip install omnidimensional            # from PyPI once published
# or, from source:
pip install .                          # core (pure stdlib, zero deps)
pip install ".[app]"                   # + Streamlit
pip install ".[server]"                # + FastAPI/uvicorn
pip install ".[dev]"                   # + pytest
pip install ".[app,server,dev]"        # everything, to run the full test suite
```

## Quickstart (Python)

```python
import omnidimensional as od

od.Geometric(1, 2).sum(64)            # 18446744073709551615  (2**64 - 1), exact
od.power_sum_closed(100, 2)           # Fraction(338350, 1), via Faulhaber, O(1) in n
od.omnidimensional_midpoint(2, 3)     # Fraction(12, 5) harmonic midpoint
od.power_mean_spectrum([3, 5, 11, 2]) # min→harmonic→…→max
od.verify("power", 1000, p=4)         # {'exact_match': True, ...}

od.compute("geometric", 1_000_000, a=1, r=2)
# one call used by every front end: result, digit count, cross-check, limits
```

CLI:

```bash
omnidimensional sum power --n 100 --p 2
omnidimensional verify power --n 100 --p 2
omnidimensional midpoint 2 3 --family harmonic
omnidimensional spectrum 3 5 11 2
```

## Run the apps

**Streamlit (flagship):**

```bash
pip install ".[app]"
streamlit run streamlit_app.py
```

**FastAPI server + React client — one process serves both:**

```bash
pip install ".[server]"
uvicorn server.app:app --reload --port 8000
# open http://localhost:8000/app
```

The React page in `web/` is mounted at `/app`, so there is no second server to
start. Open it in two tabs and compute in one — the other updates live over the
WebSocket. That is the server/client sync.

If you would rather host the client separately, it is still a single static
file; serve `web/` anywhere and point the "API base" field at your server.

### API

| Endpoint | Purpose |
| --- | --- |
| `POST /api/compute` | evaluate a family sum; broadcasts to every WS client |
| `GET /api/verify` | closed form vs term-by-term reference |
| `GET /api/families` | the closed form for each family |
| `GET /api/spectrum` | power-mean spectrum M_p |
| `GET /api/midpoint` | harmonic/arithmetic/geometric/quadratic midpoint |
| `GET /api/health` | liveness + connected client count |
| `WS /ws` | live sync feed |

## What "exact" and "O(1)" actually mean here

These claims are load-bearing, so the code is explicit about their edges:

- **Closed forms are O(1) in n, but their results are not O(1) in size.**
  `Geometric(1, 2).sum(10**6)` is an exact integer with 301,030 digits. It is
  computed exactly, then *rendered* in scientific notation —
  `omnidimensional.render` bounds the display, never the value. Requests whose
  result would exceed `MAX_RESULT_DIGITS` are refused with a reason rather than
  exhausting memory.
- **The verifier spot-checks.** Cross-checking a closed form against a
  term-by-term sum at n = 10¹² would defeat the point, so the reference runs at
  a capped `n_verified` and the report sets `spot_checked` instead of implying
  the full request was verified.
- **Harmonic sums have no elementary closed form**, and the package says so.
  Below `MAX_EXACT_HARMONIC` you get an exact `Fraction`; above it, an O(1)
  digamma approximation flagged `approximate: true`. `verify("harmonic", ...)`
  compares the two — which is a real check, unlike comparing HP against itself.

All limits live in `omnidimensional.limits`, so the CLI, the API and the
Streamlit app refuse exactly the same inputs.

## Tests

```bash
pip install ".[app,server,dev]"
pytest -q
```

35 tests covering the exact math, the digamma approximation, huge-value
rendering, the REST + WebSocket API, and the Streamlit app itself (executed via
`streamlit.testing.v1.AppTest`, not merely imported).

## Deploy

- **Streamlit Community Cloud (primary):** push this repo to GitHub →
  share.streamlit.io → New app → main file `streamlit_app.py`, requirements
  `requirements.txt`. Done.
- **FastAPI server + client:** any Python host (Render / Railway / Fly). Start
  command `uvicorn server.app:app --host 0.0.0.0 --port $PORT` — see
  [`Procfile`](Procfile). This serves the React client too, at `/app`.
- **React client standalone:** `web/index.html` is a single static file — host
  on GitHub Pages / Netlify, and set the "API base" field to your server URL.

## Layout

```
src/omnidimensional/
  families.py     AP / GP / HP / OmniFit
  faulhaber.py    exact power sums + Bernoulli numbers
  approx.py       digamma, O(1) harmonic approximation
  power_mean.py   generalized power mean M_p
  midpoint.py     the midpoint operator
  render.py       safe display of astronomically large exact values
  limits.py       shared input limits, one source of truth
  engine.py       the compute path every front end calls
  verify.py       closed form vs reference, exact
  cli.py          command line entry point
streamlit_app.py  flagship interactive app
server/app.py     FastAPI REST + WebSocket, and serves web/ at /app
web/index.html    zero-build React client (CDN)
tests/            core, server and Streamlit suites
RESEARCH.md       the four-family research note
```

## License

MIT — see [`LICENSE`](LICENSE).
