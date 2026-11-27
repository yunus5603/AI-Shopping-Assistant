import pandas as pd
import pytest

from flipkart.data_converter import dataconverter


def write_csv(tmp_path, rows):
    path = tmp_path / "reviews.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def test_converts_rows_to_documents(tmp_path):
    path = write_csv(
        tmp_path,
        [{"product_title": "boAt Rockerz", "review": " Great bass ", "rating": 4, "summary": "Nice"}],
    )

    docs = dataconverter(path)

    assert len(docs) == 1
    assert docs[0].page_content == "Great bass"
    assert docs[0].metadata == {"product_name": "boAt Rockerz", "rating": 4.0, "summary": "Nice"}


def test_skips_rows_without_review_or_product(tmp_path):
    path = write_csv(
        tmp_path,
        [
            {"product_title": "A", "review": "ok", "rating": 3, "summary": "s"},
            {"product_title": "B", "review": None, "rating": 3, "summary": "s"},
            {"product_title": None, "review": "orphan", "rating": 3, "summary": "s"},
            {"product_title": "C", "review": "   ", "rating": 3, "summary": "s"},
        ],
    )

    assert [d.metadata["product_name"] for d in dataconverter(path)] == ["A"]


def test_bad_rating_and_missing_summary_become_none_and_empty(tmp_path):
    path = write_csv(tmp_path, [{"product_title": "A", "review": "ok", "rating": "n/a", "summary": None}])

    doc = dataconverter(path)[0]

    assert doc.metadata["rating"] is None
    assert doc.metadata["summary"] == ""


def test_missing_columns_raise_clear_error(tmp_path):
    path = write_csv(tmp_path, [{"product_title": "A", "review": "ok"}])

    with pytest.raises(ValueError, match="rating, summary"):
        dataconverter(path)


def test_missing_file_points_to_setup(tmp_path):
    with pytest.raises(FileNotFoundError, match="PRODUCT_DATA_PATH"):
        dataconverter(tmp_path / "nope.csv")


def test_env_var_sets_default_path(tmp_path, monkeypatch):
    path = write_csv(tmp_path, [{"product_title": "A", "review": "ok", "rating": 5, "summary": "s"}])
    monkeypatch.setenv("PRODUCT_DATA_PATH", str(path))

    assert len(dataconverter()) == 1
