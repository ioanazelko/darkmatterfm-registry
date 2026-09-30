"""Assemble the list of astro-ph / hep-ph dark-matter candidate papers missing from the registry corpus.

Inputs (this directory unless noted):
  arxiv_meta_physics_astro-ph.jsonl.gz, arxiv_meta_physics_hep-ph.jsonl.gz   harvest_oai.py
  corpus_members_minty-astro-ph.jsonl                                        list_tar_members.py
  ../darkmatterfm_schema_starter/registry/models/all_paper_status_{hep,combined}.jsonl

A paper counts as *in the corpus* if it is a member of minty-astro-ph, a hep-ph lexical
candidate (all_paper_status_hep), or was screened at all (all_paper_status_combined).
Every other astro-ph / hep-ph paper whose title+abstract matches the DM lexicon is missing,
tagged `after_cutoff` (first version on or after CUTOFF) or `not_in_corpus`.

The lexicon is calibrated on the accepted registry papers: its recall on them is reported,
since the missing list can only be as complete as that recall.

Outputs: missing_candidates.jsonl, missing_summary.md
"""
import collections, glob, gzip, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
MODELS = os.path.join(HERE, "..", "darkmatterfm_schema_starter", "registry", "models")
CUTOFF = "2024-06-01"  # first month absent from both MINT slices

LEXICON = [
    r"dark[\s-]+matter", r"dark[\s-]+sector", r"hidden[\s-]+sector", r"dark[\s-]+photons?",
    r"\bwimps?\b", r"\bfimps?\b", r"\bsimps?\b", r"freeze[\s-]*in", r"axions?\b", r"axion[\s-]+like",
    r"\balps?\b", r"sterile[\s-]+neutrinos?", r"fuzzy[\s-]+dark", r"ultra[\s-]*light", r"self[\s-]*interacting",
    r"\bsidm\b", r"primordial[\s-]+black[\s-]+holes?", r"\bpbhs?\b", r"mirror[\s-]+(?:matter|world|sector|particles?)",
    r"twin[\s-]+higgs", r"q[\s-]*balls?", r"quark[\s-]+nuggets?", r"gravitinos?", r"neutralinos?", r"axinos?",
    r"majorons?", r"relic[\s-]+(?:abundance|density)", r"(?:direct|indirect)[\s-]+detection",
    r"dark[\s-]+(?:atoms?|forces?|glueballs?|pions?|baryons?|higgs|gauge|scalars?|fermions?|u\(1\)|radiation|energy[\s-]+interact)",
    r"inert[\s-]+(?:doublet|higgs)", r"kaluza[\s-]*klein[\s-]+(?:particle|dark)", r"lightest[\s-]+(?:supersymmetric|odd)",
    r"\blsp\b", r"\blkp\b", r"boson[\s-]+stars?", r"\bmacho", r"super[\s-]*heavy[\s-]+(?:dark|relic)", r"wimpzillas?",
    # unified dark-sector fluids and exotic relics, added after checking the accepted papers the list above missed
    r"chaplygin", r"quartessence", r"unified[\s-]+dark", r"dark[\s-]+fluids?", r"unparticle",
    r"(?:heavy|stable|long[\s-]*lived|exotic|massive|decaying|relic)[\s-]+(?:neutral[\s-]+)?(?:particles?|relics?|neutrinos?|leptons?|staus?)",
    r"fermi[\s-]+balls?", r"cryptons?", r"parallel[\s-]+world", r"\bnumsm\b|\bνmsm\b|nu\s?msm", r"ultra[\s-]*dense",
]
LEX_RE = [(p, re.compile(p, re.I)) for p in LEXICON]


def norm_id(p):
    """Registry / tar-member id -> canonical arXiv id (1003_0459 -> 1003.0459, astro-ph0405083 -> astro-ph/0405083)."""
    p = re.sub(r"\.(json|tiff)$", "", p.strip())
    p = re.sub(r"v\d+$", "", p)
    m = re.match(r"^(\d{4})[_.](\d{4,5})$", p)
    if m:
        return f"{m.group(1)}.{m.group(2)}"
    m = re.match(r"^([a-z\-]+(?:\.[A-Z]{2})?)/?(\d{7})$", p)
    if m:
        return f"{m.group(1)}/{m.group(2)}"
    return p


def lexicon_hits(title, abstract):
    t = f"{title or ''} {abstract or ''}"
    return [p for p, rx in LEX_RE if rx.search(t)]


