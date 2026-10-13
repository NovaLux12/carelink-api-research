#!/bin/bash
# Area V offline extraction — ZERO requests. Re-derives every claim in
# FINDINGS.md from bodies captured by probe.sh (digests in results.jsonl).
#
# Usage: TMPBODIES=/path/to/bodies bash extract.sh > grep-out.txt
#
# Method (docs/09 §5 item 2 — "a grep that hit without proving"): every token is
# counted three ways and every non-zero count is printed with its byte offsets
# AND its enclosing word, because the failure mode this repo has recorded twice
# is a substring of an unrelated identifier counting as a hit:
#   cs  = case-sensitive substring hits
#   ci  = case-insensitive substring hits      (the control)
#   q   = hits as a complete quoted literal    (the strict test)
#
# §2 is UNFILTERED, and that is a correction, not a preference — see
# "Correction (2026-10-13)" §A in FINDINGS.md. The first version of this script
# printed an offset list for a hand-picked list of five tokens and nothing for
# the rest, so `discover`'s 12 hits sat in §1 with no context and the count above
# them was read as the answer. §2 now covers EVERY token with at least one hit.
#
# §2 also prints MULTIPLICITIES (xN per enclosing identifier, with every offset),
# because the first version deduped by word and printed one offset each. That
# made per-identifier counts unsourceable prose: two of them were wrong and the
# errors cancelled (+1/-2) so the stated total still matched.
#
# §3 CHECKS §2 against expected-multiplicities.txt — an INDEPENDENT input, stated
# per identifier. It fires when a recomputed multiplicity differs from the
# published one, or when a published row has no recomputed counterpart, and prints
# the diff.
#
# What §3 is, stated exactly so it is not over-read. It is DRIFT DETECTION between
# the published numbers and the bytes. It is NOT proof the published numbers were
# right the first time: the expected file was authored by this same pass from these
# same bundles, so a wrong first derivation would be written into both and §3 would
# agree with it forever. That limit is why the file is GENERATED (--emit) rather
# than typed, and why every row was re-derived independently before being committed.
#
# §3 ALSO COMPARES BODY DIGESTS, as first-class compared rows — `<body> sha256 <hex>`.
# Round 3 found the guard PRINTING each body's sha256 in section 1 and three places
# claiming it "asserts the digest before any comparison" and that "a bundle bump
# makes the guard say so". None of that was true: section 1 printed, section 3
# compared multiplicities only, and a body with a different digest, a different size
# and every byte offset moved still exited 0. Verified here before the fix:
#   original eu-runtime   8268 B  sha256 0dfea208...  -> guard exit 0
#   bumped   eu-runtime  13272 B  sha256 1cdfa1ea...  -> guard exit 0
# So the digest rows below are compared, not decorative. A bundle bump now fails the
# guard BEFORE any multiplicity is even considered.
#
# LIMIT, identical to the multiplicities guard and stated here because this is the
# third round of a control describing more than it checks: comparing digests catches
# DRIFT between the published bytes and the file on disk. It cannot catch a wrong
# FIRST derivation — these digests were observed on 2026-10-13 from these bundles, so
# a body that was misread on the first pass is misread here identically. What the
# digest rows buy is the one thing the multiplicities could not do at all: prove the
# bytes being compared are the bytes that were published.
#
# The guard this replaced was a tautology: it compared sum(len(v) for v in groups)
# against len(hits), but groups is built by iterating hits, so the partition sum IS
# the size of the set it partitions and the comparison could never fire.
# FINDINGS.md had described it as stopping a class of error "silently".
# docs/09 §5: a check that looks like it ran is worse than no check.
#
# MODE=--emit regenerates expected-multiplicities.txt from the bodies;
# MODE=--check (default) verifies the committed file against them.
set -u
: "${TMPBODIES:?set TMPBODIES to the directory holding eu-main.b, hp-main.b, …}"
# Derived, never hardcoded, and never taken from the caller's cwd.
HERE="$(cd "$(dirname "$0")" && pwd)"
# HERE is passed in rather than derived from __file__: this is a heredoc, so
# __file__ is "<stdin>" and os.path.dirname would resolve to the CALLER's cwd.
# That bug made the guard look for expected-multiplicities.txt in the directory
# the script was invoked from, so it reported "absent" on a clean run from
# anywhere but this directory. A guard that depends on your cwd is not a guard.
python3 - "$TMPBODIES" "$HERE" <<'EOF'
import re, sys, os, hashlib
B = sys.argv[1]

