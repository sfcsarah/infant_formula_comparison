You are continuing work in /Users/sarahfouzia/llm_workspace/repos/infant_formula_comparison.

Goal:
Continue the manual PDF capture workflow for infant formula product pages. The process is:
1. Show me the next `website_link` from `inputs/all_formula_ingredients_manual_entry.csv` based on `index_100`.
2. I open the link in the browser and save the page as a PDF into `outputs/web_links_codex`.
3. I return and say `next`.
4. You move/rename the newest staged PDF into `outputs/formula_pages_manual/<index>_<brand>_<model>.pdf`, overwriting if needed, then show me the next link.

Current workflow files:
- `src/infant_formula/manual_pdf_workflow.py`
- `scripts/manual_pdf_workflow.py`

Current command pattern:
- Show next row:
  `UV_CACHE_DIR=/private/tmp/uv-cache uv run python scripts/manual_pdf_workflow.py show --index <INDEX>`
- Move newest staged PDF for that row and advance:
  `UV_CACHE_DIR=/private/tmp/uv-cache uv run python scripts/manual_pdf_workflow.py next --index <INDEX> --overwrite`

Important details:
- The workflow is index-driven, not auto-increment.
- The CSV is TSV: `inputs/all_formula_ingredients_manual_entry.csv`
- Final PDFs go in: `outputs/formula_pages_manual`
- Staging PDFs go in: `outputs/web_links_codex`
- The state file is: `outputs/formula_pages_manual_state.txt`
- We have already completed rows 101 through 152.
- The next row to work on is 153:
  brand: Member’s Mark (Sam’s Club)
  model: Advantage Premium
  link: https://www.samsclub.com/ip/Member-s-Mark-Advantage-Premium-Baby-Formula-Powder-with-Iron-36-oz/13581473060
  expected filename: 153_Members_Mark_Sams_Club_Advantage_Premium.pdf

Be strict about using `index_100` from the CSV, not file order. Keep responses concise and only give the next link or the move result. If I say `next` without an index, use the saved state file.
