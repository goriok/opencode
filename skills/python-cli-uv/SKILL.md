---
name: python-cli-uv
description: Build a typed, tested Python CLI installable via `uv tool`. Apply when the user asks to create a CLI, replace a Taskfile/Makefile/shell scripts with Python, or build an automation tool distributable as a uv tool.
tool: claude-only
---

# Python CLI with uv tool

## When to Activate

Activate when the user:

- Asks to build a CLI, automation tool, or script collection in Python
- Wants to replace a Taskfile, Makefile, justfile, or shell scripts with a proper CLI
- Says "uv tool", "installable CLI", "binary in PATH", or "mcx-style"
- Wants cluster, infra, or project automation that lives in a repo subdirectory

## Project Layout

Always use a dedicated subdirectory (not the repo root):

```
<cli-name>/
├── pyproject.toml          # [project.scripts] <name> = "<pkg>.cli:app"
├── .gitignore              # __pycache__/, .venv/, dist/, *.egg-info/
├── README.md               # install + command reference
├── src/<pkg>/
│   ├── __init__.py
│   ├── cli.py              # Typer root — registers subgroups only, no logic
│   ├── shell.py            # ONLY place that calls subprocess.run
│   ├── config.py           # loads .env + <name>.toml; pure data, no I/O side effects
│   ├── context.py          # get_config() singleton; walks CWD→parents for <name>.toml
│   └── commands/
│       ├── __init__.py
│       └── <domain>.py     # one file per command group (deploy, cluster, logs…)
└── tests/
    ├── __init__.py
    └── test_*.py
```

Config files at the **repo root** (not inside the subdir):

```
<name>.toml     # app/tool declarations (versionable, never secrets)
.env            # CLUSTER_HOST, API_KEY, etc. (gitignored)
bootstrap.sh    # ./bootstrap.sh → uv tool install --from ./<cli-name> <name> --force
```

## pyproject.toml

```toml
[project]
name = "<cli-name>"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "typer>=0.12",
    "rich>=13",
    "python-dotenv>=1.0",
]

[project.scripts]
<name> = "<pkg>.cli:app"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/<pkg>"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "--tb=short"

[tool.coverage.run]
source = ["src/<pkg>"]
omit = ["src/<pkg>/cli.py"]   # cli.py is pure wiring; exclude from coverage

[tool.coverage.report]
fail_under = 90
```

## Architecture Rules

| Layer | Rule |
|---|---|
| `cli.py` | Only `app.add_typer(...)` calls — zero business logic |
| `shell.py` | Single `run(argv, *, stream, dry_run)` function; all subprocess calls go through it |
| `config.py` | Pure dataclasses + `load_config(repo_root, _environ)` — `_environ` injected for tests |
| `context.py` | `get_config()` singleton that finds `<name>.toml` by walking up from CWD |
| `commands/<domain>.py` | Import `get_config` and `shell` from their modules; no direct subprocess calls |

**Never** call `subprocess.run` outside `shell.py`. This makes every command testable by mocking one function.

## shell.py — canonical implementation

```python
import subprocess, sys
from typing import Optional

def run(argv: list[str], *, stream: bool = True, dry_run: bool = False) -> Optional[subprocess.CompletedProcess]:
    if dry_run:
        return None
    kwargs: dict = {"check": True}
    if not stream:
        kwargs["capture_output"] = True
    try:
        return subprocess.run(argv, **kwargs)
    except subprocess.CalledProcessError as exc:
        sys.exit(exc.returncode)
```

## config.py — canonical pattern

