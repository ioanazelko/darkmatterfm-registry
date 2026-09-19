#!/usr/bin/env python3
"""Build a self-contained HTML browser for the DarkMatterFM schema suite.

Reads every ``*.schema.yaml`` in ``registry/schemas/`` and writes
``registry/schema_browser.html``: one dependency-free page that renders all
schemas as a navigable tree (every section and field with its description,
type, enum values, examples, required flag) with ``$ref`` links resolved
across files and a stable anchor per node, so a paper can deep-link, e.g.
``schema_browser.html#bsm_model/agent_failure_modes`` or
``schema_browser.html#route/defs/route``.

Usage:  python3 build_schema_browser.py
"""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

import yaml

REGISTRY = Path(__file__).resolve().parent
SCHEMA_DIR = REGISTRY / "schemas"
OUT_HTML = REGISTRY / "schema_browser.html"

# Order in which files are shown (top-level card first, then components).
ORDER = ["bsm_model", "common", "observable", "constraint", "route",
         "provenance", "code"]

KNOWN_KEYS = {
    "type", "description", "properties", "required", "items", "enum",
    "examples", "pattern", "$ref", "anyOf", "oneOf", "allOf",
    "additionalProperties", "title", "$defs", "default", "const",
    "minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum",
    "minItems", "maxItems", "uniqueItems", "format", "minLength",
    "maxLength", "$schema", "$id", "$comment", "deprecated",
}


def esc(s) -> str:
    return html.escape(str(s), quote=True)


def stem_of(fname: str) -> str:
    return fname.replace(".schema.yaml", "")


def load_schemas() -> dict[str, dict]:
    out = {}
    for f in SCHEMA_DIR.glob("*.schema.yaml"):
        out[stem_of(f.name)] = {"raw": f.read_text(encoding="utf-8"),
                                "doc": yaml.safe_load(f.read_text(encoding="utf-8")),
                                "file": f.name}
    missing = [s for s in ORDER if s not in out]
    if missing:
        raise SystemExit(f"schemas missing from {SCHEMA_DIR}: {missing}")
    extra = [s for s in out if s not in ORDER]
    return {s: out[s] for s in ORDER + sorted(extra)}


def ref_to_anchor(ref: str, current: str) -> tuple[str, str]:
    """Map a $ref to (anchor id, display label)."""
    if "#" in ref:
        fpart, frag = ref.split("#", 1)
    else:
        fpart, frag = ref, ""
    target = stem_of(fpart) if fpart else current
    frag = frag.lstrip("/")
    parts = [p for p in frag.split("/") if p]
    parts = [("defs" if p == "$defs" else p) for p in parts if p != "properties"]
    anchor = "/".join([target] + parts)
    label = f"{target}#{'/'.join(parts)}" if parts else target
    return anchor, label


