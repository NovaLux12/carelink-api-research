#!/usr/bin/env python3
"""census.py — zero requests. How many recorded 404s on the four clinic hosts carry a
Content-Type, and how many carry a body?

Why this exists: FINDINGS.md §5 rests on the claim that NO stock Apache 404 is
recorded anywhere on this host family, so an absence under /hcp/ is answered by
something under application control. That claim must be re-derivable, and the
committed ledgers carry at least six row schemas (area AG §3 records the set), so a
single field read undercounts. Every schema is attempted per row:

  host      : host | hostname | url (parsed) | headers.host
  status    : http_status | status | code | headers[':status']
  ctype     : content_type | ctype | headers['content-type'] | disc_headers[...]
  bytes     : body_bytes | bytes | size | len of a retained body (not available)

Counting rule: one row per line of a committed results.jsonl / requests ledger that
resolves to a status of 404 on one of the four hosts. Rows whose host or status does
not resolve are counted as unresolved and reported separately — a row this script
cannot read is NOT silently counted as "no Content-Type".

Usage: python3 census.py [REPO_ROOT]
"""
import glob
import json
import os
import sys
import urllib.parse

HOSTS = {
    "carelink.medtronic.com",
    "carelink.medtronic.eu",
    "carelink-support.medtronic.com",
    "carelinkhp.minimed.eu",
}
ROOT = sys.argv[1] if len(sys.argv) > 1 else "."


def pick(d, *names):
    for n in names:
        if n in d and d[n] not in (None, ""):
            return d[n]
    return None


def host_of(row):
    h = pick(row, "host", "hostname")
    if h:
        return str(h)
    u = pick(row, "url", "uri")
    if u:
        return urllib.parse.urlsplit(str(u)).hostname or ""
    hh = row.get("headers") or {}
    return str(hh.get("host", ""))


def status_of(row):
    s = pick(row, "http_status", "status", "code", "status_code")
    if s is not None:
        return str(s)
    hh = row.get("headers") or {}
    return str(hh.get(":status", ""))


def ctype_of(row):
    c = pick(row, "content_type", "ctype", "content-type")
    if c is not None:
        # Several ledgers record absence as the literal sentinel "(none)" or "-" in
        # the content_type FIELD. Counting that string as a Content-Type inverts the
        # finding, so the sentinel is mapped to "(absent)" explicitly.
        return "(absent)" if str(c).strip() in ("(none)", "-", "", "none", "None") else str(c)
    for key in ("headers", "disc_headers"):
        hh = row.get(key) or {}
        if isinstance(hh, dict):
            for k, v in hh.items():
                if k.lower() == "content-type":
                    return str(v)
    return "(absent)"


def bytes_of(row):
    b = pick(row, "body_bytes", "bytes", "size", "content_length")
    return b if b is not None else "?"


files = sorted(glob.glob(os.path.join(ROOT, "findings-log", "**", "*.jsonl"), recursive=True))
rows_total = 0
four_404 = []
unresolved = 0
per_file = {}
for f in files:
    for line in open(f, errors="replace"):
        line = line.strip()
        if not line.startswith("{"):
            continue
        rows_total += 1
        try:
            r = json.loads(line)
        except Exception:
            continue
        h = host_of(r)
        if h not in HOSTS:
            continue
        st = status_of(r)
        if st != "404":
            continue
        ct = ctype_of(r)
        if ct == "(absent)":
            # distinguish "we read the row and there is no CT" from "we could not read it"
            hh = r.get("headers")
            if not isinstance(hh, dict) and pick(r, "content_type", "ctype") is None:
                unresolved += 1
        four_404.append((h, ct, bytes_of(r), os.path.relpath(f, ROOT)))
    per_file[f] = per_file.get(f, 0)

print(f"ledger files walked            : {len(files)}")
print(f"json rows walked               : {rows_total}")
print(f"404 rows on the four hosts     : {len(four_404)}")
print(f"rows whose CT could not be read: {unresolved}")
print()
agg = {}
for h, ct, b, f in four_404:
    agg[(h, ct, str(b))] = agg.get((h, ct, str(b)), 0) + 1
for k, v in sorted(agg.items()):
    print(f"{v:>3}  host={k[0]:32} content-type={k[1]:12} bytes={k[2]}")
print()
withct = [x for x in four_404 if x[1] != "(absent)"]
withbody = [x for x in four_404 if str(x[2]) not in ("0", "?", "None")]
print(f"404s carrying a Content-Type   : {len(withct)} of {len(four_404)}")
print(f"404s carrying a body           : {len(withbody)} of {len(four_404)}")
print()
print("files contributing a 404 row:")
seen = sorted({x[3] for x in four_404})
for s in seen:
    print("  " + s)

# ---- POSITIVE CONTROL, because a check that cannot fail is not evidence. --------
# If ctype_of() returned "(absent)" for everything, the 31-of-31 result would be an
# artefact of the reader rather than a fact about the hosts. So read the 200 rows on
# the same four hosts through the same function: they must carry a Content-Type.
pos = 0
pos_absent = 0
for f in files:
    for line in open(f, errors="replace"):
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            r = json.loads(line)
        except Exception:
            continue
        if host_of(r) not in HOSTS:
            continue
        if status_of(r) != "200":
            continue
        pos += 1
        if ctype_of(r) == "(absent)":
            pos_absent += 1
print()
print(f"POSITIVE CONTROL — 200 rows on the same four hosts: {pos}")
print(f"  of those, Content-Type read as absent: {pos_absent}")
print(f"  VERDICT: {'reader discriminates' if pos_absent < pos else 'READER IS BLIND — the 404 result above is an artefact'}")

# ---- PER-FILE CAPABILITY, the check that makes 0-of-31 non-artefactual. --------
# A ledger that never captured headers would report "(absent)" for a 404 while being
# unable to see a Content-Type at all. So for every file that contributes a 404 row,
# ask whether the SAME reader sees a Content-Type on that file's 200 rows. A file
# with 0-of-N 200s carrying a type cannot testify about its 404s and must be named.
print()
print("PER-FILE CAPABILITY — can each contributing ledger record a Content-Type at all?")
cap_of = {}
for f in files:
    r404 = r200 = c200 = 0
    for line in open(f, errors="replace"):
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            r = json.loads(line)
        except Exception:
            continue
        if host_of(r) not in HOSTS:
            continue
        st = status_of(r)
        if st == "404":
            r404 += 1
        elif st == "200":
            r200 += 1
            if ctype_of(r) != "(absent)":
                c200 += 1
    if r404:
        cap_of[os.path.relpath(f, ROOT)] = (r404, r200, c200)
blind = [k for k, v in cap_of.items() if v[1] and v[2] == 0]
for k, (n4, n2, c2) in sorted(cap_of.items()):
    v = "capable" if c2 else ("UNCAPTURED — cannot testify" if n2 else "no 200s in file")
    print(f"  {k}: {n4} 404 row(s); its {n2} 200 row(s), {c2} carry a type — {v}")
print()
print(f"contributing files that cannot testify about Content-Type: {len(blind)}")
print(f"  {'none — 0-of-31 stands' if not blind else blind}")

