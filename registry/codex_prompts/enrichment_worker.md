# Dark-Matter Model-Card Enrichment Production Worker

You are running a bounded second-pass enrichment over completed dark-matter model cards.

Write only inside your assigned output directory. Use `uv` for Python commands. Do not use git. Do not print or write the ADS key, bearer tokens, environment dumps, or full paper-text dumps.

ADS key lookup:
- Load `.env` from the repo root `<project>`.
- Prefer `ADS_API_KEY`; also accept `ADS_DEV_KEY`.

For each assigned paper:
1. Read the existing model-card row(s) from the assignment JSON. Each assignment row includes `model_id` copied from `model_card.model_id` and a `ranking` object copied from the global ranking run.
2. Resolve the primary paper text locally from the DBs in `<enrichment-run-dir>/input/local_text_dbs.json`.
3. Convert local `paper_id` to ADS/arXiv identifier this way:
   - Modern numeric ids: `1003_0459 -> 1003.0459`.
   - Old archive ids: `astro-ph0411262 -> astro-ph/0411262`.
4. Fill obvious observables from the primary paper first.
5. Use ADS for metadata discovery: primary record, references, and citations.
6. Normalize ADS arXiv IDs to local IDs by replacing `.` with `_`, stripping versions/prefixes, and for old ids also trying `astro-ph0411262` style local ids.
7. Search local DBs for related-paper full text.
8. If no useful related full text resolves locally, or fewer than the cap resolve locally, use the production web/arXiv fallback policy in `<enrichment-run-dir>/shared/production_web_fallback_policy.md`.
9. Read at most 3 related full texts per paper total, counting local plus web/arXiv reads.
10. Emit one `outputs.jsonl` row per assigned model card, even if observables/constraints/routes are empty.
11. Put unsupported or weak claims in `unresolved_items` or `report.md`; do not invent structured fields.

Per-paper discovery bounds:
- Save at most 10 ADS candidate records per paper.
- Read at most 3 related full texts per paper total.
- If ADS fails or rate limits, still produce primary-paper-only enrichment rows and mark paper status `partial` with notes.
- If a related paper cannot be read locally or through bounded web/arXiv fallback, log the failed attempt but do not use it for scientific claims.

Evidence rules:
- ADS metadata, web-search snippets, titles, and abstracts may be logged for triage, but must not support structured scientific claims by themselves.
- A web/arXiv related paper may support structured fields only when you read source text from an arXiv abstract/full-text/PDF page, publisher page, or another stable scholarly source.
- Every structured claim supported by a related paper must cite a source reference in `provenance_updates`.

Required files in your output directory:
- `outputs.jsonl`: one enrichment object per assigned model card. Each line must validate against `<enrichment-run-dir>/shared/enrichment_output_schema.json`.
- `paper_status.jsonl`: one status row per assigned paper.
- `run_summary.json`: batch accounting and timing.
- `ads_candidates.jsonl`: sanitized ADS shortlist rows, no secrets.
- `local_resolution.jsonl`: local arXiv ID resolution attempts, no full text dumps.
- `report.md`: concise notes on what happened.

Optional file when web/arXiv fallback is attempted:
- `web_resolution.jsonl`: sanitized fallback attempts, no secrets and no full text dumps.

`paper_status.jsonl` row shape:
```json
{"paper_id":"0000_00000","status":"completed","model_row_count":1,"output_row_count":1,"ads_reference_count":0,"ads_citation_count":0,"candidate_count":0,"related_texts_read":[],"notes":null}
```

`run_summary.json` required keys:
```json
{"pilot":"full","batch_id":"batch-0000","assigned_paper_count":5,"assigned_model_count":5,"processed_paper_count":5,"output_row_count":5,"status_counts":{"completed":5},"started_at":"ISO-8601","completed_at":"ISO-8601","elapsed_seconds":123.4}
```

The parent orchestrator will run validation after you finish. Before finalizing, do your own mechanical sanity check that JSONL parses, model/status counts match the assignment, links only reference IDs present in the same row, and no secret values were written.

If you cannot complete a paper, mark that paper `partial` or `error` in `paper_status.jsonl` and explain why in `notes` and `report.md`. Continue the rest of the batch.

## This Assignment

Pilot: `full`
Batch: `batch-0000`
Assignment JSON:

```text
<enrichment-run-dir>/full/assignments/batch-0000.json
```

Assigned paper IDs, ordered by global-rank priority:

```text
["1803_05650", "1912_05563", "2305_15736", "1911_04703", "1909_07706"]
```

ADS/arXiv IDs:

```text
{"1803_05650": "1803.05650", "1909_07706": "1909.07706", "1911_04703": "1911.04703", "1912_05563": "1912.05563", "2305_15736": "2305.15736"}
```

Best global rank by paper:

```text
{"1803_05650": 1, "1909_07706": 5, "1911_04703": 4, "1912_05563": 2, "2305_15736": 3}
```

Output directory:

```text
<enrichment-run-dir>/full/batches/batch-0000
```

Final response should include counts, status counts, whether you performed web/arXiv fallback, and exact files changed.
