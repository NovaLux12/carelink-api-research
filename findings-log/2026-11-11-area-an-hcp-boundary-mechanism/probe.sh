#!/usr/bin/env bash
# Area AN — what SELECTS the /hcp/ boundary on the four clinic hosts: a rewrite mounted
# above /hcp/ that never sees a /hcp/ request, or a handler at /hcp/ that answers first?
# Claim: NovaLux12/carelink-api-research#196. Cap 20, >=2.5 s per host, INSIDE the flock.
#
# THE SINGLE SOURCE OF THE CAP. One assignment, here; `cap_guard` reads it, and
# FINDINGS.md's "19 of a 20 cap" line must equal `wc -l results.jsonl` (19 harnessed
# rows) with the 20th request accounted for separately as a pre-itemisation
# reachability GET (see FINDINGS.md §1 — it is recorded, not hidden).
#
#   CAP=20  ==  1 pre-itemisation reachability GET (already sent, FINDINGS.md §1)
#            +  4 hosts x 4 cells                      = 16
#            +  3 extra cells on carelink.medtronic.com =  3
#                                                       --
#                                                       20
#
# ============================================================================
# PRE-REGISTERED OUTCOME TABLE. Written BEFORE the first cell was sent. Every
# cell below was chosen because its outcomes were expected to DIFFER between the
# candidate mechanisms, or because it was expected to kill a third reading. A cell
# whose outcomes do NOT differ between the two mechanisms is marked NOT-SEPARATING
# and is included only to close a rival reading — the report says so per cell.
# ============================================================================
#
# THE TWO MECHANISMS AS STATED IN dict/docs/11 AN:
#   (a) a rewrite mounted ABOVE /hcp/ that never sees a /hcp/ request — Apache's
#       location resolution selects a deeper location/mount for /hcp/, so the
#       rewrite's own match is never evaluated on a /hcp/… path.
#   (b) a handler AT /hcp/ that answers before the rewrite — the /hcp/ handler
#       runs at an earlier phase, so the rewrite is never reached.
# Both entail a /hcp/ handler existing. They differ only in WHY the rewrite is
# excluded: location selection (a) versus phase ordering (b).
#
# CELL 1  /hcp            (NO trailing slash)          — per host, 4 requests
#   200 + entry-document digest  -> the selector is a LITERAL STRING PREFIX on
#       "/hcp/" including the trailing slash, and the bare prefix is NOT owned by
#       the /hcp/ handler. Kills "the /hcp/ subtree owns /hcp as well".
#   301/308 + Location: /hcp/     -> DirectorySlash: a real directory or a mount
#       point exists at /hcp/ — a filesystem/mount mapping, not a bare rewrite
#       condition. FAVOURS a mapped subtree, i.e. (b)-compatible, and is the
#       strongest single signal of a mount available to a GET.
#   404, 0 B, no Content-Type     -> the handler answers for the bare prefix too:
#       the mapping is subtree-wide and the handler is reached before any
#       directory-normalisation decision.
#   405/412/401/anything else     -> recorded; each means the handler answered the
#       bare prefix rather than Apache.
#   NOT-SEPARATING between (a) and (b) under any of the above: both predict the
#   same bytes. Separating power: prefix-string vs subtree, NOT rewrite vs handler.
#
# CELL 2  /hcp/           (prefix root, nothing after) — per host, 4 requests
#   404 0 B no CT   -> the app answers the prefix root as "no route": the /hcp/
#                       handler sees the bare prefix.
#   301/302 + Location -> directory semantics again; a redirect target that is the
#                       SAME path is mod_dir noise, a different path is a mount.
#   200 + entry digest -> the selector requires at least one segment AFTER /hcp/,
#                       i.e. the exclusion is a prefix match on a path with a
#                       child, not on the prefix itself.
#   NOT-SEPARATING between (a) and (b).
#
# CELL 3  //hcp/<absent>  (double leading slash)        — per host, 4 requests
#   same verdict as /hcp/<absent> (404) -> the selector operates on the NORMALISED
#       path (Apache merge_slashes on by default), so it sits after normalisation.
#       Says nothing about ordering.
#   200 + entry digest -> the selector did NOT match the doubled form: either it
#       compares the raw un-normalised path, or what produces the 404 is not
#       Apache's location matcher at all. The second reading is the interesting
#       one and it cuts against both (a) and (b) as stated.
#   NOT-SEPARATING if it matches cell 5's verdict; SEPARATING if it does not.
#
# CELL 4  /hcp/<absent>   (the recorded cell, RE-MEASURED on .com only, 1 request)
#   Purpose: an IN-RUN control for the 404's header set. AK recorded 404 / 0 B /
#   no Content-Type / server: Apache / cache-control / ACAH. If that reproduces,
#   this pass's header capture is proven against a known row and every header
#   comparison below is in-run rather than cross-pass. If it does not, STOP.
#   NOT-SEPARATING; it is a control.
#
# CELL 5  /hcp/<absent>/  (trailing slash on the FABRICATED name, .com, 1 request)
#   301/308 + Location -> directory semantics on a path that cannot exist: a
#       mounts/DirectorySlash artefact rather than an app route. Notable.
#   404 same as cell 4  -> no directory semantics; the handler answered.
#   NOT-SEPARATING between (a) and (b).
#
# CELL 6  /app/hcp/<absent>  (the token NOT at the start, .com, 1 request)
#   200 + entry digest -> the exclusion is ANCHORED at ^/hcp/. Consistent with both.
#   404                -> the selector matches "/hcp/" ANYWHERE in the path — a
#       substring match, which neither (a) nor (b) as stated predicts. Reportable.
#   SEPARATING in the second outcome only, and against both mechanisms.
#
# WHAT THIS PASS CANNOT DO, SAID BEFORE ANY CELL IS SENT: (a) and (b) are statements
# about Apache's request pipeline. Neither changes a byte of any response for a path
# an unauthenticated GET can reach: for any path the /hcp/ handler answers, both give
# that handler's answer; for any path it does not answer, both give the fallback.
# No cell in this file is expected to separate them. The cells separate
# PREFIX-STRING from SUBTREE and ANCHORED from SUBSTRING — two properties the
# mechanisms are usually glossed as differing in, and do not. The honest deliverable
# is therefore expected to be a NON-SEPARABILITY verdict plus the properties measured.
#
# A THIRD MECHANISM THE BINARY EXCLUDES, recorded because the binary framing hides it:
#   (c) the fallback is not a rewrite at all but `FallbackResource` / `ErrorDocument
#       404` bound to the document root, or an SPA served by a static handler whose
#       404 is overridden. (a) and (b) both presume a rewrite; nothing observed
#       requires one.
#
# GET only. No POST, no OPTIONS, no token, no cookie, no auth, no wordlist. The one
# header sent is `X-System-ID: ProWeb` on the three portal live controls, because
# without it the same key answers 412 (area AB, OBSERVED).
#
# Hosts: the four clinic hosts ONLY. carelink.minimed.* and the cumulus hosts belong
# to another lane and are not touched here.
#
# Usage: probe.sh all
set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/../../../../.." && pwd)"
RUNLOG="$HERE/run.log"
LEDGER="$HERE/results.jsonl"
SCRATCH="$REPO/.loop/an-scratch"
mkdir -p "$SCRATCH"

