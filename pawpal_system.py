"""
PawPal+ core system: Task, Pet, Owner, Scheduler
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional


# ---------------------------------------------------------------------------
# Task  (dataclass)
# ---------------------------------------------------------------------------

@dataclass
class Task:
    """A single pet-care activity with priority, duration, frequency, and optional time window."""

    description: str
    duration_minutes: int
    priority: str = "medium"
    frequency: str = "daily"
    start_time: Optional[str] = None          # preferred HH:MM window, e.g. "08:30"
    completed: bool = field(default=False, init=False)
    last_completed_date: Optional[date] = field(default=None, init=False)
    next_due_date: Optional[date] = field(default=None, init=False)

    VALID_PRIORITIES = ("low", "medium", "high")
    VALID_FREQUENCIES = ("daily", "weekly", "as_needed")

    def __post_init__(self):
        """Validate priority, frequency, start_time format, and duration after dataclass init."""
        if self.priority not in self.VALID_PRIORITIES:
            raise ValueError(f"priority must be one of {self.VALID_PRIORITIES}")
        if self.frequency not in self.VALID_FREQUENCIES:
            raise ValueError(f"frequency must be one of {self.VALID_FREQUENCIES}")
        if self.duration_minutes <= 0:
            raise ValueError("duration_minutes must be positive")
        if self.start_time is not None:
            try:
                h, m = self.start_time.split(":")
                assert 0 <= int(h) <= 23 and 0 <= int(m) <= 59
            except (ValueError, AssertionError):
                raise ValueError("start_time must be in HH:MM format, e.g. '08:30'")

    def mark_complete(self, on_date: Optional[date] = None) -> None:
        """Mark this task done, record the date, and auto-schedule the next occurrence."""
        self.completed = True
        completed_on = on_date or date.today()
        self.last_completed_date = completed_on

        # Step 3: Recurring task logic — set next_due_date using timedelta
        if self.frequency == "daily":
            self.next_due_date = completed_on + timedelta(days=1)
        elif self.frequency == "weekly":
            self.next_due_date = completed_on + timedelta(weeks=1)
        # as_needed: no automatic next occurrence

    def reset(self) -> None:
        """Clear completion status so the task appears in tomorrow's plan."""
        self.completed = False

    def is_due(self, on_date: Optional[date] = None) -> bool:
        """Return True if this task should appear in the schedule for the given date."""
        check_date = on_date or date.today()

        # If a next_due_date was set by mark_complete, use it as the authority
        if self.next_due_date is not None:
            return check_date >= self.next_due_date

        # Fallback: original frequency-based logic
        if self.completed and self.last_completed_date == check_date:
            return False
        if self.frequency == "daily":
            return True
        if self.frequency == "weekly":
            if self.last_completed_date is None:
                return True
            return (check_date - self.last_completed_date).days >= 7
        return True  # as_needed

    def priority_rank(self) -> int:
        """Return a numeric rank (3=high, 2=medium, 1=low) used for sorting."""
        return {"high": 3, "medium": 2, "low": 1}[self.priority]

    def end_time(self) -> Optional[str]:
        """Return the HH:MM end time calculated from start_time + duration, or None."""
        if self.start_time is None:
            return None
        h, m = map(int, self.start_time.split(":"))
        total = h * 60 + m + self.duration_minutes
        return f"{total // 60:02d}:{total % 60:02d}"


# ---------------------------------------------------------------------------
# Pet  (dataclass)
# ---------------------------------------------------------------------------

@dataclass
class Pet:
    """Stores pet identity and owns the list of care tasks assigned to it."""

    name: str
    species: str
    age_years: float = 0.0
    _tasks: list = field(default_factory=list, init=False, repr=False)

    def __post_init__(self):
        """Normalise species to lowercase after dataclass init."""
        self.species = self.species.lower()

    def add_task(self, task: Task) -> None:
        """Attach a Task to this pet's task list."""
        self._tasks.append(task)

    def remove_task(self, description: str) -> bool:
        """Remove the first task matching the description; return True if found."""
        for i, t in enumerate(self._tasks):
            if t.description.lower() == description.lower():
                self._tasks.pop(i)
                return True
        return False

    def get_tasks(self) -> list:
        """Return a copy of this pet's full task list."""
        return list(self._tasks)

    def get_due_tasks(self, on_date: Optional[date] = None) -> list:
        """Return tasks that are due on the given date."""
        return [t for t in self._tasks if t.is_due(on_date)]

    def reset_daily_tasks(self) -> None:
        """Reset completion flags on all daily-frequency tasks."""
        for task in self._tasks:
            if task.frequency == "daily":
                task.reset()

    def total_task_time(self) -> int:
        """Return the sum of duration_minutes across all tasks."""
        return sum(t.duration_minutes for t in self._tasks)


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------

