"""Extraction-only, offline PDF comparison. Never indexes or calls RAG providers."""

from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
import math
import multiprocessing
import os
from pathlib import Path
import platform
import re
import socket
import sys
import time

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from app.loaders.pdf_extraction import ExtractionError, ExtractionOptions, create_parser, read_source  # noqa: E402


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _deny_network(*args, **kwargs):
    raise ExtractionError("Network access is disabled in extraction workers")


def _offline_worker() -> None:
    os.environ.update({"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1",
                       "HF_DATASETS_OFFLINE": "1", "OMP_NUM_THREADS": "1", "OMP_THREAD_LIMIT": "1"})
    socket.create_connection = _deny_network
    socket.socket.connect = _deny_network
    socket.socket.connect_ex = _deny_network
    socket.socket.sendto = _deny_network


def process_peak_memory(pid: int) -> tuple[int | None, str]:
    """Windows process lifetime peak working set. Other platforms are unavailable."""
    if sys.platform != "win32":
        return None, "unavailable_on_this_platform"
    import ctypes
    from ctypes import wintypes

    class Counters(ctypes.Structure):
        _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD)] + [
            (name, ctypes.c_size_t) for name in (
                "PeakWorkingSetSize", "WorkingSetSize", "QuotaPeakPagedPoolUsage",
                "QuotaPagedPoolUsage", "QuotaPeakNonPagedPoolUsage", "QuotaNonPagedPoolUsage",
                "PagefileUsage", "PeakPagefileUsage",
            )
        ]

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
    handle = kernel.OpenProcess(0x0400 | 0x0010, False, pid)
    if not handle:
        return None, "GetProcessMemoryInfo_unavailable"
    try:
        counters = Counters()
        counters.cb = ctypes.sizeof(counters)
        if not psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb):
            return None, "GetProcessMemoryInfo_unavailable"
        return counters.PeakWorkingSetSize, "windows_process_lifetime_peak_working_set_bytes"
    finally:
        kernel.CloseHandle(handle)


def _worker(connection, engine: str, options: ExtractionOptions, ready=None) -> None:
    _offline_worker()
    if options.ocr and options.ocr_engine == "tesseract" and options.ocr_models_path:
        # Docling's language-discovery subprocess omits --tessdata-dir.
        os.environ["TESSDATA_PREFIX"] = str(Path(options.ocr_models_path).resolve())
    if ready is not None:
        ready.wait()
    try:
        start = time.perf_counter()
        parser = create_parser(engine, options)
        connection.send({"initialization_seconds": time.perf_counter() - start})
        while True:
            request = connection.recv()
            if request is None:
                break
            source, output, document_id, source_hash = request
            start = time.perf_counter()
            result = parser.extract(Path(source), options)
            elapsed = time.perf_counter() - start
            if result.source_sha256 != source_hash:
                raise ExtractionError("Extraction source hash differs from frozen input")
            folder = Path(output)
            folder.mkdir()
            write_json(folder / "normalized.json", result.normalized(document_id))
            write_json(folder / "raw.json", result.raw)
            (folder / "text.txt").write_text(result.assembled_text, encoding="utf-8")
            if result.assets:
                (folder / "assets").mkdir()
                for asset in result.assets:
                    (folder / "assets" / f"{asset.sha256}.png").write_bytes(asset.content)
            peak, method = process_peak_memory(os.getpid())
            connection.send({"status": result.status, "extraction_seconds": elapsed,
                             "peak_memory_bytes": peak, "memory_method": method,
                             "warnings": result.warnings, "unsupported": result.unsupported,
                             "pages": result.page_count, "blocks": len(result.blocks),
                             "versions": result.versions, "artifact": folder.name})
    except Exception as exc:
        connection.send({"status": "failed", "error": f"{type(exc).__name__}: {exc}"})
    finally:
        connection.close()


