# Row-alignment check of the three abstract screens

A decision is shifted when it was written against a neighbouring paper. Detected from `model_class`:
a run of ≥ 3 consecutive checked rows whose class matches the paper at the same offset (±1–2)
clearly better than their own. All rows inside a run's span are flagged (`check_alignment.py`).

| Run | Batch | Rows (0-based) | Offset | Rows pointing there |
|---|---|---|---|---|
| Sonnet 5 | batch_121.jsonl | 129–143 | -2 | 13 |
| Sonnet 5 | batch_121.jsonl | 148–168 | -1 | 17 |
| Sonnet 5 | batch_121.jsonl | 170–177 | -1 | 8 |
| Sonnet 5 | batch_169.jsonl | 199–208 | -1 | 8 |
| Opus 5.5 | batch_064.jsonl | 167–173 | +1 | 5 |

| Run | Rows flagged |
|---|---|
| Sonnet 5 | 54 |
| Opus 5.5 | 7 |
| Fable 5.1 | 0 |
