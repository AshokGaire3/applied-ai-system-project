import json
import logging
import math
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib import request
from urllib.error import HTTPError, URLError


def _default_chat_model() -> str:
    return os.getenv("PAWPAL_AI_MODEL", "gpt-4o-mini")


def _openai_chat_url() -> str:
    base = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    return f"{base}/chat/completions"


STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "before",
    "by",
    "for",
    "from",
    "how",
    "i",
    "in",
    "is",
    "it",
    "my",
    "of",
    "on",
    "or",
    "should",
    "the",
    "to",
    "today",
    "what",
    "when",
    "with",
}


def _setup_logger() -> logging.Logger:
    logger = logging.getLogger("pawpal_ai")
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    os.makedirs("logs", exist_ok=True)
    handler = logging.FileHandler("logs/ai.log")
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


def _load_env_file(path: str = ".env") -> None:
    """Load `.env` from process cwd first, then next to rag_engine.py (Streamlit cwd safe)."""
    for base in (Path.cwd(), Path(__file__).resolve().parent):
        candidate = base / path
        if not candidate.is_file():
            continue
        with open(candidate, "r", encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                if "=" not in stripped:
                    continue
                key, value = stripped.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value
        break


def load_knowledge_base(path: str) -> List[Dict[str, str]]:
    with open(path, "r") as f:
        data = json.load(f)
    return data


def _tokenize(text: str) -> List[str]:
    raw_tokens = re.findall(r"[a-z0-9]+", text.lower())
    return [token for token in raw_tokens if token not in STOPWORDS and len(token) > 1]


def _singular_form(token: str) -> Optional[str]:
    """Crude plural → singular hints for retrieval (pets/pet, walks/walk)."""
    if len(token) < 4 or not token.endswith("s"):
        return None
    if token.endswith("ss"):
        return None
    stem = token[:-1]
    if len(stem) < 3:
        return None
    return stem


def _expand_query_tokens(tokens: List[str]) -> List[str]:
    """Deduped expansion so query wording aligns with KB singular/plural."""
    out: List[str] = []
    seen: set[str] = set()
    for token in tokens:
        for cand in (token, _singular_form(token)):
            if cand and cand not in seen:
                seen.add(cand)
                out.append(cand)
    return out


def _adjacent_pair_bonus(full_lower: str, query: str) -> float:
    """Boost when consecutive query words appear together in the source text."""
    toks = re.findall(r"[a-z0-9]+", query.lower())
    if len(toks) < 2:
        return 0.0
    bonus = 0.0
    for i in range(len(toks) - 1):
        pair = f"{toks[i]} {toks[i+1]}"
        if pair in full_lower:
            bonus += 1.15
    return bonus


def _score_entry(query_tokens: List[str], entry: Dict[str, str]) -> int:
    text = " ".join(
        [
            entry.get("title", ""),
            " ".join(entry.get("tags", [])),
            entry.get("content", ""),
        ]
    ).lower()
    score = 0
    for token in query_tokens:
        if token in text:
            score += 1
    return score


def _build_index(entries: List[Dict[str, str]]) -> Dict[str, object]:
    doc_count = len(entries)
    df: Dict[str, int] = {}
    entry_meta: List[Dict[str, object]] = []

    for entry in entries:
        tokens = _tokenize(
            " ".join(
                [
                    entry.get("title", ""),
                    " ".join(entry.get("tags", [])),
                    entry.get("content", ""),
                ]
            )
        )
        unique_tokens = set(tokens)
        for token in unique_tokens:
            df[token] = df.get(token, 0) + 1

        tf: Dict[str, float] = {}
        if tokens:
            for token in tokens:
                tf[token] = tf.get(token, 0.0) + 1.0
            total = float(len(tokens))
            for token in tf:
                tf[token] = tf[token] / total

        blob = (
            entry.get("title", "")
            + " "
            + " ".join(entry.get("tags", []))
            + " "
            + entry.get("content", "")
        )
        full_lower = blob.lower()

        entry_meta.append(
            {
                "tf": tf,
                "tags": set([t.lower() for t in entry.get("tags", [])]),
                "full_lower": full_lower,
            }
        )

    for ei, entry in enumerate(entries):
        title_only = entry.get("title", "")
        t_tokens = _tokenize(title_only)
        title_tf: Dict[str, float] = {}
        if t_tokens:
            for t in t_tokens:
                title_tf[t] = title_tf.get(t, 0.0) + 1.0
            tot = float(len(t_tokens))
            for t in title_tf:
                title_tf[t] = title_tf[t] / tot
        entry_meta[ei]["title_tf"] = title_tf

    idf: Dict[str, float] = {}
    for token, count in df.items():
        idf[token] = math.log((1 + doc_count) / (1 + count)) + 1.0

    return {"idf": idf, "meta": entry_meta}


def _query_question_only(query: str) -> str:
    """Prefer the user question for phrase overlap; avoids schedule-context noise."""
    if "\n\nContext:\n" in query:
        return query.split("\n\nContext:\n", 1)[0]
    return query


_FEEDING_IDS = frozenset({"kb_feeding", "kb_medication"})
_FEEDING_TAG_NEEDLES = frozenset({"feed", "meal", "portion", "insulin"})
_TITLE_FEEDING_NEEDLES = (
    "feeding",
    "feed ",
    " meal",
    "medication timing",
)


def _score_tuple_sort_key(indexed: Tuple[float, Dict[str, str]]) -> Tuple[float, str]:
    return (indexed[0], indexed[1].get("id") or "")


def _wants_feeding_focus(question_lower: str) -> bool:
    """True when the user is primarily asking about meals or feeding time."""
    if ("portion" in question_lower or "portions" in question_lower) and any(
        m in question_lower for m in ("meal", "feed", "food", "eating")
    ):
        return True
    if any(
        needle in question_lower
        for needle in (
            "feed ",
            " feeding",
            "feed my",
            "feed my pet",
            "feed the",
            "meal time",
            "mealtime",
            "when to eat",
            "eating schedule",
            "food schedule",
            "best time to feed",
        )
    ):
        return True
    tokens = question_lower.replace("?", " ").split()
    if "feed" in tokens or question_lower.endswith("feed") or " feed" in question_lower:
        return "time" in question_lower or any(
            q in question_lower for q in ("when", "should i", "recommend")
        )
    return False


def _entry_feeding_adjacent(entry: Dict[str, str]) -> bool:
    """KB rows that genuinely discuss feeding, meals, or med timing with food."""
    eid = entry.get("id", "")
    if eid in _FEEDING_IDS:
        return True
    tags = {t.lower() for t in entry.get("tags", [])}
    if tags & _FEEDING_TAG_NEEDLES:
        return True
    title_low = entry.get("title", "").lower()
    return any(needle in title_low for needle in _TITLE_FEEDING_NEEDLES)


_HYDRATION_IDS = frozenset({"kb_hydration"})
_HYDRATION_TAG_NEEDLES = frozenset({"water", "drink", "hydration"})


def _hydration_question_is_cat(question_lower: str) -> bool:
    if re.search(
        r"\b(?:cat|cats|kitten|kittens|feline|felines)\b",
        question_lower,
    ):
        return True
    return bool(
        "litter box" in question_lower
        or "litter tray" in question_lower
        or " for cats" in question_lower
    )


def _wants_hydration_focus(question_lower: str) -> bool:
    if re.search(r"\bwater\b", question_lower):
        return True
    return any(
        needle in question_lower
        for needle in (
            "hydrat",
            "hydration",
            "water bowl",
            "water bowls",
            "drinking",
            "thirst",
            "dehydrat",
            " thirsty",
            "water intake",
        )
    )


def _entry_hydration_adjacent(entry: Dict[str, str], cat_specific: bool) -> bool:
    if entry.get("id") in _HYDRATION_IDS:
        return True
    tags = {t.lower() for t in entry.get("tags", [])}
    if tags & _HYDRATION_TAG_NEEDLES:
        return True
    if cat_specific and entry.get("id") == "kb_cats_litter":
        return True
    return False


def _wants_litter_focus(question_lower: str) -> bool:
    return bool(re.search(r"\blitter\b", question_lower))


def _entry_litter_adjacent(entry: Dict[str, str]) -> bool:
    return entry.get("id") == "kb_cats_litter"


def _wants_medication_focus(question_lower: str) -> bool:
    if "missed dose" in question_lower or "miss a dose" in question_lower:
        return True
    return bool(
        re.search(
            r"\b(pills?|medicine|medications?|meds|insulin|injection|inject|shots?)\b",
            question_lower,
        )
    )


def _wants_medication_dose_keyword(question_lower: str) -> bool:
    """Avoid treating standalone 'dose' (e.g. preventive doses) as prescription-med intent."""
    if "dose" not in question_lower and "dosage" not in question_lower:
        return False
    return bool(
        re.search(
            r"\b(pills?|medicine|medications?|meds|insulin|prescription)\b",
            question_lower,
        )
        or "missed dose" in question_lower
        or "miss a dose" in question_lower
    )


def _entry_medication_adjacent(entry: Dict[str, str]) -> bool:
    if entry.get("id") == "kb_medication":
        return True
    tags = {t.lower() for t in entry.get("tags", [])}
    return bool(tags & {"meds", "pill", "insulin", "shot"})


def _wants_walk_exercise_focus(question_lower: str) -> bool:
    if _wants_feeding_focus(question_lower):
        return False
    if re.search(r"\b(walks?|walking|hike|hiking)\b", question_lower):
        return True
    if "exercise" in question_lower:
        return bool(re.search(r"\b(dog|puppy|puppies)\b", question_lower)) and (
            "enrichment" not in question_lower
        )
    return False


def _entry_walk_exercise_adjacent(entry: Dict[str, str]) -> bool:
    return entry.get("id") == "kb_walks"


def _wants_grooming_focus(question_lower: str) -> bool:
    needles = ("groom", "grooming", "brush", "brushing", "bathing", "bath ", "nail trim")
    return any(n in question_lower for n in needles)


def _entry_grooming_adjacent(entry: Dict[str, str]) -> bool:
    return entry.get("id") == "kb_grooming"


def _wants_dental_focus(question_lower: str) -> bool:
    return any(n in question_lower for n in ("dental", "teeth", "tooth brushing", "tartar"))


def _entry_dental_adjacent(entry: Dict[str, str]) -> bool:
    return entry.get("id") == "kb_dental_home"


def _wants_rabbit_focus(question_lower: str) -> bool:
    return bool(
        re.search(r"\b(rabbit|rabbits|bunny|bunnies)\b", question_lower)
    )


def _entry_rabbit_adjacent(entry: Dict[str, str]) -> bool:
    if entry.get("id") == "kb_rabbits":
        return True
    return "rabbit" in {t.lower() for t in entry.get("tags", [])}


def _wants_enrichment_focus(question_lower: str) -> bool:
    return any(
        w in question_lower
        for w in (
            "enrichment",
            "bored",
            "boredom",
            "mental stimulation",
            "puzzle feeder",
            "destructive behavior",
            "destructive behaviour",
        )
    )


def _entry_enrichment_adjacent(entry: Dict[str, str]) -> bool:
    return entry.get("id") == "kb_enrichment"


def _maybe_drop_weak_tertiary_hit(
    scored: List[Tuple[float, Dict[str, str]]],
) -> List[Tuple[float, Dict[str, str]]]:
    """If #3 scores far below #1, it is often lexical noise rather than topical support."""
    if len(scored) < 3:
        return scored
    best = scored[0][0]
    if best <= 0:
        return scored
    if float(scored[2][0]) < float(best) * 0.33:
        return scored[:2]
    return scored


def _apply_intent_narrowing(
    query: str,
    ranked: List[Dict[str, str]],
    k: int,
) -> List[Dict[str, str]]:
    ql = _query_question_only(query).strip().lower()
    wants_feed = _wants_feeding_focus(ql)
    wants_water = _wants_hydration_focus(ql)

    if wants_feed and wants_water:
        cats = _hydration_question_is_cat(ql)
        filt = [
            e
            for e in ranked
            if _entry_feeding_adjacent(e) or _entry_hydration_adjacent(e, cats)
        ]
        if filt:
            return filt[:k]
    elif wants_feed:
        filt = [e for e in ranked if _entry_feeding_adjacent(e)]
        if filt:
            return filt[:k]
    elif wants_water:
        cats = _hydration_question_is_cat(ql)
        filt = [e for e in ranked if _entry_hydration_adjacent(e, cats)]
        if filt:
            return filt[:k]

    if _wants_litter_focus(ql):
        filt = [e for e in ranked if _entry_litter_adjacent(e)]
        if filt:
            return filt[:k]
    if _wants_rabbit_focus(ql):
        filt = [e for e in ranked if _entry_rabbit_adjacent(e)]
        if filt:
            return filt[:k]
    if _wants_enrichment_focus(ql):
        filt = [e for e in ranked if _entry_enrichment_adjacent(e)]
        if filt:
            return filt[:k]
    wants_rx_med = _wants_medication_focus(ql) or _wants_medication_dose_keyword(
        ql
    )
    if wants_rx_med and not wants_feed:
        filt = [e for e in ranked if _entry_medication_adjacent(e)]
        if filt:
            return filt[:k]
    if _wants_walk_exercise_focus(ql):
        filt = [e for e in ranked if _entry_walk_exercise_adjacent(e)]
        if filt:
            return filt[:k]
    if _wants_dental_focus(ql):
        filt = [e for e in ranked if _entry_dental_adjacent(e)]
        if filt:
            return filt[:k]
    if _wants_grooming_focus(ql):
        filt = [e for e in ranked if _entry_grooming_adjacent(e)]
        if filt:
            return filt[:k]

    return ranked[:k]


def retrieve_entries(
    query: str,
    entries: List[Dict[str, str]],
    k: int = 3,
    index: Optional[Dict[str, object]] = None,
) -> List[Dict[str, str]]:
    query_tokens = _expand_query_tokens(_tokenize(query))
    if not query_tokens:
        return []

    phrase_query = _query_question_only(query)

    if index:
        idf: Dict[str, float] = index["idf"]
        meta: List[Dict[str, object]] = index["meta"]
        scored: List[Tuple[float, Dict[str, str]]] = []
        title_w = 0.52
        for entry, entry_meta in zip(entries, meta):
            tf: Dict[str, float] = entry_meta["tf"]
            title_tf: Dict[str, float] = entry_meta.get("title_tf", {})
            tags: set = entry_meta["tags"]
            full_lower: str = entry_meta.get("full_lower", "")
            score = 0.0
            for token in query_tokens:
                widf = idf.get(token, 0.0)
                score += tf.get(token, 0.0) * widf
                score += title_w * title_tf.get(token, 0.0) * widf
                if token in tags:
                    score += 0.4
            score += _adjacent_pair_bonus(full_lower, phrase_query)
            if score > 0:
                scored.append((score, entry))

        scored.sort(key=_score_tuple_sort_key, reverse=True)
        scored = _maybe_drop_weak_tertiary_hit(scored)
        ranked = [entry for _, entry in scored]
        return _apply_intent_narrowing(query, ranked, k)

    scored: List[Tuple[int, Dict[str, str]]] = []
    for entry in entries:
        score = _score_entry(query_tokens, entry)
        if score > 0:
            scored.append((score, entry))

    scored.sort(key=_score_tuple_sort_key, reverse=True)
    scored = _maybe_drop_weak_tertiary_hit(scored)
    ranked = [entry for _, entry in scored]
    return _apply_intent_narrowing(query, ranked, k)


def _is_walk_feed_meal_timing_question(question_lower: str) -> bool:
    has_walk = any(term in question_lower for term in ("walk", "exercise", "hike", "hiking"))
    has_feed = any(term in question_lower for term in ("feed", "feeding", "meal", "food"))
    return bool(has_walk and has_feed)


def _resolve_entries_by_ids(
    entries: List[Dict[str, str]],
    ids_in_order: List[str],
) -> List[Dict[str, str]]:
    by_id = {entry.get("id"): entry for entry in entries}
    resolved: List[Dict[str, str]] = []
    for eid in ids_in_order:
        match = by_id.get(eid)
        if match is not None:
            resolved.append(match)
    return resolved


def _sources_meta(entries: List[Dict[str, str]]) -> List[Dict[str, str]]:
    meta: List[Dict[str, str]] = []
    for i, entry in enumerate(entries, start=1):
        meta.append({"label": f"S{i}", "title": entry.get("title", "Untitled")})
    return meta


def format_sources(entries: List[Dict[str, str]]) -> Tuple[str, List[Dict[str, str]]]:
    lines = []
    sources = []
    for i, entry in enumerate(entries, start=1):
        label = f"S{i}"
        title = entry.get("title", "Untitled")
        content = entry.get("content", "").strip()
        lines.append(f"[{label}] {title}: {content}")
        sources.append({"label": label, "title": title})
    return "\n".join(lines), sources


def validate_citations(answer: str, source_count: int) -> bool:
    if source_count == 0:
        return False
    matches = re.findall(r"\[S(\d+)\]", answer)
    if not matches:
        return False
    for match in matches:
        num = int(match)
        if num < 1 or num > source_count:
            return False
    return True


def _fallback_answer(
    question: str, sources: List[Dict[str, str]]
) -> Tuple[str, List[Dict[str, str]]]:
    """Return answer text and the entries actually cited (S1…Sn aligned with citations)."""
    question_lower = question.lower()
    if _is_walk_feed_meal_timing_question(question_lower) and len(sources) >= 2:
        cited = sources[:2]
        text = (
            "A good default is to keep a consistent routine and avoid feeding right before activity. "
            "For most dogs, do the walk first, then feed shortly after once your dog has settled. [S1][S2]\n\n"
            "If your dog has a medical condition, history of stomach issues, or specific vet instructions, "
            "follow your veterinarian's guidance."
        )
        return text, cited

    top_points = []
    cited_entries: List[Dict[str, str]] = []
    for i, entry in enumerate(sources, start=1):
        title = entry.get("title", "Guidance").strip()
        content = entry.get("content", "").strip()
        if content:
            top_points.append(f"- {title}: {content} [S{i}]")
            cited_entries.append(entry)

    if not top_points:
        return (
            "I found limited matching notes. Please add more details so I can give a targeted recommendation.",
            [],
        )

    max_bullets = min(3, len(top_points))
    body = "\n".join(top_points[:max_bullets])
    return (
        "Based on your question, here is the most relevant guidance:\n\n"
        + body
        + "\n\nIf symptoms or medical concerns are involved, contact a veterinarian.",
        cited_entries[:max_bullets],
    )


def _call_openai(api_key: str, prompt: str, *, log: Optional[logging.Logger] = None) -> Optional[str]:
    payload = {
        "model": _default_chat_model(),
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a pet-care assistant. Use only the provided sources and "
                    "cite them as [S1], [S2], etc. Lead with facts that directly answer "
                    "the question; avoid generic filler. If the sources do not cover "
                    "the question, say what is missing and ask one clarifying question. "
                    "Do not provide medical diagnosis; advise consulting a veterinarian "
                    "when symptoms or medical concerns are involved."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": float(os.getenv("PAWPAL_AI_TEMPERATURE", "0.2")),
    }

    data = json.dumps(payload).encode("utf-8")
    url = _openai_chat_url()
    req = request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=45) as response:
            body = json.loads(response.read().decode("utf-8"))
        return body["choices"][0]["message"]["content"].strip()
    except HTTPError as exc:
        if log:
            try:
                err_body = exc.read().decode("utf-8")[:1200]
            except OSError:
                err_body = str(exc.reason)
            log.warning("OpenAI HTTP %s %s — %s", exc.code, exc.reason, err_body[:500])
        return None
    except (URLError, KeyError, ValueError, TypeError):
        return None


