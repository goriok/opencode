# MADR — Markdown Architecture Decision Records

> Registros de decisões arquiteturais deste repositório, seguindo o formato [MADR](https://adr.github.io/madr/).

## Índice

| ADR | Título | Status |
|-----|--------|--------|
| [0001](./0001-token-tracking-via-bash-sqlite.md) | Token tracking via Bash + SQLite | Accepted |
| [0002](./0002-primary-agent-orchestration.md) | Primary agent orchestration | Accepted |
| [0003](./0003-plugin-coexistence-strategy.md) | Plugin coexistence strategy | Accepted |
| [0004](./0004-self-contained-html-dashboard.md) | Self-contained HTML dashboard for analytics | Accepted |
| [0005](./0005-prometheus-exporter-token-metrics.md) | Prometheus exporter for token metrics | Proposed |
| [0006](./0006-cache-optimization-opencode.md) | Cache optimization for opencode token usage | Accepted |
| [0007](./0007-opencode-go-model-strategy.md) | Opencode Go model routing strategy (4→7 models) | Accepted |
| [0008](./0008-litellm-proxy.md) | LiteLLM local proxy | Accepted |
| [0009](./0009-tier-routing-contract.md) | Tier-routing contract: agents/skills delegate to `oh-my-openagent.jsonc` | Accepted |

## Formato

Cada ADR segue o template MADR:

```markdown
# NNNN — Título da Decisão

- **Status**: [Proposed | Accepted | Deprecated | Superseded by ADR-NNNN]
- **Data**: YYYY-MM-DD
- **Contexto**: ...
- **Decisão**: ...
- **Consequências**: ...
```

## Quando criar um MADR

Sempre que uma decisão técnica:

- Afeta mais de um componente
- Tem trade-offs significativos
- Pode ser questionada no futuro
- Envolve escolha entre alternativas viáveis