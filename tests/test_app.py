import json

import pytest

from app import MAX_MESSAGE_CHARS, create_app
from flipkart.retrieval_generation import Source


class FakeChatbot:
    def __init__(self, fail=False):
        self.fail = fail
        self.calls = []
        self.resets = []

    def stream(self, question, session_id):
        self.calls.append((question, session_id))
        yield "sources", [Source(1, "boAt Airdopes 141", 5.0, "Superb", "Amazing bass")]
        if self.fail:
            raise RuntimeError("Groq is down: secret-internal-detail")
        yield "token", "Hello "
        yield "token", "there"

    def reset(self, session_id):
        self.resets.append(session_id)


@pytest.fixture
def bot():
    return FakeChatbot()


@pytest.fixture
def client(bot, monkeypatch):
    monkeypatch.setenv("FLASK_SECRET_KEY", "test")
    return create_app(chatbot=bot).test_client()


def events(response):
    body = response.get_data(as_text=True)
    return [json.loads(chunk[len("data: ") :]) for chunk in body.split("\n\n") if chunk]


def test_index_renders_chat_ui(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b'id="chatForm"' in response.data


def test_health(client):
    assert client.get("/health").get_json() == {"status": "ok"}


def test_unknown_route_uses_404_page(client):
    assert client.get("/nope").status_code == 404


@pytest.mark.parametrize("msg", ["", "   "])
def test_empty_message_rejected(client, msg):
    assert client.post("/get", data={"msg": msg}).status_code == 400


def test_overlong_message_rejected(client):
    response = client.post("/get", data={"msg": "x" * (MAX_MESSAGE_CHARS + 1)})
    assert response.status_code == 400


def test_chat_streams_sources_tokens_then_done(client):
    response = client.post("/get", data={"msg": "best earbuds?"})

    assert response.mimetype == "text/event-stream"
    assert events(response) == [
        {
            "sources": [
                {
                    "index": 1,
                    "product_name": "boAt Airdopes 141",
                    "rating": 5.0,
                    "summary": "Superb",
                    "snippet": "Amazing bass",
                }
            ]
        },
        {"token": "Hello "},
        {"token": "there"},
        {"done": True},
    ]


def test_errors_are_reported_without_leaking_details(monkeypatch):
    monkeypatch.setenv("FLASK_SECRET_KEY", "test")
    client = create_app(chatbot=FakeChatbot(fail=True)).test_client()

    received = events(client.post("/get", data={"msg": "hi"}))

    assert "error" in received[-2]
    assert "secret-internal-detail" not in json.dumps(received)
    assert received[-1] == {"done": True}


def test_same_browser_keeps_one_session(client, bot):
    client.post("/get", data={"msg": "one"}).get_data()
    client.post("/get", data={"msg": "two"}).get_data()

    (_, first), (_, second) = bot.calls
    assert first == second


def test_different_browsers_get_different_sessions(bot, monkeypatch):
    monkeypatch.setenv("FLASK_SECRET_KEY", "test")
    app = create_app(chatbot=bot)
    app.test_client().post("/get", data={"msg": "a"}).get_data()
    app.test_client().post("/get", data={"msg": "b"}).get_data()

    (_, first), (_, second) = bot.calls
    assert first != second


def test_reset_clears_this_sessions_memory(client, bot):
    client.post("/get", data={"msg": "one"}).get_data()

    assert client.post("/reset").get_json() == {"status": "cleared"}
    assert bot.resets == [bot.calls[0][1]]
