#!/usr/bin/env python3
"""Build missing_candidates.html: a self-contained viewer for missing_candidates.jsonl
that compares the three abstract-screen runs (Sonnet 5, Opus 5.5, Fable 5.1).

Rows are the 38,318 missing candidates plus the 1,920 hidden calibration papers, whose
full-text Codex outcome (accepted / rejected) is the reference answer. Each row shows the
decision and model_class from every run. A comparison panel counts the keep/drop patterns
across the three runs and scores each run on the calibration papers; clicking a pattern
filters the table. Full abstracts are kept for calibration papers and for candidates on
which the runs disagree; agreed candidates carry a snippet to keep the page small.
Decisions are read from screen_results*/ through screen_batches/keymap.jsonl, not from
the screen_decision field of missing_candidates.jsonl (which holds the Sonnet run only).
Rows that check_alignment.py flags as written against a neighbouring paper carry a warning.
"""
import glob, html, json, os, re

from compare_screens import load

HERE = os.path.dirname(os.path.abspath(__file__))
SNIPPET = 260
RUNS = (("Sonnet 5", "screen_results"), ("Opus 5.5", "screen_results_opus"), ("Fable 5.1", "screen_results_fable"))
CODE = {"NOVEL_MODEL": "N", "UNSURE": "U", "NOT_NOVEL_MODEL": "X"}


def id_date(aid):
    """Approximate YYYY-MM from an arXiv id (calibration papers carry no metadata here)."""
    m = re.search(r"(\d{2})(\d{2})[.\d]", aid.split("/")[-1])
    if not m:
        return ""
    yy, mm = int(m.group(1)), m.group(2)
    return f"{1900 + yy if yy > 90 else 2000 + yy}-{mm}"


