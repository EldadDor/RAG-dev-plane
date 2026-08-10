from __future__ import annotations

from collections.abc import AsyncIterator
from uuid import uuid4
import json

from app.api.schemas import ChatResponse, SourceReference
from app.clients.chat_client import ChatClient
from app.config import Settings
from app.prompts.chat_prompt import build_context_prompt
from app.prompts.chat_prompt import QUESTION_REWRITE_SYSTEM_PROMPT
from app.services.retrieval_service import RetrievalService
from app.services.conversation_store import ChatTurn, ConversationStore, InMemoryConversationStore


class ChatService:
    def __init__(
            self,
            settings: Settings,
            retrieval_service: RetrievalService,
            chat_client: ChatClient,
            conversation_store: ConversationStore | None = None,
    ) -> None:
        self._settings = settings
        self._retrieval_service = retrieval_service
        self._chat_client = chat_client
        self._conversation_store = conversation_store or InMemoryConversationStore(settings.memory_max_turns)

    async def _rewrite_question(self, question: str, history: list[ChatTurn]) -> str:
        if not history:
            return question

        history_text = "\n".join(f"{turn.role}: {turn.content}" for turn in history[-6:])
        prompt = f"Conversation:\n{history_text}\n\nLatest question: {question}"
        raw = await self._chat_client.create_chat_completion(
            self._settings.chat_model,
            prompt,
            system_prompt=QUESTION_REWRITE_SYSTEM_PROMPT,
        )
        rewritten = raw["choices"][0]["message"]["content"].strip()
        return rewritten or question

    async def _answer_impl(
            self,
            question: str,
            top_k: int | None = None,
            include_debug: bool = False,
            session_id: str | None = None,
    ) -> tuple[ChatResponse, str]:
        session_id = session_id or str(uuid4())
        history = await self._conversation_store.get(session_id)
        rewritten_question = await self._rewrite_question(question, history)

        retrieved = await self._retrieval_service.retrieve(question=rewritten_question, top_k=top_k)
        if not retrieved:
            answer = "I don't know based on the indexed documents."
            await self._conversation_store.append(session_id, "user", question)
            await self._conversation_store.append(session_id, "assistant", answer)
            debug = None
            if include_debug:
                debug = {
                    "retrieved_count": 0,
                    "chat_model": self._settings.chat_model,
                    "embedding_model": self._settings.embedding_model,
                    "embedding_provider": self._settings.embedding_provider,
                    "session_id": session_id,
                    "rewritten_question": rewritten_question,
                }
            return ChatResponse(
                answer=answer,
                sources=[],
                grounded=False,
                session_id=session_id,
                debug=debug,
            ), session_id

        prompt = build_context_prompt(question, [item.text for item in retrieved])
        try:
            raw = await self._chat_client.create_chat_completion(self._settings.chat_model, prompt)
            answer = raw["choices"][0]["message"]["content"]
        except Exception:
            raise
        else:
            await self._conversation_store.append(session_id, "user", question)
            await self._conversation_store.append(session_id, "assistant", answer)

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
                "session_id": session_id,
                "rewritten_question": rewritten_question,
            }

        return ChatResponse(
            answer=answer,
            sources=sources,
            grounded=True,
            session_id=session_id,
            debug=debug,
        ), session_id

    async def answer(
            self,
            question: str,
            top_k: int | None = None,
            include_debug: bool = False,
            session_id: str | None = None,
    ) -> ChatResponse:
        response, _ = await self._answer_impl(
            question=question,
            top_k=top_k,
            include_debug=include_debug,
            session_id=session_id,
        )
        return response

    async def answer_stream(
            self,
            question: str,
            top_k: int | None = None,
            include_debug: bool = False,
            session_id: str | None = None,
    ) -> AsyncIterator[str]:
        response, resolved_session_id = await self._answer_impl(
            question=question,
            top_k=top_k,
            include_debug=include_debug,
            session_id=session_id,
        )
        meta = {
            "session_id": resolved_session_id,
            "grounded": response.grounded,
            "sources": [source.model_dump() for source in response.sources],
            "debug": response.debug,
        }
        yield f"event: meta\ndata: {json.dumps(meta, ensure_ascii=False)}\n\n"
        for token in response.answer.split():
            yield f"data: {token}\n\n"
        yield "event: done\ndata: [DONE]\n\n"
