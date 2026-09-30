"""Compare the Sonnet 5, Opus 5.5 and Fable 5.1 abstract screens (screen_results{,_opus,_fable}/).

Only papers screened by all three runs are compared. Writes screen_comparison_3way.md.
Does not modify missing_candidates.jsonl.
"""
import collections, itertools, os

from compare_screens import HERE, LABELS, KEPT, load, kappa
import json

RUNS = (("Sonnet 5", "screen_results"), ("Opus 5.5", "screen_results_opus"), ("Fable 5.1", "screen_results_fable"))


def flat(d):
    return {k: v["decision"] for rows in load(d).values() for k, v in rows.items()}


def main():
    keymap = {json.loads(l)["key"]: json.loads(l) for l in open(os.path.join(HERE, "screen_batches", "keymap.jsonl"))}
    D = {name: flat(d) for name, d in RUNS}
    names = [n for n, _ in RUNS]
    keys = sorted(set.intersection(*(set(D[n]) for n in names)))
    real = [k for k in keys if not keymap[k]["calibration"]]
    cal = [k for k in keys if keymap[k]["calibration"]]
    kept = lambda n, k: D[n][k] in KEPT
    n_batches = len({keymap[k]["batch"] for k in keys})

    L = ["# Abstract screen: Sonnet 5 vs Opus 5.5 vs Fable 5.1", "",
         f"Batches with all three runs: {n_batches} of 192. Papers: {len(real):,} missing candidates + "
         f"{len(cal):,} hidden calibration papers. Same batches and prompt for all three.", "",
         "## Decision counts (missing candidates)", "",
         "| Decision | " + " | ".join(names) + " |", "|---|" + "---|" * len(names)]
    for l in LABELS:
        L.append(f"| {l} | " + " | ".join(f"{sum(D[n][k] == l for k in real):,}" for n in names) + " |")
    L.append("| kept (NOVEL+UNSURE) | " + " | ".join(f"{sum(kept(n, k) for k in real):,}" for n in names) + " |")

    L += ["", "## Calibration against Codex full-text triage (hidden papers)", "",
          "Recall = Codex-accepted papers kept; FP = Codex-rejected papers kept.", "",
          "| Screen | Recall | FP rate | Missing candidates kept |", "|---|---|---|---|"]
    acc = [k for k in cal if keymap[k]["calibration"] == "accepted"]
    rej = [k for k in cal if keymap[k]["calibration"] == "rejected"]
    combos = [(n, lambda k, n=n: kept(n, k)) for n in names]
    for a, b in itertools.combinations(names, 2):
        combos.append((f"{a} ∪ {b}", lambda k, a=a, b=b: kept(a, k) or kept(b, k)))
    combos.append(("any of the three", lambda k: any(kept(n, k) for n in names)))
    combos.append(("majority (≥2 of 3)", lambda k: sum(kept(n, k) for n in names) >= 2))
    for label, f in combos:
        r = sum(map(f, acc)) / len(acc) if acc else float("nan")
        p = sum(map(f, rej)) / len(rej) if rej else float("nan")
        L.append(f"| {label} | {r:.1%} | {p:.1%} | {sum(map(f, real)):,} |")
    L.append(f"\n(n = {len(acc)} accepted, {len(rej)} rejected.)")

    L += ["", "## Pairwise agreement (missing candidates)", "",
          "| Pair | Exact label | κ (3 labels) | Keep/drop | κ (keep/drop) |", "|---|---|---|---|---|"]
    for a, b in itertools.combinations(names, 2):
        p3 = [(D[a][k], D[b][k]) for k in real]
        p2 = [(kept(a, k), kept(b, k)) for k in real]
        L.append(f"| {a} – {b} | {sum(x == y for x, y in p3) / len(p3):.1%} | {kappa(p3):.2f} | "
                 f"{sum(x == y for x, y in p2) / len(p2):.1%} | {kappa(p2):.2f} |")

    votes = collections.Counter(sum(kept(n, k) for n in names) for k in real)
    L += ["", "## How many models keep each paper", "", "| Kept by | Papers |", "|---|---|"]
    for v in (3, 2, 1, 0):
        L.append(f"| {v} of 3 | {votes[v]:,} |")
    only = {n: sum(kept(n, k) and not any(kept(m, k) for m in names if m != n) for k in real) for n in names}
    L.append("")
    L.append("Kept by one model only: " + ", ".join(f"{n} {only[n]:,}" for n in names) + ".")

    open(os.path.join(HERE, "screen_comparison_3way.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
