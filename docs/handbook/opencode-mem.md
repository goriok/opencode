# opencode-mem — Persistent Memory for AI Agents

> Sistema de memória persistente com vector database para OpenCode

## Overview

`opencode-mem` é um plugin que dá aos agentes de coding memória persistente usando um vector database local. Ele permite retenção de contexto de longo prazo entre sessões usando tecnologia de indexação vetorial.

## Core Features

| Feature | Descrição |
|---------|----------|
| **Local Vector Database** | SQLite + USearch para indexação vetorial |
| **Persistent Project Memories** | Memórias por projeto |
| **Automatic User Profile Learning** | Aprende perfil do usuário automaticamente |
| **Unified Memory-Prompt Timeline** | Timeline unificada de memórias |
| **Full-Featured Web UI** | Interface web completa |
| **Intelligent Prompt-Based Memory Extraction** | Extração inteligente baseada em prompts |
| **Multi-Provider AI Support** | OpenAI, Anthropic (usa providers do OpenCode) |
| **12+ Local Embedding Models** | 12+ modelos de embedding locais |
| **Smart Deduplication** | Deduplicação inteligente |
| **Built-in Privacy Protection** | Proteção de privacidade |

## Installation

Adicione ao seu `opencode.json`:

```json
{
  "plugin": ["opencode-mem"]
}
```

## Configuration

Crie o arquivo `~/.config/opencode/opencode-mem.jsonc`:

```json
{
  "storagePath": "~/.opencode-mem/data",
  "userNameOverride": "Seu Nome",
  "userEmailOverride": "seu@email.com",
  "embeddingModel": "Xenova/nomic-embed-text-v1",
  "defaultScope": "project",
  
  "webServerEnabled": true,
  "webServerPort": 4747,
  
  "autoCaptureEnabled": true,
  "autoCaptureLanguage": "auto",
  
  "opencodeProvider": "anthropic",
  "opencodeModel": "claude-haiku-4-5-20251001",
  
  "showAutoCaptureToasts": true,
  "showUserProfileToasts": true,
  "showErrorToasts": true,
  
  "userProfileAnalysisInterval": 10,
  "maxMemories": 10,
  
  "compaction": {
    "enabled": true,
    "memoryLimit": 10
  },
  
  "chatMessage": {
    "enabled": true,
    "maxMemories": 3,
    "excludeCurrentSession": true,
    "injectOn": "first"
  }
}
```

### Config Options

| Opção | Tipo | Default | Descrição |
|------|------|---------|----------|
| `storagePath` | string | `~/.opencode-mem/data` | Caminho para armazenamento |
| `userNameOverride` | string | - | Nome override |
| `userEmailOverride` | string | - | Email override |
| `embeddingModel` | string | `Xenova/nomic-embed-text-v1` | Modelo de embedding |
| `defaultScope` | string | `project` | Escopo padrão (`project`, `all-projects`) |
| `webServerEnabled` | boolean | `true` | Habilita UI web |
| `webServerPort` | number | `4747` | Porta da UI web |
| `autoCaptureEnabled` | boolean | `true` | Auto-captura memórias |
| `autoCaptureLanguage` | string | `auto` | Idioma para captura |
| `opencodeProvider` | string | - | Provider AI (usa configOpenCode) |
| `opencodeModel` | string | - | Modelo AI |
| `maxMemories` | number | `10` | Máximo memórias injetadas |
| `compaction.enabled` | boolean | `true` | Compactação automática |
| `compaction.memoryLimit` | number | `10` | Limite para compactação |
| `chatMessage.enabled` | boolean | `true` | Injeta memórias em mensagens |
| `chatMessage.maxMemories` | number | `3` | Máximo memórias/chat |

## Memory Scope

O plugin suporta diferentes escopos de busca:

- **`scope: "project"`** (default): Busca apenas no projeto atual
- **`scope: "all-projects"`**: Busca em todos os projetos

## Web UI

Quando habilitado, acesso a interface web em:

```
http://localhost:4747
```

Features da UI:
- Visualizar todas as memórias
- Buscar memórias
- Editar/Deletar memórias
- Ver perfil do usuário
- Analytics

## Tools Disponíveis

O plugin registra as seguintes tools:

| Tool | Descrição |
|------|----------|
| `memory_save` | Salvar uma memória |
| `memory_search` | Buscar memórias por query |
| `memory_list` | Listar memórias |
| `memory_delete` | Deletar uma memória |
| `memory_update` | Atualizar uma memória |

## Auto-Capture

O plugin pode automaticamente capturar memórias durante sessões:

1. **User Profile Analysis** - Aprende preferências do usuário
2. **Session Summaries** - Salva resumos de sessões
3. **Project Context** - Mantém contexto do projeto

## Commands

| Comando | Descrição |
|--------|----------|
| `/mem` | Menu de memória interativo |
| `/mem save` | Salvar memória atual |
| `/mem search <query>` | Buscar memórias |

## Repositório

- GitHub: https://github.com/tickernelz/opencode-mem
- npm: https://www.npmjs.com/package/opencode-mem
- Download weekly: ~1.8K

## Requisitos

- OpenCode 1.0+
- Node.js 18+ (para desenvolvimento local)
- Bun (instalação automática de deps)

---

*Parte do handbook de plugins OpenCode*