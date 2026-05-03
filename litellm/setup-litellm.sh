#!/usr/bin/env bash
# setup-litellm.sh — Configura o LiteLLM proxy em uma máquina nova
#
# Uso:
#   bash ~/.config/opencode/litellm/setup-litellm.sh              # setup completo
#   bash ~/.config/opencode/litellm/setup-litellm.sh --claude-code # só gera virtual key e configura Claude Code

set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

info()    { printf "${GREEN}[litellm]${NC} %s\n" "$*"; }
warn()    { printf "${YELLOW}[litellm]${NC} %s\n" "$*"; }
error()   { printf "${RED}[litellm]${NC} %s\n" "$*" >&2; exit 1; }
section() { printf "\n${CYAN}══ %s ══${NC}\n\n" "$*"; }

LITELLM_DIR="$HOME/.config/opencode/litellm"
ENV_FILE="$LITELLM_DIR/.env"
ENV_EXAMPLE="$LITELLM_DIR/.env.example"
CLAUDE_SETTINGS="$HOME/.claude/settings.json"
PROXY_URL="http://localhost:4000"
VIRTUAL_KEY_ALIAS="claude-code-max"
CLAUDE_MODELS='["claude-sonnet-4-6","claude-opus-4-7","claude-haiku-4-5-20251001"]'

# ─── Helpers ──────────────────────────────────────────────────────────────────

proxy_is_up() {
    curl -sf "$PROXY_URL/health/liveliness" &>/dev/null
}

wait_for_proxy() {
    local max=40 waited=0
    until proxy_is_up; do
        sleep 2; waited=$((waited + 2))
        [[ $waited -ge $max ]] && error "Proxy não respondeu em ${max}s — verifique: task litellm:logs"
        printf "."
    done
    echo ""
}

generate_virtual_key() {
    local master_key="$1"
    curl -sf -X POST "$PROXY_URL/key/generate" \
        -H "Authorization: Bearer $master_key" \
        -H "Content-Type: application/json" \
        -d "{\"key_alias\":\"$VIRTUAL_KEY_ALIAS\",\"models\":$CLAUDE_MODELS}" \
        | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('key',''))" 2>/dev/null
}

update_claude_settings() {
    local proxy_url="$1" virtual_key="$2"

    [[ ! -f "$CLAUDE_SETTINGS" ]] && {
        warn "~/.claude/settings.json não encontrado. Adicione manualmente:"
        echo ""
        echo '  "env": {'
        echo "    \"ANTHROPIC_BASE_URL\": \"$proxy_url\","
        echo "    \"ANTHROPIC_CUSTOM_HEADERS\": \"x-litellm-api-key: Bearer $virtual_key\""
        echo '  }'
        return
    }

    python3 - "$CLAUDE_SETTINGS" "$proxy_url" "$virtual_key" <<'PYEOF'
import json, sys
path, proxy_url, key = sys.argv[1], sys.argv[2], sys.argv[3]
with open(path) as f:
    d = json.load(f)
d['env'] = {
    "ANTHROPIC_BASE_URL": proxy_url,
    "ANTHROPIC_CUSTOM_HEADERS": f"x-litellm-api-key: Bearer {key}"
}
with open(path, 'w') as f:
    json.dump(d, f, indent=2)
PYEOF
    info "~/.claude/settings.json atualizado"
}

# ─── Modo: só Claude Code ────────────────────────────────────────────────────

if [[ "${1:-}" == "--claude-code" ]]; then
    section "Configurar Claude Code → LiteLLM"

    [[ -f "$ENV_FILE" ]] || error ".env não encontrado — rode o setup completo primeiro: bash $0"
    # shellcheck source=/dev/null
    source "$ENV_FILE"
    [[ -z "${LITELLM_MASTER_KEY:-}" ]] && error "LITELLM_MASTER_KEY não definida no .env"

    proxy_is_up || error "Proxy offline — rode: cd ~/.config/opencode && task litellm:up"

    info "Gerando virtual key '$VIRTUAL_KEY_ALIAS'..."
    VIRTUAL_KEY=$(generate_virtual_key "$LITELLM_MASTER_KEY")
    [[ -z "$VIRTUAL_KEY" ]] && error "Falha ao gerar virtual key — verifique se o proxy está rodando"
    info "Virtual key: ${VIRTUAL_KEY:0:24}..."

    update_claude_settings "$PROXY_URL" "$VIRTUAL_KEY"

    echo ""
    info "Testando Claude Code via proxy..."
    RESPONSE=$(claude -p "reply with exactly one word: pong" 2>/dev/null | tr -d '\n' | head -c 40 || true)
    if [[ "$RESPONSE" == *"pong"* ]] || [[ -n "$RESPONSE" ]]; then
        info "OK — Claude Code está roteando pelo proxy (resposta: $RESPONSE)"
    else
        warn "Teste inconclusivo — rode manualmente: claude -p 'ping'"
    fi

    echo ""
    info "Pronto! UI disponível em $PROXY_URL/ui (login: $LITELLM_MASTER_KEY)"
    exit 0
