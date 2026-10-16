"""Derive scoped benchmark cases from frozen references and actual index availability."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
from app.chunkers.ids import make_doc_id
from app.loaders.pdf_extraction import ExtractionOptions
from compare_pdf_parsers import load_manifest, validate_output


def prepare(manifest_path: Path, ingestion_paths: list[Path], output: Path, *, assigned_document: bool = False):
    manifest_path = manifest_path.resolve()
    manifest_hash = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    _, documents = load_manifest(manifest_path, ExtractionOptions())
    reports = [json.loads(p.read_text(encoding="utf8")) for p in ingestion_paths]
    if not reports or any(r.get("status") != "indexed" or r.get("manifest_sha256") != manifest_hash for r in reports):
        raise ValueError("Matching successful ingestion reports required")
    if len({(r["chunking_profile"], r["model_profile"]) for r in reports}) != 1:
        raise ValueError("Paired ingestion profiles must be identical")
    available_sets = [{d["doc_id"] for d in r["ingestion"]["documents"]
                       if d["chunks_indexed"] > 0} for r in reports]
    available = set.intersection(*available_sets)
    review_path = PROJECT_ROOT / "evaluation/pdf_parsers/corpus/COLD_CASE_REVIEW.json"
    review = json.loads(review_path.read_text(encoding="utf8"))
    exclusions = {}
    for case in review["cases"]:
        grades = list(case.get("facts_in_reference_order", {}).values())
        if not grades:
            continue
        excluded = [i for i in range(case["fact_count"]) if all(g[i] == "X" for g in grades)]
        if excluded:
            exclusions[case["id"]] = {"indexes": excluded, "reason": case["review_note"]}
    cases, coverage = [], []
    for document in documents:
        entry = document["manifest"]
        source = str(document["source"].resolve())
        doc_id = make_doc_id(source)
        for reference in document["references"]:
            status = "eligible"
            if not reference["answerable"] and not assigned_document:
                status = "deferred_assigned_document_negative_scope"
            elif doc_id not in available:
                status = "unavailable_indexed_document"
            excluded = exclusions.get(reference["id"], {}).get("indexes", [])
            facts = [f for i, f in enumerate(reference["expected_facts"]) if i not in excluded]
            coverage.append({"id": reference["id"], "document_id": entry["id"], "doc_id": doc_id,
                             "answerable": reference["answerable"], "status": status,
                             "excluded_fact_indexes": excluded})
            if status == "eligible":
                if reference["answerable"] and not facts:
                    raise ValueError("Eligible answerable case has no valid facts")
                case = {"id": reference["id"], "question": reference["question"],
                              "expected_facts": facts, "expected_source_hints": [source],
                              "chunking_profile": reports[0]["chunking_profile"]}
                if assigned_document:
                    case.update(document_id=doc_id, answerable=reference["answerable"])
                    if "negative_scope" in reference:
                        case["negative_scope"] = reference["negative_scope"]
                cases.append(case)
    if not cases:
        raise ValueError("No eligible indexed cases")
    output = output.resolve()
    validate_output(output)
    output.mkdir(parents=True, exist_ok=False)
    dataset = output / "cases.jsonl"
    dataset.write_text("".join(json.dumps(c, ensure_ascii=False) + "\n" for c in cases), encoding="utf8")
    availability = {"manifest_sha256": manifest_hash, "dataset_sha256": hashlib.sha256(dataset.read_bytes()).hexdigest(),
                    "ingestion_reports": [{"path": str(p.resolve()), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
                                          for p in ingestion_paths],
                    "reference_review_sha256": hashlib.sha256(review_path.read_bytes()).hexdigest(),
                    "excluded_reference_facts": {k: v for k, v in exclusions.items()
                                                 if any(c["id"] == k for c in coverage)},
                    "scope": "assigned_document" if assigned_document else "workspace_positive_only",
                    "positive_cases_eligible": sum(c.get("answerable", True) for c in cases),
                    "negative_cases_eligible": sum(not c.get("answerable", True) for c in cases),
                    "cases_total": len(coverage), "cases_eligible": len(cases), "cases": coverage,
                    "limits": ["Questions and frozen references remain unchanged; derived facts omit only already recorded reference defects",
                               "Scoped mode requires an API advertising document_id; negatives remain deferred in workspace mode",
                               "Negative cases are not positive facts; unavailable documents are not successful abstentions",
                               "Reports with zero chunks, including unchanged skips without positive counts, do not establish availability",
                               "Existing fact/faithfulness metrics are token proxies, not independently verified answer scores"]}
    (output / "availability.json").write_text(json.dumps(availability, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    return dataset, availability


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--ingestion-reports", type=Path, nargs="+", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--assigned-document", action="store_true", help="Include indexed positives/negatives with enforced document scope")
    args = parser.parse_args(argv)
    try:
        dataset, report = prepare(args.manifest, args.ingestion_reports, args.output_dir, assigned_document=args.assigned_document)
        print(f"Prepared {report['cases_eligible']}/{report['cases_total']} cases: {dataset}")
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"Benchmark preparation failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
