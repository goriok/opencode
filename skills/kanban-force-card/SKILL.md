---
name: kanban-force-card
description: Cria, atualiza ou comenta cards no Kanban Force via MCP. Invocar quando o usuário pedir para criar card, atualizar card, mover card, comentar card ou qualquer operação no board do Kanban Force.
argument-hint: "[criar|atualizar|comentar|mover] [descrição da operação]"
tool: opencode-only
---

# Kanban Force — Gestão de Cards

## Configuração

**Board:** `69ea6b3fb8bea64f67f553a9`
Nome: IDM P90
URL: https://kanban-force.web.app/boards/69ea6b3fb8bea64f67f553a9

**Sempre pergunte** em qual board mostrando o id e nome a alteração deve ser realizada
O board pode ser sobrescrito pelo usuário — sempre use o board_id informado explicitamente quando fornecido.

## Autenticação

Antes de qualquer operação, tente chamar `get_board` com o board_id. Se retornar erro de autenticação:

1. Informe o usuário que precisa do Bearer token
2. Instrua: abrir o board no browser → F12 → aba Network → qualquer requisição → header `Authorization`
3. Copiar o valor `Bearer eyJ...` e passar aqui
4. Chamar `auth_manual_token(bearer_token="Bearer eyJ...")`
5. Repetir a operação original

## Fluxo obrigatório antes de criar/atualizar cards

Sempre execute em ordem:

1. `get_board(board_id)` — obtém colunas e IDs
2. `get_card_types()` — obtém tipos disponíveis (se necessário)
3. Executar a operação

Nunca invente IDs de coluna ou de tipo — sempre busque do board.

## Mapeamento de status → coluna

Use o nome da coluna para inferir onde colocar o card quando o usuário informar status:

| Status informado                         | Coluna alvo                                                    |
| ---------------------------------------- | -------------------------------------------------------------- |
| OK / Finalizado / Concluído              | Coluna do tipo `Concluído`                                     |
| Fazendo / Andamento / Em desenvolvimento | Coluna do tipo `Fazendo`                                       |
| Análise / Próximas                       | Coluna de backlog inicial (Próximas Atividades ou equivalente) |
| Despriorizado / Talvez                   | Coluna "Talvez um dia" ou equivalente                          |
| Sem status / novo                        | "Caixa de entrada" ou primeira coluna de backlog               |

Adapte conforme as colunas reais do board — sempre verifique via `get_board`.

## Tipos de card recomendados

| Contexto            | Tipo | ID                         |
| ------------------- | ---- | -------------------------- |
| Tarefa técnica      | TST  | `62bc98d80964b4d43916896d` |
| Pesquisa / Análise  | RSCH | `62deac138eb2931cccec63ca` |
| Melhoria            | IMP  | `62d55cb3f38c4880916e392f` |
| História de usuário | UST  | `60eedb232ea73100112d2c76` |
| Bug                 | BUG  | `60eedb232ea73100112d2c77` |
| Operacional         | OPS  | `61802f4b675210c427d61db7` |

Use `get_card_types()` para confirmar disponibilidade no board do usuário.

## Operações

### Criar card

```
create_card(
  board_id=<board_id>,
  current_column=<column_id>,
  card_type=<type_id>,
  name="[Responsável] Título do card",
  desc="Descrição detalhada",
  tags=["tag1", "tag2"]
)
```

- Prefixar o nome com `[NomeResponsável]` quando houver responsável identificado
- Tags em minúsculas, sem espaços ou vírgulas
- Criar múltiplos cards em paralelo quando o usuário fornecer uma lista

### Atualizar card

Fluxo obrigatório:

1. `get_cards(where="name:*TERMO*", limit=5)` — localiza o card pelo nome ou friendlyId
2. Extrair **todos** os campos do card retornado
3. `update_card(card_id, ...)` — enviar o objeto completo com os campos modificados

Nunca chamar `update_card` sem antes buscar o card atual.

### Mover card

1. Localizar o card com `get_cards`
2. Obter o `column_id` destino via `get_board`
3. `move_card(card_id, column_id)` — move dentro do mesmo board
4. `transfer_card(card_id, column_id)` — transfere para outro board

### Comentar card

1. Localizar o card com `get_cards`
2. `create_card_comment(card_id, description="texto do comentário")`

### Buscar card por código amigável (friendlyId)

```
get_cards(where="name:*STK-76F4*", limit=1)
```

## Criação em lote (a partir de documento)

Quando o usuário fornecer um documento ou lista de itens:

1. Fazer `get_board` para mapear todas as colunas disponíveis
2. Inferir coluna pelo status de cada item (ver tabela acima)
3. Inferir tipo pelo contexto (técnico → TST, análise → RSCH, melhoria → IMP)
4. Criar todos os cards em paralelo (múltiplas chamadas simultâneas por lote)
5. Confirmar ao usuário com resumo tabular: card | tipo | coluna criada

## Boas práticas

- Sempre criar cards em paralelo quando há múltiplos itens independentes
- Incluir `desc` com contexto relevante sempre que disponível (prazos, observações, sub-valores)
- Usar tags para identificar responsáveis e domínios: `["igor", "graceful", "golang"]`
- Após operações em lote, exibir resumo organizado por responsável ou por coluna
- Perguntar ao usuário antes de deletar ou arquivar cards
