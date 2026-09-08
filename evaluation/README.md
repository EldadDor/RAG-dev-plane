# Golden Evaluation Dataset

Add one JSON object per line to `golden-cases.jsonl`. Every case needs a
human-verified answer fact; do not copy a model answer into this file.

```json
{"id":"shareholder-meeting-authority","question":"Who has the power to call a special shareholder meeting?","expected_facts":["<verified fact from the document>"],"expected_source_hints":["cheveddendominos-pizza.pdf"],"chunking_profile":"default"}
```

`expected_source_hints` is optional. Use a document filename, stable path
fragment, or document ID. Keep real cases in `golden_cases.jsonl`; this README
contains the template because the expected fact still requires human review.

After creating the dataset, run an already-running local API without changing
the index:

```powershell
uv run python scripts/run_benchmark.py `
  --dataset evaluation/golden-cases.jsonl `
  --output evaluation/results/baseline.json
```

The runner makes repeated chat requests for each case to check retrieval
determinism. Those requests appear in Recent Chats; they do not ingest, delete,
or replace document chunks.
