"""Shared pytest fixtures for token_tracker tests."""

import json
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def tmp_path_factory_dir(tmp_path: Path) -> Path:
    """Provide a temporary directory for test files."""
    return tmp_path


@pytest.fixture
def sample_opencode_db(tmp_path: Path) -> Path:
    """Create a minimal OpenCode SQLite database with test data."""
    db_path = tmp_path / "opencode.db"
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS session (
            id TEXT PRIMARY KEY,
            parent_id TEXT,
            slug TEXT,
            title TEXT,
            time_created INTEGER
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS message (
            id TEXT PRIMARY KEY,
            session_id TEXT,
            time_created INTEGER,
            data TEXT
        )
    """)

    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    week_ago_ms = now_ms - 7 * 24 * 3600 * 1000

    cur.execute(
        "INSERT INTO session VALUES (?, ?, ?, ?, ?)",
        ("sess-1", None, "test-session", "Test Session", week_ago_ms),
    )

    messages = [
        {
            "role": "assistant",
            "tokens": {
                "total": 5000,
                "input": 3000,
                "output": 1500,
                "reasoning": 500,
                "cache": {"read": 800, "write": 200},
            },
            "cost": 0.05,
            "agent": "build",
            "modelID": "claude-sonnet-4-6",
            "providerID": "anthropic",
        },
        {
            "role": "assistant",
            "tokens": {
                "total": 3000,
                "input": 2000,
                "output": 800,
                "reasoning": 200,
                "cache": {"read": 400, "write": 100},
            },
            "cost": 0.03,
            "agent": "oracle",
            "modelID": "glm-5.1",
            "providerID": "opencode",
        },
    ]

    for i, msg_data in enumerate(messages):
        cur.execute(
            "INSERT INTO message VALUES (?, ?, ?, ?)",
            (f"msg-{i+1}", "sess-1", week_ago_ms + i * 1000, json.dumps(msg_data)),
        )

    conn.commit()
    conn.close()
    return db_path


@pytest.fixture
def sample_claude_projects_dir(tmp_path: Path) -> Path:
    """Create a minimal Claude Code projects directory with test JSONL data."""
    projects_dir = tmp_path / ".claude" / "projects"
    encoded_path = projects_dir / "test-project"
    encoded_path.mkdir(parents=True)

    session_file = encoded_path / "test-session-id.jsonl"
    now_iso = datetime.now(timezone.utc).isoformat()

    lines = []
    for i in range(3):
        entry = {
            "type": "assistant",
            "message": {
                "model": "claude-sonnet-4-6",
                "usage": {
                    "input_tokens": 1000 + i * 100,
                    "output_tokens": 500 + i * 50,
                    "cache_creation_input_tokens": 200,
                    "cache_read_input_tokens": 300,
                },
            },
            "timestamp": now_iso,
            "sessionId": "test-session-id",
        }
        lines.append(json.dumps(entry))

    # Add a non-assistant message (should be filtered)
    lines.append(json.dumps({"type": "user", "message": {"content": "hello"}, "timestamp": now_iso}))

    session_file.write_text("\n".join(lines))
    return projects_dir


@pytest.fixture
def sample_pricing_table() -> dict:
    """Provide a minimal pricing table for tests."""
    return {
        "claude-sonnet-4-6": (3.00 / 1e6, 15.00 / 1e6, 0.30 / 1e6),
        "claude-opus-4-6": (15.00 / 1e6, 75.00 / 1e6, 1.50 / 1e6),
        "claude-haiku-4-5": (0.80 / 1e6, 4.00 / 1e6, 0.08 / 1e6),
        "glm-5.1": (0.0, 0.0, 0.0),
    }