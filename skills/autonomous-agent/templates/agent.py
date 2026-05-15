from __future__ import annotations

import asyncio
import json
from openai import OpenAI
from .config import get_config


def _get_tools_openai_format() -> list[dict]:
    """Converte tools do MCP server para formato OpenAI function-calling."""
    from .mcp_server import mcp
    tools = []
    for name, tool in mcp._tool_manager._tools.items():
        schema = tool.parameters or {"type": "object", "properties": {}}
        tools.append({
            "type": "function",
            "function": {
                "name": name,
                "description": tool.description or "",
                "parameters": schema,
            },
        })
    return tools


def _call_mcp_tool(name: str, arguments: dict) -> str:
    """Chama uma tool MCP in-process e retorna o resultado como string."""
    from .mcp_server import mcp

    async def _run():
        result = await mcp.call_tool(name, arguments)
        parts = []
        for item in result:
            if hasattr(item, "text"):
                parts.append(item.text)
            elif isinstance(item, dict) and "text" in item:
                parts.append(item["text"])
            else:
                parts.append(str(item))
        return "\n".join(parts) if parts else "(no output)"

    # Criar loop isolado — não usar asyncio.run() dentro de thread do executor
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_run())
    finally:
        loop.close()


def run(
    system_prompt: str,
    user_prompt: str,
    history: list[dict] | None = None,
    use_memory: bool = False,
    memory_user: str = "default",
) -> str:
    """Executa o loop ReAct e retorna a resposta final."""
    cfg = get_config()
    client = OpenAI(base_url=cfg.litellm_base_url, api_key=cfg.litellm_api_key)

    if use_memory:
        from .memory import recall
        memory_ctx = recall(user_prompt, user_id=memory_user)
        if memory_ctx:
            system_prompt = f"{system_prompt}\n\n{memory_ctx}"

    tools = _get_tools_openai_format()

    messages: list[dict] = [{"role": "system", "content": system_prompt}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user_prompt})

    while True:
        response = client.chat.completions.create(
            model=cfg.model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )
        msg = response.choices[0].message
        messages.append(msg.model_dump(exclude_none=True))

        if not msg.tool_calls:
            answer = msg.content or ""
            if use_memory:
                from .memory import remember
                remember(
                    [{"role": "user", "content": user_prompt},
                     {"role": "assistant", "content": answer}],
                    user_id=memory_user,
                )
            return answer

        for call in msg.tool_calls:
            fn = call.function.name
            args = json.loads(call.function.arguments or "{}")
            print(f"[mcp] calling {fn}({args})")
            result = _call_mcp_tool(fn, args)
            messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": result,
            })
