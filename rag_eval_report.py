import json
from pathlib import Path

from rag_engine import RagAssistant, _fallback_answer, load_knowledge_base, retrieve_entries


def _load_eval_set(repo_root: Path) -> list[dict]:
    with open(repo_root / "tests" / "rag_eval_set.json", "r", encoding="utf-8") as f:
        return json.load(f)


def main() -> None:
    repo_root = Path(__file__).resolve().parent
    kb_path = repo_root / "knowledge_base.json"
    entries = load_knowledge_base(str(kb_path))
    assistant = RagAssistant(str(kb_path), k=3)
    cases = _load_eval_set(repo_root)

    in_scope = [c for c in cases if c.get("expected_kb_ids")]
    oos = [c for c in cases if not c.get("expected_kb_ids")]

    retrieval_hits = 0
    token_hits = 0
    no_source_hits = 0

    for case in in_scope:
        sources = retrieve_entries(case["question"], entries, k=3, index=assistant.index)
        retrieved_ids = {entry.get("id") for entry in sources}
        expected_ids = set(case["expected_kb_ids"])
        if expected_ids.issubset(retrieved_ids):
            retrieval_hits += 1

        fallback_answer, _ = _fallback_answer(case["question"], sources)
        needs = case.get("must_contain_any", [])
        if not needs or all(token.lower() in fallback_answer.lower() for token in needs):
            token_hits += 1

    for case in oos:
        result = assistant.answer(case["question"])
        if result.get("mode") == "no_sources":
            no_source_hits += 1

    retrieval_at_3 = retrieval_hits / len(in_scope) if in_scope else 1.0
    fallback_token_rate = token_hits / len(in_scope) if in_scope else 1.0
    oos_refusal_rate = no_source_hits / len(oos) if oos else 1.0

    retrieval_pass = retrieval_at_3 >= 0.90
    oos_pass = oos_refusal_rate >= 0.80
    overall_pass = retrieval_pass and oos_pass

    print("PawPal+ RAG Evaluation Report")
    print("=" * 30)
    print(f"In-scope cases: {len(in_scope)}")
    print(f"Out-of-scope cases: {len(oos)}")
    print(f"Retrieval@3: {retrieval_at_3:.2f}  ({retrieval_hits}/{len(in_scope)})")
    print(f"Fallback token coverage: {fallback_token_rate:.2f}  ({token_hits}/{len(in_scope)})")
    print(f"OOS refusal rate: {oos_refusal_rate:.2f}  ({no_source_hits}/{len(oos)})")
    print(f"Threshold checks: retrieval>=0.90={retrieval_pass}, oos>=0.80={oos_pass}")
    print(f"Overall: {'PASS' if overall_pass else 'FAIL'}")


if __name__ == "__main__":
    main()
