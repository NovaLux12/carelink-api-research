#!/usr/bin/env bash
# Area L probe harness — the harness AS SENT, committed as the record.
#
# Method: GET only. No POST, no OPTIONS, no token exchange, no authentication.
# Hosts:  index.commoncrawl.org, data.commoncrawl.org (nothing else).
# Cap:   45 requests total, counted in results.jsonl (see SEQ).
#
# DELAY: the claim (#57) and BRIEF.md say 2.5 s. docs/09 §1 says ">=3 s on
# archive calls", citing recon/ARCHIVE-URLS.md §0, whose q.sh does `sleep 3`.
# BRIEF.md's own precedence rule says the repository wins, so DELAY is 3.5 s.
# The sleep is INSIDE the per-host flock, so the gap is real even if another
# worker probes the same host.
#
# Every request takes $LOOP/host-<hostname>.lock before the sleep, and every
# request gets its own ledger row with its own seq, including retries.

set -u

DELAY=3.5
CAP=45
HERE="$(cd "$(dirname "$0")" && pwd)"
WT="$(git rev-parse --show-toplevel)"
LOOP="$(cd "$WT/../.." && pwd)"          # .../carelink-api-research/.loop
cd "$HERE"

mkdir -p headers tmp
BODIES="$(cd "$WT/../.." && pwd)/probe-bodies-area-l"   # outside the repo; never committed
mkdir -p "$BODIES"
# Resume the sequence from whatever is already in the ledger. Rows 1-4 are the
# four requests a debug harness sent before the send-path defect was fixed; they
# were appended by hand in this schema because the tool that sent them wrote no
# usable row. The sequence must not restart underneath them.
SEQ=0
if [ -s results.jsonl ]; then
  SEQ="$(wc -l < results.jsonl | tr -d ' ')"
fi

now() { date -u +%FT%T.%3NZ; }

