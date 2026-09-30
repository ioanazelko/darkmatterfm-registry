# Abstract screen: Sonnet 5 vs Opus 5.5 vs Fable 5.1

Batches with all three runs: 192 of 192. Papers: 38,318 missing candidates + 1,920 hidden calibration papers. Same batches and prompt for all three.

## Decision counts (missing candidates)

| Decision | Sonnet 5 | Opus 5.5 | Fable 5.1 |
|---|---|---|---|
| NOVEL_MODEL | 6,066 | 3,940 | 4,234 |
| UNSURE | 1,135 | 3,799 | 3,339 |
| NOT_NOVEL_MODEL | 31,117 | 30,579 | 30,745 |
| kept (NOVEL+UNSURE) | 7,201 | 7,739 | 7,573 |

## Calibration against Codex full-text triage (hidden papers)

Recall = Codex-accepted papers kept; FP = Codex-rejected papers kept.

| Screen | Recall | FP rate | Missing candidates kept |
|---|---|---|---|
| Sonnet 5 | 69.5% | 14.7% | 7,201 |
| Opus 5.5 | 83.9% | 8.9% | 7,739 |
| Fable 5.1 | 80.0% | 7.5% | 7,573 |
| Sonnet 5 ∪ Opus 5.5 | 86.6% | 18.0% | 9,520 |
| Sonnet 5 ∪ Fable 5.1 | 83.3% | 16.7% | 9,282 |
| Opus 5.5 ∪ Fable 5.1 | 86.0% | 10.2% | 8,402 |
| any of the three | 87.7% | 18.2% | 9,908 |
| majority (≥2 of 3) | 80.4% | 8.5% | 7,388 |

(n = 521 accepted, 1399 rejected.)

## Pairwise agreement (missing candidates)

| Pair | Exact label | κ (3 labels) | Keep/drop | κ (keep/drop) |
|---|---|---|---|---|
| Sonnet 5 – Opus 5.5 | 85.2% | 0.56 | 89.3% | 0.66 |
| Sonnet 5 – Fable 5.1 | 86.4% | 0.58 | 90.1% | 0.68 |
| Opus 5.5 – Fable 5.1 | 93.7% | 0.82 | 96.1% | 0.88 |

## How many models keep each paper

| Kept by | Papers |
|---|---|
| 3 of 3 | 5,217 |
| 2 of 3 | 2,171 |
| 1 of 3 | 2,520 |
| 0 of 3 | 28,410 |

Kept by one model only: Sonnet 5 1,506, Opus 5.5 626, Fable 5.1 388.
