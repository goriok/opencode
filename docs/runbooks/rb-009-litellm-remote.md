# RB-009 — LiteLLM Remoto (Cluster) via kftray

**Quando usar**: Acessar o LiteLLM rodando no cluster k3s remoto como provider do OpenCode via port forward persistente.
**Tempo estimado**: 5-10 minutos (instalação única do kftray)
**Pré-requisitos**: kftray instalado, kubectl configurado, cluster acessível, LiteLLM rodando no cluster

## Overview

Este runbook configura o acesso ao LiteLLM remoto (cluster k3s) usando kftray para gerenciar port forward persistente na porta localhost:4001. O kftray mantém o port forward ativo automaticamente, facilitando o uso contínuo do provider remoto.

### O que é kftray?

kftray é uma ferramenta cross-platform (macOS/Linux/Windows) para gerenciar port forwards do Kubernetes. Ele oferece:
- GUI (kftray.app) e TUI (kftui)
- Configuração via arquivo JSON
- Auto-restart de port forwards que caem
- Persistência de configurações

### Arquitetura

```
Cluster k3s (remoto)
  └─ litellm:4000 (container)
      └─ litellm:80 (service)
          │
          │ kftui (port forward)
          │
┌─────────────────────────────┐
│  Máquina local              │
│  localhost:4001 ──────────► │
│  (provider litellm-remote)  │
└─────────────────────────────┘
```

## Prerequisites

- [ ] kubectl configurado com acesso ao cluster
- [ ] Contexto Kubernetes "default" ativo: `kubectl config current-context`
- [ ] LiteLLM rodando no namespace `litellm` do cluster
- [ ] kftray instalado (se não instalado, ver Instalação abaixo)

## Quick Start

Se o kftray já está instalado e configurado:

```bash
# 1. Iniciar kftray em background (auto-start port forwards)
nohup kftui --auto-start --non-interactive > /tmp/kftui.log 2>&1 &

# 2. Verificar que port forward está ativo
lsof -i :4001 | grep LISTEN

# 3. Testar endpoint
curl -s http://localhost:4001/v1/models | jq '.'
```

## kftray Setup

### 1. Instalação

A instalação do kftray é única por máquina.

**macOS**:
```bash
# Baixar .dmg do GitHub releases
curl -L -o ~/Downloads/kftray.dmg "https://github.com/hcavarsan/kftray/releases/download/v0.27.28/kftray_0.27.28_amd64.dmg"

# Montar e copiar para /Applications
hdiutil attach ~/Downloads/kftray.dmg
cp -r /Volumes/kftray/kftray.app /Applications/
hdiutil detach /Volumes/kftray

# Instalar kftui (TUI CLI)
cd /tmp
curl -L -o kftui.tar.gz "https://github.com/hcavarsan/kftray/releases/download/v0.27.28/kftui-aarch64-apple-darwin.tar.gz"
tar -xzf kftui.tar.gz
sudo mv kftui /usr/local/bin/
chmod +x /usr/local/bin/kftui
```

**Linux**:
```bash
# Baixar AppImage
curl -L -o ~/Downloads/kftray.AppImage "https://github.com/hcavarsan/kftray/releases/download/v0.27.28/kftray_0.27.28_amd64.AppImage"
chmod +x ~/Downloads/kftray.AppImage

# Instalar kftui
sudo mv ~/Downloads/kftray.AppImage /usr/local/bin/kftray
```

**Windows**:
- Baixar `.exe` installer do GitHub releases
- Executar e seguir o wizard de instalação

### 2. Configuração

A configuração do kftray para LiteLLM já existe no repositório:

```bash
# Config já criada em: .kftray/litellm-remote.json
cat ~/.config/opencode/.kftray/litellm-remote.json
```

Conteúdo da config:
```json
[
  {
    "alias": "litellm-remote",
    "context": "default",
    "namespace": "litellm",
    "protocol": "tcp",
    "local_port": 4001,
    "remote_port": 4000,
    "service": "litellm",
    "workload_type": "service"
  }
]
```

### 3. Importar e Iniciar

```bash
# Importar config para banco de dados do kftray
kftui --configs-path ~/.config/opencode/.kftray/litellm-remote.json --save

# Iniciar em background com auto-start
nohup kftui --auto-start --non-interactive > /tmp/kftui.log 2>&1 &

# Verificar logs
tail -f /tmp/kftui.log
```

## Operational Procedures

### Start

```bash
# Método 1: Auto-start em background (recomendado)
nohup kftui --auto-start --non-interactive > /tmp/kftui.log 2>&1 &

# Método 2: GUI (macOS)
open /Applications/kftray.app
# Clique no botão "Start" para "litellm-remote"

# Método 3: TUI interativo
kftui
# Use as setas e Enter para selecionar e iniciar o port forward
```

### Stop

```bash
# Matar processo kftui
pkill -f kftui

# Verificar que parou
pgrep -f kftui
```

### Status

```bash
# Verificar se kftray está rodando
pgrep -f kftui

# Verificar se porta 4001 está escutando
lsof -i :4001 | grep LISTEN

# Verificar logs
tail -20 /tmp/kftui.log
```

### Health Check

