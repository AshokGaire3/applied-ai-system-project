# PawPal+ — Project Context (Single Source of Truth)

**Purpose:** Give any human or AI collaborator everything they need to understand PawPal+ in one read-through.
**Audience:** Project author, instructors, future contributors, AI coding agents (Claude / Cursor).
**Last updated:** 2026-04-28.
**Related docs:** [requirements.md](requirements.md) · [architecture.md](architecture.md) · [skills.md](skills.md) · [rag-spec.md](rag-spec.md) · [roadmap.md](roadmap.md).

---

## 1. Problem statement

A busy pet owner needs help staying consistent with daily care across one or more pets. They juggle walks, feeding, medication, grooming, enrichment, and vet routines, often with hard time constraints (work, school, sleep). Missing a high-priority task — a medication dose, a feeding window — has real consequences for the animal. Generic to-do apps do not understand priority, recurrence, or the time budget a real human has on a real day.

PawPal+ exists to **plan a realistic daily care schedule** within the owner's available time, **explain its choices**, **flag conflicts**, and **answer pet-care questions** with grounded citations.

## 2. Scenario

> Jordan owns a dog (Mochi) and a cat (Luna). Jordan has roughly two hours per day for pet care. Mochi needs two walks, a feeding, and a daily allergy pill. Luna needs feeding, litter scoop, and weekly grooming. Jordan opens PawPal+ in the morning, sees today's plan in priority order, sees that the 8:00 medication conflicts with the morning walk, adjusts one start time, regenerates the plan, and asks the AI Coach "should I feed before or after a walk?" — getting an answer with `[S1]` citations from the knowledge base.

This scenario drives every requirement in [requirements.md](requirements.md).

## 3. Origin (per the final-project rubric)

This is the final project for an Applied AI System / CodePath Applied AI Engineering course. The source rubric lives at [instruction.md](../../instruction.md). PawPal+ is the **extension of the Module 2 PawPal+ scheduler** project into a complete applied AI system.

The base project (Module 2) shipped:
- `Owner` / `Pet` / `Task` / `Scheduler` domain classes.
- A priority-first greedy scheduler with conflict detection.
- A Streamlit UI with five service tabs.

The final project adds:
- A **RAG AI Coach** (`RagAssistant` in [rag_engine.py](../../rag_engine.py)) — the required AI feature.
- A **modular UI package** ([ui/](../../ui/)) so pages, theme, navigation, and copy text are decoupled from the entry point.
- **Reliability features:** citation enforcement, deterministic fallback, vet disclaimer in the LLM system prompt, runtime logging to `logs/ai.log`, persistence error handling.
- A **RAG evaluation harness** ([tests/test_rag_eval.py](../../tests/test_rag_eval.py) + [tests/rag_eval_set.json](../../tests/rag_eval_set.json)) that measures retrieval@3, fallback determinism, and out-of-scope refusal rate.
- This **planning bundle** (`claude/doc/`).

## 4. Goals (in scope)

- Track owner, pets, and care tasks with validation.
- Compute a **priority-first, time-budgeted daily plan** (greedy scheduler).
- Detect time conflicts and surface them as warnings (never silently rewrite the schedule).
- Persist state to a local JSON file (`data.json`) and reload on startup.
- Provide an **AI Coach** that retrieves from a local knowledge base and answers with citations, with a deterministic fallback when no API key is set.
- Run entirely on a single laptop with `streamlit run app.py`.
- Pass the rubric in [instruction.md](../../instruction.md): functionality, design + architecture, documentation, reliability + evaluation, reflection + ethics, presentation + portfolio.

## 5. Non-goals (out of scope)

- Multi-user accounts, auth, or cloud sync.
- A vector database, embeddings model, or external retrieval service.
- A mobile native app.
- Integration with calendars (Google / Apple) or smart-home devices.
- Veterinary medical advice — the system explicitly defers to a vet on medical concerns.
- Real-time push notifications.

