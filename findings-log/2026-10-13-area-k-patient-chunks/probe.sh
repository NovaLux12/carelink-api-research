#!/bin/bash
# Area K sweep — the 211 patient lazy chunks, for the committed discovery token set.
# Claim issue #56. Cap 230, GET only, curl --compressed, 2.5 s sleep INSIDE the
# per-host flock, TS_SENT emitted inside the lock immediately before curl execs.
#
# WHY THIS SWEEP EXISTS (the area's own argument, restated so a reader of the
# harness knows what the 211 cells are for): every bundle claim this repo makes
# about clients is scoped, at every use, to the EAGER MAIN BUNDLE ONLY. Area V
# turned that scope into a load-bearing limit. A lazy chunk is exactly where a
# feature-gated call site lives, so area V's two negatives are provisional until
# this corpus is swept.
#
# THE LIST IS NOT DERIVED HERE. It is copied verbatim from area V's committed
# artefact, which was itself written from the patient runtime bundle's own f.u
# map on 2026-10-13. Zero paths are invented, enumerated or guessed here — which
# is what makes a 211-cell sweep a bounded candidate list rather than fuzzing
# (CONTRIBUTING-research.md step 2). chunks-swept.txt is that copy; if it ever
# differs from area V's file, sha256sum of both is compared before the sweep and
# the sweep does not start.
#
# URL FORM: <id>.<hash>.js at the ASSET ROOT, because the runtime sets .p="".
# The `<base href="/app">` reading is recorded as wrong in JSMAP-HUNT section 5.
#
# ORDER: three controls FIRST, so the verdict is not contaminated by the data it
# judges. Then the 211, in the committed order.
#   1. negative twin  — a real chunk id with ONE mutated hash character. Proves
#                       "does not exist" is distinguishable from "exists" on
#                       this exact path shape.
#   2. positive       — the eager main bundle, which area V measured carrying the
#                       token set. Proves the fetch-and-grep pipeline can detect
#                       these tokens AT ALL, so a zero sweep is a zero and not a
#                       broken matcher. Without it, a negative over 211 bodies
#                       means nothing.
#   3. the runtime    — re-derives the chunk map from the runtime itself, so the
#                       corpus is proven current rather than inherited from
#                       another pass's note. Compared offline against the
#                       committed list; zero requests.
#
# Bodies (the 211 chunks plus a 3.4 MB main bundle) are written to $TMPBODIES and
# never committed. Digests, sizes, the verdict table and the offline grep output
# are committed.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
# LOOP is the shared per-host lock directory. This file sits at
# <checkout>/.loop/worktrees/k/findings-log/<dir>/, so four levels up is .loop.
# It is NOT inside the worktree and is shared with the other three workers: the
# lock is what makes the spacing claim true rather than merely intended.
LOOP="$(cd "$HERE/../../../.." && pwd)"
LOGDIR=$HERE
OUT=$LOGDIR/headers
DELAY=${DELAY:-2.5}
CAP=${CAP:-230}
TMPBODIES=${TMPBODIES:?set TMPBODIES to a writable directory for the response bodies}
HOST=carelink.minimed.eu
LOCK="$LOOP/host-$HOST.lock"
LIST="$LOGDIR/chunks-swept.txt"
VTSV="$LOGDIR/verdicts.tsv"
LEDGER="$LOGDIR/results.jsonl"
RUNLOG="$LOGDIR/run.log"
mkdir -p "$OUT"
[ -d "$TMPBODIES" ] || { echo "TMPBODIES is not a directory" >&2; exit 2; }
[ -e "$LOCK" ] || : > "$LOCK"

