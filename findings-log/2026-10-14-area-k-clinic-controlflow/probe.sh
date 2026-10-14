#!/bin/bash
# Area K — clinic 225-chunk corpus, mined for CONTROL FLOW (not endpoints).
# Claim issue #121. Host carelinkhp.minimed.eu ONLY. GET only. curl --compressed.
#
# WHAT THIS SWEEP IS FOR. Every bundle claim in this repo about client call
# sites is scoped to the EAGER MAIN BUNDLE. K proper asks the question no prior
# pass asked of the clinic build: what do the call sites DO with the field names,
# and what does the conditional logic imply about the request shape. The
# corpus is the clinic build's own 225 lazy chunks + the eager main bundle.
#
# ORDER: SIX CONTROLS FIRST, then the 225, in the committed order. The oracle
# verdict must not be contaminated by the data it judges, so nothing that can
# move a verdict is sent before the controls have fixed the verdict rules.
#   C1 certainly-absent  — a fabricated chunk name. carelinkhp.minimed.eu
#                         answers 200 text/html 5518 B for EVERY unknown path,
#                         so this control exists to prove that discrimination is
#                         on Content-Type and that status carries nothing.
#   C2 positive          — the eager main bundle. Proves the fetch-and-grep
#                         pipeline can detect the target tokens AT ALL. Without
#                         it a zero over 226 bodies is a broken matcher, not a
#                         finding.
#   C3 negative twin     — a real chunk id with ONE mutated hash character.
#                         Proves "does not exist" is distinguishable from
#                         "exists" on this exact path shape.
#   C4 the runtime       — re-derives the chunk map from the build's own f.u, so
#                         the corpus is proven CURRENT rather than inherited
#                         from another pass's committed file.
#   C5 the id form of 2076 — the name f.u does NOT emit for that id. Proves the
#                         name-substitution is load-bearing on THIS corpus rather
#                         than a note inherited from the patient build.
#   C6 case control      — a real chunk name with the extension uppercased.
#                         Oracle B says this namespace is case-sensitive; this
#                         proves a name mismatch reads as ABSENT here, so a
#                         filename defect cannot masquerade as a chunk.
#
# THE LIST IS NOT DERIVED HERE. It is copied verbatim from the 2026-10-13
# clinic-denominator pass (issue #78), which derived it from this build's own
# f.u. Zero paths are invented, enumerated or guessed. C4 re-derives the map
# from the live runtime BEFORE the sweep and the two are diffed BY HASH offline
# — a name diff cannot distinguish "same file, wrong name" from "two different
# files" (docs/09 trap row 3).
#
# Bodies go to $TMPBODIES, outside the repository, and are never committed
# (AGENTS.md section 7). The ledger carries digests, sizes and a short body
# head; headers/ carries each response head.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
LOOP="$(cd "$HERE/../../.." && pwd)"          # <checkout>/.loop — shared, not in the worktree
LOGDIR=$HERE
OUT=$LOGDIR/headers
DELAY=${DELAY:-2.5}
CAP=${CAP:-231}
TMPBODIES=${TMPBODIES:?set TMPBODIES to a writable directory outside the repo}
HOST=carelinkhp.minimed.eu
LOCK="$LOOP/host-$HOST.lock"
LIST="$LOGDIR/committed-map.txt"
LEDGER="$LOGDIR/results.jsonl"
RUNLOG="$LOGDIR/run.log"
PHASE=${1:-all}
mkdir -p "$OUT"
[ -d "$TMPBODIES" ] || { echo "TMPBODIES is not a directory" >&2; exit 2; }
[ -e "$LOCK" ] || : > "$LOCK"

