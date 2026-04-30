import os

import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task
from rag_engine import RagAssistant, _default_chat_model, _load_env_file
from ui.content import RAG_GUARDRAILS, RAG_NOT_SUPPORTED, RAG_SUPPORTED_QUESTIONS, ROADMAP_STATUS
from ui.helpers import PRIORITY_EMOJI, format_plan_context, species_icon, task_emoji


def _save_owner_data(data_file: str) -> bool:
    try:
        st.session_state.owner.save_to_json(data_file)
        return True
    except Exception:
        st.error(f"Could not save data to `{data_file}`. Check file permissions and disk space.")
        return False


def render_profile_page(data_file: str) -> None:
    st.markdown('<div class="pawpal-section-title">Owner Profile</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="pawpal-card">
            <strong>Project status snapshot</strong><br/>
            <span class="pawpal-muted">Aligned with roadmap milestones and reliability goals.</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.expander("Roadmap status", expanded=False):
        status_rows = [{"Area": area, "Status": status} for area, status in ROADMAP_STATUS]
        st.dataframe(status_rows, use_container_width=True, hide_index=True)

    owner_name = st.text_input(
        "Your name",
        value=st.session_state.owner.name if "owner" in st.session_state else "Jordan",
    )
    available_minutes = st.number_input(
        "Minutes available for pet care today",
        min_value=10,
        max_value=480,
        value=st.session_state.owner.available_minutes_per_day if "owner" in st.session_state else 120,
        step=10,
    )

    col_set, col_save = st.columns(2)
    with col_set:
        if st.button("Save Owner Profile", use_container_width=True):
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
        if "owner" in st.session_state and st.button("Save to data.json", use_container_width=True):
            if _save_owner_data(data_file):
                st.success(f"Data saved to `{data_file}`.")


def render_pets_page(data_file: str) -> None:
    st.markdown('<div class="pawpal-section-title">Pet Management</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        pet_name = st.text_input("Pet name", value="Mochi")
    with col2:
        species = st.selectbox("Species", ["dog", "cat", "rabbit", "other"])
    with col3:
        age = st.number_input("Age (years)", min_value=0.0, max_value=30.0, value=2.0, step=0.5)

    if st.button("Add Pet", use_container_width=True):
        existing_names = [p.name.lower() for p in st.session_state.owner.get_pets()]
        if pet_name.lower() in existing_names:
            st.warning(f"A pet named '{pet_name}' already exists.")
        else:
            new_pet = Pet(name=pet_name, species=species, age_years=float(age))
            st.session_state.owner.add_pet(new_pet)
            _save_owner_data(data_file)
            st.success(f"Added {species_icon(species)} **{new_pet.name}** the {new_pet.species}!")

    pets = st.session_state.owner.get_pets()
    if pets:
        st.markdown("**Registered pets**")
        for p in pets:
            with st.expander(f"{species_icon(p.species)} {p.name} ({p.species}, {p.age_years}y)", expanded=False):
                st.caption(f"{len(p.get_tasks())} task(s) assigned")
                for task in p.get_tasks()[:5]:
                    st.markdown(f"- {task_emoji(task.description)} {task.description} ({task.duration_minutes}m)")
    else:
        st.info("No pets yet. Add one above.")


def render_tasks_page(data_file: str) -> None:
    st.markdown('<div class="pawpal-section-title">Task Planning</div>', unsafe_allow_html=True)
    pets = st.session_state.owner.get_pets()
    if not pets:
        st.info("Add a pet first before adding tasks.")
        return

    pet_names = [p.name for p in pets]
    selected_pet_name = st.selectbox("Assign task to", pet_names)

    col1, col2, col3 = st.columns(3)
    with col1:
        task_desc = st.text_input("Task description", value="Morning walk")
        duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
    with col2:
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
        frequency = st.selectbox("Frequency", ["daily", "weekly", "as_needed"])
    with col3:
        start_time_input = st.text_input("Start time (HH:MM)", value="", placeholder="08:00")
        st.caption("Optional: leave empty to auto-place later.")

    if st.button("Add Task", use_container_width=True):
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
            _save_owner_data(data_file)
            st.success(f"{task_emoji(task_desc)} Task '{task_desc}' added to {target_pet.name}!")
        except ValueError as e:
            st.error(f"Invalid input: {e}")

    all_pairs = st.session_state.owner.get_all_tasks()
    if all_pairs:
        sorted_pairs = sorted(all_pairs, key=lambda pair: pair[1].start_time or "99:99")
        rows = [
            {
                "Pet": f"{species_icon(pet.species)} {pet.name}",
                "Task": f"{task_emoji(task.description)} {task.description}",
                "Start Time": task.start_time or "-",
                "Duration (min)": task.duration_minutes,
                "Priority": PRIORITY_EMOJI.get(task.priority, task.priority),
                "Frequency": task.frequency,
                "Status": "Done" if task.completed else "Pending",
            }
            for pet, task in sorted_pairs
        ]
        st.dataframe(rows, use_container_width=True, hide_index=True)

        scheduler_preview = Scheduler(st.session_state.owner)
        early_conflicts = scheduler_preview.detect_time_conflicts()
        if early_conflicts:
            with st.expander(f"{len(early_conflicts)} conflict(s) detected", expanded=True):
                for c in early_conflicts:
                    st.markdown(f"- {c}")


def render_schedule_page() -> None:
    st.markdown('<div class="pawpal-section-title">Schedule Optimization</div>', unsafe_allow_html=True)
    if st.button("Generate Schedule", use_container_width=True):
        scheduler = Scheduler(st.session_state.owner)
        plan = scheduler.build_daily_plan()
        st.session_state.latest_plan = plan

        if not plan:
            st.warning("No due tasks found. Add some tasks and try again.")
            return

        total_scheduled = sum(e["end_min"] - e["start_min"] for e in plan)
        budget = st.session_state.owner.available_minutes_per_day
        st.success(f"Schedule built: {len(plan)} task(s), {total_scheduled}/{budget} minutes used.")

        plan_rows = []
        for entry in plan:
            pet = entry["pet"]
            task = entry["task"]
            start_label = scheduler._min_to_time(entry["start_min"])
            end_label = scheduler._min_to_time(entry["end_min"])
            plan_rows.append(
                {
                    "Time Window": f"{start_label} - {end_label}",
                    "Pet": f"{species_icon(pet.species)} {pet.name}",
                    "Task": f"{task_emoji(task.description)} {task.description}",
                    "Duration (min)": task.duration_minutes,
                    "Priority": PRIORITY_EMOJI.get(task.priority, task.priority),
                    "Frequency": task.frequency,
                }
            )
        st.dataframe(plan_rows, use_container_width=True, hide_index=True)

        plan_conflicts = scheduler.detect_conflicts(plan)
        time_conflicts = scheduler.detect_time_conflicts()
        all_conflicts = plan_conflicts + time_conflicts
        if all_conflicts:
            st.warning(f"{len(all_conflicts)} conflict(s) detected.")
            for c in all_conflicts:
                st.markdown(f"- {c}")
        else:
            st.success("No time conflicts. Schedule is clean.")

        skipped = scheduler.get_unscheduled_tasks(plan)
        if skipped:
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
            st.warning(f"{len(skipped)} task(s) did not fit in your budget.")
            st.dataframe(skipped_rows, use_container_width=True, hide_index=True)
        else:
            st.success("All due tasks fit in today's budget.")


def render_ai_coach_page(kb_file: str) -> None:
    st.markdown('<div class="pawpal-section-title">AI Coach (RAG)</div>', unsafe_allow_html=True)
    st.caption("Chat with PawPal+ and get source-grounded pet-care guidance.")

    _load_env_file()

    llm_ready = bool((os.getenv("OPENAI_API_KEY") or "").strip())
    model_label = _default_chat_model()
    if llm_ready:
        base = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        st.success(
            f"**LLM+RAG:** answers use retrieval + `{model_label}` (endpoint `{base}`). "
            "Citations `[S1]`… must match retrieved sources."
        )
    else:
        st.warning(
            "No `OPENAI_API_KEY` in environment or `.env` — using offline **fallback** summaries. "
            "Add your key from [OpenAI API keys](https://platform.openai.com/api-keys) to `.env` and restart Streamlit.",
        )

    st.markdown(
        """
        <div class="pawpal-card">
            <strong>AI Coach contract</strong><br/>
            <span class="pawpal-muted">Source-grounded answers with citations and fallback safety.</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("Question scope and guardrails"):
        q_col1, q_col2 = st.columns(2)
        with q_col1:
            st.markdown("**Supported question types**")
            for item in RAG_SUPPORTED_QUESTIONS:
                st.markdown(f"- {item}")
        with q_col2:
            st.markdown("**Not supported**")
            for item in RAG_NOT_SUPPORTED:
                st.markdown(f"- {item}")
        st.markdown("**Guardrails in effect**")
        for item in RAG_GUARDRAILS:
            st.markdown(f"- {item}")

    st.markdown("**Try a starter prompt**")
    starter_col1, starter_col2, starter_col3 = st.columns(3)
    submitted_question = ""
    with starter_col1:
        if st.button("Walk + meal timing", use_container_width=True):
            submitted_question = "Should I feed my dog before or after a walk today?"
    with starter_col2:
        if st.button("Hydration routine", use_container_width=True):
            submitted_question = "What is a good daily hydration routine for cats?"
    with starter_col3:
        if st.button("Plan-aware advice", use_container_width=True):
            submitted_question = "Given today's plan, suggest the best feeding window."

    include_schedule = st.checkbox("Include today's schedule context", value=True)

    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("Clear chat", use_container_width=True):
            st.session_state.ai_chat_history = []
            st.success("AI chat history cleared.")

    if st.session_state.ai_chat_history:
        for message in st.session_state.ai_chat_history:
            role = message.get("role", "assistant")
            with st.chat_message("user" if role == "user" else "assistant"):
                st.markdown(message.get("content", ""))
                if role == "assistant":
                    mode = message.get("mode", "")
                    if mode == "openai":
                        st.caption("Rendered with OpenAI (RAG + citations check).")
                    elif mode == "fallback":
                        st.caption("Offline fallback (same sources, template layout).")
                    sources = message.get("sources", [])
                    if sources:
                        st.markdown("**Sources used**")
                        for source in sources:
                            st.markdown(f"- {source['title']}")

    typed_question = st.chat_input("Ask PawPal+ anything about your pet-care plan")
    question = submitted_question or (typed_question.strip() if typed_question else "")

    if question:
        st.session_state.ai_chat_history.append({"role": "user", "content": question})
        st.session_state.ai_chat_history = st.session_state.ai_chat_history[-20:]

        context = format_plan_context(st.session_state.latest_plan) if include_schedule else ""
        try:
            assistant = RagAssistant(kb_file)
            with st.spinner("Thinking..."):
                result = assistant.answer(
                    question,
                    extra_context=context,
                    chat_history=st.session_state.ai_chat_history,
                )
        except FileNotFoundError:
            st.error("`knowledge_base.json` is missing. Add it to enable AI Coach.")
            return
        except Exception:
            st.error("AI Coach hit an unexpected error. Check `logs/ai.log` and try again.")
            return

        st.session_state.ai_chat_history.append(
            {
                "role": "assistant",
                "content": result["answer"],
                "sources": result.get("sources", []),
                "mode": result.get("mode", "unknown"),
            }
        )
        st.session_state.ai_chat_history = st.session_state.ai_chat_history[-20:]

        st.rerun()
