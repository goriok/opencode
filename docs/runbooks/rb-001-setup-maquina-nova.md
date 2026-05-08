# RB-001 — Setup de Máquina Nova

**Quando usar**: Primeiro acesso em um novo Mac/Linux para configurar o ambiente OpenCode completo.
**Tempo estimado**: 15-20 minutos
**Pré-requisitos**: Acesso admin, Homebrew instalado

## Passos

### 1. Instalar dependências

```bash
brew install git uv
```

### 2. Instalar OpenCode

```bash
curl -fsSL https://opencode.ai/install | bash
```

### 3. Clonar config

```bash
git clone <repo-url> ~/.config/opencode
```

### 4. Instalar o CLI `oc`

```bash
cd ~/.config/opencode
uv tool install --editable .
```

### 5. Rodar setup

```bash
ocx setup
```

Isso clona agency-agents, converte, e instala os agentes. Já sincroniza os primários automaticamente.

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
ocx litellm setup
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
ocx litellm down && oc litellm up
```

Modelos z.ai disponíveis via proxy: `zai/glm-5.1`, `zai/glm-5-turbo`, `zai/glm-4.7`, `zai/glm-4.5-air`

## Validação

- [ ] `opencode` abre sem erros
- [ ] Agentes primários aparecem no menu
- [ ] `ocx litellm status` retorna `"I'm alive!"`
- [ ] `ocx litellm models` lista modelos (3 Anthropic + opencode-go + z.ai)
- [ ] `claude -p "ping"` retorna `pong` (via proxy)
- [ ] `localhost:4000/ui` abre com a virtual key `claude-code-max`

## Troubleshooting

- **Agentes não aparecem**: Re-executar `ocx setup`
- **Plugin não instala**: Verificar `opencode.jsonc` e permissões