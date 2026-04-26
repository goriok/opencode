"""Tests for ClaudeCode JSONL adapter."""

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

from token_tracker.adapters.claude_code import ClaudeCodeAdapter
from token_tracker.models import DailyAggregate, SessionSummary


@pytest.fixture
def claude_adapter(sample_claude_projects_dir: Path) -> ClaudeCodeAdapter:
    return ClaudeCodeAdapter(claude_dir=sample_claude_projects_dir.parent)


@pytest.fixture
def empty_claude_dir(tmp_path: Path) -> Path:
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    (claude_dir / "projects").mkdir()
    return claude_dir


@pytest.fixture
def malformed_jsonl_dir(tmp_path: Path) -> Path:
    """Create a directory with malformed JSONL data."""
    claude_dir = tmp_path / ".claude"
    projects_dir = claude_dir / "projects" / "malformed-project"
    projects_dir.mkdir(parents=True)
    now_iso = datetime.now(timezone.utc).isoformat()

    session_file = projects_dir / "bad-session.jsonl"
    lines = [
        '{"type": "assistant", "message": {"model": "claude-sonnet-4-6", "usage": {"input_tokens": 100, "output_tokens": 50, "cache_creation_input_tokens": 10, "cache_read_input_tokens": 20}}, "timestamp": "' + now_iso + '", "sessionId": "sess-good"}',
        "this is not json at all",
        '{"type": "assistant", "message":',  # truncated
        "",
        "   ",  # whitespace only
        '{"type": "user", "message": {"content": "hello"}, "timestamp": "' + now_iso + '"}',  # user message (filtered)
        '{"type": "assistant", "message": {"model": "glm-5.1", "usage": {"input_tokens": 200, "output_tokens": 100, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}}, "timestamp": "' + now_iso + '", "sessionId": "sess-good2"}',
    ]
    session_file.write_text("\n".join(lines))
    return claude_dir


def test_discover_session_files(claude_adapter: ClaudeCodeAdapter) -> None:
    """ClaudeCode adapter discovers JSONL session files."""
    files = claude_adapter._discover_session_files()
    assert len(files) >= 1
    assert all(f.suffix == ".jsonl" for f in files)


def test_empty_projects_dir(empty_claude_dir: Path) -> None:
    """ClaudeCode adapter returns empty data when no sessions exist."""
    adapter = ClaudeCodeAdapter(claude_dir=empty_claude_dir)
    assert adapter.fetch_daily() == []
    assert adapter.fetch_sessions() == []
    assert adapter.fetch_agents() == []
    assert adapter.fetch_models() == []


def test_missing_projects_dir(tmp_path: Path) -> None:
    """ClaudeCode adapter handles missing projects directory gracefully."""
    adapter = ClaudeCodeAdapter(claude_dir=tmp_path / "nonexistent")
    assert adapter.fetch_daily() == []
    assert adapter.fetch_sessions() == []


def test_fetch_daily(claude_adapter: ClaudeCodeAdapter) -> None:
    """ClaudeCode adapter returns daily aggregates."""
    daily = claude_adapter.fetch_daily(days=30)
    assert len(daily) >= 1
    assert isinstance(daily[0], DailyAggregate)
    assert daily[0].day
    assert daily[0].total_tokens > 0
    assert daily[0].source == "claude_code"


def test_fetch_sessions(claude_adapter: ClaudeCodeAdapter) -> None:
    """ClaudeCode adapter returns session summaries."""
    sessions = claude_adapter.fetch_sessions(days=30)
    assert len(sessions) >= 1
    assert isinstance(sessions[0], SessionSummary)
    assert sessions[0].session_id


def test_fetch_models(claude_adapter: ClaudeCodeAdapter) -> None:
    """ClaudeCode adapter returns model aggregates with pricing."""
    models = claude_adapter.fetch_models(days=30)
    assert len(models) >= 1
    assert models[0].model
    assert models[0].total_tokens > 0
    assert models[0].source == "claude_code"


def test_fetch_agents(claude_adapter: ClaudeCodeAdapter) -> None:
    """ClaudeCode adapter returns agent aggregates (model proxy)."""
    agents = claude_adapter.fetch_agents(days=30)
    assert len(agents) >= 1
    assert agents[0].agent
    assert agents[0].source == "claude_code"


def test_malformed_jsonl_handled(malformed_jsonl_dir: Path) -> None:
    """ClaudeCode adapter skips malformed JSONL lines without crashing."""
    adapter = ClaudeCodeAdapter(claude_dir=malformed_jsonl_dir)
    daily = adapter.fetch_daily(days=30)
    # Should have data from the 2 valid assistant lines only
    assert len(daily) >= 1
    total_msgs = sum(d.msgs for d in daily)
    assert total_msgs == 2


def test_filter_by_timestamp(tmp_path: Path) -> None:
    """ClaudeCode adapter filters records by days parameter."""
    claude_dir = tmp_path / ".claude"
    projects_dir = claude_dir / "projects" / "old-project"
    projects_dir.mkdir(parents=True)

    old_ts = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()
    recent_ts = datetime.now(timezone.utc).isoformat()

    lines = [
        json.dumps({"type": "assistant", "message": {"model": "claude-sonnet-4-6", "usage": {"input_tokens": 5000, "output_tokens": 2000, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}}, "timestamp": old_ts, "sessionId": "old-sess"}),
        json.dumps({"type": "assistant", "message": {"model": "claude-sonnet-4-6", "usage": {"input_tokens": 1000, "output_tokens": 500, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}}, "timestamp": recent_ts, "sessionId": "recent-sess"}),
    ]
    (projects_dir / "session.jsonl").write_text("\n".join(lines))

    adapter = ClaudeCodeAdapter(claude_dir=claude_dir)

    daily_90 = adapter.fetch_daily(days=90)
    daily_30 = adapter.fetch_daily(days=30)

    total_90_msgs = sum(d.msgs for d in daily_90)
    total_30_msgs = sum(d.msgs for d in daily_30)
    assert total_90_msgs == 2
    assert total_30_msgs == 1


def test_iterations_handling(tmp_path: Path) -> None:
    """ClaudeCode adapter sums token counts across iterations."""
    claude_dir = tmp_path / ".claude"
    projects_dir = claude_dir / "projects" / "iter-project"
    projects_dir.mkdir(parents=True)
    now_iso = datetime.now(timezone.utc).isoformat()

    record_with_iterations = {
        "type": "assistant",
        "message": {"model": "claude-sonnet-4-6", "usage": {"input_tokens": 100, "output_tokens": 50, "cache_creation_input_tokens": 5, "cache_read_input_tokens": 10}},
        "timestamp": now_iso,
        "sessionId": "iter-sess",
        "iterations": [
            {"usage": {"input_tokens": 500, "output_tokens": 200, "cache_creation_input_tokens": 50, "cache_read_input_tokens": 100}},
            {"usage": {"input_tokens": 300, "output_tokens": 150, "cache_creation_input_tokens": 30, "cache_read_input_tokens": 80}},
        ],
    }
    session_file = projects_dir / "iter-session.jsonl"
    session_file.write_text(json.dumps(record_with_iterations))

    adapter = ClaudeCodeAdapter(claude_dir=claude_dir)
    daily = adapter.fetch_daily(days=30)
    # When iterations exist, their sums (500+300=800 input, 200+150=350 output) replace the top-level usage
    assert len(daily) >= 1
    assert daily[0].input_tokens == 800
    assert daily[0].output_tokens == 350