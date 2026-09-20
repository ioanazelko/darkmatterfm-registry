# Gemini screening prompt (Stage 1 — astro-ph triage gate)

The prompt used to screen the astro-ph candidate papers before extraction,
recorded verbatim from the production run. The structured-output response schema
is in `gemini_screening_response_schema.json` next to this file; the
capability-gap annotation prompt is `capability_gap_prompt.md`.

- **Model:** `google/gemini-3.1-flash-lite`
- **Task:** recall-oriented three-way triage (`NOVEL_MODEL` / `NOT_NOVEL_MODEL` / `UNSURE`)
  deciding whether a paper goes on to the expensive GPT-5.5/Codex extractor.
- **Input:** the per-paper template carries `{paper.paper_id}` and `{text}` (the paper
  text; whether full text or truncated is **TO CONFIRM**). 501 M tokens over 36,919 papers
  ≈ 13.6 k tokens per paper, consistent with full or near-full text.
- **Output:** JSON constrained by the response schema in
  `gemini_screening_response_schema.json`: a single required `decision` field, enum
  `NOVEL_MODEL` / `NOT_NOVEL_MODEL` / `UNSURE`, no additional properties (so no
  rationale or confidence was returned — the decision label is the only output).
- **Open:** which labels counted as "passed" (3,458 papers) — presumably
  `NOVEL_MODEL` + `UNSURE`, given the recall-oriented design; run dates. The block
  starting "You are deciding…" is the system prompt; the `Paper id` / `Paper text`
  portion is the per-paper message.

## Prompt text (verbatim)

```text
You are deciding whether a paper should be sent to an expensive dark-matter theory-registry extractor.

Return NOVEL_MODEL if the paper appears to introduce, propose, construct, or substantially develop a dark matter model.

Return NOT_NOVEL_MODEL if the paper only applies, constrains, observes, simulates, reviews, cites, forecasts, or compares dark matter models without introducing a new model or substantive new model variant.

Return UNSURE if it is ambiguous whether the paper introduces a new model or substantive new model variant.

This is a recall-oriented triage classifier. False positives are acceptable because a later extractor will read kept papers. False negatives are expensive. When in doubt, return UNSURE.

Return only JSON matching the schema. The decision must be exactly NOVEL_MODEL, NOT_NOVEL_MODEL, or UNSURE.

Paper id: {paper.paper_id}

Classify this paper for dark-matter model triage.

Question: does this paper introduce, propose, construct, or substantially develop a dark matter model?

Return NOVEL_MODEL when the answer is likely yes.
Return NOT_NOVEL_MODEL when the paper only applies, constrains, observes, simulates, reviews, cites, forecasts, or compares existing dark matter models.
Return UNSURE whenever this is unclear.

Paper text:
{text}
```
