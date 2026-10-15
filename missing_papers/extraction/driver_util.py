#!/usr/bin/env python3
"""Helpers for run_batches.sh: parse a `claude -p --output-format json` log.

  python3 driver_util.py record LOG_JSON LOG_ERR BATCH ATTEMPT EXIT_CODE VALIDATION SECONDS
      prints one JSON line for usage.jsonl (token usage, turns, cost estimate, error flags);
      the line has "limit": true when the log or stderr reports a usage or rate limit.
  python3 driver_util.py smoke LOG_JSON EXPECT
      exits 0 when the log is a successful result whose text contains EXPECT.
"""
import json, re, sys

LIMIT = re.compile(r"usage limit|limit reached|rate.?limit|too many requests|overloaded|quota", re.I)


def load(path):
    try:
        text = open(path, encoding="utf-8", errors="replace").read()
    except OSError:
        return None, ""
    try:
        return json.loads(text), text
    except json.JSONDecodeError:
        # Some versions print a JSON array of events; keep the last result object.
        try:
            arr = json.loads(text)
        except json.JSONDecodeError:
            return None, text
        res = [x for x in arr if isinstance(x, dict) and x.get("type") == "result"]
        return (res[-1] if res else None), text


def main():
    cmd = sys.argv[1]
    if cmd == "record":
        log, err, batch, attempt, rc, val, secs = sys.argv[2:9]
        d, raw = load(log)
        try:
            err_text = open(err, encoding="utf-8", errors="replace").read()
        except OSError:
            err_text = ""
        d = d or {}
        u = d.get("usage") or {}
        result = d.get("result") if isinstance(d.get("result"), str) else ""
        row = {"batch_id": batch, "attempt": int(attempt), "exit_code": int(rc), "validation": val,
               "seconds": int(secs), "is_error": d.get("is_error"), "subtype": d.get("subtype"),
               "num_turns": d.get("num_turns"), "total_cost_usd": d.get("total_cost_usd"),
               "input_tokens": u.get("input_tokens"), "cache_creation_input_tokens": u.get("cache_creation_input_tokens"),
               "cache_read_input_tokens": u.get("cache_read_input_tokens"), "output_tokens": u.get("output_tokens"),
               "models": sorted((d.get("modelUsage") or {}).keys()) or None,
               "result": result[:300],
               "limit": bool(val != "PASS" and (LIMIT.search(err_text) or (d.get("is_error") and LIMIT.search(result))
                                                 or (not d and LIMIT.search(raw))))}
        print(json.dumps(row))
    elif cmd == "smoke":
        d, raw = load(sys.argv[2])
        ok = bool(d) and not d.get("is_error") and sys.argv[3] in str(d.get("result", ""))
        if d:
            u = d.get("usage") or {}
            print(f"  result: {str(d.get('result'))[:120]!r}; is_error={d.get('is_error')}; turns={d.get('num_turns')}; "
                  f"tokens in/cache-write/cache-read/out = {u.get('input_tokens')}/{u.get('cache_creation_input_tokens')}/"
                  f"{u.get('cache_read_input_tokens')}/{u.get('output_tokens')}; models={sorted((d.get('modelUsage') or {}).keys())}")
        else:
            print(f"  could not parse the JSON log: {raw[:200]!r}")
        sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
