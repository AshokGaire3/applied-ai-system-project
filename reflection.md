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

I looked at three things: how much time the owner has (`available_minutes_per_day`), how important each task is (priority), and whether the task is actually due today. If something already got done yesterday and doesn't need to happen again until tomorrow, there's no reason to put it in today's plan.

Those three felt like the most obvious things a real person would care about. If I'm taking care of a pet I'm just thinking "do I have enough time and is this actually important today" — nothing more complicated than that.

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

Honestly I used it a lot throughout the project. At the beginning I used the chat to think through my class structure — I wasn't sure if the Scheduler should be its own class or just a method inside Owner. Talking it through helped me realize that putting scheduling logic inside Owner would make it way too bloated.

The most useful moment was probably when I was stuck on the recurring task bug. `is_due()` wasn't giving the right answer after `mark_complete()`, and I just couldn't see why. I pasted the function into chat and asked it to trace through with a specific date. It found the problem pretty quickly — the `check_date == last_completed_date` check was running before the `next_due_date` check, which broke the weekly case.

For tests I'd describe what I wanted to check and ask for a starting template, then fill in the actual values myself. I found narrow specific questions worked way better than vague ones. "Write a test that checks a daily task is not due the same day it was completed" got me something useful. "Improve my scheduler" just gave me random suggestions I didn't really need.

For Copilot specifically, inline completions were most useful when I was writing similar code twice — like `_hhmm_to_min` and `_min_to_time` are basically mirror functions, and Copilot predicted the second one almost completely after I wrote the first. The chat sidebar was better for design questions where I needed to go back and forth a bit.

Having a separate session per phase helped more than I expected. When everything is in one long chat it gets messy and the AI starts referencing earlier stuff that isn't relevant anymore. Keeping Phase 1 just about design and Phase 3 just about the algorithms made it way easier to follow when I went back to look at it.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

When I asked about conflict resolution, the AI suggested automatically shifting a conflicting task's start time forward until the overlap cleared. I didn't go with that.

My thinking was that the Scheduler's job is to tell the owner what's going on, not quietly rewrite their schedule. If a feeding needs to happen at a specific time — like medication for a pet — moving it silently could actually cause a problem. The owner knows things the algorithm doesn't. I kept the warning-only approach instead and checked that `test_detect_time_conflicts_with_overlap` still passed with that version.

**Summarizing what I learned about being the "lead architect" when collaborating with AI tools:**

The AI doesn't know what constraints you're working under. It'll suggest a backtracking scheduler or a database-backed system without knowing you just need something simple that a pet owner can follow. I had to keep making judgment calls about what actually fit the project versus what was technically interesting but overkill. The AI made building things faster — the deciding what to build part was still completely on me.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

I tested the main things I was worried about getting wrong. The recurring task logic was one — I wanted to make sure a daily task completed today doesn't show up again until tomorrow, and a weekly task waits the full seven days. That stuff is easy to mess up with off-by-one errors.

I also tested sorting and filtering since those are the features I added in Phase 3. And I tested that the greedy scheduler actually respects the time budget — like if you only have 60 minutes, tasks that would push you over don't get included.

For edge cases I checked things like an empty task list, a task that exactly hits the budget limit, and what happens when a low priority task gets bumped because a high priority one filled the remaining time. Input validation too — bad priority strings and wrong time formats should raise an error right away.

These mattered because if the scheduler quietly drops something or puts it in the wrong order, the person following the plan has no idea. For something like pet medication that's actually a real problem.

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

I feel pretty good about the core logic — there are 46+ tests and they cover most of the important paths. The one thing I'd add next is a test for when two tasks belong to different pets but overlap in time. Right now `detect_time_conflicts()` flags that as a conflict even if two different people could handle each pet at the same time. It'd be better if the owner could mark certain tasks as "can run in parallel" and the system would skip flagging those.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

Honestly the part I like most is how Owner and Scheduler ended up totally separate. Owner just holds pets and tasks and hands data over. Scheduler does all the planning logic. Neither one knows what the other is doing internally. That made testing a lot easier because I could test them independently and I never ran into weird circular dependency issues.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

I'd add a `pet_name` field directly to `Task`. Right now if you have a standalone Task object you have no idea which pet it belongs to, and the only reason it works is because we always pass `(Pet, Task)` tuples everywhere. That's kind of a workaround and I'd rather just fix the data model.

I'd also look at the conflict detection — doing a pairwise comparison on every task pair is fine for small lists but it's not the cleanest approach. Something interval-based would be better if this ever got bigger.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

I think the main thing I learned is that AI saves you time on writing code but not on figuring out what the code should actually do. The decisions like "should this auto-fix or just warn", "should this be greedy or optimal", "does Task need a reference to Pet" — those still took real thought. If anything, being able to implement things fast made those decisions more important because you can go pretty far in the wrong direction very quickly before you notice.
