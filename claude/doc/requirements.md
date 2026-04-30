# PawPal+ — Requirements

**Purpose:** Define what PawPal+ must do, grouped by service tab, plus non-functional requirements that span the whole app, plus the rubric requirements from [instruction.md](../../instruction.md).
**Audience:** Anyone validating that the app meets the project bar.
**Last updated:** 2026-04-28.
**Related docs:** [claude.md](claude.md) · [skills.md](skills.md) · [evaluation.md](evaluation.md) · [risks-guardrails.md](risks-guardrails.md) · [roadmap.md](roadmap.md).

---

## 0. ID conventions

- `FR-<TAB>-<n>` — functional requirement.
- `NFR-<n>` — non-functional requirement.
- `RUB-<n>` — rubric requirement traced from [instruction.md](../../instruction.md).
- `AC` — acceptance criteria for the requirement directly above.

---

## 1. Functional requirements — `Profile` tab

Implemented in [ui/pages.py](../../ui/pages.py) `render_profile_page`.

### FR-PROFILE-1 — Set or update owner identity

The owner can set their name and daily time budget.

**AC:**
- Default placeholder name is `Jordan`.
- `available_minutes_per_day` accepts integers in `[10, 480]` with step 10.
- Saving creates an `Owner` if none exists, or mutates the live one in place.
- A success toast confirms `Owner set: ...`.

### FR-PROFILE-2 — Persist owner profile to disk

Clicking **Save to data.json** writes the full owner / pets / tasks tree to `data.json`.

**AC:**
- File is created if missing, overwritten if present.
- File is JSON, indented 2 spaces.
- Round-trip invariant holds: `Owner.from_dict(saved) == owner`.
- I/O failure is caught by `_save_owner_data` and rendered as a friendly `st.error` — the UI does not crash.

### FR-PROFILE-3 — Auto-load on startup

If `data.json` exists at app start, the owner is hydrated into `st.session_state` and a green welcome banner appears.

**AC:**
- The banner is shown once, then suppressed.
- Pet count is correct.
- Missing file is silent (not an error).

### FR-PROFILE-4 — Display roadmap status

A status table is rendered at the top of the Profile tab using `ROADMAP_STATUS` from [ui/content.py](../../ui/content.py).

**AC:**
- Each row shows `Area` and `Status`.
- The sidebar's "Build progress" bar reflects the same values.

---

## 2. Functional requirements — `Pets` tab

Implemented in [ui/pages.py](../../ui/pages.py) `render_pets_page`.

### FR-PETS-1 — Register a pet

Adding a pet captures `name`, `species`, `age_years`.

**AC:**
- Species enum: `dog`, `cat`, `rabbit`, `other`.
- Age in `[0.0, 30.0]` with step 0.5.
- Duplicate names within the owner are rejected with a warning toast.
- On success: pet is added, `data.json` auto-saves through `_save_owner_data`, a success toast names the species emoji.

### FR-PETS-2 — Display all registered pets

The Pets tab lists every pet with species emoji, age, and task count.

**AC:**
- Each row uses the species emoji map from [ui/helpers.py](../../ui/helpers.py) — falls back to `🐾` for unknown species.
- Empty state says "No pets yet. Add one above."

---

## 3. Functional requirements — `Tasks` tab

Implemented in [ui/pages.py](../../ui/pages.py) `render_tasks_page`.

### FR-TASKS-1 — Create a task for a specific pet

Owner selects a pet, fills the task form, and adds it.

**AC:**
- Form fields: `description`, `duration_minutes` `[1,240]`, `priority` `{low,medium,high}`, `frequency` `{daily,weekly,as_needed}`, optional `start_time` `HH:MM`.
- Empty `start_time` becomes `None`.
- Validation errors from `Task.__post_init__` are surfaced as `st.error`.
- On success the task is appended to the pet, `data.json` auto-saves, a success toast names the task emoji.

### FR-TASKS-2 — Display all tasks sorted by start time

A single dataframe shows every `(pet, task)` pair across all pets, sorted by `start_time` ascending; tasks without a time go last.

**AC:**
- Sort uses `task.start_time or "99:99"` as the key.
- Each row shows: Pet (with species emoji), Task (with task emoji), Start Time or `-`, Duration, Priority (with color emoji), Frequency, Status.
- Priority emoji map: 🔴 High / 🟡 Medium / 🟢 Low.

### FR-TASKS-3 — Early conflict warnings

