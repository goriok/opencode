from __future__ import annotations

from mem0 import Memory

MEM0_CONFIG = {
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "host": "qdrant.memory.svc.cluster.local",
            "port": 6333,
            "collection_name": "$AGENT_NAME",
            "embedding_model_dims": 384,
        },
    },
    "embedder": {
        # fastembed: não precisa de sentence_transformers — use sempre esse, não "huggingface"
        "provider": "fastembed",
        "config": {"model": "BAAI/bge-small-en-v1.5"},
    },
    "llm": {
        "provider": "openai",
        "config": {
            "model": "deepseek-v4-flash",
            "openai_base_url": "http://litellm.litellm.svc.cluster.local:4000",
            "api_key": "placeholder",
        },
    },
}

_memory: Memory | None = None


def get_memory() -> Memory:
    global _memory
    if _memory is None:
        _memory = Memory.from_config(MEM0_CONFIG)
    return _memory


def recall(query: str, user_id: str = "default", limit: int = 5) -> str:
    # API mem0: search() usa filters=, não user_id= diretamente
    results = get_memory().search(query, filters={"user_id": user_id}, limit=limit)
    if not results or not results.get("results"):
        return ""
    memories = [r["memory"] for r in results["results"] if r.get("memory")]
    if not memories:
        return ""
    joined = "\n".join(f"- {m}" for m in memories)
    return f"## Memória relevante\n{joined}"


def remember(messages: list[dict], user_id: str = "default") -> None:
    # API mem0: add() ainda usa user_id= diretamente (não filters=)
    get_memory().add(messages, user_id=user_id)
