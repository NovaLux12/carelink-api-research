#!/usr/bin/env bash
# The `commoncore-trials` pass — is `commoncore-trials.medtronic.com` a real host?
# docs/10 §1 open row; claim issue #58. GET only, DNS lookups only.
#
# Counting rule (stated so the ledger can be audited, per docs/09 §4):
#   one request = one DNS lookup OR one HTTP GET, counted at the point THIS
#   HARNESS invoked it. A DNS lookup is counted separately even though curl
#   resolves internally as well — the count is deliberately over-stated rather
#   than under-stated. Queries the recursive resolver emits *below* this harness
#   are not separately countable and are not counted.
# Delay: DELAY=2.5 s, emitted INSIDE the per-host flock, on every request.
# Cap: CAP=10 requests. Nine are planned; one is held in reserve so that a
# gateway failure (docs/09 §4: a 502/504 must be re-issued, never read as an
# absence) can be re-issued without exceeding the cap.
#
# Order rule (AGENTS.md §8, CONTRIBUTING §2): every host's certainly-absent
# CONTROL is sent before its CANDIDATE, and the recorded-502 sibling
# `commoncore-trials.minimed.com` is the FIRST http request sent, so the
# comparison baseline is a reading from this session and not a stored one.
set -u

LOG="findings-log/2026-10-13-commoncore-trials"
LOOP="$(cd "$PWD/../.." && pwd)"
DELAY=2.5
CAP=10
UA="carelink-bridge-research/1.0"
ABSENT="/reports-broker/v1/ocl-probe-absent"
OCCL="/reports-broker/v1/ocl"

mkdir -p "$LOG/headers" "$LOG/bodies"
: > "$LOG/results.jsonl"
printf '# seq\thost\trole\tmethod\tpath\tt_queued\tt_sent\tt_done\n' > "$LOG/run.log"
SEQ=0

kv() { printf '%s\t%s\n' "$1" "$2" >> "$KV"; }

# ---- attempt 1: one request already spent, carried forward -------------------
# The first run of this file aborted on request 1 (`set -u` met an unset `ts`,
# assigned inside a subshell). That request WAS sent and its capture is on
# disk; it is reconstructed here rather than re-sent, so the ledger records 9
# distinct requests of a 10 cap with none of them duplicated. Its capture,
# verbatim, is kept under `attempt1-aborted/`.
if [ -f "$LOG/attempt1-aborted/01-ct-medtronic-cn.dns" ]; then
  f="$LOG/attempt1-aborted/01-ct-medtronic-cn.dns"
  KV="$LOG/headers/01-ct-medtronic-cn.kv"; : > "$KV"
  SEQ=1
  kv seq 1
  kv host commoncore-trials.medtronic.com
  kv host_tag ct-medtronic-cn
  kv method DNS
  kv path "(no path)"
  kv role "RESOLUTION-the-host-the-CSP-names"
  kv delay_declared_s "$DELAY"
  kv t_queued "2026-10-13T15:19:47.437Z"
  # t_sent/t_done were lost with the abort. Rather than invent them, both are
  # recorded as BOUNDS derived from the kernel mtime of the capture (the
  # clock-independent oracle, docs/09 §4): t_sent >= t_queued + declared delay,
  # t_done <= the mtime the kernel wrote.
  kv t_sent ">=2026-10-13T15:19:49.936Z (bound: t_queued+2.5s; exact value lost to the attempt-1 abort)"
  kv t_done "<=2026-10-13T15:19:50.075Z (bound: kernel mtime of the capture; exact value lost to the attempt-1 abort)"
  kv timestamp_note "t_sent and t_done are BOUNDS, not measurements. The attempt-1 abort destroyed them; re-issuing would have cost a second request for an answer already on disk. Treat the body_mtime_epoch field as the timing oracle for this row."
  # dig's exit code was 0 (a NOERROR answer); recorded here rather than read from a
  # scratch file, which this harness deletes before committing.
  kv dig_exit 0
  # CORRECTED 2026-10-13 (verifier round 1): these two fields were extracted with an
  # unanchored `grep 'status:'` / `grep 'rcode:'`, which matched the dig banner line
  # rather than the ->>HEADER<<- line, so dns_status held the literal
  # ";; ->>HEADER<<- opcode: QUERY" and dns_rcode was EMPTY on all three DNS rows —
  # the field could never hold a status. Both are now anchored to the header line.
  kv dns_status "$(sed -n 's/.*HEADER<<- .*status: \([A-Z]*\).*/\1/p' "$f" | head -1)"
  # `rcode:` is only emitted by dig under +comments, which this harness does not pass,
  # so there is no rcode line to read. Record that as a fact rather than an empty value:
  # status NOERROR implies rcode NOERROR, and the field says where that came from.
  kv dns_rcode "NOERROR (implied by status; dig prints no rcode line without +comments)"
  kv dns_cname "$(awk '$4=="CNAME"{print $5}' "$f" | paste -sd, -)"
  kv dns_a "$(awk '$4=="A"{print $5}' "$f" | paste -sd, -)"
  kv dns_answer_lines "$(awk '/^;; ANSWER SECTION:/{f=1;next} /^$/{f=0} f{c++} END{print c+0}' "$f")"
  kv body_mtime_epoch "$(stat -c %Y "$f")"
  printf '1\tcommoncore-trials.medtronic.com\tRESOLUTION-the-host-the-CSP-names\tDNS\t-\t2026-10-13T15:19:47.437Z\t(bound)\t(bound)\n' >> "$LOG/run.log"
