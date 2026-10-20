#!/usr/bin/env bash
# probe.sh — the `android/<app-version>` axis on the two cumulus host that
# have never had it swept: .com and -trials (docs/11 area AA, claim #151).
#
# Question: the app-version axis selects content on the .eu cumulus host
# (04-deep-surface pins clcloud.minimed.eu v13/discover/android/3.5 -> 200
# with an SSO selector, and .../3.9 -> 200 without). Does it GATE on
# clcloud.minimed.com and clcloud-trials.minimed.com too, or does it merely
# ECHO there (the -trials template reading)?
#
# NOTE ON HOST NAMES. Claim #151 and the pool lane brief name
# `carelink.minimed.com` and `carelink-trials.minimed.com`. Those are the
# PATIENT hosts (docs/00 deployment table); the /connect/carepartner
# discovery namespace the area describes is recorded only on the CUMULUS
# family, and every precedent the area builds on is a cumulus-family fact:
#   - the .eu app-version pins (04-deep-surface.hurl:14,:21) are clcloud.minimed.eu
#   - the v11 / v99 control verdicts the plan expects are docs/03 §7's clcloud rows
#   - the -trials fabricated-tail cell (android/absent-probe-413306,
#     findings-log/2026-10-14-pool-s8-v6split/results.jsonl seq 8) hit
#     clcloud-trials.minimed.com
#   - the 2026-10-17 base-path matrix this area extends ran on the same
#     three clcloud hosts
# docs/09 Oracle A applies to the clcloud / execute-api gateways, not the
# patient plane, so the claim's own oracle also requires the cumulus hosts.
# The hosts below are therefore clcloud.minimed.com and
# clcloud-trials.minimed.com. Resolved under the repo > claim > brief
# precedence (the lane brief's own rule); recorded in FINDINGS.md §0.
#
# Method, all of it non-negotiable (AGENTS.md §8):
#   GET only. No OPTIONS, no POST, no token, no Cookie, no auth header.
#   >= 2.5 s between requests to the SAME host, enforced by the shared
#   per-host lock with the sleep INSIDE the lock.
#   --compressed on every request (AGENTS.md §7).
#   Controls first per host: v99 (certainly-absent base path) then v11
#   (served cell), so the oracle on that host is set by the controls.
#   NEVER SEND WHILE A GATE RUN EXECUTES (claim #151 §scheduling): inside
#   the host lock, before every send, (1) acquire the shared gate lock
#   NON-BLOCKINGLY and release it immediately (the check never holds it),
#   and (2) require `gh run list --workflow research-gate.yml --status
#   queued --status in_progress` to return EMPTY. Sleep inside the host
#   lock and re-check until both hold.
#   Candidates: 2 base paths (v13, the -trials-routed v6) x 3 observed
#   app-version values (3.5/3.6/3.9) + one fabricated distinct-length tail,
#   minted after the prior absent-control shape on this path and never
#   claimed as a vendor asset. Nothing invented beyond that.

set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
H="$HERE/headers"
mkdir -p "$H"

REPO="NovaLux12/carelink-api-research"

# The per-host locks and the gate lock are shared with every other lane in
# this pool run, so they live in the pool's own `.loop/` directory. It is
# located by walking up to a directory that holds `.loop/` beside a
# `findings-log/` — never hard-coded, so no machine path enters the repo
# (AGENTS.md §7 scrub list). Override with LOCKDIR=... when running outside
# a pool checkout.
LOCKDIR="${LOCKDIR:-}"
if [ -z "$LOCKDIR" ]; then
  probe_d="$HERE"
  for _ in 1 2 3 4 5 6 7 8; do
    if [ -d "$probe_d/.loop" ] && [ -d "$probe_d/findings-log" ]; then
      LOCKDIR="$probe_d/.loop"; break
    fi
    probe_d="$(dirname "$probe_d")"
  done
fi
[ -n "$LOCKDIR" ] || { echo "LOCKDIR not found — set it to the pool .loop directory" >&2; exit 2; }
GATELOCK="$LOCKDIR/gate.lock"

