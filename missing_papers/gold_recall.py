"""Recall of the corpus, and of corpus + missing list, on the review-cited gold set (gold_review_refs.jsonl).

Restricted to gold papers listed in astro-ph or hep-ph (from the OAI harvest), split by
five-year bin. Writes gold_recall.md.
"""
import collections, gzip, glob, json, os

from build_missing_list import HARVESTS, MODELS, norm_id

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    universe = {}
    for f in HARVESTS:
        for l in gzip.open(f, "rt"):
            r = json.loads(l)
            universe[r["id"]] = r
    minty = {norm_id(json.loads(l)["name"]) for l in open(os.path.join(HERE, "corpus_members_minty-astro-ph.jsonl")) if ".json\"" in l}
    hep = {norm_id(json.loads(l)["paper_id"]) for l in open(os.path.join(MODELS, "all_paper_status_hep.jsonl"))}
    status = {norm_id(json.loads(l)["paper_id"]): json.loads(l)["status"] for l in open(os.path.join(MODELS, "all_paper_status_combined.jsonl"))}
    corpus = minty | hep | set(status)
    missing = {json.loads(l)["arxiv_id"]: json.loads(l) for l in open(os.path.join(HERE, "missing_candidates.jsonl"))}

    gold = [json.loads(l)["arxiv_id"] for l in open(os.path.join(HERE, "gold_review_refs.jsonl"))]
    outside = [g for g in gold if g not in universe]
    gold = [g for g in gold if g in universe]
    bins = collections.defaultdict(lambda: collections.Counter())
    for g in gold:
        y = universe[g]["submitted"][:4]
        b = f"{int(y) // 5 * 5}–{int(y) // 5 * 5 + 4}"
        c = bins[b]
        c["n"] += 1
        c["corpus"] += g in corpus
        c["screened"] += g in status
        c["accepted"] += status.get(g) == "accepted"
        c["missing_list"] += g in missing
        c["missing_kept"] += g in missing and missing[g].get("screen_decision") in ("NOVEL_MODEL", "UNSURE")
        c["neither"] += g not in corpus and g not in missing
    tot = sum(bins.values(), collections.Counter())
    L = ["# Recall on review-cited papers", "",
         "Gold set: arXiv papers cited by Cirelli–Strumia–Zupan 2024 (2406.01705), Arcadi et al. 2024 (2403.15860) "
         "and 2018 (1703.07364), and Bertone–Hooper–Silk 2005 (hep-ph/0404175), via INSPIRE-HEP. "
         f"{len(gold):,} are listed in astro-ph or hep-ph ({len(outside):,} others, e.g. hep-ex / gr-qc only, excluded). "
         "These are dark-matter papers of every kind (models, experiments, observations), not only model papers.", "",
         "| Submitted | Gold | In corpus | Screened | Accepted | On missing list | Neither |", "|---|---|---|---|---|---|---|"]
    for b in sorted(bins) + ["all"]:
        c = tot if b == "all" else bins[b]
        n = max(1, c["n"])
        L.append(f"| {b} | {c['n']:,} | {c['corpus']:,} ({c['corpus']/n:.0%}) | {c['screened']:,} | {c['accepted']:,} | "
                 f"{c['missing_list']:,} ({c['missing_list']/n:.0%}) | {c['neither']:,} ({c['neither']/n:.0%}) |")
    L += ["", f"Corpus + missing list together cover **{(tot['corpus'] + tot['missing_list'])/max(1, tot['n']):.1%}** of the gold set "
          f"(corpus alone {tot['corpus']/max(1, tot['n']):.1%}). The remaining {tot['neither']:,} gold papers have no lexicon term in "
          "their title or abstract; they are the recall cost of filtering on abstracts rather than full texts."]
    if any(v.get("screen_decision") for v in missing.values()):
        L.append(f"Of the gold papers on the missing list, {tot['missing_kept']:,} were kept by the abstract screen (novel model or unsure).")
    open(os.path.join(HERE, "gold_recall.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