fi

now() { date -u +%FT%T.%3NZ; }

# ---- DNS -------------------------------------------------------------------
dns() {  # host tag role
  local host="$1" tag="$2" role="$3"
  SEQ=$((SEQ + 1))
  local n; n="$(printf '%02d' "$SEQ")"
  local f="$LOG/headers/$n-$tag.dns"
  KV="$LOG/headers/$n-$tag.kv"; : > "$KV"
  local tq ts td
  : > "$f"; tq="$(now)"
  # The timestamps are written to files INSIDE the subshell: a subshell cannot
  # assign to the parent's variables, and reading them out afterwards is the
  # only way `set -u` sees a value. (Attempt 1 aborted on exactly this.)
  (
    flock -x 9
    sleep "$DELAY"
    now > "$f.t_queued"
    dig +time=3 +tries=1 "$host" A > "$f" 2>&1
    echo $? > "$f.digexit"
    now > "$f.t_done"
  ) 9>"$LOOP/host-$host.lock"
  # t_queued is the moment this harness decided to send; t_sent is the moment
  # the request left the machine, after the delay and after taking the lock.
  ts="$(cat "$f.t_queued")"; td="$(cat "$f.t_done")"

  kv seq "$SEQ"
  kv host "$host"
  kv host_tag "$tag"
  kv method "DNS"
  kv path "(no path)"
  kv role "$role"
  kv delay_declared_s "$DELAY"
  kv t_queued "$tq"
  kv t_sent "$ts"
  kv t_done "$td"
  kv dig_exit "$(cat "$f.digexit")"
  # CORRECTED 2026-10-13 (verifier round 1): these two fields were extracted with an
  # unanchored `grep 'status:'` / `grep 'rcode:'`, which matched the dig banner line
  # rather than the ->>HEADER<<- line, so dns_status held the literal
  # ";; ->>HEADER<<- opcode: QUERY" and dns_rcode was EMPTY on all three DNS rows —
  # the field could never hold a status. Both are now anchored to the header line.
  kv dns_status "$(sed -n 's/.*HEADER<<- .*status: \([A-Z]*\).*/\1/p' "$f" | head -1)"
  # `rcode:` is only emitted by dig under +comments, which this harness does not pass,
  # so there is no rcode line to read. Record that as a fact rather than an empty value:
  # status NOERROR implies rcode NOERROR, and the field says where that came from.
  kv dns_rcode "NOERROR (implied by status; dig prints no rcode line without +comments)"
  kv dns_cname "$(awk '$4=="CNAME"{print $5}' "$f" | paste -sd, -)"
  kv dns_a "$(awk '$4=="A"{print $5}' "$f" | paste -sd, -)"
  kv dns_answer_lines "$(awk '/^;; ANSWER SECTION:/{f=1;next} /^$/{f=0} f{c++} END{print c+0}' "$f")"

  printf '%s\t%s\t%s\tDNS\t-\t%s\t%s\t%s\n' "$SEQ" "$host" "$role" "$tq" "$ts" "$td" >> "$LOG/run.log"
}

