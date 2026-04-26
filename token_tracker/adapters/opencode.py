"""OpenCode SQLite adapter — reads token data from opencode.db."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import List

from token_tracker.adapters import SOURCE_OPENCODE
from token_tracker.models import (
    AgentAggregate,
    DailyAggregate,
    ModelAggregate,
    SessionSummary,
)

DEFAULT_DB_PATH = Path.home() / ".local" / "share" / "opencode" / "opencode.db"

SQL_DAILY = """
SELECT date(m.time_created/1000, 'unixepoch') AS day,
       COUNT(*) AS msgs,
       COALESCE(SUM(json_extract(m.data, '$.tokens.total')), 0) AS total_tokens,
       COALESCE(SUM(json_extract(m.data, '$.tokens.input')), 0) AS input_tokens,
       COALESCE(SUM(json_extract(m.data, '$.tokens.output')), 0) AS output_tokens,
       COALESCE(SUM(json_extract(m.data, '$.tokens.reasoning')), 0) AS reasoning_tokens,
       COALESCE(SUM(json_extract(m.data, '$.tokens.cache.read')), 0) AS cache_read,
       COALESCE(SUM(json_extract(m.data, '$.tokens.cache.write')), 0) AS cache_write,
       COALESCE(SUM(json_extract(m.data, '$.cost')), 0) AS total_cost
FROM message m
WHERE json_extract(m.data, '$.role') = 'assistant'
  AND json_extract(m.data, '$.tokens.total') IS NOT NULL
  AND m.time_created >= strftime('%s', 'now', '-{days} days') * 1000
GROUP BY day ORDER BY day"""

SQL_SESSIONS = """
SELECT s.id, s.slug, s.title, s.parent_id,
       datetime(s.time_created/1000, 'unixepoch') AS created,
       COUNT(m.id) AS msgs,
       COALESCE(SUM(json_extract(m.data, '$.tokens.total')), 0) AS total_tokens,
       COALESCE(SUM(json_extract(m.data, '$.tokens.input')), 0) AS input_tokens,
       COALESCE(SUM(json_extract(m.data, '$.tokens.output')), 0) AS output_tokens,
       COALESCE(SUM(json_extract(m.data, '$.cost')), 0) AS total_cost,
       COALESCE(SUM(json_extract(m.data, '$.tokens.cache.read')), 0) AS cache_read
FROM session s
LEFT JOIN message m ON m.session_id = s.id
  AND json_extract(m.data, '$.role') = 'assistant'
  AND json_extract(m.data, '$.tokens.total') IS NOT NULL
WHERE s.time_created >= strftime('%s', 'now', '-{days} days') * 1000
GROUP BY s.id ORDER BY s.time_created DESC"""

SQL_AGENTS = """
SELECT json_extract(m.data, '$.agent') AS agent,
       COUNT(*) AS msgs,
       COALESCE(SUM(json_extract(m.data, '$.tokens.total')), 0) AS total_tokens,
       COALESCE(SUM(json_extract(m.data, '$.tokens.input')), 0) AS input_tokens,
       COALESCE(SUM(json_extract(m.data, '$.tokens.output')), 0) AS output_tokens,
       COALESCE(SUM(json_extract(m.data, '$.tokens.cache.read')), 0) AS cache_read,
       COALESCE(SUM(json_extract(m.data, '$.cost')), 0) AS total_cost
FROM message m
WHERE json_extract(m.data, '$.role') = 'assistant'
  AND json_extract(m.data, '$.tokens.total') IS NOT NULL
  AND m.time_created >= strftime('%s', 'now', '-{days} days') * 1000
GROUP BY agent ORDER BY total_tokens DESC"""

SQL_MODELS = """
SELECT json_extract(m.data, '$.modelID') AS model,
       json_extract(m.data, '$.providerID') AS provider,
       COUNT(*) AS msgs,
       COALESCE(SUM(json_extract(m.data, '$.tokens.total')), 0) AS total_tokens,
       COALESCE(SUM(json_extract(m.data, '$.tokens.input')), 0) AS input_tokens,
       COALESCE(SUM(json_extract(m.data, '$.tokens.output')), 0) AS output_tokens,
       COALESCE(SUM(json_extract(m.data, '$.tokens.cache.read')), 0) AS cache_read,
       COALESCE(SUM(json_extract(m.data, '$.cost')), 0) AS tracked_cost
FROM message m
WHERE json_extract(m.data, '$.role') = 'assistant'
  AND json_extract(m.data, '$.tokens.total') IS NOT NULL
  AND m.time_created >= strftime('%s', 'now', '-{days} days') * 1000
GROUP BY model ORDER BY total_tokens DESC"""


class OpenCodeAdapter:
    """Reads token-usage data from OpenCode's SQLite database."""

    def __init__(self, db_path: str | Path | None = None, source: str = SOURCE_OPENCODE) -> None:
        if db_path is None:
            db_path = DEFAULT_DB_PATH
        self.db_path = Path(db_path)
        self.source = source

    def _query(self, sql_template: str, days: int) -> list[dict]:
        sql = sql_template.format(days=days)
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            cur = conn.execute(sql)
            return [dict(row) for row in cur.fetchall()]
        finally:
            conn.close()

    def fetch_daily(self, days: int = 30) -> List[DailyAggregate]:
        rows = self._query(SQL_DAILY, days)
        return [
            DailyAggregate(
                day=r["day"],
                msgs=r["msgs"],
                total_tokens=r["total_tokens"],
                input_tokens=r["input_tokens"],
                output_tokens=r["output_tokens"],
                reasoning_tokens=r["reasoning_tokens"],
                cache_read=r["cache_read"],
                cache_write=r["cache_write"],
                total_cost=r["total_cost"],
                source=self.source,
            )
            for r in rows
        ]

    def fetch_sessions(self, days: int = 30) -> List[SessionSummary]:
        rows = self._query(SQL_SESSIONS, days)
        return [
            SessionSummary(
                session_id=r["id"],
                slug=r["slug"] or "",
                title=r["title"] or "",
                parent_id=r["parent_id"],
                created=r["created"],
                msgs=r["msgs"],
                total_tokens=r["total_tokens"],
                input_tokens=r["input_tokens"],
                output_tokens=r["output_tokens"],
                cost=r["total_cost"],
                cache_read=r["cache_read"],
            )
            for r in rows
        ]

    def fetch_agents(self, days: int = 30) -> List[AgentAggregate]:
        rows = self._query(SQL_AGENTS, days)
        return [
            AgentAggregate(
                agent=r["agent"] or "(unknown)",
                msgs=r["msgs"],
                total_tokens=r["total_tokens"],
                input_tokens=r["input_tokens"],
                output_tokens=r["output_tokens"],
                cache_read=r["cache_read"],
                total_cost=r["total_cost"],
                source=self.source,
            )
            for r in rows
        ]

    def fetch_models(self, days: int = 30) -> List[ModelAggregate]:
        rows = self._query(SQL_MODELS, days)
        return [
            ModelAggregate(
                model=r["model"] or "(unknown)",
                provider=r["provider"] or "",
                msgs=r["msgs"],
                total_tokens=r["total_tokens"],
                input_tokens=r["input_tokens"],
                output_tokens=r["output_tokens"],
                cache_read=r["cache_read"],
                tracked_cost=r["tracked_cost"],
                source=self.source,
            )
            for r in rows
        ]