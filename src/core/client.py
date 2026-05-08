from __future__ import annotations

import time
from collections.abc import Callable, Mapping, Sequence
from typing import Any

from volcenginesdkarkruntime import Ark

from core.config import DEFAULT_BASE_URL, SeedanceConfig
from core.errors import SeedanceAPIError

TERMINAL_STATUSES = {"succeeded", "failed", "cancelled", "expired"}


class SeedanceClient:
    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        default_model: str | None = None,
        timeout: float = 60.0,
        ark_client: Any | None = None,
    ) -> None:
        self.default_model = default_model
        self.timeout = timeout
        self._client = ark_client or create_ark_client(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
        )

    @classmethod
    def from_env(cls) -> SeedanceClient:
        config = SeedanceConfig.from_env()
        return cls(
            api_key=config.api_key,
            base_url=config.base_url,
            default_model=config.default_model,
            timeout=config.timeout,
        )

    def close(self) -> None:
        close = getattr(self._client, "close", None)
        if callable(close):
            close()

    def __enter__(self) -> SeedanceClient:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def create_task(
        self,
        *,
        content: Sequence[Mapping[str, Any]],
        model: str | None = None,
        callback_url: str | None = None,
        return_last_frame: bool | None = None,
        service_tier: str | None = None,
        execution_expires_after: int | None = None,
        generate_audio: bool | None = None,
        draft: bool | None = None,
        tools: Sequence[Mapping[str, Any]] | None = None,
        safety_identifier: str | None = None,
        resolution: str | None = None,
        ratio: str | None = None,
        duration: int | None = None,
        frames: int | None = None,
        seed: int | None = None,
        camera_fixed: bool | None = None,
        watermark: bool | None = None,
        extra: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        task_model = model or self.default_model
        if not task_model:
            raise ValueError("model is required. Pass model=... or set SEEDANCE_MODEL.")

        payload: dict[str, Any] = {
            "model": task_model,
            "content": list(content),
            "safety_identifier": safety_identifier,
            "callback_url": callback_url,
            "return_last_frame": return_last_frame,
            "service_tier": service_tier,
            "execution_expires_after": execution_expires_after,
            "generate_audio": generate_audio,
            "draft": draft,
            "camera_fixed": camera_fixed,
            "watermark": watermark,
            "seed": seed,
            "resolution": resolution,
            "ratio": ratio,
            "duration": duration,
            "frames": frames,
            "tools": list(tools) if tools is not None else None,
            "timeout": self.timeout,
        }
        payload = without_none(payload)
        if extra:
            payload["extra_body"] = dict(extra)

        return self._call_ark(lambda: self._tasks.create(**payload))

    def get_task(self, task_id: str) -> dict[str, Any]:
        return self._call_ark(lambda: self._tasks.get(task_id=task_id, timeout=self.timeout))

    def list_tasks(
        self,
        *,
        page_num: int | None = None,
        page_size: int | None = None,
        status: str | None = None,
        task_ids: Sequence[str] | None = None,
        model: str | None = None,
        service_tier: str | None = None,
    ) -> dict[str, Any]:
        payload = without_none(
            {
                "page_num": page_num,
                "page_size": page_size,
                "status": status,
                "task_ids": list(task_ids) if task_ids is not None else None,
                "model": model,
                "service_tier": service_tier,
                "timeout": self.timeout,
            }
        )
        return self._call_ark(lambda: self._tasks.list(**payload))

    def delete_task(self, task_id: str) -> None:
        self._call_ark(lambda: self._tasks.delete(task_id, timeout=self.timeout))

    def wait_for_task(
        self,
        task_id: str,
        *,
        interval: float = 5.0,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        started_at = time.monotonic()
        while True:
            task = self.get_task(task_id)
            if task.get("status") in TERMINAL_STATUSES:
                return task
            if timeout is not None and time.monotonic() - started_at >= timeout:
                raise TimeoutError(f"Timed out waiting for task {task_id}")
            time.sleep(interval)

    @property
    def _tasks(self) -> Any:
        return self._client.content_generation.tasks

    def _call_ark(self, action: Callable[[], Any]) -> dict[str, Any]:
        try:
            return to_plain_data(action())
        except Exception as exc:
            raise to_seedance_api_error(exc) from exc


def create_ark_client(*, api_key: str, base_url: str, timeout: float) -> Any:
    return Ark(api_key=api_key, base_url=base_url, timeout=timeout)


def without_none(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if value is not None}


def to_plain_data(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    converted = convert_value(value)
    if isinstance(converted, dict):
        return converted
    return {"data": converted}


def convert_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: convert_value(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [convert_value(item) for item in value]

    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        return convert_value(model_dump(exclude_none=True))

    as_dict = getattr(value, "dict", None)
    if callable(as_dict):
        return convert_value(as_dict(exclude_none=True))

    return value


def to_seedance_api_error(exc: Exception) -> SeedanceAPIError:
    status_code = getattr(exc, "status_code", None)
    code = getattr(exc, "code", None)
    body = getattr(exc, "body", None)
    message = getattr(exc, "message", None) or str(exc)
    return SeedanceAPIError(
        message,
        status_code=status_code,
        code=code,
        response=body,
    )
