#!/usr/bin/env bash
#
# setup.sh — Install agency-agents globally for opencode
#
# Run once per machine after cloning this repo:
#   bash ~/.config/opencode/setup.sh
#
# What it does:
#   1. Clones agency-agents (shallow) to a temp dir
#   2. Runs the official convert.sh --tool opencode
#   3. Copies generated agents to ~/.config/opencode/agents/
#   4. Cleans up

set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()  { printf "${GREEN}[opencode]${NC} %s\n" "$*"; }
warn()  { printf "${YELLOW}[opencode]${NC} %s\n" "$*"; }
error() { printf "${RED}[opencode]${NC} %s\n" "$*" >&2; exit 1; }

AGENTS_DIR="$HOME/.config/opencode/agents"
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

info "Cloning agency-agents (shallow)..."
git clone --depth=1 https://github.com/msitarzewski/agency-agents "$TMP/agency-agents"

info "Converting agents for opencode format..."
bash "$TMP/agency-agents/scripts/convert.sh" --tool opencode

info "Installing agents to $AGENTS_DIR..."
mkdir -p "$AGENTS_DIR"
cp "$TMP/agency-agents/integrations/opencode/agents/"*.md "$AGENTS_DIR/"

COUNT=$(ls "$AGENTS_DIR"/*.md 2>/dev/null | wc -l | tr -d ' ')
info "Done! $COUNT agents installed to $AGENTS_DIR"

info "Syncing primary agents to Claude Code..."
bash "$HOME/.config/opencode/sync-primary-agents.sh"

info "Making scripts executable..."
chmod +x "$HOME/.config/opencode/litellm/setup-litellm.sh"
