import typer

app = typer.Typer(help="$AGENT_NAME — agent autônomo")


@app.command()
def serve(port: int = typer.Option(8080, help="Porta HTTP")) -> None:
    """Sobe o servidor HTTP (webhook + MCP SSE)."""
    from .$AGENT_MODULE.server import serve as _serve
    _serve(port=port)


@app.command()
def digest() -> None:
    """Gera e posta digest diário (entrypoint do CronJob)."""
    from .$AGENT_MODULE.triggers.cron import main
    main()


@app.command()
def react() -> None:
    """Reage a alerta via ALERT_PAYLOAD env var (entrypoint do Job webhook)."""
    from .$AGENT_MODULE.triggers.webhook import main
    main()


@app.command()
def mcp_serve() -> None:
    """Sobe MCP server via stdio (para uso local com Claude Code)."""
    import asyncio
    from mcp.server.stdio import stdio_server
    from .$AGENT_MODULE.mcp_server import mcp

    async def _run():
        async with stdio_server() as (read, write):
            await mcp._mcp_server.run(
                read, write, mcp._mcp_server.create_initialization_options()
            )

    asyncio.run(_run())


if __name__ == "__main__":
    app()