# RESUMABLE, because the rule is not a convenience: every request gets a ledger
# row, whatever issued it. A harness that truncates its own ledger on start-up
# deletes the record of the requests it already spent.
RESUME=0
if [ -s "$LEDGER" ]; then RESUME=1; fi
if [ "$RESUME" = 1 ]; then
  SEQ=$(python3 -c '
import json,sys
m=0
for line in open(sys.argv[1]):
    line=line.strip()
    if line:
        try: m=max(m,int(json.loads(line)["seq"]))
        except Exception: pass
print(m)' "$LEDGER")
else
  : > "$LEDGER"; SEQ=0
fi
# Redact at the point of generation: a machine path in a committed file is a §7
# breach and a hand-scrub of an artefact is a one-off, not a control.
echo "phase=${PHASE} run start: $(date -u +%FT%T.%3NZ) tmpbodies=<REDACTED> delay=${DELAY} cap=${CAP} host=${HOST} resume=${RESUME} from_seq=$((SEQ+1))" >> "$RUNLOG"

sent() { grep -qF "\"emitted\": \"$1\"" "$LEDGER" 2>/dev/null; }

req() { # req <filename-without-leading-slash> <id|""> <role>
  local name="$1" id="$2" role="$3"
  SEQ=$((SEQ+1)); local seq=$SEQ
  if [ "$SEQ" -gt "$CAP" ]; then
    echo "CAP REACHED at seq=$SEQ — refusing to send. Ledger holds $(wc -l < "$LEDGER") rows." >&2
    echo "cap reached: $(date -u +%FT%T.%3NZ) rows=$(wc -l < "$LEDGER")" >> "$RUNLOG"
    return 9
  fi
  local path="/$name"
  local url="https://$HOST$path"
  local hash="" emitted_name="$name"
  case "$name" in
    *.*.js) hash="${name#*.}"; hash="${hash%.js}"; emitted_name="${name%%.*}.${hash}.js" ;;
    *.js)   hash=""; emitted_name="$name" ;;
  esac
  local t_queued; t_queued=$(date -u +%FT%T.%3NZ)
  local tag="$(printf '%s' "$name" | sed 's/[^A-Za-z0-9._-]/_/g')"
  local out; out=$(flock "$LOCK" "$HERE/send.sh" "$DELAY" "$OUT/$seq.h" "$TMPBODIES/$seq-$tag.b" "$url" 2>&1)
  local t_done; t_done=$(date -u +%FT%T.%3NZ)
  local t_sent code curl_exit
  t_sent=$(printf '%s\n'  "$out" | sed -n 's/^TS_SENT //p'     | head -1)
  code=$(printf '%s\n'    "$out" | sed -n 's/^HTTP_STATUS //p' | head -1)
  curl_exit=$(printf '%s\n' "$out" | sed -n 's/^CURL_EXIT //p'  | head -1)
  [ -n "$t_sent" ]   || t_sent="(unrecorded)"
  [ -n "$code" ]     || code="000"
  [ -n "$curl_exit" ] || curl_exit="-1"
  local ct="(none)"
  [ -f "$OUT/$seq.h" ] && ct=$(grep -i '^content-type:' "$OUT/$seq.h" | tail -1 | tr -d '\r' | sed 's/^[^:]*: *//')
  [ -n "$ct" ] || ct="(none)"
  local cenc="(none)" etag="(none)" ccache="(none)" lm="(none)"
  [ -f "$OUT/$seq.h" ] && {
    cenc=$(grep -i '^content-encoding:' "$OUT/$seq.h" | tail -1 | tr -d '\r' | sed 's/^[^:]*: *//'); [ -n "$cenc" ] || cenc="(none)"
    etag=$(grep -i '^etag:' "$OUT/$seq.h" | tail -1 | tr -d '\r' | sed 's/^[^:]*: *//'); [ -n "$etag" ] || etag="(none)"
    ccache=$(grep -i '^cache-control:' "$OUT/$seq.h" | tail -1 | tr -d '\r' | sed 's/^[^:]*: *//'); [ -n "$ccache" ] || ccache="(none)"
    lm=$(grep -i '^last-modified:' "$OUT/$seq.h" | tail -1 | tr -d '\r' | sed 's/^[^:]*: *//'); [ -n "$lm" ] || lm="(none)"
  }
  local bytes=0 sha="(none)" mtns="" head=""
  local bfile="$TMPBODIES/$seq-$tag.b"
  if [ -f "$bfile" ]; then
    bytes=$(stat -c%s "$bfile")
    sha=$(sha256sum "$bfile" | cut -d' ' -f1)
    # st_mtime_ns, NOT stat -c%Y: %Y truncates to whole seconds and cannot
    # resolve a 2.5 s sleep. The mtime series is the spacing authority here
    # (docs/09 trap: the harness date series is the suspect, the kernel's write
    # time is not).
    mtns=$(python3 -c 'import os,sys;print(os.stat(sys.argv[1]).st_mtime_ns)' "$bfile")
    # 90 B head, as the 2026-10-13 clinic pass recorded it. All control
    # characters including newline are dropped: the row travels through an
    # environment variable, where an embedded newline would be ambiguous.
    head=$(head -c 90 "$bfile" | LC_ALL=C tr -d '\000-\037\177-\377' | sed 's/["\\]/_/g')
  fi
  # Row written through the ENVIRONMENT, never heredoc interpolation.
  V_SEQ="$seq" V_ID="$id" V_EMITTED="$emitted_name" V_HASH="$hash" V_PATH="$path" \
  V_ROLE="$role" V_URL="$url" V_CODE="$code" V_EXIT="$curl_exit" V_CT="$ct" V_BYTES="$bytes" \
  V_SHA="$sha" V_MTNS="$mtns" V_DELAY="$DELAY" V_TQ="$t_queued" V_TS="$t_sent" V_TD="$t_done" \
  V_HEAD="$head" V_CENC="$cenc" V_ETAG="$etag" V_CCACHE="$ccache" V_LM="$lm" \
  python3 -c '
