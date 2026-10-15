#!/bin/bash
# Area R successor 2 — is the client-side deviceFamily enum's `_*` suffix consumed
# anywhere, or is the enum declared and never read?
#
# Claim issue #132.  Cap 8, GET only, curl --compressed, 2.5 s sleep INSIDE the
# shared per-host flock, TS_SENT emitted inside the lock immediately before curl
# execs.  One host: carelink.minimed.eu.
#
# WHAT THIS PASS IS. A STATIC pass over ONE artefact. The question is not "what
# does the vendor's API do with BLE_X" — that needs a token and is not this
# project's to ask. The question is: within the corpus this pass names, is there
# a call site that BRANCHES on the `_X` suffix, or is the suffix only DECLARED?
# A declared-but-unread enum member is the shape that rots quietly, because the
# declaration reads like a specification. A negative counts as a result.
#
# WHY ONLY TWO REQUESTS OF AN EIGHT-REQUEST CAP. The corpus is one file. Fetching
# it once, behind an anchor gate, is the whole data need; the rest of the cap is
# the room the issue reserved "for a re-issue if the anchor fails". Spending
# budget on more requests would not widen the population — the population is
# defined by the artefact, not by how often it is read. The 6 unspent requests are
# reported as unspent, not as work deferred.
#
# ORDER: the certainly-absent control goes out FIRST, so the host's 404 shape on
# the `*.js` path family is known before the 200 that the anchor will return is
# interpreted as "a real chunk". A control sent after the cell it judges is a
# control written to fit the answer.
#
# THE TWO REMAINING CONTROLS COST ZERO REQUESTS, and saying so is the point.
# The case-sensitivity control and the literal-vs-directive control are searches
# over the ONE body this pass already fetched; re-fetching to run them would
# spend a request to re-observe a file whose digest is already pinned in the same
# ledger row. They are run offline by xsuffix-analyse.py and are labelled as such
# wherever they are cited.
#
# Bodies are written to $TMPBODIES and never committed (the anchor is 3.4 MB;
# findings-log rejects anything over 1 MiB). Digests, sizes, the verdict table
# and the token census are committed.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
# LOOP is the shared per-host lock directory. This file sits at
# <checkout>/.loop/worktrees/B/findings-log/<dir>/, so four levels up is .loop.
# It is NOT inside the worktree and is shared with the other three workers.
LOOP="$(cd "$HERE/../../../.." && pwd)"
LOGDIR=$HERE
OUT=$LOGDIR/headers
DELAY=${DELAY:-2.5}
CAP=${CAP:-8}
TMPBODIES=${TMPBODIES:?set TMPBODIES to a writable directory for the response bodies}
HOST=carelink.minimed.eu
LOCK="$LOOP/host-$HOST.lock"
LEDGER="$LOGDIR/results.jsonl"
RUNLOG="$LOGDIR/run.log"
TAGS=$LOGDIR/tags.tsv
mkdir -p "$OUT"
[ -d "$TMPBODIES" ] || { echo "TMPBODIES is not a directory" >&2; exit 2; }
[ -e "$LOCK" ] || : > "$LOCK"

# RESUMABLE for the same reason area K's is: every request gets a ledger row,
# whatever issued it. The ledger is APPENDED to, the sequence continues from the
# highest seq already present, and an already-ledgered path is not re-sent.
# Truncating a harness's own ledger on start-up is how a pass under-reports the
# budget it spent.
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
  : > "$LEDGER"; : > "$TAGS"; SEQ=0
fi

sent() { grep -qF "\"path\": \"$1\"" "$LEDGER" 2>/dev/null; }

# The certainly-absent candidate is derived, not enumerated: same `*.js` path
# shape as the corpus, with a nonce no vendor build has ever emitted (AGENTS.md
# section 8 — bounded, justified candidate list, derivation recorded).
NONCE="$(head -c 12 /dev/urandom | od -An -tx1 | tr -d ' \n')"
ABSENT="/zzzz.not-a-bundle-$NONCE.js"

echo "run start: $(date -u +%FT%T.%3NZ) tmpbodies=<REDACTED> delay=${DELAY} cap=${CAP} host=${HOST} resume=${RESUME} from_seq=$((SEQ+1))" >> "$RUNLOG"