class Owner:
    """Manages one or more pets and exposes their collective task data to the Scheduler."""

    def __init__(self, name: str, available_minutes_per_day: int = 120):
        """Initialise owner with a name and a daily time budget in minutes."""
        if available_minutes_per_day <= 0:
            raise ValueError("available_minutes_per_day must be positive")
        self.name = name
        self.available_minutes_per_day = available_minutes_per_day
        self._pets: list[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Register a pet under this owner."""
        self._pets.append(pet)

    def remove_pet(self, name: str) -> bool:
        """Remove the first pet matching the name; return True if found."""
        for i, p in enumerate(self._pets):
            if p.name.lower() == name.lower():
                self._pets.pop(i)
                return True
        return False

    def get_pets(self) -> list[Pet]:
        """Return a copy of this owner's pet list."""
        return list(self._pets)

    def get_all_tasks(self) -> list[tuple]:
        """Return every (Pet, Task) pair across all pets (used by Scheduler)."""
        return [(pet, task) for pet in self._pets for task in pet.get_tasks()]

    def get_all_due_tasks(self, on_date: Optional[date] = None) -> list[tuple]:
        """Return (Pet, Task) pairs for tasks due on the given date."""
        return [
            (pet, task)
            for pet in self._pets
            for task in pet.get_due_tasks(on_date)
        ]

    def total_due_minutes(self, on_date: Optional[date] = None) -> int:
        """Return total minutes needed for all due tasks today."""
        return sum(t.duration_minutes for _, t in self.get_all_due_tasks(on_date))

    def __repr__(self) -> str:
        """Return a concise string representation of this owner."""
        return (
            f"Owner(name={self.name!r}, pets={len(self._pets)}, "
            f"available={self.available_minutes_per_day}min/day)"
        )


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

class Scheduler:
    """Retrieves, sorts, and schedules tasks from an Owner's pets into a daily plan."""

    def __init__(self, owner: Owner):
        """Bind the scheduler to a specific owner."""
        self.owner = owner

    # ------------------------------------------------------------------
    # Core scheduling
    # ------------------------------------------------------------------

    def build_daily_plan(self, on_date: Optional[date] = None) -> list[dict]:
        """Sort due tasks by priority and greedily fit them into the owner's time budget."""
        check_date = on_date or date.today()
        due_pairs = self.owner.get_all_due_tasks(check_date)

        sorted_pairs = sorted(
            due_pairs,
            key=lambda pt: (-pt[1].priority_rank(), pt[1].duration_minutes),
        )

        plan: list[dict] = []
        elapsed = 0

        for pet, task in sorted_pairs:
            if elapsed + task.duration_minutes > self.owner.available_minutes_per_day:
                continue
            plan.append(
                {
                    "pet": pet,
                    "task": task,
                    "start_min": elapsed,
                    "end_min": elapsed + task.duration_minutes,
                    "reason": self._explain(pet, task, elapsed),
                }
            )
            elapsed += task.duration_minutes

        return plan

    # ------------------------------------------------------------------
    # Step 2: Sorting
    # ------------------------------------------------------------------

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """Sort Task objects by start_time (HH:MM string); tasks without a time go last.

        Uses a lambda key so Python's sorted() compares HH:MM strings
        lexicographically, which works correctly for 24-hour clock strings.
        Tasks with no start_time receive '99:99' so they sort to the end.
        """
        return sorted(tasks, key=lambda t: t.start_time or "99:99")

    # ------------------------------------------------------------------
    # Step 2: Filtering
    # ------------------------------------------------------------------

    def filter_tasks(
        self,
        pet_name: Optional[str] = None,
        completed: Optional[bool] = None,
    ) -> list[tuple]:
        """Filter (Pet, Task) pairs by pet name and/or completion status.

        Pass pet_name to restrict results to one pet.
        Pass completed=True/False to restrict by task status.
        Omit a parameter to skip that filter.
        """
        results = self.owner.get_all_tasks()

        if pet_name is not None:
            results = [(p, t) for p, t in results if p.name.lower() == pet_name.lower()]

        if completed is not None:
            results = [(p, t) for p, t in results if t.completed == completed]

        return results

    # ------------------------------------------------------------------
    # Step 4: Conflict detection (plan-level + start_time-level)
    # ------------------------------------------------------------------

    def detect_conflicts(self, plan: list[dict]) -> list[str]:
        """Scan a scheduled plan for time-slot overlaps and return warning messages."""
        conflicts: list[str] = []
        for i in range(len(plan)):
            for j in range(i + 1, len(plan)):
                a, b = plan[i], plan[j]
                if a["start_min"] < b["end_min"] and b["start_min"] < a["end_min"]:
                    conflicts.append(
                        f"WARNING — Overlap: '{a['task'].description}' "
                        f"({self._min_to_time(a['start_min'])}-{self._min_to_time(a['end_min'])}) "
                        f"conflicts with '{b['task'].description}' "
                        f"({self._min_to_time(b['start_min'])}-{self._min_to_time(b['end_min'])})"
                    )
        return conflicts

    def detect_time_conflicts(self, pairs: Optional[list[tuple]] = None) -> list[str]:
        """Check raw (Pet, Task) pairs for overlapping start_time windows.

        Compares tasks that have a start_time set. Returns a warning string
        for each overlap found — does NOT raise an exception, keeping the
        program running so the user can decide how to resolve it.
        """
        source = pairs if pairs is not None else self.owner.get_all_tasks()
        timed = [(p, t) for p, t in source if t.start_time is not None]
        conflicts: list[str] = []

        for i in range(len(timed)):
            for j in range(i + 1, len(timed)):
                p_a, t_a = timed[i]
                p_b, t_b = timed[j]

                # Convert HH:MM to minutes for comparison
                a_start = self._hhmm_to_min(t_a.start_time)
                a_end   = a_start + t_a.duration_minutes
                b_start = self._hhmm_to_min(t_b.start_time)
                b_end   = b_start + t_b.duration_minutes

                if a_start < b_end and b_start < a_end:
                    conflicts.append(
                        f"WARNING — Time conflict: '{t_a.description}' ({p_a.name}, "
                        f"{t_a.start_time}-{t_a.end_time()}) overlaps "
                        f"'{t_b.description}' ({p_b.name}, {t_b.start_time}-{t_b.end_time()})"
                    )

        return conflicts

    # ------------------------------------------------------------------
    # Unscheduled tasks
    # ------------------------------------------------------------------

    def get_unscheduled_tasks(self, plan: list[dict], on_date: Optional[date] = None) -> list[tuple]:
        """Return due (Pet, Task) pairs that were excluded from the plan due to time constraints."""
        check_date = on_date or date.today()
        scheduled_ids = {id(entry["task"]) for entry in plan}
        return [
            (pet, task)
            for pet, task in self.owner.get_all_due_tasks(check_date)
            if id(task) not in scheduled_ids
        ]

    # ------------------------------------------------------------------
    # Recurring task management
    # ------------------------------------------------------------------

    def advance_day(self) -> None:
        """Reset all daily tasks across every pet to prepare for the next day."""
        for pet in self.owner.get_pets():
            pet.reset_daily_tasks()

    # ------------------------------------------------------------------
    # Summary display
    # ------------------------------------------------------------------

    def summary(self, plan: list[dict]) -> str:
        """Render the plan as a formatted plain-text string for the CLI or Streamlit."""
        if not plan:
            return "No tasks scheduled."

        lines = [f"Daily plan for {self.owner.name}  ({date.today()})", ""]
        for entry in plan:
            start = self._min_to_time(entry["start_min"])
            end   = self._min_to_time(entry["end_min"])
            lines.append(
                f"  {start}-{end}  [{entry['task'].priority.upper()}]  "
                f"{entry['task'].description}  ({entry['pet'].name})"
            )
            lines.append(f"           -> {entry['reason']}")
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
        """Build a one-line scheduling rationale for a task entry."""
        freq_note = {"daily": "due daily", "weekly": "due this week", "as_needed": "requested"}[task.frequency]
        return f"Scheduled at {self._min_to_time(elapsed)} for {pet.name} -- {freq_note}, priority={task.priority}"

    @staticmethod
    def _min_to_time(minutes: int) -> str:
        """Convert a minute offset from 08:00 into a HH:MM time string."""
        total = 8 * 60 + minutes
        h, m = divmod(total, 60)
        return f"{h:02d}:{m:02d}"

    @staticmethod
    def _hhmm_to_min(hhmm: str) -> int:
        """Convert a HH:MM string into an absolute minute count from midnight."""
        h, m = map(int, hhmm.split(":"))
        return h * 60 + m

    def __repr__(self) -> str:
        """Return a concise string representation of this scheduler."""
        return f"Scheduler(owner={self.owner.name!r})"
