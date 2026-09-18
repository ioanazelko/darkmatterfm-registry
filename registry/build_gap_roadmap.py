#!/usr/bin/env python3
"""Aggregate the full capability-gap run into the development roadmap (item #9).

Reads models/capability_gaps_full.jsonl (2,004 annotated cards), joins model
priority scores from models/ranking_full_ranked.jsonl, and groups gaps by
(gap_type, capability theme). The theme is the normalized form of the gap
description: free-text descriptions are model-specific, so normalization maps
each description onto a named capability theme via ordered keyword rules
(first match wins); unmatched gaps fall into an 'other' bucket.

Each group is weighted by the summed adjusted_priority_score of the distinct
models it blocks. Emits:
  - models/capability_gap_roadmap.jsonl  (ranked groups with member models)
  - gap_roadmap.html                     (browsable viewer, pilot-viewer style)
  - ../../capability_gap_roadmap_report.md (markdown report, project root)

Model metadata (names, arXiv ids, observable channels, route->observable map)
comes from the run's per-card inputs in ~/darkmatterfm_gap_run/cards/ (the
reboot-proof extraction of all_outputs_combined_enriched.jsonl).
"""

import html
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

REGISTRY = Path(__file__).resolve().parent
MODELS = REGISTRY / "models"
CARDS_DIR = Path.home() / "darkmatterfm_gap_run" / "cards"
OUT_JSONL = MODELS / "capability_gap_roadmap.jsonl"
OUT_HTML = REGISTRY / "gap_roadmap.html"
OUT_MD = REGISTRY.parent.parent / "capability_gap_roadmap_report.md"

# Observable channels counted as structure formation for the restricted view.
SF_CHANNELS = {"small_scale_structure", "large_scale_structure", "lyman_alpha",
               "dwarf_galaxies", "milky_way_satellites", "clusters",
               "strong_lensing"}

SEV_ORDER = ["blocks_all_observables", "blocks_key_observables",
             "degrades_precision", "minor", "unknown"]

# Ordered (theme label, regex) rules; first match on description+resolution wins.
THEME_RULES = [
    ("Lyman-α forest modeling & likelihood", r"lyman"),
    ("21-cm signal modeling & likelihood", r"21[- ]?cm"),
    ("Milky Way satellite / subhalo-count likelihood",
     r"satellite|subhalo (mass function|abundance|count)"),
    ("Stellar-stream perturbation likelihood",
     r"stellar[- ]stream|stream (gap|perturbation|density|likelihood)|\bgd-?1\b|pal ?5"),
    ("Strong-lensing substructure likelihood",
     r"strong[- ]lens|flux[- ]ratio|lensing substructure"),
    ("Indirect-detection likelihood (γ-ray / cosmic-ray / ν)",
     r"gamma[- ]ray|antiproton|fermi|icecube|positron|indirect[- ]detection|"
     r"annihilation (signal|flux|spectrum)|cherenkov|\bcta\b"),
    ("Dwarf-galaxy dynamics & density profiles", r"dwarf"),
    ("PBH formation & abundance pipeline",
     r"\bpbh\b|primordial black hole|microlensing"),
    ("PTA / stochastic GW background likelihood",
     r"\bpta\b|pulsar timing|nanograv|stochastic (gravitational[- ]wave|gw) background"),
    ("GW detector forecasts & likelihoods (LIGO/LISA/ET)",
     r"\bligo\b|\blisa\b|einstein telescope|gravitational[- ]wave"),
    ("Sterile-neutrino production solver",
     r"shi[- ]?fuller|dodelson[- ]?widrow|sterile[- ]neutrino production|"
     r"quantum[- ]kinetic|sterile-?dm\b"),
    ("Self-interacting DM halo modeling",
     r"self[- ]interact|\bsidm\b|sigma[_ ]?t ?/ ?m|gravothermal"),
    ("Axion / fuzzy-DM field solver",
     r"axion|\bfuzzy\b|soliton|minicluster|schr(o|ö)dinger[- ]poisson|misalignment"),
    ("Boltzmann-code extension (CLASS/CAMB/ETHOS)",
     r"\bclass\b|\bcamb\b|\bethos\b|boltzmann (hierarchy|code|solver)|"
     r"transfer function|linear (matter )?power"),
    ("Relic-abundance solver extension (micrOMEGAs/MadDM/DarkSUSY)",
     r"micromegas|maddm|darksusy|relic[- ](abundance|density)|freeze[- ]?(in|out)|"
     r"kinetic (equilibrium|decoupling)|boltzmann"),
    ("Nonlinear-structure emulator", r"emulator"),
    ("N-body / hydrodynamic simulation campaign",
     r"n[- ]body|hydro(dynamic)?|simulation (suite|campaign)|cosmological simulation"),
    ("Phase-transition & defect-network computation",
     r"phase transition|cosmic string|domain wall|cosmotransitions|bubble"),
    ("CMB spectral distortions", r"spectral distortion"),
    ("Isocurvature machinery", r"isocurvature"),
    ("CMB likelihood & ΔN_eff machinery",
     r"\bcmb\b|planck|n[_ ]?eff|recombination|acoustic"),
    ("BBN code extension", r"\bbbn\b|nucleosynthesis"),
    ("Direct-detection recast & likelihood",
     r"xenon|\blz\b|nuclear recoil|direct[- ]detection|panda[- ]?x|darkside|migdal|"
     r"electron recoil"),
    ("Collider / beam-dump recast",
     r"collider|\blhc\b|beam[- ]dump|fixed[- ]target|atlas|\bcms\b|monojet|babar|"
     r"belle|na62|\bship\b|faser"),
    ("Dark-photon / light-mediator constraint recast",
     r"dark photon|kinetic mixing|fifth[- ]force|light mediator"),
    ("Compact-object capture & heating",
     r"white dwarf|neutron star|capture rate|stellar cooling|supernova"),
]
THEME_RES = [(name, re.compile(pat)) for name, pat in THEME_RULES]


