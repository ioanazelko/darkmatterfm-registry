#!/usr/bin/env bash
# Run Claude model-card extraction workers over the staged batches of one run.
#
#   bash run_batches.sh --check                 preflight: test the claude CLI on this machine
#   bash run_batches.sh RUN [--parallel N] [--limit N] [--max-attempts N] [--max-turns N]
#
# --check must pass once before any run. It runs one tiny headless job that has to call python3
# and write a file with the same tool permissions the workers get, and saves the working
# settings in runs/.cli_config.
#
# A run starts `claude -p` (headless, with the subscription this machine is logged in with) for
# every runs/RUN/batches/batch-NNNN that does not yet PASS validate_batch.py, with that batch's
# prompt.md on stdin, N at a time (default 4). Per batch it writes runs/RUN/logs/<batch>.json
# (the claude result), .err and .validation, and appends one line per attempt to
# runs/RUN/usage.jsonl (exit code, validation, token usage, turns). Passing batches are skipped,
# so rerunning resumes and retries failures, up to --max-attempts (default 3) per batch. When a
# worker hits a usage or rate limit the script writes runs/RUN/STOP and starts no new batches;
# delete STOP and rerun after the limit resets.
#
# Environment: CLAUDE_BIN (default: claude), MODEL (default: claude-opus-5-5).
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
export HERE REPO
# Workers run `python3 validate_batch.py`; use the repo's virtualenv when there is one.
[ -x "$REPO/.venv/bin/python3" ] && export PATH="$REPO/.venv/bin:$PATH"
export CLAUDE_BIN="${CLAUDE_BIN:-claude}"
export MODEL="${MODEL:-claude-opus-5-5}"
CONFIG="$HERE/runs/.cli_config"

check() {
    mkdir -p "$HERE/runs"
    echo "python3 for workers: $(command -v python3)"
    python3 -c "import jsonschema, yaml, referencing" 2>/dev/null \
        || { echo "FAIL: python3 lacks jsonschema / pyyaml / referencing (pip install jsonschema pyyaml referencing)"; return 1; }
    echo "  jsonschema, pyyaml, referencing: ok"
    echo "claude binary: $(command -v "$CLAUDE_BIN" || echo "NOT FOUND (set CLAUDE_BIN)")"
    "$CLAUDE_BIN" --version || return 1
    local help; help="$("$CLAUDE_BIN" --help 2>&1)"
    for f in --print --output-format --model --max-turns --allowedTools; do
        grep -q -- "$f" <<<"$help" && echo "  flag $f: ok" || echo "  flag $f: NOT LISTED"
    done
    local extra=""
    grep -q -- "--no-session-persistence" <<<"$help" && extra="--no-session-persistence"
    echo "  extra flags used: ${extra:-none}"
    local tmp; tmp="$(mktemp -d)"
    for bash_rule in 'Bash(python3:*)' 'Bash(python3 *)'; do
        local allowed="Read,Write,Edit,Glob,Grep,$bash_rule"
        rm -f "$tmp/smoke.txt"
        echo "smoke test with --allowedTools \"$allowed\" (model $MODEL) ..."
        printf '%s\n' "Do two things with your tools, then reply. 1) Use the Bash tool to run exactly: python3 -c 'print(6*7)'" \
            "2) Use the Write tool to create the file $tmp/smoke.txt containing the single word ready." \
            "Reply with only the number that the python3 command printed." \
          | (cd "$REPO" && "$CLAUDE_BIN" -p --model "$MODEL" --output-format json --max-turns 6 \
                --allowedTools "$allowed" $extra) > "$tmp/smoke.json" 2> "$tmp/smoke.err"
        local rc=$?
        if python3 "$HERE/driver_util.py" smoke "$tmp/smoke.json" 42 && [ "$(cat "$tmp/smoke.txt" 2>/dev/null)" = "ready" ]; then
            printf 'ALLOWED=%q\nEXTRA=%q\nMODEL=%q\n' "$allowed" "$extra" "$MODEL" > "$CONFIG"
            echo "PASS (exit $rc): python3 ran and the file was written. Settings saved to $CONFIG"
            rm -rf "$tmp"; return 0
        fi
        echo "  failed (exit $rc); stderr: $(head -c 300 "$tmp/smoke.err")"
    done
    rm -rf "$tmp"
    echo "FAIL: no tool setting worked; see the messages above."; return 1
}

