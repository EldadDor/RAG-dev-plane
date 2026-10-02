"""Local workspace-scoped warmer using atomic document publication.

Default execution is read-only; --apply embeds and publishes target documents.
Replaces the legacy direct-SQL writer so catalog counts cannot drift.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from app.config import get_settings
from app.dependencies import get_embedding_client
from app.services.model_profile_warmer import ModelProfileWarmer
from app.services.model_profiles import PostgresEmbeddingCache, PostgresModelProfileStore


async def warm(profile_name: str, source_model_profile: str, workspace_id: str, dry_run: bool):
    from app.main import _init_pg_vector_store
    settings = get_settings()
    if settings.vector_store != "postgres" or settings.app_env != "local":
        raise ValueError("Operator warming requires local PostgreSQL")
    store = await _init_pg_vector_store(settings)
    try:
        async with store.pool.acquire() as conn:
            if not await conn.fetchval(f"SELECT EXISTS(SELECT 1 FROM {settings.pg_schema}.workspaces WHERE workspace_id=$1)", workspace_id):
                raise ValueError("Workspace is not provisioned")
        warmer = ModelProfileWarmer(
            store, get_embedding_client(settings),
            PostgresModelProfileStore(store.pool, settings.pg_schema),
            PostgresEmbeddingCache(store.pool, settings.pg_schema),
            embedding_provider=settings.embedding_provider)
        return asdict(await warmer.warm(profile_name, source_model_profile, workspace_id, dry_run=dry_run))
    finally:
        await store.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile_name")
    parser.add_argument("--workspace-id", required=True)
    parser.add_argument("--source-model-profile", default="default")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--dry-run", action="store_true", help="Read-only estimate (also the default)")
    args = parser.parse_args()
    print(json.dumps(asyncio.run(warm(args.profile_name, args.source_model_profile, args.workspace_id,
                                     dry_run=not args.apply)), sort_keys=True))


if __name__ == "__main__":
    main()
