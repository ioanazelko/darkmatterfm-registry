#!/usr/bin/env python3
"""Collect the validated batches of one or more extraction runs into registry-format files.

Usage: python3 merge_extraction.py RUN [RUN ...] [--out results/NAME]

Only batches that pass validate_batch.py are taken. Writes OUT_outputs.jsonl (one card row per
line, same wrapper as all_outputs_combined.jsonl) and OUT_paper_status.jsonl (same fields as
all_paper_status_combined.jsonl plus arxiv_id, run_id and batch_id). A paper that appears in
more than one run keeps its result from the last run named. Default OUT: results/<first RUN>.
"""
import argparse, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from validate_batch import validate  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--out")
    a = ap.parse_args()
    out = Path(a.out) if a.out else HERE / "results" / a.runs[0]
    out.parent.mkdir(parents=True, exist_ok=True)
    status, rows, skipped = {}, {}, []
    for run in a.runs:
        rd = HERE / "runs" / run
        aid = {json.loads(l)["paper_id"]: json.loads(l)["arxiv_id"] for l in open(rd / "manifest.jsonl")}
        for bdir in sorted((rd / "batches").iterdir()):
            if validate(bdir)[0]:
                skipped.append(f"{run}/{bdir.name}")
                continue
            for l in open(bdir / "paper_status.jsonl"):
                if l.strip():
                    r = json.loads(l)
                    status[r["paper_id"]] = {**r, "arxiv_id": aid.get(r["paper_id"]), "run_id": run, "batch_id": bdir.name}
                    rows[r["paper_id"]] = []
            for l in open(bdir / "outputs.jsonl"):
                if l.strip():
                    r = json.loads(l)
                    rows[r["paper_id"]].append(r)
    with open(f"{out}_paper_status.jsonl", "w") as f:
        for p in sorted(status):
            f.write(json.dumps(status[p], ensure_ascii=False) + "\n")
    n = 0
    with open(f"{out}_outputs.jsonl", "w") as f:
        for p in sorted(rows):
            for r in rows[p]:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
                n += 1
    acc = sum(r["status"] == "accepted" for r in status.values())
    print(f"{len(status)} papers ({acc} accepted), {n} cards -> {out}_outputs.jsonl, {out}_paper_status.jsonl; "
          f"{len(skipped)} batches skipped (not passing)")


if __name__ == "__main__":
    main()
