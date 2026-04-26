"""Tests for the Prometheus metrics exporter."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from prometheus_client import REGISTRY

from token_tracker.models import DailyAggregate, ModelAggregate


def _clear_all_gauges() -> None:
    """Reset every exporter gauge so tests start with a clean slate."""
    from token_tracker.exporter import _METRICS

    for m in _METRICS:
        m.clear()


@pytest.fixture(autouse=True)
def _clean_registry() -> None:
    """Auto-cleared before each test to avoid cross-test leakage."""
    _clear_all_gauges()


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


class TestExporterRegistration:
    """Verifies that all four Prometheus gauges are registered on import."""

    def test_all_four_metrics_registered(self) -> None:
        """Importing exporter registers 4 gauge names in the default REGISTRY."""
        # Import triggers module-level Gauge() registration.
        import token_tracker.exporter  # noqa: F401

        names = {
            c.name
            for c in REGISTRY.collect()
            if hasattr(c, "name") and c.name.startswith("opencode_")
        }

        assert "opencode_tokens_total" in names
        assert "opencode_cost_tracked_total" in names
        assert "opencode_cost_estimated_total" in names
        assert "opencode_messages_total" in names
        assert len(names) == 4, f"Expected 4 opencode_ metrics, got {len(names)}"


# ---------------------------------------------------------------------------
# collect_metrics
# ---------------------------------------------------------------------------


def _make_mock_adapter(
    source: str,
    models: list | None = None,
    daily: list | None = None,
) -> MagicMock:
    """Build a MagicMock that looks like an adapter."""
    adapter = MagicMock()
    adapter.source = source
    adapter.fetch_models.return_value = models or []
    adapter.fetch_daily.return_value = daily or []
    return adapter


class TestCollectMetrics:
    """Tests for the ``collect_metrics()`` function."""

    @patch("token_tracker.exporter.OpenCodeAdapter")
    @patch("token_tracker.exporter.ClaudeCodeAdapter")
    def test_collect_metrics_with_mock_data(
        self,
        mock_claude_cls: MagicMock,
        mock_opencode_cls: MagicMock,
    ) -> None:
        """Gauge values reflect mocked adapter data after collection."""
        from token_tracker.exporter import collect_metrics

        opencode_model = ModelAggregate(
            model="deepseek-v4",
            provider="deepseek",
            msgs=10,
            total_tokens=5000,
            input_tokens=3000,
            output_tokens=2000,
            cache_read=100,
            tracked_cost=0.05,
            est_api_cost=0.10,
            source="opencode",
        )

        claude_model = ModelAggregate(
            model="claude-sonnet-4-6",
            provider="anthropic",
            msgs=5,
            total_tokens=2500,
            input_tokens=1500,
            output_tokens=1000,
            cache_read=200,
            tracked_cost=0.03,
            est_api_cost=0.08,
            source="claude_code",
        )

        mock_opencode = _make_mock_adapter(
            source="opencode",
            models=[opencode_model],
            daily=[DailyAggregate(day="2024-01-01", msgs=10, source="opencode")],
        )
        mock_opencode_cls.return_value = mock_opencode

        mock_claude = _make_mock_adapter(
            source="claude_code",
            models=[claude_model],
            daily=[DailyAggregate(day="2024-01-01", msgs=5, source="claude_code")],
        )
        mock_claude_cls.return_value = mock_claude

        collect_metrics(days=30)

        # Assert model-level gauges for opencode
        assert (
            REGISTRY.get_sample_value(
                "opencode_tokens_total",
                {"source": "opencode", "model": "deepseek-v4"},
            )
            == 5000
        )
        assert (
            REGISTRY.get_sample_value(
                "opencode_cost_tracked_total",
                {"source": "opencode", "model": "deepseek-v4"},
            )
            == 0.05
        )
        assert (
            REGISTRY.get_sample_value(
                "opencode_cost_estimated_total",
                {"source": "opencode", "model": "deepseek-v4"},
            )
            == 0.10
        )

        # Assert model-level gauges for claude_code
        assert (
            REGISTRY.get_sample_value(
                "opencode_tokens_total",
                {"source": "claude_code", "model": "claude-sonnet-4-6"},
            )
            == 2500
        )
        assert (
            REGISTRY.get_sample_value(
                "opencode_cost_tracked_total",
                {"source": "claude_code", "model": "claude-sonnet-4-6"},
            )
            == 0.03
        )
        assert (
            REGISTRY.get_sample_value(
                "opencode_cost_estimated_total",
                {"source": "claude_code", "model": "claude-sonnet-4-6"},
            )
            == 0.08
        )

        # Assert per-source message counts
        assert (
            REGISTRY.get_sample_value(
                "opencode_messages_total",
                {"source": "opencode"},
            )
            == 10
        )
        assert (
            REGISTRY.get_sample_value(
                "opencode_messages_total",
                {"source": "claude_code"},
            )
            == 5
        )

    @patch("token_tracker.exporter.OpenCodeAdapter")
    @patch("token_tracker.exporter.ClaudeCodeAdapter")
    def test_collect_metrics_empty_adapters(
        self,
        mock_claude_cls: MagicMock,
        mock_opencode_cls: MagicMock,
    ) -> None:
        """collect_metrics handles empty adapter results without crashing."""
        from token_tracker.exporter import collect_metrics

        mock_opencode = _make_mock_adapter(source="opencode")
        mock_opencode_cls.return_value = mock_opencode

        mock_claude = _make_mock_adapter(source="claude_code")
        mock_claude_cls.return_value = mock_claude

        # Should not raise
        collect_metrics(days=30)

        # Gauges should still be registered (default value 0)
        assert (
            REGISTRY.get_sample_value(
                "opencode_messages_total",
                {"source": "opencode"},
            )
            == 0
        )

    @patch("token_tracker.exporter.OpenCodeAdapter")
    @patch("token_tracker.exporter.ClaudeCodeAdapter")
    def test_messages_gauge_per_source(
        self,
        mock_claude_cls: MagicMock,
        mock_opencode_cls: MagicMock,
    ) -> None:
        """Messages gauge sums fetch_daily results per source."""
        from token_tracker.exporter import collect_metrics

        mock_opencode = _make_mock_adapter(
            source="opencode",
            models=[],
            daily=[
                DailyAggregate(day="2024-01-01", msgs=5, source="opencode"),
                DailyAggregate(day="2024-01-02", msgs=3, source="opencode"),
            ],
        )
        mock_opencode_cls.return_value = mock_opencode

        mock_claude = _make_mock_adapter(
            source="claude_code",
            models=[],
            daily=[
                DailyAggregate(day="2024-01-01", msgs=2, source="claude_code"),
            ],
        )
        mock_claude_cls.return_value = mock_claude

        collect_metrics(days=30)

        # 5 + 3 = 8 for opencode
        assert (
            REGISTRY.get_sample_value(
                "opencode_messages_total",
                {"source": "opencode"},
            )
            == 8
        )
        # 2 for claude_code
        assert (
            REGISTRY.get_sample_value(
                "opencode_messages_total",
                {"source": "claude_code"},
            )
            == 2
        )

    @patch("token_tracker.exporter.OpenCodeAdapter")
    @patch("token_tracker.exporter.ClaudeCodeAdapter")
    def test_adapter_failure_does_not_crash(
        self,
        mock_claude_cls: MagicMock,
        mock_opencode_cls: MagicMock,
    ) -> None:
        """When an adapter raises, collect_metrics logs a warning and continues."""
        from token_tracker.exporter import collect_metrics

        # OpenCode adapter fails on instantiation
        mock_opencode_cls.side_effect = RuntimeError("DB not found")

        # Claude adapter works fine
        mock_claude = _make_mock_adapter(
            source="claude_code",
            models=[],
            daily=[DailyAggregate(day="2024-01-01", msgs=3, source="claude_code")],
        )
        mock_claude_cls.return_value = mock_claude

        collect_metrics(days=30)

        # Claude data should be present
        assert (
            REGISTRY.get_sample_value(
                "opencode_messages_total",
                {"source": "claude_code"},
            )
            == 3
        )
