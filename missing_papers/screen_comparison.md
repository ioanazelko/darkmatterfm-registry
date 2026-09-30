# Abstract screen: Sonnet 5 vs Opus 5.5

Batches compared: 192 of 192. Papers: 38,318 missing candidates + 1,920 hidden calibration papers.
Same batches, same prompt (`screen_prompt.md` / `screen_prompt_opus.md`, differing only in output folder).

## Decision counts (missing candidates)

| Decision | Sonnet 5 | Opus 5.5 |
|---|---|---|
| NOVEL_MODEL | 6,066 | 3,940 |
| UNSURE | 1,135 | 3,799 |
| NOT_NOVEL_MODEL | 31,117 | 30,579 |
| kept (NOVEL+UNSURE) | 7,201 | 7,739 |

## Agreement (missing candidates)

- Exact label agreement: 85.2% (Cohen's κ = 0.56)
- Keep/drop agreement: 89.3% (κ = 0.66)
- Kept by either model: 9,520; by both: 5,420

Rows: Sonnet 5; columns: Opus 5.5.

| Sonnet \ Opus | NOVEL | UNSURE | NOT |
|---|---|---|---|
| NOVEL | 3,382 | 1,433 | 1,251 |
| UNSURE | 124 | 481 | 530 |
| NOT | 434 | 1,885 | 28,798 |

## Calibration against Codex full-text triage (hidden papers)

| | Sonnet 5 | Opus 5.5 | Either (union) |
|---|---|---|---|
| Codex-accepted kept (recall), n=521 | 69.5% | 83.9% | 86.6% |
| Codex-rejected kept (false-positive rate), n=1,399 | 14.7% | 8.9% | 18.0% |

Codex-accepted papers, Sonnet × Opus (rows Sonnet, columns Opus):

| Sonnet \ Opus | NOVEL | UNSURE | NOT |
|---|---|---|---|
| NOVEL | 269 | 60 | 9 |
| UNSURE | 9 | 10 | 5 |
| NOT | 24 | 65 | 70 |

## Kept share by period

| Period | n | Sonnet kept | Opus kept |
|---|---|---|---|
| ≤2004 | 7,686 | 12.7% | 14.5% |
| 2005–2024-05 | 21,932 | 20.7% | 21.6% |
| after_cutoff | 8,700 | 19.5% | 21.7% |

## Review-cited gold papers on the missing list

1,434 gold papers screened. Kept by Sonnet: 329; by Opus: 376; by either: 423. (Gold papers include experiments and observations, so this is not a recall figure.)