class Renderer:
    def __init__(self, schemas: dict[str, dict]):
        self.schemas = schemas
        self.backrefs: dict[str, list[str]] = {}   # anchor -> [anchor of referrer]
        self.nodes: list[tuple[str, str, str]] = []  # (anchor, name, description) for search

    # ---- pass 1: collect back-references -------------------------------
    def collect(self):
        for stem, s in self.schemas.items():
            self._walk_refs(s["doc"], stem, [stem])

    def _walk_refs(self, node, stem, path):
        if isinstance(node, dict):
            if "$ref" in node and isinstance(node["$ref"], str):
                anchor, _ = ref_to_anchor(node["$ref"], stem)
                self.backrefs.setdefault(anchor, []).append("/".join(path))
            for k, v in node.items():
                if k == "properties" and isinstance(v, dict):
                    for pk, pv in v.items():
                        self._walk_refs(pv, stem, path + [pk])
                elif k == "$defs" and isinstance(v, dict):
                    for dk, dv in v.items():
                        self._walk_refs(dv, stem, path + ["defs", dk])
                elif k in ("items", "anyOf", "oneOf", "allOf", "additionalProperties"):
                    if isinstance(v, list):
                        for it in v:
                            self._walk_refs(it, stem, path)
                    else:
                        self._walk_refs(v, stem, path)
        elif isinstance(node, list):
            for it in node:
                self._walk_refs(it, stem, path)

    # ---- pass 2: render ------------------------------------------------
    def type_label(self, node) -> str:
        t = node.get("type")
        if isinstance(t, list):
            t = " | ".join(t)
        if t == "array" and isinstance(node.get("items"), dict):
            inner = node["items"]
            if "$ref" in inner:
                return "array of ref"
            it = inner.get("type")
            if isinstance(it, list):
                it = " | ".join(it)
            return f"array of {it}" if it else "array"
        if not t and "$ref" in node:
            return "ref"
        if not t and any(k in node for k in ("anyOf", "oneOf", "allOf")):
            return next(k for k in ("anyOf", "oneOf", "allOf") if k in node)
        if not t and "enum" in node:
            return "enum"
        if not t and "const" in node:
            return "const"
        return t or "object"

    def render_ref(self, ref: str, stem: str) -> str:
        anchor, label = ref_to_anchor(ref, stem)
        return f'<a class="ref" href="#{esc(anchor)}">{esc(label)}</a>'

    def render_node(self, name: str, node, stem: str, path: list[str],
                    required: bool = False, depth: int = 0) -> str:
        anchor = "/".join(path)
        if not isinstance(node, dict):
            return (f'<div class="node" id="{esc(anchor)}"><div class="head">'
                    f'<span class="name">{esc(name)}</span> '
                    f'<span class="type">{esc(json.dumps(node))}</span></div></div>')
        desc = node.get("description", "")
        self.nodes.append((anchor, name, desc if isinstance(desc, str) else ""))

        props = node.get("properties") or {}
        req = set(node.get("required") or [])
        items = node.get("items") if isinstance(node.get("items"), dict) else None
        combos = [(k, node[k]) for k in ("anyOf", "oneOf", "allOf") if isinstance(node.get(k), list)]
        has_children = bool(props) or (items is not None and (items.get("properties") or items.get("enum") or items.get("anyOf") or items.get("oneOf"))) or bool(combos)

        badges = []
        badges.append(f'<span class="type">{esc(self.type_label(node))}</span>')
        if required:
            badges.append('<span class="badge req">required</span>')
        if node.get("additionalProperties") is False and (node.get("type") == "object" or props):
            badges.append('<span class="badge closed" title="additionalProperties: false">closed</span>')
        if node.get("deprecated"):
            badges.append('<span class="badge dep">deprecated</span>')
        if "$ref" in node:
            badges.append("&rarr; " + self.render_ref(node["$ref"], stem))
        if items is not None and "$ref" in items:
            badges.append("&rarr; " + self.render_ref(items["$ref"], stem))

        body = []
        if desc:
            body.append(f'<p class="desc">{esc(desc)}</p>')

        # scalar-ish facets on the node itself and on array items
        for label, src in (("", node), ("items ", items or {})):
            if not src:
                continue
            if "enum" in src:
                chips = "".join(f'<code class="enum">{esc(v)}</code>' for v in src["enum"])
                body.append(f'<div class="facet"><span class="k">{label}enum</span>{chips}</div>')
            if "const" in src:
                body.append(f'<div class="facet"><span class="k">{label}const</span><code>{esc(src["const"])}</code></div>')
            if "examples" in src:
                ex = src["examples"]
                if not isinstance(ex, list):
                    ex = [ex]
                chips = "".join(f'<code class="ex">{esc(v if isinstance(v, str) else json.dumps(v))}</code>' for v in ex)
                body.append(f'<div class="facet"><span class="k">{label}examples</span>{chips}</div>')
            if "pattern" in src:
                body.append(f'<div class="facet"><span class="k">{label}pattern</span><code>{esc(src["pattern"])}</code></div>')
            for k in ("default", "format", "minimum", "maximum", "exclusiveMinimum",
                      "exclusiveMaximum", "minItems", "maxItems", "uniqueItems",
                      "minLength", "maxLength", "$comment"):
                if k in src:
                    v = src[k]
                    body.append(f'<div class="facet"><span class="k">{label}{esc(k)}</span><code>{esc(v if isinstance(v, str) else json.dumps(v))}</code></div>')
            other = {k: v for k, v in src.items() if k not in KNOWN_KEYS}
            for k, v in other.items():
                body.append(f'<div class="facet"><span class="k">{label}{esc(k)}</span><code>{esc(json.dumps(v, default=str))}</code></div>')

        back = self.backrefs.get(anchor)
        if back:
            links = ", ".join(f'<a href="#{esc(b)}">{esc(b)}</a>' for b in sorted(set(back)))
            body.append(f'<div class="facet backrefs"><span class="k">used by</span>{links}</div>')

        children = []
        for pk, pv in props.items():
            children.append(self.render_node(pk, pv, stem, path + [pk], pk in req, depth + 1))
        if items is not None and (items.get("properties") or items.get("anyOf") or items.get("oneOf")):
            ireq = set(items.get("required") or [])
            for pk, pv in (items.get("properties") or {}).items():
                children.append(self.render_node(pk, pv, stem, path + [pk], pk in ireq, depth + 1))
            for k in ("anyOf", "oneOf"):
                if isinstance(items.get(k), list):
                    for i, alt in enumerate(items[k]):
                        children.append(self.render_node(f"{k}[{i}]", alt, stem, path + [f"{k}{i}"], False, depth + 1))
        for k, alts in combos:
            for i, alt in enumerate(alts):
                children.append(self.render_node(f"{k}[{i}]", alt, stem, path + [f"{k}{i}"], False, depth + 1))

        open_attr = " open" if depth <= 1 else ""
        n_children = len(children)
        count = f'<span class="count">{n_children} field{"s" if n_children != 1 else ""}</span>' if n_children else ""
        head = (f'<span class="name">{esc(name)}</span> {" ".join(badges)} {count}'
                f'<a class="anchor" href="#{esc(anchor)}" title="permalink">#</a>')
        if children:
            return (f'<details class="node d{min(depth,4)}" id="{esc(anchor)}"{open_attr}>'
                    f'<summary class="head">{head}</summary>'
                    f'<div class="body">{"".join(body)}<div class="children">{"".join(children)}</div></div>'
                    f'</details>')
        return (f'<div class="node leaf d{min(depth,4)}" id="{esc(anchor)}"><div class="head">{head}</div>'
                f'<div class="body">{"".join(body)}</div></div>')

    def render_file(self, stem: str) -> tuple[str, str]:
        s = self.schemas[stem]
        doc = s["doc"]
        title = doc.get("title", stem)
        desc = doc.get("description", "")
        sid = doc.get("$id", "")
        parts = []
        parts.append(f'<section class="file" id="{esc(stem)}">')
        parts.append(f'<h2><code>{esc(s["file"])}</code> &mdash; {esc(title)}'
                     f'<a class="anchor" href="#{esc(stem)}">#</a></h2>')
        if desc:
            parts.append(f'<p class="desc">{esc(desc)}</p>')
        meta = []
        if sid:
            meta.append(f'<span><span class="k">$id</span> <code>{esc(sid)}</code></span>')
        if doc.get("$schema"):
            meta.append(f'<span><span class="k">$schema</span> <code>{esc(doc["$schema"])}</code></span>')
        if doc.get("type"):
            meta.append(f'<span><span class="k">type</span> <code>{esc(doc["type"])}</code></span>')
        if doc.get("additionalProperties") is False:
            meta.append('<span class="badge closed">closed object</span>')
        parts.append(f'<div class="meta">{" ".join(meta)}</div>')

        nav = []
        props = doc.get("properties") or {}
        req = set(doc.get("required") or [])
        if props:
            parts.append(f'<h3>Properties <span class="count">{len(props)}</span></h3>')
            for pk, pv in props.items():
                parts.append(self.render_node(pk, pv, stem, [stem, pk], pk in req, 1))
                nav.append((f"{stem}/{pk}", pk, pk in req))
        defs = doc.get("$defs") or {}
        if defs:
            parts.append(f'<h3>Definitions (<code>$defs</code>) <span class="count">{len(defs)}</span></h3>')
            for dk, dv in defs.items():
                parts.append(self.render_node(dk, dv, stem, [stem, "defs", dk], False, 1))
                nav.append((f"{stem}/defs/{dk}", dk, False))
        parts.append(f'<details class="raw"><summary>Raw YAML source of <code>{esc(s["file"])}</code></summary>'
                     f'<pre>{esc(s["raw"])}</pre></details>')
        parts.append("</section>")

        navhtml = [f'<div class="navfile"><a href="#{esc(stem)}">{esc(s["file"])}</a></div>']
        for a, n, r in nav:
            navhtml.append(f'<a class="navitem{" req" if r else ""}" href="#{esc(a)}">{esc(n)}</a>')
        return "".join(parts), "".join(navhtml)