CAP=20          # hard ceiling: 16 protocol cells + 4 controls, asserted before every send
DELAY=2.5       # seconds, same host, sleep inside the lock
MAXWAIT=90      # gate-check cycles (90 x 10 s = 15 min) before giving up a send

: > "$HERE/results.jsonl"
: > "$HERE/run.log"
: > "$HERE/gh-run-err.log"

LOG() { printf '%s  %s\n' "$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)" "$*" | tee -a "$HERE/run.log"; }

now() { date +%s.%N; }

hdrval() { grep -i "^$1:" "$2" 2>/dev/null | head -1 | cut -d: -f2- | tr -d '\r' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//'; }

# gate_clear: exit 0 only when BOTH conditions hold:
#   1. the shared gate lock acquires non-blockingly (and releases at once —
#      this check never holds it), and
#   2. no research-gate workflow run is queued or in_progress.
# Exit 1 = gate lock held; 2 = the gh call failed (a failure of the check,
# not a clear signal); 3 = queued/in_progress runs exist.
gate_clear() {
  flock -n "$GATELOCK" true 2>/dev/null || return 1
  local runs
  if ! runs=$(env -u GH_CONFIG_DIR -u GH_TOKEN gh run list --repo "$REPO" --workflow research-gate.yml --status queued --status in_progress -L 10 2>>"$HERE/gh-run-err.log"); then
    return 2
  fi
  [ -z "$runs" ] || return 3
  return 0
}

seq=0

req() {
  local host="$1" base="$2" appver="$3" role="$4" hseq="$5"

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
  # Blocking acquire, with a ceiling so a stuck peer cannot hang this pass.
  if ! flock -w 300 "$lockfd"; then
    LOG "LOCK TIMEOUT on $lock for $tag"
    exec {lockfd}>&-
    exit 1
  fi

  # NEVER-SEND-WHILE-A-GATE-RUNS check, inside the host lock, per send.
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

  local bytes ctype errortype xcache cumsig cumsiglen cumsigsha sha bodyhead
  bytes=$(wc -c < "$bf" 2>/dev/null | tr -d ' ')
  ctype=$(hdrval 'content-type' "$hf")
  errortype=$(hdrval 'x-amzn-errortype' "$hf")
  xcache=$(hdrval 'x-cache' "$hf")
  cumsig=$(hdrval 'x-cum-signature' "$hf")
  cumsiglen=${#cumsig}
  if [ -n "$cumsig" ]; then cumsigsha=$(printf '%s' "$cumsig" | sha256sum | cut -d' ' -f1); else cumsigsha=""; fi
  sha=$(sha256sum "$bf" 2>/dev/null | cut -d' ' -f1)
  bodyhead=$(head -c 100 "$bf" 2>/dev/null | tr '\n' ' ' | cut -d' ' -f1-6)

  jq -nc \
    --arg seq "$seq" --arg host_seq "$hseq" \
    --arg t_queued "$t_queued" --arg t_checked "$t_checked" \
    --arg t_sent "$t_sent" --arg t_done "$t_done" \
    --arg gate_checks "$checks" --arg gate_waits "$waits" --arg gate_wait_s "$gate_wait_s" \
    --arg host "$host" --arg base "$base" --arg appver "$appver" --arg role "$role" \
    --arg method GET --arg path "$path" --arg url "$url" \
    --arg status "$status" --arg curl_exit "$curl_rc" \
    --arg content_type "$ctype" --arg bytes "$bytes" \
    --arg x_amzn_errortype "$errortype" --arg x_cache "$xcache" \
    --arg x_cum_signature_present "$([ -n "$cumsig" ] && echo yes || echo no)" \
    --arg x_cum_signature_len "$cumsiglen" --arg x_cum_signature_sha256 "$cumsigsha" \
    --arg body_head "$bodyhead" --arg body_sha256 "$sha" --arg capture "$tag" \
    '{seq:($seq|tonumber), host_seq:($host_seq|tonumber),
      t_queued:$t_queued, t_checked:$t_checked, t_sent:$t_sent, t_done:$t_done,
      gate_checks:($gate_checks|tonumber), gate_waits:($gate_waits|tonumber),
      gate_wait_s:($gate_wait_s|tonumber),
      host:$host, base:$base, appver:$appver, role:$role,
      method:$method, path:$path, url:$url,
      status:(try ($status|tonumber) catch 0), curl_exit:($curl_exit|tonumber),
      content_type:$content_type, bytes:(try ($bytes|tonumber) catch 0),
      x_amzn_errortype:$x_amzn_errortype, x_cache:$x_cache,
      x_cum_signature_present:$x_cum_signature_present,
      x_cum_signature_len:($x_cum_signature_len|tonumber),
      x_cum_signature_sha256:$x_cum_signature_sha256,
      body_head:$body_head, body_sha256:$body_sha256, capture:$capture}' \
    >> "$HERE/results.jsonl"

  LOG "seq=$seq host_seq=$hseq $host $base android/$appver [$role] GET -> ${status:-curl-rc-$curl_rc} ${ctype:-<no-ct>} ${bytes}B err=${errortype:-<none>} cum=$([ -n "$cumsig" ] && echo yes || echo no) sha=${sha:0:12} gate_waits=$waits"
}

if [ "${1:-}" = "retry" ]; then
  # One-cell re-issue after a failed send. Same method/path/cap rules; the
  # retry is a NEW request and gets its own row (a bounded revision).
  HOST="${2:?host}"; BASE="${3:?base}"; APPVER="${4:?appver}"
  lock="$LOCKDIR/host-$HOST.lock"; [ -e "$lock" ] || : > "$lock"
  LOG "=== retry run: $BASE android/$APPVER on $HOST ==="
  case "$BASE" in
    v99) req "$HOST" "$BASE" "$APPVER" control-absent 1 ;;
    v11) req "$HOST" "$BASE" "$APPVER" control-served 2 ;;
    *)   req "$HOST" "$BASE" "$APPVER" data-retry 0 ;;
  esac
  LOG "=== done: ${seq} request sent this run, cap ${CAP} ==="
  exit 0
