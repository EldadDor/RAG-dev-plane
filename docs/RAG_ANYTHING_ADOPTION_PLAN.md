# RAG-Anything adoption plan

**Created:** 2026-10-08; **last reviewed:** 2026-10-10
**Planning task:** RAG-PLAN-01
**Status:** Plan reviewed and approved by the user on 2026-10-10, with local commit of all pending changes authorized. Stage A intake is authorized by “proceed”; stage-specific design decisions, installations/model preparation, live benchmarks and rollout retain their stated gates.
**Scope:** All five priorities from RAG-REVIEW-01: PDF extraction, image enrichment, table enrichment, processing identity/cache and optional vision-assisted answers.

## 1. Objective and boundaries

Make difficult PDFs, diagrams and tables usable by the existing local RAG pipeline, with measurable improvements and reliable source citations. Preserve separate chat/embedding adapters, local embeddings, pgvector as the default, Qdrant compatibility where supported, workspace authorization, private assets and existing hybrid retrieval/reranking behavior.

Start by comparing the current pypdf extractor with a Docling adapter. Docling is the first candidate, not an assumed winner. Add MinerU only if the first comparison exposes important gaps that justify another candidate. OCR engine and language support must be evaluated explicitly, especially Hebrew and mixed right-to-left text.

Adapt the patterns from RAG-Anything rather than install its entire framework. Its parser wrappers are orchestration around external parser engines; its modality processors also perform LightRAG-specific storage/graph work. Installing RAG-Anything would not eliminate the need to normalize output into this project's models.

Knowledge graphs, visual embedding models, audio/video, replacing native Word/PowerPoint extraction and new ingestion UI are outside this plan. Whole-document overview and rendering remain NP-25/NP-26 work, with shared provenance decisions coordinated at design time.

## 2. Current implementation and integration points

| Existing component | Current behavior | Planned extension |
| --- | --- | --- |
| `src/app/loaders/pdf_loader.py` | pypdf text per page with page markers and total page count | Selectable parser implementation and structured block/page provenance |
| `src/app/loaders/base.py`, `registry.py` | Synchronous `load(path) -> Document`; registry chooses by extension | Pass resolved PDF options through file and directory loading; optional engines imported lazily |
| `src/app/domain/models.py` | `Document`, private `DocumentAsset`, text chunks and related assets | Internal normalized blocks, extraction identity and derived-content provenance |
| `src/app/loaders/word_loader.py`, `powerpoint_loader.py` | Structural extraction and embedded image assets; PowerPoint also extracts cached chart values | Reuse source blocks/assets for enrichment without replacing native extraction |
| `src/app/services/ingestion_service.py` | Loads, compares content hash, chunks, embeds, attaches assets and replaces document publication | Compare processing identity, preserve block locations, add optional bounded enrichment |
| `src/app/services/retrieval_service.py` | Semantic/lexical fusion and optional reranking | Retrieve derived text through existing text embeddings; preserve modality/source relationships |
| `src/app/clients/chat_client.py`, `services/chat_service.py` | Text-only provider interface and grounded synthesis; image assets returned with citations | Separate optional vision capability and authorized image resolution |
| `src/app/services/model_profiles.py` | Existing model-scoped embedding cache | Reuse embedding cache; add distinct parse/enrichment cache contracts |
| `scripts/run_benchmark.py`, `src/app/evaluation/` | Live API evaluation with verified JSONL cases and workspace selection | Parser experiment manifests, extraction measurements and paired quality reporting |

Paths below are proposed integration locations, not files already implemented. Recheck current source before activating each stage.

## 3. Upstream reuse and dependency policy

