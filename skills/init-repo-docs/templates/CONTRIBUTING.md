# Contributing to [Project Name]

Thank you for your interest in contributing. We welcome bug fixes, features, docs, tests, and benchmark improvements.

**We do NOT accept:** re-implementations of core design, support questions as issues, or PRs without a linked issue.

---

## Code of Conduct

This project follows the [Contributor Covenant](https://www.contributor-covenant.org/version/2/1/code_of_conduct/). Violations can be reported to `conduct@domain.com`.

---

## Legal

### Developer Certificate of Origin (DCO)

All commits must be signed off:

```bash
git commit -s -m "feat: add streaming support"
```

By signing off you certify that you authored or have the right to submit the contribution under the project's license. See [developercertificate.org](https://developercertificate.org/).

> **For corporate projects:** Replace the DCO section with a CLA requirement and link to [CLA Assistant](https://cla-assistant.io/).

**Note:** Contributions must not embed or distribute proprietary model weights.

---

## Development Setup

**Prerequisites:** Python 3.11+, Docker 24+

```bash
git clone https://github.com/org/repo
cd repo
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env          # fill in API keys (see table in README)
pre-commit install            # install git hooks
```

Most tests use mocked LLM responses. Integration tests (real API calls) require `ANTHROPIC_API_KEY` with Sonnet access.

---

## Common Commands

| Task | Command |
|------|---------|
| Run all tests | `pytest` |
| Run integration tests | `pytest -m integration` |
| Run single test | `pytest tests/test_foo.py::test_bar -v` |
| Lint | `ruff check .` |
| Format | `ruff format .` |
| Type check | `mypy --strict src/` |
| Start dev server | `uvicorn app.main:app --reload` |
| Build Docker image | `docker build -t repo:dev .` |

---

## Commit Convention

We use [Conventional Commits](https://www.conventionalcommits.org/).

```
type(scope): imperative description (max 72 chars)

Body: explain the WHY, not the what. Reference issue with "Closes #123".

BREAKING CHANGE: describe what breaks and migration path.
```

**Allowed types:** `feat` · `fix` · `docs` · `refactor` · `test` · `chore` · `perf` · `ci`

**AI-era scope:** use `model` for commits that change which model is called or how prompts are structured:
```
feat(model): switch default to claude-sonnet-4-6
```

---

## Branching Strategy

We use **GitHub Flow** (feature branches → `main`):

- `feat/short-description`
- `fix/issue-123`
- `chore/update-deps`
- `docs/improve-readme`

Never commit directly to `main`.

---

## Pull Request Process

1. Open an issue first for anything beyond a typo fix.
2. Fork, create a branch, make your changes.
3. Ensure CI passes: `pytest && ruff check . && mypy --strict src/`.
4. Open a PR using the [PR template](.github/pull_request_template.md). Required fields:
   - What does this PR do?
   - How was it tested?
   - Does it require a docs update?
   - Breaking changes? (yes/no)
   - **For AI projects:** Does this change prompt behavior or model selection? If yes, include before/after example runs.
5. Maintainers aim to review within **7 business days**.
6. PRs are merged via squash merge.

---

## Testing Requirements

- All new features require tests before merge.
- Bug fixes require a regression test that fails before the fix.
- Code coverage floor: **80%** on new code.
- Unit tests: use mocked LLM responses (never call real APIs in default test run).
- Integration tests: tag with `@pytest.mark.integration` — excluded from CI by default.
- Tests must be deterministic: no `datetime.now()`, no unfixed random seeds.

---

## Code Style

We use `ruff` for linting and formatting. Run before every push:

```bash
ruff check . && ruff format .
```

- Type hints required on all public functions (`mypy --strict` must pass).
- Pre-commit hook enforces this automatically after `pre-commit install`.

---

## Reporting Issues

**Bugs:** use the [GitHub issue template](.github/ISSUE_TEMPLATE/bug_report.md). Required: version, OS, reproduction steps, expected vs. actual output.

**Security vulnerabilities:** NEVER via public issues. Email `security@domain.com` or open a [GitHub private advisory](https://github.com/org/repo/security/advisories/new).

**Feature requests:** open an issue first; explain the use case before writing code.

---

## Prompt & Model Change Policy

Any PR modifying system prompts, tool definitions, or model parameters must include:

- Before/after example runs in the PR description.
- Benchmark results if changing the default model (see `evals/README.md`).

Model upgrades require equal or better performance on the eval suite in `evals/`. Eval contributions are first-class and welcome.

**Maintain `AGENTS.md`:** when adding tools, changing build commands, or updating conventions, update `AGENTS.md` as part of the same PR. It is code, not documentation.
