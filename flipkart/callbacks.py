from langchain.callbacks.base import BaseCallbackHandler
from typing import Any, Dict, List
from queue import Queue

class StreamingCallback(BaseCallbackHandler):
    """Callback handler for streaming LLM responses."""
    
    def __init__(self, queue: Queue):
        """Initialize with a queue to store tokens."""
        self.queue = queue

    def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        """Run on new LLM token. Push tokens to queue."""
        if token:  # Only push non-empty tokens
            self.queue.put(token)

    def on_llm_end(self, response: Any, **kwargs: Any) -> None:
        """Run when LLM ends running."""
        # Signal that we're done
        self.queue.put(None)

    def on_llm_error(self, error: Exception, **kwargs: Any) -> None:
        """Run when LLM errors."""
        print(f"LLM Error: {str(error)}")  # Add logging
        self.queue.put(None) 