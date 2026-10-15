#!/usr/bin/env bash
# probe.sh — area F successor 1: the portal lazy-chunk corpus.
# Pool lane A, 2026-10-15, claim issue #131.
#
# WHAT THIS SENT, EXACTLY. Every row of `cells.txt` is one GET. Nothing is
# generated, retried or re-ordered at request time; `cells.txt` IS the probe.
#
#   GET only. No POST, no OPTIONS, no token exchange, no authentication, no
#   Authorization / Cookie / X-Api-Key / Origin header, no -X override, no -d.
#   CAP=260 requests total for the pass; the harness refuses to exceed it and
#   refuses to start a new cell without a free slot.
#
# HOSTS — AND WHY THEY ARE NOT THE ONES THE CLAIM NAMED.
# The claim (#131) and the brief both name `carelinkhp.minimed.eu` and
# `carelinkhp.minimed.com`. The second of those does not exist: area A closed
# with "There is no `.com` `carelinkhp` variant: all five `carelinkhp*.minimed.
# {eu,com}` names outside the baseline are NXDOMAIN"
# [source: findings-log/2026-10-12-area-a-clinic-portal-region/FINDINGS.md:379-380
#  (and its summary at :10); findings-log/probe-2026-10-08/PROBE-FINDINGS.md:29
#  and :264. The Closed-table row restating it is FOUND BY GREP, not by line
#  number — `grep -nF '| A — is `carelinkhp` really the clinician portal for
#  every region?' docs/11-suggested-research-areas.md`, 1 hit — because this
#  pass inserts 200+ lines above it and a line cite into a file you are editing
#  rots by construction; that is FINDINGS.md §13 item 3.]
# The repository wins over the brief (BRIEF.md:10-15), and the support build's
# own host is the one the pinned suite already reads:
#   clinic  pow -> carelinkhp.minimed.eu          (05-public-config.check.sh:329)
#   support cua -> carelink-support.medtronic.eu   (05-public-config.check.sh:330)
# Nothing outside those two hosts was contacted.
#
# THE ORACLE IS content-type, NEVER status. Both hosts answer 200 text/html at
# exactly 5518 B for every path that does not exist (docs/09 §3, trap row), so
# a status-only read would score every fabricated name as a live asset. Every
# row therefore records content-type, and `sweep.sh` refuses to classify any
# cell whose content-type is not application/javascript.
#
# CONTROLS ARE SENT BEFORE THE DATA CELLS THEY JUDGE. Phase 1 (cells.txt
# lines 1-10) is: per host, a certainly-absent control, the entry document, the
# build's own runtime (the chunk-map source), a positive control read out of
# that freshly derived f.u, and the f.u name-form-vs-id-form defect control.
# Only then does any phase-2 sweep cell go out.
#
# SPACING. `sleep 2.5` is held INSIDE the per-host flock, and t_sent is stamped
# inside the lock immediately before curl execs, so results.jsonl's t_sent
# column is a send time and not a queue time. Sleeping outside the lock would
# let four pool workers queue and then fire inside one window, which is worse
# than no serialisation at all.
#
# THE TOKEN SWEEP IS DONE HERE, NOT LATER, because the bodies are transient:
# AGENTS.md §7 forbids committing raw captures, and these bodies total several
# MB. The per-token counts are recorded in the ledger row while the body is on
# disk, so the negative is re-derivable from the committed ledger alone. The
# token list is area F's, verbatim, unmodified:
# findings-log/2026-10-14-pool-f-timeline-caller/grep.sh TOKENS.
#
# LEDGER. One row per request in results.jsonl, at millisecond resolution, with
# t_queued / t_sent / t_done and the kernel's own body-write mtime (the second,
# clock-independent spacing series docs/09 §4 asks for). Append-only and
# resumable: a harness that truncates its own ledger on start-up is how a pass
# under-reports its own budget.

set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1

