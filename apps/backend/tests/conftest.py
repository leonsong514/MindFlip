"""Test configuration: ensure the project root is importable.

Tests run with the current working directory set to apps/backend/ (or its
parent when invoked via the recommended `pytest` invocation). We do not
rely on a particular layout; the conftest adds the package root to
sys.path so that `import app...` works regardless of CWD.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))