"""Harvest arXiv metadata (arXivRaw) for one OAI-PMH set into gzipped JSONL.

Usage: python3 harvest_oai.py physics:astro-ph [out_dir]

Resumable: the resumption token and page count are checkpointed after every page,
so re-running continues where it stopped. One row per record:
id, submitted (v1 date, ISO), versions, categories, set_specs, title, abstract,
authors, doi, journal_ref, comments, license.
"""
import gzip, json, os, subprocess, sys, time, urllib.parse
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

BASE = "https://oaipmh.arxiv.org/oai"
NS = {"o": "http://www.openarchives.org/OAI/2.0/", "r": "http://arxiv.org/OAI/arXivRaw/"}
PAUSE = 3.0


def fetch(params):
    # curl rather than urllib: the arXiv OAI server answers urllib's requests with 406.
    url = BASE + "?" + urllib.parse.urlencode(params, safe=":")
    for attempt in range(12):
        r = subprocess.run(["curl", "-sS", "-L", "-m", "300", "-A", "darkmatterfm-registry-harvester/0.1",
                            "-w", "\\n%{http_code}", url], capture_output=True)
        body, _, code = r.stdout.rpartition(b"\n")
        if r.returncode == 0 and code == b"200":
            return body
        wait = 30 * (attempt + 1)
        print(f"curl rc={r.returncode} http={code.decode(errors='replace')}; sleeping {wait}s", flush=True)
        time.sleep(wait)
    raise RuntimeError("giving up on " + url)


def text(el, path):
    x = el.find(path, NS)
    return " ".join(x.text.split()) if x is not None and x.text else None


def parse_record(rec):
    hdr = rec.find("o:header", NS)
    if hdr.get("status") == "deleted":
        return None
    m = rec.find("o:metadata/r:arXivRaw", NS)
    versions = []
    for v in m.findall("r:version", NS):
        d = text(v, "r:date")
        versions.append({"v": v.get("version"),
                         "date": parsedate_to_datetime(d).strftime("%Y-%m-%d") if d else None})
    return {
        "id": text(m, "r:id"),
        "submitted": versions[0]["date"] if versions else None,
        "versions": versions,
        "categories": (text(m, "r:categories") or "").split(),
        "set_specs": [s.text for s in hdr.findall("o:setSpec", NS)],
        "title": text(m, "r:title"),
        "abstract": text(m, "r:abstract"),
        "authors": text(m, "r:authors"),
        "doi": text(m, "r:doi"),
        "journal_ref": text(m, "r:journal-ref"),
        "comments": text(m, "r:comments"),
        "license": text(m, "r:license"),
    }


def main():
    oai_set = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.dirname(os.path.abspath(__file__))
    tag = oai_set.replace(":", "_")
    out_path = os.path.join(out_dir, f"arxiv_meta_{tag}.jsonl.gz")
    ckpt_path = os.path.join(out_dir, f".harvest_{tag}.ckpt.json")
    ckpt = json.load(open(ckpt_path)) if os.path.exists(ckpt_path) else {"token": None, "pages": 0, "records": 0}
    if ckpt.get("done"):
        print("already complete:", ckpt); return
    while True:
        params = ({"verb": "ListRecords", "resumptionToken": ckpt["token"]} if ckpt["token"]
                  else {"verb": "ListRecords", "metadataPrefix": "arXivRaw", "set": oai_set})
        root = ET.fromstring(fetch(params))
        err = root.find("o:error", NS)
        if err is not None:
            if err.get("code") == "noRecordsMatch":
                break
            raise RuntimeError(f"OAI error {err.get('code')}: {err.text}")
        lr = root.find("o:ListRecords", NS)
        rows = [r for r in (parse_record(x) for x in lr.findall("o:record", NS)) if r]
        with gzip.open(out_path, "at") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        tok = lr.find("o:resumptionToken", NS)
        ckpt["pages"] += 1
        ckpt["records"] += len(rows)
        ckpt["token"] = tok.text if tok is not None and tok.text else None
        ckpt["complete_list_size"] = tok.get("completeListSize") if tok is not None else None
        json.dump(ckpt, open(ckpt_path, "w"))
        print(f"page {ckpt['pages']}: +{len(rows)} (total {ckpt['records']} / {ckpt['complete_list_size']})", flush=True)
        if not ckpt["token"]:
            break
        time.sleep(PAUSE)
    ckpt["done"] = True
    json.dump(ckpt, open(ckpt_path, "w"))
    print("done:", ckpt["records"], "records ->", out_path)


if __name__ == "__main__":
    main()
