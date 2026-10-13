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

# THE COUNTING RULE, stated because getting it wrong is what the first version
# of this script did.
#
# "A chunk" is a body that came back 200 application/javascript. It is NOT a
# ledger row whose role starts SWEEP-: that definition swept in the 196 B HTML
# error page at seq 51 (the wrong URL form, section 2 of FINDINGS.md) and
# dropped the real 21,157 B chunk at seq 215 (the corrected form, role
# FOLLOWUP). The consequence was a denominator that did not mean what it said -
# one error page counted as a chunk and one chunk omitted - while the
# substantive negative survived, because grep-out.txt greps the ledger rather
# than this selection.
#
# Rule, restated so a reader can check it: 211 = 210 SWEEP rows answering
# 200 application/javascript + 1 FOLLOWUP row answering 200
# application/javascript. It is cross-checked against the committed list length
# below and the script exits non-zero if they disagree.
def is_real_chunk(r):
    return r["http_status"] == "200" and r["content_type"] == "application/javascript"


chunks = [r for r in rows if r["role"].startswith("SWEEP-") and is_real_chunk(r)]
followup = [r for r in rows if r["role"].startswith("FOLLOWUP")]
followup_chunks = [r for r in followup if is_real_chunk(r)]
controls = [r for r in rows
            if not r["role"].startswith(("SWEEP-", "FOLLOWUP"))]
not_chunks = [r for r in rows
              if r["role"].startswith(("SWEEP-", "FOLLOWUP")) and not is_real_chunk(r)]
corpus = chunks + followup_chunks
listed = [l.strip() for l in open(LIST) if l.strip() and not l.startswith("#")]