class WindowsWorkerJob:
    """Bound native descendants by private commit; closing kills the entire job."""

    def __init__(self, pid: int, memory_limit: int):
        if sys.platform != "win32":
            raise ExtractionError("Native OCR process-tree enforcement requires Windows")
        import ctypes
        from ctypes import wintypes

        class BasicLimits(ctypes.Structure):
            _fields_ = [("ProcessTime", ctypes.c_longlong), ("JobTime", ctypes.c_longlong),
                        ("Flags", wintypes.DWORD), ("MinWorkingSet", ctypes.c_size_t),
                        ("MaxWorkingSet", ctypes.c_size_t), ("ActiveLimit", wintypes.DWORD),
                        ("Affinity", ctypes.c_size_t), ("Priority", wintypes.DWORD),
                        ("Scheduling", wintypes.DWORD)]

        class IoCounters(ctypes.Structure):
            _fields_ = [(name, ctypes.c_ulonglong) for name in
                        ("ReadCount", "WriteCount", "OtherCount", "ReadBytes", "WriteBytes", "OtherBytes")]

        class ExtendedLimits(ctypes.Structure):
            _fields_ = [("Basic", BasicLimits), ("Io", IoCounters),
                        ("ProcessLimit", ctypes.c_size_t), ("JobLimit", ctypes.c_size_t),
                        ("ProcessPeak", ctypes.c_size_t), ("JobPeak", ctypes.c_size_t)]

        self.ctypes = ctypes
        self.info_type = ExtendedLimits
        self.kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        signatures = {
            "CreateJobObjectW": ([wintypes.LPVOID, wintypes.LPCWSTR], wintypes.HANDLE),
            "SetInformationJobObject": ([wintypes.HANDLE, ctypes.c_int, wintypes.LPVOID, wintypes.DWORD], wintypes.BOOL),
            "QueryInformationJobObject": ([wintypes.HANDLE, ctypes.c_int, wintypes.LPVOID, wintypes.DWORD, wintypes.LPVOID], wintypes.BOOL),
            "OpenProcess": ([wintypes.DWORD, wintypes.BOOL, wintypes.DWORD], wintypes.HANDLE),
            "AssignProcessToJobObject": ([wintypes.HANDLE, wintypes.HANDLE], wintypes.BOOL),
            "TerminateJobObject": ([wintypes.HANDLE, wintypes.UINT], wintypes.BOOL),
            "CloseHandle": ([wintypes.HANDLE], wintypes.BOOL),
        }
        for name, (args, result) in signatures.items():
            method = getattr(self.kernel, name)
            method.argtypes, method.restype = args, result
        self.handle = self.kernel.CreateJobObjectW(None, None)
        if not self.handle:
            raise ctypes.WinError(ctypes.get_last_error())
        process_handle = None
        try:
            info = ExtendedLimits()
            info.Basic.Flags = 0x2000 | 0x200  # KILL_ON_JOB_CLOSE | JOB_MEMORY
            info.JobLimit = memory_limit
            if not self.kernel.SetInformationJobObject(self.handle, 9, ctypes.byref(info), ctypes.sizeof(info)):
                raise ctypes.WinError(ctypes.get_last_error())
            process_handle = self.kernel.OpenProcess(0x0100 | 0x0001, False, pid)
            if not process_handle or not self.kernel.AssignProcessToJobObject(self.handle, process_handle):
                raise ctypes.WinError(ctypes.get_last_error())
        except Exception:
            self.close()
            raise
        finally:
            if process_handle:
                self.kernel.CloseHandle(process_handle)

    def peak_commit(self) -> int:
        info = self.info_type()
        if not self.kernel.QueryInformationJobObject(
            self.handle, 9, self.ctypes.byref(info), self.ctypes.sizeof(info), None
        ):
            raise self.ctypes.WinError(self.ctypes.get_last_error())
        return info.JobPeak

    def close(self) -> None:
        if self.handle:
            self.kernel.TerminateJobObject(self.handle, 1)
            self.kernel.CloseHandle(self.handle)
            self.handle = None


