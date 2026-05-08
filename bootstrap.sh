#!/usr/bin/env bash
set -euo pipefail

# Colors
RED='\033[0;31m'
GRN='\033[0;32m'
YLW='\033[1;33m'
BLD='\033[1m'
RST='\033[0m'

info()  { printf "${GRN}[bootstrap]${RST} %s\n" "$*"; }
warn()  { printf "${YLW}[bootstrap]${RST} %s\n" "$*"; }
error() { printf "${RED}[bootstrap]${RST} %s\n" "$*" >&2; exit 1; }

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── 1. Ensure we're inside the repo ──────────────────────────────────────────
if [[ ! -f "$REPO_DIR/pyproject.toml" ]]; then
  error "Must run from the root of the opencode config repo."
fi

# ── 2. Ensure uv is available ─────────────────────────────────────────────────
if ! command -v uv &>/dev/null; then
  warn "uv not found — installing via the official installer..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  # Source the env so uv is on PATH for the rest of this script
  [[ -f "$HOME/.local/bin/env" ]] && source "$HOME/.local/bin/env"
  command -v uv &>/dev/null || error "uv install failed. Add ~/.local/bin to your PATH and retry."
  info "uv installed: $(uv --version)"
else
  info "uv found: $(uv --version)"
fi

# ── 3. Source uv env if needed ───────────────────────────────────────────────
if [[ -f "$HOME/.local/bin/env" ]] && ! command -v ocx &>/dev/null 2>&1; then
  source "$HOME/.local/bin/env"
fi

# ── 4. Install / reinstall ocx ───────────────────────────────────────────────
info "Installing ocx CLI (editable)..."
cd "$REPO_DIR"
uv tool install --editable . --reinstall

# Source again so ocx is reachable in this session
[[ -f "$HOME/.local/bin/env" ]] && source "$HOME/.local/bin/env"

# ── 5. Verify ─────────────────────────────────────────────────────────────────
if ! command -v ocx &>/dev/null; then
  warn "ocx installed but not found on PATH yet."
  warn "Run: source ~/.local/bin/env  (or open a new shell)"
else
  info "ocx installed: $(ocx --version 2>/dev/null || echo 'ok')"
  info "Location: $(which ocx)"
fi

# ── 6. Alias conflict warning ─────────────────────────────────────────────────
for rc in "$HOME/.zshrc" "$HOME/.bashrc" "$HOME/.bash_profile"; do
  if [[ -f "$rc" ]] && grep -q 'alias oc=' "$rc"; then
    warn "Found 'alias oc=...' in $rc — this only affects the 'oc' alias, not 'ocx'. No action needed."
  fi
done

# ── 7. Next step hint ─────────────────────────────────────────────────────────
printf "\n${BLD}Done!${RST} Next step to finish setup:\n\n"
printf "  ${GRN}ocx setup${RST}          # clone agency-agents + sync primary agents\n"
printf "  ${GRN}ocx litellm setup${RST}  # configure LiteLLM proxy\n\n"
