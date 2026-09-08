from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from pathlib import Path
from time import perf_counter
from typing import Protocol

from app.domain.models import RetrievedChunk
from app.evaluation.metrics import expected_fact_coverage, faithfulness_proxy, source_hint_metrics
from app.evaluation.models import BenchmarkReport, CaseResult, FailureStage, GoldenCase


class Retriever(Protocol):
    async def retrieve(
        self, question: str, top_k: int | None = None, workspace_id: str | None = None,
        chunking_profile: str | None = None,
    ) -> list[RetrievedChunk]: ...


AnswerFunction = Callable[[GoldenCase], Awaitable[str]]


class BenchmarkRunner:
    """Evaluate retrieval determinism and optional generated answers.

    The runner's dependencies are deliberately narrow so the offline smoke lane
    can use mocks and a live adapter can be added without changing metrics or
    artifact shape.
    """

    def __init__(self, retriever: Retriever, answer: AnswerFunction | None = None) -> None:
        self._retriever = retriever
        self._answer = answer

    async def run_case(self, case: GoldenCase, top_k: int = 5) -> CaseResult:
        started = perf_counter()
        try:
            first = await self._retriever.retrieve(
                case.question, top_k=top_k, workspace_id=case.workspace_id, chunking_profile=case.chunking_profile,
            )
            second = await self._retriever.retrieve(
                case.question, top_k=top_k, workspace_id=case.workspace_id, chunking_profile=case.chunking_profile,
            )
        except Exception as exc:
            return CaseResult(
                case_id=case.case_id, retrieved_chunk_ids=[], answer=None,
                latency_ms=(perf_counter() - started) * 1000, metrics={}, deterministic=False,
                failure_stage=FailureStage.retrieval, failure_message=str(exc),
            )

        chunk_ids = [chunk.chunk_id for chunk in first]
        deterministic = chunk_ids == [chunk.chunk_id for chunk in second]
        precision, recall = source_hint_metrics(first, case.expected_source_hints)
        answer: str | None = None
        failure_stage: FailureStage | None = None
        failure_message: str | None = None
        if self._answer is not None:
            try:
                answer = await self._answer(case)
            except Exception as exc:
                failure_stage = FailureStage.generation
                failure_message = str(exc)

        metrics: dict[str, float | None] = {
            "context_precision": precision,
            "context_recall": recall,
            "answer_relevance": expected_fact_coverage(answer, case.expected_facts) if answer is not None else None,
            "faithfulness": faithfulness_proxy(answer, [chunk.text for chunk in first], case.expected_facts) if answer is not None else None,
        }
        if answer is not None and metrics["answer_relevance"] == 0.0 and first:
            failure_stage = failure_stage or FailureStage.generation
            failure_message = failure_message or "Answer did not cover any verified expected fact despite retrieved context."
        return CaseResult(
            case_id=case.case_id, retrieved_chunk_ids=chunk_ids, answer=answer,
            latency_ms=(perf_counter() - started) * 1000, metrics=metrics, deterministic=deterministic,
            failure_stage=failure_stage, failure_message=failure_message,
        )

    async def run(self, cases: list[GoldenCase], configuration: dict[str, object], top_k: int = 5) -> BenchmarkReport:
        report = BenchmarkReport(configuration={**configuration, "top_k": top_k})
        for case in cases:
            report.cases.append(await self.run_case(case, top_k=top_k))
        return report


def write_report(report: BenchmarkReport, path: str | Path) -> Path:
    """Write a portable JSON artifact for comparison with a later run."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return destination
