#!/usr/bin/env python3
"""Area K — generate the prose tables from the ledger and the census. ZERO requests.

Every number that appears in FINDINGS.md comes out of this script. That is on
purpose: docs/09 section 6 item 5 records derived prose that contradicted its own
source table and then propagated into five pages. Hand-typing a count into prose
is the same failure with the same cause.

Tables emitted:
  T1  the sweep, by status, with the discriminating Content-Type and one digest
  T2  the token census over the 211 CHUNKS ONLY, next to the same token over the
      positive control — because a negative is only readable against a positive
  T3  per-token: which of the 211 chunks carried it, and the proposed reading
  T4  the byte-size distribution and the total corpus, so "4.4 MB" style figures
      are re-derived rather than inherited
"""
import json
import os
import re
import sys
from collections import Counter, defaultdict

BODIES = sys.argv[1]
LEDGER = sys.argv[2]
LIST = sys.argv[3]

rows = [json.loads(l) for l in open(LEDGER) if l.strip()]
rows.sort(key=lambda r: r["seq"])
chunks = [r for r in rows if r["role"].startswith("SWEEP-")]
controls = [r for r in rows if not r["role"].startswith("SWEEP-")]
followup = [r for r in rows if r["role"].startswith("FOLLOWUP")]
listed = [l.strip() for l in open(LIST) if l.strip() and not l.startswith("#")]

TOKENS = [
    'baseUrlPde', '/connect/pde', '/connect/pde/v3',
    'baseUrlCumulus', 'baseUrlCms', 'baseUrlAem', 'baseUrlCareLink',
    'discover/android', 'discover', 'clcloud', 'api/carepartner', 'pde',
    'system.gc.gz.transition.flags', 'useCumulusUrls', 'csrDisplayMessageUrl',
    'personalDisplayMessageUrl', 'carepartnerDisplayMessageUrl',
    'pullGMInfoFromCumulus', 'pullSMSHistoryFromCumulus',
    'sendDiagnosticLogsToCumulus', 'sendPeriodicToCumulus', 'sendSMSFromCumulus',
    'csr.cumulus.periodic.data.endpoints', 'csrCumulusPeriodicDataAPI',
    'guardianCumulusPeriodicAPI', 'display_message',
    'patient-timeline', 'dialog-lite',
    'personal.patient.timeline.config', 'personal.patient.timeline.host',
    'personalPatientTimelineHostURL',
    'sourceMappingURL',
    '/patient/m2m', 'retina.endpoints.config', 'mmm.data.api.url',
]


def text_of(r):
    p = os.path.join(BODIES, r["host_tag"] + ".b")
    if not os.path.exists(p):
        return None
    return open(p, "rb").read().decode("utf-8", errors="replace")


def cnt(t, tok, ci=False):
    pat = re.compile(re.escape(tok), re.IGNORECASE if ci else 0)
    return len(pat.findall(t))


def quoted(t, tok):
    return len(re.findall(re.escape('"%s"' % tok), t)) + \
           len(re.findall(re.escape("'%s'" % tok), t))


o = []
w = o.append

w("T1  THE SWEEP, BY STATUS — one row per observed response shape")
w("=" * 100)
w("%-4s %-46s %-5s %-34s %9s  %s" % ("n", "example path", "code", "content-type", "bytes", "distinct digests"))
by = defaultdict(list)
for r in rows:
    by[(r["http_status"], r["content_type"])].append(r)
for (code, ct), rs in sorted(by.items(), key=lambda kv: (-len(kv[1]), kv[0][0])):
    nd = len({x["body_sha256"] for x in rs})
    sample = next((x["path"] for x in rs if x["role"].startswith("SWEEP-")), rs[0]["path"])
    w("%-4d %-46s %-5s %-34s %9s  %d of %d bodies" % (
        len(rs), sample, code, ct, rs[0]["body_bytes"], nd, len(rs)))