def main():
    universe = {}
    for f in sorted(glob.glob(os.path.join(HERE, "arxiv_meta_physics_*.jsonl.gz"))):
        for line in gzip.open(f, "rt"):
            r = json.loads(line)
            universe[r["id"]] = r  # later harvest rows win (dedupes resumed pages and cross-set duplicates)
    universe = {k: r for k, r in universe.items()
                if any(c.startswith("astro-ph") or c == "hep-ph" for c in r["categories"])}

    minty = set()
    mf = os.path.join(HERE, "corpus_members_minty-astro-ph.jsonl")
    if os.path.exists(mf):
        minty = {norm_id(json.loads(l)["name"]) for l in open(mf) if json.loads(l)["name"].endswith(".json")}
    hep_cands = {norm_id(json.loads(l)["paper_id"]) for l in open(os.path.join(MODELS, "all_paper_status_hep.jsonl"))}
    status = {norm_id(json.loads(l)["paper_id"]): json.loads(l) for l in open(os.path.join(MODELS, "all_paper_status_combined.jsonl"))}
    in_corpus = minty | hep_cands | set(status)

    # Lexicon recall on accepted registry papers (the calibration target).
    acc = [i for i, s in status.items() if s["status"] == "accepted"]
    acc_found = [i for i in acc if i in universe]
    acc_hit = [i for i in acc_found if lexicon_hits(universe[i]["title"], universe[i]["abstract"])]
    acc_dm = [i for i in acc_found if re.search(r"dark[\s-]+matter", f"{universe[i]['title']} {universe[i]['abstract']}", re.I)]
    rej = [i for i, s in status.items() if s["status"] == "rejected" and i in universe]
    rej_hit = [i for i in rej if lexicon_hits(universe[i]["title"], universe[i]["abstract"])]

    rows, not_in_universe = [], sorted(i for i in in_corpus if i not in universe)
    for i, r in universe.items():
        if i in in_corpus:
            continue
        hits = lexicon_hits(r["title"], r["abstract"])
        if not hits:
            continue
        cats = r["categories"]
        rows.append({
            "arxiv_id": i,
            "primary_category": cats[0] if cats else None,
            "categories": cats,
            "submitted": r["submitted"],
            "missing_reason": "after_cutoff" if (r["submitted"] or "") >= CUTOFF else "not_in_corpus",
            "slice": "astro-ph" if any(c.startswith("astro-ph") for c in cats) else "hep-ph",
            "has_dark_matter_phrase": bool(re.search(r"dark[\s-]+matter", f"{r['title']} {r['abstract']}", re.I)),
            "lexicon_hits": hits,
            "title": r["title"],
            "abstract": r["abstract"],
            "authors": r["authors"],
            "doi": r["doi"],
            "journal_ref": r["journal_ref"],
            "comments": r["comments"],
            "license": r["license"],
        })
    rows.sort(key=lambda x: (x["submitted"] or "", x["arxiv_id"]))
    with open(os.path.join(HERE, "missing_candidates.jsonl"), "w") as f:
        for x in rows:
            f.write(json.dumps(x, ensure_ascii=False) + "\n")

    # Summary.
    by = collections.Counter((x["missing_reason"], x["slice"]) for x in rows)
    dm = collections.Counter((x["missing_reason"], x["slice"]) for x in rows if x["has_dark_matter_phrase"])
    yr = collections.defaultdict(collections.Counter)
    for x in rows:
        yr[(x["submitted"] or "????")[:4]][x["slice"]] += 1
    cov = collections.defaultdict(lambda: [0, 0])  # per year: DM-phrase astro/hep papers in corpus vs total
    for i, r in universe.items():
        if (r["submitted"] or "") >= CUTOFF or not re.search(r"dark[\s-]+matter", f"{r['title']} {r['abstract']}", re.I):
            continue
        y = r["submitted"][:4]
        cov[y][1] += 1
        cov[y][0] += i in in_corpus
    L = ["# Missing-paper list: summary", "",
         f"Universe: {len(universe):,} astro-ph / hep-ph papers (primary or cross-list) from the arXiv OAI harvest.",
         f"In corpus: {len(in_corpus):,} ids (minty-astro-ph members {len(minty):,}; hep-ph candidates {len(hep_cands):,}; screened {len(status):,}); "
         f"{len(not_in_universe):,} of these are not in the harvest (withdrawn, re-identified, or outside the two sets).", "",
         "## Lexicon calibration (title + abstract)", "",
         f"- Recall on accepted registry papers: **{len(acc_hit)}/{len(acc_found)} = {len(acc_hit)/max(1,len(acc_found)):.1%}** "
         f"(the phrase \"dark matter\" alone: {len(acc_dm)/max(1,len(acc_found)):.1%}).",
         f"- Share of rejected papers that also match: {len(rej_hit)}/{len(rej)} = {len(rej_hit)/max(1,len(rej)):.1%}.", "",
         "## Missing candidates", "", "| Reason | astro-ph | hep-ph only | total | of which \"dark matter\" in abstract |", "|---|---|---|---|---|"]
    for reason in ("not_in_corpus", "after_cutoff"):
        a, h = by[(reason, "astro-ph")], by[(reason, "hep-ph")]
        L.append(f"| {reason} | {a:,} | {h:,} | {a+h:,} | {dm[(reason,'astro-ph')]+dm[(reason,'hep-ph')]:,} |")
    L.append(f"| **total** | {sum(v for (r,s),v in by.items() if s=='astro-ph'):,} | {sum(v for (r,s),v in by.items() if s=='hep-ph'):,} | **{len(rows):,}** | {sum(dm.values()):,} |")
    L += ["", "## Corpus coverage of \"dark matter\"-abstract papers, by year (before the cutoff)", "",
          "| Year | in corpus / total | coverage | missing candidates (astro-ph / hep-ph only) |", "|---|---|---|---|"]
    for y in sorted(set(cov) | set(yr)):
        c, t = cov.get(y, [0, 0])
        L.append(f"| {y} | {c:,} / {t:,} | {c/max(1,t):.0%} | {yr[y]['astro-ph']:,} / {yr[y]['hep-ph']:,} |")
    open(os.path.join(HERE, "missing_summary.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L[:20]))


if __name__ == "__main__":
    main()
