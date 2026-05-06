---
name: conventional-commits
description: Rules for writing git commit messages using Conventional Commits (without scope). Apply when creating commits, suggesting commit messages, or reviewing commit history.
---

# Conventional Commits (No Scope)

## Format

```
<type>: <description>
```

- **No parenthesised scope** — always `type: description`, never `type(scope): description`
- Description starts with **lowercase** letter
- Description is a short imperative sentence (≤ 72 chars for the full first line)
- No period at the end

## Allowed Types

| Type       | When to use                                             |
| ---------- | ------------------------------------------------------- |
| `feat`     | New feature or capability                               |
| `fix`      | Bug fix                                                 |
| `chore`    | Maintenance, deps, tooling (no production code)         |
| `docs`     | Documentation only                                      |
| `refactor` | Code change that neither fixes a bug nor adds a feature |
| `style`    | Formatting, whitespace, missing semicolons              |
| `perf`     | Performance improvement                                 |
| `test`     | Adding or updating tests                                |
| `ci`       | CI/CD configuration                                     |
| `build`    | Build system or external dependency changes             |
| `revert`   | Reverts a previous commit                               |

## Examples

```
feat: add user authentication endpoint
fix: handle null reference in payment processor
chore: update dependencies to latest stable versions
docs: document API rate limiting behaviour
refactor: extract validation logic into separate module
style: fix inconsistent indentation in config files
perf: add database index for user lookup queries
test: add integration tests for checkout flow
ci: add automated security scanning to pipeline
build: bump minimum Node.js version to 20
revert: undo payment gateway config change
```

## Multi-line Body (optional)

```
feat: add clipboard integration for SSH sessions

Use OSC52 escape sequence to enable clipboard copy
when running Neovim over SSH without X11 forwarding.
```

- Blank line between subject and body
- Body wraps at 72 characters
- Use body to explain **what** and **why**, not how

## Breaking Changes

Append `!` before the colon:

```
feat!: migrate authentication to OAuth 2.0
```

Or add a `BREAKING CHANGE:` footer in the body.

## Rules

1. **One commit per logical change** — don't mix unrelated changes
2. **Never use a scope in parentheses** — write `feat:` not `feat(auth):`
3. **Never push to remote** without explicit user approval
4. **Stage only relevant files** before committing
5. When in doubt, prefer `chore` for non-user-facing changes
6. The commit must not have more than 65 characters
