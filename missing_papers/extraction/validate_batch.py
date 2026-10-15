#!/usr/bin/env python3
"""Validate one extraction batch directory written by a worker (worker_prompt_template.md).

Usage: python3 validate_batch.py BATCH_DIR [BATCH_DIR ...] [--quiet]
       python3 validate_batch.py runs/RUN/batches --quiet     (every batch of a run; prints only FAILs)

Reads BATCH_DIR/assignment.json (written by stage_extraction.py) and checks the worker's
outputs.jsonl, paper_status.jsonl and run_summary.json against the rules of
registry/codex_prompts/extraction_output_guide.md: files present and parseable, every assigned
paper exactly once in paper_status.jsonl, counts consistent across the three files, at most 10
cards per paper, and every model_card meeting schema_profile_model_only.json (required, excluded
and enum-restricted fields, fixed provenance values) and the current registry schemas.
Prints PASS or FAIL with the errors for each directory; exit code 1 if any directory fails.
"""
import json, re, sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent


def find_registry():
    # Public repo layout: <repo>/registry; local source layout: <root>/darkmatterfm_schema_starter/registry.
    for cand in (REPO / "registry", REPO / "darkmatterfm_schema_starter" / "registry"):
        if (cand / "schemas" / "bsm_model.schema.yaml").exists():
            return cand
    sys.exit("cannot find registry/schemas")


REGISTRY = find_registry()
PROFILE = json.load(open(REGISTRY / "codex_prompts" / "schema_profile_model_only.json"))
SCHEMA_FILES = ["common", "observable", "constraint", "route", "provenance", "code", "bsm_model"]
STATUS_KEYS = ["shard", "paper_id", "source_member", "status", "accepted_model_card_count", "rejection_reason"]
SUMMARY_KEYS = ["run_id", "batch_id", "input_paper_count", "processed_paper_count", "accepted_paper_count",
                "rejected_paper_count", "error_paper_count", "accepted_model_card_count"]
MODEL_ID = re.compile(r"^[a-z0-9_-]+$")


def card_validator():
    reg, schemas = Registry(), {}
    for name in SCHEMA_FILES:
        s = yaml.safe_load(open(REGISTRY / "schemas" / f"{name}.schema.yaml"))
        res = Resource.from_contents(s)
        reg = reg.with_resource(s["$id"], res).with_resource(f"{name}.schema.yaml", res)
        schemas[name] = s
    return Draft202012Validator(schemas["bsm_model"], registry=reg)


VALIDATOR = card_validator()


def get(d, path):
    for k in path.split("."):
        if not isinstance(d, dict) or k not in d:
            return KeyError
        d = d[k]
    return d


def read_jsonl(path, errors):
    rows = []
    for n, line in enumerate(open(path, encoding="utf-8"), 1):
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError as e:
            errors.append(f"{path.name} line {n}: invalid JSON ({e.msg})")
            continue
        if not isinstance(r, dict):
            errors.append(f"{path.name} line {n}: not a JSON object")
            continue
        rows.append(r)
    return rows


def check_card(card, pid, errors, warnings, where):
    if not isinstance(card, dict):
        errors.append(f"{where}: model_card is not an object")
        return
    for f in PROFILE["required_top_level_fields"]:
        if f not in card:
            errors.append(f"{where}: missing required field {f}")
    for f in PROFILE["disallowed_top_level_fields"]:
        if f in card:
            errors.append(f"{where}: must not contain {f}")
    extra = set(card) - set(PROFILE["required_top_level_fields"]) - set(PROFILE["optional_top_level_fields"])
    for f in sorted(extra):
        errors.append(f"{where}: field {f} is not in the model-only profile")
    for parent, fields in PROFILE["required_nested_fields"].items():
        d = get(card, parent)
        if not isinstance(d, dict):
            continue  # missing parent is already reported (top level) or caught by the schema check
        for f in fields:
            if f not in d:
                errors.append(f"{where}: missing required field {parent}.{f}")
    for path, allowed in PROFILE["enum_overrides"].items():
        v = get(card, path)
        if v is not KeyError and v not in allowed:
            errors.append(f"{where}: {path} = {v!r} not in {allowed}")
    if card.get("schema_version") != "model_only_v0":
        errors.append(f"{where}: schema_version must be 'model_only_v0'")
    mid = card.get("model_id")
    if not isinstance(mid, str) or not MODEL_ID.match(mid):
        errors.append(f"{where}: model_id {mid!r} must match ^[a-z0-9_-]+$")
    elif not mid.startswith(pid.lower()):
        warnings.append(f"{where}: model_id {mid} does not start with the paper id")
    fixed = {"provenance.status": "machine_extracted", "provenance.extraction.method": "llm_assisted",
             "provenance.review.human_reviewed": False, "provenance.review.expert_reviewed": False}
    for path, want in fixed.items():
        if get(card, path) != want:
            errors.append(f"{where}: {path} must be {want!r}")
    if get(card, "provenance.model_id") not in (KeyError, mid):
        errors.append(f"{where}: provenance.model_id differs from model_id")
    prim = get(card, "provenance.sources.primary_papers")
    if not isinstance(prim, list) or not prim:
        errors.append(f"{where}: provenance.sources.primary_papers must list the assigned paper")
    for e in sorted(VALIDATOR.iter_errors(card), key=lambda e: list(e.path))[:10]:
        p = ".".join(str(x) for x in e.path) or "<root>"
        errors.append(f"{where}: schema: {p}: {e.message[:200]}")


