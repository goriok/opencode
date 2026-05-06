# Session Usage Analyzer

Python workflow que analisa o consumo de tokens em sessões do opencode usando o provider LiteLLM.

## Instalação

### Pré-requisitos

- Python 3.10 ou superior
- LiteLLM proxy rodando em `http://localhost:4100`
  - Para verificar: `task litellm:status`
  - Para iniciar: `task litellm:up`

### Instalar dependências

```bash
cd ~/.config/opencode/workflows
pip install -e .
```

Ou instalar apenas as dependências:

```bash
pip install httpx pydantic rich
```

## Uso

### Analisar a sessão atual

```bash
python session-usage-analyzer.py
```

### Analisar uma sessão específica

```bash
python session-usage-analyzer.py ses_abc123def456
```

### Formato de saída

Por padrão, o relatório é gerado em formato Markdown:

```bash
python session-usage-analyzer.py --format markdown
```

Para exibir uma versão formatada no terminal com tabelas coloridas:

```bash
python session-usage-analyzer.py --format terminal
```

### Como módulo Python

```python
import asyncio
from session_usage_analyzer import analyze_session

# Analisar sessão atual
report = asyncio.run(analyze_session())
print(report)

# Analisar sessão específica
report = asyncio.run(analyze_session(session_id="ses_abc123"))
print(report)
```

## Formato do Relatório

O relatório inclui:

### Resumo
- Total de mensagens (user/assistant)
- Número de tool calls
- Média de tools por mensagem
- Número de compressões DCP

### Token Metrics
- Input tokens
- Output tokens
- Reasoning tokens
- Cache read/write
- Custo total em dólares

### Top Tools
- Lista das ferramentas mais utilizadas
- Contagem de chamadas por ferramenta

### Análises
- ⚠️ Gargalos identificados
- ✅ Otimizações sugeridas

## Dependências

- **httpx** - Cliente HTTP assíncrono para comunicação com LiteLLM
- **pydantic** - Validação de dados (disponível mas não estritamente necessário)
- **rich** - Formatação rica de terminal para tabelas e painéis

## Integração com Skill

O workflow é invocado pela skill `session-usage-analyzer`. Para invocar:

```bash
/session-usage-analyzer
```

Ou com session_id específico:

```bash
/session-usage-analyzer ses_abc123def456
```

## Troubleshooting

### Error connecting to LiteLLM

```
Error: Error connecting to LiteLLM: Connection refused
Make sure LiteLLM is running at http://localhost:4100
```

**Solução:**
```bash
task litellm:up
```

### No current session found

```
Error: No current session found
```

**Solução:**
Passe um session_id específico como argumento.

## Desenvolvimento

### Executar testes (se implementados)

```bash
pytest
```

### Formatar código com Black

```bash
black session-usage-analyzer.py
```

### Verificar tipos com mypy

```bash
mypy session-usage-analyzer.py
```

## Licença

Parte do repositório opencode configuration.
