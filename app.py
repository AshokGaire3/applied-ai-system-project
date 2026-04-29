import os
import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler
from rag_engine import RagAssistant

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="wide")

st.title("🐾 PawPal+")
st.caption("A daily pet care planner powered by Python classes.")

st.divider()

# ---------------------------------------------------------------------------
# Helper: emoji maps  (Challenge 3 & 4 — professional UI formatting)
# ---------------------------------------------------------------------------

PRIORITY_EMOJI = {"high": "🔴 High", "medium": "🟡 Medium", "low": "🟢 Low"}
SPECIES_EMOJI  = {"dog": "🐕", "cat": "🐈", "rabbit": "🐇"}

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

DATA_FILE = "data.json"
KB_FILE = "knowledge_base.json"

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

# ---------------------------------------------------------------------------
# Step 2: Session state — the "vault"
# Challenge 2: try to load persisted data on first run
# ---------------------------------------------------------------------------

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

if "active_service" not in st.session_state:
    st.session_state.active_service = "Profile"

st.markdown(
    """
    <style>
    div[data-testid="stHorizontalBlock"] button[kind="secondary"] {
        border-radius: 999px;
        border: 1px solid #d0d7de;
        background: #f6f8fa;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown("### Services")
service_items = ["Profile", "Pets", "Tasks", "Schedule", "AI Coach"]
nav_cols = st.columns(len(service_items))
for i, service in enumerate(service_items):
    with nav_cols[i]:
        if st.button(
            service,
            key=f"nav_{service}",
            type="primary" if st.session_state.active_service == service else "secondary",
            use_container_width=True,
        ):
            st.session_state.active_service = service

nav = st.session_state.active_service

if nav == "Profile":
    st.subheader("Owner profile")

    owner_name = st.text_input(
        "Your name",
        value=st.session_state.owner.name if "owner" in st.session_state else "Jordan",
    )
    available_minutes = st.number_input(
        "Minutes available for pet care today",
        min_value=10, max_value=480,
        value=st.session_state.owner.available_minutes_per_day if "owner" in st.session_state else 120,
        step=10,
    )

    col_set, col_save = st.columns(2)
    with col_set:
        if st.button("Save Owner Profile"):
            if "owner" not in st.session_state:
                st.session_state.owner = Owner(
                    name=owner_name,
                    available_minutes_per_day=int(available_minutes),
                )
            else:
                st.session_state.owner.name = owner_name
                st.session_state.owner.available_minutes_per_day = int(available_minutes)
            st.success(f"Owner set: {st.session_state.owner}")

    with col_save:
        if "owner" in st.session_state:
            if st.button("💾 Save to data.json"):
                st.session_state.owner.save_to_json(DATA_FILE)
                st.success(f"Data saved to **{DATA_FILE}**.")

if "owner" not in st.session_state:
    st.info("Set an owner in the Profile service to continue.")
    st.stop()

owner = st.session_state.owner
metrics = get_app_metrics(owner)

with st.sidebar:
    st.markdown("### Service Center")
    st.caption("What PawPal+ provides today")
    st.markdown(f"**Current service:** `{st.session_state.active_service}`")
    st.divider()
    st.metric("Pets", metrics["pets"])
    st.metric("Tasks", metrics["tasks"])
    st.metric("Due today", metrics["due_tasks"])
    st.metric("Due minutes", metrics["due_minutes"])
    if metrics["conflicts"]:
        st.warning(f"{metrics['conflicts']} time conflict(s) need review.")
    else:
        st.success("No time conflicts detected.")

st.divider()

if nav == "Pets":
    st.subheader("Pet management")

    col1, col2, col3 = st.columns(3)
    with col1:
        pet_name = st.text_input("Pet name", value="Mochi")
    with col2:
        species = st.selectbox("Species", ["dog", "cat", "rabbit", "other"])
    with col3:
        age = st.number_input("Age (years)", min_value=0.0, max_value=30.0, value=2.0, step=0.5)

    if st.button("Add Pet"):
        existing_names = [p.name.lower() for p in st.session_state.owner.get_pets()]
        if pet_name.lower() in existing_names:
            st.warning(f"A pet named '{pet_name}' already exists.")
        else:
            new_pet = Pet(name=pet_name, species=species, age_years=float(age))
            st.session_state.owner.add_pet(new_pet)
            st.session_state.owner.save_to_json(DATA_FILE)
            st.success(f"Added {species_icon(species)} **{new_pet.name}** the {new_pet.species}!")

    pets = st.session_state.owner.get_pets()
    if pets:
        st.markdown("**Registered pets:**")
        for p in pets:
            st.markdown(
                f"- {species_icon(p.species)} **{p.name}** ({p.species}, {p.age_years}y)"
                f" — {len(p.get_tasks())} task(s)"
            )
    else:
        st.info("No pets yet. Add one above.")

    st.divider()

if nav == "Tasks":
    st.subheader("Task planning")

    pets = st.session_state.owner.get_pets()
    if not pets:
        st.info("Add a pet first before adding tasks.")
    else:
        pet_names = [p.name for p in pets]
        selected_pet_name = st.selectbox("Assign task to", pet_names)

        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            task_desc = st.text_input("Task description", value="Morning walk")
        with col2:
            duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
        with col3:
            priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
        with col4:
            frequency = st.selectbox("Frequency", ["daily", "weekly", "as_needed"])
        with col5:
            start_time_input = st.text_input("Start time (HH:MM)", value="", placeholder="08:00")

        if st.button("Add Task"):
            target_pet = next(p for p in pets if p.name == selected_pet_name)
            start_time_val = start_time_input.strip() or None
            try:
                new_task = Task(
                    description=task_desc,
                    duration_minutes=int(duration),
                    priority=priority,
                    frequency=frequency,
                    start_time=start_time_val,
                )
                target_pet.add_task(new_task)
                st.session_state.owner.save_to_json(DATA_FILE)
                st.success(f"{task_emoji(task_desc)} Task '{task_desc}' added to {target_pet.name}!")
            except ValueError as e:
                st.error(f"Invalid input: {e}")

        # Show all tasks with emoji color-coding (Challenge 3 & 4)
        all_pairs = st.session_state.owner.get_all_tasks()
        if all_pairs:
            sorted_pairs = sorted(all_pairs, key=lambda pair: pair[1].start_time or "99:99")

            st.markdown("**All tasks (sorted by scheduled start time):**")
            rows = [
                {
                    "Pet": f"{species_icon(pet.species)} {pet.name}",
                    "Task": f"{task_emoji(task.description)} {task.description}",
                    "Start Time": task.start_time or "—",
                    "Duration (min)": task.duration_minutes,
                    "Priority": PRIORITY_EMOJI.get(task.priority, task.priority),
                    "Frequency": task.frequency,
                    "Status": "✅ Done" if task.completed else "⏳ Pending",
                }
                for pet, task in sorted_pairs
            ]
            st.table(rows)

            scheduler_preview = Scheduler(st.session_state.owner)
            early_conflicts = scheduler_preview.detect_time_conflicts()
            if early_conflicts:
                st.warning(
                    f"**{len(early_conflicts)} time conflict(s) detected in your task list.**  \n"
                    "Two or more tasks overlap in the same time window. Adjust start times, "
                    "ask a helper to take one task, or remove the overlap before generating the schedule."
                )
                for c in early_conflicts:
                    st.markdown(f"- {c}")

    st.divider()

if nav == "Schedule":
    st.subheader("Schedule optimization")

    if st.button("Generate Schedule"):
        scheduler = Scheduler(st.session_state.owner)
        plan = scheduler.build_daily_plan()
        st.session_state.latest_plan = plan

        if not plan:
            st.warning("No due tasks found. Add some tasks above and try again.")
        else:
            total_scheduled = sum(e["end_min"] - e["start_min"] for e in plan)
            budget = st.session_state.owner.available_minutes_per_day
            st.success(
                f"Schedule built! {len(plan)} task(s) scheduled — "
                f"{total_scheduled} of {budget} minutes used."
            )

            plan_rows = []
            for entry in plan:
                pet  = entry["pet"]
                task = entry["task"]
                start_label = scheduler._min_to_time(entry["start_min"])
                end_label   = scheduler._min_to_time(entry["end_min"])
                plan_rows.append({
                    "Time Window": f"{start_label} – {end_label}",
                    "Pet": f"{species_icon(pet.species)} {pet.name}",
                    "Task": f"{task_emoji(task.description)} {task.description}",
                    "Duration (min)": task.duration_minutes,
                    "Priority": PRIORITY_EMOJI.get(task.priority, task.priority),
                    "Frequency": task.frequency,
                    "Reason": entry.get("reason", ""),
                })
            st.table(plan_rows)

            plan_conflicts = scheduler.detect_conflicts(plan)
            time_conflicts = scheduler.detect_time_conflicts()
            all_conflicts  = plan_conflicts + time_conflicts

            if all_conflicts:
                st.warning(
                    f"**{len(all_conflicts)} conflict(s) detected.**  \n"
                    "Some tasks overlap in time. Here's what that means for you:  \n"
                    "- If two tasks are for the same pet, you may need to stagger them "
                    "or ask a helper.  \n"
                    "- If tasks are for different pets, check whether one can wait a few minutes.  \n"
                    "Adjust the start times in **Step 3** and regenerate the schedule."
                )
                for c in all_conflicts:
                    st.markdown(f"- {c}")
            else:
                st.success("No time conflicts — your schedule is clean!")

            skipped = scheduler.get_unscheduled_tasks(plan)
            if skipped:
                st.warning(
                    f"**{len(skipped)} task(s) didn't fit in your {budget}-minute budget** "
                    "and were left out of today's plan. Consider increasing your available "
                    "time, shortening a task, or moving lower-priority tasks to another day."
                )
                skipped_rows = [
                    {
                        "Pet": f"{species_icon(pet.species)} {pet.name}",
                        "Task": f"{task_emoji(task.description)} {task.description}",
                        "Duration (min)": task.duration_minutes,
                        "Priority": PRIORITY_EMOJI.get(task.priority, task.priority),
                        "Frequency": task.frequency,
                    }
                    for pet, task in skipped
                ]
                st.table(skipped_rows)
            else:
                st.success("All due tasks fit within your time budget!")

    st.divider()

if nav == "AI Coach":
    st.subheader("AI Coach service (RAG)")
    st.caption("Ask a question and PawPal+ will retrieve care notes before answering.")
    col_left, col_right = st.columns([3, 1])
    with col_right:
        if st.button("Clear chat history"):
            st.session_state.ai_chat_history = []
            st.success("AI chat history cleared.")

    question = st.text_area(
        "Ask a pet-care question",
        placeholder="Example: How should I time walks and meals for a dog?",
    )
    include_schedule = st.checkbox("Include today's schedule context", value=True)

    if st.button("Get AI Guidance"):
        if not question.strip():
            st.warning("Please enter a question first.")
        else:
            context = ""
            if include_schedule:
                context = format_plan_context(st.session_state.latest_plan)

            try:
                assistant = RagAssistant(KB_FILE)
                result = assistant.answer(
                    question,
                    extra_context=context,
                    chat_history=st.session_state.ai_chat_history,
                )
            except FileNotFoundError:
                st.error(
                    "knowledge_base.json is missing. Add it to the project root to enable AI Coach."
                )
                st.stop()
            except Exception:
                st.error(
                    "AI Coach hit an unexpected error. Please check logs/ai.log and try again."
                )
                st.stop()

            st.session_state.ai_chat_history.append({"role": "user", "content": question.strip()})
            st.session_state.ai_chat_history.append(
                {"role": "assistant", "content": result["answer"]}
            )
            st.session_state.ai_chat_history = st.session_state.ai_chat_history[-12:]

            if not os.getenv("OPENAI_API_KEY"):
                st.info("OPENAI_API_KEY is not set. Using the local fallback response.")

            st.markdown(result["answer"])

            if result["sources"]:
                st.markdown("**Sources used**")
                for source in result["sources"]:
                    st.markdown(f"- {source['title']}")

    if st.session_state.ai_chat_history:
        st.markdown("**Recent AI conversation**")
        for message in st.session_state.ai_chat_history[-6:]:
            role = "You" if message["role"] == "user" else "AI Coach"
            st.markdown(f"- **{role}:** {message['content']}")
