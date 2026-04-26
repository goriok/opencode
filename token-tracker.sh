#!/usr/bin/env bash
#
# token-tracker.sh — Unified token usage dashboard (Python wrapper)
#
# Usage:
#   bash ~/.config/opencode/token-tracker.sh [options]
#
# What it does:
#   1. Delegates to token_tracker Python package
#   2. Maintains backward compatibility with the original Bash-only interface
#   3. Supports new --source and --with-subagents flags for Claude Code data
#
# Options:
#   --output <path>         Output HTML path (default: ~/.config/opencode/token-dashboard.html)
#   --days <N>              Look back N days (default: 30)
#   --dry-run               Print stats to terminal, no HTML generation
#   --baseline <label>      Save baseline snapshot with this label
#   --compare <label>       Compare against a specific baseline
#   --validate              Validate existing baseline files
#   --open                  Open dashboard in browser after generation
#   --source <source>       Data source: opencode, claude-code, or auto (default: auto)
#   --claude-dir <path>     Claude Code projects directory (default: ~/.claude)
#   --with-subagents        Include Claude Code subagent data
#   --baseline-dir <path>   Baseline storage directory (default: ~/.config/opencode/token-baselines)

set -euo pipefail

# ── Colors ──────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()  { printf "${GREEN}[token-tracker]${NC} %s\n" "$*"; }
warn()  { printf "${YELLOW}[token-tracker]${NC} %s\n" "$*"; }
error() { printf "${RED}[token-tracker]${NC} %s\n" "$*" >&2; exit 1; }

# ── Locate Python Package ───────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PKG_DIR="${SCRIPT_DIR}/token_tracker"

if [[ ! -f "${PKG_DIR}/__main__.py" ]]; then
  error "token_tracker package not found at ${PKG_DIR}"
fi

# ── Translate & Delegate ────────────────────────────────────────────────────
PY_ARGS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --output)       PY_ARGS+=("--output" "$2"); shift 2 ;;
    --days|-d)      PY_ARGS+=("--days" "$2"); shift 2 ;;
    --dry-run)      PY_ARGS+=("--dry-run"); shift ;;
    --baseline)     PY_ARGS+=("--baseline" "$2"); shift 2 ;;
    --compare)      PY_ARGS+=("--compare" "$2"); shift 2 ;;
    --validate)     PY_ARGS+=("--validate"); shift ;;
    --open)         PY_ARGS+=("--open"); shift ;;
    --source)       PY_ARGS+=("--source" "$2"); shift 2 ;;
    --claude-dir)   PY_ARGS+=("--claude-dir" "$2"); shift 2 ;;
    --with-subagents) PY_ARGS+=("--with-subagents"); shift ;;
    --baseline-dir) PY_ARGS+=("--baseline-dir" "$2"); shift 2 ;;
    -h|--help)
      python3 -m token_tracker --help
      exit 0
      ;;
    *) warn "Unknown option: $1 (passing through)"; PY_ARGS+=("$1"); shift ;;
  esac
done

exec python3 -m token_tracker "${PY_ARGS[@]+"${PY_ARGS[@]}"}"