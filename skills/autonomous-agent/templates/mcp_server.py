from mcp.server.fastmcp import FastMCP

mcp = FastMCP("$AGENT_NAME")


@mcp.tool()
def example_read_tool(query: str) -> str:
    """Exemplo de tool read-only. Substituir pela lógica real."""
    return f"resultado para: {query}"


# Adicionar tools específicas do agent aqui.
# Padrão para tools mutantes (HITL):
#
# @mcp.tool()
# def deploy_app(app: str) -> str:
#     """Faz deploy de uma app. Requer aprovação humana."""
#     from .companions import create_pending_action
#     action_id = create_pending_action(
#         command=f"mcx deploy cluster --app {app}",
#         description=f"Deploy da app {app}",
#     )
#     return f"Ação pendente criada: {action_id}. Aguardando aprovação em companions."
