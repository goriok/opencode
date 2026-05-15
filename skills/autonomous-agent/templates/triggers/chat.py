from __future__ import annotations

from ..$AGENT_MODULE.agent import run
from ..$AGENT_MODULE.companions import post_message, fetch_history as _fetch_history

SYSTEM_PROMPT = """Você é $AGENT_NAME, um agent autônomo.
Responda de forma concisa e útil.
Use as tools disponíveis para coletar informações antes de responder."""


def fetch_history(channel: str) -> list[dict]:
    return _fetch_history(channel)


def handle(channel: str, message: str, history: list[dict] | None = None) -> None:
    response = run(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=message,
        history=history,
        use_memory=True,
        memory_user=channel,
    )
    post_message(channel=channel, body=response)
