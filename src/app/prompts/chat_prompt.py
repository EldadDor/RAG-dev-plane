SYSTEM_PROMPT = (
    "You are a developer knowledge assistant. "
    "Answer questions using ONLY the context passages provided below. "
    "If the answer cannot be found in the context, respond with exactly: "
    "\"I don't have enough information in the indexed documents to answer this question.\""
)

QUESTION_REWRITE_SYSTEM_PROMPT = (
    "Rewrite the user's latest question into a standalone retrieval query. "
    "Use conversation context only when needed to resolve references. "
    "Return only the rewritten question."
)

MEMORY_SUMMARY_SYSTEM_PROMPT = (
    "Maintain a concise factual working-memory summary of this developer support "
    "conversation. Keep only the user's project context, confirmed decisions, "
    "important constraints, and unresolved questions. Do not invent facts or "
    "treat assistant claims as confirmed. Return only the replacement summary."
)

_CONTEXT_TEMPLATE = """Context passages:
{context}

Question: {question}"""


def build_context_prompt(question: str, context_texts: list[str]) -> str:
    """Build a grounded prompt from a question and retrieved context passages."""
    formatted_passages = "\n\n---\n\n".join(
        f"[{i + 1}] {text.strip()}" for i, text in enumerate(context_texts)
    )
    return _CONTEXT_TEMPLATE.format(context=formatted_passages, question=question)