# req <host> <url-path> <host_tag> <role>
req() {
  local host="$1" path="$2" tag="$3" role="$4"
  SEQ=$((SEQ + 1))
  local seq="$SEQ"
  if [ "$seq" -gt "$CAP" ]; then
    echo "REFUSED: seq $seq would exceed cap $CAP" >&2
    SEQ=$((SEQ - 1))
    return 9
  fi
  local slug; slug="$(printf '%02d' "$seq")"
  local H="headers/${slug}-${tag}.h"
  local E="headers/${slug}-${tag}.err"
  local B="$BODIES/${slug}.body"
  local R="tmp/${slug}"
  local t_queued; t_queued="$(now)"
  local url="https://${host}${path}"

  local hostseq; hostseq="$(python3 -c '
import json,sys,pathlib
host=sys.argv[1]; p=pathlib.Path("results.jsonl")
rows=[]
if p.exists() and p.stat().st_size:
    rows=[json.loads(l) for l in p.read_text().splitlines() if l.strip()]
print(sum(1 for r in rows if r["host"]==host)+1)' "$host")"

  # ---- the send ----
  # The command is written to its own file with every argument %q-quoted and
  # flock is given `sh <file>`, NOT `-c "<string>"`. An earlier revision nested
  # the curl inside the -c string; the nested quoting broke the send and the
  # harness aborted before anything left the machine (see FINDINGS.md
  # §"Defect 1"). This form has no nested quoting to get wrong.
  {
    printf 'sleep %q\n'       "$DELAY"
    printf 'date -u +%%FT%%T.%%3NZ > %q\n' "${R}.t0"
    printf 'curl -s --compressed -D %q -o %q -w %q %q > %q 2> %q\n' \
           "$H" "$B" '%{http_code}' "$url" "${R}.code" "$E"
    printf 'date -u +%%FT%%T.%%3NZ > %q\n' "${R}.t1"
  } > "${R}.sh"
  flock "$LOOP/host-${host}.lock" sh "${R}.sh"
  local rc=$?

  local code; code="$(cat "${R}.code" 2>/dev/null || echo 000)"
  local t_sent; t_sent="$(cat "${R}.t0" 2>/dev/null || echo '')"
  local t_done; t_done="$(cat "${R}.t1" 2>/dev/null || echo '')"
  local bytes sha
  bytes="$(wc -c < "${B}" 2>/dev/null || echo 0)"
  sha="$(sha256sum "${B}" 2>/dev/null | cut -d' ' -f1)"
  [ -z "$sha" ] && sha=""
  local ct; ct="$(grep -i '^content-type:' "${H}" 2>/dev/null | head -1 | tr -d '\r' | sed 's/^[^:]*: *//')"
  local disc="content-type: ${ct}"
  for h in x-amzn-errortype x-cache server; do
    local v; v="$(grep -i "^${h}:" "${H}" 2>/dev/null | head -1 | tr -d '\r' | sed 's/^[^:]*: *//')"
    [ -n "$v" ] && disc="${disc}|${h}: ${v}"
  done

  # ---- project the body down to facts; a raw capture is never committed ----
  python3 derive.py "${B}" > "${R}.proj" 2>/dev/null

  printf '%s  seq=%-3s host=%-24s %s  %s\n' "$t_done" "$seq" "$host" "$code" "$path" >> run.log

  python3 - "$seq" "$hostseq" "$host" "$tag" "$role" "$code" "$rc" "$bytes" "$sha" \
             "$disc" "$t_queued" "$t_sent" "$t_done" "$path" "${R}.proj" >> results.jsonl <<'PY'
import json, sys
(seq, host_seq, host, tag, role, code, rc, nbytes, sha, disc, tq, ts, td, path, projf) = sys.argv[1:16]
try:
    proj = json.loads(open(projf).read() or "{}")
except Exception as exc:
    proj = {"shape": "projection-error", "error": str(exc)[:200]}
row = {
    "seq": int(seq), "host_seq": int(host_seq), "host": host, "host_tag": tag,
    "method": "GET", "path": path, "role": role, "http_status": code,
    "curl_exit": int(rc), "body_bytes": int(nbytes), "body_sha256": sha,
    "disc_headers": disc,
    "body_head": "<withheld-by-policy: raw CDX/JSON text carries session material; see derive.py>",
    "t_queued": tq, "t_sent": ts, "t_done": td,
}
row.update(proj)
print(json.dumps(row))
PY
  echo "seq ${seq}  ${code}  ${path}"
  return 0
}

