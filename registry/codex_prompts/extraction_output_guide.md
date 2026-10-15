# Dark-Matter Model Subagent Output Guide

## Goal

Read each assigned paper and output **BSM dark-matter model-card candidate
rows**.

A row means:

> This paper introduces, proposes, constructs, or substantially develops a dark
> matter model, and the row records a structured model-card candidate derived
> from that paper.

Do not create final registry entries.
Do not deduplicate models across papers.
Do not canonicalize model names using outside knowledge.
Do not use ADS, arXiv, web search, or external lookup.

This run intentionally ignores:

```text
observables
constraints
theory_to_observable_routing
```

Do not include those fields in any `model_card`.

---

# Files To Write

Each batch must write three files:

```text
outputs.jsonl
paper_status.jsonl
run_summary.json
```

`outputs.jsonl` contains one row per accepted paper-model-card pair.

Do not write more than 10 `outputs.jsonl` rows for any single paper.

`paper_status.jsonl` contains exactly one row per processed paper, with status
`accepted`, `rejected`, or `error`.

`run_summary.json` contains batch-level counts.

---

# Acceptance Rule

Accept a model only if all of the following are true:

1. The paper itself introduces, proposes, constructs, or substantially develops
   the dark matter model or a substantive model variant.
2. The model is a dark matter model, not merely a data analysis, observation,
   simulation, constraint, review, or comparison of existing models.
3. The paper text supports at least the core identity, theory/phenomenology,
   particle content or effective dark matter candidate, and production or relic
   density logic.
4. The paper text provides enough evidence to populate a provenance block.

Reject papers that only apply, constrain, simulate, compare, forecast, review,
or cite dark matter models without introducing a model or substantive variant.

Reject generic discussion of "a model" if the model is not a dark matter model.

If a paper introduces multiple distinct dark matter models or substantive model
variants, emit one row per model/variant, capped at 10 rows for the paper.

---

# Model-Card Scope

Each accepted row has a wrapper object and a `model_card` object. The
`model_card` follows the run-local model-only profile copied to:

```text
<run-dir>/schema_profile_model_only.json
```

The profile is derived from:

```text
<run-dir>/schema_reference/registry/schemas/bsm_model.schema.yaml
```

but excludes observables, constraints, and routes.

Use the upstream schemas for field meanings:

```text
<run-dir>/schema_reference/registry/schemas/bsm_model.schema.yaml
<run-dir>/schema_reference/registry/schemas/common.schema.yaml
<run-dir>/schema_reference/registry/schemas/provenance.schema.yaml
<run-dir>/schema_reference/registry/schemas/code.schema.yaml
```

Use `unknown`, `not_applicable`, `[]`, or `null` when a required field is not
supported by the paper. Do not invent unsupported specifics.

---

# Evidence And Provenance

Every accepted `model_card` must contain a `provenance` block.

Use the assigned paper as the `primary_papers` source. Fill arXiv id from
`paper_id` when obvious from the local id; otherwise use `null`.

Use:

```json
"status": "machine_extracted"
```

for `provenance.status`.

Use:

```json
"method": "llm_assisted"
```

for `provenance.extraction.method`.

Use:

```json
"human_reviewed": false,
"expert_reviewed": false
```

for `provenance.review`.

Evidence should be compact. Prefer short notes identifying what the paper says
and where. If you include source text, keep each `quote_or_summary` or evidence
note short. Do not paste long passages.

Evidence keys should correspond to extracted physics blocks, such as:

```text
particle_content
symmetries
interactions
production_mechanism
cosmological_history
parameter_ranges
validity_domain
```

Do not use evidence keys named `observable_signatures` or `constraints` in this
run.

---

# `outputs.jsonl`

Write one row per accepted paper-model-card pair.

Example shape:

```json
{
  "shard": "data/astro-ph-0005X.tar",
  "paper_id": "150X_XXXXX",
  "source_member": "150X_XXXXX.json",
  "model_card": {
    "schema_version": "model_only_v0",
    "model_id": "150x_xxxxx_hidden_sector_freeze_in_v1",
    "identity": {
      "name": "Hidden-sector freeze-in model",
      "family": "freeze_in_dark_matter",
      "aliases": [],
      "short_description": "A dark matter model introduced in the paper and populated only from the paper text.",
      "historical_origin_or_motivation": "unknown",
      "status": "speculative",
      "model_kind": "complete_theory"
    }
  }
}
```

The real `model_card` must include all top-level fields required by the
model-only profile, not just the abbreviated example above.

---

# Required `model_card` Top-Level Fields

Each `model_card` must include:

```text
schema_version
model_id
identity
theory
particle_content
symmetries
interactions
parameters
production
relic_density
cosmological_history
phase_space
structure_formation
validity_domain
assumptions
associated_code
provenance
robustness
agent_failure_modes
```

Optional model-only fields may be included when supported:

```text
operators
mass_scales_and_hierarchies
environment_dependence
degeneracies_and_confounders
computational_representation
model_comparison
benchmarks
```

Never include:

```text
observables
constraints
theory_to_observable_routing
```

---

# Model Id Rule

`model_id` must match:

```text
^[a-z0-9_-]+$
```

Use a stable paper-local id based on the paper id and model name, for example:

```text
0810_0713_exciting_dark_matter_v1
```

Do not use spaces, periods, slashes, colons, math notation, or uppercase.

---

# `paper_status.jsonl`

Write exactly one row per processed paper.

Accepted paper:

```json
{
  "shard": "data/astro-ph-0005X.tar",
  "paper_id": "1505_XXXXX",
  "source_member": "1505_XXXXX.json",
  "status": "accepted",
  "accepted_model_card_count": 2,
  "rejection_reason": null
}
```

Rejected paper:

```json
{
  "shard": "data/astro-ph-0005X.tar",
  "paper_id": "1505_XXXXX",
  "source_member": "1505_XXXXX.json",
  "status": "rejected",
  "accepted_model_card_count": 0,
  "rejection_reason": "No introduced dark matter model."
}
```

Error paper:

```json
{
  "shard": "data/astro-ph-0005X.tar",
  "paper_id": "1505_XXXXX",
  "source_member": "1505_XXXXX.json",
  "status": "error",
  "accepted_model_card_count": 0,
  "rejection_reason": "Text missing or malformed."
}
```

Allowed `status` values:

```text
accepted
rejected
error
```

`rejection_reason` is a short string. Use `null` when `status` is `accepted`.

---

# `run_summary.json`

Write one object per batch:

```json
{
  "run_id": "20260528T000000Z",
  "batch_id": "batch-005X",
  "input_paper_count": 10,
  "processed_paper_count": 10,
  "accepted_paper_count": 7,
  "rejected_paper_count": 3,
  "error_paper_count": 0,
  "accepted_model_card_count": 8
}
```

---

# JSONL Rules

Every line in every `.jsonl` file must be valid JSON.

Do not include Markdown in JSONL files.
Do not include comments.
Do not include trailing commas.
Use double quotes for strings.
Use `null` for missing optional values.
Use `[]` for empty lists.

---

# Final Checklist

Before outputting an accepted row, confirm:

```text
The paper introduces, proposes, constructs, or substantially develops the model.
The model is a dark matter model.
The model_card has all required model-only top-level fields.
The model_card has provenance and compact evidence.
The model_card omits observables, constraints, and routes.
The model_id is stable and valid.
The JSON is valid.
```