def _try_openai_rag_answer(
    api_key: str,
    prompt: str,
    num_sources: int,
    logger: logging.Logger,
) -> Optional[str]:
    """Call chat completions; retry once if the model omits valid [Sn] citations."""
    reply = _call_openai(api_key, prompt, log=logger)
    if reply and validate_citations(reply, num_sources):
        return reply

    suffix = (
        "\n\n---\nYour previous reply failed the citation checker. Answer again briefly. "
        f"Include at least one valid bracket citation from exactly this set only: "
        f"{', '.join(f'[S{i}]' for i in range(1, num_sources + 1))}"
        ". Put citations right after supported facts."
    )
    logger.warning("OpenAI RAG citation check failed — retry")
    retry = _call_openai(api_key, prompt + suffix, log=logger)
    if retry and validate_citations(retry, num_sources):
        return retry
    return None


class RagAssistant:
    def __init__(self, kb_path: str, k: int = 3):
        self.kb_path = kb_path
        self.k = k
        self.logger = _setup_logger()
        _load_env_file()
        self.entries = load_knowledge_base(kb_path)
        self.index = _build_index(self.entries)
        self._retrieval_cache: Dict[str, List[Dict[str, str]]] = {}
        self._answer_cache: Dict[str, Dict[str, object]] = {}

    def answer(
        self,
        question: str,
        extra_context: Optional[str] = None,
        chat_history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, object]:
        question_clean = question.strip()
        retrieval_key = question_clean.lower()
        if retrieval_key in self._retrieval_cache:
            sources = self._retrieval_cache[retrieval_key]
            self.logger.info("Retrieval cache hit")
        else:
            # Use the user question only so schedule context strings do not skew ranking.
            sources = retrieve_entries(
                question_clean, self.entries, self.k, index=self.index
            )
            self._retrieval_cache[retrieval_key] = sources

        if not sources:
            self.logger.info("No sources matched query")
            return {
                "answer": "I could not find matching notes. Try rephrasing or adding details.",
                "sources": [],
                "mode": "no_sources",
            }

        if _is_walk_feed_meal_timing_question(question_clean.lower()):
            wf = _resolve_entries_by_ids(self.entries, ["kb_walks", "kb_feeding"])
            if len(wf) == 2:
                sources = wf

        source_text, source_meta = format_sources(sources)
        history_text = ""
        if chat_history:
            recent = chat_history[-6:]
            history_lines = [
                f"{item['role'].capitalize()}: {item['content'].strip()}"
                for item in recent
                if item.get("content")
            ]
            if history_lines:
                history_text = "\n".join(history_lines)

        prompt_parts = [f"Question: {question.strip()}"]
        prompt_parts.append(f"Context:\n{(extra_context or 'None').strip()}")
        if history_text:
            prompt_parts.append(f"Conversation history:\n{history_text}")
        prompt_parts.append(f"Sources:\n{source_text}")
        prompt_parts.append("Answer using only the sources. Include citations like [S1].")
        prompt = "\n\n".join(prompt_parts)

        answer_key = f"answer::{prompt}".lower()
        if answer_key in self._answer_cache:
            self.logger.info("Answer cache hit")
            return self._answer_cache[answer_key]

        api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
        if api_key:
            response = _try_openai_rag_answer(
                api_key, prompt, len(source_meta), self.logger
            )
            if response:
                result = {
                    "answer": response,
                    "sources": source_meta,
                    "mode": "openai",
                }
                self.logger.info(
                    "Answered with OpenAI model %s",
                    _default_chat_model(),
                )
                self._answer_cache[answer_key] = result
                return result
            self.logger.warning("OpenAI response missing citations or failed after retry")

        fallback_text, cited_entries = _fallback_answer(question_clean, sources)
        self.logger.info("Answered with fallback template")
        result = {
            "answer": fallback_text,
            "sources": _sources_meta(cited_entries),
            "mode": "fallback",
        }
        self._answer_cache[answer_key] = result
        return result
