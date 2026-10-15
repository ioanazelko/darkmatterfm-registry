#!/usr/bin/env python3
"""Summarise an extraction run: decisions, agreement with Codex where it exists, and token usage.

Usage: python3 score_extraction.py RUN [--tiers waves/candidates.tsv] [--project N]

Reads runs/RUN/manifest.jsonl, the paper_status.jsonl / outputs.jsonl of every batch that passes
validate_batch.py, and runs/RUN/usage.jsonl. Papers that Codex triaged (the calibration set) are
compared with all_paper_status_combined.jsonl (decision and card count per paper): confusion table,
recall on Codex-accepted papers, share of Codex-rejected papers accepted, card counts, and every
disagreement with both reasons. --tiers adds acceptance by screen tier; --project N scales the
measured tokens per paper to N papers. Writes runs/RUN/score.md and prints its head.
"""
import argparse, collections, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
sys.path.insert(0, str(HERE))
from validate_batch import validate  # noqa: E402

TOKENS = ["input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens"]


def models_dir():
    for c in (REPO / "darkmatterfm_schema_starter" / "registry" / "models", REPO / "registry" / "models"):
        if (c / "all_paper_status_combined.jsonl").exists():
            return c
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--tiers")
    ap.add_argument("--project", type=int, default=0)
    a = ap.parse_args()
    rd = HERE / "runs" / a.run
    man = [json.loads(l) for l in open(rd / "manifest.jsonl")]
    by_batch = collections.defaultdict(list)
    for r in man:
        by_batch[r["batch_id"]].append(r["paper_id"])
    status, cards, failing = {}, collections.defaultdict(list), []
    for b in sorted(by_batch):
        bdir = rd / "batches" / b
        if validate(bdir)[0]:
            failing.append(b)
            continue
        for l in open(bdir / "paper_status.jsonl"):
            if l.strip():
                r = json.loads(l)
                status[r["paper_id"]] = r
        for l in open(bdir / "outputs.jsonl"):
            if l.strip():
                r = json.loads(l)
                cards[r["paper_id"]].append(r["model_card"]["identity"]["name"])
    n_pass = len(by_batch) - len(failing)
    sc = collections.Counter(r["status"] for r in status.values())
    L = [f"# Extraction run `{a.run}`", "",
         f"- Batches: {len(by_batch)} staged, {n_pass} pass validation, {len(failing)} not (yet) passing.",
         f"- Papers with a result: {len(status)} of {len(man)}: {sc['accepted']} accepted, {sc['rejected']} rejected, "
         f"{sc['error']} error; {sum(len(v) for v in cards.values())} cards "
         f"({sum(len(v) for v in cards.values()) / max(1, sc['accepted']):.2f} per accepted paper).", ""]

    md = models_dir()
    if md:
        codex = {json.loads(l)["paper_id"]: json.loads(l) for l in open(md / "all_paper_status_combined.jsonl")}
        ccards = {p: r["accepted_model_card_count"] for p, r in codex.items()}
        both = [p for p in status if p in codex and codex[p]["status"] in ("accepted", "rejected")
                and status[p]["status"] in ("accepted", "rejected")]
        if both:
            m = collections.Counter((codex[p]["status"], status[p]["status"]) for p in both)
            ca, cr = m[("accepted", "accepted")] + m[("accepted", "rejected")], m[("rejected", "accepted")] + m[("rejected", "rejected")]
            agree = m[("accepted", "accepted")] + m[("rejected", "rejected")]
            same = [p for p in both if codex[p]["status"] == status[p]["status"] == "accepted"]
            L += ["## Agreement with Codex (calibration papers)", "",
                  "| Codex \\ Claude | accepted | rejected |", "|---|---|---|",
                  f"| accepted | {m[('accepted', 'accepted')]} | {m[('accepted', 'rejected')]} |",
                  f"| rejected | {m[('rejected', 'accepted')]} | {m[('rejected', 'rejected')]} |", "",
                  f"- Agreement: **{agree / len(both):.1%}** of {len(both)} papers",
                  f"- Recall (Codex-accepted that Claude accepts): **{m[('accepted', 'accepted')] / max(1, ca):.1%}**",
                  f"- Codex-rejected that Claude accepts: **{m[('rejected', 'accepted')] / max(1, cr):.1%}**",
                  f"- Cards on papers both accept: Claude {sum(len(cards[p]) for p in same)}, Codex {sum(ccards[p] for p in same)}; "
                  f"same count on {sum(len(cards[p]) == ccards[p] for p in same)} of {len(same)} papers", "",
                  "## Disagreements", ""]
            for p in both:
                if codex[p]["status"] != status[p]["status"]:
                    claude = (status[p]["rejection_reason"] if status[p]["status"] == "rejected"
                              else "; ".join(cards[p]))
                    L.append(f"- **{p}** Codex {codex[p]['status']} ({ccards[p]} cards; {codex[p]['rejection_reason'] or '-'}) "
                             f"· Claude {status[p]['status']}: {claude}")
            L.append("")

    if a.tiers:
        tiers = {}
        for l in open(a.tiers):
            if not l.startswith("arxiv_id"):
                f = l.rstrip("\n").split("\t")
                aid = f[0]
                tiers[aid.replace("/", "") if "/" in aid else aid.replace(".", "_")] = f[1]
        t = collections.defaultdict(collections.Counter)
        for p, r in status.items():
            t[tiers.get(p, "?")][r["status"]] += 1
        L += ["## Acceptance by screen tier", "", "| Tier | papers | accepted | share |", "|---|---|---|---|"]
        for k in sorted(t):
            n = sum(t[k].values())
            L.append(f"| {k} | {n} | {t[k]['accepted']} | {t[k]['accepted'] / max(1, n):.0%} |")
        L.append("")

    up = rd / "usage.jsonl"
    if up.exists():
        u = [json.loads(l) for l in open(up) if l.strip()]
        tot = {k: sum(r.get(k) or 0 for r in u) for k in TOKENS}
        allt = sum(tot.values())
        papers = sum(len(by_batch[r["batch_id"]]) for r in u if r["validation"] == "PASS")
        L += ["## Token usage", "",
              f"- {len(u)} worker attempts ({sum(r['validation'] == 'PASS' for r in u)} passed), "
              f"{sum(r['seconds'] for r in u) / 3600:.1f} worker-hours, median {sorted(r['seconds'] for r in u)[len(u) // 2]} s per attempt.",
              f"- Tokens: input {tot['input_tokens']:,}, cache write {tot['cache_creation_input_tokens']:,}, "
              f"cache read {tot['cache_read_input_tokens']:,}, output {tot['output_tokens']:,}; total {allt:,}.",
              f"- Per paper with a passing result (failed attempts included): {allt / max(1, papers):,.0f} tokens, "
              f"of which output {tot['output_tokens'] / max(1, papers):,.0f}."]
        if a.project:
            L.append(f"- Projected for {a.project:,} papers: {allt / max(1, papers) * a.project / 1e6:,.0f}M tokens "
                     f"({tot['output_tokens'] / max(1, papers) * a.project / 1e6:,.1f}M output).")
        L.append("")
    if failing:
        L += ["## Batches not passing", "", ", ".join(failing), ""]
    (rd / "score.md").write_text("\n".join(L) + "\n")
    print("\n".join(L[:40]))


if __name__ == "__main__":
    main()
