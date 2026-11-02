# Extraction-accuracy study (paper Sec. "Validation")

Grades a stratified sample of model cards against their source papers.
This is the paper's main reviewer-blocking validation item.

## Files

- `accuracy_sample_manifest.jsonl` — the 75 sampled cards (full card content +
  stratum metadata). Drawn by `scripts/draw_accuracy_sample.py`, seed 20260902:
  50 enriched / 25 base, all 23 taxonomy classes, tier spread, plus 5
  schema-invalid hard cases.
- `accuracy_grading.html` — the grading interface (built by
  `scripts/build_accuracy_grader.py`). Self-contained; open in any browser.
- `accuracy_grades_<grader>.jsonl` — exported grades (one file per grader).

## Grading protocol

1. Open `accuracy_grading.html`, enter your initials in the Grader box.
2. For each card: open the linked arXiv paper, then grade every section:
   - **correct** — matches the paper.
   - **partially correct** — right idea, wrong or incomplete detail.
   - **incorrect** — contradicts the paper.
   - **hallucinated** — content with no basis in the paper.
   - **cannot judge** — the paper does not let you decide (excluded from
     accuracy denominators).
3. Progress saves automatically in the browser (localStorage). Export JSONL
   when done (and periodically as backup). Import restores from an export.
4. For inter-grader agreement, a second grader repeats this on any subsample
   (>=15 cards recommended); the analysis handles overlap automatically.

## Analysis

    python scripts/analyze_accuracy.py accuracy_grades_IZ.jsonl [accuracy_grades_XX.jsonl] --latex

Reports per-section accuracy (strict and half-credit) with Wilson 95%
intervals, hallucination rates, enriched-vs-base split, Cohen's kappa per
grader pair, and a LaTeX table for the paper.

## Status (2026-09-19)

An LLM-judged grading pass over all 75 cards is done: `accuracy_grades_CLAUDE.jsonl`,
summarized in `RESULTS_LLM_GRADED.md` (instructions used: `GRADING_INSTRUCTIONS_LLM.md`).
Human expert grading (≥15 cards for inter-grader κ) is still pending and is what the
protocol above describes.

Source PDFs and the pdftotext versions the LLM graders read are kept outside any repository in
`dark_matter_model_registry/accuracy_study_source_papers/` (with the raw per-batch grader outputs).
