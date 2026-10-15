# Codex / GPT-5.5 worker prompts and schemas (Stage 2 extraction and Stage 5 enrichment)

The prompts and run-local schemas given to the GPT-5.5 Codex workers that produced the registry's
model cards and their enrichment, recorded from the production runs (prompts received 2026-10-10,
schemas and policy 2026-10-15). The only changes from the originals are placeholders for
identifying strings: absolute server paths become `<project>` (repo root), `<run-dir>` (one
extraction run's directory) and `<enrichment-run-dir>`; the profile's `source_schema_repo` owner
becomes `<owner>`; and the output schema's `$id` host becomes `project.local`. Each batch file is the
instantiation for `batch-0000`; the orchestrator filled the assignment id, paper ids, shards and
paths for every other batch. The Gemini abstract gate that preceded the astro-ph run is in
`../gemini_screening_prompt.md`.

| File | Stage | What it is |
|---|---|---|
| `extraction_batch_astro-ph.md` | 2 | Orchestrator template plus the worker prompt for the astro-ph run (2026-05-28): papers that passed the lexical filter and the Gemini `NOVEL_MODEL` gate |
| `extraction_batch_hep-ph.md` | 2 | The same for the hep-ph run (2026-05-30, rolling batches): lexical filter, no Gemini gate |
| `extraction_output_guide.md` | 2 | `subagentoutputguide.md`, the authority every extraction worker read: acceptance rule, required `model_card` fields, provenance values, output files |
| `schema_profile_model_only.json` | 2 | The run-local model-only profile the extraction workers read: required and optional top-level fields, required nested fields, enum overrides, and the three excluded fields |
| `enrichment_worker.md` | 5 | Worker prompt for the second-pass enrichment of the top-ranked cards (observables, constraints, routes; ADS lookups; at most 3 related full texts per paper) |
| `enrichment_output_schema.json` | 5 | JSON Schema (draft 2020-12) for each enrichment output row, version `dm_model_ocr_enrichment_smoke_v0` |
| `production_web_fallback_policy.md` | 5 | How enrichment finds related papers (ADS references and citations, local full text first, then a bounded web/arXiv fallback) and which sources may support structured claims |

How the extraction step worked, as these prompts show:

- **Accept/reject and card writing are one step.** A worker reads each assigned paper in full and
  either writes 1–10 model-card rows or a rejected status with a reason. There is no separate
  full-text triage.
- **Input:** full text from a run-local SQLite database (`papers` table, `full_text` column), about
  10 papers per worker; no external lookups (no ADS, arXiv, web, INSPIRE).
- **Scope:** the model-only profile `schema_profile_model_only.json`, derived from
  `../schemas/bsm_model.schema.yaml`; `observables`, `constraints`
  and `theory_to_observable_routing` are excluded and filled later by enrichment.
- **Bias:** "prefer precision over recall" once a paper is in the target pool, rejecting
  lexical-filter or Gemini false positives.
- **Outputs per batch:** `outputs.jsonl` (one row per card), `paper_status.jsonl` (one row per
  paper), `run_summary.json`.

Checks against the registry data (2026-10-15):

- All 2,004 enrichment output rows (the observables, constraints and routes merged into the
  top-ranked cards) validate against `enrichment_output_schema.json`.
- All 6,145 cards as extracted, before enrichment, have every required top-level and nested field
  in `schema_profile_model_only.json`, none of the three excluded fields, and only
  enum values the profile allows. Ten cards carry an extra top-level `reference_id`.
- The profile was derived from `registry/schemas/` at commit `7c53379` of this repository
  (2026-05-27; the repository was then named `darkmatterfm-theory-registry`). The schemas were
  revised once since then, in `7b952a0` (2026-09-18). That revision quoted `'yes'` / `'no'`, which
  YAML had read as booleans, and widened several enums to values the cards use. It also made some
  `notes` fields nullable, flattened `constraints` into a list, and added a `relations` block for
  use after deduplication.

Not included: `local_text_dbs.json` (the enrichment run's list of local full-text databases,
specific to the original server).

Note: the hep-ph worker prompt still says "a larger parallel run over astronomy papers"; it was
copied from the astro-ph template and left as it was run.
