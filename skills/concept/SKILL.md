---
name: concept
description: Documenta um conceito de AI Engineering aprendido na sessão atual. Gera um arquivo Markdown numerado em docs/concepts/ do projeto mcx-companion, sintetizando o que foi implementado, por que essa decisão foi tomada, e o que foi aprendido na prática. Ativar quando o usuário digitar /concept seguido do nome do conceito.
argument-hint: <nome-do-conceito>
allowed-tools: Read, Bash, Write, Glob
tool: claude-only
---

# Concept — Documentar Conceito de AI Engineering

## Quando Ativar

Ativar quando o usuário digitar `/concept <nome>`, onde `<nome>` é o conceito a documentar.

Exemplos:
- `/concept retry-com-backoff`
- `/concept streaming-llm-response`
- `/concept tool-calling-paralelo`

## Workflow

```
1. Ler o argumento             → identificar o conceito pelo nome fornecido
2. Analisar o contexto         → sintetizar da conversa atual o que foi implementado/descoberto
3. Ler docs existentes         → listar docs/concepts/ para determinar o próximo número
4. Ler arquivos relevantes     → buscar código real no projeto que ilustra o conceito
5. Redigir o documento         → usar o template abaixo
6. Salvar                      → docs/concepts/NN-nome-do-conceito.md
7. Confirmar                   → reportar o caminho e oferecer follow-up
```

## Regras

- O nome do arquivo segue o padrão `NN-kebab-case.md` onde `NN` é o próximo número sequencial (ex: `07-`, `08-`)
- Para determinar o número: listar `docs/concepts/*.md`, pegar o maior prefixo numérico e incrementar
- O documento deve conter código **real do projeto** — não pseudocódigo
- Seção "O que aprendemos na prática" é obrigatória e deve conter erros reais encontrados
- Escrever em **português**
- Seções seguem o template `[templates/concept-doc.md](templates/concept-doc.md)`
- Se o conceito já existir em um doc anterior, perguntar se quer complementar ou criar novo

## Prioridade de fontes de código

| Prioridade | Fonte | Quando usar |
|------------|-------|-------------|
| 1 | Código real do projeto (agent.py, server.py, etc.) | Conceito está implementado no projeto |
| 2 | Código adaptado/simplificado do projeto | Código real é complexo demais para ilustrar |
| 3 | Exemplo sintético mínimo | Conceito não está no projeto mas é relevante |

Sempre indicar a fonte acima do bloco:
- Código real → `# source: src/mcx_companion/agent.py`
- Sintético → `# exemplo sintético`

## Caminho dos docs

O projeto mcx-companion fica em `~/sources/mcx-companion/`.
Os conceitos ficam em `~/sources/mcx-companion/docs/concepts/`.

Se não conseguir determinar o caminho, usar `./docs/concepts/` relativo ao working directory.

## Anti-patterns

- ❌ Pseudocódigo quando o código real está disponível
- ❌ Número de arquivo duplicado ou fora de sequência
- ❌ Seção "O que aprendemos" vazia ou genérica
- ❌ Escrever em inglês (o projeto é em português)
- ❌ Criar doc sem verificar se o conceito já existe
