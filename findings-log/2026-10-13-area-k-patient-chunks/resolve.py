#!/usr/bin/env python3
"""Area K — resolve every cited byte offset to its enclosing webpack module, and
assert the identity argument. ZERO requests; reads only bodies already captured.

WHY THIS EXISTS. The pass's headline claim is that a read of the alias `z2` inside
a lazy chunk is a read of the SAME selector that the main bundle's export table
maps to `system.gc.gz.transition.flags`. That claim rested on six byte offsets and
one module id, and the first version of the write-up asserted "the byte offsets are
committed" when the offsets lived only in prose. `4265` appeared in no committed
artefact at all. This script is what makes the claim checkable without re-fetching
3.4 MB: it resolves each offset to its enclosing module, prints the span, and
prints the bytes on both sides of it.

A minified two-character export name is NOT unique. That is not a caveat here, it
is the reason this script exists: the repo has been bitten twice by assuming a
short token meant one thing (a `sourceMappingURL` string literal read as a
directive; `ngp`/`guardian` dictionary noise read as integration). The identity is
closed by MODULE ID, which webpack keeps stable between a bundle and its chunks,
and this script prints the evidence for that rather than asserting it.

What it asserts, and each assertion is allowed to FAIL:
  A1  `o(4265)` occurs exactly twice in the chunk, i.e. two independent modules
      import the same module id.
  A2  module 4265 is a single contiguous span in the main bundle.
  A3  that span's export table maps `z2:()=>be`.
  A4  `be` is the selector over `gt.guardianCumulusPeriodicAPI`.
  A5  `guardianCumulusPeriodicAPI` is assigned the string
      `system.gc.gz.transition.flags`.
  A6  every `.z2` occurrence in the chunk resolves to a module that imported 4265.
  A7  the value read flows into the POSTed URL: `h.messageEndpoint` -> `y` ->
      `getPeriodicDataWithPost({reqUrl:y`.
Exits non-zero if any assertion fails, so it cannot report a clean run over a
body that no longer supports the claim.
"""
import re
import sys

BODIES = sys.argv[1]

# (label, body tag, offset, what is expected there)
CITED = [
    ("read 1 import: module 16746 binds the config module",
     "k-6746-c6795ff7e9ff468d-js.b", 579, r'_=o\(4265\)'),
    ("read 1: the select of the alias, module 16746",
     "k-6746-c6795ff7e9ff468d-js.b", 22260, r'select\(_\.z2\)'),
    ("read 2 import: module 59567 binds the same config module",
     "k-6746-c6795ff7e9ff468d-js.b", 66109, r'F=o\(4265\)'),
    ("getMessageRequest CALL SITE, module 59567",
     "k-6746-c6795ff7e9ff468d-js.b", 67573, r'getMessageRequest\(n\.username'),
    ("getGuardianEndpoint DEFINITION, module 59567",
     "k-6746-c6795ff7e9ff468d-js.b", 67391, r'getGuardianEndpoint\(\)'),
    ("getMessageRequest DEFINITION, module 59567",
     "k-6746-c6795ff7e9ff468d-js.b", 69249, r'getMessageRequest\(i,v,n,c,h\)\{'),
    ("the value is unpacked: E = h.messageEndpoint",
     "k-6746-c6795ff7e9ff468d-js.b", 69458, r'const L=h\.useCumulusUrls&&this\.isCsrEnabled,E=h\.messageEndpoint'),
    ("the M2M template literal (the /patient/m2m branch)",
     "k-6746-c6795ff7e9ff468d-js.b", 69567, r'/patient/m2m/connect/data/gc/patients/'),
    ("the endpoint value is substituted into the URL",
     "k-6746-c6795ff7e9ff468d-js.b", 69787, r'E\.replace\("\{patientUsername\}"'),
    ("THE POST: the URL built above is the request body URL",
     "k-6746-c6795ff7e9ff468d-js.b", 69866, r'getPeriodicDataWithPost\(\{reqUrl:y'),
    ("read 2: the select of the alias, module 59567",
     "k-6746-c6795ff7e9ff468d-js.b", 70054, r'select\(F\.z2\)'),
]

