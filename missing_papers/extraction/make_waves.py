#!/usr/bin/env python3
"""Split the full-text fetch set into priority tiers from the Opus 5.5 and Fable 5.1 abstract screens.

Usage: python3 make_waves.py [--out waves]

Reads the screens of the astro-ph / hep-ph list (screen_batches/, screen_results_{opus,fable}/)
and, where present, of the hep-th / gr-qc list (screen_batches_hepth/,
screen_results_hepth_{opus,fable}/). Calibration rows are skipped. A paper enters a tier if at
least one screen kept it (NOVEL_MODEL or UNSURE) or its Opus / Fable row was flagged as shifted
(alignment_flags*.json), the same set fetch_fulltext.py downloads:

  tier 1  both screens NOVEL_MODEL
  tier 2  one NOVEL_MODEL, the other UNSURE
  tier 3  both UNSURE
  tier 4  kept by one screen only, or flagged as shifted

When fulltext/manifest.jsonl exists, papers whose text was not fetched are left out and counted.
Writes OUT/candidates.tsv (arxiv_id, tier, slice, opus, fable) and OUT/tier{1..4}.txt.
"""
import argparse, collections, glob, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
MP = os.path.dirname(HERE)
KEEP = {"NOVEL_MODEL", "UNSURE"}
LISTS = [("", "screen_results_opus", "screen_results_fable", "alignment_flags.json"),
         ("_hepth", "screen_results_hepth_opus", "screen_results_hepth_fable", "alignment_flags_hepth.json")]


def decisions(folder):
    d = {}
    for f in glob.glob(os.path.join(MP, folder, "batch_*.jsonl")):
        for l in open(f):
            r = json.loads(l)
            d[r["key"]] = r["decision"]
    return d


def tier(o, f, shifted):
    if shifted:
        return 4  # its labels may belong to a neighbouring row, so it is fetched and run whatever they say
    if o not in KEEP and f not in KEEP:
        return None
    if (o in KEEP) != (f in KEEP):
        return 4
    if o == f == "NOVEL_MODEL":
        return 1
    if "NOVEL_MODEL" in (o, f):
        return 2
    return 3


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "waves"))
    a = ap.parse_args()
    fetched = None
    man = os.path.join(MP, "fulltext", "manifest.jsonl")
    if os.path.exists(man):
        fetched = {json.loads(l)["arxiv_id"] for l in open(man) if json.loads(l)["status"] == "ok"}
    rows, unfetched = {}, collections.Counter()
    for suffix, opus_dir, fable_dir, flags_file in LISTS:
        keymap = os.path.join(MP, f"screen_batches{suffix}", "keymap.jsonl")
        if not os.path.exists(keymap) or not os.path.isdir(os.path.join(MP, opus_dir)):
            print(f"skipping screen_batches{suffix}: not present")
            continue
        o, f = decisions(opus_dir), decisions(fable_dir)
        shifted = set()
        flags = os.path.join(MP, flags_file)
        if os.path.exists(flags):
            for name, keys in json.load(open(flags)).items():
                if name.startswith(("Opus", "Fable")):
                    shifted |= set(keys)
        for l in open(keymap):
            r = json.loads(l)
            if r.get("calibration"):
                continue
            k = r["key"]
            t = tier(o.get(k), f.get(k), k in shifted)
            if t is None:
                continue
            sl = r.get("slice") or ("hep-th/gr-qc" if suffix else "astro-ph/hep-ph")
            if fetched is not None and r["arxiv_id"] not in fetched:
                unfetched[t] += 1
                continue
            rows[r["arxiv_id"]] = (t, sl, o.get(k), f.get(k))
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "candidates.tsv"), "w") as fh:
        fh.write("arxiv_id\ttier\tslice\topus\tfable\n")
        for aid, (t, sl, o, f) in sorted(rows.items(), key=lambda x: (x[1][0], x[0])):
            fh.write(f"{aid}\t{t}\t{sl}\t{o}\t{f}\n")
    for t in (1, 2, 3, 4):
        ids = sorted(aid for aid, v in rows.items() if v[0] == t)
        open(os.path.join(a.out, f"tier{t}.txt"), "w").write("".join(i + "\n" for i in ids))
        by_slice = collections.Counter(v[1] for v in rows.values() if v[0] == t)
        note = f"; {unfetched[t]} without fetched text" if fetched is not None else ""
        print(f"tier {t}: {len(ids):,} papers ({', '.join(f'{s} {n:,}' for s, n in sorted(by_slice.items()))}){note}")
    print(f"total {len(rows):,} -> {a.out}")


if __name__ == "__main__":
    main()
