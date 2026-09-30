#!/usr/bin/env python3
"""Build missing_candidates.html: a self-contained viewer for missing_candidates.jsonl.

Stat cards, candidates per year (stacked by reason), filters (text, reason, slice,
"dark matter" phrase, minimum INSPIRE citations) and a sortable, paginated table.
Abstracts are cut to a snippet to keep the page small; each id links to arXiv.
"""
import html, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
SNIPPET = 260


def main():
    rows = [json.loads(l) for l in open(os.path.join(HERE, "missing_candidates.jsonl"))]
    data = [{
        "i": r["arxiv_id"], "d": r["submitted"], "t": r["title"],
        "a": (r["abstract"] or "")[:SNIPPET], "r": r["missing_reason"], "s": r["slice"],
        "p": r["primary_category"], "m": int(r["has_dark_matter_phrase"]),
        "c": r.get("inspire_citations"), "y": ",".join(r.get("document_type") or []),
        "h": len(r["lexicon_hits"]), "z": r.get("screen_decision") or "", "k": r.get("screen_model_class") or "",
    } for r in rows]
    sub = f"{len(rows):,} astro-ph / hep-ph papers matching the dark-matter lexicon that never entered the registry corpus"
    out = TEMPLATE.replace("__SUB__", html.escape(sub)).replace(
        "__DATA__", json.dumps(data, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/"))
    path = os.path.join(HERE, "missing_candidates.html")
    open(path, "w", encoding="utf-8").write(out)
    print(f"wrote {path} ({os.path.getsize(path) / 1e6:.1f} MB, {len(rows):,} rows)")


TEMPLATE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Missing Paper Candidates</title>
<style>
  :root { --bg:#0f1115; --panel:#181b22; --panel-2:#20242d; --border:#2a2f3a; --text:#e6e8ee; --muted:#8a94a6;
          --a:#66a3ff; --b:#f5b041; --ok:#2ecc71; }
  * { box-sizing: border-box; }
  body { margin:0; font:14px/1.45 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif; background:var(--bg); color:var(--text); }
  header { padding:20px 24px 12px; border-bottom:1px solid var(--border); }
  header h1 { margin:0 0 4px; font-size:18px; font-weight:600; } header .sub { color:var(--muted); font-size:12px; }
  main { padding:16px 24px 80px; }
  .cards { display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:12px; margin-bottom:20px; }
  .card { background:var(--panel); border:1px solid var(--border); border-radius:8px; padding:12px 14px; }
  .card .label { color:var(--muted); font-size:11px; text-transform:uppercase; letter-spacing:.05em; }
  .card .value { font-size:22px; font-weight:600; margin-top:4px; font-variant-numeric:tabular-nums; }
  .panel { background:var(--panel); border:1px solid var(--border); border-radius:8px; padding:14px 16px; margin-bottom:16px; }
  .panel h2 { margin:0 0 10px; font-size:13px; font-weight:600; color:var(--muted); text-transform:uppercase; letter-spacing:.05em; }
  .legend { display:flex; gap:16px; font-size:12px; color:var(--muted); margin-bottom:8px; }
  .sw { display:inline-block; width:10px; height:10px; border-radius:2px; margin-right:5px; vertical-align:-1px; }
  .yr { display:grid; grid-template-columns:44px 1fr 60px; gap:8px; align-items:center; font-size:12px; margin:2px 0; }
  .track { background:var(--panel-2); height:10px; border-radius:4px; overflow:hidden; display:flex; }
  .yr .n { text-align:right; color:var(--muted); font-variant-numeric:tabular-nums; }
  .filters { display:flex; flex-wrap:wrap; gap:10px; align-items:center; margin-bottom:12px; }
  .filters input, .filters select { background:var(--panel); border:1px solid var(--border); color:var(--text); padding:7px 10px; border-radius:6px; font:inherit; }
  .filters input[type=search] { flex:1 1 260px; min-width:0; }
  .filters label { color:var(--muted); font-size:12px; display:flex; gap:6px; align-items:center; }
  .count { color:var(--muted); font-size:12px; }
  .tablewrap { overflow-x:auto; }
  table { width:100%; border-collapse:collapse; font-size:13px; }
  th, td { text-align:left; padding:7px 8px; border-bottom:1px solid var(--border); vertical-align:top; }
  th { color:var(--muted); font-weight:600; font-size:11px; text-transform:uppercase; letter-spacing:.04em; cursor:pointer; white-space:nowrap; user-select:none; }
  th.sorted::after { content:" ▾"; } th.sorted.asc::after { content:" ▴"; }
  td.num { text-align:right; font-variant-numeric:tabular-nums; }
  a { color:var(--a); text-decoration:none; } a:hover { text-decoration:underline; }
  .abs { color:var(--muted); font-size:12px; margin-top:2px; }
  .pill { font-size:11px; padding:1px 7px; border-radius:10px; border:1px solid var(--border); white-space:nowrap; }
  .pill.after_cutoff { color:var(--b); } .pill.not_in_corpus { color:var(--a); }
  .pill.scr-NOVEL_MODEL { color:var(--ok); } .pill.scr-UNSURE { color:var(--b); } .pill.scr-NOT_NOVEL_MODEL { color:var(--muted); }
  .pager { display:flex; gap:8px; align-items:center; margin-top:12px; }
  .pager button { background:var(--panel); border:1px solid var(--border); color:var(--text); padding:5px 12px; border-radius:6px; cursor:pointer; font:inherit; }
  .pager button:disabled { opacity:.4; cursor:default; }
  @media (max-width:640px) { main, header { padding-left:16px; padding-right:16px; } .hide-sm { display:none; } }
</style></head>
<body>
<header><h1>Missing Paper Candidates</h1><div class="sub">__SUB__</div></header>
<main>
  <div class="cards" id="cards"></div>
  <div class="panel"><h2>Candidates per year of first submission</h2>
    <div class="legend"><span><span class="sw" style="background:var(--a)"></span>not in corpus</span><span><span class="sw" style="background:var(--b)"></span>after cutoff (≥ 2024-06)</span></div>
    <div id="years"></div></div>
  <div class="panel">
    <div class="filters">
      <input type="search" id="q" placeholder="Search id, title, abstract…">
      <select id="reason"><option value="">All reasons</option><option value="not_in_corpus">Not in corpus</option><option value="after_cutoff">After cutoff</option></select>
      <select id="slice"><option value="">Both slices</option><option value="astro-ph">astro-ph</option><option value="hep-ph">hep-ph only</option></select>
      <select id="scr"><option value="">Any screen</option><option value="KEEP">Novel or unsure</option><option value="NOVEL_MODEL">Novel model</option><option value="UNSURE">Unsure</option><option value="NOT_NOVEL_MODEL">Not novel</option><option value="NONE">Not screened</option></select>
      <label><input type="checkbox" id="dm"> "dark matter" in abstract</label>
      <label>min cites <input type="number" id="mc" min="0" value="0" style="width:80px"></label>
      <span class="count" id="count"></span>
    </div>
    <div class="tablewrap"><table><thead><tr>
      <th data-k="i">arXiv id</th><th data-k="d" class="sorted">Submitted</th><th data-k="t">Title</th>
      <th data-k="r">Reason</th><th data-k="z">Screen</th><th data-k="p" class="hide-sm">Primary</th><th data-k="c">Cites</th><th data-k="h" class="hide-sm">Hits</th>
    </tr></thead><tbody id="tb"></tbody></table></div>
    <div class="pager"><button id="prev">Prev</button><span class="count" id="page"></span><button id="next">Next</button></div>
  </div>
</main>
<script>
const D = __DATA__;
const $ = id => document.getElementById(id);
const fmt = n => n.toLocaleString();
const esc = s => (s||"").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
function cards() {
  const n = (f) => D.filter(f).length;
  const cs = [["Candidates", D.length], ["Screened novel / unsure", n(r=>r.z==="NOVEL_MODEL"||r.z==="UNSURE")], ["Not in corpus", n(r=>r.r==="not_in_corpus")], ["After cutoff", n(r=>r.r==="after_cutoff")],
    ["astro-ph", n(r=>r.s==="astro-ph")], ["hep-ph only", n(r=>r.s==="hep-ph")], ['"dark matter" in abstract', n(r=>r.m)]];
  $("cards").innerHTML = cs.map(([l,v]) => `<div class="card"><div class="label">${l}</div><div class="value">${fmt(v)}</div></div>`).join("");
  const by = {};
  for (const r of D) { const y=(r.d||"????").slice(0,4); by[y] = by[y] || {n:0,a:0}; by[y][r.r==="after_cutoff"?"a":"n"]++; }
  const ys = Object.keys(by).sort(), mx = Math.max(...ys.map(y => by[y].n + by[y].a));
  $("years").innerHTML = ys.map(y => { const b = by[y];
    return `<div class="yr"><span>${y}</span><div class="track"><div style="width:${100*b.n/mx}%;background:var(--a)"></div><div style="width:${100*b.a/mx}%;background:var(--b)"></div></div><span class="n">${fmt(b.n+b.a)}</span></div>`; }).join("");
}
let sortK = "d", asc = false, page = 0, rows = D;
const PER = 200;
function apply() {
  const sc = $("scr").value;
  const q = $("q").value.trim().toLowerCase(), re = $("reason").value, sl = $("slice").value, dm = $("dm").checked, mc = +$("mc").value || 0;
  rows = D.filter(r => (!sc || (sc==="KEEP" ? (r.z==="NOVEL_MODEL"||r.z==="UNSURE") : sc==="NONE" ? !r.z : r.z===sc)) && (!re || r.r===re) && (!sl || r.s===sl) && (!dm || r.m) && ((r.c||0) >= mc) &&
    (!q || r.i.includes(q) || (r.t||"").toLowerCase().includes(q) || (r.a||"").toLowerCase().includes(q) || r.k.toLowerCase().includes(q)));
  rows.sort((x, y) => { const a = x[sortK] ?? -1, b = y[sortK] ?? -1; return (a < b ? -1 : a > b ? 1 : 0) * (asc ? 1 : -1); });
  page = 0; render();
}
function render() {
  const n = rows.length, pages = Math.max(1, Math.ceil(n / PER));
  $("count").textContent = `${fmt(n)} shown`;
  $("page").textContent = `page ${page+1} / ${pages}`;
  $("prev").disabled = page === 0; $("next").disabled = page >= pages - 1;
  $("tb").innerHTML = rows.slice(page*PER, (page+1)*PER).map(r => `<tr>
    <td><a href="https://arxiv.org/abs/${r.i}" target="_blank" rel="noopener">${r.i}</a></td><td>${r.d||""}</td>
    <td>${esc(r.t)}<div class="abs">${esc(r.a)}…</div></td>
    <td><span class="pill ${r.r}">${r.r.replace(/_/g," ")}</span></td>
    <td>${r.z?`<span class="pill scr-${r.z}">${r.z.replace(/_MODEL$/,"").replace(/_/g," ").toLowerCase()}</span>`:""}${r.k?`<div class="abs">${esc(r.k)}</div>`:""}</td><td class="hide-sm">${r.p||""}</td>
    <td class="num">${r.c==null?"—":fmt(r.c)}</td><td class="num hide-sm">${r.h}</td></tr>`).join("");
}
document.querySelectorAll("th").forEach(th => th.onclick = () => {
  const k = th.dataset.k; asc = sortK === k ? !asc : (k === "i" || k === "t" || k === "p"); sortK = k;
  document.querySelectorAll("th").forEach(t => t.classList.remove("sorted", "asc"));
  th.classList.add("sorted"); if (asc) th.classList.add("asc"); apply();
});
["q","reason","scr","slice","dm","mc"].forEach(id => $(id).addEventListener("input", apply));
$("prev").onclick = () => { page--; render(); }; $("next").onclick = () => { page++; render(); };
cards(); apply();
</script></body></html>
"""

if __name__ == "__main__":
    main()
