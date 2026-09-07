from __future__ import annotations

import json
from pathlib import Path

from app.evaluation.models import GoldenCase


def load_golden_cases(path: str | Path) -> list[GoldenCase]:
    """Load a non-empty, duplicate-free JSONL golden set."""
    source = Path(path)
    cases: list[GoldenCase] = []
    case_ids: set[str] = set()
    for line_number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON on golden case line {line_number}") from exc
        if not isinstance(raw, dict):
            raise ValueError(f"Golden case line {line_number} must be a JSON object")
        case = GoldenCase.from_dict(raw, line_number)
        if case.case_id in case_ids:
            raise ValueError(f"Duplicate golden case id: {case.case_id}")
        case_ids.add(case.case_id)
        cases.append(case)
    if not cases:
        raise ValueError("Golden dataset must contain at least one case")
    return cases
