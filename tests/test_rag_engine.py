import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from rag_engine import retrieve_entries, format_sources, validate_citations


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


def test_validate_citations_accepts_valid_labels():
    assert validate_citations("Answer with [S1]", 1) is True
    assert validate_citations("Answer with [S2]", 1) is False
