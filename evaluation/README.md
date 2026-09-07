# Golden Evaluation Dataset

Add one JSON object per line to `golden_cases.jsonl`. Every case needs a
human-verified answer fact; do not copy a model answer into this file.

```json
{"id":"shareholder-meeting-authority","question":"Who has the power to call a special shareholder meeting?","expected_facts":["<verified fact from the document>"],"expected_source_hints":["cheveddendominos-pizza.pdf"],"chunking_profile":"default"}
```

`expected_source_hints` is optional. Use a document filename, stable path
fragment, or document ID. Keep real cases in `golden_cases.jsonl`; this README
contains the template because the expected fact still requires human review.
