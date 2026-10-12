#!/usr/bin/env python3
"""Render the Area X corpus (results.jsonl) as a table, and answer one question.

This script reports. It does not explain. It assigns no evidence class and
asserts no cause: it prints what came back off the wire and nothing else.

Four refusals, each one a guard against a specific way this repo has been
wrong (AGENTS.md section 6):

  1. curl_exit is asserted to be 0 on every row BEFORE any table is emitted. A
     non-zero exit means the response head and body may never have existed, so
     such a row is a hole in the evidence and never a vendor answer. The count
     of offending rows is printed, never silently skipped, and the run stops.
  2. Every field is resolved and TYPE-ASSERTED before it is compared. A lookup
     that could be None is never compared (section 6 item 3). The sentinel
     string "(none)" is rendered as ABSENT and is never hashed, never counted as
     a value, and never enters a digest group.
  3. http_status is asserted to be a digit string before it is compared to 200.
     The harness substitutes a prose string when there was no response head, so
     "== 200" on an unresolved value would be a silent truth claim.
  4. The all-zero sha256 is treated as the EMPTY-BODY MARKER, not as a value.
     Four rows here legitimately return a zero-byte body; grouping them by
     digest would present an artefact of emptiness as a shared content.

Usage: python3 verdict.py results.jsonl
"""
import json
import re
import sys
from datetime import datetime

NONE = "(none)"
EMPTY_SHA = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
ORIGIN_LITERAL = "https://example.invalid"
SELF = "https://example.invalid"


# ------------------------------------------------------------------ resolvers
def field(r, key):
    """Resolve one field to a printable token, asserting its type first.

    Never returns None. An absent header is the literal ABSENT, which cannot be
    confused with a value by any comparison below.
    """
    v = r.get(key)
    assert v is not None, f"seq {r['seq']}: field {key} is absent from the row"
    assert isinstance(v, str), f"seq {r['seq']}: field {key} is {type(v).__name__}, not str"
    return "ABSENT" if v == NONE else v


def status(r):
    """http_status, type-asserted. Digit string or an explicit non-status token."""
    v = r.get("http_status")
    assert v is not None, f"seq {r['seq']}: http_status is absent from the row"
    assert isinstance(v, str), f"seq {r['seq']}: http_status is {type(v).__name__}, not str"
    if v == NONE:
        return "NONE"
    if not v.isdigit():
        # The harness writes prose here when there was no response head.
        return f"NO-STATUS({v})"
    return v


def origin_sent(r):
    """Assert the sent_headers shape, then say whether an Origin went on the wire.

    Asserting the two legal shapes is the point: without it, "sent_headers !=
    '(none)'" would be a claim about a string, not about the wire.
    """
    s = r.get("sent_headers")
    assert s is not None, f"seq {r['seq']}: sent_headers is absent from the row"
    assert isinstance(s, str), f"seq {r['seq']}: sent_headers is {type(s).__name__}, not str"
    if s == NONE:
        return False
    assert s.startswith("Origin:" + ORIGIN_LITERAL + "|Access-Control-Request-Method:"), \
        f"seq {r['seq']}: unrecognised sent_headers shape {s!r}"
    return True


def digest_of(r):
    """(digest, is_empty_marker). The all-zero digest is a marker, not a value."""
    d = r.get("body_sha256")
    assert d is not None, f"seq {r['seq']}: body_sha256 is absent from the row"
    assert isinstance(d, str), f"seq {r['seq']}: body_sha256 is {type(d).__name__}, not str"
    if d == "":
        return "(empty string -- FAILURE MARKER)", True
    if d == EMPTY_SHA:
        return d, True
    return d, False


# ------------------------------------------------------------------ load
rows = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
print(f"rows read: {len(rows)}")
assert len(rows) == len({r["seq"] for r in rows}), "duplicate seq -- the probe ran twice"
assert [r["seq"] for r in rows] == list(range(1, len(rows) + 1)), "seq is not contiguous 1..N"