def wait_result(connection, process, timeout: float, memory_limit: int | None, job=None) -> dict:
    def receive():
        try:
            record = connection.recv()
        except EOFError as exc:
            process.join(timeout=0.1)
            raise ExtractionError(f"Extraction worker exited without a result (exit code {process.exitcode})") from exc
        if memory_limit is not None and record.get("peak_memory_bytes", 0) is not None:
            if record.get("peak_memory_bytes", 0) > memory_limit:
                raise ExtractionError(f"Worker exceeds {memory_limit} byte memory budget")
        if memory_limit is not None and "peak_memory_bytes" in record and record["peak_memory_bytes"] is None:
            raise ExtractionError("Worker memory measurement is unavailable; cannot enforce requested budget")
        if job is not None:
            record["process_tree_peak_commit_bytes"] = job.peak_commit()
            record["process_tree_memory_method"] = "windows_job_lifetime_peak_private_commit_bytes"
            if memory_limit is not None and record["process_tree_peak_commit_bytes"] > memory_limit:
                raise ExtractionError("Native OCR process-tree peak commit exceeds the memory budget")
        return record

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if job is not None and memory_limit is not None and job.peak_commit() > memory_limit:
            raise ExtractionError("Native OCR process-tree peak commit exceeds the memory budget")
        if connection.poll(0):
            return receive()
        peak, method = process_peak_memory(process.pid)
        if memory_limit is not None and peak is not None and peak > memory_limit:
            raise ExtractionError(f"Worker exceeds {memory_limit} byte memory budget ({method})")
        if memory_limit is not None and peak is None and process.is_alive():
            raise ExtractionError("Cannot enforce requested memory budget on this platform/process")
        if connection.poll(min(0.05, max(0, deadline - time.monotonic()))):
            return receive()
        if not process.is_alive():
            raise ExtractionError(f"Extraction worker exited with code {process.exitcode}")
    raise ExtractionError(f"Extraction worker exceeded {timeout:g} second timeout")


def _stop(process, connection, job=None) -> None:
    if job is not None:
        job.close()
    if process.is_alive():
        process.terminate()
    process.join(timeout=5)
    if process.is_alive():
        process.kill()
        process.join(timeout=5)
    connection.close()


def compare_document(engine: str, options: ExtractionOptions, source: Path, folder: Path,
                     document_id: str, source_hash: str, timeout: float,
                     memory_limit: int | None, warm_runs: int) -> dict:
    context = multiprocessing.get_context("spawn")
    parent, child = context.Pipe()
    ready = context.Event()
    process = context.Process(target=_worker, args=(child, engine, options, ready))
    job = None
    report = {"document_id": document_id, "engine": engine, "runs": [], "status": "failed"}
    folder.mkdir()
    process.start()
    child.close()
    try:
        if engine == "docling" and options.ocr and options.ocr_engine == "tesseract":
            if memory_limit is None:
                raise ExtractionError("Native OCR requires an explicit process-tree memory budget")
            job = WindowsWorkerJob(process.pid, memory_limit)
        ready.set()
        initialization = wait_result(parent, process, timeout, memory_limit, job)
        report.update(initialization)
        if initialization.get("status") == "failed":
            return report
        for index in range(warm_runs + 1):
            run_name = "cold" if index == 0 else f"warm-{index}"
            parent.send((str(source), str(folder / run_name), document_id, source_hash))
            record = wait_result(parent, process, timeout, memory_limit, job)
            record["run"] = run_name
            report["runs"].append(record)
            if record["status"] == "failed":
                return report
        report["status"] = "completed" if all(r["status"] == "completed" for r in report["runs"]) else "partial"
        return report
    except (ExtractionError, OSError) as exc:
        report["error"] = str(exc)
        return report
    finally:
        _stop(process, parent, job)


