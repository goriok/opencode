# Runbooks — Procedimentos Operacionais

> Procedimentos passo-a-passo para tarefas recorrentes e incidentes.

## Índice

| Runbook | Título | Quando usar |
|---------|--------|-------------|
| [RB-001](./rb-001-setup-maquina-nova.md) | Setup de máquina nova | Primeiro acesso em novo Mac |
| [RB-002](./rb-002-token-tracker-dashboard.md) | Gerar dashboard de tokens | Verificar uso, comparar estratégias |
| [RB-003](./rb-003-troubleshoot-dashboard-vazio.md) | Dashboard vazio ou com erros | Dashboard não mostra dados |
| [RB-004](./rb-004-adicionar-agente-primario.md) | Adicionar agente primário | Criar novo orquestrador |
| [RB-005](./rb-005-atualizar-agents.md) | Atualizar agents do agency-agents | Nova versão disponível |
| [RB-006](./rb-006-baseline-comparacao-estrategia.md) | Comparar estratégias com baseline | Avaliar mudança de modelo ou workflow |
| [RB-007](./rb-007-prometheus-exporter.md) | Iniciar e configurar o Prometheus exporter | Exportar métricas para Grafana |

## Formato

Cada runbook segue:

```markdown
# RB-NNNN — Título

**Quando usar**: [gatilho]
**Tempo estimado**: [duração]
**Pré-requisitos**: [o que precisa antes]

## Passos
1. ...
2. ...

## Validação
- [ ] Resultado esperado A

## Troubleshooting
- Se erro X: fazer Y
```