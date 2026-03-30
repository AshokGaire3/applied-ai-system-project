"""
PawPal+ Core Models

Represents the domain entities: Owner, Pet, Task, and scheduling logic.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum


class Priority(Enum):
    """Task priority levels."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3


class Recurrence(Enum):
    """Task recurrence patterns."""
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"


@dataclass
class Owner:
    """Represents a pet owner."""
    name: str
    available_hours_per_day: float = 8.0
    preferences: dict = field(default_factory=dict)
    
    def __str__(self) -> str:
        return f"Owner: {self.name} ({self.available_hours_per_day}h available/day)"


@dataclass
class Pet:
    """Represents a pet."""
    name: str
    species: str  # dog, cat, other
    age: int = 1
    special_needs: List[str] = field(default_factory=list)
    
    def __str__(self) -> str:
        needs_str = f" (Special needs: {', '.join(self.special_needs)})" if self.special_needs else ""
        return f"Pet: {self.name} ({self.species}, age {self.age}){needs_str}"


@dataclass
class Task:
    """Represents a pet care task."""
    name: str
    duration_minutes: int
    priority: Priority
    task_type: str  # walk, feed, meds, enrichment, grooming, etc.
    recurrence: Recurrence = Recurrence.ONCE
    earliest_time: Optional[str] = None  # HH:MM format, e.g., "08:00"
    latest_time: Optional[str] = None    # HH:MM format, e.g., "20:00"
    notes: Optional[str] = None
    
    def __str__(self) -> str:
        duration_str = f"{self.duration_minutes}min"
        time_constraint = ""
        if self.earliest_time or self.latest_time:
            time_constraint = f" (between {self.earliest_time or 'any'} and {self.latest_time or 'any'})"
        return f"{self.name} [{self.priority.name}] - {duration_str}{time_constraint}"
    
    def duration_hours(self) -> float:
        """Return duration in hours."""
        return self.duration_minutes / 60


@dataclass
class ScheduledTask:
    """Represents a task assigned to a specific time slot in the schedule."""
    task: Task
    start_time: str  # HH:MM format
    end_time: str    # HH:MM format
    
    def __str__(self) -> str:
        return f"{self.start_time}-{self.end_time}: {self.task.name}"


class DailySchedule:
    """Represents a complete daily schedule for a pet."""
    
    def __init__(self, owner: Owner, pet: Pet, available_hours: float):
        self.owner = owner
        self.pet = pet
        self.available_hours = available_hours
        self.scheduled_tasks: List[ScheduledTask] = []
        self.unscheduled_tasks: List[Task] = []
        self.conflicts: List[str] = []
    
    def total_scheduled_time(self) -> float:
        """Return total time scheduled in hours."""
        return sum(task.task.duration_hours() for task in self.scheduled_tasks)
    
    def remaining_time(self) -> float:
        """Return remaining available time in hours."""
        return self.available_hours - self.total_scheduled_time()
    
    def add_scheduled_task(self, task: ScheduledTask) -> bool:
        """Add a task to the schedule. Returns True if successful."""
        if self.remaining_time() >= task.task.duration_hours():
            self.scheduled_tasks.append(task)
            return True
        return False
    
    def mark_unschedulable(self, task: Task, reason: str) -> None:
        """Mark a task as unable to be scheduled."""
        self.unscheduled_tasks.append(task)
        self.conflicts.append(f"Could not schedule '{task.name}': {reason}")
    
    def __str__(self) -> str:
        result = f"\n=== Daily Schedule for {self.pet.name} (owned by {self.owner.name}) ===\n"
        result += f"Available time: {self.available_hours}h | Used: {self.total_scheduled_time():.1f}h | Remaining: {self.remaining_time():.1f}h\n"
        result += "\nScheduled Tasks:\n"
        if not self.scheduled_tasks:
            result += "  (none)\n"
        else:
            for task in self.scheduled_tasks:
                result += f"  {task}\n"
        
        if self.unscheduled_tasks:
            result += f"\nCould not schedule ({len(self.unscheduled_tasks)} tasks):\n"
            for task in self.unscheduled_tasks:
                result += f"  - {task.name}\n"
        
        if self.conflicts:
            result += "\nConflicts/Notes:\n"
            for conflict in self.conflicts:
                result += f"  - {conflict}\n"
        
        return result


