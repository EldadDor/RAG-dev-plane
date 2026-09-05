# Working on

- Backend NP-08: run one live chunking experiment with a named profile.
- Backend NP-08: configure a recursive-character experiment profile and run `dry_run` on representative documents.
- Backend NP-08: ingest that profile, query chat/retrieval with it, and verify it returns only experiment chunks.
- Backend NP-08: verify the `default` profile's 55 sources and 433 chunks remain unchanged after the experiment.
- Backend NP-08: record the live evidence, close the phase, and add its completion record.
- Frontend: no active implementation phase; FP-01 and FP-02 are complete.
- Planning: reconcile NP-11 in the backend roadmap with the frontend record that FP-01 is already closed and live streaming validation was completed.

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
- Whether NP-11 should be closed as satisfied or retained for a separate full operator checklist review.
- Final Azure model/provider choice, gateway identity details, and deployment configuration.
