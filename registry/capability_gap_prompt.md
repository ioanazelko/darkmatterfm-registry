# Capability-gap enrichment prompt (build-log item #9, paper application A7)

Status: v1 draft, validated on a 20-card pilot (2026-09-02). Intended to run over
the enriched ~2k cards after pilot review.

## Task given to the model (per card)

You are annotating a structured dark-matter model card with **capability gaps**:
what is MISSING — theory, tools, simulations, emulators, likelihoods, or data —
to evaluate this model against observations. You receive the card's identity,
theory, microphysics, cosmology, structure-formation, observables, constraints,
computational_representation, associated_code, and theory_to_observable_routing
blocks.

Produce two things:

1. **Route-step status.** For every step in every route of
   `theory_to_observable_routing.routes[].forward_model_chain`, assign
   `status: available | partial | missing | unknown`:
   - `available` — a named public tool/code exists and covers this model's regime
     (`tool_or_code` non-null and adequate).
   - `partial` — a tool exists but needs modification, is calibrated outside this
     model's regime, is private, or covers only part of the parameter space.
   - `missing` — no tool exists; the step is currently done by hand, by rough
     analytic estimate, or not at all.
   - `unknown` — the card gives too little information to judge.
   Judge from the card content only; do not invent tools not implied by the card.

2. **The `capability_gaps` block** (see `schemas/bsm_model.schema.yaml`):
   for each genuine gap, an entry with:
   - `gap_type`: theory | derivation | tool | simulation | emulator | likelihood
     | data | calibration | other
   - `description`: what exactly is missing, specific to this model (not generic
     boilerplate — "no Boltzmann solver handles oscillatory kinetic decoupling
     with this model's dark-radiation coupling", not "needs more simulations").
   - `blocking_observables`: ids/channels from the card's `observables` that
     cannot be evaluated (or only degraded) until the gap closes.
   - `blocking_routes`: route or step ids whose status is missing/partial
     because of this gap.
   - `proposed_resolution`: a concrete, actionable approach — extend which
     existing tool, derive which quantity, run which class of simulation, with
     what parameterization. This answers "if there is a theory gap, how would
     you close it."
   - `estimated_effort`: small | medium | large | major_program | unknown
   - `severity`: blocks_all_observables | blocks_key_observables |
     degrades_precision | minor | unknown

## Rules

- 0 gaps is a valid answer (a well-served WIMP may have none); do not pad.
- Deduplicate: one gap entry per underlying missing capability, even if it
  blocks several routes.
- Never mark a step `missing` merely because `tool_or_code` is null — check
  whether the step is trivially analytic first (then it is `available`).
- Gaps must be evaluable capabilities, not open physics questions ("is the
  model true?" is not a gap; "no likelihood exists for its 21cm signature" is).
- Output must validate against the `capability_gaps` and route-step `status`
  schema definitions.

## Aggregation (after the full run)

Registry-wide roadmap: group gaps by (gap_type, normalized description),
weight each group by the summed adjusted_priority_score of the models it
blocks, and rank. Deliverable: "which capability, if built, unblocks the most
high-priority models" — overall and restricted to structure-formation
observables.
