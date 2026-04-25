#!/usr/bin/env bash
#
# install-opencode-shortcuts.sh — Instala atalhos para OpenCode no shell
#
# Usage:
#   bash install-opencode-shortcuts.sh [--shell zsh|bash|fish]
#
# O que faz:
#   1. Detecta o shell do usuário
#   2. Adiciona alias e funções para opencode e opencode web

set -euo pipefail

SHELL_CONFIG=""
DETECTED_SHELL="${SHELL:-}"

detect_shell() {
  if [[ -n "$DETECTED_SHELL" ]]; then
    echo "$DETECTED_SHELL"
    return
  fi
  
  if [[ -n "${ZSH_VERSION:-}" ]]; then
    echo "zsh"
  elif [[ -n "${BASH_VERSION:-}" ]]; then
    echo "bash"
  elif command -v fish &>/dev/null; then
    echo "fish"
  else
    echo "zsh"
  fi
}

install_zsh() {
  local config_file="$HOME/.zshrc"
  
  if [[ ! -f "$config_file" ]]; then
    touch "$config_file"
  fi
  
  if grep -q "^# OpenCode Shortcuts" "$config_file" 2>/dev/null; then
    echo "[opencode] Atalhos já existem em ~/.zshrc"
    return
  fi
  
  cat >> "$config_file" << 'EOF'

# OpenCode Shortcuts
alias oc="opencode"
alias ocw="opencode web"

ocwserve() {
  local port="${1:-4096}"
  local host="${2:-0.0.0.0}"
  opencode web --port "$port" --hostname "$host"
}
EOF
  
  echo "[opencode] Atalhos instalados em ~/.zshrc"
}

install_bash() {
  local config_file="$HOME/.bashrc"
  
  if [[ ! -f "$config_file" ]]; then
    touch "$config_file"
  fi
  
  if grep -q "^# OpenCode Shortcuts" "$config_file" 2>/dev/null; then
    echo "[opencode] Atalhos já existem em ~/.bashrc"
    return
  fi
  
  cat >> "$config_file" << 'EOF'

# OpenCode Shortcuts
alias oc="opencode"
alias ocw="opencode web"

ocwserve() {
  local port="${1:-4096}"
  local host="${2:-0.0.0.0}"
  opencode web --port "$port" --hostname "$host"
}
EOF
  
  echo "[opencode] Atalhos instalados em ~/.bashrc"
}

install_fish() {
  local config_file="$HOME/.config/fish/config.fish"
  
  mkdir -p "$(dirname "$config_file")"
  
  if [[ ! -f "$config_file" ]]; then
    touch "$config_file"
  fi
  
  if grep -q "# OpenCode Shortcuts" "$config_file" 2>/dev/null; then
    echo "[opencode] Atalhos já existem em config.fish"
    return
  fi
  
  cat >> "$config_file" << 'EOF'

# OpenCode Shortcuts
alias oc "opencode"
alias ocw "opencode web"

function ocwserve
  set port (test -n "$argv[1]"; and echo "$argv[1]"; or echo "4096")
  set host (test -n "$argv[2]"; and echo "$argv[2]"; or echo "0.0.0.0")
  opencode web --port "$port" --hostname "$host"
end
EOF
  
  echo "[opencode] Atalhos instalados em Fish config"
}

main() {
  local shell_type=""
  
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --shell)
        shell_type="$2"
        shift 2
        ;;
      *)
        echo "Usage: $0 [--shell zsh|bash|fish]"
        exit 1
        ;;
    esac
  done
  
  if [[ -z "$shell_type" ]]; then
    shell_type=$(detect_shell)
  fi
  
  echo "[opencode] Instalando atalhos para shell: $shell_type"
  
  case "$shell_type" in
    zsh)
      install_zsh
      ;;
    bash)
      install_bash
      ;;
    fish)
      install_fish
      ;;
    *)
      echo "[opencode] Shell não suportado: $shell_type"
      exit 1
      ;;
  esac
  
  echo ""
  echo "用法 / Usage:"
  echo "  oc              — Abre OpenCode TUI"
  echo "  ocw             — Abre OpenCode Web (porta aleatória)"
  echo "  ocwserve 4096   — Abre Web na porta 4096"
  echo "  ocwserve 4096 127.0.0.1 — Web local only"
  echo ""
  echo "Para aplicar agora: source ~/.zshrc"
}

main "$@"