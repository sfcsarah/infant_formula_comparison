import argparse
from pathlib import Path

import pandas as pd
from playwright.sync_api import sync_playwright

_REPO_ROOT = Path(__file__).parent.parent.parent
CSV_PATH = _REPO_ROOT / "inputs" / "all_formula_ingredients_manual_entry.csv"
WEB_LINKS_DIR = _REPO_ROOT / "outputs" / "web_links"


def save_pdf(url: str, brand: str, model: str, index_100: int) -> None:
    WEB_LINKS_DIR.mkdir(parents=True, exist_ok=True)

    filename = f"{index_100}_{brand}_{model}.pdf"
    pdf_path = WEB_LINKS_DIR / filename

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url, wait_until="load", timeout=60_000)
        page.wait_for_timeout(3_000)
        page.pdf(path=str(pdf_path))
        browser.close()

    print(f"Saved: {pdf_path}")


def run(index_100: int) -> None:
    df = pd.read_csv(CSV_PATH)
    row_index = index_100 - 100
    row = df.iloc[row_index]

    url = row["website_link"]
    if pd.isna(url) or not str(url).strip():
        raise ValueError(f"No website_link for index_100={index_100} ({row['brand']} {row['model']})")

    save_pdf(str(url), str(row["brand"]), str(row["model"]), index_100)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Save a formula product page as PDF from the CSV.")
    parser.add_argument("index_100", type=int, help="index_100 value (row index + 100)")
    args = parser.parse_args()
    run(args.index_100)
