#!/usr/bin/env python3
"""Rank capability gaps as research projects (item #9 follow-on).

Reads models/capability_gap_roadmap.jsonl (the (gap_type, theme) groups built
by build_gap_roadmap.py) and merges groups belonging to the same capability
theme into one research project: one concrete deliverable that would close
the theme's tool + likelihood + derivation gaps together.

Each project is scored by:
  impact       = sum over distinct blocked models of
                 adjusted_priority_score x severity multiplier
                 (a model counts once, at its worst-severity gap in the theme)
  impact_sf    = same, counting only gap entries that block
                 structure-formation observables
  cost         = mean effort of the member gap entries, on the scale
                 small=1, medium=3, large=10, major_program=30 (unknown=3) —
                 rough person-months of the typical closing work in the
                 theme (the median is degenerate: almost every theme's
                 median entry is 'medium')
  value_ratio  = impact / cost  ("science unblocked per unit effort")

Emits models/research_projects_ranked.jsonl and the human-readable report
../../research_project_ranking.md (project root), with three orderings:
by impact, by value ratio, and by structure-formation impact.
"""

import json
import statistics
from collections import defaultdict
from pathlib import Path

REGISTRY = Path(__file__).resolve().parent
MODELS = REGISTRY / "models"
IN_JSONL = MODELS / "capability_gap_roadmap.jsonl"
OUT_JSONL = MODELS / "research_projects_ranked.jsonl"
OUT_MD = REGISTRY.parent.parent / "research_project_ranking.md"

SEV_MULT = {"blocks_all_observables": 1.0, "blocks_key_observables": 0.8,
            "degrades_precision": 0.4, "minor": 0.1, "unknown": 0.3}
EFFORT_COST = {"small": 1, "medium": 3, "large": 10, "major_program": 30,
               "unknown": 3}

