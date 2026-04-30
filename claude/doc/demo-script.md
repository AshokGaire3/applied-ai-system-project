# PawPal+ — Demo Script (Loom-friendly, 5–7 minutes)

**Purpose:** A timed walkthrough you can record once into Loom (or present live) that hits every feature graders care about per [instruction.md](../../instruction.md).
**Audience:** The presenter (you), reviewers watching the demo / Loom.
**Last updated:** 2026-04-28.
**Related docs:** [claude.md](claude.md) · [requirements.md](requirements.md) · [skills.md](skills.md) · [rag-spec.md](rag-spec.md) · [roadmap.md](roadmap.md).

The rubric in [instruction.md](../../instruction.md) requires:

> Loom video walkthrough showing 2–3 inputs end-to-end, AI feature behavior (RAG, agent, etc.), reliability/guardrail or evaluation behavior, clear outputs for each case. **It does not need to show code setup, file structure, or installation steps.**

This script is built specifically for that bar.

---

## 1. Pre-record checklist

Run this 5 minutes before pressing record.

- [ ] Activate venv: `source .venv/bin/activate`.
- [ ] Confirm dependencies: `pip install -r requirements.txt`.
- [ ] Reset data state for a clean recording: rename `data.json` → `data.json.bak` (you will restore it after).
- [ ] Clear the chat log file if you want a clean log: `> logs/ai.log`.
- [ ] Decide whether to demo the OpenAI path:
  - With key: `export OPENAI_API_KEY=sk-...` then `streamlit run app.py`.
  - Without key: ensure the variable is unset; fallback mode will be the default.
- [ ] Open `streamlit run app.py` in one terminal.
- [ ] Open the browser at `http://localhost:8501`. Increase browser zoom to ~110% so the layout is readable in the recording.
- [ ] Open Loom, set window to 1280×720 capture, microphone on, camera optional.
- [ ] Have [reflection.md](../../reflection.md) and the [README.md](../../README.md) open in your editor as backup talking-point sources.
- [ ] Close noisy apps (chat, mail, IDE notifications). Mute Slack.

---

## 2. Time budget (7 minutes hard cap, target 5–6)

| Segment | Minutes | Cumulative | What you cover |
|---------|--------:|-----------:|----------------|
| 1. Hook + base project | 0:30 | 0:30 | Module 2 PawPal+ scheduler + final-project additions in one breath. |
| 2. Architecture overview | 0:45 | 1:15 | Layered diagram from [architecture.md](architecture.md); the `ui/` package; decoupling rules. |
| 3. Live: input #1 — add owner / pet / tasks | 1:00 | 2:15 | Real input, real output. First sample interaction. |
| 4. Live: input #2 — generate schedule + conflict | 1:00 | 3:15 | Real input, real output. Second sample interaction. |
| 5. Live: input #3 — AI Coach (RAG) | 1:30 | 4:45 | Real input, real output with citations. Third sample interaction. |
| 6. Reliability and guardrails | 1:00 | 5:45 | Citation gate, fallback, vet deferral, persistence error toast, eval harness summary. |
| 7. Wrap | 0:45 | 6:30 | What is next, link to repo + planning bundle. |
| Buffer | 0:30 | 7:00 | Recovery if something stalls. |

If you fall behind: skip the **persistence error toast** in segment 6 — the eval-harness summary is more important.

---

## 3. Segment 1 — Hook + base project (0:30)

**Talking points:**
- "PawPal+ is the final-project extension of my Module 2 PawPal+ scheduler — a Streamlit app that helps a busy pet owner plan daily care across multiple pets within a real time budget."
- "The Module 2 version had the scheduler. The final project adds a RAG-based AI Coach that answers pet-care questions with citations and a deterministic fallback when there is no API key."
- "I'll show three real inputs end-to-end."

**Visual:** App home tab with the hero card visible.

---

## 4. Segment 2 — Architecture overview (0:45)

