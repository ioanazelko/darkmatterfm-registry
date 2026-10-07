# Handoff: missing-papers work, as of 2026-10-07

For a Claude session picking this up on the server. Read `README.md` (astro-ph + hep-ph list and the
three abstract screens) and `hep_th_plan.md` (hep-th / gr-qc extension) first.

## State

| Piece | Status | Files |
|---|---|---|
| astro-ph + hep-ph missing list | done, 38,318 candidates | `missing_candidates.jsonl` |
| Abstract screen of that list (Sonnet 5 / Opus 5.5 / Fable 5.1) | done; recommended fetch set Opus ∪ Fable = 8,402 papers (86.0% recall, 10.2% FP on 1,920 Codex-labelled calibration papers) | `screen_results*/`, `screen_comparison_3way.md` |
| hep-th / gr-qc harvest | done (186,164 + 125,153 records) | `arxiv_meta_physics_{hep-th,gr-qc}.jsonl.gz` (local only, not in git) |
| hep-th / gr-qc missing list | done, 6,369 candidates (hep-th 3,572, gr-qc 2,797) | `missing_candidates_hepth.jsonl`, `missing_summary_hepth.md` |
| INSPIRE enrichment of the hep-th / gr-qc list | may be running or done: `python3 enrich_inspire.py missing_candidates_hepth.jsonl`, log `inspire_hepth.log` | |

Local-only inputs already copied to this server: the four `arxiv_meta_physics_*.jsonl.gz` harvests,
`corpus_members_minty-astro-ph.jsonl`, `inspire_cache.jsonl`, and
`../darkmatterfm_schema_starter/registry/models/all_paper_status_{hep,combined}.jsonl` (excluded via
`.git/info/exclude`).

## Next tasks (token-heavy; the user wants to use this week's token budget)

- **A. Abstract screen of the 6,369 hep-th / gr-qc candidates** with Opus 5.5 and Fable 5.1, same prompt
  as `screen_prompt_opus.md` / `screen_prompt_fable.md`, same 10 hidden calibration rows per batch so
  recall stays comparable. `make_screen_batches.py` reads only `missing_candidates.jsonl`; give it an
  option for the hep-th file and a separate output folder (e.g. `screen_batches_hepth/`,
  `screen_results_hepth_{opus,fable}/`). Screen gr-qc in its own batches: the prompt has no rule for
  "modified gravity instead of dark matter" papers. Run `check_alignment.py`-style row-shift checks after.
- **B. Full-text download** of the fetch set (Opus ∪ Fable 8,402, plus whatever A keeps) from arXiv
  e-prints, ~1 request/s (~3 h). No script exists yet. Keep the `.tex` text in MINT JSON form. This
  server has ~1.3 TB free, so the laptop's batch-and-delete scheme is not needed.
- **C. Full-text accept/reject** of the downloaded papers. The original step ran on GPT-5.5/Codex; write a
  Claude version of the prompt, check it against the 1,920 Codex-labelled calibration papers before the
  full run. Roughly 25k tokens per paper.
- **D. Card extraction** for accepted papers (schema in `registry/`).

## Rules from the user

- Ask before starting B (bulk arXiv download) and before choosing a fetch set other than Opus ∪ Fable.
- Subagents run on **Opus 5.5** (or Fable 5.1 where a second screen is wanted), never Sonnet unless the user says so.
- Do not run `build_missing_list.py`: it rewrites `missing_candidates.jsonl` and wipes its INSPIRE and screen fields.
- The laptop is the source of truth and this repo is public and mirrored anonymously: no names, emails,
  hostnames or home paths in committed files. Ask before committing or pushing from the server; new
  results normally go back to the laptop and are committed from there.
