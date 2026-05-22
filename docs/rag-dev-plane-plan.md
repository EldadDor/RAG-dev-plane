🛠️ PLAN Document: Building a Production-Ready RAG Pipeline (LangChain v0.2+ & LCEL, 2026)

    Key Takeaway:
    This PLAN provides a step-by-step, phase-based blueprint for implementing a robust Retrieval-Augmented Generation (RAG) pipeline using modern best practices and LangChain v0.2+ LCEL. Each phase includes rationale, design decisions, and Python code snippets ready for coding agents. 

📋 Phase 1: Document Ingestion & Chunking
1.1 Document Loaders
Goal: Ingest diverse document types (PDF, HTML, Markdown, plain text) with structure and metadata preserved.
File Type	Loader (LangChain)	Key Params/Notes	Example Code Snippet
PDF	OpenDataLoaderPDFLoader	format, split_pages, use_struct_tree	See below
HTML	UnstructuredHTMLLoader	mode="elements" for tag-based splitting	See below
Markdown	UnstructuredMarkdownLoader	mode="elements" or mode="paged"	See below
Plain Text	TextLoader	Simple, for .txt files	See below
Batch	DirectoryLoader + loader_cls	For batch ingestion, supports multithreading	See below
PDF Example:			
python

from langchain_community.document_loaders import OpenDataLoaderPDFLoader

loader = OpenDataLoaderPDFLoader(
    file_path="path/to/file.pdf",
    format="markdown",
    split_pages=True,
    use_struct_tree=True,
)
documents = loader.load()

HTML Example:
python

from langchain_community.document_loaders import UnstructuredHTMLLoader

loader = UnstructuredHTMLLoader(
    file_path="path/to/file.html",
    mode="elements"
)
documents = loader.load()

Markdown Example:
python

from langchain_community.document_loaders import UnstructuredMarkdownLoader

loader = UnstructuredMarkdownLoader(
    file_path="path/to/file.md",
    mode="elements"
)
documents = loader.load()

Plain Text Example:
python

from langchain_community.document_loaders import TextLoader

loader = TextLoader("path/to/file.txt")
documents = loader.load()

Batch Ingestion Example:
python

from langchain_community.document_loaders import DirectoryLoader, UnstructuredMarkdownLoader

loader = DirectoryLoader(
    path="docs/",
    glob="**/*.md",
    loader_cls=UnstructuredMarkdownLoader,
    loader_kwargs={"mode": "elements"},
    show_progress=True,
    use_multithreading=True
)
documents = loader.load()

    Key Finding: Always preserve and propagate metadata (source, page, section) for downstream filtering and traceability
    . 

1.2 Chunking Strategies
Goal: Split documents into contextually meaningful chunks for embedding and retrieval.
Strategy	When to Use	Key Params/Tradeoffs	Example Code Snippet
Fixed-Size	Simple, uniform text	May break context	See below
Recursive Character (default)	Most use cases, preserves context	chunk_size=512, chunk_overlap=80	See below
Semantic Chunking	High-accuracy, topic shifts	More expensive, higher recall	See below
Structure-Aware	Markdown/HTML, logical sections	Preserves document structure	See below
Recursive Character Chunking (Recommended Default):			
python

from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=512,
    chunk_overlap=80,
    separators=["\n\n", "\n", ". ", " ", ""]
)
chunks = splitter.split_documents(documents)

Markdown Header Chunking:
python

from langchain.text_splitter import MarkdownHeaderTextSplitter

splitter = MarkdownHeaderTextSplitter(headers_to_split_on=["#", "##", "###"])
chunks = splitter.split_documents(documents)

Semantic Chunking (LlamaIndex):
python

from llama_index.node_parser import SemanticSplitterNodeParser

parser = SemanticSplitterNodeParser(
    chunk_size=512,
    chunk_overlap=80,
    similarity_threshold=0.8
)
chunks = parser.get_nodes_from_documents(documents)

    Design Decision: Use 10–20% overlap to preserve context across chunks. For PDFs with strong page semantics, use split_pages=True
    . 

📋 Phase 2: Embedding Generation & Vector Database Setup
2.1 Embedding Model Selection
Model	Pros/Cons	When to Use	Example Code Snippet
OpenAI text-embedding-3-large	High accuracy, 8192 tokens, paid	Production, best accuracy	See below
OpenAI text-embedding-3-small	Lower cost, smaller vectors	Dev/test, cost-sensitive	See below
HuggingFace sentence-transformers/all-MiniLM-L6-v2	Open-source, fast, local	On-prem, cost-sensitive	See below
Cohere Embed	Multilingual, competitive accuracy	Multilingual, alternative to OpenAI	See below
OpenAI Example:			
python

from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
vectors = embeddings.embed_documents([chunk.page_content for chunk in chunks])

HuggingFace Example:
python

from langchain_community.embeddings import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vectors = embeddings.embed_documents([chunk.page_content for chunk in chunks])

