"""Tests for dashboard HTML generation."""

import json
from pathlib import Path

from token_tracker.dashboard import (
    compute_kpis,
    generate_dashboard,
    write_dashboard,
)
from token_tracker.models import (
    AgentAggregate,
    DailyAggregate,
    KPIs,
    ModelAggregate,
    SessionSummary,
)


def _sample_daily():
    return [
        DailyAggregate(day="2024-01-15", msgs=10, total_tokens=50000, input_tokens=30000,
                       output_tokens=15000, reasoning_tokens=1000, cache_read=5000,
                       cache_write=0, total_cost=0.45),
        DailyAggregate(day="2024-01-16", msgs=8, total_tokens=40000, input_tokens=25000,
                       output_tokens=12000, reasoning_tokens=800, cache_read=3000,
                       cache_write=0, total_cost=0.36),
    ]


def _sample_agents():
    return [
        AgentAggregate(agent="build", msgs=12, total_tokens=60000, input_tokens=35000,
                        output_tokens=20000, cache_read=8000, total_cost=0.60),
        AgentAggregate(agent="oracle", msgs=6, total_tokens=30000, input_tokens=20000,
                        output_tokens=7000, cache_read=2000, total_cost=0.21),
    ]


def _sample_models():
    return [
        ModelAggregate(model="claude-sonnet-4-6", provider="anthropic", msgs=15,
                        total_tokens=70000, input_tokens=45000, output_tokens=20000,
                        cache_read=9000, tracked_cost=0.60, est_api_cost=0.75),
        ModelAggregate(model="glm-5.1", provider="zhipu", msgs=3,
                        total_tokens=20000, input_tokens=10000, output_tokens=7000,
                        cache_read=1000, tracked_cost=0.21, est_api_cost=0.0),
    ]


def _sample_sessions():
    return [
        SessionSummary(session_id="abc123", slug="my-project", title="Test Session",
                        created="2024-01-15T10:00:00", msgs=10, total_tokens=50000,
                        input_tokens=30000, output_tokens=15000, cost=0.45, cache_read=5000),
    ]


def _sample_kpis():
    daily = _sample_daily()
    return compute_kpis(daily, _sample_agents(), _sample_models(), days=30)


class TestComputeKpis:
    """KPI computation from aggregated data."""

    def test_total_tokens(self):
        daily = _sample_daily()
        kpis = compute_kpis(daily, _sample_agents(), _sample_models())
        assert kpis.total_tokens == 90000

    def test_total_msgs(self):
        daily = _sample_daily()
        kpis = compute_kpis(daily, _sample_agents(), _sample_models())
        assert kpis.total_msgs == 18

    def test_active_days(self):
        daily = _sample_daily()
        kpis = compute_kpis(daily, _sample_agents(), _sample_models())
        assert kpis.active_days == 2

    def test_cache_hit_rate(self):
        daily = _sample_daily()
        kpis = compute_kpis(daily, _sample_agents(), _sample_models())
        expected = 8000 / 90000 * 100
        assert abs(kpis.cache_hit_rate - expected) < 0.2

    def test_output_ratio(self):
        daily = _sample_daily()
        kpis = compute_kpis(daily, _sample_agents(), _sample_models())
        expected = 27000 / 90000 * 100
        assert abs(kpis.output_ratio - expected) < 0.2

    def test_empty_daily(self):
        kpis = compute_kpis([], [], [])
        assert kpis.total_tokens == 0
        assert kpis.active_days == 0
        assert kpis.cache_hit_rate == 0

    def test_tokens_per_day(self):
        daily = _sample_daily()
        kpis = compute_kpis(daily, _sample_agents(), _sample_models())
        assert kpis.tokens_per_day == 45000