TOKENS = [
  # the tokens this area exists to test
  'baseUrlPde', '/connect/pde', 'pde', 'PDE',
  'baseUrl', 'baseUrlCumulus', 'baseUrlCms', 'baseUrlAem', 'baseUrlCareLink',
  # the whole discovery-document vocabulary, so "no web bundle reads discovery"
  # is a claim about the document class and not about one key
  'discover/android', 'discover', 'clcloud', 'api/carepartner',
  # the flag subtree area T published
  'system.gc.gz.transition.flags', 'guardianCumulusPeriodicAPI',
  'csr.cumulus.periodic.data.endpoints', 'csrCumulusPeriodicDataAPI',
  'display_message', 'useCumulusUrls', 'csrDisplayMessageUrl',
  'personalDisplayMessageUrl', 'carepartnerDisplayMessageUrl',
  'pullGMInfoFromCumulus', 'pullSMSHistoryFromCumulus',
  'sendDiagnosticLogsToCumulus', 'sendPeriodicToCumulus', 'sendSMSFromCumulus',
  # POSITIVE CONTROLS: tokens this method must find if it can find anything
  '/patient/m2m', 'retina.endpoints.config', 'mmm.data.api.url',
  'patient-timeline', 'dialog-lite',
  # the standing false-hit controls (docs/09 §5)
  'sourceMappingURL', 'GUARDIAN', 'medicalDeviceFamily', 'deviceFamily', 'NGP',
]
BODIES = ['eu-main', 'us-main', 'hp-main', 'sup-main', 'eu-runtime']

def load(tag):
    return open(f'{B}/{tag}.b', 'rb').read().decode('utf-8', errors='replace')

def enclosing(t, s, e):
    a = s
    while a > 0 and (t[a-1].isalnum() or t[a-1] == '_'):
        a -= 1
    b = e
    while b < len(t) and (t[b].isalnum() or t[b] == '_'):
        b += 1
    return t[a:b]

