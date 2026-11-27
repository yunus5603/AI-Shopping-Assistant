import json
from pathlib import Path

from langchain_core.language_models.fake_chat_models import FakeListChatModel

from eval.metrics import citations, parse_judge_score, retrieval_scores, summarize
from eval.run_eval import evaluate, load_golden_set


def test_retrieval_scores():
    assert retrieval_scores(["Great BASS", "nice case"], ["bass"]) == (True, 0.5)
    assert retrieval_scores(["nice case"], ["bass"]) == (False, 0.0)
    assert retrieval_scores([], ["bass"]) == (False, 0.0)


def test_citations():
    assert citations("Buy it [1][2].", 2) == (True, True)
    assert citations("Buy it [3].", 2) == (True, False)
    assert citations("No sources.", 2) == (False, True)


def test_parse_judge_score():
    assert parse_judge_score('{"score": 4, "reason": "ok"}') == 4
    assert parse_judge_score('Sure! {"score": "5"}') == 5
    assert parse_judge_score('{"score": 9}') is None
    assert parse_judge_score("no json") is None


def test_golden_set_is_well_formed():
    items = load_golden_set(Path(__file__).parent.parent / "eval" / "golden_set.jsonl")
    assert len({item["id"] for item in items}) == len(items)
    for item in items:
        assert item["question"]
        assert bool(item["relevant_keywords"]) == item["in_scope"]


def test_evaluate_end_to_end_with_fakes(make_chatbot):
    bot = make_chatbot(["Try boAt [1].", "I only know headphone reviews."])
    judge = FakeListChatModel(responses=['{"score": 5}', '{"score": 4}', '{"score": 5}'])
    items = [
        {"id": "a", "question": "bass?", "relevant_keywords": ["bass"], "in_scope": True},
        {"id": "b", "question": "fridge?", "relevant_keywords": [], "in_scope": False},
    ]

    records = evaluate(bot, judge, items)
    summary = summarize(records)

    assert summary.hit_rate == 1.0
    assert summary.precision == 0.5
    assert summary.faithfulness == 5 and summary.relevance == 4
    assert summary.citation_rate == 1.0 and summary.valid_citation_rate == 1.0
    assert summary.abstention_rate == 1.0
    assert "| Retrieval hit rate @k | 100% |" in summary.to_markdown()
    json.dumps(records)  # results file must be serializable