class TestGenerateDashboard:
    """Dashboard HTML generation."""

    def test_produces_valid_html(self):
        html = generate_dashboard(
            daily=_sample_daily(),
            sessions=_sample_sessions(),
            agents=_sample_agents(),
            models=_sample_models(),
            kpis=_sample_kpis(),
        )
        assert html.startswith("<!DOCTYPE html>")
        assert "</html>" in html

    def test_includes_chart_js_cdn(self):
        html = generate_dashboard(
            daily=_sample_daily(),
            sessions=_sample_sessions(),
            agents=_sample_agents(),
            models=_sample_models(),
            kpis=_sample_kpis(),
        )
        assert "chart.js@4" in html

    def test_includes_kpi_cards(self):
        html = generate_dashboard(
            daily=_sample_daily(),
            sessions=_sample_sessions(),
            agents=_sample_agents(),
            models=_sample_models(),
            kpis=_sample_kpis(),
        )
        assert "kpi-grid" in html
        assert "Total Tokens" in html

    def test_includes_delta_data(self):
        delta = {"total_tokens": "+15.2%", "tracked_cost": "-3.1%"}
        html = generate_dashboard(
            daily=_sample_daily(),
            sessions=_sample_sessions(),
            agents=_sample_agents(),
            models=_sample_models(),
            kpis=_sample_kpis(),
            delta=delta,
        )
        assert "+15.2%" in html
        assert "-3.1%" in html

    def test_no_placeholder_remnants(self):
        html = generate_dashboard(
            daily=_sample_daily(),
            sessions=_sample_sessions(),
            agents=_sample_agents(),
            models=_sample_models(),
            kpis=_sample_kpis(),
        )
        assert "SUMMARY_DATA" not in html
        assert "DAILY_DATA" not in html
        assert "SESSION_DATA" not in html
        assert "AGENT_DATA" not in html
        assert "MODEL_DATA" not in html
        assert "DELTA_DATA" not in html

    def test_source_label_in_title(self):
        html = generate_dashboard(
            daily=_sample_daily(),
            sessions=_sample_sessions(),
            agents=_sample_agents(),
            models=_sample_models(),
            kpis=_sample_kpis(),
            source="claude-code",
        )
        assert "claude-code" in html

    def test_json_data_embedded(self):
        html = generate_dashboard(
            daily=_sample_daily(),
            sessions=_sample_sessions(),
            agents=_sample_agents(),
            models=_sample_models(),
            kpis=_sample_kpis(),
        )
        assert '"total_tokens": 90000' in html or '"total_tokens":90000' in html

    def test_includes_sortable_tables(self):
        html = generate_dashboard(
            daily=_sample_daily(),
            sessions=_sample_sessions(),
            agents=_sample_agents(),
            models=_sample_models(),
            kpis=_sample_kpis(),
        )
        assert "sortTable" in html
        assert "agentTable" in html
        assert "modelTable" in html
        assert "sessionTable" in html

    def test_includes_all_charts(self):
        html = generate_dashboard(
            daily=_sample_daily(),
            sessions=_sample_sessions(),
            agents=_sample_agents(),
            models=_sample_models(),
            kpis=_sample_kpis(),
        )
        assert "tokensChart" in html
        assert "costChart" in html
        assert "cacheChart" in html
        assert "agentChart" in html
        assert "modelChart" in html


class TestWriteDashboard:
    """Dashboard file writing."""

    def test_writes_html_file(self, tmp_path):
        html = generate_dashboard(
            daily=_sample_daily(),
            sessions=_sample_sessions(),
            agents=_sample_agents(),
            models=_sample_models(),
            kpis=_sample_kpis(),
        )
        output_path = str(tmp_path / "dashboard.html")
        result = write_dashboard(html, output_path)
        assert Path(result).exists()
        content = Path(result).read_text()
        assert "<!DOCTYPE html>" in content

    def test_creates_parent_directory(self, tmp_path):
        html = "<html>test</html>"
        output_path = str(tmp_path / "subdir" / "nested" / "dashboard.html")
        result = write_dashboard(html, output_path)
        assert Path(result).exists()