# ------------------------------------------------------------------ 1. transport
print("\n== 1. transport health (a non-zero curl_exit is a hole, never an answer) ==")
bad_exit = []
for r in rows:
    ec = r.get("curl_exit")
    assert ec is not None, f"seq {r['seq']}: curl_exit is absent from the row"
    assert isinstance(ec, int), f"seq {r['seq']}: curl_exit is {type(ec).__name__}, not int"
    if ec != 0:
        bad_exit.append(r)
print(f"  rows: {len(rows)}   curl_exit == 0: {len(rows) - len(bad_exit)}   "
      f"curl_exit != 0: {len(bad_exit)}")
for r in bad_exit:
    print(f"  HOLE seq={r['seq']} {r['host_tag']} {r['method']} {r['path']} exit={r['curl_exit']}")
print(f"  rows whose http_status is not a digit string: "
      f"{sum(1 for r in rows if not status(r).isdigit())}")
assert not bad_exit, "REFUSING to render a table over a transport failure"

# ------------------------------------------------------------------ 2. full table
print("\n== 2. every row, every field as received ==")
hdr = (f"{'seq':>3} {'host_tag':<10} {'method':<7} {'path':<46} {'sent_headers':<62} "
       f"{'st':<4} {'errortype-token':<32} {'x-ca-err':<8} {'acao':<6} {'acam':<6} "
       f"{'access_control_family_seen':<95} {'bytes':>6} {'sha256'}")
print(hdr)
print("-" * len(hdr))
for r in rows:
    st = status(r)
    d, empty = digest_of(r)
    ds = f"{d[:16]}..(EMPTY-BODY)" if empty else d
    print(f"{r['seq']:>3} {r['host_tag']:<10} {r['method']:<7} {r['path']:<46} "
          f"{field(r, 'sent_headers'):<62} {st:<4} {field(r, 'x_amzn_errortype_token'):<32} "
          f"{field(r, 'x_ca_err'):<8} {field(r, 'access_control_allow_origin'):<6} "
          f"{field(r, 'access_control_allow_methods'):<6} "
          f"{field(r, 'access_control_family_seen'):<95} {r['body_bytes']:>6} {ds}")

# ------------------------------------------------------------------ 3. the question
print("\n== 3. one question: for every row whose http_status is 200, does it carry ACAO? ==")
print("   grouped by whether an Origin was sent on that request")
print(f"   (the Origin literal is {ORIGIN_LITERAL} -- RFC 2606 reserved, never resolved)")
print()

groups = {True: [], False: []}
for r in rows:
    st = status(r)
    assert isinstance(st, str), "status() must return str"
    if not st.isdigit():
        continue
    if st != "200":
        continue
    groups[origin_sent(r)].append(r)

for sent in (False, True):
    label = "Origin SENT" if sent else "Origin NOT SENT"
    sel = groups[sent]
    with_acao = [r for r in sel if field(r, "access_control_allow_origin") != "ABSENT"]
    without = [r for r in sel if field(r, "access_control_allow_origin") == "ABSENT"]
    print(f"  {label}: {len(sel)} rows with http_status 200")
    print(f"    carries ACAO:        {len(with_acao)}  seq {[r['seq'] for r in with_acao]}")
    print(f"    carries no ACAO:     {len(without)}  seq {[r['seq'] for r in without]}")
    for r in sel:
        acao = field(r, "access_control_allow_origin")
        mark = "ACAO" if acao != "ABSENT" else "no ACAO"
        print(f"      seq {r['seq']:>2} {r['host_tag']:<10} {r['method']:<7} {mark:<8} "
              f"acao={acao}")
    print()

# ------------------------------------------------------------------ 4. disagreements
print("\n== 4. rows where ACAO and http_status 200 DISAGREE ==")
disagree = []
for r in rows:
    st = status(r)
    acao = field(r, "access_control_allow_origin")
    is200 = st.isdigit() and st == "200"
    has_acao = acao != "ABSENT"
    if is200 and not has_acao:
        disagree.append((r, "200 but NO ACAO"))
    elif not is200 and has_acao:
        disagree.append((r, f"http_status {st} but ACAO PRESENT"))
