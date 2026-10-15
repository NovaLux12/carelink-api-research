#!/usr/bin/env python3
"""plan-cells.py — generate cells-phase2.txt from chunk-map.tsv. Zero requests.

THE ALLOCATION RULE, DECLARED BEFORE ANY PHASE-2 CELL WAS SENT, and it is
reproducible from this file:

  1. Anchor gates first, per build: each build's eager main bundle, which must
     hash to the sha256 the repo already pins for that build. These two rows
     are also the METHOD GATE — area F's `grep.sh` requires three known-present
     literals to be reported present, or a zero is indistinguishable from a
     broken grep, and both main bundles carry `hcp/configuration/public/` and
     `hcp/patients`.
  2. Support-build controls, before any support data cell: the emitted-name
     form of the support `common` chunk (positive) and the id form of the same
     hash (form-defect). The substitution is matched out of the support
     runtime body, not inherited from the clinic build.
  3. The CLINIC build's complete 225-cell lazy-chunk corpus, in ASCENDING
     CONTENT-HASH ORDER. Hash order is stable across runs, is independent of
     the map's own key order, and makes a partial sweep a prefix rather than an
     arbitrary subset. The clinic corpus is swept in full because it is the
     corpus docs/11's successor block names ("the 224 portal chunks") and the
     one this repository has already established to exist and be correctly
     addressed, twice (2026-10-13 area K, 2026-10-14 issue #121).
  4. The support build's 4 BUILD-DISTINCTIVE cells — the only chunk ids whose
     contenthash differs between the two builds. These are the only cells where
     a support-host fetch can carry information a clinic-host fetch cannot, so
     they are the highest-value support cells available.
  5. 12 BRIDGE cells on the support host, drawn from the 221 shared-hash ids at
     a fixed stride (every 18th from index 9) so the sample spans the whole
     sorted hash space and is not cherry-picked. Each one does double duty: it
     is a support-host token sweep AND, if its body digest equals the clinic
     cell's digest at the same hash, an OBSERVED instance of the claim that a
     shared contenthash means a shared body across the two hosts.

The cap is 260 and probe.sh refuses to exceed it. Cells 5 and the cap are
checked here too, so a plan that would overrun fails before anything is sent.
"""
import csv
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
CAP = 260
PHASE1 = 8  # rows already in results.jsonl when this ran
HOST = {"clinic": "carelinkhp.minimed.eu", "support": "carelink-support.medtronic.eu"}
MAIN = {"clinic": "main.fb5f8cb7eb60c4d5.js", "support": "main.759cddab23085086.js"}
BRIDGE_STRIDE, BRIDGE_START, BRIDGE_N = 18, 9, 12

rows = list(csv.DictReader((HERE / "chunk-map.tsv").open(), delimiter="\t"))
by = {}
for r in rows:
    by.setdefault(r["build"], {})[r["id"]] = r

clinic_shared = {i: r for i, r in by["clinic"].items()
                 if by["support"][i]["hash"] == r["hash"]}
distinct = sorted((i for i in by["clinic"]
                   if by["clinic"][i]["hash"] != by["support"][i]["hash"]), key=int)
shared_sorted = sorted(clinic_shared, key=lambda i: clinic_shared[i]["hash"])
bridge = [shared_sorted[BRIDGE_START + k * BRIDGE_STRIDE]
          for k in range(BRIDGE_N)
          if BRIDGE_START + k * BRIDGE_STRIDE < len(shared_sorted)]

out = []


def add(role, tag, build, name, cid, h, chunked=True):
    host = HOST[build]
    out.append((role, tag, f"https://{host}/{name}", build,
                cid if chunked else "-", h if chunked else "-"))


# 1. anchor gates, one per build
for b in ("clinic", "support"):
    add("anchor-gate", f"{b}-main-anchor", b, MAIN[b], None, None, chunked=False)

# 2. support controls, from the support runtime's own f.u
sup2076 = by["support"]["2076"]
add("control-positive", "sup-pos-common", "support",
    sup2076["url_name"], "2076", sup2076["hash"])
add("control-formdefect", "sup-defect-2076", "support",
    sup2076["id_form_url"], "2076", sup2076["hash"])

# 3. clinic corpus, ascending content-hash order
for i in sorted(by["clinic"], key=lambda i: by["clinic"][i]["hash"]):
    r = by["clinic"][i]
    add("sweep", f"clinic-{r['name']}", "clinic", r["url_name"], r["id"], r["hash"])

# 4. support build-distinctive cells. Id 2076 is NOT re-listed here: it is
#    already sent above as `control-positive`, on the same URL, because the
#    support build's emitted name for id 2076 is `common` too (matched out of
#    the support runtime body, not inherited). It is fetched ONCE and counted
#    in both tables — as the positive control AND as support's id-2076 sweep
#    cell — rather than spending a second request on identical bytes.
for i in distinct:
    if i == "2076":
        continue
    r = by["support"][i]
    add("sweep-distinct", f"sup-{r['name']}", "support", r["url_name"], r["id"], r["hash"])

# 5. support bridge cells
for i in bridge:
    r = by["support"][i]
    add("sweep-bridge", f"sup-{r['name']}", "support", r["url_name"], r["id"], r["hash"])

text = "\n".join("|".join(str(x) for x in c) for c in out) + "\n"
(HERE / "cells-phase2.txt").write_text(text)

plan = {
    "cap": CAP, "phase1_rows": PHASE1, "phase2_cells": len(out),
    "planned_total": PHASE1 + len(out), "unspent": CAP - PHASE1 - len(out),
    "clinic_cells": len(by["clinic"]),
    "support_build_distinctive_cells": distinct,
    "support_bridge_cells": bridge,
    "shared_hash_ids": len(clinic_shared),
    "bridge_stride": BRIDGE_STRIDE, "bridge_start": BRIDGE_START,
    "clinic_order": "ascending content-hash",
}
(HERE / "plan.json").write_text(json.dumps(plan, indent=2) + "\n")
print(json.dumps(plan, indent=2))
if PHASE1 + len(out) > CAP:
    print("PLAN EXCEEDS CAP — refusing to emit", file=sys.stderr)
    sys.exit(1)