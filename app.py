from pathlib import Path

import streamlit as st
from pawpal_system import Owner
from ui.helpers import (
    get_app_metrics,
    render_quick_actions,
    render_right_panel,
    render_summary_cards,
    render_today_overview,
    render_top_bar,
)
from ui.pages import (
    render_ai_coach_page,
    render_pets_page,
    render_profile_page,
    render_schedule_page,
    render_tasks_page,
)
from ui.navigation import normalize_service, render_sidebar_nav, service_from_query_params
from ui.theme import apply_theme
from ui.content import ROADMAP_STATUS

try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent / ".env", override=False)
except ImportError:
    pass

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="wide")

apply_theme()

DATA_FILE = "data.json"
KB_FILE = "knowledge_base.json"

if "owner" not in st.session_state:
    loaded = Owner.load_from_json(DATA_FILE)
    if loaded is not None:
        st.session_state.owner = loaded
        st.session_state._loaded_from_file = True
    else:
        st.session_state._loaded_from_file = False

if st.session_state.get("_loaded_from_file"):
    st.success(
        f"Data loaded from **{DATA_FILE}** — welcome back, "
        f"{st.session_state.owner.name}! "
        f"({len(st.session_state.owner.get_pets())} pet(s) restored)"
    )
    st.session_state._loaded_from_file = False   # only show banner once

if "latest_plan" not in st.session_state:
    st.session_state.latest_plan = []

if "ai_chat_history" not in st.session_state:
    st.session_state.ai_chat_history = []

nav = normalize_service(service_from_query_params())
st.session_state.active_service = nav

if "owner" not in st.session_state:
    st.info("Set an owner in the Profile service to continue.")
    st.stop()

owner = st.session_state.owner
metrics = get_app_metrics(owner)

with st.sidebar:
    with st.expander("Insights", expanded=False):
        st.metric("Pets", metrics["pets"])
        st.metric("Tasks", metrics["tasks"])
        st.metric("Due today", metrics["due_tasks"])
        st.metric("Conflicts", metrics["conflicts"])
        done_count = sum(1 for _, status in ROADMAP_STATUS if status == "Done")
        st.progress(done_count / len(ROADMAP_STATUS))
        st.caption(f"{done_count}/{len(ROADMAP_STATUS)} roadmap areas completed")

nav = render_sidebar_nav(nav)
st.session_state.active_service = nav
render_top_bar(nav)
render_summary_cards(metrics)

if nav == "Profile":
    render_today_overview(owner)

main_col, side_col = st.columns([2.4, 1], gap="large")
with main_col:
    if nav == "Profile":
        render_profile_page(DATA_FILE)
    elif nav == "Pets":
        render_pets_page(DATA_FILE)
    elif nav == "Tasks":
        render_tasks_page(DATA_FILE)
    elif nav == "Schedule":
        render_schedule_page()
    elif nav == "AI Coach":
        render_ai_coach_page(KB_FILE)

with side_col:
    if nav != "AI Coach":
        render_right_panel(metrics)

render_quick_actions()
