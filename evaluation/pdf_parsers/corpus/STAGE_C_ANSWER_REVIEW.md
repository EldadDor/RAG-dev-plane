# Stage C saved-answer fact and citation review

**Task:** RAG-C-02. **Reviewed:** 2026-10-15. **Reviewer:** Codex assistant.
**Decision:** Keep pypdf as the production default. Neither candidate establishes
overall answer fidelity or production acceptance.

## Scope and evidence

Reviewed all 99 saved second-request answers: 42 pypdf, 28 no-OCR and 29 OCR.
Compared them with the frozen approved facts and their source-page evidence.
Verified all 17 private artifacts recorded in [the Stage C summary](STAGE_C_SUMMARY.json),
all 17 source PDFs and all 17 reference files against their recorded SHA-256s.
Questions, eligible facts and matched case IDs align across the derived datasets;
the previously excluded descriptive fact in pdf-007-q3 remains excluded.
No frozen input or original result was edited.

Visually inspected 12 layout-sensitive source pages: pdf-003 p8; pdf-004 p3;
pdf-006 p6; pdf-010 p1; pdf-011 p2; pdf-012 p1; pdf-013 p4/5/6; pdf-014 p2/4/5.
Other judgments use the human-approved source evidence and saved answers, rather
than claiming a new visual review of every page or every possible answer claim.

[Review data](STAGE_C_ANSWER_REVIEW.json) contains 99 answer hashes and original
response indices, reference/page pointers, case judgments/rationales, 495 citation
locations and snippet hashes, input hashes, totals and matched-case transitions.
Answer bodies remain in the existing private artifacts. The case table below
is an assistant qualitative review, **not independent human adjudication**.

## Rubric

- **C:** All eligible approved fact groups are conveyed. Additional wrong claims
  and citation defects can still occur; C is not a clean-answer pass.
- **P:** Some requested information is correct, but required facts are omitted,
  conflated or corrupted.
- **W:** Wrong requested answer, without substantive correct required information.
- **A:** Explicit abstention without the requested answer.
- **U:** No saved candidate answer because the document was not publishable.
  This is availability loss, not model abstention.

Paraphrases and harmless spacing are accepted. Exact table values, entities,
dates, labels and identifiers are not repaired by inference. Completeness uses
all valid frozen fact groups, even where they extend beyond the narrow question
(notably the 25-card/5x5 group in pdf-017-q2). Missing such a group is an omission
under this rubric, not automatically a substantively wrong response.
No per-fact accuracy percentage or statistical significance is claimed.

## Coverage and matched comparison

| Treatment | Available / 42 | C | P | W | A | Unavailable |
| --- | --- | --- | --- | --- | --- | --- |
| pypdf | 42 | 14 | 21 | 6 | 1 | 0 |
| Docling no OCR | 28 | 11 | 11 | 6 | 0 | 14 |
| Docling OCR | 29 | 14 | 11 | 4 | 0 | 13 |

These unequal populations must not be ranked by their raw counts or percentages.
On the same 28 no-OCR case IDs, complete approved-fact coverage is baseline
10/28 versus candidate 11/28: four gains and three losses. On the same 29 OCR
case IDs it is baseline 11/29 versus candidate 14/29: seven gains and four losses.
Exact transition IDs are in the review data. One gain in each comparison,
pdf-005-q3, still incorrectly labels optional servers/editor setup links as
primary servers. It includes all expected capabilities but is not a correct
primary-server list. These counts therefore cannot be presented as answer
correctness or citation-supported acceptance rates.

OCR's useful recoveries include the two weather-table answers, exact roulette
values and the Egan bibliography/page-25 answer. Both candidates lose the
stage-5 table answer that pypdf supplies; neither candidate resolves the diagram
or timeline questions. All treatments answer the casino-guide introduction
question from unrelated material. Retrieval of the expected document alone
does not prevent these errors.

## Citation support and attribution

All 495 saved citation paths exist and their page values are within the frozen
document page ranges. At least one citation matches an approved reference page
in 37/42 baseline, 25/28 no-OCR and 26/29 OCR answers. These are **location
diagnostics**, not entailment grades. A citation on the correct page can refer
to another row, only a heading, or an excerpt that ends before the required fact.
Conversely, a correct fact may appear on more pages than the selective reference.

