#!/usr/bin/env python3
"""Build the self-contained HTML grading interface for the accuracy study.

Reads accuracy_study/accuracy_sample_manifest.jsonl (from
draw_accuracy_sample.py) and writes accuracy_study/accuracy_grading.html:
a dependency-free page that shows each sampled card section by section next
to its arXiv link, records per-section verdicts + notes, persists progress in
localStorage, and exports grades as JSONL (one row per card).

Usage:
    python scripts/build_accuracy_grader.py
"""

from __future__ import annotations

import html
import json
import sys
from pathlib import Path

import yaml

REGISTRY = Path(__file__).resolve().parents[1] / "registry"
MANIFEST = REGISTRY / "accuracy_study" / "accuracy_sample_manifest.jsonl"
OUT = REGISTRY / "accuracy_study" / "accuracy_grading.html"

SKIP_SECTIONS = {"schema_version", "model_id", "provenance"}
VERDICTS = ["correct", "partially_correct", "incorrect", "hallucinated", "cannot_judge"]


def section_yaml(value) -> str:
    return yaml.safe_dump(value, sort_keys=False, allow_unicode=True, width=90)


def main() -> int:
    cards = []
    with MANIFEST.open() as f:
        for line in f:
            row = json.loads(line)
            card = row.pop("card")
            sections = []
            for key, value in card.items():
                if key in SKIP_SECTIONS or value in (None, [], {}):
                    continue
                sections.append({"name": key, "yaml": section_yaml(value)})
            row["sections"] = sections
            cards.append(row)

    data_json = json.dumps(cards).replace("</", "<\\/")
    verdicts_json = json.dumps(VERDICTS)

    page = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>DarkMatterFM extraction-accuracy grading</title>
