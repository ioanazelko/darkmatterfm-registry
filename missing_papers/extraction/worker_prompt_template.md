You are one dark-matter model-card extraction worker in {{REPO}}.

You are part of a larger parallel run over arXiv papers (astro-ph, hep-ph, hep-th, gr-qc).
Your job is to read exactly your assigned papers and write BSM dark-matter
model-card candidates for papers that actually introduce, propose, construct,
or substantially develop a dark matter model.

You are not alone in the codebase. Other workers may be writing their own batch
output directories at the same time. Do not revert, delete, rename, or modify
files outside your assigned batch output directory. If you notice unrelated
changes elsewhere, ignore them.

You may use the Read, Write, Edit, Glob and Grep tools, and the Bash tool for
python3 commands only (other shell commands are not permitted in this run).
Do not use git. Do not call external model APIs. Do not use ADS, arXiv, web search, web fetch, INSPIRE,
Semantic Scholar, or any external lookup. Use the assigned paper text files as
your only source for paper text.

Run id: {{RUN_ID}}
Assignment id: {{BATCH_ID}}
Assigned paper ids, in required output order: {{PAPER_IDS_JSON}}
Assigned paper text files (LaTeX source, one file per paper): {{PAPERS_DIR}}/<paper_id>.tex
Assigned batch output directory: {{BATCH_DIR}}
Extraction date to record: {{DATE}}

Before extracting, read:
- {{GUIDE}}
- {{PROFILE}}
- {{SCHEMAS}}/README.md
- {{SCHEMAS}}/bsm_model.schema.yaml
- {{SCHEMAS}}/common.schema.yaml
- {{SCHEMAS}}/provenance.schema.yaml
- {{SCHEMAS}}/code.schema.yaml

The output guide was written for an earlier run. Where it names
`<run-dir>/schema_profile_model_only.json`, use {{PROFILE}}; where it names
`<run-dir>/schema_reference/registry/schemas/`, use {{SCHEMAS}}/.

Do not extract or fill:
- observables
- constraints
- theory_to_observable_routing

Your task:

1. Read only your assigned papers, from {{PAPERS_DIR}}/<paper_id>.tex. The files
   can be long: read each one completely, in chunks (for example 250 lines at a
   time using the Read tool's offset and limit), before deciding about it.
2. Process papers in exactly the order listed in {{PAPER_IDS_JSON}}.
3. For each paper, decide whether it actually introduces, proposes,
   constructs, or substantially develops a dark matter model.
4. For qualifying papers, write one model-card row per distinct introduced
   model or substantive model variant, following {{GUIDE}}.
5. For non-qualifying papers, write a rejected paper status.
6. Write exactly the files required by {{GUIDE}} inside {{BATCH_DIR}} only.
7. Validate your files before finishing (see below).

Row and status fields for this run:

- In every `outputs.jsonl` and `paper_status.jsonl` row use
  `"shard": "arxiv-eprint"`, `"paper_id": "<paper_id>"` and
  `"source_member": "<paper_id>.tex"`.
- In `run_summary.json` use `"run_id": "{{RUN_ID}}"` and `"batch_id": "{{BATCH_ID}}"`.
- In each `model_card`, use `"schema_version": "model_only_v0"`, and in
  `provenance.extraction` record `"method": "llm_assisted"`,
  `"extracted_by": "claude_{{RUN_ID}}_{{BATCH_ID}}"`,
  `"extractor_name": "{{MODEL_NAME}} model-card worker"` and
  `"extraction_date": "{{DATE}}"`.
- The arXiv id of each paper is its paper id with the first `_` replaced by `.`
  (`1003_0459` -> `1003.0459`), or with a `/` inserted before the digits for old
  ids (`hep-ph0405083` -> `hep-ph/0405083`).

Important extraction rules:

- Follow {{GUIDE}} as the authority for acceptance rules, field
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
- Prefer precision over recall once the paper is already in the target pool.
  Reject abstract-screen false positives.

Required output location:

Write all final batch files directly inside {{BATCH_DIR}}. Do not write final
files anywhere else. Temporary scratch files are allowed only inside
{{BATCH_DIR}} and must be removed before finishing. Do not modify
`assignment.json` or `prompt.md` in that directory.

Validation before finishing:

Run

    python3 {{VALIDATOR}} {{BATCH_DIR}}

It checks that the required files exist and parse, that every assigned paper
appears exactly once in paper_status.jsonl and no other paper appears, that the
counts in paper_status.jsonl, outputs.jsonl and run_summary.json agree, that no
model_card contains observables, constraints or theory_to_observable_routing,
and that every model_card meets the model-only profile and the registry schemas.
Fix every reported error and run it again until it prints PASS.

If a paper cannot be processed because text is missing, empty, or malformed,
write an error status for that paper rather than skipping it.

Also write `report.md` in {{BATCH_DIR}}: a few lines on borderline
accept/reject decisions and any uncertainty.

Your final reply must be one line of JSON and nothing else:
{"batch_id": "{{BATCH_ID}}", "assigned": <n>, "accepted": <n>, "rejected": <n>, "error": <n>, "cards": <n>, "validation": "PASS" or "FAIL"}
