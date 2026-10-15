#!/usr/bin/env python3
"""Stage downloaded full texts as batches for the Claude model-card extraction workers.

Usage: python3 stage_extraction.py RUN IDS_FILE [--source DIR ...] [--max-papers 5]
                                   [--max-chars 350000] [--model-name "Claude Opus 5.5"]
                                   [--date YYYY-MM-DD] [--seed N] [--force]

IDS_FILE lists arXiv ids, one per line (anything after the first whitespace is ignored).
Each id's text is read from <source>/<id without "/">.json (fetch_fulltext.py output, MINT
layout {"texts": [latex], ...}); the first source that has it wins. Writes, under runs/RUN/:

  papers/<paper_id>.tex                  the LaTeX text, lines over 1000 characters wrapped at spaces;
                                         paper_id is the registry form of the id
                                         (1003.0459 -> 1003_0459, hep-ph/0405083 -> hep-ph0405083)
  batches/batch-NNNN/assignment.json     run id, batch id, paper ids in order, extraction date
  batches/batch-NNNN/prompt.md           worker_prompt_template.md filled in for that batch
  manifest.jsonl                         one row per staged paper: ids, batch, text size, source
  missing.txt                            ids with no text in any source

Papers are shuffled with a fixed seed, then packed greedily: a batch holds at most --max-papers
papers and --max-chars characters of text, and a longer paper gets a batch of its own.
"""
import argparse, datetime, json, os, random, shutil, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent


def find_registry():
    for cand in (REPO / "registry", REPO / "darkmatterfm_schema_starter" / "registry"):
        if (cand / "codex_prompts" / "extraction_output_guide.md").exists():
            return cand
    sys.exit("cannot find registry/codex_prompts")


def paper_id(arxiv_id):
    return arxiv_id.replace("/", "") if "/" in arxiv_id else arxiv_id.replace(".", "_")


def wrap_long_lines(text, width=1000):
    # File-reading tools may truncate very long lines, and LaTeX often keeps a paragraph on one
    # line. Break such lines at spaces (or hard, if there is no space); no character is dropped.
    out = []
    for line in text.split("\n"):
        while len(line) > width:
            cut = line.rfind(" ", 0, width)
            cut = cut + 1 if cut > width // 2 else width
            out.append(line[:cut])
            line = line[cut:]
        out.append(line)
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("ids")
    ap.add_argument("--source", nargs="+", default=[str(HERE.parent / "fulltext"), str(HERE.parent / "fulltext_calib")])
    ap.add_argument("--max-papers", type=int, default=5)
    ap.add_argument("--max-chars", type=int, default=350000)
    ap.add_argument("--model-name", default="Claude Opus 5.5")
    ap.add_argument("--date", default=datetime.date.today().isoformat())
    ap.add_argument("--seed", type=int, default=20261015)
    ap.add_argument("--force", action="store_true", help="replace an existing run directory")
    a = ap.parse_args()

    run_dir = HERE / "runs" / a.run
    if run_dir.exists():
        if not a.force:
            sys.exit(f"{run_dir} exists; pass --force to replace it")
        shutil.rmtree(run_dir)
    (run_dir / "papers").mkdir(parents=True)
    registry = find_registry()
    template = (HERE / "worker_prompt_template.md").read_text()

    ids = list(dict.fromkeys(l.split()[0] for l in open(a.ids) if l.strip() and not l.startswith("#")))
    staged, missing = [], []
    for aid in ids:
        src = next((Path(s) / (aid.replace("/", "") + ".json") for s in a.source
                    if (Path(s) / (aid.replace("/", "") + ".json")).exists()), None)
        if src is None:
            missing.append(aid)
            continue
        text = json.load(open(src))["texts"][0] or ""
        pid = paper_id(aid)
        (run_dir / "papers" / f"{pid}.tex").write_text(wrap_long_lines(text))
        staged.append({"paper_id": pid, "arxiv_id": aid, "text_chars": len(text), "source": str(src)})

    random.Random(a.seed).shuffle(staged)
    batches, cur, size = [], [], 0
    for p in staged:
        if p["text_chars"] > a.max_chars:
            batches.append([p])
            continue
        if cur and (len(cur) >= a.max_papers or size + p["text_chars"] > a.max_chars):
            batches.append(cur)
            cur, size = [], 0
        cur.append(p)
        size += p["text_chars"]
    if cur:
        batches.append(cur)

    subs = {"{{REPO}}": str(REPO), "{{RUN_ID}}": a.run, "{{PAPERS_DIR}}": str(run_dir / "papers"),
            "{{DATE}}": a.date, "{{MODEL_NAME}}": a.model_name,
            "{{GUIDE}}": str(registry / "codex_prompts" / "extraction_output_guide.md"),
            "{{PROFILE}}": str(registry / "codex_prompts" / "schema_profile_model_only.json"),
            "{{SCHEMAS}}": str(registry / "schemas"), "{{VALIDATOR}}": str(HERE / "validate_batch.py")}
    with open(run_dir / "manifest.jsonl", "w") as man:
        for b, rows in enumerate(batches):
            bid = f"batch-{b:04d}"
            bdir = run_dir / "batches" / bid
            bdir.mkdir(parents=True)
            pids = [r["paper_id"] for r in rows]
            json.dump({"run_id": a.run, "batch_id": bid, "paper_ids": pids, "extraction_date": a.date,
                       "papers_dir": str(run_dir / "papers")}, open(bdir / "assignment.json", "w"), indent=1)
            prompt = template
            for k, v in {**subs, "{{BATCH_ID}}": bid, "{{BATCH_DIR}}": str(bdir),
                         "{{PAPER_IDS_JSON}}": json.dumps(pids)}.items():
                prompt = prompt.replace(k, v)
            assert "{{" not in prompt, "unfilled placeholder in worker prompt"
            (bdir / "prompt.md").write_text(prompt)
            for r in rows:
                man.write(json.dumps({**r, "batch_id": bid}) + "\n")
    (run_dir / "missing.txt").write_text("".join(m + "\n" for m in missing))
    chars = sum(p["text_chars"] for p in staged)
    print(f"{len(staged)} papers staged in {len(batches)} batches ({chars / 1e6:.1f}M characters of LaTeX); "
          f"{len(missing)} ids without text -> {run_dir}")


if __name__ == "__main__":
    main()