def main():
    keymap = {json.loads(l)["key"]: json.loads(l) for l in open(os.path.join(HERE, "screen_batches", "keymap.jsonl"))}
    runs = [{k: v for rows in load(d).values() for k, v in rows.items()} for _, d in RUNS]
    by_id = {}
    for k, km in keymap.items():
        by_id[km["arxiv_id"] if not km["calibration"] else "cal:" + k] = k
    texts = {}
    for f in glob.glob(os.path.join(HERE, "screen_batches", "batch_*.jsonl")):
        for l in open(f):
            if l.strip():
                r = json.loads(l)
                if keymap[r["key"]]["calibration"]:
                    texts[r["key"]] = (r["title"], r["abstract"])

    fp = os.path.join(HERE, "alignment_flags.json")
    flags = json.load(open(fp)) if os.path.exists(fp) else {}
    flags = [flags.get(n, {}) for n, _ in RUNS]

    def screens(k):
        z = "".join(CODE.get(run.get(k, {}).get("decision"), "-") for run in runs)
        return z, [run.get(k, {}).get("model_class") or "" for run in runs], [fl.get(k, 0) for fl in flags]

    data = []
    for r in map(json.loads, open(os.path.join(HERE, "missing_candidates.jsonl"))):
        z, mc, w = screens(by_id.get(r["arxiv_id"], ""))
        agree = len(set(z)) == 1
        data.append({
            "i": r["arxiv_id"], "d": r["submitted"], "t": r["title"],
            "a": (r["abstract"] or "")[:SNIPPET] if agree else (r["abstract"] or ""), "f": int(not agree),
            "r": r["missing_reason"], "s": r["slice"], "p": r["primary_category"],
            "m": int(r["has_dark_matter_phrase"]), "c": r.get("inspire_citations"), "h": len(r["lexicon_hits"]),
            "z": z, "k": mc, "w": w, "g": "",
        })
    for k, km in keymap.items():
        if not km["calibration"]:
            continue
        t, a = texts.get(k, ("", ""))
        z, mc, w = screens(k)
        data.append({"i": km["arxiv_id"], "d": id_date(km["arxiv_id"]), "t": t, "a": a or "", "f": 1,
                     "r": "calibration", "s": "", "p": "", "m": int("dark matter" in (a or "").lower()),
                     "c": None, "h": 0, "z": z, "k": mc, "w": w, "g": km["calibration"]})

    n_cand = sum(1 for d in data if not d["g"])
    sub = (f"{n_cand:,} astro-ph / hep-ph papers matching the dark-matter lexicon that never entered the registry "
           f"corpus, plus {len(data) - n_cand:,} hidden calibration papers with a known full-text answer; "
           f"abstract-screen decisions from {', '.join(n for n, _ in RUNS)}")
    out = (TEMPLATE.replace("__SUB__", html.escape(sub))
           .replace("__RUNS__", json.dumps([n for n, _ in RUNS]))
           .replace("__DATA__", json.dumps(data, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/")))
    path = os.path.join(HERE, "missing_candidates.html")
    open(path, "w", encoding="utf-8").write(out)
    print(f"wrote {path} ({os.path.getsize(path) / 1e6:.1f} MB, {len(data):,} rows, "
          f"{sum(d['f'] for d in data if not d['g']):,} candidates with disagreement)")


TEMPLATE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Missing Paper Candidates</title>
<style>
  :root { --bg:#0f1115; --panel:#181b22; --panel-2:#20242d; --border:#2a2f3a; --text:#e6e8ee; --muted:#8a94a6;
          --a:#66a3ff; --b:#f5b041; --ok:#2ecc71; --bad:#ff6b6b; }
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
  .panel p.note { color:var(--muted); font-size:12px; margin:0 0 10px; }
  .grid2 { display:grid; grid-template-columns:minmax(0,3fr) minmax(0,2fr); gap:16px; }
  @media (max-width:900px) { .grid2 { grid-template-columns:1fr; } }
  .legend { display:flex; gap:16px; font-size:12px; color:var(--muted); margin-bottom:8px; flex-wrap:wrap; }
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
  th { color:var(--muted); font-weight:600; font-size:11px; text-transform:uppercase; letter-spacing:.04em; white-space:nowrap; user-select:none; }
  #main th[data-k] { cursor:pointer; }
  th.sorted::after { content:" ▾"; } th.sorted.asc::after { content:" ▴"; }
  td.num, th.num { text-align:right; font-variant-numeric:tabular-nums; }
  a { color:var(--a); text-decoration:none; } a:hover { text-decoration:underline; }
  .abs { color:var(--muted); font-size:12px; margin-top:2px; }
  .abs.full { color:#c4cad6; white-space:normal; }
  .more { color:var(--a); font-size:11px; cursor:pointer; background:none; border:0; padding:0; font:inherit; font-size:11px; }
  .pill { font-size:11px; padding:1px 7px; border-radius:10px; border:1px solid var(--border); white-space:nowrap; display:inline-block; }
  .pill.after_cutoff { color:var(--b); } .pill.not_in_corpus { color:var(--a); } .pill.calibration { color:#c39bff; }
  .pill.N { color:var(--ok); border-color:#2ecc7155; } .pill.U { color:var(--b); border-color:#f5b04155; } .pill.X { color:var(--muted); }
  .pill.acc { color:var(--ok); } .pill.rej { color:var(--bad); }
  td.scr { min-width:120px; } td.scr .abs { font-size:11px; }
  td.scr.odd { background:#f5b0410f; }
  .warn { color:var(--bad); font-size:11px; margin-top:2px; cursor:help; }
  .pat { font-family:ui-monospace,SFMono-Regular,Menlo,monospace; letter-spacing:.1em; }
  .pat .k { color:var(--ok); } .pat .d { color:#5b6475; }
  #pats tr { cursor:pointer; } #pats tr:hover td { background:var(--panel-2); } #pats tr.on td { background:#66a3ff22; }
  .bar { display:inline-block; height:8px; background:var(--a); border-radius:2px; vertical-align:middle; margin-right:6px; }
  .pager { display:flex; gap:8px; align-items:center; margin-top:12px; }
  .pager button { background:var(--panel); border:1px solid var(--border); color:var(--text); padding:5px 12px; border-radius:6px; cursor:pointer; font:inherit; }
  .pager button:disabled { opacity:.4; cursor:default; }
  @media (max-width:640px) { main, header { padding-left:16px; padding-right:16px; } .hide-sm { display:none; } }
</style></head>
<body>
<header><h1>Missing Paper Candidates</h1><div class="sub">__SUB__</div></header>
<main>
  <div class="cards" id="cards"></div>
  <div class="panel">
    <h2>How the three screens compare</h2>
    <p class="note">"Kept" = NOVEL_MODEL or UNSURE. Calibration papers are registry papers hidden in the batches; Codex's full-text triage says whether each really introduces a model, so recall = accepted papers kept and false positives = rejected papers kept. Click a pattern to list its papers below. A few decisions were written against a neighbouring paper (see <code>alignment_report.md</code>); they are marked ⚠ and can be listed with the "Suspected row shift" filter.</p>
    <div class="grid2">
      <div class="tablewrap"><table><thead><tr><th>Kept by (<span id="runhdr"></span>)</th><th class="num">Candidates</th><th class="num">Calib. accepted</th><th class="num">Calib. rejected</th></tr></thead><tbody id="pats"></tbody></table></div>
      <div class="tablewrap"><table><thead><tr><th>Screen</th><th class="num">Recall</th><th class="num">False pos.</th><th class="num">Candidates kept</th></tr></thead><tbody id="score"></tbody></table></div>
    </div>
  </div>
  <div class="panel"><h2>Candidates per year of first submission</h2>
    <div class="legend"><span><span class="sw" style="background:var(--a)"></span>not in corpus</span><span><span class="sw" style="background:var(--b)"></span>after cutoff (≥ 2024-06)</span></div>
    <div id="years"></div></div>
  <div class="panel">
    <div class="filters">
      <input type="search" id="q" placeholder="Search id, title, abstract, model class…">
      <select id="set"><option value="cand">Missing candidates</option><option value="cal">Calibration papers</option><option value="cal-acc">Calibration: Codex accepted</option><option value="cal-rej">Calibration: Codex rejected</option><option value="">Both</option></select>
      <select id="agree"><option value="">Any agreement</option><option value="dis">Labels differ</option><option value="kdis">Keep/drop differs</option><option value="same">All three identical</option><option value="shift">Suspected row shift</option></select>
      <select id="pat"><option value="">Any keep/drop pattern</option></select>
      <select id="r0"></select><select id="r1"></select><select id="r2"></select>
      <select id="reason"><option value="">All reasons</option><option value="not_in_corpus">Not in corpus</option><option value="after_cutoff">After cutoff</option></select>
      <select id="slice"><option value="">Both slices</option><option value="astro-ph">astro-ph</option><option value="hep-ph">hep-ph only</option></select>
      <label><input type="checkbox" id="dm"> "dark matter" in abstract</label>
      <label>min cites <input type="number" id="mc" min="0" value="0" style="width:80px"></label>
      <span class="count" id="count"></span>
    </div>
    <div class="tablewrap"><table id="main"><thead><tr id="mainhead"></tr></thead><tbody id="tb"></tbody></table></div>
    <div class="pager"><button id="prev">Prev</button><span class="count" id="page"></span><button id="next">Next</button></div>
  </div>
</main>
<script>
const RUNS = __RUNS__;
const D = __DATA__;
const $ = id => document.getElementById(id);
const fmt = n => n.toLocaleString();
const pct = (a, b) => b ? (100 * a / b).toFixed(1) + "%" : "—";
const esc = s => (s||"").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const LBL = {N:"novel", U:"unsure", X:"not novel", "-":"—"};
const kept = c => c === "N" || c === "U";
const kpat = z => [...z].map(c => kept(c) ? "K" : "D").join("");
for (const r of D) r.kp = kpat(r.z);
const CAND = D.filter(r => !r.g), CAL = D.filter(r => r.g);
const short = n => n.split(" ")[0];

function header() {
  $("runhdr").textContent = RUNS.map(short).join(" · ");
  $("mainhead").innerHTML = `<th data-k="i">arXiv id</th><th data-k="d" class="sorted">Submitted</th><th data-k="t">Title / abstract</th><th data-k="r">Set</th>` +
    RUNS.map((n, j) => `<th data-k="z${j}">${esc(n)}</th>`).join("") +
    `<th data-k="c" class="num">Cites</th>`;
  RUNS.forEach((n, j) => { $("r" + j).innerHTML = `<option value="">${esc(short(n))}: any</option>` +
    ["N","U","X"].map(c => `<option value="${c}">${esc(short(n))}: ${LBL[c]}</option>`).join("") + `<option value="K">${esc(short(n))}: kept</option>`; });
}
function patLabel(p) { return p.split("").map((c, j) => `<span class="${c==="K"?"k":"d"}">${c==="K"?"✓":"✗"}</span>`).join(" "); }
function compare() {
  const pats = {};
  for (const r of D) { const o = pats[r.kp] = pats[r.kp] || {c:0, a:0, x:0}; if (!r.g) o.c++; else if (r.g === "accepted") o.a++; else o.x++; }
  const order = Object.keys(pats).sort((p, q) => (q.split("K").length - p.split("K").length) || (pats[q].c - pats[p].c));
  const mx = Math.max(...order.map(p => pats[p].c));
  $("pats").innerHTML = order.map(p => `<tr data-p="${p}"><td class="pat">${patLabel(p)}</td>
    <td class="num"><span class="bar" style="width:${60*pats[p].c/mx}px"></span>${fmt(pats[p].c)}</td><td class="num">${fmt(pats[p].a)}</td><td class="num">${fmt(pats[p].x)}</td></tr>`).join("");
  $("pat").innerHTML = `<option value="">Any keep/drop pattern</option>` + order.map(p =>
    `<option value="${p}">${p.split("").map((c,j)=>short(RUNS[j]) + (c==="K"?" keeps":" drops")).join(", ")}</option>`).join("");
  document.querySelectorAll("#pats tr").forEach(tr => tr.onclick = () => {
    const p = tr.dataset.p, on = $("pat").value === p;
    $("pat").value = on ? "" : p; $("agree").value = "";
    if (!on && $("set").value === "") $("set").value = "cand";
    apply(); $("main").scrollIntoView({behavior:"smooth"});
  });
  const acc = CAL.filter(r => r.g === "accepted"), rej = CAL.filter(r => r.g === "rejected");
  const scr = (name, f) => `<tr><td>${name}</td><td class="num">${pct(acc.filter(f).length, acc.length)}</td><td class="num">${pct(rej.filter(f).length, rej.length)}</td><td class="num">${fmt(CAND.filter(f).length)}</td></tr>`;
  const K = j => r => kept(r.z[j]);
  $("score").innerHTML = RUNS.map((n, j) => scr(esc(n), K(j))).join("") +
    scr(`${short(RUNS[1])} ∪ ${short(RUNS[2])}`, r => K(1)(r) || K(2)(r)) +
    scr("≥ 2 of 3", r => [0,1,2].filter(j => K(j)(r)).length >= 2) +
    scr("any of 3", r => [0,1,2].some(j => K(j)(r))) +
    `<tr><td colspan="4" class="abs">n = ${fmt(acc.length)} accepted, ${fmt(rej.length)} rejected calibration papers</td></tr>`;
}
function cards() {
  const n = f => CAND.filter(f).length;
  const cs = [["Candidates", CAND.length], ["Kept by any screen", n(r => r.kp.includes("K"))], ["Kept by all three", n(r => !r.kp.includes("D"))],
    ["Labels differ", n(r => new Set(r.z).size > 1)], ["Keep/drop differs", n(r => r.kp.includes("K") && r.kp.includes("D"))],
    ["Calibration papers", CAL.length], ["Suspected row shifts", D.filter(r => r.w.some(x => x)).length], ["Not in corpus", n(r=>r.r==="not_in_corpus")], ["After cutoff", n(r=>r.r==="after_cutoff")]];
  $("cards").innerHTML = cs.map(([l,v]) => `<div class="card"><div class="label">${l}</div><div class="value">${fmt(v)}</div></div>`).join("");
  const by = {};
  for (const r of CAND) { const y=(r.d||"????").slice(0,4); by[y] = by[y] || {n:0,a:0}; by[y][r.r==="after_cutoff"?"a":"n"]++; }
  const ys = Object.keys(by).sort(), mx = Math.max(...ys.map(y => by[y].n + by[y].a));
  $("years").innerHTML = ys.map(y => { const b = by[y];
    return `<div class="yr"><span>${y}</span><div class="track"><div style="width:${100*b.n/mx}%;background:var(--a)"></div><div style="width:${100*b.a/mx}%;background:var(--b)"></div></div><span class="n">${fmt(b.n+b.a)}</span></div>`; }).join("");
}
let sortK = "d", asc = false, page = 0, rows = CAND;
const PER = 100;
const val = (r, k) => k[0] === "z" && k.length === 2 ? "NUX-".indexOf(r.z[+k[1]]) : r[k];
function apply() {
  const q = $("q").value.trim().toLowerCase(), set = $("set").value, ag = $("agree").value, pt = $("pat").value;
  const rs = [0,1,2].map(j => $("r" + j).value);
  const re = $("reason").value, sl = $("slice").value, dm = $("dm").checked, mc = +$("mc").value || 0;
  rows = D.filter(r =>
    (set === "" || (set === "cand" ? !r.g : set === "cal" ? r.g : r.g === (set === "cal-acc" ? "accepted" : "rejected"))) &&
    (!ag || (ag === "shift" ? r.w.some(x => x) : ag === "dis" ? new Set(r.z).size > 1 : ag === "same" ? new Set(r.z).size === 1 : (r.kp.includes("K") && r.kp.includes("D")))) &&
    (!pt || r.kp === pt) &&
    rs.every((v, j) => !v || (v === "K" ? kept(r.z[j]) : r.z[j] === v)) &&
    (!re || r.r === re) && (!sl || r.s === sl) && (!dm || r.m) && ((r.c||0) >= mc) &&
    (!q || r.i.includes(q) || (r.t||"").toLowerCase().includes(q) || (r.a||"").toLowerCase().includes(q) || r.k.some(x => x.toLowerCase().includes(q))));
  rows.sort((x, y) => { const a = val(x, sortK) ?? -1, b = val(y, sortK) ?? -1; return (a < b ? -1 : a > b ? 1 : 0) * (asc ? 1 : -1); });
  document.querySelectorAll("#pats tr").forEach(tr => tr.classList.toggle("on", tr.dataset.p === pt));
  page = 0; render();
}
function setPill(r) {
  if (r.g) return `<span class="pill calibration">calibration</span><div class="abs"><span class="pill ${r.g==="accepted"?"acc":"rej"}">Codex ${r.g}</span></div>`;
  return `<span class="pill ${r.r}">${r.r.replace(/_/g," ")}</span>`;
}
function render() {
  const n = rows.length, pages = Math.max(1, Math.ceil(n / PER));
  $("count").textContent = `${fmt(n)} shown`;
  $("page").textContent = `page ${page+1} / ${pages}`;
  $("prev").disabled = page === 0; $("next").disabled = page >= pages - 1;
  $("tb").innerHTML = rows.slice(page*PER, (page+1)*PER).map((r, ix) => {
    const counts = {}; for (const c of r.z) counts[c] = (counts[c]||0) + 1;
    const long = r.a.length > 320;
    return `<tr>
    <td><a href="https://arxiv.org/abs/${r.i}" target="_blank" rel="noopener">${r.i}</a></td><td>${r.d||""}</td>
    <td>${esc(r.t)}<div class="abs${r.f?" full":""}" data-full="${long?1:0}">${esc(long ? r.a.slice(0, 320) + "…" : r.a + (r.f ? "" : "…"))}</div>${long?`<button class="more" data-ix="${page*PER+ix}">show full abstract</button>`:""}</td>
    <td>${setPill(r)}</td>
    ${[0,1,2].map(j => { const c = r.z[j]; return `<td class="scr${Object.keys(counts).length > 1 && counts[c] === 1 ? " odd" : ""}"><span class="pill ${c}">${LBL[c]}</span>${r.w[j]?`<div class="warn" title="check_alignment.py: this run's decisions around here were written against the paper ${r.w[j]>0?"+":""}${r.w[j]} row(s) away">⚠ row shift ${r.w[j]>0?"+":""}${r.w[j]}</div>`:""}${r.k[j]?`<div class="abs">${esc(r.k[j])}</div>`:""}</td>`; }).join("")}
    <td class="num">${r.c==null?"—":fmt(r.c)}</td></tr>`; }).join("");
  document.querySelectorAll("button.more").forEach(b => b.onclick = () => {
    const r = rows[+b.dataset.ix], div = b.previousElementSibling;
    const open = b.textContent.startsWith("show");
    div.textContent = open ? r.a : r.a.slice(0, 320) + "…"; b.textContent = open ? "hide" : "show full abstract";
  });
}
header(); compare(); cards();
document.querySelectorAll("#main th[data-k]").forEach(th => th.onclick = () => {
  const k = th.dataset.k; asc = sortK === k ? !asc : (k === "i" || k === "t" || k === "r" || k[0] === "z"); sortK = k;
  document.querySelectorAll("#main th").forEach(t => t.classList.remove("sorted", "asc"));
  th.classList.add("sorted"); if (asc) th.classList.add("asc"); apply();
});
["q","set","agree","pat","r0","r1","r2","reason","slice","dm","mc"].forEach(id => $(id).addEventListener("input", apply));
$("prev").onclick = () => { page--; render(); window.scrollTo({top: $("main").offsetTop - 80}); };
$("next").onclick = () => { page++; render(); window.scrollTo({top: $("main").offsetTop - 80}); };
apply();
</script></body></html>
"""

if __name__ == "__main__":
    main()
