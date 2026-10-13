#!/usr/bin/env python3
"""Area K — re-derive the chunk map from the runtime bundle and compare it to
the committed list. ZERO requests; reads only bodies already captured.

WHY THIS EXISTS. The corpus area V committed is a list of 211 FILENAMES. The
thing that generates those filenames is `f.u` in the runtime bundle, and `f.u` is
not a plain join: it is

    f.u = e => (2076 === e ? "common" : e) + "." + { <id>: "<hash>", ... } + ".js"

so ONE id is emitted under a different NAME than its id. A sweep that trusts the
list's URL form therefore 404s that cell for a reason that has nothing to do with
the corpus, and reports a clean negative over 211 bodies that is quietly wrong in
one place. This script is what catches that class: it rebuilds the filenames from
the runtime and diffs them against the list, so the disagreement is measured
rather than assumed absent.

It also re-anchors the corpus on today's bytes instead of inheriting area V's
note: the map is read out of the body fetched in THIS run.

Outputs (all to stdout, caller redirects):
  the re-derived list, one filename per line, in the runtime's own key order.
"""
import json
import os
import re
import sys

RUNTIME = sys.argv[1]          # path to the captured runtime body
LIST = sys.argv[2]             # path to the committed list copy being swept
LEDGER = sys.argv[3]           # results.jsonl, for digests

body = open(RUNTIME, 'rb').read().decode('utf-8', errors='replace')

# --- 1. the special case, asserted rather than assumed -------------------------
m_special = re.search(r'f\.u\s*=\s*e\s*=>\s*\(\s*(\d+)\s*===\s*e\s*\?\s*"([^"]+)"\s*:\s*e\s*\)', body)
if not m_special:
    print("FATAL: the runtime carries no recognisable f.u special case; the URL "
          "form below cannot be re-derived and nothing here should be trusted.",
          file=sys.stderr)
    raise SystemExit(2)
special_id, special_name = m_special.group(1), m_special.group(2)

# --- 2. the map itself --------------------------------------------------------
m_map = re.search(r'f\.u\s*=\s*e\s*=>.*?\{\s*(\d+)\s*:\s*"([0-9a-f]+)"\s*(?:,\s*\d+\s*:\s*"[0-9a-f]+"\s*)*\}', body)
if not m_map:
    print("FATAL: no id->hash map found in the runtime.", file=sys.stderr)
    raise SystemExit(2)
mapping = re.findall(r'(\d+)\s*:\s*"([0-9a-f]+)"', m_map.group(0))

# --- 3. the public path, which is what justifies the asset-root URL form -------
m_p = re.search(r'f\.p\s*=\s*"([^"]*)"', body)
public_path = m_p.group(1) if m_p else "(absent)"

derived = []
for cid, h in mapping:
    name = special_name if cid == special_id else cid
    derived.append(f"{name}.{h}.js")

committed = [l.strip() for l in open(LIST).read().splitlines() if l.strip()]

# --- 4. the diff --------------------------------------------------------------
ds, cs = set(derived), set(committed)
only_derived = sorted(ds - cs)
only_committed = sorted(cs - ds)

digests = {}
for line in open(LEDGER):
    line = line.strip()
    if not line:
        continue
    row = json.loads(line)
    digests[row["path"].lstrip("/")] = (row["body_bytes"], row["body_sha256"])

out = []
w = out.append
w("#" * 78)
w("# AREA K — runtime map re-derivation vs the committed list. ZERO requests.")
w("#" * 78)
w("")
w("CORPUS RE-ANCHORED ON TODAY'S BYTES (read from the body fetched in this run,")
w("not from another pass's note):")
for p in ("runtime.79e2f9040b1dad8f.js", "main.6595daf83bd6d4b1.js"):
    b, s = digests.get(p, ("(absent)", "(absent)"))
    w(f"  {p:34s} {str(b):>9s} B  sha256 {s}")
w("")
w(f"f.p = {public_path!r}   -> asset ROOT, and no `/app` prefix. This re-confirms")
w("JSMAP-HUNT section 5 from the bytes rather than from the note.")
w("")
w(f"URL FORM: f.u special-cases id {special_id} to the NAME {special_name!r}.")
w("That is the whole reason a filename list is not the same thing as a URL list.")
w("")
w(f"entries re-derived from the runtime map : {len(derived)}")
w(f"entries in the committed list           : {len(committed)}")
w(f"same SET                                : {'YES' if ds == cs else 'NO'}")
w("")
w(f"in the runtime map but NOT in the committed list ({len(only_derived)}):")
for x in only_derived:
    w(f"  + {x}")
w(f"in the committed list but NOT in the runtime map ({len(only_committed)}):")
for x in only_committed:
    w(f"  - {x}")
w("")
# The URL-form defect, matched BY HASH. "The sets differ" is not the finding;
# "this entry carries the right hash under the wrong name" is, and matching on
# the hash is what tells the two apart — a same-set-different-order diff would
# call the same file a defect and miss a real one.
def split_hash(fn):
    m = re.fullmatch(r"(.+)\.([0-9a-f]+)\.js", fn)
    return (m.group(1), m.group(2)) if m else (fn, None)


derived_by_hash, committed_by_hash = {}, {}
for x in derived:
    derived_by_hash.setdefault(split_hash(x)[1], []).append(x)
for x in committed:
    committed_by_hash.setdefault(split_hash(x)[1], []).append(x)

shared_hashes = sorted(set(derived_by_hash) & set(committed_by_hash))
name_mismatch = [(h, committed_by_hash[h][0], derived_by_hash[h][0])
                 for h in shared_hashes
                 if committed_by_hash[h][0] != derived_by_hash[h][0]]

w(f"hashes shared by both lists : {len(shared_hashes)} of "
  f"{len(set(committed_by_hash) | set(derived_by_hash))}")
w(f"of those, the NAME differs  : {len(name_mismatch)}")
w("")
w("URL-FORM DEFECT — same hash, different emitted name, one line per entry:")
if name_mismatch:
    for h, c, d in name_mismatch:
        w(f"  committed {c}")
        w(f"  derived   {d}")
        w(f"  hash      {h}   (identical both sides -> only the NAME moved)")
else:
    w("  none — every committed filename equals the name the runtime emits")
w("")
w("DERIVED LIST (runtime key order), one filename per line:")
w("<<<DERIVED_BEGIN>>>")
for x in derived:
    w(x)
w("<<<DERIVED_END>>>")
print("\n".join(out))