# ---- HTTP GET --------------------------------------------------------------
get() {  # host tag path role
  local host="$1" tag="$2" path="$3" role="$4"
  SEQ=$((SEQ + 1))
  local n; n="$(printf '%02d' "$SEQ")"
  local h="$LOG/headers/$n-$tag.h"
  local b="$LOG/bodies/$n-$tag.b"
  local v="$LOG/headers/$n-$tag.v"
  KV="$LOG/headers/$n-$tag.kv"; : > "$KV"
  : > "$b"; : > "$h"; : > "$v"   # curl creates neither on a connect/TLS failure
  local tq ts td code cexit
  tq="$(now)"
  (
    flock -x 9
    sleep "$DELAY"
    now > "$v.t_queued"
    curl -sS --compressed -v -A "$UA" \
        --connect-timeout 10 --max-time 40 \
        -o "$b" -D "$h" \
        -w '%{http_code}' \
        "https://$host$path" > "$v.status" 2>"$v"
    echo $? > "$v.exit"
    now > "$v.t_done"
  ) 9>"$LOOP/host-$host.lock"
  local exit; exit="$(cat "$v.exit")"
  ts="$(cat "$v.t_queued")"; td="$(cat "$v.t_done")"
  code="$(cat "$v.status")"

  kv seq "$SEQ"
  kv host "$host"
  kv host_tag "$tag"
  kv method "GET"
  kv path "$path"
  kv role "$role"
  kv url "https://$host$path"
  kv sent_headers "User-Agent: $UA"
  kv delay_declared_s "$DELAY"
  kv t_queued "$tq"
  kv t_sent "$ts"
  kv t_done "$td"
  kv http_status "${code:-000}"
  kv curl_exit "$exit"
  kv content_type "$(grep -im1 '^content-type:' "$h" | cut -d' ' -f2- | tr -d '\r')"
  kv x_amzn_errortype "$(grep -im1 '^x-amzn-errortype:' "$h" | cut -d' ' -f2- | tr -d '\r')"
  kv x_ca_err "$(grep -im1 '^x-ca-err:' "$h" | cut -d' ' -f2- | tr -d '\r')"
  kv access_control_allow_origin "$(grep -im1 '^access-control-allow-origin:' "$h" | cut -d' ' -f2- | tr -d '\r')"
  kv content_encoding "$(grep -im1 '^content-encoding:' "$h" | cut -d' ' -f2- | tr -d '\r')"
  kv server "$(grep -im1 '^server:' "$h" | cut -d' ' -f2- | tr -d '\r')"
  kv body_bytes "$(wc -c < "$b" | tr -d ' ')"
  kv body_sha256 "$(sha256sum "$b" | cut -d' ' -f1)"
  kv body_mtime_epoch "$(stat -c %Y "$b")"
  kv body_head256 "$(head -c 256 "$b" | tr -d '\0' | tr '\n' ' ' | cut -c1-256)"
  kv tls_protocol "$(grep -m1 'SSL connection using' "$v" | sed 's/.*SSL connection using //')"
  kv tls_subject "$(grep -m1 'subjectAltName' "$v" | sed 's/.*subjectAltName: //')"
  kv tls_issuer "$(grep -m1 '^ \* issuer:' "$v" | sed 's/.*issuer: //')"
  kv tls_cert_expire "$(grep -m1 'expire date:' "$v" | sed 's/.*expire date: //')"

  printf '%s\t%s\t%s\tGET\t%s\t%s\t%s\t%s\n' "$SEQ" "$host" "$role" "$path" "$tq" "$ts" "$td" >> "$LOG/run.log"
}

