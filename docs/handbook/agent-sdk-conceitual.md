# Agent SDK — Orquestração Independente de Agentes

> Um framework para construir sistemas multi-agente que coordenam workflows sem depender de CLI ou orquestrador central.

## Visão Geral

Um **Agent SDK** é uma biblioteca que permite que aplicações (scripts, servidores, automações) spawnem e orquestrem agentes especializados de forma programática. Diferente de um CLI que você controla interativamente, um SDK deixa você **definir fluxos** onde agentes colaboram com delegação de subtarefas, passagem de contexto, e decisões tomadas em código.

O SDK não substitui o CLI — é um complemento. O CLI é para exploração e execução interativa; o SDK é para pipelines, automação sem humano no loop, e integração com outros sistemas.

## Arquitetura Conceitual

| Camada | Responsabilidade | Exemplos |
|--------|------------------|----------|
| **API do SDK** | Spawn, contexto, stream de eventos | `query()`, `ClaudeAgentOptions`, async generators |
| **Agente Filho** | Executa tarefa delegada, acesso a tools/skills | read-only analysis, code generation, testing |
| **Orquestrador (seu código)** | Coordena fluxo, extrai output, decide próximo passo | pipeline de 3 agentes, curadoria manual, decisões condicionais |
| **Subsistemas** | Persistência, logging, integração externa | bancos de dados, Slack, Jira, git |

## Características Fundamentais

| Recurso | O que faz | Diferencial vs CLI |
|---------|-----------|-------------------|
| **Async/Streaming** | Eventos chegam em tempo real sem bloquear | CLI bloqueia até fim da resposta |
| **Least Privilege** | Cada agente recebe só as tools necessárias | CLI herda todas as permissões do usuário |
| **Composição de Skills** | Orquestrador invoca skills em sequência | CLI você navega manualmente entre skills |
| **Contexto Persistente** | Output de agente A é input para agente B | CLI não tem contexto automático entre turns |
| **Sem UI** | Roda headless em scripts, cron, CI/CD | CLI é interativo com UI |

## Casos de Uso

### Deep Research (Primário)

**Cenário:** Você quer investigar um tópico complexo — padrões de código, análise de segurança, recomendações de arquitetura — mas de forma **sistemática e reproduzível**.

**Fluxo com SDK:**
1. **Fase 1 — Exploração Rápida** (Ada Lovelace)
   - Busca padrões, identifica gaps, gera insights rápidos
   - Tools: `Read`, `Glob`, `WebSearch`
   
2. **Pausa Humana** (opcional)
   - Você revisa a análise, edita `analysis.md`, aprova ou redireciona
   
3. **Fase 2 — Deep Analysis** (Margaret Hamilton)
   - Pega insights da Ada, faz investigação profunda com ATAM/RM-ODP
   - Tools: `Read`, `WebFetch`, análise formal
   
4. **Fase 3 — Recomendações** (Alan Turing ou Grace Hopper)
   - Sintetiza em decisões arquiteturais ou plano de ação
   - Tools: `Read`, `Write` (RFC, relatório)

**Output:** Documento estruturado pronto para decisão.

### Automação em Pipelines

**Cenário:** PR mergeia, pipeline CI roda análise automática, resultado postado em Slack.

**Sem SDK:** Script bash chama CLI interativamente (lento, frágil).  
**Com SDK:** Agente análise spawned, resultado capturado em JSON, enviado via webhook.

### Integração com Sistemas Externos

**Cenário:** Jira recebe task, você quer que um agente analise o código relacionado e sugira PR.

**Com SDK:**
```python
task = jira.get_issue("PROJ-123")
async for event in query(
    f"analise o código de {task.repo_url} e sugira refactor",
    options=ClaudeAgentOptions(allowed_tools=["Read", "Bash"])
):
    ...
```

Resultado volta para Jira como comentário.

### Batch Processing

**Cenário:** 50 pull requests para revisar, 100 arquivos para migração.

**Com SDK:** Loop paralelo de agentes, cada um com seu slice, resultados consolidados.

## Quando Usar (vs CLI Interativo)

### ✅ Use SDK quando:
- Há fluxo **determinístico** — mesmos passos toda vez
- Precisa rodar **sem humano** — CI/CD, cron, serverless
- Envolve **múltiplos agentes** com contexto compartilhado
- Output vai para **outro sistema** — database, webhook, file
- Quer **reproduzibilidade** — mesma entrada = mesma saída

