from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class Config:
    litellm_base_url: str
    litellm_api_key: str
    model: str
    companions_url: str
    companions_agent_key: str


_config: Config | None = None


def get_config() -> Config:
    global _config
    if _config is None:
        _config = Config(
            litellm_base_url=os.environ.get("LITELLM_BASE_URL", "http://litellm.litellm.svc.cluster.local:4000"),
            litellm_api_key=os.environ["LITELLM_API_KEY"],
            model=os.environ.get("MODEL", "deepseek-v4-flash"),
            companions_url=os.environ["COMPANIONS_URL"],
            companions_agent_key=os.environ["COMPANIONS_AGENT_KEY"],
        )
    return _config
