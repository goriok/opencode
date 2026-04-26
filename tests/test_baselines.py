"""Tests for baseline snapshot management."""

import json
from pathlib import Path

import pytest

from token_tracker.baselines import (
    compare_baselines,
    load_baseline,
    save_baseline,
    validate_baselines,
    _pct_change,
)


@pytest.fixture
def baseline_dir(tmp_path: Path) -> Path:
    return tmp_path / "baselines"


def test_save_and_load_roundtrip(baseline_dir: Path) -> None:
    """Save baseline then load it — data preserved exactly."""
    metrics = {"total_tokens": 100000, "total_cost": 5.50, "period_days": 30}
    daily = [{"day": "2025-01-01", "msgs": 10, "total_tokens": 5000}]
    agents = [{"agent": "build", "msgs": 10, "total_tokens": 5000}]
    models = [{"model": "claude-sonnet-4-6", "msgs": 10, "total_tokens": 5000}]

    filepath = save_baseline("test-roundtrip", metrics, daily, agents, models, baseline_dir)
    assert filepath.exists()
    assert filepath.name == "baseline-test-roundtrip.json"

    loaded = load_baseline("test-roundtrip", baseline_dir)
    assert loaded["label"] == "test-roundtrip"
    assert loaded["metrics"]["total_tokens"] == 100000
    assert loaded["metrics"]["total_cost"] == 5.50
    assert loaded["daily"] == daily
    assert loaded["agents"] == agents
    assert loaded["models"] == models
    assert "created_at" in loaded


def test_save_creates_directory(baseline_dir: Path) -> None:
    """save_baseline creates the directory if it doesn't exist."""
    nested = baseline_dir / "nested" / "dir"
    save_baseline("test-nested", {}, [], [], [], nested)
    assert (nested / "baseline-test-nested.json").exists()


def test_load_baseline_not_found(baseline_dir: Path) -> None:
    """load_baseline raises FileNotFoundError for missing baseline."""
    with pytest.raises(FileNotFoundError):
        load_baseline("nonexistent", baseline_dir)


def test_compare_positive_change() -> None:
    """compare_baselines computes +20% when tokens go 1000→1200."""
    previous = {"metrics": {"total_tokens": 1000, "total_cost": 10.0}}
    current = {"metrics": {"total_tokens": 1200, "total_cost": 12.0}}

    deltas = compare_baselines(current, previous)
    assert deltas["total_tokens"] == 20.0
    assert deltas["total_cost"] == 20.0


def test_compare_negative_change() -> None:
    """compare_baselines computes -20% when tokens go 1000→800."""
    previous = {"metrics": {"total_tokens": 1000}}
    current = {"metrics": {"total_tokens": 800}}

    deltas = compare_baselines(current, previous)
    assert deltas["total_tokens"] == -20.0


def test_compare_zero_division() -> None:
    """compare_baselines returns 'N/A' and inf for edge cases."""
    previous = {"metrics": {"total_tokens": 0}}
    current = {"metrics": {"total_tokens": 0}}
    deltas = compare_baselines(current, previous)
    assert deltas["total_tokens"] == "N/A"

    previous = {"metrics": {"total_tokens": 0}}
    current = {"metrics": {"total_tokens": 500}}
    deltas = compare_baselines(current, previous)
    assert deltas["total_tokens"] == float("inf")


def test_compare_includes_labels() -> None:
    """compare_baselines includes baseline labels in output."""
    previous = {"label": "baseline-v1", "metrics": {"total_tokens": 100}}
    current = {"label": "baseline-v2", "metrics": {"total_tokens": 150}}

    deltas = compare_baselines(current, previous)
    assert deltas["current_label"] == "baseline-v2"
    assert deltas["previous_label"] == "baseline-v1"


def test_validate_good_baselines(baseline_dir: Path) -> None:
    """validate_baselines returns empty list for valid files."""
    save_baseline("valid1", {"total_tokens": 100}, [], [], [], baseline_dir)
    save_baseline("valid2", {"total_tokens": 200}, [], [], [], baseline_dir)

    issues = validate_baselines(baseline_dir)
    assert issues == []


def test_validate_missing_keys(baseline_dir: Path) -> None:
    """validate_baselines reports missing required keys."""
    baseline_dir.mkdir(parents=True, exist_ok=True)
    bad_data = {"label": "bad"}
    filepath = baseline_dir / "baseline-bad.json"
    filepath.write_text(json.dumps(bad_data))

    issues = validate_baselines(baseline_dir)
    assert len(issues) == 1
    assert "missing keys" in issues[0]


def test_validate_invalid_json(baseline_dir: Path) -> None:
    """validate_baselines reports invalid JSON."""
    baseline_dir.mkdir(parents=True, exist_ok=True)
    filepath = baseline_dir / "baseline-corrupt.json"
    filepath.write_text("{not valid json}")

    issues = validate_baselines(baseline_dir)
    assert len(issues) == 1
    assert "invalid JSON" in issues[0]


def test_validate_missing_dir(tmp_path: Path) -> None:
    """validate_baselines reports when directory doesn't exist."""
    issues = validate_baselines(tmp_path / "nonexistent")
    assert len(issues) == 1
    assert "does not exist" in issues[0]


def test_pct_change_normal() -> None:
    assert _pct_change(100, 120) == 20.0
    assert _pct_change(100, 80) == -20.0


def test_pct_change_zero_old() -> None:
    assert _pct_change(0, 0) == "N/A"
    assert _pct_change(0, 100) == float("inf")


def test_backward_compat_format(baseline_dir: Path) -> None:
    """Baseline JSON format is backward-compatible with Bash version."""
    metrics = {
        "total_tokens": 50000,
        "total_cost": 0.75,
        "total_msgs": 100,
        "input_tokens": 30000,
        "output_tokens": 15000,
        "cache_hit_rate": 25.0,
        "output_ratio": 30.0,
        "cost_per_output_token": 0.00005,
        "tokens_per_day": 1666,
        "period_days": 30,
    }
    filepath = save_baseline("compat", metrics, [], [], [], baseline_dir)

    raw = json.loads(filepath.read_text())
    assert "label" in raw
    assert "created_at" in raw
    assert "metrics" in raw
    assert "daily" in raw
    assert "agents" in raw
    assert "models" in raw
    assert "period_days" in raw