"""Entrypoint do CronJob de digest diário."""
from __future__ import annotations

from ..$AGENT_MODULE.agent import run
from ..$AGENT_MODULE.companions import post_message

SYSTEM_PROMPT = """Você é $AGENT_NAME, um agent autônomo de observabilidade.
Gere um digest diário em markdown com o estado atual do sistema.
Seja conciso — bullets, não parágrafos longos.
Destaque anomalias, erros ou itens que requerem atenção."""

DIGEST_PROMPT = """Gere um digest diário do sistema.
Colete status, métricas e eventos recentes.
Apresente um resumo executivo com destaques e recomendações se houver."""


def main() -> None:
    response = run(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=DIGEST_PROMPT,
        use_memory=False,
    )
    post_message(channel="cluster", body=f"## Digest Diário\n\n{response}")


if __name__ == "__main__":
    main()
