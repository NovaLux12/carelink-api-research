#!/bin/bash
# Area AU — the 211 patient lazy chunks, swept on their EMITTED names, for the
# INSTINCT range tail and for any model-mapping route literal the eager bundle
# never names. Claim issue #217. Cap 225. GET only. 2.5 s sleep INSIDE the
# per-host flock. One host: carelink.minimed.eu.
#
# ORDER IS THE ARGUMENT. Three controls first, each with an asserted digest, and
# the run ABORTS (exit 3) rather than sweeping if any control disagrees. Without
# them a zero over 211 bodies says nothing: it could be a broken matcher, a stale
# corpus, or a wrong URL form. With them it is a measurement.
#
#   1. common.206e355a4a593fbd.js — a chunk KNOWN to exist, on the EMITTED name
#      (id-major 2076), digest pinned from area K's ledger: 200 / 21157 B /
#      de1f782d…. This is simultaneously the control for the id->name defect:
#      the id form 2076.… 404s, so if this 200s the name form is right.
#   2. runtime.79e2f9040b1dad8f.js — 200 / 8268 B / 0dfea208…. `f.u` is the only
#      thing that defines the corpus and the rename; derive.py rebuilds the list
#      from THESE bytes, so the population is re-anchored on today's fetch and
#      not inherited from another pass's note.
#   3. main.6595daf83bd6d4b1.js — the eager bundle, 200 / 3417255 B / 0fb4fbd4…. It
#      carries 3 `Instinct` occurrences and 0 `7896[0-9]` (area AM), so it is the
#
# THE LIST IS RE-DERIVED, NOT COPIED. derive.py reads `f.u` from the body fetched
# at seq 2 and writes lists/derived.txt; the run aborts unless it holds exactly
# 211 entries. The committed chunks-swept.txt is diffed against it offline
# (list-diff.txt) so the one known id->name divergence is MEASURED, not assumed.
#
# Bodies are written to $TMPBODIES and never committed. Digests, sizes and the
# census are. results.jsonl gets one row per request immediately after that
# request completes; hits.tsv gets one row per chunk as its body lands — so a
# kill mid-sweep loses at most the in-flight cell.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
# LOOP is the shared per-host lock directory: <checkout>/.loop/worktrees/lau/… is
# five levels below .loop. The lock is what makes the spacing claim true rather
# than merely intended, and it is shared with the other workers on this host.
LOOP="$(cd "$HERE/../../../../.." && pwd)"
LOGDIR=$HERE
OUT=$LOGDIR/headers
LISTS=$LOGDIR/lists
DELAY=${DELAY:-2.5}
CAP=${CAP:-225}
TMPBODIES=${TMPBODIES:?set TMPBODIES to a writable directory for the response bodies}
HOST=carelink.minimed.eu
LOCK="$LOOP/host-$HOST.lock"
VTSV=$LOGDIR/hits.tsv
LEDGER=$LOGDIR/results.jsonl
RUNLOG=$LOGDIR/run.log
mkdir -p "$OUT" "$LISTS"
[ -d "$TMPBODIES" ] || { echo "TMPBODIES is not a directory" >&2; exit 2; }
[ -e "$LOCK" ] || : > "$LOCK"

: > "$LEDGER"; : > "$VTSV"; : > "$RUNLOG"
SEQ=0

# The temp-body path is REDACTED AT THE POINT OF GENERATION: AGENTS.md §7 forbids a
# machine path in any committed file, and a hand-scrub is a one-off rather than a
# control.
echo "run start: $(date -u +%FT%T.%3NZ) tmpbodies=<REDACTED> delay=${DELAY} cap=${CAP} host=${HOST}" >> "$RUNLOG"

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
  local bytes=0 sha="(none)" mtns=""
  if [ -f "$TMPBODIES/$tag.b" ]; then
    bytes=$(stat -c%s "$TMPBODIES/$tag.b")
    sha=$(sha256sum "$TMPBODIES/$tag.b" | cut -d' ' -f1)
    # st_mtime_ns, NOT stat -c%Y: %Y truncates to whole seconds and cannot resolve
    # a 2.5 s sleep (area V recorded that defect and its fix).
    mtns=$(python3 -c 'import os,sys;print(os.stat(sys.argv[1]).st_mtime_ns)' "$TMPBODIES/$tag.b")
  fi
  V_SEQ="$seq" V_HOST="$HOST" V_TAG="$tag" V_PATH="$path" V_ROLE="$role" V_URL="$url" \
  V_CODE="$code" V_EXIT="$curl_exit" V_CT="$ct" V_BYTES="$bytes" \
  V_SHA="$sha" V_MTNS="$mtns" V_DELAY="$DELAY" V_TQ="$t_queued" V_TS="$t_sent" V_TD="$t_done" \
  python3 -c '