# theme -> (project title, deliverable statement)
PROJECTS = {
    "Lyman-α forest modeling & likelihood": (
        "A reusable Lyman-α forest likelihood for non-CDM cosmologies",
        "A public likelihood package that takes an arbitrary suppressed or "
        "oscillatory linear power spectrum (WDM-like, interacting, mixed, "
        "fuzzy) and returns constraints from eBOSS/DESI and high-resolution "
        "flux-power data, with an emulator-based nonlinear mapping so users "
        "never rerun hydrodynamical simulations."),
    "Boltzmann-code extension (CLASS/CAMB/ETHOS)": (
        "A maintained general non-CDM Boltzmann-code framework",
        "A supported CLASS/ETHOS-style branch implementing interacting, "
        "decaying, warm, mixed and self-interacting species behind one "
        "interface, with standardized transfer-function output that "
        "downstream structure-formation pipelines can consume."),
    "Relic-abundance solver extension (micrOMEGAs/MadDM/DarkSUSY)": (
        "A community model-implementation library for relic-abundance solvers",
        "A curated, validated library of FeynRules/CalcHEP model files plus "
        "solver extensions (freeze-in, co-annihilation, resonances, "
        "non-standard histories) so registry models get relic densities from "
        "micrOMEGAs/MadDM instead of bespoke by-hand estimates."),
    "Indirect-detection likelihood (γ-ray / cosmic-ray / ν)": (
        "A unified indirect-detection likelihood suite",
        "One package wrapping Fermi dwarf-spheroidal, Galactic-center, "
        "AMS-02 antiproton/positron and neutrino-telescope likelihoods with "
        "user-supplied annihilation/decay spectra, replacing per-paper "
        "digitized limits."),
    "Direct-detection recast & likelihood": (
        "A direct-detection recast framework beyond the standard WIMP",
        "Recast machinery for XENONnT/LZ/CRESST-class results covering "
        "sub-GeV kinematics, non-standard form factors, inelastic and "
        "boosted scenarios, exposing proper likelihoods rather than "
        "published 90% curves."),
    "Dwarf-galaxy dynamics & density profiles": (
        "A dwarf-galaxy structure likelihood",
        "A likelihood connecting model predictions for inner density "
        "profiles, dynamical heating and star-cluster survival in dwarfs to "
        "stellar-kinematics datasets, with marginalization over baryonic "
        "feedback."),
    "Milky Way satellite / subhalo-count likelihood": (
        "A subhalo-abundance-to-satellite-counts pipeline",
        "A pipeline from a suppressed subhalo mass function to the observed "
        "Milky Way satellite luminosity function (DES/Rubin selection "
        "functions included), packaged as a likelihood any transfer "
        "function can be pushed through."),
    "Axion / fuzzy-DM field solver": (
        "A public wave-dark-matter solver suite",
        "Maintained Schrödinger–Poisson / axion-field solvers with soliton, "
        "minicluster and oscillon modules, calibrated scaling relations, and "
        "hooks to structure-formation observables."),
    "N-body / hydrodynamic simulation campaign": (
        "A targeted non-CDM simulation campaign with public halo products",
        "A coordinated N-body/hydro campaign spanning the registry's "
        "recurring non-CDM physics (velocity-dependent SIDM, decays, "
        "late-forming DM), releasing halo catalogs and calibrations others "
        "can build likelihoods on."),
    "Sterile-neutrino production solver": (
        "An extended sterile-neutrino production code",
        "A quantum-kinetic production solver going beyond "
        "Dodelson–Widrow/Shi–Fuller: new mediators, self-interactions, and "
        "non-standard expansion histories, emitting phase-space "
        "distributions ready for Boltzmann codes."),
    "PBH formation & abundance pipeline": (
        "An end-to-end primordial-black-hole pipeline",
        "One pipeline from a primordial P(k) (or collapse mechanism) to an "
        "extended PBH mass function and current constraints (microlensing, "
        "CMB accretion, GW rates), replacing monochromatic by-hand "
        "estimates."),
    "PTA / stochastic GW background likelihood": (
        "A modern PTA stochastic-background likelihood for dark sectors",
        "NANOGrav-15yr/EPTA-class likelihoods packaged for dark-sector "
        "sources (strings, phase transitions, superradiance) so cards stop "
        "relying on pre-2017 exclusions."),
    "GW detector forecasts & likelihoods (LIGO/LISA/ET)": (
        "Interferometer forecasts and likelihoods for DM-sector signals",
        "Shared LIGO/LISA/ET sensitivity and event-rate machinery for "
        "dark-sector mergers, backgrounds and continuous waves."),
    "CMB likelihood & ΔN_eff machinery": (
        "A CMB energy-injection and ΔN_eff constraint toolkit",
        "Standardized Planck(+ACT/SPT) likelihood wrappers for energy "
        "injection, annihilation/decay, and ΔN_eff from dark radiation, "
        "consumable without a full cosmology-pipeline setup."),
    "BBN code extension": (
        "A BBN code extension for dark-sector energy injection",
        "PRIMAT/AlterBBN-class extensions handling hadronic/electromagnetic "
        "injection, non-standard expansion and MeV-scale sectors, with a "
        "packaged likelihood."),
    "Collider / beam-dump recast": (
        "A collider and beam-dump recast library for DM benchmarks",
        "Recast implementations (LHC, Belle II, fixed-target/beam-dump) of "
        "the registry's recurring signatures, with acceptances and "
        "likelihoods, in a CheckMATE/Contur-style framework."),
    "Dark-photon / light-mediator constraint recast": (
        "A light-mediator constraint compilation with proper likelihoods",
        "A maintained, recastable compilation of dark-photon/fifth-force/"
        "light-scalar constraints (beyond static exclusion plots) mapped to "
        "arbitrary coupling structures."),
    "Self-interacting DM halo modeling": (
        "A velocity-dependent SIDM halo-modeling kit",
        "Calibrated halo-level models (gravothermal evolution, core "
        "formation/collapse) for velocity-dependent cross sections, plus "
        "the likelihood connecting sigma(v)/m to rotation curves, clusters "
        "and dwarfs."),
    "Stellar-stream perturbation likelihood": (
        "A stellar-stream perturbation likelihood",
        "A likelihood from subhalo population predictions to observed "
        "stream density/track perturbations (GD-1, Pal 5, Rubin-era "
        "samples), usable by any model that predicts a subhalo mass "
        "function."),
    "Strong-lensing substructure likelihood": (
        "A strong-lensing substructure likelihood",
        "Flux-ratio and gravitational-imaging likelihoods for suppressed or "
        "enhanced substructure, packaged for arbitrary transfer functions."),
    "21-cm signal modeling & likelihood": (
        "A 21-cm signal modeling and likelihood package for non-CDM",
        "21cmFAST-class modeling plus EDGES/HERA/SKA likelihoods for "
        "models altering the timing of structure formation or injecting "
        "energy."),
    "Nonlinear-structure emulator": (
        "Nonlinear-structure emulators for non-CDM cosmologies",
        "Emulators mapping modified linear spectra to nonlinear power, "
        "halo mass functions and profiles, trained on the simulation "
        "campaign above."),
    "Phase-transition & defect-network computation": (
        "A dark-sector phase-transition and defect computation toolkit",
        "CosmoTransitions-class tooling extended to the registry's dark "
        "sectors (nucleation, GW spectra, string/wall networks) with "
        "validated defaults."),
    "CMB spectral distortions": (
        "A spectral-distortion prediction and constraint module",
        "mu/y-distortion computation for dark-sector energy release with "
        "FIRAS(+PIXIE-forecast) likelihoods."),
    "Isocurvature machinery": (
        "An isocurvature constraint pipeline",
        "From a model's isocurvature production mechanism to Planck "
        "isocurvature likelihoods, for axion-like and multi-field "
        "scenarios."),
    "Compact-object capture & heating": (
        "A compact-object capture and heating calculator",
        "A public calculator for DM capture, thermalization and heating in "
        "neutron stars/white dwarfs, with observational comparison to "
        "cooling data."),
}


