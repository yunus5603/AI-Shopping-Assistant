"""Flask web app: chat UI plus a Server-Sent Events endpoint that streams answers."""

from __future__ import annotations

import json
import logging
import os
import secrets
import uuid
from collections.abc import Iterator
from typing import Any, Protocol

from dotenv import load_dotenv
from flask import Flask, Response, jsonify, render_template, request, session, stream_with_context

MAX_MESSAGE_CHARS = 1000

log = logging.getLogger("shopping_assistant")


class Chatbot(Protocol):
    def stream(self, question: str, session_id: str) -> Iterator[tuple[str, Any]]: ...

    def reset(self, session_id: str) -> None: ...


def _sse(payload: dict[str, Any]) -> str:
    return f"data: {json.dumps(payload)}\n\n"


def _session_id() -> str:
    """A random id kept in a signed cookie, so each browser gets its own memory."""
    if "sid" not in session:
        session["sid"] = uuid.uuid4().hex
    return session["sid"]


def create_app(chatbot: Chatbot | None = None) -> Flask:
    load_dotenv()
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    app = Flask(__name__, static_folder="static", template_folder="templates")
    secret = os.getenv("FLASK_SECRET_KEY")
    if not secret:
        log.warning("FLASK_SECRET_KEY not set; sessions reset when the app restarts.")
    app.secret_key = secret or secrets.token_hex(32)
    app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")

    if chatbot is None:
        from flipkart.retrieval_generation import ChatbotManager

        chatbot = ChatbotManager()

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/health")
    def health():
        return jsonify(status="ok")

    @app.post("/get")
    def chat():
        msg = (request.form.get("msg") or "").strip()
        if not msg:
            return jsonify(error="No message provided"), 400
        if len(msg) > MAX_MESSAGE_CHARS:
            return jsonify(error=f"Message is longer than {MAX_MESSAGE_CHARS} characters"), 400

        sid = _session_id()
        log.info("chat session=%s chars=%d", sid[:8], len(msg))

        def generate() -> Iterator[str]:
            try:
                for kind, value in chatbot.stream(msg, sid):
                    if kind == "token":
                        yield _sse({"token": value})
                    elif kind == "sources":
                        yield _sse({"sources": [s.to_dict() for s in value]})
            except Exception:
                log.exception("generation failed session=%s", sid[:8])
                yield _sse({"error": "Sorry, something went wrong. Please try again."})
            yield _sse({"done": True})

        return Response(
            stream_with_context(generate()),
            mimetype="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    @app.post("/reset")
    def reset():
        chatbot.reset(_session_id())
        return jsonify(status="cleared")

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def internal_error(error):
        log.error("server error: %s", error)
        return render_template("500.html"), 500

    return app


if __name__ == "__main__":
    create_app().run(
        host=os.getenv("FLASK_HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", os.getenv("FLASK_PORT", "5000"))),
        debug=os.getenv("FLASK_DEBUG", "false").lower() == "true",
    )
