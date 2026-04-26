# Agentes Orchestration Guide — Coexistência Harmônica

> Guia prático para usar seus agentes orquestradores primários junto com os agentes dos plugins instalados.

## Quick Decision Tree

```
Entrada do usuário
    │
    ├─→ "Preciso criar algo novo" / "Implementar feature"
    │       Alan Turing (SDLC) → micode (executor)
    │
    ├─→ "Algo quebrou" / "Erro" / "Debug"
    │       Grace Hopper (troubleshooting)
    │
    ├─→ "Revise/analise isso" / "Audite"
    │       Ada Lovelace (análise) → /review (workspace)
    │
    ├─→ "Quick fix" / "Rapidinho"
    │       oh-my-opencode (ultrawork)
    │
    └─→ "Pesquise" / "Como funcionam X"
            oh-my-opencode (Librarian/Explorer)
```

---

## Camada 1: Orquestradores Primários (Seus)

| Orquestrador | Framework | Quando Invocar |
|-------------|-----------|----------------|
| **Alan Turing** | SDLC: Requirements → Monitoring | Feature completo, novo projeto |
| **Grace Hopper** | Incident: Detection → Prevention | Problemas, bugs, falhas |
| **Ada Lovelace** | ATAM: Scope → Validation | Análise profunda, arquitetura |

### Setup dos Orquestrados

```
/alan-turing   → Skill: alan-turing
/grace-hopper → Skill: grace-hopper  
/ada-lovelace → Skill: ada-lovelace
```

---

## Camada 2: Plugins

### oh-my-opencode (Quick + Ultrawork)

| Agente | Propósito | Melhor Uso |
|--------|----------|----------|
| **Sisyphus** | Orquestração geral | Quick tasks integradas |
| **Oracle** | Q&A, arquitetura | Perguntas técnicas |
| **Librarian** | Documentação | Buscar docs |
| **Explorer** | Codebase exploration | Entender projeto |
| **Multimodal** | Imagens/mídia | Analisar telas |

### opencode-workspace (Pesquisa + Review)

| Agente | Propósito | Melhor Uso |
|--------|----------|----------|
| **researcher** | Pesquisa externa | Web search, docs |
| **reviewer** | Code review | Revisão estruturada |
| **coder** | Implementação | Tasks isoladas |
| **scribe** | Documentação | WRITE sem shell |

### micode (Estrutura + TDD)

| Agente | Propósito | Melhor Uso |
|--------|----------|----------|
| **commander** | Orquestrador micode | Workflow completo |
| **executor** | Execução micode | Implementação TDD |
| **planner** | Planning | Tasks detalhadas |

---

## Integração por Tipo de Task

### 🔨 Novo Feature / Projeto

```
1. Alan Turing (SDLC) 
   → Cria escopo + requisitos
2. micode (commander)
   → Brainstorm → Plan → Implement
3. oh-my-opencode (ultrawork se necessário)
   → Paralelização extrema
```

### 🐛 Bug / Incidente

```
1. Grace Hopper (troubleshooting)
   → Triagem → RCA → Correção
2. opencode-workspace (reviewer)
   → Verifica correção
```

### 📊 Análise / Arquitetura

```
1. Ada Lovelace (ATAM)
   → Investigation → Tradeoffs
2. opencode-workspace (researcher)
   → Pesquisa contexto
3. oh-my-opencode (Oracle)
   → Q&A arquitetural
```

### 🔍 Code Review

```
1. /review command (workspace)
   → Review estruturado
2. oh-my-opencode (Sisyphus)
   → Correções se necessárias
```

### 📖 Pesquisa / Documentação

```
1. oh-my-opencode (Librarian)
   → Busca em docs locais
2. opencode-workspace (researcher)
   → Search externo (context7, exa)
```

---

## Command Quick Reference

```
/alan-turing     → Iniciar feature completo
/grace-hopper   → Debug/incidente
/ada-lovelace   → Análise/arquitetura
/ultrawork     → Modo paralelo intenso
/review        → Code review (workspace)
/mem           → Memória persistente
/dcp           → Gerenciamento contexto
```

---

## Anti-Conflitos

| Situação | Solução |
|---------|--------|
| Turing + micode duelando | Turing = escopo, micode = execução |
| Hopper + Oh-My-Opencode | Hopper = diagnóstico, Oh-My-Opencode = fix |
| Lovelace + Workspace | Lovelace = análise, Workspace = research |
| Todos querendo usar agente próprio | Use a decision treeabove |

---

## Conflito de Dominância

Se dois orquestradores querem actuar no mesmo contexto:

**Regra de Preempção**:

```
1. Incidente ativo (bug, erro) → Grace Hopper wins
2. Decisão arquitetural → Ada Lovelace wins  
3. Feature novo → Alan Turing wins
4. Quick/none-of-above → oh-my-opencode wins
```

---

## Session Recovery

Se perder contexto entre sessões:

| Plugin | Ferramenta |
|--------|------------|
| opencode-mem | `/mem search <topic>` |
| micode | `thoughts/ledgers/` |
| DCP | `/dcp compress` → pode /dcp decompress |

---

*Handbook de coexistência — baseado nos handbooks originais dos plugins*