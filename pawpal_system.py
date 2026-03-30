"""
PawPal+ core system: Task, Pet, Owner, Scheduler
"""

from datetime import date, timedelta
from typing import Optional


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

class Task:
    """A single pet-care activity."""

    VALID_PRIORITIES = ("low", "medium", "high")
    VALID_FREQUENCIES = ("daily", "weekly", "as_needed")

    def __init__(
        self,
        description: str,
        duration_minutes: int,
        priority: str = "medium",
        frequency: str = "daily",
    ):
        if priority not in self.VALID_PRIORITIES:
            raise ValueError(f"priority must be one of {self.VALID_PRIORITIES}")
        if frequency not in self.VALID_FREQUENCIES:
            raise ValueError(f"frequency must be one of {self.VALID_FREQUENCIES}")
        if duration_minutes <= 0:
            raise ValueError("duration_minutes must be positive")

        self.description = description
        self.duration_minutes = duration_minutes
        self.priority = priority
        self.frequency = frequency
        self.completed: bool = False
        self.last_completed_date: Optional[date] = None

    # ------------------------------------------------------------------
    # State helpers
    # ------------------------------------------------------------------

    def mark_complete(self, on_date: Optional[date] = None) -> None:
        """Mark the task as completed (defaults to today)."""
        self.completed = True
        self.last_completed_date = on_date or date.today()

    def reset(self) -> None:
        """Reset completion status (e.g. at the start of a new day)."""
        self.completed = False

    def is_due(self, on_date: Optional[date] = None) -> bool:
        """
        Return True when the task should appear in today's schedule.

        - daily      → always due (unless already completed today)
        - weekly     → due if never done OR last done ≥ 7 days ago
        - as_needed  → always due (owner decides when to include it)
        """
        check_date = on_date or date.today()

        if self.completed and self.last_completed_date == check_date:
            return False  # already done today

        if self.frequency == "daily":
            return True
        if self.frequency == "weekly":
            if self.last_completed_date is None:
                return True
            return (check_date - self.last_completed_date).days >= 7
        # as_needed
        return True

    # ------------------------------------------------------------------
    # Priority helpers
    # ------------------------------------------------------------------

    def priority_rank(self) -> int:
        """Return a numeric rank for sorting (higher = more urgent)."""
        return {"high": 3, "medium": 2, "low": 1}[self.priority]

    # ------------------------------------------------------------------
    # Dunder
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        status = "done" if self.completed else "pending"
        return (
            f"Task({self.description!r}, {self.duration_minutes}min, "
            f"priority={self.priority}, freq={self.frequency}, {status})"
        )


# ---------------------------------------------------------------------------
# Pet
# ---------------------------------------------------------------------------

class Pet:
    """Stores pet details and owns a list of care tasks."""

    def __init__(self, name: str, species: str, age_years: float = 0.0):
        self.name = name
        self.species = species.lower()
        self.age_years = age_years
        self._tasks: list[Task] = []

    # ------------------------------------------------------------------
    # Task management
    # ------------------------------------------------------------------

    def add_task(self, task: Task) -> None:
        """Attach a Task to this pet."""
        self._tasks.append(task)

    def remove_task(self, description: str) -> bool:
        """Remove the first task whose description matches. Returns True if found."""
        for i, t in enumerate(self._tasks):
            if t.description.lower() == description.lower():
                self._tasks.pop(i)
                return True
        return False

    def get_tasks(self) -> list[Task]:
        """Return a copy of the task list (preserves internal ordering)."""
        return list(self._tasks)

    def get_due_tasks(self, on_date: Optional[date] = None) -> list[Task]:
        """Return only tasks that are due on the given date."""
        return [t for t in self._tasks if t.is_due(on_date)]

    def reset_daily_tasks(self) -> None:
        """Reset completion flags on all daily tasks (call at start of each day)."""
        for task in self._tasks:
            if task.frequency == "daily":
                task.reset()

    def total_task_time(self) -> int:
        """Sum of duration_minutes across all tasks."""
        return sum(t.duration_minutes for t in self._tasks)

    # ------------------------------------------------------------------
    # Dunder
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return f"Pet(name={self.name!r}, species={self.species!r}, tasks={len(self._tasks)})"


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------

class Owner:
    """Manages one or more pets and exposes their collective task data."""

    def __init__(self, name: str, available_minutes_per_day: int = 120):
        if available_minutes_per_day <= 0:
            raise ValueError("available_minutes_per_day must be positive")

        self.name = name
        self.available_minutes_per_day = available_minutes_per_day
        self._pets: list[Pet] = []

    # ------------------------------------------------------------------
    # Pet management
    # ------------------------------------------------------------------

    def add_pet(self, pet: Pet) -> None:
        """Register a pet with this owner."""
        self._pets.append(pet)

    def remove_pet(self, name: str) -> bool:
        """Remove the first pet whose name matches. Returns True if found."""
        for i, p in enumerate(self._pets):
            if p.name.lower() == name.lower():
                self._pets.pop(i)
                return True
        return False

    def get_pets(self) -> list[Pet]:
        """Return a copy of the pet list."""
        return list(self._pets)

    # ------------------------------------------------------------------
    # Aggregate task access (the bridge Scheduler uses)
    # ------------------------------------------------------------------

    def get_all_tasks(self) -> list[tuple[Pet, Task]]:
        """
        Return every (pet, task) pair across all pets.
        The Scheduler calls this to retrieve the full workload.
        """
        return [(pet, task) for pet in self._pets for task in pet.get_tasks()]

    def get_all_due_tasks(self, on_date: Optional[date] = None) -> list[tuple[Pet, Task]]:
        """
        Return (pet, task) pairs for tasks that are due on the given date.
        """
        return [
            (pet, task)
            for pet in self._pets
            for task in pet.get_due_tasks(on_date)
        ]

    def total_due_minutes(self, on_date: Optional[date] = None) -> int:
        """Total minutes required for all due tasks today."""
        return sum(t.duration_minutes for _, t in self.get_all_due_tasks(on_date))

    # ------------------------------------------------------------------
    # Dunder
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"Owner(name={self.name!r}, pets={len(self._pets)}, "
            f"available={self.available_minutes_per_day}min/day)"
        )


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