# ===================== 9 planned requests, of a 10 cap =======================

# 1. Resolution of the host the CSP names — the parking-namespace discriminator.
#    `*.carelink.{eu,com}` / `*.clcloud.eu` are wildcard parking DNS (docs/09 §4),
#    so "it resolves" is not evidence; the CNAME chain and the answer addresses
#    are. SENT IN ATTEMPT 1 and carried forward above — see the block there.

# 2. Control (b), sent FIRST among the HTTP requests: the recorded sibling on
#    the identical path, so the recorded 502 is anchored to this session (a 502
#    is not an absence — docs/09 §4, and area O read it as an origin-side DNS
#    failure).
get commoncore-trials.minimed.com ct-minimed-sibling "$OCCL" CONTROL-b-sibling-recorded-502

# 3-5. `commoncore.medtronic.com` — the sibling sharing the naming convention, and
#      the host whose recorded reading is disputed (docs/07: 403 on every route;
#      docs/00: CloudFront 502 origin DNS failure). Control first.
dns  commoncore.medtronic.com cc-medtronic-com-cn RESOLUTION-us-sibling
get  commoncore.medtronic.com cc-medtronic-com-absent "$ABSENT" CONTROL-certainly-absent-same-prefix
get  commoncore.medtronic.com cc-medtronic-com-ocl "$OCCL" CANDIDATE-us-sibling

# 6-7. `commoncore.medtronic.eu` — the EU half of the same brace. No absent-path
#      control is spent here (cap), so this cell is corroboration, not an
#      adjudicated reading; that limit is stated in the write-up.
dns commoncore.medtronic.eu cc-medtronic-eu-cn RESOLUTION-eu-sibling
get commoncore.medtronic.eu cc-medtronic-eu-ocl "$OCCL" CANDIDATE-eu-sibling

# 8-9. The host the question is about. Control first, then the candidate, on the
#      one path the repo already records for this family.
get commoncore-trials.medtronic.com ct-medtronic-absent "$ABSENT" CONTROL-certainly-absent-same-prefix
get commoncore-trials.medtronic.com ct-medtronic-ocl "$OCCL" CANDIDATE-the-host-this-area-is-about

# ---- ledger ---------------------------------------------------------------
# The per-request `.kv` files and the in-subshell timestamp/exit scratch are
# intermediate: the ledger is derived from the `.kv` set and then they are
# removed, so a re-run leaves the same tree this commit carries. No prior pass
# in this repo commits them (0 such files on origin/main before this one).
find "$LOG" -type f \( -name '*.kv' -o -name '*.v.exit' -o -name '*.v.status' \
  -o -name '*.v.t_done' -o -name '*.v.t_queued' -o -name '*.dns.t_done' \
  -o -name '*.dns.t_queued' -o -name '*.digexit' \) -delete

python3 - "$LOG" <<'PY'
import json, os, sys
log = sys.argv[1]
rows = []
for f in sorted(os.listdir(os.path.join(log, 'headers'))):
    if not f.endswith('.kv'):
        continue
    with open(os.path.join(log, 'headers', f)) as fh:
        rows.append({l.split('\t', 1)[0]: l.rstrip('\n').split('\t', 1)[1]
                     for l in fh if '\t' in l})
with open(os.path.join(log, 'results.jsonl'), 'w') as out:
    for r in rows:
        out.write(json.dumps(r) + '\n')
print(f'{len(rows)} ledger rows written')
PY

echo "requests sent: $SEQ of a $CAP cap"