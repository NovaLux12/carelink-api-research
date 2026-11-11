#!/usr/bin/env bash
# Area AX — is the trailing-slash sensitivity GENERAL, or specific to `/hcp`?
# Claim: NovaLux12/carelink-api-research#211. Host: carelink.medtronic.com ONLY.
# Cap 10, >= 2.5 s between requests to this host, slept INSIDE the per-host flock.
#
# THE SINGLE SOURCE OF THE CAP. One assignment, here; `cap_guard` reads it, and
# FINDINGS.md's "N of a 10 cap" line must equal `wc -l results.jsonl`.
#
#   CAP=10  ==  2 controls
#             + 2 cells  pair A  (/app        vs /app/)
#             + 2 cells  pair B  (/hcp/configuration vs /hcp/configuration/)
#             + 2 cells  apex    (/            vs //)
#             + 1 anchor (/hcp, re-measuring area AN in-run)
#             + 1 unspent
#                                              --
#                                              10
#
# THE QUESTION. Area AN measured, on all four clinic hosts, that `/hcp` (bare)
# answers 200 + the deployment's own entry document (5518 B) while `/hcp/`
# (slashed) answers a real 404 (0 B, no Content-Type) — and no DirectorySlash 301
# appears anywhere. Area AK's 200-at-`/app/` was measured WITH the trailing slash.
# Whether bare `/app` is the same handler, a different one, or an absence is
# recorded NOWHERE. If slashed-ness is a general property of this deployment's
# prefix selection, then EVERY recorded `/prefix/` verdict in this repository has
# an unmeasured counterpart at `/prefix`, and a probing client that omits the slash
# gets a 200 that says nothing about whether the thing exists.
#
# ---------------------------------------------------------------------------
# PRE-REGISTERED OUTCOME TABLE — written BEFORE the first cell is sent, so the
# interpretation cannot be fitted to the result afterwards.
# ---------------------------------------------------------------------------
#
# PAIR A — `/app` (bare) versus `/app/` (slashed)
#   Reference for `/app/`: area AK row 5, `.com`, 200 / 5518 B / 0f2c5f62…
#   A1  both 200, SAME digest            -> ONE handler, slash-INSENSITIVE.
#                                           The sensitivity is /hcp-specific.
#   A2  `/app/` 200 + `/app` 404        -> the `/hcp` pattern GENERALISES:
#                                           the slashed form is the handler's,
#                                           the bare form is outside it. Every
#                                           recorded /prefix/ verdict needs its
#                                           bare counterpart.
#   A3  `/app` 200, DIFFERENT digest     -> a SECOND fallback surface, not the
#                                           same handler; neither A1 nor A2.
#   A4  `/app/` 301/308                  -> Apache DirectorySlash is live here,
#                                           which AN did not see at /hcp.
#   A5  `/app` 200 fallback + `/app/` 404 -> AN's shape reproduced at a second
#                                           prefix: GENERAL, and the strongest
#                                           form of A2.
#   A6  any 000 / 5xx / timeout          -> a FAILURE, never an absence. Retry
#                                           or record unmeasured.
#
# ⚠ RECORDED CAP REVISION (declared BEFORE the 10th request was sent; one only).
#   The itemisation above left 1 unspent. It is now spent on ONE cell:
#     GET /hcp/configuration/zz-ax-absent-8147  (expect 405 + Allow: POST, OPTIONS)
#   WHY, and it is a defect of this design, not a new question: the PAIR-B
#   reference below was mis-set. AG and AL measured `/hcp/configuration/<CHILD>`
#   (`/hcp/configuration/zz-ag-absent-8713`, `/hcp/configuration/zz-ak-absent-4713`),
#   never the PREFIX ROOT `/hcp/configuration/` — so the slashed half of pair B had
#   no recorded reference at all and the 405 quoted below was inherited from a
#   different path shape. This cell buys the genuine AG/AL reference in-run, so a
#   reader can tell a 404 at the prefix root apart from the subtree being gone.
#   It is sent LAST, after every pre-registered cell, so it cannot influence the
#   pre-registered reading. If it 405s, the subtree's 405 handler is live one
#   segment deeper in the same run and the two 404s are statements about
#   prefix-root paths. If it 404s, AG/AL no longer reproduce on this host and that
#   drift is reported as drift.
#
# PAIR B — `/hcp/configuration` (bare) versus `/hcp/configuration/` (slashed)
#   Reference for the slashed form: area AG/AL, 405 + `Allow: POST, OPTIONS`, 0 B
#   — ⚠ ON `/hcp/configuration/<CHILD>`, NOT on the prefix root (see the recorded
#   cap revision above). The prefix root was unmeasured before this pass, which is
#   why B1/B2 are read as "what the two forms do", not as a comparison to a 405.
#   B1  bare 200 fallback + slashed 405  -> the bare form ESCAPES the slashed
#                                           handler, exactly as `/hcp` does.
#                                           GENERAL at a second, deeper prefix.
#   B2  bare 405 + slashed 405, same Allow -> slash-INSENSITIVE at this prefix:
#                                           the 405 handler owns both forms.
#                                           Sensitivity is /hcp-specific.
#   B3  bare 200 fallback + slashed 200 fallback, same digest -> neither form is
#                                           in a handler; /hcp/configuration/ is
#                                           NOT the 405 surface any more, which
#                                           would contradict AG/AL and must be
#                                           reported as a drift, not smoothed.
#   B4  bare 404 (0 B, no CT) + slashed 405 -> the bare form is excluded from a
#                                           DIFFERENT surface than the fallback;
#                                           a third behaviour, neither AN's nor
#                                           AK's.
#   B5  any 000 / 5xx / timeout          -> FAILURE, never an absence.
#   B6  ⚠ ADDED AFTER THE CELL, and labelled as such: BOTH forms 404 (0 B, no CT)
#       -> the pre-registered table above did NOT enumerate this, because its
#       slashed reference was a 405 that had been measured one segment deeper.
#       What it means: neither form of this prefix name reaches the fallback, and
#       neither reaches the 405 handler — so bare-ness is not what selects here.
#       It is the ONE outcome that separates slash-INSENSITIVE from AN's pattern
#       (both forms get the SAME non-fallback answer) while also killing B1's
#       escape reading. Named as a post-hoc label, not a pre-registration.
#
# APEX PAIR — `/` versus `//`
#   Reference for `/`: area AN row 13 / AK, 200 / 5518 B / 0f2c5f62… (that anchor
#   was bought on carelinkhp; this pass buys it on .com — see the note below).
#   X1  `//` 200, SAME digest as `/`     -> the client-side/`merge_slashes`
#                                           normalisation AN observed under
#                                           `/hcp/` also holds at the apex; the
#                                           apex is slash-count-INSENSITIVE.
#   X2  `//` 404 (0 B, no CT)            -> a doubled leading slash is OUTSIDE
#                                           the apex fallback: the fallback keys
#                                           on a literal string too, which is a
#                                           NEW boundary no area has recorded.
#   X3  `//` 400 / 414                   -> Apache rejects the request line
#                                           before the app sees it; says nothing
#                                           about prefix selection, and must not
#                                           be reported as one.
#   X4  `//` 200, DIFFERENT digest       -> a distinct handler at `//`; neither
#                                           X1 nor X2.
#   X5  any 000 / 5xx / timeout          -> FAILURE, never an absence.
#   NOTE `//` REQUIRES `--path-as-is`; without it curl collapses the doubled
#   leading slash client-side and the cell measures `/`, not `//`. Area AN §4
#   cell 3 used the same flag for `//hcp/…`.
#
# ANCHOR — `/hcp` (bare) on this host
#   Purpose: re-measure area AN's own cell IN-RUN, so the bare-prefix behaviour
#   this pass generalises (or fails to) is compared against a fresh observation
#   on the SAME host, in the SAME run, rather than against a cross-pass digest.
#   H1  `/hcp` -> 200 / 5518 B / 0f2c5f62… -> AN reproduces in-run; the pair
#       comparisons above rest on a live anchor.
#   H2  anything else                    -> AN's cell no longer reproduces on
#       this host: report the drift and do NOT read the pairs as a generalisation
#       of AN.
#
# A NEGATIVE IS A FIRST-CLASS ANSWER. If A1 holds — bare `/app` byte-identical to
# `/app/` — then the sensitivity is `/hcp`-specific, and that is the finding. This
# pass does not force a generalisation.
#
# LABELLING. Every claim in FINDINGS.md is labelled OBSERVED / PUBLISHED /
# INFERRED in the same sentence. The MECHANISM behind a bare-prefix 200 is NOT
# observable by GET (area AN §6); if one is offered it is INFERRED and says so.
#
# ---------------------------------------------------------------------------
# Controls FIRST. A status is not an oracle until it is shown to discriminate.
#   C1  GET /hcp/configuration/public/pow.crm.settings  + X-System-ID: ProWeb
#         MUST be 200, 97 B, sha256 370e3bba0d28…
#   C2  GET /hcp/zz-ax-absent-8147
#         MUST be 404, 0 B, no Content-Type
#   If EITHER disagrees the run STOPS and no pair cell is sent.
#
# GET only. No POST, no OPTIONS, no token, no cookie, no auth, no wordlist.
# The one header sent is `X-System-ID: ProWeb` on C1, because without it the same
# key answers 412 (area AB). The fabricated name `zz-ax-absent-8147` is checked
# for 0 `git grep` hits in FINDINGS.md.
#
# Usage: probe.sh all
set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/../../../../.." && pwd)"
RUNLOG="$HERE/run.log"
LEDGER="$HERE/results.jsonl"
SCRATCH="$REPO/.loop/ax-scratch"
mkdir -p "$SCRATCH"

