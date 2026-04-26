"""Test that the project scaffold is importable and discoverable."""

import importlib
import subprocess
import sys


def test_package_imports():
    """Verify token_tracker package imports cleanly."""
    import token_tracker

    assert hasattr(token_tracker, "__version__")
    assert token_tracker.__version__ == "1.0.0"


def test_submodules_importable():
    """Verify all submodules can be imported."""
    from token_tracker import models, pricing, cli, dashboard, baselines

    assert models is not None
    assert pricing is not None
    assert cli is not None
    assert dashboard is not None
    assert baselines is not None


def test_adapters_importable():
    """Verify adapter subpackage can be imported."""
    from token_tracker.adapters import opencode, claude_code

    assert opencode is not None
    assert claude_code is not None


def test_models_dataclass_creation():
    """Verify data models can be instantiated."""
    from token_tracker.models import TokenUsage, DailyAggregate, SessionSummary

    t = TokenUsage(total=100, input=50, output=50)
    assert t.total == 100
    assert t.input == 50

    d = DailyAggregate(day="2025-01-01", msgs=10, total_tokens=5000)
    assert d.day == "2025-01-01"
    assert d.total_tokens == 5000

    s = SessionSummary(session_id="abc", slug="test", title="Test")
    assert s.session_id == "abc"


def test_cli_help():
    """Verify CLI entry point responds to --help."""
    result = subprocess.run(
        [sys.executable, "-m", "token_tracker", "--help"],
        capture_output=True,
        text=True,
    )
    # Scaffold only — --help may not be fully implemented yet
    # Just verify the module runs without import errors
    assert result.returncode in (0, 2), f"CLI failed: {result.stderr}"


def test_pytest_discovers_tests():
    """Verify pytest collects at least this test."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "--collect-only", "-q"],
        capture_output=True,
        text=True,
        cwd=str(__import__("pathlib").Path(__file__).parent.parent),
    )
    assert result.returncode == 0, f"pytest collection failed: {result.stderr}"