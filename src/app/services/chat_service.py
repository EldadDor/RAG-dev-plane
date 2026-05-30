from app.api.schemas import ChatResponse, SourceReference
from app.clients.chat_client import ChatClient
from app.config import Settings
from app.prompts.chat_prompt import build_context_prompt
from app.services.retrieval_service import RetrievalService


class ChatService:
    def __init__(self, settings: Settings, retrieval_service: RetrievalService, chat_client: ChatClient) -> None:
        self._settings = settings
        self._retrieval_service = retrieval_service
        self._chat_client = chat_client

    async def answer(self, question: str, top_k: int | None = None, include_debug: bool = False) -> ChatResponse:
        retrieved = await self._retrieval_service.retrieve(question=question, top_k=top_k)
        if not retrieved:
            return ChatResponse(
                answer="I don't know based on the indexed documents.",
                sources=[],
                grounded=False,
                debug={"retrieved_count": 0} if include_debug else None,
            )

        prompt = build_context_prompt(question, [item.text for item in retrieved])
        raw = await self._chat_client.create_chat_completion(self._settings.chat_model, prompt)
        answer = raw["choices"][0]["message"]["content"]
        sources = [
            SourceReference(
                doc_id=item.doc_id,
                chunk_id=item.chunk_id,
                source_path=item.source_path,
                title=item.title,
                page=item.page,
                section=item.section,
                score=item.score,
                snippet=item.text[:300],
            )
            for item in retrieved
        ]
        debug = None
        if include_debug:
            debug = {
                "retrieved_count": len(retrieved),
                "chat_model": self._settings.chat_model,
                "embedding_model": self._settings.embedding_model,
                "embedding_provider": self._settings.embedding_provider,
            }
        return ChatResponse(answer=answer, sources=sources, grounded=True, debug=debug)