```bash
# Testar endpoint de modelos (requer API key do cluster)
curl -s http://localhost:4001/v1/models | jq '.'

# Testar com header de autorização (substitua SK pela chave do cluster)
curl -s http://localhost:4001/v1/models \
  -H "Authorization: Bearer SK_LITELLM_MASTER_KEY" | jq '.'

# Verificar porta escutando
lsof -i :4001
```

### Restart

```bash
# Parar e reiniciar
pkill -f kftui
sleep 2
nohup kftui --auto-start --non-interactive > /tmp/kftui.log 2>&1 &

# Verificar que reiniciou
sleep 3
lsof -i :4001 | grep LISTEN
```

## Integration with OpenCode

O provider `litellm-remote` já está configurado em `opencode.jsonc`:

```jsonc
"provider": {
  "litellm-remote": {
    "npm": "@ai-sdk/openai-compatible",
    "name": "LiteLLM Remote (Cluster)",
    "options": {
      "baseURL": "http://localhost:4001/v1",
      "apiKey": "sk-litellm-remote"
    },
    "models": {
      "gemini/gemini-2.5-flash-lite": { "name": "Gemini 2.5 Flash Lite" },
      "gemini/gemini-2.5-flash": { "name": "Gemini 2.5 Flash" },
      "gemini/gemini-2.5-pro": { "name": "Gemini 2.5 Pro" },
      "gemini/gemini-3.1-flash-lite-preview": { "name": "Gemini 3.1 Flash Lite Preview" },
      "gemini/gemini-3-flash-preview": { "name": "Gemini 3 Flash Preview" },
      "gemini/gemini-3.1-pro-preview": { "name": "Gemini 3.1 Pro Preview" }
    }
  }
}
```

### Usar no OpenCode

O provider `litellm-remote` aparece automaticamente na lista de providers disponíveis. Selecione qualquer modelo Gemini (ex: `gemini/gemini-2.5-pro`) e ele usará o port forward via kftray.

## Model Mapping

6 modelos Gemini disponíveis via provider remoto:

| Model ID | Nome | Tipo |
|----------|------|------|
| `gemini/gemini-2.5-flash-lite` | Gemini 2.5 Flash Lite | Fast, lightweight |
| `gemini/gemini-2.5-flash` | Gemini 2.5 Flash | Fast |
| `gemini/gemini-2.5-pro` | Gemini 2.5 Pro | High quality |
| `gemini/gemini-3.1-flash-lite-preview` | Gemini 3.1 Flash Lite Preview | Fast, experimental |
| `gemini/gemini-3-flash-preview` | Gemini 3 Flash Preview | Fast, experimental |
| `gemini/gemini-3.1-pro-preview` | Gemini 3.1 Pro Preview | High quality, experimental |

## Troubleshooting

### kftray não inicia

**Sintoma**: `kftui --auto-start` não responde ou falha.

**Solução**:
```bash
# Verificar se está rodando
pgrep -f kftui

# Se não estiver, tentar iniciar manualmente
kftui --auto-start --non-interactive

# Verificar logs
cat /tmp/kftui.log
```

### Port forward cai e não recupera

**Sintoma**: Porta 4001 para de escutar.

**Solução**:
```bash
# Matar kftui e reiniciar
pkill -f kftui
sleep 2
nohup kftui --auto-start --non-interactive > /tmp/kftui.log 2>&1 &

# Verificar logs para erros
tail -30 /tmp/kftui.log
```

### Endpoint retorna 401

**Sintoma**: `curl http://localhost:4001/v1/models` retorna `"error": { "message": "Authentication Error..." }`

**Isso é normal!** O port forward está funcionando. O erro 401 indica que o LiteLLM remoto requer uma API key válida (a key do cluster), mas isso é tratado automaticamente pelo provider configurado em `opencode.jsonc`.

Para verificar que o port forward está conectado:
```bash
# Verificar que a porta está escutando
lsof -i :4001 | grep LISTEN

# Verificar que o kftui está rodando
pgrep -f kftui
```

### Service não encontrado

**Sintoma**: kftui log mostra "service not found" ou connection refused.

**Causa**: Service `litellm` não existe no namespace `litellm` do cluster.

**Solução**:
```bash
# Verificar service no cluster
kubectl get svc litellm -n litellm

# Se não existir, verificar deployment
kubectl get deployment litellm -n litellm

# Verificar logs do deployment
kubectl logs deployment/litellm -n litellm
```

### Porta 4001 já em uso

**Sintoma**: `lsof -i :4001` mostra outro processo.

**Solução**:
```bash
# Verificar qual processo está usando a porta
lsof -i :4001

# Se for outro processo, decidir: matar ou usar porta diferente
# Para usar porta diferente, editar .kftray/litellm-remote.json e mudar "local_port"
```

## References

- [kftray GitHub](https://github.com/hcavarsan/kftray)
- [kftray Blog - Manage all k8s port forwards](https://kftray.app/blog/kftray-manage-all-k8s-port-forward)
- [LiteLLM Docs](https://docs.litellm.ai/)
- [RB-008 — LiteLLM Proxy Setup (Local)](./rb-008-litellm-proxy-setup.md)
