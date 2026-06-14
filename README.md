# Infant Formula Comparison

Comparison of infant formulas for contaminants and ingredients, based on Consumer Reports test data (2025 and 2026).

## Setup

```bash
git clone <repo>
cd infant_formula_comparison
uv sync
uv pip install -e .
```

## Notebooks

Register the project's virtual environment as a Jupyter kernel (once per machine):

```bash
uv add --dev ipykernel
uv run python -m ipykernel install --user --name infant-formula --display-name "Infant Formula (uv)"
```

Then open the notebook:

```bash
uv run jupyter lab
```

Open `notebooks/01_process.ipynb`. It will automatically select the "Infant Formula (uv)" kernel.

## Scripts

Run the PDF extraction and collation pipeline:

```bash
uv run python scripts/extract_pdf_tables.py
uv run python scripts/collate.py
```

## Project structure

```
inputs/       PDF reports and manual ingredient entry file
outputs/      Extracted and collated CSVs
configs/      Column name configs generated during PDF extraction
src/          Importable package (infant_formula)
scripts/      Thin CLI wrappers around src/
notebooks/    Step-by-step pipeline walkthrough and visualization
```
