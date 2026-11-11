#!/usr/bin/env python3
"""Area AQ — re-derive every published figure from results.jsonl at ZERO requests.

Usage:  python3 verify.py [--quiet]

Re-derives, from the ledger alone:
  1. the row count and that it equals the cap (24);
  2. both controls on all three hosts, to status + bytes + full digest;
  3. the 3 × 3 question matrix (fabricated sibling vs real leaf per base per host);
  4. the per-subtree verdict implied by the matrix, under the stated rule;
  5. the spacing floor on clock A and the mtime evidence for clock B;
  6. the gap count against sum(rows_per_host - 1) after grouping by host and sorting
     by seq — never zip() over an interleaved file.

Exit 0 when every assertion holds, 1 otherwise. Prints each assertion.
"""
import sys, json, os, itertools
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, "results.jsonl")

CAP = 24
DIGEST_LIVE = "d551247201fc8fc27dee1ae62538455ea04258855f1880443176930399875a7a"
DIGEST_ABSENT = "f249b63cb2fcb66b47e86f906c98f8fd912e82dd035b4e53d7e72fc1960cfd16"
DELAY = 2.5
HOSTS = ["clcloud.minimed.com", "clcloud.minimed.eu", "clcloud-trials.minimed.com"]
# (base, label) for the three subtrees under test
BASES = [
    ("/connect/csr/v2", "csr/v2"),
    ("/connect/v2", "bare v2"),
    ("/connect/carepartner/v6", "v6"),
]

fails = []
def check(cond, msg):
    print(("  ok   " if cond else "  FAIL ") + msg)
    if not cond:
        fails.append(msg)

rows = []
with open(LEDGER) as fh:
    for line in fh:
        if line.strip():
            rows.append(json.loads(line))

print("--- 1. accounting ---")
check(len(rows) == CAP, f"ledger holds {len(rows)} rows, cap {CAP}")
check([r["seq"] for r in rows] == list(range(1, CAP + 1)),
      "seq contiguous 1..%d" % CAP)
check(all(r["curl_exit"] == 0 for r in rows),
      "every curl_exit == 0 (no failures, no retries)")
check(all(r["method"] in ("GET", "OPTIONS") for r in rows),
      "methods are GET/OPTIONS only — no POST")
check(sum(1 for r in rows if r["method"] == "GET") == 6,
      "6 GETs (the two controls on three hosts), 18 empty-body OPTIONS")

print("--- 2. controls (gates) on every host ---")
for h in HOSTS:
    live = [r for r in rows if r["host"] == h and r["tag"].startswith("c1-")]
    absent = [r for r in rows if r["host"] == h and r["tag"].startswith("c2-")]
    check(len(live) == 1 and live[0]["http_status"] == "401"
          and live[0]["body_bytes"] == 36 and live[0]["body_sha256"] == DIGEST_LIVE,
          f"{h} control-live: 401 / 36 B / d5512472…")
    check(len(absent) == 1 and absent[0]["http_status"] == "403"
          and absent[0]["body_bytes"] == 42 and absent[0]["body_sha256"] == DIGEST_ABSENT,
          f"{h} control-absent: 403 / 42 B / f249b63c… (full digest)")

print("--- 3. the 3 x 3 question matrix ---")
def one(host, tag):
    got = [r for r in rows if r["host"] == host and r["tag"] == tag]
    assert len(got) == 1, (host, tag, len(got))
    return got[0]

verdicts = {}
for host in HOSTS:
    slug = host.replace(".", "-")
    for base, label in BASES:
        kind = "csr" if label == "csr/v2" else ("v2" if label == "bare v2" else "v6")
        fab = one(host, f"q-{slug}-{kind}-fab")
        leaf = one(host, f"q-{slug}-{kind}-leaf")
        absent_shape = (fab["http_status"] == "403"
                        and fab["body_bytes"] == 42
                        and fab["body_sha256"] == DIGEST_ABSENT
                        and fab["acao"] == "(none)")
        live_shape = (leaf["http_status"] == "200"
                      and leaf["body_bytes"] == 0
                      and leaf["acao"] == "*"
                      and leaf["errortype"] == "(none)")
        check(absent_shape,
              f"{host} {label}: fabricated OPTIONS -> {fab['http_status']} "
              f"{fab['body_bytes']}B {fab['body_sha256'][:8]} ACAO={fab['acao']}")
        check(live_shape,
              f"{host} {label}: real leaf OPTIONS -> {leaf['http_status']} "
              f"{leaf['body_bytes']}B ACAO={leaf['acao']} ACAM={leaf['acam']}")
        # the stated rule, applied mechanically
        if live_shape and absent_shape:
            v = "PER-ROUTE — the verdict's OPTIONS half STANDS"
        elif live_shape and not absent_shape and fab["http_status"] == "200":
            v = "SUBTRACE-WIDE preflight — the verdict FALLS to 'no GET route'"
        else:
            v = "INCONCLUSIVE"
        verdicts[(host, label)] = v

print("--- 4. verdicts implied by the matrix ---")
for host in HOSTS:
    for base, label in BASES:
        print(f"       {label:9s} {host:30s} {verdicts[(host, label)]}")
for k, v in verdicts.items():
    check(v.startswith("PER-ROUTE"), f"{k[1]} on {k[0]}: {v.split(' —')[0]}")

print("--- 5. the corrupt-timestamp class, declared before it is used ---")
def ts(s):
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.%fZ").timestamp()