import json, os
e = os.environ
row = {
  "seq": int(e["V_SEQ"]), "host": e["V_HOST"], "host_tag": e["V_TAG"],
  "method": "GET", "path": e["V_PATH"], "role": e["V_ROLE"], "url": e["V_URL"],
  "http_status": e["V_CODE"], "curl_exit": int(e["V_EXIT"]),
  "content_type": e["V_CT"],
  "body_bytes": int(e["V_BYTES"]), "body_sha256": e["V_SHA"],
  "body_mtime_ns": e["V_MTNS"] or "(none)",
  "delay_declared_s": e["V_DELAY"],
  "t_queued": e["V_TQ"], "t_sent": e["V_TS"], "t_done": e["V_TD"],
}
open(e["LEDGER"], "a").write(json.dumps(row) + "\n")
' 
  printf '%s seq=%s tag=%s code=%s ctype=%s bytes=%s sha=%s\n' \
    "$t_sent" "$seq" "$tag" "$code" "$ct" "$bytes" "$sha" >> "$RUNLOG"
  echo "seq=$seq tag=$tag code=$code ctype=$ct bytes=$bytes" >&2
  # hits.tsv: one row per chunk, written as the body lands.
  if [ "$role" = "SWEEP-lazy-chunk-on-its-emitted-name" ]; then
    local row
    row=$(python3 "$HERE/census.py" "$TMPBODIES/$tag.b" "$path" 2>/dev/null | python3 -c '
import json,sys
try: o=json.load(sys.stdin)
except Exception: print("CENSUS_FAILED"); raise SystemExit
c=o["counts"]
cols=["7896","7896[0-9]","SKU-","productName","marketingName","Instinct",
      "model-mapping","modelMapping","ModelMapping","deviceModelMapping",
      "configuration/system"]
print("\t".join(str(c[t]["cs"]) for t in cols))')
    printf '%s\t%s\t%s\t%s\t%s\n' "$path" "$code" "$bytes" "$sha" "$row" >> "$VTSV"
  fi
  export V_SHA_OUT="$sha" V_BYTES_OUT="$bytes" V_CODE_OUT="$code"
  return 0
}
LEDGER="$LEDGER"  # exported for the python row writer
export LEDGER

# ---------------------------------------------------------------- control 1
# A chunk KNOWN to exist, requested on the name the runtime EMITS rather than on
# its id. Area K measured 200 / 21157 B / de1f782d… for this exact name.
echo "== control 1: known chunk on its emitted name (common.*) ==" >&2
req "/common.206e355a4a593fbd.js" \
    "CONTROL-known-chunk-on-its-emitted-name-proves-200-is-reachable-and-the-name-form-is-right" \
    "au-control1-common" || exit 9
C1_SHA=$(sha256sum "$TMPBODIES/au-control1-common.b" | cut -d' ' -f1)
C1_BYTES=$(stat -c%s "$TMPBODIES/au-control1-common.b")
if [ "$C1_SHA" != "de1f782d13c4a459683a8d770d9c4a19fc33406e5bc7d7b29aacf0edab6715e3" ] \
   || [ "$C1_BYTES" != "21157" ]; then
  echo "CONTROL 1 FAILED: expected 21157 B / de1f782d…, got $C1_BYTES B / $C1_SHA — ABORTING before the sweep." >&2
  echo "control 1 FAILED bytes=$C1_BYTES sha=$C1_SHA" >> "$RUNLOG"
  exit 3
fi
echo "control 1 PASS: 21157 B / de1f782d… (emitted name resolves; id form is the defect)" | tee -a "$RUNLOG" >&2

# ---------------------------------------------------------------- control 2
echo "== control 2: the runtime, to re-derive the corpus ==" >&2
req "/runtime.79e2f9040b1dad8f.js" \
    "CONTROL-the-runtime-defines-the-corpus-re-derived-here-not-inherited" \
    "au-control2-runtime" || exit 9
C2_SHA=$(sha256sum "$TMPBODIES/au-control2-runtime.b" | cut -d' ' -f1)
C2_BYTES=$(stat -c%s "$TMPBODIES/au-control2-runtime.b")
if [ "$C2_SHA" != "0dfea208804facf881a79ea9e8758dc6900e74ef174c11ba50250c0a62273722" ] \
   || [ "$C2_BYTES" != "8268" ]; then
  echo "CONTROL 2 FAILED: expected 8268 B / 0dfea208…, got $C2_BYTES B / $C2_SHA — ABORTING." >&2
  echo "control 2 FAILED bytes=$C2_BYTES sha=$C2_SHA" >> "$RUNLOG"
  exit 3
fi
echo "control 2 PASS: 8268 B / 0dfea208…" | tee -a "$RUNLOG" >&2

# ---- derive the list from TODAY'S runtime bytes, and assert the population ----
DERIVE_OUT=$(python3 "$HERE/derive.py" "$TMPBODIES/au-control2-runtime.b" "$LISTS/derived.txt") \
  || { echo "derive.py REFUSED — ABORTING before the sweep." >&2; exit 4; }
