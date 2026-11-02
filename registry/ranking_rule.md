---
description: First-pass global ranking rule for BSM dark-matter model cards before adding observational-detail extensions.
globs:
  - "registry/models/**/*.yaml"
  - "registry/models/**/*.yml"
  - "registry/model_cards/**/*.yaml"
  - "registry/model_cards/**/*.yml"
alwaysApply: false
---

# DarkMatterFM Rule: Global Observational-Extension Ranking

## Purpose

Use this rule to rank every non-eliminated BSM dark-matter model card by its expected value for observational-detail extension.

This rule is not a model-popularity ranking and not a judgment of which dark-matter model is most likely to be true. It is a reproducible prioritization ranking for observational follow-up.

The rule has two phases:

1. **Strict elimination gate:** reject globally eliminated models before any scoring.
2. **Global ranking:** score and rank all remaining models, with no hard cutoff and no `top_2000` flag.

A downstream workflow may later choose the first N models allowed by a labor or budget constraint, but that cutoff is not part of this rule and should not be stored as a property of the model.

## Inputs

Each candidate is a filled model card following `bsm_model.schema.yaml`. The rule uses, at minimum, these fields when present:

- `model_id`
- `identity.status`
- `identity.family`
- `identity.model_kind`
- `theory.theory_level`
- `particle_content.dark_matter_candidate.statistics`
- `particle_content.dark_matter_candidate.elementary_or_composite`
- `particle_content.dark_matter_candidate.number_of_components`
- `interactions.portals`
- `production`
- `relic_density.can_produce_all_dark_matter`
- `cosmological_history.bbn_relevance`
- `cosmological_history.cmb_relevance`
- `phase_space.distribution_type`
- `phase_space.distribution_function_available`
- `structure_formation.linear.transfer_function_shape`
- `structure_formation.linear.small_scale_power_effect`
- `structure_formation.linear.half_mode_mass`
- `structure_formation.nonlinear.halo_mass_function_effect`
- `structure_formation.nonlinear.subhalo_mass_function_effect`
- `structure_formation.nonlinear.simulation_calibrated`
- `environment_dependence`
- `observables`
- `constraints.applicable`
- `constraints.disputed_or_contextual`
- `validity_domain`
- `computational_representation`
- `associated_code`
- `theory_to_observable_routing.routes`
- `assumptions`
- `provenance`
- `model_comparison`
- `robustness`
- `benchmarks.points`
- `agent_failure_modes.warnings`

## Required output

For every model, emit a ranking record. The output should not include a field that marks the model as being inside or outside a fixed budget such as 2000 models.

```yaml
triage:
  ranking_state: rejected_eliminated | ranked | defer_manual_review
  observational_followup_allowed: boolean
  raw_priority_score: number | null
  adjusted_priority_score: number | null
  global_rank: integer | null
  rank_percentile: number | null
  family_rank: integer | null
  priority_tier: tier1 | tier2 | tier3 | defer | rejected
  rejection_reason:
    - string
  ranking_components:
    scientific_value: number
    observational_leverage: number
    complementarity: number
    feasibility: number
    provenance_and_robustness: number
    diversity_value: number
    penalties: number
  ranking_rationale:
    - string
  defer_reason:
    - string
```

Definitions:

- `raw_priority_score`: score from science, observational leverage, complementarity, feasibility, provenance, diversity value, and penalties.
- `adjusted_priority_score`: optional tie-broken or diversity-adjusted score used for final global ordering. If no adjustment is applied, set equal to `raw_priority_score`.
- `global_rank`: rank among all scored non-eliminated models. Rank 1 is highest priority.
- `rank_percentile`: percentile among all scored non-eliminated models, where 100 is highest priority.
- `family_rank`: rank within `identity.family`, if available.
- `priority_tier`: qualitative band derived from the score. This is not a selection flag.

## Step 0: Normalize values

Before triage, normalize enum-like string values to lowercase. Treat missing fields conservatively, but do not confuse missing information with elimination.

- Missing elimination fields should produce `defer_manual_review`, not `rejected_eliminated`.
- Unknown viability should not be treated as exclusion.
- A model is eliminated only if a global model-level status or compatibility field says it is excluded, or if the card explicitly states that the entire model class has no viable parameter space.

## Step 1: Strict elimination gate

Apply this gate before all scoring.

A model is rejected from observational follow-up if any of the following are true:

