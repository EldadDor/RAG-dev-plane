# Working on

- Backend NP-09: build the golden evaluation dataset and regression harness.
- Frontend: no active implementation phase; FP-01 and FP-02 are complete.
- Backend NP-09: collect human-verified expected facts and optional source hints for representative questions.
- Backend NP-09: expand the initial three-case smoke set to roughly 10–20 cases before using trends for product decisions.

# Approved For future

- NP-06: define required unit/API CI lanes and a separate manual live-stack lane.
- NP-09: build the golden evaluation dataset and repeatable regression harness.
- NP-07: reduce answer length through context packing, duplicate filtering, and prompt tuning after NP-08 and NP-09.
- NP-10: activate cross-encoder reranking after NP-09 proves its value.
- NP-12: deploy to Azure/office infrastructure after NP-08 and NP-09.
- FP-03: integrate the frontend with office deployment, gateway identity, proxy, TLS, CORS, and delivery infrastructure.

# Still in deliberation

- Which documents and developer questions should form the first chunking experiment and later golden set.
- Which named chunking profiles and size/overlap settings should be compared first.
- Whether the optional semantic splitter is worth enabling for comparison.
- Whether to expose chunking-profile selection in the frontend; the current UI correctly continues to use `default`.
- Final Azure model/provider choice, gateway identity details, and deployment configuration.
