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
opencode plugin install oh-my-opencode --global
opencode plugin install opencode-workspace --global
opencode plugin install micode --global
```

### 7. Verificar instalação

```bash
ls ~/.config/opencode/agents/ | wc -l   # Deve ser ~191
ls ~/.claude/agents/ | wc -l            # Deve ser 3-4 (primários)
opencode --version                        # Confirmar versão
```

### 8. Gerar primeiro baseline de tokens

```bash
bash ~/.config/opencode/token-tracker.sh --baseline "setup" --open
```

## Validação

- [ ] `opencode` abre sem erros
- [ ] Agentes primários aparecem no menu
- [ ] `token-tracker.sh --dry-run` mostra dados
- [ ] Dashboard abre no browser com dados

## Troubleshooting

- **sqlite3 não encontrado**: `brew install sqlite3`
- **Agentes não aparecem**: Re-executar `setup.sh`
- **Plugin não instala**: Verificar `opencode.jsonc` e permissões
- **Dashboard vazio**: Ver RB-003