CSS = """
:root{--bg:#fff;--fg:#1b1f23;--muted:#5c6470;--line:#e1e4e8;--accent:#0b5fff;--chip:#f1f3f5;--req:#b42318;--reqbg:#fde8e6;--closed:#5b4b00;--closedbg:#fff4c2;--depbg:#eee}
*{box-sizing:border-box}
body{margin:0;font:14px/1.45 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:var(--fg);background:var(--bg)}
a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}
code{font:12.5px/1.4 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;background:var(--chip);padding:1px 5px;border-radius:4px}
pre{font:12px/1.4 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;background:#f6f8fa;padding:12px;border-radius:6px;overflow:auto;max-height:70vh}
header{position:sticky;top:0;z-index:5;background:var(--bg);border-bottom:1px solid var(--line);padding:10px 20px;display:flex;gap:16px;align-items:center;flex-wrap:wrap}
header h1{font-size:18px;margin:0}
header .sub{color:var(--muted);font-size:13px}
header input{flex:1;min-width:220px;max-width:480px;padding:6px 10px;border:1px solid var(--line);border-radius:6px;font-size:14px}
.layout{display:flex;align-items:flex-start}
nav{width:270px;flex:none;position:sticky;top:56px;max-height:calc(100vh - 56px);overflow:auto;padding:12px 8px 40px 16px;border-right:1px solid var(--line);font-size:13px}
nav .navfile{margin:12px 0 4px;font-weight:600}
nav .navitem{display:block;padding:1px 8px;color:var(--fg);border-radius:4px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
nav .navitem.req::after{content:" *";color:var(--req)}
nav .navitem:hover{background:var(--chip);text-decoration:none}
main{flex:1;min-width:0;padding:16px 28px 80px}
section.file{margin-bottom:48px;padding-top:8px}
h2{font-size:20px;margin:24px 0 6px;border-bottom:2px solid var(--line);padding-bottom:6px}
h3{font-size:15px;margin:22px 0 8px;color:var(--muted);text-transform:uppercase;letter-spacing:.04em}
.meta{display:flex;gap:16px;flex-wrap:wrap;color:var(--muted);font-size:12.5px;margin:6px 0 10px}
.k{color:var(--muted);font-size:11.5px;text-transform:uppercase;letter-spacing:.04em;margin-right:8px}
.count{color:var(--muted);font-size:12px;font-weight:400;margin-left:6px}
.node{border-left:2px solid var(--line);margin:4px 0 4px 0;padding-left:10px}
.node.d1{border-left-color:#c7d2fe;margin-top:10px}
.node.leaf{padding:2px 0 2px 10px}
.head{cursor:default;padding:3px 0}
details>summary.head{cursor:pointer;list-style:none}
details>summary.head::before{content:"\\25B8";display:inline-block;width:14px;color:var(--muted);transition:transform .1s}
details[open]>summary.head::before{transform:rotate(90deg)}
.name{font-weight:600;font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:13.5px}
.type{color:var(--muted);font-size:12.5px;margin-left:6px}
.badge{font-size:11px;padding:1px 6px;border-radius:10px;margin-left:6px;vertical-align:middle}
.badge.req{color:var(--req);background:var(--reqbg)}
.badge.closed{color:var(--closed);background:var(--closedbg)}
.badge.dep{background:var(--depbg)}
a.ref{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:12.5px}
a.anchor{opacity:0;margin-left:8px;color:var(--muted)}
.head:hover a.anchor{opacity:1}
.body{padding:2px 0 4px 16px}
p.desc{margin:2px 0 6px;max-width:90ch}
.facet{margin:3px 0;line-height:1.9}
.facet code.enum{margin-right:4px;background:#e8f0fe}
.facet code.ex{margin-right:4px;background:#f0f0f0;color:#444}
.facet.backrefs a{margin-right:6px;font-size:12.5px}
details.raw{margin-top:18px}
details.raw>summary{cursor:pointer;color:var(--muted)}
:target{outline:2px solid var(--accent);outline-offset:2px;border-radius:4px;background:#f3f7ff}
.hidden{display:none!important}
#hits{color:var(--muted);font-size:12.5px}
.intro{max-width:100ch;color:var(--muted);margin:10px 0 0}
.intro code{background:var(--chip)}
"""

