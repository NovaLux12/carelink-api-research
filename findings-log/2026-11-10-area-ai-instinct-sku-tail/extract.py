#!/usr/bin/env python3
"""Area AI — offline extraction. ZERO requests.

Reads the two bodies the probe retained in $AI_SCRATCH and writes the extracted
rows into this log dir. Follows area H's precedent: the *extracted* rows are
committed (`family-map-verbatim.txt` there), not the raw config body.

Writes:
  family-map-verbatim.txt   the 16 family rows, verbatim, one per line
  sku-occurrences.tsv       every SKU-* and NNNNN-NN string found, with where
  tail-diff.txt             the 78961..78968 accounting, explicit per code
  drift-report-gen.txt      the report.dict's shape vs the recorded 10937 B body

Exits non-zero if it cannot find the family map's INSTINCT row, so a silent
parse failure cannot read as an absence.
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCRATCH = os.environ.get("AI_SCRATCH") or ""
if not SCRATCH or not os.path.isdir(SCRATCH):
    sys.exit("AI_SCRATCH not set / not a directory — run probe.sh first")

# Missing is a FAILURE, never an absence: every host must have both bodies.
SOURCES = [
    ("d1-carelink-minimed-com-family-map.b",      "family-map"),
    ("d2-carelink-minimed-com-report-gen.b",      "report-gen"),
    ("d1-carelink-minimed-eu-family-map.b",       "family-map"),
    ("d2-carelink-minimed-eu-report-gen.b",       "report-gen"),
    ("d1-carelink-trials-minimed-com-family-map.b","family-map"),
    ("d2-carelink-trials-minimed-com-report-gen.b","report-gen"),
]

SKU = re.compile(r'SKU-\d{5}-\d{2}')
BARE = re.compile(r'(?<![\w-])(\d{5}-\d{2})(?![\w-])')

# The range docs/05 records, and the tail area G declined to check.
LO, HI = 78893, 78968
TAIL = list(range(78961, 78969))


def unwrap(raw):
    """These dedicated routes wrap the value: {"value": "<json-encoded string>"}.

    Recorded shape — area E's per-key projection and this pass's own bodies.
    The unwrap is explicit and a failure is a failure, not an absence: if the
    envelope is present but the inner string will not parse, we raise.
    """
    doc = json.loads(raw)
    if isinstance(doc, dict) and set(doc) == {"value"} and isinstance(doc["value"], str):
        return json.loads(doc["value"]), True
    return doc, False

bodies, missing = {}, []
for fname, kind in SOURCES:
    p = os.path.join(SCRATCH, fname)
    if not os.path.exists(p):
        missing.append(fname)
        continue
    bodies[fname] = open(p, encoding="utf-8").read()

if missing:
    for m in missing:
        print(f"MISSING BODY: {m}", file=sys.stderr)
    sys.exit(3)

# ---------------------------------------------------------------- family map
# One row per family, de-duplicated ACROSS HOSTS: the three bodies are
# digest-identical, so 48 collected rows are one artefact served three times.
# The per-host count is kept in `sku-occurrences.tsv` so the multiplicity is
# visible rather than silently collapsed.
fam_lines, fam_parsed, fam_collected = [], {}, 0
for fname, kind in SOURCES:
    if kind != "family-map":
        continue
    raw = bodies[fname]
    try:
        doc, wrapped = unwrap(raw)
    except json.JSONDecodeError as e:
        sys.exit(f"family map {fname} is not JSON: {e}")
    if not isinstance(doc, dict):
        sys.exit(f"STOP: family map {fname} parsed to {type(doc).__name__}, "
                 f"not a dict — no row can be read off it")
    for fam in sorted(doc):
        fam_collected += 1
        val = doc[fam]
        if fam not in fam_parsed:
            fam_lines.append(f"{fam} ||| {json.dumps(val)}")
        fam_parsed.setdefault(fam, set()).update(
            v for v in val if isinstance(v, str))

# A collapse that hid a host disagreement would be the exact defect this repo
# forbids, so assert the host copies agree before writing one row per family.
if fam_collected != len(fam_parsed) * 3:
    sys.exit(f"STOP: {fam_collected} family rows collected but "
             f"{len(fam_parsed)} distinct × 3 hosts — the hosts disagree")

if "INSTINCT" not in fam_parsed:
    sys.exit("STOP: no INSTINCT family row parsed — an absence cannot be "
             "reported off a failed parse")
open(os.path.join(HERE, "family-map-verbatim.txt"), "w").write(
    "\n".join(fam_lines) + "\n")

# ------------------------------------------------- every SKU / bare occurrence
rows = []
for fname, kind in SOURCES:
    raw = bodies[fname]
    for m in SKU.finditer(raw):
        tok = m.group(0)
        ctx = raw[max(0, m.start() - 60):m.end() + 60].replace("\n", " ")
        rows.append((kind, "SKU-prefixed", tok, m.start(), ctx))
    for m in BARE.finditer(raw):
        tok = m.group(1)
        ctx = raw[max(0, m.start() - 60):m.end() + 60].replace("\n", " ")
        rows.append((kind, "bare", tok, m.start(), ctx))

# union across the three hosts — the bodies are digests-identical so this is
# a READ of one artefact served three times, not three sources (§2.1)
seen = {}
for kind, form, tok, off, ctx in rows:
    seen.setdefault((kind, form, tok), 0)
    seen[(kind, form, tok)] += 1

with open(os.path.join(HERE, "sku-occurrences.tsv"), "w") as f:
    f.write("document\tform\ttoken\toccurrences_across_3_hosts\n")
    for (kind, form, tok), n in sorted(seen.items(), key=lambda kv: (kv[0][0], kv[0][2])):
        f.write(f"{kind}\t{form}\t{tok}\t{n}\n")

# ------------------------------------------------------------ the tail table
instinct = sorted(fam_parsed.get("INSTINCT", set()))
instinct_sku = sorted(t for t in instinct if SKU.fullmatch(t))
instinct_bare = sorted(t for t in instinct if BARE.fullmatch(t))

# report-list entries that look like the INSTINCT alias shape
report_doc_raw = None
for fname, kind in SOURCES:
    if kind == "report-gen":
        report_doc_raw = bodies[fname]
        break
if report_doc_raw is None:
    sys.exit("STOP: report-gen document not present")
report_doc, report_wrapped = unwrap(report_doc_raw)
if not isinstance(report_doc, dict):
    sys.exit(f"STOP: report-gen parsed to {type(report_doc).__name__}, not a dict")
rl = None
for k, v in report_doc.items():
    if isinstance(v, dict) and "reportFileNamingSupportedPumpModels" in v:
        rl = v["reportFileNamingSupportedPumpModels"]
    elif k == "reportFileNamingSupportedPumpModels":
        rl = v
if rl is None:
    sys.exit("STOP: reportFileNamingSupportedPumpModels not found — the "
             "document's shape changed and no absence may be reported off it")

rl_sku = sorted({s for s in rl if isinstance(s, str) and SKU.fullmatch(s)})
rl_bare = sorted({s for s in rl if isinstance(s, str) and BARE.fullmatch(s)})

lines = []
lines.append("# Area AI — the INSTINCT range, code by code")
lines.append("")
lines.append(f"Range recorded in docs/05: SKU-{LO}-01 … SKU-{HI}-01 "
             f"({HI - LO + 1} integers in the span).")
lines.append("")
lines.append("## Present in the patient FAMILY MAP (`personal.device.family.to.model.mapping`)")
lines.append("")
lines.append(f"INSTINCT row holds {len(instinct)} strings: {len(instinct_sku)} "
             f"`SKU-NNNNN-01` + {len(instinct_bare)} bare `NNNNN-01` + placeholders.")
lines.append("")
lines.append("| code | SKU-form in map | bare form in map |")
lines.append("|---|---|---|")
for n in range(LO, HI + 1):
    s = f"SKU-{n}-01"
    b = f"{n}-01"
    lines.append(f"| `{n}` | {'yes' if s in instinct_sku else '**no**'} | "
                 f"{'yes' if b in instinct_bare else '**no**'} |")
lines.append("")
lines.append("## Present in the report-naming list (`reportFileNamingSupportedPumpModels`)")
lines.append("")
lines.append(f"List holds {len(rl)} entries; {len(rl_sku)} are `SKU-NNNNN-01` "
             f"and {len(rl_bare)} are bare `NNNNN-01`.")
lines.append("")
lines.append("| code | SKU-form in list | bare form in list |")
lines.append("|---|---|---|")
for n in range(LO, HI + 1):
    s = f"SKU-{n}-01"
    b = f"{n}-01"
    lines.append(f"| `{n}` | {'yes' if s in rl_sku else '**no**'} | "
                 f"{'yes' if b in rl_bare else '**no**'} |")
lines.append("")
lines.append("## The tail, 78961–78968, explicitly")
lines.append("")
lines.append("| code | family map | report list | first name it carries, if any |")
lines.append("|---|---|---|---|")
for n in TAIL:
    s = f"SKU-{n}-01"
    in_fam = s in instinct_sku
    in_rep = s in rl_sku
    name = ""
    if in_fam or in_rep:
        # name only exists in the portal device table, not these documents
        name = "(no display name in either document; family=list membership only)"
    else:
        name = "—"
    lines.append(f"| `{n}` | {'present' if in_fam else '**absent**'} | "
                 f"{'present' if in_rep else '**absent**'} | {name} |")
open(os.path.join(HERE, "tail-diff.txt"), "w").write("\n".join(lines) + "\n")

# ------------------------------------------------------- report-gen drift note
drift = []
drift.append("# The report.dict body is not the 2026-10-13 size")
drift.append("")
drift.append("Area E recorded `personal.common.core.report.generation` at "
             "10937 B, sha256 `2f918b71cb2889d2…` on `.com` (seq 29) and "
             "`-trials` (seq 105).")
drift.append("This pass reads **9470 B**, sha256 `ef92e9f39a1709b4…` on all "
             "three hosts — a different body, recorded as a fact, no cause "
             "asserted.")
drift.append("")
drift.append(f"`reportFileNamingSupportedPumpModels` holds **{len(rl)}** entries "
             f"here. The 2026-11-03 drift pass measured 236 and committed the "
             f"list verbatim; the 2026-10-13 area H pass measured 214.")
drift.append("")
drift.append("Top-level keys of the document, with the type and length of each:")
drift.append("")
for k in sorted(report_doc):
    v = report_doc[k]
    if isinstance(v, list):
        drift.append(f"- `{k}` — list, {len(v)}")
    elif isinstance(v, dict):
        drift.append(f"- `{k}` — dict, {len(v)} keys: {', '.join(sorted(v))}")
    else:
        drift.append(f"- `{k}` — {type(v).__name__}: {v!r}")
open(os.path.join(HERE, "drift-report-gen.txt"), "w").write("\n".join(drift) + "\n")

print(f"family map: {len(fam_parsed)} families; INSTINCT {len(instinct)} strings "
      f"({len(instinct_sku)} SKU + {len(instinct_bare)} bare)")
print(f"report list: {len(rl)} entries ({len(rl_sku)} SKU + {len(rl_bare)} bare)")
print("tail 78961-78968 in family map: " +
      ", ".join(f"{n}={'Y' if f'SKU-{n}-01' in instinct_sku else 'N'}" for n in TAIL))
print("tail 78961-78968 in report list: " +
      ", ".join(f"{n}={'Y' if f'SKU-{n}-01' in rl_sku else 'N'}" for n in TAIL))
