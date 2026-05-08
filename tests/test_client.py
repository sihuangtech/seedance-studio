from __future__ import annotations

import json

import httpx
import pytest

from core import SeedanceAPIError, SeedanceClient
from core.config import DEFAULT_MODEL_CHOICES, unique_items
from core.content import bytes_to_data_url, image_content, text_content


def make_client(handler) -> SeedanceClient:
    return SeedanceClient("test-key", transport=httpx.MockTransport(handler))


def test_create_task_sends_expected_payload() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/api/v3/contents/generations/tasks"
        assert request.headers["authorization"] == "Bearer test-key"
        payload = json.loads(request.content)
        assert payload["model"] == "doubao-seedance-2-0-260128"
        assert payload["content"] == [text_content("hello")]
        assert payload["duration"] == 5
        return httpx.Response(200, json={"id": "cgt-1"})

    client = make_client(handler)
    assert client.create_task(
        model="doubao-seedance-2-0-260128",
        content=[text_content("hello")],
        duration=5,
    ) == {"id": "cgt-1"}


def test_list_tasks_repeats_task_id_filter() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params.get_list("filter.task_ids") == ["cgt-1", "cgt-2"]
        assert request.url.params["filter.status"] == "succeeded"
        return httpx.Response(200, json={"items": [], "total": 0})

    client = make_client(handler)
    assert client.list_tasks(status="succeeded", task_ids=["cgt-1", "cgt-2"])["total"] == 0


def test_delete_task_accepts_empty_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "DELETE"
        assert request.url.path.endswith("/contents/generations/tasks/cgt-1")
        return httpx.Response(204)

    client = make_client(handler)
    assert client.delete_task("cgt-1") is None


def test_raises_api_error_with_code_and_message() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            400,
            json={"error": {"code": "InvalidParameter", "message": "bad request"}},
        )

    client = make_client(handler)
    with pytest.raises(SeedanceAPIError) as exc_info:
        client.get_task("cgt-1")

    assert exc_info.value.status_code == 400
    assert exc_info.value.code == "InvalidParameter"
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