UA="carelink-bridge-research/1.0"
DELAY=2.5
CAP=10
HOST=carelink.medtronic.com
PROWEB="X-System-ID: ProWeb"
ABS=zz-ax-absent-8147

P_C1="/hcp/configuration/public/pow.crm.settings"
P_C2="/hcp/$ABS"

[ -f "$LEDGER" ] || : > "$LEDGER"
SEQ=$(awk 'NF' "$LEDGER" 2>/dev/null | wc -l | tr -d ' '); SEQ=${SEQ:-0}
[ -f "$RUNLOG" ] || : > "$RUNLOG"

log() { printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)" "$*" >> "$RUNLOG"; }
ledger_len() { awk 'NF' "$LEDGER" 2>/dev/null | wc -l | tr -d ' '; }

cap_guard() {
  local n; n=$(ledger_len)
  if [ "$n" -ge "$CAP" ]; then log "CAP STOP at $n of $CAP"; echo "CAP STOP: $n of $CAP" >&2; return 1; fi
  return 0
}

# req <path> <role> <tag> [header] [path_as_is]
req() {
  local path="$1" role="$2" tag="$3" hdr="${4:-}" pas="${5:-}"
  cap_guard || return 1
  SEQ=$((SEQ+1))
  local out="$SCRATCH/$tag" tq ts td code exitc
  tq=$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)
  local -a cargs=(-s --compressed --max-time 120 -A "$UA" -D "$out.h" -o "$out.b" -w '%{http_code}')
  [ -n "$hdr" ] && cargs+=(-H "$hdr")
  [ "$pas" = asis ] && cargs+=(--path-as-is)
  touch "$REPO/.loop/host-carelink_medtronic_com.lock" 2>/dev/null || true
  exec 9>"$REPO/.loop/host-carelink_medtronic_com.lock"
  flock 9
  sleep "$DELAY"                       # the sleep is INSIDE the per-host lock
  ts=$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)
  code=$(curl "${cargs[@]}" "https://$HOST$path" 2>>"$RUNLOG")
  exitc=$?
  flock -u 9
  exec 9>&-
  td=$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)
  python3 - "$LEDGER" "$out.h" "$out.b" "$SEQ" "$HOST" "$tag" "$path" "$role" "${hdr:-(none)}" "${pas:-no}" "$code" "$exitc" "$tq" "$ts" "$td" <<'PY'