def _hash_file(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def load_manifest(path: Path, options: ExtractionOptions) -> tuple[dict, list[dict]]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ExtractionError("Manifest must be an object")
    if manifest.get("schema_version") != 1 or manifest.get("status") != "frozen":
        raise ExtractionError("Manifest must be schema_version 1 with status frozen")
    documents = manifest.get("documents")
    if not isinstance(documents, list) or not documents:
        raise ExtractionError("Manifest requires a nonempty permitted document list")
    ids = set()
    question_ids = set()
    prepared = []
    for document in documents:
        if not isinstance(document, dict):
            raise ExtractionError("Manifest document must be an object")
        document_id = document.get("id", "")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", document_id) or document_id in ids:
            raise ExtractionError("Document IDs must be unique opaque safe filenames")
        ids.add(document_id)
        for field in ("source_path", "source_sha256", "categories", "languages",
                      "inspection_pages", "permission_basis", "references_path", "references_sha256"):
            if not document.get(field):
                raise ExtractionError(f"Document {document_id} requires {field}")
        for field in ("categories", "languages", "inspection_pages"):
            if not isinstance(document[field], list):
                raise ExtractionError(f"{field} must be a list")
        if any(type(page) is not int or not 1 <= page <= options.max_pages for page in document["inspection_pages"]):
            raise ExtractionError("Inspection pages must be one-based within the page budget")
        source = Path(document["source_path"])
        references_path = Path(document["references_path"])
        if not source.is_absolute() or not references_path.is_absolute():
            raise ExtractionError("Private source/reference paths must be absolute local paths")
        if str(source).startswith(("\\\\", "//")) or str(references_path).startswith(("\\\\", "//")):
            raise ExtractionError("Network share source/reference paths are not allowed in offline runs")
        _, actual_hash = read_source(source, options)
        if actual_hash != document["source_sha256"]:
            raise ExtractionError(f"Source hash mismatch for {document_id}")
        with references_path.open("rb") as stream:
            reference_bytes = stream.read(10 * 1024 * 1024 + 1)
        if len(reference_bytes) > 10 * 1024 * 1024:
            raise ExtractionError("Reference file exceeds 10 MiB limit")
        if hashlib.sha256(reference_bytes).hexdigest() != document["references_sha256"]:
            raise ExtractionError(f"Reference hash mismatch for {document_id}")
        references = []
        for line in reference_bytes.decode("utf-8").splitlines():
            if not line.strip():
                continue
            reference = json.loads(line)
            if not isinstance(reference, dict):
                raise ExtractionError("Reference must be an object")
            question_id = reference.get("id")
            if not isinstance(question_id, str) or not question_id or question_id in question_ids:
                raise ExtractionError("Question IDs must be nonempty and globally unique")
            question_ids.add(question_id)
            if reference.get("document_id") != document_id or not reference.get("question"):
                raise ExtractionError("Reference question/document identity is missing or mismatched")
            if not reference.get("verified_by") or not reference.get("verified_on"):
                raise ExtractionError("References require human verification metadata")
            if type(reference.get("answerable")) is not bool:
                raise ExtractionError("Reference answerable must be boolean")
            facts, evidence = reference.get("expected_facts"), reference.get("evidence")
            if not isinstance(facts, list) or not isinstance(evidence, list):
                raise ExtractionError("References require fact/evidence lists")
            if reference["answerable"]:
                if not facts or not evidence or any(not isinstance(fact, str) or not fact.strip() for fact in facts):
                    raise ExtractionError("Answerable references require verified facts and evidence")
                if any(not isinstance(item, dict) or type(item.get("page")) is not int or item["page"] not in document["inspection_pages"]
                       or not item.get("source_evidence") for item in evidence):
                    raise ExtractionError("Evidence needs an inspection page and source_evidence")
            elif facts or evidence or not reference.get("reason"):
                raise ExtractionError("Unanswerable references require empty facts/evidence and a reason")
            references.append(reference)
        if not references:
            raise ExtractionError("Each document requires human-verified references")
        prepared.append({"manifest": document, "source": source, "references": references})
    return manifest, prepared


def validate_output(output: Path) -> None:
    if output.exists():
        raise ExtractionError("Output directory already exists; refusing to overwrite a run")
    if output.is_relative_to(PROJECT_ROOT):
        raise ExtractionError("Private experiment output must be outside the repository")
    if any((parent / ".git").exists() for parent in (output, *output.parents)):
        raise ExtractionError("Private experiment output must be outside a Git checkout")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--parsers", nargs="+", choices=("pypdf", "docling"), default=["pypdf", "docling"])
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--artifacts-path", type=Path)
    parser.add_argument("--ocr", action="store_true", help="Use an explicitly selected prepared local OCR engine")
    parser.add_argument("--ocr-engine", choices=("easyocr", "tesseract"), default="easyocr")
    parser.add_argument("--ocr-executable", type=Path, help="Explicit local Tesseract executable")
    parser.add_argument("--ocr-languages", nargs="+", default=["en"])
    parser.add_argument("--ocr-models-path", type=Path)
    parser.add_argument("--max-bytes", type=int, default=50 * 1024 * 1024)
    parser.add_argument("--max-pages", type=int, default=200)
    parser.add_argument("--timeout", type=float, default=180, help="Seconds per initialization/extraction")
    parser.add_argument("--max-memory-mib", type=int, help="Worker lifetime peak working-set ceiling; Windows only")
    parser.add_argument("--warm-runs", type=int, default=3)
    args = parser.parse_args(argv)
    report = None
    try:
        if not math.isfinite(args.timeout) or args.timeout <= 0 or args.warm_runs < 3 or len(set(args.parsers)) != len(args.parsers):
            raise ExtractionError("Use a positive timeout, at least three warm runs and unique parsers")
        if args.max_memory_mib is not None and args.max_memory_mib <= 0:
            raise ExtractionError("Memory limit must be positive")
        if "docling" in args.parsers and args.max_memory_mib is None:
            raise ExtractionError("Docling requires an explicit --max-memory-mib resource budget")
        output = args.output.resolve()
        validate_output(output)
        options = ExtractionOptions(
            max_bytes=args.max_bytes, max_pages=args.max_pages,
            artifacts_path=str(args.artifacts_path.resolve()) if args.artifacts_path else None,
            ocr=args.ocr, ocr_languages=tuple(args.ocr_languages),
            ocr_engine=args.ocr_engine,
            ocr_executable=str(args.ocr_executable.resolve()) if args.ocr_executable else None,
            ocr_models_path=str(args.ocr_models_path.resolve()) if args.ocr_models_path else None,
        )
        manifest_path = args.manifest.resolve()
        manifest_hash = _hash_file(manifest_path)
        manifest, documents = load_manifest(manifest_path, options)
        if _hash_file(manifest_path) != manifest_hash:
            raise ExtractionError("Manifest changed during validation")
        output.mkdir(parents=True, exist_ok=False)
        write_json(output / "manifest.json", manifest)
        report = {"format_version": 1, "created_at": datetime.now(timezone.utc).isoformat(),
                  "manifest_sha256": manifest_hash, "settings": asdict(options),
                  "timeout_seconds": args.timeout, "memory_limit_mib": args.max_memory_mib,
                  "warm_runs": args.warm_runs, "parsers": args.parsers,
                  "machine": {"platform": platform.platform(), "python": sys.version,
                              "cpu": platform.processor(), "logical_cpus": os.cpu_count()},
                  "quality_status": "manual_inspection_pending", "status": "running", "documents": []}
        write_json(output / "report.json", report)
        memory_limit = args.max_memory_mib * 1024 * 1024 if args.max_memory_mib else None
        for item in documents:
            entry = item["manifest"]
            folder = output / entry["id"]
            folder.mkdir()
            content, sha256 = read_source(item["source"], options)
            if sha256 != entry["source_sha256"]:
                raise ExtractionError(f"Source changed after validation: {entry['id']}")
            snapshot = folder / "source.pdf"
            snapshot.write_bytes(content)
            write_json(folder / "references.json", item["references"])
            for engine in args.parsers:
                record = compare_document(
                    engine, options, snapshot, folder / engine, entry["id"], sha256,
                    args.timeout, memory_limit, args.warm_runs,
                )
                record["categories"] = entry["categories"]
                record["inspection_pages"] = entry["inspection_pages"]
                report["documents"].append(record)
                write_json(output / "report.json", report)
            if _hash_file(item["source"]) != sha256:
                raise ExtractionError(f"Source changed during comparison: {entry['id']}")
        report["status"] = "completed" if all(d["status"] == "completed" for d in report["documents"]) else "failed"
        write_json(output / "report.json", report)
        inspection = ["# Manual extraction inspection", "", "Quality has not been scored.", "",
                      "For each document compare source.pdf and references.json with each engine's",
                      "cold/normalized.json (ordered blocks/pages/boxes) and cold/text.txt.", "",
                      "| Document | Engine | Status | Pages to inspect | Artifacts |",
                      "| --- | --- | --- | --- | --- |"]
        for record in report["documents"]:
            doc_id, engine = record["document_id"], record["engine"]
            inspection.append(f"| {doc_id} | {engine} | {record['status']} | {record['inspection_pages']} | {doc_id}/{engine}/ |")
        inspection.extend(["", "Record exact matches/inspected counts, wrong page/asset links, reading-order",
                           "errors and critical fact/cell regressions per category using the frozen rubric.", ""])
        (output / "inspection.md").write_text("\n".join(inspection), encoding="utf-8")
        print(f"Wrote extraction artifacts to {output}; manual quality inspection remains required")
        return 0 if report["status"] == "completed" else 1
    except (ExtractionError, OSError, ValueError, TypeError, KeyError) as exc:
        if report is not None:
            report.update(status="failed", error=str(exc))
            write_json(output / "report.json", report)
        print(f"PDF comparison failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    multiprocessing.freeze_support()
    raise SystemExit(main())