def classify(gap: dict) -> str:
    text = (gap.get("description", "") + " " +
            gap.get("proposed_resolution", "")).lower()
    for name, rx in THEME_RES:
        if rx.search(text):
            return name
    return "Other / unclassified"


def arxiv_id(paper_id: str) -> str:
    m = re.fullmatch(r"(\d{4})_(\d{4,5})", paper_id or "")
    if m:
        return f"{m.group(1)}.{m.group(2)}"
    m = re.fullmatch(r"([a-z-]+(?:\.[A-Z]{2})?)(\d{7})", paper_id or "")
    if m:
        return f"{m.group(1)}/{m.group(2)}"
    return paper_id or ""


def esc(x) -> str:
    return html.escape(str(x if x is not None else ""))


def load_models() -> dict:
    """model_id -> {name, family, short_description, arxiv,
                    obs_channel: {obs_id: channel},
                    route_obs: {route_id: [obs_ids]}, sf_obs: set}"""
    out = {}
    for p in CARDS_DIR.glob("*.json"):
        d = json.loads(p.read_text())
        card = d["card"]
        mid = card["model_id"]
        ident = card.get("identity") or {}
        obs_channel = {o.get("id"): o.get("channel")
                       for o in (card.get("observables") or []) if o.get("id")}
        route_obs = {}
        for r in (card.get("theory_to_observable_routing") or {}).get("routes", []):
            route_obs[r.get("id")] = r.get("observable_ids") or []
        out[mid] = {
            "name": ident.get("name") or mid,
            "family": ident.get("family") or "",
            "short_description": ident.get("short_description") or "",
            "arxiv": arxiv_id(d.get("paper_id", "")),
            "obs_channel": obs_channel,
            "route_obs": route_obs,
            "sf_obs": {oid for oid, ch in obs_channel.items()
                       if ch in SF_CHANNELS},
        }
    return out


def gap_blocks_sf(gap: dict, meta: dict) -> bool:
    """A gap counts for the structure-formation view if it blocks an observable
    in an SF channel, blocks a route leading to one, or blocks everything for a
    model that has SF observables."""
    if not meta:
        return False
    sf = meta["sf_obs"]
    if not sf:
        return False
    for oid in gap.get("blocking_observables") or []:
        if oid in sf:
            return True
    for rid in gap.get("blocking_routes") or []:
        rid_base = rid.split(":")[0]  # some entries are "route_id:step_id"
        if set(meta["route_obs"].get(rid_base, [])) & sf:
            return True
    if (not gap.get("blocking_observables") and not gap.get("blocking_routes")
            and gap.get("severity") == "blocks_all_observables"):
        return True
    return False