JS = """
(function(){
  function openAncestors(el){
    var p=el; while(p){ if(p.tagName==='DETAILS') p.open=true; p=p.parentElement; }
  }
  function goHash(){
    var h=decodeURIComponent(location.hash.slice(1)); if(!h) return;
    var el=document.getElementById(h); if(!el) return;
    openAncestors(el); if(el.tagName==='DETAILS') el.open=true;
    var go=function(){ el.scrollIntoView({block:'start'}); window.scrollBy(0,-64); };
    requestAnimationFrame(go); setTimeout(go,150); setTimeout(go,500);
  }
  window.addEventListener('hashchange',goHash); window.addEventListener('load',goHash);
  var box=document.getElementById('q'), hits=document.getElementById('hits');
  var nodes=Array.prototype.slice.call(document.querySelectorAll('.node'));
  var idx=nodes.map(function(n){return (n.id+' '+((n.querySelector('.body>p.desc')||{}).textContent||'')).toLowerCase();});
  var t=null;
  box.addEventListener('input',function(){
    clearTimeout(t); t=setTimeout(function(){
      var q=box.value.trim().toLowerCase();
      if(!q){ nodes.forEach(function(n){n.classList.remove('hidden');}); hits.textContent=''; return; }
      var keep=new Set(); var count=0;
      nodes.forEach(function(n,i){ if(idx[i].indexOf(q)>=0){ count++; var p=n; while(p){ if(p.classList&&p.classList.contains('node')) keep.add(p); p=p.parentElement; } } });
      nodes.forEach(function(n){ if(keep.has(n)){ n.classList.remove('hidden'); if(n.tagName==='DETAILS') n.open=true; } else n.classList.add('hidden'); });
      hits.textContent=count+' matching field'+(count===1?'':'s');
    },120);
  });
  document.getElementById('expand').onclick=function(){document.querySelectorAll('details.node').forEach(function(d){d.open=true;});};
  document.getElementById('collapse').onclick=function(){document.querySelectorAll('details.node').forEach(function(d){d.open=false;});};
})();
"""