LOGDIR="findings-log/2026-10-15-area-f1-portal-chunks"
SELF_DIR="$(cd "$(dirname "$0")" && pwd -P)"
WORKTREE="$(cd "$SELF_DIR/../.." && pwd -P)"
case "$WORKTREE" in
  */.loop/worktrees/*) LOCKDIR="${WORKTREE%%/.loop/worktrees/*}/.loop" ;;
  *)                  LOCKDIR="$WORKTREE/.loop" ;;
esac
[ -d "$LOCKDIR" ] || { printf 'lock dir missing — refusing to send\n' >&2; exit 4; }

# Bodies are transient and land OUTSIDE the repository (AGENTS.md §7: no raw
# captures; and these bodies total several MB, breaching the per-file log limit).
# No path is baked in here, for the same reason — the caller chooses it.
SCRATCH="${SCRATCH:-$(mktemp -d)}"
mkdir -p "$SCRATCH" "$LOGDIR/headers"

CELLS="${1:-$LOGDIR/cells.txt}"
[ -f "$CELLS" ] || { printf 'no cell list at %s\n' "$CELLS" >&2; exit 2; }

LEDGER="$LOGDIR/results.jsonl"
RUNLOG="$LOGDIR/run.log"
CAP=260
LOCKD=2.5
UA="carelink-bridge-research/1.0"

ts() { date -u +%FT%T.%3NZ; }

# Area F's token list, verbatim, from
# findings-log/2026-10-14-pool-f-timeline-caller/grep.sh (TOKENS array).
# Not edited, not extended: this pass asks area F's question of a corpus area F
# never read, and changing the question would make the two passes incomparable.
TOKENS=(
  'patient-timeline'
  'dialog-lite'
  'app-patient-timeline'
  'patientTimeline'
  'personal.patient.timeline.config'
  'personal.patient.timeline.host'
  'execute-api'
  '0ptoikank6'
  'r5djbmetbb'
  'd4mwt26mmi'
  '7r9xxd72kk'
  'oflhmnvbe6'
  'prodous'
  'm2m'
  'baseUrl'
  'hcp/configuration/public/'
  'hcp/patients'
  '/patient/'
  'clcloud'
  'carelink.minimed'
  'timeline'
  'Timeline'
  'TIMELINE'
  'personal.'
)

# Resume: the next seq is one past the highest already in the ledger.
SEQ=0
[ -f "$LEDGER" ] && SEQ=$(python3 - "$LEDGER" <<'PY'
import json,sys
m=0
for line in open(sys.argv[1]):
    line=line.strip()
    if not line: continue
    try: m=max(m,int(json.loads(line)["seq"]))
    except Exception: pass
print(m)
PY
)
START=$SEQ
printf 'resuming at seq %s (ledger rows so far: %s)\n' "$((SEQ+1))" "$(wc -l < "$LEDGER" 2>/dev/null || echo 0)" >&2

while IFS='|' read -r role tag url build chunkid hash || [ -n "${role:-}" ]; do
  [ -z "${role:-}" ] && continue
  case "$role" in \#*) continue ;; esac
  SEQ=$((SEQ + 1))
  if [ "$SEQ" -gt "$CAP" ]; then
    printf 'CAP REACHED (%s) at %s — refusing to send %s\n' "$CAP" "$SEQ" "$tag" >&2
    SEQ=$((SEQ - 1))
    break
  fi
  host="${url#*://}"; host="${host%%/*}"
  sn="$(printf '%03d' "$SEQ")"
  hdr="$LOGDIR/headers/$sn-$tag.h"
  body="$SCRATCH/$sn-$tag.body"
  codef="$SCRATCH/$sn-$tag.code"
  tsf="$SCRATCH/$sn-$tag.ts"
  tq="$(ts)"
  # sleep INSIDE the lock; t_sent stamped inside the lock immediately pre-curl.
  flock "$LOCKDIR/host-$host.lock" -c "
    sleep $LOCKD
    date -u +%FT%T.%3NZ > '$tsf'
    curl -sS --compressed --max-time 40 -A '$UA' -o '$body' -D '$hdr' -w '%{http_code}' '$url' > '$codef' 2>'$SCRATCH/$sn-$tag.err'
  "
  t_done="$(ts)"
  t_sent="$(cat "$tsf" 2>/dev/null)"
  code="$(tr -dc '0-9' < "$codef" 2>/dev/null)"
  bytes=0; [ -f "$body" ] && bytes="$(stat -c%s "$body")"
  bsha="-";  [ -f "$body" ] && bsha="$(sha256sum "$body" | cut -c1-64)"
  bmtime="-"; [ -f "$body" ] && bmtime="$(date -u -d "@$(stat -c%Y "$body")" +%FT%T.%3NZ)"
  hval() { grep -i "^$1:" "$hdr" 2>/dev/null | head -1 | cut -d' ' -f2- | tr -d '\r'; }
  ct="$(hval content-type)"; ce="$(hval content-encoding)"
  etag="$(hval etag)"; server="$(hval server)"; cc="$(hval cache-control)"
  head_txt=""
  [ -f "$body" ] && head_txt="$(head -c 80 "$body" | tr -d '\r\n' | tr -c '[:print:]' '.' | cut -c1-80)"

  # ---- the token sweep, run while the transient body is still on disk ----
  tokjson="{}"
  if [ -f "$body" ]; then
    tokjson="$(TOKBODY="$body" TOKSPEC="$(printf '%s\n' "${TOKENS[@]}")" python3 <<'PY'
import os, json
body = os.environ["TOKBODY"]
spec = os.environ["TOKSPEC"].split("\n")
out = {}
data = open(body, "rb").read()
for t in spec:
    if not t:
        continue
    out[t] = data.count(t.encode())
print(json.dumps(out, sort_keys=True))
PY
)"
  fi

  # NOTE ON run.log: bash printf REUSES the format string when the argument
  # list outnumbers its conversions, so an under-specified format silently
  # emits extra lines rather than failing. The format below was written with
  # one conversion too few for its argument list and did exactly that. The
  # defect was found by reading run.log, it touched this file only, and the
  # file is now generated from the ledger by `runlog.py` instead — the ledger
  # is one python3 row per request and was never affected.
  printf '%s\t%s\t%s\t%s\t%s\tGET\t%s\t%s\t%s\t%s\n' \
    "$tq" "$t_sent" "$t_done" "$bmtime" "$host" "$url" "$code" "$ct" "$bytes" >> "$RUNLOG"

  SEQJ="$SEQ" ROLEJ="$role" TAGJ="$tag" BUILDJ="$build" CHUNKIDJ="$chunkid" HASHJ="$hash"
  HOSTJ="$host" URLJ="$url" CODEJ="$code" TQJ="$tq" TSJ="$t_sent" TDJ="$t_done"
  MTJ="$bmtime" BYTESJ="$bytes" BSHAJ="$bsha" HEADJ="$head_txt" HDRI="$hdr"
  CTJ="$ct" CEJ="$ce" ETAGJ="$etag" SERVERJ="$server" CCJ="$cc"
  TOKJ="$tokjson" ERRJ="$(tr -d '\r\n' < "$SCRATCH/$sn-$tag.err" 2>/dev/null)"
  python3 - "$SEQJ" "$ROLEJ" "$TAGJ" "$BUILDJ" "$CHUNKIDJ" "$HASHJ" "$HOSTJ" "$URLJ" \
      "$CODEJ" "$TQJ" "$TSJ" "$TDJ" "$MTJ" "$BYTESJ" "$BSHAJ" "$HEADJ" "$HDRI" \
      "$CTJ" "$CEJ" "$ETAGJ" "$SERVERJ" "$CCJ" "$TOKJ" "$ERRJ" <<'PY' >> "$LEDGER"
import json, sys
f = sys.argv[1:]
n = lambda s: None if s in ("", "None") else s
path = f[7].split("/", 3)[3] if f[7].count("/") > 2 else "/"
print(json.dumps({
    "seq": int(f[0]), "role": f[1], "tag": f[2],
    "build": n(f[3]), "chunk_id": n(f[4]), "chunk_hash": n(f[5]),
    "host": f[6], "url": f[7], "path": path, "method": "GET",
    "status": n(f[8]),
    "content_type": n(f[17]), "content_encoding": n(f[18]), "etag": n(f[19]),
    "server": n(f[20]), "cache_control": n(f[21]),
    "body_bytes": int(f[13]), "body_sha256": f[14], "body_head": f[15],
    "headers_file": f[16],
    "tokens": json.loads(f[22]), "curl_stderr": n(f[23]),
    "t_queued": f[9], "t_sent": f[10], "t_done": f[11],
    "body_mtime": n(f[12]),
}, sort_keys=False))
PY
  printf 'sent seq %s %s %s %s %s\n' "$SEQ" "$tag" "$host" "$code" "$ct" >&2
done < "$CELLS"

printf 'phase complete: %s requests in this invocation, %s total, cap %s\n' \
  "$((SEQ-START))" "$SEQ" "$CAP" >&2