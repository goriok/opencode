"""Edge case and integration tests for the full CLI pipeline, error paths,
and cross-source merging behavior."""

import argparse
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

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
    build_parser,
    main,
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


# ── Cross-source merge: merging data from opencode + claude-code ────────


class TestCrossSourceMerge:
    """Tests for merging data from multiple sources (opencode + claude-code)."""

    def test_merge_daily_from_two_sources(self):
        """Daily totals correctly merge across two source lists."""
        opencode_daily = [
            DailyAggregate(day="2025-01-01", total_tokens=100, msgs=5, total_cost=1.0),
            DailyAggregate(day="2025-01-02", total_tokens=200, msgs=10, total_cost=2.0),
        ]
        claude_daily = [
            DailyAggregate(day="2025-01-01", total_tokens=300, msgs=15, total_cost=3.0),
            DailyAggregate(day="2025-01-03", total_tokens=400, msgs=20, total_cost=4.0),
        ]
        result = _merge_daily(opencode_daily, claude_daily)
        # 3 unique days, Jan-01 has summed values
        assert len(result) == 3
        jan01 = next(d for d in result if d.day == "2025-01-01")
        assert jan01.total_tokens == 400  # 100 + 300
        assert jan01.msgs == 20  # 5 + 15
        assert jan01.total_cost == 4.0  # 1.0 + 3.0

    def test_merge_agents_from_two_sources(self):
        """Agent totals correctly merge across two source lists."""
        oc_agents = [
            AgentAggregate(agent="build", total_tokens=500, msgs=10),
        ]
        cc_agents = [
            AgentAggregate(agent="build", total_tokens=300, msgs=6),
            AgentAggregate(agent="oracle", total_tokens=200, msgs=4),
        ]
        result = _merge_agents(oc_agents, cc_agents)
        build = next(a for a in result if a.agent == "build")
        assert build.total_tokens == 800
        assert build.msgs == 16
        assert len(result) == 2

    def test_merge_models_from_two_sources(self):
        """Model totals correctly merge across two source lists."""
        oc_models = [
            ModelAggregate(model="claude-sonnet", provider="anthropic", total_tokens=1000),
        ]
        cc_models = [
            ModelAggregate(model="claude-sonnet", provider="anthropic", total_tokens=2000),
            ModelAggregate(model="gpt-4", provider="openai", total_tokens=500),
        ]
        result = _merge_models(oc_models, cc_models)
        sonnet = next(m for m in result if m.model == "claude-sonnet")
        assert sonnet.total_tokens == 3000
        assert len(result) == 2

    def test_merge_sessions_cross_source_dedup(self):
        """Sessions from different sources with same ID get summed."""
        oc_sessions = [
            SessionSummary(session_id="ses-001", total_tokens=100, msgs=5, cost=1.0),
        ]
        cc_sessions = [
            SessionSummary(session_id="ses-001", total_tokens=50, msgs=3, cost=0.5),
        ]
        result = _merge_sessions(oc_sessions, cc_sessions)
        assert len(result) == 1
        assert result[0].total_tokens == 150
        assert result[0].msgs == 8
        assert result[0].cost == 1.5


# ── Empty + zero-value edge cases ─────────────────────────────────────


class TestEmptyEdgeCases:
    """Tests for empty/zero-value edge cases."""

    def test_merge_daily_all_zero_fields(self):
        """Merging daily aggregates with zero token fields."""
        d = DailyAggregate(day="2025-01-01")
        result = _merge_daily([d])
        assert len(result) == 1
        assert result[0].total_tokens == 0
        assert result[0].msgs == 0
        assert result[0].total_cost == 0.0

    def test_merge_agents_all_zeros(self):
        """Merging agent aggregates with zero fields."""
        a = AgentAggregate(agent="test")
        result = _merge_agents([a])
        assert result[0].total_tokens == 0

    def test_merge_models_all_zeros(self):
        """Merging model aggregates with zero fields."""
        m = ModelAggregate(model="test-model", provider="test")
        result = _merge_models([m])
        assert result[0].total_tokens == 0
        assert result[0].provider == "test"

    def test_merge_sessions_empty_list(self):
        """Merging with no session lists returns empty."""
        result = _merge_sessions()
        assert result == []

    def test_fmt_num_zero(self):
        """Zero integer formats as '0'."""
        assert _fmt_num(0) == "0"

    def test_fmt_num_exact_thousand(self):
        """Exactly 1000 formats as '1.0K'."""
        assert _fmt_num(1000) == "1.0K"

    def test_fmt_num_exact_million(self):
        """Exactly 1M formats as '1.0M'."""
        assert _fmt_num(1_000_000) == "1.0M"

    def test_fmt_pct_with_decimals(self):
        """Percentage with many decimals rounds to 1 decimal."""
        assert _fmt_pct(33.333) == "33.3%"


