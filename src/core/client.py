from __future__ import annotations

import time
from collections.abc import Mapping, Sequence
from typing import Any

import httpx

from core.config import SeedanceConfig
from core.errors import SeedanceAPIError

TERMINAL_STATUSES = {"succeeded", "failed", "cancelled", "expired"}


class SeedanceClient:
    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = "https://ark.cn-beijing.volces.com/api/v3",
        default_model: str | None = None,
        timeout: float = 60.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.default_model = default_model
        self._client = httpx.Client(
            base_url=base_url.rstrip("/"),
            timeout=timeout,
            transport=transport,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "seedance-studio/0.1.0",
            },
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
        self._client.close()

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

        payload: dict[str, Any] = {"model": task_model, "content": list(content)}
        optional_fields = {
            "callback_url": callback_url,
            "return_last_frame": return_last_frame,
            "service_tier": service_tier,
            "execution_expires_after": execution_expires_after,
            "generate_audio": generate_audio,
            "draft": draft,
            "tools": list(tools) if tools is not None else None,
            "safety_identifier": safety_identifier,
            "resolution": resolution,
            "ratio": ratio,
            "duration": duration,
            "frames": frames,
            "seed": seed,
            "camera_fixed": camera_fixed,
            "watermark": watermark,
        }
        payload.update({key: value for key, value in optional_fields.items() if value is not None})
        if extra:
            payload.update(extra)

        return self._request("POST", "/contents/generations/tasks", json=payload)

    def get_task(self, task_id: str) -> dict[str, Any]:
        return self._request("GET", f"/contents/generations/tasks/{task_id}")

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
        params: list[tuple[str, str | int]] = []
        if page_num is not None:
            params.append(("page_num", page_num))
        if page_size is not None:
            params.append(("page_size", page_size))
        if status is not None:
            params.append(("filter.status", status))
        if model is not None:
            params.append(("filter.model", model))
        if service_tier is not None:
            params.append(("filter.service_tier", service_tier))
        for task_id in task_ids or ():
            params.append(("filter.task_ids", task_id))

        return self._request("GET", "/contents/generations/tasks", params=params)

    def delete_task(self, task_id: str) -> None:
        self._request("DELETE", f"/contents/generations/tasks/{task_id}")

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

    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        response = self._client.request(method, path, **kwargs)
        if response.status_code == 204 or not response.content:
            return {}

        try:
            data = response.json()
        except ValueError as exc:
            if response.is_success:
                return {}
            raise SeedanceAPIError(
                response.text,
                status_code=response.status_code,
                response=response.text,
            ) from exc

        if response.is_success:
            return data

        error = data.get("error") if isinstance(data, dict) else None
        message = None
        code = None
        if isinstance(error, dict):
            message = error.get("message")
            code = error.get("code")
        if not message and isinstance(data, dict):
            message = data.get("message")
            code = code or data.get("code")
        raise SeedanceAPIError(
            message or f"Seedance API request failed with HTTP {response.status_code}",
            status_code=response.status_code,
            code=code,
            response=data,
        )