req() { # req <path> <role> <tag>
  local path="$1" role="$2" tag="$3"
  # FORCE=1 re-issues a path already in the ledger. The first run of this pass
  # produced a row whose t_sent was later than its own t_done, so the ledger's
  # send-times could not carry a spacing claim; the cells were re-sent rather
  # than the claim being made from a record known to be broken. A re-issued
  # request is still a request: it gets its own row, with seq continuing, and
  # this pass accounts for it.
  if sent "$path" && [ "${FORCE:-0}" != "1" ]; then
    echo "already in ledger: $path" >&2; return 0
  fi
  SEQ=$((SEQ+1)); local seq=$SEQ
  if [ "$SEQ" -gt "$CAP" ]; then
    echo "CAP REACHED at seq=$SEQ — refusing to send. Ledger holds $(wc -l < "$LEDGER") rows." >&2
    echo "cap reached: $(date -u +%FT%T.%3NZ) rows=$(wc -l < "$LEDGER")" >> "$RUNLOG"
    return 9
  fi
  local url="https://$HOST$path"
  local t_queued; t_queued=$(date -u +%FT%T.%3NZ)
  local out; out=$(flock "$LOCK" "$HERE/send.sh" "$DELAY" "$OUT/$tag.h" "$TMPBODIES/$tag.b" "$url" 2>&1)
  local t_lock t_sent code curl_exit t_done
  IFS=$'\t' read -r t_lock t_sent code curl_exit t_done <<<"$out"
  # ASSERT THE ORDERING BEFORE THE ROW IS WRITTEN. A ledger that can record a
  # send-time later than its own completion-time cannot be used to recompute a
  # gap, and a spacing claim made from it would be a claim from nothing.
  if ! [[ "$t_lock" < "$t_sent" ]] || ! [[ "$t_sent" < "$t_done" ]]; then
    echo "REFUSING TO LEDGER seq=$seq — stamp order violated:" \
         "lock=$t_lock sent=$t_sent done=$t_done" >&2
    echo "stamp-order violation: $(date -u +%FT%T.%3NZ) seq=$seq lock=$t_lock sent=$t_sent done=$t_done" >> "$RUNLOG"
    return 8
  fi
  local bytes="" sha=""
  if [ -f "$TMPBODIES/$tag.b" ]; then
    bytes=$(wc -c < "$TMPBODIES/$tag.b" | tr -d ' ')
    sha=$(sha256sum "$TMPBODIES/$tag.b" | cut -d' ' -f1)
  fi
  printf '%s\t%s\n' "$tag" "$path" >> "$TAGS"
  python3 - "$LEDGER" "$seq" "$t_queued" "$t_lock" "$t_sent" "$t_done" "$HOST" "$path" \
              "$role" "$url" "$code" "$curl_exit" "$bytes" "$sha" \
              "$OUT/$tag.h" "$DELAY" <<'PY'
import json, os, re, sys
(ledger, seq, tq, tlk, ts, td, host, path, role, url, code, cx, nbytes, sha, hdr, delay) = sys.argv[1:17]
h = {}
if os.path.exists(hdr):
    for line in open(hdr, errors='replace'):
        m = re.match(r'^([A-Za-z0-9-]+):\s*(.*)$', line.strip())
        if m:
            h[m.group(1).lower()] = m.group(2).strip()
row = {
    "seq": int(seq), "host": host, "method": "GET", "path": path, "role": role,
    "url": url, "http_status": code, "curl_exit": int(cx),
    "content_type": h.get("content-type", "(none)"),
    "content_encoding": h.get("content-encoding", "(none)"),
    "x_amzn_errortype": h.get("x-amzn-errortype", "(none)"),
    "x_ca_err": h.get("x-ca-err", "(none)"),
    "x_cache": h.get("x-cache", "(none)"),
    "access_control_allow_origin": h.get("access-control-allow-origin", "(none)"),
    "server": h.get("server", "(none)"),
    "etag": h.get("etag", "(none)"),
    "last_modified": h.get("last-modified", "(none)"),
    "body_bytes": int(nbytes) if nbytes else None,
    "body_sha256": sha or None,
    "delay_declared_s": delay,
    "t_queued": tq, "t_lock_acquired": tlk, "t_sent": ts, "t_done": td,
}
open(ledger, "a").write(json.dumps(row) + "\n")
PY
  echo "$(date -u +%FT%T.%3NZ) seq=$seq host=$HOST tag=$tag code=$code ctype=$(grep -i '^content-type:' "$OUT/$tag.h" 2>/dev/null | head -1 | cut -d' ' -f2-) bytes=${bytes:-0} sha=${sha:-none} role=$role" >> "$RUNLOG"
  echo "seq=$seq tag=$tag code=$code bytes=${bytes:-0} sha=${sha:-none} sent=$t_sent"
}

# ---- 1. CONTROL, certainly-absent path (goes out before the cell it judges) ----
# ---- 2. DATA CELL + POSITIVE CONTROL: the corpus, behind the anchor gate ----
# Run 1 wrote ledger rows 1-2 whose send-times were not usable (see send.sh).
# Both cells were re-sent under the fixed instrument; those rows are 3-4 and
# they are the pair the spacing claim is made from. FORCE=1 re-issues the paths
# deliberately — the requests were spent, so they are accounted for.
ROLE_SUFFIX="${ROLE_SUFFIX:-}"
req "$ABSENT" "CONTROL-certainly-absent-proves-the-hosts-404-shape-on-this-path-family-is-not-a-chunk$ROLE_SUFFIX" "b-absent"

req "/main.6595daf83bd6d4b1.js" "DATA-corpus-and-POSITIVE-control-anchor-gate-pinned-sha256-and-byte-length$ROLE_SUFFIX" "b-main"

echo "run end: $(date -u +%FT%T.%3NZ) rows=$(wc -l < "$LEDGER") cap=$CAP" >> "$RUNLOG"