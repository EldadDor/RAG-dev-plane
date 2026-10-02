"""Operator-only metadata backfill. Default is read-only; never calls models.

Apply during rollout with old writers stopped. Profile publication locks prevent
new writers from changing the vector corpus while metadata is reconciled.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from app.clients.pg_vector_store import PgVectorStore
from app.config import get_settings
from app.services.document_catalog import publish_metadata, bump_revision


async def recover_legacy_rows(conn, schema: str, rows: list[dict]):
    """Recover scoped aliases only from an exact catalog identity/path match.

    Unscoped pre-authorization vectors are unreachable through workspace search
    and remain untouched. Malformed scoped records still fail certification.
    """
    scoped, recovered, excluded = [], [], 0
    for row in rows:
        payload = row["metadata"]
        encoded_object = isinstance(payload, str)
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except ValueError:
                scoped.append(row)
                continue
        if not isinstance(payload, dict):
            scoped.append(row)
            continue
        if payload.get("workspace_id") is None:
            excluded += 1
            continue
        payload = dict(payload)
        alias = payload.get("document_id")
        if not payload.get("doc_id") and isinstance(alias, str) and alias:
            source = await conn.fetchrow(
                f"SELECT * FROM {schema}.source_documents WHERE workspace_id=$1 AND chunking_profile=$2 AND doc_id=$3",
                payload["workspace_id"], payload.get("chunking_profile") or "default", alias)
            if source and source["source_path"] == (row.get("source") or payload.get("source_path")):
                payload["doc_id"] = alias
                payload.setdefault("source_type", source["source_type"])
                recovered.append({"id": row["id"], "metadata": payload})
        elif encoded_object and isinstance(payload.get("doc_id"), str):
            source = await conn.fetchrow(
                f"SELECT * FROM {schema}.source_documents WHERE workspace_id=$1 AND chunking_profile=$2 AND doc_id=$3",
                payload["workspace_id"], payload.get("chunking_profile") or "default", payload["doc_id"])
            if source and source["source_path"] == (row.get("source") or payload.get("source_path")):
                recovered.append({"id": row["id"], "metadata": payload})
            else:
                # A decoded object cannot be counted by SQL until normalized;
                # without matching provenance, certification must fail.
                scoped.append({**row, "metadata": None})
                continue
        scoped.append({**row, "metadata": payload})
    return scoped, recovered, excluded


def analyze_chunks(rows: list[dict]) -> tuple[list[dict], list[str]]:
    """Pure analysis keeps malformed identities from silently entering a catalog."""
    groups = defaultdict(list)
    errors = []
    for row in rows:
        metadata = row["metadata"]
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except ValueError:
                errors.append("malformed_chunk_metadata")
                continue
        if not isinstance(metadata, dict):
            errors.append("malformed_chunk_metadata")
            continue
        workspace, doc_id = metadata.get("workspace_id"), metadata.get("doc_id")
        if not isinstance(workspace, str) or not workspace or not isinstance(doc_id, str) or not doc_id:
            errors.append("chunk_missing_identity")
            continue
        if (not isinstance(metadata.get("chunking_profile") or "default", str)
                or metadata.get("title") is not None and not isinstance(metadata["title"], str)
                or metadata.get("source_type") is not None and not isinstance(metadata["source_type"], str)
                or not isinstance(metadata.get("related_asset_ids", []), list)
                or any(not isinstance(value, str) for value in metadata.get("related_asset_ids", []))):
            errors.append("malformed_chunk_metadata")
            continue
        groups[(workspace, metadata.get("chunking_profile") or "default", doc_id)].append((row, metadata))
    documents = []
    for (workspace, chunking, doc_id), entries in sorted(groups.items()):
        # Do not print paths/content in the operator summary either.
        identity = f"{workspace}/{chunking}/{doc_id}"
        identities = [payload.get("chunk_id", str(row["id"])) for row, payload in entries]
        paths = {row.get("source") or payload.get("source_path") for row, payload in entries}
        types = {payload.get("source_type", "unknown") for _, payload in entries}
        titles = {payload.get("title") for _, payload in entries}
        if len(set(identities)) != len(identities):
            errors.append(f"duplicate_chunk_identity:{identity}")
        if len(paths) != 1 or not next(iter(paths)) or len(types) != 1 or len(titles) != 1:
            errors.append(f"conflicting_document_metadata:{identity}")
            continue
        hashes = {payload.get("content_hash") for _, payload in entries}
        roots = {payload.get("root_path") for _, payload in entries}
        asset_ids = {asset for _, payload in entries for asset in payload.get("related_asset_ids", [])}
        documents.append({
            "workspace_id": workspace, "chunking_profile": chunking, "doc_id": doc_id,
            "source_path": next(iter(paths)), "source_type": next(iter(types)), "title": next(iter(titles)),
            "content_hash": next(iter(hashes)) if len(hashes) == 1 else None,
            "root_path": next(iter(roots)) if len(roots) == 1 else None,
            "last_ingested_at": None, "count": len(entries), "asset_ids": asset_ids,
        })
    return documents, errors


async def reconcile(apply: bool = False) -> dict:
    from app.main import _init_pg_vector_store
    settings = get_settings()
    if settings.vector_store != "postgres":
        raise ValueError("Document reconciliation requires PostgreSQL")
    store = await _init_pg_vector_store(settings)
    schema = settings.pg_schema
    report = {"dry_run": not apply, "profiles": 0, "documents": 0, "chunks": 0,
              "legacy_alias_chunks_recovered": 0, "unscoped_chunks_excluded": 0,
              "historical_zero_chunk_rows_unassigned": 0, "orphan_groups": 0,
              "errors": [], "warnings": [], "ready": False}
    try:
        # This first read chooses lock targets. Recheck the registry under the
        # locks; registry provisioning itself remains an operator operation.
        async with store.pool.acquire() as conn:
            if apply:
                # Commit maintenance visibility before backfill. A failed apply
                # must never leave an already-enabled but uncertified catalog.
                await conn.execute(f"UPDATE {schema}.document_catalog_state SET ready=FALSE,updated_at=clock_timestamp() WHERE singleton=TRUE")
            profiles = await conn.fetch(f"SELECT * FROM {schema}.model_profiles ORDER BY profile_name")
        async with store.publication_session(*(row["profile_name"] for row in profiles)) as conn:
            pinned_store = store.bound_to(conn)
            async with conn.transaction():
                # All changes including readiness commit together or roll back.
                registry = await conn.fetch(f"SELECT * FROM {schema}.model_profiles ORDER BY profile_name FOR SHARE")
                if [dict(r) for r in registry] != [dict(r) for r in profiles]:
                    raise ValueError("Registry changed; restart reconciliation")
                represented = set()
                for profile in profiles:
                    target = profile["storage_target"]
                    try:
                        view = await pinned_store.for_profile(target, profile["dimensions"])
                    except (RuntimeError, ValueError):
                        diagnostics = report["errors"] if profile["status"] == "ready" else report["warnings"]
                        diagnostics.append(f"unprovisioned_profile:{profile['profile_name']}")
                        continue
                    rows = await conn.fetch(f"SELECT id,content,metadata,source FROM {schema}.{target} ORDER BY id")
                    scoped, recovered, excluded = await recover_legacy_rows(conn, schema, [dict(row) for row in rows])
                    documents, errors = analyze_chunks(scoped)
                    report["legacy_alias_chunks_recovered"] += len(recovered)
                    report["unscoped_chunks_excluded"] += excluded
                    if excluded:
                        report["warnings"].append(f"unscoped_chunks_excluded:{profile['profile_name']}:{excluded}")
                    if apply:
                        for recovered_row in recovered:
                            await conn.execute(f"UPDATE {schema}.{target} SET metadata=$1::jsonb WHERE id=$2",
                                               recovered_row["metadata"], recovered_row["id"])
                    report["errors"].extend(errors)
                    report["profiles"] += 1
                    report["documents"] += len(documents)
                    report["chunks"] += len(rows)
                    existing = await conn.fetch(
                        f"SELECT * FROM {schema}.document_index_metadata WHERE model_profile=$1",
                        profile["profile_name"])
                    prior = {(r["workspace_id"], r["chunking_profile"], r["doc_id"]): dict(r) for r in existing}
                    represented.update(identity for identity, row in prior.items() if row["indexed_chunk_count"] == 0)
                    seen = set()
                    for document in documents:
                        identity = (document["workspace_id"], document["chunking_profile"], document["doc_id"])
                        represented.add(identity)
                        seen.add(identity)
                        if not await conn.fetchval(f"SELECT EXISTS(SELECT 1 FROM {schema}.workspaces WHERE workspace_id=$1)", identity[0]):
                            report["errors"].append("unknown_chunk_workspace")
                            continue
                        source = await conn.fetchrow(
                            f"SELECT * FROM {schema}.source_documents WHERE workspace_id=$1 AND chunking_profile=$2 AND doc_id=$3", *identity)
                        if source is None:
                            report["orphan_groups"] += 1
                        elif document["root_path"] is None and source["source_path"] == document["source_path"]:
                            document["root_path"] = source["root_path"]
                        old = prior.get(identity)
                        if old and document["content_hash"] is not None and old["content_hash"] == document["content_hash"]:
                            document["last_ingested_at"] = old["last_ingested_at"]
                        assets = await conn.fetch(
                            f"""SELECT asset_id FROM {schema}.document_assets WHERE asset_id=ANY($1::text[])
                                AND workspace_id=$2 AND chunking_profile=$3 AND doc_id=$4""",
                            sorted(document["asset_ids"]), *identity)
                        if len(assets) != len(document["asset_ids"]):
                            report["errors"].append("missing_or_misscoped_asset")
                            continue
                        if apply:
                            # The shared record is needed by the existing asset
                            # FK. Do not overwrite another model's source version.
                            await conn.execute(
                                f"""INSERT INTO {schema}.source_documents
                                    (workspace_id,chunking_profile,doc_id,source_path,source_type,content_hash,root_path)
                                    VALUES ($1,$2,$3,$4,$5,$6,$7) ON CONFLICT DO NOTHING""",
                                *identity, document["source_path"], document["source_type"],
                                document["content_hash"] or "", document["root_path"])
                            await publish_metadata(conn, schema, target, profile["profile_name"], document, preserve_time=True)
                            await conn.execute(
                                f"""DELETE FROM {schema}.document_index_assets
                                    WHERE workspace_id=$1 AND chunking_profile=$2 AND doc_id=$3 AND model_profile=$4""",
                                *identity, profile["profile_name"])
                            for asset in assets:
                                await conn.execute(
                                    f"""INSERT INTO {schema}.document_index_assets
                                        (workspace_id,chunking_profile,doc_id,model_profile,asset_id)
                                        VALUES ($1,$2,$3,$4,$5) ON CONFLICT DO NOTHING""",
                                    *identity, profile["profile_name"], asset["asset_id"])
                    for identity, old in prior.items():
                        if identity not in seen and old["indexed_chunk_count"] > 0 and apply:
                            await conn.execute(
                                f"""DELETE FROM {schema}.document_index_metadata
                                    WHERE workspace_id=$1 AND chunking_profile=$2 AND doc_id=$3 AND model_profile=$4""",
                                *identity, profile["profile_name"])
                            await bump_revision(conn, schema, identity[0], profile["profile_name"], identity[1])
                source_rows = await conn.fetch(f"SELECT workspace_id,chunking_profile,doc_id FROM {schema}.source_documents")
                report["historical_zero_chunk_rows_unassigned"] = sum(
                    (row["workspace_id"], row["chunking_profile"], row["doc_id"]) not in represented for row in source_rows)
                if apply:
                    if report["errors"]:
                        # Raising rolls back partial metadata updates too.
                        raise ValueError("Catalog not certified: " + json.dumps(report, ensure_ascii=True))
                    await conn.execute(f"UPDATE {schema}.document_catalog_state SET ready=TRUE,updated_at=clock_timestamp() WHERE singleton=TRUE")
                    report["ready"] = True
        return report
    finally:
        await store.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Write metadata and certify readiness (default: read-only report)")
    args = parser.parse_args()
    print(json.dumps(asyncio.run(reconcile(args.apply)), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
