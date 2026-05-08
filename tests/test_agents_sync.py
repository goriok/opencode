"""Tests for frontmatter stripping in agents sync — highest-risk logic."""

import pytest
from ocx.commands.agents import _strip_opencode_frontmatter


def _fm(*lines: str) -> str:
    """Wrap lines in YAML front matter block."""
    return "---\n" + "\n".join(lines) + "\n---\n"


def test_strips_mode_field():
    text = _fm("name: test-agent", "mode: auto", "description: A test agent") + "Body line\n"
    result = _strip_opencode_frontmatter(text)
    assert "mode:" not in result
    assert "name: test-agent" in result
    assert "description: A test agent" in result
    assert "Body line" in result


def test_strips_permission_block():
    text = _fm(
        "name: test-agent",
        "permission:",
        "  allow: []",
        "  deny: []",
        "description: A test agent",
    ) + "Body\n"
    result = _strip_opencode_frontmatter(text)
    assert "permission:" not in result
    assert "allow:" not in result
    assert "deny:" not in result
    assert "description: A test agent" in result
    assert "Body" in result


def test_strips_mode_and_permission_together():
    text = _fm(
        "name: alan-turing",
        "mode: act",
        "permission:",
        "  allow:",
        "    - Bash",
        "  deny: []",
        "description: Alan Turing agent",
    ) + "# Content here\n"
    result = _strip_opencode_frontmatter(text)
    assert "mode:" not in result
    assert "permission:" not in result
    assert "allow:" not in result
    assert "deny:" not in result
    assert "name: alan-turing" in result
    assert "description: Alan Turing agent" in result
    assert "# Content here" in result


def test_preserves_frontmatter_delimiters():
    text = _fm("name: test") + "Body\n"
    result = _strip_opencode_frontmatter(text)
    assert result.startswith("---\n")
    lines = result.splitlines()
    assert "---" in lines[1:]  # closing delimiter still present


def test_no_frontmatter_unchanged():
    text = "No front matter here\nJust body content\n"
    assert _strip_opencode_frontmatter(text) == text


def test_empty_frontmatter_unchanged():
    text = "---\n---\nBody\n"
    result = _strip_opencode_frontmatter(text)
    assert "Body" in result
    assert result.startswith("---\n")


def test_body_content_preserved():
    body = "## Instructions\n\nDo complex things.\n\nMore content.\n"
    text = _fm("name: agent", "mode: auto") + body
    result = _strip_opencode_frontmatter(text)
    assert body in result


def test_no_mode_no_permission_unchanged_aside_from_whitespace():
    text = _fm("name: test", "description: Clean agent") + "Body\n"
    result = _strip_opencode_frontmatter(text)
    assert "name: test" in result
    assert "description: Clean agent" in result
    assert "mode:" not in result


def test_permission_block_with_deeper_nesting():
    text = _fm(
        "name: agent",
        "permission:",
        "  allow:",
        "    - Bash",
        "    - Read",
        "description: after",
    ) + "Body\n"
    result = _strip_opencode_frontmatter(text)
    assert "permission:" not in result
    assert "Bash" not in result
    assert "description: after" in result
