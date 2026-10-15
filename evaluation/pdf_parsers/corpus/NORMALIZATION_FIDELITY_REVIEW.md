# Normalization fidelity follow-up

**Tasks:** RAG-B-V4 / RAG-B-PARENT / RAG-B-INDEX
**Reviewed:** 2026-10-14
**Decision:** Keep pypdf as production default. Correct two omissions in the
experimental adapter; retain OCR text verbatim and preserve the original evidence.
Real ingestion is held until the user confirms laptop readiness.

## Saved v4 audit

[Structural audit](V4_ADDED_TEXT_AUDIT.json) checks all 31 available saved v4
results against their recorded hashes, original raw exports and source refs.
Existing text/page associations and asset hashes are retained; block identities
are unique, Unicode offsets match text, and box coordinates stay within page bounds.
All 1,743 added blocks resolve through raw hierarchy to a picture on the same page.
Numeric bounds do not certify geometry: raw-loading clamping warnings remain relevant.

The additions contain 19,569 characters, including 260 blocks of one codepoint
and 126 nonempty blocks with no letter or number. These are diagnostic counts,
not false-text grades or deletion rules. Short diagram labels and punctuation
can be valid. Four blocks contain control characters: the same two font-decoding
defects in each treatment, `De<U+001F>ne` and `Way<U+001E>nding`.

Selective source-page review finds useful labels alongside errors. pdf-015 page 2
contains real English screenshot menu labels and their keyboard shortcuts, but
the added OCR also includes unrelated Hebrew fragments and corrupted shortcuts.
Its 619 OCR additions are mostly screenshot tokens; 363 are on page 2 and 137
on page 12. They cannot all be called garbage. On pdf-008 page 1, added OCR
recognizes a logo dot as `0` and produces Hebrew/currency tokens over product
photography. A language or minimum-length filter would also risk losing valid
mixed-language labels. No automatic text suppression was added.

## Adapter corrections in v5

The existing experimental adapter now uses policy
`picture_parent_document_index_export_clamp_pages_without_boxes_v5`.
Its processing identity and block IDs differ from v4.

- Each nested item retains its nearest `picture_parent_ref` and
  `picture_parent_block_id`, including children reached through groups and nested
  pictures. Cycles, unresolved refs and omitted picture parents fail explicitly.
  These links preserve recorded containment; they do not establish leader-line
  edges or semantic diagram relations.
- `document_index` items use the existing table representation: cell/spans payload
  and searchable Markdown. Original labels remain in the payload. Eight such
  tables across both treatments (pdf-003 page 2, pdf-004 page 3 and pdf-012 pages
  4/5) recover 296 cells and 24,658 Markdown characters. No expected answer was
  used to construct text.

**Correction to the earlier diagnosis:** pdf-004's required contents entry was
already present in raw `#/tables/0`, row 3: `METAL AND TECHNICAL TOYS`, page `21`.
The adapter mapped its `document_index` label to empty text; this was an adapter
omission, not missing upstream contents. Original-output and v4 grades remain
valid for their saved normalized text. The new mapping recovers the entry and
page association through the recorded table cells; no aggregate v5 score is assigned.

## Verification and geometry limits

52 focused offline tests passed:
`.venv/Scripts/python.exe -X utf8 -m pytest -q -p no:cacheprovider
--basetemp .codex-test-tmp-rag-v5 tests/test_pdf_extraction.py tests/test_loaders.py`.
The broader sandbox run stalled in subprocess checks and was interrupted; the
final scoped run completed with elevated execution. The checks cover document-index
mapping, direct/grouped/nested parent links and invalid associations.

[In-memory saved-export replay](V5_FIDELITY_REPLAY.json) passed for 31 documents:
1,787 picture-child links, including all 1,743 newly exposed v4 blocks. Source
hashes, block order, non-index text, pages and asset hashes are preserved; offsets
validate after adding table text and all v4/v5 block IDs are disjoint. Input
raw/v4 hashes and canonical v5 JSON hashes are recorded. Full v5 extraction files
were not written and models were not initialized.

Replay captures raw-loading clamping warnings inside extraction. On pdf-002
page 3 it therefore omits boxes from 73 no-OCR and 79 OCR blocks that the earlier
v4 replay retained. All unaffected boxes remain identical. This is a stricter
replay disclosure, not repaired geometry or fresh native-runtime evidence.

## Remaining work

1. Font/glyph corruption remains in raw text; removing controls cannot reconstruct
   the missing letters safely.
2. pdf-014 page 2 has stage-5 continuation text attached to stage 6 in raw table
   cell coordinates (`#/tables/1`, row 3). Source review confirms it belongs to
   stage 5. Mapping preserves the upstream cells; an evidence-based table/reading
   order treatment is still needed.
3. pdf-015 raw `#/texts/22` already reverses `Add New Item`, `Web Form` and
   `Default.aspx` in its mixed-script prose. Parent links and table mapping do not
   fix logical RTL order. Original source text is retained.
4. Review all added text against source pages before claiming a false-text rate
   or assigning complete v5 case grades. Three original timeout results remain
   unavailable; fixed-budget resource and geometry gates are unresolved.

No model reruns, live providers/stores, SQL, service operations, production wiring,
real ingestion, independent human adjudication, CER or full application suite ran.
