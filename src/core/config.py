from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from core.errors import SeedanceConfigError

DEFAULT_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
DEFAULT_MODEL = "doubao-seedance-2-0-260128"
DEFAULT_MODEL_CHOICES = (
    "doubao-seedance-2-0-260128",
    "doubao-seedance-2-0-fast-260128",
    "doubao-seedance-1-5-pro-251215",
    "doubao-seedance-1-0-pro-250528",
    "doubao-seedance-1-0-pro-fast-250610",
    "doubao-seedance-1-0-lite-t2v-250428",
    "doubao-seedance-1-0-lite-i2v-250428",
)
DEFAULT_TIMEOUT_SECONDS = 60.0


@dataclass(frozen=True)
class SeedanceConfig:
    api_key: str
    base_url: str = DEFAULT_BASE_URL
    default_model: str | None = None
    timeout: float = DEFAULT_TIMEOUT_SECONDS

    @classmethod
    def from_env(cls) -> SeedanceConfig:
        load_dotenv()
        api_key = os.getenv("SEEDANCE_API_KEY") or os.getenv("ARK_API_KEY")
        if not api_key:
            raise SeedanceConfigError(
                "Missing API key. Set SEEDANCE_API_KEY or pass api_key explicitly."
            )

        timeout = os.getenv("SEEDANCE_TIMEOUT")
        return cls(
            api_key=api_key,
            base_url=os.getenv("SEEDANCE_BASE_URL", DEFAULT_BASE_URL),
            default_model=os.getenv("SEEDANCE_MODEL"),
            timeout=float(timeout) if timeout else DEFAULT_TIMEOUT_SECONDS,
        )


def get_model_choices() -> list[str]:
    raw_value = os.getenv("SEEDANCE_MODEL_CHOICES", "")
    configured = [item.strip() for item in raw_value.split(",") if item.strip()]
    return unique_items([*configured, *DEFAULT_MODEL_CHOICES])


def unique_items(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def load_dotenv(path: str | Path = ".env") -> None:
    env_path = Path(path)
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)
