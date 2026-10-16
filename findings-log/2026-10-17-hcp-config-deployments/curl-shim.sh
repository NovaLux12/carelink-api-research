#!/usr/bin/env bash
# curl-logging shim — lane l2. Not a proxy, not a filter: it records, then execs
# the real curl.
#
# WHY IT EXISTS. `./scripts/research-gate.sh` runs regression/hurl/05-public-config.check.sh,
# which issues real vendor requests — AGENTS.md §11 permits exactly this ("run the pinned
# suite") and nobody may extend it. Those requests are part of this pass's vendor
# traffic and therefore part of its cap. Without a shim they are invisible to
# results.jsonl, and an accounting line that silently excludes the gate's own traffic
# is the same failure mode as `probe3.sh` in area A, where the log append failed and
# the row had to be added by hand.
#
# WHAT IT CHANGES IN THE REQUEST: nothing. No method, URL, header or body argument is
# added, removed or reordered. The ONE addition is conditional and output-only:
#
#   - if the caller's argv already carries `-w` / `--write-out`, NOTHING is added.
#     curl REPLACES rather than concatenates multiple `--write-out` options (verified
#     locally on a file:// URL: `-w '%{http_code}' --write-out '%{stderr}%{http_code}'`
#     left stdout EMPTY), so adding one would destroy the status the caller is capturing.
#     The status is read from the caller's own stdout in that case.
#   - if the caller carries no `-w`, `--write-out '%{stderr}%{http_code}'` is appended.
#     `%{stderr}` redirects that output to stderr, so **stdout stays exactly what the
#     caller would have seen** — the response body — and the status lands on stderr.
#     Verified locally on a file:// URL: stdout was the body, stderr the status.
#
# WHY THIS WAS REWRITTEN (2026-10-17, verifier round 1 finding B1). The first version
# logged the whole of curl's stdout as `http_status` with no discrimination. For the
# requests the suite sends with `-o <file>` and no `-w`, stdout IS the body, so 11 of
# 13 rows in the first absorbed run carried a body fragment — one of them an HTML
# document — in a status column, and the repair pass that ran afterwards covered only
# that first run. The defect was never the shim's intent but its refusal to ask curl
# for the status on a channel of its own.
L2_CURL_LOG="${L2_CURL_LOG:?L2_CURL_LOG must be set}"
__real=/usr/bin/curl
__args=("$@")
__url=""
__method="GET"
__has_w=0
for ((i=0; i<${#__args[@]}; i++)); do
  case "${__args[$i]}" in
    -X) __method="${__args[$((i+1))]:-GET}";;
    --request) __method="${__args[$((i+1))]:-GET}";;
    -X*) __method="${__args[$i]#-X}";;
    -w|--write-out) __has_w=1;;
    --write-out=*) __has_w=1;;
    -o) :;;
    http://*|https://*) __url="${__args[$i]}";;
  esac
done
__tq=$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)
__err=$(mktemp "${TMPDIR:-/tmp}/l2-shim-err-XXXXXX")
trap 'rm -f "$__err"' EXIT
if [ "$__has_w" -eq 1 ]; then
  # caller owns the write-out; stdout carries the status and stdout is NOT the body
  __out=$("$__real" "$@" 2>/dev/null)
  __rc=$?
  __status="$__out"
  __src="caller's own -w on stdout (curl REPLACES rather than concatenates multiple --write-out, so none was added)"
else
  # caller writes the body to stdout; ask curl for the status on stderr only
  __out=$("$__real" "$@" --write-out '%{stderr}%{http_code}' 2>"$__err")
  __rc=$?
  __status=$(tr -d '\r\n' < "$__err")
  __src="curl --write-out '%{stderr}%{http_code}' appended; stdout left as the caller would have seen it"
fi
__td=$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)
python3 - "$L2_CURL_LOG" "$__tq" "$__td" "$__method" "$__url" "$__status" "$__src" "$__rc" <<'PY'
import json, sys
(p, tq, td, method, url, status, src, rc) = sys.argv[1:9]
# A silently dropped log line would put a vendor request in this pass's traffic with no
# row for it — the exact defect this shim exists to prevent. So a write failure is LOUD
# on stderr, and it never changes the exit status the caller sees.
try:
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "t_queued": tq, "t_done": td, "method": method, "url": url,
            "http_status": status, "curl_exit": int(rc),
            "status_source": src,
            "issued_by": "regression/hurl/05-public-config.check.sh via the curl shim, under "
                         "scripts/research-gate.sh — AGENTS.md §11 permits re-running the "
                         "pinned suite and nothing else; the suite's own pacing is the "
                         "repo's, not this pass's sleep-inside-flock harness",
        }) + "\n")
except OSError as e:
    sys.stderr.write(f"l2 curl-shim: COULD NOT LOG {url} ({e}) — request unrecorded\n")
PY
printf '%s' "$__out"
exit $__rc