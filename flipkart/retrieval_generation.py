"""The RAG conversation chain: history-aware retrieval, grounded answers, citations."""

from __future__ import annotations

import os
import threading
from collections import OrderedDict
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

from dotenv import load_dotenv
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.chat_history import BaseChatMessageHistory, InMemoryChatMessageHistory
from langchain_core.documents import Document
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain_core.retrievers import BaseRetriever
from langchain_core.runnables.history import RunnableWithMessageHistory

DEFAULT_MODEL = "llama-3.3-70b-versatile"

REPHRASE_PROMPT = (
    "Given the chat history and the latest user question, write a standalone search query "
    "for a product-review database. Keep product names, brands, budgets and features. "
    "Do NOT answer the question; only return the query."
)

SYSTEM_PROMPT = """You are a shopping assistant for an e-commerce store. You answer using \
real customer reviews retrieved for each question.

Rules:
- Base product claims only on the reviews in CONTEXT. Each review starts with its number, \
for example [1]. Cite reviews you rely on with those numbers.
- If the reviews don't cover the question, say so plainly and suggest what to ask instead. \
Never invent products, prices or specs.
- Keep answers short and scannable. Use bullet points when comparing products.
- For greetings or small talk, reply briefly and steer back to shopping.

CONTEXT:
{context}"""

# How each retrieved review is shown to the LLM; the number matches the citation.
DOCUMENT_PROMPT = PromptTemplate.from_template("[{index}] {product_name} (rating {rating}/5): {page_content}")


@dataclass(frozen=True)
class Source:
    index: int
    product_name: str
    rating: float | None
    summary: str
    snippet: str

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


def _number_documents(docs: list[Document]) -> list[Document]:
    """Add a 1-based ``index`` to metadata so the prompt and citations line up."""
    numbered = []
    for i, doc in enumerate(docs, start=1):
        metadata = {"product_name": "Unknown product", "rating": "n/a", **doc.metadata, "index": i}
        numbered.append(Document(page_content=doc.page_content, metadata=metadata))
    return numbered


def sources_from_documents(docs: list[Document], snippet_chars: int = 180) -> list[Source]:
    sources = []
    for i, doc in enumerate(docs, start=1):
        text = " ".join(doc.page_content.split())
        if len(text) > snippet_chars:
            text = text[: snippet_chars - 1].rstrip() + "…"
        rating = doc.metadata.get("rating")
        sources.append(
            Source(
                index=doc.metadata.get("index", i),
                product_name=str(doc.metadata.get("product_name", "Unknown product")),
                rating=rating if isinstance(rating, (int, float)) else None,
                summary=str(doc.metadata.get("summary", "")),
                snippet=text,
            )
        )
    return sources


class SessionStore:
    """Bounded in-memory chat histories: last ``max_messages`` per session, LRU over sessions."""

    def __init__(self, max_sessions: int = 1000, max_messages: int = 12):
        self.max_sessions = max_sessions
        self.max_messages = max_messages
        self._histories: OrderedDict[str, InMemoryChatMessageHistory] = OrderedDict()
        self._lock = threading.Lock()

    def get(self, session_id: str) -> BaseChatMessageHistory:
        with self._lock:
            history = self._histories.pop(session_id, None) or InMemoryChatMessageHistory()
            if len(history.messages) > self.max_messages:
                history.messages = history.messages[-self.max_messages :]
            self._histories[session_id] = history
            while len(self._histories) > self.max_sessions:
                self._histories.popitem(last=False)
            return history

    def clear(self, session_id: str) -> None:
        with self._lock:
            self._histories.pop(session_id, None)

    def __len__(self) -> int:
        return len(self._histories)


class ChatbotManager:
    """Builds the RAG chain once and serves answers per session.

    Every dependency can be injected, so tests run with fake models and retrievers
    and no API keys. With nothing injected it uses Groq and the AstraDB store.
    """

    def __init__(
        self,
        model: BaseChatModel | None = None,
        retriever: BaseRetriever | None = None,
        rephrase_model: BaseChatModel | None = None,
        sessions: SessionStore | None = None,
        top_k: int = 4,
    ):
        load_dotenv()
        self.model = model or self._default_model(temperature=0.3)
        # Query rewriting should be deterministic and is never streamed to the user.
        self.rephrase_model = rephrase_model or (
            self.model if model is not None else self._default_model(temperature=0.0)
        )
        if retriever is None:
            from flipkart.data_ingestion import DataIngestionManager

            retriever = DataIngestionManager().retriever(k=top_k)
        self.retriever = retriever
        self.sessions = sessions or SessionStore()
        self.chain = self._build_chain()

    @staticmethod
    def _default_model(temperature: float) -> BaseChatModel:
        from langchain_groq import ChatGroq

        return ChatGroq(model=os.getenv("GROQ_MODEL", DEFAULT_MODEL), temperature=temperature)

    def _build_chain(self) -> RunnableWithMessageHistory:
        rephrase_prompt = ChatPromptTemplate.from_messages(
            [("system", REPHRASE_PROMPT), MessagesPlaceholder("chat_history"), ("human", "{input}")]
        )
        history_aware_retriever = (
            create_history_aware_retriever(self.rephrase_model, self.retriever, rephrase_prompt)
            | _number_documents
        )

        qa_prompt = ChatPromptTemplate.from_messages(
            [("system", SYSTEM_PROMPT), MessagesPlaceholder("chat_history"), ("human", "{input}")]
        )
        answer_chain = create_stuff_documents_chain(self.model, qa_prompt, document_prompt=DOCUMENT_PROMPT)
        rag_chain = create_retrieval_chain(history_aware_retriever, answer_chain)

        return RunnableWithMessageHistory(
            rag_chain,
            self.sessions.get,
            input_messages_key="input",
            history_messages_key="chat_history",
            output_messages_key="answer",
        )

    @staticmethod
    def _config(session_id: str) -> dict[str, Any]:
        return {"configurable": {"session_id": session_id}}

    def ask(self, question: str, session_id: str) -> dict[str, Any]:
        """Answer a question and return ``{"answer": str, "sources": [Source, ...]}``."""
        result = self.chain.invoke({"input": question}, config=self._config(session_id))
        return {"answer": result["answer"], "sources": sources_from_documents(result["context"])}

    def stream(self, question: str, session_id: str) -> Iterator[tuple[str, Any]]:
        """Yield ``("sources", [Source, ...])`` once retrieval finishes, then ``("token", str)``.

        Tokens come straight from the LLM as it generates, so the UI shows the
        answer while it is being written.
        """
        for chunk in self.chain.stream({"input": question}, config=self._config(session_id)):
            if "context" in chunk:
                yield "sources", sources_from_documents(chunk["context"])
            if chunk.get("answer"):
                yield "token", chunk["answer"]

    def reset(self, session_id: str) -> None:
        self.sessions.clear(session_id)


def main() -> None:
    chatbot = ChatbotManager()
    session = "cli"
    questions = ("What are the best bluetooth earbuds under 2000?", "Which of those has the best battery?")
    for question in questions:
        result = chatbot.ask(question, session)
        print(f"\nQ: {question}\nA: {result['answer']}")
        for src in result["sources"]:
            print(f"   [{src.index}] {src.product_name} ({src.rating})")


if __name__ == "__main__":
    main()
