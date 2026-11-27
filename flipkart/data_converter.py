"""Turn the Flipkart product-review CSV into LangChain documents."""

from __future__ import annotations

import math
import os
from pathlib import Path

import pandas as pd
from langchain_core.documents import Document

DEFAULT_DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "flipkart_product_review.csv"
REQUIRED_COLUMNS = ("product_title", "review", "rating", "summary")


def _clean_text(value: object) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    return str(value).strip()


def _clean_rating(value: object) -> float | None:
    try:
        rating = float(value)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(rating) else rating


def dataconverter(data_path: str | os.PathLike | None = None) -> list[Document]:
    """Load the review CSV and return one Document per non-empty review.

    The review text is the page content (what gets embedded). Product name,
    rating and summary go into metadata so answers can cite their sources.

    The path is resolved from the argument, then ``PRODUCT_DATA_PATH``, then
    ``data/flipkart_product_review.csv``.
    """
    path = Path(data_path or os.getenv("PRODUCT_DATA_PATH") or DEFAULT_DATA_PATH)
    if not path.exists():
        raise FileNotFoundError(
            f"Product review CSV not found at {path}. "
            "Download it into data/ or set PRODUCT_DATA_PATH (see README)."
        )

    frame = pd.read_csv(path)
    missing = [col for col in REQUIRED_COLUMNS if col not in frame.columns]
    if missing:
        raise ValueError(f"{path.name} is missing required columns: {', '.join(missing)}")

    docs: list[Document] = []
    for row in frame[list(REQUIRED_COLUMNS)].itertuples(index=False):
        review = _clean_text(row.review)
        product = _clean_text(row.product_title)
        if not review or not product:
            continue
        docs.append(
            Document(
                page_content=review,
                metadata={
                    "product_name": product,
                    "rating": _clean_rating(row.rating),
                    "summary": _clean_text(row.summary),
                },
            )
        )
    return docs
