# PawPal+ Planning Bundle

**Purpose:** Index and reading guide for the `claude/doc/` planning bundle.
**Audience:** Project author, instructors, future contributors, AI coding agents.
**Last updated:** 2026-04-28.

This folder is the **single planning surface** for the PawPal+ final project (CodePath Applied AI Engineering / Applied AI System course). It contains spec / design / planning documents only — no application code lives here. Code lives at the repository root (`app.py`, `pawpal_system.py`, `rag_engine.py`) and inside the [ui/](../../ui/) package.

The course-level rubric and submission requirements live in the repository's [instruction.md](../../instruction.md). This bundle traces every requirement to a specific design decision.

---

## What is PawPal+?

PawPal+ is a Streamlit web app that helps a busy pet owner plan daily care tasks across one or more pets. It combines a deterministic priority-based scheduler with a Retrieval-Augmented Generation (RAG) "AI Coach" that answers pet-care questions grounded in a local knowledge base. See [claude.md](claude.md) for the full problem statement and scope.

PawPal+ extends the **Module 2 PawPal+ scheduler** project into a complete applied AI system that satisfies the final-project rubric in [instruction.md](../../instruction.md):

- **Required AI feature:** RAG (`RagAssistant` in [rag_engine.py](../../rag_engine.py)).
- **Reliability / testing:** automated test harness ([tests/](../../tests/)) with a dedicated RAG evaluation set ([tests/test_rag_eval.py](../../tests/test_rag_eval.py)) and runtime logging to `logs/ai.log`.
- **Stretch features under consideration:** RAG enhancement (multi-source / metadata filters) and a CLI-style test-harness script — tracked in [roadmap.md](roadmap.md).

---

## Documents in this folder

| # | Document | One-line purpose |
|---|----------|------------------|
| 1 | [claude.md](claude.md) | Single source of truth: problem, scope, glossary, repo map, AI-collaborator rules, rubric trace. |
| 2 | [requirements.md](requirements.md) | Functional + non-functional requirements with acceptance criteria, grouped by service tab. |
| 3 | [architecture.md](architecture.md) | Layered architecture (UI / Domain / RAG / Persistence), `ui/` package layout, sequence diagrams. |
| 4 | [data-model.md](data-model.md) | Class diagram, JSON schemas (`data.json`, `knowledge_base.json`, `tests/rag_eval_set.json`, `logs/ai.log`), serialization contract. |
| 5 | [skills.md](skills.md) | Capability catalog: every feature expressed as a contract (trigger, inputs, outputs, deps, failure mode). |
| 6 | [rag-spec.md](rag-spec.md) | Full RAG architecture spec following the 2026 IdeaPlan / Microsoft RAG template. |
| 7 | [evaluation.md](evaluation.md) | Test strategy: 63 pytest cases (incl. RAG eval harness), scheduler invariants, manual scenarios. |
| 8 | [risks-guardrails.md](risks-guardrails.md) | Reliability, safety, fallback flow, secrets handling, accepted limitations, incident playbook. |
| 9 | [roadmap.md](roadmap.md) | Milestones with status (done vs. remaining), submission deliverables from [instruction.md](../../instruction.md). |
| 10 | [demo-script.md](demo-script.md) | 5–7 minute Loom-friendly walkthrough mapped to the rubric in [instruction.md](../../instruction.md). |

---

## Recommended reading order

For a **new contributor or reviewer**, read top-to-bottom:

1. [claude.md](claude.md) — what is being built and why.
2. [requirements.md](requirements.md) — what the system must do.
3. [architecture.md](architecture.md) — how the system is shaped.
4. [data-model.md](data-model.md) — what the data looks like on disk.
5. [skills.md](skills.md) — what capabilities the system exposes.
6. [rag-spec.md](rag-spec.md) — how the AI Coach works.
7. [evaluation.md](evaluation.md) — how we know it works.
8. [risks-guardrails.md](risks-guardrails.md) — what can go wrong and how it is contained.
9. [roadmap.md](roadmap.md) — what is done vs. what is left, plus submission checklist.
10. [demo-script.md](demo-script.md) — how to present the Loom walkthrough.

For a **demo / Loom prep session**, jump straight to [demo-script.md](demo-script.md) and back-fill from [skills.md](skills.md).

For an **AI coding agent picking up a task**, read [claude.md](claude.md) for ground rules, then jump to the doc that matches the task domain (e.g., RAG work → [rag-spec.md](rag-spec.md), scheduler work → [skills.md](skills.md) + [architecture.md](architecture.md), UI work → [architecture.md](architecture.md) section on the `ui/` package).

For a **grader checking the rubric**, [roadmap.md](roadmap.md) section 1 maps every [instruction.md](../../instruction.md) requirement to a deliverable, and [evaluation.md](evaluation.md) summarizes test results.

---

## Document conventions

- All cross-references use **markdown links to actual repo paths** (e.g., [app.py](../../app.py), [pawpal_system.py](../../pawpal_system.py), [ui/pages.py](../../ui/pages.py)).
- Diagrams are written in **Mermaid** inside `claude/doc/` so they render in GitHub/Cursor without checked-in raster images. Export any diagrams to **`assets/`** only if your grader prefers PNGs—the author controls filenames and refreshes.
- Each document opens with a short header: **Purpose / Audience / Last-updated / Related docs**.
- Documents describe what is built or planned — they do not contain executable code.
- No emojis are used in the planning docs (the app UI itself uses emoji color-coding; that is documented in [requirements.md](requirements.md)).

---

## Out of scope for this folder

- Application source code (lives at repo root + the [ui/](../../ui/) package).
- Test code (lives in [tests/](../../tests/)).
- Generated artifacts: `data.json`, `logs/ai.log`, `assets/*` — referenced from these docs but produced by the running app or by recording the demo.
- The author's reflective writing ([reflection.md](../../reflection.md)); [`model_card.md`](../../model_card.md) mirrors rubric prompts.

---

## Related repository files

- [README.md](../../README.md) — public-facing user-and-developer README. Will be expanded for final submission per [instruction.md](../../instruction.md) section 3.
- [instruction.md](../../instruction.md) — official course rubric and submission checklist (source of truth for grading).
- [reflection.md](../../reflection.md) — design + AI collaboration reflection (Module 2 deliverable; final-project addendum tracked in [roadmap.md](roadmap.md)).
- [uml_diagram.md](../../uml_diagram.md) — Mermaid UML source.
- [requirements.txt](../../requirements.txt) — Python dependencies (`streamlit`, `pytest`).
