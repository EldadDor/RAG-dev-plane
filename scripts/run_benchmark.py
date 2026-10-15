"""Run verified golden cases against an already-running local RAG API."""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
import sys

import httpx

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from app.evaluation.dataset import load_golden_cases  # noqa: E402
from app.evaluation.live_api import LiveApiBenchmarkClient  # noqa: E402
from app.evaluation.runner import BenchmarkRunner, write_report  # noqa: E402


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", required=True, help="Path to verified golden-case JSONL")
    parser.add_argument("--output", required=True, help="Path for the JSON result artifact")
    parser.add_argument("--api-url", default="http://localhost:8000", help="Running API base URL")
    parser.add_argument("--workspace-id", default=None)
    parser.add_argument("--model-profile", default=None)
    parser.add_argument("--chunking-profile", default=None)
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()
    if Path(args.output).exists():
        parser.error("Refusing to overwrite an existing benchmark artifact")

    cases = load_golden_cases(args.dataset)
    async with httpx.AsyncClient(base_url=args.api_url, timeout=120) as http_client:
        api = LiveApiBenchmarkClient(http_client, workspace_id=args.workspace_id,
                                     model_profile=args.model_profile, chunking_profile=args.chunking_profile)
        report = await BenchmarkRunner(api, api.answer_function(args.top_k)).run(
            cases,
            configuration={"api_url": args.api_url, "workspace_id": args.workspace_id,
                           "model_profile": args.model_profile, "chunking_profile": args.chunking_profile},
            top_k=args.top_k,
        )
    output = write_report(report, args.output)
    print(f"Wrote {len(report.cases)} benchmark cases to {output}")


if __name__ == "__main__":
    asyncio.run(main())
