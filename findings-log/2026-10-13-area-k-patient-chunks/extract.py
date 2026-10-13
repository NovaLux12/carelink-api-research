#!/usr/bin/env python3
"""Area K — offline token census over the 211 captured lazy chunks. ZERO requests.

Reads only bodies already on disk, writes nothing back to disk.

METHOD, per docs/09 section 5 item 2 ("a grep that hit without proving"). This
repo's recorded failure is a grep on a bare name reporting an integration that is
not there: `sourceMappingURL` read as a directive when it was a worker-loader
string literal, and area V's five `patient-timeline` hits in the main bundle all
being Angular component selectors rather than URLs. So every token is counted
three ways and EVERY non-zero count is printed with its byte offsets and the
enclosing identifier:

    cs   case-SENSITIVE substring hits      the count
    ci   case-INSENSITIVE substring hits    the control, and the difference
    q    hits as a COMPLETE QUOTED LITERAL  the strict test

and every hit carries a PROPOSED reading, printed next to the bytes that justify
it. The proposal is a proposal: the classifier is a set of patterns over the byte
window, and every hit it cannot classify prints its window in full rather than
being dropped. Nothing is filtered out of the report. (That is area V's own
correction: its first extractor printed offsets for a hand-picked list of five
tokens and nothing for the rest, so a count sat on the page with no context and
the count above it got read as the answer.)

A hit is a token, not a claim. The byte offset is printed so a reader can open the
body and check what the classifier said.
"""
import json
import os
import re
import sys

BODIES_DIR = sys.argv[1]
LEDGER = sys.argv[2]

TOKENS = [
    # the discovery-document vocabulary this sweep exists to test
    'baseUrlPde', '/connect/pde',
    'baseUrl', 'baseUrlCumulus', 'baseUrlCms', 'baseUrlAem', 'baseUrlCareLink',
    'discover/android', 'discover', 'clcloud', 'api/carepartner',
    'pde',
    # area T's published flag subtree: the parent and all nine leaves
    'system.gc.gz.transition.flags', 'useCumulusUrls', 'csrDisplayMessageUrl',
    'personalDisplayMessageUrl', 'carepartnerDisplayMessageUrl',
    'pullGMInfoFromCumulus', 'pullSMSHistoryFromCumulus',
    'sendDiagnosticLogsToCumulus', 'sendPeriodicToCumulus', 'sendSMSFromCumulus',
    # area V's pointer the client demonstrably follows, and its sibling
    'csr.cumulus.periodic.data.endpoints', 'csrCumulusPeriodicDataAPI',
    'guardianCumulusPeriodicAPI', 'display_message',
    # area F's caller question
    'patient-timeline', 'dialog-lite',
    # the timeline config key area V found NAMED and READ in the main bundle,
    # plus the unpublished sibling it named. Carried here because the question
    # this sweep can answer for area F is not "does the name appear" but "where".
    'personal.patient.timeline.config', 'personal.patient.timeline.host',
    'personalPatientTimelineHostURL',
    # area V's own positive controls: tokens the method must find if it can find
    # anything. If these read 0 the matcher is broken, and a zero sweep is a
    # broken matcher rather than a finding.
    '/patient/m2m', 'retina.endpoints.config', 'mmm.data.api.url',
    # the standing false-hit controls (docs/09 section 5)
    'sourceMappingURL', 'GUARDIAN', 'deviceFamily', 'NGP',
]

# --- the proposed readings -----------------------------------------------------
# Ordered: the first pattern that matches the byte window wins, and every pattern
# names what it keys on so the reader can disagree with it.
CLASSIFIERS = [
    ('ANGULAR COMPONENT SELECTOR (not a URL)',
     re.compile(r'["\[]\s*["\']?app-patient-timeline|app-patient-timeline')),
    ('URL-shaped pointer inside a quoted string',
     re.compile(r'["\'][^"\']*(https?://|//|/connect/|/patient/)[^"\']*["\']')),
    ('quoted dotted config key',
     re.compile(r'["\'][a-z][a-z0-9]*(\.[a-zA-Z0-9_]+){2,}["\']')),
    ('quoted path literal',
     re.compile(r'["\']/[a-zA-Z0-9][^"\']*["\']')),
    ('bare token in an identifier or expression',
     re.compile(r'.')),
]


def classify(window):
    for name, pat in CLASSIFIERS:
        if pat.search(window):
            return name
    return 'UNCLASSIFIED'


def enclosing(text, s, e):
    a = s
    while a > 0 and (text[a - 1].isalnum() or text[a - 1] == '_'):
        a -= 1
    b = e
    while b < len(text) and (text[b].isalnum() or text[b] == '_'):
        b += 1
    return text[a:b]


