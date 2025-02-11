from flask import Flask, render_template, request, jsonify
from flipkart.retrieval_generation import ChatbotManager
from typing import Dict, Any
import logging
from logging.handlers import RotatingFileHandler
import os
from dotenv import load_dotenv

class FlipkartAssistant:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Initialize Flask app
        self.app = Flask(__name__)
        
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
            """Handle chat messages."""
            try:
                if request.method != "POST":
                    return jsonify({"error": "Method not allowed"}), 405

                msg = request.form.get("msg")
                if not msg:
                    return jsonify({"error": "No message provided"}), 400

                # Generate unique session ID (in production, this should come from user authentication)
                session_id = request.remote_addr  # Simple example using IP address

                # Get response from chatbot
                response = self.conversation_chain.invoke(
                    {"input": msg},
                    config={"configurable": {"session_id": session_id}}
                )

                if not response or "answer" not in response:
                    raise ValueError("Invalid response from chatbot")

                return response["answer"]

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