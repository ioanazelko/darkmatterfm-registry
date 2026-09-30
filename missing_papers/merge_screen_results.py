"""Merge Claude abstract-screen decisions into missing_candidates.jsonl and score the calibration rows.

Reads screen_batches/keymap.jsonl and screen_results/batch_*.jsonl; adds `screen_decision` and
`screen_model_class` to each candidate (null where its batch has not been screened yet) and
writes screen_summary.md with decision counts and agreement with the registry's Codex triage
on the hidden calibration papers.
"""
import collections, glob, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
LABELS = ("NOVEL_MODEL", "UNSURE", "NOT_NOVEL_MODEL")


def main():
    keymap = {json.loads(l)["key"]: json.loads(l) for l in open(os.path.join(HERE, "screen_batches", "keymap.jsonl"))}
    dec, problems = {}, []
    for f in sorted(glob.glob(os.path.join(HERE, "screen_results", "batch_*.jsonl"))):
        b = os.path.basename(f)
        want = {json.loads(l)["key"] for l in open(os.path.join(HERE, "screen_batches", b))}
        got = []
        for l in open(f):
            if l.strip():
                try:
                    got.append(json.loads(l))
                except json.JSONDecodeError:
                    problems.append(f"{b}: unparsable line")
        keys = [g.get("key") for g in got]
        if set(keys) != want or len(keys) != len(want):
            problems.append(f"{b}: {len(set(keys) & want)}/{len(want)} keys, {len(keys)} lines")
        for g in got:
            if g.get("key") in want and g.get("decision") in LABELS:
                dec[g["key"]] = g
    by_id = {keymap[k]["arxiv_id"]: v for k, v in dec.items() if not keymap[k]["calibration"]}

    path = os.path.join(HERE, "missing_candidates.jsonl")
    rows = [json.loads(l) for l in open(path)]
    for r in rows:
        d = by_id.get(r["arxiv_id"])
        r["screen_decision"] = d["decision"] if d else None
        r["screen_model_class"] = d.get("model_class") if d else None
    with open(path, "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    screened = [r for r in rows if r["screen_decision"]]
    cnt = collections.Counter((r["screen_decision"], r["missing_reason"]) for r in screened)
    cal = collections.Counter((keymap[k]["calibration"], v["decision"]) for k, v in dec.items() if keymap[k]["calibration"])
    acc_n = sum(cal[("accepted", l)] for l in LABELS)
    rej_n = sum(cal[("rejected", l)] for l in LABELS)
    kept = lambda s: cal[(s, "NOVEL_MODEL")] + cal[(s, "UNSURE")]
    L = ["# Abstract pre-screen: summary", "",
         f"Screened {len(screened):,} of {len(rows):,} missing candidates "
         f"({len(glob.glob(os.path.join(HERE, 'screen_results', 'batch_*.jsonl')))} batches).", "",
         "| Decision | not_in_corpus | after_cutoff | total |", "|---|---|---|---|"]
    for l in LABELS:
        a, b = cnt[(l, "not_in_corpus")], cnt[(l, "after_cutoff")]
        L.append(f"| {l} | {a:,} | {b:,} | {a + b:,} |")
    L += ["", "## Calibration against the registry's Codex triage (hidden papers, full-text decisions)", "",
          "| Codex outcome | NOVEL_MODEL | UNSURE | NOT_NOVEL_MODEL | kept (NOVEL+UNSURE) |", "|---|---|---|---|---|"]
    for s, n in (("accepted", acc_n), ("rejected", rej_n)):
        L.append(f"| {s} ({n}) | " + " | ".join(str(cal[(s, l)]) for l in LABELS) + f" | {kept(s)/max(1, n):.1%} |")
    L += ["", f"Recall of the screen on Codex-accepted papers (kept = NOVEL_MODEL or UNSURE): "
          f"**{kept('accepted')/max(1, acc_n):.1%}**; share of Codex-rejected papers also kept: {kept('rejected')/max(1, rej_n):.1%}."]
    if problems:
        L += ["", "## Batch problems", ""] + [f"- {p}" for p in problems]
    open(os.path.join(HERE, "screen_summary.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
