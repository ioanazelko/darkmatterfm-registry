"""Detect abstract-screen decisions written against the wrong row.

Each decision carries a model_class. For every row with a class, compare the class words
with the title+abstract of its own paper and of its neighbours (offset -2..+2). A row
points at a neighbour when that neighbour matches clearly better (>= 50% of class words,
>= 34 points above the own-row match). Isolated hits are usually neighbouring papers on a
similar topic, so only runs of >= 3 consecutive checked rows pointing the same way count as
a shift. Every row inside a run's span (including rows with no class) is flagged.

Writes alignment_report.md and alignment_flags.json ({run: {key: offset}}).
"""
import glob, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
RUNS = (("Sonnet 5", "screen_results"), ("Opus 5.5", "screen_results_opus"), ("Fable 5.1", "screen_results_fable"))
STOP = {"dark", "matter", "model", "models", "with", "from", "that", "this", "particle", "particles", "field"}
MIN_RUN = 3


def words(s):
    return {w for w in re.findall(r"[a-z]{4,}", (s or "").lower()) if w not in STOP}


def sim(c, t):
    a = words(c)
    return len(a & words(t)) / len(a) if a else 0.0


def shifts(inp, res):
    txt = [x["title"] + " " + (x["abstract"] or "") for x in inp]
    best = []
    for i, r in enumerate(res):
        c = r.get("model_class")
        if not c or not words(c):
            best.append(None)
            continue
        sc = {k: sim(c, txt[i + k]) for k in range(-2, 3) if 0 <= i + k < len(txt)}
        k = max(sc, key=sc.get)
        best.append(k if sc[k] >= 0.5 and sc[k] > sc.get(0, 0) + 0.34 else 0)
    segs, run = [], []
    for i in [i for i, x in enumerate(best) if x is not None] + [None]:
        if i is not None and best[i] and (not run or best[i] == best[run[-1]]):
            run.append(i)
            continue
        if len(run) >= MIN_RUN:
            segs.append((run[0], run[-1], best[run[0]], len(run)))
        run = [i] if i is not None and best[i] else []
    return segs


def main():
    flags, L = {}, ["# Row-alignment check of the three abstract screens", "",
                    "A decision is shifted when it was written against a neighbouring paper. Detected from `model_class`:",
                    f"a run of ≥ {MIN_RUN} consecutive checked rows whose class matches the paper at the same offset (±1–2)",
                    "clearly better than their own. All rows inside a run's span are flagged (`check_alignment.py`).", "",
                    "| Run | Batch | Rows (0-based) | Offset | Rows pointing there |", "|---|---|---|---|---|"]
    for name, d in RUNS:
        flags[name] = {}
        for f in sorted(glob.glob(os.path.join(HERE, "screen_batches", "batch_*.jsonl"))):
            b = os.path.basename(f)
            inp = [json.loads(l) for l in open(f) if l.strip()]
            res = [json.loads(l) for l in open(os.path.join(HERE, d, b)) if l.strip()]
            for lo, hi, off, n in shifts(inp, res):
                L.append(f"| {name} | {b} | {lo}–{hi} | {off:+d} | {n} |")
                for i in range(lo, hi + 1):
                    flags[name][res[i]["key"]] = off
    L += ["", "| Run | Rows flagged |", "|---|---|"] + [f"| {n} | {len(v)} |" for n, v in flags.items()]
    open(os.path.join(HERE, "alignment_report.md"), "w").write("\n".join(L) + "\n")
    json.dump(flags, open(os.path.join(HERE, "alignment_flags.json"), "w"))
    print("\n".join(L))


if __name__ == "__main__":
    main()
