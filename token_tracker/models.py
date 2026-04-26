"""Data models for token tracking."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TokenUsage:
    total: int = 0
    input: int = 0
    output: int = 0
    reasoning: int = 0
    cache_read: int = 0
    cache_write: int = 0
    cost: float = 0.0
    timestamp: Optional[str] = None


@dataclass
class SessionSummary:
    session_id: str = ""
    slug: str = ""
    title: str = ""
    parent_id: Optional[str] = None
    created: str = ""
    msgs: int = 0
    total_tokens: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cost: float = 0.0
    cache_read: int = 0


@dataclass
class MessageRecord:
    source: str = ""
    model: str = ""
    agent: str = ""
    tokens: TokenUsage = field(default_factory=TokenUsage)
    cost: float = 0.0
    timestamp: str = ""


@dataclass
class DailyAggregate:
    day: str = ""
    msgs: int = 0
    total_tokens: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    reasoning_tokens: int = 0
    cache_read: int = 0
    cache_write: int = 0
    total_cost: float = 0.0
    source: str = ""


@dataclass
class AgentAggregate:
    agent: str = ""
    msgs: int = 0
    total_tokens: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read: int = 0
    total_cost: float = 0.0
    source: str = ""


@dataclass
class ModelAggregate:
    model: str = ""
    provider: str = ""
    msgs: int = 0
    total_tokens: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read: int = 0
    tracked_cost: float = 0.0
    est_api_cost: float = 0.0
    source: str = ""


@dataclass
class SubagentInfo:
    agent_type: str = ""
    description: str = ""
    parent_session_id: str = ""
    tokens: TokenUsage = field(default_factory=TokenUsage)
    model: str = ""


@dataclass
class KPIs:
    total_tokens: int = 0
    total_cost: float = 0.0
    total_msgs: int = 0
    active_days: int = 0
    cache_hit_rate: float = 0.0
    output_ratio: float = 0.0
    cost_per_output_token: float = 0.0
    tokens_per_day: int = 0
    avg_tracked_cost_day: float = 0.0
    avg_est_cost_day: float = 0.0
    source: str = ""