# ── _detect_sources edge cases ─────────────────────────────────────────


class TestDetectSourcesEdgeCases:
    """Additional edge cases for source detection."""

    def test_auto_detect_with_default_paths(self, tmp_path):
        """Auto-detect with no args uses module defaults."""
        args = argparse.Namespace(source="auto", db=None, claude_dir=None)
        # This will check actual default paths on this machine
        result = _detect_sources(args)
        # Result depends on the machine's actual paths
        assert isinstance(result, list)
        assert all(s in ("opencode", "claude-code") for s in result)

    def test_explicit_source_overrides_auto(self, tmp_path):
        """Explicit --source always wins even if paths don't exist."""
        args = argparse.Namespace(
            source="opencode",
            db=str(tmp_path / "nope.db"),
            claude_dir=None,
        )
        # Even though the db doesn't exist, explicit source wins
        assert _detect_sources(args) == ["opencode"]


# ── CLI argument parsing edge cases ─────────────────────────────────────


class TestParserEdgeCases:
    """Edge case tests for argument parser."""

    def test_parser_baseline_dir(self):
        """--baseline-dir flag is parsed correctly."""
        parser = build_parser()
        args = parser.parse_args(["--baseline-dir", "/tmp/baselines"])
        assert args.baseline_dir == "/tmp/baselines"

    def test_parser_all_flags_combined(self):
        """All flags can be combined."""
        parser = build_parser()
        args = parser.parse_args([
            "--source", "claude-code",
            "--days", "14",
            "--dry-run",
            "--baseline", "weekly",
            "--with-subagents",
            "--open",
        ])
        assert args.source == "claude-code"
        assert args.days == 14
        assert args.dry_run is True
        assert args.baseline == "weekly"
        assert args.with_subagents is True
        assert args.open is True

    def test_parser_invalid_source_fails(self):
        """Invalid --source value causes parser error."""
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--source", "invalid"])


# ── Dashboard generation (compute_kpis + generate_dashboard) ─────────


class TestDashboardGeneration:
    """Tests for compute_kpis and dashboard HTML generation."""

    def test_compute_kpis_empty_data(self):
        """KPIs with empty data produce zero values."""
        from token_tracker.dashboard import compute_kpis

        kpis = compute_kpis([], [], [])
        assert kpis.total_tokens == 0
        assert kpis.total_cost == 0.0
        assert kpis.total_msgs == 0
        assert kpis.active_days == 0
        assert kpis.cache_hit_rate == 0.0
        assert kpis.output_ratio == 0.0
        assert kpis.tokens_per_day == 0

    def test_compute_kpis_with_data(self):
        """KPIs are computed correctly from aggregates."""
        from token_tracker.dashboard import compute_kpis

        daily = [
            DailyAggregate(
                day="2025-01-01",
                total_tokens=10000,
                msgs=100,
                input_tokens=6000,
                output_tokens=3000,
                cache_read=5000,
                total_cost=5.0,
            ),
            DailyAggregate(
                day="2025-01-02",
                total_tokens=20000,
                msgs=200,
                input_tokens=12000,
                output_tokens=6000,
                cache_read=10000,
                total_cost=10.0,
            ),
        ]
        agents = [AgentAggregate(agent="build", total_tokens=30000, msgs=300)]
        models = [
            ModelAggregate(
                model="claude-sonnet",
                provider="anthropic",
                total_tokens=30000,
                est_api_cost=15.0,
            )
        ]

        kpis = compute_kpis(daily, agents, models, days=30)
        assert kpis.total_tokens == 30000
        assert kpis.total_cost == 15.0
        assert kpis.total_msgs == 300
        assert kpis.active_days == 2
        assert kpis.cache_hit_rate == 50.0  # 15000/30000 * 100
        assert kpis.output_ratio == 30.0  # 9000/30000 * 100
        assert kpis.tokens_per_day == 15000  # 30000/2

    def test_generate_dashboard_produces_html(self):
        """generate_dashboard returns an HTML string with expected sections."""
        from token_tracker.dashboard import generate_dashboard

        kpis = KPIs(total_tokens=100, total_cost=1.0, total_msgs=10, active_days=1)
        html = generate_dashboard([], [], [], [], kpis)
        assert "<!DOCTYPE html>" in html
        assert "Token Dashboard" in html
        assert "SUMMARY_DATA" not in html  # Should be replaced
        assert "SOURCE_DATA" not in html  # No placeholder leakage


