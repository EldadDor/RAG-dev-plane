from __future__ import annotations

from collections.abc import AsyncIterator
from uuid import uuid4
import json
import re

from app.api.schemas import ChatResponse, SourceReference
from app.clients.chat_client import ChatClient
from app.config import Settings
from app.prompts.chat_prompt import build_context_prompt
from app.prompts.chat_prompt import QUESTION_REWRITE_SYSTEM_PROMPT
from app.prompts.chat_prompt import MEMORY_SUMMARY_SYSTEM_PROMPT
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

    async def _rewrite_question(self, question: str, history: list[ChatTurn], summary: str | None) -> str:
        if not history and not summary:
            return question

        history_text = "\n".join(f"{turn.role}: {turn.content}" for turn in history[-6:])
        prompt = (
            f"Session summary:\n{summary or '(none)'}\n\n"
            f"Recent conversation:\n{history_text or '(none)'}\n\nLatest question: {question}"
        )
        raw = await self._chat_client.create_chat_completion(
            self._settings.chat_model,
            prompt,
            system_prompt=QUESTION_REWRITE_SYSTEM_PROMPT,
        )
        rewritten = raw["choices"][0]["message"]["content"].strip()
        return rewritten or question

    async def _refresh_summary_if_needed(self, session_id: str) -> None:
        turns = await self._conversation_store.get_unsummarized_turns(session_id)
        if len(turns) < self._settings.memory_summary_after_turns:
            return
        existing_summary = await self._conversation_store.get_summary(session_id)
        turns_text = "\n".join(f"{turn.role}: {turn.content}" for turn in turns)
        prompt = f"Existing summary:\n{existing_summary or '(none)'}\n\nNew turns:\n{turns_text}"
        raw = await self._chat_client.create_chat_completion(
            self._settings.chat_model,
            prompt,
            system_prompt=MEMORY_SUMMARY_SYSTEM_PROMPT,
        )
        summary = raw["choices"][0]["message"]["content"].strip()
        if summary:
            await self._conversation_store.save_summary(session_id, summary)

    async def _answer_impl(
            self,
            question: str,
            top_k: int | None = None,
            include_debug: bool = False,
            session_id: str | None = None,
            workspace_id: str | None = None,
            owner_id: str = "local-dev",
    ) -> tuple[ChatResponse, str]:
        session_id = session_id or str(uuid4())
        workspace_id = workspace_id or self._settings.default_workspace_id
        await self._conversation_store.ensure_session(session_id, owner_id, workspace_id, question[:80])
        history = await self._conversation_store.get(session_id)
        summary = await self._conversation_store.get_summary(session_id)
        rewritten_question = await self._rewrite_question(question, history, summary)

        retrieved = await self._retrieval_service.retrieve(question=rewritten_question, top_k=top_k, workspace_id=workspace_id)
        if not retrieved:
            answer = "I don't know based on the indexed documents."
            await self._conversation_store.append(session_id, "user", question)
            await self._conversation_store.append(session_id, "assistant", answer)
            await self._conversation_store.update_session(session_id, owner_id, workspace_id, answer)
            try:
                await self._refresh_summary_if_needed(session_id)
            except Exception:
                # Memory enrichment must never make an otherwise valid answer fail.
                pass
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
            await self._conversation_store.update_session(session_id, owner_id, workspace_id, answer)
            try:
                await self._refresh_summary_if_needed(session_id)
            except Exception:
                pass

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
            workspace_id: str | None = None,
            owner_id: str = "local-dev",
    ) -> ChatResponse:
        response, _ = await self._answer_impl(
            question=question,
            top_k=top_k,
            include_debug=include_debug,
            session_id=session_id,
            workspace_id=workspace_id,
            owner_id=owner_id,
        )
        return response

    async def answer_stream(
            self,
            question: str,
            top_k: int | None = None,
            include_debug: bool = False,
            session_id: str | None = None,
            workspace_id: str | None = None,
            owner_id: str = "local-dev",
    ) -> AsyncIterator[str]:
        response, resolved_session_id = await self._answer_impl(
            question=question,
            top_k=top_k,
            include_debug=include_debug,
            session_id=session_id,
            workspace_id=workspace_id,
            owner_id=owner_id,
        )
        meta = {
            "session_id": resolved_session_id,
            "grounded": response.grounded,
            "sources": [source.model_dump() for source in response.sources],
            "debug": response.debug,
        }
        # Preserve every character in the completed answer.  The event name and
        # JSON envelope are the browser-facing contract; clients append
        # ``delta`` verbatim rather than trying to reconstruct whitespace.
        for token in re.findall(r"\S+\s*|\s+", response.answer):
            yield f"event: answer\ndata: {json.dumps({'delta': token}, ensure_ascii=False)}\n\n"
        yield f"event: meta\ndata: {json.dumps(meta, ensure_ascii=False)}\n\n"
        yield 'event: done\ndata: {"reason":"completed"}\n\n'