import json, os, sys
e = os.environ
row = {
  "seq": int(e["V_SEQ"]),
  "id": (int(e["V_ID"]) if e["V_ID"] else None),
  "emitted": e["V_EMITTED"], "hash": e["V_HASH"] or None,
  "role": e["V_ROLE"], "path": e["V_PATH"],
  "t_queued": e["V_TQ"], "t_sent": e["V_TS"], "t_done": e["V_TD"],
  "status": e["V_CODE"], "content_type": e["V_CT"],
  "content_encoding": e["V_CENC"], "etag": e["V_ETAG"],
  "cache_control": e["V_CCACHE"], "last_modified": e["V_LM"],
  "size": int(e["V_BYTES"]), "sha256": e["V_SHA"],
  "body_mtime_ns": e["V_MTNS"] or "(none)",
  "body_head": e["V_HEAD"],
  "delay_declared_s": e["V_DELAY"], "curl_exit": int(e["V_EXIT"]),
}
open(sys.argv[1], "a").write(json.dumps(row) + "\n")
' "$LEDGER"
  printf '%s seq=%s name=%s code=%s ctype=%s bytes=%s sha=%s\n' \
    "$t_sent" "$seq" "$emitted_name" "$code" "$ct" "$bytes" "$sha" >> "$RUNLOG"
  echo "seq=$seq name=$emitted_name code=$code ctype=$ct bytes=$bytes sha=$sha" >&2
  return 0
}

# =============================================================== C1..C6, FIRST
# C1 CERTAINLY-ABSENT. The name is the one the 2026-10-13 pool-K pass recorded
# as absent (findings-log/2026-10-13-pool-k-clinic-url-form/FINDINGS.md req 4),
# so this cell is also a drift check on the SPA shell's own digest.
sent "probe-absent-9f8e7d6c5b4a.js" || req "probe-absent-9f8e7d6c5b4a.js" "" \
  "C1-certainly-absent-fabricated-name-proves-the-oracle-is-content-type-not-status" || exit 9

# C2 POSITIVE. The eager main bundle, 3,397,615 B, sha256 2a7fa8e7af519c2b…, which
# area P measured carrying the system.logbook.entry.validation.config route
# literal at byte 2,768,979. If it does not resolve, or does not carry the token,
# the 225-cell zero below is a broken matcher and not a finding.
sent "main.fb5f8cb7eb60c4d5.js" || req "main.fb5f8cb7eb60c4d5.js" "" \
  "C2-positive-the-eager-main-bundle-proves-the-fetch-and-grep-pipeline-can-detect-the-target-tokens" || exit 9

