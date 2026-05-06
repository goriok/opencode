---
name: bug-fix
description: Guidelines for diagnosing and fixing bugs during feature implementation. Apply when the user reports an error, unexpected behaviour, test failure, or asks to fix/debug code.
---

# Bug Fix — Feature Implementation

## When to Activate

Activate when the user:

- Reports an error, exception, or unexpected behaviour
- Asks to "fix", "debug", or "investigate" something
- Shows a failing test, LSP diagnostic, or runtime error
- Describes behaviour that doesn't match intent

## Diagnosis First — Never Fix Blindly

Always gather context before editing:

1. **Run `get_diagnostics`** on the affected file(s) — errors take priority over warnings
2. **Read the full file** (or the relevant section) to understand surrounding logic
3. **Check related files** — imports, dependencies, callers, or config that the bug touches
4. **Reproduce mentally** — trace the execution path that leads to the failure

Only start editing after the root cause is clear.

## Fix Workflow

```
1. get_diagnostics  →  identify all errors/warnings
2. read_file        →  understand context around the bug
3. grep_search      →  find related files / callers if needed
4. insert_edit_into_file  →  apply minimal, targeted fix
5. get_diagnostics  →  confirm errors are gone
6. run_command      →  run tests or the relevant command to validate
```

Repeat steps 4–6 until the file is clean. Stop after **3 failed iterations** — surface the blocker to the user instead of continuing.

## Fix Rules

| Rule                | Detail                                                                       |
| ------------------- | ---------------------------------------------------------------------------- |
| **Minimal scope**   | Fix only the code that causes the bug; do not refactor unrelated logic       |
| **Preserve style**  | Match indentation, naming conventions, and patterns of the existing file     |
| **No new deps**     | Do not add new libraries, plugins, or modules without explicit user approval |
| **No side effects** | A bug fix must not change observable behaviour in unrelated code paths       |
| **One bug per fix** | If multiple bugs are found, fix them sequentially and confirm each one       |

## Validation Checklist

After every fix, verify:

- [ ] `get_diagnostics` returns no new errors on the edited file
- [ ] Related files that import/call the fixed code still pass diagnostics
- [ ] If tests exist, run them with `run_command` and confirm they pass
- [ ] The original symptom (error message / wrong output) no longer reproduces

## Communicating Results

- State the **root cause** in one sentence before showing the fix
- If multiple issues were found, list them briefly before addressing each
- If the fix required a trade-off or assumption, call it out explicitly
- If 3 iterations failed, summarise what was tried and ask the user for more context

## Anti-patterns

- ❌ Editing a file without reading it first
- ❌ Suppressing errors with `pcall` / `try-catch` without understanding why they occur
- ❌ Changing function signatures or interfaces to "work around" a bug
- ❌ Adding `print` / `console.log` debug statements and leaving them in
- ❌ Fixing a symptom without understanding the cause

---

## Documentation Standards

If a bug report or post-fix summary document is produced, it MUST follow these rules:

**Format & Location**
- File format: `.md` (Markdown only)
- Save path: `docs/bug-reports/` relative to the project root

**Frontmatter (mandatory)**

```yaml
---
title: "Bug Report: [short description]"
date: YYYY-MM-DD
type: bug-report
status: draft | resolved
authors: []
tags: []
---
```

- `tags` — include affected file/module, language, and error category
- When searching for prior bug reports, grep `type: bug-report` and `tags` first

**Diagrams**

If a diagram is needed to explain the execution path or root cause, use Mermaid strict mode:

````markdown
```mermaid
%%{init: {"theme": "default"}}%%
%% strict mode — no implicit node creation %%
flowchart LR
    A --> B
```
````

No ASCII art diagrams.
