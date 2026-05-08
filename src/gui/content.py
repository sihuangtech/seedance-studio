from __future__ import annotations

from typing import Any

from core.content import (
    audio_content,
    bytes_to_data_url,
    draft_task_content,
    image_content,
    text_content,
    video_content,
)


def build_content(
    *,
    prompt: str,
    first_frame_url: str,
    first_frame_file: Any,
    last_frame_url: str,
    last_frame_file: Any,
    reference_image_urls: str,
    reference_image_files: list[Any],
    reference_video_urls: str,
    reference_audio_urls: str,
    reference_audio_files: list[Any],
    draft_task_id: str,
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    if prompt.strip():
        items.append(text_content(prompt.strip()))

    for source in collect_sources(first_frame_url, first_frame_file):
        items.append(image_content(source, role="first_frame"))
    for source in collect_sources(last_frame_url, last_frame_file):
        items.append(image_content(source, role="last_frame"))

    reference_images = [
        *split_lines(reference_image_urls),
        *uploaded_files_to_data_urls(reference_image_files),
    ]
    for source in reference_images:
        items.append(image_content(source, role="reference_image"))

    for source in split_lines(reference_video_urls):
        items.append(video_content(source))

    reference_audio = [
        *split_lines(reference_audio_urls),
        *uploaded_files_to_data_urls(reference_audio_files),
    ]
    for source in reference_audio:
        items.append(audio_content(source))

    if draft_task_id.strip():
        items.append(draft_task_content(draft_task_id.strip()))

    return items


def collect_sources(url: str, uploaded_file: Any | None) -> list[str]:
    sources = split_lines(url)
    if uploaded_file is not None:
        sources.append(bytes_to_data_url(uploaded_file.name, uploaded_file.getvalue()))
    return sources


def uploaded_files_to_data_urls(files: list[Any] | None) -> list[str]:
    return [bytes_to_data_url(file.name, file.getvalue()) for file in files or []]


def split_lines(value: str) -> list[str]:
    return [line.strip() for line in value.splitlines() if line.strip()]