The saved responses expose shortened snippets, rather than complete retrieved
chunks or a mapping from every answer claim to a citation. Consequently this
review does not certify full-chunk support, exact offsets, every claim or every
cross-page association. In particular, some Docling snippets contain later
`[PAGE n]` markers while their citation metadata identifies the chunk's starting
page. A matching first page is not proof of exact claim location.

Concrete support checks against snippets and source evidence:

| Case | Observed support or attribution failure |
| --- | --- |
| pdf-003-q1 | Source p8 has distinct Bar, Video Walls, Table Games and Audio labels. Baseline conflates/omits labels; no-OCR mixes the diagram with contents entries; OCR repeats contents entries despite returning a p8 citation. None is a complete, source-faithful diagram answer. |
| pdf-003-q2 | All answer another document's subject despite returning the expected document somewhere in the source list. Their actual answers do not follow the approved introduction. |
| pdf-004-q3 | Neither available answer cites the requested catalogue at all. Baseline uses a Hebrew summary; no-OCR uses the casino guide's budget entry. Source catalogue p3 visibly gives entry 4 and page 21. |
| pdf-006-q2 | Baseline cites both p6 and p10 and gives correct dimensions, but explicitly identifies p10/RLTB.R.206, a round-leg table. Source p6's requested square-leg row is MTB.R.206. This fails entity/page attribution despite numeric coverage C. |
| pdf-007-q3 | Baseline's returned p5 snippet already contains Egan/title/publication/page 25, yet the answer says section/page 7. OCR's first p5 snippet visibly contains the requested bibliography and supports that core answer; its additional `18-8` statistic is corrupted. No-OCR's answer does not identify the bibliography. |
| pdf-009-q1 | No-OCR turns a snippet's npm-install exception into a claim that mvn install is unnecessary. The citation does not support that substitution. |
| pdf-009-q2 | OCR quotes MAVEN_OPTS evidence while answering a compiler-heap question. Same-document/page presence does not resolve the setting mismatch. |
| pdf-010-q1 | OCR's weather-row snippet explicitly associates Metro Manila with cloudy skies/scattered rains/thunderstorms, matching source p1. Baseline has no forecast citation and abstains. |
| pdf-010-q2 | OCR gives the correct source-p1 row; its saved first snippet ends at the beginning of the Northern Luzon row. Full requested row is visually verified in the PDF, but that shortened snippet alone cannot establish complete retrieved support. Baseline cites unrelated agricultural/table content. |
| pdf-011-q1 | Source p2 visibly gives 5.3%/$5.30. Candidates retain that pair; baseline substitutes 5.26%/$5.26 even though it returns the correct document. |
| pdf-012-q1 | Returned snippets already contain opening-diagram text including small adapter/base plus adapter. All answers instead describe the later hyperparameter workflow. This is an observed answer-selection error, not proof that the diagram facts were absent from extraction. |
| pdf-014-q1 | Source p2 visibly keeps Stacks, 100 teachers and the 500-student/LLM continuation in stage 5. Candidate snippets show headings or other-stage prose; candidate answers substitute other activities. Baseline retains the requested stage-5 facts. |
| pdf-014-q2 | Candidate citations include p4 timeline content plus Jan/May conference prose. Answers call those conferences February events, contradicting the source's Feb 9/11 training columns. Baseline gives the right training identities but omits dates/stage. |

For remaining cases, the table records answer/reference discrepancies and the
machine data preserves every citation location for follow-up. No blanket
"all citations support the answer" conclusion is justified by these artifacts.

## Case review

The rationale in each row describes all available treatments; U cells have no
answer to grade. Full approved facts and source evidence remain in the frozen
reference files linked by the machine data.

