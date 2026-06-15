import argparse
import re
import time
from pathlib import Path

import pandas as pd
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

_REPO_ROOT = Path(__file__).parent.parent.parent
CSV_PATH = _REPO_ROOT / "inputs" / "all_formula_ingredients_manual_entry.csv"
PDF_DIR = _REPO_ROOT / "outputs" / "formula_pages_codex"

CLICK_THROUGH_TEXT = (
    "accept",
    "accept all",
    "accept all cookies",
    "agree",
    "allow all",
    "continue",
    "confirm",
    "confirm choices",
    "no thanks",
    "close",
    "got it",
    "ok",
)

EXPAND_SECTION_TEXT = (
    "ingredients",
    "ingredient list",
    "nutrition",
    "nutrition facts",
    "product details",
    "details",
    "what's inside",
    "whats inside",
    "learn more",
    "read more",
    "show more",
    "view more",
)


def _safe_filename_part(value: object) -> str:
    text = str(value).strip().replace("\n", " ")
    text = re.sub(r"[^\w .-]+", "", text)
    text = re.sub(r"\s+", "_", text)
    return text[:80] or "unknown"


def _click_text_buttons(scope, labels: tuple[str, ...], timeout_ms: int = 900) -> int:
    clicks = 0
    for text in labels:
        pattern = re.compile(rf"^\s*{re.escape(text)}\s*$", re.IGNORECASE)
        for role in ("button", "link"):
            try:
                locator = scope.get_by_role(role, name=pattern).first
                if locator.count() and locator.is_visible(timeout=timeout_ms):
                    locator.click(timeout=timeout_ms)
                    clicks += 1
                    break
            except PlaywrightTimeoutError:
                continue
    return clicks


def _click_common_overlays(page) -> None:
    _click_text_buttons(page, CLICK_THROUGH_TEXT)
    for frame in page.frames:
        try:
            _click_text_buttons(frame, CLICK_THROUGH_TEXT)
        except PlaywrightTimeoutError:
            continue


def _expand_likely_product_sections(page) -> None:
    _click_text_buttons(page, EXPAND_SECTION_TEXT)

    for text in EXPAND_SECTION_TEXT:
        pattern = re.compile(text, re.IGNORECASE)
        for selector in ("summary", "button[aria-expanded='false']", "[role='button'][aria-expanded='false']"):
            try:
                page.locator(selector).filter(has_text=pattern).first.click(timeout=900)
            except PlaywrightTimeoutError:
                continue


def _scroll_page(page) -> None:
    page.evaluate(
        """
        async () => {
            const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
            const step = Math.max(500, Math.floor(window.innerHeight * 0.75));
            for (let y = 0; y < document.body.scrollHeight; y += step) {
                window.scrollTo(0, y);
                await delay(300);
            }
            window.scrollTo(0, 0);
        }
        """
    )


def _visible_control_texts(page) -> list[str]:
    texts = []
    selectors = (
        "button",
        "a",
        "[role='button']",
        "summary",
        "input[type='button']",
        "input[type='submit']",
    )
    for selector in selectors:
        for locator in page.locator(selector).all():
            try:
                if not locator.is_visible(timeout=300):
                    continue
                text = locator.inner_text(timeout=300).strip()
                if not text:
                    text = locator.get_attribute("aria-label", timeout=300) or ""
                if not text:
                    text = locator.get_attribute("value", timeout=300) or ""
                text = re.sub(r"\s+", " ", text.strip())
                if text:
                    texts.append(text)
            except PlaywrightTimeoutError:
                continue

    deduped = []
    seen = set()
    for text in texts:
        key = text.lower()
        if key not in seen:
            deduped.append(text)
            seen.add(key)
    return deduped


def load_rows(csv_path: Path = CSV_PATH) -> pd.DataFrame:
    return pd.read_csv(csv_path, sep="\t")


def save_formula_page(
    url: str,
    brand: str,
    model: str,
    index_100: int,
    output_dir: Path = PDF_DIR,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    filename_base = f"{index_100}_{_safe_filename_part(brand)}_{_safe_filename_part(model)}"
    pdf_path = output_dir / f"{filename_base}.pdf"

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 1200})
        page.emulate_media(media="screen")
        page.goto(url, wait_until="domcontentloaded", timeout=90_000)
        try:
            page.wait_for_load_state("networkidle", timeout=15_000)
        except PlaywrightTimeoutError:
            pass
        _click_common_overlays(page)
        _expand_likely_product_sections(page)
        _scroll_page(page)
        page.pdf(path=str(pdf_path), format="Letter", print_background=True)
        browser.close()

    print(f"Saved: {pdf_path}")
    return pdf_path


def save_first_n(limit: int = 10, csv_path: Path = CSV_PATH, output_dir: Path = PDF_DIR) -> list[Path]:
    df = load_rows(csv_path)
    rows = df[df["website_link"].notna() & df["website_link"].astype(str).str.strip().ne("")].head(limit)

    saved_paths = []
    for row in rows.itertuples(index=False):
        try:
            saved_paths.append(
                save_formula_page(
                    url=str(row.website_link),
                    brand=str(row.brand),
                    model=str(row.model),
                    index_100=int(row.index_100),
                    output_dir=output_dir,
                )
            )
        except Exception as exc:
            message = f"{type(exc).__name__}: {exc}"
            print(f"Failed {int(row.index_100)} {row.brand} {row.model}: {message}")
        time.sleep(2)

    return saved_paths


def inspect_buttons(limit: int = 10, csv_path: Path = CSV_PATH, click_overlays: bool = False) -> None:
    df = load_rows(csv_path)
    rows = df[df["website_link"].notna() & df["website_link"].astype(str).str.strip().ne("")].head(limit)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        for row in rows.itertuples(index=False):
            page = browser.new_page(viewport={"width": 1440, "height": 1200})
            print(f"\n=== {int(row.index_100)} | {row.brand} | {row.model} ===")
            print(str(row.website_link))
            try:
                page.goto(str(row.website_link), wait_until="domcontentloaded", timeout=90_000)
                try:
                    page.wait_for_load_state("networkidle", timeout=10_000)
                except PlaywrightTimeoutError:
                    pass

                print("\nVisible controls before clicks:")
                controls = _visible_control_texts(page)
                for text in controls[:80]:
                    print(f"- {text}")
                if len(controls) > 80:
                    print(f"... {len(controls) - 80} more")

                if click_overlays:
                    _click_common_overlays(page)
                    print("\nVisible controls after cookie/overlay clicks:")
                    controls = _visible_control_texts(page)
                    for text in controls[:80]:
                        print(f"- {text}")
                    if len(controls) > 80:
                        print(f"... {len(controls) - 80} more")
            except Exception as exc:
                print(f"Failed to inspect: {type(exc).__name__}: {exc}")
            finally:
                page.close()
            time.sleep(2)
        browser.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Save formula website pages from the manual-entry TSV.")
    parser.add_argument("--first", type=int, default=10, help="Number of non-empty website links to save.")
    parser.add_argument("--output-dir", type=Path, default=PDF_DIR, help="Directory for PDFs.")
    parser.add_argument("--inspect-buttons", action="store_true", help="Print visible buttons/links instead of saving PDFs.")
    parser.add_argument(
        "--click-overlays",
        action="store_true",
        help="With --inspect-buttons, click known cookie/overlay buttons and print controls again.",
    )
    args = parser.parse_args()
    if args.inspect_buttons:
        inspect_buttons(limit=args.first, click_overlays=args.click_overlays)
    else:
        save_first_n(limit=args.first, output_dir=args.output_dir)


if __name__ == "__main__":
    main()
