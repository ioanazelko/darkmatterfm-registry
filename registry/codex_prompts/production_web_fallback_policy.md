# Production Web Fallback Policy

Use this policy in the production dark-matter enrichment worker prompt. It replaces the pilot-only rule that said not to use broad web search.

## Related-Paper Lookup Order

For each assigned primary paper:

1. Resolve and read the primary paper text locally from `input/local_text_dbs.json`.
2. Use ADS for metadata discovery: primary record, references, and citations.
3. Normalize ADS arXiv IDs to local IDs by replacing `.` with `_` and stripping versions/prefixes.
4. Search all configured local DBs for related-paper full text.
5. If no useful related full text resolves locally, or fewer than the per-paper cap resolve locally, use bounded web/arXiv fallback for the best missing ADS references/citations.

## Bounded Web/ArXiv Fallback

- Prefer arXiv full text or arXiv abstract pages over general web snippets.
- Search by normalized arXiv ID first. If no arXiv ID is available, search by exact title plus first author.
- Try missing ADS references/citations in relevance order until either:
  - 3 related full texts have been read for that primary paper, counting local plus web/arXiv reads, or
  - 3 web/arXiv lookup attempts have failed for that primary paper.
- If a paper has many citations, do not enumerate all of them. Keep the ADS shortlist capped at 10 candidate records per primary paper, then apply the web/arXiv fallback only to that shortlist.
- Web/arXiv fallback is required when the ADS shortlist has plausible related papers and none of them resolve locally. Do not stop at "no local related full text."

## Evidence Rules

- ADS metadata, web-search snippets, titles, and abstracts may be logged for triage, but must not support structured scientific claims by themselves.
- A web/arXiv related paper may support structured fields only when the worker reads source text from an arXiv abstract/full-text/PDF page, publisher page, or another stable scholarly source.
- Every structured claim supported by a web/arXiv related paper must include a source reference in `provenance_updates`.
- Put claims that remain metadata-only, snippet-only, or weakly supported in `unresolved_items` or `report.md`.

## Logging

Continue writing:

- `ads_candidates.jsonl`: sanitized ADS shortlist rows, no secrets.
- `local_resolution.jsonl`: local arXiv ID resolution attempts, no full text dumps.

For web/arXiv fallback, also write:

- `web_resolution.jsonl`: one sanitized row per web/arXiv attempt with `paper_id`, `candidate_arxiv_id`, `candidate_title`, `lookup_method`, `url`, `status`, and `notes`.

Do not print or write API keys or bearer tokens.
