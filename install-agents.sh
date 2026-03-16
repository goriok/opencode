#!/usr/bin/env bash
#
# install-agents.sh — Install agency-agents into the current project directory
#
# Usage (from your project root):
#   bash ~/.config/opencode/install-agents.sh
#
# Or with an explicit target directory:
#   bash ~/.config/opencode/install-agents.sh /path/to/project
#
# Installs agents to: <target>/.opencode/agents/

set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()  { printf "${GREEN}[opencode]${NC} %s\n" "$*"; }
warn()  { printf "${YELLOW}[opencode]${NC} %s\n" "$*"; }
error() { printf "${RED}[opencode]${NC} %s\n" "$*" >&2; exit 1; }

TARGET_DIR="${1:-$PWD}"
AGENTS_DIR="$TARGET_DIR/.opencode/agents"
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

if [[ -d "$AGENTS_DIR" ]]; then
  warn "Agents already installed at $AGENTS_DIR"
  warn "Remove the directory to reinstall: rm -rf $AGENTS_DIR"
  exit 0
fi

info "Cloning agency-agents (shallow)..."
git clone --depth=1 https://github.com/msitarzewski/agency-agents "$TMP/agency-agents"

info "Converting agents for opencode format..."
bash "$TMP/agency-agents/scripts/convert.sh" --tool opencode

info "Installing agents to $AGENTS_DIR..."
# The official install.sh targets \${PWD}/.opencode/agents — run from TARGET_DIR
(cd "$TARGET_DIR" && bash "$TMP/agency-agents/scripts/install.sh" --tool opencode --no-interactive)

COUNT=$(ls "$AGENTS_DIR"/*.md 2>/dev/null | wc -l | tr -d ' ')
info "Done! $COUNT agents installed to $AGENTS_DIR"
