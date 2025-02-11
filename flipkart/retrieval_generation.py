from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import MessagesPlaceholder, ChatPromptTemplate
from langchain.chains import create_history_aware_retriever
from langchain_groq import ChatGroq
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from flipkart.callbacks import StreamingCallback
from flipkart.data_ingestion import DataIngestionManager
from typing import Dict, Any, Optional, List
from queue import Queue
from dotenv import load_dotenv
import os

class ChatbotManager:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Initialize configuration
        self.config = {
            "groq_api_key": os.getenv("GROQ_API_KEY"),
            "model_name": "llama-3.3-70b-versatile",
            "temperature": 0.5
        }
        
        # Initialize chat store
        self.store: Dict[str, BaseChatMessageHistory] = {}
        
        # Initialize LLM with streaming enabled
        self.model = ChatGroq(
            model=self.config["model_name"],
            temperature=self.config["temperature"],
            streaming=True,  # Enable streaming
            callbacks=[]  # Will be set during invocation
        )
        
        # Initialize data manager
        self.data_manager = DataIngestionManager()

    def get_session_history(self, session_id: str) -> BaseChatMessageHistory:
        """Get or create chat history for a session."""
        if session_id not in self.store:
            self.store[session_id] = ChatMessageHistory()
        return self.store[session_id]

    def _create_retriever_chain(self, vstore: Any) -> Any:
        """Create the retriever chain with history awareness."""
        retriever = vstore.as_retriever(search_kwargs={"k": 3})

        retriever_prompt = (
            "Given a chat history and the latest user question, formulate a search query that will help find relevant information. "
            "If the question is about products or shopping, focus on those keywords. "
            "If it's a general question, formulate it clearly while maintaining context. "
            "Do NOT answer the question, just reformulate it if needed and otherwise return it as is."
        )

        contextualize_q_prompt = ChatPromptTemplate.from_messages([
            ("system", retriever_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}")
        ])

        return create_history_aware_retriever(
            self.model,
            retriever,
            contextualize_q_prompt
        )

    def create_conversation_chain(self, streaming_callback: Optional[StreamingCallback] = None) -> RunnableWithMessageHistory:
        """
        Create the complete conversation chain.
        
        Args:
            streaming_callback: Optional callback for streaming tokens
        """
        # Update model callbacks if streaming is requested
        if streaming_callback:
            self.model.callbacks = [streaming_callback]
        
        # Get vector store
        vstore, _ = self.data_manager.ingest_data(True)
        
        # Create retriever and QA chains
        history_aware_retriever = self._create_retriever_chain(vstore)
        
        # Create QA chain with streaming configuration
        qa_prompt = ChatPromptTemplate.from_messages([
            ("system", self._create_system_prompt()),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}")
        ])
        
        question_answer_chain = create_stuff_documents_chain(
            self.model,
            qa_prompt,
            document_variable_name="context"
        )
        
        # Create retrieval chain
        rag_chain = create_retrieval_chain(
            retriever=history_aware_retriever,
            combine_docs_chain=question_answer_chain,
        )

        return RunnableWithMessageHistory(
            rag_chain,
            self.get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history",
            output_messages_key="answer"
        )

    def _create_system_prompt(self) -> str:
        return """
        You are a helpful and knowledgeable e-commerce chatbot. Your primary expertise is in product recommendations and customer queries, 
        but you can also engage in general conversation while staying professional.

        When product-related context is available, use it to provide accurate recommendations and information.
        When asked general questions:
        - Provide helpful, concise responses
        - Stay professional and friendly
        - If the question is inappropriate or off-topic, politely guide the conversation back to shopping-related topics
        - Maintain ethical boundaries and avoid harmful content

        CONTEXT:
        {context}

        QUESTION: {input}

        YOUR ANSWER:
        """

def main():
    # Initialize chatbot manager
    chatbot = ChatbotManager()
    
    # Create conversation chain
    conversation_chain = chatbot.create_conversation_chain()
    
    # Example conversation
    session_id = "test_session"
    
    # First question
    response1 = conversation_chain.invoke(
        {"input": "Can you tell me the best bluetooth buds?"},
        config={"configurable": {"session_id": session_id}}
    )
    print("\nQuestion 1:", response1["answer"])
    
    # Follow-up question
    response2 = conversation_chain.invoke(
        {"input": "What was my previous question?"},
        config={"configurable": {"session_id": session_id}}
    )
    print("\nQuestion 2:", response2["answer"])

if __name__ == "__main__":
    main()