class Scheduler:
    """
    Main scheduler that generates a daily plan for pet care tasks.
    
    Algorithm:
    1. Sort tasks by priority (HIGH > MEDIUM > LOW)
    2. Try to fit high-priority tasks first
    3. Check time constraints (earliest_time, latest_time)
    4. Detect conflicts (overlapping time slots, insufficient time)
    5. Generate schedule and explanation
    """
    
    def __init__(self, owner: Owner, pet: Pet):
        self.owner = owner
        self.pet = pet
    
    def schedule_day(self, tasks: List[Task], available_hours: Optional[float] = None) -> DailySchedule:
        """
        Generate a daily schedule for the given tasks.
        
        Args:
            tasks: List of tasks to schedule
            available_hours: Override owner's available hours (default: use owner setting)
        
        Returns:
            DailySchedule object with scheduled tasks and conflicts
        """
        if available_hours is None:
            available_hours = self.owner.available_hours_per_day
        
        schedule = DailySchedule(self.owner, self.pet, available_hours)
        
        # Sort tasks by priority (HIGH > MEDIUM > LOW), then by duration (longer first)
        sorted_tasks = sorted(
            tasks,
            key=lambda t: (-t.priority.value, -t.duration_minutes)
        )
        
        # Try to fit each task
        current_time_minutes = 8 * 60  # Start at 8:00 AM
        end_of_day_minutes = 8 * 60 + int(available_hours * 60)  # End time
        
        for task in sorted_tasks:
            scheduled = self._try_schedule_task(
                task, current_time_minutes, end_of_day_minutes, schedule
            )
            if scheduled:
                current_time_minutes += task.duration_minutes
            else:
                schedule.mark_unschedulable(task, f"Insufficient time or time constraint conflict")
        
        return schedule
    
    def _try_schedule_task(
        self,
        task: Task,
        current_time_minutes: int,
        end_of_day_minutes: int,
        schedule: DailySchedule
    ) -> bool:
        """
        Attempt to schedule a single task.
        
        Returns True if successfully scheduled, False otherwise.
        """
        # Check if task fits before end of day
        if current_time_minutes + task.duration_minutes > end_of_day_minutes:
            return False
        
        # Check time constraints
        start_time_str = self._minutes_to_time(current_time_minutes)
        end_time_str = self._minutes_to_time(current_time_minutes + task.duration_minutes)
        
        if task.earliest_time and start_time_str < task.earliest_time:
            return False
        if task.latest_time and end_time_str > task.latest_time:
            return False
        
        # Create and add scheduled task
        scheduled_task = ScheduledTask(task, start_time_str, end_time_str)
        schedule.add_scheduled_task(scheduled_task)
        
        return True
    
    @staticmethod
    def _minutes_to_time(minutes: int) -> str:
        """Convert minutes since midnight to HH:MM format."""
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours:02d}:{mins:02d}"
    
    @staticmethod
    def _time_to_minutes(time_str: str) -> int:
        """Convert HH:MM format to minutes since midnight."""
        hours, mins = map(int, time_str.split(":"))
        return hours * 60 + mins


class PawPalSystem:
    """Main system coordinator."""
    
    def __init__(self):
        self.owners: dict[str, Owner] = {}
        self.pets: dict[str, Pet] = {}
        self.tasks: dict[str, List[Task]] = {}  # tasks per pet
    
    def register_owner(self, owner: Owner) -> None:
        """Register an owner."""
        self.owners[owner.name] = owner
    
    def register_pet(self, pet: Pet, owner_name: str) -> None:
        """Register a pet with an owner."""
        self.pets[pet.name] = pet
        if pet.name not in self.tasks:
            self.tasks[pet.name] = []
    
    def add_task(self, pet_name: str, task: Task) -> None:
        """Add a task for a pet."""
        if pet_name not in self.tasks:
            self.tasks[pet_name] = []
        self.tasks[pet_name].append(task)
    
    def generate_schedule(self, owner_name: str, pet_name: str) -> Optional[DailySchedule]:
        """Generate a daily schedule for a pet."""
        if owner_name not in self.owners or pet_name not in self.pets:
            return None
        
        owner = self.owners[owner_name]
        pet = self.pets[pet_name]
        tasks = self.tasks.get(pet_name, [])
        
        scheduler = Scheduler(owner, pet)
        return scheduler.schedule_day(tasks)
