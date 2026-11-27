import pytest
from langchain_core.documents import Document
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.retrievers import BaseRetriever

from flipkart.retrieval_generation import ChatbotManager

REVIEWS = [
    Document(
        page_content="Amazing bass and the battery easily lasts two days.",
        metadata={"product_name": "boAt Airdopes 141", "rating": 5.0, "summary": "Superb"},
    ),
    Document(
        page_content="Sound is fine but the case feels cheap.",
        metadata={"product_name": "realme Buds Q2", "rating": 3.0, "summary": "Okay"},
    ),
]


class RecordingRetriever(BaseRetriever):
    """Returns fixed documents and remembers every query it was asked."""

    docs: list[Document]
    queries: list[str] = []

    def _get_relevant_documents(self, query, *, run_manager=None):
        self.queries.append(query)
        return self.docs


@pytest.fixture
def retriever():
    return RecordingRetriever(docs=REVIEWS, queries=[])


@pytest.fixture
def make_chatbot(retriever):
    def _make(answers, rephrases=("standalone query",), **kwargs):
        return ChatbotManager(
            model=FakeListChatModel(responses=list(answers)),
            rephrase_model=FakeListChatModel(responses=list(rephrases)),
            retriever=retriever,
            **kwargs,
        )

    return _make