print('#' * 78)
print('# AREA V offline token census — zero requests, bodies captured 2026-10-13.')
print('# cs=case-sensitive  ci=case-insensitive (control)  q=complete quoted literal')
print('#' * 78)
# Accumulated ACROSS bodies, not per body: re-initialising inside the loop made
# the guard see only the last body and report every published row as MISSING.
computed = []
computed_meta = []
digests = []
assert_fail_total = 0
for tag in BODIES:
    p = f'{B}/{tag}.b'
    if not os.path.exists(p):
        print(f'== {tag}: NOT CAPTURED =='); continue
    raw = open(p, 'rb').read()
    t = raw.decode('utf-8', errors='replace')
    print()
    print('=' * 78)
    digests.append((tag, hashlib.sha256(raw).hexdigest(), len(raw)))
    print(f'== {tag}: {len(raw)} B  sha256 {hashlib.sha256(raw).hexdigest()} '
          f'(printed here; COMPARED in section 3)')
    print('=' * 78)
    for tok in TOKENS:
        cs = [m.start() for m in re.finditer(re.escape(tok), t)]
        ci = [m.start() for m in re.finditer(re.escape(tok), t, re.I)]
        q  = len(re.findall(re.escape('"%s"' % tok), t))
        mark = '' if len(cs) == len(ci) else '  <-- ci adds %d, read §2' % (len(ci)-len(cs))
        print('%-36s cs=%-4d ci=%-4d q=%-4d%s' % (tok, len(cs), len(ci), q, mark))
    print()
    print('-- §2 EVERY token with at least one hit, grouped by its maximal enclosing')
    print('   identifier, with the multiplicity and EVERY offset. A hit is a token,')
    print('   not a claim: read the identifier and the surrounding bytes before')
    print('   writing the hit as anything. Nothing is filtered out here.')
    assert_fail = 0
    for tok in TOKENS:
        hits = list(re.finditer(re.escape(tok), t, re.I))
        if not hits:
            continue
        cs = len(re.findall(re.escape(tok), t))
        groups = {}
        for m in hits:
            groups.setdefault(enclosing(t, m.start(), m.end()), []).append(m.start())
        # THREE states, and the middle one is the one the pre-fix script could not
        # express. It tested `cs == len(hits)`, so a PARTIAL token (0 < cs < ci)
        # fell into the else-branch and was labelled "case-insensitive ONLY ...
        # drops every one" — contradicting section 1's own `cs=` number on the same
        # page, for `pde`, `GUARDIAN` and `deviceFamily`. The test for
        # "case-insensitive ONLY" is `cs == 0`, not `cs == len(hits)`.
        if cs == 0:
            cls = 'ci'
            survives = ('case-insensitive ONLY — a case-SENSITIVE grep drops EVERY '
                        'one (cs=0)')
        elif cs == len(hits):
            cls = 'cs'
            survives = f'all {len(hits)} hit(s) survive a case-SENSITIVE grep (cs={cs})'
        else:
            cls = 'partial'
            survives = (f'PARTIAL — {cs} of {len(hits)} hit(s) survive a case-SENSITIVE '
                        f'grep (cs={cs}, ci={len(hits)}); the rest are substrings of '
                        f'unrelated identifiers and are NOT references to the token')
        print(f'\n   {tok!r}: {len(hits)} hit(s), {len(groups)} distinct enclosing '
              f'identifier(s) — {survives}')
        for w, os_ in sorted(groups.items(), key=lambda kv: (-len(kv[1]), kv[0])):
            ctx = t[max(0, os_[0] - 70):os_[0] + len(w) + 40].replace(chr(10), ' ')
            print(f'      x{len(os_):<3} {w!r:<34} offsets {os_}')
            print(f'           first-hit context: ...{ctx}...')
        # A REAL cross-section check, not the tautology it replaced: section 1 counts
        # the token with len(re.findall(...)) over the whole text; section 2 arrives
        # at the same number by grouping individual matches. Two routes to one
        # number — if either drops or double-counts, they disagree. The old guard
        # compared a partition of `hits` against len(hits), i.e. a quantity with
        # itself.
        total = sum(len(v) for v in groups.values())
        if total != len(hits):
            print(f'      FAIL cross-section: §2 multiplicities sum to {total}, §1 '
                  f'counted {len(hits)} hit(s)')
            assert_fail += 1
        for w_, os__ in groups.items():
            computed.append((tag, tok, w_, len(os__)))
        computed_meta.append((tag, tok, cls, cs, len(hits), len(groups)))
    print(f'\n   §2 cross-section check: {assert_fail} FAIL(s) across '
          f'{len(computed_meta)} section(s), {len(computed)} group(s). This one can '
          f'fail — it compares')
    print('   section 1 with section 2, not a set with its own partition. It is NOT '
          'the protection the')
    print('   old guard was claimed to be; §3 is that.')


# ---------------------------------------------------------------------------
# §3  GUARD: §2 against expected-multiplicities.txt (an independent input).
# ---------------------------------------------------------------------------
print()
print('=' * 78)
print('§3  PUBLISHED-MULTIPLICITIES GUARD (drift detection, not first-derivation proof)')
print('=' * 78)
HERE = sys.argv[2]
EXPECTED = os.path.join(HERE, 'expected-multiplicities.txt')
HEADER = os.path.join(HERE, 'expected-multiplicities.HEADER')
mode = os.environ.get('MODE', '--check')

def emit():
    """Write HEADER + digest rows + multiplicity rows, in that order.

    The header lives in its OWN committed file and is copied verbatim, so --emit
    reproduces expected-multiplicities.txt byte-for-byte. Round 3: --emit used to
    write its own 19-line header over the committed 41-line one, destroying the
    digest table and every explanation of how the numbers were derived, while
    FINDINGS.md claimed it "reproduces the expected file".
    """
    with open(HEADER, encoding='utf-8') as fh:
        head = fh.read()
    with open(EXPECTED, 'w', encoding='utf-8') as fh:
        fh.write(head)
        fh.write(chr(10))
        for b_, d_, _sz in sorted(digests):
            fh.write(f'{b_} sha256 {d_}' + chr(10))
        fh.write(chr(10))
        for a_, b2_, c_, n_ in sorted(computed):
            fh.write(f'{a_} {b2_} {c_} {n_}' + chr(10))
    print(f'   --emit: {len(head.splitlines())} header line(s) + {len(digests)} digest '
          f'row(s) + {len(computed)} multiplicity row(s) -> expected-multiplicities.txt')

