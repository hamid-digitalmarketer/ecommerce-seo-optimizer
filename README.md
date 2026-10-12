# E-commerce SEO Optimizer

A practical tool for e-commerce teams and SEO specialists to audit and improve on-page product listings at scale. Built with Python, Pandas, and Streamlit: upload a product catalog, see every title/description/image/price issue, review keyword-aware suggestions, and export an optimized copy — original columns are always preserved.

## Problem it solves

E-commerce stores often have hundreds or thousands of thin product listings: short titles, missing descriptions, no keywords, broken image references. Fixing them manually in a spreadsheet is slow and error-prone. This tool surfaces the exact problems, proposes concrete title/description improvements using the product's own brand/category/keywords, and produces a safe export for review before applying changes upstream.

## Key features

- Upload CSV or XLSX product catalogs (title, description, price, category, brand, image columns recognized and normalized)
- Audit engine: empty/short/long titles, empty/short descriptions, missing prices, missing or malformed image URLs, duplicate titles
- Severity grading: critical / warning / info
- Suggestion engine: expands short titles with brand/category keywords, generates description copy, records reasons for every change
- Safe apply: writes `optimized_title`, `optimized_description`, `optimized` columns without overwriting originals
- Download the optimized catalog as CSV

## Data expectations

The tool looks for a title column (`title`, `name`, `product`, `product title`) and optional description, price, category, brand, image columns. Unknown columns are ignored. Missing values are flagged, never guessed.

## Technology stack

- Python 3.11
- Pandas (catalog processing)
- Streamlit (web UI)
- openpyxl (XLSX support)

## Folder structure

```
ecommerce-seo-optimizer/
├── app.py                  # Streamlit application
├── optimizer.py            # Validation, suggestion, and export engine
├── tests/
│   └── test_optimizer.py
├── requirements.txt
└── .gitignore
```

## Installation

```bash
python -m venv venv
# Windows: venv/Scripts/activate  |  macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
streamlit run app.py
```

Upload a catalog or use the bundled sample, review the issues and suggestions, then apply and download the optimized file.

## Testing

```bash
pytest -q
```

Tests cover issue detection, suggestion generation, missing-title handling, safe apply behavior, and CSV export.

## Limitations and known issues

- Keyword extraction is heuristic (brand, category, top words); it is not a full SEO content service
- Title length guidance uses common best-practice ranges (20-70 title, 50-160 description) — tune the constants in `optimizer.py` to your vertical if needed
- No integration with platforms (Shopify, WooCommerce, etc.); export and import manually

## Future improvements

- Keyword density scoring and SERP snippet preview
- Competitor title analysis (from a comparison file)
- Shopify/WooCommerce export formats
- Batch apply via a reviewed CSV diff

## License

MIT (add a `LICENSE` file before commercial use if required by your use case).

---

**Developed by Muhammad Hamid**

Digital Marketing | SEO | Performance Marketing | E-commerce | Web Development

- Portfolio: [https://abouthamid.web.app/](https://abouthamid.web.app/)
- LinkedIn: [https://www.linkedin.com/in/muhammad-hamid-digital-marketing/](https://www.linkedin.com/in/muhammad-hamid-digital-marketing/)
- WhatsApp: [https://wa.me/923167417135](https://wa.me/923167417135)

Have a project, job opportunity, or collaboration in mind? [Contact Muhammad Hamid on WhatsApp](https://wa.me/923167417135).