# RESUMABLE, and the reason is a rule rather than a convenience: every request
# gets a row, whatever issued it. A harness that truncates its own ledger on
# start-up deletes the record of the requests it already spent, which is how a
# pass under-reports its own budget. So the ledger is APPENDED to, the sequence
# continues from the highest seq already present, and any path already in the
# ledger is not re-sent. This run genuinely needed it: attempt 1 was launched
# detached and died with its parent shell after 4 rows, and those 4 requests
# were real and are kept here rather than discarded.
RESUME=0
if [ -s "$LEDGER" ]; then RESUME=1; fi
if [ "$RESUME" = "1" ]; then
  SEQ=$(python3 -c '
import json,sys
m=0
for line in open(sys.argv[1]):
    line=line.strip()
    if line:
        try: m=max(m,int(json.loads(line)["seq"]))
        except Exception: pass
print(m)' "$LEDGER")
  echo "RESUME: ledger already holds $SEQ rows; continuing from seq $((SEQ+1))" >&2
else
  : > "$LEDGER"; : > "$VTSV"; : > "$RUNLOG"; SEQ=0
fi

sent() { # sent <path> -> 0 if this exact path already has a ledger row
  grep -qF "\"path\": \"$1\"" "$LEDGER" 2>/dev/null
}

# The temp-body directory is REDACTED AT THE POINT OF GENERATION, not afterwards:
# AGENTS.md section 7 forbids a machine path in any committed file, and a
# hand-scrub of an artefact is a one-off rather than a control (area V recorded
# that this exact mistake cost a re-run).
echo "run start: $(date -u +%FT%T.%3NZ) tmpbodies=<REDACTED> delay=${DELAY} cap=${CAP} host=${HOST} resume=${RESUME} from_seq=$((SEQ+1))" >> "$RUNLOG"

# Hits column for verdicts.tsv: ONE case-SENSITIVE alternation over the core
# token set. It is a summary count, not a verdict — the full cs / ci / quoted-
# literal census with byte offsets and enclosing identifiers is extract.sh, which
# is offline and makes no claim this count cannot support.
hits_of() { # hits_of <bodyfile>
  [ -f "$1" ] || { echo "NO_BODY"; return 0; }
  LC_ALL=C grep -o -E 'baseUrlPde|baseUrlCumulus|baseUrlCms|baseUrlAem|baseUrlCareLink|baseUrl|discover/android|discover|clcloud|api/carepartner|pde|system\.gc\.gz\.transition\.flags|patient-timeline|dialog-lite' "$1" 2>/dev/null | wc -l | tr -d ' '
}

req() { # req <path> <role> <tag>
  local path="$1" role="$2" tag="$3"
  SEQ=$((SEQ+1)); local seq=$SEQ
  if [ "$SEQ" -gt "$CAP" ]; then
    echo "CAP REACHED at seq=$SEQ — refusing to send. Ledger holds $(wc -l < "$LEDGER") rows." >&2
    echo "cap reached: $(date -u +%FT%T.%3NZ) rows=$(wc -l < "$LEDGER")" >> "$RUNLOG"
    return 9
  fi
  local url="https://$HOST$path"
  local t_queued; t_queued=$(date -u +%FT%T.%3NZ)
  local out; out=$(flock "$LOCK" "$HERE/send.sh" "$DELAY" "$OUT/$tag.h" "$TMPBODIES/$tag.b" "$url" 2>&1)
  local t_done; t_done=$(date -u +%FT%T.%3NZ)
  local t_sent code curl_exit
  t_sent=$(printf '%s\n' "$out"  | sed -n 's/^TS_SENT //p'     | head -1)
  code=$(printf '%s\n'    "$out"  | sed -n 's/^HTTP_STATUS //p' | head -1)
  curl_exit=$(printf '%s\n' "$out" | sed -n 's/^CURL_EXIT //p'  | head -1)
  [ -n "$t_sent" ]   || t_sent="(unrecorded)"
  [ -n "$code" ]     || code="000"
  [ -n "$curl_exit" ] || curl_exit="-1"
  local ct="(none)"
  [ -f "$OUT/$tag.h" ] && ct=$(grep -i '^content-type:' "$OUT/$tag.h" | tail -1 | tr -d '\r' | sed 's/^[^:]*: *//')
  [ -n "$ct" ] || ct="(none)"
  # The discriminating headers this host family actually offers. x-amzn-errortype
  # and x-ca-err are the clcloud.* signals and are expected to be ABSENT here;
  # they are captured anyway so a reader can see that rather than assume it.
  local amz="(none)" caerr="(none)" xcache="(none)" acao="(none)" cenc="(none)"
  [ -f "$OUT/$tag.h" ] && {
    amz=$(grep -i '^x-amzn-errortype:' "$OUT/$tag.h" | tail -1 | tr -d '\r' | sed 's/^[^:]*: *//'); [ -n "$amz" ] || amz="(none)"
    caerr=$(grep -i '^x-ca-err:' "$OUT/$tag.h" | tail -1 | tr -d '\r' | sed 's/^[^:]*: *//'); [ -n "$caerr" ] || caerr="(none)"
    xcache=$(grep -i '^x-cache:' "$OUT/$tag.h" | tail -1 | tr -d '\r' | sed 's/^[^:]*: *//'); [ -n "$xcache" ] || xcache="(none)"
    acao=$(grep -i '^access-control-allow-origin:' "$OUT/$tag.h" | tail -1 | tr -d '\r' | sed 's/^[^:]*: *//'); [ -n "$acao" ] || acao="(none)"
    cenc=$(grep -i '^content-encoding:' "$OUT/$tag.h" | tail -1 | tr -d '\r' | sed 's/^[^:]*: *//'); [ -n "$cenc" ] || cenc="(none)"
  }
  local ctype_full="(none)"
  [ -f "$OUT/$tag.h" ] && ctype_full=$(tr '\r' ' ' < "$OUT/$tag.h" | tr '\n' '|' | sed 's/|$//')
  [ -n "$ctype_full" ] || ctype_full="(none)"
  local bytes=0 sha="(none)" mtns=""
  if [ -f "$TMPBODIES/$tag.b" ]; then
    bytes=$(stat -c%s "$TMPBODIES/$tag.b")
    sha=$(sha256sum "$TMPBODIES/$tag.b" | cut -d' ' -f1)
    # st_mtime_ns, NOT stat -c%Y: %Y truncates to whole seconds and therefore
    # cannot resolve a 2.5 s sleep (area V recorded that defect and its fix).
    mtns=$(python3 -c 'import os,sys;print(os.stat(sys.argv[1]).st_mtime_ns)' "$TMPBODIES/$tag.b")
  fi
  # Row written through the ENVIRONMENT, never heredoc interpolation: raw header
  # bytes contain quotes.
  V_SEQ="$seq" V_HOST="$HOST" V_TAG="$tag" V_PATH="$path" V_ROLE="$role" V_URL="$url" \
  V_CODE="$code" V_EXIT="$curl_exit" V_CT="$ct" V_CFULL="$ctype_full" V_BYTES="$bytes" \
  V_SHA="$sha" V_MTNS="$mtns" V_DELAY="$DELAY" V_TQ="$t_queued" V_TS="$t_sent" V_TD="$t_done" \
  V_AMZ="$amz" V_CAERR="$caerr" V_XCACHE="$xcache" V_ACAO="$acao" V_CENC="$cenc" \
  python3 -c '
import json, os, sys
e = os.environ
row = {
  "seq": int(e["V_SEQ"]), "host": e["V_HOST"], "host_tag": e["V_TAG"],
  "method": "GET", "path": e["V_PATH"], "role": e["V_ROLE"], "url": e["V_URL"],
  "http_status": e["V_CODE"], "curl_exit": int(e["V_EXIT"]),
  "content_type": e["V_CT"], "ctype_full": e["V_CFULL"],
  "content_encoding": e["V_CENC"],
  "x_amzn_errortype": e["V_AMZ"], "x_ca_err": e["V_CAERR"],
  "x_cache": e["V_XCACHE"], "access_control_allow_origin": e["V_ACAO"],
  "body_bytes": int(e["V_BYTES"]), "body_sha256": e["V_SHA"],
  "body_mtime_ns": e["V_MTNS"] or "(none)",
  "delay_declared_s": e["V_DELAY"],
  "t_queued": e["V_TQ"], "t_sent": e["V_TS"], "t_done": e["V_TD"],
}
open(sys.argv[1], "a").write(json.dumps(row) + "\n")
' "$LEDGER"
  printf '%s seq=%s host=%s tag=%s code=%s ctype=%s bytes=%s sha=%s\n' \
    "$t_sent" "$seq" "$HOST" "$tag" "$code" "$ct" "$bytes" "$sha" >> "$RUNLOG"
  echo "seq=$seq tag=$tag code=$code ctype=$ct bytes=$bytes" >&2
  local h; h=$(hits_of "$TMPBODIES/$tag.b")
  printf '%s\t%s\t%s\t%s\t%s\n' "$path" "$code" "$bytes" "$sha" "$h" >> "$VTSV"
  return 0
}

# ---------------------------------------------------------------- controls, first
# 1. NEGATIVE TWIN. First entry of the committed list is 12.c22952a522974f5f.js;
# the twin differs in the final hash character only. A mutation of a real entry,
# so the comparison is like-for-like and no path outside the list is invented.
FIRST=$(head -1 "$LIST")
if [ -z "$FIRST" ]; then echo "chunks-swept.txt is empty — refusing to run" >&2; exit 2; fi
# One character of the CONTENT HASH is replaced, nothing else: the id stays real,
# the hash becomes wrong. Assert the mutation actually happened rather than
# trusting the regex — a control that silently built the real path would make the
# negative twin a false control.
MUT=$(printf '%s' "$FIRST" | python3 -c '
import sys, re
s = sys.argv[1].strip()
m = re.fullmatch(r"([0-9]+)\.([0-9a-f]+)\.js", s)
if not m: print(""); raise SystemExit
i, h = m.group(1), m.group(2)
h2 = h[:-1] + ("e" if h[-1] != "e" else "f")
print(f"{i}.{h2}.js")' "$FIRST")
if [ -z "$MUT" ] || [ "$MUT" = "$FIRST" ]; then
  echo "negative-twin mutation failed (got '$MUT' from '$FIRST') — refusing to run" >&2; exit 2
fi
echo "== control 1: negative twin ${MUT} (from ${FIRST}) ==" >&2
sent "/$MUT" || req "/$MUT" "CONTROL-negative-twin-of-a-real-chunk-id-proves-absent-is-distinguishable" "k-negative-twin" || exit 9

# 2. POSITIVE. The eager main bundle area V measured at 3,417,255 B,
# sha256 0fb4fbd4... . It must resolve AND carry the token set; if it does not,
# the sweep below is not a zero, it is a broken matcher.
echo "== control 2: positive, the eager main bundle ==" >&2
sent "/main.6595daf83bd6d4b1.js" || req "/main.6595daf83bd6d4b1.js" "CONTROL-positive-proves-the-fetch-and-grep-pipeline-can-detect-the-token-set" "k-main" || exit 9

# 3. THE RUNTIME. Re-derives the chunk map so the corpus is proven current rather
# than inherited. Compared offline against the committed list.
echo "== control 3: the runtime bundle, to re-derive the chunk map ==" >&2
sent "/runtime.79e2f9040b1dad8f.js" || req "/runtime.79e2f9040b1dad8f.js" "CONTROL-the-runtime-defines-the-corpus-compared-offline-against-the-committed-list" "k-runtime" || exit 9

# ------------------------------------------------------------------ the 211 cells
n=0
while IFS= read -r chunk || [ -n "$chunk" ]; do
  [ -n "$chunk" ] || continue
  case "$chunk" in \#*) continue ;; esac
  n=$((n+1))
  sent "/$chunk" && continue
  req "/$chunk" "SWEEP-lazy-chunk-from-the-committed-list" "k-$(printf '%s' "$chunk" | sed 's/\./-/g')" || exit 9
done < "$LIST"
echo "swept $n cells from the committed list (skipped any already in the ledger)" >> "$RUNLOG"

echo "run end: $(date -u +%FT%T.%3NZ) rows=$(wc -l < "$LEDGER") cap=${CAP}" >> "$RUNLOG"
# The bodies path goes to the operator's terminal only, never to a file.
echo "TMPBODIES=$TMPBODIES" >&2