2.2 Vector Database Setup
Vector DB	Use Case	Persistence	Metadata Filtering	Example Code Snippet
ChromaDB	Dev/local	Yes	No	See below
Qdrant	Production	Yes	Yes	See below
Pinecone	Managed/Scalable	Yes	Yes	See below
Weaviate	Managed/Scalable	Yes	Yes	See below
ChromaDB Example:				
python

from langchain_community.vectorstores import Chroma

vectorstore = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory="./chroma_db"
)

Qdrant Example:
python

from langchain_community.vectorstores import QdrantVectorStore

vectorstore = QdrantVectorStore.from_documents(
    documents=chunks,
    embedding=embeddings,
    url="http://localhost:6333",
    collection_name="my_docs",
    persist=True
)

Metadata Filtering Example (Qdrant):
python

results = vectorstore.similarity_search(
    query_vector,
    filter={"metadata": {"source": "manual.pdf", "section": "Introduction"}}
)

    Key Finding: Always store and propagate metadata for filtering and traceability. Use persistent vector stores for production. 

📋 Phase 3: Retrieval Chain & Prompt Engineering
3.1 Retrieval Strategies
Strategy	Purpose/When to Use	Key Params/Notes	Example Code Snippet
Similarity Search	Standard dense retrieval	k (top results)	See below
MMR	Diverse, relevant results	lambda_mult	See below
Hybrid (BM25+dense)	Combine keyword & semantic	weights for each retriever	See below
SelfQueryRetriever	LLM-generated structured queries	Needs LLM, metadata fields	See below
CrossEncoderReranker	Precision re-ranking	Cross-encoder model	See below
MultiQueryRetriever	Query expansion for recall	LLM for query variants	See below
Similarity Search:			
python

retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

MMR:
python

retriever = vectorstore.as_retriever(search_type="mmr", search_kwargs={"k": 5, "lambda_mult": 0.5})

Hybrid (BM25 + Dense):
python

from langchain.retrievers import BM25Retriever, EnsembleRetriever

bm25_retriever = BM25Retriever.from_documents(docs)
dense_retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

ensemble_retriever = EnsembleRetriever(
    retrievers=[bm25_retriever, dense_retriever],
    weights=[0.5, 0.5]
)

SelfQueryRetriever:
python

from langchain.retrievers.self_query.base import SelfQueryRetriever
from langchain_openai import ChatOpenAI

llm = ChatOpenAI()
self_query_retriever = SelfQueryRetriever.from_llm(
    llm=llm,
    retriever=vectorstore.as_retriever(),
    document_content_description="Support tickets",
    metadata_field_info=[...],
    search_kwargs={"k": 5}
)

CrossEncoderReranker:
python

from langchain.retrievers import CrossEncoderReranker

reranker = CrossEncoderReranker(model="BAAI/bge-reranker-v2-m3")
reranked_docs = reranker.rerank(query, docs)

MultiQueryRetriever:
python

from langchain.retrievers.multi_query import MultiQueryRetriever

multi_query_retriever = MultiQueryRetriever.from_llm(
    retriever=vectorstore.as_retriever(),
    llm=llm
)

3.2 Prompt Engineering Patterns
Pattern	Purpose/When to Use	Example Code Snippet
System Prompt	Set LLM behavior	See below
Context Injection	Insert retrieved docs as {context}	See below
Few-Shot Examples	Demonstrate answer style	See below
Chain-of-Thought	Step-by-step reasoning	See below
System Prompt:		
python

from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant. Use only the provided context to answer. If unsure, say 'I don't know.'"),
    ("human", "{question}"),
])

Context Injection:
python

prompt = ChatPromptTemplate.from_messages([
    ("system", "Answer using only the following context:\n{context}"),
    ("human", "{question}"),
])

Few-Shot Examples:
python

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a medical assistant."),
    ("human", "What is hypertension?"),
    ("ai", "Hypertension is high blood pressure."),
    ("human", "{question}"),
])

Chain-of-Thought:
python

prompt = ChatPromptTemplate.from_messages([
    ("system", "Answer the question step by step using the context."),
    ("human", "{question}"),
])

📋 Phase 4: LLM Integration & Conversational Memory
4.1 LCEL Chaining & LLM Integration
Goal: Compose retrieval, prompt, LLM, and output parsing in a declarative, maintainable pipeline.LCEL Pipe Operator Chaining:
python

from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser

llm = ChatOpenAI(model="gpt-4o", streaming=True)
chain = retriever | prompt | llm | StrOutputParser()

Streaming & Async:
python

# Streaming output
for chunk in chain.stream({"question": "Explain RAG pipelines"}):
    print(chunk, end="")

# Async call (in async context)
result = await chain.ainvoke({"question": "Explain RAG pipelines"})

Multi-Provider Support:
python

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_community.llms import ChatOllama

llm_openai = ChatOpenAI(model="gpt-4o")
llm_anthropic = ChatAnthropic(model="claude-3-opus")
llm_ollama = ChatOllama(model="llama3")

    Deprecated: Avoid LLMChain and old memory wrappers from LangChain v0.1. 

