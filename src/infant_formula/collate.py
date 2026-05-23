from pathlib import Path
import pandas as pd

OUTPUTS_DIR = Path(__file__).parent.parent.parent / "outputs"


def collate() -> None:
    csvs = sorted(OUTPUTS_DIR.glob("*_p*_t*.csv"))
    if not csvs:
        raise FileNotFoundError(f"No extracted page CSVs found in {OUTPUTS_DIR}")

    df = pd.concat([pd.read_csv(f) for f in csvs], ignore_index=True)

    # remove thousands-separator commas from numeric-like strings
    # (e.g. "8,026,667" -> "8026667"). leave ND and NT as strings.
    cols_to_fix = df.columns.difference(["brand", "model"])
    for col in cols_to_fix:
        if df[col].dtype == "object":
            df[col] = df[col].str.replace(",", "", regex=False)

    # subheader rows (e.g. "POWDERED", "LIQUID") have no model value
    df = df[df["model"].notna()]

    out_path = OUTPUTS_DIR / "all_formula.csv"
    df.to_csv(out_path, index=False)
    print(f"Saved {len(df)} rows to {out_path}")


if __name__ == "__main__":
    collate()