def validate(batch_dir):
    d = Path(batch_dir)
    errors, warnings = [], []
    try:
        a = json.load(open(d / "assignment.json"))
    except Exception as e:
        return [f"assignment.json unreadable: {e}"], []
    assigned = a["paper_ids"]
    for name in ("outputs.jsonl", "paper_status.jsonl", "run_summary.json"):
        if not (d / name).exists():
            errors.append(f"missing {name}")
    if errors:
        return errors, warnings
    status = read_jsonl(d / "paper_status.jsonl", errors)
    outputs = read_jsonl(d / "outputs.jsonl", errors)
    try:
        summary = json.load(open(d / "run_summary.json"))
    except Exception as e:
        errors.append(f"run_summary.json: {e}")
        summary = {}

    # paper_status.jsonl
    seen = {}
    for r in status:
        pid = r.get("paper_id")
        for k in STATUS_KEYS:
            if k not in r:
                errors.append(f"paper_status {pid}: missing {k}")
        if pid not in assigned:
            errors.append(f"paper_status: unassigned paper {pid}")
        if pid in seen:
            errors.append(f"paper_status: {pid} appears more than once")
        seen[pid] = r
        st, n, reason = r.get("status"), r.get("accepted_model_card_count"), r.get("rejection_reason")
        if st not in ("accepted", "rejected", "error"):
            errors.append(f"paper_status {pid}: status {st!r}")
        if not isinstance(n, int):
            errors.append(f"paper_status {pid}: accepted_model_card_count must be an integer")
        if st == "accepted" and reason is not None:
            errors.append(f"paper_status {pid}: rejection_reason must be null when accepted")
        if st in ("rejected", "error") and not (isinstance(reason, str) and reason.strip()):
            errors.append(f"paper_status {pid}: {st} needs a short rejection_reason")
        if st in ("rejected", "error") and n != 0:
            errors.append(f"paper_status {pid}: {st} paper must have accepted_model_card_count 0")
    for pid in assigned:
        if pid not in seen:
            errors.append(f"paper_status: assigned paper {pid} missing")
    if [r.get("paper_id") for r in status] != [p for p in assigned if p in seen]:
        warnings.append("paper_status rows are not in the assigned order")

    # outputs.jsonl
    per_paper, ids = {}, set()
    for i, r in enumerate(outputs, 1):
        pid = r.get("paper_id")
        where = f"outputs row {i} ({pid})"
        for k in ("shard", "paper_id", "source_member", "model_card"):
            if k not in r:
                errors.append(f"{where}: missing {k}")
        if pid not in assigned:
            errors.append(f"{where}: unassigned paper")
            continue
        per_paper[pid] = per_paper.get(pid, 0) + 1
        mid = (r.get("model_card") or {}).get("model_id")
        if mid in ids:
            errors.append(f"{where}: duplicate model_id {mid}")
        ids.add(mid)
        check_card(r.get("model_card"), pid, errors, warnings, where)
    for pid, r in seen.items():
        n = per_paper.get(pid, 0)
        if r.get("status") == "accepted":
            if n == 0:
                errors.append(f"{pid}: accepted but has no outputs rows")
            if n != r.get("accepted_model_card_count"):
                errors.append(f"{pid}: accepted_model_card_count {r.get('accepted_model_card_count')} but {n} outputs rows")
        elif n:
            errors.append(f"{pid}: status {r.get('status')} but has {n} outputs rows")
        if n > 10:
            errors.append(f"{pid}: {n} cards (maximum 10)")

    # run_summary.json
    for k in SUMMARY_KEYS:
        if k not in summary:
            errors.append(f"run_summary.json: missing {k}")
    want = {"run_id": a.get("run_id"), "batch_id": a.get("batch_id"), "input_paper_count": len(assigned),
            "processed_paper_count": len(seen),
            "accepted_paper_count": sum(r.get("status") == "accepted" for r in seen.values()),
            "rejected_paper_count": sum(r.get("status") == "rejected" for r in seen.values()),
            "error_paper_count": sum(r.get("status") == "error" for r in seen.values()),
            "accepted_model_card_count": len(outputs)}
    for k, v in want.items():
        if k in summary and summary[k] != v:
            errors.append(f"run_summary.json: {k} = {summary[k]!r}, expected {v!r}")

    leftovers = sorted(p.name for p in d.iterdir() if p.name not in
                       {"assignment.json", "prompt.md", "outputs.jsonl", "paper_status.jsonl", "run_summary.json", "report.md"})
    if leftovers:
        warnings.append(f"extra files in batch directory: {', '.join(leftovers)}")
    return errors, warnings


def expand(args):
    # A directory without assignment.json stands for all batch directories inside it.
    out = []
    for x in args:
        p = Path(x)
        if not (p / "assignment.json").exists() and p.is_dir():
            out += sorted(str(q.parent) for q in p.glob("*/assignment.json"))
        else:
            out.append(x)
    return out


def main():
    args = expand([x for x in sys.argv[1:] if not x.startswith("--")])
    quiet = "--quiet" in sys.argv
    if not args:
        sys.exit(__doc__)
    bad = 0
    for b in args:
        errors, warnings = validate(b)
        bad += bool(errors)
        if errors:
            print(f"FAIL {b}")
            for e in errors[:40]:
                print("  -", e)
            if len(errors) > 40:
                print(f"  ... {len(errors) - 40} more")
        elif not quiet:
            print(f"PASS {b}")
        if not quiet:
            for w in warnings:
                print("  warning:", w)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
