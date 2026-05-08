from __future__ import annotations

import base64
import mimetypes
from pathlib import Path
from typing import Any, Literal

ImageRole = Literal["first_frame", "last_frame", "reference_image"]
VideoRole = Literal["reference_video"]
AudioRole = Literal["reference_audio"]


def text_content(prompt: str) -> dict[str, str]:
    return {"type": "text", "text": prompt}


def image_content(url: str, *, role: ImageRole | None = None) -> dict[str, Any]:
    item: dict[str, Any] = {"type": "image_url", "image_url": {"url": url}}
    if role:
        item["role"] = role
    return item


def video_content(url: str, *, role: VideoRole = "reference_video") -> dict[str, Any]:
    return {"type": "video_url", "video_url": {"url": url}, "role": role}


def audio_content(url: str, *, role: AudioRole = "reference_audio") -> dict[str, Any]:
    return {"type": "audio_url", "audio_url": {"url": url}, "role": role}


def draft_task_content(task_id: str) -> dict[str, Any]:
    return {"type": "draft_task", "draft_task": {"id": task_id}}


def file_to_data_url(path: str | Path) -> str:
    file_path = Path(path)
    media_type = mimetypes.guess_type(file_path.name)[0]
    if not media_type:
        raise ValueError(f"Cannot infer MIME type for {file_path}")

    data = base64.b64encode(file_path.read_bytes()).decode("ascii")
    return f"data:{media_type};base64,{data}"


def bytes_to_data_url(filename: str, data: bytes) -> str:
    media_type = mimetypes.guess_type(filename)[0]
    if not media_type:
        raise ValueError(f"Cannot infer MIME type for {filename}")

    encoded = base64.b64encode(data).decode("ascii")
    return f"data:{media_type};base64,{encoded}"
