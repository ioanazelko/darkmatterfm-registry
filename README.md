# darkmatterfm-theory-registry

Schemas, viewers and roadmap products of **DarkMatterFM-Registry**, a
machine-readable registry of beyond-the-Standard-Model dark-matter models
extracted from the arXiv literature with a staged large-language-model
pipeline. Every model is a structured *model card* that records not only
what the model is, but which observables and constraints apply, which
computational routes evaluate it, what is *missing* to evaluate it, and
where automated reasoning about it is most likely to go wrong.

This repository holds the parts of the project that are small enough for
Git: the schema suite, a browser for it, the capability-gap roadmap, the
derived research-project ranking, and the scripts that build them. The
full card release (thousands of cards, ~100 MB) is distributed separately.

## Contents

| Path | What it is |
|---|---|
| `registry/schemas/*.schema.yaml` | The seven JSON Schema (draft 2020-12, YAML source) files that every card is validated against: `bsm_model` (the card, 31 top-level sections), `common`, `observable`, `constraint`, `route`, `provenance`, `code`. See `registry/schemas/README.md`. |
| `registry/schema_browser.html` | **Start here.** A self-contained, dependency-free browser for the whole schema suite: every section and field with its description, type, enum values, examples and required flag, `$ref` links resolved across files, and a stable anchor per node for deep links (e.g. `schema_browser.html#bsm_model/agent_failure_modes`, `#bsm_model/capability_gaps`, `#route/defs/route`). Download the file and open it in any browser. Built by `registry/build_schema_browser.py`. |
| `registry/capability_gap_prompt.md` | The specification given to the annotation agents for the capability-gap pass: how each route step is judged available / partial / missing / unknown, and how gap entries are typed, graded and resolved. |
| `registry/models/capability_gaps_full.jsonl` | Per-card capability-gap annotations for the 2,004 enriched cards (5,166 gap entries), schema-valid against the `capability_gaps` block of `bsm_model`. |
| `registry/models/ranking_full_ranked.jsonl` | The follow-up-value priority ranking of every card; supplies the weights used to aggregate gaps. |
| `registry/models/capability_gap_roadmap.jsonl` | Gaps grouped into 150 (gap type, capability theme) groups, each weighted by the summed priority of the models it blocks. Built by `registry/build_gap_roadmap.py`. |
| `capability_gap_roadmap_report.md`, `registry/gap_roadmap.html` | Human-readable and browsable versions of the roadmap (the HTML lists every member model per group). |
| `registry/models/research_projects_ranked.jsonl` | 25 concrete research projects, one per capability theme, scored by impact, structure-formation impact, cost and value ratio. Built by `registry/build_research_project_ranking.py`. |
| `research_project_ranking.md`, `registry/darkmatterfm_research_roadmap.html` | The project ranking in three orderings (impact, value ratio, structure-formation impact) with per-project descriptions and the highest-priority blocked models; and a browsable version. |
| `scripts/validate_schema.py` | Validates a card (YAML or JSON) against the schema suite. `pip install jsonschema pyyaml referencing`. |

## Reproducing the products

```bash
pip install pyyaml jsonschema referencing
python3 registry/build_schema_browser.py            # -> registry/schema_browser.html
python3 registry/build_research_project_ranking.py  # -> registry/models/research_projects_ranked.jsonl, research_project_ranking.md
python3 registry/build_gap_roadmap.py               # -> registry/models/capability_gap_roadmap.jsonl, gap_roadmap.html, report
```

The schema browser and the project ranking rebuild from files in this
repository alone (the ranking reads `capability_gap_roadmap.jsonl`). The
roadmap builder reads `capability_gaps_full.jsonl` and
`ranking_full_ranked.jsonl` (both included) **plus** the 2,004 enriched
model cards themselves, for model names, families and observable channels;
those cards belong to the full data release and are not in this repository,
so that script is included for inspection of the aggregation rule and its
outputs are committed. The per-card gap annotation step calls an LLM and is
not re-run by any script here; its outputs are `capability_gaps_full.jsonl`.

## Scoring, in one paragraph

Each gap entry names the missing capability (tool, likelihood, derivation,
simulation, theory, data, calibration or emulator), what it blocks and how
badly (`blocks_all_observables`, `blocks_key_observables`,
`degrades_precision`, `minor`), the effort to close it, and a concrete
proposed resolution. Gaps are grouped by normalized theme; a group's weight
is the sum over the distinct models it blocks of each model's
`adjusted_priority_score` times a severity weight (1.0 / 0.8 / 0.4 / 0.1).
A research project is one theme phrased as a deliverable; its *impact* is
that weight, its *cost* the mean effort of its member gaps, and its *value
ratio* impact divided by cost. A structure-formation view counts only gaps
that block structure-formation observables.

## Scope and provenance

Card content is machine-extracted from paper full texts and is not yet
expert-verified; provenance and review-status fields in the schema record
this per claim. The documents `BSM Dark-Matter Theory Registry: Model
Aspects.md` and `Table Relating Concepts to Schema Modules.md` describe the
conceptual scope that the schema modules implement.
