---
applyTo: "src/**/*eval*.py,src/**/*metric*.py,src/**/*dataset*.py,tests/**/*eval*.py,tests/**/*metric*.py,docs/**/*eval*.*,docs/**/*benchmark*.*"
---

# Evaluation instructions

These instructions apply to evaluation datasets, metrics, benchmark scripts, and regression tracking.

## Baseline assumptions
- Use pytest-compatible smoke checks for CI.
- Keep richer benchmark flows available for local runs.
- Separate retrieval evaluation from answer evaluation.

## Required behavior
- Store evaluation cases in structured files with question, expected facts, and optional expected source hints.
- Record latency and failures alongside quality metrics.
- Maintain a golden set of real developer questions.
- Make comparison between runs possible.

## Testing and reporting
- Add tests for dataset loading and metric helpers.
- Avoid fragile thresholds unless fixtures are stable.
- Report whether failures came from ingestion, retrieval, reranking, prompting, or generation.
