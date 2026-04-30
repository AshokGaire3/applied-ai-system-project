"""
PawPal+ tests — run with:  python -m pytest
"""

import sys
import os
from datetime import date, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from pawpal_system import Task, Pet, Owner, Scheduler


# ---------------------------------------------------------------------------
# Original tests (Phase 2)
# ---------------------------------------------------------------------------

def test_task_completion():
    """mark_complete() should flip completed from False to True."""
    task = Task("Morning walk", duration_minutes=30, priority="high", frequency="daily")

    assert task.completed is False

    task.mark_complete()

    assert task.completed is True


def test_add_task_increases_pet_task_count():
    """Adding a task to a Pet should increase its task count by 1."""
    pet = Pet(name="Mochi", species="dog")

    assert len(pet.get_tasks()) == 0

    pet.add_task(Task("Breakfast feeding", duration_minutes=10, priority="high", frequency="daily"))

    assert len(pet.get_tasks()) == 1


# ---------------------------------------------------------------------------
# Phase 5 — Sorting
# ---------------------------------------------------------------------------

def test_sort_by_time_orders_tasks_by_start_time():
    """sort_by_time() should return tasks in HH:MM chronological order."""
    owner = Owner("Jordan", available_minutes_per_day=120)
    pet = Pet("Mochi", "dog")
    owner.add_pet(pet)

    t1 = Task("Lunch walk",     duration_minutes=20, priority="medium", start_time="12:00")
    t2 = Task("Morning walk",   duration_minutes=30, priority="high",   start_time="07:30")
    t3 = Task("Evening walk",   duration_minutes=25, priority="low",    start_time="18:00")

    # Added out of order on purpose
    tasks = [t1, t2, t3]

    scheduler = Scheduler(owner)
    sorted_tasks = scheduler.sort_by_time(tasks)

    assert [t.start_time for t in sorted_tasks] == ["07:30", "12:00", "18:00"]


def test_sort_by_time_puts_no_time_tasks_last():
    """Tasks with no start_time should sort to the end."""
    owner = Owner("Jordan", available_minutes_per_day=120)
    scheduler = Scheduler(owner)

    t_timed   = Task("Walk",    duration_minutes=20, start_time="08:00")
    t_untimed = Task("Feeding", duration_minutes=10)  # no start_time

    result = scheduler.sort_by_time([t_untimed, t_timed])

    assert result[0].start_time == "08:00"
    assert result[1].start_time is None


# ---------------------------------------------------------------------------
# Phase 5 — Filtering
# ---------------------------------------------------------------------------

def test_filter_tasks_by_pet_name():
    """filter_tasks(pet_name=...) should return only that pet's tasks."""
    owner = Owner("Jordan", available_minutes_per_day=120)
    mochi = Pet("Mochi", "dog")
    luna  = Pet("Luna",  "cat")
    mochi.add_task(Task("Walk",     duration_minutes=30, priority="high"))
    luna.add_task( Task("Playtime", duration_minutes=20, priority="low"))
    owner.add_pet(mochi)
    owner.add_pet(luna)

    scheduler = Scheduler(owner)
    results = scheduler.filter_tasks(pet_name="Mochi")

    assert len(results) == 1
    assert results[0][0].name == "Mochi"


def test_filter_tasks_by_completion_status():
    """filter_tasks(completed=True) should return only completed tasks."""
    owner = Owner("Jordan", available_minutes_per_day=120)
    pet = Pet("Mochi", "dog")
    t_done    = Task("Walk",    duration_minutes=30, priority="high")
    t_pending = Task("Feeding", duration_minutes=10, priority="high")
    t_done.mark_complete()
    pet.add_task(t_done)
    pet.add_task(t_pending)
    owner.add_pet(pet)

    scheduler = Scheduler(owner)
    done    = scheduler.filter_tasks(completed=True)
    pending = scheduler.filter_tasks(completed=False)

    assert len(done)    == 1
    assert len(pending) == 1
    assert done[0][1].description    == "Walk"
    assert pending[0][1].description == "Feeding"


# ---------------------------------------------------------------------------
# Phase 5 — Recurring tasks
# ---------------------------------------------------------------------------

def test_daily_task_sets_next_due_date_to_tomorrow():
    """mark_complete() on a daily task should set next_due_date to today + 1 day."""
    task = Task("Morning walk", duration_minutes=30, frequency="daily")
    today = date.today()

    task.mark_complete(on_date=today)

    assert task.next_due_date == today + timedelta(days=1)


def test_weekly_task_sets_next_due_date_to_next_week():
    """mark_complete() on a weekly task should set next_due_date to today + 7 days."""
    task = Task("Flea treatment", duration_minutes=15, frequency="weekly")
    today = date.today()

    task.mark_complete(on_date=today)

    assert task.next_due_date == today + timedelta(weeks=1)


