# Plan: adding hep-th (and possibly gr-qc) to the missing-papers list

Drafted 2026-09-30. Extends `missing_papers_plan.md` (astro-ph + hep-ph, steps A–G done).

> **Status (2026-10-01):** H1 done. `missing_papers/arxiv_meta_physics_hep-th.jsonl.gz` (186,164
> records, 75 MB) and `arxiv_meta_physics_gr-qc.jsonl.gz` (125,153, 57 MB); log
> `harvest_hepth_grqc.log`. Lexicon hits: hep-th-only 3,572 of 137,514 (603 with "dark matter" in
> abstract, 7 gold review refs); gr-qc-only (not astro-ph/hep-ph/hep-th) 2,797 of 44,277 (1,390 DM
> in abstract, 10 gold refs). Combined ≈6.4k new candidates.
> H2–H4 done 2026-10-07: `build_missing_list_hepth.py` → `missing_candidates_hepth.jsonl` (6,369:
> hep-th 3,572, gr-qc 2,797; 1,133 after the cutoff; 2,037 with "dark matter"; 1,656 have source in
> MINT) and `missing_summary_hepth.md`. None were in the corpus or the existing list. Gold set: 17
> review-cited papers are hep-th/gr-qc-only, 8 match the lexicon. `build_missing_list.py` and
> `gold_recall.py` now read only the astro-ph/hep-ph harvests (outputs unchanged). Next: H5 INSPIRE.

## 1. How big the hep-th gap is

hep-th is not entirely missing. The current universe in `missing_papers/` is "any paper with an
astro-ph* or hep-ph category", so hep-th papers **cross-listed** to those categories are already in
it (48,585 of them; 3,683 have "dark matter" in the abstract). The gap is hep-th papers with no
astro-ph or hep-ph category. The original hep-ph run took only hep-ph-tagged papers from
MINT-1T-ArXiv, so none of these papers ever reached the registry, even when MINT holds their source.

arXiv API counts (2026-09-30, all years):

| Query | Papers |
|---|---|
| hep-th, any | 186,164 |
| hep-th, not cross-listed to hep-ph / astro-ph | 137,514 |
| hep-th with "dark matter" in abstract | 4,297 |
| — of which not cross-listed to hep-ph / astro-ph (**the gap**) | **605** |
| gr-qc with "dark matter" in abstract, not in hep-ph / astro-ph / hep-th | 1,395 |

The full DM lexicon (axions, hidden sector, PBHs, boson stars, gravitinos, ...) will catch more
than the "dark matter" counts above. Expect about 1.5–3k hep-th-only lexicon candidates, many of
them string/axion papers with no DM model. gr-qc-only is about twice the hep-th gap and carries the
"modified gravity instead of DM" ambiguity the screen prompt does not yet resolve.

## 2. Steps (reusing the existing pipeline)

| Step | What | Script | Cost |
|---|---|---|---|
| H1 | Harvest OAI set `physics:hep-th` (and `gr-qc`, if included) | `harvest_oai.py physics:hep-th` (resumable, curl, sandbox off) | ~190k records, ~60 MB gz, about an hour at the polite pause |
| H2 | Widen the universe to hep-th-only (+ gr-qc-only); new slice label `hep-th` / `gr-qc`; new `missing_reason = category_not_selected`; record MINT-1T-ArXiv membership (a possible full-text source) | `build_missing_list.py` (small edit) | minutes |
| H3 | Lexicon filter, same lexicon; report the hep-th-only candidate count and how many have "dark matter" in the abstract | same | — |
| H4 | Recall check: of the 242 gold review-cited papers outside astro-ph/hep-ph, how many does hep-th (+ gr-qc) recover? This gives a number to quote for the gain | `gold_recall.py` | minutes |
| H5 | INSPIRE enrichment (cached, only the new ids) | `enrich_inspire.py` | ~1 req/paper |
| H6 | Abstract screen of the new candidates only, with **Opus 5.5 and Fable 5.1** (same prompt, same 10 hidden calibration rows per batch, so recall stays comparable); keep Opus ∪ Fable | `make_screen_batches.py` (new-ids-only mode) → agents → `merge_screen_results.py` | ~10–15 batches per model |
| H7 | Rebuild the viewer and README numbers; the kept hep-th papers join the step-H full-text fetch set | `build_missing_viewer.py`, README | — |

Re-running `build_missing_list.py` wipes the INSPIRE and screen fields. Either re-run merge and
enrich afterwards (both cached), or write the hep-th rows to a separate
`missing_candidates_hepth.jsonl` and leave the existing 38,318 rows alone. The separate file is
safer and is the default.

Disk: the harvest is about 60 MB. The full-text fetch for a few hundred to 1k kept papers is
≈0.1 GB of kept text, fetched in the same /tmp batches as the main set.

## 3. Decisions needed

1. **gr-qc too?** Recommended yes for the harvest and lexicon list, since the cost is the same.
   Screen gr-qc separately so its modified-gravity ambiguity does not mix with hep-th.
2. **Other categories** (nucl-th, cond-mat for DM detection theory, physics.ins-det)? Recommended
   no. They hold detector and nuclear-response papers, not DM models.
3. **Date range:** all years up to today, matching the astro-ph/hep-ph list (cutoff 2026-09-23;
   bump both to the harvest date).
