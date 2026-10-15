#!/usr/bin/env python3
"""verify-derivable.py — re-derive every claim this pass says is re-derivable
from its committed artefacts. ZERO requests, no network, no SCRATCH.

WHY THIS EXISTS. The response bodies are not committed (AGENTS.md section 7) and
were written to a `mktemp -d` that no longer exists, so the byte-level reads in
FINDINGS.md section 5c cannot be reproduced by a stranger from a clean clone.
That is a real limit and FINDINGS.md section 8b names it. What this script does
is close the OTHER half properly: every claim whose inputs ARE committed gets a
machine check that runs offline and exits non-zero on any mismatch, so "re-
derivable" is a property of the directory rather than a promise in prose.

It is deliberately separate from sweep.py / spacing.py, which regenerate the
PASS's own artefacts. This one asserts the published numbers against those
artefacts. A disagreement between the two is the signal worth having.

What it checks, and what it deliberately does NOT:

  CHECKED   ledger shape and the request accounting
            the content-type gate: 0 of 240 sweep cells returned the SPA shell
            the redundant request, present and counted
            the per-build 24-token census
            the method gate and the case-sensitivity control
            both spacing series, the negative durations, the three large gaps
            the section 2d overhead arithmetic and its unexplained rows
            the chunk map: id sets, 221 shared hashes, the 4 differing ids
            the by-hash diff against area K's committed map
            the 12-cell bridge selection and 12-of-12 byte identity
            distinct-diff.json internal arithmetic
            run.log regenerates byte-identically from the ledger

  NOT CHECKED (and FINDINGS.md section 8b says so, per claim)
            per-hit byte offsets and quoted minified source -- bodies gone
            that the five divergent bytes are the ONLY divergence -- bodies gone

Usage: ./verify-derivable.py [dir]      exit 0 = every stated figure holds
"""
import csv
import hashlib
import json
import pathlib
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone

HERE = pathlib.Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else pathlib.Path(__file__).resolve().parent


def find_repo_root(start):
    """Walk upward for the checkout root, identified by AGENTS.md.

    NOT `parents[1]`. That form only resolves at exactly
    `<repo>/findings-log/<name>/`, so a copy anywhere else -- `.loop/vr3/<pass>/`,
    a scratch mirror -- raised FileNotFoundError on committed-map.txt and exited 1
    before checking anything, which reads as "the checker is red" rather than
    "the checker could not find its inputs" (verification round 3). Searching
    upward for AGENTS.md works at any depth and in a worktree.
    """
    for cand in [start, *start.parents]:
        if (cand / "AGENTS.md").is_file() and (cand / "findings-log").is_dir():
            return cand
    raise SystemExit(
        "verify-derivable: no checkout root above %s -- expected a directory "
        "holding both AGENTS.md and findings-log/. Pass the pass directory "
        "explicitly, or run it from inside the checkout." % start)


REPO = find_repo_root(HERE)
LEDGER = HERE / "results.jsonl"
DECLARED, FLOOR, LOCKD = 2.5, 2.0, 2.5
CAP = 260

# The one token list this pass is allowed to use: area F's, verbatim.
TOKENS = ['patient-timeline', 'dialog-lite', 'app-patient-timeline', 'patientTimeline',
          'personal.patient.timeline.config', 'personal.patient.timeline.host', 'execute-api',
          '0ptoikank6', 'r5djbmetbb', 'd4mwt26mmi', '7r9xxd72kk', 'oflhmnvbe6', 'prodous',
          'm2m', 'baseUrl', 'hcp/configuration/public/', 'hcp/patients', '/patient/',
          'clcloud', 'carelink.minimed', 'timeline', 'Timeline', 'TIMELINE', 'personal.']
ANCHORS = {'clinic': '2a7fa8e7af519c2b', 'support': 'a054555a0f22176e'}
SHELL_BYTES = 5518
SWEEP_ROLES = {'sweep', 'sweep-distinct', 'sweep-bridge'}

FAILS, CHECKS = [], [0]