def test_completed_daily_task_is_not_due_until_next_due_date():
    """A completed daily task should not be due until its next_due_date arrives."""
    task = Task("Walk", duration_minutes=20, frequency="daily")
    today = date.today()

    task.mark_complete(on_date=today)

    # Still today → not due
    assert task.is_due(on_date=today) is False
    # Tomorrow → due again
    assert task.is_due(on_date=today + timedelta(days=1)) is True


# ---------------------------------------------------------------------------
# Phase 5 — Conflict detection
# ---------------------------------------------------------------------------

def test_detect_time_conflicts_finds_overlapping_tasks():
    """detect_time_conflicts() should flag two tasks with overlapping HH:MM windows."""
    owner = Owner("Jordan", available_minutes_per_day=120)
    mochi = Pet("Mochi", "dog")
    luna  = Pet("Luna",  "cat")

    # Both start at 09:00 and run 20 min — clear overlap
    mochi.add_task(Task("Flea treatment", duration_minutes=20, start_time="09:00"))
    luna.add_task( Task("Playtime",       duration_minutes=20, start_time="09:00"))

    owner.add_pet(mochi)
    owner.add_pet(luna)

    scheduler = Scheduler(owner)
    conflicts = scheduler.detect_time_conflicts()

    assert len(conflicts) == 1
    assert "WARNING" in conflicts[0]


def test_detect_time_conflicts_no_conflict_when_sequential():
    """detect_time_conflicts() should return empty list when tasks do not overlap."""
    owner = Owner("Jordan", available_minutes_per_day=120)
    pet = Pet("Mochi", "dog")

    pet.add_task(Task("Walk",    duration_minutes=30, start_time="08:00"))  # ends 08:30
    pet.add_task(Task("Feeding", duration_minutes=10, start_time="08:30"))  # starts 08:30

    owner.add_pet(pet)
    scheduler = Scheduler(owner)

    assert scheduler.detect_time_conflicts() == []


# ---------------------------------------------------------------------------
# Phase 5 — build_daily_plan() sorting by priority
# ---------------------------------------------------------------------------

def test_build_daily_plan_sorts_high_before_medium_before_low():
    """build_daily_plan() should return tasks ordered high → medium → low priority."""
    owner = Owner("Jordan", available_minutes_per_day=120)
    pet = Pet("Mochi", "dog")
    pet.add_task(Task("Play fetch",    duration_minutes=10, priority="low"))
    pet.add_task(Task("Give medicine", duration_minutes=10, priority="high"))
    pet.add_task(Task("Brush fur",     duration_minutes=10, priority="medium"))
    owner.add_pet(pet)

    scheduler = Scheduler(owner)
    plan = scheduler.build_daily_plan()

    priorities = [e["task"].priority for e in plan]
    assert priorities == ["high", "medium", "low"]


def test_build_daily_plan_same_priority_shorter_task_first():
    """Within equal priority, the shorter task is scheduled first."""
    owner = Owner("Jordan", available_minutes_per_day=120)
    pet = Pet("Mochi", "dog")
    pet.add_task(Task("Long walk",   duration_minutes=45, priority="high"))
    pet.add_task(Task("Quick treat", duration_minutes=5,  priority="high"))
    owner.add_pet(pet)

    scheduler = Scheduler(owner)
    plan = scheduler.build_daily_plan()

    assert plan[0]["task"].description == "Quick treat"
    assert plan[1]["task"].description == "Long walk"


def test_build_daily_plan_start_end_minutes_sequential():
    """Each plan entry's start_min should equal the previous entry's end_min."""
    owner = Owner("Jordan", available_minutes_per_day=120)
    pet = Pet("Mochi", "dog")
    pet.add_task(Task("Walk",  duration_minutes=30, priority="high"))
    pet.add_task(Task("Brush", duration_minutes=15, priority="medium"))
    owner.add_pet(pet)

    scheduler = Scheduler(owner)
    plan = scheduler.build_daily_plan()

    assert plan[0]["start_min"] == 0
    assert plan[0]["end_min"]   == 30
    assert plan[1]["start_min"] == 30
    assert plan[1]["end_min"]   == 45


# ---------------------------------------------------------------------------
# Phase 5 — detect_conflicts() on plan-level dicts
# ---------------------------------------------------------------------------

def _make_plan_entry(description, start, end, priority="medium"):
    """Build a minimal plan dict for detect_conflicts() tests."""
    task = Task(description, duration_minutes=end - start, priority=priority)
    return {"task": task, "start_min": start, "end_min": end}