| Case | pypdf | No OCR | OCR | Review rationale |
| --- | --- | --- | --- | --- |
| pdf-001-q1 | C | C | C | Eager fetching and LAZY/delayed initialization retained. Baseline additionally suggests LAZY avoids n+1; source's Mistake 3 warns LAZY can still cause n+1. Candidate general prevention wording also needs qualification. |
| pdf-001-q2 | C | P | P | Baseline retains all three groups. Candidates give Query interface and exact 5/0 calls but omit the explicit JPQL OFFSET/LIMIT limitation. |
| pdf-002-q1 | P | U | U | Baseline says 5 cards instead of 54; nine tokens retained, shapes/colors and dice counts omitted. |
| pdf-002-q2 | P | U | U | Baseline retains the same-question/single-winner condition but invents token-revealing, reversing and token-count victory; card-back checking and two-winner allocation missing. |
| pdf-003-q1 | P | P | W | Baseline misses Table Games and conflates Bar/Video Walls and Audio with branding, then appends abstention. No-OCR mixes contents entries with labels and joins/splits several labels, then abstains. OCR repeats contents entries instead of the diagram labels and ends mid-list. |
| pdf-003-q2 | W | W | W | Baseline answers about astronautics; candidates answer about AI planning/fine-tuning. No answer states the approved casino-guide purpose. |
| pdf-004-q1 | P | P | U | Both omit 25+ years, collector/toy framing and 0 gauge. Baseline also omits significant hand production; candidate retains it. |
| pdf-004-q2 | P | P | U | Baseline omits century, 2009 ensemble and international performances; extends countryside work to all generations. Candidate adds ensemble/locations but omits first-half-19th-century and 2009 specificity. |
| pdf-004-q3 | W | W | U | Baseline chooses Hebrew summary/page 1; no-OCR chooses another document's Define Your Budget/page 6. Neither returns METAL AND TECHNICAL TOYS/page 21. |
| pdf-005-q1 | C | C | C | All three management/500-line/fresh-conversation facts retained; extra rules do not establish superior extraction. |
| pdf-005-q2 | P | P | P | Baseline retains purpose and beginning-of-conversation instruction but loses the proposed prompt wording. Candidates retain purpose but replace the requested usage instructions with a long generic checklist. |
| pdf-005-q3 | P | C | C | Baseline substitutes File system/Git for primary servers and omits Supabase. Candidates mention all three expected capabilities in concluding prose but falsely list optional servers and editor setup links as primary servers. C here is fact coverage only, not a correct answer. |
| pdf-006-q1 | W | U | U | Baseline gives other-chair heights and guesses 790 or higher, not the specified 950/620/380/355 row. |
| pdf-006-q2 | C | U | U | Baseline gives 2000/600 correctly but attributes them to RLTB.R.206/viewer page 10 (round legs), not square-leg MTB.R.206/viewer page 6. Correct values with incorrect entity/page provenance. |
| pdf-006-q3 | P | U | U | Baseline retains durable frame and chrome-plated upgrade but omits most features and packaging. |
| pdf-007-q1 | P | C | C | Baseline mentions tax income but does not faithfully give unreported-turnover/lost-tax argument and adds unsupported economic claims. Candidates explicitly retain both reference facts. |
| pdf-007-q2 | P | P | P | Baseline omits employment/rehabilitation/policing and the 18/35-percent study. Candidates retain first four groups despite intrusive footnote numbers, but omit the study group. |
| pdf-007-q3 | W | W | C | Baseline calls a section the source and says page 7; no-OCR supplies study prose/page 1 without bibliography. OCR retains Egan/title/publication/Nov 1997/page 25, but also reproduces corrupted 18-8 statistic. |
| pdf-008-q1 | C | U | U | Baseline retains up to 2000 m and external 10-30 VDC. |
| pdf-008-q2 | C | U | U | Baseline retains Ethernet, CAN, analog and Ethernet/browser configuration. |
| pdf-009-q1 | P | P | P | All retain commands but omit explicit successful CLI compilation before IntelliJ. No-OCR additionally transfers npm-install exception to mvn install, contradicting always-start instruction. |
| pdf-009-q2 | C | C | P | Baseline/no-OCR retain path and 1024m. OCR gives an incomplete/different settings path and cites MAVEN_OPTS instead of compiler heap. |
| pdf-009-q3 | C | C | C | All retain CRM 1536m/JIDI 1024m and -Xmx/run configuration. Baseline adds a 512m JIDI example below the stated requirement. |
| pdf-010-q1 | A | U | C | Baseline abstains without retrieving forecast; OCR retains Metro Manila condition. |
| pdf-010-q2 | W | U | C | Baseline speculates from unrelated agricultural text; OCR retains all wind/direction/wave-height facts. |
| pdf-011-q1 | W | C | C | Baseline substitutes 5.26 percent/$5.26 for source table's 5.3 percent/$5.30. Candidates retain exact source values. |
| pdf-011-q2 | C | C | C | All retain average-player, typical-offering and regulatory/actual-variation qualifications. |
| pdf-011-q3 | C | P | P | Baseline retains all groups. Candidates retain percentage/non-guarantee/factors but omit explicit hypothetical average player, $100 basis and reasonable-period formulation. |
| pdf-012-q1 | P | P | P | All substitute later hyperparameter workflow for opening diagram. Small-parameter adapter idea partly retained; correct Base LLM + data -> fine-tuning -> adapted model flow and base-plus-adapter result not stated. Candidate says LoRA is second stage of its invented four-stage list. |
| pdf-012-q2 | P | C | C | Baseline omits numeric VRAM savings; candidates retain 2x, near 70 percent/RL 50-90 percent and all four HF/TRL workflows. |
| pdf-012-q3 | C | C | C | All retain 8192 and correct ds1/ds2/ds3 counts and dataset associations; harmless spacing tolerated. |
| pdf-013-q1 | P | W | P | Baseline says six and changes blue 1 to blue 3/omits orange 3. No-OCR invents card-symbol totals/examples. OCR retains four geometric shape/color pairs but says four, omitting three numeral examples. |
| pdf-013-q2 | P | P | P | Baseline/no-OCR omit free choice of route length; baseline lacks precise first-card/next-card mechanics. OCR invents fixed six-card setup and compares two pile cards rather than pile top with first route card; omits face-down/advance rules. |
| pdf-014-q1 | C | W | W | Baseline retains all stage-5 groups. No-OCR substitutes generic training/exam/project activities; OCR supplies stage-1 urgency activities and appends abstention. Source row visibly contains Stacks/100 teachers/500 students/LLM alternatives. |
| pdf-014-q2 | P | W | W | Baseline names correct basic/advanced trainings but omits exact dates and Kotter stage 3. Candidates name Jan 7 and May 4 conferences as February events, not the Feb 9/11 trainings. |
| pdf-015-q1 | C | U | C | Available answers retain 7 Boom and divisibility/digit 7/+40 rule. |
| pdf-015-q2 | P | U | P | Both available answers stop at File -> New -> Website; omit empty ASP.NET template, Browse, Add New Item and Web Form/Default.aspx. |
| pdf-016-q1 | P | U | U | Baseline describes host-dependent virus reproduction without explicitly stating source's asexual classification; bacteria fission conveys asexual reproduction; fungi sexual/asexual/spores retained. Not a complete source-table answer. |
| pdf-016-q2 | P | U | U | Baseline retains germination and some division/elongation but mixes other hormone effects; omits stamens, flower sex, starch breakdown and seed dormancy suppression. |
| pdf-016-q3 | P | U | U | Baseline retains March 2008/Nisan 5768 but substitutes pest-control content for potted plants/bonsai and omits Jerusalem. |
| pdf-017-q1 | C | C | C | All retain starting-team double-sided agent, color-up orientation and placement in corresponding pile. |
| pdf-017-q2 | P | P | P | All retain key/color semantics but omit 25 cards/5x5 setup. That final reference group extends beyond the question's color-mapping focus; strict frozen-fact completeness is not the same as usefulness. |

## Acceptance and next work

This review establishes that the source-recall/proxy gains in
[Stage C](STAGE_C_RESULTS.md) do not imply exact-answer or citation acceptance.
Preserve the pypdf default and all extraction exclusions. The 14/42 baseline
coverage count also makes clear that retaining pypdf is not a claim that its
answers already meet acceptance.

Prioritize a design for assigned-document evaluation and negative cases, then
source-grounded retrieval/answer diagnostics for wrong-document selection,
diagram-versus-contents confusion and table-row association. Keep numeric
coverage separate from entity/page correctness. A full claim-level citation
audit needs complete saved retrieved chunks and explicit claim/source mapping;
independent human acceptance remains outstanding. Any API structural change
needs its own G2 decision. Controlled equal-load latency/resource comparisons
also remain outstanding and cannot be inferred from these saved answers.

Offline validation: 17 recorded artifact hashes, 34 source/reference hashes,
99 unique answer/case alignments, 495 existing citation paths/page ranges,
matched ID sets, verdict totals, report links and documentation whitespace.
No application tests, first-request answer review, live providers/stores,
new extraction/OCR, services, controlled timing, production promotion,
push/merge or phase closure were performed.
