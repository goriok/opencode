from __future__ import annotations

import httpx
from .config import get_config


def post_message(channel: str, body: str, metadata: dict | None = None) -> None:
    cfg = get_config()
    payload: dict = {"channel": channel, "body": body}
    if metadata:
        payload["metadata"] = metadata
    resp = httpx.post(
        f"{cfg.companions_url}/api/inbox",
        json=payload,
        headers={"X-Agent-Key": cfg.companions_agent_key},
        timeout=10,
    )
    resp.raise_for_status()


def create_pending_action(
    command: str,
    description: str,
    channel: str = "cluster",
) -> str:
    """Cria pending action no companions e retorna o action_id."""
    cfg = get_config()
    payload = {
        "channel": channel,
        "body": f"Ação pendente: **{description}**\n\nComando: `{command}`",
        "pending_action": {
            "command": command,
            "description": description,
        },
    }
    resp = httpx.post(
        f"{cfg.companions_url}/api/inbox",
        json=payload,
        headers={"X-Agent-Key": cfg.companions_agent_key},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    return data.get("action_id", "unknown")


def fetch_history(channel: str, limit: int = 20) -> list[dict]:
    cfg = get_config()
    resp = httpx.get(
        f"{cfg.companions_url}/api/channels/{channel}/messages",
        params={"limit": limit},
        headers={"X-Agent-Key": cfg.companions_agent_key},
        timeout=10,
    )
    resp.raise_for_status()
    messages = resp.json().get("messages", [])
    history = []
    for msg in messages:
        role = "assistant" if msg.get("author_type") == "agent" else "user"
        history.append({"role": role, "content": msg.get("body", "")})
    return history
