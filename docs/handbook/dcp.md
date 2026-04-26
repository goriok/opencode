# Dynamic Context Pruning (DCP)

Plugin oficial para gerenciamento inteligente de contexto no OpenCode.

## O que é

DCP reduz automaticamente o uso de tokens durante sessões longas do OpenCode. Ele substitui conteúdo antigo por placeholders antes de enviar requisições ao LLM, mantendo o histórico original intacto no session storage.

## Comandos

| Comando | Descrição |
|---------|-----------|
| `/dcp` | Lista todos os comandos disponíveis |
| `/dcp context` | Mostra breakdown de tokens por categoria (system, user, assistant, tools) e economia obtida |
| `/dcp stats` | Mostra estatísticas cumulativas de pruning across todas as sessões |
| `/dcp sweep` | Remove todas as tool calls desde a última mensagem do usuário |
| `/dcp sweep N` | Remove as últimas N tool calls |
| `/dcp manual [on\|off]` | Toggle modo manual (AI não usa ferramentas de context management autonomamente) |
| `/dcp compress [focus]` | Força uma compressão individual. Texto opcional define o foco da compressão |
| `/dcp decompress ID` | Restaura uma compressão ativa pelo ID |
| `/dcp recompress ID` | Re-aplica uma compressão descomprimida |

## Modos de Compressão

- **Autônomo** (padrão): DCP gerencia automaticamente baseado em thresholds configurados
- **Manual**: Desabilita uso automático de ferramentas de context management

## Instalação

```bash
opencode plugin @tarquinen/opencode-dcp@latest --global
```

## Configuração

O plugin é adicionado automaticamente ao `opencode.jsonc`. Opções disponíveis:

- `enabled`: Habilita/desabilita o plugin
- `autoPrune`: Compressão automática ativada
- `threshold`: Limite de tokens para acionar compressão
- `deduplication`: Remove mensagens duplicadas
- `purgeErrors`: Remove erros de ferramentas após resolução
- `protectedTools`: Ferramentas que nunca são pruneadas

## Como Funciona

1. DCP monitora o contexto em cada turn
2. Quando o tamanho excede o threshold, ativa compressão
3. Conteúdo antigo é substituído por `(bN)` placeholders
4. Placeholders preservam referência sem consumir tokens
5. Histórico original permanece em session storage se necessário descomprimir