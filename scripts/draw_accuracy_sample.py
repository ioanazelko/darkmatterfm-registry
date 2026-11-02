#!/usr/bin/env python3
"""Draw the stratified sample for the extraction-accuracy study.

Strata (paper Sec. "Validation"):
  - taxonomy class (from family_taxonomy_proposed.csv): >=1 card per class
  - enriched vs. base cards: ~50/50 overall
  - ranking tier spread (from ranking_full_ranked.jsonl)
  - a few cards that fail schema validation (designed hard cases)

Deterministic under --seed. Writes accuracy_study/accuracy_sample_manifest.jsonl
with one row per sampled card: model_id, paper_id, arxiv_id, family, taxonomy
class, tier, enriched flag, stratum label, and the full model_card (so the
grading interface builds without re-reading the 100 MB release file).

Usage:
    python scripts/draw_accuracy_sample.py [--n 75] [--seed 20260902]
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import re
import sys
from collections import defaultdict
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_schema import build_registry

REGISTRY = Path(__file__).resolve().parents[1] / "registry"
RELEASE = REGISTRY / "models" / "all_outputs_combined_enriched.jsonl"
RANKING = REGISTRY / "models" / "ranking_full_ranked.jsonl"
TAXONOMY = REGISTRY / "models" / "family_taxonomy_proposed.csv"
OUT_DIR = REGISTRY / "accuracy_study"


def arxiv_id(paper_id: str) -> str:
    """paper_id like 2103_13397 -> 2103.13397; hep-ph0607012 -> hep-ph/0607012."""
    m = re.fullmatch(r"(\d{4})_(\d{4,5})", paper_id or "")
    if m:
        return f"{m.group(1)}.{m.group(2)}"
    m = re.fullmatch(r"([a-z-]+(?:\.[A-Z]{2})?)(\d{7})", paper_id or "")
    if m:
        return f"{m.group(1)}/{m.group(2)}"
    return paper_id or ""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=75)
    parser.add_argument("--n-invalid", type=int, default=5,
                        help="How many schema-invalid cards to include as hard cases.")
    parser.add_argument("--seed", type=int, default=20260902)
    args = parser.parse_args()
    rng = random.Random(args.seed)

    cls_of_family = {}
    with TAXONOMY.open() as f:
        for r in csv.DictReader(f):
            cls_of_family[r["raw_family"]] = r["proposed_class"]

    tier_of_model = {}
    with RANKING.open() as f:
        for line in f:
            r = json.loads(line)
            tier_of_model[r["model_id"]] = (r.get("triage") or {}).get("priority_tier", "unknown")

    schema, registry = build_registry(REGISTRY / "schemas")
    validator = Draft202012Validator(schema, registry=registry)

    rows = []
    with RELEASE.open() as f:
        for line in f:
            row = json.loads(line)
            card = row.get("model_card") or {}
            fam = (card.get("identity") or {}).get("family", "")
            rows.append({
                "model_id": card.get("model_id", ""),
                "paper_id": row.get("paper_id", ""),
                "family": fam,
                "taxonomy_class": cls_of_family.get(fam, "unclassified"),
                "tier": tier_of_model.get(card.get("model_id", ""), "unknown"),
                "enriched": bool(row.get("enriched")),
                "valid": not next(iter(validator.iter_errors(card)), None),
                "card": card,
            })

    picked: list[dict] = []
    picked_ids: set[str] = set()

    def take(pool, k, stratum):
        pool = [r for r in pool if r["model_id"] not in picked_ids]
        rng.shuffle(pool)
        for r in pool[:k]:
            r["stratum"] = stratum
            picked.append(r)
            picked_ids.add(r["model_id"])

    # 1. hard cases: schema-invalid cards
    take([r for r in rows if not r["valid"]], args.n_invalid, "schema_invalid")

    # 2. one valid card per taxonomy class (enriched preferred)
    by_class = defaultdict(list)
    for r in rows:
        if r["valid"]:
            by_class[r["taxonomy_class"]].append(r)
    for c in sorted(by_class):
        pool = sorted(by_class[c], key=lambda r: not r["enriched"])
        enr = [r for r in pool if r["enriched"]]
        take(enr or pool, 1, f"class:{c}")

    # 3. fill remaining, alternating enriched/base and cycling tiers
    remaining = args.n - len(picked)
    valid = [r for r in rows if r["valid"]]
    tiers = sorted({r["tier"] for r in valid})
    want_enriched = True
    i = 0
    while remaining > 0:
        tier = tiers[i % len(tiers)]
        pool = [r for r in valid
                if r["tier"] == tier and r["enriched"] == want_enriched]
        before = len(picked)
        take(pool, 1, f"fill:{tier}:{'enriched' if want_enriched else 'base'}")
        if len(picked) > before:
            remaining -= 1
        want_enriched = not want_enriched
        i += 1
        if i > 10 * args.n:  # safety
            break

    OUT_DIR.mkdir(exist_ok=True)
    manifest = OUT_DIR / "accuracy_sample_manifest.jsonl"
    with manifest.open("w") as f:
        for r in picked:
            f.write(json.dumps({
                "model_id": r["model_id"],
                "paper_id": r["paper_id"],
                "arxiv_id": arxiv_id(r["paper_id"]),
                "family": r["family"],
                "taxonomy_class": r["taxonomy_class"],
                "tier": r["tier"],
                "enriched": r["enriched"],
                "schema_valid": r["valid"],
                "stratum": r["stratum"],
                "seed": args.seed,
                "card": r["card"],
            }) + "\n")

    n_enr = sum(1 for r in picked if r["enriched"])
    print(f"sampled {len(picked)} cards -> {manifest}")
    print(f"  enriched {n_enr} / base {len(picked)-n_enr}; "
          f"classes {len({r['taxonomy_class'] for r in picked})}; "
          f"tiers {sorted({r['tier'] for r in picked})}")
    print(f"  schema-invalid hard cases: {sum(1 for r in picked if not r['valid'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