def test_detect_conflicts_fully_overlapping_tasks():
    """Two tasks at the exact same time slot produce one conflict message."""
    owner = Owner("Jordan", available_minutes_per_day=120)
    scheduler = Scheduler(owner)

    plan = [
        _make_plan_entry("Walk",    start=0, end=30),
        _make_plan_entry("Feeding", start=0, end=30),
    ]
    conflicts = scheduler.detect_conflicts(plan)

    assert len(conflicts) == 1
    assert "Walk" in conflicts[0]
    assert "Feeding" in conflicts[0]


def test_detect_conflicts_no_conflict_for_sequential_tasks():
    """Sequential non-overlapping tasks produce zero conflicts."""
    owner = Owner("Jordan", available_minutes_per_day=120)
    scheduler = Scheduler(owner)

    plan = [
        _make_plan_entry("Walk",    start=0,  end=30),
        _make_plan_entry("Feeding", start=30, end=45),
        _make_plan_entry("Play",    start=45, end=75),
    ]
    assert scheduler.detect_conflicts(plan) == []


def test_detect_conflicts_empty_plan():
    """An empty plan should never produce conflicts."""
    owner = Owner("Jordan", available_minutes_per_day=120)
    scheduler = Scheduler(owner)
    assert scheduler.detect_conflicts([]) == []


# ---------------------------------------------------------------------------
# Phase 5 — Edge cases
# ---------------------------------------------------------------------------

def test_pet_with_no_tasks_produces_empty_plan():
    """A registered pet with no tasks results in an empty daily plan."""
    owner = Owner("Jordan", available_minutes_per_day=120)
    owner.add_pet(Pet("Ghost", "cat"))
    scheduler = Scheduler(owner)
    assert scheduler.build_daily_plan() == []


def test_task_exceeding_budget_is_unscheduled():
    """A task longer than the owner's full time budget should not appear in the plan."""
    owner = Owner("Jordan", available_minutes_per_day=10)
    pet = Pet("Rex", "dog")
    pet.add_task(Task("Long bath", duration_minutes=60, priority="high"))
    owner.add_pet(pet)

    scheduler = Scheduler(owner)
    plan = scheduler.build_daily_plan()
    unscheduled = scheduler.get_unscheduled_tasks(plan)

    assert len(plan) == 0
    assert len(unscheduled) == 1
    assert unscheduled[0][1].description == "Long bath"


def test_owner_persistence_round_trip_preserves_date_fields(tmp_path):
    owner = Owner("Jordan", available_minutes_per_day=120)
    pet = Pet("Mochi", "dog")
    task = Task("Morning walk", duration_minutes=20, frequency="daily", start_time="08:00")
    task.mark_complete(on_date=date(2026, 4, 28))
    pet.add_task(task)
    owner.add_pet(pet)

    file_path = tmp_path / "owner_data.json"
    owner.save_to_json(str(file_path))
    loaded = Owner.load_from_json(str(file_path))

    assert loaded is not None
    loaded_task = loaded.get_pets()[0].get_tasks()[0]
    assert loaded_task.last_completed_date == date(2026, 4, 28)
    assert loaded_task.next_due_date == date(2026, 4, 29)


def test_min_to_time_base_starts_at_eight_am():
    owner = Owner("Jordan", available_minutes_per_day=120)
    scheduler = Scheduler(owner)
    assert scheduler._min_to_time(0) == "08:00"
    assert scheduler._min_to_time(90) == "09:30"


def test_low_priority_task_dropped_when_budget_full():
    """High-priority task fills the budget; the low-priority task is unscheduled."""
    owner = Owner("Jordan", available_minutes_per_day=30)
    pet = Pet("Buddy", "dog")
    pet.add_task(Task("High task", duration_minutes=30, priority="high"))
    pet.add_task(Task("Low task",  duration_minutes=20, priority="low"))
    owner.add_pet(pet)

    scheduler = Scheduler(owner)
    plan = scheduler.build_daily_plan()
    unscheduled = scheduler.get_unscheduled_tasks(plan)

    assert any(e["task"].description == "High task" for e in plan)
    assert len(unscheduled) == 1
    assert unscheduled[0][1].description == "Low task"


def test_invalid_priority_raises_value_error():
    """Creating a Task with an unknown priority string should raise ValueError."""
    with pytest.raises(ValueError, match="priority"):
        Task("Bad task", duration_minutes=10, priority="urgent")


def test_invalid_start_time_format_raises_value_error():
    """Creating a Task with a malformed start_time should raise ValueError."""
    with pytest.raises(ValueError, match="start_time"):
        Task("Bad time", duration_minutes=10, start_time="8am")
