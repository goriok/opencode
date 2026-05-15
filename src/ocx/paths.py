from pathlib import Path

HOME = Path.home()
OPENCODE_DIR = HOME / ".config" / "opencode"
AGENTS_DIR = OPENCODE_DIR / "agents"
SKILLS_DIR = OPENCODE_DIR / "skills"
CLAUDE_AGENTS_DIR = HOME / ".claude" / "agents"
CLAUDE_SKILLS_DIR = HOME / ".claude" / "skills"
CLAUDE_SETTINGS = HOME / ".claude" / "settings.json"
LITELLM_DIR = OPENCODE_DIR / "litellm"
LITELLM_ENV = LITELLM_DIR / ".env"
LITELLM_ENV_EXAMPLE = LITELLM_DIR / ".env.example"
PROXY_URL = "http://localhost:4000"

OPENCODE_CONFIGS = [
    "opencode.jsonc",
    "oh-my-opencode.jsonc",
    "opencode-mem.jsonc",
    "micode.jsonc",
    "dcp.jsonc",
]

PRIMARY_AGENTS = [
    "alan-turing.md",
    "grace-hopper.md",
    "tony-hoare.md",
    "ada-lovelace.md",
    "margaret-hamilton.md",
    "agents-orchestrator.md",
]

AGENCY_AGENTS_REPO = "https://github.com/msitarzewski/agency-agents"

TIERS_DIR = OPENCODE_DIR / "tiers"
PROVIDERS_DIR = OPENCODE_DIR / "providers"
TIER_STATE = OPENCODE_DIR / ".tier-state.json"
OH_MY_OPENAGENT = OPENCODE_DIR / "oh-my-openagent.jsonc"
LITELLM_CONFIG = LITELLM_DIR / "config.yaml"