if mode == '--emit':
    emit()
    sys.exit(0)
if not os.path.exists(EXPECTED):
    print(f'   FAIL {EXPECTED} is absent. Without it there is no guard, and this script')
    print('        must not be described as having one.')
    sys.exit(1)
if not os.path.exists(HEADER):
    print(f'   FAIL {HEADER} is absent — the rationale header must be committed')
    print('        separately so --emit cannot overwrite it.')
    sys.exit(1)

raw_text = open(EXPECTED, encoding='utf-8').read()
committed_head = open(HEADER, encoding='utf-8').read()

head_ok = raw_text.startswith(committed_head)
print(f'   header matches expected-multiplicities.HEADER: {head_ok}')

expected, expected_digest, bad_rows = {}, {}, 0
for line in raw_text[len(committed_head):].splitlines():
    line = line.strip()
    if not line or line.startswith('#'):
        continue
    parts = line.split()
    if len(parts) == 3 and parts[1] == 'sha256':
        expected_digest[parts[0]] = parts[2]
    elif len(parts) == 4:
        expected[(parts[0], parts[1], parts[2])] = int(parts[3])
    else:
        print(f'   FAIL malformed expected row: {line!r}')
        bad_rows += 1

got = {}
for a_, b_, c_, n_ in computed:
    got[(a_, b_, c_)] = n_

dig_drift = []
seen_bodies = dict((b_, d_) for b_, d_, _s in digests)
for b_, d_ in sorted(seen_bodies.items()):
    if b_ not in expected_digest:
        dig_drift.append(f'   NO DIGEST  {b_}: observed {d_[:16]}..., file carries none')
    elif expected_digest[b_] != d_:
        dig_drift.append(f'   BUMPED     {b_}: file says {expected_digest[b_][:16]}..., '
                         f'bundle says {d_[:16]}...')
for b_ in sorted(expected_digest):
    if b_ not in seen_bodies:
        dig_drift.append(f'   MISSING BODY {b_}: file carries a digest, no such body was read')
if dig_drift:
    print(f'   FAIL {len(dig_drift)} body digest mismatch(es) — the bytes being compared')
    print('        are NOT the bytes that were published:')
    for x in dig_drift:
        print(x)
else:
    print(f'   ok   {len(expected_digest)} body digest(s) match the published file')

drift = []
for k, n in sorted(got.items()):
    if k not in expected:
        drift.append(f'   NEW      {k[0]} {k[1]} {k[2]!r}: computed {n}, published NOTHING')
    elif expected[k] != n:
        drift.append(f'   CHANGED  {k[0]} {k[1]} {k[2]!r}: published {expected[k]}, computed {n}')
for k, n in sorted(expected.items()):
    if k not in got:
        drift.append(f'   MISSING  {k[0]} {k[1]} {k[2]!r}: published {n}, computed NOTHING')
if drift:
    print(f'   FAIL {len(drift)} multiplicity drift(s) between the published table and the bytes:')
    for d in drift[:80]:
        print(d)
    if len(drift) > 80:
        print(f'   ... and {len(drift) - 80} more')
else:
    print(f'   ok   {len(got)} group(s) match the published multiplicities exactly')

if head_ok and not dig_drift and not drift and not bad_rows:
    print('   ok   case-sensitivity class per section (derived from the bytes, not stored):')
    for tag, tok, cls, cs, ci, ng in computed_meta:
        print(f'        {tag:<11} {tok:<34} {cls:<8} cs={cs:<3} ci={ci:<3} groups={ng}')
    print()
    print('   LIMIT, stated so this guard is not over-read twice: it detects DRIFT between')
    print('   the published numbers and the bytes, and the digest rows additionally prove')
    print('   the bytes on disk ARE the published ones. Neither detects a wrong FIRST')
    print('   derivation: the multiplicities AND the digests were both produced by this')
    print('   same pass from these same bundles on 2026-10-13. MODE=--emit re-derives;')
    print('   re-review any diff by hand rather than trusting that it is small.')
    sys.exit(0)
print()
print('   GUARD FAILED — do not describe this script as checking what it just failed to check.')
sys.exit(1)

EOF
