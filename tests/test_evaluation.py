import json

import httpx
import pytest

from app.domain.models import RetrievedChunk
from app.evaluation.dataset import load_golden_cases
from app.evaluation.metrics import expected_fact_coverage, faithfulness_proxy, source_hint_metrics
from app.evaluation.models import GoldenCase
from app.evaluation.runner import BenchmarkRunner, write_report
from app.evaluation.live_api import LiveApiBenchmarkClient


def test_load_golden_cases_validates_and_loads_jsonl(tmp_path):
    dataset = tmp_path / "golden.jsonl"
    dataset.write_text(json.dumps({
        "id": "one", "question": "Where is the release guide?",
        "expected_facts": ["The release guide is in docs/release.md"],
        "expected_source_hints": ["release.md"],
    }) + "\n", encoding="utf-8")

    [case] = load_golden_cases(dataset)

    assert case.case_id == "one"
    assert case.expected_source_hints == ("release.md",)


def test_metrics_are_deterministic_and_source_hint_aware():
    chunks = [
        RetrievedChunk("one", "doc-one", "docs/release.md", "The release guide is in docs/release.md", 0.9),
        RetrievedChunk("two", "doc-two", "docs/other.md", "Other context", 0.7),
    ]

    precision, recall = source_hint_metrics(chunks, ["release.md"])

    assert precision == 0.5
    assert recall == 1.0
    assert expected_fact_coverage("The release guide is in docs/release.md.", ["The release guide is in docs/release.md"]) == 1.0
    assert faithfulness_proxy("The release guide is in docs/release.md.", [chunk.text for chunk in chunks], ["The release guide is in docs/release.md"]) == 1.0


@pytest.mark.asyncio
async def test_runner_reports_determinism_metrics_and_generation_failures(tmp_path):
    chunk = RetrievedChunk("one", "doc-one", "docs/release.md", "The release guide is in docs/release.md", 0.9)

    class MockRetriever:
        async def retrieve(self, *_args, **_kwargs):
            return [chunk]

    case = GoldenCase("one", "Where is the release guide?", ("The release guide is in docs/release.md",), ("release.md",))

    async def answer(_: GoldenCase) -> str:
        return "The release guide is in docs/release.md."

    report = await BenchmarkRunner(MockRetriever(), answer).run([case], {"chunking_profile": "default"})

    result = report.cases[0]
    assert result.deterministic is True
    assert result.metrics == {
        "context_precision": 1.0,
        "context_recall": 1.0,
        "answer_relevance": 1.0,
        "faithfulness": 1.0,
    }
    assert report.configuration["chunking_profile"] == "default"
    artifact = write_report(report, tmp_path / "artifacts" / "run.json")
    assert json.loads(artifact.read_text(encoding="utf-8"))["cases"][0]["deterministic"] is True


@pytest.mark.asyncio
async def test_live_api_adapter_maps_chat_sources_without_network():
    def responder(request):
        assert request.url.path == "/chat"
        assert json.loads(request.content)["chunking_profile"] == "experiment-small"
        return httpx.Response(200, json={"answer": "Answer", "sources": [{
            "chunk_id": "chunk", "doc_id": "doc", "source_path": "docs/guide.md", "score": 0.8, "snippet": "Context",
        }]})

    transport = httpx.MockTransport(responder)
    async with httpx.AsyncClient(base_url="http://test", transport=transport) as client:
        adapter = LiveApiBenchmarkClient(client)
        chunks = await adapter.retrieve("question", chunking_profile="experiment-small")

    assert chunks[0].chunk_id == "chunk"
    assert chunks[0].text == "Context"
