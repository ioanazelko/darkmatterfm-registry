# Missing papers: astro-ph + hep-ph, brought up to 2026-09-23

Built 2026-09-24. This lists the arXiv papers that could hold a dark-matter model but never
entered the registry, either because the happyface (MINT-1T) corpus lacked them or because
they appeared after its cutoff. Plan: `missing_papers_plan.md`.

## Headline numbers

| | |
|---|---|
| arXiv universe (astro-ph + hep-ph, primary or cross-list, to 2026-09-23) | 558,439 papers |
| Registry corpus (minty-astro-ph 156,031 + hep-ph candidates + screened) | 165,547 ids |
| **Missing candidates** (title/abstract match the DM lexicon, not in corpus) | **38,318** |
| — not in corpus, within the corpus span (≤ 2024-05) | 29,618 |
| — after the corpus cutoff (2024-06 → 2026-09) | 8,700 |
| — with "dark matter" in the abstract | 24,378 |
| Abstract screen, kept (NOVEL_MODEL + UNSURE): Sonnet 5 / Opus 5.5 / Fable 5.1 | 7,201 / 7,739 / 7,573 |
| — kept by Opus ∪ Fable (recommended set) | 8,402 |
| — kept by any of the three | 9,908 |

**Corpus coverage** of papers with "dark matter" in the abstract, by year: ≈0–15% before
1999 (MINT's arXiv sources start 2000-01), 21–30% for 2000–04, ≈50% for 2010–18, and 68% for
2022–24 (`missing_summary.md`).

**Independent recall check** (`gold_recall.md`): the arXiv papers cited by four major DM
reviews (Cirelli–Strumia–Zupan 2024, Arcadi et al. 2018 and 2024, Bertone–Hooper–Silk 2005),
3,504 of them in astro-ph/hep-ph. The corpus held **49.7%** of them. The corpus plus this list
covers **90.6%**. The remaining 9% have no lexicon term in their title or abstract.

## How far to trust each stage

- **Lexicon filter** (title + abstract): catches 96.5% of the 4,922 accepted registry papers.
  The misses are mostly inflation, brane and dark-energy papers that Codex accepted loosely.
- **Abstract screen** (the Gemini gate's question applied to title + abstract, three-label
  output). Run three times on the same 192 batches and prompt, with three models. Each batch
  hides 10 calibration papers that Codex had already triaged from full text (1,920 total:
  521 accepted, 1,399 rejected):

  | Screen | Recall (Codex-accepted kept) | False positives (Codex-rejected kept) | Candidates kept |
  |---|---|---|---|
  | Sonnet 5 (first run, `screen_results/`) | 69.5% | 14.7% | 7,201 |
  | Opus 5.5 (`screen_results_opus/`) | **83.9%** | 8.9% | 7,739 |
  | Fable 5.1 (`screen_results_fable/`) | 80.0% | **7.5%** | 7,573 |
  | Opus ∪ Fable | 86.0% | 10.2% | 8,402 |
  | ≥ 2 of 3 | 80.4% | 8.5% | 7,388 |
  | any of the three | 87.7% | 18.2% | 9,908 |

  Opus and Fable agree on keep/drop for 96.1% of candidates (κ = 0.88); Sonnet agrees with
  either at ~90% (κ 0.66–0.68). Sonnet leans strict and uses NOVEL_MODEL heavily; Opus and
  Fable put more papers into UNSURE. Adding Sonnet to Opus ∪ Fable gains only 1.7 points of
  recall for +1,500 papers, mostly false positives. The first run was meant to use Opus and
  ran on Sonnet by mistake (run log: `screen_run_log.md`). Even the best screen misses ~14% of
  real model papers, because abstracts undersell the model: **use it to rank, not to drop.**
- **Known ambiguity:** the prompt has no rule for "modified gravity instead of dark matter"
  papers; all three models mark these UNSURE or NOT_NOVEL_MODEL inconsistently.
- Expected yield: at ~84% recall on a pool resembling the triaged one, roughly 5–7k
  model-introducing papers among the 38k, similar to or larger than the current 4,922.

## Opus 5.5 rerun of the abstract screen (2026-09-24)

Same 192 batches and prompt (`screen_prompt_opus.md`, identical except for the output folder and a
"read abstracts in full" line), results in `screen_results_opus/`. Comparison in
`screen_comparison.md` (`compare_screens.py`); disagreements listed in `screen_comparison.jsonl`.
On the 1,920 hidden calibration papers, Opus kept **83.9%** of Codex-accepted papers (Sonnet 69.5%)
while keeping only 8.9% of Codex-rejected ones (Sonnet 14.7%). The union of both keeps 86.6% / 18.0%.
Opus keeps 7,739 missing candidates (3,940 NOVEL_MODEL + 3,799 UNSURE) vs Sonnet's 7,201; 9,520 are
kept by either. `missing_candidates.jsonl` still carries the Sonnet decisions.

## Fable 5.1 rerun and three-way comparison (2026-09-29)

Same batches and prompt (`screen_prompt_fable.md`), results in `screen_results_fable/`; three-way
comparison in `screen_comparison_3way.md` (`compare_screens_3way.py`). On the calibration papers:
Sonnet 69.5% recall / 14.7% FP, Opus 83.9% / 8.9%, Fable 80.0% / 7.5%; Opus ∪ Fable 86.0% / 10.2%
(8,402 candidates kept); any of the three 87.7% / 18.2% (9,908). Opus and Fable agree on keep/drop
for 96.1% of candidates (κ 0.88); Sonnet agrees with either at ~90% (κ 0.66–0.68).

## Files

| File | What |
|---|---|
| `missing_candidates.jsonl` | One row per candidate: id, categories, submitted, missing_reason, slice, lexicon hits, title, abstract, authors, DOI/journal, INSPIRE citations / doc type, screen_decision, screen_model_class |
| `missing_candidates.html` | Viewer: filters by reason, slice, screen decision, "dark matter" phrase, minimum citations; sortable (19 MB, local) |
| `missing_summary.md`, `screen_summary.md`, `gold_recall.md` | The numbers above (`screen_summary.md` and the gold-set "kept" line are Sonnet-only) |
| `arxiv_meta_physics_{astro-ph,hep-ph}.jsonl.gz` | Full OAI harvest (330 MB) |
| `corpus_members_minty-astro-ph.jsonl` | Rebuilt minty-astro-ph manifest (156,031 papers, 287 shards) |
| `gold_review_refs.jsonl` | Review-cited gold set |
| `screen_batches/` | Screen inputs, 192 batches with hidden calibration rows; `keymap.jsonl` maps keys to arXiv ids |
| `screen_results/`, `screen_results_opus/`, `screen_results_fable/` | Per-batch decisions from Sonnet 5, Opus 5.5 and Fable 5.1 |
| `screen_prompt.md`, `screen_prompt_opus.md`, `screen_prompt_fable.md` | The three prompts (identical task; output folder differs; the Opus/Fable versions add "read every abstract in full") |
| `screen_comparison.md`, `screen_comparison.jsonl` | Sonnet vs Opus comparison; every disagreeing paper with title (`compare_screens.py`) |
| `screen_comparison_3way.md` | Sonnet vs Opus vs Fable: counts, calibration, unions, pairwise κ (`compare_screens_3way.py`) |
| `screen_run_log.md`, `screen_traces/` | Token and model log plus transcripts for the Sonnet run |

Rebuild order: `harvest_oai.py` → `list_tar_members.py` → `build_missing_list.py` →
`enrich_inspire.py` (cached) → `make_screen_batches.py` → agents → `merge_screen_results.py`
→ `gold_recall.py` → `build_missing_viewer.py`. Re-running `build_missing_list.py` resets the
INSPIRE and screen fields, so re-run the later steps after it.

## Suggested next step (not started; needs a go-ahead)

Fetch full texts for the missing list and run them through the original funnel (full-text
lexical filter → Gemini gate for astro-ph → Codex triage → extraction).

- **Which papers:** recommended Opus ∪ Fable (8,402 papers, 86% recall, 10% false positives).
  Alternatives: ≥ 2 of 3 (7,388) or any of the three (9,908). Later, the "dark matter"-abstract
  papers that all screens reject. Not yet decided; `missing_candidates.jsonl` and the viewer
  still carry the Sonnet decisions until the choice is written in.
- **Disk budget** (measured 2026-09-24 on 149 sampled e-prints, 15 downloaded and deleted):
  e-print tarballs average 1.29 MB (median 0.21 MB); LaTeX text alone averages ~91 KB. For
  ~8.4k papers that is ~11 GB to download but only ~0.8 GB of text to keep. The disk was 89%
  full (41 GB free), so fetch in batches of ~200 into `/tmp` (RAM-backed), keep only the
  `.tex` text in MINT JSON form, delete each batch's tarballs and figures, and store the text
  outside Dropbox. About 3 hours at arXiv's polite rate of 1 request/s.
- **Open:** whether to put a contact address in the User-Agent (one size-sampling pass sent
  the user's email; later requests did not).