import json, sys, os, hashlib
(L, hp, bp, seq, host, tag, path, role, sent, pas, code, exitc,
 tq, ts, td) = sys.argv[1:16]
KEEP = ('content-type','content-length','content-encoding','allow','server','vary',
        'cache-control','etag','last-modified',
        'access-control-allow-headers','access-control-allow-methods')
hdrs = {}
if os.path.exists(hp):
    for line in open(hp, 'rb').read().decode('latin-1').splitlines():
        if ':' in line:
            k, v = line.split(':', 1)
            if k.strip().lower() in KEEP:
                hdrs[k.strip().lower()] = v.strip()
n = os.path.getsize(bp) if os.path.exists(bp) else 0
d = hashlib.sha256(open(bp,'rb').read()).hexdigest() if n else ''
row = {"seq": int(seq), "host": host, "tag": tag, "method": "GET", "path": path,
       "role": role, "sent_headers": sent, "path_as_is": pas == 'asis',
       "http_status": code, "curl_exit": int(exitc),
       "body_bytes": n, "body_sha256": d,
       "content_type": hdrs.get('content-type','(none)'),
       "allow": hdrs.get('allow','(none)'),
       "content_encoding": hdrs.get('content-encoding','(none)'),
       "server": hdrs.get('server','(none)'),
       "headers": hdrs, "t_queued": tq, "t_sent": ts, "t_done": td}
