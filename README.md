# PawPal+ (Applied AI Systems Final Project)

**PawPal+** is a Streamlit application that helps a pet owner plan daily care tasks for one or more pets. It combines a priority-based greedy scheduler, overlap warnings, recurrence logic, and an **AI Coach** that answers pet-care questions using **retrieval-augmented generation (RAG)** over a small local knowledge base with citation guardrails.

This repository is the **final-project** evolution of an earlier Module mini-project — see **[Base project (Module 2)](#base-project-applied-ai-module-2-mini-project)** below for what the prototype covered versus what shipped for the submission.

---

## Base project (Applied AI Module 2 mini-project)

The **Module 2 PawPal+ prototype** focused on building a coherent **domain model**: `Owner` (daily time budget), multiple `Pet` records, recurring `Task` objects with validated priorities and optional `HH:MM` slots, and a `Scheduler` that produced a **greedy, priority-first daily plan** plus **overlap warnings** rather than silently reshuffling user-confirmed times. The original goal was to prove **OO decomposition**, **deterministic scheduling semantics**, and **JSON persistence** (`data.json`), with Streamlit wiring that let an owner register pets/tasks and glance at workloads — before the fuller **RAG layer**, **evaluation harness**, and **modular `ui/`** package used in this final codebase.

---

## What changed for the final applied AI system

- **Integrated RAG (`rag_engine`)** — TF-IDF retrieval over `knowledge_base.json`, `[S1]`-style citations, optional OpenAI generation, deterministic fallback when no key or when citations fail validation, logging to `logs/ai.log`.
- **Modular UI** — Thin [`app.py`](app.py) plus [`ui/`](ui/) (theme, navigation, pages, helpers) for maintainable services: Profile, Pets, Tasks, Schedule, AI Coach.
- **Reliability testing** — `pytest` across [`tests/`](tests/), including [`tests/test_rag_eval.py`](tests/test_rag_eval.py) + [`tests/rag_eval_set.json`](tests/rag_eval_set.json) for retrieval and out-of-scope behavior.
- **Planning and architecture docs** — [`claude/doc/`](claude/doc/) (requirements, RAG spec, risks, demo script, etc.).
- **Ethics and model narrative** — [`model_card.md`](model_card.md) for reflection prompts required by the course.

Deeper design history and optional prompt-comparison write-up: [`reflection.md`](reflection.md).

---

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan
- Ask an **AI Coach** questions grounded in care notes, with sources

---

## Features

- **Service-oriented UI** — Top navigation for `Profile`, `Pets`, `Tasks`, `Schedule`, and `AI Coach` (see [`ui/navigation.py`](ui/navigation.py)).
- **Live metrics** — Sidebar insights: pets, tasks, due today, conflicts, plus optional roadmap progress ([`ui/content.py`](ui/content.py)).
- **Modular UI structure** — [`ui/theme.py`](ui/theme.py), [`ui/helpers.py`](ui/helpers.py), [`ui/pages.py`](ui/pages.py) so the entrypoint stays small.
- **Sort by time** — `Scheduler.sort_by_time()` orders tasks by optional `start_time` (`HH:MM`); missing times sort last.
- **Filter tasks** — `Scheduler.filter_tasks()` filters by pet name and/or completion (used in CLI/tests).
- **Daily / weekly recurrence** — `Task.mark_complete()` updates `next_due_date`; `is_due()` gates what appears today.
- **Conflict warnings** — `detect_time_conflicts()` flags overlapping timed windows; the app does not auto-edit times.
- **Greedy scheduling** — `build_daily_plan()` packs by priority within `available_minutes_per_day`; skipped tasks are listed explicitly.
- **Persistence** — `Owner.save_to_json` / `load_from_json` with symmetric `to_dict` / `from_dict` on nested types.
- **AI Coach (RAG)** — Retrieves top notes, enforces citations, falls back safely; see [`model_card.md`](model_card.md) and [`claude/doc/rag-spec.md`](claude/doc/rag-spec.md).

---

## AI requirement coverage (course alignment)

- **Useful AI in the main app** — AI Coach is a first-class service tab; schedule context can be included.
- **Advanced feature: RAG** — Retrieval changes the answer; sources are not decorative.
- **Guardrails and logging** — Citation validation, fallback path, `logs/ai.log`.
- **Reproducibility** — `requirements.txt`, optional `.env`, documented run commands below.

---

## Sample interactions (AI Coach)

These are **representative** patterns; exact wording may vary slightly with temperature or API version. **Fallback mode** (no `OPENAI_API_KEY`) still returns cited bullets from retrieved sources.

**1. Feeding routine**

- **Input:** `How important is a consistent feeding schedule for pets?`
- **Expected behavior:** Retrieves `kb_feeding` (and possibly nearby entries); answer cites sources as `[S1]`, `[S2]`, etc.; **mode** `openai` if key set and citations valid, else **fallback** with the same source titles listed under "Sources used".

**2. Walks and exercise**

- **Input:** `How often should I walk my dog?`
- **Expected behavior:** Retrieves `kb_walks`; answer ties guidance to retrieved text; includes vet-deferral line in **fallback** path.

**3. Out-of-scope / no KB match**

- **Input:** `What is the stock price of pet food companies tomorrow?`
- **Expected behavior:** Often **`no_sources`** or a refusal to answer from KB — see [`tests/rag_eval_set.json`](tests/rag_eval_set.json) out-of-scope cases and [`tests/test_rag_eval.py`](tests/test_rag_eval.py).

---

## Design decisions and trade-offs

- **Streamlit** — Fast UI for a portfolio demo; single-process, no separate API server.
- **Greedy scheduler** — Easy to explain and test; not globally optimal (see [`reflection.md`](reflection.md)).
- **TF-IDF retrieval** — No embedding dependency; sufficient for the small shipped KB; upgrade path documented in [`claude/doc/rag-spec.md`](claude/doc/rag-spec.md).
- **Citations required** — `validate_citations` rejects non-citing OpenAI replies so the user always sees traceable grounded text or deterministic fallback.
- **Warning-only conflicts** — Safer than auto-moving medication-like tasks ([`reflection.md`](reflection.md)).

---

## Testing summary

Run the full suite:

```bash
pytest tests/
```

- **[`tests/test_pawpal.py`](tests/test_pawpal.py)** — Scheduler, recurrence, conflicts, serialization paths.
- **[`tests/test_models.py`](tests/test_models.py)** — Legacy `models` layer coverage (kept from earlier scaffolding).
- **[`tests/test_rag_engine.py`](tests/test_rag_engine.py)** — Retrieval, `format_sources`, `validate_citations`.
- **[`tests/test_rag_eval.py`](tests/test_rag_eval.py)** — Retrieval@3 threshold, deterministic fallback, out-of-scope refusal rate using [`tests/rag_eval_set.json`](tests/rag_eval_set.json).

Tests are designed to pass **without** `OPENAI_API_KEY`. For optional live LLM verification, set the key and use the AI Coach manually.

---

## Reflection (portfolio)

Building PawPal+ as an **applied AI system** reinforced that **retrieval quality and citation discipline** matter as much as model choice: a smaller model with enforced `[Sn]` grounding and fallback behavior can be **more dependable** than a larger model that drifts off-source. Separating **`ui/`**, **`pawpal_system`**, and **`rag_engine`** kept responsibilities testable — the same lesson as parallelizing OO design vs. stuffing logic into one file. See **[`reflection.md`](reflection.md)** for Module 2 design narrative and **[`model_card.md`](model_card.md)** for ethics, limitations, and AI collaboration examples required by the course.

---

## Demo and video walkthrough

- **Screenshots:** [`assets/Demo1.png`](assets/Demo1.png), [`assets/Demo2.png`](assets/Demo2.png).
- **12-minute presenter script:** [`claude/doc/demo-script.md`](claude/doc/demo-script.md).

**Course Loom requirement:** Add your recording link once available:

```text
Loom: (paste URL here — show end-to-end run, AI Coach, and guardrail/fallback behavior)
```

---

## System architecture

**Class-centric view (exported UML):**

[![PawPal UML](assets/uml_final.png)](assets/uml_final.png)

**Layered runtime view:** Data flows **user → Streamlit (`app.py` + `ui/`) → domain (`pawpal_system`) OR RAG (`rag_engine`) → JSON / logs.** The domain stack does **not** import Streamlit or the RAG layer; the UI stitches schedule context into questions. Full Mermaid diagrams, dependency rules, and sequences: **[`claude/doc/architecture.md`](claude/doc/architecture.md)**.

**Images:** Screenshots and any exported diagram PNGs live under [`assets/`](assets/) — add or refresh them whenever you finalize visuals for grading or portfolio.

---

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Run the Streamlit app

```bash
streamlit run app.py
```

### Optional: enable AI responses

```bash
export OPENAI_API_KEY="your-key-here"
```

Or copy `.env.example` to `.env` and add your key.

### Run the CLI demo

```bash
python main.py
```

### Run tests

```bash
pytest tests/
```

---

## Project structure

```
.
├── app.py                 # Thin Streamlit entry + navigation dispatch
├── ui/                    # Theme, helpers, pages, navigation, content
├── pawpal_system.py       # Task, Pet, Owner, Scheduler
├── rag_engine.py          # RAG + OpenAI/fallback + logging
├── main.py                # CLI demo of scheduling features
├── cli_demo.py            # Extended CLI scenarios
├── knowledge_base.json    # Local KB for AI Coach
├── data.json              # Persisted owner/pets/tasks (generated at runtime)
├── logs/ai.log            # RAG decisions (gitignored)
├── model_card.md          # Ethics, limitations, collaboration (submission)
├── reflection.md          # Deeper Module 2 + AI collaboration reflection
├── uml_diagram.md         # Mermaid source for class diagram
├── claude/doc/            # Planning: requirements, RAG spec, roadmap, demo script
├── assets/                # Screenshots and diagram PNGs (you maintain)
├── tests/
│   ├── test_pawpal.py
│   ├── test_models.py
│   ├── test_rag_engine.py
│   ├── test_rag_eval.py
│   └── rag_eval_set.json
└── requirements.txt
```

---

## Smarter scheduling (CLI)

`python main.py` demonstrates sorting, filtering, recurrence, and conflict detection in the terminal.

---

## Documentation index

| Doc | Role |
|-----|------|
| [`README.md`](README.md) | This file — setup, architecture summary, samples, testing |
| [`model_card.md`](model_card.md) | Model/ethics card for submission |
| [`reflection.md`](reflection.md) | Design and collaboration reflection |
| [`claude/doc/README.md`](claude/doc/README.md) | Full planning bundle index |
