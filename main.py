from __future__ import annotations

import os
import sys
from pathlib import Path


def _find_repo_venv_python(root_dir: Path) -> Path | None:
    for candidate in (root_dir / ".venv" / "bin" / "python", root_dir / ".venv" / "Scripts" / "python.exe"):
        if candidate.exists():
            return candidate
    return None


def _maybe_reexec_into_repo_venv() -> None:
    # Prefer the repo venv so `python main.py ...` works from a mismatched shell interpreter.
    if os.environ.get("TRIP_OPERATOR_SKIP_VENV_REEXEC") == "1":
        return

    root_dir = Path(__file__).resolve().parent
    venv_python = _find_repo_venv_python(root_dir)
    if venv_python is None:
        return

    current_python = Path(sys.executable).resolve()
    if current_python == venv_python.resolve():
        return

    os.environ["TRIP_OPERATOR_SKIP_VENV_REEXEC"] = "1"
    os.execv(str(venv_python), [str(venv_python), str(Path(__file__).resolve()), *sys.argv[1:]])


if __name__ == "__main__":
    _maybe_reexec_into_repo_venv()

from trip_operator.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
