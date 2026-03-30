---
name: tdd
description: Guidelines for Test Driven Development. Apply when the user asks to implement a feature or fix a bug using TDD, or mentions "test first", "red green refactor", or "write tests".
---

# Test Driven Development

## When to Activate

Activate when the user:

- Asks to use TDD, "test first", or "red green refactor"
- Requests a feature and mentions writing tests before implementation
- Asks to fix a bug and wants a regression test first
- Says "write the test", "start with the test", or "prove it fails"

When combined with the **bug-fix** skill: write a failing test that reproduces the bug before applying the fix.

## The TDD Cycle

```
  ┌─────────┐     ┌─────────┐     ┌───────────┐
  │  🔴 RED │ ──▶ │ 🟢 GREEN│ ──▶ │ 🔵 REFACTOR│
  └─────────┘     └─────────┘     └───────────┘
       ▲                                 │
       └─────────────────────────────────┘
```

1. **Red** — Write a test that describes the expected behaviour. Run it. It **must fail**.
2. **Green** — Write the **minimum** code to make the test pass. No more.
3. **Refactor** — Improve the code (remove duplication, rename, extract). Tests must stay green.

Repeat for each small increment of functionality.

## Workflow

```
RED phase:
1. Understand the requirement
2. Create/open the test file (see conventions below)
3. Write ONE failing test — assert the expected behaviour
4. run_command  →  confirm the test FAILS (red)

GREEN phase:
5. Write the minimal production code to pass the test
6. run_command  →  confirm the test PASSES (green)
7. get_diagnostics  →  ensure no errors in both files

REFACTOR phase:
8. Improve code quality — extract, rename, simplify
9. run_command  →  confirm all tests still pass
10. get_diagnostics  →  clean diagnostics
```

Repeat steps 1–10 for each new behaviour.

## Rules

| Rule                                  | Detail                                                                                      |
| ------------------------------------- | ------------------------------------------------------------------------------------------- |
| **One test at a time**                | Never write multiple failing tests before making one pass                                   |
| **Minimal green**                     | Write only enough code to pass the current test — resist over-engineering                   |
| **Run after every change**            | Every edit must be followed by a test run                                                   |
| **No test skipping**                  | Never use `skip`, `pending`, or comment out a failing test to move forward                  |
| **Tests are first-class**             | Test code follows the same quality standards as production code                             |
| **Descriptive names**                 | Test names describe behaviour, not implementation: `test_returns_error_when_input_is_empty` |
| **No production code without a test** | If there is no failing test demanding it, don't write it                                    |
| **Refactor only on green**            | Never refactor while tests are red                                                          |

## Test File Conventions

| Language | Test framework              | Test location             | Naming pattern   | Template                                             |
| -------- | --------------------------- | ------------------------- | ---------------- | ---------------------------------------------------- |
| Lua      | `busted` / `plenary.busted` | `tests/` or `spec/`       | `*_spec.lua`     | [templates/lua-spec.lua](templates/lua-spec.lua)     |
| Python   | `pytest`                    | `tests/`                  | `test_*.py`      | [templates/python-test.py](templates/python-test.py) |
| Go       | `testing`                   | same package              | `*_test.go`      | [templates/go-test.go](templates/go-test.go)         |
| Ruby     | `rspec`                     | `spec/`                   | `*_spec.rb`      | —                                                    |
| JS/TS    | `vitest` / `jest`           | `__tests__/` or colocated | `*.test.{js,ts}` | —                                                    |

If the project already has tests, **follow the existing convention** — check for test directories and patterns before creating new files.

## Test Run Commands

| Language | Command                                                          |
| -------- | ---------------------------------------------------------------- |
| Lua      | `busted` or `nvim --headless -c "PlenaryBustedDirectory tests/"` |
| Python   | `pytest` or `pytest path/to/test_file.py::test_name`             |
| Go       | `go test ./...` or `go test -run TestName ./path/`               |
| Ruby     | `bundle exec rspec` or `rspec spec/path_spec.rb`                 |
| JS/TS    | `npx vitest run` or `npx jest --testPathPattern=path`            |

Prefer running **the single test** during Red/Green. Run the **full suite** after Refactor.

## Bug Fix Integration

When fixing a bug with TDD:

1. **Reproduce** — understand the bug (read file, diagnostics)
2. **Red** — write a test that exposes the bug (it must fail, proving the bug exists)
3. **Green** — fix the bug with minimal code (test passes)
4. **Refactor** — clean up if needed
5. The regression test stays in the suite permanently

## Example

User: "implement a function that reverses a string, use TDD"

```
🔴 RED:
  → Create test file with: assert reverse("hello") == "olleh"
  → Run tests → FAIL (function doesn't exist)

🟢 GREEN:
  → Implement: function reverse(s) return string.reverse(s) end
  → Run tests → PASS

🔵 REFACTOR:
  → No duplication to remove — move on

🔴 RED (next increment):
  → Add test: assert reverse("") == ""
  → Run tests → PASS (already works — skip to next)

🔴 RED:
  → Add test: assert reverse(nil) returns error or empty
  → Run tests → FAIL

🟢 GREEN:
  → Add nil guard → Run tests → PASS
```

## Anti-patterns

- ❌ Writing all tests upfront before any production code
- ❌ Writing production code first and tests after ("test last")
- ❌ Making a test pass by hardcoding the expected return value
- ❌ Skipping the red phase — always confirm the test fails first
- ❌ Large steps — if the green phase requires many lines, the test was too big
- ❌ Refactoring while a test is red
- ❌ Deleting a test because it's "inconvenient"
