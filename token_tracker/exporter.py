"""Prometheus metrics exporter for token usage data.

Exposes token usage metrics (totals, costs, message counts) from both
OpenCode and Claude Code adapters as Prometheus Gauge metrics at a
``/metrics`` HTTP endpoint.
"""

from __future__ import annotations

import logging
from typing import List

from prometheus_client import REGISTRY, Gauge, start_http_server

from token_tracker.adapters.claude_code import ClaudeCodeAdapter
from token_tracker.adapters.opencode import OpenCodeAdapter
from token_tracker.models import ModelAggregate

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Gauge metrics — registered with the default REGISTRY once at import time.
# All model-specific gauges carry ``source`` and ``model`` labels so that
# multi-source / multi-model data can be queried and aggregated in PromQL.
# ---------------------------------------------------------------------------

tokens_total = Gauge(
    "opencode_tokens_total",
    "Total tokens consumed per source and model",
    labelnames=["source", "model"],
)

cost_tracked_total = Gauge(
    "opencode_cost_tracked_total",
    "Tracked (recorded) cost per source and model",
    labelnames=["source", "model"],
)

cost_estimated_total = Gauge(
    "opencode_cost_estimated_total",
    "Estimated API cost per source and model",
    labelnames=["source", "model"],
)

messages_total = Gauge(
    "opencode_messages_total",
    "Total assistant messages per source",
    labelnames=["source"],
)

# Collect metric references for the unregister/re-register pattern.
_METRICS: List[Gauge] = [
    tokens_total,
    cost_tracked_total,
    cost_estimated_total,
    messages_total,
]


def collect_metrics(days: int = 30) -> None:
    """Query all adapters and populate the Prometheus gauges.

    Clears previous label combinations before re-populating so that
    stale combinations (e.g. a model that no longer appears in the
    data window) do not linger in the registry.
    """
    # Clear stale label combinations from previous collections.
    for metric in _METRICS:
        metric.clear()

    # Instantiate adapters — each may fail independently (missing DB,
    # projects directory, etc.) so we wrap each in a try/except.
    adapters: List = []

    try:
        adapters.append(OpenCodeAdapter(source="opencode"))
    except Exception as exc:
        logger.warning("Failed to instantiate OpenCodeAdapter: %s", exc)

    try:
        adapters.append(ClaudeCodeAdapter(source="claude_code"))
    except Exception as exc:
        logger.warning("Failed to instantiate ClaudeCodeAdapter: %s", exc)

    for adapter in adapters:
        source = adapter.source

        # ---- model-level metrics -----------------------------------------
        try:
            models: List[ModelAggregate] = adapter.fetch_models(days=days)
        except Exception as exc:
            logger.warning("fetch_models failed for %s: %s", source, exc)
            models = []

        for m in models:
            tokens_total.labels(source=m.source, model=m.model).set(m.total_tokens)
            cost_tracked_total.labels(source=m.source, model=m.model).set(
                m.tracked_cost
            )
            cost_estimated_total.labels(source=m.source, model=m.model).set(
                m.est_api_cost
            )

        # ---- per-source message counts -----------------------------------
        try:
            daily = adapter.fetch_daily(days=days)
        except Exception as exc:
            logger.warning("fetch_daily failed for %s: %s", source, exc)
            daily = []

        total_msgs = sum(d.msgs for d in daily)
        messages_total.labels(source=source).set(total_msgs)


def export_metrics(port: int = 9090, host: str = "0.0.0.0", days: int = 30) -> None:
    """Start the Prometheus HTTP server.

    Metrics are collected **once** at startup (via :func:`collect_metrics`)
    and persist in the default REGISTRY for the lifetime of the process.
    """
    collect_metrics(days=days)
    start_http_server(port, addr=host)
    logger.info("Prometheus exporter listening on %s:%s", host, port)
