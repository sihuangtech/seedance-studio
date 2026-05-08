from __future__ import annotations

from typing import Any

from core.client import SeedanceClient
from core.config import DEFAULT_BASE_URL
from core.errors import SeedanceConfigError


def make_client(config: dict[str, Any]) -> SeedanceClient:
    api_key = config["api_key"]
    if not api_key:
        raise SeedanceConfigError("请填写 API Key，或在 .env 中配置 SEEDANCE_API_KEY。")
    return SeedanceClient(
        api_key,
        base_url=config["base_url"] or DEFAULT_BASE_URL,
        default_model=config["default_model"] or None,
        timeout=config["timeout"],
    )