def count(text, tok, ci=False):
    if ci:
        pat = re.compile(re.escape(tok), re.IGNORECASE)
    else:
        pat = re.compile(re.escape(tok))
    return [m.start() for m in pat.finditer(text)]


def quoted_literal(text, tok):
    return count(text, '"%s"' % tok) + count(text, "'%s'" % tok)


def window(text, s, e, pad=110):
    return text[max(0, s - pad):min(len(text), e + pad)].replace('\n', '\\n')


# --- load the ledger, so every count is attached to a captured artefact --------
rows = []
for line in open(LEDGER):
    line = line.strip()
    if line:
        rows.append(json.loads(line))
rows.sort(key=lambda r: r['seq'])

bodies = []  # (tag, path, bytes, sha, text)
for r in rows:
    tag = r['host_tag']
    p = os.path.join(BODIES_DIR, tag + '.b')
    if not os.path.exists(p):
        continue
    b = open(p, 'rb').read()
    bodies.append((tag, r['path'], len(b), r['body_sha256'],
                   b.decode('utf-8', errors='replace')))

out = []
w = out.append
w('#' * 78)
w('# AREA K offline token census — ZERO requests, bodies captured 2026-10-13.')
w('# cs=case-sensitive  ci=case-insensitive (the control)  q=complete quoted literal')
w('# Every non-zero count is printed with its byte offsets and a PROPOSED reading.')
w('# A proposed reading is a proposal: open the body and check the window.')
w('#' * 78)
w('')
w(f'bodies analysed: {len(bodies)}')
w('')

total_cs = {t: 0 for t in TOKENS}
total_ci = {t: 0 for t in TOKENS}
total_q = {t: 0 for t in TOKENS}

for tag, path, nbytes, sha, text in bodies:
    w('=' * 78)
    w(f'== {path}   {nbytes} B   sha256 {sha}')
    w('=' * 78)
    for tok in TOKENS:
        cs = count(text, tok)
        ci = count(text, tok, ci=True)
        q = quoted_literal(text, tok)
        total_cs[tok] += len(cs)
        total_ci[tok] += len(ci)
        total_q[tok] += len(q)
        note = ''
        if len(ci) > len(cs):
            note = '   <-- ci adds %d, read §2' % (len(ci) - len(cs))
        if len(cs) == 0 and len(ci) == 0 and len(q) == 0:
            continue
        w(f'{tok:38s} cs={len(cs):<6d} ci={len(ci):<6d} q={len(q)}{note}')
    w('')

w('=' * 78)
w('§1  CORPUS TOTALS — accumulated over every body above')
w('=' * 78)
for tok in TOKENS:
    if total_cs[tok] == 0 and total_ci[tok] == 0 and total_q[tok] == 0:
        w(f'{tok:38s} cs=0       ci=0       q=0')
    else:
        w(f'{tok:38s} cs={total_cs[tok]:<8d} ci={total_ci[tok]:<8d} q={total_q[tok]}')
w('')

w('=' * 78)
w('§2  EVERY TOKEN WITH AT LEAST ONE HIT — every offset, the maximal enclosing')
w('    identifier, the proposed reading and the bytes that justify it.')
w('    UNFILTERED, on purpose: see the header of this script.')
w('=' * 78)
w('')
for tok in TOKENS:
    groups = {}
    for tag, path, nbytes, sha, text in bodies:
        for s in count(text, tok):
            e = s + len(tok)
            groups.setdefault(enclosing(text, s, e), []).append((path, s, text))
    if not groups:
        continue
    n = sum(len(v) for v in groups.values())
    w(f"--- {tok!r}: {n} hit(s), {len(groups)} distinct enclosing identifier(s) ---")
    for ident in sorted(groups, key=lambda i: (-len(groups[i]), i)):
        hits = groups[ident]
        w(f"  x{len(hits):<5d} {ident}")
        offs = [h[1] for h in hits]
        w(f"           offsets {offs if len(offs) <= 24 else str(offs[:24]) + ' ...'}")
        w(f"           proposed: {classify(window(hits[0][2], hits[0][1], hits[0][1] + len(tok)))}")
        w(f"           first-hit context: ...{window(hits[0][2], hits[0][1], hits[0][1] + len(tok), 90)}...")
        w(f"           first-hit file: {hits[0][0]}")
    w('')

w('=' * 78)
w('§3  BODIES WITH ZERO HITS FOR THE WHOLE TOKEN SET')
w('=' * 78)
clean = 0
for tag, path, nbytes, sha, text in bodies:
    hits = sum(len(count(text, t)) for t in TOKENS)
    if hits == 0:
        clean += 1
w(f'{clean} of {len(bodies)} bodies carry none of the {len(TOKENS)} tokens.')
w('')
print('\n'.join(out))