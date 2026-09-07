from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class FailureStage(StrEnum):
    ingestion = "ingestion"
    retrieval = "retrieval"
    rerank = "rerank"
    prompt = "prompt"
    generation = "generation"


@dataclass(frozen=True)
class GoldenCase:
    case_id: str
    question: str
    expected_facts: tuple[str, ...]
    expected_source_hints: tuple[str, ...] = ()
    workspace_id: str | None = None
    chunking_profile: str | None = None

    @classmethod
    def from_dict(cls, value: dict[str, Any], line_number: int) -> "GoldenCase":
        required = ("id", "question", "expected_facts")
        missing = [key for key in required if key not in value]
        if missing:
            raise ValueError(f"Golden case line {line_number} is missing: {', '.join(missing)}")
        case_id = value["id"]
        question = value["question"]
        facts = value["expected_facts"]
        hints = value.get("expected_source_hints", [])
        if not isinstance(case_id, str) or not case_id.strip():
            raise ValueError(f"Golden case line {line_number} has an invalid id")
        if not isinstance(question, str) or not question.strip():
            raise ValueError(f"Golden case {case_id!r} has an invalid question")
        if not isinstance(facts, list) or not facts or not all(isinstance(fact, str) and fact.strip() for fact in facts):
            raise ValueError(f"Golden case {case_id!r} requires one or more expected_facts")
        if not isinstance(hints, list) or not all(isinstance(hint, str) and hint.strip() for hint in hints):
            raise ValueError(f"Golden case {case_id!r} has invalid expected_source_hints")
        return cls(
            case_id=case_id,
            question=question,
            expected_facts=tuple(facts),
            expected_source_hints=tuple(hints),
            workspace_id=value.get("workspace_id"),
            chunking_profile=value.get("chunking_profile"),
        )


@dataclass
class CaseResult:
    case_id: str
    retrieved_chunk_ids: list[str]
    answer: str | None
    latency_ms: float
    metrics: dict[str, float | None]
    deterministic: bool
    failure_stage: FailureStage | None = None
    failure_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {**asdict(self), "failure_stage": self.failure_stage.value if self.failure_stage else None}


@dataclass
class BenchmarkReport:
    cases: list[CaseResult] = field(default_factory=list)
    configuration: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "configuration": self.configuration,
            "cases": [case.to_dict() for case in self.cases],
        }
