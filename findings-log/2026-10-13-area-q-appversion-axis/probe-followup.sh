#!/usr/bin/env bash
# Area Q — follow-up phase, 2 requests of the 20 cap left after probe.sh.
#
# WHY THIS EXISTS, and it is the reason the controls ran first:
#   probe.sh seq=6 and seq=7 both returned 404 "Not Found" for
#     app/src/main/java/com/eveningoutpost/dexdrip/cgm/carelinkfollow/CareLinkClient.java
#   at BOTH the pinned commit 366c97a8 and at master. The 404 body is byte-identical
#   to the certainly-absent-path control (seq=3, same sha256), and is NOT the
#   bad-ref control's body (seq=2, a different sha256, "No commit found for the ref").
#   So the ref resolved and the PATH did not. The path used here was reconstructed
#   from the sparse-checkout line in the source pass's "Reproducing this pass"
#   section, which is the one part of that citation this repo never checked.
#
#   Two readings, and they are not equivalent:
#     (a) the package directory moved/renamed at or after that commit, or
#     (b) the reconstructed path was simply wrong and the file is elsewhere.
#   One directory listing separates them. It is worth spending on, because the
#   difference between "the cited file:line does not resolve" and "the file
#   moved" is exactly the AGENTS.md section 6 item 6 distinction, and because
#   guessing a second path with no budget left would be how a citation gets
#   asserted without a resolution (docs/09 section 5 item 3).
#
# Same harness conventions as probe.sh: GET only, unauthenticated, sleep 2.5
# inside the per-host flock, three millisecond timestamps per row, ledger and
# run.log appended in the same schema and the same seq sequence.

set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="$HERE"
CAP=20
DELAY=2.5
SEQ=18   # continues probe.sh's sequence

LOCKS=""
d="$HERE"
while [ "$d" != "/" ]; do
  if [ -f "$d/.loop/BRIEF.md" ]; then LOCKS="$d/.loop"; break; fi
  d="$(dirname "$d")"
done
: "${LOCKS:?could not locate the pool .loop directory}"

mkdir -p "$OUT/headers" "$OUT/bodies" "$OUT/ts"

XD_FULL="366c97a8de5fe644b20910ab008da98a07391c7b"   # resolved at probe.sh seq=4

log() { echo "$*" >> "$OUT/run.log"; }

