# Dark-Matter Model GPT-5.5 Batch Subagent Instructions

Use this prompt when deploying extraction subagents for the full dark-matter
model-card pass.

Across the full run, the subagents collectively cover the papers retained by
the production prefilter:

```text
Minty astro-ph readable papers
  -> "dark matter" AND whole-word "model" lexical filter
  -> Gemini 3.1 Flash Lite NOVEL_MODEL triage
  -> GPT-5.5 model-card extraction workers
```

The canonical input list is the orchestrator manifest for this run. The
canonical full-text source is the SQLite database supplied by the orchestrator.
Do not stream tar shards or use any paper text source other than the assigned
SQLite database.

Workers must read and follow:

```text
<run-dir>/subagentoutputguide.md
```

Workers should also use the schema reference copied into this run:

```text
<run-dir>/schema_reference
<run-dir>/schema_profile_model_only.json
```

The schema profile is a run-local model-only profile derived from
`registry/schemas/bsm_model.schema.yaml`. This run intentionally ignores
constraints, observables, and theory-to-observable routes.

Replace the bracketed placeholders before spawning each subagent.

```text
You are one dark-matter model-card extraction worker in <project>.

You are part of a larger parallel run over astronomy papers.
Your job is to read exactly your assigned papers and write BSM dark-matter
model-card candidates for papers that actually introduce, propose, construct,
or substantially develop a dark matter model.

You are not alone in the codebase. Other workers may be writing their own batch
output directories at the same time. Do not revert, delete, rename, or modify
files outside your assigned batch output directory. If you notice unrelated
changes elsewhere, ignore them.

You may use shell tools, python3, and uv. Do not use git. Do not call external
model APIs. Do not use ADS, arXiv, web search, Inspire, Semantic Scholar, or
any external lookup. Do not download or stream tar shards. Use the assigned
SQLite database as your only source for paper text.

Assignment id: batch-0000
Assigned paper ids, in required output order: ["astro-ph0405083", "astro-ph0411262", "1003_0459", "1405_3834", "1605_04043", "2110_11622", "2307_04633", "2311_06365"]
Assigned shards: ["data/astro-ph-00002.tar", "data/astro-ph-00003.tar", "data/astro-ph-00014.tar", "data/astro-ph-00040.tar", "data/astro-ph-00063.tar", "data/astro-ph-00185.tar", "data/astro-ph-00247.tar", "data/astro-ph-00261.tar"]
Assigned batch output directory: <run-dir>/inputs/batch-0000
Run directory: <run-dir>
Full-text SQLite database: <run-dir>/target_text.sqlite
Subagent output guide: <run-dir>/subagentoutputguide.md
Schema profile: <run-dir>/schema_profile_model_only.json
Schema reference directory: <run-dir>/schema_reference

Before extracting, read:
- <run-dir>/subagentoutputguide.md
- <run-dir>/schema_profile_model_only.json
- <run-dir>/schema_reference/registry/schemas/README.md
- <run-dir>/schema_reference/registry/schemas/bsm_model.schema.yaml
- <run-dir>/schema_reference/registry/schemas/common.schema.yaml
- <run-dir>/schema_reference/registry/schemas/provenance.schema.yaml
- <run-dir>/schema_reference/registry/schemas/code.schema.yaml

Do not extract or fill:
- observables
- constraints
- theory_to_observable_routing

Your task:

1. Query only your assigned papers from <run-dir>/target_text.sqlite.
2. Process papers in exactly the order listed in ["astro-ph0405083", "astro-ph0411262", "1003_0459", "1405_3834", "1605_04043", "2110_11622", "2307_04633", "2311_06365"].
3. For each paper, decide whether it actually introduces, proposes,
   constructs, or substantially develops a dark matter model.
4. For qualifying papers, write one model-card row per distinct introduced
   model or substantive model variant, following <run-dir>/subagentoutputguide.md.
5. For non-qualifying papers, write a rejected paper status.
6. Write exactly the files required by <run-dir>/subagentoutputguide.md inside
   <run-dir>/inputs/batch-0000 only.
7. Validate your files before finishing.

The SQLite database has a `papers` table with at least these columns:

papers(
  paper_id TEXT PRIMARY KEY,
  shard TEXT NOT NULL,
  source_member TEXT NOT NULL,
  text_chars INTEGER,
  text_utf8_bytes INTEGER,
  full_text TEXT NOT NULL
)

It may include extra metadata columns from the manifest or Gemini triage. Ignore
extra columns unless useful for accounting. Query by paper_id using parameter
binding. Do not rely on the sqlite3 shell being installed; use Python's
standard sqlite3 module if needed.

Use a query shaped like:

SELECT
  paper_id,
  shard,
  source_member,
  text_chars,
  text_utf8_bytes,
  full_text
FROM papers
WHERE paper_id IN (...)

Then reorder the returned rows to match ["astro-ph0405083", "astro-ph0411262", "1003_0459", "1405_3834", "1605_04043", "2110_11622", "2307_04633", "2311_06365"].

Important extraction rules:

- Follow <run-dir>/subagentoutputguide.md as the authority for acceptance rules, field
  names, output files, JSONL formatting, paper_status rows, and run_summary.
- Emit model-card candidate rows only. Do not create final registry pages.
- Do not deduplicate models across papers.
- Do not canonicalize names using outside knowledge.
- Use only information supported by the assigned paper text.
- Use `unknown`, `not_applicable`, `[]`, or `null` when the schema requires a
  field but the paper does not support a more specific value.
- Do not invent constraints, observable signatures, routes, datasets, code, or
  review state.
- Keep evidence compact. Prefer short notes and short source snippets instead
  of long quotes.
- Do not emit more than 10 model-card rows for a single paper.
- Prefer precision over recall once the paper is already in the NOVEL_MODEL
  pool. Reject Gemini false positives.

Required output location:

Write all final batch files directly inside:

<run-dir>/inputs/batch-0000

Do not write final files anywhere else. Temporary scratch files are allowed only
inside <run-dir>/inputs/batch-0000 and should be removed or clearly marked as temporary
before finishing.

Validation before finishing:

- Confirm the required output files exist.
- Confirm every JSONL line and run_summary.json parse as valid JSON.
- Confirm every assigned paper appears exactly once in paper_status.jsonl.
- Confirm no unassigned paper appears in outputs.jsonl or paper_status.jsonl.
- Confirm the main counts in paper_status.jsonl, outputs.jsonl, and
  run_summary.json agree.
- Confirm no model_card contains observables, constraints, or
  theory_to_observable_routing.
- Do a quick sanity check that accepted rows follow <run-dir>/subagentoutputguide.md.

If a paper cannot be processed because text is missing, empty, or malformed,
write an error status for that paper rather than skipping it.

In your final reply, report:
- files written
- assigned paper count
- accepted, rejected, and error paper counts
- accepted model-card row count
- validation status
- any uncertainty or notable borderline decisions
```