def main():
    schemas = load_schemas()
    r = Renderer(schemas)
    r.collect()
    sections, navs = [], []
    for stem in schemas:
        sec, nav = r.render_file(stem)
        sections.append(sec)
        navs.append(nav)
    n_files = len(schemas)
    n_nodes = len(r.nodes)
    intro = (
        "<p class=\"intro\">Every schema file is rendered as a tree of its properties and "
        "<code>$defs</code>. Each row shows the field name, its type, whether it is "
        "<span class=\"badge req\">required</span>, its description, enum values, examples and "
        "constraints; <code>&rarr;</code> links follow <code>$ref</code> targets across files, and "
        "<em>used by</em> lists every place a definition is referenced. Click a name to expand it, "
        "hover it for a permalink (e.g. <code>#bsm_model/agent_failure_modes</code>). "
        "The raw YAML of each file is at the end of its section.</p>"
    )
    page = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>DarkMatterFM schema browser</title>
<style>{CSS}</style></head>
<body>
<header>
  <div><h1>DarkMatterFM schema suite</h1>
  <div class="sub">{n_files} schema files &middot; {n_nodes} fields &middot; JSON Schema draft 2020-12 (YAML source)</div></div>
  <input id="q" type="search" placeholder="Filter fields by name or description&hellip;" autocomplete="off">
  <span id="hits"></span>
  <button id="expand" type="button">Expand all</button>
  <button id="collapse" type="button">Collapse all</button>
</header>
<div class="layout">
<nav>{"".join(navs)}</nav>
<main>{intro}{"".join(sections)}</main>
</div>
<script>{JS}</script>
</body></html>"""
    OUT_HTML.write_text(page, encoding="utf-8")
    print(f"wrote {OUT_HTML} ({OUT_HTML.stat().st_size/1024:.0f} KB, {n_files} files, {n_nodes} fields)")


if __name__ == "__main__":
    main()
