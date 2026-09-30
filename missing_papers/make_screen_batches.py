"""Split missing candidates into abstract-screening batches for Claude agents, with a hidden calibration sample.

Each batch file screen_batches/batch_NNN.jsonl holds rows {key, title, abstract}. The key is an
opaque token, so the screening agent cannot tell a missing candidate from a calibration paper.
screen_batches/keymap.jsonl maps keys back to arXiv ids and marks calibration rows with the
registry's Codex triage outcome (accepted / rejected) for measuring agreement afterwards.

Order: candidates with "dark matter" in the abstract first, then the rest, so an interrupted
night still covers the most likely papers.
"""
import gzip, glob, json, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_missing_list import MODELS, norm_id  # noqa: E402

BATCH = 200
CALIB_PER_BATCH = 10


def main():
    rng = random.Random(20260924)
    cands = [json.loads(l) for l in open(os.path.join(HERE, "missing_candidates.jsonl"))]
    cands.sort(key=lambda r: (not r["has_dark_matter_phrase"], r["submitted"] or ""))
    universe = {}
    for f in glob.glob(os.path.join(HERE, "arxiv_meta_physics_*.jsonl.gz")):
        for l in gzip.open(f, "rt"):
            r = json.loads(l)
            universe[r["id"]] = r
    status = [json.loads(l) for l in open(os.path.join(MODELS, "all_paper_status_combined.jsonl"))]
    calib = [(norm_id(s["paper_id"]), s["status"]) for s in status if s["status"] in ("accepted", "rejected")]
    calib = [(i, st) for i, st in calib if i in universe]
    rng.shuffle(calib)

    out = os.path.join(HERE, "screen_batches")
    os.makedirs(out, exist_ok=True)
    keymap, k, ci = [], 0, 0
    nb = (len(cands) + BATCH - 1) // BATCH
    for b in range(nb):
        rows = [(r["arxiv_id"], r["title"], r["abstract"], None) for r in cands[b * BATCH:(b + 1) * BATCH]]
        for _ in range(CALIB_PER_BATCH):
            i, st = calib[ci % len(calib)]
            ci += 1
            rows.append((i, universe[i]["title"], universe[i]["abstract"], st))
        rng.shuffle(rows)
        with open(os.path.join(out, f"batch_{b:03d}.jsonl"), "w") as f:
            for i, t, a, st in rows:
                key = f"p{k:06d}"
                k += 1
                f.write(json.dumps({"key": key, "title": t, "abstract": a}, ensure_ascii=False) + "\n")
                keymap.append({"key": key, "arxiv_id": i, "batch": b, "calibration": st})
    with open(os.path.join(out, "keymap.jsonl"), "w") as f:
        for m in keymap:
            f.write(json.dumps(m) + "\n")
    print(f"{nb} batches, {len(cands)} candidates + {nb * CALIB_PER_BATCH} calibration rows")


if __name__ == "__main__":
    main()
