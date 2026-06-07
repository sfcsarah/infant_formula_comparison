# Plan: Notebooks + Streamlit Dashboard for Infant Formula Comparison

## Context

The pipeline already exists and has run successfully:
- `scripts/extract_pdf_tables.py` → per-page CSVs in `outputs/`
- `scripts/collate.py` → `outputs/all_formula.csv`
- `outputs/all_formula_ingredients.csv` — enriched final table (20 cols: brand, model, contaminants, has_soy, has_palm_oil, ingredient_list, website_link, report_year)

Three deliverables: package migration (Option B), a processing notebook, and a hosted Streamlit dashboard with an interactive table.

---

## Phase 0: Option B migration

Convert the project from loose scripts to a proper importable package.

**Files to create:**
```
src/
  infant_formula/
    __init__.py          # empty
    collate.py           # moved from scripts/collate.py
    extract_pdf_tables.py  # moved from scripts/extract_pdf_tables.py
    save_page.py         # moved from scripts/save_page.py
```

**Files to update:**
- `pyproject.toml` — add `[build-system]` with hatchling
- `scripts/collate.py` → thin wrapper: imports + calls `infant_formula.collate.collate()`
- `scripts/extract_pdf_tables.py` → thin wrapper calling `infant_formula.extract_pdf_tables.main()`
- `scripts/save_page.py` → thin wrapper

**Run once after migration:**
```bash
uv pip install -e .
```

**Internal imports:** existing scripts use relative imports like `from pathlib import Path` — these don't change. No cross-module imports between the three files today.

---

## Phase 1: Processing notebook

**File:** `notebooks/01_process.ipynb`

No `sys.path` hacks needed — package is installed. Imports are clean:
```python
from infant_formula.collate import collate
from infant_formula.extract_pdf_tables import extract_data_rows
```

Sections:
1. **Setup** — imports, path constants
2. **Raw per-page CSVs** — load all `outputs/*_p*_t*.csv`, display shapes + head
3. **Column configs** — show both `configs/*.json` files
4. **Collate** — call `collate()`, show `all_formula.csv` shape
5. **Enriched table** — load `all_formula_ingredients.csv`, dtypes, `.describe()`, value counts for `has_soy`/`has_palm_oil`
6. **Data quality** — count ND/NT vs numeric per contaminant column; flag `recalled` rows

---

## Phase 2: Streamlit dashboard

**File:** `streamlit_app.py` (repo root — required by Streamlit Community Cloud)

### Interactive table (main panel)
- `st.dataframe` with the full `all_formula_ingredients.csv`
- Column selector (multiselect): user picks which columns to show
- All active filters applied before display

### Sidebar filters
| Filter | Widget | Column(s) |
|---|---|---|
| Brand | multiselect | `brand` |
| Report year | checkboxes | `report_year` |
| Has soy | radio (Yes / No / Either) | `has_soy` |
| Has palm oil | radio (Yes / No / Either) | `has_palm_oil` |
| Contaminant threshold | dropdown (pick contaminant) + number input (max value) | any numeric contaminant col |

### Summary row above table
- Filtered formula count
- Brands represented
- % rows with detected lead (lead != ND/NT)

### ND/NT handling
Contaminant columns contain mixed types: numeric strings with commas (`"8,026,667"`), `"ND"`, `"NT"`.
Strategy: coerce to float on load (strip commas, ND/NT → NaN). Keep a separate `_raw` column if original strings are needed for display. The threshold slider operates on the numeric version; the table displays the raw strings.

---

## Phase 3: Streamlit Community Cloud deploy

**New file:** `requirements.txt` (repo root)
```
pandas
plotly
streamlit
-e .
```

`-e .` installs the local `infant_formula` package in Streamlit's build environment (requires `[build-system]` in pyproject.toml — set up in Phase 0).

**Deploy steps (manual, post-implementation):**
1. Push repo to GitHub
2. Go to share.streamlit.io → "New app"
3. Select repo, branch `main`, main file `streamlit_app.py`
4. Deploy

---

## Dependencies to add to pyproject.toml
```
plotly>=5.0
streamlit>=1.35
```

(jupyter is a dev tool — install separately with `uv add --dev jupyter`)

---

## File summary

| File | Action |
|---|---|
| `src/infant_formula/__init__.py` | Create (empty) |
| `src/infant_formula/collate.py` | Move from `scripts/` |
| `src/infant_formula/extract_pdf_tables.py` | Move from `scripts/` |
| `src/infant_formula/save_page.py` | Move from `scripts/` |
| `scripts/collate.py` | Replace with thin wrapper |
| `scripts/extract_pdf_tables.py` | Replace with thin wrapper |
| `scripts/save_page.py` | Replace with thin wrapper |
| `pyproject.toml` | Add `[build-system]` + plotly/streamlit deps |
| `requirements.txt` | Create |
| `notebooks/01_process.ipynb` | Create |
| `streamlit_app.py` | Create |

---

## Verification
1. `uv pip install -e .` — installs cleanly, no errors
2. `python -c "from infant_formula.collate import collate"` — no import error
3. `python scripts/collate.py` — still works as CLI
4. `uv run jupyter lab` → open `notebooks/01_process.ipynb` → Run All — no errors
5. `uv run streamlit run streamlit_app.py` — app loads, filters respond, table updates
6. Push to GitHub → deploy on share.streamlit.io → confirm it loads
