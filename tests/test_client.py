from __future__ import annotations

import os

import pytest

from core import SeedanceClient
from core.config import DEFAULT_MODEL_CHOICES, unique_items
from core.content import bytes_to_data_url, image_content, text_content
from core.errors import SeedanceAPIError


class RecordingTasks:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []

    def create(self, **kwargs):
        self.calls.append(("create", kwargs))
        return {"id": "cgt-1"}

    def get(self, **kwargs):
        self.calls.append(("get", kwargs))
        return {"id": kwargs["task_id"], "status": "succeeded"}

    def list(self, **kwargs):
        self.calls.append(("list", kwargs))
        return {"items": [], "total": 0}

    def delete(self, task_id, **kwargs):
        self.calls.append(("delete", {"task_id": task_id, **kwargs}))


class RecordingArk:
    def __init__(self) -> None:
        self.tasks = RecordingTasks()
        self.content_generation = type("ContentGeneration", (), {"tasks": self.tasks})()


def make_client() -> tuple[SeedanceClient, RecordingTasks]:
    ark = RecordingArk()
    return SeedanceClient("test-key", ark_client=ark, timeout=12), ark.tasks


def test_create_task_uses_official_sdk_tasks_create() -> None:
    client, tasks = make_client()
    assert client.create_task(
        model="doubao-seedance-2-0-260128",
        content=[text_content("hello")],
        duration=5,
    ) == {"id": "cgt-1"}

    method, payload = tasks.calls[-1]
    assert method == "create"
    assert payload["model"] == "doubao-seedance-2-0-260128"
    assert payload["content"] == [text_content("hello")]
    assert payload["duration"] == 5
    assert payload["timeout"] == 12


def test_list_tasks_uses_official_sdk_filters() -> None:
    client, tasks = make_client()
    assert client.list_tasks(status="succeeded", task_ids=["cgt-1", "cgt-2"])["total"] == 0

    method, payload = tasks.calls[-1]
    assert method == "list"
    assert payload["task_ids"] == ["cgt-1", "cgt-2"]
    assert payload["status"] == "succeeded"


def test_delete_task_uses_official_sdk_delete() -> None:
    client, tasks = make_client()
    assert client.delete_task("cgt-1") is None
    assert tasks.calls[-1] == ("delete", {"task_id": "cgt-1", "timeout": 12})


def test_wraps_sdk_errors() -> None:
    class FailingTasks(RecordingTasks):
        def get(self, **_kwargs):
            raise RuntimeError("bad request")

    ark = RecordingArk()
    ark.content_generation.tasks = FailingTasks()
    client = SeedanceClient("test-key", ark_client=ark)

    with pytest.raises(SeedanceAPIError) as exc_info:
        client.get_task("cgt-1")

    assert "bad request" in str(exc_info.value)


def test_content_helpers() -> None:
    assert image_content("asset://abc", role="reference_image") == {
        "type": "image_url",
        "image_url": {"url": "asset://abc"},
        "role": "reference_image",
    }
    assert bytes_to_data_url("demo.png", b"abc") == "data:image/png;base64,YWJj"


def test_default_model_choices_cover_seedance_families() -> None:
    assert "doubao-seedance-2-0-260128" in DEFAULT_MODEL_CHOICES
    assert "doubao-seedance-2-0-fast-260128" in DEFAULT_MODEL_CHOICES
    assert "doubao-seedance-1-5-pro-251215" in DEFAULT_MODEL_CHOICES
    assert "doubao-seedance-1-0-lite-t2v-250428" in DEFAULT_MODEL_CHOICES
    assert unique_items(["a", "b", "a"]) == ["a", "b"]


@pytest.mark.integration
def test_real_official_sdk_can_list_tasks() -> None:
    if os.getenv("SEEDANCE_RUN_INTEGRATION_TESTS") != "1":
        pytest.skip("Set SEEDANCE_RUN_INTEGRATION_TESTS=1 to call the real Ark SDK.")
    if not os.getenv("SEEDANCE_API_KEY") and not os.getenv("ARK_API_KEY"):
        pytest.skip("Set SEEDANCE_API_KEY or ARK_API_KEY to call the real Ark SDK.")

    client = SeedanceClient.from_env()
    result = client.list_tasks(page_num=1, page_size=1)
    assert "items" in result
