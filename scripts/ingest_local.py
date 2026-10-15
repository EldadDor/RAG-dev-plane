"""Local-only isolated PDF ingestion; defaults to validation without writes/models."""
from __future__ import annotations

import argparse
import asyncio
from dataclasses import asdict
import json
import ipaddress
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from app.config import get_settings
from app.loaders.prepared_pdf_loader import PreparedPDFLoader, TREATMENTS
from app.services.asset_store import LocalFileAssetStore
from app.services.ingestion_service import IngestionService
from app.services.model_profiles import PostgresEmbeddingCache, PostgresModelProfileStore


async def ingest(args, settings=None):
    settings = settings or get_settings()
    if settings.app_env != "local" or settings.auth_mode != "local":
        raise ValueError("Stage C operator ingestion requires local application/auth mode")
    if not re.fullmatch(r"rag-stage-c-[a-z0-9-]{1,100}", args.workspace_id):
        raise ValueError("A dedicated rag-stage-c-* workspace is required")
    profile_name, profile = settings.chunking_profile(args.chunking_profile)
    model_name = args.model_profile or settings.model_profile
    loader = PreparedPDFLoader(args.manifest, args.run_root, args.treatment,
                               max_asset_bytes=settings.asset_max_image_bytes,
                               max_assets=settings.asset_max_images_per_document,
                               max_total_asset_bytes=settings.asset_max_total_bytes_per_document)
    source = args.source.resolve()
    permitted = set(loader.entries)
    if source.is_dir():
        if {p.resolve() for p in source.iterdir() if p.is_file() and p.suffix.lower() == ".pdf"} != permitted:
            raise ValueError("Directory must contain exactly the frozen manifest PDF set")
        if any(p.parent != source for p in permitted):
            raise ValueError("Directory input requires a single complete manifest root")
    elif source not in permitted:
        raise ValueError("Single-file source must be in the frozen manifest")
    selected_sources = sorted(permitted) if source.is_dir() else [source]
    validated = []
    for path in selected_sources:
        try:
            validated.append(loader.load(str(path)))
        except (OSError, ValueError, KeyError, TypeError):
            pass
    report = {"treatment": args.treatment, "workspace_id": args.workspace_id,
              "chunking_profile": profile_name, "model_profile": model_name,
              "manifest_sha256": loader.manifest_hash, "documents_total": len(selected_sources),
              "documents_publishable": len(validated), "apply": args.apply,
              "failures": list(loader.errors)}
    if not args.apply:
        report["status"] = "dry_run"
        report["chunks_estimated"] = None
        if profile.provider in {"default", "langchain", "recursive-character"}:
            service = IngestionService(settings, None, None, document_loader=loader.load)
            chunker = service._chunker_for(profile_name)
            report["chunks_estimated"] = sum(len(chunker.chunk(d.content.strip())) for d in validated)
        else:
            report["chunking_pending"] = "Model/tokenizer-backed chunking is not invoked by validation"
        return report
    if not validated:
        raise ValueError("No publishable complete extraction documents")
    if settings.vector_store != "postgres" or settings.embedding_provider != "ollama":
        raise ValueError("This isolated experiment requires existing PostgreSQL and local Ollama embeddings")
    host = urlsplit(settings.embedding_base_url).hostname
    try:
        local_host = ipaddress.ip_address(host).is_private
    except ValueError:
        local_host = host in {"localhost", "host.docker.internal"}
    if not local_host:
        raise ValueError("Local embeddings endpoint required; no cloud fallback")
    from app.main import _init_pg_vector_store
    store = await _init_pg_vector_store(settings)
    try:
        model_store = PostgresModelProfileStore(store.pool, settings.pg_schema)
        selected = await model_store.get(model_name)
        if selected is None or selected.status != "ready" or selected.provider != "ollama":
            raise ValueError("Existing ready local embedding model profile required")
        # Validate storage before provisioning any workspace.
        await store.for_profile(selected.storage_target, selected.dimensions)
        display_name = f"Stage C / {args.treatment} / {loader.manifest_hash[:12]}"
        async with store.pool.acquire() as conn:
            async with conn.transaction():
                existing = await conn.fetchval(
                    f"SELECT display_name FROM {settings.pg_schema}.workspaces WHERE workspace_id=$1", args.workspace_id)
                if existing is None:
                    if not args.provision_workspace:
                        raise ValueError("Workspace is absent; explicitly select --provision-workspace")
                    await conn.execute(f"INSERT INTO {settings.pg_schema}.workspaces (workspace_id,display_name) VALUES ($1,$2)",
                                       args.workspace_id, display_name)
                    await conn.execute(f"INSERT INTO {settings.pg_schema}.workspace_members (workspace_id,subject,role) VALUES ($1,$2,'owner')",
                                       args.workspace_id, settings.local_subject)
                elif not args.resume or existing != display_name:
                    raise ValueError("Workspace exists; --resume requires its matching experiment identity")
                role = await conn.fetchval(f"SELECT role FROM {settings.pg_schema}.workspace_members WHERE workspace_id=$1 AND subject=$2",
                                          args.workspace_id, settings.local_subject)
                if role != "owner":
                    raise ValueError("Operator is not the owner of the experiment workspace")
        from app.clients.embedding_client import OllamaEmbeddingClient
        embedding_client = OllamaEmbeddingClient(settings.embedding_base_url, timeout=settings.embedding_timeout_seconds)
        service = IngestionService(settings, embedding_client, store,
                                   LocalFileAssetStore(settings.asset_storage_root), model_store,
                                   PostgresEmbeddingCache(store.pool, settings.pg_schema)
                                   if settings.embedding_cache_enabled else None,
                                   document_loader=loader.load)
        result = await service.ingest_path(str(source), workspace_id=args.workspace_id,
                                           chunking_profile=profile_name, model_profile=model_name)
        report.update(status="indexed", ingestion=asdict(result),
                      embedding_model=selected.model, embedding_dimensions=selected.dimensions,
                      storage_target=selected.storage_target)
        report["failures"] = list({(e["path"], e["reason"]): e for e in loader.errors}.values())
        return report
    finally:
        await store.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--run-root", type=Path, help="Completed fresh extraction run, outside Git")
    parser.add_argument("--treatment", required=True, choices=tuple(TREATMENTS))
    parser.add_argument("--workspace-id", required=True)
    parser.add_argument("--chunking-profile", default="default")
    parser.add_argument("--model-profile")
    parser.add_argument("--provision-workspace", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--output", required=True, type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    output = args.output.resolve()
    if output.exists() or any((p / ".git").exists() for p in (output.parent, *output.parent.parents)):
        parser.error("Private output must be a new file outside all Git checkouts")
    if args.apply and args.run_root is None:
        parser.error("--apply requires fresh prepared --run-root; no model invocation is implicit")
    try:
        report = asyncio.run(ingest(args))
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("x", encoding="utf8") as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        print(f"{report['status']}: {report['documents_publishable']}/{report['documents_total']} publishable; report {output}")
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"Local ingestion failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
