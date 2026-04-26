"""Claude Code JSONL adapter — reads token data from ~/.claude/projects/."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from token_tracker.adapters import SOURCE_CLAUDE_CODE
from token_tracker.models import (
    AgentAggregate,
    DailyAggregate,
    ModelAggregate,
    SessionSummary,
    SubagentInfo,
    TokenUsage,
)
from token_tracker.pricing import calculate_cost

logger = logging.getLogger(__name__)

DEFAULT_CLAUDE_DIR = Path.home() / ".claude"


class ClaudeCodeAdapter:
    """Reads token-usage data from Claude Code's JSONL session files."""

    def __init__(self, claude_dir: str | Path | None = None, source: str = SOURCE_CLAUDE_CODE) -> None:
        if claude_dir is None:
            claude_dir = DEFAULT_CLAUDE_DIR
        self.claude_dir = Path(claude_dir)
        self.projects_dir = self.claude_dir / "projects"
        self.source = source

    def _parse_iso_timestamp(self, ts: str) -> Optional[datetime]:
        """Parse ISO 8601 timestamp, handling various formats."""
        if not ts:
            return None
        for fmt in (
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S.%f%z",
            "%Y-%m-%dT%H:%M:%S%z",
        ):
            try:
                return datetime.strptime(ts, fmt)
            except (ValueError, TypeError):
                continue
        try:
            return datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            logger.warning("Could not parse timestamp: %s", ts)
            return None

    def _discover_session_files(self, days: int = 30) -> List[Path]:
        """Find all JSONL session files within the projects directory."""
        if not self.projects_dir.is_dir():
            logger.warning("Claude projects directory not found: %s", self.projects_dir)
            return []

        session_files: List[Path] = []

        for project_dir in self.projects_dir.iterdir():
            if not project_dir.is_dir():
                continue
            for jsonl_file in project_dir.glob("*.jsonl"):
                if jsonl_file.name.endswith(".meta.json"):
                    continue
                if jsonl_file.parent.name == "subagents":
                    continue
                session_files.append(jsonl_file)

        return session_files

    def _parse_jsonl_file(self, filepath: Path) -> List[Dict]:
        """Parse a JSONL file, skipping malformed lines."""
        records: List[Dict] = []
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError:
                        logger.debug(
                            "Skipping malformed line %d in %s", line_num, filepath
                        )
                        continue
                    records.append(record)
        except OSError as e:
            logger.warning("Could not read %s: %s", filepath, e)
        return records

    def _extract_usage(self, record: Dict) -> Optional[TokenUsage]:
        """Extract token usage from a single JSONL record."""
        if record.get("type") != "assistant":
            return None

        message = record.get("message", {})
        if not message:
            return None

        usage = message.get("usage", {})
        if not usage:
            return None

        # Handle iterations — sum across all iterations if present
        iterations = record.get("iterations")
        if iterations and isinstance(iterations, list):
            total_input = 0
            total_output = 0
            total_cache_create = 0
            total_cache_read = 0
            for iteration in iterations:
                iter_usage = iteration.get("usage", {})
                total_input += iter_usage.get("input_tokens", 0)
                total_output += iter_usage.get("output_tokens", 0)
                total_cache_create += iter_usage.get(
                    "cache_creation_input_tokens", 0
                )
                total_cache_read += iter_usage.get("cache_read_input_tokens", 0)
            input_tokens = total_input
            output_tokens = total_output
            cache_write = total_cache_create
            cache_read = total_cache_read
        else:
            input_tokens = usage.get("input_tokens", 0)
            output_tokens = usage.get("output_tokens", 0)
            cache_write = usage.get("cache_creation_input_tokens", 0)
            cache_read = usage.get("cache_read_input_tokens", 0)

        # Handle ephemeral cache variants
        cache_write += usage.get("cache_creation_ephemeral_1h_input_tokens", 0)
        cache_write += usage.get("cache_creation_ephemeral_5m_input_tokens", 0)
        cache_read += usage.get("cache_read_ephemeral_1h_input_tokens", 0)
        cache_read += usage.get("cache_read_ephemeral_5m_input_tokens", 0)

        reasoning = usage.get("reasoning_tokens", 0)

        model = message.get("model", "(unknown)")
        total_tokens = input_tokens + output_tokens + reasoning
        cost = calculate_cost(model, input_tokens, output_tokens, cache_read)

        return TokenUsage(
            total=total_tokens,
            input=input_tokens,
            output=output_tokens,
            reasoning=reasoning,
            cache_read=cache_read,
            cache_write=cache_write,
            cost=cost,
            timestamp=record.get("timestamp", ""),
        )

    def _get_all_records(self, days: int = 30) -> List[Tuple[Dict, TokenUsage]]:
        """Fetch all records with extracted token usage within the days window."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        results: List[Tuple[Dict, TokenUsage]] = []

        for filepath in self._discover_session_files(days):
            records = self._parse_jsonl_file(filepath)
            for record in records:
                usage = self._extract_usage(record)
                if usage is None:
                    continue

                # Filter by date
                ts_str = record.get("timestamp", "")
                if ts_str:
                    ts = self._parse_iso_timestamp(ts_str)
                    if ts is not None:
                        ts_utc = ts.replace(tzinfo=timezone.utc) if ts.tzinfo is None else ts.astimezone(timezone.utc)
                        if ts_utc < cutoff:
                            continue

                results.append((record, usage))

        return results

    def fetch_daily(self, days: int = 30) -> List[DailyAggregate]:
        """Aggregate token usage by day."""
        all_records = self._get_all_records(days)

        daily_map: Dict[str, Dict] = {}
        for record, usage in all_records:
            ts_str = usage.timestamp or record.get("timestamp", "")
            ts = self._parse_iso_timestamp(ts_str)
            if ts is None:
                continue
            day = ts.strftime("%Y-%m-%d")

            if day not in daily_map:
                daily_map[day] = {
                    "day": day,
                    "msgs": 0,
                    "total_tokens": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "reasoning_tokens": 0,
                    "cache_read": 0,
                    "cache_write": 0,
                    "total_cost": 0.0,
                }
            d = daily_map[day]
            d["msgs"] += 1
            d["total_tokens"] += usage.total
            d["input_tokens"] += usage.input
            d["output_tokens"] += usage.output
            d["reasoning_tokens"] += usage.reasoning
            d["cache_read"] += usage.cache_read
            d["cache_write"] += usage.cache_write
            d["total_cost"] += usage.cost

        return [
            DailyAggregate(**daily_map[day], source=self.source)
            for day in sorted(daily_map.keys())
        ]

    def fetch_sessions(self, days: int = 30) -> List[SessionSummary]:
        """Aggregate token usage by session."""
        all_records = self._get_all_records(days)

        session_map: Dict[str, Dict] = {}
        for record, usage in all_records:
            session_id = record.get("sessionId", "unknown")

            if session_id not in session_map:
                ts_str = usage.timestamp or record.get("timestamp", "")
                session_map[session_id] = {
                    "session_id": session_id,
                    "slug": "",
                    "title": "",
                    "parent_id": None,
                    "created": ts_str,
                    "msgs": 0,
                    "total_tokens": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "cost": 0.0,
                    "cache_read": 0,
                }
            s = session_map[session_id]
            s["msgs"] += 1
            s["total_tokens"] += usage.total
            s["input_tokens"] += usage.input
            s["output_tokens"] += usage.output
            s["cost"] += usage.cost
            s["cache_read"] += usage.cache_read

        return [
            SessionSummary(**s)
            for s in sorted(session_map.values(), key=lambda x: x["created"], reverse=True)
        ]

    def fetch_agents(self, days: int = 30) -> List[AgentAggregate]:
        """Aggregate token usage by agent (using model as proxy)."""
        all_records = self._get_all_records(days)

        agent_map: Dict[str, Dict] = {}
        for record, usage in all_records:
            message = record.get("message", {})
            model = message.get("model", "(unknown)")

            if model not in agent_map:
                agent_map[model] = {
                    "agent": model,
                    "msgs": 0,
                    "total_tokens": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "cache_read": 0,
                    "total_cost": 0.0,
                }
            a = agent_map[model]
            a["msgs"] += 1
            a["total_tokens"] += usage.total
            a["input_tokens"] += usage.input
            a["output_tokens"] += usage.output
            a["cache_read"] += usage.cache_read
            a["total_cost"] += usage.cost

        return [
            AgentAggregate(**a, source=self.source)
            for a in sorted(agent_map.values(), key=lambda x: x["total_tokens"], reverse=True)
        ]

    def fetch_models(self, days: int = 30) -> List[ModelAggregate]:
        """Aggregate token usage by model with pricing."""
        all_records = self._get_all_records(days)

        model_map: Dict[str, Dict] = {}
        for record, usage in all_records:
            message = record.get("message", {})
            model = message.get("model", "(unknown)")

            if model not in model_map:
                model_map[model] = {
                    "model": model,
                    "provider": "anthropic",
                    "msgs": 0,
                    "total_tokens": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "cache_read": 0,
                    "tracked_cost": 0.0,
                }
            m = model_map[model]
            m["msgs"] += 1
            m["total_tokens"] += usage.total
            m["input_tokens"] += usage.input
            m["output_tokens"] += usage.output
            m["cache_read"] += usage.cache_read
            m["tracked_cost"] += usage.cost

        results = []
        for m in model_map.values():
            est_api_cost = calculate_cost(
                m["model"],
                m["input_tokens"],
                m["output_tokens"],
                m["cache_read"],
            )
            results.append(
                ModelAggregate(
                    model=m["model"],
                    provider=m["provider"],
                    msgs=m["msgs"],
                    total_tokens=m["total_tokens"],
                    input_tokens=m["input_tokens"],
                    output_tokens=m["output_tokens"],
                    cache_read=m["cache_read"],
                    tracked_cost=m["tracked_cost"],
                    est_api_cost=est_api_cost,
                    source=self.source,
                )
            )
        return sorted(results, key=lambda x: x.total_tokens, reverse=True)

    def fetch_subagents(self, days: int = 30) -> List[SubagentInfo]:
        """Discover and aggregate subagent token usage."""
        if not self.projects_dir.is_dir():
            return []

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        subagents: List[SubagentInfo] = []

        for project_dir in self.projects_dir.iterdir():
            if not project_dir.is_dir():
                continue
            subagents_dir = project_dir / "subagents"
            if not subagents_dir.is_dir():
                continue

            for meta_file in subagents_dir.glob("agent-*.meta.json"):
                agent_type = ""
                description = ""
                try:
                    with open(meta_file, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                    agent_type = meta.get("agentType", "(unknown)")
                    description = meta.get("description", "")
                except (json.JSONDecodeError, OSError) as e:
                    logger.warning("Could not read meta file %s: %s", meta_file, e)
                    continue

                agent_stem = meta_file.stem.replace(".meta", "")
                jsonl_file = subagents_dir / f"{agent_stem}.jsonl"
                if not jsonl_file.exists():
                    continue

                total_usage = TokenUsage()
                model = ""
                parent_session_id = ""

                records = self._parse_jsonl_file(jsonl_file)
                for record in records:
                    usage = self._extract_usage(record)
                    if usage is None:
                        continue

                    ts_str = usage.timestamp or record.get("timestamp", "")
                    if ts_str:
                        ts = self._parse_iso_timestamp(ts_str)
                        if ts is not None:
                            ts_utc = ts.replace(tzinfo=timezone.utc) if ts.tzinfo is None else ts.astimezone(timezone.utc)
                            if ts_utc < cutoff:
                                continue

                    total_usage.total += usage.total
                    total_usage.input += usage.input
                    total_usage.output += usage.output
                    total_usage.reasoning += usage.reasoning
                    total_usage.cache_read += usage.cache_read
                    total_usage.cache_write += usage.cache_write
                    total_usage.cost += usage.cost

                    if not model:
                        model = record.get("message", {}).get("model", "(unknown)")
                    if not parent_session_id:
                        parent_session_id = record.get("sessionId", "")

                if total_usage.total > 0:
                    subagents.append(
                        SubagentInfo(
                            agent_type=agent_type,
                            description=description,
                            parent_session_id=parent_session_id,
                            tokens=total_usage,
                            model=model,
                        )
                    )

        return subagents