| Priority | Upstream reference | What to adapt |
| --- | --- | --- |
| 1 | [parser.py](https://github.com/HKUDS/RAG-Anything/blob/main/raganything/parser.py) | Parser selection, engine initialization/reuse, structured output mapping and actionable extraction errors |
| 2 | [modalprocessors.py](https://github.com/HKUDS/RAG-Anything/blob/main/raganything/modalprocessors.py), [prompt.py](https://github.com/HKUDS/RAG-Anything/blob/main/raganything/prompt.py) | Bounded neighboring context, captions and image-description prompt structure |
| 3 | [modalprocessors.py](https://github.com/HKUDS/RAG-Anything/blob/main/raganything/modalprocessors.py) | Table body/caption/footnote/context processing |
| 4 | [processor.py](https://github.com/HKUDS/RAG-Anything/blob/main/raganything/processor.py) | Source fingerprint plus processing configuration in cache identity; bounded work scheduling |
| 5 | [query.py](https://github.com/HKUDS/RAG-Anything/blob/main/raganything/query.py) | Retrieving text first and supplying relevant images to vision synthesis |

At implementation, record the inspected upstream commit SHA and relevant symbols in an attribution note. Copy only reviewed, needed fragments; exclude LightRAG graph/storage calls and upstream path/URL conventions. Preserve the [MIT notice](https://github.com/HKUDS/RAG-Anything/blob/main/LICENSE) for copied substantial code. Check each parser engine's own package and model licenses separately before redistribution.

Verify Windows and Python 3.14 installation/runtime compatibility before selecting versions. A project's declared Python range alone does not prove that all native/transitive wheels work. Preferred design: an optional Docling dependency and adapter. If compatibility prevents that, propose an isolated local parser worker with a supported Python version and a versioned JSON boundary at G2; do not downgrade the application interpreter implicitly.

Use [Docling configuration guidance](https://docling-project.github.io/docling/usage/advanced_options/) to select local artifacts, OCR/table settings and resource limits. Model downloads are an explicit preparation step; warmed parsing must demonstrate that it can run offline. No remote document processing is part of the initial experiment.

## 4. Shared normalized representation

Introduce an internal, versioned extraction result containing:

- Stable document identity, SHA-256 of original bytes, parser name/version/settings and extraction warnings/status.
- Ordered blocks with stable block ID, ordinal, kind (`text`, `table`, `image`, `equation`), raw text/structured payload, heading path, source page or slide and optional bounding box.
- Character offsets into the deterministic text assembled for existing chunking. Page numbering at the application boundary is one-based; normalize engine coordinates and numbering explicitly.
- Assets linked to blocks through source anchors and content hashes, converted into existing `DocumentAsset` objects for persistence.
- Extracted source text and derived descriptions as separate fields, with model/prompt/version provenance for generated content.

Map this result into `Document.content`, structural metadata and assets. A pypdf result reports unsupported structures as unavailable, not as successful empty detections. Do not fabricate layout or figure captions for the baseline. Use source offsets to derive chunk page/section metadata; retain all contributing block/page IDs for chunks spanning multiple locations, with an agreed primary citation location.

Generated descriptions must not replace source text, table cells or cached chart values. Derived chunks link back to the original block, asset and source revision. Final prompt assembly must label derived interpretations and include original evidence when available.

## 5. Priority 1 — PDF comparison and switching

### P1-A: Define the corpus and reference answers

1. Select approximately 12–20 locally permitted PDFs covering ordinary text, two-column layouts, tables, diagrams, scanned pages, mixed scanned/text pages, Hebrew and mixed English/Hebrew. Include malformed/encrypted documents as error fixtures separately.
2. Create a corpus manifest under `evaluation/pdf_parsers/` with opaque document ID, private source path, source SHA-256, category, language and pages selected for inspection. Keep confidential PDFs and generated content outside committed fixtures; use synthetic/public fixtures for CI.
3. Manually verify reading-order expectations, table cells/headers/units, visible figure labels and page locations. Add roughly 30–50 questions with expected facts and evidence locations, including unanswerable cases. Freeze these references before comparing engines.

Deliverable: corpus manifest, extraction rubric, verified question set and fixed experiment configuration. Document counts are targets; coverage of each required category matters more than the number of files.

### P1-B: Build extraction-only comparison

Implement a proposed `scripts/compare_pdf_parsers.py` using the common result format and adapters. Run pypdf and Docling on identical bytes and write separate raw engine outputs, normalized JSON, assembled text and comparison reports. No indexing, embeddings, chat calls or production asset-store writes occur in this stage.

Record engine/dependency versions, settings, hardware, initialization time, per-document extraction time, peak memory where measurable, warnings and failures. Measure one cold run and at least three warm runs; separate downloaded/model initialization time from parsing. Disable automatic fallback during comparison so a failed candidate cannot be mistaken for a successful baseline result.

Proposed invocation, available only after implementation:

```powershell
uv run python scripts/compare_pdf_parsers.py --manifest evaluation/pdf_parsers/corpus.json --parsers pypdf docling --output evaluation/results/pdf-parsers/run-001
```

Evaluate manually against selected pages: reading order, text coverage, OCR accuracy, exact table values/units, captions, image associations and page provenance. Use normalized edit distance for reference text where appropriate; raw character counts are diagnostics, not quality scores. Add an inspection report showing source-page references alongside each engine's blocks. If page rendering is added, use approved isolated tooling and record its dependency separately.

Deliverable: reproducible extraction comparison with representative failures, not just averages.

### P1-C: Add the selector to local ingestion

Proposed selection precedence: explicit local comparison/ingestion option, then configured `PDF_PARSER`, then `pypdf`. Start with `pypdf|docling`; unknown names fail validation. Keep optional engine imports/model loading out of the baseline startup path.

Expose per-run selection through a local ingestion command first. Its entry point must invoke the existing ingestion service and propagate parser options through both single-file and directory loading. If API selection is needed, propose `pdf_parser` on `IngestRequest` and corresponding diagnostics under a separate G2 public-contract decision. This field does not exist today.

Proposed command shape:

```powershell
uv run python scripts/ingest_local.py --source <corpus-root> --workspace-id <approved-benchmark-workspace> --pdf-parser docling --chunking-profile default --model-profile <existing-ready-profile>
```

Resolve parser settings once per run; reuse heavy engine instances. Run blocking parsing outside the API event loop with bounded workers, or through the approved isolated worker. Enforce file/page/runtime/resource limits and actionable missing-engine/model errors. Benchmark failures remain visible. Any operational fallback must be explicit, recorded in document metadata and included in processing identity.

Preserve the current dry-run guarantee of no model calls. For the new engines, define dry-run as validation plus cached extraction where available; when extraction would invoke OCR/layout/vision models, report that extraction is pending. The extraction comparison command is a separate, explicitly requested model-using operation and must not masquerade as ingestion dry-run.

### P1-D: Compare indexed RAG results

Provision two dedicated benchmark workspaces through the existing authorized operator workflow: one for pypdf, one for Docling. Match workspace memberships and model/chunking settings. Do not overload `model_profile` or `chunking_profile` to identify parser variants; those have existing meanings.

Index the same corpus once per workspace using explicit parser selection. Keep embedding model, dimensions, chunker, retrieval settings, reranking and chat model fixed. Different extracted text may produce different chunk boundaries; that is part of the parser treatment. Use the complete manifest root for directory runs so stale-source cleanup cannot remove unrelated material.

Use `scripts/run_benchmark.py` with its existing `--workspace-id`, `--dataset` and `--output` options against an already-running authorized API. The current runner needs authenticated-request support verified before use with gateway authentication. It does not currently provide a `model_profile` option; use a fixed approved server default or add support explicitly if required. Omit workspace overrides in shared cases so each CLI run uses its assigned workspace.

Compare source Recall@k/MRR, verified answer facts, exact numerical accuracy, page/block citation accuracy, abstention behavior and latency. Existing coverage/faithfulness metrics are proxies; manual evidence checks remain required. Use fresh sessions, freeze the index during each run and keep cold/warm cache conditions consistent. Store paired per-question results and configurations.

### P1-E: Decision and rollback

Proposed acceptance rubric to freeze at G2: all mandatory offline correctness/isolation tests pass; no wrong source page/asset links in the inspected set; no loss of critical table values or simple-text reference facts; meaningful paired improvement on at least one difficult-document category without an unexplained regression elsewhere. Record counts and uncertainty rather than claiming statistical significance from a small corpus. Agree machine-specific latency/memory ceilings before runs.

Choose among retaining pypdf, making Docling opt-in for suitable documents, or promoting a new default after evidence. Add MinerU only through a scoped follow-up using the same manifest and rubric. Rollback selects pypdf and explicitly reingests affected publications; changing a setting alone does not restore previously indexed content. Keep baseline workspace/results until the decision is accepted. Benchmark cleanup is a separate explicit operator action.

## 6. Priority 2 — Context-aware image enrichment

**Dependency:** normalized blocks/assets and minimal P4 identity/invalidation. Can begin on existing Word/PowerPoint assets independently of choosing a PDF winner.

1. Add an optional image-enrichment adapter with a separately configured vision capability. The provider may share an endpoint with chat, but its capability, model and processing provenance are explicit; embeddings still use the existing embedding adapter.
2. Assemble bounded nearby source text, heading path, captions and alt text for each image. Define page/block windows and token limits; retain the IDs of all context contributors. Use actual tokenizer accounting where supported.
3. Generate a structured description: visible labels, components/relationships, relevant chart observations and uncertainty. Require the model to distinguish visible facts from contextual inference and treat document instructions as data.
4. Keep image bytes/source anchors unchanged. Add a separate searchable derived chunk linked to its asset, block, revision and generating model/prompt. Include meaningful source text alongside it at synthesis time.
5. Bound image count/bytes, concurrency, timeout and retries. Skip unsupported media with diagnostics. Enrichment failure preserves base extraction and records partial status; retry missing items without duplicating chunks.

Validate with synthetic diagrams, screenshot-only facts, misleading nearby text, duplicate images, unsupported media and provider failures. Mock provider/network calls for unit tests; real vision runs require explicit experiment authorization. Paired baseline/enriched evaluation must show improved visual-question answers and no invented labels or incorrect citations.

Rollback disables enrichment for future runs; explicitly reprocess affected publications to remove derived chunks while retaining source assets. Update `.env.example`, central prompts, docs and provider tests for any configuration change.

## 7. Priority 3 — Table enrichment and source fidelity

**Dependency:** structured tables from PDFs or existing native Word/PowerPoint blocks, plus minimal P4 identity.

1. Preserve raw table representation, row/column headers, values, units, captions, footnotes and source location. Identify merged cells and extraction gaps explicitly.
2. Build a deterministic table rendering for embedding. For large tables, split by row groups while repeating relevant headers/units and retaining table/block ID and row ranges.
3. Add optional text-model summaries describing table purpose and directly supported comparisons. Keep summaries separate from original cells. Numeric answers must be supported by original table evidence; any calculated result needs a reproducible calculation path or must remain out of scope.
4. Retrieve summaries to discover relevant tables, then include source rows/cells in the answer context. Retain applicable footnotes and fit context to the model's input budget.
5. Reuse bounded enrichment execution/cache infrastructure from P2 where appropriate, without requiring vision for text tables.

Validate exact decimals, signs, percentages, units, empty/merged cells, repeated headers, multi-page tables, Hebrew labels and misleading model summaries. Compare baseline, deterministic table handling and optional summaries separately so their effects are measurable. Gate summary rollout on improved table discovery with preserved numerical accuracy.

Rollback keeps extracted tables and disables/removes only generated summaries through explicit reprocessing.

## 8. Priority 4 — Processing identity, caches and publication lifecycle

Implement the identity portion before indexed P1 comparison, and the enrichment portion before P2/P3 rollout. Persistent cache optimization follows correctness.

1. Keep original source SHA-256 separate from a canonical processing fingerprint. Include parser engine/version/options, normalized-format version, chunker implementation/settings and enabled enrichment configuration. A changed processing fingerprint invalidates the unchanged-document skip even if source bytes match. Parser settings changes must not require renaming a chunking profile.
2. Define parse cache keys from original bytes, parser/version/settings and normalized-format version. Define enrichment keys from source revision, asset/table bytes, exact surrounding-context digest, model/provider identity, model revision where available, prompt version and generation settings.
3. Store application-visible cache entries within workspace/document authorization and retention boundaries. Never expose a result solely by knowing its content hash. Continue using the existing embedding cache for embeddings.
4. Begin with a bounded local cache abstraction for the experiment. Propose durable PostgreSQL/filesystem metadata, retention, encryption requirements if applicable and explicit cache management only when justified; any SQL objects use a new versioned migration.
5. Store pending/completed/partial/failed stage state. Publish one coherent document revision using existing replacement semantics; a failed replacement must preserve the last usable publication. Stage private bytes first, then metadata/chunks; leave unreferenced bytes for approved cleanup rather than deleting shared content during rollback.
6. Coalesce duplicate work for the same authorized key, bound concurrency and use atomic cache writes. Do not cache failures as successful results. Force-reprocess options bypass relevant cache/skip stages explicitly and are auditable.

Tests: identical input reuse, same-size changed bytes, changed parser/model/prompt/context/settings, workspace isolation, corruption recovery, concurrent requests, failed replacement and restart/retry behavior. Measure cache hits and avoided extraction/provider work without logging private text. Verify model-profile publication/scoping and Qdrant behavior separately; unsupported durability/isolation capabilities must be reported clearly.

Rollback disables cache reuse; fingerprint/provenance metadata remains readable. Any migration needs its own forward/rollback strategy before approval.

## 9. Priority 5 — Optional vision-assisted synthesis

**Dependency:** trustworthy image retrieval links, authorized asset resolution, provider capability and bounded context assembly. P2 helps discover relevant visuals; P5 lets the answer model inspect original bytes.

1. Add a separate vision-capable completion interface accepting text and validated image content. Keep existing text completion available and local embeddings unchanged.
2. Retrieve through the current workspace/model/chunking scope. Resolve only assets belonging to cited, authorized document revisions through application metadata and `AssetStore`; do not extract arbitrary file paths or URLs from model text.
3. Limit images, bytes, image resolution and total prompt budget. Construct request-local messages with source citation identifiers, extracted text and original images. Avoid shared mutable image state across requests.
4. Label generated enrichment as interpretation. Require source-backed claims and uncertainty when a visual cannot be read. Provider errors or missing images use an explicit fallback policy; text-only fallback must not claim to have inspected unavailable visual evidence.
5. Make vision opt-in. If request options, response diagnostics or SSE behavior change, obtain G2 approval and update the authoritative API contract plus frontend handoff. Preserve citation asset routes and ordinary JSON/SSE semantics.

Validate text-only regression, supported/unsupported provider capability, oversized/missing assets, cross-workspace/revision denial, concurrent request isolation, timeout/cancellation and visual prompt injection. Paired evaluation uses original visual facts and identical retrieved scope, then measures accuracy, grounding, latency and token/cost impact. Enable only for the workloads that benefit.

Rollback selects text synthesis; image assets and citations remain available. No automatic cloud-provider fallback is introduced.

## 10. Delivery sequence and gates

| Stage | Deliverable | Entry decision / dependency | Exit evidence |
| --- | --- | --- | --- |
| A | Corpus, reference answers, adapter contract and compatibility decision | G1 implementation intake; G2 modules/dependency/normalized representation | Frozen rubric and compatibility findings |
| B | Extraction-only pypdf/Docling comparison | Approved adapter design and model preparation | Offline tests, artifacts and extraction decision |
| C | Local selector, minimal P4 identity and isolated indexed comparison | G2 selector/publication design; operator approval for workspace setup and live runs | Paired RAG report and parser recommendation |
| D | Remaining P4 cache/state infrastructure | G2 storage/migration design where needed | Invalidation, isolation and recovery checks |
| E | P2 image enrichment | Blocks/assets, identity, approved vision provider | Baseline/enriched evidence and failure handling |
| F | P3 deterministic table handling, then optional summaries | Structured tables and identity | Exact-value tests and paired table evaluation |
| G | P5 vision synthesis | Authorized retrieval/assets and provider support; G2 API if changed | Capability/security regression tests and visual benchmark |
| H | Selected rollout and closure | Explicit defaults/operational decision; G3 merge/push and G4 closure | Final evidence, limitations and carry-over list |

At each G2 request, record the chosen design, one rejected alternative and migration/rollback implications. Plan approval and “proceed” on 2026-10-10 authorize Stage A intake; subsequent task-specific design and operational gates remain required. Routine work within an approved stage proceeds autonomously; service operations, secrets and live-service tests retain their existing explicit authorization requirements.

Proposed task families P1–P5 are identifiers within this plan, not newly activated repository phases. At implementation intake, assign repository task IDs and copy only the selected stage's scope/tasks onto the current board. Preserve the existing next-three phase priorities until the user selects a change.

## 11. Validation, rollout and handoff checklist

- Run focused offline loader, ingestion, asset, publication and API tests for each changed boundary. Optional-dependency absence must not break the baseline install.
- Keep fixture providers/stores for CI; live parsing/model/API runs form a separately authorized experiment lane. Do not start services or apply migrations as part of ordinary tests.
- Record every experiment's source hashes, package/model/prompt versions, hardware, all relevant settings, errors and paired outcomes. Protect private result artifacts from accidental Git inclusion.
- Update configuration examples and operational documentation alongside new settings. Resolve default/fallback behavior through measured evidence.
- Coordinate page/slide/block identity with NP-25/NP-26 before public preview/overview changes. Future API proposals require `docs/frontend_architecture.md` and newest-first handoff entries; this plan creates no new contract.
- Report unsupported cases and checks not run. Rollout readiness requires functional evidence, resource acceptance, source fidelity and practical rollback, not successful parsing alone.

## 12. Decisions still needed at implementation intake

Select the permitted corpus and machine resource budget; approve an engine/runtime installation strategy after compatibility checks; choose whether local CLI selection is sufficient; authorize isolated benchmark workspace setup and live runs; freeze quality/resource thresholds. Provider/model choices for image enrichment and vision synthesis occur at their own stages.

The first implementation request should activate Stage A and the Stage B design review. The first completed experiment should answer whether richer PDF extraction improves this project's actual documents before broader enrichment is enabled.
