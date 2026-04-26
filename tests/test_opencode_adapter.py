"""Tests for OpenCode SQLite adapter."""

import sqlite3
from pathlib import Path

import pytest

from token_tracker.adapters.opencode import OpenCodeAdapter
from token_tracker.models import AgentAggregate, DailyAggregate, ModelAggregate, SessionSummary


def _insert_message(cur, msg_id, session_id, time_ms, data_dict):
    import json
    cur.execute(
        "INSERT INTO message VALUES (?, ?, ?, ?)",
        (msg_id, session_id, time_ms, json.dumps(data_dict)),
    )


def _build_db(db_path, days_back=7):
    import json
    from datetime import datetime, timezone

    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS session (
            id TEXT PRIMARY KEY, parent_id TEXT, slug TEXT,
            title TEXT, time_created INTEGER
        )""")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS message (
            id TEXT PRIMARY KEY, session_id TEXT,
            time_created INTEGER, data TEXT
        )""")

    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    week_ago_ms = now_ms - days_back * 24 * 3600 * 1000

    cur.execute(
        "INSERT INTO session VALUES (?, ?, ?, ?, ?)",
        ("sess-1", None, "slug-1", "My Session", week_ago_ms),
    )

    assistant_msgs = [
        {
            "role": "assistant",
            "tokens": {"total": 5000, "input": 3000, "output": 1500, "reasoning": 500,
                       "cache": {"read": 800, "write": 200}},
            "cost": 0.05,
            "agent": "build",
            "modelID": "claude-sonnet-4-6",
            "providerID": "anthropic",
        },
        {
            "role": "assistant",
            "tokens": {"total": 3000, "input": 2000, "output": 800, "reasoning": 200,
                       "cache": {"read": 400, "write": 100}},
            "cost": 0.03,
            "agent": "oracle",
            "modelID": "glm-5.1",
            "providerID": "opencode",
        },
    ]
    for i, msg in enumerate(assistant_msgs):
        _insert_message(cur, f"msg-{i+1}", "sess-1", week_ago_ms + i * 1000, msg)

    user_msg = {"role": "user", "content": "hello"}
    _insert_message(cur, "msg-user", "sess-1", week_ago_ms + 5000, user_msg)

    conn.commit()
    conn.close()


@pytest.fixture
def opencode_db(tmp_path):
    db_path = tmp_path / "opencode.db"
    _build_db(db_path)
    return db_path


def test_fetch_daily_returns_data(opencode_db):
    adapter = OpenCodeAdapter(opencode_db)
    results = adapter.fetch_daily(days=30)
    assert len(results) >= 1
    day = results[0]
    assert isinstance(day, DailyAggregate)
    assert day.total_tokens > 0
    assert day.msgs == 2
    assert day.input_tokens == 5000
    assert day.output_tokens == 2300
    assert day.reasoning_tokens == 700
    assert day.cache_read == 1200
    assert day.cache_write == 300
    assert day.source == "opencode"


def test_fetch_daily_no_data(tmp_path):
    db_path = tmp_path / "empty.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE session (id TEXT PRIMARY KEY)")
    conn.execute("CREATE TABLE message (id TEXT PRIMARY KEY, session_id TEXT, time_created INTEGER, data TEXT)")
    conn.close()
    adapter = OpenCodeAdapter(db_path)
    assert adapter.fetch_daily(days=30) == []


def test_fetch_sessions(opencode_db):
    adapter = OpenCodeAdapter(opencode_db)
    sessions = adapter.fetch_sessions(days=30)
    assert len(sessions) >= 1
    s = sessions[0]
    assert isinstance(s, SessionSummary)
    assert s.session_id == "sess-1"
    assert s.slug == "slug-1"
    assert s.msgs == 2
    assert s.total_tokens > 0


def test_fetch_agents(opencode_db):
    adapter = OpenCodeAdapter(opencode_db)
    agents = adapter.fetch_agents(days=30)
    assert len(agents) == 2
    agent_names = {a.agent for a in agents}
    assert "build" in agent_names
    assert "oracle" in agent_names
    build = next(a for a in agents if a.agent == "build")
    assert isinstance(build, AgentAggregate)
    assert build.total_tokens == 5000
    assert build.total_cost == pytest.approx(0.05)
    assert build.source == "opencode"


def test_fetch_models(opencode_db):
    adapter = OpenCodeAdapter(opencode_db)
    models = adapter.fetch_models(days=30)
    assert len(models) == 2
    model_ids = {m.model for m in models}
    assert "claude-sonnet-4-6" in model_ids
    assert "glm-5.1" in model_ids
    sonnet = next(m for m in models if m.model == "claude-sonnet-4-6")
    assert isinstance(sonnet, ModelAggregate)
    assert sonnet.provider == "anthropic"
    assert sonnet.tracked_cost == pytest.approx(0.05)
    assert sonnet.source == "opencode"


def test_default_db_path():
    adapter = OpenCodeAdapter()
    assert "opencode" in str(adapter.db_path)


def test_user_msg_filtered_out(opencode_db):
    adapter = OpenCodeAdapter(opencode_db)
    daily = adapter.fetch_daily(days=30)
    assert len(daily) == 1
    assert daily[0].msgs == 2