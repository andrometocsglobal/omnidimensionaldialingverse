"""Make the repo root importable so `from server.app import app` works.

`python -m pytest` happens to add the CWD to sys.path, but a bare `pytest`
(what CI runs) does not — without this, the API tests fail to collect.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
