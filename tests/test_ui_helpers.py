import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from pawpal_system import Owner, Pet, Scheduler, Task
from ui.helpers import build_care_handoff_document, format_plan_context


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


def test_build_care_handoff_document_lists_tasks_and_med_hint():
    owner = Owner("Jordan", available_minutes_per_day=180)
    rex = Pet("Rex", "dog", age_years=4.0)
    rex.add_task(Task("Morning pill", duration_minutes=5, priority="high", frequency="daily"))
    rex.add_task(Task("Breakfast", duration_minutes=15, priority="medium"))
    owner.add_pet(rex)
    txt = build_care_handoff_document(
        owner,
        caregiver_label="Alex",
        vet_phone="555-0100",
        emergency_line="ER vet 555-0199",
        household_notes="Kibble Brand X",
    )
    assert "Jordan" in txt and "Alex" in txt and "555-0100" in txt
    assert "Rex" in txt and "Breakfast" in txt and "Morning pill" in txt
    assert "555-0199" in txt
