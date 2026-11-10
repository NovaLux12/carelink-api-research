#!/usr/bin/env bash
# probe.sh — area AE: is the `android/<app-version>` tail a lookup table, or a
# threshold?  Pass of 2026-11-10, claim #161, branch research/ae-appversion-tail.
#
# Prior art: findings-log/2026-10-17-area-aa-appversion-axis/.  AA established,
# OBSERVED 20/20 GETs, that at base v13 the tail SELECTS content on both
# clcloud.minimed.com and clcloud-trials.minimed.com, and is never validated.
# AA's four tails were 3.5, 3.6, 3.9 and one fabricated value, so a boundary
# anywhere in (3.5,3.6] or (3.6,3.9] fits its cells exactly as well as a
# per-string table.  This pass ladders STRICTLY INSIDE (3.6,3.9) on host 1.
#
# Method, all of it non-negotiable (AGENTS.md §8):
#   GET only. No POST, no OPTIONS, no token, no Cookie, no auth header.
#   >= 2.5 s between requests to the SAME host, with the sleep INSIDE the
#   shared per-host flock.
#   --compressed on every request (AGENTS.md §7).
#   Controls FIRST per host: v99 (certainly-absent base) then v11 (served).
#   Never send while a gate run executes (AA's rule, kept unchanged).
#   Bodies are transient: only status/content-type/bytes/sha256 and the
#   tail-erased digest are written to the ledger (AGENTS.md §7).
#
# Usage:  ./probe.sh host1     # controls + the 7-cell ladder on clcloud.minimed.com
#         ./probe.sh host2     # same ladder on clcloud-trials.minimed.com
#
# CAP is asserted against the LEDGER, not a counter local to this process, so a
# second invocation cannot silently exceed the pass budget.

set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
H="$(mktemp -d "${TMPDIR:-/tmp}/ae-bodies.XXXXXX")"   # bodies are transient
mkdir -p "$H"

REPO="NovaLux12/carelink-api-research"

LOCKDIR=""
probe_d="$HERE"
for _ in 1 2 3 4 5 6 7 8; do
  if [ -d "$probe_d/.loop" ] && [ -d "$probe_d/findings-log" ]; then
    LOCKDIR="$probe_d/.loop"; break
  fi
  probe_d="$(dirname "$probe_d")"
done
[ -n "$LOCKDIR" ] || { echo "LOCKDIR not found — set LOCKDIR to the pool .loop directory" >&2; exit 2; }
GATELOCK="$LOCKDIR/gate.lock"

CAP=20          # hard ceiling for the whole pass, checked against the ledger
DELAY=2.5       # seconds, same host, sleep inside the lock
MAXWAIT=60      # gate-check cycles (60 x 10 s = 10 min) before giving up a send

: > "$HERE/gh-run-err.log"
[ -f "$HERE/results.jsonl" ] || : > "$HERE/results.jsonl"
[ -f "$HERE/run.log" ] || : > "$HERE/run.log"

LOG() { printf '%s  %s\n' "$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)" "$*" | tee -a "$HERE/run.log"; }

now() { date +%s.%N; }