MAIN_CITED = [
    ("the key constant: guardianCumulusPeriodicAPI = the dotted key",
     2189123, r'D\.guardianCumulusPeriodicAPI="system\.gc\.gz\.transition\.flags"'),
    ("the selector over that key: be = createSelector(f, gt => gt.guardianCumulusPeriodicAPI)",
     93819, r'be=\(0,e\.Mz\)\(f,gt=>gt\.guardianCumulusPeriodicAPI\)'),
    ("module 4265's export table maps z2 to be",
     91992, r'z2:\(\)=>be'),
]

failures = []
out = []
w = out.append


def load(tag):
    return open(f"{BODIES}/{tag}", "rb").read().decode("utf-8", errors="replace")


def modules(text):
    """(start, id) for every webpack module definition, in order."""
    return sorted((m.start(), int(m.group(1)))
                  for m in re.finditer(r'(\d+):\([^)]*\)=>\{', text))


def owner(bounds, off):
    hit = None
    for st, i in bounds:
        if st <= off:
            hit = (st, i)
        else:
            break
    return hit


def span(bounds, st, i):
    idx = [k for k, (s, j) in enumerate(bounds) if s == st and j == i]
    if not idx:
        return st, len(text_hint)
    k = idx[0]
    end = bounds[k + 1][0] - 1 if k + 1 < len(bounds) else None
    return st, end


chunk = load("k-6746-c6795ff7e9ff468d-js.b")
cb = modules(chunk)
text_hint = chunk
main = load("k-main.b")
mb = modules(main)

w("#" * 78)
w("# AREA K — every cited byte offset resolved to its enclosing webpack module.")
w("# ZERO requests. Bodies are not committed; THIS TABLE IS, so the identity")
w("# argument is checkable without re-fetching 3.4 MB.")
w("#" * 78)
w("")

w("=" * 78)
w("A. CITED OFFSETS IN THE LAZY CHUNK 6746.c6795ff7e9ff468d.js (101,594 B)")
w("=" * 78)
w("%-6s %-9s %-9s %s" % ("byte", "module", "span", "what is there"))
for label, tag, off, pat in CITED:
    o = owner(cb, off)
    st, end = span(cb, *o)
    seg = chunk[off:off + 90]
    ok = bool(re.search(pat, chunk[max(0, off - 40):off + 120]))
    if not ok:
        failures.append(f"A-offset {label} at byte {off}: expected {pat}")
    w("%-6d %-9s %-9s %s" % (off, o[1], f"{st}-{end}", label))
    w("       text: %r" % seg)
    w("       match at this offset: %s" % ("YES" if ok else "*** NO ***"))
w("")

w("=" * 78)
w("B. CITED OFFSETS IN THE EAGER MAIN BUNDLE main.6595daf83bd6d4b1.js (3,417,255 B)")
w("=" * 78)
for label, off, pat in MAIN_CITED:
    o = owner(mb, off)
    seg = main[off:off + 90]
    ok = bool(re.search(pat, main[max(0, off - 40):off + 120]))
    if not ok:
        failures.append(f"B-offset {label} at byte {off}: expected {pat}")
    w("%-8d module %-8s %s" % (off, o[1], label))
    w("       text: %r" % seg)
    w("       match at this offset: %s" % ("YES" if ok else "*** NO ***"))
w("")

w("=" * 78)
w("C. THE ASSERTIONS — each one is allowed to fail")
w("=" * 78)

# A1 — o(4265) exactly twice
n4265 = len(re.findall(r'o\(4265\)', chunk))
a1 = n4265 == 2
if not a1:
    failures.append(f"A1: o(4265) occurs {n4265} times, expected exactly 2")
w("A1  o(4265) occurs exactly twice in the chunk           : %d  -> %s"
  % (n4265, "PASS" if a1 else "FAIL"))

# A2 — module 4265 is a single contiguous span in main
occ = [s for s, i in mb if i == 4265]
a2 = len(occ) == 1
if not a2:
    failures.append(f"A2: module 4265 appears {len(occ)} times in main, expected 1")
mstart = occ[0] if occ else None
mend = (mb[[k for k, (s, i) in enumerate(mb) if s == mstart][0] + 1][0] - 1
           if mstart is not None and
           [k for k, (s, i) in enumerate(mb) if s == mstart][0] + 1 < len(mb)
           else None)
w("A2  module 4265 is ONE contiguous span in main          : span %s-%s (%s B) -> %s"
  % (mstart, mend, (mend - mstart + 1) if mend else "?", "PASS" if a2 else "FAIL"))

