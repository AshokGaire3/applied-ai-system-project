# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Smarter Scheduling

PawPal+ includes four algorithmic features that make the daily plan more intelligent:

- **Sorting** — `Scheduler.sort_by_time()` orders tasks by their optional `start_time` field (HH:MM string) using a `lambda` key with Python's `sorted()`. Tasks without a preferred time slot sort to the end automatically.
- **Filtering** — `Scheduler.filter_tasks()` lets you slice the full task list by pet name, completion status, or both at once.
- **Recurring tasks** — When `task.mark_complete()` is called, `next_due_date` is automatically set using `timedelta`: +1 day for daily tasks, +7 days for weekly tasks. `is_due()` uses this date to resurface the task at the right time.
- **Conflict detection** — `detect_time_conflicts()` scans all tasks that have a `start_time` and flags any overlapping windows. It returns a warning message instead of crashing, so the owner can decide how to resolve it.

Run `python main.py` to see all four features demonstrated in the terminal.

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