hdrval() { grep -i "^$1:" "$2" 2>/dev/null | head -1 | cut -d: -f2- | tr -d '\r' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//'; }

gate_clear() {
  flock -n "$GATELOCK" true 2>/dev/null || return 1
  local runs
  if ! runs=$(env -u GH_CONFIG_DIR -u GH_TOKEN gh run list --repo "$REPO" --workflow research-gate.yml --status queued --status in_progress -L 10 2>>"$HERE/gh-run-err.log"); then
    return 2
  fi
  [ -z "$runs" ] || return 3
  return 0
}

seq=$(grep -c . "$HERE/results.jsonl" 2>/dev/null || true)
seq=${seq:-0}

req() {
  local host="$1" base="$2" appver="$3" role="$4" hseq="$5"

  seq=$(grep -c . "$HERE/results.jsonl" 2>/dev/null || true); seq=${seq:-0}
  if [ "$seq" -ge "$CAP" ]; then
    LOG "CAP REACHED at ${seq} of ${CAP} — refusing to send $host $base android/$appver"
    exit 1
  fi

  seq=$((seq + 1))
  local tag
  tag="$(printf '%02d' "$seq")-$host-$base-android-$appver"
  local path="/connect/carepartner/$base/discover/android/$appver"
  local url="https://$host$path"
  local lock="$LOCKDIR/host-$host.lock"
  local hf="$H/$tag.h" bf="$H/$tag.b"

  local t_queued t_checked t_sent t_done status curl_rc checks waits gate_wait_s
  t_queued=$(now)

  exec {lockfd}>"$lock" || { LOG "cannot open lock $lock"; exit 1; }
  if ! flock -w 600 "$lockfd"; then
    LOG "LOCK TIMEOUT on $lock for $tag"
    exec {lockfd}>&-
    exit 1
  fi

  checks=0; waits=0
  gate_skip_start=$(now)
  while :; do
    checks=$((checks + 1))
    gate_clear
    rc=$?
    if [ "$rc" -eq 0 ]; then break; fi
    waits=$((waits + 1))
    LOG "seq=$seq gate busy (rc=$rc) — wait $waits/$MAXWAIT inside the host lock, then re-check"
    if [ "$waits" -ge "$MAXWAIT" ]; then
      LOG "seq=$seq gate never cleared after $waits waits — send ABORTED, never sent"
      flock -u "$lockfd"; exec {lockfd}>&-
      exit 1
    fi
    sleep 10
  done
  t_checked=$(now)
  gate_wait_s=$(awk "BEGIN{printf \"%.3f\", $t_checked - $gate_skip_start}")

  sleep "$DELAY"          # the delay is INSIDE the lock, after the gate check
  t_sent=$(now)
  status=$(curl -s --compressed -m 45 -D "$hf" -o "$bf" -w '%{http_code}' "$url")
  curl_rc=$?
  t_done=$(now)
  flock -u "$lockfd"
  exec {lockfd}>&-

  local bytes ctype errortype sha erased erase_ok
  bytes=$(wc -c < "$bf" 2>/dev/null | tr -d ' ')
  ctype=$(hdrval 'content-type' "$hf")
  errortype=$(hdrval 'x-amzn-errortype' "$hf")
  sha=$(sha256sum "$bf" 2>/dev/null | cut -d' ' -f1)
  # tail-erased digest: replace the echoed tail inside the `config` field with a
  # fixed marker, then re-digest.  A pure echo cannot survive this; the status
  # line cannot see the difference at all (AA §4.1).
  erased=$(python3 - "$bf" "$appver" <<'PY'
import hashlib, re, sys
raw = open(sys.argv[1], 'rb').read()
tail = sys.argv[2].encode()
m = re.match(rb'\{"config":"android,([^"]*)",', raw)
if not m:
    print(''); sys.exit(0)
canon = raw[:m.start(1)] + b'@@' + raw[m.end(1):]
print('echo_n=%d' % raw.count(tail))
print(hashlib.sha256(canon).hexdigest())
PY
)
  erase_ok=$(printf '%s\n' "$erased" | sed -n '1p')
  erased=$(printf '%s\n' "$erased" | sed -n '2p')

  # Truncate the echoed document's identity columns too (bounded projection).
  local struct
  struct=$(python3 - "$bf" "$appver" <<'PY'
import json, re, sys
raw = open(sys.argv[1], 'rb').read()
try:
    doc = json.loads(raw)
    cp = doc["CP"]
    bases = sorted({re.search(r"/carepartner/(v[\w]+)$", c["baseUrlCumulus"]).group(1) for c in cp})
    print(json.dumps({
        "adv_cumulus": ",".join(bases),
        "carelink": cp[0]["baseUrlCareLink"].rsplit("/", 1)[-1],
        "n_cp": len(cp),
        "n_ctry": len(doc.get("supportedCountries", [])),
        "n_cert": len(doc.get("certificates", [])),
        "sso": sorted({c["SSOConfiguration"].rsplit("/", 1)[-1] for c in cp}),
    }, sort_keys=True))
except Exception as e:
    print("")
PY
)

  jq -nc \
    --arg seq "$seq" --arg host_seq "$hseq" \
    --arg t_queued "$t_queued" --arg t_checked "$t_checked" \
    --arg t_sent "$t_sent" --arg t_done "$t_done" \
    --arg gate_checks "$checks" --arg gate_waits "$waits" --arg gate_wait_s "$gate_wait_s" \
    --arg host "$host" --arg base "$base" --arg appver "$appver" --arg role "$role" \
    --arg method GET --arg path "$path" --arg url "$url" \
    --arg status "$status" --arg curl_exit "$curl_rc" \
    --arg content_type "$ctype" --arg bytes "$bytes" \
    --arg x_amzn_errortype "$errortype" \
    --arg echo_field "$erase_ok" \
    --arg erased_config_sha256 "$erased" \
    --arg body_sha256 "$sha" --arg structure "$struct" --arg capture "$tag" \
    '{seq:($seq|tonumber), host_seq:($host_seq|tonumber),
      t_queued:$t_queued, t_checked:$t_checked, t_sent:$t_sent, t_done:$t_done,
      gate_checks:($gate_checks|tonumber), gate_waits:($gate_waits|tonumber),
      gate_wait_s:($gate_wait_s|tonumber),
      host:$host, base:$base, appver:$appver, role:$role,
      method:$method, path:$path, url:$url,
      status:(try ($status|tonumber) catch 0), curl_exit:($curl_exit|tonumber),
      content_type:$content_type, bytes:(try ($bytes|tonumber) catch 0),
      x_amzn_errortype:$x_amzn_errortype, $echo_field,
      erased_config_sha256:$erased_config_sha256,
      body_sha256:$body_sha256,
      structure:(try ($structure|fromjson) catch null), capture:$capture}' \
    >> "$HERE/results.jsonl"

  LOG "seq=$seq host_seq=$hseq $host $base android/$appver [$role] GET -> ${status:-curl-rc-$curl_rc} ${ctype:-<no-ct>} ${bytes}B err=${errortype:-<none>} sha=${sha:0:12} erased=${erased:0:12} gate_waits=$waits"
  local d
  d=$(printf '%s\n' "$struct")
  [ -n "$d" ] && LOG "   structure: $d"
  return 0
}

