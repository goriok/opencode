# MADR — Markdown Architecture Decision Records

> Registros de decisões arquiteturais deste repositório, seguindo o formato [MADR](https://adr.github.io/madr/).

## Índice

| ADR | Título | Status |
|-----|--------|--------|
| [0001](./0001-token-tracking-via-bash-sqlite.md) | Token tracking via Bash + SQLite | Accepted |
| [0002](./0002-primary-agent-orchestration.md) | Primary agent orchestration | Accepted |
| [0003](./0003-plugin-coexistence-strategy.md) | Plugin coexistence strategy | Accepted |
| [0004](./0004-self-contained-html-dashboard.md) | Self-contained HTML dashboard for analytics | Accepted |

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