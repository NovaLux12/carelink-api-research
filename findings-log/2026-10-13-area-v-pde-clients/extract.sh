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
# errors cancelled (+1/-2) so the stated total still matched. §2 therefore ends
# with an arithmetic assertion — the per-identifier multiplicities of §2 MUST sum
# to the §1 hit count for that token — and prints FAIL loudly if they do not.
set -u
: "${TMPBODIES:?set TMPBODIES to the directory holding eu-main.b, hp-main.b, …}"
python3 - "$TMPBODIES" <<'EOF'
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
for tag in BODIES:
    p = f'{B}/{tag}.b'
    if not os.path.exists(p):
        print(f'== {tag}: NOT CAPTURED =='); continue
    raw = open(p, 'rb').read()
    t = raw.decode('utf-8', errors='replace')
    print()
    print('=' * 78)
    print(f'== {tag}: {len(raw)} B  sha256 {hashlib.sha256(raw).hexdigest()}')
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
        survives = 'case-SENSITIVE hits survive' if cs == len(hits) else \
                   'case-insensitive ONLY (case-sensitive grep drops every one)'
        print(f'\n   {tok!r}: {len(hits)} hit(s), {len(groups)} distinct enclosing '
              f'identifier(s) — {survives}')
        for w, os_ in sorted(groups.items(), key=lambda kv: (-len(kv[1]), kv[0])):
            ctx = t[max(0, os_[0] - 70):os_[0] + len(w) + 40].replace(chr(10), ' ')
            print(f'      x{len(os_):<3} {w!r:<34} offsets {os_}')
            print(f'           first-hit context: ...{ctx}...')
        total = sum(len(v) for v in groups.values())
        if total != len(hits):
            print(f'      FAIL arithmetic: multiplicities sum to {total}, '
                  f'expected {len(hits)}')
            assert_fail += 1
    print(f'\n   §2 arithmetic: {assert_fail} FAIL(s). A per-identifier count that does '
          f'not sum to the token total is how the first version of this file published')
    print('   two wrong multiplicities whose errors cancelled.')
EOF