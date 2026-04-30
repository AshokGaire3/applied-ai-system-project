# PawPal+ — Model and ethics card

This document satisfies the Applied AI Systems final-project prompts on **reflection, ethics, biases, misuse, AI collaboration**, and aligns with grading expectations for **`model_card.md`**.

---

## System purpose (one paragraph)

**PawPal+** evolved from CodePath Applied AI **Module 2 (PawPal scheduling prototype)** into a full **applied AI system**: Streamlit UI, domain scheduler (`Owner` / `Pet` / `Task` / `Scheduler`), JSON persistence, and an **AI Coach** powered by retrieval-augmented generation over a curated local knowledge base (`knowledge_base.json`, ~16 topical notes). The model tier is optional: **OpenAI Chat Completions** (`gpt-4o-mini` by default via `urllib`) produces grounded answers with `[S1]`-style citations; without an API key, a deterministic **fallback** summarizes **only cited** retrieved sources so the sidebar matches citations. Retrieval uses the **user question** for lexical matching so optional “today’s plan” context can inform the prompt without drowning ranking. Questions that combine **walking and feeding/meals** deterministically tie `[S1]`/`[S2]` to the walks + feeding KB entries after we saw generic retrieval mis-order sources. Runtime behavior is logged to `logs/ai.log`; citation format is validated before an OpenAI answer is shown.

---

## Limitations and biases

- **Small, author-written knowledge base:** Notes are actionable but general. They are not peer-reviewed veterinary guidance. Coverage is uneven across species and edge cases even after expanding from the original stub set into topics like parasite prevention and travel carriers.
- **Retrieval:** Scoring blends **document TF-IDF**, **extra weight on title matches**, **tag hits**, **adjacent two-word overlaps** between query and KB text, and **crude plural → singular query expansion**. It still does **not** use embeddings, so creatively phrased questions can miss unless tokens align. Corpus size is modest (~16 docs), so **wording collisions** remain possible (mitigated once by rewriting medication vs. feeding blurbs after eval failures).
- **Scheduler:** The daily plan is **greedy by priority**, not globally optimal. It may skip lower-priority tasks that could have fit if ordered differently.
- **Conflict detection:** Overlaps are flagged for all timed tasks; the app does not know that two people could handle two pets at once.
- **Language / locale:** UI and prompts are English-first; timezone and feeding norms are not localized.

---

## Possible misuse and mitigations

| Misuse | Mitigation built in |
|--------|---------------------|
| Treating AI Coach output as a diagnosis | System prompt and fallback emphasize **see a veterinarian** for medical symptoms; citations tie answers to KB text only; no symptom triage UX. |
| Running without reviewing schedule conflicts | **Warnings only:** the UI never auto-fixes overlaps; humans must resolve. |
| Committing secrets | `.env` is gitignored; README documents env-based keys only. |
| Scraping personal data via logs | Logs use **structured decision lines** (`pawpal_ai`); extend only with care — avoid logging full user questions if policy tightens (see roadmap). |

---

## What surprised me while testing reliability

- **Citation validation matters:** Even a low-temperature model can omit `[Sn]` tokens; treating that as failure and falling back made offline demos and CI stable.
- **Retrieval@3 on a tiny KB is forgiving** until you add out-of-scope questions; the eval harness (`tests/test_rag_eval.py` + `tests/rag_eval_set.json`) exposed the need for explicit “no source” cases.
- **Persistence round-trips** are easy to break when adding a field to `Task` without updating both `to_dict` and `from_dict` — symmetric serialization caught real bugs early.
- **Lexical leakage from “helpful” context:** Appending today’s scheduled task lines to the *retrieval query* inadvertently retrieved unrelated KB articles when task titles shared words (“introducing,” “pets”) with enrichment articles. Fixing it meant **retrieve on the question; keep context only in the LLM prompt.**
- **Template citations can lie:** The walk+meal fallback assumed `[S1]`/`[S2]` matched retrieval order once **ID/recovery copy** accidentally outranked walks because of benign words (`before`). We now **pin** walks + feeding for that intent and align **sources in the UI** with what the fallback actually cites (including up to three bullets when useful).

---

## Collaboration with AI during this project

**Helpful suggestion:** When designing JSON persistence, an AI proposed **symmetric `to_dict` / `from_dict` on each class** instead of a monolithic loader that reached into private `_tasks`. That matched encapsulation goals and made tests smaller.

**Flawed or incomplete suggestion:** An AI once suggested **auto-shifting conflicting task start times** to remove overlaps. That was rejected: silent schedule changes are unsafe for medication-like tasks; **warning-only** behavior matches human judgment and is what we shipped (see `reflection.md`).

**Iteration on RAG UX:** Collaboration helped prototype **phrase bonuses and title-heavy scoring** quickly, plus KB edits to separate near-duplicate intents (scheduled meds vs. “same meal time”). Human review stayed necessary to catch **evaluation regressions** (feeding question suddenly ranking meds) and **product-truth failures** (citations not matching sidebar).

---

## Testing summary (short)

- Run **`pytest tests/`** — includes **core scheduler tests** (`test_pawpal.py`), legacy model tests (`test_models.py`), RAG unit tests (`test_rag_engine.py`), and **RAG eval** (`test_rag_eval.py` against `tests/rag_eval_set.json`).
- **Without `OPENAI_API_KEY`:** UI and tests use fallback and retrieval paths; no network required for acceptance.
- **With API key:** Optional manual check that OpenAI answers pass `validate_citations` or fall back.

---

## Data and privacy

- **Training data:** This project does **not** fine-tune a model; it calls a general-purpose chat API or uses deterministic fallback.
- **User data:** `data.json` stays local; KB is static repo content unless you edit it.

---

## Version and configuration

| Item | Value |
|------|-------|
| Default model (`PAWPAL_AI_MODEL`) | `gpt-4o-mini` |
| Temperature | `0.2` (in `rag_engine._call_openai`) |
| Knowledge base file | `knowledge_base.json` |
| Retrieval top-K | `3` |

Last updated: reflects RAG retrieval/citation iteration, expanded KB (~16 entries), question-only lexical retrieval with walk-meal pinning, and alignment of fallback citations with “Sources used.”