fi

# Per-host order: controls first (v99 absent, v11 served), then the 8 data
# cells: {v13, v6} x {3.5, 3.6, 3.9, the fabricated tail}.
# The fabricated tail `absent-probe-871` follows the prior pass's
# absent-control shape on this path (`absent-probe-<digits>`,
# findings-log/2026-10-14-pool-s8-v6split) at a distinct length — 3 chars for
# the observed values, 19 chars for the prior tail, 16 chars here — minted
# from the recorded convention and never a vendor asset claim.
HOSTS=(clcloud.minimed.com clcloud-trials.minimed.com)

for host in "${HOSTS[@]}"; do
  lock="$LOCKDIR/host-$host.lock"
  [ -e "$lock" ] || : > "$lock"
  hseq=0
  LOG "=== host $host — 10 requests, controls first (v99 absent, v11 served) ==="
  req "$host" v99 3.6 control-absent $((hseq += 1)) &&
  req "$host" v11 3.6 control-served $((hseq += 1)) &&
  req "$host" v13 3.5 data-v13 $((hseq += 1)) &&
  req "$host" v13 3.6 data-v13 $((hseq += 1)) &&
  req "$host" v13 3.9 data-v13 $((hseq += 1)) &&
  req "$host" v13 absent-probe-871 data-v13 $((hseq += 1)) &&
  req "$host" v6 3.5 data-v6 $((hseq += 1)) &&
  req "$host" v6 3.6 data-v6 $((hseq += 1)) &&
  req "$host" v6 3.9 data-v6 $((hseq += 1)) &&
  req "$host" v6 absent-probe-871 data-v6 $((hseq += 1))
  LOG "=== host $host done: $hseq requests, controls first ==="
done

LOG "=== done: ${seq} requests sent, cap ${CAP} ==="
