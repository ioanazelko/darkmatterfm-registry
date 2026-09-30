"""Compare the Sonnet 5 abstract screen (screen_results/) with the Opus 5.5 rerun (screen_results_opus/).

Only batches present in both directories are compared. Writes screen_comparison.md and
screen_comparison.jsonl (one row per paper where the two models disagree). Does not modify
missing_candidates.jsonl.
"""
import collections, glob, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
LABELS = ("NOVEL_MODEL", "UNSURE", "NOT_NOVEL_MODEL")
SHORT = {"NOVEL_MODEL": "NOVEL", "UNSURE": "UNSURE", "NOT_NOVEL_MODEL": "NOT"}
KEPT = ("NOVEL_MODEL", "UNSURE")


def load(d):
    out = {}
    for f in glob.glob(os.path.join(HERE, d, "batch_*.jsonl")):
        rows = {}
        for l in open(f):
            if l.strip():
                try:
                    g = json.loads(l)
                except json.JSONDecodeError:
                    continue
                if g.get("decision") in LABELS:
                    rows[g["key"]] = g
        out[os.path.basename(f)] = rows
    return out


def kappa(pairs):
    n = len(pairs)
    po = sum(a == b for a, b in pairs) / n
    ca, cb = collections.Counter(a for a, _ in pairs), collections.Counter(b for _, b in pairs)
    pe = sum(ca[l] * cb[l] for l in set(ca) | set(cb)) / n / n
    return (po - pe) / (1 - pe) if pe < 1 else 1.0


