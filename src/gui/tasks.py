from __future__ import annotations

from typing import Any

import streamlit as st

from core.errors import SeedanceAPIError, SeedanceConfigError
from gui.client import make_client
from gui.state import STATUS_LABELS, add_history


def render_task_lookup(config: dict[str, Any]) -> None:
    col_a, col_b = st.columns([0.7, 0.3], gap="large")
    with col_a:
        task_id = st.text_input("任务 ID", value=st.session_state.get("latest_task_id", ""))
    with col_b:
        st.write("")
        st.write("")
        query_clicked = st.button("查询", use_container_width=True)
        delete_clicked = st.button("取消 / 删除", use_container_width=True)

    if query_clicked:
        run_get_task(config, task_id)
    if delete_clicked:
        run_delete_task(config, task_id)

    latest_task = st.session_state.get("latest_task")
    if latest_task:
        render_task_result(latest_task)


def render_task_list(config: dict[str, Any]) -> None:
    status, page_num, page_size, model = render_list_filters()
    if st.button("刷新列表", type="primary"):
        try:
            with make_client(config) as client:
                result = client.list_tasks(
                    page_num=int(page_num),
                    page_size=int(page_size),
                    status=None if status == "全部" else status,
                    model=model.strip() or None,
                )
            st.session_state["task_list"] = result
        except (SeedanceAPIError, SeedanceConfigError, ValueError) as exc:
            st.error(str(exc))

    result = st.session_state.get("task_list")
    if result:
        render_task_table(result)


def render_list_filters() -> tuple[str, int, int, str]:
    col_a, col_b, col_c, col_d = st.columns(4)
    with col_a:
        status = st.selectbox(
            "状态",
            ["全部", "queued", "running", "succeeded", "failed", "cancelled"],
        )
    with col_b:
        page_num = st.number_input("页码", min_value=1, max_value=500, value=1)
    with col_c:
        page_size = st.number_input("每页", min_value=1, max_value=500, value=10)
    with col_d:
        model = st.text_input("接入点 ID")
    return status, int(page_num), int(page_size), model


def render_task_table(result: dict[str, Any]) -> None:
    items = result.get("items", [])
    st.caption(f"共 {result.get('total', len(items))} 条")
    if not items:
        st.info("没有匹配任务。")
        return

    rows = [
        {
            "id": item.get("id"),
            "status": item.get("status"),
            "model": item.get("model"),
            "created_at": item.get("created_at"),
            "updated_at": item.get("updated_at"),
            "video_url": item.get("content", {}).get("video_url"),
        }
        for item in items
    ]
    st.dataframe(rows, use_container_width=True, hide_index=True)
    st.json(result)


def run_get_task(config: dict[str, Any], task_id: str) -> None:
    if not task_id.strip():
        st.error("请填写任务 ID。")
        return
    try:
        with make_client(config) as client:
            task = client.get_task(task_id.strip())
        st.session_state["latest_task_id"] = task_id.strip()
        st.session_state["latest_task"] = task
        add_history(task_id.strip())
    except (SeedanceAPIError, SeedanceConfigError, ValueError) as exc:
        st.error(str(exc))


def run_delete_task(config: dict[str, Any], task_id: str) -> None:
    if not task_id.strip():
        st.error("请填写任务 ID。")
        return
    try:
        with make_client(config) as client:
            client.delete_task(task_id.strip())
        st.success(f"已提交操作：{task_id.strip()}")
    except (SeedanceAPIError, SeedanceConfigError, ValueError) as exc:
        st.error(str(exc))


def render_task_result(task: dict[str, Any]) -> None:
    task_id = task.get("id", "")
    status = task.get("status")
    label = STATUS_LABELS.get(status, status or "未知")
    st.metric("任务", task_id, label)

    content = task.get("content") or {}
    video_url = content.get("video_url")
    last_frame_url = content.get("last_frame_url")
    if video_url:
        st.video(video_url)
        st.link_button("打开视频", video_url, use_container_width=True)
    if last_frame_url:
        st.image(last_frame_url, caption="尾帧")

    st.json(task)
