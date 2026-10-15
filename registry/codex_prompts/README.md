# Codex / GPT-5.5 worker prompts (Stage 2 extraction and Stage 5 enrichment)

The prompts given to the GPT-5.5 Codex workers that produced the registry's model cards and their
enrichment, recorded from the production runs (received 2026-10-10). The only change from the
originals is that absolute server paths are replaced by placeholders: `<project>` (repo root),
`<run-dir>` (one extraction run's directory) and `<enrichment-run-dir>`. Each batch file is the
instantiation for `batch-0000`; the orchestrator filled the assignment id, paper ids, shards and
paths for every other batch. The Gemini abstract gate that preceded the astro-ph run is in
`../gemini_screening_prompt.md`.

| File | Stage | What it is |
|---|---|---|
| `extraction_batch_astro-ph.md` | 2 | Orchestrator template plus the worker prompt for the astro-ph run (2026-05-28): papers that passed the lexical filter and the Gemini `NOVEL_MODEL` gate |
| `extraction_batch_hep-ph.md` | 2 | The same for the hep-ph run (2026-05-30, rolling batches): lexical filter, no Gemini gate |
| `extraction_output_guide.md` | 2 | `subagentoutputguide.md`, the authority every extraction worker read: acceptance rule, required `model_card` fields, provenance values, output files |
| `enrichment_worker.md` | 5 | Worker prompt for the second-pass enrichment of the top-ranked cards (observables, constraints, routes; ADS lookups; at most 3 related full texts per paper) |

How the extraction step worked, as these prompts show:

- **Accept/reject and card writing are one step.** A worker reads each assigned paper in full and
  either writes 1–10 model-card rows or a rejected status with a reason. There is no separate
  full-text triage.
- **Input:** full text from a run-local SQLite database (`papers` table, `full_text` column), about
  10 papers per worker; no external lookups (no ADS, arXiv, web, INSPIRE).
- **Scope:** model-only profile of `../schemas/bsm_model.schema.yaml`; `observables`, `constraints`
  and `theory_to_observable_routing` are excluded and filled later by enrichment.
- **Bias:** "prefer precision over recall" once a paper is in the target pool, rejecting
  lexical-filter or Gemini false positives.
- **Outputs per batch:** `outputs.jsonl` (one row per card), `paper_status.jsonl` (one row per
  paper), `run_summary.json`.

Not included, because they were not part of what was received: the run-local
`schema_profile_model_only.json` (the model-only field list is spelled out in
`extraction_output_guide.md`), and for enrichment `enrichment_output_schema.json`,
`production_web_fallback_policy.md` and `local_text_dbs.json`.

Note: the hep-ph worker prompt still says "a larger parallel run over astronomy papers"; it was
copied from the astro-ph template and left as it was run.