class Scheduler:
    """
    The 'brain' of PawPal+.

    Retrieves tasks from an Owner's pets, sorts by priority, detects time
    conflicts, handles recurring tasks, and produces a daily plan.
    """

    def __init__(self, owner: Owner):
        self.owner = owner

    # ------------------------------------------------------------------
    # Core scheduling
    # ------------------------------------------------------------------

    def build_daily_plan(self, on_date: Optional[date] = None) -> list[dict]:
        """
        Build a prioritised daily plan that fits within the owner's
        available time budget.

        Returns a list of plan entries in scheduled order:
            {
                "pet":       <Pet>,
                "task":      <Task>,
                "start_min": <int>,   # minutes from 08:00
                "end_min":   <int>,
                "reason":    <str>,
            }

        Tasks that don't fit are omitted (see get_unscheduled_tasks).
        """
        check_date = on_date or date.today()
        due_pairs = self.owner.get_all_due_tasks(check_date)

        # Sort: high priority first, then by shortest duration (greedy fit)
        sorted_pairs = sorted(
            due_pairs,
            key=lambda pt: (-pt[1].priority_rank(), pt[1].duration_minutes),
        )

        plan: list[dict] = []
        elapsed = 0  # minutes used so far

        for pet, task in sorted_pairs:
            if elapsed + task.duration_minutes > self.owner.available_minutes_per_day:
                continue  # doesn't fit — skip for now

            reason = self._explain(pet, task, elapsed)
            plan.append(
                {
                    "pet": pet,
                    "task": task,
                    "start_min": elapsed,
                    "end_min": elapsed + task.duration_minutes,
                    "reason": reason,
                }
            )
            elapsed += task.duration_minutes

        return plan

    # ------------------------------------------------------------------
    # Conflict detection
    # ------------------------------------------------------------------

    def detect_conflicts(self, plan: list[dict]) -> list[str]:
        """
        Scan a plan for time-slot overlaps.
        Returns a list of human-readable conflict descriptions.
        """
        conflicts: list[str] = []
        for i in range(len(plan)):
            for j in range(i + 1, len(plan)):
                a, b = plan[i], plan[j]
                # Overlap when one starts before the other ends
                if a["start_min"] < b["end_min"] and b["start_min"] < a["end_min"]:
                    conflicts.append(
                        f"Overlap: '{a['task'].description}' ({a['start_min']}–{a['end_min']}min) "
                        f"conflicts with '{b['task'].description}' ({b['start_min']}–{b['end_min']}min)"
                    )
        return conflicts

    # ------------------------------------------------------------------
    # Unscheduled tasks
    # ------------------------------------------------------------------

    def get_unscheduled_tasks(
        self, plan: list[dict], on_date: Optional[date] = None
    ) -> list[tuple[Pet, Task]]:
        """Return due tasks that were excluded from the plan (time budget exceeded)."""
        check_date = on_date or date.today()
        scheduled_tasks = {entry["task"] for entry in plan}
        return [
            (pet, task)
            for pet, task in self.owner.get_all_due_tasks(check_date)
            if task not in scheduled_tasks
        ]

    # ------------------------------------------------------------------
    # Recurring task management
    # ------------------------------------------------------------------

    def advance_day(self, on_date: Optional[date] = None) -> None:
        """
        Mark all scheduled daily tasks as complete and reset them for
        tomorrow. Call this at end-of-day to roll the planner forward.
        """
        check_date = on_date or date.today()
        for pet in self.owner.get_pets():
            pet.reset_daily_tasks()

    # ------------------------------------------------------------------
    # Summary display
    # ------------------------------------------------------------------

    def summary(self, plan: list[dict]) -> str:
        """Return a plain-text summary of the plan (useful for CLI + Streamlit)."""
        if not plan:
            return "No tasks scheduled."

        lines = [f"Daily plan for {self.owner.name}  ({date.today()})", ""]
        for entry in plan:
            start = self._min_to_time(entry["start_min"])
            end = self._min_to_time(entry["end_min"])
            lines.append(
                f"  {start}–{end}  [{entry['task'].priority.upper()}]  "
                f"{entry['task'].description}  ({entry['pet'].name})"
            )
            lines.append(f"           → {entry['reason']}")
        lines.append("")
        lines.append(
            f"Total time: {sum(e['end_min'] - e['start_min'] for e in plan)} min "
            f"/ {self.owner.available_minutes_per_day} min available"
        )
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _explain(self, pet: Pet, task: Task, elapsed: int) -> str:
        """Generate a one-line reason string for a scheduled task."""
        time_str = self._min_to_time(elapsed)
        freq_note = {"daily": "due daily", "weekly": "due this week", "as_needed": "requested"}[
            task.frequency
        ]
        return (
            f"Scheduled at {time_str} for {pet.name} — "
            f"{freq_note}, priority={task.priority}"
        )

    @staticmethod
    def _min_to_time(minutes: int) -> str:
        """Convert offset-from-08:00 minutes to a HH:MM string."""
        total = 8 * 60 + minutes  # start day at 08:00
        h, m = divmod(total, 60)
        return f"{h:02d}:{m:02d}"

    def __repr__(self) -> str:
        return f"Scheduler(owner={self.owner.name!r})"
