# Amazon Sales Dataset — Data Cleaning & Reporting Automation

Data Analysis internship project: an end-to-end pipeline that cleans, analyzes,
visualizes, and reports on the Amazon Sales product dataset (1,465 rows, 16 columns).

## What it does

1. **Load & understand** the raw dataset
2. **Assess data quality** — missing values, duplicates, wrong data types
3. **Clean the data** — strip ₹/commas from prices, % from discount, fix invalid ratings,
   drop rows with missing identifiers or impossible values
4. **Exploratory Data Analysis** — totals, averages, top categories, top-rated/most-reviewed/
   most-expensive products
5. **Visualization** — 8 charts (category distribution, ratings, discounts, price comparisons, etc.)
6. **Automation** — the whole pipeline runs from one function (`main()` in `main.py`)
7. **Automated reporting** — a formatted Excel workbook and a PDF summary report,
   both regenerated automatically from the latest data

## Project structure

```
Amazon-Sales-Automation/
├── data/amazon.csv                       # Raw dataset
├── cleaned_data/cleaned_amazon_sales.csv # Cleaned output
├── charts/*.png                          # 8 generated charts
├── reports/report.xlsx                   # Excel report (Summary, Cleaned Data,
│                                          #   Category Stats, Top Products sheets)
├── reports/report.pdf                    # PDF report with charts & findings
├── notebook.ipynb                        # Step-by-step notebook (run this)
├── main.py                               # Core reusable pipeline functions
├── report_generator.py                   # Excel/PDF report generation
└── requirements.txt
```

## How to run

**Option A — Notebook (recommended for walking through each stage):**
```bash
pip install -r requirements.txt
jupyter notebook notebook.ipynb
```
Run all cells top to bottom.

**Option B — One-command automation:**
```bash
pip install -r requirements.txt
python main.py
```
This regenerates the cleaned CSV, all 8 charts, and both reports in one run —
useful if the source `amazon.csv` is ever refreshed.

## Data quality issues found & fixed

| Issue | Fix |
|---|---|
| Prices stored as text with `₹` and commas | Stripped and converted to float |
| `discount_percentage` stored as text with `%` | Stripped and converted to float |
| `rating_count` stored as text with commas | Stripped and converted to numeric |
| One row had a corrupted (non-numeric) rating | Row dropped |
| Missing `rating_count` | Filled with 0 |
| Extra whitespace in text columns | Trimmed |
| Rows with non-positive prices | Removed as invalid |

## Key results (from the cleaned data)

- 1,464 products across ~9 major categories after cleaning
- Average rating: 4.1 / 5
- Average discount: ~48%
- Full breakdown, top-10 lists, and 8 charts are in `reports/report.pdf` and `reports/report.xlsx`