open(L, 'a').write(json.dumps(row) + "\n")
print(f"seq={seq} GET {host}{path} -> {code} ctype={hdrs.get('content-type','-')} "
      f"bytes={n} allow={hdrs.get('allow','-')} sha256={d[:16] or '-'}")
PY
  log "seq=$SEQ GET https://$HOST$path status=$code exit=$exitc tag=$tag role=[$role] path_as_is=${pas:-no}"
}

# Read a field from the ledger row with a given seq.
field() { python3 -c "import json,sys
for l in open('$LEDGER'):
    r=json.loads(l)
    if r['seq']==$1: print(r['$2']); break" ; }

run() {
  echo "== controls first =="
  req "$P_C1" "CONTROL-1 positive: known-live key WITH X-System-ID: ProWeb; MUST be 200 / 97 B / 370e3bba0d28… (area AB)" c1-pow-crm "$PROWEB" || return 1
  req "$P_C2" "CONTROL-2 certainly-absent: MUST be 404 / 0 B / no Content-Type (area AK row 3 envelope)" c2-absent || return 1

  local c1s c1b c1d c2s c2b c2t
  c1s=$(field 1 http_status); c1b=$(field 1 body_bytes); c1d=$(field 1 body_sha256)
  c2s=$(field 2 http_status); c2b=$(field 2 body_bytes); c2t=$(field 2 content_type)
  echo "C1: $c1s $c1b B ${c1d:0:16}"; echo "C2: $c2s $c2b B ct=$c2t"
  if [ "$c1s" != "200" ] || [ "$c1b" != "97" ] || [ "${c1d:0:12}" != "370e3bba0d28" ]; then
    log "STOP: CONTROL-1 disagreed — no pair cell sent"
    echo "STOP: CONTROL-1 disagreed (want 200/97 B/370e3bba0d28…)" >&2; return 1
  fi
  if [ "$c2s" != "404" ] || [ "$c2b" != "0" ] || [ "$c2t" != "(none)" ]; then
    log "STOP: CONTROL-2 disagreed — no pair cell sent"
    echo "STOP: CONTROL-2 disagreed (want 404/0 B/no Content-Type)" >&2; return 1
  fi
  echo "== controls PASS — pairs may be sent =="

  req "/"                    "APEX slashed: recorded 0f2c5f62… / 5518 B / 200 (AN row 13 was bought on carelinkhp; this is .com)" a1-apex-slash || return 1
  req "//"                   "APEX bare-doubled: what '//' does is UNRECORDED; --path-as-is so it reaches the wire as '//'. X1/X2/X3/X4 in the header table" a2-apex-double "" asis || return 1
  req "/app"                 "PAIR-A bare: is bare /app the same handler as /app/, a different one, or an absence? A1/A2/A3/A5" a3-app-bare || return 1
  req "/app/"                "PAIR-A slashed: AK row 5 reference — 200 / 5518 B / 0f2c5f62… on .com" a4-app-slash || return 1
  req "/hcp/configuration"   "PAIR-B bare: does the bare form escape the slashed handler, as /hcp does? B1/B2/B4" b1-hcpcfg-bare || return 1
  req "/hcp/configuration/"  "PAIR-B slashed: AG/AL reference — 405 + Allow: POST, OPTIONS, 0 B" b2-hcpcfg-slash || return 1
  req "/hcp"                 "ANCHOR: area AN's own bare-prefix cell re-measured in-run — 200 / 5518 B / 0f2c5f62… expected (H1/H2)" h1-hcp-bare || return 1
  # The recorded cap revision's one cell — sent LAST, after every pre-registered
  # cell, so it cannot influence the pre-registered reading.
  req "/hcp/configuration/$ABS" "REFERENCE (cap revision): the genuine AG/AL 405 cell — one segment under the subtree, NOT the prefix root pair B compares. Expect 405 / 0 B / Allow: POST, OPTIONS" r1-hcpcfg-child || return 1
}

case "${1:-all}" in
  all) run ;;
  *) echo "usage: probe.sh all" >&2; exit 64 ;;
esac
echo "LEDGER_ROWS=$(ledger_len) CAP=$CAP"
