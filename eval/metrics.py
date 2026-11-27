"""Pure scoring helpers for the RAG evaluation (no network, unit-tested)."""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from dataclasses import dataclass

CITATION = re.compile(r"\[(\d+)\]")


def is_relevant(text: str, keywords: Iterable[str]) -> bool:
    lowered = text.lower()
    return any(keyword.lower() in lowered for keyword in keywords)


def retrieval_scores(retrieved_texts: list[str], keywords: list[str]) -> tuple[bool, float]:
    """Return (hit, precision): did any retrieved review match, and what share matched."""
    if not retrieved_texts or not keywords:
        return False, 0.0
    matches = [is_relevant(text, keywords) for text in retrieved_texts]
    return any(matches), sum(matches) / len(matches)


def citations(answer: str, n_sources: int) -> tuple[bool, bool]:
    """Return (has_citation, all_citations_valid) for ``[n]`` markers in an answer."""
    cited = {int(n) for n in CITATION.findall(answer)}
    return bool(cited), all(1 <= n <= n_sources for n in cited)


def parse_judge_score(raw: str) -> int | None:
    """Pull a 1-5 integer ``score`` out of a judge reply (JSON, or JSON inside prose)."""
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        return None
    try:
        score = int(json.loads(match.group(0)).get("score"))
    except (ValueError, TypeError, AttributeError):
        return None
    return score if 1 <= score <= 5 else None


@dataclass
class Summary:
    n_in_scope: int
    hit_rate: float
    precision: float
    faithfulness: float | None
    relevance: float | None
    citation_rate: float
    valid_citation_rate: float
    n_out_of_scope: int
    abstention_rate: float | None

    def to_markdown(self) -> str:
        def pct(value):
            return "n/a" if value is None else f"{value:.0%}"

        def score(value):
            return "n/a" if value is None else f"{value:.2f} / 5"

        rows = [
            ("Retrieval hit rate @k", pct(self.hit_rate)),
            ("Retrieval precision @k", pct(self.precision)),
            ("Faithfulness (LLM judge)", score(self.faithfulness)),
            ("Answer relevance (LLM judge)", score(self.relevance)),
            ("Answers with citations", pct(self.citation_rate)),
            ("Citations pointing at a real source", pct(self.valid_citation_rate)),
            ("Out-of-scope questions declined", pct(self.abstention_rate)),
        ]
        lines = [
            f"Questions: {self.n_in_scope} in scope, {self.n_out_of_scope} out of scope",
            "",
            "| Metric | Result |",
            "|---|---|",
        ]
        lines += [f"| {name} | {value} |" for name, value in rows]
        return "\n".join(lines)


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def summarize(records: list[dict]) -> Summary:
    in_scope = [r for r in records if r["in_scope"]]
    out_scope = [r for r in records if not r["in_scope"]]
    return Summary(
        n_in_scope=len(in_scope),
        hit_rate=_mean([float(r["hit"]) for r in in_scope]) or 0.0,
        precision=_mean([r["precision"] for r in in_scope]) or 0.0,
        faithfulness=_mean([r["faithfulness"] for r in in_scope if r.get("faithfulness")]),
        relevance=_mean([r["relevance"] for r in in_scope if r.get("relevance")]),
        citation_rate=_mean([float(r["has_citation"]) for r in in_scope]) or 0.0,
        valid_citation_rate=_mean([float(r["citations_valid"]) for r in in_scope if r["has_citation"]])
        or 0.0,
        n_out_of_scope=len(out_scope),
        abstention_rate=_mean([float(r["abstained"]) for r in out_scope if r.get("abstained") is not None]),
    )
