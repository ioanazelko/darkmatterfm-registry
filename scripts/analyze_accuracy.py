#!/usr/bin/env python3
"""Analyze extraction-accuracy grades exported from accuracy_grading.html.

Input: one or more accuracy_grades_<grader>.jsonl files (one row per graded
card, with sections: {name: {verdict, note}}).

Reports:
  - per-section accuracy (correct / graded, with partially_correct counted
    as half credit in a secondary column) with Wilson 95% intervals
  - overall accuracy, split by enriched vs base cards
  - hallucination rate per section
  - Cohen's kappa between each grader pair on the overlap set
  - a LaTeX table ready for the paper's Validation section (--latex)

Usage:
    python scripts/analyze_accuracy.py accuracy_grades_IZ.jsonl [more.jsonl] [--latex]
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from itertools import combinations
from pathlib import Path

GRADED = {"correct", "partially_correct", "incorrect", "hallucinated"}


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, center - half), min(1.0, center + half))


def cohens_kappa(pairs: list[tuple[str, str]]) -> float:
    if not pairs:
        return float("nan")
    cats = sorted({v for p in pairs for v in p})
    n = len(pairs)
    po = sum(1 for a, b in pairs if a == b) / n
    pe = sum(
        (sum(1 for a, _ in pairs if a == c) / n) * (sum(1 for _, b in pairs if b == c) / n)
        for c in cats
    )
    return (po - pe) / (1 - pe) if pe < 1 else 1.0


def load(path: Path):
    rows = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("grade_files", nargs="+", type=Path)
    parser.add_argument("--latex", action="store_true")
    args = parser.parse_args()

    by_grader: dict[str, dict[str, dict]] = {}
    for path in args.grade_files:
        for row in load(path):
            grader = row.get("grader", path.stem)
            by_grader.setdefault(grader, {})[row["model_id"]] = row

    # pooled per-section stats (all graders; a card graded by two people counts twice)
    sec_counts = defaultdict(lambda: defaultdict(int))
    split_counts = defaultdict(lambda: defaultdict(int))  # enriched/base
    for grader, cards in by_grader.items():
        for row in cards.values():
            kind = "enriched" if row.get("enriched") else "base"
            for sec, g in (row.get("sections") or {}).items():
                v = (g or {}).get("verdict")
                if v in GRADED:
                    sec_counts[sec][v] += 1
                    split_counts[kind][v] += 1

    print(f"graders: {', '.join(sorted(by_grader))}; "
          f"cards graded: {sum(len(c) for c in by_grader.values())} rows")
    print(f"\n{'section':34s} {'n':>4s} {'strict':>7s} {'95% CI':>15s} "
          f"{'half-credit':>11s} {'halluc.':>7s}")
    rows_out = []
    for sec in sorted(sec_counts, key=lambda s: -sum(sec_counts[s].values())):
        c = sec_counts[sec]
        n = sum(c.values())
        strict = c["correct"] / n
        half = (c["correct"] + 0.5 * c["partially_correct"]) / n
        lo, hi = wilson(c["correct"], n)
        halluc = c["hallucinated"] / n
        print(f"{sec:34s} {n:4d} {strict:6.1%} [{lo:5.1%},{hi:5.1%}] "
              f"{half:10.1%} {halluc:6.1%}")
        rows_out.append((sec, n, strict, lo, hi, half, halluc))

    print("\nby card type:")
    for kind, c in split_counts.items():
        n = sum(c.values())
        if n:
            print(f"  {kind:9s} n={n:4d}  strict {c['correct']/n:.1%}  "
                  f"half-credit {(c['correct']+0.5*c['partially_correct'])/n:.1%}")

    # inter-grader agreement on overlap
    for g1, g2 in combinations(sorted(by_grader), 2):
        pairs = []
        for mid in set(by_grader[g1]) & set(by_grader[g2]):
            s1 = by_grader[g1][mid].get("sections") or {}
            s2 = by_grader[g2][mid].get("sections") or {}
            for sec in set(s1) & set(s2):
                v1, v2 = (s1[sec] or {}).get("verdict"), (s2[sec] or {}).get("verdict")
                if v1 in GRADED and v2 in GRADED:
                    pairs.append((v1, v2))
        if pairs:
            print(f"\nCohen's kappa {g1} vs {g2}: {cohens_kappa(pairs):.3f} "
                  f"on {len(pairs)} shared section grades")

    if args.latex:
        print("\n% LaTeX table for the Validation section")
        print("\\begin{tabular}{lrrrr}\n\\toprule")
        print("Section & $n$ & Correct & 95\\% CI & Halluc. \\\\\n\\midrule")
        for sec, n, strict, lo, hi, half, halluc in rows_out:
            print(f"\\texttt{{{sec.replace('_', '\\_')}}} & {n} & "
                  f"{strict*100:.0f}\\% & [{lo*100:.0f},{hi*100:.0f}]\\% & "
                  f"{halluc*100:.0f}\\% \\\\")
        print("\\bottomrule\n\\end{tabular}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
