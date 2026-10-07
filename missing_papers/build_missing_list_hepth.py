"""Assemble the hep-th / gr-qc dark-matter candidate papers that the astro-ph / hep-ph list cannot see.

Inputs (this directory unless noted):
  arxiv_meta_physics_hep-th.jsonl.gz, arxiv_meta_physics_gr-qc.jsonl.gz   harvest_oai.py
  corpus_members_minty-astro-ph.jsonl                                     list_tar_members.py
  corpus_members_mint-1t-arxiv.jsonl  (optional; sets in_mint)           list_tar_members.py
  missing_candidates.jsonl, gold_review_refs.jsonl
  ../darkmatterfm_schema_starter/registry/models/all_paper_status_{hep,combined}.jsonl

A paper enters this list if none of its categories is astro-ph* or hep-ph (so the original runs
never selected it), it is not in the registry corpus or the astro-ph / hep-ph missing list, and its
title + abstract match the same DM lexicon. Slice `hep-th` = has a hep-th category; slice `gr-qc` =
gr-qc without hep-th. Every row has missing_reason `category_not_selected`; `after_cutoff` marks
papers first submitted after the MINT cutoff. missing_candidates.jsonl is read, never written.

Outputs: missing_candidates_hepth.jsonl, missing_summary_hepth.md
"""
import collections, gzip, json, os, re

from build_missing_list import CUTOFF, HERE, LEXICON, MODELS, lexicon_hits, norm_id

SLICES = ("hep-th", "gr-qc")
ANY_LEX = re.compile("|".join(f"(?:{p})" for p in LEXICON), re.I)  # cheap prefilter before per-term hits
DM = re.compile(r"dark[\s-]+matter", re.I)


def selected_before(cats):
    return any(c.startswith("astro-ph") or c == "hep-ph" for c in cats)


def main():
    universe = {}
    for s in SLICES:
        for line in gzip.open(os.path.join(HERE, f"arxiv_meta_physics_{s}.jsonl.gz"), "rt"):
            r = json.loads(line)
            universe[r["id"]] = r  # later rows win (dedupes resumed pages and hep-th / gr-qc cross-lists)
    pool = {k: r for k, r in universe.items() if not selected_before(r["categories"])}

    minty = {norm_id(json.loads(l)["name"]) for l in open(os.path.join(HERE, "corpus_members_minty-astro-ph.jsonl"))
             if ".json\"" in l}
    hep_cands = {norm_id(json.loads(l)["paper_id"]) for l in open(os.path.join(MODELS, "all_paper_status_hep.jsonl"))}
    status = {norm_id(json.loads(l)["paper_id"]) for l in open(os.path.join(MODELS, "all_paper_status_combined.jsonl"))}
    in_corpus = minty | hep_cands | status
    listed = {json.loads(l)["arxiv_id"] for l in open(os.path.join(HERE, "missing_candidates.jsonl"))}
    mf = os.path.join(HERE, "corpus_members_mint-1t-arxiv.jsonl")
    mint = ({norm_id(json.loads(l)["name"]) for l in open(mf) if ".json\"" in l} if os.path.exists(mf) else None)

    rows, skipped = [], collections.Counter()
    for i, r in pool.items():
        if i in in_corpus:
            skipped["in_corpus"] += 1
            continue
        if i in listed:
            skipped["already_listed"] += 1
            continue
        if not ANY_LEX.search(f"{r['title'] or ''} {r['abstract'] or ''}"):
            continue
        cats = r["categories"]
        rows.append({
            "arxiv_id": i,
            "primary_category": cats[0] if cats else None,
            "categories": cats,
            "submitted": r["submitted"],
            "missing_reason": "category_not_selected",
            "after_cutoff": (r["submitted"] or "") >= CUTOFF,
            "slice": "hep-th" if "hep-th" in cats else "gr-qc",
            "in_mint": (i in mint) if mint is not None else None,
            "has_dark_matter_phrase": bool(DM.search(f"{r['title']} {r['abstract']}")),
            "lexicon_hits": lexicon_hits(r["title"], r["abstract"]),
            "title": r["title"],
            "abstract": r["abstract"],
            "authors": r["authors"],
            "doi": r["doi"],
            "journal_ref": r["journal_ref"],
            "comments": r["comments"],
            "license": r["license"],
        })
    rows.sort(key=lambda x: (x["submitted"] or "", x["arxiv_id"]))
    with open(os.path.join(HERE, "missing_candidates_hepth.jsonl"), "w") as f:
        for x in rows:
            f.write(json.dumps(x, ensure_ascii=False) + "\n")

    # Summary.
    ids = {x["arxiv_id"] for x in rows}
    by = collections.Counter((x["slice"], x["after_cutoff"]) for x in rows)
    dm = collections.Counter(x["slice"] for x in rows if x["has_dark_matter_phrase"])
    term = collections.Counter(p for x in rows for p in x["lexicon_hits"])
    yr = collections.defaultdict(collections.Counter)
    for x in rows:
        yr[(x["submitted"] or "????")[:4]][x["slice"]] += 1
    gold = {json.loads(l)["arxiv_id"] for l in open(os.path.join(HERE, "gold_review_refs.jsonl"))}
    gold_pool = gold & set(pool)
    pool_n = collections.Counter("hep-th" if "hep-th" in r["categories"] else "gr-qc" for r in pool.values())
    tot = lambda s: by[(s, False)] + by[(s, True)]
    L = ["# hep-th / gr-qc missing-paper list: summary", "",
         f"Harvest: {len(universe):,} hep-th / gr-qc papers (primary or cross-list). Not in astro-ph or hep-ph: "
         f"{len(pool):,} ({pool_n['hep-th']:,} with hep-th, {pool_n['gr-qc']:,} gr-qc without hep-th).",
         f"Excluded: {skipped['in_corpus']:,} already in the registry corpus, "
         f"{skipped['already_listed']:,} already in missing_candidates.jsonl.",
         f"MINT-1T-ArXiv membership: " + (f"{sum(bool(x['in_mint']) for x in rows):,} of the candidates have source in MINT."
                                          if mint is not None else "not computed (corpus_members_mint-1t-arxiv.jsonl absent)."), "",
         "## Candidates", "", "| Slice | ≤ cutoff | after cutoff | total | \"dark matter\" in title/abstract |", "|---|---|---|---|---|"]
    for s in SLICES:
        L.append(f"| {s} | {by[(s, False)]:,} | {by[(s, True)]:,} | {tot(s):,} | {dm[s]:,} |")
    L.append(f"| **total** | {sum(by[(s, False)] for s in SLICES):,} | {sum(by[(s, True)] for s in SLICES):,} | "
             f"**{len(rows):,}** | {sum(dm.values()):,} |")
    L += ["", "## Review-cited gold set", "",
          f"{len(gold_pool)} gold papers are hep-th / gr-qc only; {len(gold_pool & ids)} are candidates here, "
          f"{len(gold_pool & in_corpus)} already in the corpus.", "",
          "## Most frequent lexicon terms", "", "| Term | candidates |", "|---|---|"]
    L += [f"| `{p}` | {n:,} |" for p, n in term.most_common(15)]
    L += ["", "## Candidates by year", "", "| Year | hep-th | gr-qc |", "|---|---|---|"]
    L += [f"| {y} | {yr[y]['hep-th']:,} | {yr[y]['gr-qc']:,} |" for y in sorted(yr)]
    open(os.path.join(HERE, "missing_summary_hepth.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L[:22]))


if __name__ == "__main__":
    main()
