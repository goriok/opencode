"""Fixed model_name → litellm_params mapping for models routed through LiteLLM.

Only Anthropic and Gemini go through the proxy today; zai/opencode-go are direct.
Tier profiles reference models by their model_name (key in this dict).
"""

KNOWN_MODELS: dict[str, dict] = {
    # ── Anthropic (Claude Code Max subscription via OAuth) ────────────────
    "claude-sonnet-4-6": {
        "model": "anthropic/claude-sonnet-4-6",
        "max_retries": 0,
    },
    "claude-opus-4-7": {
        "model": "anthropic/claude-opus-4-7",
        "max_retries": 0,
    },
    "claude-haiku-4-5-20251001": {
        "model": "anthropic/claude-haiku-4-5-20251001",
        "max_retries": 0,
    },
    # ── Gemini 3.* (GEMINI_API_KEY) ────────────────────────────────────────
    "gemini/gemini-3.1-flash-lite-preview": {
        "model": "gemini/gemini-3.1-flash-lite-preview",
        "api_key": "os.environ/GEMINI_API_KEY",
    },
    "gemini/gemini-3-flash-preview": {
        "model": "gemini/gemini-3-flash-preview",
        "api_key": "os.environ/GEMINI_API_KEY",
    },
    "gemini/gemini-3.1-pro-preview": {
        "model": "gemini/gemini-3.1-pro-preview",
        "api_key": "os.environ/GEMINI_API_KEY",
    },
}
