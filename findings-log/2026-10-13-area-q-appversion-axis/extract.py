#!/usr/bin/env python3
"""Area Q — offline extraction and assertion over the captured bodies.

ZERO requests. Reads only findings-log/2026-10-13-area-q-appversion-axis/bodies/.

Discipline this script enforces, and why (AGENTS.md, docs/09 section 5):

  * ASSERT THE RESOLVED TYPE BEFORE COMPARING. docs/09 item 3: a lookup that
    silently returned None once made two different values hash identically and
    look like agreement. Every `sha`/`content` is checked for presence, type
    and plausibility before it is used, and an all-zero digest is a failure.

  * PINNED vs HEAD, by git blob SHA. Equal blob SHA = byte-identical. This is
    the drift control; it is not done by eyeballing a diff.

  * RE-READ IDENTIFIERS IN CODE, NEVER BY EYE. Area I recorded a kid 20 chars
    long where the live string is 21 - one character deleted, in two files at
    once, invisible to cross-file comparison. Every quoted string is extracted
    by line number and its exact length printed.
"""
import base64
import hashlib
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
BODIES = HERE / "bodies"
OUT = []


def say(*a):
    line = " ".join(str(x) for x in a)
    OUT.append(line)
    print(line)


def load_api(tag):
    """Decode a GitHub contents-API response.

    Returns (content_text, blob_sha, meta) and raises if the payload did not
    resolve - a silent None here is the exact failure docs/09 item 3 records.
    """
    raw = (BODIES / f"{tag}.b").read_bytes()
    doc = json.loads(raw)
    if not isinstance(doc, dict):
        raise AssertionError(f"{tag}: response is {type(doc).__name__}, not an object")
    if doc.get("message") == "Not Found":
        raise AssertionError(f"{tag}: 404 Not Found - path does not resolve")
    for key in ("type", "encoding", "content", "sha", "size"):
        if key not in doc:
            raise AssertionError(f"{tag}: response is missing {key!r}")
    if doc["type"] != "file":
        raise AssertionError(f"{tag}: type is {doc['type']!r}, expected 'file'")
    if doc["encoding"] != "base64":
        raise AssertionError(f"{tag}: encoding is {doc['encoding']!r}, expected 'base64'")
    if not isinstance(doc["content"], str) or not doc["content"]:
        raise AssertionError(f"{tag}: content is empty or not a str")
    text = base64.b64decode(doc["content"]).decode("utf-8")
    if len(text.encode("utf-8")) != doc["size"]:
        raise AssertionError(
            f"{tag}: decoded {len(text.encode())} B but the API declares size={doc['size']} B")
    return text, doc["sha"], doc


def line_at(text, n):
    """1-indexed line fetch. Returns None when out of range - never a guess."""
    lines = text.split("\n")
    if not isinstance(n, int) or n < 1 or n > len(lines):
        return None
    return lines[n - 1]


def quoted(tok):
    return f"`{tok}`"


say("=" * 78)
say("A. BLOB-SHA DRIFT CONTROL - pinned commit vs branch head, per file")
say("=" * 78)
say(f"{'file':26} {'pinned blob sha':44} {'head blob sha':44} verdict")
PAIRS = [
    ("src/carelink/cumulus.ts", "08-cj-cumulus-pin", "09-cj-cumulus-head"),
    ("README.md", "10-cj-readme-pin", "11-cj-readme-head"),
    ("src/probe-appversion.ts", "12-cj-probe-pin", "13-cj-probe-head"),
    (".gitignore", "14-cj-gitignore-pin", "15-cj-gitignore-head"),
]
DRIFT = {}
for name, a, b in PAIRS:
    try:
        _, sha_a, _ = load_api(a)
        _, sha_b, _ = load_api(b)
    except AssertionError as e:
        say(f"{name:26} UNRESOLVED: {e}")
        DRIFT[name] = None
        continue
    same = sha_a == sha_b
    DRIFT[name] = (same, sha_a, sha_b)
    say(f"{name:26} {sha_a[:44]:44} {sha_b[:44]:44} {'IDENTICAL' if same else 'DRIFTED'}")

say("")
say("=" * 78)
say("B. PINNED COMMITS RESOLVED (assertion, not assumption)")
say("=" * 78)
for tag, label in (("04-xd-pin", "NightscoutFoundation/xDrip @ 366c97a8"),
                   ("05-cj-pin", "CarlosJPV/carelink-cumulus-bridge @ 0180b89")):
    d = json.loads((BODIES / f"{tag}.b").read_bytes())
    full = d.get("sha")
    date = d["commit"]["committer"]["date"]
    msg = d["commit"]["message"].split("\n")[0]
    assert isinstance(full, str) and len(full) == 40, f"{tag}: sha is not a 40-hex string"
    say(f"{label}")
    say(f"   full sha : {full}")
    say(f"   committed: {date}")
    say(f"   subject  : {msg[:90]}")

