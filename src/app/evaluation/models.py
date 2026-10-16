from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any
import re


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

    document_id: str | None = None
    answerable: bool = True
    negative_scope: str | None = None

    def __post_init__(self) -> None:
        if type(self.answerable) is not bool:
            raise ValueError("answerable must be a boolean")
        if self.document_id is not None and (not isinstance(self.document_id, str) or not re.fullmatch(r"[0-9a-f]{64}", self.document_id)):
            raise ValueError("Invalid document_id")
        if self.answerable and not self.expected_facts:
            raise ValueError("Positive cases require expected facts")
        if not self.answerable and (self.expected_facts or self.document_id is None):
            raise ValueError("Negative cases require empty facts and document scope")
        if self.negative_scope is not None and (not isinstance(self.negative_scope, str) or not self.negative_scope.strip()):
            raise ValueError("Invalid negative_scope")

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
        if not isinstance(facts, list) or not all(isinstance(fact, str) and fact.strip() for fact in facts):
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
            document_id=value.get("document_id"),
            answerable=value.get("answerable", True),
            negative_scope=value.get("negative_scope"),
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

    document_id: str | None = None
    answerable: bool = True

    response_indices: list[int] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {**asdict(self), "failure_stage": self.failure_stage.value if self.failure_stage else None}


@dataclass
class BenchmarkReport:
    cases: list[CaseResult] = field(default_factory=list)
    configuration: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "configuration": self.configuration,
            "summary": {
                "positive_cases": sum(c.answerable for c in self.cases),
                "negative_cases": sum(not c.answerable for c in self.cases),
                "negative_failures": sum(not c.answerable and c.failure_stage is not None for c in self.cases),
                "negative_scored": sum(not c.answerable and c.metrics.get("abstained") is not None for c in self.cases),
                "negative_exact_abstentions": sum(not c.answerable and c.metrics.get("abstained") == 1.0 for c in self.cases),
            },
            "cases": [case.to_dict() for case in self.cases],
        }
