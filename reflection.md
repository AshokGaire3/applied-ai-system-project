# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

When I first thought about PawPal+, I asked myself what the real "things" in this problem are. A pet owner has pets, pets have care tasks, and something needs to figure out what to do each day. That gave me four natural classes.

**Task** was the simplest starting point. Every care activity — a walk, a feeding, a vet visit — has a description, a duration, a priority (low / medium / high), and a frequency (daily, weekly, or as-needed). I also gave it a `completed` flag and a `last_completed_date` so the system can tell whether something still needs to happen today. The key methods are `mark_complete()`, `reset()`, `is_due()`, and `priority_rank()` — that last one converts the string priority into a number so the Scheduler can sort cleanly.

**Pet** is basically a container. It holds the pet's name, species, and age, and it owns a private list of Task objects. I gave it `add_task()` / `remove_task()` for managing that list, `get_due_tasks()` to filter by date, and `reset_daily_tasks()` to roll daily tasks back to pending at the start of a new day. The pet itself doesn't schedule anything — it just knows what it needs.

**Owner** sits one level above Pet. It holds the owner's name and — critically — their `available_minutes_per_day`, the time budget the Scheduler has to work within. The most important methods are `get_all_tasks()` and `get_all_due_tasks()`, which loop across every pet and flatten their tasks into a single `(Pet, Task)` list. This is the bridge the Scheduler calls so it never has to reach directly into a pet's internals.

**Scheduler** is the brain. It takes an Owner in its constructor and uses `owner.get_all_due_tasks()` to pull the full workload. `build_daily_plan()` sorts that list by priority (high first), then greedily packs tasks into the time budget. It also exposes `detect_conflicts()` for catching time-slot overlaps, `get_unscheduled_tasks()` for surfacing what didn't fit, and `summary()` to render the plan as readable text for the CLI or Streamlit UI.

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

Yes, a few things shifted once I started actually writing code.

The biggest change was converting `Task` and `Pet` to **Python dataclasses** (`@dataclass`). My original plan used plain `__init__` methods, but dataclasses cut out a lot of repetitive setup code while keeping validation clean inside `__post_init__`. It made both classes easier to read.

After reviewing the skeleton more carefully I also noticed two things worth flagging:

- **Missing relationship:** `Task` has no direct reference back to its `Pet`. If a task gets passed around as a standalone object you lose track of which pet it belongs to. The system works around this by always passing `(Pet, Task)` tuples — but storing a `pet_name` field on Task directly would be cleaner in a future iteration.
- **Logic bottleneck:** `detect_conflicts()` does an O(n²) pairwise comparison on the plan. Since the Scheduler assigns sequential non-overlapping slots by design, this method will almost never find a real conflict in normal operation — it's defensive code. Not broken, but worth knowing if the plan ever gets large.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

The main tradeoff I noticed is that `build_daily_plan()` is greedy — it just goes through tasks in priority order and adds them if they fit. It never looks back. So if a big high-priority task eats up a lot of time early, you might miss three smaller tasks that could have all fit instead.

I left it greedy on purpose though. For something like a daily pet care schedule, you don't need a perfect solution — you need something fast and easy to understand. If the highest priority task goes first, that makes sense to any pet owner without any explanation needed. I'd only rethink this if the task list got really long.

The conflict detection is also a soft tradeoff. When two tasks have overlapping start times, `detect_time_conflicts()` just prints a warning instead of crashing or auto-fixing it. That felt right to me — maybe two people are helping out, or the owner just wants to know and decide for themselves. Silently moving things around without telling anyone would feel worse.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
