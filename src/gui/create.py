from __future__ import annotations

from typing import Any

import streamlit as st

from core.errors import SeedanceAPIError, SeedanceConfigError
from gui.client import make_client
from gui.content import build_content
from gui.state import add_history
from gui.tasks import render_task_result


def render_create_task(config: dict[str, Any]) -> None:
    left, right = st.columns([1.1, 0.9], gap="large")
    with left:
        form = render_create_form(config)

    with right:
        st.subheader("结果")
        latest_task = st.session_state.get("latest_task")
        if latest_task:
            render_task_result(latest_task)
        else:
            st.info("创建后会显示任务 ID 和返回内容。")

    if not form.pop("submitted"):
        return

    try:
        content = build_content(**form["content_fields"])
        if not content:
            raise ValueError("请至少填写提示词、素材或样片任务 ID。")

        with make_client(config) as client:
            task = client.create_task(model=form["model"], content=content, **form["options"])

        task_id = task.get("id", "")
        if task_id:
            st.session_state["latest_task_id"] = task_id
            add_history(task_id)
        st.session_state["latest_task"] = task
        st.success(f"任务已创建：{task_id}")
        st.rerun()
    except (SeedanceAPIError, SeedanceConfigError, ValueError) as exc:
        st.error(str(exc))


def render_create_form(config: dict[str, Any]) -> dict[str, Any]:
    st.subheader("输入")
    prompt = st.text_area("提示词", height=180)
    model = render_model_input(config)

    media_tab, advanced_tab = st.tabs(["素材", "参数"])
    with media_tab:
        content_fields = render_media_inputs(prompt)
    with advanced_tab:
        options = render_generation_options()

    submitted = st.button("创建任务", type="primary", use_container_width=True)
    return {
        "submitted": submitted,
        "model": model,
        "content_fields": content_fields,
        "options": options,
    }


def render_model_input(config: dict[str, Any]) -> str:
    choices = config.get("model_choices", [])
    default_model = config["default_model"]
    model_options = choices if default_model in choices else [default_model, *choices]
    selected_model = st.selectbox("模型", model_options, index=0)
    custom_model = st.text_input("自定义模型 / Endpoint ID")
    return (custom_model or selected_model).strip()


def render_media_inputs(prompt: str) -> dict[str, Any]:
    first_frame_url = st.text_input("首帧图片 URL / Asset ID")
    first_frame_file = image_uploader("首帧图片文件", "first_frame_file")
    last_frame_url = st.text_input("尾帧图片 URL / Asset ID")
    last_frame_file = image_uploader("尾帧图片文件", "last_frame_file")
    reference_image_urls = st.text_area("参考图片 URL / Asset ID", height=90)
    reference_image_files = image_uploader(
        "参考图片文件",
        "reference_image_files",
        accept_multiple_files=True,
    )
    reference_video_urls = st.text_area("参考视频 URL / Asset ID")
    reference_audio_urls = st.text_area("参考音频 URL / Asset ID")
    reference_audio_files = st.file_uploader(
        "参考音频文件",
        type=["wav", "mp3"],
        accept_multiple_files=True,
        key="reference_audio_files",
    )
    draft_task_id = st.text_input("样片任务 ID")
    return {
        "prompt": prompt,
        "first_frame_url": first_frame_url,
        "first_frame_file": first_frame_file,
        "last_frame_url": last_frame_url,
        "last_frame_file": last_frame_file,
        "reference_image_urls": reference_image_urls,
        "reference_image_files": reference_image_files,
        "reference_video_urls": reference_video_urls,
        "reference_audio_urls": reference_audio_urls,
        "reference_audio_files": reference_audio_files,
        "draft_task_id": draft_task_id,
    }


def render_generation_options() -> dict[str, Any]:
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        resolution = st.selectbox("分辨率", ["720p", "480p", "1080p"], index=0)
        ratio = st.selectbox("比例", ["adaptive", "16:9", "9:16", "1:1", "4:3", "3:4", "21:9"])
        duration_mode = st.radio("时长", ["固定", "智能"], horizontal=True)
        duration = -1 if duration_mode == "智能" else st.number_input("秒", 4, 15, 5)
    with col_b:
        generate_audio = st.toggle("生成声音", value=True)
        return_last_frame = st.toggle("返回尾帧", value=False)
        watermark = st.toggle("水印", value=False)
        web_search = st.toggle("联网搜索", value=False)
    with col_c:
        service_tier = st.selectbox("服务等级", ["default", "flex"])
        seed_enabled = st.toggle("指定 Seed", value=False)
        seed = st.number_input("Seed", min_value=-1, value=-1, disabled=not seed_enabled)
        expires = st.number_input("超时秒数", 3600, 259200, 172800, step=3600)

    return {
        "resolution": resolution,
        "ratio": ratio,
        "duration": int(duration),
        "generate_audio": generate_audio,
        "return_last_frame": return_last_frame,
        "watermark": watermark,
        "service_tier": service_tier,
        "seed": int(seed) if seed_enabled else None,
        "execution_expires_after": int(expires),
        "tools": [{"type": "web_search"}] if web_search else None,
    }


def image_uploader(label: str, key: str, *, accept_multiple_files: bool = False) -> Any:
    return st.file_uploader(
        label,
        type=["jpg", "jpeg", "png", "webp", "bmp", "tiff", "gif"],
        accept_multiple_files=accept_multiple_files,
        key=key,
    )