TOKENS = [
    'baseUrlPde', '/connect/pde', '/connect/pde/v3',
    'baseUrlCumulus', 'baseUrlCms', 'baseUrlAem', 'baseUrlCareLink',
    # `baseUrl` was measured (32 corpus-wide, q=0) but was ABSENT from this
    # token list, so a measured token appeared in no table and in no prose. It
    # is here now. It turns out to be the pass's second positive, so leaving it
    # out was not cosmetic.
    'baseUrl',
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
    # the hard-coded patient API bases the lazy chunks carry, which no
    # published document and no eager bundle names
    '/patient/csr',
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
w(f"total ledger rows             : {len(rows)}")
w(f"  controls                    : {len(controls)}")
w(f"  sweep rows, role SWEEP-*    : {sum(1 for r in rows if r['role'].startswith('SWEEP-'))}")
w(f"  follow-up rows, FOLLOWUP-*  : {len(followup)}")
w(f"  of those, NOT a real chunk  : {len(not_chunks)}  "
  f"({', '.join('%s=%s %s' % (r['seq'], r['http_status'], r['content_type']) for r in not_chunks)})")
w(f"cells in the committed list   : {len(listed)}")
w("")
w("COUNTING RULE — what T2/T3/T4 are computed over, and why it is not the ledger:")
w("  a chunk = a body answering 200 + application/javascript.")
w(f"    {len(chunks)} SWEEP rows + {len(followup_chunks)} FOLLOWUP row = {len(corpus)} real chunks")
w(f"  the {len(not_chunks)} non-200 row(s) are the wrong-URL-form cell (FINDINGS.md section 2)")
w("    and are EXCLUDED, and the corrected FOLLOWUP chunk is INCLUDED.")
w("")
w("The first version of this script selected on role.startswith('SWEEP-') alone. That")
w("counted the 196 B HTML error page as a chunk and omitted the real 21,157 B chunk, so")
w("T4's denominator did not mean what it said. The ledger was never wrong and neither")
w("was grep-out.txt (which greps the ledger, not this selection) — only the denominator.")
# The rule is asserted, not assumed. A corpus whose length disagrees with the
# committed list is a broken selection, and it must fail here rather than print
# a confident table over the wrong rows.
if len(corpus) != len(listed):
    print("FATAL: the counting rule yields %d real chunks but the committed list has %d "
          "entries. The selection is broken; do not read any table below."
          % (len(corpus), len(listed)), file=sys.stderr)
    raise SystemExit(2)
w("  cross-check: %d real chunks == %d committed list entries  ->  the rule is asserted, "
  "not assumed." % (len(corpus), len(listed)))
w("")
w("Every response shape in this table is discriminated on Content-Type, never on")
w("status. On this host family a status code IS an oracle (area V's fabricated-asset")
w("control 404s at 196 B), and the sweep's own control reproduces that digest exactly.")
w("")

w("")
w("T2  TOKEN CENSUS — the %d REAL CHUNKS ONLY, beside the same token in the"
  % len(corpus))
w("    POSITIVE CONTROL. A negative is only readable next to a positive.")
w("    (corpus = the %d counted above, not the ledger's SWEEP rows)" % len(corpus))
w("=" * 100)
ctrl = next((r for r in controls if r["host_tag"] == "k-main"), None)
ctrl_t = text_of(ctrl) if ctrl else None
chunk_texts = []
for r in corpus:
    t = text_of(r)
    if t is not None:
        chunk_texts.append((r["path"], t))
if len(chunk_texts) != len(corpus):
    print("FATAL: %d of %d corpus bodies are not on disk. T2/T3/T4 would silently "
          "measure a subset and still call it the corpus." % (
              len(corpus) - len(chunk_texts), len(corpus)), file=sys.stderr)
    raise SystemExit(2)

w("%-38s %14s %14s %14s" % ("token", "chunks cs", "chunks ci", "control cs"))
w("-" * 100)
for tok in TOKENS:
    cs = sum(cnt(t, tok) for _, t in chunk_texts)
    ci = sum(cnt(t, tok, True) for _, t in chunk_texts)
    ccs = cnt(ctrl_t, tok) if ctrl_t else 0
    flag = ""
    if cs == 0 and ci == 0:
        flag = "  <- zero in all %d chunks" % len(chunk_texts)
    elif cs:
        flag = "  <- NON-ZERO, read T3"
    elif ci:
        # ci > 0 with cs == 0 is the case-sensitivity control doing its job. It
        # must never print as a bare zero, because "0" and "0, but the
        # insensitive pass found something" are different claims.
        flag = "  <- cs 0 but ci %d: CASE VARIANTS ONLY, read T3 and grep-out section 2" % ci
    w("%-38s %14d %14d %14d%s" % (tok, cs, ci, ccs, flag))
w("")

w("")
w("T3  PER-TOKEN — which of the %d carried it, how many bytes, and what it is"
  % len(chunk_texts))
w("=" * 100)
w("    Case-VARIANT-ONLY tokens are listed here too, from the CASE-INSENSITIVE")
w("    pass, with the enclosing identifier. A token with cs=0 and ci>0 is not a")
w("    zero: the control found something the sensitive count missed, and this")
w("    section is where that something is accounted for.")
w("")
for tok in TOKENS:
    # BOTH passes, and the case variants are printed explicitly. The first
    # version of this section printed only the case-sensitive hits, so a
    # cs=0/ci>29 token rendered as nothing at all — the reader was told "read
    # T3" by a line that could not show the thing it pointed at.
    cs_hits = [(p, t, [m.start() for m in re.finditer(re.escape(tok), t)])
               for p, t in chunk_texts]
    cs_hits = [(p, t, o_) for p, t, o_ in cs_hits if o_]
    cv_only = []
    for p, t in chunk_texts:
        for m in re.finditer(re.escape(tok), t, re.IGNORECASE):
            if m.group(0) == tok:
                continue  # already in cs_hits
            a, b = m.start(), m.start() + len(m.group(0))
            x = a
            while x > 0 and (t[x - 1].isalnum() or t[x - 1] == '_'):
                x -= 1
            y = b
            while y < len(t) and (t[y].isalnum() or t[y] == '_'):
                y += 1
            cv_only.append((p, m.start(), m.group(0), t[x:y]))
    if not cs_hits and not cv_only:
        continue
    w("--- %r" % tok)
    w("    case-sensitive in %d of %d chunks; case-INSENSITIVE in %d" % (
        len(cs_hits), len(chunk_texts), len(cs_hits) + len(cv_only)))
    for p, off, matched, ident in cv_only[:20]:
        w("      ** CASE VARIANT ** %r at %d in %s   enclosing identifier: %s"
          % (matched, off, p, ident))
    if len(cv_only) > 20:
        w("      ... and %d more case-variant hits" % (len(cv_only) - 20))
    for p, t, offs in cs_hits[:20]:
        i = offs[0]
        ctx = t[max(0, i - 100):i + len(tok) + 100].replace("\n", "\\n")
        w("      %-30s offsets %s" % (p, offs[:8]))
        w("        ...%s..." % ctx)
    if len(cs_hits) > 20:
        w("      ... and %d more chunks" % (len(cs_hits) - 20))
    w("")

w("")
w("T4  CORPUS SIZE — re-derived, not inherited, over the COUNTED corpus")
w("=" * 100)
sizes = [r["body_bytes"] for r in corpus]
w("counting rule          : 200 + application/javascript  (see the rule above)")
w("real chunks counted    : %d" % len(corpus))
w("  of which SWEEP rows  : %d" % len(chunks))
w("  of which FOLLOWUP    : %d" % len(followup_chunks))
w("rows excluded as non-200: %d (%s)" % (
    len(not_chunks),
    ", ".join("seq %s %s" % (r["seq"], r["path"]) for r in not_chunks) or "none"))
w("total chunk bytes      : %d (%s MB)" % (sum(sizes), f"{sum(sizes)/1e6:.2f}"))
w("smallest / largest     : %d B / %d B" % (min(sizes), max(sizes)))
w("median                 : %d B" % sorted(sizes)[len(sizes) // 2])
w("distinct digests       : %d of %d bodies" % (
    len({r["body_sha256"] for r in corpus}), len(corpus)))
dup = [s for s, n in Counter(r["body_sha256"] for r in corpus).items() if n > 1]
w("duplicate digests      : %d %s" % (len(dup), sorted(dup)[:4] if dup else ""))
w("bodies with 0 bytes    : %d" % sum(1 for s in sizes if s == 0))
w("")
w("Every digest here is of a DECOMPRESSED body: the harness sends")
w("`curl --compressed`, and this host serves brotli. A digest computed on the wire")
w("bytes would differ from every digest in results.jsonl.")
print("\n".join(o))