# Compilation Report (Revision 2)

Document: `Dissertation_IoT_AI_Poultry.tex` (single source file)
Compiled PDF: `Dissertation_IoT_AI_Poultry_UPDATED.pdf` (original name was locked/open in a viewer at write time)
Engine: pdfLaTeX, 3 passes (manual `hangparas` references; no BibTeX run needed)
Date: 2026-06-26

## Result: SUCCESS — complete 93-page PDF produced

- LaTeX errors: 0
- Undefined citations: 0
- Undefined references/labels (`??`): 0
- Duplicate labels: 0
- Missing figure files: 0
- Overfull \hbox > 30 pt: 0
- Font: Times (mathptmx) | Landscape page: 1 (hardware materials table) | UBa logo: renders on title page

## Page counts

| Section | Start | Length |
|---------|-------|--------|
| Chapter 1: Introduction | 1 | ~5 pages |
| Chapter 2: Literature Review | 6 | ~26 pages |
| Chapter 3: Materials and Methods | 32 | ~45 pages |
| Appendix A: Project Time Frame | 77 | 1 page |
| Appendix B: Budget Estimate | 78 | 1 page |
| References | 79 | to p.93 |

Total ≈ 93 pages (within NAHPI M.Eng 80–150).

## Front matter
- Table of Contents, List of Tables (21), List of Figures (33): populated.
- Roman numerals for preliminaries; Arabic from Chapter 1.

## Revision-2 verification
- Em-dashes in the body: 0.
- Diagrams 3.2/3.8/3.12/3.17 (iterative, ML pipeline, alert state, component): confirmed vertical (media-box height > width).
- Complete-workflow and overall-architecture diagrams: each on its own dedicated page.
- 11 placeholders inline at their discussed subsections; filenames p01–p11; no duplicate labels.
- Table 3.2 column widths adjusted (tool 3.3 cm fixed; role flexible).
- Hardware section: wiring schedule + build procedure added.

## Recompile
```
pdflatex Dissertation_IoT_AI_Poultry.tex   (x3)
```
No bibtex/biber step (manual APA `hangparas` list).

## Residual items
- Close the open `Dissertation_IoT_AI_Poultry.pdf` so the next compile can overwrite it (or rename `_UPDATED.pdf`).
- 16 minor overfull boxes (≤ ~22 pt) — cosmetic.
- Two stray helper images `_cand_600.jpg` / `_cand_232.jpg` and `_verify_title.png` can be deleted (could not be removed automatically by this environment).