```python
from __future__ import annotations
import os, tomllib
from dataclasses import dataclass, field
from pathlib import Path
from dotenv import dotenv_values

class ConfigError(Exception): pass

@dataclass
class Config:
    # cluster/tool-level fields
    ...
    def item(self, name: str) -> "ItemConfig":   # validate + fetch by name
        for i in self.items:
            if i.name == name: return i
        raise ConfigError(f"unknown item '{name}' — check <name>.toml")

def load_config(repo_root: Path, _environ: dict | None = None) -> Config:
    toml_path = repo_root / "<name>.toml"
    if not toml_path.exists():
        raise ConfigError(f"<name>.toml not found at {toml_path}")
    env_from_file = dotenv_values(repo_root / ".env") if (repo_root / ".env").exists() else {}
    env = {**env_from_file, **(dict(os.environ) if _environ is None else _environ)}
    # validate required keys, parse toml, return Config(...)
```

## Mutating vs Read-only Commands

| Type | Behaviour |
|---|---|
| Read-only (`get`, `logs`, `status`, `ssh`) | Call `shell.run()` immediately, no prompt |
| Mutating (`apply`, `create`, `delete`, `restart`) | Print the command, `typer.confirm("Proceed?")`, accept `--yes/-y` to skip |

```python
@app.command("cluster")
def cluster(yes: bool = typer.Option(False, "--yes", "-y")):
    cmd = ["kubectl", "apply", "-k", "k8s/"]
    if not yes:
        console.print(f"[yellow]Will run:[/yellow] {' '.join(cmd)}")
        if not typer.confirm("Proceed?"): raise typer.Abort()
    shell.run(cmd)
```

## TDD — Mandatory Discipline

Every command follows **red → green → refactor** strictly.

Tests never touch real subprocesses — mock `shell.run` at the command module level:

```python
# Pattern for all command tests
def test_deploy_calls_correct_argv():
    with patch("myapp.commands.deploy.get_config", return_value=FAKE_CFG), \
         patch("myapp.commands.deploy.shell") as mock_shell:
        result = runner.invoke(app, ["deploy", "image", "myapp"])
    assert result.exit_code == 0
    mock_shell.run.assert_called_once_with(["rsync", "-az", ...])
```

Test order per command:
1. Parser test — command exists, flags are correct, help renders
2. Composition test — exact `argv` sequence dispatched to `shell.run`
3. Config test — `load_config` resolves `.env` + toml correctly; missing keys raise `ConfigError`
4. Gate test — mutating command does NOT call `shell.run` when user declines

Always pass `_environ={}` in config tests to prevent `os.environ` bleed.

## bootstrap.sh

```bash
#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
echo "==> Checking uv..."
if ! command -v uv &>/dev/null; then
  echo "uv not found. Install: https://docs.astral.sh/uv/getting-started/installation/"
  exit 1
fi
echo "==> Installing <name>..."
uv tool install --from "$REPO_ROOT/<cli-dir>" <name> --force
echo ""
echo "Done. Run '<name> --help' to get started."
```

## <name>.toml — declarative config

Declare all targets (apps, environments, services) so adding a new one never requires Python edits:

```toml
[[apps]]
name = "my-app"
source_path = "../my-app"
kustomize_path = "k8s/apps/my-app"
rsync_excludes = [".venv/", ".git/", "__pycache__/"]
```

## Smoke Verification Sequence

After implementation:

1. `uv run --with pytest pytest -v` — all tests green
2. `uv tool install --from ./<cli-dir> <name> --force` (or `./bootstrap.sh`)
3. `<name> --help` — all subcommands listed
4. `<name> config show` — resolved config printed correctly
5. One read-only command against the real target — confirms subprocess wiring

## Anti-patterns

- ❌ Calling `subprocess.run` anywhere except `shell.py`
- ❌ Business logic in `cli.py` — it is only a router
- ❌ Using `os.environ` directly in `config.py` — inject via `_environ` for testability
- ❌ Hardcoding app names in Python — put them in `<name>.toml`
- ❌ Merging mutating and read-only commands without a confirmation gate
- ❌ Committing `__pycache__/`, `.venv/`, `uv.lock` without a `.gitignore`
- ❌ Skipping the red phase — always confirm the test fails before implementing