# ── Baseline integration ──────────────────────────────────────────────


class TestBaselineIntegration:
    """Integration tests for baseline save/load/compare."""

    def test_save_and_load_roundtrip(self, tmp_path):
        """Baseline save → load produces identical data."""
        from token_tracker.baselines import save_baseline, load_baseline

        metrics = {"total_tokens": 1000, "total_cost": 5.0, "period_days": 7}
        daily = [{"day": "2025-01-01", "total_tokens": 500}]
        agents = [{"agent": "build", "total_tokens": 500}]
        models = [{"model": "claude-sonnet", "total_tokens": 500}]

        path = save_baseline("test-roundtrip", metrics, daily, agents, models, output_dir=tmp_path)
        assert path.exists()

        loaded = load_baseline("test-roundtrip", output_dir=tmp_path)
        assert loaded["metrics"]["total_tokens"] == 1000
        assert loaded["metrics"]["total_cost"] == 5.0
        assert len(loaded["daily"]) == 1

    def test_compare_baselines_delta(self, tmp_path):
        """compare_baselines produces correct percentage deltas."""
        from token_tracker.baselines import compare_baselines, save_baseline

        prev_metrics = {
            "total_tokens": 1000,
            "total_cost": 5.0,
            "total_msgs": 100,
            "input_tokens": 600,
            "output_tokens": 300,
            "cache_read": 200,
            "reasoning_tokens": 50,
            "cache_hit_rate": 20.0,
            "output_ratio": 30.0,
            "cost_per_output_token": 0.0166,
            "tokens_per_day": 142,
            "period_days": 7,
        }
        curr_metrics = {
            "total_tokens": 2000,
            "total_cost": 10.0,
            "total_msgs": 150,
            "input_tokens": 1200,
            "output_tokens": 600,
            "cache_read": 400,
            "reasoning_tokens": 100,
            "cache_hit_rate": 25.0,
            "output_ratio": 35.0,
            "cost_per_output_token": 0.0166,
            "tokens_per_day": 285,
            "period_days": 7,
        }

        save_baseline("prev", prev_metrics, [], [], [], output_dir=tmp_path)
        current = {"label": "current", "metrics": curr_metrics, "daily": [], "agents": [], "models": []}
        previous = load_baseline("prev", output_dir=tmp_path)

        delta = compare_baselines(current, previous)
        # Tokens doubled: +100%
        assert delta["total_tokens"] == 100.0
        # Cost doubled: +100%
        assert delta["total_cost"] == 100.0

    def test_validate_baselines_empty_dir(self, tmp_path):
        """validate_baselines returns no issues for empty dir."""
        from token_tracker.baselines import validate_baselines

        issues = validate_baselines(tmp_path)
        assert issues == []

    def test_load_nonexistent_baseline_raises(self, tmp_path):
        """Loading a non-existent baseline raises FileNotFoundError."""
        from token_tracker.baselines import load_baseline

        with pytest.raises(FileNotFoundError):
            load_baseline("does-not-exist", output_dir=tmp_path)


# ── Main pipeline edge cases (mocked) ─────────────────────────────────