## 6. Target user

A non-technical pet owner with one to four pets, a single laptop, and roughly 60–240 minutes available per day for pet care.

## 7. Success criteria

The project is "done" when:

1. A user can complete the full scenario in section 2 without reading code.
2. The full pytest suite passes locally without `OPENAI_API_KEY` set.
3. With `OPENAI_API_KEY` set, the AI Coach returns answers that contain valid `[Sn]` citations on every successful response.
4. Every code path that talks to the network has a documented fallback.
5. All 10 documents in this folder exist and are internally consistent.
6. The repository submission checklist in [instruction.md](../../instruction.md) is satisfied — see [roadmap.md](roadmap.md) section 1 for the trace.

## 8. Glossary

| Term | Meaning |
|------|---------|
| **Owner** | The human user. Has a name and an `available_minutes_per_day` budget. Owns one or more Pets. Implemented in [pawpal_system.py](../../pawpal_system.py). |
| **Pet** | A single animal (dog, cat, rabbit, …). Owns a private list of Tasks. |
| **Task** | A single care activity with `description`, `duration_minutes`, `priority` (low/medium/high), `frequency` (daily/weekly/as_needed), optional `start_time` (HH:MM). |
| **Scheduler** | The planning brain. Reads tasks from an Owner and produces a daily plan + conflict warnings. |
| **Daily plan** | An ordered list of `(pet, task, start_min, end_min, reason)` entries that fit within the owner's time budget. |
| **AI Coach** | The Streamlit "AI Coach" service tab. A multi-turn chat that retrieves from the knowledge base and answers questions. |
| **RagAssistant** | Class in [rag_engine.py](../../rag_engine.py) that powers the AI Coach. |
| **Knowledge base** | Local JSON file [knowledge_base.json](../../knowledge_base.json) containing pet-care notes (id, title, tags, content). |
| **Citation** | A reference like `[S1]` in an AI Coach answer that points to one of the retrieved sources. |
| **Fallback mode** | Deterministic local response used by `RagAssistant` when no `OPENAI_API_KEY` is set or the API call fails. |
| **Service tab** | One of the five top-level Streamlit pages: Profile, Pets, Tasks, Schedule, AI Coach. |
| **Eval set** | The hand-authored question / expected-source pairs in [tests/rag_eval_set.json](../../tests/rag_eval_set.json) used by the RAG eval tests. |
| **Model card** | The reflective document required by [instruction.md](../../instruction.md) submission checklist. To be added at the repo root as `model_card.md`. |

## 9. Repo map

```
applied-ai-system-final/
├── app.py                    # Streamlit entry point: session state + nav + sidebar (93 lines)
├── pawpal_system.py          # Domain model: Task, Pet, Owner, Scheduler
├── rag_engine.py             # RagAssistant + retrieval index + OpenAI/fallback
├── models.py                 # (legacy) earlier model layer kept for tests
├── main.py                   # CLI demo of all algorithmic features
├── cli_demo.py               # Extended scenario CLI walkthrough
├── ui/
│   ├── __init__.py           # package marker
│   ├── theme.py              # apply_theme(), render_hero() — CSS + hero card
│   ├── helpers.py            # emoji maps, get_app_metrics, format_plan_context
│   ├── navigation.py         # render_navbar, query-param sync
│   ├── pages.py              # render_*_page functions for the five tabs
│   └── content.py            # static copy: RAG_SUPPORTED_QUESTIONS, ROADMAP_STATUS, ...
├── knowledge_base.json       # Local KB used by the AI Coach
├── data.json                 # Persisted Owner/Pets/Tasks (auto-saved)
├── logs/ai.log               # RAG runtime log (gitignored)
├── requirements.txt          # streamlit, pytest
├── tests/
│   ├── test_pawpal.py        # Domain tests (22 cases)
│   ├── test_models.py        # Legacy model tests (28 cases)
│   ├── test_rag_engine.py    # RAG unit tests (3 cases)
│   ├── test_rag_eval.py      # RAG evaluation harness (3 cases)
│   ├── test_navigation.py    # UI nav tests (3 cases)
│   ├── test_ui_helpers.py    # UI helper tests (2 cases)
│   └── rag_eval_set.json     # Eval set: questions + expected_kb_ids + must_contain_any
├── assets/                   # System architecture PNG + demo screenshots (to refresh)
├── reflection.md             # Module-2 design / AI-collaboration reflection
├── uml_diagram.md            # Mermaid UML source
├── README.md                 # Public README (final-project version pending)
├── instruction.md            # Course rubric + submission checklist (source of truth)
└── claude/doc/               # ← THIS FOLDER (planning + spec docs)
```