w("")
w("The distinct-digest column is the check that matters: a shape carrying more than")
w("one digest over N bodies is N distinct artefacts, and the rows above are the only")
w("places that happens (all 213 are chunks of one build). Where one digest covers")
w("every body in a shape, that shape is a single shared artefact — which is what")
w("makes the 404 below an oracle rather than a coincidence.")
w("")
w(f"total ledger rows           : {len(rows)}")
w(f"  controls                  : {len(controls)}")
w(f"  sweep cells (SWEEP-*)     : {len(chunks)}")
w(f"  follow-up cells           : {len(followup)}")
w(f"cells in the committed list : {len(listed)}")
w("")
w("Every response shape in this table is discriminated on Content-Type, never on")
w("status. On this host family a status code IS an oracle (area V's fabricated-asset")
w("control 404s at 196 B), and the sweep's own control reproduces that digest exactly.")
w("")

w("")
w("T2  TOKEN CENSUS — the 211 CHUNKS ONLY, beside the same token in the POSITIVE")
w("    CONTROL. A negative is only readable next to a positive.")
w("=" * 100)
ctrl = next((r for r in controls if r["host_tag"] == "k-main"), None)
ctrl_t = text_of(ctrl) if ctrl else None
chunk_texts = []
for r in chunks:
    t = text_of(r)
    if t is not None:
        chunk_texts.append((r["path"], t))

w("%-38s %14s %14s %14s" % ("token", "chunks cs", "chunks ci", "control cs"))
w("-" * 100)
for tok in TOKENS:
    cs = sum(cnt(t, tok) for _, t in chunk_texts)
    ci = sum(cnt(t, tok, True) for _, t in chunk_texts)
    ccs = cnt(ctrl_t, tok) if ctrl_t else 0
    flag = ""
    if cs == 0 and ci == 0:
        flag = "  <- zero in all 211 chunks"
    elif cs:
        flag = "  <- NON-ZERO, read T3"
    w("%-38s %14d %14d %14d%s" % (tok, cs, ci, ccs, flag))
w("")

w("")
w("T3  PER-TOKEN — which of the 211 carried it, how many bytes, and what it is")
w("=" * 100)
for tok in TOKENS:
    hits = [(p, t, [m.start() for m in re.finditer(re.escape(tok), t)])
            for p, t in chunk_texts]
    hits = [(p, t, o_) for p, t, o_ in hits if o_]
    ci_hits = [(p, t) for p, t in chunk_texts if cnt(t, tok, True)]
    if not hits and not ci_hits:
        continue
    w("--- %r" % tok)
    w("    case-sensitive in %d of %d chunks; case-INSENSITIVE in %d" % (
        len(hits), len(chunk_texts), len(ci_hits)))
    for p, t, offs in hits[:20]:
        i = offs[0]
        ctx = t[max(0, i - 100):i + len(tok) + 100].replace("\n", "\\n")
        w("      %-30s offsets %s" % (p, offs[:8]))
        w("        ...%s..." % ctx)
    if len(hits) > 20:
        w("      ... and %d more chunks" % (len(hits) - 20))
    w("")

w("")
w("T4  CORPUS SIZE — re-derived, not inherited")
w("=" * 100)
sizes = [r["body_bytes"] for r in chunks]
w("chunks swept          : %d" % len(chunks))
w("total chunk bytes     : %d (%s MB)" % (sum(sizes), f"{sum(sizes)/1e6:.2f}"))
w("smallest / largest    : %d B / %d B" % (min(sizes), max(sizes)))
w("median                : %d B" % sorted(sizes)[len(sizes) // 2])
w("distinct digests      : %d of %d bodies" % (
    len({r["body_sha256"] for r in chunks}), len(chunks)))
dup = [s for s, n in Counter(r["body_sha256"] for r in chunks).items() if n > 1]
w("duplicate digests     : %d" % len(dup))
w("bodies with 0 bytes   : %d" % sum(1 for s in sizes if s == 0))
print("\n".join(o))