# Rows whose t_done precedes t_sent carry an impossible duration. docs/09 §4 records this
# class; the cause is NOT established here and is not asserted. They are named, counted,
# and excluded from clock A's floor rather than silently averaged in.
corrupt = sorted(r["seq"] for r in rows if ts(r["t_done"]) < ts(r["t_sent"]))
check(len(corrupt) == 4, f"{len(corrupt)} rows carry t_done < t_sent: {corrupt}")
# On those rows the fields are mutually inconsistent — there is no ordering of t_sent,
# t_done and body_mtime that satisfies program order. The cause is NOT established here
# (docs/09 §4's known class) and is not asserted. Consequence: these 4 rows' `date`-derived
# fields are unusable as spacing evidence, and the figures below say which gaps that costs.
check(all(ts(r["t_sent"]) > float(r["body_mtime"]) for r in rows if r["seq"] in corrupt),
      "on all 4, t_sent reads LATER than the response body's own kernel mtime — impossible in "
      "program order, so t_sent is not a trustworthy clock reading on these rows")
check(all(float(r["body_mtime"]) >= ts(r["t_queued"]) for r in rows),
      "on every row body_mtime >= t_queued, so every body was written after its request was queued")

print("--- 6. spacing, clock A (t_sent) ---")

# group by host and sort by seq, THEN pair — zip() over the interleaved ledger would
# silently skip every cross-host boundary pair.
by_host = {}
for r in rows:
    by_host.setdefault(r["host"], []).append(r)
for h in by_host:
    by_host[h].sort(key=lambda r: r["seq"])

gaps = []
for h, rs in by_host.items():
    for a, b in zip(rs, rs[1:]):
        gaps.append((a["seq"], b["seq"], ts(b["t_sent"]) - ts(a["t_sent"])))

expected = sum(len(v) - 1 for v in by_host.values())
check(len(gaps) == expected,
      f"gap count {len(gaps)} == sum(rows_per_host - 1) == {expected} "
      f"(rows/host {[len(by_host[h]) for h in HOSTS]})")
check(all(g > 0 for *_, g in gaps),
      f"0 negative t_sent gaps (range {min(g for *_,g in gaps):.3f}–{max(g for *_,g in gaps):.3f} s)")

# A gap is only a spacing claim if BOTH endpoints have sane timestamps. Six of the 21 gaps
# touch a corrupt row; the other 15 are the clock-A floor, and that is the figure published.
clean = [(a, b, g) for a, b, g in gaps if a not in corrupt and b not in corrupt]
dirty = [(a, b, g) for a, b, g in gaps if a in corrupt or b in corrupt]
check(len(clean) == 15 and len(dirty) == 6,
      f"{len(clean)} clean gaps + {len(dirty)} touching a corrupt row = {len(gaps)}")
floor = min(g for *_, g in clean)
check(floor >= DELAY, f"clock A floor over CLEAN gaps {floor:.3f} s >= {DELAY} s ({len(clean)} gaps)")
sub = [(a, b, g) for a, b, g in gaps if g < DELAY]
# A sub-2.5 s t_sent gap that ends on a corrupt row is a reading artefact, not a spacing
# event. On those two the clock-B evidence decides it: the kernel mtime gap across the same
# pair is quoted below, and it is over the rule.
mg_by_pair = {}
for h, rs in by_host.items():
    for a, b in zip(rs, rs[1:]):
        mg_by_pair[(a["seq"], b["seq"])] = float(b["body_mtime"]) - float(a["body_mtime"])
check(len(sub) == 2 and all(a in corrupt for a, b, g in sub)
      and all(mg_by_pair[(a, b)] >= DELAY for a, b, g in sub),
      f"the only 2 sub-{DELAY}s t_sent gaps are {[(a, b) for a, b, _ in sub]}, each STARTING on a "
      f"corrupt row; the kernel-mtime gap across the same pairs is "
      + ", ".join(f"{mg_by_pair[(a,b)]:.3f} s" for a, b, _ in sub)
      + f" — both >= {DELAY} s, so no delay rule was breached on either")

print("--- 7. spacing, clock B (kernel body mtime) ---")
mt = [r["body_mtime"] for r in rows]
check(all(float(m) > 0 for m in mt), "every row carries a non-zero body_mtime")
distinct = len(set(mt))
check(distinct == len(mt), f"{distinct} distinct mtimes across {len(mt)} rows — one clock per request")
inside = sum(1 for r in rows if ts(r["t_sent"]) <= float(r["body_mtime"]) <= ts(r["t_done"]))
check(inside == len(rows) - 4,
      f"{inside} of {len(rows)} mtimes fall inside t_sent..t_done; the 4 outside are exactly "
      f"the corrupt rows {sorted(r['seq'] for r in rows if not (ts(r['t_sent']) <= float(r['body_mtime']) <= ts(r['t_done'])))} "
      f"— the same 4, so the mtime is consistent with the rows read as 't_sent corrupt'")
mgaps = []
for h, rs in by_host.items():
    for a, b in zip(sorted(rs, key=lambda r: r["seq"]), sorted(rs, key=lambda r: r["seq"])[1:]):
        mgaps.append(float(b["body_mtime"]) - float(a["body_mtime"]))
check(min(mgaps) >= DELAY, f"clock B floor {min(mgaps):.3f} s >= {DELAY} s over {len(mgaps)} gaps")
check(len(mgaps) == expected, f"clock B gap count {len(mgaps)} == {expected}")

print()
if fails:
    print(f"VERIFY FAILED — {len(fails)} assertion(s)")
    sys.exit(1)
print("VERIFY OK — every published figure re-derives from results.jsonl at zero requests")
