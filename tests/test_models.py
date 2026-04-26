"""Tests for data models."""

from token_tracker.models import (
    AgentAggregate,
    DailyAggregate,
    KPIs,
    MessageRecord,
    ModelAggregate,
    SessionSummary,
    SubagentInfo,
    TokenUsage,
)


def test_token_usage_defaults():
    t = TokenUsage()
    assert t.total == 0
    assert t.input == 0
    assert t.cost == 0.0
    assert t.timestamp is None


def test_token_usage_with_values():
    t = TokenUsage(total=100, input=60, output=40, cost=0.05, timestamp="2026-01-01")
    assert t.total == 100
    assert t.timestamp == "2026-01-01"


def test_session_summary_defaults():
    s = SessionSummary()
    assert s.session_id == ""
    assert s.parent_id is None


def test_daily_aggregate_fields():
    d = DailyAggregate(day="2026-01-15", msgs=10, total_tokens=5000)
    assert d.day == "2026-01-15"
    assert d.reasoning_tokens == 0


def test_agent_aggregate():
    a = AgentAggregate(agent="build", msgs=5, total_tokens=1000)
    assert a.agent == "build"
    assert a.cache_read == 0


def test_model_aggregate():
    m = ModelAggregate(model="claude-sonnet-4-6", provider="anthropic", msgs=100)
    assert m.provider == "anthropic"
    assert m.tracked_cost == 0.0
    assert m.est_api_cost == 0.0


def test_subagent_info():
    s = SubagentInfo(agent_type="explore", parent_session_id="abc123")
    assert s.agent_type == "explore"
    assert isinstance(s.tokens, TokenUsage)


def test_kpis():
    k = KPIs(total_tokens=100000, active_days=10, cache_hit_rate=0.45)
    assert k.cache_hit_rate == 0.45
    assert k.output_ratio == 0.0


def test_daily_aggregate_source_default():
    d = DailyAggregate()
    assert d.source == ""


def test_daily_aggregate_source():
    d = DailyAggregate(day="2026-01-15", source="opencode")
    assert d.source == "opencode"


def test_agent_aggregate_source_default():
    a = AgentAggregate()
    assert a.source == ""


def test_agent_aggregate_source():
    a = AgentAggregate(agent="build", source="claude_code")
    assert a.source == "claude_code"


def test_model_aggregate_source_default():
    m = ModelAggregate()
    assert m.source == ""


def test_model_aggregate_source():
    m = ModelAggregate(model="claude-sonnet-4-6", source="opencode")
    assert m.source == "opencode"


def test_kpis_source_default():
    k = KPIs()
    assert k.source == ""


def test_kpis_source():
    k = KPIs(total_tokens=100000, source="opencode")
    assert k.source == "opencode"


def test_message_record_source():
    m = MessageRecord(source="opencode", model="glm-5.1")
    assert m.source == "opencode"
    assert isinstance(m.tokens, TokenUsage)