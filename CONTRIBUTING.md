# Contributing to opencode-config

## Welcome & Scope

This repository manages the global opencode configuration: AI agent personas, the `ocx` CLI, LiteLLM proxy configs, skills, and budget tiers. Contributions touch configuration files, Python CLI code, and agent/skill Markdown definitions.

## Code of Conduct

Be respectful and constructive. This is a personal configuration repo — keep discussions focused on technical improvements.

## Legal (DCO)

All commits must be signed off:

```bash
git commit -s -m "feat: your message"
```

By signing off, you certify that you wrote the code and have the right to contribute it under the project's license ([Developer Certificate of Origin v1.1](https://developercertificate.org/)).

## Development Setup

**Prerequisites:** Python 3.10+, [`uv`](https://docs.astral.sh/uv/)

```bash
git clone <repo-url> ~/.config/opencode
cd ~/.config/opencode

# Install ocx CLI (editable, no reinstall needed for src/ changes)
uv tool install --editable .

# Verify
which ocx && ocx --help

# Install Python dev deps and run tests
uv run pytest
```

## Common Commands

```bash
ocx --help                        # all subcommands
ocx agents sync                   # sync primary agents to ~/.claude/agents/
ocx agents count                  # count installed agents
ocx tier list                     # list all budget tiers
ocx tier set med                  # switch to medium tier
ocx litellm up                    # start LiteLLM proxy
ocx litellm down                  # stop proxy
uv run pytest                     # run full test suite
uv run pytest tests/test_cli.py   # single test file
```

## Commit Convention

This project uses [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add new ocx subcommand
fix: correct tier eligibility check
docs: update AGENTS.md with correct agent count
refactor: extract tier logic to tier_apply module
test: add guard test for provider routing
chore: bump litellm proxy image version
```

Use `model` scope when changing default model assignments:

```
feat(model): switch default orchestrator to claude-sonnet-4-6
```

## Branching Strategy

- `main` — always deployable; direct pushes for solo work are fine
- Feature branches for significant changes: `feat/tier-copilot-blend`
- Hotfixes: `fix/provider-eligibility`

## Pull Request Process

1. Link or describe the motivation in the PR description
2. Run `uv run pytest` locally — all tests must pass
3. Run `ocx agents sync --check` if you touched any agent or skill file
4. Update `AGENTS.md` if you added/changed a command, agent, or skill

## Testing Requirements

- Tests live in `tests/`; pytest discovers them automatically
- Real LLM integration tests (if any) must be marked `@pytest.mark.integration` and are not run in default CI
- Add a guard test for any new tier routing contract or provider eligibility rule

## Code Style & Linting

- Follow the Python CLI Style Guide in `AGENTS.md` (logging via `oc.log`, subprocess via `oc.proc`, paths via `oc.paths`)
- No raw `print`, no `os.system`, no hardcoded `~/.config/opencode` strings
- Every write operation should check before acting and warn if already done (idempotency)

## Agent & Skill File Changes

- **Agent files** (`agents/*.md`): after editing a primary agent, run `ocx agents sync`
- **Skill files** (`skills/*/SKILL.md`): set `tool:` frontmatter (`shared`, `opencode-only`, `claude-only`)
- **Do NOT edit** `~/.claude/agents/*.md` or `~/.claude/skills/*.md` directly — they are generated mirrors

PRs that modify prompt/tool definitions in agent or skill files must include a before/after example showing the behavioral difference.

## Tier & Config Changes

- Tier profiles live in `tiers/<name>.yaml` — edit these, not the generated files
- `oh-my-openagent.jsonc` and `litellm/config.yaml` model/agent blocks are overwritten by `ocx tier set`
- After changing tiers: `ocx litellm down && ocx litellm up`

## Reporting Bugs & Security

- Bugs: open a GitHub issue with reproduction steps
- Security issues: **do not file public issues** — email `igorsoaresalves@gmail.com` directly

## Feature Requests

Open a GitHub issue describing the use case and expected behavior. For significant changes, consider writing an RFC using the `skills/rfc-template/SKILL.md` template.