def main() -> None:
    rows = [json.loads(l) for l in (MODELS / "capability_gaps_full.jsonl").open()]
    meta = load_models()
    scores = {}
    for l in (MODELS / "ranking_full_ranked.jsonl").open():
        r = json.loads(l)
        s = (r.get("triage") or {}).get("adjusted_priority_score")
        scores[r["model_id"]] = s if isinstance(s, (int, float)) else 0.0

    # ---- group gaps -------------------------------------------------------
    groups: dict = defaultdict(lambda: {"members": [], "sev": Counter(),
                                        "eff": Counter()})
    for r in rows:
        mid = r["model_id"]
        m = meta.get(mid, {})
        sc = scores.get(mid, 0.0)
        for g in r["capability_gaps"]["gaps"]:
            key = (g["gap_type"], classify(g))
            grp = groups[key]
            grp["members"].append({
                "model_id": mid,
                "model_name": m.get("name", mid),
                "family": m.get("family", ""),
                "arxiv": m.get("arxiv", ""),
                "score": sc,
                "severity": g.get("severity"),
                "estimated_effort": g.get("estimated_effort"),
                "description": g.get("description"),
                "proposed_resolution": g.get("proposed_resolution"),
                "blocks_structure_formation": gap_blocks_sf(g, m),
            })
            grp["sev"][g.get("severity")] += 1
            grp["eff"][g.get("estimated_effort")] += 1

    def weight(members, sf_only=False):
        seen, w = set(), 0.0
        for mm in members:
            if sf_only and not mm["blocks_structure_formation"]:
                continue
            if mm["model_id"] not in seen:
                seen.add(mm["model_id"])
                w += mm["score"]
        return w, len(seen)

    records = []
    for (gtype, theme), grp in groups.items():
        members = sorted(grp["members"], key=lambda mm: -mm["score"])
        w_all, n_all = weight(members)
        w_sf, n_sf = weight(members, sf_only=True)
        records.append({
            "gap_type": gtype,
            "theme": theme,
            "n_gaps": len(members),
            "n_models": n_all,
            "weight": round(w_all, 1),
            "n_models_structure_formation": n_sf,
            "weight_structure_formation": round(w_sf, 1),
            "severity_counts": dict(grp["sev"]),
            "effort_counts": dict(grp["eff"]),
            "members": members,
        })
    records.sort(key=lambda rec: -rec["weight"])
    for i, rec in enumerate(records, 1):
        rec["rank"] = i
    sf_sorted = sorted([r for r in records if r["weight_structure_formation"] > 0],
                       key=lambda rec: -rec["weight_structure_formation"])
    for i, rec in enumerate(sf_sorted, 1):
        rec["rank_structure_formation"] = i

    with OUT_JSONL.open("w") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    n_gaps = sum(rec["n_gaps"] for rec in records)
    print(f"wrote {OUT_JSONL}: {len(records)} groups, {n_gaps} gaps")

    # ---- markdown report --------------------------------------------------
    def md_group(rec, sf=False):
        w = rec["weight_structure_formation"] if sf else rec["weight"]
        n = rec["n_models_structure_formation"] if sf else rec["n_models"]
        mem = [mm for mm in rec["members"]
               if not sf or mm["blocks_structure_formation"]]
        top = mem[:3]
        lines = [f"### {rec['theme']}  —  `{rec['gap_type']}`",
                 f"Priority weight {w:,.0f} across {n} models "
                 f"({rec['n_gaps']} gap entries overall). "
                 f"Severity: " + ", ".join(f"{k} × {v}" for k, v in sorted(
                     rec["severity_counts"].items(),
                     key=lambda kv: SEV_ORDER.index(kv[0]) if kv[0] in SEV_ORDER else 9)) + ". "
                 f"Effort: " + ", ".join(f"{k} × {v}" for k, v in
                                         rec["effort_counts"].items()) + ".", ""]
        for mm in top:
            lines.append(f"- **{mm['model_name']}** "
                         f"([arXiv:{mm['arxiv']}](https://arxiv.org/abs/{mm['arxiv']}), "
                         f"score {mm['score']:.0f}): {mm['description']}\n"
                         f"  *Proposed resolution:* {mm['proposed_resolution']}")
        if len(mem) > len(top):
            lines.append(f"- … and {len(mem) - len(top)} more models "
                         f"(see `gap_roadmap.html`).")
        lines.append("")
        return "\n".join(lines)

    md = ["# Capability-gap development roadmap (item #9, application A7)", "",
          f"Built from the full run: **2,004 annotated model cards, "
          f"{n_gaps} capability-gap entries** in "
          f"`registry/models/capability_gaps_full.jsonl`, grouped into "
          f"**{len(records)} (gap type, capability theme) groups** and weighted "
          f"by the summed `adjusted_priority_score` of the models each group "
          f"blocks (from `ranking_full_ranked.jsonl`).", "",
          "A *theme* is the normalized capability behind many model-specific "
          "gap descriptions (e.g. every \"no Lyman-α likelihood for this "
          "model's transfer function\" lands in the Lyman-α theme). The "
          "browsable version with every member model is "
          "`registry/gap_roadmap.html`; machine-readable groups are in "
          "`registry/models/capability_gap_roadmap.jsonl`.", "",
          "## Top gaps overall", ""]
    for rec in records[:20]:
        md.append(md_group(rec))
    md += ["## Top gaps blocking structure-formation observables", "",
           "Restricted to gap entries that block an observable in a "
           "structure-formation channel (" + ", ".join(sorted(SF_CHANNELS)) +
           "), a route leading to one, or everything for a model with such "
           "observables; re-weighted accordingly.", ""]
    for rec in sf_sorted[:20]:
        md.append(md_group(rec, sf=True))
    OUT_MD.write_text("\n".join(md))
    print(f"wrote {OUT_MD}")

    # ---- HTML viewer ------------------------------------------------------
    parts = ["""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>Capability-gap development roadmap</title><style>
body{font-family:system-ui,sans-serif;margin:20px auto;max-width:1100px;padding:0 14px}
h1{font-size:20px} h2{font-size:16px;margin-top:34px;background:#f0f2f5;
padding:8px 12px;border-radius:6px}
h3{font-size:14px;margin:22px 0 2px}
.summary{background:#f5f6f8;border-radius:8px;padding:10px 16px;font-size:13.5px}
.defs{border:1px solid #cfd8e3;background:#fbfcfe;border-radius:8px;
padding:4px 18px 12px;margin:14px 0;font-size:13.5px;line-height:1.5}
.defs h3{margin:10px 0 4px;font-size:15px}
.defs dt{font-weight:bold;margin-top:8px} .defs dd{margin:2px 0 0 14px}
.meta{color:#666;font-size:12.5px}
.member{border:1px solid #ddd;border-left:4px solid #888;border-radius:4px;
padding:8px 12px;margin:8px 0;font-size:13px}
.member a{color:#1a58c2}
details{margin:4px 0 14px} summary{cursor:pointer;font-size:13px;color:#1a58c2}
.badge{display:inline-block;background:#eef1f5;border-radius:10px;
padding:1px 9px;font-size:12px;margin-right:6px}
</style></head><body>
<h1>Capability-gap development roadmap (item #9, application A7)</h1>"""]
    parts.append(
        f'<div class="summary">Full production run: <b>2,004 model cards</b> '
        f'annotated · <b>{n_gaps} gap entries</b> · grouped into '
        f'<b>{len(records)} capability groups</b>, ranked by the summed '
        f'priority score of the models each group blocks. Two views: overall, '
        f'and restricted to structure-formation observables. Source data: '
        f'<code>models/capability_gaps_full.jsonl</code>; groups: '
        f'<code>models/capability_gap_roadmap.jsonl</code>.</div>')
    parts.append("""
<div class="defs">
<h3>Definitions — read this first</h3>
<p><b>The idea.</b> Every model card contains <b>routes</b>: recipes for
testing that model against data (theory &rarr; equations &rarr; predicted
observable &rarr; comparison with measurements). The gap run asked, for every
step of every recipe of every model: <i>does the tool to do this step actually
exist?</i> Whatever is missing became a <b>gap</b> entry. This page aggregates
those entries into a development roadmap: which missing capabilities block the
most high-priority models.</p>
<dl>
<dt>capability theme</dt><dd>The shared missing capability behind many
model-specific gap descriptions — e.g. every variant of "no Lyman-&alpha;
likelihood exists for this model's power-spectrum cutoff" lands in the
Lyman-&alpha; theme. One theme may appear under several gap types (a missing
piece of software vs. a missing statistical comparison for the same probe).</dd>
<dt>gap type</dt><dd><b>theory</b> — a framework nobody has worked out;
<b>derivation</b> — a doable-but-not-done calculation; <b>tool</b> — missing
software; <b>simulation</b> — missing N-body/hydro runs; <b>emulator</b> — a
fast surrogate for such runs; <b>likelihood</b> — the statistical machinery to
compare a prediction with a specific dataset; <b>data</b> — a needed
measurement; <b>calibration</b> — an existing method with unmeasured
inputs.</dd>
<dt>priority weight</dt><dd>The sum of the observational-priority scores
(<code>adjusted_priority_score</code> from the ranking pass) of the distinct
models blocked by the group. A high weight means: closing this one gap
unblocks many high-priority models.</dd>
<dt>severity</dt><dd><b>blocks_all_observables</b> — the model cannot be
confronted with data at all; <b>blocks_key_observables</b> — its most
constraining observables are out of reach; <b>degrades_precision</b> —
testable, with avoidable error; <b>minor</b> — convenience gap.</dd>
<dt>effort</dt><dd><b>small</b> — days-to-weeks for one person; <b>medium</b>
— a focused project, months; <b>large</b> — a substantial collaboration
effort; <b>major_program</b> — a multi-year program.</dd>
<dt>structure-formation view</dt><dd>Same groups, but counting only gap
entries that block an observable in a structure-formation channel
(""" + esc(", ".join(sorted(SF_CHANNELS))) + """), a route leading to one, or
everything for a model that has such observables.</dd>
</dl></div>""")

    def html_group(rec, sf=False):
        w = rec["weight_structure_formation"] if sf else rec["weight"]
        rank = rec.get("rank_structure_formation") if sf else rec["rank"]
        n = rec["n_models_structure_formation"] if sf else rec["n_models"]
        mem = [mm for mm in rec["members"]
               if not sf or mm["blocks_structure_formation"]]
        sev = " · ".join(f"{k} × {v}" for k, v in sorted(
            rec["severity_counts"].items(),
            key=lambda kv: SEV_ORDER.index(kv[0]) if kv[0] in SEV_ORDER else 9))
        eff = " · ".join(f"{k} × {v}" for k, v in rec["effort_counts"].items())
        out = [f"<h3>{rank}. {esc(rec['theme'])}</h3>",
               f"<div class='meta'><span class='badge'>{esc(rec['gap_type'])}</span>"
               f"priority weight <b>{w:,.0f}</b> · {n} models · "
               f"{len(mem)} gap entries<br>severity: {esc(sev)}<br>"
               f"effort: {esc(eff)}</div>"]
        shown = mem[:8]
        blocks = []
        for mm in shown:
            ax = mm["arxiv"]
            blocks.append(
                f"<div class='member'><b>{esc(mm['model_name'])}</b> "
                f"<span class='meta'>(<a href='https://arxiv.org/abs/{ax}' "
                f"target='_blank'>arXiv:{esc(ax)}</a> · priority score "
                f"{mm['score']:.0f} · severity: {esc(mm['severity'])} · effort: "
                f"{esc(mm['estimated_effort'])})</span><br>"
                f"{esc(mm['description'])}<br><i>proposed resolution:</i> "
                f"{esc(mm['proposed_resolution'])}</div>")
        out.append("\n".join(blocks))
        if len(mem) > len(shown):
            rest = []
            for mm in mem[len(shown):]:
                ax = mm["arxiv"]
                rest.append(
                    f"<div class='member'><b>{esc(mm['model_name'])}</b> "
                    f"<span class='meta'>(<a href='https://arxiv.org/abs/{ax}' "
                    f"target='_blank'>arXiv:{esc(ax)}</a> · score "
                    f"{mm['score']:.0f})</span><br>{esc(mm['description'])}<br>"
                    f"<i>proposed resolution:</i> "
                    f"{esc(mm['proposed_resolution'])}</div>")
            out.append(f"<details><summary>show the other {len(mem) - len(shown)} "
                       f"models in this group</summary>{''.join(rest)}</details>")
        return "\n".join(out)

    parts.append("<h2>Top gaps overall</h2>")
    for rec in records[:25]:
        parts.append(html_group(rec))
    parts.append("<h2>Top gaps blocking structure-formation observables</h2>")
    for rec in sf_sorted[:25]:
        parts.append(html_group(rec, sf=True))
    parts.append("</body></html>")
    OUT_HTML.write_text("\n".join(parts))
    print(f"wrote {OUT_HTML} ({OUT_HTML.stat().st_size/1e6:.1f} MB)")

    # console summary
    print("\nTop 10 overall:")
    for rec in records[:10]:
        print(f"  {rec['rank']:2d}. [{rec['gap_type']}] {rec['theme']} — "
              f"w={rec['weight']:,.0f}, models={rec['n_models']}")
    print("Top 10 structure formation:")
    for rec in sf_sorted[:10]:
        print(f"  {rec['rank_structure_formation']:2d}. [{rec['gap_type']}] "
              f"{rec['theme']} — w_sf={rec['weight_structure_formation']:,.0f}, "
              f"models={rec['n_models_structure_formation']}")
    other = [rec for rec in records if rec["theme"] == "Other / unclassified"]
    print(f"unclassified gaps: {sum(rec['n_gaps'] for rec in other)}")


if __name__ == "__main__":
    main()
