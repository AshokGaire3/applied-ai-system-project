import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from pawpal_system import Owner, Pet, Scheduler, Task
from ui.helpers import format_plan_context


def test_format_plan_context_empty_plan():
    assert format_plan_context([]) == "No scheduled tasks yet."


def test_format_plan_context_multi_pet_plan():
    owner = Owner("Jordan", available_minutes_per_day=180)
    mochi = Pet("Mochi", "dog")
    luna = Pet("Luna", "cat")
    mochi.add_task(Task("Morning walk", duration_minutes=20, priority="high"))
    luna.add_task(Task("Breakfast", duration_minutes=10, priority="medium"))
    owner.add_pet(mochi)
    owner.add_pet(luna)

    scheduler = Scheduler(owner)
    plan = scheduler.build_daily_plan()
    context = format_plan_context(plan)
    assert "Scheduled tasks:" in context
    assert "Mochi: Morning walk" in context
    assert "Luna: Breakfast" in context
