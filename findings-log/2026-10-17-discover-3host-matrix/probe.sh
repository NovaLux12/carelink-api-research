#!/usr/bin/env bash
# probe.sh — the `discover/android/3.6` version axis on all three clcloud hosts.
#
# Question (issue #145): ORACLE-PROBE-MATRIX.md carries three-host coverage for
# 3 of 16 versions on this path. Is `v6` the ONLY version that splits across
# hosts? docs/10 row 58 warns explicitly against reading "v6-specific" as
# "only v6 splits" — this settles it.
#
# Method, all of it non-negotiable (AGENTS.md §8):
#   GET only. No OPTIONS, no POST, no token, no Cookie, no auth header.
#   >= 2.5 s between requests to the SAME host, enforced by the shared
#   per-host lock with the sleep INSIDE the lock (the locks are shared with
#   every other lane in this pool run, so the delay has to be inside).
#   --compressed on every request (AGENTS.md §7).
#   Controls first per host, so the oracle is not judged by the data it judges.
#   Candidates: the 16 version values already in the corpus, plus v99 as a
#   certainly-absent control. Nothing invented. Cap cannot need raising.
#
# Path: the matrix's `namespace` column is `connect/carepartner` and ALREADY
# includes `connect/`. It is used verbatim here. Prefixing it again would give
# `connect/connect/...` — the area-Y defect (docs/11, "Why there is no area AA").

set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
H="$HERE/headers"
mkdir -p "$H"

# The per-host locks are shared with every other lane in a pool run, so they
# live in the pool's own `.loop/` directory rather than in this worktree. It is
# located by walking up to a directory that holds `.loop/` beside a
# `findings-log/` — never hard-coded, so no machine path enters the repo
# (AGENTS.md §7 scrub list). Override with LOCKDIR=... if you are running this
# outside a pool checkout.
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

CAP=54          # hard ceiling, asserted below before every send
DELAY=2.5       # seconds, same host, sleep inside the lock

: > "$HERE/results.jsonl"
: > "$HERE/run.log"

LOG() { printf '%s  %s\n' "$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)" "$*" | tee -a "$HERE/run.log"; }

hdrval() { grep -i "^$1:" "$2" 2>/dev/null | head -1 | cut -d: -f2- | tr -d '\r' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//'; }

seq=0

req() {
  local host="$1" ver="$2" role="$3"
  local hseq="$4"

  if [ "$seq" -ge "$CAP" ]; then
    LOG "CAP REACHED at ${seq} of ${CAP} — refusing to send $host $ver"
    exit 1
  fi

  seq=$((seq + 1))
  local tag
  tag="$(printf '%02d' "$seq")-$host-$ver"
  local url="https://$host/connect/carepartner/$ver/discover/android/3.6"
  local lock="$LOCKDIR/host-$host.lock"

  local t_queued t_sent t_done status
  t_queued=$(date +%s.%N)

  exec {lockfd}>"$lock" || { LOG "cannot open lock $lock"; exit 1; }
  # Blocking acquire, with a ceiling so a stuck peer cannot hang this pass.
  if ! flock -w 300 "$lockfd"; then
    LOG "LOCK TIMEOUT on $lock for $tag"
    exec {lockfd}>&-
    exit 1
  fi
  sleep "$DELAY"          # <-- the delay is INSIDE the lock, on purpose
  t_sent=$(date +%s.%N)
  status=$(curl -s --compressed -D "$H/$tag.h" -o "$H/$tag.b" -w '%{http_code}' "$url")
  t_done=$(date +%s.%N)
  flock -u "$lockfd"
  exec {lockfd}>&-

  local bytes ctype errortype xcache cumsig sha
  bytes=$(wc -c < "$H/$tag.b" 2>/dev/null | tr -d ' ')
  ctype=$(hdrval 'content-type' "$H/$tag.h")
  errortype=$(hdrval 'x-amzn-errortype' "$H/$tag.h")
  xcache=$(hdrval 'x-cache' "$H/$tag.h")
  cumsig=$(hdrval 'x-cum-signature' "$H/$tag.h")
  sha=$(sha256sum "$H/$tag.b" 2>/dev/null | cut -d' ' -f1)

  jq -nc \
    --arg seq "$seq" --arg host_seq "$hseq" \
    --arg t_queued "$t_queued" --arg t_sent "$t_sent" --arg t_done "$t_done" \
    --arg host "$host" --arg ver "$ver" --arg role "$role" --arg method GET \
    --arg url "$url" --arg status "$status" --arg content_type "$ctype" \
    --arg bytes "$bytes" --arg x_amzn_errortype "$errortype" \
    --arg x_cache "$xcache" --arg x_cum_signature_present "$([ -n "$cumsig" ] && echo yes || echo no)" \
    --arg body_sha256 "$sha" --arg tag "$tag" \
    '{seq:($seq|tonumber), host_seq:($host_seq|tonumber),
      t_queued:$t_queued, t_sent:$t_sent, t_done:$t_done,
      host:$host, ver:$ver, role:$role, method:$method, url:$url,
      status:($status|tonumber), content_type:$content_type,
      bytes:($bytes|tonumber), x_amzn_errortype:$x_amzn_errortype,
      x_cache:$x_cache, x_cum_signature_present:$x_cum_signature_present,
      body_sha256:$body_sha256, capture:$tag}' \
    >> "$HERE/results.jsonl"

  LOG "seq=$seq host_seq=$hseq $host $ver [$role] GET -> $status ${ctype:-<no-ct>} ${bytes}B err=${errortype:-<none>} cum=${cumsig:+yes}${cumsig:-no} sha=${sha:0:12}"
}

# Per-host request order. v99 is the certainly-absent control and v11 is the
# known-served control, both recorded in ORACLE-PROBE-MATRIX.md rows 15/17 and
# 29/37/38. v11 is sent ONCE per host: its control cell and its matrix cell are
# the same method, path and host, so a second send would be a request that buys
# nothing. That is why the pass costs 51 requests against a 54 cap.
HOSTS=(clcloud.minimed.eu clcloud.minimed.com clcloud-trials.minimed.com)
VERS=(v99 v11 v1 v2 v3 v4 v5 v6 v7 v8 v9 v10 v12 v13 v14 v15 v16)

for host in "${HOSTS[@]}"; do
  lock="$LOCKDIR/host-$host.lock"
  [ -e "$lock" ] || : > "$lock"
  hseq=0
  LOG "=== host $host — 17 requests, controls first (v99 absent, v11 served) ==="
  for ver in "${VERS[@]}"; do
    hseq=$((hseq + 1))
    case "$ver" in
      v99) role=control-absent ;;
      v11) role=control-served+matrix-v11 ;;
      *)   role=matrix ;;
    esac
    req "$host" "$ver" "$role" "$hseq"
  done
done

LOG "=== done: ${seq} requests sent, cap ${CAP} ==="