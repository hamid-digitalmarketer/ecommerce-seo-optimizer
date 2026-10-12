"""E-commerce SEO Optimizer - Streamlit application.

Run with: streamlit run app.py
"""
from __future__ import annotations

import io
import os

import pandas as pd
import streamlit as st

from optimizer import apply_suggestions, export_updated, generate_suggestions, validate_catalog

st.set_page_config(page_title="E-commerce SEO Optimizer", page_icon="🔍", layout="wide")
st.title("E-commerce SEO Optimizer")
st.caption(
    "Upload a product catalog (CSV/XLSX) with title and description columns. The tool validates "
    "on-page SEO, generates keyword-aware title/description suggestions, and lets you export an "
    "optimized copy while keeping your original columns intact."
)

SAMPLE_PATH = os.path.join(os.path.dirname(__file__), "sample_catalog.csv")

source = st.radio("Data source", ["Upload a file", "Use bundled sample catalog"], horizontal=True)

df_raw = None
if source == "Upload a file":
    uploaded = st.file_uploader("Upload product catalog", type=["csv", "xlsx"])
    if uploaded is not None:
        if uploaded.name.lower().endswith(".xlsx"):
            df_raw = pd.read_excel(uploaded)
        else:
            df_raw = pd.read_csv(uploaded)
else:
    if os.path.exists(SAMPLE_PATH):
        df_raw = pd.read_csv(SAMPLE_PATH)

if df_raw is None:
    st.info("Please upload a file or choose the sample catalog to continue.")
    st.stop()

try:
    issues = validate_catalog(df_raw)
    suggestions = generate_suggestions(df_raw)
except ValueError as exc:
    st.error(f"Could not process the catalog: {exc}")
    st.stop()

st.success(f"Loaded {len(df_raw):,} products. Found {len(issues):,} SEO issues and generated {len(suggestions):,} suggestions.")

st.subheader("Catalog issues")
severity_order = {"critical": 0, "warning": 1, "info": 2}
issues_sorted = issues.copy()
if not issues_sorted.empty:
    issues_sorted["_order"] = issues_sorted["severity"].map(severity_order).fillna(3)
    issues_sorted = issues_sorted.sort_values("_order").drop(columns="_order")
st.dataframe(issues_sorted, use_container_width=True, hide_index=True)

if not issues_sorted.empty:
    by_severity = issues_sorted["severity"].value_counts()
    c1, c2, c3 = st.columns(3)
    c1.metric("Critical", int(by_severity.get("critical", 0)))
    c2.metric("Warnings", int(by_severity.get("warning", 0)))
    c3.metric("Info", int(by_severity.get("info", 0)))

st.subheader("Generated suggestions")
preview = pd.DataFrame(
    [
        {
            "SKU": s.sku,
            "Current title": s.current_title,
            "Suggested title": s.suggested_title,
            "Reasons": "; ".join(s.reasons) if s.reasons else "OK",
        }
        for s in suggestions
    ]
)
st.dataframe(preview, use_container_width=True, hide_index=True)

st.subheader("Apply & export")
if st.button("Apply suggestions to catalog"):
    updated = apply_suggestions(df_raw, suggestions)
    st.success("Optimized columns added: optimized_title, optimized_description, optimized.")
    st.dataframe(updated, use_container_width=True, hide_index=True)

    csv_buffer = io.StringIO()
    updated.to_csv(csv_buffer, index=False)
    st.download_button(
        "Download optimized catalog (CSV)",
        data=csv_buffer.getvalue(),
        file_name="optimized_catalog.csv",
        mime="text/csv",
    )
