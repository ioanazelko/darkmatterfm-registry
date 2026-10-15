# Model-card extraction for the missing papers (Claude workers)

The Claude version of the original Codex step that produced the registry's 6,145 cards: one pass in
which a worker reads each paper's full text and either writes 1–10 model-only cards or a rejected
status with a reason. It reuses the recovered Codex material in `registry/codex_prompts/`: the
output guide (acceptance rule, fields, files), the model-only profile, and the worker prompt, which
`worker_prompt_template.md` follows closely.

| File | What it does |
|---|---|
| `worker_prompt_template.md` | The worker prompt: the Codex worker prompt with paper text from `.tex` files instead of an SQLite database, the fixed row and provenance fields of this run, a validation step, and a one-line JSON reply |
| `stage_extraction.py` | Turns a list of arXiv ids into `runs/RUN/`: paper texts, batches of at most 5 papers and 350k characters (longer papers alone), one `assignment.json` and filled-in `prompt.md` per batch, `manifest.jsonl` |
| `run_batches.sh` | Runs `claude -p` headless on every batch that does not yet pass validation, N in parallel; logs token usage per attempt; stops when a usage limit is hit; rerun to resume. `--check` tests the CLI first |
| `validate_batch.py` | Checks a batch: files parse, every assigned paper exactly once, counts agree, ≤ 10 cards per paper, cards meet the profile and the current schemas. Workers run it before finishing |
| `make_waves.py` | Splits the fetch set into tiers from the Opus and Fable abstract screens (tier 1: both NOVEL_MODEL … tier 4: kept by one screen) |
| `score_extraction.py` | Decisions per run, agreement with Codex on calibration papers, acceptance by tier, measured tokens per paper and a projection |
| `merge_extraction.py` | Collects passing batches into registry-format `results/NAME_outputs.jsonl` and `_paper_status.jsonl` |
| `driver_util.py` | Log parsing for `run_batches.sh` |

What differs from the Codex run: the text is the arXiv e-print LaTeX from `../fetch_fulltext.py`
(overlong lines wrapped at spaces) rather than MINT; batches hold up to 5 papers rather than 10; the
validator also requires every card to pass the current registry schemas (true for about 97% of the
Codex cards); the worker's final reply is a single JSON line, with notes in `report.md`; and the
worker model is Claude Opus 5.5. `runs/` holds full texts and is not committed; merged results go in
`results/`.

## Runbook (on the server, from `missing_papers/extraction/`)

**Setup, once.**

```bash
cd <repo> && git pull --ff-only && .venv/bin/pip install jsonschema pyyaml referencing
cd missing_papers/extraction && bash run_batches.sh --check
```

`--check` confirms the validator's packages, the `claude` binary (set `CLAUDE_BIN=~/.local/bin/claude`
if it is not on PATH), and runs one tiny headless job (a few thousand tokens) that must run
`python3` and write a file under the workers' tool permissions. It saves the working settings in
`runs/.cli_config`; runs refuse to start without it. Workers get Read, Write, Edit, Glob, Grep and
Bash limited to `python3`, so no web access. They load the user-level `~/.claude/CLAUDE.md` if
there is one, so keep it free of instructions that would interfere.

**1. One batch, by hand.** Stage the 200 calibration papers (100 Codex-accepted, 100 Codex-rejected;
the same set as the earlier triage pilot) and run a single batch:

```bash
python3 stage_extraction.py pilot ../fulltext_triage/calib_pilot_ids.txt
bash run_batches.sh pilot --limit 1 --parallel 1
cat runs/pilot/logs/batch-0000.validation; tail -1 runs/pilot/usage.jsonl
```

Read `runs/pilot/batches/batch-0000/` (`outputs.jsonl`, `paper_status.jsonl`, `report.md`) and
check the cards make sense before spending more.

**2. Calibration pilot.** Run the remaining pilot batches and score them:

```bash
bash run_batches.sh pilot --parallel 4
python3 score_extraction.py pilot --project 9214
```

`runs/pilot/score.md` gives agreement with Codex, recall on Codex-accepted papers, the share of
Codex-rejected papers accepted, card counts, every disagreement with both reasons, and measured
tokens per paper projected to the full fetch set. For comparison, the reconstructed triage rule
(`../fulltext_triage/pilot/score_opus.md`) reached 79% agreement, 59% recall and 1% false
positives. See *Decision after the pilot* before going on.

**3. Waves, in priority order.**

```bash
python3 make_waves.py
python3 stage_extraction.py tier1 waves/tier1.txt
bash run_batches.sh tier1 --parallel 4
python3 score_extraction.py tier1 --tiers waves/candidates.tsv
```

Then `tier2`, `tier3`, `tier4` the same way. Tier sizes for the astro-ph / hep-ph list are 3,621,
906, 2,383 and 1,496; `make_waves.py` adds the hep-th / gr-qc papers and drops papers without
fetched text. Start long runs inside `screen` or `tmux`. Rerunning the same `run_batches.sh`
command resumes; batches that fail validation are retried up to 3 times. If `runs/RUN/STOP`
appears, a usage limit was hit: delete it after the limit resets and rerun. `--parallel` trades
speed against how fast the 5-hour usage window drains.

**4. Merge and send back.**

```bash
python3 merge_extraction.py tier1 tier2 tier3 tier4 --out results/missing_papers
```

The pilot is left out: its papers are already in the registry. Copy `results/` back to the laptop, the source of truth, to review and commit from there.

## Decision after the pilot

The guide accepts papers that "introduce, propose, construct, or substantially develop" a dark
matter model. Codex read "substantially develops" broadly, accepting many follow-up papers that work
out the phenomenology of an existing model. Claude reads it more strictly: under the reconstructed
rule it rejected 41 of 100 Codex-accepted papers. If the pilot with the original guide still shows
low recall against Codex, the choice is:

- keep Claude's stricter reading: cleaner cards, but the new papers follow a stricter standard than
  the existing 6,145; or
- add one clarifying sentence to `worker_prompt_template.md` (for example, that a paper which works
  out new phenomenology, parameter space or production for a specific model counts as substantially
  developing it), restage, and rerun the pilot.

Leave `registry/codex_prompts/` unchanged either way: it is the record of the Codex run.

Budget: reading all 9,214 fetched texts once is about 157M tokens. Real use per paper is several
times that, because each tool turn re-reads the cached context, and the pilot's `score.md` gives
the measured figure.
