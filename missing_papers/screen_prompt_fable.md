# Abstract pre-screen of missing candidates (Claude agents) — Fable 5.1 rerun

Identical to `screen_prompt.md` except for the output directory (`screen_results_fable/`), so
the Fable 5.1 decisions can be compared with the Sonnet 5 (`screen_results/`) and Opus 5.5 (`screen_results_opus/`) runs.

## Task given to each agent

You screen arXiv papers for a dark-matter theory registry. Input file: one JSON object per
line, `{key, title, abstract}`. For **every** line, decide:

Question: does this paper introduce, propose, construct, or substantially develop a dark
matter model (a new particle/field candidate, a new production mechanism, a new dark sector,
a new interaction or cosmological behaviour of dark matter, or a substantive new variant of
an existing model)?

- `NOVEL_MODEL`: the answer is likely yes.
- `NOT_NOVEL_MODEL`: the paper only applies, constrains, observes, simulates, reviews,
  cites, forecasts, or compares existing dark-matter models, or is not about dark matter.
- `UNSURE`: unclear from the abstract.

The screen is recall-oriented. False positives are acceptable, because a later extractor
reads the full text of kept papers. False negatives are expensive. When in doubt, return
`UNSURE`.

Also give `model_class`: a 2–6 word label of the dark-matter model involved (e.g. "freeze-in
sterile neutrino", "self-interacting dark photon DM", "axion-like particle"), or `null` if
none.

Write one JSON object per input line, in input order, to the output file:
`{"key": "...", "decision": "NOVEL_MODEL|NOT_NOVEL_MODEL|UNSURE", "model_class": "..."|null}`.
Judge each paper independently and only from its title and abstract. Do not look anything up.

## Files and procedure (for batch NNN)

- Input: `missing_papers/screen_batches/batch_NNN.jsonl` (~210 lines)
- Output: `missing_papers/screen_results_fable/batch_NNN.jsonl` (one line per input line, same order)
- Full directory: `<registry-root>/missing_papers/`

Read the whole input file with the Read tool (it may take a couple of reads). Read every
abstract in full: do not print, truncate or summarise abstracts with a script. If the output
file already exists, overwrite it. Judge every
paper yourself from its title and abstract. Do NOT use keyword scripts or code heuristics to
make decisions, and do not look anything up online. Write the decisions to the output file,
in a few chunks if needed: append with a small Python heredoc that writes the JSON lines you
composed, or use the Write tool. Do NOT read or write anything in `screen_results/` or `screen_results_opus/` (the other
runs). Every input key must appear exactly once. When done, check with a one-line
Python script that the output has the same number of lines and the same set of keys as the
input. Reply with just the count of each decision and any problems.