MODE="${1:-}"
case "$MODE" in
  host1) HOST=clcloud.minimed.com ;;
  host2) HOST=clcloud-trials.minimed.com ;;
  *) echo "usage: $0 host1|host2" >&2; exit 2 ;;
esac

lock="$LOCKDIR/host-$HOST.lock"; [ -e "$lock" ] || : > "$lock"
LOG "=== host $HOST — controls first (v99 absent, v11 served), then 7 tails in (3.6,3.9) ==="
hseq=0
req "$HOST" v99 3.6 control-absent $((hseq += 1)) &&
req "$HOST" v11 3.6 control-served $((hseq += 1)) &&
req "$HOST" v13 3.61 data-ladder $((hseq += 1)) &&
req "$HOST" v13 3.65 data-ladder $((hseq += 1)) &&
req "$HOST" v13 3.7  data-ladder $((hseq += 1)) &&
req "$HOST" v13 3.75 data-ladder $((hseq += 1)) &&
req "$HOST" v13 3.8  data-ladder $((hseq += 1)) &&
req "$HOST" v13 3.85 data-ladder $((hseq += 1)) &&
req "$HOST" v13 3.89 data-ladder $((hseq += 1))
LOG "=== host $HOST done: $hseq requests this run; ledger now $(grep -c . "$HERE/results.jsonl") of cap $CAP ==="
