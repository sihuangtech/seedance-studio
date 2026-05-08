from __future__ import annotations

import os
from typing import Any

import streamlit as st

from core.config import DEFAULT_BASE_URL, DEFAULT_MODEL, get_model_choices


def render_sidebar() -> dict[str, Any]:
    with st.sidebar:
        st.header("连接")
        env_api_key = os.getenv("SEEDANCE_API_KEY") or os.getenv("ARK_API_KEY") or ""
        api_key = st.text_input("API Key", value=env_api_key, type="password")
        base_url = st.text_input("Base URL", value=os.getenv("SEEDANCE_BASE_URL", DEFAULT_BASE_URL))
        model_choices = get_model_choices()
        env_model = os.getenv("SEEDANCE_MODEL", DEFAULT_MODEL)
        model_index = model_choices.index(env_model) if env_model in model_choices else 0
        default_model = st.selectbox(
            "默认模型",
            model_choices,
            index=model_index,
        )
        custom_model = st.text_input(
            "自定义模型 / Endpoint ID",
            value="" if env_model in model_choices else env_model,
        )
        timeout = st.number_input("请求超时", min_value=5, max_value=300, value=60, step=5)

        st.divider()
        st.header("最近任务")
        history = st.session_state.get("task_history", [])
        if history:
            for task_id in history[-8:][::-1]:
                st.code(task_id)
        else:
            st.caption("暂无")

    return {
        "api_key": api_key.strip(),
        "base_url": base_url.strip(),
        "default_model": (custom_model or default_model).strip(),
        "model_choices": model_choices,
        "timeout": float(timeout),
    }
