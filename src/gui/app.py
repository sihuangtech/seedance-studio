from __future__ import annotations

import streamlit as st

from core.config import load_dotenv
from gui.create import render_create_task
from gui.sidebar import render_sidebar
from gui.state import ensure_state, inject_style
from gui.tasks import render_task_list, render_task_lookup


def main() -> None:
    load_dotenv()
    st.set_page_config(page_title="Seedance Studio", page_icon=None, layout="wide")
    inject_style()
    ensure_state()

    st.title("Seedance Studio")
    config = render_sidebar()

    create_tab, task_tab, list_tab = st.tabs(["创建任务", "任务查询", "任务列表"])
    with create_tab:
        render_create_task(config)
    with task_tab:
        render_task_lookup(config)
    with list_tab:
        render_task_list(config)


if __name__ == "__main__":
    main()