run_one() {
    local b="$1" bdir="$RUN_DIR/batches/$1" log="$RUN_DIR/logs/$1"
    [ -e "$RUN_DIR/STOP" ] && return 0
    local attempt=$(( $(cat "$log.attempts" 2>/dev/null || echo 0) + 1 ))
    if [ "$attempt" -gt "$MAX_ATTEMPTS" ]; then echo "$b: skipped after $MAX_ATTEMPTS failed attempts"; return 0; fi
    echo "$attempt" > "$log.attempts"
    rm -f "$bdir/outputs.jsonl" "$bdir/paper_status.jsonl" "$bdir/run_summary.json" "$bdir/report.md"
    local start; start=$(date +%s)
    (cd "$REPO" && "$CLAUDE_BIN" -p --model "$MODEL" --output-format json --max-turns "$MAX_TURNS" \
        --allowedTools "$ALLOWED" $EXTRA < "$bdir/prompt.md") > "$log.json" 2> "$log.err"
    local rc=$? val=FAIL
    python3 "$HERE/validate_batch.py" "$bdir" > "$log.validation" 2>&1 && val=PASS
    local row; row="$(python3 "$HERE/driver_util.py" record "$log.json" "$log.err" "$b" "$attempt" "$rc" "$val" $(( $(date +%s) - start )))"
    echo "$row" >> "$RUN_DIR/usage.jsonl"
    if grep -q '"limit": true' <<<"$row"; then
        echo "$(date -Is) usage or rate limit reported by $b" > "$RUN_DIR/STOP"
        echo "$b: LIMIT reached, stopping new batches (see $RUN_DIR/STOP)"
    fi
    echo "$(date +%H:%M:%S) $b attempt $attempt exit=$rc $val"
}
export -f run_one

if [ "${1:-}" = "--check" ]; then check; exit $?; fi
RUN="${1:?usage: bash run_batches.sh RUN [--parallel N] [--limit N] [--max-attempts N] [--max-turns N] | --check}"; shift
PARALLEL=4; LIMIT=0; MAX_ATTEMPTS=3; MAX_TURNS=150
while [ $# -gt 0 ]; do
    case "$1" in
        --parallel) PARALLEL="$2"; shift 2 ;;
        --limit) LIMIT="$2"; shift 2 ;;
        --max-attempts) MAX_ATTEMPTS="$2"; shift 2 ;;
        --max-turns) MAX_TURNS="$2"; shift 2 ;;
        *) echo "unknown option $1"; exit 2 ;;
    esac
done
[ -f "$CONFIG" ] || { echo "run 'bash run_batches.sh --check' first"; exit 2; }
# shellcheck disable=SC1090
source "$CONFIG"
export RUN_DIR="$HERE/runs/$RUN" ALLOWED EXTRA MODEL MAX_ATTEMPTS MAX_TURNS
[ -d "$RUN_DIR/batches" ] || { echo "no staged run at $RUN_DIR (run stage_extraction.py first)"; exit 2; }
[ -e "$RUN_DIR/STOP" ] && { echo "$RUN_DIR/STOP exists: $(cat "$RUN_DIR/STOP"). Delete it to continue."; exit 3; }
mkdir -p "$RUN_DIR/logs"

mapfile -t pending < <(python3 "$HERE/validate_batch.py" "$RUN_DIR/batches" --quiet | sed -n 's#^FAIL .*/##p')
total=$(ls "$RUN_DIR/batches" | wc -l)
[ "$LIMIT" -gt 0 ] && pending=("${pending[@]:0:$LIMIT}")
echo "$RUN: $total batches, ${#pending[@]} to run now (model $MODEL, $PARALLEL in parallel, max $MAX_TURNS turns)"
[ "${#pending[@]}" -eq 0 ] && exit 0
printf '%s\n' "${pending[@]}" | xargs -P "$PARALLEL" -I{} bash -c 'run_one "$1"' _ {}
left=$(python3 "$HERE/validate_batch.py" "$RUN_DIR/batches" --quiet | grep -c '^FAIL ')
echo "$RUN: done for now; $((total - left)) of $total batches pass validation."
[ -e "$RUN_DIR/STOP" ] && echo "Stopped early: $(cat "$RUN_DIR/STOP")"
exit 0
