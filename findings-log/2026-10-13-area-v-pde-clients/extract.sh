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
# A token with cs=0 and ci>0 is noise until its enclosing words are read, and
# §2 prints them.
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
    print('-- §2 every case-INsensitive hit that case-sensitive grep did NOT keep,')
    print('   with the maximal enclosing identifier. A hit is a token, not a claim.')
    shown = set()
    for tok in TOKENS:
        for m in re.finditer(re.escape(tok), t, re.I):
            s, e = m.start(), m.end()
            if tok not in ('pde', 'PDE', 'NGP', 'GUARDIAN', 'deviceFamily'):
                continue
            w = enclosing(t, s, e)
            if w == tok:
                continue
            key = (tok.lower(), w)
            if key in shown:
                continue
            shown.add(key)
            print(f'   {tok:<12} @s<{s:<9} enclosing identifier {w!r}')
EOF