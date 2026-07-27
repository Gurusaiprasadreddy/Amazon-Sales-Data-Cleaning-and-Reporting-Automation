"""
Amazon Sales Dataset - Data Cleaning & Reporting Automation
Internship Project - main.py

This module contains all reusable functions used by the Jupyter Notebook.
Run end-to-end with: python main.py
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

pd.set_option("display.max_columns", None)
plt.rcParams["figure.dpi"] = 100

DATA_PATH = "data/amazon.csv"
CLEANED_PATH = "cleaned_data/cleaned_amazon_sales.csv"
CHARTS_DIR = "charts"
REPORTS_DIR = "reports"


# ---------------------------------------------------------------------------
# STAGE 1: LOAD DATA
# ---------------------------------------------------------------------------
def load_data(path=DATA_PATH):
    """Load the raw Amazon sales CSV into a DataFrame."""
    df = pd.read_csv(path)
    return df


# ---------------------------------------------------------------------------
# STAGE 2: DATA QUALITY ASSESSMENT
# ---------------------------------------------------------------------------
def data_quality_report(df):
    """Return a dictionary summarizing data quality issues in the raw data."""
    report = {
        "n_rows": len(df),
        "n_columns": df.shape[1],
        "missing_values": df.isnull().sum()[df.isnull().sum() > 0].to_dict(),
        "duplicate_rows": int(df.duplicated().sum()),
        "duplicate_product_ids": int(df["product_id"].duplicated().sum()),
        "dtypes": df.dtypes.astype(str).to_dict(),
    }
    return report


# ---------------------------------------------------------------------------
# STAGE 3: DATA CLEANING
# ---------------------------------------------------------------------------
def _clean_price(series):
    """Strip ₹ symbol and thousands commas, convert to float."""
    return (
        series.astype(str)
        .str.replace("₹", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.strip()
        .replace("nan", np.nan)
        .astype(float)
    )


def _clean_percentage(series):
    """Strip % sign and convert to a numeric percentage (0-100)."""
    return (
        series.astype(str)
        .str.replace("%", "", regex=False)
        .str.strip()
        .replace("nan", np.nan)
        .astype(float)
    )


def _clean_rating_count(series):
    """Strip thousands commas from rating_count and convert to Int64."""
    return (
        series.astype(str)
        .str.replace(",", "", regex=False)
        .str.strip()
        .replace("nan", np.nan)
        .astype(float)
    )


def clean_data(df):
    """
    Apply all cleaning steps to the raw Amazon sales dataframe and return
    a cleaned copy. Steps:
      1. Drop exact duplicate rows
      2. Trim whitespace on all text columns
      3. Convert discounted_price / actual_price to numeric
      4. Convert discount_percentage to numeric
      5. Convert rating to numeric, drop rows with invalid (non-numeric) ratings
      6. Convert rating_count to numeric (nullable Int64)
      7. Fill missing rating_count with 0
      8. Drop rows missing product_name (core identifying field)
      9. Flag / remove impossible values (negative or zero prices)
    """
    df = df.copy()

    # 1. Remove duplicate rows
    df = df.drop_duplicates()

    # 2. Trim whitespace in text/object columns
    text_cols = df.select_dtypes(include=["object", "string"]).columns
    for col in text_cols:
        df[col] = df[col].astype(str).str.strip()

    # 3. Clean price columns
    df["discounted_price"] = _clean_price(df["discounted_price"])
    df["actual_price"] = _clean_price(df["actual_price"])

    # 4. Clean discount_percentage
    df["discount_percentage"] = _clean_percentage(df["discount_percentage"])

    # 5. Clean rating - some rows contain a stray "|" instead of a number
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
    df = df.dropna(subset=["rating"])

    # 6. Clean rating_count
    df["rating_count"] = _clean_rating_count(df["rating_count"])
    # 7. Fill missing rating_count with 0 and cast to nullable integer
    df["rating_count"] = df["rating_count"].fillna(0).astype("Int64")

    # 8. Drop rows with missing product_name or category
    df = df.dropna(subset=["product_name", "category"])
    df = df[df["product_name"].str.lower() != "nan"]

    # 9. Remove impossible values: non-positive prices
    df = df[(df["discounted_price"] > 0) & (df["actual_price"] > 0)]

    # Standardize category text (keep hierarchy but strip stray spaces)
    df["category"] = df["category"].str.strip()

    # Reset index after all filtering
    df = df.reset_index(drop=True)
    return df


# ---------------------------------------------------------------------------
# STAGE 4: EXPLORATORY DATA ANALYSIS
# ---------------------------------------------------------------------------
def analyze_data(df):
    """Compute key summary statistics used in the report. Returns a dict."""
    df = df.copy()
    df["main_category"] = df["category"].str.split("|").str[0]

    top_category_counts = df["main_category"].value_counts().head(10)
    top_rated_products = df.sort_values("rating", ascending=False)[
        ["product_name", "rating"]
    ].head(5)
    most_reviewed = df.sort_values("rating_count", ascending=False)[
        ["product_name", "rating_count"]
    ].head(10)
    most_expensive = df.sort_values("actual_price", ascending=False)[
        ["product_name", "actual_price"]
    ].head(10)

    stats = {
        "total_products": len(df),
        "total_categories": df["main_category"].nunique(),
        "average_rating": round(df["rating"].mean(), 2),
        "average_discount_pct": round(df["discount_percentage"].mean(), 2),
        "average_discounted_price": round(df["discounted_price"].mean(), 2),
        "average_actual_price": round(df["actual_price"].mean(), 2),
        "highest_discount_pct": df["discount_percentage"].max(),
        "highest_rating": df["rating"].max(),
        "lowest_rating": df["rating"].min(),
        "top_categories": top_category_counts,
        "top_rated_products": top_rated_products,
        "most_reviewed_products": most_reviewed,
        "most_expensive_products": most_expensive,
        "avg_price_by_category": df.groupby("main_category")["discounted_price"]
        .mean()
        .sort_values(ascending=False)
        .head(10),
        "avg_rating_by_category": df.groupby("main_category")["rating"]
        .mean()
        .sort_values(ascending=False)
        .head(10),
    }
    return stats, df


# ---------------------------------------------------------------------------
# STAGE 5: VISUALIZATION
# ---------------------------------------------------------------------------
def create_visualizations(df, stats, out_dir=CHARTS_DIR):
    """Generate all charts and save them as PNGs in out_dir. Returns list of paths."""
    os.makedirs(out_dir, exist_ok=True)
    saved = []

    # 1. Top 10 Categories - Bar Chart
    plt.figure(figsize=(10, 6))
    stats["top_categories"].plot(kind="bar", color="#4C72B0")
    plt.title("Top 10 Product Categories by Number of Listings")
    plt.xlabel("Category")
    plt.ylabel("Number of Products")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    p = os.path.join(out_dir, "category_chart.png")
    plt.savefig(p)
    plt.close()
    saved.append(p)

    # 2. Rating Distribution - Histogram
    plt.figure(figsize=(8, 6))
    plt.hist(df["rating"], bins=20, color="#55A868", edgecolor="black")
    plt.title("Distribution of Product Ratings")
    plt.xlabel("Rating")
    plt.ylabel("Frequency")
    plt.tight_layout()
    p = os.path.join(out_dir, "rating_chart.png")
    plt.savefig(p)
    plt.close()
    saved.append(p)

    # 3. Top 10 Most Reviewed Products - Horizontal Bar
    plt.figure(figsize=(10, 6))
    top10 = stats["most_reviewed_products"].iloc[::-1]
    labels = [n[:40] + "..." if len(n) > 40 else n for n in top10["product_name"]]
    plt.barh(labels, top10["rating_count"], color="#C44E52")
    plt.title("Top 10 Most Reviewed Products")
    plt.xlabel("Number of Ratings")
    plt.tight_layout()
    p = os.path.join(out_dir, "top_products.png")
    plt.savefig(p)
    plt.close()
    saved.append(p)

    # 4. Discount Percentage Distribution - Histogram
    plt.figure(figsize=(8, 6))
    plt.hist(df["discount_percentage"], bins=20, color="#8172B2", edgecolor="black")
    plt.title("Distribution of Discount Percentage")
    plt.xlabel("Discount %")
    plt.ylabel("Frequency")
    plt.tight_layout()
    p = os.path.join(out_dir, "discount_chart.png")
    plt.savefig(p)
    plt.close()
    saved.append(p)

    # 5. Average Price by Category - Bar Chart
    plt.figure(figsize=(10, 6))
    stats["avg_price_by_category"].plot(kind="bar", color="#CCB974")
    plt.title("Average Discounted Price by Category (Top 10)")
    plt.xlabel("Category")
    plt.ylabel("Average Price (₹)")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    p = os.path.join(out_dir, "avg_price_by_category.png")
    plt.savefig(p)
    plt.close()
    saved.append(p)

    # 6. Top Rated Categories - Bar Chart
    plt.figure(figsize=(10, 6))
    stats["avg_rating_by_category"].plot(kind="bar", color="#64B5CD")
    plt.title("Top Rated Categories (Average Rating)")
    plt.xlabel("Category")
    plt.ylabel("Average Rating")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    p = os.path.join(out_dir, "top_rated_categories.png")
    plt.savefig(p)
    plt.close()
    saved.append(p)

    # 7. Actual Price vs Discounted Price - Scatter Plot
    plt.figure(figsize=(8, 6))
    plt.scatter(df["actual_price"], df["discounted_price"], alpha=0.4, color="#DD8452")
    plt.title("Actual Price vs Discounted Price")
    plt.xlabel("Actual Price (₹)")
    plt.ylabel("Discounted Price (₹)")
    plt.tight_layout()
    p = os.path.join(out_dir, "price_scatter.png")
    plt.savefig(p)
    plt.close()
    saved.append(p)

    # 8. Top 10 Expensive Products - Bar Chart
    plt.figure(figsize=(10, 6))
    exp = stats["most_expensive_products"]
    labels = [n[:35] + "..." if len(n) > 35 else n for n in exp["product_name"]]
    plt.bar(labels, exp["actual_price"], color="#937860")
    plt.title("Top 10 Most Expensive Products")
    plt.ylabel("Actual Price (₹)")
    plt.xticks(rotation=60, ha="right")
    plt.tight_layout()
    p = os.path.join(out_dir, "expensive_products.png")
    plt.savefig(p)
    plt.close()
    saved.append(p)

    return saved


# ---------------------------------------------------------------------------
# STAGE 6/7: SAVE CLEANED DATA + REPORT GENERATION (see report_generator.py)
# ---------------------------------------------------------------------------
def save_cleaned_dataset(df, path=CLEANED_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    export_cols = [c for c in df.columns if c not in ("about_product", "img_link")]
    df[export_cols].to_csv(path, index=False)
    return path


# ---------------------------------------------------------------------------
# MASTER PIPELINE
# ---------------------------------------------------------------------------
def main():
    print("Stage 1: Loading data...")
    raw_df = load_data()
    print(f"  Loaded {len(raw_df)} rows, {raw_df.shape[1]} columns")

    print("Stage 2: Data quality assessment...")
    dq = data_quality_report(raw_df)
    print(f"  Duplicates: {dq['duplicate_rows']}, Missing value columns: {len(dq['missing_values'])}")

    print("Stage 3: Cleaning data...")
    clean_df = clean_data(raw_df)
    print(f"  Cleaned dataset: {len(clean_df)} rows remain")

    print("Stage 4: Analyzing data...")
    stats, enriched_df = analyze_data(clean_df)
    print(f"  Avg rating: {stats['average_rating']}, Avg discount: {stats['average_discount_pct']}%")

    print("Stage 5: Creating visualizations...")
    chart_paths = create_visualizations(enriched_df, stats)
    print(f"  Saved {len(chart_paths)} charts to {CHARTS_DIR}/")

    print("Stage 6: Saving cleaned dataset...")
    out_path = save_cleaned_dataset(clean_df)
    print(f"  Saved to {out_path}")

    print("Stage 7: Generating reports...")
    from report_generator import generate_excel_report, generate_pdf_report
    generate_excel_report(clean_df, stats, dq)
    generate_pdf_report(stats, dq, chart_paths)
    print("  Reports saved to reports/")

    print("\nAll stages complete!")
    return raw_df, clean_df, stats, dq, chart_paths


if __name__ == "__main__":
    main()
