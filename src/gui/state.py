from __future__ import annotations

import streamlit as st

STATUS_LABELS = {
    "queued": "排队中",
    "running": "运行中",
    "cancelled": "已取消",
    "succeeded": "成功",
    "failed": "失败",
    "expired": "超时",
}


def ensure_state() -> None:
    st.session_state.setdefault("latest_task_id", "")
    st.session_state.setdefault("latest_task", None)
    st.session_state.setdefault("task_history", [])


def add_history(task_id: str) -> None:
    history = [item for item in st.session_state.get("task_history", []) if item != task_id]
    history.append(task_id)
    st.session_state["task_history"] = history[-20:]


def inject_style() -> None:
    st.markdown(
        """
        <style>
        .block-container { padding-top: 2rem; }
        div[data-testid="stMetric"] {
            border: 1px solid rgba(49, 51, 63, 0.18);
            border-radius: 8px;
            padding: 12px 14px;
        }
        textarea, input { border-radius: 6px !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )
