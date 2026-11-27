from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.documents import Document
from langchain_core.messages import AIMessage, HumanMessage

from flipkart.retrieval_generation import SessionStore, sources_from_documents


def test_ask_returns_answer_and_numbered_sources(make_chatbot):
    bot = make_chatbot(["Go for the boAt Airdopes 141 [1]."])

    result = bot.ask("Best earbuds for bass?", "s1")

    assert result["answer"] == "Go for the boAt Airdopes 141 [1]."
    assert [(s.index, s.product_name, s.rating) for s in result["sources"]] == [
        (1, "boAt Airdopes 141", 5.0),
        (2, "realme Buds Q2", 3.0),
    ]


def test_retrieved_reviews_are_numbered_in_the_prompt(make_chatbot):
    bot = make_chatbot(["ok"])
    prompts = []

    class Spy(BaseCallbackHandler):
        def on_chat_model_start(self, serialized, messages, **kwargs):
            prompts.append(messages[0][0].content)

    bot.model.callbacks = [Spy()]
    bot.ask("bass?", "s1")

    assert "[1] boAt Airdopes 141 (rating 5.0/5): Amazing bass" in prompts[0]
    assert "[2] realme Buds Q2 (rating 3.0/5)" in prompts[0]


def test_first_turn_searches_with_the_raw_question(make_chatbot, retriever):
    bot = make_chatbot(["answer"])

    bot.ask("earbuds under 2000", "s1")

    assert retriever.queries == ["earbuds under 2000"]


def test_follow_up_is_rephrased_using_history(make_chatbot, retriever):
    bot = make_chatbot(["first", "second"], rephrases=["boAt Airdopes 141 battery life"])

    bot.ask("Best earbuds?", "s1")
    bot.ask("How is its battery?", "s1")

    assert retriever.queries == ["Best earbuds?", "boAt Airdopes 141 battery life"]


def test_history_is_kept_per_session(make_chatbot):
    bot = make_chatbot(["a1", "b1"])

    bot.ask("question from A", "A")
    bot.ask("question from B", "B")

    assert bot.sessions.get("A").messages == [HumanMessage("question from A"), AIMessage("a1")]
    assert bot.sessions.get("B").messages == [HumanMessage("question from B"), AIMessage("b1")]


def test_stream_yields_sources_then_tokens_and_saves_history(make_chatbot):
    bot = make_chatbot(["Try boAt [1]."])

    events = list(bot.stream("bass?", "s1"))

    kinds = [kind for kind, _ in events]
    assert kinds[0] == "sources"
    assert set(kinds[1:]) == {"token"}
    assert "".join(value for kind, value in events if kind == "token") == "Try boAt [1]."
    assert bot.sessions.get("s1").messages[-1] == AIMessage("Try boAt [1].")


def test_reset_clears_memory(make_chatbot):
    bot = make_chatbot(["a"])
    bot.ask("hi", "s1")

    bot.reset("s1")

    assert bot.sessions.get("s1").messages == []


def test_session_store_trims_old_messages():
    store = SessionStore(max_messages=4)
    history = store.get("s")
    for i in range(6):
        history.add_message(HumanMessage(f"m{i}"))

    assert [m.content for m in store.get("s").messages] == ["m2", "m3", "m4", "m5"]


def test_session_store_evicts_least_recently_used():
    store = SessionStore(max_sessions=2)
    store.get("a").add_message(HumanMessage("a"))
    store.get("b")
    store.get("a")  # touch a, so b is now the oldest
    store.get("c")

    assert len(store) == 2
    assert store.get("a").messages == [HumanMessage("a")]


def test_sources_truncate_long_reviews_and_handle_missing_metadata():
    doc = Document(page_content="word " * 100, metadata={})

    (source,) = sources_from_documents([doc], snippet_chars=20)

    assert source.product_name == "Unknown product"
    assert source.rating is None
    assert len(source.snippet) == 20 and source.snippet.endswith("…")
