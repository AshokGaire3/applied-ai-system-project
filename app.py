import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")
st.caption("A daily pet care planner powered by Python classes.")

st.divider()

# ---------------------------------------------------------------------------
# Step 2: Session state — the "vault"
# The Owner object lives here so it survives every Streamlit rerun.
# We only create it once; after that we just read it from the vault.
# ---------------------------------------------------------------------------

# ── Owner setup ─────────────────────────────────────────────────────────────
st.subheader("1. Owner Setup")

owner_name = st.text_input("Your name", value="Jordan")
available_minutes = st.number_input(
    "Minutes available for pet care today",
    min_value=10, max_value=480, value=120, step=10
)

if st.button("Set / Update Owner"):
    # Always rebuild the owner when the user explicitly submits,
    # but keep any pets that were already registered.
    if "owner" not in st.session_state:
        st.session_state.owner = Owner(
            name=owner_name,
            available_minutes_per_day=int(available_minutes)
        )
    else:
        # Update name and budget without losing pets
        st.session_state.owner.name = owner_name
        st.session_state.owner.available_minutes_per_day = int(available_minutes)
    st.success(f"Owner set: {st.session_state.owner}")

if "owner" not in st.session_state:
    st.info("Set an owner above to continue.")
    st.stop()          # Nothing below can run without an owner

st.divider()

# ── Pet management ───────────────────────────────────────────────────────────
st.subheader("2. Add a Pet")

col1, col2, col3 = st.columns(3)
with col1:
    pet_name = st.text_input("Pet name", value="Mochi")
with col2:
    species = st.selectbox("Species", ["dog", "cat", "rabbit", "other"])
with col3:
    age = st.number_input("Age (years)", min_value=0.0, max_value=30.0, value=2.0, step=0.5)

if st.button("Add Pet"):
    # Check the owner's existing pets so we don't add the same name twice
    existing_names = [p.name.lower() for p in st.session_state.owner.get_pets()]
    if pet_name.lower() in existing_names:
        st.warning(f"A pet named '{pet_name}' already exists.")
    else:
        new_pet = Pet(name=pet_name, species=species, age_years=float(age))
        st.session_state.owner.add_pet(new_pet)   # <-- Pet method call
        st.success(f"Added {new_pet.name} the {new_pet.species}!")

# Show current pets
pets = st.session_state.owner.get_pets()
if pets:
    st.markdown("**Registered pets:**")
    for p in pets:
        st.markdown(f"- **{p.name}** ({p.species}, {p.age_years}y) — {len(p.get_tasks())} task(s)")
else:
    st.info("No pets yet. Add one above.")

st.divider()

# ── Task management ──────────────────────────────────────────────────────────
st.subheader("3. Add a Task")

if not pets:
    st.info("Add a pet first before adding tasks.")
else:
    pet_names = [p.name for p in pets]
    selected_pet_name = st.selectbox("Assign task to", pet_names)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        task_desc = st.text_input("Task description", value="Morning walk")
    with col2:
        duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
    with col3:
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
    with col4:
        frequency = st.selectbox("Frequency", ["daily", "weekly", "as_needed"])

    if st.button("Add Task"):
        # Find the selected Pet object from the owner's list
        target_pet = next(p for p in pets if p.name == selected_pet_name)
        new_task = Task(
            description=task_desc,
            duration_minutes=int(duration),
            priority=priority,
            frequency=frequency,
        )
        target_pet.add_task(new_task)    # <-- Pet method call
        st.success(f"Task '{task_desc}' added to {target_pet.name}!")

    # Show all tasks across all pets
    all_pairs = st.session_state.owner.get_all_tasks()
    if all_pairs:
        st.markdown("**All tasks:**")
        rows = [
            {
                "Pet": pet.name,
                "Task": task.description,
                "Duration (min)": task.duration_minutes,
                "Priority": task.priority,
                "Frequency": task.frequency,
            }
            for pet, task in all_pairs
        ]
        st.table(rows)

st.divider()

# ── Schedule generation ──────────────────────────────────────────────────────
st.subheader("4. Generate Today's Schedule")

if st.button("Generate Schedule"):
    scheduler = Scheduler(st.session_state.owner)   # <-- Scheduler wired to live Owner
    plan = scheduler.build_daily_plan()

    if not plan:
        st.warning("No due tasks found. Add some tasks above and try again.")
    else:
        st.success("Schedule built!")
        st.text(scheduler.summary(plan))

        # Surface anything that didn't fit
        skipped = scheduler.get_unscheduled_tasks(plan)
        if skipped:
            st.warning(f"{len(skipped)} task(s) didn't fit in your time budget:")
            for pet, task in skipped:
                st.markdown(f"- **{task.description}** ({pet.name}) — {task.duration_minutes} min")