UA="carelink-bridge-research/1.0"
DELAY=2.5
CAP=20
PROWEB="X-System-ID: ProWeb"
TAB=$'\t'

HOSTS="carelink.medtronic.com carelink.medtronic.eu carelink-support.medtronic.com carelinkhp.minimed.eu"
LIVE_PORTAL=/hcp/configuration/public/pow.crm.settings   # AB/AK: 200 (97 B .com/support, 96 B .eu) WITH the header
LIVE_HP=/                                                # area G/AK: 200, 5518 B entry document
ABS=zz-an-absent-1913                                    # fabricated; 0 `git grep` hits at base c27662f

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

# req <host> <path-as-requested> <role> <tag> [header]
# `path` is passed to curl VERBATIM (so //hcp/... keeps its double slash — curl does
# not collapse it, and --path-as-is guarantees the wire form is the recorded form).
req() {
  local host="$1" path="$2" role="$3" tag="$4" hdr="${5:-}"
  cap_guard || return 1
  SEQ=$((SEQ+1))
  local out="$SCRATCH/$tag" tq ts td code exitc
  tq=$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)
  local -a cargs=(-s --compressed --path-as-is --max-time 120 -A "$UA" -D "$out.h" -o "$out.b" -w '%{http_code}')
  [ -n "$hdr" ] && cargs+=(-H "$hdr")
  touch "$REPO/.loop/host-$host.lock" 2>/dev/null || true
  exec 9>"$REPO/.loop/host-$host.lock"
  flock 9
  sleep "$DELAY"                       # the sleep is INSIDE the per-host lock
  ts=$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)
  code=$(curl "${cargs[@]}" "https://$host$path" 2>>"$RUNLOG")
  exitc=$?
  flock -u 9
  exec 9>&-
  td=$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)
  python3 - "$LEDGER" "$out.h" "$out.b" "$SEQ" "$host" "$tag" "$path" "$role" "${hdr:-(none)}" "$code" "$exitc" "$tq" "$ts" "$td" <<'PY'
