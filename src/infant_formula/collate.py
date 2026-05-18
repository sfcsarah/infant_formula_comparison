from pathlib import Path
import pandas as pd

OUTPUTS_DIR = Path("outputs")


def collate() -> None:
    csvs = sorted(OUTPUTS_DIR.glob("*_p*_t*.csv"))
    if not csvs:
        raise FileNotFoundError(f"No extracted page CSVs found in {OUTPUTS_DIR}")

    df = pd.concat([pd.read_csv(f) for f in csvs], ignore_index=True)

    # subheader rows (e.g. "POWDERED", "LIQUID") have no model value
    df = df[df["model"].notna()]

    out_path = OUTPUTS_DIR / "all_formula.csv"
    df.to_csv(out_path, index=False)
    print(f"Saved {len(df)} rows to {out_path}")


if __name__ == "__main__":
    collate()