# ---------------------------------------------------------------- stages ----
# Usage: ./probe.sh <stage>
case "${1:-}" in
  stage1)  # controls, in order, before any candidate
    # (a) POSITIVE — a record query for a host/crawl pair area M's committed
    #     ledger already answers 200 for (its seq 60, matchType=host,
    #     CC-MAIN-2020-50, carelink.minimed.eu). Sent first, domain shape.
    req index.commoncrawl.org '/CC-MAIN-2020-50-index?url=carelink.minimed.eu&output=json&matchType=domain&limit=100' \
        control-A-positive-record-form-known-covered-host-and-crawl 'CONTROL-positive'
    # (b) ABSENCE, record form — the zero-oracle, behind (a)
    req index.commoncrawl.org '/CC-MAIN-2020-50-index?url=zz-area-l-absent-20261013.minimed.eu&output=json&matchType=host' \
        control-B-absent-record-form-fabricated-host-under-covered-domain 'CONTROL-absent'
    # (c) ABSENCE, count form — behind (a)
    req index.commoncrawl.org '/CC-MAIN-2020-50-index?url=zz-area-l-absent-20261013.minimed.eu&output=json&showNumPages=true&matchType=host' \
        control-C-absent-count-form-fabricated-host-under-covered-domain 'CONTROL-absent-count-instrument'
    # (d) POSITIVE, count instrument, on the covered host — and the exact cell
    #     area M left as a 504 (its seq 33), so it is both control and gap-fill
    req index.commoncrawl.org '/CC-MAIN-2020-50-index?url=carelink.minimed.eu&output=json&showNumPages=true&matchType=domain' \
        control-D-positive-count-instrument-covered-host-area-M-gap 'CONTROL-positive-count-instrument'
    ;;
  stage2)  # inventory — the crawl list, so the date anchors are chosen from
           # the published inventory rather than guessed
    req index.commoncrawl.org '/collinfo.json' \
        inventory-collinfo-json 'CRAWL-INVENTORY'
    ;;
  stage3)  # does a record query truncate? docs/10 §1's open row.
           # seq 5 returned 6 records with limit=100 while the count cell (seq 8)
           # said pages=1 pageSize=5. These three cells read that contradiction.
    #   3a: same query, NO limit -- does the default pageSize=5 cut it to 5?
    req index.commoncrawl.org '/CC-MAIN-2020-50-index?url=carelink.minimed.eu&output=json&matchType=domain' \
        trunc-A-no-limit-same-cell-as-seq5 'TRUNCATION-no-limit'
    #   3b: limit=2 -- WHICH end is kept when a limit bites?
    req index.commoncrawl.org '/CC-MAIN-2020-50-index?url=carelink.minimed.eu&output=json&matchType=domain&limit=2' \
        trunc-B-limit2-which-end-is-kept 'TRUNCATION-limit2'
    #   3c: page=1 -- does a second page exist, or is pages=1 the whole world?
    req index.commoncrawl.org '/CC-MAIN-2020-50-index?url=carelink.minimed.eu&output=json&matchType=domain&page=1&limit=100' \
        trunc-C-page1-does-a-second-page-exist 'TRUNCATION-page1'
    #   3d: docs/10's own closes-when -- "one query against a domain with a
    #       known-large result set compared against its blocks figure". M
    #       measured blocks=5 for medtronic.com on this crawl (its seq 40 cell).
    req index.commoncrawl.org '/CC-MAIN-2026-39-index?url=medtronic.com&output=json&matchType=domain&limit=2000' \
        trunc-D-known-large-set-medtronic-com-records 'TRUNCATION-known-large-records'
    req index.commoncrawl.org '/CC-MAIN-2026-39-index?url=medtronic.com&output=json&showNumPages=true&matchType=domain' \
        trunc-E-known-large-set-medtronic-com-blocks-figure 'TRUNCATION-known-large-count'
    ;;
  stage4)  # RE-ISSUES. Area M's binding correction: a 502/504/503/400 from this
           # API is a FAILURE and is re-issued -- never an absence. seq 12 (400)
           # and seq 14 (502) are both re-issued verbatim, each as its own row.
    req index.commoncrawl.org '/CC-MAIN-2020-50-index?url=carelink.minimed.eu&output=json&matchType=domain&page=1&limit=100' \
        reissue-R1-page1-was-400 'REISSUE-of-seq-12'
    req index.commoncrawl.org '/CC-MAIN-2026-39-index?url=medtronic.com&output=json&showNumPages=true&matchType=domain' \
        reissue-R2-medtronic-count-was-502 'REISSUE-of-seq-14'
    ;;
  stage5)  # THE TWO ENDS. ARCHIVE-URLS §3 dates the family 2013-05-17 ->
           # 2022-05-13. collinfo.json (seq 9) puts those two dates in coverage
           # gaps, so the anchors are the nearest crawl at or after each date.
           #   2013-05-17 -> next published crawl is CC-MAIN-2014-10
           #                  (2014-03-07 -> 2014-03-17)
           #   2022-05-13 -> next published crawl is CC-MAIN-2022-21
           #                  (2022-05-16 -> 2022-05-29, 3 days after the date);
           #                  the crawl before it is CC-MAIN-2022-05
           #                  (2022-01-16 -> 2022-01-29)
    req index.commoncrawl.org '/CC-MAIN-2014-10-index?url=minimed.eu&output=json&matchType=domain&limit=200' \
        anchor-2013-end-next-published-crawl-2014-10 'ANCHOR-2013-END'
    req index.commoncrawl.org '/CC-MAIN-2022-21-index?url=minimed.eu&output=json&matchType=domain&limit=200' \
        anchor-2022-end-next-published-crawl-2022-21 'ANCHOR-2022-END'
    req index.commoncrawl.org '/CC-MAIN-2022-05-index?url=minimed.eu&output=json&matchType=domain&limit=200' \
        anchor-2022-end-preceding-crawl-2022-05 'ANCHOR-2022-END-BEFORE'
    ;;
  stage6)  # THE SPREAD. Area M named six crawls; this sweep asks the five it
           # did not, spread across the ARCHIVE-URLS window, for the paths
           # Common Crawl itself records under minimed.eu. Same domain record
           # query as every other cell, so a hit is a sibling and a miss is a
           # miss readable behind this pass's control A.
    for c in CC-MAIN-2015-22 CC-MAIN-2017-04 CC-MAIN-2019-51 CC-MAIN-2020-24 CC-MAIN-2021-04 CC-MAIN-2021-25; do
      req index.commoncrawl.org "/${c}-index?url=minimed.eu&output=json&matchType=domain&limit=200" \
          "spread-${c}-minimed-eu-domain" 'CRAWL-SPREAD'
    done
    ;;
  stage7)  # RE-ISSUES of the three anchors. All three of stage 5's cells came
           # back 504/502/504 -- FAILURES, not absences, and the 2013 and 2022
           # ends are therefore UNKNOWN at this point, not empty. Each is
           # re-issued verbatim as its own row with its own seq.
    req index.commoncrawl.org '/CC-MAIN-2014-10-index?url=minimed.eu&output=json&matchType=domain&limit=200' \
        reissue-R3-anchor-2013-end-2014-10-was-504 'REISSUE-of-seq-17'
    req index.commoncrawl.org '/CC-MAIN-2022-21-index?url=minimed.eu&output=json&matchType=domain&limit=200' \
        reissue-R4-anchor-2022-end-2022-21-was-502 'REISSUE-of-seq-18'
    req index.commoncrawl.org '/CC-MAIN-2022-05-index?url=minimed.eu&output=json&matchType=domain&limit=200' \
        reissue-R5-anchor-2022-end-2022-05-was-504 'REISSUE-of-seq-19'
    ;;
  stage8)  # THIRD attempt on the two anchors that failed twice, PLUS the
           # diagnostic that decides what a repeat failure MEANS: a query for a
           # universal known-covered host on the SAME crawl. If example.com
           # answers 200 on CC-MAIN-2014-10 then the index is served and the
           # minimed.eu 504s are query failures; if example.com also fails, the
           # crawl itself is not being served and the failures say nothing about
           # minimed.eu in either direction.
    req index.commoncrawl.org '/CC-MAIN-2014-10-index?url=minimed.eu&output=json&matchType=domain&limit=200' \
        reissue-R6-anchor-2013-end-2014-10-third-attempt-verbatim 'REISSUE-of-seq-20'
    req index.commoncrawl.org '/CC-MAIN-2022-21-index?url=minimed.eu&output=json&matchType=domain&limit=200' \
        reissue-R7-anchor-2022-end-2022-21-third-attempt-verbatim 'REISSUE-of-seq-21'
    # the crawl-scoped reachability control, same crawl, universal host
    req index.commoncrawl.org '/CC-MAIN-2014-10-index?url=example.com&output=json&matchType=domain&limit=5' \
        diag-crawl-scoped-reachability-2014-10-universal-host 'CONTROL-crawl-scoped'
    req index.commoncrawl.org '/CC-MAIN-2022-21-index?url=example.com&output=json&matchType=domain&limit=5' \
        diag-crawl-scoped-reachability-2022-21-universal-host 'CONTROL-crawl-scoped'
    ;;
  stage9)  # RE-ISSUES of the three spread cells that came back 504. A 504 is a
           # FAILURE and never an absence; each is re-issued verbatim.
    req index.commoncrawl.org '/CC-MAIN-2015-22-index?url=minimed.eu&output=json&matchType=domain&limit=200' \
        reissue-R8-spread-2015-22-was-504 'REISSUE-of-seq-27'
    req index.commoncrawl.org '/CC-MAIN-2020-24-index?url=minimed.eu&output=json&matchType=domain&limit=200' \
        reissue-R9-spread-2020-24-was-504 'REISSUE-of-seq-30'
    req index.commoncrawl.org '/CC-MAIN-2021-25-index?url=minimed.eu&output=json&matchType=domain&limit=200' \
        reissue-R10-spread-2021-25-was-504 'REISSUE-of-seq-32'
    ;;
  stage10) # re-issue the two spread cells that failed twice, and an independent
           # second query shape for the NEW family member area M never saw, so
           # it carries the same "two shapes agree" weight M gave its anchor.
    req index.commoncrawl.org '/CC-MAIN-2015-22-index?url=minimed.eu&output=json&matchType=domain&limit=200' \
        reissue-R11-spread-2015-22-second-504 'REISSUE-of-seq-33'
    req index.commoncrawl.org '/CC-MAIN-2021-25-index?url=minimed.eu&output=json&matchType=domain&limit=200' \
        reissue-R12-spread-2021-25-second-400 'REISSUE-of-seq-35'
    req index.commoncrawl.org '/CC-MAIN-2020-24-index?url=carelink.minimed.eu&output=json&matchType=host&limit=200' \
        crosscheck-2020-24-host-shape-second-query-shape-for-new-member 'CROSSCHECK-host-shape'
    ;;
  stage11) # THE 2013 END, ANCHORED CORRECTLY. FINDINGS.md §3a first named
           # CC-MAIN-2014-10 as the crawl after 2013-05-17; that was WRONG. The
           # published inventory (collinfo.json, seq 9) shows the crawl after
           # 2013-05-17 is CC-MAIN-2013-20 (2013-05-18 -> 2013-06-20) -- one day
           # after the date ARCHIVE-URLS §3 records. The crawl-scoped control
           # (example.com on the same crawl) goes with it, because that is what
           # distinguishes an absent host from an unserved crawl.
    req index.commoncrawl.org '/CC-MAIN-2013-20-index?url=minimed.eu&output=json&matchType=domain&limit=200' \
        anchor-2013-end-CORRECT-crawl-2013-20 'ANCHOR-2013-END'
    req index.commoncrawl.org '/CC-MAIN-2013-20-index?url=example.com&output=json&matchType=domain&limit=5' \
        diag-crawl-scoped-reachability-2013-20-universal-host 'CONTROL-crawl-scoped'
    ;;
  stage12) # The last 2013 crawl, with its crawl-scoped control. CC-MAIN-2013-20
           # turned out to be LISTED in collinfo.json but NOT SERVED by the API
           # -- example.com 404s on it -- so its 404 on minimed.eu is an artefact
           # and not a negative. This is the one remaining honest attempt at the
           # 2013 end inside the cap.
    req index.commoncrawl.org '/CC-MAIN-2013-48-index?url=minimed.eu&output=json&matchType=domain&limit=200' \
        anchor-2013-end-last-2013-crawl-2013-48 'ANCHOR-2013-END'
    req index.commoncrawl.org '/CC-MAIN-2013-48-index?url=example.com&output=json&matchType=domain&limit=5' \
        diag-crawl-scoped-reachability-2013-48-universal-host 'CONTROL-crawl-scoped'
    ;;
  stage13) # BOUNDING THE UNSERVED REGION. Three 2013/2014-era crawls have each
           # answered its crawl-scoped control with "not served". This asks
           # whether a 2015-era crawl IS served, which bounds the region rather
           # than leaving it open-ended. Last stage inside the cap.
    req index.commoncrawl.org '/CC-MAIN-2015-06-index?url=minimed.eu&output=json&matchType=domain&limit=200' \
        bound-unserved-region-probe-2015-06 'BOUND-UNSERVED-REGION'
    req index.commoncrawl.org '/CC-MAIN-2015-06-index?url=example.com&output=json&matchType=domain&limit=5' \
        diag-crawl-scoped-reachability-2015-06-universal-host 'CONTROL-crawl-scoped'
    ;;
  *)
    echo "usage: $0 stage1|stage2|stage3|stage4|stage5|stage6|stage7|stage8" >&2; exit 2 ;;
esac
