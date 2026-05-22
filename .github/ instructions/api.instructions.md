---
applyTo: "src/**/*api*.py,src/**/routers/*.py,src/**/routes/*.py,src/**/schemas/*.py,tests/**/*api*.py"
---

# FastAPI API instructions

These instructions apply to FastAPI routers, schemas, and service wiring.

## API design rules
- Use FastAPI routers and explicit response models.
- Keep handlers thin; call service-layer functions for orchestration.
- Use dependency injection for settings, vector store clients, and model clients.
- Expose health and readiness endpoints.
- Return structured errors and avoid leaking provider internals in HTTP responses.

## Chat endpoint rules
- Chat endpoints must return answer text plus structured sources.
- Keep request and response schemas explicit with Pydantic models.
- Include optional debugging fields only behind explicit flags or non-production settings.
- Do not return raw provider responses directly.

## Testing
- Add API tests for success, validation failures, and insufficient-context behavior.
- Mock service dependencies at the API layer where appropriate.
