# Extraction-accuracy study — results (LLM-graded pass, 2026-09-18/19)

**Grader:** Claude (Anthropic; Claude Code subagents, model claude-fable-5-1), 15 parallel graders of 5 cards each,
following `GRADING_INSTRUCTIONS_LLM.md`. Each grader read the full paper text (arXiv PDF → pdftotext) before
grading every non-empty section of the card and had to cite the paper location behind each non-`correct` verdict.
**This is not the expert-human grading the protocol calls for.** It is an LLM-judge pass; a human should re-grade
≥15 cards (`accuracy_grading.html`, Import → grade → Export) so `analyze_accuracy.py` can report Cohen's κ
between the human and this file. Until then the paper must describe these numbers as LLM-judged.

Grades: `accuracy_grades_CLAUDE.jsonl` (75/75 cards; every section listed by the grader UI has a verdict).
Reproduce the tables with `python scripts/analyze_accuracy.py registry/accuracy_study/accuracy_grades_CLAUDE.jsonl --latex`.

## Headline numbers

| | value |
|---|---|
| cards graded | 75 (50 enriched, 25 base; incl. 5 schema-invalid hard cases) |
| section verdicts | 1359 (1326 graded + 33 cannot_judge) |
| correct / partially correct / incorrect / hallucinated | 1080 / 243 / 3 / 0 |
| strict accuracy (correct ÷ graded) | 81.4% |
| half-credit accuracy | 90.6% |
| base cards strict / half-credit | 83.6% / 91.4% (n=385) |
| enriched cards strict / half-credit | 80.6% / 90.3% (n=941) |
| cards with every section `correct` | 3 |

Per-section table (strict, Wilson 95% CI): see `analyze_accuracy.py` output. Best sections: `assumptions` 100%,
`validity_domain` 96%, `agent_failure_modes` 93%, `identity` 92%. Weakest: `observables` 46%, `constraints` 50%,
`parameters` 59%, `interactions` 72%.

## What "hallucinated = 0" does and does not mean

Graders reserved `hallucinated` for content with no basis anywhere (invented numbers, particles, mechanisms,
code names). No section met that bar. However, the dominant defect in the enriched `observables`/`constraints`
sections is **real external literature content (later papers, generic likelihood inputs, other experiments)
presented as if derived from the source paper**; graders scored that `partially_correct` with the offending
reference in the note. A stricter reading could call some of those attributions hallucinated *provenance*.
Report both facts.

## Recurring failure modes (from grader notes)

1. **Provenance bleed in enriched sections** — `observables`/`constraints` attach references or numbers the
   source paper never cites (e.g. arXiv:1308.3021, 1312.1898, 2212.13272, 0906.2968, 1910.08422 attributions).
2. **Under-extraction** — values present in the paper left "unknown" or "not specified" (mixing angles, benchmark
   masses, R-parity, code names such as micrOMEGAs 3.2, Hazma, DarkSUSY, FeynHiggs, ISAJET, modified Gadget2).
3. **Formula/number transcription errors** — exponent signs and missing square roots
   (1.3e3 vs 1.3e-3; 10^16 vs 10^-16 M_sun; B/(A+B) vs sqrt; sqrt(2Gμ) lost by pdftotext), sometimes propagated
   through several sections of the same card.
4. **Symbol/label mismatches** — parameter renamed relative to the paper (λ vs α, ψ vs ξ, η vs ζ, α vs γ).
5. **`theory_level` misclassification** — full UV models filed as `simplified_model`, EFTs as `uv_complete`.
6. **Directional/status errors (rare, the only `incorrect` verdicts)** — "excluded" where the paper says
   "highly constrained"; "nonthermal" for a thermal freeze-out relic; lifetime-bound direction inverted.

## Lowest-scoring cards (strict fraction of graded sections)
- `1408_0233_nonabelian_triplet_collisional_xdm_v1` — 43% correct ({'correct': 6, 'cannot_judge': 2, 'partially_correct': 7, 'incorrect': 1})
- `2312_03837_u1x_dark_photon_subcomponent_v1` — 50% correct ({'correct': 9, 'partially_correct': 9, 'cannot_judge': 1})
- `1504_07970_susy_su2h_confinement_z2_r_parity_dm_v1` — 50% correct ({'partially_correct': 8, 'correct': 8, 'cannot_judge': 3})
- `2204_04672_majoraxion_case_a_v1` — 60% correct ({'partially_correct': 6, 'correct': 9, 'cannot_judge': 1})
- `2202_07784_dark_sector_scalar_eta_dm_v1` — 62% correct ({'partially_correct': 4, 'correct': 10, 'incorrect': 2})

## Caveats
- LLM grader; the same model family that did the extraction was not used, but LLM-vs-LLM agreement is not
  expert validation. Human κ study pending.
- Paper text came from pdftotext; graders were told to read around layout noise, but a few card errors trace
  to the *extraction-time* text having the same defects (e.g. lost radicals).
- Two duplicate-paper pairs in the sample (2008.02279, 1603.04723) were graded independently per card.
