from flask import Flask, render_template, request, jsonify, Response, stream_with_context
from flipkart.retrieval_generation import ChatbotManager
from flipkart.callbacks import StreamingCallback
from typing import Dict, Any
import logging
from logging.handlers import RotatingFileHandler
import os
from dotenv import load_dotenv
import json
from queue import Queue

class FlipkartAssistant:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Initialize Flask app
        self.app = Flask(__name__,
            static_folder='static',  # Define static folder
            template_folder='templates'  # Define templates folder
        )
        
        # Configure logging
        self._setup_logging()
        
        # Initialize chatbot manager
        self.chatbot = ChatbotManager()
        
        # Create conversation chain
        self.conversation_chain = self.chatbot.create_conversation_chain()
        
        # Setup routes
        self._setup_routes()
        
        # Session storage for conversation history
        self.sessions: Dict[str, Any] = {}

    def _setup_logging(self) -> None:
        """Configure application logging."""
        if not os.path.exists('logs'):
            os.makedirs('logs')
            
        file_handler = RotatingFileHandler(
            'logs/flipkart_assistant.log',
            maxBytes=10240,
            backupCount=10
        )
        
        formatter = logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        )
        file_handler.setFormatter(formatter)
        
        self.app.logger.addHandler(file_handler)
        self.app.logger.setLevel(logging.INFO)
        self.app.logger.info('Flipkart Assistant startup')

    def _setup_routes(self) -> None:
        """Setup Flask route handlers."""
        
        @self.app.route("/")
        def index():
            """Render the chat interface."""
            return render_template("index.html")

        @self.app.route("/get", methods=["POST"])
        def chat():
            """Handle chat messages with streaming response."""
            try:
                msg = request.form.get("msg")
                if not msg:
                    return jsonify({"error": "No message provided"}), 400

                self.app.logger.info(f"Received message: {msg}")
                
                # Create queue for streaming tokens
                queue = Queue()
                streaming_callback = StreamingCallback(queue)

                # Create conversation chain with streaming callback
                conversation_chain = self.chatbot.create_conversation_chain(streaming_callback)

                def generate():
                    try:
                        self.app.logger.info("Starting LLM generation")
                        
                        # Start LLM generation with the streaming-enabled chain
                        conversation_chain.invoke(
                            {"input": msg},
                            config={
                                "configurable": {"session_id": request.remote_addr}
                            }
                        )
                        
                        self.app.logger.info("LLM generation started")
                        
                        # Stream tokens as they come
                        while True:
                            token = queue.get(timeout=30)
                            if token is None:  # End of streaming
                                self.app.logger.info("Streaming completed")
                                break
                            yield f"data: {json.dumps({'token': token})}\n\n"
                            
                    except Exception as e:
                        self.app.logger.error(f"Streaming error: {str(e)}")
                        yield f"data: {json.dumps({'error': str(e)})}\n\n"

                return Response(
                    stream_with_context(generate()),
                    mimetype='text/event-stream',
                    headers={
                        'Cache-Control': 'no-cache',
                        'X-Accel-Buffering': 'no'
                    }
                )

            except Exception as e:
                self.app.logger.error(f'Error processing message: {str(e)}')
                return jsonify({
                    "error": "An error occurred processing your request"
                }), 500

        @self.app.errorhandler(404)
        def not_found_error(error):
            """Handle 404 errors."""
            return render_template('404.html'), 404

        @self.app.errorhandler(500)
        def internal_error(error):
            """Handle 500 errors."""
            self.app.logger.error(f'Server Error: {str(error)}')
            return render_template('500.html'), 500

    def run(self, host: str = "0.0.0.0", port: int = 5000, debug: bool = False) -> None:
        """Run the Flask application."""
        self.app.run(host=host, port=port, debug=debug)

def create_app() -> Flask:
    """Create and configure the Flask application."""
    assistant = FlipkartAssistant()
    return assistant.app

def main():
    """Main entry point for the application."""
    assistant = FlipkartAssistant()
    
    # Get configuration from environment variables
    host = os.getenv("FLASK_HOST", "0.0.0.0")
    port = int(os.getenv("FLASK_PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    
    assistant.run(host=host, port=port, debug=debug)

if __name__ == '__main__':
    main()