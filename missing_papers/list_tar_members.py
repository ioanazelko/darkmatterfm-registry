"""List the members of remote WebDataset .tar shards on Hugging Face without downloading them.

Walks the tar headers with HTTP range requests (512 bytes per member, then skips the
member body), so a 3 GB shard costs about one small request per paper.

Usage: python3 list_tar_members.py Smith42/minty-astro-ph 'data/astro-ph-{00000..00286}.tar' out.jsonl
Or pass @shards.txt (one path per line) in place of the pattern.
Output: one row per member {shard, name, size}. Resumable: shards already in out.jsonl are skipped.
"""
import concurrent.futures as cf, json, os, re, sys, threading, time, urllib.request

import requests

UA = {"User-Agent": "darkmatterfm-registry-manifest/0.1"}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


def cdn_url(repo, path):
    """Resolve the HF file once to its signed CDN URL (reused for every range read)."""
    url = f"https://huggingface.co/datasets/{repo}/resolve/main/{path}"
    opener = urllib.request.build_opener(NoRedirect)
    for attempt in range(6):
        try:
            opener.open(urllib.request.Request(url, method="HEAD", headers=UA), timeout=60)
        except urllib.error.HTTPError as e:
            if e.code in (301, 302, 303, 307, 308):
                return e.headers["Location"], int(e.headers.get("X-Linked-Size") or 0)
            raise
        except (urllib.error.URLError, OSError):  # timeouts and dropped TLS handshakes
            if attempt == 5:
                raise
            time.sleep(5 * (attempt + 1))
            continue
        raise RuntimeError("no redirect for " + url)


WINDOW = 64 << 10  # bytes per range request: covers a header plus a typical .json member; big members are jumped over
_local = threading.local()


def session():
    if not hasattr(_local, "s"):
        _local.s = requests.Session()
        _local.s.headers.update(UA)
    return _local.s


def read_range(url, start, n):
    for attempt in range(6):
        try:
            r = session().get(url, headers={"Range": f"bytes={start}-{start + n - 1}"}, timeout=120)
            r.raise_for_status()
            return r.content
        except Exception:
            if attempt == 5:
                raise
            time.sleep(5 * (attempt + 1))


class Reader:
    """Serves byte ranges from a cached window, refetching only when a request falls outside it."""

    def __init__(self, url, total):
        self.url, self.total, self.buf_start, self.buf = url, total, 0, b""

    def get(self, start, n):
        if not (self.buf_start <= start and start + n <= self.buf_start + len(self.buf)):
            self.buf_start = start
            self.buf = read_range(self.url, start, max(n, min(WINDOW, self.total - start)))
        o = start - self.buf_start
        return self.buf[o:o + n]


def parse_pax(data):
    out, i = {}, 0
    while i < len(data):
        sp = data.index(b" ", i)
        ln = int(data[i:sp])
        k, _, v = data[sp + 1:i + ln - 1].partition(b"=")
        out[k.decode()] = v.decode("utf-8", "replace")
        i += ln
    return out


def walk(repo, path):
    url, total = cdn_url(repo, path)
    rd = Reader(url, total)
    pos, rows, pax = 0, [], {}
    while pos + 512 <= total:
        h = rd.get(pos, 512)
        if h.strip(b"\0") == b"":
            break
        name = h[0:100].rstrip(b"\0").decode("utf-8", "replace")
        prefix = h[345:500].rstrip(b"\0").decode("utf-8", "replace")
        size_field = h[124:136].rstrip(b"\0 ").decode() or "0"
        size = int(size_field, 8)
        typ = h[156:157]
        body = pos + 512
        if typ in (b"x", b"g"):  # pax extended header applies to the next member
            pax = parse_pax(rd.get(body, size)) if typ == b"x" else pax
        else:
            full = pax.get("path") or (prefix + "/" + name if prefix else name)
            rows.append({"shard": path, "name": full, "size": int(pax.get("size", size))})
            size = int(pax.get("size", size))
            pax = {}
        pos = body + ((size + 511) // 512) * 512
    return rows


def expand(pattern):
    m = re.search(r"\{(\d+)\.\.(\d+)\}", pattern)
    if not m:
        return [pattern]
    a, b = m.group(1), m.group(2)
    return [pattern[:m.start()] + str(i).zfill(len(a)) + pattern[m.end():] for i in range(int(a), int(b) + 1)]


def main():
    repo, pattern, out = sys.argv[1], sys.argv[2], sys.argv[3]
    if pattern.startswith("@"):  # @file: one shard path per line (too many for one argv string)
        paths = [l.strip() for l in open(pattern[1:]) if l.strip()]
    else:
        paths = expand(pattern) if "{" in pattern else [p for p in pattern.split(",")]
    done = set()
    if os.path.exists(out):
        done = {json.loads(l)["shard"] for l in open(out)}
    todo = [p for p in paths if p not in done]
    print(f"{len(todo)} shards to list ({len(done)} done)", flush=True)
    with cf.ThreadPoolExecutor(max_workers=int(os.environ.get("MANIFEST_WORKERS", 16))) as ex, open(out, "a") as f:
        futs = {ex.submit(walk, repo, p): p for p in todo}
        for fut in cf.as_completed(futs):
            p = futs[fut]
            try:
                rows = fut.result()
            except Exception as e:
                print(f"FAILED {p}: {e}", flush=True)
                continue
            for r in rows:
                f.write(json.dumps(r) + "\n")
            f.flush()
            print(f"{p}: {len(rows)} members", flush=True)


if __name__ == "__main__":
    main()