**Talking points:**
- "Four layers: UI, Domain, RAG, Persistence. Each layer can be tested in isolation."
- "The UI is split into a small `app.py` entry point and a `ui/` package — `theme`, `helpers`, `navigation`, `pages`, `content`. Pages depend on helpers; helpers do not depend on pages."
- "Domain has zero UI imports. RAG has zero domain imports. Streamlit is the only thing that bridges them — by passing today's plan as `extra_context` to the AI Coach."
- "Persistence is plain JSON. No database. No external services except an optional OpenAI call."

**Visual:** Show the layered diagram from [architecture.md](architecture.md) in your editor, or embed any PNG you saved under `assets/`.

---

## 5. Segment 3 — Live: input #1 — add owner / pet / tasks (1:00)

**Sample interaction #1.** This is the first of the three the rubric asks for.

1. **Profile tab.** Type `Jordan` and `120` minutes. Click **Save Owner Profile**. Click **Save to data.json**.
   - Talking point: "State is persisted to `data.json`. The save call is wrapped in a try/except — if the disk is read-only the user gets a friendly toast, not a traceback."
2. **Pets tab.** Add `Mochi` (dog, 2y).
   - Talking point: "Validation happens at the domain layer. Notice the species emoji."
3. **Tasks tab.** Add three tasks for Mochi:
   - `Morning walk`, 20m, **high**, daily, `08:00`.
   - `Allergy pill`, 5m, **high**, daily, `08:00` — deliberate conflict.
   - `Evening play`, 15m, medium, daily, `18:00`.
   - Talking point: "Two tasks are timed at 08:00 — the system warns me **right now**, before I even build the schedule."
4. Point at the warning banner. Reference: [requirements.md](requirements.md) FR-TASKS-3.

**Output beat:** the early-conflict warning is visible.

---

## 6. Segment 4 — Live: input #2 — generate schedule + conflict (1:00)

**Sample interaction #2.**

1. **Schedule tab.** Click **Generate Schedule**.
2. Walk through the dataframe:
   - Time window, pet, task, priority, frequency.
   - Total minutes vs. the 120-minute budget.
   - Plan-level + start-time-level conflict warnings.
   - "Unscheduled tasks" section if any tasks did not fit.
3. Talking points:
   - "The scheduler is greedy — high priority first, ties broken by shorter duration."
   - "It never silently rewrites the schedule. Conflicts are flagged so the human decides."
   - "Tasks that did not fit are explicitly listed — nothing is dropped quietly."

**Output beat:** schedule renders, conflict block appears, no traceback.

---

## 7. Segment 5 — Live: input #3 — AI Coach / RAG (1:30)

**Sample interaction #3.** This is the segment graders pay the most attention to.

1. **AI Coach tab.** Open the **Question scope and guardrails** expander briefly to show "supported / not supported / guardrails".
2. Tick "Include today's schedule context" (default).
3. Click the **Walk + meal timing** starter button (or type "Should I feed before or after a walk for a young dog?").
4. Watch the spinner, then walk through the response:
   - The chat bubble (`st.chat_message`) with the answer text.
   - The "Sources used" expander beneath it — `[S1]`, `[S2]`, `[S3]` labels.
   - The info banner ("OPENAI_API_KEY is not set. Using local fallback response.") if running in fallback mode.
5. Talking points (timed beats):
   - **Retrieval (15s).** "First, the question is tokenized and matched against a TF-IDF index built over `knowledge_base.json`. Top-3 entries become the source set."
   - **Context assembly (15s).** "Each source gets a label `[S1]`, `[S2]`, `[S3]`. Today's schedule is appended as optional context. The system prompt tells the model: use only the sources, cite them, never give medical diagnosis — refer to a vet."
   - **Generation (15s).** "If a key is set, we call `gpt-4o-mini` with temperature 0.2. The response is rejected unless it contains a valid `[Sn]` citation. That is a hard guardrail."
   - **Fallback (15s).** "Without a key — or if validation fails — we fall back to a deterministic local template that still cites every source and ends with a vet disclaimer. The demo runs the same either way."
   - **Logs (15s).** Switch to a terminal: `tail -n 5 logs/ai.log`. Point at the `Answered with fallback template` (or `Answered with OpenAI model`) lines.

---

## 8. Segment 6 — Reliability and guardrails (1:00)