print(f"  total disagreements: {len(disagree)}")
for r, why in disagree:
    print(f"    seq {r['seq']:>2} {r['host_tag']:<10} {r['method']:<7} {why:<34} "
          f"acao={field(r, 'access_control_allow_origin')}")
if not disagree:
    print("    none")

# ------------------------------------------------------------------ 5. digests
print("\n== 5. body digests grouped (the all-zero digest is an EMPTY-BODY marker) ==")
real, empty_rows = {}, []
for r in rows:
    d, empty = digest_of(r)
    nb = r.get("body_bytes")
    assert isinstance(nb, int), f"seq {r['seq']}: body_bytes is {type(nb).__name__}, not int"
    if empty:
        assert nb == 0, f"seq {r['seq']}: empty-body marker but body_bytes={nb}"
        empty_rows.append(r)
    else:
        assert nb > 0, f"seq {r['seq']}: non-empty digest but body_bytes={nb}"
        real.setdefault(d, []).append(r)
print(f"  zero-byte bodies (marker, not a value): {len(empty_rows)} "
      f"seq {[r['seq'] for r in empty_rows]}")
print(f"  distinct non-empty body digests: {len(real)}")
for d, rs in sorted(real.items(), key=lambda kv: -len(kv[1])):
    print(f"    {d}")
    print(f"      count {len(rs)}  seq {[r['seq'] for r in rs]}  "
          f"bytes {sorted({r['body_bytes'] for r in rs})}  "
          f"hosts {sorted({r['host'] for r in rs})}")

# ------------------------------------------------------------------ 6. spacing
print("\n== 6. same-host spacing, measured from run.log (not the harness's stated value) ==")
import os
log = os.path.join(os.path.dirname(os.path.abspath(sys.argv[1])), "run.log")
# Assert the target exists and is a file BEFORE reading it. A spacing section
# that silently parses nothing would report "no gaps" and read as a pass.
# (AGENTS.md section 6 item 6: never cite or read from a path that was assumed.)
assert os.path.exists(log), f"run.log not found at the expected sibling path: {log}"
assert os.path.isfile(log), f"expected a file at {log}, found a directory"
ts = []
for line in open(log):
    m = re.match(r"\[(\d{4}-\d\d-\d\dT[\d:.]+Z)\] \[(\d+)\] (\S+)", line)
    if m:
        # host_tag is "<host>-<NN>"; rsplit strips the per-request counter so
        # same-host gaps are actually computable.
        ts.append((int(m.group(2)), m.group(3).rsplit("-", 1)[0],
                   datetime.strptime(m.group(1), "%Y-%m-%dT%H:%M:%S.%fZ")))
print(f"  timestamped requests parsed from run.log: {len(ts)}")
last, gaps, short = {}, [], []
for seq, tag, t in ts:
    if tag in last:
        gap = (t - last[tag][1]).total_seconds()
        gaps.append((tag, seq, gap))
        if gap < 2.5:
            short.append((tag, seq, gap))
    last[tag] = (seq, t)
print(f"  same-host gaps measured: {len(gaps)}")
print(f"  gaps >= 2.5s: {sum(1 for _, _, g in gaps if g >= 2.5)}")
print(f"  gaps <  2.5s: {len(short)}")
if gaps:
    print(f"  single measured MINIMUM same-host gap: {min(g for _, _, g in gaps):.3f}s")
    lo = min(gaps, key=lambda x: x[2])
    print(f"    at {lo[0]} -> request {lo[1]}: {lo[2]:.3f}s")
if short:
    print("  GAPS BELOW 2.5s, listed and not rounded away:")
    for tag, seq, gap in short:
        print(f"    {tag} -> request {seq}: {gap:.3f}s")
else:
    print("  no same-host gap fell below 2.5s")
print(f"\nrequests issued: {len(rows)}   cap: 26")