If two timed tasks overlap, a warning is shown in the Tasks tab even before generating the schedule.

**AC:**
- `Scheduler.detect_time_conflicts()` is called on the full task list.
- Each conflict line names both tasks, both pets, and both time windows.
- The system **never** auto-resolves the conflict.

---

## 4. Functional requirements — `Schedule` tab

Implemented in [ui/pages.py](../../ui/pages.py) `render_schedule_page`.

### FR-SCHEDULE-1 — Generate a daily plan

Clicking **Generate Schedule** produces a priority-first, time-budgeted plan.

**AC:**
- Sort key: `(-priority_rank, duration_minutes)`.
- Greedy fit: a task is added only if `elapsed + duration ≤ available_minutes_per_day`.
- Output is a list of dicts: `pet`, `task`, `start_min`, `end_min`, `reason`.
- Reasons name the time, the pet, the frequency, and the priority.

### FR-SCHEDULE-2 — Show schedule with conflicts and unscheduled tasks

The Schedule tab renders three sections after generation: the plan, the conflicts, and the skipped tasks.

**AC:**
- Plan dataframe columns: Time Window, Pet, Task, Duration, Priority, Frequency.
- Total scheduled minutes are reported against the budget.
- Conflicts include both `detect_conflicts(plan)` (plan-level) and `detect_time_conflicts()` (start-time-level).
- Skipped tasks listed via `Scheduler.get_unscheduled_tasks(plan)`.
- The empty plan case shows a warning and an early `return`, not a crash.

### FR-SCHEDULE-3 — Time conversion contract

All `start_min` / `end_min` values are minute offsets from a fixed `08:00` start (`Scheduler._min_to_time`).

**AC:**
- `_min_to_time(0)` → `"08:00"`.
- `_min_to_time(90)` → `"09:30"`.
- The chosen base time is documented and consistent.

---

## 5. Functional requirements — `AI Coach` tab

Implemented in [ui/pages.py](../../ui/pages.py) `render_ai_coach_page`. Backed by [rag_engine.py](../../rag_engine.py).

### FR-COACH-1 — Ask a pet-care question

User submits a free-text question via `st.chat_input` or via one of three starter buttons: **Walk + meal timing**, **Hydration routine**, **Plan-aware advice**.

**AC:**
- `RagAssistant.answer(question, extra_context, chat_history)` is called.
- `top_k = 3` (set in `RagAssistant.__init__`).
- Empty input triggers no LLM call.
- The response is appended to `st.session_state.ai_chat_history` and rendered in `st.chat_message` with the sources expander beneath it.

### FR-COACH-2 — Optionally include the day's schedule as context

A checkbox lets the user inject the current `latest_plan` as `extra_context` (default: checked).

**AC:**
- When checked, `format_plan_context(latest_plan)` is appended to the query.
- When unchecked, the query is sent unmodified.
- An empty plan is summarized as `"No scheduled tasks yet."`.

### FR-COACH-3 — Multi-turn chat history

The most recent 20 messages are kept in `st.session_state.ai_chat_history` and passed to the assistant.

**AC:**
- History is appended after every successful answer.
- It is truncated to the last 20 entries.
- Each rendered turn uses `st.chat_message("user" / "assistant")` for native Streamlit chat UI.
- A "Clear chat" button empties it.

### FR-COACH-4 — Citation enforcement

Every successful AI answer includes at least one valid `[Sn]` token where `1 ≤ n ≤ source_count`.

**AC:**
- `validate_citations` returns True before the OpenAI response is shown.
- If validation fails, the deterministic fallback is used and `mode == "fallback"`.

### FR-COACH-5 — Fallback when no API key

When `OPENAI_API_KEY` is not set, the deterministic template `_fallback_answer` is used.

**AC:**
- The UI shows an info banner: `OPENAI_API_KEY is not set. Using local fallback response.`.
- Sources are still listed.
- No network call is attempted.

### FR-COACH-6 — Friendly error if KB is missing or AI Coach crashes

`FileNotFoundError` for the knowledge base and any other `Exception` are caught.

**AC:**
- Missing KB → red error: `` `knowledge_base.json` is missing. Add it to enable AI Coach. ``
- Generic exception → red error: `AI Coach hit an unexpected error. Check `logs/ai.log` and try again.`
- The function `return`s after either, leaving the chat history clean.

### FR-COACH-7 — Scope and guardrails are visible to the user

