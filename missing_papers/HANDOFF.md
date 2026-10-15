# Handoff: missing-papers work, as of 2026-10-15

For a Claude session picking this up on the server. Read `README.md` (astro-ph + hep-ph list and the
three abstract screens), `hep_th_plan.md` (hep-th / gr-qc extension) and **`extraction/README.md`
(the runbook for the next step)** first.

## State

| Piece | Status | Files |
|---|---|---|
| astro-ph + hep-ph missing list | done, 38,318 candidates | `missing_candidates.jsonl` |
| Abstract screen of that list (Sonnet 5 / Opus 5.5 / Fable 5.1) | done; fetch set Opus ∪ Fable = 8,402 papers (86.0% recall, 10.2% FP on 1,920 Codex-labelled calibration papers) | `screen_results*/`, `screen_comparison_3way.md` |
| hep-th / gr-qc missing list | done, 6,369 candidates (hep-th 3,572, gr-qc 2,797) | `missing_candidates_hepth.jsonl`, `missing_summary_hepth.md` |
| Abstract screen of the hep-th / gr-qc list (Opus 5.5, Fable 5.1) | done on the server: Opus ∪ Fable kept 1,046 (hep-th 429, gr-qc 617) | `screen_*_hepth*` (server only, not yet in git) |
| Full-text download | done on the server: 9,214 ok, 210 PDF-only, 27 not found, 1 error (669 MB) | `fulltext/`, calibration texts in `fulltext_calib/` (server only) |
| Full-text triage pilot, reconstructed rule | done on the server: 79% agreement with Codex, 59% recall, 1% FP on 200 calibration papers | `fulltext_triage/pilot/score_opus.md` (server only) |
| INSPIRE enrichment of the hep-th / gr-qc list | not run (optional; metadata only): `python3 enrich_inspire.py missing_candidates_hepth.jsonl` | |

Local-only inputs on the server, excluded via `.git/info/exclude`: the four
`arxiv_meta_physics_*.jsonl.gz` harvests, `corpus_members_minty-astro-ph.jsonl`, `inspire_cache.jsonl`,
and `../darkmatterfm_schema_starter/registry/models/all_paper_status_{hep,combined}.jsonl`.

## Next step: full-text accept/reject and card writing, as one step

The original Codex prompts are in `registry/codex_prompts/` (see its `README.md`). They show the
original pipeline had **no** separate full-text triage: each GPT-5.5 worker read ~10 papers in full
and either wrote 1–10 model-only cards or a rejected status with a reason, following
`extraction_output_guide.md`. The 1,920 calibration labels come from that combined step.

`extraction/` is the Claude version of that step, ready to run: worker prompt (adapted from the
Codex one), staging, a headless parallel driver with usage logging and stop-on-limit, a batch
validator (guide, profile and current schemas), priority waves from the two screens, scoring
against Codex, and merging. Follow `extraction/README.md`: setup and `--check`, one batch by hand,
the 200-paper calibration pilot, the acceptance-rule decision, then waves by tier. The reconstructed
`fulltext_triage_prompt.md` is superseded by the original guide, but its pilot is a useful
comparison.

## Rules from the user

- Subagents and workers run on **Opus 5.5** (or Fable 5.1 where a second screen is wanted), never
  Sonnet unless the user says so.
- After the calibration pilot, show the user `runs/pilot/score.md` and let them choose the
  acceptance rule before the waves start.
- Do not run `build_missing_list.py`: it rewrites `missing_candidates.jsonl` and wipes its INSPIRE
  and screen fields.
- The laptop is the source of truth and this repo is public and mirrored anonymously: no names,
  emails, hostnames or home paths in committed files. Ask before committing or pushing from the
  server; new results normally go back to the laptop and are committed from there.
