import argparse
import re
import shutil
from pathlib import Path

import pandas as pd

_REPO_ROOT = Path(__file__).parent.parent.parent
CSV_PATH = _REPO_ROOT / "inputs" / "all_formula_ingredients_manual_entry.csv"
STAGING_DIR = _REPO_ROOT / "outputs" / "web_links_codex"
FINAL_DIR = _REPO_ROOT / "outputs" / "formula_pages_manual"
STATE_PATH = _REPO_ROOT / "outputs" / "formula_pages_manual_state.txt"


def _safe_filename_part(value: object) -> str:
    text = str(value).strip().replace("\n", " ")
    text = re.sub(r"[^\w .-]+", "", text)
    text = re.sub(r"\s+", "_", text)
    return text[:80] or "unknown"


def load_rows(csv_path: Path = CSV_PATH) -> pd.DataFrame:
    df = pd.read_csv(csv_path, sep="\t")
    return df[df["website_link"].notna() & df["website_link"].astype(str).str.strip().ne("")]


def expected_filename(row: pd.Series) -> str:
    return f"{int(row['index_100'])}_{_safe_filename_part(row['brand'])}_{_safe_filename_part(row['model'])}.pdf"


def row_for_index(rows: pd.DataFrame, index_100: int) -> pd.Series:
    matches = rows[rows["index_100"] == index_100]
    if matches.empty:
        raise ValueError(f"No row found for index_100={index_100}")
    return matches.iloc[0]


def first_index(rows: pd.DataFrame) -> int:
    return int(rows.iloc[0]["index_100"])


def next_index_after(rows: pd.DataFrame, index_100: int) -> int | None:
    indexes = rows["index_100"].astype(int).tolist()
    for idx in indexes:
        if idx > index_100:
            return idx
    return None


def read_state(rows: pd.DataFrame, state_path: Path = STATE_PATH) -> int:
    if state_path.exists():
        return int(state_path.read_text().strip())
    return first_index(rows)


def write_state(index_100: int, state_path: Path = STATE_PATH) -> None:
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(f"{index_100}\n")


def newest_staged_pdf(staging_dir: Path = STAGING_DIR) -> Path:
    staging_dir.mkdir(parents=True, exist_ok=True)
    pdfs = sorted(staging_dir.glob("*.pdf"), key=lambda path: path.stat().st_mtime, reverse=True)
    if not pdfs:
        raise FileNotFoundError(f"No staged PDFs found in {staging_dir}")
    return pdfs[0]


def print_row_instructions(row: pd.Series, final_dir: Path = FINAL_DIR) -> None:
    print(f"index_100: {int(row['index_100'])}")
    print(f"brand: {row['brand']}")
    print(f"model: {row['model']}")
    print(f"link: {row['website_link']}")
    print(f"save as/final filename: {expected_filename(row)}")
    print(f"final folder: {final_dir}")


def show_index(
    csv_path: Path = CSV_PATH,
    final_dir: Path = FINAL_DIR,
    state_path: Path = STATE_PATH,
    index_100: int | None = None,
) -> None:
    rows = load_rows(csv_path)
    if index_100 is None:
        index_100 = read_state(rows, state_path)
    row = row_for_index(rows, index_100)
    print_row_instructions(row, final_dir)


def move_index_and_show_next(
    csv_path: Path = CSV_PATH,
    staging_dir: Path = STAGING_DIR,
    final_dir: Path = FINAL_DIR,
    state_path: Path = STATE_PATH,
    index_100: int | None = None,
    overwrite: bool = False,
) -> None:
    rows = load_rows(csv_path)
    if index_100 is None:
        index_100 = read_state(rows, state_path)
    row = row_for_index(rows, index_100)

    staged_pdf = newest_staged_pdf(staging_dir)
    final_dir.mkdir(parents=True, exist_ok=True)
    final_path = final_dir / expected_filename(row)
    if final_path.exists() and not overwrite:
        raise FileExistsError(f"Final PDF already exists: {final_path}. Use --overwrite to replace it.")
    if final_path.exists() and overwrite:
        final_path.unlink()

    shutil.move(str(staged_pdf), str(final_path))
    print(f"Moved: {staged_pdf}")
    print(f"To: {final_path}")

    next_index = next_index_after(rows, index_100)
    if next_index is None:
        print("No later rows with website links.")
        return

    write_state(next_index, state_path)
    next_row = row_for_index(rows, next_index)
    print("\nNext link:")
    print_row_instructions(next_row, final_dir)


def main() -> None:
    parser = argparse.ArgumentParser(description="Manual one-at-a-time formula page PDF workflow.")
    parser.add_argument(
        "command",
        choices=("show", "next"),
        help="'show' prints the current/indexed link. 'next' moves the newest staged PDF for that index and advances.",
    )
    parser.add_argument("--index", type=int, help="Explicit index_100 to show or move.")
    parser.add_argument("--overwrite", action="store_true", help="Replace an existing final PDF for the target index.")
    parser.add_argument("--csv-path", type=Path, default=CSV_PATH)
    parser.add_argument("--staging-dir", type=Path, default=STAGING_DIR)
    parser.add_argument("--final-dir", type=Path, default=FINAL_DIR)
    parser.add_argument("--state-path", type=Path, default=STATE_PATH)
    args = parser.parse_args()

    if args.command == "show":
        show_index(
            csv_path=args.csv_path,
            final_dir=args.final_dir,
            state_path=args.state_path,
            index_100=args.index,
        )
    else:
        move_index_and_show_next(
            csv_path=args.csv_path,
            staging_dir=args.staging_dir,
            final_dir=args.final_dir,
            state_path=args.state_path,
            index_100=args.index,
            overwrite=args.overwrite,
        )


if __name__ == "__main__":
    main()