# C3 NEGATIVE TWIN. First entry of the committed map is id 12, hash cfb28fafc1fe9cf5.
# Exactly one character of the CONTENT HASH is replaced, so the id stays real and
# the comparison is like-for-like. Assert the mutation happened rather than
# trusting the regex — a control that silently built the real path would make the
# twin a false control.
FIRST="$(head -1 "$LIST")"
[ -n "$FIRST" ] || { echo "committed-map.txt is empty — refusing to run" >&2; exit 2; }
MUT=$(printf '%s' "$FIRST" | python3 -c '
import sys, re
s = sys.argv[1].strip()
m = re.fullmatch(r"([0-9a-f]+) ([0-9a-zA-Z-]+) ([0-9a-f]+)", s)
if not m: print(""); raise SystemExit
i, n, h = m.group(1), m.group(2), m.group(3)
h2 = h[:-1] + ("e" if h[-1] != "e" else "f")
print(f"{i} {n} {h2}")' "$FIRST")
if [ -z "$MUT" ] || [ "$MUT" = "$FIRST" ]; then
  echo "negative-twin mutation failed (got '$MUT' from '$FIRST') — refusing to run" >&2; exit 2
fi
echo "== C3 negative twin: '$MUT' from '$FIRST' ==" >&2
MUTNAME="${MUT%% *}.$(printf '%s' "$MUT" | awk '{print $3}').js"
sent "$MUTNAME" || req "$MUTNAME" "$(printf '%s' "$MUT" | awk '{print $1}')" \
  "C3-negative-twin-a-real-chunk-id-with-one-mutated-hash-character-proves-absent-is-distinguishable" || exit 9

# C4 THE RUNTIME. Re-derives the chunk map from the build itself. The comparison
# against committed-map.txt is OFFLINE and makes no request; if the two disagree
# the sweep does not start on the stale list.
sent "runtime.a752bb828cca4b2c.js" || req "runtime.a752bb828cca4b2c.js" "" \
  "C4-the-runtime-defines-the-corpus-compared-offline-by-hash-against-the-committed-list" || exit 9

# C5 THE ID FORM OF 2076. f.u emits "common.<hash>.js" for that id, so this path
# must NOT exist. It reproduces the name-substitution trap on this corpus rather
# than inheriting the patient's measurement.
sent "2076.a62bb847b4ea289e.js" || req "2076.a62bb847b4ea289e.js" 2076 \
  "C5-the-id-form-of-chunk-2076-proves-the-f.u-name-substitution-is-load-bearing-on-this-corpus" || exit 9

# C6 CASE CONTROL. A real chunk name with the extension uppercased. Oracle B
# records this namespace as case-sensitive; the cell proves that a name defect
# reads as ABSENT here, so it cannot pass as a chunk.
sent "12.cfb28fafc1fe9cf5.JS" || req "12.cfb28fafc1fe9cf5.JS" "" \
  "C6-case-control-a-real-chunk-name-with-an-uppercased-extension-proves-a-name-defect-reads-as-absent" || exit 9

echo "controls done at seq=$SEQ" >&2

# ================================================================ the 225 cells
if [ "$PHASE" != "controls" ]; then
  n=0
  while read -r id name hash || [ -n "$id" ]; do
    [ -n "${id:-}" ] || continue
    case "$id" in \#*) continue ;; esac
    n=$((n+1))
    f="$name.$hash.js"
    sent "$f" && continue
    req "$f" "$id" "SWEEP-lazy-chunk-from-the-committed-map-under-the-name-f.u-emits" || exit 9
  done < "$LIST"
  echo "swept $n cells from the committed map (any already in the ledger were skipped)" >> "$RUNLOG"
fi

echo "phase=${PHASE} run end: $(date -u +%FT%T.%3NZ) rows=$(wc -l < "$LEDGER") cap=${CAP}" >> "$RUNLOG"
echo "TMPBODIES=$TMPBODIES" >&2