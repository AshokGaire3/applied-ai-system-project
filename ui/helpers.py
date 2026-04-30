from pawpal_system import Owner, Scheduler
import streamlit as st


PRIORITY_EMOJI = {"high": "🔴 High", "medium": "🟡 Medium", "low": "🟢 Low"}
SPECIES_EMOJI = {"dog": "🐕", "cat": "🐈", "rabbit": "🐇"}


def species_icon(species: str) -> str:
    return SPECIES_EMOJI.get(species.lower(), "🐾")


def task_emoji(description: str) -> str:
    desc = description.lower()
    if any(w in desc for w in ("walk", "run", "exercise", "hike")):
        return "🦮"
    if any(w in desc for w in ("feed", "food", "meal", "kibble", "treat")):
        return "🍖"
    if any(w in desc for w in ("med", "pill", "insulin", "shot", "vet")):
        return "💊"
    if any(w in desc for w in ("groom", "brush", "bath", "nail", "clean")):
        return "✂️"
    if any(w in desc for w in ("play", "toy", "fetch", "enrichment")):
        return "🎾"
    if any(w in desc for w in ("water", "drink")):
        return "💧"
    return "📋"


def get_app_metrics(owner: Owner) -> dict:
    all_tasks = owner.get_all_tasks()
    due_tasks = owner.get_all_due_tasks()
    scheduler = Scheduler(owner)
    conflicts = scheduler.detect_time_conflicts()
    due_minutes = owner.total_due_minutes()
    return {
        "pets": len(owner.get_pets()),
        "tasks": len(all_tasks),
        "due_tasks": len(due_tasks),
        "due_minutes": due_minutes,
        "daily_budget": owner.available_minutes_per_day,
        "conflicts": len(conflicts),
    }


def format_plan_context(plan: list[dict]) -> str:
    if not plan:
        return "No scheduled tasks yet."
    lines = ["Scheduled tasks:"]
    for entry in plan:
        task = entry["task"]
        pet = entry["pet"]
        lines.append(
            f"- {pet.name}: {task.description} ({task.duration_minutes} min, priority={task.priority})"
        )
    return "\n".join(lines)


def render_top_bar(page_title: str) -> None:
    st.markdown(
        f"""
        <div class="pawpal-topbar">
            <div class="pawpal-topbar-title">{page_title}</div>
            <div class="pawpal-topbar-subtitle">Modern pet-care workspace</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_summary_cards(metrics: dict) -> None:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Pets", metrics["pets"])
    col2.metric("Tasks", metrics["tasks"])
    col3.metric("Due Today", metrics["due_tasks"])
    col4.metric("Conflicts", metrics["conflicts"])


def render_today_overview(owner: Owner) -> None:
    due_tasks = owner.get_all_due_tasks()
    scheduler = Scheduler(owner)
    time_conflicts = scheduler.detect_time_conflicts()
    latest_plan = st.session_state.get("latest_plan", [])

    left, mid, right = st.columns([1.2, 1, 1.4])
    with left:
        st.markdown("### Today Overview")
        if due_tasks:
            for pet, task in due_tasks[:5]:
                st.markdown(f"- {species_icon(pet.species)} **{pet.name}** · {task_emoji(task.description)} {task.description}")
        else:
            st.caption("No due tasks for today.")
    with mid:
        st.markdown("### Health Alerts")
        if time_conflicts:
            st.error(f"{len(time_conflicts)} scheduling conflict(s)")
        else:
            st.success("No conflict alerts")
        if owner.total_due_minutes() > owner.available_minutes_per_day:
            st.warning("Due minutes exceed daily budget")
        else:
            st.info("Workload fits daily budget")
    with right:
        st.markdown("### Timeline")
        if latest_plan:
            for entry in latest_plan[:5]:
                task = entry["task"]
                pet = entry["pet"]
                st.markdown(f"- {pet.name}: **{task.description}** ({task.duration_minutes}m)")
        else:
            st.caption("Generate a schedule to preview timeline.")


def render_right_panel(metrics: dict) -> None:
    st.markdown("### Insights Panel")
    st.caption("Quick stats and AI-ready context")
    st.progress(min(1.0, metrics["due_minutes"] / max(1, metrics["daily_budget"])))
    st.caption(f"{metrics['due_minutes']} / {metrics['daily_budget']} minutes")
    if metrics["conflicts"]:
        st.warning("Resolve conflicts before finalizing schedule.")
    else:
        st.success("Schedule health looks good.")
    with st.expander("Suggested next actions"):
        st.markdown("- Add missing feeding tasks")
        st.markdown("- Run Schedule Optimization")
        st.markdown("- Ask AI Coach for timing advice")


def render_quick_actions() -> None:
    with st.container():
        st.markdown('<div class="pawpal-fab-marker"></div>', unsafe_allow_html=True)
        with st.popover("➕ Quick Actions", use_container_width=False):
            if st.button("Add Pet", use_container_width=True, key="fab_add_pet"):
                st.query_params["page"] = "pets"
                st.rerun()
            if st.button("Add Task", use_container_width=True, key="fab_add_task"):
                st.query_params["page"] = "tasks"
                st.rerun()
