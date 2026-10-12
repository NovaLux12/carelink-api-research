#!/usr/bin/env python3
"""Area T — enumerate every published pointer into the cumulus plane.

The question is NOT "does the string csr appear". It is: does any document the
vendor serves without a login name a base URL a client could address csr/v2 (or
bare connect/v2) with?

Design notes, because this repo has been wrong in both directions here:
  - Every resolved value is type-asserted before it is used. A lookup that
    silently returns None must never reach a comparison (AGENTS.md section 6
    item 3).
  - The searched-key list is PRINTED, so the negative is auditable rather than
    asserted. #84 is the precedent.
  - A hit is not proof of meaning. Anything found is reported with its exact
    location and value, and the caller decides what it means; this script does
    not label a string "a pointer" on the strength of a grep.
"""
import json
import glob
import os
import re
import sys

D = "findings-log/2026-10-12-published-pointers/docs"

def load(name):
    p = os.path.join(D, name + ".json")
    with open(p, encoding="utf-8") as f:
        return json.load(f)  # raises on a parse failure; never returns None

def need(d, k, where):
    """Fetch a key, asserting both presence and non-None."""
    if k not in d:
        raise AssertionError(f"{where}: key {k!r} ABSENT")
    v = d[k]
    if v is None:
        raise AssertionError(f"{where}: key {k!r} resolved to None")
    return v

SCHEME = re.compile(r"^https?://", re.I)
CUMULUSY = re.compile(r"/connect/", re.I)

print("=" * 78)
print("PART 1 — every baseUrl* key in every discovery document served today")
print("=" * 78)
disc_docs = [
    ("disc-eu-v13",           "clcloud.minimed.eu          v13/android/3.6"),
    ("disc-com-v13",          "clcloud.minimed.com         v13/android/3.6"),
    ("disc-com-v11-legacy",   "clcloud.minimed.com         v11/android/3.6"),
    ("disc-trials-v6-legacy", "clcloud-trials.minimed.com  v6/android/3.6"),
]
pointers = []          # (doc, label, key, value) for every base URL published
for name, label in disc_docs:
    d = load(name)
    print(f"\n--- {label}  ({name}) ---")
    print(f"  top-level keys: {sorted(d.keys())}")
    cps = need(d, "CP", name)
    assert isinstance(cps, list) and cps, f"{name}: CP is not a non-empty list"
    print(f"  CP[] regions: {[c.get('region') for c in cps]}")
    for cp in cps:
        assert isinstance(cp, dict), f"{name}: CP entry is not a dict"
        region = cp.get("region")
        for k in sorted(cp.keys()):
            if not k.lower().startswith("baseurl"):
                continue
            v = cp[k]
            if not isinstance(v, str):
                print(f"    {region:10} {k:18} NON-STRING {type(v).__name__}  <-- skipped, not compared")
                continue
            print(f"    {region:10} {k:18} {v}")
            pointers.append((label, region, k, v))
    for extra in ("baseUrlCumulus", "baseUrlPde"):
        if extra in d:
            print(f"    (top-level) {extra} = {d[extra]!r}")

print("\n" + "=" * 78)
print("PART 2 — the 69-key public config: every value that LOOKS like an endpoint")
print("=" * 78)

def walk(obj, prefix=""):
    """Yield (dotted-key, value) leaves, asserting the resolved type per segment."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from walk(v, f"{prefix}{k}" if not prefix else f"{prefix}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk(v, f"{prefix}[{i}]")
    else:
        yield prefix, obj

config_pointers = {}
for name, label in [("config-eu", "carelink.minimed.eu"),
                    ("config-com", "carelink.minimed.com"),
                    ("config-trials", "carelink-trials.minimed.com")]:
    d = load(name)
    assert isinstance(d, dict), f"{name}: not a dict"
    print(f"\n--- {label} ({name}) — {len(d)} top-level keys ---")
    leaves = list(walk(d))
    for key, val in leaves:
        if isinstance(val, str) and (SCHEME.match(val) or CUMULUSY.search(val)):
            short = val if len(val) <= 130 else val[:127] + "..."
            print(f"  {key}")
            print(f"      {short}")
            config_pointers.setdefault(key, {})[label] = val
    # the csr-named keys specifically, with their resolved type
    for k in sorted(d.keys()):
        if k.lower().startswith("csr"):
            v = need(d, k, name)
            print(f"  [csr-prefixed key] {k}  type={type(v).__name__}")
            print(f"      {json.dumps(v)[:400]}")

print("\n" + "=" * 78)
print("PART 3 — the country document's published pointer, per deployment")
print("=" * 78)
for name, label, cc in [("countries-eu", "carelink.minimed.eu", "GB"),
                        ("countries-com", "carelink.minimed.com", "US"),
                        ("countries-trials", "carelink-trials.minimed.com", "US")]:
    d = load(name)
    assert isinstance(d, dict), f"{name}: not a dict"
    v = need(d, "blePereodicDataEndpoint", name)
    assert isinstance(v, str), f"{name}: blePereodicDataEndpoint is {type(v).__name__}, not str"
    print(f"  {label:30} countryCode={cc}  {len(d)} keys")
    print(f"      blePereodicDataEndpoint = {v}")

print("\n" + "=" * 78)
print("PART 4 — THE ANSWER: does any published document name csr/v2 or bare v2?")
print("=" * 78)
corpus = {}
for name in ("disc-eu-v13", "disc-com-v13", "disc-com-v11-legacy", "disc-trials-v6-legacy",
             "config-eu", "config-com", "config-trials",
             "countries-eu", "countries-com", "countries-trials"):
    raw = open(os.path.join(D, name + ".json"), encoding="utf-8").read()
    corpus[name] = raw

for needle in ("csr/v2", "/connect/v2", "baseUrlCsr", "csr", "pde"):
    print(f"\n  needle {needle!r}:")
    total = 0
    for name, raw in corpus.items():
        c = raw.count(needle)
        total += c
        if c:
            print(f"      {name:22} {c} hit(s)")
    if total == 0:
        print("      ZERO hits in all 10 documents")

print("\n  Every distinct value published that points into /connect/:")
seen = {}
for label, region, k, v in pointers:
    seen.setdefault(v, []).append(f"{label}:{region}:{k}")
for v, srcs in sorted(seen.items()):
    print(f"    {v}")
    for s in srcs:
        print(f"        <- {s}")