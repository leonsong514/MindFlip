"""Stdio IPC entrypoint.

Run as `python -m app.ipc_main`. Lives in its own module to avoid the
RuntimeWarning that Python emits when a package's `__init__` imports
from a module that is then re-imported as the program entry point.
"""

from __future__ import annotations

from app.api import handle_line
from app.api.ipc import _emit

import sys


def main() -> int:
    line = sys.stdin.readline()
    _emit(handle_line(line))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
