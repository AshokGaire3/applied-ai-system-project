"""
PawPal+ CLI demo — run with:  python main.py

Demonstrates sorting, filtering, recurring tasks, and conflict detection.
"""

from datetime import date
from pawpal_system import Task, Pet, Owner, Scheduler

SEP  = "=" * 58
SEP2 = "-" * 58

# ---------------------------------------------------------------------------
# 1. Setup: Owner + Pets
# ---------------------------------------------------------------------------

jordan = Owner(name="Jordan", available_minutes_per_day=180)

mochi = Pet(name="Mochi", species="dog", age_years=3)
luna  = Pet(name="Luna",  species="cat", age_years=5)

# ---------------------------------------------------------------------------
# 2. Tasks added OUT OF ORDER by start_time (intentional, to demo sorting)
#    Mochi's tasks
# ---------------------------------------------------------------------------

mochi.add_task(Task("Obedience training", duration_minutes=20, priority="medium",
                    frequency="daily",    start_time="10:00"))
mochi.add_task(Task("Morning walk",       duration_minutes=30, priority="high",
                    frequency="daily",    start_time="07:30"))
mochi.add_task(Task("Breakfast feeding",  duration_minutes=10, priority="high",
                    frequency="daily",    start_time="08:00"))
mochi.add_task(Task("Flea treatment",     duration_minutes=15, priority="high",
                    frequency="weekly",   start_time="09:00"))

# Luna's tasks — note "Evening playtime" has the same window as "Flea treatment"
# to demonstrate conflict detection
luna.add_task(Task("Dinner feeding",    duration_minutes=10, priority="high",
                   frequency="daily",   start_time="17:30"))
luna.add_task(Task("Litter box clean",  duration_minutes=10, priority="medium",
                   frequency="daily",   start_time="08:30"))
luna.add_task(Task("Playtime",          duration_minutes=25, priority="low",
                   frequency="daily",   start_time="19:00"))
luna.add_task(Task("Evening playtime",  duration_minutes=20, priority="medium",
                   frequency="daily",   start_time="09:00"))  # overlaps Flea treatment

jordan.add_pet(mochi)
jordan.add_pet(luna)

scheduler = Scheduler(owner=jordan)

# ---------------------------------------------------------------------------
# 3. SORTING — sort all tasks by start_time using a lambda key on HH:MM strings
# ---------------------------------------------------------------------------

print(SEP)
print("  SECTION 1: Tasks sorted by start_time (HH:MM)")
print(SEP)

all_tasks = [task for _, task in jordan.get_all_tasks()]
sorted_tasks = scheduler.sort_by_time(all_tasks)

for t in sorted_tasks:
    time_label = t.start_time if t.start_time else "(no time)"
    print(f"  {time_label}  [{t.priority.upper():6}]  {t.description}  ({t.duration_minutes}min)")

# ---------------------------------------------------------------------------
# 4. FILTERING — by pet name and by completion status
# ---------------------------------------------------------------------------

print()
print(SEP)
print("  SECTION 2: Filtering tasks")
print(SEP)

print("\n  -- Mochi's tasks only --")
mochi_pairs = scheduler.filter_tasks(pet_name="Mochi")
for pet, task in mochi_pairs:
    print(f"  [{task.priority.upper()}] {task.description} ({task.frequency})")

print("\n  -- Pending (not yet completed) tasks --")
pending = scheduler.filter_tasks(completed=False)
for pet, task in pending:
    print(f"  {pet.name}: {task.description}")

# ---------------------------------------------------------------------------
# 5. RECURRING TASKS — mark_complete auto-schedules next_due_date via timedelta
# ---------------------------------------------------------------------------

print()
print(SEP)
print("  SECTION 3: Recurring task logic")
print(SEP)

walk = mochi.get_tasks()[1]  # "Morning walk" (daily)
print(f"\n  Task: '{walk.description}' | frequency: {walk.frequency}")
print(f"  Before mark_complete: completed={walk.completed}, next_due_date={walk.next_due_date}")

walk.mark_complete(on_date=date.today())
print(f"  After  mark_complete: completed={walk.completed}, next_due_date={walk.next_due_date}")
print(f"  -> Will automatically reappear on: {walk.next_due_date} (today + 1 day via timedelta)")

flea = mochi.get_tasks()[3]  # "Flea treatment" (weekly)
flea.mark_complete(on_date=date.today())
print(f"\n  Task: '{flea.description}' | frequency: {flea.frequency}")
print(f"  next_due_date set to: {flea.next_due_date} (today + 7 days via timedelta)")

# ---------------------------------------------------------------------------
# 6. CONFLICT DETECTION — two tasks overlap at 09:00
# ---------------------------------------------------------------------------

print()
print(SEP)
print("  SECTION 4: Conflict detection")
print(SEP)

print("\n  Checking raw start_time conflicts across all tasks...")
time_conflicts = scheduler.detect_time_conflicts()

if time_conflicts:
    for warning in time_conflicts:
        print(f"  {warning}")
else:
    print("  No start_time conflicts found.")

# Also check the built plan for slot-level conflicts
plan = scheduler.build_daily_plan()
plan_conflicts = scheduler.detect_conflicts(plan)

print()
if plan_conflicts:
    print("  Scheduled plan conflicts:")
    for warning in plan_conflicts:
        print(f"  {warning}")
else:
    print("  No overlaps in the built plan (greedy scheduler assigns sequential slots).")

# ---------------------------------------------------------------------------
# 7. TODAY'S SCHEDULE
# ---------------------------------------------------------------------------

print()
print(SEP)
print("  SECTION 5: Today's Schedule")
print(SEP)
print()
print(scheduler.summary(plan))

skipped = scheduler.get_unscheduled_tasks(plan)
if skipped:
    print()
    print("  Tasks that did not fit today's time budget:")
    for pet, task in skipped:
        print(f"    * {task.description} ({pet.name}, {task.duration_minutes}min, priority={task.priority})")

print()
print(SEP)
