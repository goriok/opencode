---
name: openclaw-companion
description: Create or update an OpenClaw skill that connects to a companions chat hub — wraps curl-based tools for posting messages, reading channels, and interacting with autonomous agents
metadata:
  type: skill
  invocation: /openclaw-companion
  arguments: "<skill-name> — name of the OpenClaw skill to create (kebab-case)"
tool: claude-only
---

# openclaw-companion — Create an OpenClaw Agent Skill

## When to Activate

Activate when the user types `/openclaw-companion <skill-name>`.

The skill creates a publishable OpenClaw skill directory at
`~/.openclaw/skills/<skill-name>/` (or the workspace skills dir) that enables
any OpenClaw agent to interact with a `companions` chat hub via `curl`.

## Workflow

```
1. Determine target directory
   → ~/.openclaw/skills/<skill-name>/   (managed install)
   → OR <workspace>/skills/<skill-name>/  (project-local, higher precedence)
   → Ask user if ambiguous

2. Read context from conversation
   → COMPANIONS_URL in use (check SOUL.md or TOOLS.md if present)
   → Channels available (cluster, incidents, etc.)
   → Any existing agent API key variable name

3. Create SKILL.md
   → frontmatter: name, description, emoji, requires.bins, requires.env
   → sections: When to Use, When NOT to Use, commands for each operation

4. Confirm and suggest next steps
   → how to install: openclaw skills install --local <path>
   → how to set env vars in openclaw.json
   → suggest /concept to document the pattern
```

## SKILL.md Template to Generate

```markdown
---
name: <skill-name>
description: Interact with <companions-url> — post messages, read channels, manage pending actions
emoji: 🤝
metadata:
  openclaw:
    requires:
      bins: [curl, jq]
      env: [COMPANIONS_URL, COMPANIONS_AGENT_KEY]
---

# <skill-name>

Skill to interact with the companions chat hub at `$COMPANIONS_URL`.

## When to Use
- Posting summaries, digests, or findings to a channel
- Reading recent messages from cluster or incidents channels
- Checking pending approval actions
- Triggering another agent via webhook

## When NOT to Use
- Direct kubectl/shell operations (use exec directly)
- Questions unrelated to agent communication

---

## Post a Message

\`\`\`bash
curl -s -X POST \
  -H "Content-Type: application/json" \
  -H "X-Agent-Key: $COMPANIONS_AGENT_KEY" \
  -d "{\"channel\": \"cluster\", \"body\": \"$MESSAGE\"}" \
  "$COMPANIONS_URL/api/inbox"
\`\`\`

Replace `cluster` with `incidents` or any other channel slug.

---

## Read Channel Messages

\`\`\`bash
curl -s \
  -H "X-Agent-Key: $COMPANIONS_AGENT_KEY" \
  "$COMPANIONS_URL/api/channels/cluster/messages?limit=10" \
  | jq '.messages[] | {author: .author_type, body: .body}'
\`\`\`

---

## Check Pending Actions

\`\`\`bash
curl -s \
  -H "X-Agent-Key: $COMPANIONS_AGENT_KEY" \
  "$COMPANIONS_URL/api/actions?status=pending" \
  | jq '.actions[] | {id, command, description, expires_at}'
\`\`\`

To approve, direct the user:
> "Ação pendente ID `<id>`: `<command>`. Acesse companions para aprovar."

---

## Trigger Another Agent

\`\`\`bash
curl -s -X POST \
  -H "Content-Type: application/json" \
  -H "X-Agent-Key: $COMPANIONS_AGENT_KEY" \
  -d "{\"channel\": \"cluster\", \"body\": \"$PROMPT\"}" \
  "$COMPANIONS_URL/webhook/chat"
\`\`\`

Fire-and-forget — wait ~10 seconds, then read channel messages for the response.

---

## Notes
- Always pipe JSON through `jq` before presenting to the user
- If curl fails (connection refused, 5xx), report the error — do not infer cluster state
- `COMPANIONS_AGENT_KEY` must be registered as an agent in companions `/admin/agents`
```

## Anti-patterns

- ❌ Hardcoding URLs or tokens in SKILL.md — always use env var references
- ❌ Blocking on webhook responses — use fire-and-forget + poll pattern
- ❌ Skipping `jq` parsing — raw JSON is noise for the agent
- ❌ Creating the skill without the user having registered an agent key in companions

## Output

After creating the file, print:

```
Skill criada em: <path>/SKILL.md

Para ativar no OpenClaw:
  openclaw skills install --local <path>

Adicione ao openclaw.json:
  "skills": {
    "entries": {
      "<skill-name>": {
        "env": {
          "COMPANIONS_URL": "<url>",
          "COMPANIONS_AGENT_KEY": "<key>"
        }
      }
    }
  }

Registre o agent no companions: https://companions.goriok.com/admin/agents
```