This is the rubric's "Reliability/guardrail or evaluation behavior" beat.

Pick **two** of these to show on screen — pick the eval harness as one of them:

- **Eval harness (always).** In a terminal: `pytest tests/test_rag_eval.py -v`. Point at the three passing tests:
  - `test_rag_eval_retrieval_at_3_and_coverage` (≥ 0.90, full coverage).
  - `test_rag_eval_fallback_determinism_and_token_expectations` (deterministic, must-contain tokens present).
  - `test_rag_eval_oos_refusal_rate` (≥ 0.80 of nonsense queries refused).
- **Citation gate.** Mention `validate_citations` rejects non-citing answers.
- **Vet deferral.** Show the disclaimer in the fallback answer and / or read the system-prompt line.
- **Persistence error toast.** Live: `chmod 444 data.json` in a terminal, then click **Save** — friendly red toast appears, no traceback.
- **No-source refusal.** Type a nonsense query like `xylophar nimbic`; the AI Coach says it could not find matching notes.

Closing line for this segment: *"The eval harness is the evidence. It runs offline, it's deterministic, and it catches regressions in retrieval quality without needing an API key."*

---

## 9. Segment 7 — Wrap (0:45)

**Talking points:**
- "Everything I just showed is documented under `claude/doc/` — 11 spec / planning files including the RAG spec, the skills catalog, and the eval plan."
- "The repo includes 61 pytest cases that all pass without an API key."
- "Next: a stretch test-harness CLI and an embeddings-based retrieval upgrade — both tracked in [roadmap.md](roadmap.md) §4."
- "Code is on GitHub at `<repo URL>`. Thanks for watching."

---

## 10. Post-record / post-demo

- [ ] Restore `data.json` from `data.json.bak` if you renamed it.
- [ ] If you `chmod 444`'d `data.json` for the persistence demo, `chmod 644 data.json` to restore.
- [ ] Unset `OPENAI_API_KEY` in your terminal if you exported it.
- [ ] Trim the Loom recording (Loom's editor — drop the awkward first 2 seconds).
- [ ] Copy the Loom share URL.
- [ ] Add the Loom link to [README.md](../../README.md). Required by the [instruction.md](../../instruction.md) submission checklist.
- [ ] Note any audience question you could not answer — add it to [roadmap.md](roadmap.md) §1 (rubric) or §4 (stretch) as appropriate.

---

## 11. Backup talking-points cheat sheet

| Beat | One-liner |
|------|-----------|
| Base project | Module 2 PawPal+ scheduler. |
| What's new | RAG AI Coach, modular `ui/` package, eval harness, persistence reliability. |
| Architecture | UI / Domain / RAG / Persistence — strictly decoupled. |
| Scheduling | Greedy, time-budgeted, never silently rewrites. |
| RAG | TF-IDF retrieval, `[Sn]` citations, deterministic fallback, vet deferral in the system prompt. |
| Reliability | Citation guardrail, vet deferral, source-only prompt, offline-first, persistence error toast. |
| Tests | 61 pytest cases, all pass without an API key; RAG eval harness asserts retrieval@3 ≥ 0.90 and OOS refusal ≥ 0.80. |
| Next | Stretch test-harness CLI, embeddings upgrade. |

---

## 12. Common Q&A you can answer fast

- **"Why TF-IDF instead of embeddings?"** → 8-entry KB, zero dependency, deterministic tests. See [rag-spec.md](rag-spec.md) §2.5.
- **"Why greedy instead of optimal?"** → Easy to explain to a non-technical user; fast enough at scale. See [reflection.md](../../reflection.md) §2b.
- **"What about hallucination?"** → Three layers: source-only system prompt, hard `validate_citations` gate, deterministic fallback. See [risks-guardrails.md](risks-guardrails.md) §2.
- **"Could it be misused?"** → Medical diagnosis is the main risk; mitigated by the vet-deferral in both the system prompt and the fallback. See [risks-guardrails.md](risks-guardrails.md) §5.
- **"How big is the codebase?"** → ~1k lines of domain + UI + RAG, plus ~700 lines of tests, plus the planning folder.
