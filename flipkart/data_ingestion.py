from langchain_astradb import AstraDBVectorStore
from langchain_community.embeddings import HuggingFaceInferenceAPIEmbeddings
import os
from flipkart.data_converter import dataconverter
from typing import Optional, Tuple, List
from langchain_core.documents import Document
from dotenv import load_dotenv

class DataIngestionManager:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Initialize configuration
        self.config = {
            "groq_api_key": os.getenv("GROQ_API_KEY"),
            "astra_db_api_endpoint": os.getenv("ASTRA_DB_API_ENDPOINT"),
            "astra_db_token": os.getenv("ASTRA_DB_APPLICATION_TOKEN"),
            "astra_db_keyspace": os.getenv("ASTRA_DB_KEYSPACE"),
            "hf_token": os.getenv("HF_TOKEN"),
            "collection_name": "Recommendation_chatbot"
        }
        
        # Initialize embedding model
        self.embedding = HuggingFaceInferenceAPIEmbeddings(
            api_key=self.config["hf_token"],
            model_name="BAAI/bge-base-en-v1.5"
        )
        
        # Initialize vector store
        self.vector_store = self._initialize_vector_store()

    def _initialize_vector_store(self) -> AstraDBVectorStore:
        """Initialize the AstraDB vector store with configuration."""
        return AstraDBVectorStore(
            embedding=self.embedding,
            collection_name=self.config["collection_name"],
            api_endpoint=self.config["astra_db_api_endpoint"],
            token=self.config["astra_db_token"],
            namespace=self.config["astra_db_keyspace"]
        )

    def ingest_data(self, status: Optional[bool] = None) -> Tuple[AstraDBVectorStore, Optional[List[str]]]:
        """
        Ingest data into AstraDB vector store.
        
        Args:
            status: Flag to determine if data should be ingested or just return vector store
            
        Returns:
            Tuple containing vector store and optionally inserted document IDs
        """
        if status is None:
            # Convert and ingest new data
            docs = dataconverter()
            insert_ids = self.vector_store.add_documents(docs)
            return self.vector_store, insert_ids
        
        return self.vector_store, None

    def search_similar_products(self, query: str, k: int = 4) -> List[Document]:
        """
        Search for similar products based on query.
        
        Args:
            query: Search query string
            k: Number of results to return
            
        Returns:
            List of similar documents
        """
        return self.vector_store.similarity_search(query, k=k)

def main():
    # Initialize manager
    manager = DataIngestionManager()
    
    # Ingest data and get vector store
    vstore, insert_ids = manager.ingest_data(None)
    
    if insert_ids:
        print(f"\nInserted {len(insert_ids)} documents.")
    
    # Example search
    results = manager.search_similar_products("looking for budget headphones with good bass")
    for result in results:
        print(f"Review: {result.page_content}")
        print(f"Product: {result.metadata['product_name']}")
        print(f"Rating: {result.metadata['rating']}")

if __name__ == "__main__":
    main()