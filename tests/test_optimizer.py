"""Unit tests for the E-commerce SEO Optimizer."""

import pandas as pd
import pytest

from optimizer import (
    apply_suggestions,
    export_updated,
    generate_suggestions,
    validate_catalog,
)


@pytest.fixture
def catalog():
    return pd.DataFrame(
        {
            "SKU": ["S1", "S2", "S3"],
            "Title": ["Short", "A complete and descriptive product title for a nice widget", ""],
            "Description": [
                "",
                "A reasonably long description that explains the product benefits in enough detail for shoppers.",
                "",
            ],
            "Price": [9.99, 19.99, None],
            "Category": ["Widgets", "Widgets", "Gadgets"],
        }
    )


def test_validate_catalog_flags_issues(catalog):
    issues = validate_catalog(catalog)
    types = set(issues["issue_type"])
    assert "title" in types
    assert "description" in types
    assert "price" in types
    assert issues[issues["issue_type"] == "price"].shape[0] == 1


def test_generate_suggestions_covers_all_rows(catalog):
    suggestions = generate_suggestions(catalog)
    assert len(suggestions) == len(catalog)
    short = suggestions[0]
    assert short.current_title == "Short"
    assert short.suggested_title != "Short"
    assert short.reasons  # a reason must be recorded


def test_missing_title_gets_placeholder(catalog):
    suggestions = generate_suggestions(catalog)
    empty = suggestions[2]
    assert empty.current_title == ""
    assert empty.suggested_title


def test_apply_suggestions_keeps_original_columns(catalog):
    suggestions = generate_suggestions(catalog)
    updated = apply_suggestions(catalog, suggestions)
    assert "optimized_title" in updated.columns
    assert "optimized_description" in updated.columns
    assert "optimized" in updated.columns
    assert updated["optimized"].all()
    assert "Title" not in updated.columns or "product_title" in updated.columns


def test_export_updated_writes_csv(tmp_path):
    catalog = pd.DataFrame(
        {"SKU": ["S1"], "Title": ["A complete and descriptive product title for a nice widget"], "Description": ["long enough description for export test purposes here"]}
    )
    suggestions = generate_suggestions(catalog)
    updated = apply_suggestions(catalog, suggestions)
    out = tmp_path / "catalog_out.csv"
    path = export_updated(updated, str(out))
    assert path == str(out)
    assert out.exists()
