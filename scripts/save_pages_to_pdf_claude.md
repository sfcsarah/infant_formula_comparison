You are continuing work in /Users/sarahfouzia/llm_workspace/repos/infant_formula_comparison.

Task:
Resume the manual formula-page PDF workflow. The user opens each link manually, saves the page as a PDF into `outputs/web_links_codex`, then says `next`. Your job is to move/rename that staged PDF into the final folder and then provide the next link.

Workflow details:
- Source CSV: `inputs/all_formula_ingredients_manual_entry.csv` (TSV)
- Final PDF folder: `outputs/formula_pages_manual`
- Staging folder: `outputs/web_links_codex`
- Workflow scripts:
  - `src/infant_formula/manual_pdf_workflow.py`
  - `scripts/manual_pdf_workflow.py`

Commands to use:
- Show the current row/link:
  `UV_CACHE_DIR=/private/tmp/uv-cache uv run python scripts/manual_pdf_workflow.py show --index <INDEX>`
- Move the newest staged PDF for that row and advance:
  `UV_CACHE_DIR=/private/tmp/uv-cache uv run python scripts/manual_pdf_workflow.py next --index <INDEX> --overwrite`

Rules:
- Use the CSV `index_100` values exactly.
- Do not infer the next row from filenames.
- If the user says `next` without an index, use the saved state file:
  `outputs/formula_pages_manual_state.txt`
- Keep the response short: either the next link, or the move result plus the next link.

Current progress:
- Rows 101 through 152 are completed.
- Next row to work on: 153
  - brand: Member’s Mark (Sam’s Club)
  - model: Advantage Premium
  - link: https://www.samsclub.com/ip/Member-s-Mark-Advantage-Premium-Baby-Formula-Powder-with-Iron-36-oz/13581473060
  - expected filename: 153_Members_Mark_Sams_Club_Advantage_Premium.pdf
