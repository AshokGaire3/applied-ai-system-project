import json
import logging
import math
import os
import re
from typing import Dict, List, Optional, Tuple
from urllib import request
from urllib.error import HTTPError, URLError


DEFAULT_MODEL = os.getenv("PAWPAL_AI_MODEL", "gpt-4o-mini")
OPENAI_URL = "https://api.openai.com/v1/chat/completions"
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
    if not os.path.exists(path):
        return

    with open(path, "r") as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            key = key.strip()
            value = value.strip().strip("\"").strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


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

        scored.sort(key=lambda item: item[0], reverse=True)
        return [entry for _, entry in scored[:k]]

    scored: List[Tuple[int, Dict[str, str]]] = []
    for entry in entries:
        score = _score_entry(query_tokens, entry)
        if score > 0:
            scored.append((score, entry))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [entry for _, entry in scored[:k]]


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


def _fallback_answer(question: str, sources: List[Dict[str, str]]) -> str:
    question_lower = question.lower()
    has_walk = any(term in question_lower for term in ("walk", "exercise"))
    has_feed = any(term in question_lower for term in ("feed", "feeding", "meal", "food"))

    if has_walk and has_feed:
        return (
            "A good default is to keep a consistent routine and avoid feeding right before activity. "
            "For most dogs, do the walk first, then feed shortly after once your dog has settled. [S1][S2]\n\n"
            "If your dog has a medical condition, history of stomach issues, or specific vet instructions, "
            "follow your veterinarian's guidance."
        )

    top_points = []
    for i, entry in enumerate(sources, start=1):
        title = entry.get("title", "Guidance").strip()
        content = entry.get("content", "").strip()
        if content:
            top_points.append(f"- {title}: {content} [S{i}]")

    if not top_points:
        return "I found limited matching notes. Please add more details so I can give a targeted recommendation."

    return (
        "Based on your question, here is the most relevant guidance:\n\n"
        + "\n".join(top_points[:2])
        + "\n\nIf symptoms or medical concerns are involved, contact a veterinarian."
    )


def _call_openai(api_key: str, prompt: str) -> Optional[str]:
    payload = {
        "model": DEFAULT_MODEL,
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
        "temperature": 0.2,
    }

    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        OPENAI_URL,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=20) as response:
            body = json.loads(response.read().decode("utf-8"))
        return body["choices"][0]["message"]["content"].strip()
    except (HTTPError, URLError, KeyError, ValueError):
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
        query = question.strip()
        if extra_context:
            query = f"{query}\n\nContext:\n{extra_context.strip()}"

        cache_key = f"sources::{query}".lower()
        if cache_key in self._retrieval_cache:
            sources = self._retrieval_cache[cache_key]
            self.logger.info("Retrieval cache hit")
        else:
            sources = retrieve_entries(query, self.entries, self.k, index=self.index)
            self._retrieval_cache[cache_key] = sources

        if not sources:
            self.logger.info("No sources matched query")
            return {
                "answer": "I could not find matching notes. Try rephrasing or adding details.",
                "sources": [],
                "mode": "no_sources",
            }

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

        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            response = _call_openai(api_key, prompt)
            if response and validate_citations(response, len(source_meta)):
                self.logger.info("Answered with OpenAI model")
                result = {"answer": response, "sources": source_meta, "mode": "openai"}
                self._answer_cache[answer_key] = result
                return result
            self.logger.warning("OpenAI response missing citations or failed")

        fallback = _fallback_answer(question, sources)
        self.logger.info("Answered with fallback template")
        result = {"answer": fallback, "sources": source_meta, "mode": "fallback"}
        self._answer_cache[answer_key] = result
        return result