The AI Coach tab includes an expander titled **Question scope and guardrails** that lists supported question types, unsupported types, and active guardrails (sourced from `RAG_SUPPORTED_QUESTIONS`, `RAG_NOT_SUPPORTED`, `RAG_GUARDRAILS` in [ui/content.py](../../ui/content.py)).

**AC:**
- All three lists render as bullet lists inside the expander.
- The text is identical to the constants in [ui/content.py](../../ui/content.py).

---

## 6. Functional requirements — Sidebar / Control Panel

Implemented in [app.py](../../app.py).

### FR-SIDEBAR-1 — Live KPIs

The sidebar shows: pets count, tasks count, due-today count, due minutes, conflict count.

**AC:**
- Values come from `get_app_metrics(owner)` in [ui/helpers.py](../../ui/helpers.py).
- Conflict count > 0 renders a warning; 0 renders a success message.
- The currently active service tab is shown.

### FR-SIDEBAR-2 — Build progress

A progress bar reports the fraction of `ROADMAP_STATUS` rows marked `Done`.

**AC:**
- Bar value = `done_count / total_count`.
- Caption shows `<done>/<total> roadmap areas completed`.

---

## 7. Functional requirements — Navigation

Implemented in [ui/navigation.py](../../ui/navigation.py).

### FR-NAV-1 — Five-tab horizontal nav with icons

The five service tabs are rendered as a single `st.radio` with horizontal layout and emoji icons.

**AC:**
- Tabs in order: `Profile` 👤, `Pets` 🐾, `Tasks` ✅, `Schedule` 🗓️, `AI Coach` 🤖.
- Selection persists across reruns via `st.session_state.active_service`.

### FR-NAV-2 — Deep-linkable URL

The active service is reflected in the URL as `?page=<slug>`.

**AC:**
- Slug map: `Profile` → `profile`, `Pets` → `pets`, `Tasks` → `tasks`, `Schedule` → `schedule`, `AI Coach` → `ai-coach`.
- Loading the app with `?page=tasks` opens the Tasks tab on first paint.
- Unknown slugs fall back to `Profile`.

---

## 8. Non-functional requirements

### NFR-1 — Reproducibility

A fresh checkout must run with:

