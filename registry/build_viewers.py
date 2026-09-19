#!/usr/bin/env python3
"""Build three self-contained HTML viewers:

  * ranking.html            — models/ranking_full_ranked.jsonl
  * enrichment_status.html  — models/enrichment_all_paper_status.jsonl
  * enrichment_outputs.html — models/enrichment_all_outputs.jsonl

With --hosted, build instead the hosted variant of the wiki for web mirrors
that refuse a 62 MB page: hosted/darkmatterwiki.html embeds only the ~3 MB
index and fetches each card's detail subtree on demand from
hosted/darkmatterwiki_data/shard-XX.json (256 shards keyed by a hash of
model_id). Serve the hosted/ directory over HTTP; file:// will not work.
"""

import html
import json
import sys
from pathlib import Path

REGISTRY = Path(__file__).resolve().parent

SHARED_CSS = """
  :root {
    --bg: #0f1115; --panel: #181b22; --panel-2: #20242d; --border: #2a2f3a;
    --text: #e6e8ee; --muted: #8a94a6;
    --accept: #2ecc71; --reject: #ff6b6b; --warn: #f5b041; --accent: #66a3ff;
    --tier2: #2ecc71; --tier3: #66a3ff; --defer: #8a94a6; --rejected: #ff6b6b;
  }
  * { box-sizing: border-box; }
  body { margin: 0; font: 14px/1.45 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: var(--bg); color: var(--text); }
  header { padding: 20px 24px 12px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: flex-end; }
  header h1 { margin: 0 0 4px; font-size: 18px; font-weight: 600; }
  header .sub { color: var(--muted); font-size: 12px; }
  header nav { display: flex; gap: 14px; }
  header nav a { color: var(--muted); text-decoration: none; font-size: 12px; padding: 4px 8px; border: 1px solid var(--border); border-radius: 6px; }
  header nav a.active { color: var(--text); border-color: var(--accent); }
  header nav a:hover { color: var(--text); }
  main { padding: 16px 24px 80px; }
  .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; margin-bottom: 20px; }
  .card { background: var(--panel); border: 1px solid var(--border); border-radius: 8px; padding: 12px 14px; }
  .card .label { color: var(--muted); font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; }
  .card .value { font-size: 22px; font-weight: 600; margin-top: 4px; }
  .card.accept .value { color: var(--accept); }
  .card.reject .value { color: var(--reject); }
  .card.warn   .value { color: var(--warn); }
  .panel-row { display: grid; gap: 16px; grid-template-columns: repeat(auto-fit, minmax(360px, 1fr)); margin-bottom: 16px; }
  .panel { background: var(--panel); border: 1px solid var(--border); border-radius: 8px; padding: 14px 16px; }
  .panel h2 { margin: 0 0 10px; font-size: 13px; font-weight: 600; color: var(--muted); text-transform: uppercase; letter-spacing: 0.05em; display: flex; justify-content: space-between; align-items: center; }
  .panel h2 .legend { font-size: 11px; color: var(--muted); text-transform: none; letter-spacing: 0; }
  .bars { display: grid; gap: 4px; }
  .bar-row { display: grid; grid-template-columns: minmax(160px, 220px) 1fr 70px; gap: 8px; align-items: center; font-size: 12px; }
  .bar-row .name { color: var(--text); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .bar-row .name.muted { color: var(--muted); }
  .bar-track { background: var(--panel-2); height: 10px; border-radius: 4px; overflow: hidden; display: flex; }
  .bar-fill { height: 100%; background: var(--accent); }
  .bar-fill.accept { background: var(--accept); }
  .bar-fill.reject { background: var(--reject); }
  .bar-fill.warn { background: var(--warn); }
  .bar-fill.tier2 { background: var(--tier2); }
  .bar-fill.tier3 { background: var(--tier3); }
  .bar-fill.defer { background: var(--defer); }
  .bar-fill.rejected { background: var(--rejected); }
  .bar-row .count { text-align: right; color: var(--muted); font-variant-numeric: tabular-nums; }
  .bar-row.clickable { cursor: pointer; }
  .bar-row.clickable:hover .name { color: var(--accent); }
  .filters { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; margin-bottom: 12px; }
  .filters input, .filters select {
    background: var(--panel); border: 1px solid var(--border); color: var(--text);
    padding: 7px 10px; border-radius: 6px; font: inherit;
  }
  .filters input[type="search"] { min-width: 260px; }
  .filters .meta { color: var(--muted); font-size: 12px; margin-left: auto; }
  table { width: 100%; border-collapse: collapse; background: var(--panel); border: 1px solid var(--border); border-radius: 8px; overflow: hidden; }
  th, td { padding: 8px 12px; text-align: left; border-bottom: 1px solid var(--border); vertical-align: top; }
  th { background: var(--panel-2); cursor: pointer; user-select: none; font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; color: var(--muted); position: sticky; top: 0; }
  th .arrow { opacity: 0.4; font-size: 10px; }
  th.sorted .arrow { opacity: 1; color: var(--accent); }
  tbody tr:hover { background: rgba(255,255,255,0.02); }
  tbody tr.expandable { cursor: pointer; }
  tbody tr.detail-row td { background: var(--panel-2); padding: 0; }
  tbody tr.detail-row .detail-pane { padding: 12px 16px; }
  tbody tr.detail-row pre { margin: 0; max-height: 480px; overflow: auto; background: var(--bg); padding: 12px; border-radius: 6px; font-size: 11px; }
  td.mono { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 12px; }
  td.paper { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 12px; color: var(--accent); }
  td.muted { color: var(--muted); }
  td.num { text-align: right; font-variant-numeric: tabular-nums; }
  td.reason { color: var(--text); max-width: 600px; }
  .pill { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; }
  .pill.tier2 { background: rgba(46, 204, 113, 0.18); color: var(--tier2); }
  .pill.tier3 { background: rgba(102, 163, 255, 0.18); color: var(--tier3); }
  .pill.defer { background: rgba(138, 148, 166, 0.18); color: var(--defer); }
  .pill.rejected { background: rgba(255, 107, 107, 0.18); color: var(--rejected); }
  .pill.completed { background: rgba(46, 204, 113, 0.18); color: var(--accept); }
  .pill.error { background: rgba(255, 107, 107, 0.18); color: var(--reject); }
  .pill.pending { background: rgba(245, 176, 65, 0.18); color: var(--warn); }
  .pager { display: flex; justify-content: space-between; align-items: center; margin-top: 12px; color: var(--muted); font-size: 12px; }
  .pager button { background: var(--panel); border: 1px solid var(--border); color: var(--text); padding: 6px 12px; border-radius: 6px; cursor: pointer; font: inherit; }
  .pager button:disabled { opacity: 0.4; cursor: not-allowed; }
"""

NAV_HTML = """
  <nav>
    <a href="paper_status.html">paper status</a>
    <a href="darkmatterwiki.html" data-page="darkmatterwiki">darkmatterwiki</a>
    <a href="ranking.html" data-page="ranking">ranking</a>
    <a href="enrichment_status.html" data-page="enrichment_status">enrichment status</a>
    <a href="enrichment_outputs.html" data-page="enrichment_outputs">enrichment outputs</a>
  </nav>
"""


def shell(title: str, subtitle: str, page_id: str, panels_html: str, table_html: str, app_js: str, data_json: str, extra_css: str = "") -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{html.escape(title)}</title>
<style>{SHARED_CSS}{extra_css}</style>
</head>
<body>
<header>
  <div>
    <h1>{html.escape(title)}</h1>
    <div class="sub">{html.escape(subtitle)}</div>
  </div>
{NAV_HTML}
</header>
<main>
  {panels_html}
  {table_html}
