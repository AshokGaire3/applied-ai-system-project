import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from rag_engine import (
    RagAssistant,
    _fallback_answer,
    _resolve_entries_by_ids,
    format_sources,
    retrieve_entries,
    validate_citations,
)


def _load_entries():
    root = os.path.dirname(os.path.dirname(__file__))
    kb_path = os.path.join(root, "knowledge_base.json")
    with open(kb_path, "r") as f:
        return json.load(f)


def test_retrieve_entries_returns_matches():
    entries = _load_entries()
    results = retrieve_entries("dog walk exercise", entries, k=2)
    assert results
    assert any("walk" in entry["title"].lower() for entry in results)


def test_format_sources_creates_labels():
    entries = _load_entries()
    sources = retrieve_entries("feeding routine", entries, k=1)
    text, meta = format_sources(sources)
    assert "[S1]" in text
    assert meta[0]["label"] == "S1"


def test_fallback_walk_feed_lists_only_cited_kb_order():
    entries = _load_entries()
    wf = _resolve_entries_by_ids(entries, ["kb_walks", "kb_feeding"])
    assert len(wf) == 2
    text, cited = _fallback_answer("Should I feed my dog before or after a walk?", wf)
    assert "[S1]" in text and "[S2]" in text
    assert [e.get("id") for e in cited] == ["kb_walks", "kb_feeding"]


def test_intent_narrowing_feeding_question_drops_unrelated_topics():
    root = os.path.dirname(os.path.dirname(__file__))
    kb_path = os.path.join(root, "knowledge_base.json")
    assistant = RagAssistant(kb_path)
    q = "Any recommended time to feed my pet?"
    r = retrieve_entries(q, assistant.entries, k=3, index=assistant.index)
    ids = [e.get("id") for e in r]
    assert "kb_feeding" in ids
    assert "kb_parasite_prevention" not in ids
    assert "kb_id_recovery" not in ids


def test_intent_narrowing_cat_hydration_prefers_water_and_litter():
    root = os.path.dirname(os.path.dirname(__file__))
    kb_path = os.path.join(root, "knowledge_base.json")
    assistant = RagAssistant(kb_path)
    q = "What is a good daily hydration routine for cats?"
    r = retrieve_entries(q, assistant.entries, k=3, index=assistant.index)
    ids = [e.get("id") for e in r]
    assert "kb_hydration" in ids
    assert "kb_cats_litter" in ids
    assert "kb_feeding" not in ids


def test_intent_narrowing_targets_enrichment_article():
    root = os.path.dirname(os.path.dirname(__file__))
    kb_path = os.path.join(root, "knowledge_base.json")
    assistant = RagAssistant(kb_path)
    q = "Why is enrichment play important for pets?"
    r = retrieve_entries(q, assistant.entries, k=3, index=assistant.index)
    assert [e.get("id") for e in r] == ["kb_enrichment"]


def test_intent_narrowing_targets_rabbit_article():
    root = os.path.dirname(os.path.dirname(__file__))
    kb_path = os.path.join(root, "knowledge_base.json")
    assistant = RagAssistant(kb_path)
    q = "What should rabbits always have access to?"
    r = retrieve_entries(q, assistant.entries, k=3, index=assistant.index)
    assert [e.get("id") for e in r] == ["kb_rabbits"]


def test_intent_narrowing_cat_litter_only():
    root = os.path.dirname(os.path.dirname(__file__))
    kb_path = os.path.join(root, "knowledge_base.json")
    assistant = RagAssistant(kb_path)
    q = "How often should I clean a cat litter box?"
    r = retrieve_entries(q, assistant.entries, k=3, index=assistant.index)
    assert [e.get("id") for e in r] == ["kb_cats_litter"]


def test_heartworm_flea_keeps_parasite_article_without_rx_med_narrowing():
    root = os.path.dirname(os.path.dirname(__file__))
    kb_path = os.path.join(root, "knowledge_base.json")
    assistant = RagAssistant(kb_path)
    q = "What flea and heartworm prevention schedule works for indoor dogs?"
    r = retrieve_entries(q, assistant.entries, k=3, index=assistant.index)
    ids = [e.get("id") for e in r]
    assert "kb_parasite_prevention" in ids
    assert ids[0] == "kb_parasite_prevention"


def test_intent_feed_and_hydration_combines_both_buckets():
    root = os.path.dirname(os.path.dirname(__file__))
    kb_path = os.path.join(root, "knowledge_base.json")
    assistant = RagAssistant(kb_path)
    q = "Should I soak dry food in water before feeding my cat?"
    r = retrieve_entries(q, assistant.entries, k=3, index=assistant.index)
    ids = set(e.get("id") for e in r)
    assert "kb_feeding" in ids
    assert "kb_hydration" in ids


def test_validate_citations_accepts_valid_labels():
    assert validate_citations("Answer with [S1]", 1) is True
    assert validate_citations("Answer with [S2]", 1) is False