4.2 Conversational Memory Patterns
Pattern	Use Case	Example Code Snippet
ConversationBufferMemory	Full chat history	See below
ConversationSummaryMemory	Summarized for long conversations	See below
RunnableWithMessageHistory	LCEL-compatible chat history	See below
ConversationBufferMemory:		
python

from langchain.memory import ConversationBufferMemory

memory = ConversationBufferMemory()

ConversationSummaryMemory:
python

from langchain.memory import ConversationSummaryMemory

memory = ConversationSummaryMemory(llm=llm)

RunnableWithMessageHistory:
python

from langchain_core.runnables.history import RunnableWithMessageHistory

chain_with_history = RunnableWithMessageHistory(
    chain,
    memory=memory
)

📋 Phase 5: Evaluation & Testing Strategies
5.1 RAG Evaluation Frameworks
Framework	Metrics/Focus	Integration Style	Example Code Snippet
RAGAS	Faithfulness, answer relevancy, context precision/recall	Batch/dev eval	See below
DeepEval	50+ metrics, pytest-style, CI/CD	Pytest	See below
TruLens	RAG Triad, tracing, observability	Tracing + eval	See below
RAGAS Example:			
python

from ragas import evaluate
from datasets import Dataset

data = [
    {
        "question": "What is the capital of France?",
        "answer": "Paris is the capital of France.",
        "contexts": ["Paris is the capital and largest city of France."],
    },
]
dataset = Dataset.from_list(data)
result = evaluate(dataset)
print(result.scores)

DeepEval Example (Pytest):
python

import deepeval
from deepeval.metrics import FaithfulnessMetric, ContextPrecisionMetric

def test_rag_output():
    question = "What is the capital of France?"
    answer = "Paris is the capital of France."
    contexts = ["Paris is the capital and largest city of France."]

    faithfulness = FaithfulnessMetric()
    context_precision = ContextPrecisionMetric()
    assert faithfulness.evaluate(answer, contexts) > 0.8
    assert context_precision.evaluate(contexts, question) > 0.8

TruLens Example:
python

from trulens_eval import Feedback, Tru

tru = Tru()
@tru.feedback
def answer_relevance(query, answer):
    # Custom logic or use built-in metrics
    return some_metric(query, answer)

5.2 Synthetic QA Dataset Generation
RAGAS Synthetic Data Example:
python

from ragas.synthetic import KnowledgeGraph, SingleHopSpecificQuerySynthesizer

kg = KnowledgeGraph.from_documents(documents)
synthesizer = SingleHopSpecificQuerySynthesizer(llm=generator_llm)
queries = synthesizer.generate(kg, num_queries=100)

5.3 Unit & Integration Testing Patterns
Pytest Unit Test with Mocked Embeddings:
python

import pytest
from unittest.mock import MagicMock

def test_retriever_returns_relevant_context():
    retriever = MyRetriever()
    retriever.embed = MagicMock(return_value=[0.1, 0.2, 0.3])
    query = "What is the capital of France?"
    contexts = retriever.retrieve(query)
    assert "Paris" in " ".join(contexts)

End-to-End Integration Test:
python

def test_rag_pipeline_end_to_end():
    question = "What is the capital of France?"
    expected_answer = "Paris is the capital of France."
    answer, contexts = rag_pipeline.run(question)
    assert "Paris" in answer

5.4 Monitoring & Observability
LangSmith Tracing Setup:
python

from langchain.callbacks.tracers.langchain import LangSmithTracer

tracer = LangSmithTracer(project_name="my_rag_project")
rag_pipeline = MyRAGPipeline(callbacks=[tracer])

# During pipeline execution, traces are automatically logged
answer = rag_pipeline.run("What is the capital of France?")

    Best Practice: Log both retrieved contexts and generated answers for each query to enable post-hoc analysis and debugging. 

✅ Summary Table: Phase-by-Phase Blueprint
Phase	Key Steps & Tools	Code Snippet Reference
1	Document loaders (PDF, HTML, Markdown, Text, Directory), chunking (recursive, semantic, structure)	1.1, 1.2
2	Embedding model selection (OpenAI, HF, Cohere), vector DB setup (Chroma, Qdrant, Pinecone, Weaviate)	2.1, 2.2
3	Retrieval strategies (similarity, MMR, hybrid, self-query, reranker, multi-query), prompt patterns	3.1, 3.2
4	LCEL chaining, streaming/async, multi-provider LLMs, conversational memory patterns	4.1, 4.2
5	Evaluation (RAGAS, DeepEval, TruLens), synthetic QA, unit/integration tests, LangSmith tracing	5.1–5.4
🏁 Conclusion

    Key Takeaway:
    This PLAN provides a modular, phase-based approach for building, testing, and deploying a state-of-the-art RAG pipeline. Each phase is designed for clarity, maintainability, and production-readiness, with code coding agents. 