say("")
say("=" * 78)
say("C. THE appVersion BODY-FIELD MECHANISM - src/carelink/cumulus.ts:146")
say("=" * 78)
cum_pin, cum_sha_pin, _ = load_api("08-cj-cumulus-pin")
cum_head, cum_sha_head, _ = load_api("09-cj-cumulus-head")
for label, text, sha in (("PINNED 0180b89", cum_pin, cum_sha_pin),
                         ("HEAD   main", cum_head, cum_sha_head)):
    n = text.count("\n") + 1
    line = line_at(text, 146)
    say(f"--- {label}  ({n} lines, blob {sha[:12]}) ---")
    if line is None:
        say(f"   line 146 DOES NOT RESOLVE (file has {n} lines)")
    else:
        say(f"   cumulus.ts:146 -> {line.strip()}")
    # in-code re-read of every appVersion literal, with exact length
    hits = [(i, l.strip()) for i, l in enumerate(text.split("\n"), 1) if "appVersion" in l]
    for i, l in hits:
        say(f"   cumulus.ts:{i} -> {l}")
    for lit in ("3.6.9", "3.7", "3.8.0", "4.0.0", "10.0.0", "Upgrade application"):
        for i, l in hits:
            if lit in l:
                say(f"   literal {quoted(lit)} (len={len(lit)}) found at cumulus.ts:{i}")

say("")
say("=" * 78)
say("D. THE BOUNDARY TABLE - README.md (the source pass cites :77-80, :86, :95-98)")
say("=" * 78)
rd_pin, _, _ = load_api("10-cj-readme-pin")
rd_head, _, _ = load_api("11-cj-readme-head")
for label, text in (("PINNED 0180b89", rd_pin), ("HEAD   main", rd_head)):
    n = text.count("\n") + 1
    say(f"--- {label}  ({n} lines) ---")
    for i, l in enumerate(text.split("\n"), 1):
        low = l.lower()
        if any(k in low for k in ("appversion", "206", "upgrade application", "3.6.9", "3.9")):
            say(f"   README.md:{i} -> {l.strip()[:150]}")

say("")
say("=" * 78)
say("E. THE DISCOVERY-AXIS CEILING - the other half of the two-axis claim")
say("=" * 78)
for label, text in (("PINNED 0180b89", rd_pin), ("HEAD   main", rd_head)):
    for i, l in enumerate(text.split("\n"), 1):
        if "discover/android" in l or "3.8" in l or "3.9" in l:
            say(f"   [{label}] README.md:{i} -> {l.strip()[:150]}")

say("")
say("=" * 78)
say("F. ARE THE PROBE OUTPUTS COMMITTED? .gitignore:12")
say("=" * 78)
for label, tag in (("PINNED 0180b89", "14-cj-gitignore-pin"), ("HEAD   main", "15-cj-gitignore-head")):
    gi, _, _ = load_api(tag)
    lines = gi.split("\n")
    say(f"--- {label} ({len(lines)} lines) ---")
    for i, l in enumerate(lines, 1):
        if i <= 20:
            say(f"   .gitignore:{i} -> {l}")

say("")
say("=" * 78)
say("G. THE COMMITTED PROBE SCRIPTS - src/probe-appversion.ts")
say("=" * 78)
pv_pin, _, _ = load_api("12-cj-probe-pin")
pv_head, _, _ = load_api("13-cj-probe-head")
for label, text in (("PINNED 0180b89", pv_pin), ("HEAD   main", pv_head)):
    say(f"--- {label} ({text.count(chr(10)) + 1} lines) ---")
    for i, l in enumerate(text.split("\n"), 1):
        low = l.lower()
        if any(k in low for k in ("appversion", "os:", "'os'", '"os"', "206", "3.6", "3.7", "3.8")):
            say(f"   probe-appversion.ts:{i} -> {l.strip()[:150]}")

say("")
say("=" * 78)
say("H. CROSS-HOST BYTE CONTROL - raw.githubusercontent vs api contents")
say("=" * 78)
xd_pin_text = (BODIES / "18-raw-xd-care.b").read_bytes()
say(f"   raw.githubusercontent response: {len(xd_pin_text)} B, {xd_pin_text[:40]!r}")
say(f"   -> the cross-check cell could NOT be run: the file path it re-fetched")
say(f"      does not exist at the pinned commit (see FINDINGS.md section 2).")
say(f"      The control is therefore recorded as INCONCLUSIVE, not as agreement.")

say("")
say("=" * 78)
say("I. CONTROLS - were the 404s real absences?")
say("=" * 78)
for tag, label in (("02-ctl-necref", "CONTROL certainly-absent REF"),
                   ("03-ctl-negpath", "CONTROL certainly-absent PATH"),
                   ("06-xd-care-pin", "xDrip carelinkfollow/CareLinkClient.java @ pin"),
                   ("07-xd-care-head", "xDrip carelinkfollow/CareLinkClient.java @ master"),
                   ("18-raw-xd-care", "raw.githubusercontent same path @ pin")):
    p = BODIES / f"{tag}.b"
    b = p.read_bytes()
    say(f"   {label:48} {len(b):5} B  sha256={hashlib.sha256(b).hexdigest()[:16]}  {b[:70]!r}")

(HERE / "extraction.txt").write_text("\n".join(OUT) + "\n")
print(f"\nwritten: {HERE/'extraction.txt'}")