## 10. Tech stack

- **Language:** Python 3.10+
- **UI:** Streamlit (`streamlit>=1.30` from [requirements.txt](../../requirements.txt))
- **Domain model:** `dataclass`-based Python classes; no ORM
- **Persistence:** Plain JSON files via `json.dump` / `json.load`
- **RAG retrieval:** TF-IDF index built in pure Python (no third-party retrieval lib)
- **LLM:** OpenAI Chat Completions (`gpt-4o-mini` by default), called via `urllib.request` — no `openai` SDK dependency
- **Tests:** pytest (`pytest>=7.0`)

## 11. AI-collaborator rules

These rules apply to any AI agent (Claude, Cursor, Copilot) editing this repo:

1. **Respect encapsulation.** Never read or write a private attribute from outside its class. Use `Pet.get_tasks()` not `pet._tasks`. The `to_dict` / `from_dict` symmetric pattern was chosen specifically for this — see [reflection.md](../../reflection.md) section 6.
2. **Symmetric serialization.** If you add a field to `Task`, `Pet`, or `Owner`, you must update **both** `to_dict` and `from_dict` in the same edit.
3. **Domain layer is UI-free.** [pawpal_system.py](../../pawpal_system.py) must not import `streamlit` or anything from [ui/](../../ui/). The Streamlit layer adapts to the domain, not the other way around.
4. **RAG layer is domain-free and UI-free.** [rag_engine.py](../../rag_engine.py) must not import `pawpal_system` or `ui`. The UI is the only thing allowed to bridge the two — it formats schedule context as a string in [ui/helpers.py](../../ui/helpers.py) and passes it as `extra_context` to `RagAssistant.answer`.
5. **`app.py` stays thin.** New page logic goes into [ui/pages.py](../../ui/pages.py). New copy text goes into [ui/content.py](../../ui/content.py). New visual rules go into [ui/theme.py](../../ui/theme.py).
6. **Every external call needs a fallback.** OpenAI failures must degrade to the local fallback answer, not crash the UI.
7. **Citations are mandatory** when sources exist. If the LLM response does not contain a valid `[Sn]` citation, fall back to the deterministic template.
8. **No secrets in the repo.** `.env` is git-ignored; `.env.example` is the template.
9. **Logs go to `logs/ai.log`.** Never print AI decisions to stdout in production paths.
10. **Tests must pass without an API key.** All RAG tests must work in fallback mode. The OOS-refusal eval explicitly exercises that path.
11. **Do not add new top-level dependencies** without updating [requirements.txt](../../requirements.txt) and [risks-guardrails.md](risks-guardrails.md).

## 12. Where to look next

- For **what to build / acceptance criteria** → [requirements.md](requirements.md).
- For **how the system fits together** → [architecture.md](architecture.md).
- For **per-feature contracts** → [skills.md](skills.md).
- For **how the AI Coach works** → [rag-spec.md](rag-spec.md).
- For **what is done and what remains** → [roadmap.md](roadmap.md).
- For **how to grade the project against the rubric** → [roadmap.md](roadmap.md) section 1 + [evaluation.md](evaluation.md).