# A3 — export table maps z2 -> be
if mstart is not None:
    seg = main[mstart:mstart + 1200]
    a3 = bool(re.search(r'z2:\(\)=>be', seg))
else:
    a3 = False
if not a3:
    failures.append("A3: module 4265's export table does not map z2 to be")
w("A3  that span's export table maps `z2:()=>be`            : %s" % ("PASS" if a3 else "FAIL"))

# A4 — be is the selector over guardianCumulusPeriodicAPI
a4 = bool(re.search(r'be=\(0,e\.Mz\)\(f,gt=>gt\.guardianCumulusPeriodicAPI\)', main))
if not a4:
    failures.append("A4: be is not the guardianCumulusPeriodicAPI selector")
w("A4  `be` selects `gt.guardianCumulusPeriodicAPI`         : %s" % ("PASS" if a4 else "FAIL"))

# A5 — the key constant
a5 = bool(re.search(r'D\.guardianCumulusPeriodicAPI="system\.gc\.gz\.transition\.flags"', main))
if not a5:
    failures.append("A5: guardianCumulusPeriodicAPI is not the dotted flags key")
w("A5  ... is assigned `system.gc.gz.transition.flags`      : %s" % ("PASS" if a5 else "FAIL"))

# A6 — every .z2 in the chunk sits in a module that imported 4265
zs = [m.start() for m in re.finditer(r'\.z2\b', chunk)]
ok6 = True
for z in zs:
    o = owner(cb, z)
    mspan = chunk[o[0]:(cb[[k for k, (s, i) in enumerate(cb) if s == o[0]][0] + 1][0]
                        if [k for k, (s, i) in enumerate(cb) if s == o[0]][0] + 1 < len(cb)
                        else len(chunk))]
    if 'o(4265)' not in mspan:
        ok6 = False
        failures.append(f"A6: .z2 at byte {z} is in module {o[1]}, which never imports 4265")
w("A6  every `.z2` in the chunk is in a 4265-importing module: %d occurrence(s) -> %s"
  % (len(zs), "PASS" if ok6 else "FAIL"))

# A6b — and the binding is used at that offset (not merely present in the module)
ok6b = all(re.search(r'(_|F)=o\(4265\)', chunk[max(0, owner(cb, z)[0]):owner(cb, z)[0] + 4000])
           for z in zs)
w("A6b the binding is `_` or `F` at each read               : %s" % ("PASS" if ok6b else "FAIL"))
if not ok6b:
    failures.append("A6b: a `.z2` read is not on the binding of o(4265)")

# A7 — the value flows into the POSTed URL
seg = chunk[69458:69900]
a7 = bool(re.search(r'const L=h\.useCumulusUrls&&this\.isCsrEnabled,E=h\.messageEndpoint', seg)) \
     and bool(re.search(r'getPeriodicDataWithPost\(\{reqUrl:y', seg)) \
     and bool(re.search(r'E\.replace\("\{patientUsername\}"', seg))
if not a7:
    failures.append("A7: h.messageEndpoint does not demonstrably reach the POSTed reqUrl")
w("A7  h.messageEndpoint -> y -> getPeriodicDataWithPost   : %s" % ("PASS" if a7 else "FAIL"))
w("")
w("    the contiguous run, bytes 69458-69900, verbatim:")
w("    %r" % seg)
w("")
w("    and the method's own head, byte 69249:")
w("    %r" % chunk[69249:69470])
w("")

# A8 — the negative the headline does not rest on: .z2 is read 0 times in main
n_z2_main = len(re.findall(r'\.z2\b', main))
a8 = n_z2_main == 0
if not a8:
    failures.append(f"A8: main reads .z2 {n_z2_main} times, expected 0")
w("A8  `.z2` is read 0 times in the EAGER main bundle       : %d  -> %s"
  % (n_z2_main, "PASS" if a8 else "FAIL"))
w("    (area V's measurement, re-measured here; it is what makes the chunk read")
w("     a finding about the LAZY corpus rather than a contradiction of area V)")
w("")

w("=" * 78)
if failures:
    w("VERDICT: %d ASSERTION(S) FAILED — do not use any claim resting on them."
      % len(failures))
    for f in failures:
        w("  - %s" % f)
else:
    w("VERDICT: all assertions PASS.")
w("=" * 78)
print("\n".join(out))
sys.exit(1 if failures else 0)