```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

…and reach a usable home screen in under 10 seconds on a 2020-era laptop.

### NFR-2 — No hard dependency on the OpenAI SDK

The HTTP call uses only the Python standard library (`urllib.request`). The repo must continue to work even if the user never installs the `openai` package.

### NFR-3 — Tests pass without `OPENAI_API_KEY`

`pytest tests/` must pass on a machine with no API key set. Tests that exercise the LLM path mock `_call_openai` or assert against the fallback path. The OOS-refusal eval explicitly exercises the no-sources path.

### NFR-4 — Logs only, never prints

AI runtime decisions go to `logs/ai.log` via the `pawpal_ai` logger. No `print(...)` calls in `rag_engine.py` or domain code paths.

### NFR-5 — Secrets stay out of the repo

`.env` is git-ignored ([.gitignore](../../.gitignore)). The README documents the variable.

### NFR-6 — Graceful network failure

Any of `HTTPError`, `URLError`, `KeyError`, `ValueError` from the OpenAI call must be caught in `_call_openai` and converted to `None` so the caller can fall back.

### NFR-7 — Determinism in fallback mode

In fallback mode, the same `(question, knowledge_base.json)` pair must produce the same answer string every time. Asserted by `test_rag_eval_fallback_determinism_and_token_expectations`.

### NFR-8 — Encapsulation

External callers (UI, tests) use only public methods of `Pet` and `Owner`. Direct access to `_pets` or `_tasks` is forbidden — see rule 1 in [claude.md](claude.md) section 11.

### NFR-9 — UI accessibility

Color is never the only signal: priority is encoded as both color emoji and the word ("🔴 High"). Streamlit's native dataframes provide keyboard navigation and screen-reader access.

### NFR-10 — Documentation freshness

When a `to_dict` / `from_dict` field is added or a new service tab is added, this file and [claude.md](claude.md) section 9 (repo map) must be updated in the same change-set.

### NFR-11 — Persistence reliability

Persistence I/O failures (disk full, read-only filesystem, permission denied) must not crash the UI. They must surface as a friendly toast via `_save_owner_data`.

---

## 9. Rubric requirements (traced from [instruction.md](../../instruction.md))

The rubric in [instruction.md](../../instruction.md) is the source of truth for grading. Each item below maps a rubric line to the deliverable that satisfies it. The full submission checklist lives in [roadmap.md](roadmap.md) section 1.

### RUB-1 — Functionality (instruction §1)

The system must do something useful with AI and integrate **at least one** advanced feature: RAG, agentic workflow, fine-tuning, or reliability/testing.

**Deliverable:** RAG (`RagAssistant` in [rag_engine.py](../../rag_engine.py)) is integrated into the AI Coach tab and reshapes the response with cited sources. The reliability/testing path is also satisfied via [tests/test_rag_eval.py](../../tests/test_rag_eval.py). See [rag-spec.md](rag-spec.md) for the full spec.

### RUB-2 — Reproducibility, logging, guardrails (instruction §1)

**Deliverable:** Setup steps in [README.md](../../README.md), runtime logging to `logs/ai.log`, guardrails enumerated in [risks-guardrails.md](risks-guardrails.md).

### RUB-3 — Architecture diagram (instruction §2)

A short system diagram showing components, data flow, and human/test checkpoints.

**Deliverable:** Mermaid diagrams in [architecture.md](architecture.md) and [rag-spec.md](rag-spec.md). For submission, the architecture diagram will also be exported to `assets/architecture.png` (tracked in [roadmap.md](roadmap.md)).

### RUB-4 — Documentation (instruction §3)

The README must include: name of the original module project, title and summary, architecture overview, setup, sample interactions, design decisions, testing summary, reflection.

**Deliverable:** [README.md](../../README.md) is being expanded to satisfy each bullet. The deeper writing lives in [reflection.md](../../reflection.md) and the upcoming `model_card.md` per [instruction.md](../../instruction.md) submission checklist.

### RUB-5 — Reliability and evaluation (instruction §4)

At least one form of testing or evaluation. Summary line example: "X of Y tests passed; the AI struggled when context was missing."

**Deliverable:** 61 pytest cases (see [evaluation.md](evaluation.md) section 2). Specifically: retrieval@3 ≥ 0.90, fallback determinism = 1.00, OOS refusal rate ≥ 0.80 — all asserted by [tests/test_rag_eval.py](../../tests/test_rag_eval.py).

### RUB-6 — Reflection and ethics (instruction §5)

What are the limitations / biases? Could it be misused? What surprised you? AI collaboration story (one helpful + one flawed suggestion).

**Deliverable:** [reflection.md](../../reflection.md) (Module 2 reflection) plus a final-project addendum, plus the `model_card.md` to be added at repo root for submission.

### RUB-7 — Stretch features (instruction "Optional")

Up to +8 points across: RAG enhancement, agentic workflow, fine-tuning, test harness script.

**Deliverable considered:**
- **RAG enhancement (+2):** add tag-filter and metadata-aware retrieval, or extend the KB with an additional source. Tracked in [roadmap.md](roadmap.md) section 4.
- **Test harness or evaluation script (+2):** a `python -m tests.run_eval` style CLI that prints retrieval@3, refusal rate, and fallback determinism summary. Tracked in [roadmap.md](roadmap.md) section 4.

### RUB-8 — Presentation and portfolio (instruction §6 + submission checklist)

5–7 minute presentation, Loom video walkthrough showing 2–3 inputs end-to-end, GitHub link, portfolio reflection.

**Deliverable:** [demo-script.md](demo-script.md) is the script for the Loom recording. The Loom URL gets embedded in [README.md](../../README.md).

---

## 10. Acceptance scenarios (end-to-end)

The full project is "accepted" when these scenarios pass manually:

1. **First-run scenario.** Fresh checkout, no `data.json`, no API key. App launches, owner can be created, a pet added, two tasks added, schedule generated, AI Coach answers a question with `[S1]` citation in fallback mode. No tracebacks anywhere.
2. **Reload scenario.** Restart the app. Owner, pets, tasks, dates persist. Welcome banner shown once.
3. **Conflict scenario.** Two tasks with overlapping `start_time` produce a warning in the Tasks tab AND in the Schedule tab.
4. **Budget scenario.** Tasks totaling more than the budget produce a non-empty "Unscheduled" table.
5. **API scenario.** With `OPENAI_API_KEY` set, the AI Coach returns a `mode: "openai"` answer with valid citations.
6. **Deep-link scenario.** Visiting `http://localhost:8501/?page=tasks` opens the Tasks tab on first paint.
7. **Persistence-failure scenario.** Making `data.json` read-only and clicking save shows a friendly error toast — no traceback.
