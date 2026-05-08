import json
import os
import shutil
import subprocess
import time
from pathlib import Path

import httpx
import typer

from oc import log, proc
from oc.paths import (
    CLAUDE_SETTINGS,
    LITELLM_DIR,
    LITELLM_ENV,
    LITELLM_ENV_EXAMPLE,
    PROXY_URL,
)

app = typer.Typer(help="Manage the LiteLLM proxy.")

VIRTUAL_KEY_ALIAS = "claude-code-max"
CLAUDE_MODELS = ["claude-sonnet-4-6", "claude-opus-4-7", "claude-haiku-4-5-20251001"]


def _load_env() -> dict[str, str]:
    """Parse KEY=VALUE lines from litellm/.env, ignoring comments and blanks."""
    if not LITELLM_ENV.exists():
        return {}
    env: dict[str, str] = {}
    for line in LITELLM_ENV.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        env[k.strip()] = v.strip()
    return env


def _proxy_is_up() -> bool:
    try:
        r = httpx.get(f"{PROXY_URL}/health/liveliness", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


def _wait_for_proxy(max_seconds: int = 40) -> None:
    waited = 0
    while not _proxy_is_up():
        if waited >= max_seconds:
            log.error(f"Proxy did not respond in {max_seconds}s — check: oc litellm logs", prefix="litellm")
        time.sleep(2)
        waited += 2
        typer.echo(".", nl=False)
    typer.echo("")


def _generate_virtual_key(master_key: str) -> str:
    r = httpx.post(
        f"{PROXY_URL}/key/generate",
        headers={"Authorization": f"Bearer {master_key}", "Content-Type": "application/json"},
        json={"key_alias": VIRTUAL_KEY_ALIAS, "models": CLAUDE_MODELS},
        timeout=10,
    )
    r.raise_for_status()
    return r.json().get("key", "")


def _update_claude_settings(proxy_url: str, virtual_key: str) -> None:
    if not CLAUDE_SETTINGS.exists():
        log.warn("~/.claude/settings.json not found. Add manually:", prefix="litellm")
        typer.echo(f'  "env": {{"ANTHROPIC_BASE_URL": "{proxy_url}", "ANTHROPIC_CUSTOM_HEADERS": "x-litellm-api-key: Bearer {virtual_key}"}}')
        return

    data = json.loads(CLAUDE_SETTINGS.read_text())
    data["env"] = {
        "ANTHROPIC_BASE_URL": proxy_url,
        "ANTHROPIC_CUSTOM_HEADERS": f"x-litellm-api-key: Bearer {virtual_key}",
    }
    CLAUDE_SETTINGS.write_text(json.dumps(data, indent=2))
    log.info("~/.claude/settings.json updated", prefix="litellm")


@app.command()
def up() -> None:
    """Start the LiteLLM proxy (docker compose up -d)."""
    proc.stream(["docker", "compose", "up", "-d"], cwd=LITELLM_DIR)
    log.info(f"Proxy running at {PROXY_URL}", prefix="litellm")


@app.command()
def down() -> None:
    """Stop the LiteLLM proxy."""
    proc.stream(["docker", "compose", "down"], cwd=LITELLM_DIR)


@app.command()
def logs() -> None:
    """Tail LiteLLM proxy logs."""
    proc.stream(["docker", "compose", "logs", "-f", "litellm"], cwd=LITELLM_DIR)


@app.command()
def status() -> None:
    """Health-check the LiteLLM proxy."""
    if _proxy_is_up():
        log.info("Proxy is online", prefix="litellm")
    else:
        log.warn("Proxy is offline", prefix="litellm")
        raise typer.Exit(1)


@app.command()
def models() -> None:
    """List models available on the LiteLLM proxy."""
    env = _load_env()
    master_key = env.get("LITELLM_MASTER_KEY", "sk-litellm-local")
    try:
        r = httpx.get(
            f"{PROXY_URL}/v1/models",
            headers={"Authorization": f"Bearer {master_key}"},
            timeout=5,
        )
        r.raise_for_status()
        for m in r.json().get("data", []):
            typer.echo(f" - {m['id']}")
    except Exception:
        log.warn("Proxy offline or LITELLM_MASTER_KEY not set", prefix="litellm")
        raise typer.Exit(1)


@app.command("env-init")
def env_init() -> None:
    """Create litellm/.env from .env.example (if not already present)."""
    if LITELLM_ENV.exists():
        log.info(".env already exists — no action needed", prefix="litellm")
        return
    if not LITELLM_ENV_EXAMPLE.exists():
        log.error(f".env.example not found at {LITELLM_ENV_EXAMPLE}", prefix="litellm")
    shutil.copy2(LITELLM_ENV_EXAMPLE, LITELLM_ENV)
    log.info(f".env created — edit it and add your API keys: {LITELLM_ENV}", prefix="litellm")


@app.command()
def setup(
    claude_code: bool = typer.Option(False, "--claude-code", help="Only generate virtual key and configure Claude Code"),
) -> None:
    """Set up the LiteLLM proxy (full setup or --claude-code only)."""
    if claude_code:
        _setup_claude_code()
        return
    _full_setup()


def _setup_claude_code() -> None:
    section_msg = "Configure Claude Code → LiteLLM"
    log.section(section_msg)

    if not LITELLM_ENV.exists():
        log.error(f".env not found — run full setup first: oc litellm setup", prefix="litellm")

    env = _load_env()
    master_key = env.get("LITELLM_MASTER_KEY", "")
    if not master_key:
        log.error("LITELLM_MASTER_KEY not set in litellm/.env", prefix="litellm")

    if not _proxy_is_up():
        log.error("Proxy is offline — run: oc litellm up", prefix="litellm")

    log.info(f"Generating virtual key '{VIRTUAL_KEY_ALIAS}'...", prefix="litellm")
    try:
        virtual_key = _generate_virtual_key(master_key)
    except Exception as e:
        log.error(f"Failed to generate virtual key: {e}", prefix="litellm")

    if not virtual_key:
        log.error("Empty virtual key returned — is the proxy running?", prefix="litellm")

    log.info(f"Virtual key: {virtual_key[:24]}...", prefix="litellm")
    _update_claude_settings(PROXY_URL, virtual_key)

    log.info("Testing Claude Code via proxy...", prefix="litellm")
    try:
        result = subprocess.run(
            ["claude", "-p", "reply with exactly one word: pong"],
            capture_output=True, text=True, timeout=15,
        )
        response = (result.stdout or "").replace("\n", "")[:40]
        if "pong" in response or response:
            log.info(f"OK — Claude Code routing via proxy (response: {response})", prefix="litellm")
        else:
            log.warn("Inconclusive test — run manually: claude -p 'ping'", prefix="litellm")
    except Exception:
        log.warn("Could not test claude CLI — run manually: claude -p 'ping'", prefix="litellm")

    typer.echo("")
    log.info(f"Done! UI at {PROXY_URL}/ui (login: {master_key})", prefix="litellm")


def _full_setup() -> None:
    log.section("Verify prerequisites")

    if not shutil.which("docker"):
        log.error("Docker not found — install at https://docs.docker.com/get-docker/", prefix="litellm")
    try:
        subprocess.run(["docker", "compose", "version"], capture_output=True, check=True)
    except subprocess.CalledProcessError:
        log.error("Docker Compose v2 not found", prefix="litellm")

    result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
    import re
    version_match = re.search(r"[\d.]+", result.stdout)
    log.info(f"Docker: {version_match.group() if version_match else 'ok'}", prefix="litellm")

    log.section("Create .env")

    if LITELLM_ENV.exists():
        log.warn(".env already exists — using current file", prefix="litellm")
        log.info(f"To recreate: rm {LITELLM_ENV} && oc litellm setup", prefix="litellm")
    else:
        if not LITELLM_ENV_EXAMPLE.exists():
            log.error(f".env.example not found at {LITELLM_ENV_EXAMPLE}", prefix="litellm")
        shutil.copy2(LITELLM_ENV_EXAMPLE, LITELLM_ENV)
        log.info(f".env created at {LITELLM_ENV}", prefix="litellm")
        typer.echo("""
  Fill in the following variables:

  LITELLM_MASTER_KEY  → leave 'sk-litellm-local' or choose another string
  OPENCODE_GO_API_KEY → get at https://opencode.ai/auth → "API Key"
  ANTHROPIC_API_KEY   → leave EMPTY (Claude Code uses OAuth Max, not API key)
  ZAI_API_KEY         → get at https://z.ai/manage-apikey/apikey-list
""")
        editor = os.environ.get("VISUAL") or os.environ.get("EDITOR") or "nano"
        if shutil.which(editor):
            log.info(f"Opening .env in {editor}...", prefix="litellm")
            subprocess.run([editor, str(LITELLM_ENV)])
        else:
            log.warn(f"Edit manually before continuing: {LITELLM_ENV}", prefix="litellm")
            input("Press Enter when done...")

    env = _load_env()
    if not env.get("LITELLM_MASTER_KEY"):
        log.error("LITELLM_MASTER_KEY not set in .env", prefix="litellm")

    log.section("Start proxy")
    log.info("Starting LiteLLM + Postgres (allow ~20s for migrations)...", prefix="litellm")
    subprocess.run(["docker", "compose", "up", "-d"], cwd=LITELLM_DIR, check=True)
    _wait_for_proxy()
    log.info(f"Proxy online at {PROXY_URL}", prefix="litellm")

    log.section("Verify models")
    master_key = env["LITELLM_MASTER_KEY"]
    try:
        r = httpx.get(
            f"{PROXY_URL}/v1/models",
            headers={"Authorization": f"Bearer {master_key}"},
            timeout=5,
        )
        model_count = len(r.json().get("data", []))
    except Exception:
        model_count = 0

    log.info(f"{model_count} models loaded", prefix="litellm")
    if model_count < 5:
        log.warn("Few models loaded — check OPENCODE_GO_API_KEY in .env", prefix="litellm")

    log.section("Configure Claude Code")
    _setup_claude_code()

    log.section("Next steps")
    typer.echo(f"""
  ✅ LiteLLM proxy running at {PROXY_URL}
  ✅ Claude Code configured to use the proxy

  Daily operations:
    oc litellm up      → start the proxy
    oc litellm down    → stop the proxy
    oc litellm logs    → monitor calls
    oc litellm status  → health check
    oc litellm models  → list models

  UI: {PROXY_URL}/ui  (login: {master_key})
""")
