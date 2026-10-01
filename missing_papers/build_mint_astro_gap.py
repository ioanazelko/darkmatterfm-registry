"""List the astro-ph papers that MINT-1T-ArXiv holds but minty-astro-ph (its astro-ph subset) dropped.

Inputs (this directory unless noted):
  corpus_members_mint-1t-arxiv.jsonl     list_tar_members.py mlfoundations/MINT-1T-ArXiv @mint_shards.txt
  corpus_members_minty-astro-ph.jsonl    list_tar_members.py Smith42/minty-astro-ph ...
  arxiv_meta_physics_astro-ph.jsonl.gz   harvest_oai.py (categories, dates, titles, abstracts)
  ../darkmatterfm_schema_starter/registry/models/all_paper_status_{hep,combined}.jsonl
  missing_candidates.jsonl               build_missing_list.py

A paper is in the gap if it is a MINT-1T-ArXiv member (a .json document) whose arXiv
categories include any astro-ph category, and it is not a minty-astro-ph member. Each row
says whether the registry reached it anyway (as a hep-ph candidate or screened paper), whether
its title/abstract matches the DM lexicon, and whether it is already on the missing list.

Outputs: mint_astro_gap.jsonl, mint_astro_gap.md
"""
import collections, gzip, json, os

from build_missing_list import HERE, LEXICON, MODELS, lexicon_hits, norm_id


def members(path):
    out = {}
    for line in open(path):
        r = json.loads(line)
        if r["name"].endswith(".json"):
            out[norm_id(r["name"])] = r
    return out


def main():
    mint = members(os.path.join(HERE, "corpus_members_mint-1t-arxiv.jsonl"))
    minty = members(os.path.join(HERE, "corpus_members_minty-astro-ph.jsonl"))
    meta = {}
    for line in gzip.open(os.path.join(HERE, "arxiv_meta_physics_astro-ph.jsonl.gz"), "rt"):
        r = json.loads(line)
        meta[r["id"]] = r
    astro = {i for i, r in meta.items() if any(c.startswith("astro-ph") for c in r["categories"])}
    hep_cands = {norm_id(json.loads(l)["paper_id"]) for l in open(os.path.join(MODELS, "all_paper_status_hep.jsonl"))}
    status = {norm_id(json.loads(l)["paper_id"]): json.loads(l)["status"]
              for l in open(os.path.join(MODELS, "all_paper_status_combined.jsonl"))}
    missing = {json.loads(l)["arxiv_id"] for l in open(os.path.join(HERE, "missing_candidates.jsonl"))}

    mint_astro = {i for i in mint if i in astro}
    gap = sorted(mint_astro - set(minty), key=lambda i: (meta[i]["submitted"] or "", i))
    rows = []
    for i in gap:
        r = meta[i]
        hits = lexicon_hits(r["title"], r["abstract"])
        rows.append({
            "arxiv_id": i,
            "primary_category": r["categories"][0],
            "categories": r["categories"],
            "submitted": r["submitted"],
            "mint_shard": mint[i]["shard"],
            "mint_json_bytes": mint[i]["size"],
            "has_dark_matter_phrase": LEXICON[0] in hits,
            "lexicon_hits": hits,
            "in_hep_candidates": i in hep_cands,
            "registry_status": status.get(i),
            "on_missing_list": i in missing,
            "title": " ".join(r["title"].split()),
        })
    with open(os.path.join(HERE, "mint_astro_gap.jsonl"), "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    lex = [r for r in rows if r["lexicon_hits"]]
    unreached = [r for r in lex if not r["in_hep_candidates"] and not r["registry_status"]]
    by_year = collections.defaultdict(lambda: [0, 0, 0])  # MINT astro-ph members, gap, gap with lexicon hit
    for i in mint_astro:
        by_year[(meta[i]["submitted"] or "????")[:4]][0] += 1
    for r in rows:
        y = (r["submitted"] or "????")[:4]
        by_year[y][1] += 1
        by_year[y][2] += bool(r["lexicon_hits"])
    minty_not_mint = [i for i in minty if i not in mint]
    mint_unknown = [i for i in mint if i not in meta]
    L = [
        "# astro-ph papers in MINT-1T-ArXiv but not in minty-astro-ph",
        "",
        f"MINT-1T-ArXiv: {len(mint):,} documents in {len({r['shard'] for r in mint.values()}):,} shards; "
        f"{len(mint_astro):,} carry an astro-ph category (primary or cross-list).",
        f"minty-astro-ph: {len(minty):,} documents; {len(minty_not_mint):,} of them are not MINT-1T-ArXiv members.",
        f"MINT members not in the astro-ph harvest (other categories only, or unmatched ids): {len(mint_unknown):,}.",
        "",
        "| | papers |",
        "|---|---|",
        f"| **In MINT-1T-ArXiv with astro-ph, not in minty-astro-ph** | **{len(rows):,}** |",
        f"| — astro-ph primary | {sum(r['primary_category'].startswith('astro-ph') for r in rows):,} |",
        f"| — astro-ph cross-list only | {sum(not r['primary_category'].startswith('astro-ph') for r in rows):,} |",
        f"| — title/abstract match the DM lexicon | {len(lex):,} |",
        f"| — with \"dark matter\" in title/abstract | {sum(r['has_dark_matter_phrase'] for r in rows):,} |",
        f"| — lexicon match, reached the registry via the hep-ph slice | {len(lex) - len(unreached):,} |",
        f"| — lexicon match, never reached the registry | {len(unreached):,} |",
        f"| — of those, already on `missing_candidates.jsonl` | {sum(r['on_missing_list'] for r in unreached):,} |",
        "",
        "## By year",
        "",
        "| Year | MINT astro-ph papers | not in minty | share | of which DM lexicon |",
        "|---|---|---|---|---|",
    ]
    for y in sorted(by_year):
        a, g, x = by_year[y]
        L.append(f"| {y} | {a:,} | {g:,} | {g / a:.0%} | {x:,} |")
    open(os.path.join(HERE, "mint_astro_gap.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L[:18]))


if __name__ == "__main__":
    main()
