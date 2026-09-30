# Plan: assembling the list of papers missing from the happyface corpus

Drafted 2026-09-24. Goal: a list of the arXiv papers that could hold a dark-matter model but
never reached the registry pipeline because they were not in the happyface (MINT-1T) corpus.
The list is built first; deciding which papers to fetch and run comes after.

> **Status (2026-09-29):** steps A–G are done; results and files in `missing_papers/README.md`.
> 38,318 candidates (astro-ph + hep-ph, to 2026-09-23). Gold-set recall: corpus 49.7%, corpus +
> list 90.6%. The abstract screen ran on three models (Sonnet 5, Opus 5.5, Fable 5.1); best
> calibration recall is Opus 83.9% / Fable 80.0%, and the recommended fetch set is Opus ∪ Fable
> (8,402 papers, 86% recall). Step H (full-text fetch) has a disk plan (~0.8 GB of kept text)
> and awaits a go-ahead plus the choice of paper set.

## 1. What the collection had

| Slice | Source | Papers | Lexical hits ("dark matter" AND whole-word "model") | Entered triage |
|---|---|---|---|---|
| astro-ph | `Smith42/minty-astro-ph`, shards `data/astro-ph-00000..00286.tar` | 156,006 | 39,004 → 36,919 | 3,458 (after Gemini gate) |
| hep-ph | `mlfoundations/MINT-1T-ArXiv`, shards `arXiv_src_YYMM_NNN_wds.tar` | 69,093 | 17,748 → 17,379 | 17,379 (no gate) |
| combined | deduplicated | | | 18,871 screened → 4,922 accepted → 6,145 cards |

Measured from `models/all_paper_status_*.jsonl`:

- **Time span:** both slices run 1994-08 to **2024-05 (arXiv 2405)** and hold nothing later.
  There are about 28 months of papers since then (2024-06 to now).
- **Whole months absent (hep-ph):** no candidate from 23 months: 9409–9412, 9501–9503, 9505,
  9507, 9510–9512, 9603, 9612, 9704, 9812, **0110, 0205, 0206, 0305, 0403, 0506, 0602**.
  The pre-1999 gaps may just be low volume. The 2001–2006 gaps look like whole arXiv source
  tars that MINT did not process.
- **Partial months:** even the months that are present are thinned. In the pilot below,
  roughly 30–50% of hep-ph papers with "dark matter" in the abstract are missing.
- **No local corpus manifest:** nothing on disk lists the 156,006 / 69,093 IDs, or the
  39,004 / 36,919 astro-ph lexical hits. The status files only list papers that entered
  triage. For astro-ph that is after the Gemini gate, so astro-ph coverage cannot be measured
  from local files yet.

### Coverage pilot (arXiv API, 2026-09-24)

This asks, for each sampled month, what fraction of arXiv papers cross-listed to hep-ph with
"dark matter" in the abstract are among the 17,379 hep-ph candidates. A paper in the corpus
with "dark matter" in its abstract passes the full-text lexical filter almost surely, so a
paper not found is in effect not in the corpus.

| Month | DM-abstract papers (hep-ph*) | Found in hep candidates |
|---|---|---|
| 2007-03 | 32 | 59% |
| 2010-03 | 57 | 47% |
| 2015-12 | 117 | 50% |
| 2020-12 | 113 | 62% |
| 2023-05 | 107 | 61% |
| 2024-03 | 91 | 71% |

**Coverage of in-scope hep-ph papers is about 50–70%.** For papers whose primary category is
hep-ph it is about 55–80%. (2006-02 returned an API error; retry it. It is one of the
"absent" months.)

### Size of the missing pool (arXiv API totals, "dark matter" in abstract)

| Category (primary or cross-list) | All time | ≤ 2024-05 | After 2024-05 |
|---|---|---|---|
| hep-ph | 20,264 | 17,046 | ~3,200 |
| astro-ph | 32,415 | 27,798 | ~4,600 |
| hep-th | 4,290 | | |
| gr-qc | 7,004 | | |
| any category | 45,824 | | |

First-order estimate: **~15–20k DM-abstract papers are missing** (hep-ph ~7k within the span
plus 3.2k after it; astro-ph probably of similar or larger size, not yet measured). The
full-text filter was broader than an abstract filter, so the true missing candidate pool is
larger. We expect roughly one accepted paper in four of these, i.e. **~4–5k more
model-introducing papers**, on the order of today's 4,922.

## 2. Where the gaps come from (each missing paper gets one of these tags)

1. `not_in_mint`: inside 1994-08…2024-05 and in astro-ph/hep-ph, but not in the MINT release
   (a whole month missing, or thinned within a month).