1. `identity.status == "excluded"`.
2. `model_comparison.compatibility_with_current_data == "excluded"`.
3. The model card contains an explicit global statement in `constraints.applicable`, `validity_domain`, `robustness`, or `agent_failure_modes.warnings` that the whole model class is ruled out and has no remaining viable parameter space.
4. The only physically meaningful parameter regimes listed in `benchmarks.points` are globally excluded and there is no surviving regime in `validity_domain`.

If the model is rejected at this gate, output:

```yaml
triage:
  ranking_state: rejected_eliminated
  observational_followup_allowed: false
  raw_priority_score: null
  adjusted_priority_score: null
  global_rank: null
  rank_percentile: null
  family_rank: null
  priority_tier: rejected
  rejection_reason:
    - "Model eliminated before observational-extension scoring."
```

Then stop. Do not compute science, observational, complementarity, feasibility, provenance, diversity, or penalty scores for this model. Do not rank it among observational-follow-up candidates.

### Important distinction

Do not reject merely because:

- `identity.status == "deprecated"`;
- `identity.status == "unknown"`;
- `model_comparison.compatibility_with_current_data == "unknown"`;
- some benchmark points are excluded but others are allowed, disputed, near-future-testable, stress-test, emulator-training, or likelihood-validation points;
- a specific constraint excludes part of parameter space;
- a model is underconstrained, speculative, incomplete, or missing some observational details.

Those models should still be scored, ranked, deferred, or manually reviewed.

## Step 2: Score every surviving model

For all models not rejected by Step 1, compute:

```text
S_total = S_science
        + S_observational
        + S_complementarity
        + S_feasibility
        + S_provenance
        + S_diversity
        - S_penalty
```

The maximum nominal score before penalties is 100.

## Step 2A: Scientific value score, max 20

Use `identity`, `theory`, `model_comparison`, and `relic_density`.

### Status score, max 5

```text
identity.status == canonical:   +5
identity.status == benchmark:   +5
identity.status == emerging:    +4
identity.status == speculative: +2
identity.status == deprecated:  +1
identity.status == unknown:     +0
```

### Theory level score, max 4

```text
theory.theory_level == uv_complete:                       +4
theory.theory_level == simplified_model:                  +3
theory.theory_level == effective_field_theory:            +2
theory.theory_level == phenomenological_parameterization: +1
theory.theory_level == benchmark_mapping:                 +2
theory.theory_level == unknown:                           +0
```

### Motivation and explanatory score, max 6

```text
model_comparison.theoretical_motivation == high:    +3
model_comparison.theoretical_motivation == medium:  +2
model_comparison.theoretical_motivation == low:     +0
model_comparison.theoretical_motivation == unknown: +0

model_comparison.explanatory_power nonempty:        +1 to +3
```

Award more explanatory points for models that connect dark matter to additional physics such as neutrino masses, baryogenesis, strong CP, hidden sectors, inflationary relics, Hubble/S8 tensions, phase transitions, or gravitational-wave signatures.

### Relic-density relevance, max 3

```text
relic_density.can_produce_all_dark_matter == yes:     +3
relic_density.can_produce_all_dark_matter == partial: +2
relic_density.can_produce_all_dark_matter == no:      +0
relic_density.can_produce_all_dark_matter == unknown: +0
```

### Compatibility bonus, max 2

```text
model_comparison.compatibility_with_current_data == allowed:           +2
model_comparison.compatibility_with_current_data == partially_allowed: +1
model_comparison.compatibility_with_current_data == disputed:          +1
model_comparison.compatibility_with_current_data == unknown:           +0
```

## Step 2B: Observational leverage score, max 30

Use `observables`, `constraints`, `cosmological_history`, `phase_space`, `structure_formation`, `environment_dependence`, and `model_comparison`.

### Observational distinctiveness, max 5

```text
model_comparison.observational_distinctiveness == high:    +5
model_comparison.observational_distinctiveness == medium:  +3
model_comparison.observational_distinctiveness == low:     +1
model_comparison.observational_distinctiveness == unknown: +0
```

### Near-term testability, max 5

```text
model_comparison.near_term_testability == high:    +5
model_comparison.near_term_testability == medium:  +3
model_comparison.near_term_testability == low:     +1
model_comparison.near_term_testability == unknown: +0
```

### Cosmological relevance, max 4