### ❌ Use CLI quando:
- Explorando / pesquisando **ad-hoc** — decisões dinâmicas
- Quer **UI visual** e contexto histórico no chat
- Iterando rápido com feedback imediato
- Output é consumido **por você agora** — não para integração futura

## Padrões de Implementação

### Padrão 1: Sequencial com Curadoria

```python
async def deep_research():
    # Fase 1: Ada explora
    analysis = await run_agent("Ada Lovelace", "explore code at {path}")
    
    # Pausa humana
    print("Análise completa. Revise e pressione Enter.")
    input()
    
    # Fase 2: Margaret aprofunda
    deep = await run_agent("Margaret Hamilton", f"aprofunde em: {analysis}")
    
    # Fase 3: Alan decide
    rfc = await run_agent("Alan Turing", f"escreva RFC com base em: {deep}")
    
    return rfc
```

### Padrão 2: Paralelo com Consolidação

```python
async def batch_analysis(files):
    tasks = []
    for file in files:
        task = run_agent(
            "Code Reviewer",
            f"revise {file}",
            allowed_tools=["Read", "Bash"]
        )
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    return consolidate(results)
```

### Padrão 3: Condicional (Decisão-Driven)

```python
async def adaptive_workflow(codebase):
    # Decide qual agent usar baseado em análise anterior
    analysis = await run_agent("Ada Lovelace", "classifique a qualidade do código")
    
    if "security_risk" in analysis:
        agent = "Security Engineer"
        task = "audit de segurança"
    elif "performance_issue" in analysis:
        agent = "Performance Benchmarker"
        task = "otimize gargalos"
    else:
        agent = "Code Reviewer"
        task = "melhore legibilidade"
    
    return await run_agent(agent, task)
```

## Diferenças vs Alternativas

| Abordagem | Força | Fraqueza |
|-----------|-------|----------|
| **CLI interativo** | Exploração natural, histórico em chat | Não automatiza, sem integração externa |
| **Agent SDK** | Pipelines reproduzíveis, sem UI overhead | Requer código, menos interativo |
| **RPA (Selenium, etc)** | Automatiza qualquer UI | Frágil, lento, manutenção alta |
| **LLM API raw** | Controle total | Sem tools nativas, sem agent patterns |
| **Multi-agent frameworks** (AutoGen, CrewAI) | Genérico, agnóstico | Menos integrado, overhead maior |

## Deep Research como Caso de Uso

Deep research é o caso mais natural para Agent SDK porque:

1. **Estrutura clara:** explore → analisa profundo → recomenda
2. **Agentes especializados:** Ada (rápida), Margaret (formal), Alan (decisão) têm papéis complementares
3. **Contexto acumulado:** cada fase depende da anterior
4. **Saída documentada:** resultado é um RFC ou relatório, não conversação
5. **Reproduzível:** mesma codebase → mesma análise

**Exemplo real:**
```
Input: "analise a arquitetura de autenticação em src/auth/"

Fase 1 (Ada, 2 min):
- Encontra 3 padrões: session, JWT, OAuth
- Identifica 2 gaps: sem rate limiting, tokens sem expiry
- Retorna: analysis.json

Fase 2 (Margaret, 10 min):
- Aplica ISO-25010 (security, reliability, maintainability)
- Mapa RM-ODP (trust, identity, policy domains)
- Retorna: formal-analysis.md

Fase 3 (Alan, 5 min):
- Escreve RFC com decisão: migrar para OAuth2 + rate limit
- Retorna: rfc-0007-auth-migration.md

Total: 17 minutos, documento pronto para implementação.
```

Sem SDK, você navegaria entre 3 turns no CLI manualmente, perdendo contexto entre eles.

## Implementação Mínima

Um Agent SDK mínimo precisa de:

1. **Função de spawn** — `query(prompt, options)` retorna async generator
2. **Options object** — `ClaudeAgentOptions(allowed_tools=[...], model=...)`
3. **Event streaming** — cada evento do agente filho flui para você
4. **Error handling** — timeouts, rate limits, falhas de tool

Tudo mais (memory, caching, skill composition, logging) é opcional.

## Quando Implementar

### Já implementado:
- Claude Agent SDK (Python)
- OpenCode plugin SDK (@opencode-ai/plugin, TypeScript)

### Faria sentido para:
- Sistemas que orquestram múltiplos agentes
- Pipelines automatizados sem UI
- Produtos que integram agentes como subsistema

### Não é necessário se:
- Você só precisa do CLI
- O caso é ad-hoc, exploração, pesquisa pessoal

---

*Parte do handbook de conceitos do OpenCode*