echo "derive: $DERIVE_OUT" | tee -a "$RUNLOG" >&2
DERIVED_N=$(wc -l < "$LISTS/derived.txt" | tr -d ' ')
if [ "$DERIVED_N" != "211" ]; then
  echo "POPULATION MISMATCH: f.u yields $DERIVED_N entries, the area's population is 211 — ABORTING." >&2
  echo "population mismatch: derived=$DERIVED_N expected=211" >> "$RUNLOG"
  exit 4
fi
echo "population OK: f.u yields 211 emitted names" | tee -a "$RUNLOG" >&2

# Offline diff against the committed list — the id->name defect, MEASURED.
python3 - "$LISTS/derived.txt" \
  "$LOGDIR/../../findings-log/2026-10-13-area-k-patient-chunks/chunks-swept.txt" \
  > "$LISTS/list-diff.txt" <<'PY'
import sys
d = [l.strip() for l in open(sys.argv[1]) if l.strip()]
c = [l.strip() for l in open(sys.argv[2]) if l.strip()]
ds, cs = set(d), set(c)
print(f"derived from f.u (today's runtime bytes) : {len(d)}")
print(f"committed chunks-swept.txt               : {len(c)}")
print(f"same SET                                 : {'YES' if ds == cs else 'NO'}")
print(f"in f.u but not committed ({len(ds-cs)}):")
for x in sorted(ds - cs): print(f"  + {x}")
print(f"in committed but not in f.u ({len(cs-ds)}):")
for x in sorted(cs - ds): print(f"  - {x}")
PY
cat "$LISTS/list-diff.txt" >> "$RUNLOG"

# ---------------------------------------------------------------- control 3
echo "== control 3: the eager bundle, matcher-positive ==" >&2
req "/main.6595daf83bd6d4b1.js" \
    "CONTROL-eager-bundle-proves-Instinct-is-seen-and-7896-is-not-so-both-answers-are-live" \
    "au-control3-main" || exit 9
C3_SHA=$(sha256sum "$TMPBODIES/au-control3-main.b" | cut -d' ' -f1)
C3_BYTES=$(stat -c%s "$TMPBODIES/au-control3-main.b")
if [ "$C3_SHA" != "0fb4fbd483b5f5d21320ffc595e1befad999eac170d1e7d484fd1c9b09c8ebaa" ] \
   || [ "$C3_BYTES" != "3417255" ]; then
  echo "CONTROL 3 FAILED: expected 3417255 B / 0fb4fbd4…, got $C3_BYTES B / $C3_SHA — ABORTING." >&2
  echo "control 3 FAILED bytes=$C3_BYTES sha=$C3_SHA" >> "$RUNLOG"
  exit 3
fi
python3 "$HERE/census.py" "$TMPBODIES/au-control3-main.b" "/main.6595daf83bd6d4b1.js" \
  > "$LOGDIR/census-eager.json"
C3_INST=$(python3 -c 'import json;print(json.load(open("'"$LOGDIR"'/census-eager.json"))["counts"]["Instinct"]["cs"])')
C3_7896=$(python3 -c 'import json;print(json.load(open("'"$LOGDIR"'/census-eager.json"))["counts"]["7896[0-9]"]["cs"])')
C3_BARE=$(python3 -c 'import json;print(json.load(open("'"$LOGDIR"'/census-eager.json"))["counts"]["7896"]["cs"])')
if [ "$C3_INST" = "0" ] || [ "$C3_7896" != "0" ]; then
  echo "CONTROL 3 FAILED the matcher test: Instinct=$C3_INST (must be non-zero), 7896[0-9]=$C3_7896 (must be 0) — ABORTING." >&2
  echo "control 3 matcher FAILED instinct=$C3_INST 7896x=$C3_7896" >> "$RUNLOG"
  exit 3
fi
echo "control 3 PASS: 3417255 B / 0fb4fbd4…; Instinct=$C3_INST (non-zero), 7896[0-9]=$C3_7896 (zero), bare 7896=$C3_BARE (SVG coordinates — why the anchored form is the token)" \
  | tee -a "$RUNLOG" >&2

# ---------------------------------------------------------------- the 211 cells
n=0
while IFS= read -r chunk || [ -n "$chunk" ]; do
  [ -n "$chunk" ] || continue
  n=$((n+1))
  tag="au-$(printf '%s' "$chunk" | sed 's/\./-/g')"
  req "/$chunk" "SWEEP-lazy-chunk-on-its-emitted-name" "$tag" || exit 9
done < "$LISTS/derived.txt"
echo "swept $n cells from the f.u-derived list" >> "$RUNLOG"

echo "run end: $(date -u +%FT%T.%3NZ) rows=$(wc -l < "$LEDGER") cap=${CAP}" >> "$RUNLOG"
echo "TMPBODIES=$TMPBODIES" >&2
