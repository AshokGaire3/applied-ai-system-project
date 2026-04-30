# PawPal+ — One-picture RAG + LLM + fallback (`rag_engine.py`)

Copy the **single fenced block** below into **[Mermaid Live](https://mermaid.live/)** -> **Export PNG** -> save as `assets/uml_rag.png` (or merge with your domain diagram in an image editor if you truly need everything in one raster).

For a deeper **sequence** view only, still see **`claude/doc/architecture.md`** §3.3.

---

## Single diagram (UI → retrieval → OpenAI vs fallback → three modes)

```mermaid
flowchart TB
    UI[["Streamlit — AI Coach tab<br/>user question + optional schedule context"]]

    subgraph PIPE["RagAssistant.answer — rag_engine.py"]
        Q[Compose retrieval query<br/>question + newline Context block if any]
        R1{"Retrieval cache<br/>hit?"}
        R2["retrieve_entries TF-IDF + tags + phrase bonus top-k"]
        R3{"Any KB<br/>matches?"}
        FMT["format_sources [S1]…[Sn] + assemble prompt<br/>+ recent chat excerpt"]
        A1{"Full answer<br/>cache hit?"}
        K{"OPENAI_API_KEY<br/>present?"}
        OAI["_call_openai — POST chat completions"]
        RSP{"Valid JSON body<br/>+ assistant text?"}
        VC{"validate_citations every Sn label in 1..k"}
        FALL["_fallback_answer — deterministic template"]
    end

    KB[["knowledge_base.json loaded + TF-IDF index at init"]]
    API[["OpenAI<br/>/v1/chat/completions"]]

    UI --> Q
    Q --> R1
    R1 -->|no| R2
    R1 -->|yes| R3
    R2 --> R3
    R2 -.uses.-> KB

    R3 -->|no| OUT1(["**no_sources** — no matching notes"])
    R3 -->|yes| FMT
    FMT --> A1
    A1 -->|yes| OUT4(["**cached** — prior identical prompt path"])
    A1 -->|no| K

    K -->|no| FALL
    K -->|yes| OAI
    OAI <--> API
    OAI --> RSP
    RSP -->|no| FALL
    RSP -->|yes| VC
    VC -->|no| FALL
    VC -->|yes| OUT2(["**openai** — cited model answer"])

    FALL --> OUT3(["**fallback** — template + KB bullets + [Sn]"])

    style OUT1 fill:#fdd,stroke:#333
    style OUT2 fill:#dfd,stroke:#333
    style OUT3 fill:#ffd,stroke:#333
    style OUT4 fill:#e8e8ff,stroke:#333
```

**How to read it:** Red = refuse (nothing retrieved). Green = live model with valid `[Sn]`. Yellow = deterministic fallback (no key, API error, bad parse, or invalid/missing citations). Purple = exact cache replay.
