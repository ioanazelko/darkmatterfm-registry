"""Add INSPIRE-HEP citation counts, document type and journal to missing_candidates.jsonl.

Queries INSPIRE in batches ("arxiv:a or arxiv:b ..."), caching results in inspire_cache.jsonl
so re-runs only ask for ids not yet seen. Papers INSPIRE does not index (common for
astro-ph-only work) get inspire_found = false. Rewrites the candidate file in place.

Usage: python3 enrich_inspire.py [candidate file, default missing_candidates.jsonl]
"""
import json, os, subprocess, sys, time, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
CAND = os.path.join(HERE, sys.argv[1] if len(sys.argv) > 1 else "missing_candidates.jsonl")
CACHE = os.path.join(HERE, "inspire_cache.jsonl")
BATCH = 40
FIELDS = "arxiv_eprints.value,citation_count,document_type,publication_info.journal_title,titles.title"


def query(ids):
    q = " or ".join(f"arxiv:{i}" for i in ids)
    url = ("https://inspirehep.net/api/literature?" +
           urllib.parse.urlencode({"q": q, "fields": FIELDS, "size": 2 * len(ids)}))
    for attempt in range(8):
        r = subprocess.run(["curl", "-sS", "-m", "120", url], capture_output=True)
        try:
            return json.loads(r.stdout)["hits"]["hits"]
        except Exception:
            time.sleep(15 * (attempt + 1))
    raise RuntimeError("INSPIRE failed for batch starting " + ids[0])


def main():
    rows = [json.loads(l) for l in open(CAND)]
    cache = {}
    if os.path.exists(CACHE):
        for l in open(CACHE):
            d = json.loads(l)
            cache[d["arxiv_id"]] = d
    todo = [r["arxiv_id"] for r in rows if r["arxiv_id"] not in cache]
    print(f"{len(rows)} candidates, {len(todo)} to query", flush=True)
    with open(CACHE, "a") as f:
        for k in range(0, len(todo), BATCH):
            ids = todo[k:k + BATCH]
            got = {}
            for h in query(ids):
                m = h["metadata"]
                for e in m.get("arxiv_eprints", []):
                    got[e["value"]] = {
                        "inspire_found": True,
                        "inspire_recid": h.get("id"),
                        "inspire_citations": m.get("citation_count", 0),
                        "document_type": m.get("document_type", []),
                        "journal_title": next((p.get("journal_title") for p in m.get("publication_info", []) if p.get("journal_title")), None),
                    }
            for i in ids:
                d = {"arxiv_id": i, **got.get(i, {"inspire_found": False})}
                cache[i] = d
                f.write(json.dumps(d) + "\n")
            f.flush()
            if (k // BATCH) % 25 == 0:
                print(f"  {k + len(ids)}/{len(todo)}", flush=True)
            time.sleep(0.5)  # INSPIRE allows 15 requests / 5 s
    with open(CAND, "w") as f:
        for r in rows:
            c = cache.get(r["arxiv_id"], {})
            r.update({k: v for k, v in c.items() if k != "arxiv_id"})
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    found = sum(1 for r in rows if r.get("inspire_found"))
    print(f"done: {found}/{len(rows)} found in INSPIRE")


if __name__ == "__main__":
    main()
