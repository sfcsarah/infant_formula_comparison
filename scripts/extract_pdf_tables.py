from pathlib import Path
import json
import pdfplumber
import pandas as pd

INPUTS_DIR = Path("inputs")
OUT_DIR = Path("outputs")
CONFIGS_DIR = Path("configs")

PDFS = {
    INPUTS_DIR / "Consumer-Reports-Baby-Formula-Test-Results-v4-March-2026.pdf": 2026,
    INPUTS_DIR / "Consumer-Reports-Test-Results-Infant-Formula-v2.pdf": 2025,
}


def decode_cell(cell: str | None) -> str | None:
    # pdfplumber reads rotated-90° text top-to-bottom, which reverses each character.
    # reversing per line recovers readable text; unit strings (containing '/') are dropped
    # because they add noise to column names (e.g. 'ug/kg').
    if not cell:
        return None
    lines = cell.split("\n")
    decoded = [line[::-1] for line in lines]
    meaningful = [w for w in decoded if "/" not in w and w.strip()]
    if not meaningful:
        return None
    return "_".join(meaningful).lower()


def get_column_names(table: list[list]) -> list[str]:
    # table[0] holds upright headers (Brand, Model, then None for contaminant sub-columns).
    # table[1] holds the rotated sub-headers (contaminant names, reversed by pdfplumber).
    # the rotated value wins when present; falls back to the upright header.
    cols = []
    for i, (h0, h1) in enumerate(zip(table[0], table[1])):
        decoded = decode_cell(h1)
        if decoded:
            cols.append(decoded)
        elif h0:
            cols.append(h0.lower())
        else:
            cols.append(f"col_{i}")
    return cols


def inspect_header_row(pdf_path: Path) -> None:
    # decodes column names from the rotated second header row and writes a JSON
    # template to configs/ for the user to review and correct before running extraction.
    # only the first table found is used — pages share the same structure.
    CONFIGS_DIR.mkdir(exist_ok=True)
    config_path = CONFIGS_DIR / f"{pdf_path.stem}_columns.json"

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                if len(table) < 2:
                    continue
                cols = get_column_names(table)
                config_path.write_text(json.dumps(cols, indent=2))
                print(f"Column names decoded from {pdf_path.name}:")
                for i, col in enumerate(cols):
                    print(f"  {i:2d}: {col}")
                print(f"\nSaved to {config_path}")
                print("Edit any incorrect names, then run again to extract.\n")
                return


def extract_data_rows(pdf_path: Path, report_year: int, out_dir: Path) -> int:
    # reads the user-edited column name config, then extracts rows 3+ from all pages
    # (skipping both header rows) and saves each page's table as a CSV.
    config_path = CONFIGS_DIR / f"{pdf_path.stem}_columns.json"
    columns = json.loads(config_path.read_text())

    count = 0
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables()
            for table_idx, table in enumerate(tables):
                if len(table) < 3:
                    continue
                data = table[2:]
                if len(data[0]) != len(columns):
                    print(f"  WARNING p{page_num} t{table_idx}: expected {len(columns)} cols, got {len(data[0])} — skipping")
                    continue
                df = pd.DataFrame(data, columns=columns)
                df["report_year"] = report_year
                out_path = out_dir / f"{pdf_path.stem}_p{page_num}_t{table_idx}.csv"
                df.to_csv(out_path, index=False)
                print(f"  p{page_num} t{table_idx}: {df.shape}")
                count += 1
    return count


def main():
    # two-phase: inspect generates the config for user review; extract runs once config exists.
    # delete a config file to re-inspect that PDF.
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for pdf_path, report_year in PDFS.items():
        print(f"\n{pdf_path.name}")
        config_path = CONFIGS_DIR / f"{pdf_path.stem}_columns.json"
        if not config_path.exists():
            inspect_header_row(pdf_path)
        else:
            n = extract_data_rows(pdf_path, report_year, out_dir=OUT_DIR)
            print(f"  → {n} table(s) saved")


if __name__ == "__main__":
    main()