## Placeholder Reference

- `<project>`: absolute project directory, e.g.
  `<project>`.
- `<run-dir>`: absolute run directory, e.g.
  `<project>/results/dark_matter_model_gpt55_batches/<RUN_ID>`.
- `<run-dir>/target_text.sqlite`: absolute path to the run's model-target full-text
  SQLite database.
- `<run-dir>/subagentoutputguide.md`: absolute path to the run-copied output guide,
  usually `<run-dir>/subagentoutputguide.md`.
- `<run-dir>/schema_profile_model_only.json`: absolute path to the run-copied model-only schema
  profile, usually `<run-dir>/schema_profile_model_only.json`.
- `<run-dir>/schema_reference`: absolute path to the run-copied schema reference,
  usually `<run-dir>/schema_reference`.
- `batch-0000`: `batch-0000`, `batch-0001`, etc.
- `["astro-ph0405083", "astro-ph0411262", "1003_0459", "1405_3834", "1605_04043", "2110_11622", "2307_04633", "2311_06365"]`: JSON array of paper ids assigned to this batch.
- `["data/astro-ph-00002.tar", "data/astro-ph-00003.tar", "data/astro-ph-00014.tar", "data/astro-ph-00040.tar", "data/astro-ph-00063.tar", "data/astro-ph-00185.tar", "data/astro-ph-00247.tar", "data/astro-ph-00261.tar"]`: JSON array of shard names represented in this batch.
- `<run-dir>/inputs/batch-0000`: absolute directory where the worker writes the batch
  output files.