</main>
<script id="data" type="application/json">{data_json}</script>
<script>
  document.querySelectorAll('header nav a').forEach(a => {{
    if (a.dataset.page === '{page_id}') a.classList.add('active');
  }});
  const rows = JSON.parse(document.getElementById('data').textContent);
  function esc(s) {{
    return (s ?? '').toString().replace(/[&<>"']/g, c => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}})[c]);
  }}
  function fmt(n, d=0) {{ return n == null ? '—' : Number(n).toLocaleString(undefined, {{minimumFractionDigits: d, maximumFractionDigits: d}}); }}
  function pill(label, cls) {{ return `<span class="pill ${{cls}}">${{esc(label)}}</span>`; }}
  function safeJoin(arr) {{ return Array.isArray(arr) ? arr.map(x => esc(typeof x === 'string' ? x : JSON.stringify(x))).join('<br>') : esc(arr); }}

  function bindBars(panelId, key, value) {{
    document.querySelectorAll(`#${{panelId}} .clickable`).forEach(el => {{
      el.addEventListener('click', () => {{
        const input = document.getElementById('search');
        const sel = document.getElementById(key + 'Filter');
        if (sel && [...sel.options].some(o => o.value === el.dataset.value)) {{
          sel.value = el.dataset.value;
          state[key] = el.dataset.value;
        }} else if (input) {{
          input.value = el.dataset.value;
          state.search = el.dataset.value;
        }}
        state.page = 0;
        render();
        document.getElementById('table').scrollIntoView({{ behavior: 'smooth', block: 'start' }});
      }});
    }});
  }}

  {app_js}
</script>
</body>
</html>
"""


# ----------------------------------------------------------------------------
# RANKING
# ----------------------------------------------------------------------------

RANKING_PANELS = """
  <section class="cards" id="summaryCards"></section>
  <section class="panel-row">
    <div class="panel"><h2>Priority tiers</h2><div class="bars" id="tierBars"></div></div>
    <div class="panel"><h2>Adjusted priority score distribution</h2><div class="bars" id="scoreBars"></div></div>
  </section>
  <section class="panel-row">
    <div class="panel"><h2>Mean ranking-component contribution</h2><div class="bars" id="compBars"></div></div>
    <div class="panel"><h2>Top families by best score (≥ 5 models)</h2><div class="bars" id="familyBars"></div></div>
  </section>
"""

RANKING_TABLE = """
  <section>
    <div class="filters">
      <input id="search" type="search" placeholder="Search paper id, model id, family, rationale…">
      <select id="tierFilter"><option value="">All tiers</option>
        <option value="tier2">tier2</option>
        <option value="tier3">tier3</option>
        <option value="defer">defer</option>
        <option value="rejected">rejected</option>
      </select>
      <select id="familyFilter"><option value="">All families</option></select>
      <span class="meta" id="rowMeta"></span>
    </div>
    <table id="table">
      <thead>
        <tr>
          <th data-sort="global_rank" data-numeric="1">Global rank <span class="arrow">↑</span></th>
          <th data-sort="family_rank" data-numeric="1">Family rank <span class="arrow">↕</span></th>
          <th data-sort="adjusted_priority_score" data-numeric="1">Score <span class="arrow">↕</span></th>
          <th data-sort="priority_tier">Tier <span class="arrow">↕</span></th>
          <th data-sort="family">Family <span class="arrow">↕</span></th>
          <th data-sort="paper_id">Paper / model <span class="arrow">↕</span></th>
        </tr>
      </thead>
      <tbody id="tbody"></tbody>
    </table>
    <div class="pager">
      <button id="prevBtn">‹ Prev</button>
      <span id="pageInfo"></span>
      <button id="nextBtn">Next ›</button>
    </div>
  </section>
"""

RANKING_JS = r"""
  const PAGE = 50;
  const TIER_ORDER = { tier2: 0, tier3: 1, defer: 2, rejected: 3 };
  const state = { search: '', tier: '', family: '', sortKey: 'global_rank', sortDir: 1, page: 0, expanded: new Set() };

  // Flatten triage for table display
  for (const r of rows) {
    const t = r.triage || {};
    r._tier = t.priority_tier || '';
    r._score = t.adjusted_priority_score;
    r._raw = t.raw_priority_score;
    r._global = t.global_rank;
    r._family_rank = t.family_rank;
    r._pct = t.rank_percentile;
    r._rationale = (t.ranking_rationale || []).join(' ');
    r._defer = (t.defer_reason || []).join(' ');
    r._reject = (t.rejection_reason || []).join(' ');
  }

  // --- summary cards ---
  const tierCounts = {};
  for (const r of rows) tierCounts[r._tier] = (tierCounts[r._tier] || 0) + 1;
  const scoredVals = rows.map(r => r._score).filter(x => x != null);
  const meanScore = scoredVals.reduce((a, b) => a + b, 0) / Math.max(1, scoredVals.length);
  const cards = [
    { label: 'Total models',  value: rows.length.toLocaleString() },
    { label: 'Tier 2',         value: (tierCounts.tier2 || 0).toLocaleString(), cls: 'accept' },
    { label: 'Tier 3',         value: (tierCounts.tier3 || 0).toLocaleString() },
    { label: 'Deferred',       value: (tierCounts.defer || 0).toLocaleString(), cls: 'warn' },
    { label: 'Rejected',       value: (tierCounts.rejected || 0).toLocaleString(), cls: 'reject' },
    { label: 'Mean score',     value: meanScore.toFixed(2) },
    { label: 'Max score',      value: Math.max(...scoredVals).toFixed(1) },
    { label: 'Families',       value: new Set(rows.map(r => r.family)).size.toLocaleString() },
  ];
  document.getElementById('summaryCards').innerHTML = cards.map(c =>
    `<div class="card ${c.cls || ''}"><div class="label">${c.label}</div><div class="value">${c.value}</div></div>`
  ).join('');

  // --- tier bars (clickable) ---
  const tierTotal = rows.length;
  const tierMax = Math.max(...Object.values(tierCounts));
  document.getElementById('tierBars').innerHTML = ['tier2', 'tier3', 'defer', 'rejected'].map(t => {
    const n = tierCounts[t] || 0;
    return `<div class="bar-row clickable" data-value="${t}">
      <span class="name">${t}</span>
      <div class="bar-track"><div class="bar-fill ${t}" style="width:${(100*n/tierMax).toFixed(2)}%"></div></div>
      <span class="count">${n.toLocaleString()}</span>
    </div>`;
  }).join('');
  bindBars('tierBars', 'tier');

  // --- score histogram ---
  const bins = [
    { label: '< 0',     min: -Infinity, max: 0 },
    { label: '0–10',    min: 0,  max: 10 },
    { label: '10–20',   min: 10, max: 20 },
    { label: '20–30',   min: 20, max: 30 },
    { label: '30–40',   min: 30, max: 40 },
    { label: '40+',     min: 40, max: Infinity },
    { label: 'null',    min: null, max: null },
  ];
  for (const b of bins) b.count = 0;
  for (const r of rows) {
    if (r._score == null) { bins.find(b => b.label === 'null').count += 1; continue; }
    const b = bins.find(b => r._score >= b.min && r._score < b.max);
    if (b) b.count += 1;
  }
  const scoreMax = Math.max(...bins.map(b => b.count));
  document.getElementById('scoreBars').innerHTML = bins.map(b =>
    `<div class="bar-row"><span class="name">${b.label}</span>
       <div class="bar-track"><div class="bar-fill" style="width:${(100*b.count/scoreMax).toFixed(2)}%"></div></div>
       <span class="count">${b.count.toLocaleString()}</span></div>`
  ).join('');

  // --- component means ---
  const compKeys = ['scientific_value', 'observational_leverage', 'complementarity', 'diversity_value', 'provenance_and_robustness', 'feasibility', 'penalties'];
  const compMeans = compKeys.map(k => {
    const vals = rows.map(r => (r.triage && r.triage.ranking_components || {})[k]).filter(v => v != null);
    return { k, mean: vals.reduce((a,b)=>a+b,0) / Math.max(1, vals.length) };
  });
  const compMax = Math.max(...compMeans.map(c => c.mean));
  document.getElementById('compBars').innerHTML = compMeans.map(c =>
    `<div class="bar-row"><span class="name">${c.k.replace(/_/g, ' ')}</span>
       <div class="bar-track"><div class="bar-fill ${c.k === 'penalties' ? 'reject' : ''}" style="width:${(100*c.mean/compMax).toFixed(2)}%"></div></div>
       <span class="count">${c.mean.toFixed(2)}</span></div>`
  ).join('');

  // --- top families ---
  const famStats = new Map();
  for (const r of rows) {
    if (!famStats.has(r.family)) famStats.set(r.family, { count: 0, best: -Infinity });
    const s = famStats.get(r.family);
    s.count += 1;
    if (r._score != null && r._score > s.best) s.best = r._score;
  }
  const eligibleFams = [...famStats.entries()].filter(([_, s]) => s.count >= 5 && s.best > -Infinity);
  eligibleFams.sort((a, b) => b[1].best - a[1].best);
  const famSlice = eligibleFams.slice(0, 12);
  const famMax = famSlice.length ? famSlice[0][1].best : 1;
  document.getElementById('familyBars').innerHTML = famSlice.map(([k, s]) =>
    `<div class="bar-row clickable" data-value="${esc(k)}">
       <span class="name" title="${esc(k)}">${esc(k)}</span>
       <div class="bar-track"><div class="bar-fill" style="width:${(100*s.best/famMax).toFixed(2)}%"></div></div>
       <span class="count">${s.best.toFixed(1)} · n=${s.count}</span></div>`
  ).join('');
  bindBars('familyBars', 'family');

  // --- family filter populate ---
  const famSelect = document.getElementById('familyFilter');
  [...famStats.entries()].sort((a, b) => b[1].count - a[1].count).forEach(([k, s]) => {
    const opt = document.createElement('option');
    opt.value = k;
    opt.textContent = `${k}  (${s.count})`;
    famSelect.appendChild(opt);
  });

  // --- sorting / filtering ---
  function compare(a, b, key) {
    if (key === 'global_rank') return (a.triage.global_rank ?? Infinity) - (b.triage.global_rank ?? Infinity);
    if (key === 'family_rank') return (a.triage.family_rank ?? Infinity) - (b.triage.family_rank ?? Infinity);
    if (key === 'adjusted_priority_score') return (a._score ?? -Infinity) - (b._score ?? -Infinity);
    if (key === 'priority_tier') return (TIER_ORDER[a._tier] ?? 99) - (TIER_ORDER[b._tier] ?? 99);
    const av = (a[key] ?? '').toString().toLowerCase();
    const bv = (b[key] ?? '').toString().toLowerCase();
    return av < bv ? -1 : (av > bv ? 1 : 0);
  }
  function filtered() {
    const q = state.search.toLowerCase();
    return rows.filter(r => {
      if (state.tier && r._tier !== state.tier) return false;
      if (state.family && r.family !== state.family) return false;
      if (!q) return true;
      return (r.paper_id || '').toLowerCase().includes(q)
        || (r.model_id || '').toLowerCase().includes(q)
        || (r.family || '').toLowerCase().includes(q)
        || r._rationale.toLowerCase().includes(q)
        || r._defer.toLowerCase().includes(q)
        || r._reject.toLowerCase().includes(q);
    }).sort((a, b) => state.sortDir * compare(a, b, state.sortKey));
  }
  function render() {
    const data = filtered();
    const pages = Math.max(1, Math.ceil(data.length / PAGE));
    state.page = Math.min(Math.max(0, state.page), pages - 1);
    const slice = data.slice(state.page * PAGE, state.page * PAGE + PAGE);
    const tbody = document.getElementById('tbody');
    tbody.innerHTML = slice.map((r, i) => {
      const idx = state.page * PAGE + i;
      const components = r.triage && r.triage.ranking_components || {};
      const compStr = Object.entries(components).map(([k, v]) => `${k}=${v}`).join(', ');
      const expanded = state.expanded.has(r.model_id);
      const detail = expanded ? `
        <tr class="detail-row" data-key="${esc(r.model_id)}-d">
          <td colspan="6"><div class="detail-pane">
            <div><strong>Rationale:</strong> ${esc(r._rationale) || '<em class="muted">none</em>'}</div>
            <div style="margin-top:8px"><strong>Defer reasons:</strong> ${esc(r._defer) || '<em class="muted">none</em>'}</div>
            <div style="margin-top:8px"><strong>Rejection reasons:</strong> ${esc(r._reject) || '<em class="muted">none</em>'}</div>
            <div style="margin-top:8px"><strong>Components:</strong> ${esc(compStr)}</div>
            <div style="margin-top:8px"><strong>Raw score:</strong> ${esc(r._raw)} · <strong>Percentile:</strong> ${esc((r._pct ?? '').toString())}</div>
          </div></td>
        </tr>` : '';
      return `
        <tr class="expandable" data-key="${esc(r.model_id)}">
          <td class="num">${r.triage.global_rank ?? '—'}</td>
          <td class="num muted">${r.triage.family_rank ?? '—'}</td>
          <td class="num">${r._score == null ? '—' : r._score.toFixed(1)}</td>
          <td>${pill(r._tier || '—', r._tier)}</td>
          <td><span class="mono">${esc(r.family)}</span></td>
          <td><span class="paper">${esc(r.paper_id)}</span><br><span class="mono muted">${esc(r.model_id)}</span></td>
        </tr>${detail}`;
    }).join('');
    tbody.querySelectorAll('tr.expandable').forEach(tr => {
      tr.addEventListener('click', () => {
        const k = tr.dataset.key;
        if (state.expanded.has(k)) state.expanded.delete(k); else state.expanded.add(k);
        render();
      });
    });
    document.getElementById('rowMeta').textContent = `${data.length.toLocaleString()} of ${rows.length.toLocaleString()} rows`;
    document.getElementById('pageInfo').textContent = `Page ${state.page + 1} / ${pages}`;
    document.getElementById('prevBtn').disabled = state.page === 0;
    document.getElementById('nextBtn').disabled = state.page >= pages - 1;
    document.querySelectorAll('th').forEach(th => {
      th.classList.toggle('sorted', th.dataset.sort === state.sortKey);
      const a = th.querySelector('.arrow');
      if (a) a.textContent = th.dataset.sort === state.sortKey ? (state.sortDir === 1 ? '↑' : '↓') : '↕';
    });
  }
  document.getElementById('search').addEventListener('input', e => { state.search = e.target.value; state.page = 0; render(); });
  document.getElementById('tierFilter').addEventListener('change', e => { state.tier = e.target.value; state.page = 0; render(); });
  document.getElementById('familyFilter').addEventListener('change', e => { state.family = e.target.value; state.page = 0; render(); });
  document.getElementById('prevBtn').addEventListener('click', () => { state.page -= 1; render(); });
  document.getElementById('nextBtn').addEventListener('click', () => { state.page += 1; render(); });
  document.querySelectorAll('th[data-sort]').forEach(th => {
    th.addEventListener('click', () => {
      const k = th.dataset.sort;
      if (state.sortKey === k) state.sortDir *= -1;
      else { state.sortKey = k; state.sortDir = (k === 'adjusted_priority_score' || k === 'family_rank' || k === 'global_rank') ? (k === 'adjusted_priority_score' ? -1 : 1) : 1; }
      state.page = 0;
      render();
    });
  });
  render();
"""


# ----------------------------------------------------------------------------
# ENRICHMENT STATUS
# ----------------------------------------------------------------------------

ENRICH_STATUS_PANELS = """
  <section class="cards" id="summaryCards"></section>
  <section class="panel-row">
    <div class="panel"><h2>Enrichment status</h2><div class="bars" id="statusBars"></div></div>
    <div class="panel"><h2>Output rows per paper</h2><div class="bars" id="outputBars"></div></div>
  </section>
  <section class="panel-row">
    <div class="panel"><h2>ADS citation count distribution</h2><div class="bars" id="citeBars"></div></div>
    <div class="panel"><h2>Candidate count distribution</h2><div class="bars" id="candBars"></div></div>
  </section>
"""

ENRICH_STATUS_TABLE = """
  <section>
    <div class="filters">
      <input id="search" type="search" placeholder="Search paper id, notes, related texts…">
      <select id="statusFilter"><option value="">All statuses</option></select>
      <span class="meta" id="rowMeta"></span>
    </div>
    <table id="table">
      <thead>
        <tr>
          <th data-sort="paper_id">Paper ID <span class="arrow">↕</span></th>
          <th data-sort="status">Status <span class="arrow">↕</span></th>
          <th data-sort="candidate_count" data-numeric="1">Candidates <span class="arrow">↕</span></th>
          <th data-sort="model_row_count" data-numeric="1">Model rows <span class="arrow">↕</span></th>
          <th data-sort="output_row_count" data-numeric="1">Output rows <span class="arrow">↕</span></th>
          <th data-sort="ads_citation_count" data-numeric="1">ADS cites <span class="arrow">↕</span></th>
          <th data-sort="ads_reference_count" data-numeric="1">ADS refs <span class="arrow">↕</span></th>
          <th data-sort="related_count" data-numeric="1">Related <span class="arrow">↕</span></th>
          <th data-sort="notes">Notes <span class="arrow">↕</span></th>
        </tr>
      </thead>
      <tbody id="tbody"></tbody>
    </table>
    <div class="pager">
      <button id="prevBtn">‹ Prev</button>
      <span id="pageInfo"></span>
      <button id="nextBtn">Next ›</button>
    </div>
  </section>
"""

ENRICH_STATUS_JS = r"""
  const PAGE = 100;
  const state = { search: '', status: '', sortKey: 'paper_id', sortDir: 1, page: 0 };

  for (const r of rows) {
    r.related_count = Array.isArray(r.related_texts_read) ? r.related_texts_read.length : 0;
  }

  // summary cards
  const statusCounts = {};
  let totalCand = 0, totalOut = 0, totalCites = 0, totalRefs = 0;
  for (const r of rows) {
    statusCounts[r.status] = (statusCounts[r.status] || 0) + 1;
    totalCand += r.candidate_count || 0;
    totalOut  += r.output_row_count || 0;
    totalCites += r.ads_citation_count || 0;
    totalRefs += r.ads_reference_count || 0;
  }
  const cards = [
    { label: 'Total papers',  value: rows.length.toLocaleString() },
    { label: 'Completed',     value: (statusCounts.completed || 0).toLocaleString(), cls: 'accept' },
    { label: 'Errored',       value: (statusCounts.error || 0).toLocaleString(), cls: 'reject' },
    { label: 'Candidates',    value: totalCand.toLocaleString() },
    { label: 'Output rows',   value: totalOut.toLocaleString() },
    { label: 'ADS citations', value: totalCites.toLocaleString() },
    { label: 'ADS references',value: totalRefs.toLocaleString() },
  ];
  document.getElementById('summaryCards').innerHTML = cards.map(c =>
    `<div class="card ${c.cls || ''}"><div class="label">${c.label}</div><div class="value">${c.value}</div></div>`
  ).join('');

  // status bars
  const statusEntries = Object.entries(statusCounts).sort((a, b) => b[1] - a[1]);
  const statusMax = statusEntries.length ? statusEntries[0][1] : 1;
  document.getElementById('statusBars').innerHTML = statusEntries.map(([k, v]) => {
    const fill = k === 'completed' ? 'accept' : (k === 'error' ? 'reject' : '');
    return `<div class="bar-row clickable" data-value="${esc(k)}">
      <span class="name">${esc(k)}</span>
      <div class="bar-track"><div class="bar-fill ${fill}" style="width:${(100*v/statusMax).toFixed(2)}%"></div></div>
      <span class="count">${v.toLocaleString()}</span>
    </div>`;
  }).join('');
  bindBars('statusBars', 'status');

  // status filter
  const sel = document.getElementById('statusFilter');
  for (const [k] of statusEntries) {
    const opt = document.createElement('option');
    opt.value = k; opt.textContent = k;
    sel.appendChild(opt);
  }

  // helper: build histogram bars
  function histogram(values, edges, labels) {
    const counts = new Array(edges.length - 1).fill(0);
    for (const v of values) {
      if (v == null) continue;
      for (let i = 0; i < edges.length - 1; i++) {
        if (v >= edges[i] && v < edges[i + 1]) { counts[i]++; break; }
      }
    }
    const max = Math.max(1, ...counts);
    return labels.map((label, i) =>
      `<div class="bar-row"><span class="name">${label}</span>
        <div class="bar-track"><div class="bar-fill" style="width:${(100*counts[i]/max).toFixed(2)}%"></div></div>
        <span class="count">${counts[i].toLocaleString()}</span></div>`
    ).join('');
  }

  document.getElementById('outputBars').innerHTML = histogram(
    rows.map(r => r.output_row_count || 0),
    [0, 1, 2, 3, 5, 10, Infinity],
    ['0', '1', '2', '3–4', '5–9', '10+']
  );
  document.getElementById('citeBars').innerHTML = histogram(
    rows.map(r => r.ads_citation_count || 0),
    [0, 10, 50, 100, 500, 1000, Infinity],
    ['0–9', '10–49', '50–99', '100–499', '500–999', '1000+']
  );
  document.getElementById('candBars').innerHTML = histogram(
    rows.map(r => r.candidate_count || 0),
    [0, 1, 5, 10, 25, 50, Infinity],
    ['0', '1–4', '5–9', '10–24', '25–49', '50+']
  );

  // table
  function compare(a, b, key) {
    if (key === 'related_count') return (a.related_count || 0) - (b.related_count || 0);
    const isNum = ['candidate_count', 'model_row_count', 'output_row_count', 'ads_citation_count', 'ads_reference_count'].includes(key);
    if (isNum) return (a[key] ?? 0) - (b[key] ?? 0);
    const av = (a[key] ?? '').toString().toLowerCase();
    const bv = (b[key] ?? '').toString().toLowerCase();
    return av < bv ? -1 : (av > bv ? 1 : 0);
  }
  function filtered() {
    const q = state.search.toLowerCase();
    return rows.filter(r => {
      if (state.status && r.status !== state.status) return false;
      if (!q) return true;
      return (r.paper_id || '').toLowerCase().includes(q)
        || (r.notes || '').toLowerCase().includes(q)
        || (r.related_texts_read || []).some(t => (t || '').toLowerCase().includes(q));
    }).sort((a, b) => state.sortDir * compare(a, b, state.sortKey));
  }
  function render() {
    const data = filtered();
    const pages = Math.max(1, Math.ceil(data.length / PAGE));
    state.page = Math.min(Math.max(0, state.page), pages - 1);
    const slice = data.slice(state.page * PAGE, state.page * PAGE + PAGE);
    document.getElementById('tbody').innerHTML = slice.map(r => `
      <tr>
        <td class="paper">${esc(r.paper_id)}</td>
        <td>${pill(r.status, r.status)}</td>
        <td class="num">${r.candidate_count ?? 0}</td>
        <td class="num">${r.model_row_count ?? 0}</td>
        <td class="num">${r.output_row_count ?? 0}</td>
        <td class="num">${r.ads_citation_count ?? '—'}</td>
        <td class="num">${r.ads_reference_count ?? '—'}</td>
        <td class="num">${r.related_count}</td>
        <td class="reason ${r.notes ? '' : 'muted'}">${r.notes ? esc(r.notes) : '—'}</td>
      </tr>
    `).join('');
    document.getElementById('rowMeta').textContent = `${data.length.toLocaleString()} of ${rows.length.toLocaleString()} rows`;
    document.getElementById('pageInfo').textContent = `Page ${state.page + 1} / ${pages}`;
    document.getElementById('prevBtn').disabled = state.page === 0;
    document.getElementById('nextBtn').disabled = state.page >= pages - 1;
    document.querySelectorAll('th').forEach(th => {
      th.classList.toggle('sorted', th.dataset.sort === state.sortKey);
      const a = th.querySelector('.arrow');
      if (a) a.textContent = th.dataset.sort === state.sortKey ? (state.sortDir === 1 ? '↑' : '↓') : '↕';
    });
  }
  document.getElementById('search').addEventListener('input', e => { state.search = e.target.value; state.page = 0; render(); });
  document.getElementById('statusFilter').addEventListener('change', e => { state.status = e.target.value; state.page = 0; render(); });
  document.getElementById('prevBtn').addEventListener('click', () => { state.page -= 1; render(); });
  document.getElementById('nextBtn').addEventListener('click', () => { state.page += 1; render(); });
  document.querySelectorAll('th[data-sort]').forEach(th => {
    th.addEventListener('click', () => {
      const k = th.dataset.sort;
      if (state.sortKey === k) state.sortDir *= -1;
      else { state.sortKey = k; state.sortDir = th.dataset.numeric ? -1 : 1; }
      state.page = 0; render();
    });
  });
  render();
"""


# ----------------------------------------------------------------------------
# ENRICHMENT OUTPUTS
# ----------------------------------------------------------------------------

ENRICH_OUT_PANELS = """
  <section class="cards" id="summaryCards"></section>
  <section class="panel-row">
    <div class="panel"><h2>Observables per model</h2><div class="bars" id="obsBars"></div></div>
    <div class="panel"><h2>Constraints per model</h2><div class="bars" id="conBars"></div></div>
  </section>
  <section class="panel-row">
    <div class="panel"><h2>Top observable channels</h2><div class="bars" id="channelBars"></div></div>
    <div class="panel"><h2>Top constraint types</h2><div class="bars" id="ctypeBars"></div></div>
  </section>
"""

ENRICH_OUT_TABLE = """
  <section>
    <div class="filters">
      <input id="search" type="search" placeholder="Search paper id, model id, observable/constraint name…">
      <select id="channelFilter"><option value="">All channels</option></select>
      <span class="meta" id="rowMeta"></span>
    </div>
    <table id="table">
      <thead>
        <tr>
          <th data-sort="paper_id">Paper / model <span class="arrow">↕</span></th>
          <th data-sort="arxiv_id">arXiv <span class="arrow">↕</span></th>
          <th data-sort="obs_count" data-numeric="1">Observables <span class="arrow">↕</span></th>
          <th data-sort="con_count" data-numeric="1">Constraints <span class="arrow">↕</span></th>
          <th data-sort="route_count" data-numeric="1">Routes <span class="arrow">↕</span></th>
          <th data-sort="unresolved_count" data-numeric="1">Unresolved <span class="arrow">↕</span></th>
        </tr>
      </thead>
      <tbody id="tbody"></tbody>
    </table>
    <div class="pager">
      <button id="prevBtn">‹ Prev</button>
      <span id="pageInfo"></span>
      <button id="nextBtn">Next ›</button>
    </div>
  </section>
"""

ENRICH_OUT_JS = r"""
  const PAGE = 50;
  const state = { search: '', channel: '', sortKey: 'paper_id', sortDir: 1, page: 0, expanded: new Set() };

  // Pre-compute counts and gather channel/type tallies
  const channelTally = new Map();
  const typeTally = new Map();
  for (const r of rows) {
    r.obs_count = (r.observables || []).length;
    r.con_count = (r.constraints || []).length;
    r.route_count = ((r.theory_to_observable_routing || {}).routes || []).length;
    r.unresolved_count = (r.unresolved_items || []).length;
    r._channels = new Set();
    for (const o of (r.observables || [])) {
      const c = o.channel || '(none)';
      r._channels.add(c);
      channelTally.set(c, (channelTally.get(c) || 0) + 1);
    }
    for (const c of (r.constraints || [])) {
      const t = c.constraint_type || '(none)';
      typeTally.set(t, (typeTally.get(t) || 0) + 1);
    }
  }

  // cards
  const totalObs = rows.reduce((a, r) => a + r.obs_count, 0);
  const totalCon = rows.reduce((a, r) => a + r.con_count, 0);
  const totalRt = rows.reduce((a, r) => a + r.route_count, 0);
  const totalUn = rows.reduce((a, r) => a + r.unresolved_count, 0);
  document.getElementById('summaryCards').innerHTML = [
    { label: 'Enriched models', value: rows.length.toLocaleString() },
    { label: 'Unique papers',   value: new Set(rows.map(r => r.paper_id)).size.toLocaleString() },
    { label: 'Observables',     value: totalObs.toLocaleString() },
    { label: 'Constraints',     value: totalCon.toLocaleString() },
    { label: 'Routes',          value: totalRt.toLocaleString() },
    { label: 'Unresolved items',value: totalUn.toLocaleString(), cls: totalUn ? 'warn' : '' },
  ].map(c => `<div class="card ${c.cls || ''}"><div class="label">${c.label}</div><div class="value">${c.value}</div></div>`).join('');

  function histogram(values, edges, labels) {
    const counts = new Array(edges.length - 1).fill(0);
    for (const v of values) {
      for (let i = 0; i < edges.length - 1; i++) {
        if (v >= edges[i] && v < edges[i + 1]) { counts[i]++; break; }
      }
    }
    const max = Math.max(1, ...counts);
    return labels.map((label, i) =>
      `<div class="bar-row"><span class="name">${label}</span>
        <div class="bar-track"><div class="bar-fill" style="width:${(100*counts[i]/max).toFixed(2)}%"></div></div>
        <span class="count">${counts[i].toLocaleString()}</span></div>`
    ).join('');
  }
  document.getElementById('obsBars').innerHTML = histogram(
    rows.map(r => r.obs_count), [0, 1, 2, 3, 4, 6, 10, Infinity],
    ['0', '1', '2', '3', '4–5', '6–9', '10+']);
  document.getElementById('conBars').innerHTML = histogram(
    rows.map(r => r.con_count), [0, 1, 2, 3, 4, 6, 10, Infinity],
    ['0', '1', '2', '3', '4–5', '6–9', '10+']);

  // channels
  const channelSorted = [...channelTally.entries()].sort((a, b) => b[1] - a[1]);
  const channelMax = channelSorted.length ? channelSorted[0][1] : 1;
  document.getElementById('channelBars').innerHTML = channelSorted.slice(0, 12).map(([k, v]) =>
    `<div class="bar-row clickable" data-value="${esc(k)}"><span class="name">${esc(k)}</span>
      <div class="bar-track"><div class="bar-fill" style="width:${(100*v/channelMax).toFixed(2)}%"></div></div>
      <span class="count">${v.toLocaleString()}</span></div>`
  ).join('');
  bindBars('channelBars', 'channel');

  const typeSorted = [...typeTally.entries()].sort((a, b) => b[1] - a[1]);
  const typeMax = typeSorted.length ? typeSorted[0][1] : 1;
  document.getElementById('ctypeBars').innerHTML = typeSorted.slice(0, 12).map(([k, v]) =>
    `<div class="bar-row"><span class="name">${esc(k)}</span>
      <div class="bar-track"><div class="bar-fill" style="width:${(100*v/typeMax).toFixed(2)}%"></div></div>
      <span class="count">${v.toLocaleString()}</span></div>`
  ).join('');

  // channel filter
  const sel = document.getElementById('channelFilter');
  for (const [k, v] of channelSorted) {
    const opt = document.createElement('option');
    opt.value = k; opt.textContent = `${k} (${v})`;
    sel.appendChild(opt);
  }

  function compare(a, b, key) {
    const numKeys = ['obs_count', 'con_count', 'route_count', 'unresolved_count'];
    if (numKeys.includes(key)) return (a[key] || 0) - (b[key] || 0);
    const av = (a[key] ?? '').toString().toLowerCase();
    const bv = (b[key] ?? '').toString().toLowerCase();
    return av < bv ? -1 : (av > bv ? 1 : 0);
  }
  function filtered() {
    const q = state.search.toLowerCase();
    return rows.filter(r => {
      if (state.channel && !r._channels.has(state.channel)) return false;
      if (!q) return true;
      if ((r.paper_id || '').toLowerCase().includes(q)) return true;
      if ((r.model_id || '').toLowerCase().includes(q)) return true;
      if ((r.arxiv_id || '').toLowerCase().includes(q)) return true;
      for (const o of (r.observables || [])) {
        if ((o.name || '').toLowerCase().includes(q)) return true;
        if ((o.channel || '').toLowerCase().includes(q)) return true;
      }
      for (const c of (r.constraints || [])) {
        if ((c.name || '').toLowerCase().includes(q)) return true;
        if ((c.constraint_type || '').toLowerCase().includes(q)) return true;
      }
      return false;
    }).sort((a, b) => state.sortDir * compare(a, b, state.sortKey));
  }
  function detailHTML(r) {
    const obsList = (r.observables || []).map(o =>
      `<li><strong>${esc(o.name || o.id || '(unnamed)')}</strong> <span class="muted">[${esc(o.channel || '')}]</span> — ${esc(o.predicted_effect || o.effect_direction || '')}</li>`
    ).join('');
    const conList = (r.constraints || []).map(c =>
      `<li><strong>${esc(c.name || c.id || '(unnamed)')}</strong> <span class="muted">[${esc(c.constraint_type || '')}]</span> — applies: ${esc(c.applies || '?')}, robustness: ${esc(c.robustness || '?')}</li>`
    ).join('');
    const routes = ((r.theory_to_observable_routing || {}).routes || []).map(rt =>
      `<li><strong>${esc(rt.id || rt.name || '(unnamed)')}</strong> — ${esc(rt.summary || rt.notes || '')}</li>`
    ).join('');
    const unresolved = (r.unresolved_items || []).map(u =>
      `<li>${esc(typeof u === 'string' ? u : JSON.stringify(u))}</li>`
    ).join('');
    return `
      <div class="detail-pane">
        <div><strong>Observables (${r.obs_count}):</strong><ul>${obsList || '<li class="muted">none</li>'}</ul></div>
        <div><strong>Constraints (${r.con_count}):</strong><ul>${conList || '<li class="muted">none</li>'}</ul></div>
        <div><strong>Routes (${r.route_count}):</strong><ul>${routes || '<li class="muted">none</li>'}</ul></div>
        <div><strong>Unresolved (${r.unresolved_count}):</strong><ul>${unresolved || '<li class="muted">none</li>'}</ul></div>
      </div>`;
  }
  function render() {
    const data = filtered();
    const pages = Math.max(1, Math.ceil(data.length / PAGE));
    state.page = Math.min(Math.max(0, state.page), pages - 1);
    const slice = data.slice(state.page * PAGE, state.page * PAGE + PAGE);
    document.getElementById('tbody').innerHTML = slice.map(r => {
      const expanded = state.expanded.has(r.model_id);
      const detail = expanded ? `<tr class="detail-row" data-key="${esc(r.model_id)}-d"><td colspan="6">${detailHTML(r)}</td></tr>` : '';
      return `
        <tr class="expandable" data-key="${esc(r.model_id)}">
          <td><span class="paper">${esc(r.paper_id)}</span><br><span class="mono muted">${esc(r.model_id)}</span></td>
          <td class="mono">${esc(r.arxiv_id || '')}</td>
          <td class="num">${r.obs_count}</td>
          <td class="num">${r.con_count}</td>
          <td class="num">${r.route_count}</td>
          <td class="num">${r.unresolved_count}</td>
        </tr>${detail}`;
    }).join('');
    document.querySelectorAll('tr.expandable').forEach(tr => {
      tr.addEventListener('click', () => {
        const k = tr.dataset.key;
        if (state.expanded.has(k)) state.expanded.delete(k); else state.expanded.add(k);
        render();
      });
    });
    document.getElementById('rowMeta').textContent = `${data.length.toLocaleString()} of ${rows.length.toLocaleString()} rows`;
    document.getElementById('pageInfo').textContent = `Page ${state.page + 1} / ${pages}`;
    document.getElementById('prevBtn').disabled = state.page === 0;
    document.getElementById('nextBtn').disabled = state.page >= pages - 1;
    document.querySelectorAll('th').forEach(th => {
      th.classList.toggle('sorted', th.dataset.sort === state.sortKey);
      const a = th.querySelector('.arrow');
      if (a) a.textContent = th.dataset.sort === state.sortKey ? (state.sortDir === 1 ? '↑' : '↓') : '↕';
    });
  }
  document.getElementById('search').addEventListener('input', e => { state.search = e.target.value; state.page = 0; render(); });
  document.getElementById('channelFilter').addEventListener('change', e => { state.channel = e.target.value; state.page = 0; render(); });
  document.getElementById('prevBtn').addEventListener('click', () => { state.page -= 1; render(); });
  document.getElementById('nextBtn').addEventListener('click', () => { state.page += 1; render(); });
  document.querySelectorAll('th[data-sort]').forEach(th => {
    th.addEventListener('click', () => {
      const k = th.dataset.sort;
      if (state.sortKey === k) state.sortDir *= -1;
      else { state.sortKey = k; state.sortDir = th.dataset.numeric ? -1 : 1; }
      state.page = 0; render();
    });
  });
  render();
"""


# ----------------------------------------------------------------------------
# DARKMATTERWIKI (all_outputs_combined)
# ----------------------------------------------------------------------------

WIKI_PANELS = """
  <section class="cards" id="summaryCards"></section>
  <section class="panel-row">
    <div class="panel"><h2>Top families</h2><div class="bars" id="familyBars"></div></div>
    <div class="panel"><h2>Model kind</h2><div class="bars" id="kindBars"></div></div>
  </section>
  <section class="panel-row">
    <div class="panel"><h2>Status</h2><div class="bars" id="statusBars"></div></div>
    <div class="panel"><h2>Portals</h2><div class="bars" id="portalBars"></div></div>
  </section>
"""

WIKI_TABLE = """
  <section>
    <div class="filters">
      <input id="search" type="search" placeholder="Search name, aliases, paper id, family, description…">
      <select id="familyFilter"><option value="">All families</option></select>
      <select id="statusFilter"><option value="">All statuses</option></select>
      <select id="kindFilter"><option value="">All model kinds</option></select>
      <select id="portalFilter"><option value="">All portals</option></select>
      <span class="meta" id="rowMeta"></span>
    </div>
    <table id="table">
      <thead>
        <tr>
          <th data-sort="name">Name <span class="arrow">↕</span></th>
          <th data-sort="candidate">DM candidate <span class="arrow">↕</span></th>
          <th data-sort="family">Family <span class="arrow">↕</span></th>
          <th data-sort="model_kind">Kind <span class="arrow">↕</span></th>
          <th data-sort="status">Status <span class="arrow">↕</span></th>
          <th data-sort="paper_id">Paper <span class="arrow">↕</span></th>
        </tr>
      </thead>
      <tbody id="tbody"></tbody>
    </table>
    <div class="pager">
      <button id="prevBtn">‹ Prev</button>
      <span id="pageInfo"></span>
      <button id="nextBtn">Next ›</button>
    </div>
  </section>
"""

WIKI_JS = r"""
  const PAGE = 60;
  const state = { search: '', family: '', status: '', kind: '', portal: '', sortKey: 'name', sortDir: 1, page: 0, expanded: new Set() };

  // Pre-compute searchable strings + tallies
  const familyTally = new Map();
  const kindTally = new Map();
  const statusTally = new Map();
  const portalTally = new Map();
  for (const r of rows) {
    r._aliasStr = (r.aliases || []).join(' ');
    r._portalStr = (r.portals || []).join(' ');
    familyTally.set(r.family || '(none)', (familyTally.get(r.family || '(none)') || 0) + 1);
    kindTally.set(r.model_kind || '(none)', (kindTally.get(r.model_kind || '(none)') || 0) + 1);
    statusTally.set(r.status || '(none)', (statusTally.get(r.status || '(none)') || 0) + 1);
    for (const p of (r.portals || [])) portalTally.set(p, (portalTally.get(p) || 0) + 1);
  }

  // --- summary cards ---
  document.getElementById('summaryCards').innerHTML = [
    { label: 'Model cards',  value: rows.length.toLocaleString() },
    { label: 'Unique papers', value: new Set(rows.map(r => r.paper_id)).size.toLocaleString() },
    { label: 'Families',      value: familyTally.size.toLocaleString() },
    { label: 'Benchmark',     value: (statusTally.get('benchmark') || 0).toLocaleString(), cls: 'accept' },
    { label: 'Canonical',     value: (statusTally.get('canonical') || 0).toLocaleString(), cls: 'accept' },
    { label: 'Speculative',   value: (statusTally.get('speculative') || 0).toLocaleString(), cls: 'warn' },
    { label: 'Excluded',      value: (statusTally.get('excluded') || 0).toLocaleString(), cls: 'reject' },
  ].map(c => `<div class="card ${c.cls || ''}"><div class="label">${c.label}</div><div class="value">${c.value}</div></div>`).join('');

  // --- family bars (clickable) ---
  const familySorted = [...familyTally.entries()].sort((a, b) => b[1] - a[1]);
  const familyMax = familySorted.length ? familySorted[0][1] : 1;
  document.getElementById('familyBars').innerHTML = familySorted.slice(0, 15).map(([k, v]) =>
    `<div class="bar-row clickable" data-value="${esc(k)}"><span class="name" title="${esc(k)}">${esc(k)}</span>
       <div class="bar-track"><div class="bar-fill" style="width:${(100*v/familyMax).toFixed(2)}%"></div></div>
       <span class="count">${v.toLocaleString()}</span></div>`
  ).join('');
  bindBars('familyBars', 'family');

  // --- kind bars (clickable) ---
  const kindSorted = [...kindTally.entries()].sort((a, b) => b[1] - a[1]);
  const kindMax = kindSorted.length ? kindSorted[0][1] : 1;
  document.getElementById('kindBars').innerHTML = kindSorted.map(([k, v]) =>
    `<div class="bar-row clickable" data-value="${esc(k)}"><span class="name">${esc(k)}</span>
       <div class="bar-track"><div class="bar-fill" style="width:${(100*v/kindMax).toFixed(2)}%"></div></div>
       <span class="count">${v.toLocaleString()}</span></div>`
  ).join('');
  bindBars('kindBars', 'kind');

  // --- status bars (clickable) ---
  const statusOrder = ['benchmark', 'canonical', 'emerging', 'speculative', 'excluded'];
  const statusSorted = statusOrder
    .filter(k => statusTally.has(k))
    .map(k => [k, statusTally.get(k)])
    .concat([...statusTally.entries()].filter(([k]) => !statusOrder.includes(k)));
  const statusMax = Math.max(...statusSorted.map(([, v]) => v));
  document.getElementById('statusBars').innerHTML = statusSorted.map(([k, v]) => {
    const fill = (k === 'benchmark' || k === 'canonical') ? 'accept' : (k === 'excluded' ? 'reject' : (k === 'speculative' ? 'warn' : ''));
    return `<div class="bar-row clickable" data-value="${esc(k)}"><span class="name">${esc(k)}</span>
      <div class="bar-track"><div class="bar-fill ${fill}" style="width:${(100*v/statusMax).toFixed(2)}%"></div></div>
      <span class="count">${v.toLocaleString()}</span></div>`;
  }).join('');
  bindBars('statusBars', 'status');

  // --- portal bars (clickable) ---
  const portalSorted = [...portalTally.entries()].sort((a, b) => b[1] - a[1]);
  const portalMax = portalSorted.length ? portalSorted[0][1] : 1;
  document.getElementById('portalBars').innerHTML = portalSorted.slice(0, 12).map(([k, v]) =>
    `<div class="bar-row clickable" data-value="${esc(k)}"><span class="name">${esc(k)}</span>
       <div class="bar-track"><div class="bar-fill" style="width:${(100*v/portalMax).toFixed(2)}%"></div></div>
       <span class="count">${v.toLocaleString()}</span></div>`
  ).join('');
  bindBars('portalBars', 'portal');

  // --- populate selects ---
  for (const [sel, entries] of [
    ['familyFilter', familySorted],
    ['kindFilter',   kindSorted],
    ['statusFilter', statusSorted],
    ['portalFilter', portalSorted],
  ]) {
    const el = document.getElementById(sel);
    entries.forEach(([k, v]) => {
      const opt = document.createElement('option');
      opt.value = k; opt.textContent = `${k}  (${v})`;
      el.appendChild(opt);
    });
  }

  function arxivLink(paperId) {
    if (!paperId) return '';
    // best-effort: "astro-ph0411262" -> "astro-ph/0411262", "1803_05650" -> "1803.05650"
    let id = paperId;
    const m = id.match(/^(hep-(?:ph|ex|th|lat)|astro-ph|gr-qc|nucl-(?:ex|th)|math-ph|cond-mat)(\d{7})$/);
    if (m) id = `${m[1]}/${m[2]}`;
    else if (/^\d{4}_\d{4,5}$/.test(id)) id = id.replace('_', '.');
    return `https://arxiv.org/abs/${encodeURIComponent(id)}`;
  }

  function detailHTML(r) {
    const c = r.card || {};
    const sec = (title, body) => body ? `<div class="wiki-sec"><h3>${esc(title)}</h3>${body}</div>` : '';
    const list = arr => Array.isArray(arr) && arr.length ? `<ul>${arr.map(x => `<li>${esc(typeof x === 'string' ? x : JSON.stringify(x))}</li>`).join('')}</ul>` : '';
    const grid = pairs => {
      const items = pairs.filter(([_, v]) => v != null && v !== '');
      if (!items.length) return '';
      return `<div class="wiki-grid">${items.map(([k, v]) => `<div><span class="wiki-k">${esc(k)}</span><span class="wiki-v">${esc(v)}</span></div>`).join('')}</div>`;
    };
    const identity = c.identity || {};
    const part = c.particle_content || {};
    const dm = part.dark_matter_candidate || {};
    const inter = c.interactions || {};
    const theory = c.theory || {};
    const production = c.production || {};
    const relic = c.relic_density || {};
    const cosm = c.cosmological_history || {};
    const sf = c.structure_formation || {};
    const ps = c.phase_space || {};
    const sym = c.symmetries || {};
    const params = (c.parameters || {}).core || [];
    const prov = c.provenance || {};
    const sources = (prov.sources || {}).primary_papers || [];
    const robust = c.robustness || {};
    const warnings = ((c.agent_failure_modes || {}).warnings || []);

    const paramRows = params.length ? `<table class="wiki-table"><thead><tr><th>Name</th><th>Symbol</th><th>Role</th><th>Status</th><th>Value/Range</th><th>Unit</th></tr></thead><tbody>${
      params.map(p => `<tr>
        <td>${esc(p.name || '')}</td>
        <td>${esc(p.symbol || '')}</td>
        <td>${esc(p.role || '')}</td>
        <td>${esc(p.status || '')}</td>
        <td>${esc(p.value ?? p.range ?? '')}</td>
        <td>${esc(p.unit || '')}</td>
      </tr>`).join('')
    }</tbody></table>` : '';

    const sourceRows = sources.length ? `<ul>${sources.map(s => {
      const link = s.arxiv_id ? ` <a href="https://arxiv.org/abs/${encodeURIComponent(s.arxiv_id)}" target="_blank" rel="noopener">[arXiv:${esc(s.arxiv_id)}]</a>` : '';
      return `<li><strong>${esc(s.title || '(untitled)')}</strong> — ${esc((s.authors || []).join(', '))} (${esc(s.year ?? '')})${link}</li>`;
    }).join('')}</ul>` : '';

    return `
      <div class="wiki-pane">
        <div class="wiki-head">
          <div class="wiki-name">${esc(identity.name || r.name || '(unnamed)')}</div>
          ${r.aliases && r.aliases.length ? `<div class="wiki-aliases">aka ${r.aliases.map(esc).join(' · ')}</div>` : ''}
          <div class="wiki-meta">
            ${pill(identity.status || '—', identity.status || 'defer')}
            <span class="mono muted">${esc(identity.family || '')}</span>
            <span class="muted">·</span>
            <span class="muted">${esc(identity.model_kind || '')}</span>
            ${r.paper_id ? `<span class="muted">·</span><a href="${arxivLink(r.paper_id)}" target="_blank" rel="noopener" class="mono">${esc(r.paper_id)}</a>` : ''}
          </div>
        </div>
        ${identity.short_description ? `<p class="wiki-desc">${esc(identity.short_description)}</p>` : ''}
        ${identity.historical_origin_or_motivation ? `<p class="wiki-desc muted"><em>${esc(identity.historical_origin_or_motivation)}</em></p>` : ''}

        ${sec('Particle content',
          grid([
            ['DM candidate', dm.name],
            ['Spin', dm.spin],
            ['Statistics', dm.statistics],
            ['Elementary/composite', dm.elementary_or_composite],
            ['Components', dm.number_of_components],
            ['SM extension', part.standard_model_extension],
          ]) +
          (Array.isArray(part.mediators) && part.mediators.length ? `<div><strong>Mediators:</strong> ${part.mediators.map(esc).join(', ')}</div>` : '') +
          (Array.isArray(part.additional_dark_sector_particles) && part.additional_dark_sector_particles.length ? `<div><strong>Other DS particles:</strong> ${part.additional_dark_sector_particles.map(esc).join(', ')}</div>` : '')
        )}

        ${sec('Interactions',
          grid([
            ['Portals', (inter.portals || []).join(', ')],
            ['Targets', (inter.standard_model_targets || []).join(', ')],
            ['Tree/loop', inter.tree_or_loop_level],
          ]) +
          ((inter.annihilation_channels || []).length ? `<div><strong>Annihilation:</strong> ${inter.annihilation_channels.map(esc).join(', ')}</div>` : '') +
          ((inter.decay_channels || []).length ? `<div><strong>Decay:</strong> ${inter.decay_channels.map(esc).join(', ')}</div>` : '') +
          ((inter.self_scattering_channels || []).length ? `<div><strong>Self-scattering:</strong> ${inter.self_scattering_channels.map(esc).join(', ')}</div>` : '')
        )}

        ${sec('Theory',
          grid([
            ['Theory level', theory.theory_level],
            ['Lagrangian', theory.lagrangian_available],
            ['Renormalizable', theory.renormalizable],
            ['Embedded?', theory.embedded_in_larger_framework],
          ]) +
          ((theory.parent_frameworks || []).length ? `<div><strong>Parent frameworks:</strong> ${theory.parent_frameworks.map(esc).join(', ')}</div>` : '') +
          (theory.notes ? `<p class="muted">${esc(theory.notes)}</p>` : '')
        )}

        ${sec('Symmetries',
          (sym.stabilizing_mechanism ? `<p>${esc(sym.stabilizing_mechanism)}</p>` : '') +
          ((sym.symmetries || []).length ? `<ul>${sym.symmetries.map(s => `<li><strong>${esc(s.name || '')}</strong> [${esc(s.type || '?')}] — ${esc(s.exact_or_approximate || '?')}; breaking: ${esc(s.breaking || '?')}</li>`).join('')}</ul>` : '')
        )}

        ${sec('Production',
          ((production.mechanisms || []).length ? `<div><strong>Mechanisms:</strong> ${production.mechanisms.map(esc).join(', ')}</div>` : '') +
          grid([
            ['SM equilibrium', production.thermal_equilibrium_with_standard_model],
            ['Hidden equilibrium', production.thermal_equilibrium_with_hidden_sector],
            ['T_R dependence', production.depends_on_reheating_temperature],
            ['Can be all DM', production.can_produce_all_dark_matter],
          ]) +
          (production.notes ? `<p class="muted">${esc(production.notes)}</p>` : '')
        )}

        ${sec('Relic density',
          grid([
            ['Coverage', relic.full_or_subcomponent],
            ['Calculation', relic.calculation_type],
            ['Overclosure risk', relic.overclosure_risk],
            ['Underproduction risk', relic.underproduction_risk],
            ['Entropy dilution', relic.requires_entropy_dilution],
            ['Tuning', relic.tuning_assessment],
          ])
        )}

        ${sec('Cosmological history',
          grid([
            ['Standard history?', cosm.standard_history_assumed],
            ['ΔN_eff', cosm.delta_neff],
            ['Kinetic decoupling', cosm.kinetic_decoupling],
            ['Chemical decoupling', cosm.chemical_decoupling],
            ['BBN relevance', cosm.bbn_relevance],
            ['CMB relevance', cosm.cmb_relevance],
            ['Isocurvature', cosm.isocurvature_perturbations],
          ]) +
          ((cosm.nonstandard_features || []).length ? `<div><strong>Non-standard features:</strong> ${cosm.nonstandard_features.map(esc).join(', ')}</div>` : '')
        )}

        ${sec('Phase space',
          grid([
            ['Distribution', ps.distribution_type],
            ['f(p) available', ps.distribution_function_available],
          ]) +
          (ps.notes ? `<p class="muted">${esc(ps.notes)}</p>` : '')
        )}

        ${sec('Structure formation',
          (() => {
            const lin = sf.linear || {};
            const nl = sf.nonlinear || {};
            return grid([
              ['Linear behaves like CDM', lin.behaves_like_cdm],
              ['Transfer function', lin.transfer_function_shape],
              ['Small-scale power', lin.small_scale_power_effect],
              ['Halo MF effect', nl.halo_mass_function_effect],
              ['Subhalo MF effect', nl.subhalo_mass_function_effect],
              ['Simulation calibrated', nl.simulation_calibrated],
            ]);
          })()
        )}

        ${sec('Core parameters', paramRows)}

        ${sec('Validity & assumptions',
          ((c.validity_domain || []).length ? `<ul>${c.validity_domain.map(v => `<li><strong>${esc(v.id || '')}</strong> [${esc(v.applies_to || '?')}, ${esc(v.status || '?')}]: ${esc(v.condition || '')}</li>`).join('')}</ul>` : '') +
          (((c.assumptions || {}).global || []).length ? `<ul>${c.assumptions.global.map(a => `<li><strong>${esc(a.id || '')}</strong> [${esc(a.scope || '?')}]: ${esc(a.description || '')}</li>`).join('')}</ul>` : '')
        )}

        ${sec('Robustness',
          grid([
            ['Overall', robust.overall],
            ['Theory', robust.theory_robustness],
            ['Observational', robust.observational_robustness],
            ['Computational', robust.computational_robustness],
            ['Validation', robust.validation_status],
          ]) + (robust.notes ? `<p class="muted">${esc(robust.notes)}</p>` : '')
        )}

        ${sec('Sources', sourceRows)}

        ${sec('Agent warnings',
          warnings.length ? `<ul>${warnings.map(w => `<li>[${esc(w.severity || '?')}, ${esc(w.category || '?')}] ${esc(w.warning || '')}</li>`).join('')}</ul>` : ''
        )}
      </div>`;
  }

  function compare(a, b, key) {
    const av = (a[key] ?? '').toString().toLowerCase();
    const bv = (b[key] ?? '').toString().toLowerCase();
    return av < bv ? -1 : (av > bv ? 1 : 0);
  }
  function filtered() {
    const q = state.search.toLowerCase();
    return rows.filter(r => {
      if (state.family && r.family !== state.family) return false;
      if (state.status && r.status !== state.status) return false;
      if (state.kind && r.model_kind !== state.kind) return false;
      if (state.portal && !(r.portals || []).includes(state.portal)) return false;
      if (!q) return true;
      return (r.name || '').toLowerCase().includes(q)
        || (r.candidate || '').toLowerCase().includes(q)
        || (r.family || '').toLowerCase().includes(q)
        || (r.paper_id || '').toLowerCase().includes(q)
        || (r.description || '').toLowerCase().includes(q)
        || r._aliasStr.toLowerCase().includes(q)
        || r._portalStr.toLowerCase().includes(q)
        || (r.model_id || '').toLowerCase().includes(q);
    }).sort((a, b) => state.sortDir * compare(a, b, state.sortKey));
  }
  function render() {
    const data = filtered();
    const pages = Math.max(1, Math.ceil(data.length / PAGE));
    state.page = Math.min(Math.max(0, state.page), pages - 1);
    const slice = data.slice(state.page * PAGE, state.page * PAGE + PAGE);
    document.getElementById('tbody').innerHTML = slice.map(r => {
      const expanded = state.expanded.has(r.model_id);
      const detail = expanded ? `<tr class="detail-row" data-key="${esc(r.model_id)}-d"><td colspan="6">${detailHTML(r)}</td></tr>` : '';
      return `
        <tr class="expandable" data-key="${esc(r.model_id)}">
          <td><strong>${esc(r.name || '')}</strong>${r.aliases && r.aliases.length ? `<br><span class="muted" style="font-size:11px">${esc((r.aliases || []).slice(0, 3).join(' · '))}</span>` : ''}</td>
          <td>${esc(r.candidate || '')}<br><span class="muted" style="font-size:11px">spin ${esc(r.spin || '?')}</span></td>
          <td><span class="mono">${esc(r.family || '')}</span></td>
          <td><span class="muted">${esc(r.model_kind || '')}</span></td>
          <td>${pill(r.status || '—', r.status || 'defer')}</td>
          <td><span class="paper">${esc(r.paper_id || '')}</span></td>
        </tr>${detail}`;
    }).join('');
    document.querySelectorAll('tr.expandable').forEach(tr => {
      tr.addEventListener('click', () => {
        const k = tr.dataset.key;
        if (state.expanded.has(k)) state.expanded.delete(k); else state.expanded.add(k);
        render();
      });
    });
    document.getElementById('rowMeta').textContent = `${data.length.toLocaleString()} of ${rows.length.toLocaleString()} rows`;
    document.getElementById('pageInfo').textContent = `Page ${state.page + 1} / ${pages}`;
    document.getElementById('prevBtn').disabled = state.page === 0;
    document.getElementById('nextBtn').disabled = state.page >= pages - 1;
    document.querySelectorAll('th').forEach(th => {
      th.classList.toggle('sorted', th.dataset.sort === state.sortKey);
      const a = th.querySelector('.arrow');
      if (a) a.textContent = th.dataset.sort === state.sortKey ? (state.sortDir === 1 ? '↑' : '↓') : '↕';
    });
  }
  document.getElementById('search').addEventListener('input', e => { state.search = e.target.value; state.page = 0; render(); });
  document.getElementById('familyFilter').addEventListener('change', e => { state.family = e.target.value; state.page = 0; render(); });
  document.getElementById('statusFilter').addEventListener('change', e => { state.status = e.target.value; state.page = 0; render(); });
  document.getElementById('kindFilter').addEventListener('change', e => { state.kind = e.target.value; state.page = 0; render(); });
  document.getElementById('portalFilter').addEventListener('change', e => { state.portal = e.target.value; state.page = 0; render(); });
  document.getElementById('prevBtn').addEventListener('click', () => { state.page -= 1; render(); });
  document.getElementById('nextBtn').addEventListener('click', () => { state.page += 1; render(); });
  document.querySelectorAll('th[data-sort]').forEach(th => {
    th.addEventListener('click', () => {
      const k = th.dataset.sort;
      if (state.sortKey === k) state.sortDir *= -1;
      else { state.sortKey = k; state.sortDir = 1; }
      state.page = 0; render();
    });
  });
  render();
"""

WIKI_EXTRA_CSS = """
  .wiki-pane { padding: 16px 20px; }
  .wiki-head { border-bottom: 1px solid var(--border); padding-bottom: 10px; margin-bottom: 12px; }
  .wiki-name { font-size: 18px; font-weight: 600; }
  .wiki-aliases { font-size: 12px; color: var(--muted); margin-top: 2px; }
  .wiki-meta { margin-top: 8px; display: flex; gap: 10px; align-items: center; font-size: 12px; }
  .wiki-desc { margin: 6px 0 10px; line-height: 1.5; max-width: 850px; }
  .wiki-sec { margin-top: 14px; }
  .wiki-sec h3 { margin: 0 0 6px; font-size: 12px; text-transform: uppercase; letter-spacing: 0.05em; color: var(--accent); }
  .wiki-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 4px 16px; margin: 4px 0; }
  .wiki-k { color: var(--muted); margin-right: 6px; font-size: 11px; text-transform: uppercase; letter-spacing: 0.04em; }
  .wiki-v { color: var(--text); }
  .wiki-table { width: 100%; border-collapse: collapse; background: var(--bg); border: 1px solid var(--border); border-radius: 6px; overflow: hidden; font-size: 12px; margin-top: 4px; }
  .wiki-table th, .wiki-table td { padding: 6px 10px; border-bottom: 1px solid var(--border); text-align: left; }
  .wiki-table th { background: var(--panel); color: var(--muted); font-size: 10px; text-transform: uppercase; letter-spacing: 0.05em; }
  .wiki-sec ul { margin: 4px 0; padding-left: 20px; }
  .wiki-sec li { margin-bottom: 3px; }
"""


def trim_card(row: dict) -> dict:
    """Flatten + slim each row so the embedded payload only carries fields the viewer reads."""
    mc = row.get("model_card") or {}
    identity = mc.get("identity") or {}
    part = mc.get("particle_content") or {}
    dm = part.get("dark_matter_candidate") or {}
    inter = mc.get("interactions") or {}
    return {
        "paper_id": row.get("paper_id"),
        "model_id": mc.get("model_id"),
        "name": identity.get("name"),
        "family": identity.get("family"),
        "model_kind": identity.get("model_kind"),
        "status": identity.get("status"),
        "aliases": identity.get("aliases") or [],
        "description": identity.get("short_description"),
        "candidate": dm.get("name"),
        "spin": dm.get("spin"),
        "portals": inter.get("portals") or [],
        # Card sub-trees displayed in the detail pane.
        "card": {
            "identity": identity,
            "particle_content": part,
            "interactions": inter,
            "theory": mc.get("theory"),
            "symmetries": mc.get("symmetries"),
            "production": mc.get("production"),
            "relic_density": mc.get("relic_density"),
            "cosmological_history": mc.get("cosmological_history"),
            "phase_space": mc.get("phase_space"),
            "structure_formation": mc.get("structure_formation"),
            "parameters": mc.get("parameters"),
            "validity_domain": mc.get("validity_domain"),
            "assumptions": mc.get("assumptions"),
            "robustness": mc.get("robustness"),
            "agent_failure_modes": mc.get("agent_failure_modes"),
            "provenance": {
                "sources": (mc.get("provenance") or {}).get("sources"),
                "extraction": (mc.get("provenance") or {}).get("extraction"),
                "review": (mc.get("provenance") or {}).get("review"),
                "caveats": (mc.get("provenance") or {}).get("caveats"),
            },
        },
    }


# ----------------------------------------------------------------------------
# main
# ----------------------------------------------------------------------------

def load_jsonl(path: Path):
    rows = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_viewer(path: Path, title: str, page_id: str, rows, panels: str, table: str, app_js: str,
                 source_label: str | None = None, extra_css: str = "") -> None:
    src = source_label if source_label is not None else f"models/{path.stem.replace('viewer_', '')}.jsonl"
    subtitle = f"{len(rows):,} rows · source: {src}"
    payload = json.dumps(rows, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/")
    html_text = shell(title, subtitle, page_id, panels, table, app_js, payload, extra_css=extra_css)
    path.write_text(html_text, encoding="utf-8")
    print(f"  wrote {path.relative_to(REGISTRY)}  ({path.stat().st_size / 1024:.1f} KB, {len(rows):,} rows)")


HOSTED_SHARDS = 256


def shard_of(model_id: str) -> str:
    """Two-hex-digit shard id; must match shardOf() in HOSTED_WIKI_JS."""
    h = 0
    for ch in model_id:
        h = (h * 31 + ord(ch)) & 0xFFFFFFFF
    return f"{h % HOSTED_SHARDS:02x}"


HOSTED_WIKI_JS_LOADER = r"""
  // Hosted variant: card detail subtrees live in darkmatterwiki_data/shard-XX.json
  // and are fetched the first time a row is expanded.
  const DATA_DIR = 'darkmatterwiki_data/';
  const shardCache = {};
  function shardOf(id) {
    let h = 0;
    for (let i = 0; i < id.length; i++) h = (Math.imul(h, 31) + id.charCodeAt(i)) >>> 0;
    return (h % 256).toString(16).padStart(2, '0');
  }
  function loadCard(r) {
    if (r.card || r._loading) return;
    r._loading = true;
    const sh = shardOf(r.model_id);
    const p = shardCache[sh] || (shardCache[sh] = fetch(DATA_DIR + 'shard-' + sh + '.json')
      .then(x => { if (!x.ok) throw new Error('HTTP ' + x.status); return x.json(); }));
    p.then(m => { r.card = m[r.model_id] || {}; r._loading = false; render(); })
     .catch(e => { r.card = { _error: String(e) }; r._loading = false; render(); });
  }
"""


def hosted_wiki_js() -> str:
    js = WIKI_JS
    a = "    const c = r.card || {};\n"
    b = ("    const c = r.card || {};\n"
         "    if (c._error) return `<div class=\"muted\">Could not load card details (${esc(c._error)}).</div>`;\n")
    assert js.count(a) == 1, "detailHTML anchor"
    js = js.replace(a, b)
    a = ("      const detail = expanded ? `<tr class=\"detail-row\" data-key=\"${esc(r.model_id)}-d\">"
         "<td colspan=\"6\">${detailHTML(r)}</td></tr>` : '';")
    b = ("      const detail = !expanded ? '' : (r.card\n"
         "        ? `<tr class=\"detail-row\" data-key=\"${esc(r.model_id)}-d\"><td colspan=\"6\">${detailHTML(r)}</td></tr>`\n"
         "        : (loadCard(r), `<tr class=\"detail-row\" data-key=\"${esc(r.model_id)}-d\"><td colspan=\"6\">"
         "<div class=\"muted\">Loading card details…</div></td></tr>`));")
    assert js.count(a) == 1, "render anchor"
    js = js.replace(a, b)
    a = "  function render() {"
    assert js.count(a) == 1, "render fn anchor"
    return js.replace(a, HOSTED_WIKI_JS_LOADER + a)


def build_hosted_wiki() -> int:
    out_dir = REGISTRY / "hosted"
    data_dir = out_dir / "darkmatterwiki_data"
    data_dir.mkdir(parents=True, exist_ok=True)
    for old in data_dir.glob("shard-*.json"):
        old.unlink()
    rows = [trim_card(r) for r in load_jsonl(REGISTRY / "models" / "all_outputs_combined.jsonl")]
    shards: dict[str, dict] = {}
    index = []
    for r in rows:
        card = r.pop("card")
        shards.setdefault(shard_of(r["model_id"]), {})[r["model_id"]] = card
        index.append(r)
    total = 0
    for sh, cards in sorted(shards.items()):
        p = data_dir / f"shard-{sh}.json"
        p.write_text(json.dumps(cards, separators=(",", ":"), ensure_ascii=False), encoding="utf-8")
        total += p.stat().st_size
    print(f"  wrote {len(shards)} shards to {data_dir.relative_to(REGISTRY)}/  ({total / 1024 / 1024:.1f} MB)")
    path = out_dir / "darkmatterwiki.html"
    subtitle = f"{len(index):,} rows · source: models/all_outputs_combined.jsonl · card details load on demand"
    payload = json.dumps(index, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/")
    path.write_text(shell("darkmatterwiki", subtitle, "darkmatterwiki", WIKI_PANELS, WIKI_TABLE,
                          hosted_wiki_js(), payload, extra_css=WIKI_EXTRA_CSS), encoding="utf-8")
    print(f"  wrote {path.relative_to(REGISTRY)}  ({path.stat().st_size / 1024:.1f} KB, {len(index):,} rows)")
    return 0


def main() -> int:
    if "--hosted" in sys.argv[1:]:
        print("building hosted darkmatterwiki…")
        return build_hosted_wiki()
    print("building HTML viewers…")
    wiki_rows = [trim_card(r) for r in load_jsonl(REGISTRY / "models" / "all_outputs_combined.jsonl")]
    write_viewer(
        REGISTRY / "darkmatterwiki.html",
        "darkmatterwiki",
        "darkmatterwiki",
        wiki_rows,
        WIKI_PANELS,
        WIKI_TABLE,
        WIKI_JS,
        source_label="models/all_outputs_combined.jsonl",
        extra_css=WIKI_EXTRA_CSS,
    )
    write_viewer(
        REGISTRY / "ranking.html",
        "Ranking viewer",
        "ranking",
        load_jsonl(REGISTRY / "models" / "ranking_full_ranked.jsonl"),
        RANKING_PANELS,
        RANKING_TABLE,
        RANKING_JS,
    )
    write_viewer(
        REGISTRY / "enrichment_status.html",
        "Enrichment status viewer",
        "enrichment_status",
        load_jsonl(REGISTRY / "models" / "enrichment_all_paper_status.jsonl"),
        ENRICH_STATUS_PANELS,
        ENRICH_STATUS_TABLE,
        ENRICH_STATUS_JS,
    )
    write_viewer(
        REGISTRY / "enrichment_outputs.html",
        "Enrichment outputs viewer",
        "enrichment_outputs",
        load_jsonl(REGISTRY / "models" / "enrichment_all_outputs.jsonl"),
        ENRICH_OUT_PANELS,
        ENRICH_OUT_TABLE,
        ENRICH_OUT_JS,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
