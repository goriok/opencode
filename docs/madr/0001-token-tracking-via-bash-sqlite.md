# 0001 — Token Tracking via Bash + SQLite

- **Status**: Accepted
- **Data**: 2026-04-26

## Contexto

Precisávamos de um baseline de uso de tokens por sessão ao longo do tempo para comparar a eficácia de diferentes estratégias de IA. O OpenCode já grava todos os dados necessários (tokens, custo, agente, modelo) em um banco SQLite local, mas não oferece nenhuma forma de visualizar tendências ou comparar períodos.

## Decisão

Usar um script Bash que lê diretamente do SQLite existente do OpenCode e gera um dashboard HTML auto-contido com Chart.js. Sem servidor, sem dependências além de `sqlite3` e `awk`.

## Alternativas Consideradas

1. **Grafana + Prometheus** — Requer infraestrutura de servidor, exportador customizado, manutenção contínua. Overkill para uso pessoal.
2. **Jupyter Notebook** — Requer Python + libs, pesado demais para um dashboard simples. Difícil de compartilhar.
3. **CLI puro (texto)** — Funciona mas impossível ver tendências visuais. Sem baseline comparison.
4. **Web app com backend** — Complexidade desnecessária. Dados já estão locais no SQLite.

## Consequências

**Positivas:**
- Zero dependências além de sqlite3 (já presente)
- Dashboard auto-contido — abre no browser, sem servidor
- Baseline snapshots em JSON permitem comparação before/after
- Fácil de versionar e compartilhar (um script, um HTML)

**Negativas:**
- Chart.js requer CDN (não funciona offline sem vendor)
- Bash + python3 para processamento — não é tão portátil quanto Go
- Sem atualização em tempo real (re-executar o script para refresh)