# AGENTS.md — [Project Name]

## Project Overview

[One sentence: primary stack and any non-standard architectural choice that affects how agents should approach the codebase.]

## Tech Stack

- Language: Python 3.11
- Framework: FastAPI 0.111
- Package manager: `uv` — always use `uv run`, never `pip` directly
- Model: `claude-sonnet-4-6` via Anthropic SDK

## Key Commands

```bash
# Install
uv sync

# Dev server (hot reload)
uv run uvicorn app.main:app --reload

# Build
uv build

# Type check
uv run mypy --strict src/

# Lint + format
uv run ruff check . && uv run ruff format .

# Test (all, mocked)
uv run pytest

# Test (single)
uv run pytest tests/test_foo.py::test_bar -v

# Test (integration, real API)
uv run pytest -m integration

# Watch mode
uv run pytest-watch
```

## Non-Obvious Patterns

<!-- Document counterintuitive decisions with a one-line mechanism explanation. -->
<!-- Add rules only after observing agent failures — not speculatively. -->

- `normalizeUser()` must be called before any persistence operation — not enforced by types; skipping causes silent data corruption at the reporting layer.
- `src/lib/db.py` exposes a singleton client. Never import from the ORM directly in application code.
- Integration tests tagged `@pytest.mark.integration` are excluded from default CI — run them explicitly with `pytest -m integration`.

## Code Style

```python
# Preferred: typed, named results, no bare exceptions
async def fetch_user(user_id: str) -> Result[User, NotFoundError]:
    ...
```

- Strict typing enforced (`mypy --strict`); no `Any`, no `cast()` without a comment
- Use `Result[T, E]` from `src/lib/result.py` across module boundaries — never raise across them
- Named exports only; no wildcard imports

## Testing Rules

- Unit tests: mock all external HTTP calls via `respx`; never mock internal modules
- Tests must be deterministic: use `freezegun` for time, fixed seeds for randomness
- New features require tests before merge
- Bug fixes require a regression test demonstrating the bug before the fix

## Boundaries

### Always (no approval needed)

- Read any file, list directories, grep/glob searches
- Run `pytest`, `ruff`, `mypy`
- Create git branches and commits

### Ask First (require explicit user approval)

- Adding or upgrading packages (`uv add`)
- Deleting files
- Database schema changes
- Changes to CI/CD configuration (`.github/workflows/`)
- Changes to system prompts or tool definitions in `src/prompts/`

### Never

- Commit `.env` files or any secrets
- Force push to `main` or any protected branch
- Modify `dist/`, `build/`, or generated files under `src/generated/`
- Remove or bypass lint/typecheck steps
- Call real LLMs in unit tests — use fixtures or mocks

## Known Issues

<!-- Document active bugs or environmental quirks that would mislead an agent. -->
<!-- Remove entries when issues are resolved. -->

- `docker-compose up` requires `COMPOSE_DOCKER_CLI_BUILD=1` on Apple Silicon — set it in `.env`
