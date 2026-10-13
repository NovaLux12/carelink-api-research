#!/usr/bin/env python3
"""Area M — classify every failed request by what the LEDGER had already proven
about that URL before it was sent, and count the failures per class.

WHY THIS SCRIPT EXISTS
---------------------
FINDINGS.md originally claimed "0 of the 20 requests against hosts known to be
covered ever failed". That was false, and a verifier found it from the ledger:
seq 50 and seq 53 query `carelink.minimed.eu` on `CC-MAIN-2018-39`, a host seq
42 had already returned 200 for **32.6 seconds earlier**. The claim was load
bearing — it was the reassurance that made the 28% failure rate survivable — and
it was published unlabelled in three places.

The fix is not to swap one hand-counted number for another. It is to state the
COUNTING RULE first (AGENTS.md §6 item 7: a count generalised from a subset,
with no counting rule recorded) and let this script produce the number.

THE RULE, applied in send order
-------------------------------
Only a **record-form** query (`output=json` without `showNumPages`) returns a
host list, so only a record-form query can prove anything about a specific host.
A `showNumPages` cell answers with `{"pages": N, "blocks": M}` and names no host
at all — reading its empty host set as "no captures" is the bug this script was
born catching, and it is why the first version of this file reported
`CC-MAIN-2018-39`'s own `minimed.eu` cell as proving absence.

  covered        an earlier record-form query in the same crawl returned 200
                 and its host set CONTAINS this host
  absent         an earlier query answered the definitive absence form for this
                 host on this crawl — the 404 `No Captures found`, a
                 `{"pages": 0}` count, or a record-form domain enumeration whose
                 host set is complete and does NOT contain this host
  indeterminate  neither. This includes every host no completed enumeration ever
                 named, every `showNumPages` cell, and every fabricated name —
                 including a fabricated sibling of a covered host, because
                 coverage of `www.medtronic.com` says nothing about
                 `zz-<fabricated>.medtronic.com`
  n/a            not an index-API query at all (a data.commoncrawl.org fetch)

A GATEWAY ERROR (502/503/504/400) is counted per class. The number that matters
is not "how many failed" but "how many failed on a host the ledger had already
proven covered" — that is the one that refutes "coverage protects you", and it
is the count a reader is most likely to check.

`--selftest` asserts the classifier is falsifiable. It feeds the classifier a
two-row ledger in which a covered host's query FAILS, and refuses to exit 0
unless the class comes back "covered"; it also asserts a fabricated sibling of
a covered host comes back "indeterminate", and that a `showNumPages` cell does
not mark its own domain absent. A classifier that cannot report the very cases
it exists to catch is not a classifier.

Exit 0 always. This counts; it does not gate.
"""
from __future__ import annotations

import json
import os
import re
import sys
from urllib.parse import parse_qs

HERE = os.path.dirname(os.path.abspath(__file__))
GATEWAY = {"502", "503", "504", "400"}
NOT_INDEX = "data.commoncrawl.org"


def params(path: str) -> dict:
    m = re.search(r"-index\?(.*)$", path)
    return parse_qs(m.group(1)) if m else {}


def p(path: str, key: str, default: str = "") -> str:
    return params(path).get(key, [default])[0]


def target(path: str) -> tuple[str, str, str, bool]:
    """Return (crawl, url, matchType, is_record_form)."""
    crawl = re.match(r"^/(CC-MAIN-[0-9A-Za-z-]+)-index\?", path)
    crawl = crawl.group(1) if crawl else path
    url = p(path, "url")
    mt = p(path, "matchType", "exact")
    record_form = p(path, "showNumPages") != "true"
    return crawl, url, mt, record_form


def host_of(url: str) -> str:
    m = re.match(r"^[a-z]+://([^/?#]+)", url, re.I)
    return (m.group(1) if m else url.split("/")[0]).lower()


def registrable(host: str) -> str:
    parts = host.split(".")
    return ".".join(parts[-2:]) if len(parts) > 2 else host


def body_of(row: dict) -> bytes:
    try:
        with open(os.path.join(HERE, "bodies", row["host_tag"] + ".b"), "rb") as fh:
            return fh.read()
    except OSError:
        return b""


def establishes_absence(row: dict) -> bool:
    """The definitive absence forms: the 404 body, or a zero-page count."""
    if row["http_status"] == "404":
        return b"No Captures found" in body_of(row)
    if row["http_status"] == "200" and p(row["path"], "showNumPages") == "true":
        return b'"pages": 0' in body_of(row)
    return False


