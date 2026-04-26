"""Baseline snapshot management: save, load, compare, validate."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

DEFAULT_BASELINE_DIR = Path.home() / ".config" / "opencode" / "token-baselines"


def save_baseline(
    label: str,
    metrics: Dict[str, Any],
    daily: List[Dict[str, Any]],
    agents: List[Dict[str, Any]],
    models: List[Dict[str, Any]],
    output_dir: Optional[Path] = None,
) -> Path:
    """Save a baseline snapshot as JSON."""
    if output_dir is None:
        output_dir = DEFAULT_BASELINE_DIR
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    baseline_data = {
        "label": label,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "period_days": metrics.get("period_days", 30),
        "metrics": metrics,
        "daily": daily,
        "agents": agents,
        "models": models,
    }

    filepath = output_dir / f"baseline-{label}.json"
    filepath.write_text(json.dumps(baseline_data, indent=2, default=str))
    return filepath


def load_baseline(label: str, output_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Load a baseline snapshot by label."""
    if output_dir is None:
        output_dir = DEFAULT_BASELINE_DIR
    output_dir = Path(output_dir)

    filepath = output_dir / f"baseline-{label}.json"
    if not filepath.exists():
        raise FileNotFoundError(f"Baseline '{label}' not found at {filepath}")

    return json.loads(filepath.read_text(encoding="utf-8"))


def compare_baselines(current: Dict[str, Any], previous: Dict[str, Any]) -> Dict[str, Any]:
    """Compute percentage deltas between two baselines."""
    current_metrics = current.get("metrics", {})
    previous_metrics = previous.get("metrics", {})

    deltas: Dict[str, Any] = {}
    numeric_keys = [
        "total_tokens", "total_cost", "total_msgs", "input_tokens",
        "output_tokens", "cache_read", "reasoning_tokens",
    ]

    for key in numeric_keys:
        curr_val = current_metrics.get(key, 0)
        prev_val = previous_metrics.get(key, 0)
        deltas[key] = _pct_change(prev_val, curr_val)

    computed_keys = ["cache_hit_rate", "output_ratio", "cost_per_output_token", "tokens_per_day"]
    for key in computed_keys:
        curr_val = current_metrics.get(key, 0)
        prev_val = previous_metrics.get(key, 0)
        deltas[key] = _pct_change(prev_val, curr_val)

    deltas["current_metrics"] = current_metrics
    deltas["previous_metrics"] = previous_metrics
    deltas["current_label"] = current.get("label", "")
    deltas["previous_label"] = previous.get("label", "")
    return deltas


def validate_baselines(output_dir: Optional[Path] = None) -> List[str]:
    """Validate all baseline files in directory. Returns list of issues."""
    if output_dir is None:
        output_dir = DEFAULT_BASELINE_DIR
    output_dir = Path(output_dir)

    issues: List[str] = []
    if not output_dir.is_dir():
        return [f"Baseline directory does not exist: {output_dir}"]

    for filepath in sorted(output_dir.glob("baseline-*.json")):
        try:
            data = json.loads(filepath.read_text(encoding="utf-8"))
            required_keys = {"label", "created_at", "metrics"}
            missing = required_keys - set(data.keys())
            if missing:
                issues.append(f"{filepath.name}: missing keys {missing}")
        except json.JSONDecodeError as e:
            issues.append(f"{filepath.name}: invalid JSON — {e}")
        except OSError as e:
            issues.append(f"{filepath.name}: read error — {e}")

    return issues


def _pct_change(old: float, new: float) -> Any:
    """Calculate percentage change, returning 'N/A' for zero-division."""
    if old == 0:
        if new == 0:
            return "N/A"
        return float("inf")
    return round(((new - old) / old) * 100, 1)