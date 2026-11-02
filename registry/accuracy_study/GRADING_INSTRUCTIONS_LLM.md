# Extraction-accuracy grading — instructions for a grader agent

You grade machine-extracted "model cards" against the arXiv paper each card was
extracted from. You are a skeptical referee: the default is NOT "correct". Every
verdict must be backed by what the paper actually says.

## Inputs (per card)
- `packets/<NN>_<model_id>.card.yaml` — the card, split into `## SECTION: <name>` blocks.
  Grade EVERY section listed in its header line "Sections to grade".
- `packets/<NN>_<model_id>.json` — metadata incl. `paper_txt`, the path to the paper's
  full text (pdftotext output; may have layout noise, equations garbled — read around it).
  Two cards may share one paper; read the paper once.

## Procedure
1. Read the paper text fully (use Read with offset/limit if long; do not skim only the abstract).
2. For each section of the card, compare every substantive claim in the section to the paper.
3. Assign ONE verdict per section:
   - `correct` — every substantive claim in the section is supported by the paper
     (paraphrase and reasonable schema-level normalization are fine; generic
     boilerplate that is true of the model, e.g. "requires standard cosmology", counts as supported
     only if the paper assumes it explicitly or it is a plain, uncontroversial consequence).
   - `partially_correct` — the gist is right but at least one detail is wrong, missing,
     over-specific, or stated with a confidence the paper does not support.
   - `incorrect` — a central claim of the section contradicts the paper.
   - `hallucinated` — the section asserts specific content (numbers, particle names,
     mechanisms, constraints, code names, references) that has NO basis in the paper.
     Use this when the content is invented, not merely imprecise.
   - `cannot_judge` — the paper genuinely does not let you decide (e.g. the section is about
     tooling the paper never discusses and the card explicitly marks it unknown). Do NOT use this
     to avoid a hard call; if the card asserts something the paper is silent on, that is
     `hallucinated` (specific invented content) or `partially_correct` (mild over-reach).
4. For enriched cards, `observables`, `constraints`, `theory_to_observable_routing` and
   `agent_failure_modes` often contain generic domain knowledge beyond the paper. Grade them on:
   (a) do the observable/constraint entries that cite the paper match the paper's numbers, channels,
   and assumptions? (b) is anything attributed to the paper that is not there? Generic but
   physically sound routing/warnings not contradicted by the paper -> `partially_correct` if
   they are presented as paper-derived, `correct` if the card marks them as generic/inferred.
5. Write a short `note` for every verdict that is not `correct`: what is wrong, and a
   <=15-word quote or pointer (section/equation/table) from the paper as evidence.
   For `correct` verdicts on sections with numbers, note the paper location that confirms them.

## Output
Append ONE JSON line per card to the output file given in your task, with exactly this shape:
{"model_id": "...", "arxiv_id": "...", "stratum": "...", "enriched": true|false,
 "grader": "CLAUDE", "exported_at": "<ISO timestamp>",
 "sections": {"<section_name>": {"verdict": "<one of the five>", "note": "..."}, ...},
 "overall_note": "1-3 sentences: overall fidelity of this card; the worst problem found."}
Every section named in the card header MUST appear in `sections`. Do not add sections.
Do not modify any file outside your output file. Do not edit the packets or the paper text.