def classify(rows: list[dict]) -> dict[int, str]:
    covered: dict[str, set[str]] = {}   # crawl -> hosts a 200 record query returned
    absent: set[tuple[str, str]] = set()  # (crawl, host) proven absent
    complete: set[str] = set()         # crawls where a domain enumeration finished
    classes: dict[int, str] = {}

    for r in sorted(rows, key=lambda x: x["seq"]):
        if r["host"] == NOT_INDEX:
            classes[r["seq"]] = "n/a"
            continue
        crawl, url, mt, record_form = target(r["path"])
        host = host_of(url)

        # --- what did the ledger already know, at the instant of this send?
        if host in covered.get(crawl, set()):
            classes[r["seq"]] = "covered"
        elif (crawl, host) in absent:
            classes[r["seq"]] = "absent"
        elif crawl in complete and mt == "domain":
            # a completed enumeration of this registrable domain named every
            # host it holds; this one was not among them
            classes[r["seq"]] = "absent"
        else:
            classes[r["seq"]] = "indeterminate"

        # --- what does this row add?
        if r["http_status"] == "200" and record_form and r["distinct_hosts"]:
            covered.setdefault(crawl, set()).update(r["distinct_hosts"])
            if mt == "domain":
                complete.add(crawl)
                reg = registrable(host)
                for known in list(covered.get(crawl, set())):
                    if registrable(known) == reg and known not in r["distinct_hosts"]:
                        absent.add((crawl, known))
        if establishes_absence(r):
            absent.add((crawl, host))
    return classes


def main() -> int:
    rows = [json.loads(l) for l in open(os.path.join(HERE, "results.jsonl"), encoding="utf-8")]
    classes = classify(rows)
    fails = [r for r in rows if r["http_status"] in GATEWAY]
    print(f"ledger rows: {len(rows)}   gateway errors (502/503/504/400): {len(fails)}\n")
    tally: dict[str, list[int]] = {}
    for r in fails:
        tally.setdefault(classes[r["seq"]], []).append(r["seq"])
    for k in ("covered", "absent", "indeterminate", "n/a"):
        s = sorted(tally.get(k, []))
        if s:
            print(f"  {k:<15} {len(s):>2}  seq {s}")
    print(f"  {'TOTAL':<15} {len(fails):>2}\n")
    print("  the three rows the correction turned on:")
    by = {r["seq"]: r for r in rows}
    t50 = params(by[50]["path"])
    from datetime import datetime
    fmt = "%Y-%m-%dT%H:%M:%S.%fZ"
    d = (datetime.strptime(by[50]["t_sent"], fmt)
         - datetime.strptime(by[42]["t_sent"], fmt)).total_seconds()
    for s in (42, 50, 53):
        r = by[s]
        print(f"    seq{s:>3} {r['t_sent']} {r['http_status']} "
              f"class={classes[s]:<14} hosts={r['distinct_hosts']}")
    print(f"    seq 50 asked for a host seq 42 had proven covered "
          f"{d:.1f} s earlier -> {t50.get('url')}")
    return 0


def _selftest() -> int:
    fails = []

    # (1) a failure on a proven-covered host must classify as covered
    rows = [
        {"seq": 1, "host": "index.commoncrawl.org", "http_status": "200", "host_tag": "t1",
         "path": "/CC-MAIN-2018-39-index?url=minimed.eu&output=json&matchType=domain",
         "distinct_hosts": ["carelink.minimed.eu", "minimed.eu"]},
        {"seq": 2, "host": "index.commoncrawl.org", "http_status": "504", "host_tag": "t2",
         "path": "/CC-MAIN-2018-39-index?url=carelink.minimed.eu&output=json&matchType=host",
         "distinct_hosts": []},
    ]
    c = classify(rows)
    if c[2] != "covered":
        fails.append(f"a failure on a host an earlier row proved covered "
                     f"classified {c[2]!r}, not 'covered'")

    # (2) a fabricated sibling of a covered host must NOT inherit coverage
    rows[1] = {**rows[1],
               "path": "/CC-MAIN-2018-39-index?url=zz-fabricated.medtronic.com&output=json&matchType=host"}
    rows[0] = {**rows[0],
               "path": "/CC-MAIN-2018-39-index?url=medtronic.com&output=json&matchType=domain",
               "distinct_hosts": ["www.medtronic.com"]}
    c = classify(rows)
    if c[2] != "indeterminate":
        fails.append(f"a fabricated sibling inherited coverage "
                     f"({c[2]!r}); coverage of one host proves nothing about another")

    # (3) a showNumPages cell names no host and must not mark its own domain absent
    rows = [
        {"seq": 1, "host": "index.commoncrawl.org", "http_status": "200", "host_tag": "t3",
         "path": "/CC-MAIN-2018-39-index?url=minimed.eu&output=json&showNumPages=true&matchType=domain",
         "distinct_hosts": []},
        {"seq": 2, "host": "index.commoncrawl.org", "http_status": "504", "host_tag": "t4",
         "path": "/CC-MAIN-2018-39-index?url=minimed.eu&output=json&matchType=host",
         "distinct_hosts": []},
    ]
    c = classify(rows)
    if c[2] == "absent":
        fails.append("a showNumPages cell with a non-zero page count marked its "
                     "own domain absent — it names no host at all")

    if fails:
        for f in fails:
            print(f"  !! {f}")
        print("SELFTEST FAIL — the classifier cannot be trusted on the cases it "
              "exists to catch; publish no count from it.")
        return 1
    print("SELFTEST PASS — the classifier reports 'covered' for a failure on a "
          "proven-covered host, refuses to let a fabricated sibling inherit "
          "coverage, and is not fooled by a host-less count cell.")
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(_selftest())
    sys.exit(main())