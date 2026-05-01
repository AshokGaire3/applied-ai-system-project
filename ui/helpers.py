from typing import Iterator

from pawpal_system import Owner, Pet, Scheduler, Task
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


_MEDICATION_HINTS = (
    "med",
    "pill",
    "insulin",
    "shot",
    "injection",
    "prescription",
    "metformin",
    "antibiotic",
)


def iter_medication_adjacent_tasks(owner: Owner) -> Iterator[tuple[Pet, Task]]:
    for pet in owner.get_pets():
        for task in pet.get_tasks():
            d = task.description.lower()
            if any(h in d for h in _MEDICATION_HINTS):
                yield pet, task


def count_tasks_missing_start_time(owner: Owner) -> int:
    count = 0
    for _, task in owner.get_all_tasks():
        if task.start_time is None and task.priority == "high":
            count += 1
    return count


def build_care_handoff_document(
    owner: Owner,
    *,
    caregiver_label: str,
    vet_phone: str,
    emergency_line: str,
    household_notes: str,
) -> str:
    lines = [
        "=" * 56,
        "PAWPAL+ — CARE HANDOFF (human-generated summary)",
        "=" * 56,
        "",
        f"Owner / primary caregiver: {owner.name}",
        f"Daily care budget (minutes/day): {owner.available_minutes_per_day}",
        f"Printed for sitter/contact: {(caregiver_label or '').strip() or '(not entered)'}",
        f"Preferred vet clinic line (if any): {(vet_phone or '').strip() or '(not entered)'}",
        f"Local emergency guideline: {(emergency_line or '').strip() or '(e.g. ER vet / animal hospital)'}",
        "",
        "--- Household notes ---",
        (household_notes or "").strip() or "(none entered — add food brands, quirks, leash rules.)",
        "",
        "--- Pets (from your PawPal+ profile) ---",
    ]

    pets = owner.get_pets()
    if not pets:
        lines.append("(No pets on file — register pets before exporting.)")

    med_lines: list[str] = []
    for pet in pets:
        lines.append(
            f"* {species_icon(pet.species)} {pet.name} — {pet.species}, age ~{pet.age_years} y"
        )
        lines.append(f"  Tasks captured: {len(pet.get_tasks())}")
        for task in sorted(
            pet.get_tasks(), key=lambda t: (-t.priority_rank(), t.description.lower())
        ):
            st_hint = task.start_time or "no_fixed_time_entered"
            lines.append(
                f"    - [{task.priority}] {task_emoji(task.description)} {task.description} "
                f"({task.duration_minutes}m, {task.frequency}, start_hint={st_hint})"
            )
    for pet, task in sorted(iter_medication_adjacent_tasks(owner), key=lambda x: x[0].name):
        med_lines.append(f"  · {pet.name}: {task.description} (priority={task.priority})")

    lines.append("")
    lines.append("--- Medication / procedure-like tasks (keyword scan) ---")
    if med_lines:
        lines.extend(med_lines)
        lines.append(
            "Verify timing with the pet’s veterinarian; do not change doses from this sheet."
        )
    else:
        lines.append(
            "(None detected from task descriptions — add meds tasks explicitly if applicable.)"
        )

    lines.extend(
        [
            "",
            "--- Operational checklist ---",
            "- Confirm food type, portion cheat-sheet, and any allergies (not tracked in PawPal+).",
            "- Show sitter conflict-free schedule preview from the Schedule service.",
            "- Leave written vet authorization if your clinic requires permission for emergencies.",
            "",
            "Disclaimer: This export is informational for trusted caregivers—not medical advice.",
        ]
    )
    return "\n".join(lines)


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


def render_top_bar_actions(page_title: str) -> None:
    actions = {
        "Profile": [("Go to Pets", "pets"), ("Go to Tasks", "tasks")],
        "Pets": [("Add Task", "tasks"), ("Open Schedule", "schedule")],
        "Tasks": [("Add Pet", "pets"), ("Open Schedule", "schedule")],
        "Schedule": [("Back to Tasks", "tasks"), ("Ask AI Coach", "ai-coach")],
        "Wellness": [("Open Schedule", "schedule"), ("Care handoff", "care-handoff")],
        "Care handoff": [("Wellness", "wellness"), ("AI Coach", "ai-coach")],
        "AI Coach": [("Wellness", "wellness"), ("Care handoff", "care-handoff")],
    }
    page_actions = actions.get(page_title, [])
    if not page_actions:
        return
    col_spacer, col_a, col_b = st.columns([4, 1, 1])
    with col_a:
        if st.button(page_actions[0][0], use_container_width=True, key=f"topbar_a_{page_title}"):
            st.query_params["page"] = page_actions[0][1]
            st.rerun()
    with col_b:
        if st.button(page_actions[1][0], use_container_width=True, key=f"topbar_b_{page_title}"):
            st.query_params["page"] = page_actions[1][1]
            st.rerun()


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
        st.markdown("- Add missing feeding or medication tasks")
        st.markdown("- Run **Schedule** optimization and clear conflicts")
        st.markdown("- Scan **Wellness** for readiness gaps")
        st.markdown("- Export **Care handoff** before travel")
        st.markdown("- Ask **AI Coach** for timing or care basics (RAG)")


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
            if st.button("Wellness", use_container_width=True, key="fab_wellness"):
                st.query_params["page"] = "wellness"
                st.rerun()
            if st.button("Care handoff", use_container_width=True, key="fab_handoff"):
                st.query_params["page"] = "care-handoff"
                st.rerun()


def render_skeleton_cards(count: int = 3) -> None:
    cols = st.columns(count)
    for col in cols:
        with col:
            st.markdown('<div class="pawpal-skeleton-card"></div>', unsafe_allow_html=True)
