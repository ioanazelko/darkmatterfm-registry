"""Independent recall gold set: the arXiv papers cited by major dark-matter reviews (via INSPIRE-HEP).

Output: gold_review_refs.jsonl, one row per cited arXiv id with the reviews citing it.
"""
import collections, json, os, subprocess, time

HERE = os.path.dirname(os.path.abspath(__file__))
REVIEWS = {
    "2406.01705": "Cirelli, Strumia, Zupan 2024, Dark Matter",
    "2403.15860": "Arcadi et al. 2024, The waning of the WIMP: endgame?",
    "1703.07364": "Arcadi et al. 2018, The waning of the WIMP?",
    "hep-ph/0404175": "Bertone, Hooper, Silk 2005, Particle dark matter",
}


def inspire(q, fields):
    url = f"https://inspirehep.net/api/literature?q={q}&fields={fields}&size=25"
    for attempt in range(6):
        r = subprocess.run(["curl", "-sS", "-m", "120", url], capture_output=True)
        try:
            return json.loads(r.stdout)["hits"]["hits"]
        except Exception:
            time.sleep(10 * (attempt + 1))
    raise RuntimeError(url)


def main():
    cited = collections.defaultdict(list)
    for arx, label in REVIEWS.items():
        hits = inspire(f"arxiv:{arx}", "titles,references.reference.arxiv_eprint")
        refs = {r["reference"]["arxiv_eprint"] for r in hits[0]["metadata"].get("references", [])
                if r.get("reference", {}).get("arxiv_eprint")}
        for e in refs:
            cited[e].append(arx)
        print(f"{arx} ({label}): {len(refs)} arXiv references", flush=True)
        time.sleep(1)
    with open(os.path.join(HERE, "gold_review_refs.jsonl"), "w") as f:
        for e in sorted(cited):
            f.write(json.dumps({"arxiv_id": e, "cited_by": cited[e]}) + "\n")
    print(len(cited), "distinct cited arXiv papers")


if __name__ == "__main__":
    main()