req() { # req <host> <path> <role> <tag>
  local host="$1" path="$2" role="$3" tag="$4"
  SEQ=$((SEQ+1))
  if [ "$SEQ" -gt "$CAP" ]; then
    log "seq=$SEQ ABORTED cap $CAP reached before $host$path"
    return 1
  fi
  touch "$LOCKS/host-$host.lock"
  local url="https://$host$path"
  local t_queued; t_queued=$(date -u +%FT%T.%3NZ)
  flock "$LOCKS/host-$host.lock" -c "
    sleep $DELAY
    date -u +%FT%T.%3NZ > '$OUT/ts/$tag.sent'
    curl -sS --compressed \
      -H 'Accept: application/vnd.github+json' \
      -H 'User-Agent: carelink-api-research-static-audit' \
      -D '$OUT/headers/$tag.h' -o '$OUT/bodies/$tag.b' \
      -w '%{http_code}' '$url' > '$OUT/ts/$tag.code' 2>'$OUT/headers/$tag.err'
    date -u +%FT%T.%3NZ > '$OUT/ts/$tag.done'
  "
  local flock_exit=$?
  local t_sent t_done code
  t_sent=$(cat "$OUT/ts/$tag.sent" 2>/dev/null || echo "(none)")
  t_done=$(cat "$OUT/ts/$tag.done" 2>/dev/null || echo "(none)")
  code=$(cat "$OUT/ts/$tag.code" 2>/dev/null || echo "000")
  local nbytes=0 sha="(none)"
  if [ -f "$OUT/bodies/$tag.b" ]; then
    nbytes=$(wc -c < "$OUT/bodies/$tag.b" | tr -d ' ')
    sha=$(sha256sum "$OUT/bodies/$tag.b" | cut -d' ' -f1)
  fi
  local cf
  cf=$(awk 'NR>1' "$OUT/headers/$tag.h" 2>/dev/null \
        | tr -d '\r' | awk '/: /{i=index($0,": ");k=tolower(substr($0,1,i-1));v=substr($0,i+2);
          if(k in a)a[k]=a[k]", "v;else a[k]=v} END{for(k in a)printf "%s: %s|",k,a[k]}' \
        | sed 's/|$//')
  [ -n "$cf" ] || cf="(none)"
  printf '%s' "$cf" > "$OUT/ts/$tag.cf"
  local status="${code:-000}"
  local curl_exit=0
  [ "$flock_exit" -eq 0 ] || curl_exit=$flock_exit
  local host_seq; host_seq=$(python3 -c "
import json
n = 0
try:
    for line in open('$OUT/results.jsonl'):
        try:
            if json.loads(line).get('host') == '$host': n += 1
        except ValueError: pass
except FileNotFoundError: pass
print(n + 1)")
  local head=""; head=$(head -c 200 "$OUT/bodies/$tag.b" 2>/dev/null | tr -d '\n\r')
  printf '%s' "$head" > "$OUT/ts/$tag.head"
  python3 - "$OUT/results.jsonl" "$SEQ" "$host_seq" "$host" "$tag" "$role" "$path" "$status" "$curl_exit" "$nbytes" "$sha" "$t_queued" "$t_sent" "$t_done" "$OUT/ts/$tag.cf" "$OUT/ts/$tag.head" <<'PY'
import json, sys
(_, out, seq, host_seq, host, tag, role, path, status, exit_, nbytes, sha,
 t_queued, t_sent, t_done, cf_file, head_file) = sys.argv
cf = open(cf_file, encoding="utf-8").read() or "(none)"
head = open(head_file, encoding="utf-8").read()
row = {
  "seq": int(seq), "host_seq": int(host_seq), "host": host, "host_tag": tag,
  "method": "GET", "path": path, "role": role,
  "sent_headers": "Accept: application/vnd.github+json | User-Agent: carelink-api-research-static-audit (UNAUTHENTICATED — no Authorization header)",
  "http_status": status, "curl_exit": int(exit_),
  "body_bytes": int(nbytes), "body_sha256": sha,
  "ctype_full": cf, "body_head_200": head,
  "t_queued": t_queued, "t_sent": t_sent, "t_done": t_done,
}
open(out, "a").write(json.dumps(row) + "\n")
PY
  log "t_queued=$t_queued t_sent=$t_sent t_done=$t_done seq=$SEQ host_seq=$host_seq $host $path method=GET role=$role status=$status bytes=$nbytes sha=$sha"
  echo "seq=$SEQ host_seq=$host_seq $host $path status=$status bytes=$nbytes sha=${sha:0:12}"
}

# Request 19 — the package directory one level up, at the PINNED commit.
req "api.github.com" "/repos/NightscoutFoundation/xDrip/contents/app/src/main/java/com/eveningoutpost/dexdrip/cgm?ref=$XD_FULL" \
    "DIAG-locate-package-dir" "19-xd-cgm-listing" || exit 1

# Request 20 — the last of the cap. NOT a re-ask of seq=6: the ledger has already
# established that carelinkfollow/CareLinkClient.java is absent at both refs, and
# re-asking a known 404 would spend the last request to confirm what the ledger
# already says. What is missing is the NAME of what is there, which is what turns
# "the cited file:line does not resolve" into a repairable citation or an honestly
# retired one.
req "api.github.com" "/repos/NightscoutFoundation/xDrip/contents/app/src/main/java/com/eveningoutpost/dexdrip/cgm/carelinkfollow?ref=$XD_FULL" \
    "DIAG-locate-file" "20-xd-carelinkfollow-listing" || exit 1

echo "done: $SEQ of a $CAP cap" | tee -a "$OUT/run.log"