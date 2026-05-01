# PawPal+: problem space & service map

This note is an **internal product brief**: what multi-pet households actually struggle with, how PawPal+ addresses those jobs without replacing veterinary judgment, and how each Streamlit **service** fits together—including the AI Coach.

---

## 1. Who the system is for

**Primary persona:** One adult (sometimes two) juggling **paid work**, **travel**, **irregular hours**, or **multiple species**—with **different routines per pet** (e.g. meds with meals, rabbit hay ad lib, cat litter scoops).

**Secondary persona:** Sitters / partners who need a **single view** of “what matters today,” not a dump of unstructured notes.

**Non-goals:** Diagnosis, emergency triage, regulatory compliance for boarding kennels, or replacing legally required disclosure from a veterinarian.

---

## 2. The core jobs-to-be-done (JTBD)

| Job | Plain-language pain | What “good” looks like |
|-----|---------------------|-------------------------|
| **Coordinate** | “I forgot which pet gets what and when.” | Every recurring need is modeled as tasks with priorities and optional time cues. |
| **Pack time** | “I only have X minutes.” | Scheduler produces an honest plan + **shows what didn’t fit** instead of pretending everything ran. |
| **De-risk timing** | “Two things overlap and I’m one pair of hands.” | **Conflict detection** warns; humans decide—critical for meds-like semantics. |
| **Educate safely** | “Dr. Google contradicts itself.” | **AI Coach**: answers **grounded in your KB** + citations; escalate to vet for symptoms/clinical ambiguity. |
| **Hand off** | “The sitter texted seventeen questions.” | **Care handoff** exports a concise sheet: pets, meds signals, dietary clues, emergencies. |

---

## 3. Layered trust model (applied AI framing)

1. **Data you entered** (`data.json`) is the scheduling source of truth.  
2. **Knowledge base** (`knowledge_base.json`) is static, author-maintained—not live medical records.  
3. **Retriever** biases answers toward the right topical notes (lexical scoring + intent routing).  
4. **Optional LLM** rewrites retrieval into fluent prose **only when** citations validate; otherwise **fallback** quoting.

This stack matches course expectations: *retrieval changes behavior*, failures are observable (logs), and limits are disclosed (`model_card.md`).

---

## 4. Service catalog (navigation)

| Service | Responsibility | Expert intent |
|---------|----------------|----------------|
| **Profile** | Owner identity + **daily minute budget**. | Cognitive anchor: feasibility is meaningless without capacity. |
| **Pets** | Registry per animal (species, age). | Lets tasks and summaries be species-aware in language and risk hints. |
| **Tasks** | Atomic care units with recurrence + priority + optional clocks. | Models *interruption load* alongside *importance*. |
| **Schedule** | Greedy pack within budget + **explicit skips**. | Transparency beats fake optimality—especially for meds. |
| **Wellness** | **Operational QA** layer: budget vs due load, conflicts, med-like tasks lacking times, species checklists. | Turns raw metrics into caregiver-facing readiness signals. |
| **Care handoff** | Generates a **situation-specific brief** (exportable text) for trusted helpers. | Reduces asymmetric information cost when you physically leave home. |
| **AI Coach (RAG)** | Question answering conditioned on retrieval + citations (+ optional LLM). | Lightweight “second brain” anchored to curated notes. |

Cross-links: Wellness suggests **Schedule** friction when conflicts exist; Handoff leverages **same task strings** pets already use—no duplicate medical chart.

---

## 5. How AI plugs in—without hallucinating autonomy

Typical runtime path:

```
User question
  → retrieve notes (intent-narrow where safe)
    → optionally pin intents (walk+meal sequencing)
      → assemble prompt (+ optional schedule excerpt)
        → chat model OR deterministic fallback with valid [Sn]
```

AI **does not**:

- Invent tasks,
- Rewrite your schedule silently,
- Promise clinical outcomes,

—without those constraints, portfolio reviewers correctly flag *unsafe agentic creep*.

---

## 6. Known trade-offs

- **Greedy scheduler** sacrifices global optimality for explainability.  
- **Lexical retrieval** skips embedding cost but needs careful KB intent routing as the corpus grows.  
- **English-first copy** ignores locale-specific norms unless extended.

---

## 7. Operational checklist (runs even without AI)

- Every **high priority** task should have either a plausible **daily fit** under budget or explicit owner acknowledgment (“skipped”).  
- **Medication-like** descriptors should ideally carry a **preferred time** (`HH:MM`) to tighten conflict UX.  
- After schedule changes: refresh **Care handoff** before travel.

---

_Last maintained alongside feature work in repo; keep terse and sync nav labels with `ui/navigation.py`._
