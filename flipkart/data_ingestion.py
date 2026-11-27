"""Embed product reviews and store them in AstraDB.

Run ``python -m flipkart.data_ingestion`` once to load the CSV into the
vector store. The web app only reads from the store.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStore

from flipkart.data_converter import dataconverter

EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"
DEFAULT_COLLECTION = "Recommendation_chatbot"


@dataclass
class AstraConfig:
    api_endpoint: str
    token: str
    keyspace: str | None
    hf_token: str
    collection_name: str = DEFAULT_COLLECTION
    embedding_model: str = EMBEDDING_MODEL

    @classmethod
    def from_env(cls) -> AstraConfig:
        load_dotenv()
        required = {
            "ASTRA_DB_API_ENDPOINT": os.getenv("ASTRA_DB_API_ENDPOINT"),
            "ASTRA_DB_APPLICATION_TOKEN": os.getenv("ASTRA_DB_APPLICATION_TOKEN"),
            "HF_TOKEN": os.getenv("HF_TOKEN"),
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise RuntimeError(
                f"Missing environment variables: {', '.join(missing)}. Copy .env.example to .env."
            )
        return cls(
            api_endpoint=required["ASTRA_DB_API_ENDPOINT"],
            token=required["ASTRA_DB_APPLICATION_TOKEN"],
            keyspace=os.getenv("ASTRA_DB_KEYSPACE") or None,
            hf_token=required["HF_TOKEN"],
            collection_name=os.getenv("ASTRA_DB_COLLECTION", DEFAULT_COLLECTION),
        )


@dataclass
class DataIngestionManager:
    """Owns the vector store. Pass ``vector_store`` to skip AstraDB (tests, local runs)."""

    config: AstraConfig | None = None
    vector_store: VectorStore | None = field(default=None)

    def __post_init__(self) -> None:
        if self.vector_store is None:
            self.config = self.config or AstraConfig.from_env()
            self.vector_store = self._connect(self.config)

    @staticmethod
    def _connect(config: AstraConfig) -> VectorStore:
        # Imported lazily so tests and tooling don't need the AstraDB client.
        from langchain_astradb import AstraDBVectorStore
        from langchain_community.embeddings import HuggingFaceInferenceAPIEmbeddings

        embedding = HuggingFaceInferenceAPIEmbeddings(
            api_key=config.hf_token, model_name=config.embedding_model
        )
        return AstraDBVectorStore(
            embedding=embedding,
            collection_name=config.collection_name,
            api_endpoint=config.api_endpoint,
            token=config.token,
            namespace=config.keyspace,
        )

    def ingest(self, docs: list[Document] | None = None) -> list[str]:
        """Embed and insert documents (defaults to the full review CSV)."""
        docs = dataconverter() if docs is None else docs
        return self.vector_store.add_documents(docs)

    def retriever(self, k: int = 4):
        return self.vector_store.as_retriever(search_kwargs={"k": k})

    def search_similar_products(self, query: str, k: int = 4) -> list[Document]:
        return self.vector_store.similarity_search(query, k=k)


def main() -> None:
    manager = DataIngestionManager()
    ids = manager.ingest()
    print(f"Inserted {len(ids)} reviews into '{manager.config.collection_name}'.")
    for doc in manager.search_similar_products("budget headphones with good bass"):
        print(f"- {doc.metadata['product_name']} ({doc.metadata['rating']}): {doc.page_content[:80]}")


if __name__ == "__main__":
    main()