class TestMainPipelineEdgeCases:
    """Tests for main() pipeline with mocked adapters."""

    def test_main_validate_no_issues(self, tmp_path, capsys):
        """--validate with empty baseline dir succeeds."""
        main(["--validate", "--baseline-dir", str(tmp_path)])
        captured = capsys.readouterr()
        assert "valid" in captured.out.lower()

    def test_main_validate_with_issues(self, tmp_path, capsys):
        """--validate with corrupt baseline file reports issues."""
        from token_tracker.baselines import DEFAULT_BASELINE_DIR

        baseline_dir = tmp_path / "baselines"
        baseline_dir.mkdir()
        # Write corrupted baseline file
        bad_file = baseline_dir / "baseline-bad.json"
        bad_file.write_text("not valid json{{{")

        with pytest.raises(SystemExit):
            main(["--validate", "--baseline-dir", str(baseline_dir)])

    def test_main_no_sources_exits(self, tmp_path, capsys):
        """main() exits with error when no data sources found."""
        empty_db = tmp_path / "nope.db"
        empty_claude = tmp_path / "no-claude"

        with pytest.raises(SystemExit) as exc_info:
            main([
                "--source", "auto",
                "--db", str(empty_db),
                "--claude-dir", str(empty_claude),
            ])
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "No data sources found" in captured.err

    def test_main_dry_run_with_opencode(self, tmp_path, capsys):
        """--dry-run with mocked OpenCode adapter prints KPI summary."""
        # Create a fake DB file so auto-detect finds opencode
        fake_db = tmp_path / "opencode.db"
        fake_db.touch()

        mock_daily = [DailyAggregate(day="2025-01-01", total_tokens=1000, msgs=10)]
        mock_sessions = [SessionSummary(session_id="s1", total_tokens=500, msgs=5)]
        mock_agents = [AgentAggregate(agent="build", total_tokens=1000, msgs=10)]
        mock_models = [
            ModelAggregate(
                model="claude-sonnet",
                provider="anthropic",
                total_tokens=1000,
                msgs=10,
                est_api_cost=5.0,
            )
        ]

        with patch("token_tracker.cli.OpenCodeAdapter") as MockAdapter:
            instance = MagicMock()
            instance.fetch_daily.return_value = mock_daily
            instance.fetch_sessions.return_value = mock_sessions
            instance.fetch_agents.return_value = mock_agents
            instance.fetch_models.return_value = mock_models
            MockAdapter.return_value = instance

            main([
                "--source", "opencode",
                "--db", str(fake_db),
                "--dry-run",
                "--days", "7",
            ])

        captured = capsys.readouterr()
        assert "Token Tracker" in captured.out
        assert "KPI Summary" in captured.out

    def test_main_opencode_adapter_error_continues(self, tmp_path, capsys):
        """If OpenCode adapter throws, main() prints error and exits with no data."""
        fake_db = tmp_path / "opencode.db"
        fake_db.touch()

        with patch("token_tracker.cli.OpenCodeAdapter") as MockAdapter:
            instance = MagicMock()
            instance.fetch_daily.side_effect = Exception("DB read error")
            instance.fetch_sessions.side_effect = Exception("DB read error")
            instance.fetch_agents.side_effect = Exception("DB read error")
            instance.fetch_models.side_effect = Exception("DB read error")
            MockAdapter.return_value = instance

            # No data found → exits with code 0 with message
            with pytest.raises(SystemExit):
                main([
                    "--source", "opencode",
                    "--db", str(fake_db),
                    "--dry-run",
                ])

    def test_main_with_subagents_flag_no_claude(self, tmp_path, capsys):
        """--with-subagents without claude-code source is a no-op for subagents."""
        fake_db = tmp_path / "opencode.db"
        fake_db.touch()

        mock_daily = [DailyAggregate(day="2025-01-01", total_tokens=100)]
        mock_kpis = KPIs(total_tokens=100, total_cost=0.5, total_msgs=5, active_days=1)

        with patch("token_tracker.cli.OpenCodeAdapter") as MockAdapter:
            instance = MagicMock()
            instance.fetch_daily.return_value = mock_daily
            instance.fetch_sessions.return_value = []
            instance.fetch_agents.return_value = []
            instance.fetch_models.return_value = []
            MockAdapter.return_value = instance

            with patch("token_tracker.cli.compute_kpis", return_value=mock_kpis):
                with patch("token_tracker.cli.generate_dashboard", return_value="<html>test</html>"):
                    with patch("token_tracker.cli.write_dashboard", return_value="/tmp/out.html"):
                        main([
                            "--source", "opencode",
                            "--db", str(fake_db),
                            "--with-subagents",
                            "--output", str(tmp_path / "out.html"),
                        ])

        captured = capsys.readouterr()
        assert "Dashboard written" in captured.out

    def test_main_dry_run_with_subagents(self, tmp_path, capsys):
        """--dry-run --with-subagents with claude-code shows subagent section."""
        fake_db = tmp_path / "opencode.db"
        fake_db.touch()
        claude_dir = tmp_path / "claude"
        claude_dir.mkdir()
        (claude_dir / "projects").mkdir()

        mock_kpis = KPIs(total_tokens=100, total_cost=0.5, total_msgs=5, active_days=1)
        mock_subagents = [
            SubagentInfo(agent_type="code-review", tokens=TokenUsage(total=500), model="claude-sonnet"),
        ]

        with patch("token_tracker.cli.ClaudeCodeAdapter") as MockCC:
            cc_instance = MagicMock()
            cc_instance.fetch_daily.return_value = [DailyAggregate(day="2025-01-01", total_tokens=100)]
            cc_instance.fetch_sessions.return_value = []
            cc_instance.fetch_agents.return_value = []
            cc_instance.fetch_models.return_value = []
            cc_instance.fetch_subagents.return_value = mock_subagents
            MockCC.return_value = cc_instance

            with patch("token_tracker.cli.compute_kpis", return_value=mock_kpis):
                main([
                    "--source", "claude-code",
                    "--claude-dir", str(claude_dir),
                    "--dry-run",
                    "--with-subagents",
                ])

        captured = capsys.readouterr()
        assert "Subagents" in captured.out
        assert "code-review" in captured.out

    def test_main_dry_run_with_delta(self, tmp_path, capsys):
        """--dry-run --compare shows baseline comparison."""
        fake_db = tmp_path / "opencode.db"
        fake_db.touch()

        mock_kpis = KPIs(total_tokens=1000, total_cost=5.0, total_msgs=50, active_days=1)
        mock_daily = [DailyAggregate(day="2025-01-01", total_tokens=1000, msgs=50)]

        baseline_dir = tmp_path / "baselines"
        baseline_dir.mkdir()
        # Create a baseline file
        baseline_data = {
            "label": "previous",
            "created_at": "2025-01-01T00:00:00",
            "period_days": 7,
            "metrics": {"total_tokens": 500, "total_cost": 2.0, "total_msgs": 25,
                        "input_tokens": 300, "output_tokens": 150, "cache_read": 100,
                        "reasoning_tokens": 25, "cache_hit_rate": 20.0, "output_ratio": 30.0,
                        "cost_per_output_token": 0.0133, "tokens_per_day": 71},
            "daily": [], "agents": [], "models": [],
        }
        (baseline_dir / "baseline-test-compare.json").write_text(json.dumps(baseline_data))

        with patch("token_tracker.cli.OpenCodeAdapter") as MockAdapter:
            instance = MagicMock()
            instance.fetch_daily.return_value = mock_daily
            instance.fetch_sessions.return_value = []
            instance.fetch_agents.return_value = []
            instance.fetch_models.return_value = []
            MockAdapter.return_value = instance

            with patch("token_tracker.cli.compute_kpis", return_value=mock_kpis):
                main([
                    "--source", "opencode",
                    "--db", str(fake_db),
                    "--dry-run",
                    "--compare", "test-compare",
                    "--baseline-dir", str(baseline_dir),
                ])

        captured = capsys.readouterr()
        assert "Baseline Comparison" in captured.out

    def test_main_baseline_save(self, tmp_path, capsys):
        """--baseline saves a baseline file."""
        fake_db = tmp_path / "opencode.db"
        fake_db.touch()

        mock_kpis = KPIs(total_tokens=100, total_cost=0.5, total_msgs=5, active_days=1)
        mock_daily = [DailyAggregate(day="2025-01-01", total_tokens=100)]

        baseline_dir = tmp_path / "baselines"

        with patch("token_tracker.cli.OpenCodeAdapter") as MockAdapter:
            instance = MagicMock()
            instance.fetch_daily.return_value = mock_daily
            instance.fetch_sessions.return_value = []
            instance.fetch_agents.return_value = []
            instance.fetch_models.return_value = []
            MockAdapter.return_value = instance

            with patch("token_tracker.cli.compute_kpis", return_value=mock_kpis):
                main([
                    "--source", "opencode",
                    "--db", str(fake_db),
                    "--baseline", "test-save",
                    "--baseline-dir", str(baseline_dir),
                    "--output", str(tmp_path / "out.html"),
                ])

        captured = capsys.readouterr()
        assert "saved" in captured.out.lower()
        # Verify baseline file was created
        assert (baseline_dir / "baseline-test-save.json").exists()


# ── Models edge cases ──────────────────────────────────────────────────


class TestModelsEdgeCases:
    """Edge case tests for data models."""

    def test_subagent_info_defaults(self):
        """SubagentInfo has sensible defaults."""
        sa = SubagentInfo()
        assert sa.agent_type == ""
        assert sa.tokens.total == 0
        assert sa.model == ""

    def test_token_usage_fields(self):
        """TokenUsage accumulates correctly."""
        t = TokenUsage(total=100, input=50, output=50, cost=1.0)
        assert t.total == 100
        assert t.input == 50
        assert t.output == 50

    def test_daily_aggregate_defaults(self):
        """DailyAggregate has zero defaults."""
        d = DailyAggregate(day="2025-01-01")
        assert d.total_tokens == 0
        assert d.msgs == 0
        assert d.total_cost == 0.0

    def test_session_summary_defaults(self):
        """SessionSummary has zero defaults."""
        s = SessionSummary(session_id="abc")
        assert s.total_tokens == 0
        assert s.msgs == 0
        assert s.cost == 0.0