<style>
  :root { --ok:#2e7d32; --part:#f9a825; --bad:#c62828; --hall:#6a1b9a; --cj:#546e7a; }
  * { box-sizing: border-box; }
  body { margin:0; font-family: system-ui, sans-serif; display:flex; height:100vh; }
  #side { width:290px; overflow-y:auto; border-right:1px solid #ccc; padding:10px; flex-shrink:0; }
  #main { flex:1; overflow-y:auto; padding:18px 26px; }
  h1 { font-size:17px; margin:4px 0 10px; }
  .cardlink { display:block; padding:3px 6px; font-size:12.5px; cursor:pointer;
              border-radius:4px; margin:1px 0; color:#222; text-decoration:none; }
  .cardlink:hover { background:#eee; }
  .cardlink.active { background:#dbe9ff; }
  .cardlink .done { color:var(--ok); font-weight:bold; }
  .meta { font-size:13px; color:#444; margin-bottom:12px; }
  .meta a { color:#1a58c2; }
  .section { border:1px solid #ddd; border-radius:6px; margin-bottom:14px; }
  .sec-head { display:flex; align-items:center; gap:8px; flex-wrap:wrap;
              padding:6px 10px; background:#f5f6f8; border-bottom:1px solid #ddd; }
  .sec-head b { font-family:monospace; font-size:13.5px; }
  pre { margin:0; padding:10px; font-size:12px; line-height:1.45; overflow-x:auto;
        white-space:pre-wrap; max-height:420px; overflow-y:auto; }
  .vbtn { font-size:11.5px; padding:2px 8px; border-radius:10px; border:1px solid #bbb;
          background:#fff; cursor:pointer; }
  .vbtn.sel-correct { background:var(--ok); color:#fff; border-color:var(--ok); }
  .vbtn.sel-partially_correct { background:var(--part); color:#fff; border-color:var(--part); }
  .vbtn.sel-incorrect { background:var(--bad); color:#fff; border-color:var(--bad); }
  .vbtn.sel-hallucinated { background:var(--hall); color:#fff; border-color:var(--hall); }
  .vbtn.sel-cannot_judge { background:var(--cj); color:#fff; border-color:var(--cj); }
  .note { width:100%; border:none; border-top:1px dashed #ddd; padding:6px 10px;
          font-size:12px; font-family:inherit; }
  #topbar { position:sticky; top:0; background:#fff; padding:6px 0 10px; z-index:5;
            border-bottom:2px solid #eee; margin-bottom:12px; }
  #grader { padding:4px 6px; }
  button.action { padding:5px 12px; margin-left:6px; cursor:pointer; }
  #progress { font-size:12.5px; color:#555; margin-left:10px; }
  textarea.overall { width:100%; min-height:52px; font-family:inherit; font-size:13px;
                     margin-top:6px; }
</style>
</head>
<body>
<div id="side"><h1>Cards (<span id="ndone">0</span>/__NCARDS__)</h1><div id="cardlist"></div></div>
<div id="main">
  <div id="topbar">
    Grader: <input id="grader" placeholder="your initials" size="10">
    <button class="action" onclick="exportGrades()">Export JSONL</button>
    <button class="action" onclick="document.getElementById('importfile').click()">Import</button>
    <input type="file" id="importfile" style="display:none" onchange="importGrades(event)">
    <span id="progress"></span>
  </div>
  <div id="cardview"></div>
</div>
<script>
const CARDS = __DATA__;
const VERDICTS = __VERDICTS__;
let current = 0;
let grades = JSON.parse(localStorage.getItem('dmfm_grades') || '{}');

function cardDone(c) {
  const g = grades[c.model_id];
  if (!g || !g.sections) return false;
  return c.sections.every(s => g.sections[s.name] && g.sections[s.name].verdict);
}
function save() { localStorage.setItem('dmfm_grades', JSON.stringify(grades)); renderList(); }
function g4(mid) {
  if (!grades[mid]) grades[mid] = {sections:{}, overall_note:''};
  return grades[mid];
}
function setVerdict(mid, sec, v) {
  const g = g4(mid);
  if (!g.sections[sec]) g.sections[sec] = {};
  g.sections[sec].verdict = (g.sections[sec].verdict === v) ? null : v;
  save(); renderCard();
}
function setNote(mid, sec, t) { const g=g4(mid); if(!g.sections[sec]) g.sections[sec]={}; g.sections[sec].note=t; save(); }
function setOverall(mid, t) { g4(mid).overall_note = t; save(); }

function renderList() {
  const el = document.getElementById('cardlist');
  el.innerHTML = '';
  let ndone = 0;
  CARDS.forEach((c, i) => {
    const done = cardDone(c); if (done) ndone++;
    const a = document.createElement('a');
    a.className = 'cardlink' + (i === current ? ' active' : '');
    a.innerHTML = (done ? '<span class="done">✓</span> ' : '&#9633; ') +
      c.model_id + '<br><small>' + c.taxonomy_class + ' · ' + c.stratum + '</small>';
    a.onclick = () => { current = i; renderCard(); renderList(); window.scrollTo(0,0); };
    el.appendChild(a);
  });
  document.getElementById('ndone').textContent = ndone;
  document.getElementById('progress').textContent =
    'card ' + (current+1) + '/' + CARDS.length;
}

function renderCard() {
  const c = CARDS[current];
  const g = g4(c.model_id);
  const v = document.getElementById('cardview');
  const absUrl = 'https://arxiv.org/abs/' + c.arxiv_id;
  const pdfUrl = 'https://arxiv.org/pdf/' + c.arxiv_id;
  let h = '<div class="meta"><b>' + c.model_id + '</b> — family <code>' + c.family +
    '</code> · class <code>' + c.taxonomy_class + '</code> · tier ' + c.tier +
    (c.enriched ? ' · enriched' : ' · base') +
    (c.schema_valid ? '' : ' · <b style="color:#c62828">schema-invalid hard case</b>') +
    '<br>source paper: <a href="' + absUrl + '" target="_blank">' + c.arxiv_id +
    ' (abstract)</a> · <a href="' + pdfUrl + '" target="_blank">PDF</a>' +
    ' — grade each section against this paper.</div>';
  c.sections.forEach(s => {
    const sg = (g.sections[s.name]) || {};
    h += '<div class="section"><div class="sec-head"><b>' + s.name + '</b>';
    VERDICTS.forEach(vd => {
      h += '<button class="vbtn ' + (sg.verdict === vd ? 'sel-' + vd : '') +
        '" onclick="setVerdict(\\'' + c.model_id + '\\',\\'' + s.name + '\\',\\'' + vd + '\\')">' +
        vd.replace('_',' ') + '</button>';
    });
    h += '</div><pre>' + escapeHtml(s.yaml) + '</pre>' +
      '<input class="note" placeholder="section note (optional)" value="' +
      escapeAttr(sg.note || '') + '" onchange="setNote(\\'' + c.model_id + '\\',\\'' +
      s.name + '\\', this.value)">' + '</div>';
  });
  h += '<div><b>Overall note for this card</b><textarea class="overall" ' +
    'onchange="setOverall(\\'' + c.model_id + '\\', this.value)">' +
    escapeHtml(g.overall_note || '') + '</textarea></div>';
  h += '<p><button class="action" onclick="prev()">&larr; previous</button>' +
    '<button class="action" onclick="next()">next &rarr;</button></p>';
  v.innerHTML = h;
}
function prev(){ if(current>0){current--; renderCard(); renderList(); window.scrollTo(0,0);} }
function next(){ if(current<CARDS.length-1){current++; renderCard(); renderList(); window.scrollTo(0,0);} }
function escapeHtml(t){ return t.replace(/&/g,'&amp;').replace(/</g,'&lt;'); }
function escapeAttr(t){ return escapeHtml(t).replace(/"/g,'&quot;'); }

function exportGrades() {
  const grader = document.getElementById('grader').value || 'anonymous';
  const lines = CARDS.filter(c => grades[c.model_id]).map(c => JSON.stringify({
    model_id: c.model_id, paper_id: c.paper_id, arxiv_id: c.arxiv_id,
    stratum: c.stratum, enriched: c.enriched, grader: grader,
    exported_at: new Date().toISOString(),
    sections: grades[c.model_id].sections,
    overall_note: grades[c.model_id].overall_note || ''
  }));
  const blob = new Blob([lines.join('\\n') + '\\n'], {type:'application/jsonl'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'accuracy_grades_' + grader + '.jsonl';
  a.click();
}
function importGrades(ev) {
  const file = ev.target.files[0]; if (!file) return;
  file.text().then(t => {
    t.trim().split('\\n').forEach(line => {
      const r = JSON.parse(line);
      grades[r.model_id] = {sections: r.sections || {}, overall_note: r.overall_note || ''};
    });
    save(); renderCard();
  });
}
localStorage.setItem('dmfm_grader_hint','1');
renderList(); renderCard();
</script>
</body>
</html>
"""
    page = page.replace("__NCARDS__", str(len(cards)))
    page = page.replace("__DATA__", data_json)
    page = page.replace("__VERDICTS__", verdicts_json)
    OUT.write_text(page)
    size_mb = OUT.stat().st_size / 1e6
    print(f"wrote {OUT} ({size_mb:.1f} MB, {len(cards)} cards)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
