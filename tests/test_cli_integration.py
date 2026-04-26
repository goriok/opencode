"""Integration tests for cli.py internal functions: _detect_sources, merge functions,
_fmt_num, _fmt_pct, _print_dry_run."""

import argparse
from unittest.mock import patch

import pytest

from token_tracker.cli import (
    _detect_sources,
    _fmt_num,
    _fmt_pct,
    _merge_agents,
    _merge_daily,
    _merge_models,
    _merge_sessions,
    _print_dry_run,
)
from token_tracker.models import (
    AgentAggregate,
    DailyAggregate,
    KPIs,
    ModelAggregate,
    SessionSummary,
    SubagentInfo,
    TokenUsage,
)


# ── _detect_sources ──────────────────────────────────────────


class TestDetectSources:
    """Tests for _detect_sources auto-detection logic."""

    def test_explicit_opencode(self, tmp_path):
        """When source is explicitly set, return it regardless of path existence."""
        args = argparse.Namespace(
            source="opencode", db=str(tmp_path / "nonexistent.db"), claude_dir=None
        )
        assert _detect_sources(args) == ["opencode"]

    def test_explicit_claude_code(self, tmp_path):
        """When source is explicitly set to claude-code, return it."""
        args = argparse.Namespace(
            source="claude-code", db=None, claude_dir=None
        )
        assert _detect_sources(args) == ["claude-code"]

    def test_auto_both_exist(self, tmp_path):
        """Auto-detect returns both sources when both paths exist."""
        db_file = tmp_path / "opencode.db"
        db_file.touch()
        claude_dir = tmp_path / "claude"
        claude_dir.mkdir()
        (claude_dir / "projects").mkdir()

        args = argparse.Namespace(
            source="auto", db=str(db_file), claude_dir=str(claude_dir)
        )
        result = _detect_sources(args)
        assert "opencode" in result
        assert "claude-code" in result

    def test_auto_only_opencode(self, tmp_path):
        """Auto-detect returns only opencode when only DB exists."""
        db_file = tmp_path / "opencode.db"
        db_file.touch()

        args = argparse.Namespace(
            source="auto", db=str(db_file), claude_dir=str(tmp_path / "no-claude")
        )
        result = _detect_sources(args)
        assert result == ["opencode"]

    def test_auto_only_claude(self, tmp_path):
        """Auto-detect returns only claude-code when only projects dir exists."""
        claude_dir = tmp_path / "claude"
        claude_dir.mkdir()
        (claude_dir / "projects").mkdir()

        args = argparse.Namespace(
            source="auto", db=str(tmp_path / "nonexistent.db"), claude_dir=str(claude_dir)
        )
        result = _detect_sources(args)
        assert result == ["claude-code"]

    def test_auto_neither_exist(self, tmp_path):
        """Auto-detect returns empty list when nothing exists."""
        args = argparse.Namespace(
            source="auto", db=str(tmp_path / "nonexistent.db"), claude_dir=None
        )
        with patch("token_tracker.cli.DEFAULT_DB_PATH", tmp_path / "nope.db"):
            with patch("token_tracker.cli.DEFAULT_CLAUDE_DIR", tmp_path / "nope"):
                result = _detect_sources(args)
        assert result == []


# ── _merge_daily ─────────────────────────────────────────────


class TestMergeDaily:
    """Tests for _merge_daily list merging."""

    def test_merge_single_list(self):
        """Single list returns same items sorted by day."""
        d1 = DailyAggregate(day="2025-01-01", total_tokens=100, msgs=5)
        d2 = DailyAggregate(day="2025-01-03", total_tokens=200, msgs=10)
        result = _merge_daily([d1, d2])
        assert len(result) == 2
        assert result[0].day == "2025-01-01"
        assert result[1].day == "2025-01-03"

    def test_merge_overlapping_days(self):
        """Days with same key get summed."""
        list_a = [DailyAggregate(day="2025-01-01", total_tokens=100, msgs=5)]
        list_b = [DailyAggregate(day="2025-01-01", total_tokens=50, msgs=3)]
        result = _merge_daily(list_a, list_b)
        assert len(result) == 1
        assert result[0].total_tokens == 150
        assert result[0].msgs == 8

    def test_merge_empty(self):
        """No input lists returns empty."""
        result = _merge_daily()
        assert result == []

    def test_merge_sorted_output(self):
        """Output is sorted by day string."""
        d1 = DailyAggregate(day="2025-01-15", total_tokens=500)
        d2 = DailyAggregate(day="2025-01-01", total_tokens=100)
        d3 = DailyAggregate(day="2025-01-10", total_tokens=300)
        result = _merge_daily([d1], [d2], [d3])
        assert [r.day for r in result] == ["2025-01-01", "2025-01-10", "2025-01-15"]


# ── _merge_agents ────────────────────────────────────────────


class TestMergeAgents:
    """Tests for _merge_agents list merging."""

    def test_merge_sums_tokens(self):
        """Same agent from two lists gets summed."""
        a1 = AgentAggregate(agent="sisyphus", total_tokens=1000, msgs=10)
        a2 = AgentAggregate(agent="sisyphus", total_tokens=2000, msgs=20)
        result = _merge_agents([a1], [a2])
        assert len(result) == 1
        assert result[0].agent == "sisyphus"
        assert result[0].total_tokens == 3000
        assert result[0].msgs == 30

    def test_merge_different_agents(self):
        """Different agents stay separate."""
        a1 = AgentAggregate(agent="sisyphus", total_tokens=1000)
        a2 = AgentAggregate(agent="oracle", total_tokens=500)
        result = _merge_agents([a1], [a2])
        assert len(result) == 2

    def test_merge_sorted_by_tokens_desc(self):
        """Sorted by total_tokens descending."""
        a1 = AgentAggregate(agent="small", total_tokens=100)
        a2 = AgentAggregate(agent="big", total_tokens=9999)
        result = _merge_agents([a1, a2])
        assert result[0].agent == "big"
        assert result[1].agent == "small"