```text
cosmological_history.cmb_relevance == high:    +2
cosmological_history.cmb_relevance == medium:  +1
cosmological_history.bbn_relevance == high:    +2
cosmological_history.bbn_relevance == medium:  +1
```

### Structure-formation relevance, max 8

```text
structure_formation.linear.small_scale_power_effect in [suppression, enhancement, oscillations, mixed]: +3
structure_formation.linear.transfer_function_shape != cdm_like and != unknown:                         +2
structure_formation.linear.half_mode_mass not null:                                                     +1
structure_formation.nonlinear.halo_mass_function_effect informative/nonempty/not unknown:               +1
structure_formation.nonlinear.subhalo_mass_function_effect informative/nonempty/not unknown:            +1
```

### Phase-space relevance, max 3

```text
phase_space.distribution_type in [nonthermal, resonant, decay_produced, mixed_cold_warm, field_like]: +2
phase_space.distribution_function_available in [yes, approximate]:                                  +1
```

### Existing observable/constraint content, max 5

```text
observables nonempty:                         +1 to +3 depending on specificity
constraints.applicable nonempty:              +1
constraints.disputed_or_contextual nonempty:  +1
```

## Step 2C: Probe complementarity score, max 15

Use `observables`, `constraints`, and `theory_to_observable_routing.routes`.

Count distinct probe classes touched by the model. Examples of probe classes:

- CMB
- BBN
- Lyman-alpha forest
- galaxy satellites
- stellar streams
- strong gravitational lensing
- weak lensing / large-scale structure
- direct detection
- indirect detection
- collider / fixed-target / beam dump
- compact objects / microlensing / dynamics
- gravitational waves
- black-hole superradiance
- laboratory precision / clocks / fifth-force searches

Score:

```text
1 distinct probe class:   +2
2 distinct probe classes: +5
3 distinct probe classes: +8
4+ distinct probe classes:+10
```

Then add:

```text
model_comparison.complementarity_across_probes == high:    +5
model_comparison.complementarity_across_probes == medium:  +3
model_comparison.complementarity_across_probes == low:     +1
model_comparison.complementarity_across_probes == unknown: +0
```

Cap this section at 15.

## Step 2D: Feasibility score, max 15

Use `computational_representation`, `associated_code`, `theory_to_observable_routing.routes`, and `benchmarks`.

```text
computational_representation.analytic_formula_available == yes:          +2
computational_representation.analytic_formula_available == approximate:  +1
computational_representation.semi_analytic_model_available == yes:       +2
computational_representation.semi_analytic_model_available == partial:   +1
computational_representation.emulator_available == yes:                  +2
computational_representation.emulator_available == partial:              +1
computational_representation.likelihoods_available nonempty:             +3
computational_representation.public_codes nonempty:                      +2
computational_representation.recasting_pipeline_available == yes:         +2
computational_representation.recasting_pipeline_available == partial:     +1
theory_to_observable_routing.routes nonempty:                            +2
benchmarks.points nonempty:                                              +2
associated_code present and usable:                                      +1 to +2
```

Cap this section at 15.

## Step 2E: Provenance and robustness score, max 10

Use `provenance`, `validity_domain`, `assumptions`, `robustness`, and `agent_failure_modes`.

```text
provenance present with credible literature/source trace: +3
validity_domain nonempty:                                +2
assumptions.global nonempty:                             +1
assumptions.constraint_specific nonempty:                 +1
robustness present and informative:                       +2
agent_failure_modes.warnings present and actionable:      +1
```

This score measures whether an observational extension can be trusted and audited, not whether the model is true.

## Step 2F: Diversity value, max 10

Diversity is part of the global ranking, not a post-hoc selection flag.

Award diversity value when a model occupies underrepresented or phenomenologically distinct space in the registry. Use the whole scored population to estimate rarity and coverage.

A model can receive diversity value for being distinctive in any of the following:

- `identity.family`
- `identity.model_kind`
- `theory.theory_level`
- `particle_content.dark_matter_candidate.statistics`
- `particle_content.dark_matter_candidate.elementary_or_composite`
- `particle_content.dark_matter_candidate.number_of_components`
- `interactions.portals`
- `production` mechanisms
- `phase_space.distribution_type`
- `structure_formation.linear.transfer_function_shape`
- `structure_formation.linear.small_scale_power_effect`
- dominant observational probe class

Suggested scoring:

```text
rare model family or underrepresented family:                         +1 to +3
distinctive production mechanism relative to current registry:         +1 to +2
distinctive phase-space or transfer-function behavior:                 +1 to +2
distinctive dominant observational probe class:                        +1 to +2
non-duplicate representative of a sparse but viable model class:       +1
```

Cap this section at 10.

Do not use diversity to mark a model as selected or not selected. It only changes the model's position in the full global ranking.

## Step 2G: Penalties, max 20

Apply only to models that survive the strict elimination gate.

```text
identity.status == deprecated:                                                   -3
model_comparison.compatibility_with_current_data == unknown:                     -2
many required fields are unknown or empty:                                       -1 to -5
validity_domain empty:                                                           -3
assumptions.global empty:                                                        -2
theory_to_observable_routing.routes empty:                                       -4
observables empty:                                                               -4
constraints.applicable empty:                                                    -2
computational_representation mostly unknown and no associated_code/public_codes:  -3
agent_failure_modes include severe unmitigated warnings:                         -2 to -5
model is near-duplicate of a higher-ranked model:                                -1 to -6
```

Do not use these penalties to reject a model unless the strict elimination gate applies. Penalized models may still rank above others if they are scientifically valuable, observationally distinctive, or strategically important.

## Step 3: Assign priority tier to every scored model

After scoring surviving models:

```text
S_total >= 70:       tier1
50 <= S_total < 70:  tier2
30 <= S_total < 50:  tier3
S_total < 30:        defer
```

Interpretation:

- `tier1`: highest-value observational-extension candidates.
- `tier2`: strong observational-extension candidates.
- `tier3`: useful for breadth, benchmarks, edge cases, or less mature routes.
- `defer`: low current value for observational extension, but not globally eliminated.
- `rejected`: eliminated before scoring; no observational follow-up.

The tier is a qualitative ranking band, not a selection flag and not a fixed-size bucket.

## Step 4: Produce a complete global ranking

After every non-eliminated model is scored:

1. Sort all scored models by `adjusted_priority_score` descending.
2. Break ties using, in order:
   - higher `observational_leverage`;
   - higher `complementarity`;
   - higher `feasibility`;
   - higher `provenance_and_robustness`;
   - lower penalty magnitude;
   - stable lexical ordering by `model_id`.
3. Assign `global_rank` from 1 to N, where N is the number of scored non-eliminated models.
4. Assign `rank_percentile = 100 * (N - global_rank + 1) / N`.
5. Assign `family_rank` by sorting within each `identity.family` using the same ordering.

Eliminated models remain in the output artifact with `ranking_state: rejected_eliminated`, but they receive no score and no rank among observational-follow-up candidates.

## Step 5: Rationale format

For every ranked model, write a short rationale explaining the rank-relevant information.

Good rationale examples:

```text
High-ranked because it is an allowed benchmark model with distinctive small-scale-power suppression, available transfer-function routing, and complementary Lyman-alpha, satellite, and strong-lensing observables.
```

```text
Mid-ranked because it has interesting nonthermal phase-space structure and contextual constraints, but the observational routing and public likelihood support are incomplete.
```

```text
Low-ranked but not rejected because it is viable and distinct, but currently lacks a clear observable mapping, usable parameter benchmarks, and provenance-rich constraints.
```

Rejected rationale example:

```text
Rejected before scoring because the card marks the model as excluded by current data with no remaining viable parameter domain. Observational-detail extension is not allowed.
```

## Non-negotiable behavior

- Never score an eliminated model.
- Never rank an eliminated model among observational-follow-up candidates.
- Never use a fixed cutoff such as 2000 inside this rule.
- Never create `selected_for_top_2000`, `inside_2000`, `covered_in_first_pass`, or equivalent fields.
- Never use popularity alone as a ranking criterion.
- Never let missing information count as exclusion unless the card explicitly states global elimination.
- Always rank every non-eliminated model globally.
- Always keep `raw_priority_score`, `adjusted_priority_score`, `global_rank`, and `family_rank` separate.
- Always preserve the reason for rejection or ranking in a machine-readable form.

## Optional downstream use outside this rule

A downstream workflow may decide to extend only the first N models due to labor or time constraints. That workflow may use `global_rank`, `priority_tier`, and `family_rank`, but it must not modify the ranking rule or write the budget cutoff into the ranking record.

For example, a separate workflow may say: "extend observational details for the highest-ranked N currently feasible models." That is a scheduling decision, not a ranking decision.
