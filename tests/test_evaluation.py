import json

import httpx
import pytest

from app.domain.models import RetrievedChunk
from app.evaluation.dataset import load_golden_cases
from app.evaluation.metrics import expected_fact_coverage, faithfulness_proxy, source_hint_metrics, source_hint_mrr
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
    assert source_hint_mrr(chunks, ["release.md"]) == 1.0
    assert source_hint_mrr(chunks, ["other.md"]) == 0.5
    assert source_hint_mrr(chunks, ["missing.md"]) == 0.0
    assert expected_fact_coverage("The release guide is in docs/release.md.", ["The release guide is in docs/release.md"]) == 1.0
    assert faithfulness_proxy("The release guide is in docs/release.md.", [chunk.text for chunk in chunks], ["The release guide is in docs/release.md"]) == 1.0
    assert expected_fact_coverage("Water transports minerals.", ["Water transports minerals through the plant."]) > 0.5


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
        "source_mrr": 1.0,
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
        answer = await adapter.answer_function(5)(GoldenCase("case", "question", ("fact",), chunking_profile="experiment-small"))

    assert chunks[0].chunk_id == "chunk"
    assert chunks[0].text == "Context"
    assert answer == "Answer"


@pytest.mark.asyncio
async def test_live_adapter_preserves_explicit_model_and_chunking_scope():
    requests = []

    def responder(request):
        payload = json.loads(request.content)
        requests.append(payload)
        assert payload["workspace_id"] == "isolated"
        assert payload["model_profile"] == "frozen-model"
        assert payload["chunking_profile"] == "fixed-chunker"
        return httpx.Response(200, json={"answer": "scoped answer", "sources": []})

    async with httpx.AsyncClient(base_url="http://test", transport=httpx.MockTransport(responder)) as client:
        adapter = LiveApiBenchmarkClient(client, "isolated", "frozen-model", "fixed-chunker")
        await adapter.retrieve("question")
        answer = await adapter.answer_function(5)(GoldenCase("case", "question", ("fact",)))
    assert answer == "scoped answer" and len(requests) == 1


@pytest.mark.parametrize("extra", [
    {"answerable": False}, {"answerable": "false", "document_id": "a" * 64},
    {"answerable": 0, "document_id": "a" * 64},
    {"answerable": False, "document_id": "bad"},
    {"answerable": True, "document_id": "a" * 64},
    {"answerable": False, "document_id": "a" * 64, "expected_facts": ["fact"]},
])
def test_negative_dataset_rejects_inconsistent_scope_and_facts(extra):
    with pytest.raises(ValueError):
        GoldenCase.from_dict({"id": "neg", "question": "Absent?", "expected_facts": [], **extra}, 1)


@pytest.mark.asyncio
@pytest.mark.parametrize("answer,score,failed", [
    ("I don't know based on the indexed documents.", 1.0, False),
    (" I don't have enough information in the indexed documents to answer this question.\n", 1.0, False),
    ("I don't know based on the indexed documents. It costs $10.", 0.0, False),
    ("No evidence was found.", 0.0, False), ("", None, True), (None, None, True),
])
async def test_negative_abstention_is_separate_strict_and_not_vacuous(answer, score, failed):
    class Retriever:
        async def retrieve(self, question, **kwargs):
            assert kwargs["document_id"] == "a" * 64
            return []

    async def respond(case):
        return answer

    case = GoldenCase("neg", "Absent?", (), document_id="a" * 64, answerable=False)
    result = await BenchmarkRunner(Retriever(), respond).run_case(case)
    assert result.metrics["abstained"] == score
    assert result.metrics["answer_relevance"] is None
    assert result.metrics["faithfulness"] is None
    assert (result.failure_stage is not None) == failed


def scoped_openapi():
    return {"paths": {"/chat": {"post": {"requestBody": {"content": {"application/json": {
        "schema": {"$ref": "#/components/schemas/ChatRequest"}}}}}}},
        "components": {"schemas": {"ChatRequest": {"properties": {"document_id": {}}}}}}


@pytest.mark.asyncio
async def test_scoped_adapter_checks_capability_keys_cache_and_records_both_probes():
    requests = []

    def responder(request):
        if request.method == "GET":
            return httpx.Response(200, json=scoped_openapi())
        payload = json.loads(request.content)
        requests.append(payload)
        return httpx.Response(200, json={"answer": payload["document_id"] + str(len(requests)), "sources": [], "session_id": None, "grounded": False})

    async with httpx.AsyncClient(base_url="http://test", transport=httpx.MockTransport(responder)) as client:
        api = LiveApiBenchmarkClient(client)
        for doc in ["a" * 64, "b" * 64]:
            case = GoldenCase(doc, "Same?", (), document_id=doc, answerable=False)
            result = await BenchmarkRunner(api, api.answer_function(5)).run_case(case)
            assert result.answer == doc + str(len(requests))
            assert result.failure_stage is None
        assert len(api.response_records) == len(requests) == 4
        assert [r["request"]["document_id"] for r in api.response_records] == ["a" * 64] * 2 + ["b" * 64] * 2


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", ["old_server", "leaked_source", "session", "empty_answer", "transport"])
async def test_negative_adapter_cannot_pass_unsupported_scope_or_bad_responses(failure):
    def responder(request):
        if request.method == "GET":
            schema = scoped_openapi()
            if failure == "old_server":
                schema["components"]["schemas"]["ChatRequest"]["properties"].clear()
            return httpx.Response(200, json=schema)
        if failure == "transport":
            return httpx.Response(503)
        return httpx.Response(200, json={
            "answer": "" if failure == "empty_answer" else "I don't know based on the indexed documents.",
            "sources": [{"doc_id": "b" * 64}] if failure == "leaked_source" else [],
            "session_id": "old" if failure == "session" else None,
            "grounded": False,
        })

    async with httpx.AsyncClient(base_url="http://test", transport=httpx.MockTransport(responder)) as client:
        api = LiveApiBenchmarkClient(client)
        case = GoldenCase("neg", "Absent?", (), document_id="a" * 64, answerable=False)
        result = await BenchmarkRunner(api, api.answer_function(5)).run_case(case)
    assert result.failure_stage is not None
    assert result.answer is None
    assert result.metrics.get("abstained") is None