def main() -> None:
    groups = [json.loads(l) for l in IN_JSONL.open()]
    by_theme = defaultdict(list)
    for g in groups:
        by_theme[g["theme"]].append(g)

    projects = []
    skipped_unclassified = 0
    for theme, grps in by_theme.items():
        if theme not in PROJECTS:
            skipped_unclassified += sum(g["n_gaps"] for g in grps)
            continue
        title, deliverable = PROJECTS[theme]
        members = [m for g in grps for m in g["members"]]
        gap_types = sorted({g["gap_type"] for g in grps})
        # one contribution per model: worst-severity gap wins
        best = {}
        best_sf = {}
        for m in members:
            mult = SEV_MULT.get(m["severity"], 0.3)
            contrib = m["score"] * mult
            mid = m["model_id"]
            if contrib > best.get(mid, (-1, None))[0]:
                best[mid] = (contrib, m)
            if m["blocks_structure_formation"] and \
                    contrib > best_sf.get(mid, (-1, None))[0]:
                best_sf[mid] = (contrib, m)
        impact = sum(c for c, _ in best.values())
        impact_sf = sum(c for c, _ in best_sf.values())
        costs = [EFFORT_COST.get(m["estimated_effort"], 3) for m in members]
        cost = round(statistics.mean(costs), 1)
        eff = defaultdict(int)
        sev = defaultdict(int)
        for m in members:
            eff[m["estimated_effort"]] += 1
            sev[m["severity"]] += 1
        top_models = sorted((mm for _, mm in best.values()),
                            key=lambda mm: -mm["score"])
        projects.append({
            "project": title,
            "theme": theme,
            "deliverable": deliverable,
            "gap_types": gap_types,
            "impact": round(impact, 1),
            "impact_structure_formation": round(impact_sf, 1),
            "cost": cost,
            "value_ratio": round(impact / cost, 1),
            "n_models": len(best),
            "n_models_structure_formation": len(best_sf),
            "n_gaps": len(members),
            "effort_counts": dict(eff),
            "severity_counts": dict(sev),
            "top_models": [{
                "model_id": mm["model_id"], "model_name": mm["model_name"],
                "arxiv": mm["arxiv"], "score": mm["score"],
                "severity": mm["severity"],
                "description": mm["description"],
                "proposed_resolution": mm["proposed_resolution"],
            } for mm in top_models[:10]],
        })

    projects.sort(key=lambda p: -p["impact"])
    for i, p in enumerate(projects, 1):
        p["rank_impact"] = i
    for i, p in enumerate(sorted(projects, key=lambda p: -p["value_ratio"]),
                          1):
        p["rank_value"] = i
    for i, p in enumerate(sorted(projects,
                                 key=lambda p: -p["impact_structure_formation"]),
                          1):
        p["rank_structure_formation"] = i

    with OUT_JSONL.open("w") as f:
        for p in projects:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
    print(f"wrote {OUT_JSONL}: {len(projects)} projects "
          f"({skipped_unclassified} unclassified gaps excluded)")

    # ---- markdown report --------------------------------------------------
    def table(rows, key, sf=False):
        lines = ["| # | project | impact | SF impact | models | cost | "
                 "value ratio |",
                 "|---|---------|-------:|----------:|-------:|-----:|"
                 "------------:|"]
        for p in rows:
            lines.append(
                f"| {p[key]} | {p['project']} | {p['impact']:,.0f} | "
                f"{p['impact_structure_formation']:,.0f} | {p['n_models']} | "
                f"{p['cost']:g} | {p['value_ratio']:,.0f} |")
        return "\n".join(lines)

    md = ["# Research-project ranking from the capability-gap registry", "",
          "Each project is one capability theme from the gap roadmap, "
          "phrased as a concrete deliverable that would close its tool, "
          "likelihood and derivation gaps together. Scores:", "",
          "- **impact** — summed `adjusted_priority_score` of the distinct "
          "models the project unblocks, each weighted by how badly it is "
          "blocked (blocks_all_observables 1.0, blocks_key 0.8, "
          "degrades_precision 0.4, minor 0.1, unknown 0.3).",
          "- **SF impact** — the same sum counting only gap entries that "
          "block structure-formation observables.",
          "- **cost** — mean effort of the member gap entries "
          "(small=1, medium=3, large=10, major_program=30; rough "
          "person-months of the typical closing work in the theme).",
          "- **value ratio** — impact / cost: science unblocked per unit "
          "effort.", "",
          "Machine-readable version with full member lists: "
          "`registry/models/research_projects_ranked.jsonl`; underlying "
          "groups: `registry/models/capability_gap_roadmap.jsonl`.", "",
          "## Ranking by impact", "",
          table(projects, "rank_impact"), "",
          "## Ranking by value ratio (impact per unit effort)", "",
          table(sorted(projects, key=lambda p: -p["value_ratio"]),
                "rank_value"), "",
          "## Ranking by structure-formation impact", "",
          table(sorted(projects,
                       key=lambda p: -p["impact_structure_formation"]),
                "rank_structure_formation"), "",
          "## Project descriptions (impact order)", ""]
    for p in projects:
        md += [f"### {p['rank_impact']}. {p['project']}", "",
               f"**Deliverable.** {p['deliverable']}", "",
               f"Impact {p['impact']:,.0f} (structure formation "
               f"{p['impact_structure_formation']:,.0f}) · unblocks "
               f"{p['n_models']} models ({p['n_models_structure_formation']} "
               f"via structure-formation observables) · {p['n_gaps']} gap "
               f"entries ({', '.join(p['gap_types'])}) · typical effort "
               f"{max(p['effort_counts'], key=p['effort_counts'].get)}.", "",
               "Highest-priority blocked models:", ""]
        for mm in p["top_models"][:3]:
            md.append(f"- **{mm['model_name']}** "
                      f"([arXiv:{mm['arxiv']}](https://arxiv.org/abs/"
                      f"{mm['arxiv']}), score {mm['score']:.0f}, "
                      f"{mm['severity']}): {mm['description']}")
        md.append("")
    OUT_MD.write_text("\n".join(md))
    print(f"wrote {OUT_MD}")

    print("\nTop 10 by impact:")
    for p in projects[:10]:
        print(f"  {p['rank_impact']:2d}. {p['project']} — impact "
              f"{p['impact']:,.0f}, SF {p['impact_structure_formation']:,.0f},"
              f" models {p['n_models']}, cost {p['cost']:g}, value "
              f"{p['value_ratio']:,.0f}")
    print("Top 5 by value ratio:")
    for p in sorted(projects, key=lambda p: -p["value_ratio"])[:5]:
        print(f"  {p['rank_value']:2d}. {p['project']} — value "
              f"{p['value_ratio']:,.0f} (impact {p['impact']:,.0f}, cost "
              f"{p['cost']:g})")
    print("Top 5 by SF impact:")
    for p in sorted(projects,
                    key=lambda p: -p["impact_structure_formation"])[:5]:
        print(f"  {p['rank_structure_formation']:2d}. {p['project']} — SF "
              f"{p['impact_structure_formation']:,.0f}")


if __name__ == "__main__":
    main()
