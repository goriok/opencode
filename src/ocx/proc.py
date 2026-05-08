import shutil
import subprocess
import sys
from pathlib import Path

from ocx import log


def run(
    cmd: list[str],
    *,
    cwd: Path | None = None,
    check: bool = True,
    capture: bool = False,
) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        cwd=cwd,
        check=check,
        capture_output=capture,
        text=True,
    )


def run_capture(cmd: list[str], *, cwd: Path | None = None) -> str:
    result = run(cmd, cwd=cwd, capture=True)
    return result.stdout.strip()


def stream(cmd: list[str], *, cwd: Path | None = None) -> None:
    """Run a command inheriting stdin/stdout/stderr (for interactive or streaming commands)."""
    subprocess.run(cmd, cwd=cwd, check=True)


def require(tool: str) -> str:
    path = shutil.which(tool)
    if path is None:
        log.error(f"'{tool}' not found — please install it and retry")
    return path  # type: ignore[return-value]
