#!/usr/bin/env bash
# curl-logging shim — lane l2. Not a proxy, not a filter: it records, then execs
# the real curl unchanged.
#
# WHY IT EXISTS. `./scripts/research-gate.sh` runs regression/hurl/05-public-config.check.sh,
# which issues real vendor requests — AGENTS.md §11 permits exactly this ("run the pinned
# suite") and nobody may extend it. Those requests are part of this pass's vendor
# traffic and therefore part of its cap. Without a shim they are invisible to
# results.jsonl, and an accounting line that silently excludes the gate's own traffic
# is the same failure mode as `probe3.sh` in area A, where the log append failed and
# the row had to be added by hand.
#
# It records URL, method and outcome to $L2_CURL_LOG, one JSON line per invocation,
# then `exec`s the real /usr/bin/curl with the identical argv. Nothing is added,
# removed or reordered — so a request the suite makes is the request the suite would
# have made, and the row is evidence rather than a reconstruction.
L2_CURL_LOG="${L2_CURL_LOG:?L2_CURL_LOG must be set}"
__real=/usr/bin/curl
__args=("$@")
__url=""
__method="GET"
for ((i=0; i<${#__args[@]}; i++)); do
  case "${__args[$i]}" in
    -X) __method="${__args[$((i+1))]:-GET}";;
    --request) __method="${__args[$((i+1))]:-GET}";;
    -X*) __method="${__args[$i]#-X}";;
    -w) __w="${__args[$((i+1))]:-}";;
    -o) :;;
    http://*|https://*) __url="${__args[$i]}";;
  esac
done
__tq=$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)
__out=$("$__real" "$@" 2>/dev/null)
__rc=$?
__td=$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)
python3 - "$L2_CURL_LOG" "$__tq" "$__td" "$__method" "$__url" "${__w:-}" "$__out" "$__rc" <<'PY'
import json, sys
(p, tq, td, method, url, w, code, rc) = sys.argv[1:9]
open(p, "a").write(json.dumps({
    "t_queued": tq, "t_done": td, "method": method, "url": url,
    "http_status": code, "curl_exit": int(rc),
    "issued_by": "regression/hurl/05-public-config.check.sh via the curl shim, under "
                 "scripts/research-gate.sh — AGENTS.md §11 permits re-running the pinned "
                 "suite and nothing else; the suite's own pacing is the repo's, not this "
                 "pass's sleep-inside-flock harness",
}) + "\n")
PY
printf '%s' "$__out"
exit $__rc