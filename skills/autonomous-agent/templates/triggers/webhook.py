"""Entrypoint do Job criado por alertas externos (ex: Alertmanager)."""
from __future__ import annotations

import json
import os

from ..$AGENT_MODULE.agent import run
from ..$AGENT_MODULE.companions import post_message

SYSTEM_PROMPT = """Você é $AGENT_NAME, um agent autônomo de resposta a incidentes.
Ao receber um alerta, investigue usando as tools disponíveis.
Apresente diagnóstico claro: o que está errado, causa provável, ação recomendada.
Para ações corretivas, use request_approval em vez de executar diretamente."""


def main() -> None:
    payload_str = os.environ.get("ALERT_PAYLOAD", "{}")
    try:
        payload = json.loads(payload_str)
    except json.JSONDecodeError:
        payload = {"raw": payload_str}

    alert_summary = json.dumps(payload, indent=2, ensure_ascii=False)
    user_prompt = f"Alerta recebido. Investigue e diagnostique:\n\n```json\n{alert_summary}\n```"

    response = run(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        use_memory=False,
    )
    post_message(channel="incidents", body=response)


if __name__ == "__main__":
    main()
