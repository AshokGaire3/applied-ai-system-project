import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from rag_engine import RagAssistant, _fallback_answer, load_knowledge_base, retrieve_entries


def _repo_root() -> str:
    return os.path.dirname(os.path.dirname(__file__))


def _load_eval_set():
    with open(os.path.join(_repo_root(), "tests", "rag_eval_set.json"), "r") as f:
        return json.load(f)


def test_rag_eval_retrieval_at_3_and_coverage():
    kb_path = os.path.join(_repo_root(), "knowledge_base.json")
    entries = load_knowledge_base(kb_path)
    assistant = RagAssistant(kb_path, k=3)
    cases = _load_eval_set()

    in_scope_cases = [c for c in cases if c["expected_kb_ids"]]
    hits = 0
    covered_ids = set()

    for case in in_scope_cases:
        sources = retrieve_entries(case["question"], entries, k=3, index=assistant.index)
        retrieved_ids = {entry.get("id") for entry in sources}
        expected = set(case["expected_kb_ids"])
        if expected.issubset(retrieved_ids):
            hits += 1
        covered_ids.update(expected.intersection(retrieved_ids))

    retrieval_at_3 = hits / len(in_scope_cases)
    assert retrieval_at_3 >= 0.90

    expected_all = {eid for case in in_scope_cases for eid in case["expected_kb_ids"]}
    assert covered_ids == expected_all


def test_rag_eval_fallback_determinism_and_token_expectations():
    kb_path = os.path.join(_repo_root(), "knowledge_base.json")
    entries = load_knowledge_base(kb_path)
    assistant = RagAssistant(kb_path, k=3)
    cases = _load_eval_set()

    for case in cases:
        expected_ids = case.get("expected_kb_ids", [])
        if not expected_ids:
            continue
        sources = retrieve_entries(case["question"], entries, k=3, index=assistant.index)
        a = _fallback_answer(case["question"], sources)
        b = _fallback_answer(case["question"], sources)
        assert a == b
        for token in case.get("must_contain_any", []):
            assert token.lower() in a.lower()


def test_rag_eval_oos_refusal_rate():
    kb_path = os.path.join(_repo_root(), "knowledge_base.json")
    assistant = RagAssistant(kb_path, k=3)
    cases = _load_eval_set()

    oos_cases = [c for c in cases if not c.get("expected_kb_ids")]
    no_source_count = 0
    for case in oos_cases:
        result = assistant.answer(case["question"])
        if result["mode"] == "no_sources":
            no_source_count += 1

    refusal_rate = no_source_count / len(oos_cases)
    assert refusal_rate >= 0.80
