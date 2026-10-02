"""Local rollout acceptance: HTTP reads plus PostgreSQL fixtures always rolled back.

No real embedding/chat calls. The fixture warmer uses deterministic synthetic
vectors; fixture workspaces, vectors, memberships and cache writes never commit.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from app.config import get_settings
from app.main import app, _init_pg_vector_store
from app.services.document_catalog import PinnedConnectionPool, PostgresDocumentCatalog
from app.services.model_profiles import PostgresModelProfileStore, PostgresEmbeddingCache
from app.services.model_profile_warmer import ModelProfileWarmer
from app.services.workspace_store import PostgresWorkspaceStore

logging.getLogger("httpx").setLevel(logging.WARNING)


def check_headers(response):
    assert response.headers.get("cache-control") == "private, no-store"
    assert {"cookie", "authorization"} <= {v.strip().lower() for v in response.headers["vary"].split(",")}


async def validate(base_url: str):
    settings = get_settings()
    assert settings.app_env == "local" and settings.vector_store == "postgres"
    assert settings.document_list_enabled
    assert base_url.startswith("http://127.0.0.1:")
    report = {"validated_at": datetime.now(timezone.utc).isoformat(), "provider_calls": 0,
              "http_scopes": [], "checks": [], "fixtures_rolled_back": False}
    store = await _init_pg_vector_store(settings)
    schema = settings.pg_schema
    try:
        async with httpx.AsyncClient(base_url=base_url, timeout=30) as client:
            assert (await client.get("/health")).status_code == 200
            assert (await client.get("/readiness")).status_code == 200
            discovery = await client.get("/workspaces")
            assert discovery.status_code == 200
            workspaces = discovery.json()["workspaces"]
            async with store.pool.acquire() as conn:
                profiles = await conn.fetch(f"SELECT * FROM {schema}.model_profiles WHERE status='ready' ORDER BY profile_name")
                for workspace in workspaces:
                    wid = workspace["workspace_id"]
                    for profile in profiles:
                        view = await store.for_profile(profile["storage_target"], profile["dimensions"])
                        expected = await conn.fetch(
                            f"""SELECT doc_id,indexed_chunk_count FROM {schema}.document_index_metadata
                                WHERE workspace_id=$1 AND model_profile=$2 AND chunking_profile=$3
                                ORDER BY last_ingested_at DESC NULLS LAST,doc_id COLLATE "C"
                            """,
                            wid, profile["profile_name"], settings.default_chunking_profile)
                        for limit in (1, 25, 100):
                            observed, cursor = [], None
                            for _ in range(len(expected) + 2):
                                params = {"limit": limit, "model_profile": profile["profile_name"]}
                                if cursor:
                                    params["cursor"] = cursor
                                response = await client.get(f"/workspaces/{wid}/documents", params=params)
                                assert response.status_code == 200, (response.status_code, response.text)
                                check_headers(response)
                                body = response.json()
                                for item in body["items"]:
                                    assert set(item) == {"doc_id", "title", "file_name", "document_type", "last_ingested_at", "indexed_chunk_count"}
                                    assert "/" not in item["file_name"] and "\\" not in item["file_name"]
                                    observed.append((item["doc_id"], item["indexed_chunk_count"]))
                                cursor = body["page"]["next_cursor"]
                                assert bool(cursor) == body["page"]["has_more"]
                                if not cursor:
                                    break
                            assert observed == [(r["doc_id"], r["indexed_chunk_count"]) for r in expected]
                        for row in expected:
                            count = await conn.fetchval(
                                f"""SELECT count(*) FROM {schema}.{profile['storage_target']}
                                    WHERE metadata->>'workspace_id'=$1 AND metadata->>'doc_id'=$2
                                    AND COALESCE(metadata->>'chunking_profile','default')=$3""",
                                wid, row["doc_id"], settings.default_chunking_profile)
                            assert count == row["indexed_chunk_count"]
                        report["http_scopes"].append({"workspace_id": wid, "model_profile": profile["profile_name"],
                            "documents": len(expected), "chunks": sum(r["indexed_chunk_count"] for r in expected),
                            "page_limits": [1, 25, 100]})
            for params in ({"limit": 0}, {"limit": 101}, {"cursor": "tampered"}, {"model_profile": "unknown-np20"}):
                response = await client.get(f"/workspaces/{settings.default_workspace_id}/documents", params=params)
                assert response.status_code == 422
                check_headers(response)
            denied = await client.get("/workspaces/np20-nonmember/documents")
            assert denied.status_code == 403
            check_headers(denied)
            report["checks"].extend(["live_health_readiness", "http_pagination_order_count_parity", "public_field_allowlist",
                                     "cache_headers", "invalid_queries", "workspace_denial"])

        # Use real SQL on one connection with an outer transaction that never
        # commits. The production router/identity/membership code runs in ASGI;
        # only environment settings and its connection pool are injected.
        async with store.pool.acquire() as conn:
            transaction = conn.transaction(isolation="repeatable_read")
            await transaction.start()
            marker = "np20-qa-" + uuid.uuid4().hex
            first, second = marker + "-a", marker + "-b"
            try:
                for wid, subject in ((first, "np20-alice"), (second, "np20-bob")):
                    await conn.execute(f"INSERT INTO {schema}.workspaces(workspace_id,display_name) VALUES($1,'NP20 QA')", wid)
                    await conn.execute(f"INSERT INTO {schema}.workspace_members(workspace_id,subject,role) VALUES($1,$2,'owner')", wid, subject)
                await conn.execute(f"INSERT INTO {schema}.workspace_members(workspace_id,subject) VALUES($1,'np20-bob')", first)
                pinned = PinnedConnectionPool(conn)
                profile_store = PostgresModelProfileStore(pinned, schema)
                selected = await profile_store.get(settings.model_profile)
                other = next(p for p in profiles if p["profile_name"] != selected.profile_name)
                views = [await store.bound_to(conn).for_profile(selected.storage_target, selected.dimensions),
                         await store.bound_to(conn).for_profile(other["storage_target"], other["dimensions"])]

                def document(wid, doc_id, version="one"):
                    return {"workspace_id": wid, "doc_id": doc_id, "chunking_profile": "default",
                            "source_path": f"C:/np20-qa/{doc_id}.txt", "root_path": "C:/np20-qa",
                            "source_type": "text", "title": "QA document", "content_hash": version}

                def chunks(doc, n, view):
                    return [{"chunk_id": f"{doc['doc_id']}:{i}", "payload": {**doc, "text": "synthetic QA", "chunk_index": i},
                             "vector": [0.01] * view._vector_dim} for i in range(n)]

                for wid in (first, second):
                    for doc_id, n in (("one", 2), ("two", 1), ("zero", 0)):
                        doc = document(wid, doc_id)
                        await views[0].replace_document(doc, chunks(doc, n, views[0]))
                doc = document(first, "one")
                await views[1].replace_document(doc, chunks(doc, 1, views[1]))
                original = await conn.fetchrow(f"SELECT * FROM {schema}.document_index_metadata WHERE workspace_id=$1 AND doc_id='one' AND model_profile=$2", first, selected.profile_name)
                await views[0].replace_document(doc, chunks(doc, 2, views[0]))
                unchanged = await conn.fetchrow(f"SELECT * FROM {schema}.document_index_metadata WHERE workspace_id=$1 AND doc_id='one' AND model_profile=$2", first, selected.profile_name)
                assert dict(original) == dict(unchanged)
                try:
                    broken = document(first, "one", "broken")
                    invalid = chunks(broken, 1, views[0]); invalid[0]["vector"] = [1.0]
                    await views[0].replace_document(broken, invalid)
                    raise AssertionError("Invalid vector unexpectedly committed")
                except Exception as exc:
                    assert "dimensions" in str(exc)
                assert await views[0].get_document_hash("one", first) == "one"

                gateway = settings.model_copy(update={"auth_mode": "gateway", "document_list_cursor_secret": "np20-fixture-key-" * 4})
                app.dependency_overrides[get_settings] = lambda: gateway
                app.state.workspace_store = PostgresWorkspaceStore(pinned, schema)
                app.state.document_catalog = PostgresDocumentCatalog(pinned, schema)
                app.state.model_profile_store = profile_store
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://qa") as client:
                    headers = {gateway.chat_identity_header: "np20-alice"}
                    path = f"/workspaces/{first}/documents"
                    no_identity = await client.get(path)
                    assert no_identity.status_code == 401
                    page = await client.get(path, params={"limit": 1}, headers=headers)
                    assert page.status_code == 200, page.text
                    token = page.json()["page"]["next_cursor"]
                    cross_user = await client.get(path, params={"limit": 1, "cursor": token}, headers={gateway.chat_identity_header: "np20-bob"})
                    assert cross_user.status_code == 422
                    cross_workspace = await client.get(f"/workspaces/{second}/documents", headers=headers)
                    assert cross_workspace.status_code == 403
                    full = await client.get(path, params={"limit": 100}, headers=headers)
                    assert {i["doc_id"]: i["indexed_chunk_count"] for i in full.json()["items"]} == {"one": 2, "two": 1, "zero": 0}
                    changed = document(first, "one", "two")
                    await views[0].replace_document(changed, chunks(changed, 1, views[0]))
                    stale = await client.get(path, params={"limit": 1, "cursor": token}, headers=headers)
                    assert stale.status_code == 409
                    await conn.execute(f"DELETE FROM {schema}.workspace_members WHERE workspace_id=$1 AND subject='np20-alice'", first)
                    revoked = await client.get(path, params={"limit": 1, "cursor": token}, headers=headers)
                    assert revoked.status_code == 403
                    for response in (no_identity, cross_user, cross_workspace, full, stale, revoked):
                        check_headers(response)
                report["checks"].extend(["two_principal_workspace_isolation", "cross_user_cursor_binding", "membership_revocation",
                                        "zero_chunk_publication", "unchanged_skip", "failed_replace_rollback", "changed_revision_409"])

                class SyntheticEmbedding:
                    async def create_embedding(self, model, text):
                        return [0.01] * other["dimensions"]

                cache = PostgresEmbeddingCache(pinned, schema)
                warmer = ModelProfileWarmer(store.bound_to(conn), SyntheticEmbedding(), profile_store, cache,
                                           embedding_provider=settings.embedding_provider)
                await warmer.warm(other["profile_name"], selected.profile_name, first, dry_run=False)
                source_rows = await conn.fetch(f"SELECT doc_id,indexed_chunk_count,last_ingested_at FROM {schema}.document_index_metadata WHERE workspace_id=$1 AND model_profile=$2 ORDER BY doc_id", first, selected.profile_name)
                target_rows = await conn.fetch(f"SELECT doc_id,indexed_chunk_count,last_ingested_at FROM {schema}.document_index_metadata WHERE workspace_id=$1 AND model_profile=$2 ORDER BY doc_id", first, other["profile_name"])
                assert [dict(r) for r in source_rows] == [dict(r) for r in target_rows]
                assert await views[0].delete_missing_documents("C:/np20-qa", first, ["two", "zero"], recursive=False) == 1
                assert await views[1].get_document_hash("one", first) == "two"
                assert await views[0].get_document_hash("one", second) == "one"
                report["checks"].extend(["synthetic_warm_count_time_parity", "scoped_directory_cleanup", "other_profile_workspace_preserved"])
            finally:
                app.dependency_overrides.clear()
                await transaction.rollback()
            assert not await conn.fetchval(f"SELECT EXISTS(SELECT 1 FROM {schema}.workspaces WHERE workspace_id=ANY($1::text[]))", [first, second])
            report["fixtures_rolled_back"] = True
        return report
    finally:
        await store.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = asyncio.run(validate(args.base_url))
    encoded = json.dumps(report, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
