from __future__ import annotations

import re
from collections.abc import Iterable

from app.domain.models import RetrievedChunk


def _normalise(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().casefold()


def _content_tokens(value: str) -> set[str]:
    stop_words = {"a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "in", "is", "it", "of", "or", "that", "the", "to", "with"}
    return {token for token in re.findall(r"[\w-]+", _normalise(value)) if len(token) > 2 and token not in stop_words}


def expected_fact_coverage(answer: str, expected_facts: Iterable[str]) -> float:
    """Deterministic proxy for answer relevance, based on verified facts."""
    facts = [_normalise(fact) for fact in expected_facts]
    if not facts:
        return 1.0
    answer_text = _normalise(answer)
    answer_tokens = _content_tokens(answer)
    scores = []
    for fact in facts:
        if fact in answer_text:
            scores.append(1.0)
            continue
        fact_tokens = _content_tokens(fact)
        scores.append(len(fact_tokens & answer_tokens) / len(fact_tokens) if fact_tokens else 0.0)
    return sum(scores) / len(scores)


def source_hint_metrics(chunks: Iterable[RetrievedChunk], source_hints: Iterable[str]) -> tuple[float | None, float | None]:
    """Return deterministic context precision/recall when source hints exist."""
    hints = [_normalise(hint) for hint in source_hints]
    results = list(chunks)
    if not hints:
        return None, None
    matched_results = [
        chunk for chunk in results
        if any(hint in _normalise(chunk.source_path) or hint in _normalise(chunk.doc_id) for hint in hints)
    ]
    matched_hints = {
        hint for hint in hints
        if any(hint in _normalise(chunk.source_path) or hint in _normalise(chunk.doc_id) for chunk in results)
    }
    precision = len(matched_results) / len(results) if results else 0.0
    recall = len(matched_hints) / len(hints)
    return precision, recall


def faithfulness_proxy(answer: str, contexts: Iterable[str], expected_facts: Iterable[str]) -> float:
    """Score expected answer facts that are also present in retrieved context.

    This deterministic proxy is intentionally not an LLM-as-judge metric. A
    later RAGAS/DeepEval adapter may provide semantic judging without changing
    the result format.
    """
    answer_tokens = _content_tokens(answer)
    context_tokens = _content_tokens(" ".join(contexts))
    facts = [_normalise(fact) for fact in expected_facts]
    answer_facts = []
    for fact in facts:
        fact_tokens = _content_tokens(fact)
        if fact_tokens and fact_tokens & answer_tokens:
            answer_facts.append(fact_tokens)
    if not answer_facts:
        return 0.0
    return sum(len(fact & context_tokens) / len(fact) for fact in answer_facts) / len(answer_facts)