def main():
    keymap = {json.loads(l)["key"]: json.loads(l) for l in open(os.path.join(HERE, "screen_batches", "keymap.jsonl"))}
    son, opu = load("screen_results"), load("screen_results_opus")
    batches = sorted(set(son) & set(opu))
    S, O = {}, {}
    for b in batches:
        common = set(son[b]) & set(opu[b])
        S.update({k: son[b][k] for k in common})
        O.update({k: opu[b][k] for k in common})
    keys = sorted(S)
    cand = {json.loads(l)["arxiv_id"]: json.loads(l) for l in open(os.path.join(HERE, "missing_candidates.jsonl"))}
    gold = {json.loads(l)["arxiv_id"] for l in open(os.path.join(HERE, "gold_review_refs.jsonl"))}

    real = [k for k in keys if not keymap[k]["calibration"]]
    cal = [k for k in keys if keymap[k]["calibration"]]
    pairs = [(S[k]["decision"], O[k]["decision"]) for k in real]
    kept_pairs = [(a in KEPT, b in KEPT) for a, b in pairs]

    L = ["# Abstract screen: Sonnet 5 vs Opus 5.5", "",
         f"Batches compared: {len(batches)} of 192. Papers: {len(real):,} missing candidates + {len(cal):,} hidden calibration papers.",
         "Same batches, same prompt (`screen_prompt.md` / `screen_prompt_opus.md`, differing only in output folder).", "",
         "## Decision counts (missing candidates)", "",
         "| Decision | Sonnet 5 | Opus 5.5 |", "|---|---|---|"]
    cs, co = collections.Counter(a for a, _ in pairs), collections.Counter(b for _, b in pairs)
    for l in LABELS:
        L.append(f"| {l} | {cs[l]:,} | {co[l]:,} |")
    L.append(f"| kept (NOVEL+UNSURE) | {cs['NOVEL_MODEL'] + cs['UNSURE']:,} | {co['NOVEL_MODEL'] + co['UNSURE']:,} |")

    L += ["", "## Agreement (missing candidates)", "",
          f"- Exact label agreement: {sum(a == b for a, b in pairs) / len(pairs):.1%} (Cohen's κ = {kappa(pairs):.2f})",
          f"- Keep/drop agreement: {sum(a == b for a, b in kept_pairs) / len(pairs):.1%} (κ = {kappa(kept_pairs):.2f})",
          f"- Kept by either model: {sum(a or b for a, b in kept_pairs):,}; by both: {sum(a and b for a, b in kept_pairs):,}", "",
          "Rows: Sonnet 5; columns: Opus 5.5.", "",
          "| Sonnet \\ Opus | " + " | ".join(SHORT[l] for l in LABELS) + " |", "|---|---|---|---|"]
    cm = collections.Counter(pairs)
    for a in LABELS:
        L.append(f"| {SHORT[a]} | " + " | ".join(f"{cm[(a, b)]:,}" for b in LABELS) + " |")

    L += ["", "## Calibration against Codex full-text triage (hidden papers)", "",
          "| | Sonnet 5 | Opus 5.5 | Either (union) |", "|---|---|---|---|"]
    for outcome, name in (("accepted", "Codex-accepted kept (recall)"), ("rejected", "Codex-rejected kept (false-positive rate)")):
        ks = [k for k in cal if keymap[k]["calibration"] == outcome]
        if not ks:
            continue
        s = sum(S[k]["decision"] in KEPT for k in ks)
        o = sum(O[k]["decision"] in KEPT for k in ks)
        u = sum(S[k]["decision"] in KEPT or O[k]["decision"] in KEPT for k in ks)
        L.append(f"| {name}, n={len(ks):,} | {s / len(ks):.1%} | {o / len(ks):.1%} | {u / len(ks):.1%} |")
    acc = [k for k in cal if keymap[k]["calibration"] == "accepted"]
    if acc:
        L += ["", "Codex-accepted papers, Sonnet × Opus (rows Sonnet, columns Opus):", "",
              "| Sonnet \\ Opus | " + " | ".join(SHORT[l] for l in LABELS) + " |", "|---|---|---|---|"]
        ca = collections.Counter((S[k]["decision"], O[k]["decision"]) for k in acc)
        for a in LABELS:
            L.append(f"| {SHORT[a]} | " + " | ".join(f"{ca[(a, b)]:,}" for b in LABELS) + " |")

    by_year = collections.defaultdict(lambda: collections.Counter())
    for k in real:
        c = cand.get(keymap[k]["arxiv_id"], {})
        y = (c.get("submitted") or "????")[:4]
        blk = "after_cutoff" if c.get("missing_reason") == "after_cutoff" else ("≤2004" if y <= "2004" else "2005–2024-05")
        by_year[blk]["n"] += 1
        by_year[blk]["s"] += S[k]["decision"] in KEPT
        by_year[blk]["o"] += O[k]["decision"] in KEPT
    L += ["", "## Kept share by period", "", "| Period | n | Sonnet kept | Opus kept |", "|---|---|---|---|"]
    for blk in ("≤2004", "2005–2024-05", "after_cutoff"):
        c = by_year[blk]
        if c["n"]:
            L.append(f"| {blk} | {c['n']:,} | {c['s'] / c['n']:.1%} | {c['o'] / c['n']:.1%} |")

    g = [k for k in real if keymap[k]["arxiv_id"] in gold]
    if g:
        L += ["", "## Review-cited gold papers on the missing list", "",
              f"{len(g):,} gold papers screened. Kept by Sonnet: {sum(S[k]['decision'] in KEPT for k in g):,}; "
              f"by Opus: {sum(O[k]['decision'] in KEPT for k in g):,}; by either: "
              f"{sum(S[k]['decision'] in KEPT or O[k]['decision'] in KEPT for k in g):,}. "
              "(Gold papers include experiments and observations, so this is not a recall figure.)"]

    open(os.path.join(HERE, "screen_comparison.md"), "w").write("\n".join(L) + "\n")
    with open(os.path.join(HERE, "screen_comparison.jsonl"), "w") as f:
        for k in keys:
            if S[k]["decision"] != O[k]["decision"]:
                c = cand.get(keymap[k]["arxiv_id"], {})
                f.write(json.dumps({"key": k, "arxiv_id": keymap[k]["arxiv_id"], "calibration": keymap[k]["calibration"],
                                    "sonnet": S[k]["decision"], "opus": O[k]["decision"],
                                    "sonnet_class": S[k].get("model_class"), "opus_class": O[k].get("model_class"),
                                    "title": c.get("title")}, ensure_ascii=False) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
