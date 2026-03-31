"""
PawPal+ tests — run with:  python -m pytest
"""

import sys
import os
from datetime import date, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

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