import json, sys, os, hashlib
(L, hp, bp, seq, host, tag, path, role, sent, code, exitc,
 tq, ts, td) = sys.argv[1:15]
KEEP = ('content-type','content-length','content-encoding','allow','server','vary',
        'cache-control','etag','last-modified','location',
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
       "role": role, "sent_headers": sent, "http_status": code, "curl_exit": int(exitc),
       "body_bytes": n, "body_sha256": d,
       "content_type": hdrs.get('content-type','(none)'),
       "content_encoding": hdrs.get('content-encoding','(none)'),
       "location": hdrs.get('location','(none)'),
       "allow": hdrs.get('allow','(none)'),
       "server": hdrs.get('server','(none)'),
       "headers": hdrs, "t_queued": tq, "t_sent": ts, "t_done": td}
open(L, 'a').write(json.dumps(row) + "\n")
print(f"seq={seq} GET {host}{path} -> {code} ctype={hdrs.get('content-type','-')} "
      f"loc={hdrs.get('location','-')} bytes={n} sha256={d[:16]}")
PY
  log "seq=$SEQ GET https://$host$path status=$code exit=$exitc tag=$tag role=[$role]"
}

sweep() {
  local h
  for h in $HOSTS; do
    # ---- control FIRST, per host: a status is not an oracle until it discriminates
    if [ "$h" = "carelinkhp.minimed.eu" ]; then
      req "$h" "$LIVE_HP" \
        "CONTROL: the baseline entry document. Area G/AK: 200 text/html 5518 B sha256 0f2c5f62… here. A non-200 aborts the pass, not recorded as an absence." \
        "ctl-$h" "" || return 0
    else
      req "$h" "$LIVE_PORTAL" \
        "CONTROL: known-live config key WITH X-System-ID: ProWeb. AB/AK: 200 (97 B .com/support, 96 B .eu). Proves the host answers and the header gate is passed." \
        "ctl-$h" "$PROWEB" || return 0
    fi
    # ---- CELL 1: /hcp, no trailing slash (prefix-string vs subtree)
    req "$h" "/hcp" \
      "CELL 1 /hcp no trailing slash: 200 entry digest => literal '/hcp/' prefix selector, bare prefix not owned; 301 => DirectorySlash/mount (strongest mount signal a GET can get); 404 0 B => handler owns the bare prefix too. NOT-SEPARATING between (a) and (b)." \
      "noslash-$h" "" || return 0
    # ---- CELL 2: /hcp/ exactly
    req "$h" "/hcp/" \
      "CELL 2 /hcp/ prefix root: 404 0 B => app answers the prefix root as no-route; 301/302 => directory semantics; 200 entry digest => the selector needs a segment AFTER /hcp/. NOT-SEPARATING between (a) and (b)." \
      "slash-$h" "" || return 0
    # ---- CELL 3: //hcp/<absent>
    req "$h" "//hcp/$ABS" \
      "CELL 3 //hcp/<absent> doubled leading slash: 404 (same as the recorded /hcp/ cell) => selector runs on the NORMALISED path; 200 entry digest => the selector reads the raw path, or the 404 is not produced by Apache's location matcher. SEPARATING only in the second outcome." \
      "dbl-$h" "" || return 0
  done
  # ---- CELL 4-6, control host only ----------------------------------------
  local h=carelink.medtronic.com
  req "$h" "/hcp/$ABS" \
    "CELL 4 in-run control for the 404 header set: AK recorded 404 / 0 B / NO Content-Type / server: Apache / cache-control / ACAH at this exact path. Reproducing it proves this pass's header capture against a known row; a different shape ABORTS the header comparison. NOT-SEPARATING." \
    "rec404-$h" "" || return 0
  req "$h" "/hcp/$ABS/" \
    "CELL 5 /hcp/<absent>/ trailing slash on a name that cannot exist: 301/308 => directory/mount semantics on a path with no directory; 404 as cell 4 => no directory semantics. NOT-SEPARATING between (a) and (b)." \
    "trailslash-$h" "" || return 0
  req "$h" "/app/hcp/$ABS" \
    "CELL 6 the token NOT at the start (/app/hcp/…): 200 entry digest => the exclusion is anchored at ^/hcp/; 404 => the selector matches '/hcp/' anywhere, which neither (a) nor (b) as stated predicts. SEPARATING in the second outcome, against both." \
    "apphcp-$h" "" || return 0
}

case "${1:-}" in
  all) sweep ;;
  *) echo "usage: probe.sh all" >&2; exit 64 ;;
esac
echo "LEDGER_ROWS=$(ledger_len) CAP=$CAP"
echo "DONE — $(ledger_len) harnessed of $CAP (20th = pre-itemisation reachability GET, FINDINGS.md §1)" >> "$RUNLOG"
