---
name: kanban-force-planner
description: Planejamento e organização de demandas no Kanban Force via MCP — hierarquia de cards, Gantt (dtStart/dtEnd), predecessores/sucessores, bloqueios e priorização. Invocar quando o usuário pedir para planejar sprints, organizar roadmap, criar hierarquia de cards, definir datas, ou analisar dependências.
argument-hint: "[planejar|roadmap|gantt|hierarquia|sprint|priorizar] [descrição do objetivo]"
tool: opencode-only
---

# Kanban Force — Planejamento e Organização

## Referência rápida de MCP tools

### Board tools
| Tool | Quando usar |
|---|---|
| `list_my_boards` | Listar todos os boards do usuário logado |
| `get_board(boardId)` | Obter colunas, lanes, membros e cards de um board |
| `get_board_members(boardId)` | Listar membros e permissões do board |

### Card tools
| Tool | Quando usar |
|---|---|
| `list_my_cards` | Cards do usuário logado (filtros: status, limit, page, order) |
| `list_cards(boardId)` | Todos os cards de um board |
| `get_card(cardId)` | Detalhes completos de um card (ID ou friendlyId) |
| `get_card_metrics(cardId)` | Tempo em cada coluna, lead time, cycle time |
| `get_card_moviments(cardId)` | Histórico de movimentos de coluna |
| `get_card_logs(cardId)` | Histórico de edições e alterações |
| `get_card_types` | Listar tipos disponíveis (INI, EPC, UST, OPS, BUG, TST…) |
| `create_card(...)` | Criar novo card |
| `update_card(cardId, ...)` | Atualizar campos de um card existente |
| `move_card(cardId, columnId)` | Mover card para outra coluna (mesmo board) |
| `block_card(cardId, blockedReason)` | Bloquear card com justificativa |
| `unblock_card(cardId)` | Desbloquear card |
| `archive_cards([cardIds])` | Arquivar cards concluídos |
| `add_comment_card(cardId, comment)` | Adicionar comentário |
| `list_comment_card(cardId)` | Listar comentários |

## Autenticação

Antes de qualquer operação, chame `get_board` ou `list_my_boards`. Se retornar erro de autenticação:

1. Informe o usuário que precisa do Bearer token
2. Instrua: abrir o app no browser → F12 → aba Network → qualquer requisição → header `Authorization`
3. Copiar o valor `Bearer eyJ...` e passar aqui
4. Chamar `auth_manual_token(bearer_token="Bearer eyJ...")`
5. Repetir a operação original

## Fluxo obrigatório antes de criar/atualizar cards

```
1. get_board(boardId)         → mapeia colunas e seus IDs
2. get_card_types()           → confirma tipos disponíveis
3. Executar operação
```

Nunca invente IDs de coluna ou de tipo — sempre busque da API.

## Hierarquia de tipos de card

```
INI (Iniciativa)
 └─ EPC (Épico)
     └─ UST (História de usuário)
         ├─ TST (Tarefa técnica)
         ├─ OPS (Operacional)
         └─ BUG (Bug)
```

- `ancestralCard` = ID do card pai imediato
- `descendentCards` = array de IDs dos filhos diretos
- Ao criar um card filho, sempre preencher `ancestralCard`
- Ao criar um card pai, preencher `descendentCards` com os IDs criados

## Planejamento Gantt

### Campos de data
- `dtStart` — data de início (ISO 8601, ex: `2024-03-01T12:00:00Z`)
- `dtEnd` — data de fim previsto
- `dtDone` — data de conclusão real (setada automaticamente ao concluir)

### Dependências sequenciais
- `predecessorCards` — cards que devem ser concluídos **antes** deste
- `successorCards` — cards que dependem deste card

### Regras de Gantt consistente
1. `dtStart` de um card filho nunca deve ser anterior ao `dtStart` do pai
2. `dtEnd` de um card filho nunca deve ser posterior ao `dtEnd` do pai
3. `dtStart` de um card sucessor deve ser ≥ `dtEnd` do predecessor
4. Ao planejar em lote, calcular datas em cascata: predecessores primeiro, sucessores depois