fi

# ─── Setup completo ───────────────────────────────────────────────────────────

section "Verificar pré-requisitos"

command -v docker &>/dev/null      || error "Docker não encontrado — instale em https://docs.docker.com/get-docker/"
docker compose version &>/dev/null || error "Docker Compose v2 não encontrado"
info "Docker: $(docker --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')"

section "Criar .env"

if [[ -f "$ENV_FILE" ]]; then
    warn ".env já existe — usando arquivo atual"
    info "Para recriar: rm $ENV_FILE && bash $0"
else
    cp "$ENV_EXAMPLE" "$ENV_FILE"
    info ".env criado em $ENV_FILE"
    cat <<'INSTRUCTIONS'

  Preencha as seguintes variáveis no arquivo:

  LITELLM_MASTER_KEY  → deixe 'sk-litellm-local' ou escolha outra string
  OPENCODE_GO_API_KEY → obtenha em https://opencode.ai/auth → "API Key"
  ANTHROPIC_API_KEY   → deixe VAZIO (Claude Code usa OAuth Max, não API key)
  ZAI_API_KEY         → obtenha em https://z.ai/manage-apikey/apikey-list

  NOTA: z.ai usa o Coding Plan endpoint (api.z.ai/api/coding/paas/v4).
        O config.yaml já aponta pro endpoint correto — basta preencher a key.

INSTRUCTIONS

    EDITOR="${VISUAL:-${EDITOR:-nano}}"
    if command -v "$EDITOR" &>/dev/null; then
        info "Abrindo .env no $EDITOR..."
        "$EDITOR" "$ENV_FILE"
    else
        warn "Edite manualmente antes de continuar: $ENV_FILE"
        read -r -p "Pressione Enter quando terminar..."
    fi
fi

# shellcheck source=/dev/null
source "$ENV_FILE"
[[ -z "${LITELLM_MASTER_KEY:-}" ]] && error "LITELLM_MASTER_KEY não definida no .env"

section "Subir o proxy"

info "Iniciando LiteLLM + Postgres (aguarde ~20s para migrations)..."
(cd "$LITELLM_DIR" && docker compose up -d) || error "Falha ao subir — verifique Docker"

wait_for_proxy
info "Proxy online em $PROXY_URL"

section "Verificar modelos"

MODEL_COUNT=$(curl -sf "$PROXY_URL/v1/models" \
    -H "Authorization: Bearer $LITELLM_MASTER_KEY" \
    | python3 -c "import json,sys; print(len(json.load(sys.stdin).get('data',[])))" 2>/dev/null || echo "0")

info "$MODEL_COUNT modelos carregados"
[[ "$MODEL_COUNT" -lt 5 ]] && warn "Poucos modelos — verifique OPENCODE_GO_API_KEY no .env"

section "Configurar Claude Code"

bash "$0" --claude-code

section "Próximos passos"

cat <<NEXT

  ✅ LiteLLM proxy rodando em $PROXY_URL
  ✅ Claude Code configurado para usar o proxy

  Pendente (manual):
     (nenhum — z.ai já roteia pelo proxy via ZAI_API_KEY)

   Operação diária (cd ~/.config/opencode):
    task litellm:up      → inicia o proxy
    task litellm:down    → para o proxy
    task litellm:logs    → monitora chamadas
    task litellm:status  → health check
    task litellm:models  → lista modelos

  UI: $PROXY_URL/ui  (login: $LITELLM_MASTER_KEY)

NEXT