def ck(label, got, want):
    CHECKS[0] += 1
    if got == want:
        if isinstance(got, (list, tuple, dict, set)) and len(got) > 8:
            k = f"{len(got)} items" if not isinstance(got, dict) else f"{len(got)} keys"
            shown = f"{k} (values elided)"
        else:
            shown = got
        print(f"  ok   {label}: {shown}")
    else:
        print(f"  FAIL {label}: got {got!r}, want {want!r}")
        FAILS.append(label)


def t_ms(s):
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc).timestamp()


def t_s(s):
    return int(datetime.strptime(s[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc).timestamp())


rows = [json.loads(l) for l in LEDGER.read_text().splitlines() if l.strip()]
rows.sort(key=lambda r: r["seq"])

print("=" * 74)
print("A. ledger shape and request accounting")
seqs = [r["seq"] for r in rows]
ck("rows", len(rows), 252)
ck("seq contiguous 1..252", seqs, list(range(1, 253)))
ck("methods", dict(Counter(r["method"] for r in rows)), {"GET": 252})
ck("hosts", dict(Counter(r["host"] for r in rows)),
   {"carelinkhp.minimed.eu": 231, "carelink-support.medtronic.eu": 21})
ck("statuses", dict(Counter(r["status"] for r in rows)), {"200": 252})
roles = Counter(r["role"] for r in rows)
CONTROL_ROLES = {'control-absent', 'control-positive', 'control-formdefect',
                 'corpus-entry', 'corpus-runtime', 'anchor-gate'}
ck("control / map-derivation rows",
   sum(v for k, v in roles.items() if k in CONTROL_ROLES), 12)
ck("sweep cells", sum(v for k, v in roles.items() if k in SWEEP_ROLES), 240)
ck("under cap", len(rows) <= CAP, True)

print("\nB. content-type gate -- status is never the discriminator")
for b, n in (("clinic", 225), ("support", 15)):
    cells = [r for r in rows if r["role"] in SWEEP_ROLES and r["build"] == b]
    js = [r for r in cells if (r.get("content_type") or "").startswith("application/javascript")]
    shell = [r for r in cells if r["body_bytes"] == SHELL_BYTES
             or (r.get("content_type") or "").startswith("text/html")]
    ck(f"{b} sweep cells", len(cells), n)
    ck(f"{b} returned a chunk", len(js), n)
    ck(f"{b} returned the SPA shell", len(shell), 0)
    ck(f"{b} distinct body digests", len({r["body_sha256"] for r in js}), n)
    ck(f"{b} empty bodies", len([r for r in cells if r["body_bytes"] == 0]), 0)
ck("fallback cells overall", len([r for r in rows if r["body_bytes"] == SHELL_BYTES]), 6)
ck("clinic decoded bytes", sum(r["body_bytes"] for r in rows
                               if r["role"] in SWEEP_ROLES and r["build"] == "clinic"), 4374660)
ck("support decoded bytes", sum(r["body_bytes"] for r in rows
                                if r["role"] in SWEEP_ROLES and r["build"] == "support"), 861735)

print("\nC. the redundant request is present and counted, not dropped")
dup = [(k, v) for k, v in Counter((r["host"], r["path"]) for r in rows).items() if v > 1]
ck("duplicate (host,path) count", len(dup), 1)
ck("duplicate is the clinic positive control",
   dup[0][0] if dup else None,
   ("carelinkhp.minimed.eu", "common.a62bb847b4ea289e.js"))
pair = sorted(r["seq"] for r in rows if r["path"] == "common.a62bb847b4ea289e.js")
ck("duplicate seqs", pair, [4, 151])
ck("bodies byte-identical",
   len({r["body_sha256"] for r in rows if r["seq"] in pair}), 1)

print("\nD. the 24-token census, per build, never pooled")
ck("ledger token keys == area F's list, verbatim",
   sorted({k for r in rows for k in r["tokens"]}), sorted(TOKENS))
NONZERO = {"clinic": ["hcp/patients", "personal.", "timeline", "Timeline"],
           "support": ["hcp/patients", "personal.", "Timeline"]}
for b in ("clinic", "support"):
    cells = [r for r in rows if r["role"] in SWEEP_ROLES and r["build"] == b
             and (r.get("content_type") or "").startswith("application/javascript")]
    agg = Counter()
    for r in cells:
        agg.update({k: v for k, v in r["tokens"].items() if v})
    ck(f"{b} non-zero tokens", sorted(agg), sorted(NONZERO[b]))
    # every token outside that named set reads exactly 0 -- which is the claim
    # "every service-identifying token is 0", stated as an exhaustive partition
    ck(f"{b} every other token reads exactly 0",
       sorted(t for t in TOKENS if not agg[t]), sorted(t for t in TOKENS if t not in NONZERO[b]))
    ck(f"{b} m2m across all its cells", agg["m2m"], 0)

# MAGNITUDES, not just the name set. docs/11 publishes these exact numbers, and a
# name-set-only check let a mutated count through (verification round 2): the set
# was unchanged, so every assertion above still passed on a wrong number.
MAGNITUDE = {
    "clinic": {"Timeline": 104, "timeline": 44, "personal.": 23, "hcp/patients": 1},
    "support": {"Timeline": 4, "personal.": 14, "hcp/patients": 1},
}
for b in ("clinic", "support"):
    cells = [r for r in rows if r["role"] in SWEEP_ROLES and r["build"] == b
             and (r.get("content_type") or "").startswith("application/javascript")]
    agg = Counter()
    for r in cells:
        agg.update({k: v for k, v in r["tokens"].items() if v})
    for tok, want in MAGNITUDE[b].items():
        ck(f"{b} census magnitude {tok}={want}", agg[tok], want)
ck("the four scored clinic tokens sum to the published 148+23+1",
   sum(MAGNITUDE["clinic"].values()), 172)
ck("clinic timeline+Timeline == the published 148",
   MAGNITUDE["clinic"]["timeline"] + MAGNITUDE["clinic"]["Timeline"], 148)
ck("support timeline+Timeline == the published 4",
   MAGNITUDE["support"]["Timeline"], 4)
# support includes the seq-11 positive control, which is also its 2076 cell
sup16 = [r for r in rows if r["build"] == "support"
         and (r["role"] in SWEEP_ROLES or r["seq"] == 11)
         and (r.get("content_type") or "").startswith("application/javascript")]
ck("support cells incl. the 2076 control", len(sup16), 16)

print("\nE. method gate and case-sensitivity control")
for b in ANCHORS:
    m = next(r for r in rows if r["role"] == "anchor-gate" and r["build"] == b)
    t = m["tokens"]
    ck(f"{b} anchor sha256_16", m["body_sha256"][:16], ANCHORS[b])
    ck(f"{b} hcp/configuration/public/", t["hcp/configuration/public/"], 15)
    ck(f"{b} hcp/patients", t["hcp/patients"], 42)
    ck(f"{b} three-form timeline total", t["timeline"] + t["Timeline"] + t["TIMELINE"], 196)
c = rows[35]["tokens"]
ck("seq 36 Timeline", c["Timeline"], 84)
ck("seq 36 timeline", c["timeline"], 44)
ck("seq 36 TIMELINE", c["TIMELINE"], 0)
ck("seq 105 all 24 tokens 0",
   len([v for v in rows[104]["tokens"].values() if v]), 0)

print("\nF. both spacing series, same-host pairs in request order")
per_host = defaultdict(list)
for r in rows:
    per_host[r["host"]].append(r)
for host, rs in sorted(per_host.items()):
    gaps = [round(t_ms(b["t_sent"]) - t_ms(a["t_sent"]), 3) for a, b in zip(rs, rs[1:])]
    ck(f"{host} t_sent gaps", len(gaps), len(rs) - 1)
    if host == "carelinkhp.minimed.eu":
        ck(f"{host} t_sent min", min(gaps), 1.801)
        ck(f"{host} t_sent under declared", len([g for g in gaps if g < DECLARED]), 29)
        ck(f"{host} t_sent under floor", len([g for g in gaps if g < FLOOR]), 9)
    else:
        ck(f"{host} t_sent min", min(gaps), 2.213)
        ck(f"{host} t_sent under declared", len([g for g in gaps if g < DECLARED]), 1)
        ck(f"{host} t_sent under floor", len([g for g in gaps if g < FLOOR]), 0)
    mg = [t_s(b["body_mtime"]) - t_s(a["body_mtime"]) for a, b in zip(rs, rs[1:])]
    ck(f"{host} mtime min", min(mg), 2)
    ck(f"{host} mtime under floor", len([g for g in mg if g < FLOOR]), 0)
neg = [r["seq"] for r in rows if t_ms(r["t_done"]) < t_ms(r["t_sent"])]
ck("negative durations", len(neg), 28)

print("\nG. the three gaps above 11.892 s, and their stated causes")
big = []
for host, rs in sorted(per_host.items()):
    for a, b in zip(rs, rs[1:]):
        g = round(t_ms(b["t_sent"]) - t_ms(a["t_sent"]), 3)
        if g > 11.892:
            big.append((a["seq"], b["seq"], g))
big.sort()
ck("gaps > 11.892 s", len(big), 3)
ck("gaps > 11.892 s, as (seqA,seqB,gap)", big,
   [(5, 9, 101.048), (8, 10, 95.997), (12, 238, 602.961)])
clinic = [r["seq"] for r in rows if r["build"] == "clinic" and 13 <= r["seq"] <= 237]
ck("clinic phase-2 sweep rows between the two support gaps", len(clinic), 225)
ck("that sweep's t_sent span",
   round(t_ms(rows[236]["t_sent"]) - t_ms(rows[12]["t_sent"]), 3), 597.040)

print("\nH. FINDINGS.md section 2d -- gap = 2.5 + dur[prev] + overhead")
dur = {r["seq"]: round(t_ms(r["t_done"]) - t_ms(r["t_sent"]), 3) for r in rows}
fits, misses = [], []
for host, rs in sorted(per_host.items()):
    for a, b in zip(rs, rs[1:]):
        g = round(t_ms(b["t_sent"]) - t_ms(a["t_sent"]), 3)
        if g >= DECLARED:
            continue
        ov = round(g - LOCKD - dur[a["seq"]], 3)
        (fits if 0.086 <= ov <= 0.099 else misses).append((a["seq"], b["seq"], g, dur[a["seq"]], ov))
ck("short gaps (under declared) total", len(fits) + len(misses), 30)
ck("explained by the identity", len(fits), 26)
ck("unexplained by the identity", len(misses), 4)
ck("every explained row has a negative predecessor duration",
   all(x[3] < 0 for x in fits), True)
ck("every unexplained row has a POSITIVE predecessor duration",
   all(x[3] > 0 for x in misses), True)
ck("the two unexplained sub-floor gaps",
   sorted(x[0] for x in misses if x[2] < FLOOR), [230, 236])
ck("overhead range", (min(x[4] for x in fits), max(x[4] for x in fits)), (0.086, 0.099))

print("\nI. chunk map: id sets, shared hashes, the four that differ")
# FINDINGS.md section 8a fact #2 cites special_case_id_to_name, which lives in
# chunk-map.json -- so this section reads the JSON as well as the TSV. Before
# verification round 2 the checker read the TSV only, which meant a claim sourced
# from the JSON was checked nowhere.
mp = list(csv.DictReader((HERE / "chunk-map.tsv").open(), delimiter="\t"))
CM = json.loads((HERE / "chunk-map.json").read_text())
for b in ("clinic", "support"):
    d = CM["builds"][b]
    ck(f"{b} JSON f.u special case is 2076 -> common",
       d["special_case_id_to_name"], {"id": "2076", "name": "common"})
    ck(f"{b} JSON entries", len(d["entries"]), 225)
    ck(f"{b} JSON n_entries / duplicate ids / distinct hashes",
       (d["n_entries"], d["n_duplicate_ids"], d["distinct_hashes"]), (225, 0, 225))
    # the truncation note must survive, or the display field reads as the whole f.u
    ck(f"{b} JSON marks the expression as a truncated prefix",
       (d.get("f_u_expression_truncated_at"),
        "DISPLAY PREFIX ONLY" in d.get("f_u_expression_note", "")),
       (400, True))
    ck(f"{b} JSON and TSV agree on all 225 (id, name, hash)",
       {i: (r["name"], r["hash"]) for i, r in
        {x["id"]: x for x in mp if x["build"] == b}.items()},
       {i: (n, h) for i, h in d["entries"].items()
        for n in [next(x["name"] for x in mp if x["build"] == b and x["id"] == i)]})
ck("JSON cross_build shared_hashes", CM["cross_build"]["shared_hashes"], 221)
ck("JSON vs_committed name/id differences are both empty",
   (CM["vs_committed_clinic_map"]["name_differences"],
    CM["vs_committed_clinic_map"]["id_differences"]), ([], []))
ck("JSON vs_committed shared hashes", CM["vs_committed_clinic_map"]["shared_hashes"], 225)
ck("JSON vs_committed only-in lists are both empty",
   (CM["vs_committed_clinic_map"]["hashes_only_in_re_derived"],
    CM["vs_committed_clinic_map"]["hashes_only_in_committed"]), ([], []))

by = defaultdict(dict)
for r in mp:
    by[r["build"]][r["id"]] = r
cl, su = by["clinic"], by["support"]
ck("clinic ids", len(cl), 225)
ck("support ids", len(su), 225)
ck("identical id sets", set(cl) == set(su), True)
ck("distinct hashes per build", (len({r["hash"] for r in cl.values()}),
                                 len({r["hash"] for r in su.values()})), (225, 225))
ck("ids sharing a contenthash", len([i for i in cl if cl[i]["hash"] == su[i]["hash"]]), 221)
ck("the 4 that differ", sorted((i for i in cl if cl[i]["hash"] != su[i]["hash"]), key=int),
   ["2076", "2873", "6831", "8285"])
ck("the 2076 -> common substitution on clinic", (cl["2076"]["name"], cl["2076"]["hash"]),
   ("common", "a62bb847b4ea289e"))
ck("the 2076 -> common substitution on support, out of ITS OWN runtime",
   (su["2076"]["name"], su["2076"]["hash"]), ("common", "f55548f9efbc71ce"))
ck("names differ between builds", len([i for i in cl if cl[i]["name"] != su[i]["name"]]), 0)

print("\nJ. by-hash diff against area K's committed clinic map")
cm = REPO / "findings-log/2026-10-14-area-k-clinic-controlflow/committed-map.txt"
com = {}
for line in cm.read_text().splitlines():
    p = line.split()
    if len(p) == 3:
        com[p[0]] = (p[1], p[2])
ck("committed map rows", len(com), 225)
# "id differences" is asserted as SET EQUALITY, checked BEFORE any per-id lookup,
# so it fires cleanly and by name in either direction.
#
# The line this replaces was `[i for i in cl if i != com[i][0] and False]`: `com`
# is keyed BY id, so `com[i][0]` is the NAME, and the trailing `and False`
# hard-wired the result to [] -- a check that could not fail on any data while
# counting toward this script's headline (verification round 3). Two things
# replace it:
#   * set equality, which is stronger than a difference count and falsifiable in
#     both directions without raising;
#   * ordering, because the old form was also shadowed -- a *missing* key makes
#     the per-id lookup below raise KeyError and abort the whole run before any
#     boolean could report it. Checking the sets first turns that crash into a
#     named failure. The KeyError remains as a backstop.
ck("committed id keys == re-derived id keys (id differences = 0)", set(com) == set(cl), True)
ck("committed rows whose id is absent from the re-derived map",
   sorted(set(com) - set(cl)), [])
ck("re-derived ids the committed map never carried",
   sorted(set(cl) - set(com)), [])
ck("shared hashes", len([i for i in cl if cl[i]["hash"] == com[i][1]]), 225)
ck("only in re-derived", sorted({cl[i]["hash"] for i in cl} - {v[1] for v in com.values()}), [])
ck("only in committed", sorted({v[1] for v in com.values()} - {cl[i]["hash"] for i in cl}), [])
ck("name differences", [i for i in cl if cl[i]["name"] != com[i][0]], [])

print("\nK. the bridge: stride 18 from index 9, and 12 of 12 byte-identical")
shared = sorted({cl[i]["hash"] for i in cl if cl[i]["hash"] == su[i]["hash"]})
bridge = [shared[9 + k * 18] for k in range(12)]
ck("bridge cells selected", len(bridge), 12)
ck("bridge hashes match the ledger's support cells",
   sorted(r["chunk_hash"] for r in rows if r["role"] == "sweep-bridge"), sorted(bridge))
clinic_by_hash = {r["chunk_hash"]: r for r in rows if r["build"] == "clinic" and r["chunk_hash"]}
sup_bridge = sorted((r for r in rows if r["role"] == "sweep-bridge"), key=lambda r: r["seq"])
ck("byte-identical to the clinic cell at the same hash",
   len([r for r in sup_bridge
        if clinic_by_hash.get(r["chunk_hash"], {}).get("body_sha256") == r["body_sha256"]]), 12)

print("\nL. distinct-diff.json internal arithmetic")
dd = json.loads((HERE / "distinct-diff.json").read_text())
ck("four distinct pairs", len(dd), 4)
for x in dd:
    tot = x["longest_common_prefix"] + x["divergent_middle_bytes_clinic"] + x["longest_common_suffix"]
    CHECKS[0] += 1
    if tot == x["clinic_bytes"] == x["support_bytes"] and x["length_delta"] == 0 \
            and x["divergent_middle_bytes_clinic"] == 5 == x["divergent_middle_bytes_support"] \
            and not x["identical"] and x["clinic_sha256_16"] != x["support_sha256_16"]:
        print(f"  ok   id {x['chunk_id']}: {x['longest_common_prefix']} + 5 + "
              f"{x['longest_common_suffix']} = {tot} = body_bytes, digests differ")
    else:
        print(f"  FAIL id {x['chunk_id']}: arithmetic does not close")
        FAILS.append(f"distinct-diff id {x['chunk_id']}")

print("\nM. the four distinct pairs, from the ledger alone")
for a, b, cid in ((4, 11, "2076"), (225, 238, "2873"), (120, 239, "6831"), (185, 240, "8285")):
    A, B = rows[a - 1], rows[b - 1]
    ck(f"id {cid} equal body_bytes, different sha256",
       (A["body_bytes"] == B["body_bytes"], A["body_sha256"] != B["body_sha256"]), (True, True))
    ck(f"id {cid} identical token census",
       {k: v for k, v in A["tokens"].items() if v},
       {k: v for k, v in B["tokens"].items() if v})

print("\nN. run.log regenerates byte-identically from the ledger")
buf = []
for r in rows:
    buf.append("\t".join(str(x if x is not None else "") for x in (
        r["t_queued"], r["t_sent"], r["t_done"], r.get("body_mtime"), r["host"],
        r["method"], r["url"], r["status"], r.get("content_type"),
        r["body_bytes"], r["role"], r["tag"])) + "\n")
ck("run.log is a rendering of the ledger, not a second record",
   "".join(buf) == (HERE / "run.log").read_text(), True)

print("\n" + "=" * 74)
if FAILS:
    print(f"FAIL -- {len(FAILS)} of {CHECKS[0]} checks disagree with the published figures:")
    for f in FAILS:
        print(f"  - {f}")
    print("\nNOT CHECKED HERE, and FINDINGS.md section 8b says so per claim:")
    print("  - per-hit byte offsets and quoted minified source (bodies gone)")
    print("  - that the five divergent bytes are the ONLY divergence (bodies gone)")
    sys.exit(1)
print(f"PASS -- all {CHECKS[0]} stated figures re-derive from the committed artefacts, zero requests.")
print("NOT CHECKED HERE, and FINDINGS.md section 8b says so per claim:")
print("  - per-hit byte offsets and quoted minified source (bodies gone)")
print("  - that the five divergent bytes are the ONLY divergence (bodies gone)")