# ── _merge_models ────────────────────────────────────────────


class TestMergeModels:
    """Tests for _merge_models list merging."""

    def test_merge_same_model(self):
        """Same model from two lists gets summed."""
        m1 = ModelAggregate(model="claude-sonnet", provider="anthropic", total_tokens=100, tracked_cost=1.0)
        m2 = ModelAggregate(model="claude-sonnet", provider="anthropic", total_tokens=200, tracked_cost=2.0)
        result = _merge_models([m1], [m2])
        assert len(result) == 1
        assert result[0].total_tokens == 300
        assert result[0].tracked_cost == 3.0

    def test_merge_preserves_provider(self):
        """First occurrence's provider is preserved on merge."""
        m1 = ModelAggregate(model="gpt-4", provider="openai", total_tokens=50)
        m2 = ModelAggregate(model="gpt-4", provider="openai", total_tokens=50)
        result = _merge_models([m1], [m2])
        assert result[0].provider == "openai"


# ── _merge_sessions ──────────────────────────────────────────


class TestMergeSessions:
    """Tests for _merge_sessions dedup logic."""

    def test_dedup_by_session_id(self):
        """Same session_id gets merged (summed tokens, keep first)."""
        s1 = SessionSummary(session_id="abc", total_tokens=100, msgs=5)
        s2 = SessionSummary(session_id="abc", total_tokens=50, msgs=3)
        result = _merge_sessions([s1], [s2])
        assert len(result) == 1
        assert result[0].total_tokens == 150
        assert result[0].msgs == 8

    def test_different_sessions_preserved(self):
        """Different session_ids stay separate."""
        s1 = SessionSummary(session_id="abc", total_tokens=100)
        s2 = SessionSummary(session_id="def", total_tokens=200)
        result = _merge_sessions([s1], [s2])
        assert len(result) == 2

    def test_merge_sorted_by_created_desc(self):
        """Sorted by created descending."""
        s1 = SessionSummary(session_id="a", created="2025-01-01")
        s2 = SessionSummary(session_id="b", created="2025-01-10")
        result = _merge_sessions([s1, s2])
        assert result[0].session_id == "b"


# ── _fmt_num ─────────────────────────────────────────────────


class TestFmtNum:
    """Tests for _fmt_num number formatter."""

    def test_small_int(self):
        assert _fmt_num(42) == "42"

    def test_thousands(self):
        assert _fmt_num(1500) == "1.5K"

    def test_millions(self):
        assert _fmt_num(2_500_000) == "2.5M"

    def test_tiny_float(self):
        result = _fmt_num(0.005)
        assert "$0.0050" in result

    def test_regular_float(self):
        result = _fmt_num(3.14)
        assert result == "$3.14"


# ── _fmt_pct ─────────────────────────────────────────────────


class TestFmtPct:
    """Tests for _fmt_pct percentage formatter."""

    def test_basic(self):
        assert _fmt_pct(42.5) == "42.5%"

    def test_zero(self):
        assert _fmt_pct(0.0) == "0.0%"

    def test_hundred(self):
        assert _fmt_pct(100.0) == "100.0%"


# ── _print_dry_run ───────────────────────────────────────────


class TestPrintDryRun:
    """Tests for _print_dry_run terminal output."""

    def test_basic_output(self, capsys):
        """Prints KPI summary with expected header."""
        kpis = KPIs(
            total_tokens=5000, total_cost=1.5, total_msgs=100,
            active_days=10, cache_hit_rate=45.0, output_ratio=30.0,
            tokens_per_day=500, avg_tracked_cost_day=0.15, avg_est_cost_day=0.20,
        )
        _print_dry_run("OpenCode", 30, [], [], [], [], kpis)
        captured = capsys.readouterr()
        assert "Token Tracker — OpenCode — Last 30 days" in captured.out
        assert "KPI Summary" in captured.out

    def test_with_subagents(self, capsys):
        """Subagents section shows when subagents list is provided."""
        kpis = KPIs(total_tokens=100)
        sa = SubagentInfo(
            agent_type="code-review",
            tokens=TokenUsage(total=5000),
            model="claude-sonnet",
        )
        _print_dry_run("Test", 7, [], [], [], [], kpis, subagents=[sa])
        captured = capsys.readouterr()
        assert "Subagents" in captured.out
        assert "code-review" in captured.out

    def test_without_subagents(self, capsys):
        """No subagents section when subagents is None."""
        kpis = KPIs(total_tokens=100)
        _print_dry_run("Test", 7, [], [], [], [], kpis, subagents=None)
        captured = capsys.readouterr()
        assert "Subagents" not in captured.out

    def test_with_delta(self, capsys):
        """Delta comparison prints baseline section."""
        kpis = KPIs(total_tokens=100)
        delta = {
            "total_tokens": 10.5,
            "previous_label": "before-change",
        }
        _print_dry_run("Test", 7, [], [], [], [], kpis, delta=delta)
        captured = capsys.readouterr()
        assert "Baseline Comparison" in captured.out
        assert "before-change" in captured.out

    def test_empty_lists_no_crash(self, capsys):
        """Empty data lists don't crash dry-run."""
        kpis = KPIs(total_tokens=0)
        _print_dry_run("Empty", 1, [], [], [], [], kpis)
        captured = capsys.readouterr()
        assert "Empty" in captured.out