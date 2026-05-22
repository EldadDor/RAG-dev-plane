SYSTEM_PROMPT = (
    "You are a developer knowledge assistant. "
    "Answer questions using ONLY the context passages provided below. "
    "If the answer cannot be found in the context, respond with exactly: "
    "\"I don't have enough information in the indexed documents to answer this question.\""
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
