# RB-001 — Setup de Máquina Nova

**Quando usar**: Primeiro acesso em um novo Mac/Linux para configurar o ambiente OpenCode completo.
**Tempo estimado**: 15-20 minutos
**Pré-requisitos**: Acesso admin, Homebrew instalado

## Passos

### 1. Instalar dependências

```bash
brew install sqlite3 node bun git
```

### 2. Instalar OpenCode

```bash
curl -fsSL https://opencode.ai/install | bash
```

### 3. Clonar config

```bash
git clone <repo-url> ~/.config/opencode
```

### 4. Rodar setup

```bash
bash ~/.config/opencode/setup.sh
```

Isso clona agency-agents, converte, e instala os 191 agentes.

### 5. Sincronizar agentes primários

```bash
bash ~/.config/opencode/sync-primary-agents.sh
```

### 6. Instalar plugins

```bash
opencode plugin install @tarquinen/opencode-dcp@latest --global
opencode plugin install opencode-mem --global
opencode plugin install oh-my-openagent --global
opencode plugin install opencode-workspace --global
```

### 7. Verificar instalação

```bash
ls ~/.config/opencode/agents/ | wc -l   # Deve ser ~191
ls ~/.claude/agents/ | wc -l            # Deve ser 3-4 (primários)
opencode --version                        # Confirmar versão
```

### 8. Configurar LiteLLM proxy

```bash
bash ~/.config/opencode/litellm/setup-litellm.sh
```

Isso cria o `.env`, sobe o proxy Docker, gera a virtual key e configura o Claude Code automaticamente. Ver [RB-008](./rb-008-litellm-proxy-setup.md) para detalhes.

### 9. Configurar z.ai API key

A z.ai já roteia pelo proxy LiteLLM — basta preencher a API key no `.env`:

```bash
# Obtenha sua key em: https://z.ai/manage-apikey/apikey-list
# Edite o .env:
nano ~/.config/opencode/litellm/.env
# Preencha: ZAI_API_KEY=sua_key_aqui

# Reinicie o proxy para carregar a nova key:
cd ~/.config/opencode && task litellm:down && task litellm:up
```

Modelos z.ai disponíveis via proxy: `zai/glm-5.1`, `zai/glm-5-turbo`, `zai/glm-4.7`, `zai/glm-4.5-air`

### 10. Gerar primeiro baseline de tokens

```bash
bash ~/.config/opencode/token-tracker.sh --baseline "setup" --open
```

## Validação

- [ ] `opencode` abre sem erros
- [ ] Agentes primários aparecem no menu
- [ ] `token-tracker.sh --dry-run` mostra dados
- [ ] Dashboard abre no browser com dados
- [ ] `task litellm:status` retorna `"I'm alive!"`
- [ ] `task litellm:models` lista 15 modelos (3 Anthropic + 8 opencode-go + 4 z.ai)
- [ ] `claude -p "ping"` retorna `pong` (via proxy)
- [ ] `localhost:4000/ui` abre com a virtual key `claude-code-max`

## Troubleshooting

- **sqlite3 não encontrado**: `brew install sqlite3`
- **Agentes não aparecem**: Re-executar `setup.sh`
- **Plugin não instala**: Verificar `opencode.jsonc` e permissões
- **Dashboard vazio**: Ver RB-003