# 0004 — Self-Contained HTML Dashboard for Analytics

- **Status**: Accepted
- **Data**: 2026-04-26

## Contexto

Dashboards de analytics tipicamente requerem backend + database + deploy. Para uso pessoal com dados locais (SQLite), isso é excessivo. Precisávamos de uma solução que qualquer pessoa na equipe pudesse gerar e compartilhar com um comando.

## Decisão

Gerar HTML auto-contido com dados inline como JSON e Chart.js via CDN. O resultado é um arquivo único que qualquer browser abre sem infraestrutura.

## Alternativas Consideradas

1. **React app com Vite** — Requer Node, build step, deploy. Muito overhead.
2. **Streamlit / Gradio** — Requer Python runtime, servidor. Não é portátil.
3. **Jupyter Widgets** — Requer Jupyter, não é compartilhável facilmente.
4. **SVG estático** — Sem interatividade (zoom, hover, sort).

## Consequências

**Positivas:**
- Um arquivo HTML = dashboard completo
- Zero infraestrutura — `bash token-tracker.sh && open dashboard.html`
- Compartilhável por email, Slack, git
- Dados sempre atualizados ao re-gerar

**Negativas:**
- Requer internet para Chart.js CDN (a menos que vendored)
- Sem atualização em tempo real — precisa re-executar o script
- HTML pode ficar grande com muitos dados (30KB+ para 30 dias)