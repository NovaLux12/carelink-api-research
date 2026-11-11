#!/usr/bin/env python3
"""Area AU — rebuild the chunk list from the runtime's `f.u`, on EMITTED names.

    derive.py <runtime-body> <out-list>

WHY THIS EXISTS, and it is the whole reason the sweep is safe to report:

    f.u = e => (2076 === e ? "common" : e) + "." + { <id>: "<hash>", ... } + ".js"

`f.u` is not a plain join — one id is emitted under a NAME that is not its id. The
committed `chunks-swept.txt` carries the id form for that entry, and area K measured
the consequence: `2076.206e355a4a593fbd.js` → 404 / 196 B / text/html, while
`common.206e355a4a593fbd.js` → 200 / 21 157 B / application/javascript. A sweep that
trusts a filename list therefore reports a clean negative over a population that
silently excludes one member.

The special case and the map are ASSERTED, not assumed: if either regex fails the
script exits 2 and the sweep must not start, because a re-derivation that quietly
found nothing would look exactly like a list of zero chunks.
"""
import re
import sys

body = open(sys.argv[1], "rb").read().decode("utf-8", errors="replace")

m_special = re.search(
    r'f\.u\s*=\s*e\s*=>\s*\(\s*(\d+)\s*===\s*e\s*\?\s*"([^"]+)"\s*:\s*e\s*\)', body)
if not m_special:
    print("FATAL: no recognisable f.u special case — the URL form cannot be "
          "re-derived, so nothing here should be trusted.", file=sys.stderr)
    raise SystemExit(2)
special_id, special_name = m_special.group(1), m_special.group(2)

m_map = re.search(
    r'f\.u\s*=\s*e\s*=>.*?\{\s*(\d+)\s*:\s*"([0-9a-f]+)"\s*'
    r'(?:,\s*\d+\s*:\s*"[0-9a-f]+"\s*)*\}', body)
if not m_map:
    print("FATAL: no id->hash map found in the runtime.", file=sys.stderr)
    raise SystemExit(2)
mapping = re.findall(r'(\d+)\s*:\s*"([0-9a-f]+)"', m_map.group(0))

m_p = re.search(r'f\.p\s*=\s*"([^"]*)"', body)
public_path = m_p.group(1) if m_p else "(absent)"

derived = []
for cid, h in mapping:
    name = special_name if cid == special_id else cid
    derived.append(f"{name}.{h}.js")

if len(derived) != len(set(derived)):
    print(f"FATAL: derived {len(derived)} names, {len(set(derived))} distinct — "
          f"the map is not 1:1 and a duplicate would double-count a cell.",
          file=sys.stderr)
    raise SystemExit(2)

with open(sys.argv[2], "w") as fh:
    fh.write("\n".join(derived) + "\n")

# A machine-readable header line for the run log. Zero requests.
print(f"f.p={public_path!r} special={special_id}->{special_name} "
      f"entries={len(derived)} renamed={sum(1 for c, _ in mapping if c == special_id)}")
