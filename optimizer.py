"""Core engine for the E-commerce SEO Optimizer.

Validates product catalog exports, detects on-page SEO problems, generates
keyword-aware title and description suggestions, and applies them while
preserving the original columns for review/undo.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

import pandas as pd

TITLE_MIN_LEN = 20
TITLE_MAX_LEN = 70
DESC_MIN_LEN = 50
DESC_MAX_LEN = 160

STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "for", "with", "of", "on", "in",
    "to", "at", "by", "from", "is", "are", "was", "were", "be", "been",
}


@dataclass
class Suggestion:
    """A single optimization suggestion for a product row."""

    sku: str
    current_title: str
    suggested_title: str
    current_description: str
    suggested_description: str
    reasons: list[str]


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]
    rename = {
        "title": "product_title",
        "name": "product_title",
        "product name": "product_title",
        "product": "product_title",
        "meta description": "description",
        "body": "description",
        "image": "image_url",
        "main image": "image_url",
        "brand name": "brand",
        "product type": "category",
        "type": "category",
    }
    df = df.rename(columns=rename)
    return df


def validate_catalog(df: pd.DataFrame) -> pd.DataFrame:
    """Return a DataFrame of issues found in the catalog.

    Issue columns: sku, current_title, category, issue_type, severity, message.
    """
    df = _normalize_columns(df)
    if "product_title" not in df.columns:
        raise ValueError("No title/name column found. Expected 'title', 'name', or 'product title'.")

    sku_col = "sku" if "sku" in df.columns else df.index.name or "index"
    rows = []
    for idx, row in df.iterrows():
        sku = row.get("sku", idx)
        title = str(row.get("product_title", "") or "").strip()
        desc = str(row.get("description", "") or "").strip()
        price = row.get("price", None)
        image = str(row.get("image_url", "") or "").strip()
        category = str(row.get("category", "") or "").strip()

        if not title:
            rows.append([sku, title, category, "title", "critical", "Product title is empty."])
        elif len(title) < TITLE_MIN_LEN:
            rows.append([sku, title, category, "title", "warning", f"Title is short ({len(title)} chars)."])
        elif len(title) > TITLE_MAX_LEN:
            rows.append([sku, title, category, "title", "warning", f"Title is long ({len(title)} chars)."])

        if not desc:
            rows.append([sku, title, category, "description", "warning", "Description is empty."])
        elif len(desc) < DESC_MIN_LEN:
            rows.append([sku, title, category, "description", "warning", f"Description is short ({len(desc)} chars)."])

        if price is None or pd.isna(price):
            rows.append([sku, title, category, "price", "warning", "Price is missing."])

        if not image:
            rows.append([sku, title, category, "image", "info", "Image URL is missing."])
        elif image and not image.lower().startswith(("http://", "https://", "/")):
            rows.append([sku, title, category, "image", "info", "Image URL looks relative or invalid."])

    issues = pd.DataFrame(rows, columns=["sku", "current_title", "category", "issue_type", "severity", "message"])

    # Duplicate titles
    dup = df[df.duplicated(subset="product_title", keep=False)]
    if not dup.empty:
        for _, row in dup.iterrows():
            issues = pd.concat(
                [
                    issues,
                    pd.DataFrame(
                        [[row.get("sku", "?"), row["product_title"], row.get("category", ""), "title", "warning", "Duplicate title across catalog."]],
                        columns=issues.columns,
                    ),
                ],
                ignore_index=True,
            )
    return issues


def _extract_keywords(title: str, category: str = "", brand: str = "") -> list[str]:
    """Heuristic keyword extraction: brand, category, and significant words."""
    keywords = []
    if brand and brand.lower() not in title.lower():
        keywords.append(brand.strip())
    if category and category.lower() not in title.lower():
        keywords.append(category.strip())
    words = [w for w in re.split(r"[\s\-/]+", title.lower()) if w not in STOPWORDS and len(w) > 2]
    keywords.extend(words[:4])
    seen = set()
    ordered = []
    for k in keywords:
        kl = k.lower()
        if kl not in seen:
            seen.add(kl)
            ordered.append(k)
    return ordered


def generate_suggestions(df: pd.DataFrame) -> list[Suggestion]:
    """Generate title/description suggestions for each product row."""
    df = _normalize_columns(df)
    if "product_title" not in df.columns:
        raise ValueError("No title/name column found.")

    suggestions: list[Suggestion] = []
    for _, row in df.iterrows():
        sku = row.get("sku", row.name)
        title = str(row.get("product_title", "") or "").strip()
        desc = str(row.get("description", "") or "").strip()
        brand = str(row.get("brand", "") or "").strip()
        category = str(row.get("category", "") or "").strip()

        reasons: list[str] = []
        suggested_title = title
        if not title:
            suggested_title = brand or category or "Product"
            reasons.append("Missing title; created a placeholder based on available fields.")
        else:
            keywords = _extract_keywords(title, category, brand)
            combined = " ".join(keywords) if keywords else title
            if len(combined) > TITLE_MAX_LEN:
                suggested_title = combined[: TITLE_MAX_LEN].rsplit(" ", 1)[0].rstrip(" ,-")
            elif len(combined) > len(title):
                suggested_title = combined
                reasons.append("Added brand/category keywords to the title.")
            elif len(title) < TITLE_MIN_LEN:
                suggested_title = combined
                reasons.append("Expanded short title with keywords.")

        suggested_description = desc
        if not desc or len(desc) < DESC_MIN_LEN:
            base = (title or suggested_title).strip()
            suggested_description = (
                f"Discover the {base} — {category or 'premium quality'} designed for everyday use. "
                f"Fast delivery, easy returns, and dedicated customer support. "
                f"Order now and enjoy the best value."
            )[:DESC_MAX_LEN]
            if not desc:
                reasons.append("Generated a description from the product title and category.")
            else:
                reasons.append("Expanded a short description.")

        suggestions.append(
            Suggestion(
                sku=sku,
                current_title=title,
                suggested_title=suggested_title,
                current_description=desc,
                suggested_description=suggested_description,
                reasons=reasons,
            )
        )
    return suggestions


def apply_suggestions(df: pd.DataFrame, suggestions: list[Suggestion]) -> pd.DataFrame:
    """Return a copy of the catalog with optimized_* columns appended.

    Original columns are never overwritten; reviewers can compare before/after.
    """
    df = _normalize_columns(df).copy()
    lookup = {s.sku: s for s in suggestions}
    optimized_titles: list[str] = []
    optimized_descs: list[str] = []
    applied = []
    for _, row in df.iterrows():
        sku = row.get("sku", row.name)
        sug = lookup.get(sku)
        if sug is None:
            optimized_titles.append(row.get("product_title", ""))
            optimized_descs.append(row.get("description", ""))
            applied.append(False)
            continue
        optimized_titles.append(sug.suggested_title)
        optimized_descs.append(sug.suggested_description)
        applied.append(True)

    df["optimized_title"] = optimized_titles
    df["optimized_description"] = optimized_descs
    df["optimized"] = applied
    return df


def export_updated(df: pd.DataFrame, path: str) -> str:
    """Write the updated catalog (originals + optimized columns) to CSV/Excel."""
    df = _normalize_columns(df).copy()
    if path.lower().endswith(".xlsx"):
        df.to_excel(path, index=False)
    else:
        df.to_csv(path, index=False)
    return path
