"""Evaluate the RAG pipeline against eval/golden_set.jsonl.

Measures retrieval (keyword hit rate and precision over the top-k reviews),
answer faithfulness and relevance with an LLM judge, citation use, and whether
out-of-scope questions are declined instead of answered from thin air.

Usage (needs the same .env as the app, with data already ingested):

    python -m eval.run_eval              # full run, writes eval/results/latest.json
    python -m eval.run_eval --limit 5    # quick smoke run
"""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

from eval.metrics import citations, parse_judge_score, retrieval_scores, summarize

HERE = Path(__file__).parent

FAITHFULNESS_PROMPT = """You are grading a shopping assistant. Score how well every claim in the \
ANSWER is supported by the REVIEWS (5 = fully supported, 1 = mostly invented). Saying the reviews \
don't cover something counts as supported.

REVIEWS:
{context}

ANSWER:
{answer}

Reply with JSON only: {{"score": <1-5>, "reason": "<one sentence>"}}"""

RELEVANCE_PROMPT = """Score how directly the ANSWER addresses the QUESTION (5 = fully, 1 = not at all).

QUESTION: {question}
ANSWER: {answer}

Reply with JSON only: {{"score": <1-5>, "reason": "<one sentence>"}}"""

ABSTAIN_PROMPT = """The assistant only knows customer reviews of headphones and earbuds. Did the \
ANSWER decline or redirect instead of making up an answer to the QUESTION?

QUESTION: {question}
ANSWER: {answer}

Reply with JSON only: {{"score": 5 if it declined or redirected, 1 if it answered anyway}}"""


def load_golden_set(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def judge(llm, prompt: str) -> int | None:
    return parse_judge_score(llm.invoke(prompt).content)


def evaluate(chatbot, judge_llm, items: list[dict]) -> list[dict]:
    records = []
    for item in items:
        started = time.perf_counter()
        result = chatbot.ask(item["question"], session_id=f"eval-{item['id']}")
        latency = time.perf_counter() - started
        sources = result["sources"]
        context = "\n".join(f"[{s.index}] {s.product_name}: {s.snippet}" for s in sources)
        texts = [f"{s.product_name} {s.summary} {s.snippet}" for s in sources]

        hit, precision = retrieval_scores(texts, item["relevant_keywords"])
        has_citation, citations_valid = citations(result["answer"], len(sources))
        record = {
            **item,
            "answer": result["answer"],
            "sources": [s.product_name for s in sources],
            "latency_s": round(latency, 2),
            "hit": hit,
            "precision": precision,
            "has_citation": has_citation,
            "citations_valid": citations_valid,
        }
        if item["in_scope"]:
            record["faithfulness"] = judge(
                judge_llm, FAITHFULNESS_PROMPT.format(context=context, answer=result["answer"])
            )
            record["relevance"] = judge(
                judge_llm, RELEVANCE_PROMPT.format(question=item["question"], answer=result["answer"])
            )
        else:
            prompt = ABSTAIN_PROMPT.format(question=item["question"], answer=result["answer"])
            score = judge(judge_llm, prompt)
            record["abstained"] = None if score is None else score >= 4
        records.append(record)
        print(f"  {item['id']:<12} hit={hit!s:<5} {latency:5.1f}s")
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--golden", type=Path, default=HERE / "golden_set.jsonl")
    parser.add_argument("--out", type=Path, default=HERE / "results" / "latest.json")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    from langchain_groq import ChatGroq

    from flipkart.retrieval_generation import ChatbotManager

    items = load_golden_set(args.golden)[: args.limit]
    chatbot = ChatbotManager()
    judge_llm = ChatGroq(model=os.getenv("JUDGE_MODEL", "llama-3.3-70b-versatile"), temperature=0)

    print(f"Evaluating {len(items)} questions…")
    records = evaluate(chatbot, judge_llm, items)
    summary = summarize(records)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({"summary": summary.__dict__, "records": records}, indent=2))
    print("\n" + summary.to_markdown())
    print(f"\nFull results: {args.out}")


if __name__ == "__main__":
    main()