2. `after_cutoff`: submitted 2024-06 or later.
3. `out_of_category`: DM papers whose primary category is outside the two slices and that
   are not cross-listed to astro-ph or hep-ph: hep-th, gr-qc, hep-ex, nucl-th, quant-ph (axion
   and ultralight searches), cond-mat (detector-target DM).
   Note: the hep-ph slice already holds 468 astro-ph, 76 hep-th and 21 gr-qc primaries,
   because MINT tags by cross-list.
4. `in_corpus_not_triaged`: *not missing, and tracked separately*. Examples: astro-ph papers
   the Gemini gate rejected (36,919 → 3,458), the 3 extraction errors, and the lexical-filter
   misses. This is a recall question about the pipeline, not about the corpus.

## 3. Assembly steps

**A. Build the arXiv universe (metadata only, no full texts).**
Harvest arXiv OAI-PMH (`export.arxiv.org/oai2`, `metadataPrefix=arXivRaw`, sets
`physics:astro-ph`, `physics:hep-ph`, `physics:hep-th`, `physics:gr-qc`, `physics:hep-ex`,
`physics:nucl-th`). Each record gives id, version dates, all categories, title, abstract,
DOI and journal-ref. Alternative: the Kaggle "Cornell arXiv metadata" snapshot (one ~4 GB
JSON file, needs a download OK). Output: `missing_papers/arxiv_universe.jsonl`.

**B. Recover the corpus manifest.** Get the full ID lists of the 156,006 astro-ph and 69,093
hep-ph papers, plus the 39,004 / 36,919 astro-ph lexical hits, from whoever ran the lexical
filter (Nolan did the 156,006 count). Fallback: list tar member names straight from Hugging
Face with HTTP range reads of the tar headers. That is slow (one request per member) but needs
no 800 GB download. Output: `missing_papers/corpus_manifest.jsonl` (`arxiv_id`, `slice`,
`shard`).

**C. Normalize IDs and diff.** Map registry IDs (`1003_0459` → `1003.0459`,
`astro-ph0405083` → `astro-ph/0405083`) and strip versions. Then:
`missing = universe − corpus_manifest − screened(18,871)`. Tag each entry with the §2 reason.

**D. Abstract-level candidate filter, calibrated on what we already have.** Without full
text, filter on title + abstract with a DM lexicon: "dark matter", "dark sector", WIMP,
FIMP/freeze-in, axion/ALP, sterile neutrino, fuzzy/ultralight, SIDM/self-interacting,
primordial black hole, asymmetric DM, dark photon, hidden sector, mirror/twin, Q-ball, … .
Calibrate on the in-corpus papers. Pull the abstracts of the 4,922 accepted papers from the
step-A metadata and choose the lexicon whose recall on them is ≥ 97%. Report that recall and
the precision on rejected papers. This makes the missing-list filter comparable to the
original full-text filter.

**E. Enrich for prioritization.** Add INSPIRE-HEP citation counts (and ADS for astro-ph-only
papers) plus the publication venue. Flag reviews and proceedings (triage usually rejects
them). INSPIRE queries also act as a second recall source.

**F. Independent recall check.** Build a small gold set of known DM-model papers, for
example the model papers cited in two or three major DM reviews, or the papers behind the
current family taxonomy. Measure the fraction in the (i) corpus, (ii) registry, and
(iii) corpus + missing list. This measures the recall number the paper now calls
"unmeasured".

**G. Output the list.** Write `missing_papers/missing_candidates.jsonl` with one row per
paper: `arxiv_id, primary_category, categories, submitted, title, abstract,
missing_reason, lexicon_hits, inspire_citations, doi, journal_ref, priority`. Add a summary
table by reason × year × category and an HTML viewer in the style of `paper_status.html`.

**H. (Next phase, not part of the list) Fetch and run.** Get LaTeX sources via the arXiv
e-print endpoint at a polite rate, or the arXiv S3 requester-pays bulk for large volumes.
Convert them to the MINT `.json` member format and push them through the *same* funnel:
full-text lexical filter → Gemini gate (astro-ph) → Codex triage → extraction. The
before/after counts then stay comparable. Registry IDs must stay unique against the
existing 18,871.

## 4. Open decisions

- ~~Scope of categories~~: decided 2026-09-24, astro-ph + hep-ph (primary or cross-list) only.
- ~~Time cutoff~~: decided 2026-09-24, up to 2026-09-23 (the harvest date).
- Which screen output feeds step H: recommended Opus ∪ Fable (8,402); see the README table.
- Should the astro-ph missing papers go through the Gemini gate like the originals, or
  straight to Codex like hep-ph?
- ~~Who holds the corpus manifest (step B)?~~ Rebuilt from HF tar headers
  (`corpus_members_minty-astro-ph.jsonl`, 156,031 papers).
