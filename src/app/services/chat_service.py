from __future__ import annotations

import asyncio
from collections import defaultdict
from collections.abc import AsyncIterator
from dataclasses import dataclass
from uuid import uuid4
import json

from app.api.schemas import ChatResponse, SourceReference
from app.clients.chat_client import ChatClient
from app.config import Settings
from app.prompts.chat_prompt import build_context_prompt
from app.services.retrieval_service import RetrievalService


@dataclass
class ChatTurn:
    role: str
    content: str


class ConversationStore:
    def __init__(self, max_turns: int = 10) -> None:
        self._max_turns = max_turns
        self._sessions: dict[str, list[ChatTurn]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def get(self, session_id: str) -> list[ChatTurn]:
        async with self._lock:
            return list(self._sessions.get(session_id, []))

    async def append(self, session_id: str, role: str, content: str) -> None:
        async with self._lock:
            turns = self._sessions[session_id]
            turns.append(ChatTurn(role=role, content=content))
            self._sessions[session_id] = turns[-self._max_turns:]


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
        self._conversation_store = conversation_store or ConversationStore()

    async def _rewrite_question(self, question: str, history: list[ChatTurn]) -> str:
        if not history:
            return question

        history_text = "
".join(f"{turn.role}: {turn.content}" for turn in history[-6:])
prompt = [
    {
        "role": "system",
        "content": (
            "Rewrite the user's latest question into a standalone retrieval query. "
            "Use conversation context only when needed to resolve references. "
            "Return only the rewritten question."
        ),
    },
    {
        "role": "user",
        "content": f"Conversation:
        {history_text}

            Latest question: {question}",
    },
]
raw = await self._chat_client.create_chat_completion(self._settings.chat_model, prompt)
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
        return ChatResponse(answer=answer, sources=[], grounded=False, debug=debug), session_id

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

    await self._conversation_store.append(session_id, "user", question)
    await self._conversation_store.append(session_id, "assistant", answer)

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

    return ChatResponse(answer=answer, sources=sources, grounded=True, debug=debug), session_id

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