### Exemplo: criar roadmap sequencial
```
Etapa 1 (dtStart: 2024-04-01, dtEnd: 2024-04-14)
  └─ predecessorCards: []
  └─ successorCards: [<id_etapa_2>]

Etapa 2 (dtStart: 2024-04-15, dtEnd: 2024-04-28)
  └─ predecessorCards: [<id_etapa_1>]
  └─ successorCards: [<id_etapa_3>]
```

## Priorização e ordenação

- `order` — posição do card na coluna (número inteiro; menor = mais ao topo)
- Para repriorizar, use `update_card(cardId, order=<nova_posição>)`
- Para sprints: mover cards da coluna de backlog para "Fazendo" via `move_card`

## Mapeamento de status → coluna

Sempre confirmar IDs das colunas via `get_board`. Mapeamento típico:

| Status informado | Coluna alvo |
|---|---|
| Novo / Backlog / A fazer | Primeira coluna de backlog |
| Em andamento / Fazendo | Coluna "Fazendo" ou equivalente |
| Concluído / Done | Coluna do tipo "Concluído" |
| Bloqueado | Manter na coluna atual + chamar `block_card` |

## Gestão de bloqueios

Quando um impedimento é identificado:
1. `block_card(cardId, blockedReason="<descrição clara do impedimento>")`
2. Adicionar comentário com contexto: `add_comment_card(cardId, comment="Bloqueado: <detalhes>")`
3. Quando resolvido: `unblock_card(cardId)` + comentário explicando a resolução

## Planejamento de sprint

Fluxo recomendado:
1. `list_my_boards` → identificar board da sprint
2. `get_board(boardId)` → mapear colunas
3. `list_cards(boardId, status="Ativo")` → listar backlog
4. Selecionar cards com o usuário (por prioridade, tamanho, capacidade)
5. Para cada card selecionado: `update_card(cardId, dtStart=<início_sprint>, dtEnd=<fim_sprint>)`
6. Mover cards para coluna "Fazendo" se já iniciados: `move_card(cardId, columnId)`

## Análise de progresso

Para analisar o status de uma iniciativa:
1. `get_card(iniciativaId)` → ver `percDone`, `descendentCards`
2. Para cada card filho: `get_card_metrics(cardId)` → tempo em cada coluna
3. Identificar cards bloqueados (`blocked: true`) e sem data (`dtEnd: null`)
4. Gerar resumo tabular: card | status | responsável | dtEnd | percDone | bloqueado

## Criação em lote a partir de documento

Quando o usuário fornecer lista de itens para planejar:

1. `get_board(boardId)` → mapear colunas e membros
2. `get_card_types()` → confirmar tipos disponíveis
3. Para cada item, inferir:
   - **tipo**: iniciativa → INI, épico → EPC, história → UST, tarefa técnica → TST, bug → BUG
   - **coluna**: pelo status (ver tabela acima)
   - **datas**: calcular em cascata respeitando dependências
4. Criar cards em paralelo (múltiplas chamadas simultâneas por lote)
5. Atualizar `ancestralCard`/`descendentCards` para compor a hierarquia
6. Definir `predecessorCards`/`successorCards` para dependências
7. Confirmar ao usuário com resumo: card | tipo | coluna | dtStart | dtEnd | pai

## Boas práticas

- Sempre criar cards em paralelo quando independentes — maximizar velocidade
- Preencher `desc` com contexto: objetivo, critérios de aceite, links relevantes
- Usar `tags` para rastreabilidade: responsável, domínio, sprint (`["igor", "backend", "sprint-42"]`)
- Nunca deletar cards — usar `archive_cards` para cards concluídos
- Perguntar ao usuário antes de arquivar, bloquear ou mover em lote
- Ao atualizar datas em cascata, confirmar o plano com o usuário antes de executar
- Para cards com `percDone` entre 1 e 99, não mover para coluna "Concluído" — apenas atualizar o percentual
