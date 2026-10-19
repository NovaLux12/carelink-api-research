#!/usr/bin/env python3
"""plan.py — lane l2. Zero vendor requests.

Two jobs, in this order, and the second cannot run if the first fails.

1. ASSERT THE CORPUS CONTROL. Every bundle fetched by `probe.sh bundles` must
   reproduce the sha256 this repository already records for it, at a named
   file:line. On this host family the catch-all IS the entry document, so a
   content-hashed chunk is the only thing that detects a deployment; if a digest
   does not reproduce, that host serves a build no recorded key list applies to
   and the pass STOPS for that host rather than extrapolating onto it.

2. BUILD THE REQUEST PLAN. Each host's candidate list is extracted offline from
   THAT host's own bundle route table. No key is typed from memory, no key is
   inherited from another host, and docs/07 is never used as a candidate source
   (it is the page being tested, not the page the plan is read from). Controls
   are placed first per host.

Writes plan.json and plan.md — the human-readable reasoning, one line per
candidate, written BEFORE the request goes out.
"""
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))

# ---- the recorded anchors, each with the file:line that records it -------------
CLINIC = {
    "asset": "/main.fb5f8cb7eb60c4d5.js",
    "bytes": 3397615,
    "sha256": "2a7fa8e7af519c2b493caf62c00b46c5e75a357048444dbf7abff6136bfc02ba",
    "asset_src": "findings-log/probe-2026-10-08/AUTH-TENANT-FINDINGS.md:248-249",
    "digest_src": "findings-log/2026-10-14-area-k-clinic-controlflow/differential.py:142",
    "tag": "b01-carelinkhp-minimed-eu-clinic-asset",
    "build": "A / clinic pow",
}
SUPPORT = {
    "asset": "/main.759cddab23085086.js",
    "bytes": 3410666,
    "sha256": "a054555a0f22176ecb51d8f6439680a394e2be5e889494bec5004c93be28c954",
    "asset_src": "findings-log/2026-10-13-area-g-device-tables/FINDINGS.md:70",
    "digest_src": "findings-log/2026-10-13-area-g-device-tables/FINDINGS.md:70",
    "tag": "b04-carelink-support-medtronic-com-support-asset",
    "build": "B / support cua",
}

CLINIC_HOSTS = ["carelink.medtronic.com", "carelink.medtronic.eu"]
CLINIC_TAGS = ["b01-carelinkhp-minimed-eu-clinic-asset",
               "b02-carelink-medtronic-com-clinic-asset",
               "b03-carelink-medtronic-eu-clinic-asset"]
SUPPORT_HOST = "carelink-support.medtronic.com"

P = "/hcp/configuration/public/"
ABSENT = P + "zzz.this.does.not.exist.zzz"        # HCP-CONFIG-SCHEMA.md:108
CASE_UP = P + "CSU.CONTROL.CODES.SETTINGS"         # HCP-CONFIG-SCHEMA.md:121,188
CASE_LO = P + "cua.control.codes.settings"         # HCP-CONFIG-SCHEMA.md:125,155
HDR_ABSENT_KEY = P + "logbook.supported.entry.types"  # docs/07:222-230 (one of the nine 412 siblings)
PROWEB = "X-System-ID: ProWeb"

ROUTE = re.compile(rb"hcp/configuration/public/([A-Za-z0-9._?=&/()-]+)")
# The one templated literal. Area K measured that exactly 1 of the build's route
# literals carries a query string and that its only marker is ((countryCode))
# (2026-10-14-area-k-clinic-controlflow/FINDINGS.md:301 §3i, and :128 for the
# substitution mechanism). It is instantiated here with the value this repository
# already recorded for that exact URL — HCP-CONFIG-SCHEMA.md:185 measured
# `?countryCode=EU` -> 200/423 B on carelinkhp — so that the cell is directly
# comparable to the record it is testing for portability. The marker is never sent.
TEMPLATE_SUBST = {"countryCode=((countryCode))": "countryCode=EU"}


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%3NZ")


def load_ledger(path):
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]


def assert_corpus(rows, spec):
    """Return the recorded ledger row for a bundle tag, or exit non-zero."""
    r = next((x for x in rows if x["tag"] == spec["tag"]), None)
    if r is None:
        die(f"no corpus-control row for {spec['tag']}")
    if r["http_status"] != "200":
        die(f"{spec['tag']}: status {r['http_status']}, expected 200")
    if "javascript" not in (r["content_type"] or ""):
        die(f"{spec['tag']}: content-type {r['content_type']} — the catch-all "
            f"answered, so this host served NO build (AGENTS.md §7 / area A)")
    if r["body_sha256"] != spec["sha256"]:
        die(f"{spec['tag']}: sha256 {r['body_sha256'][:16]}… != recorded "
            f"{spec['sha256'][:16]}… ({spec['digest_src']}). This host serves a "
            f"build no recorded key list applies to. STOP for this host; do not "
            f"extrapolate a key list onto it.")
    if r["body_bytes"] != spec["bytes"]:
        # Not fatal — the digest is the assertion — but it is recorded either way.
        sys.stderr.write(f"WARN {spec['tag']}: bytes {r['body_bytes']} != recorded "
                         f"{spec['bytes']} (digest matched)\n")
    return r


def die(msg):
    sys.stderr.write("STOP: " + msg + "\n")
    sys.exit(2)


def route_literals(path):
    body = open(path, "rb").read()
    seen, occ, templated = set(), 0, []
    for m in ROUTE.finditer(body):
        occ += 1
        raw = m.group(1).decode()
        for marker, value in TEMPLATE_SUBST.items():
            if raw.endswith(marker):
                raw = raw[: -len(marker)] + value
                templated.append((raw, marker, value))
        seen.add(raw)
    return sorted(seen), occ, templated, body


def build_plan():
    ledger = os.path.join(HERE, "results.jsonl")
    rows = load_ledger(ledger)
    assets = os.environ.get("L2_ASSETS")

    # ---- 1. corpus control ---------------------------------------------------
    for t in CLINIC_TAGS:
        assert_corpus(rows, dict(CLINIC, tag=t))
    assert_corpus(rows, SUPPORT)

    # ---- 2. each host's own route table -------------------------------------
    # carelinkhp's fetch is the clinic list; the two other clinic hosts are
    # asserted byte-identical to it by the three digest assertions above, so one
    # extraction covers all three — that is the portability claim being tested,
    # and it is made from the corpus control rather than assumed.
    clinic_key_path = os.path.join(assets, CLINIC["tag"] + ".b.assets")
    support_key_path = os.path.join(assets, SUPPORT["tag"] + ".b.assets")
    for p in (clinic_key_path, support_key_path):
        if not os.path.exists(p):
            die(f"missing fetched bundle body {p} — run `probe.sh bundles` first")

    ckeys, cocc, ctempl, cbody = route_literals(clinic_key_path)
    skeys, socc, stempl, sbody = route_literals(support_key_path)

    # Cross-check, zero requests: HCP-CONFIG-SCHEMA.md §10 states "all 15
    # bundle-declared public/* keys and all 6 direct hcp/configuration/*
    # endpoints have been resolved". If this extraction does not return 15 and 6
    # it is not reading the same population the record describes, and the plan
    # must not be trusted.
    DIRECT = re.compile(rb"hcp/configuration/(?!public/)([A-Za-z0-9._?=&/()-]+)")
    cdirect = sorted({m.group(1).decode() for m in DIRECT.finditer(cbody)})
    sdirect = sorted({m.group(1).decode() for m in DIRECT.finditer(sbody)})
    if len(ckeys) != 15 or len(cdirect) != 6:
        die(f"extraction self-check failed: clinic build yields {len(ckeys)} public/* "
            f"and {len(cdirect)} direct literals, HCP-CONFIG-SCHEMA.md §10 records 15 and 6")
    if ckeys != skeys or cdirect != sdirect:
        die("the two builds' hcp/configuration route tables differ — the clinic list "
            "would not be portable to the support host; re-derive per build")

    # The support list is compared against the clinic list, but a support-only
    # literal is a CANDIDATE FOR THE SUPPORT HOST ONLY. Nothing is carried across.
    cset, sset = set(ckeys), set(skeys)

    plan = []
    md = []

    def add(host, path, role, hdr, kind, note):
        plan.append({"host": host, "path": path, "role": role,
                     "header": hdr, "kind": kind, "note": note})

    # ---- controls, per host, first ------------------------------------------
    for host in CLINIC_HOSTS:
        t = host.replace(".", "-")
        add(host, P + "pow.crm.settings",
            "CONTROL-1 positive: `pow.crm.settings` with X-System-ID: ProWeb. Known live — "
            "HCP-CONFIG-SCHEMA.md:148 recorded 200/96 B `application/octet-stream` on carelinkhp, "
            "and area A results.jsonl seq 6 recorded this exact host answering 200/97 B. "
            "Proves the header is ACCEPTED on this host and that the verdict rule is live here "
            "rather than uniform.", PROWEB, "control",
            "positive control — a 200 here is what a parked page cannot fake")
        add(host, ABSENT,
            "CONTROL-2 absent: `zzz.this.does.not.exist.zzz` — certainly not a route "
            "(HCP-CONFIG-SCHEMA.md:108, 404 with 0 bytes on carelinkhp). Proves a 404 on THIS "
            "host is distinguishable from the SPA fallback and therefore that a 404 on a key "
            "here is a true absence.", PROWEB, "control",
            "absent control")
        add(host, CASE_LO,
            "CONTROL-3a case, correct spelling: `cua.control.codes.settings` — 200/778 B on "
            "carelinkhp (HCP-CONFIG-SCHEMA.md:155).", PROWEB, "control",
            "case control, correct spelling")
        add(host, CASE_UP,
            "CONTROL-3b case, UPPER spelling: `CSU.CONTROL.CODES.SETTINGS` — 404 on carelinkhp "
            "(HCP-CONFIG-SCHEMA.md:188). 3a+3b together re-derive docs/07's case-sensitivity "
            "half ON THIS HOST instead of inheriting it from .eu.", PROWEB, "control",
            "case control, wrong case")
        add(host, HDR_ABSENT_KEY,
            "CONTROL-4 header-absent: `logbook.supported.entry.types` with NO X-System-ID. "
            "Expected 412 (HCP-CONFIG-SCHEMA.md:151). Proves that on this host 412 means "
            "'header rejected at the edge' and not 'key absent'. Deliberately NOT "
            "`pow.crm.settings`: docs/07:222-230 records that on carelink.medtronic.eu that one "
            "key alone answers 200 with no header while `logbook.supported.entry.types` is one "
            "of the nine siblings that return 412 — so it is the cell that can discriminate.",
            None, "control", "header-absent control, expected 412")

    sp = [
        (P + "pow.crm.settings",
         "CONTROL-1 positive: `pow.crm.settings` WITH the header. Area A results.jsonl seq 10 "
         "recorded this exact host answering it 200/97 B with NO header at all, so the "
         "headered cell is the one that carries the verdict. Proves X-System-ID: ProWeb is "
         "accepted on the support deployment.", PROWEB, "positive control"),
        (ABSENT,
         "CONTROL-2 absent: `zzz.this.does.not.exist.zzz` — certainly not a route "
         "(HCP-CONFIG-SCHEMA.md:108). Proves a 404 on the support deployment is distinguishable "
         "from the SPA fallback.", PROWEB, "absent control"),
        (CASE_LO,
         "CONTROL-3a case, correct spelling: `cua.control.codes.settings`. **The POW/CUA cell.** "
         "`cua.*` returned 200 on the CLINIC build (HCP-CONFIG-SCHEMA.md:155) and `pow.*` "
         "returned 200 on this SUPPORT host (area A seq 10), so the two products may both be "
         "published everywhere; docs/07:148-149 says `cua.crm.settings` was never probed on "
         "this host and the split 'stands as recorded'.", PROWEB, "case control, correct spelling"),
        (CASE_UP,
         "CONTROL-3b case, UPPER spelling: `CSU.CONTROL.CODES.SETTINGS` — 404 on the clinic "
         "build (HCP-CONFIG-SCHEMA.md:188). Re-derives case-sensitivity on the support build.",
         PROWEB, "case control, wrong case"),
        (HDR_ABSENT_KEY,
         "CONTROL-4 header-absent: `logbook.supported.entry.types` with NO X-System-ID. Expected "
         "412. Proves 412 means 'header rejected at the edge' on the support deployment.",
         None, "header-absent control, expected 412"),
    ]
    for path, role, hdr, _k in sp:
        add(SUPPORT_HOST, path, role, hdr, "control", "")

    # ---- that host's own keys, in route-table order -------------------------
    seen_paths = {(r["host"], r["path"]) for r in plan}
    for host in CLINIC_HOSTS:
        for k in ckeys:
            if (host, P + k) in seen_paths:
                continue
            shared = k in sset
            note = (f"clinic build literal; also present in the SUPPORT build's route table "
                    f"({len(skeys) - len(sset)} support-only literals, {len(sset)} shared)"
                    if shared else
                    f"clinic build literal; NOT in the support build's route table "
                    f"(one of the {len(cset - sset)} clinic-only literals)")
            add(host, P + k,
                f"KEY `{k}` — extracted offline from the CLINIC build's own route table "
                f"(asset {CLINIC['asset']}, sha256 {CLINIC['sha256'][:16]}…, asserted above). "
                f"Not typed from memory and not taken from docs/07. {note}.",
                PROWEB, "key", note)
    for k in skeys:
        if (SUPPORT_HOST, P + k) in seen_paths:
            continue
        only = k not in cset
        note = ("support-only literal — absent from the clinic build's route table, so this "
                "cell also measures whether the support deployment publishes a key the clinic "
                "build does not name" if only else
                "also present in the clinic build's route table")
        add(SUPPORT_HOST, P + k,
            f"KEY `{k}` — extracted offline from the SUPPORT build's own route table "
            f"(asset {SUPPORT['asset']}, sha256 {SUPPORT['sha256'][:16]}…, asserted above). "
            f"Not typed from memory, not inherited from the clinic list, not taken from "
            f"docs/07. {note}.",
            PROWEB, "key", note)

    md.append("# plan.md — the candidate list, written before the first request (lane l2)\n")
    md.append("Generated by `plan.py`, **zero vendor requests**. Every row below is derived, "
              "not guessed: a `KEY` row names the asset whose route table produced it and the "
              "sha256 that asset was asserted against.\n")
    md.append("## Corpus control — asserted before this plan was written\n")
    md.append("| tag | host | status | content-type | bytes | sha256 | recorded sha256 | verdict |")
    md.append("|---|---|---|---|---|---|---|---|")
    for t in CLINIC_TAGS + [SUPPORT["tag"]]:
        r = next(x for x in rows if x["tag"] == t)
        want = CLINIC["sha256"] if t in CLINIC_TAGS else SUPPORT["sha256"]
        md.append(f"| `{t}` | `{r['host']}` | {r['http_status']} | {r['content_type']} | "
                  f"{r['body_bytes']} | `{r['body_sha256'][:16]}…` | `{want[:16]}…` | "
                  f"**{'reproduces' if r['body_sha256'] == want else 'MISMATCH'}** |")
    md.append("")
    md.append("## The two route tables, extracted offline\n")
    md.append(f"- clinic build `{CLINIC['asset']}` — **{len(ckeys)} distinct** "
              f"`hcp/configuration/public/*` literals across {cocc} occurrences")
    md.append(f"- support build `{SUPPORT['asset']}` — **{len(skeys)} distinct** "
              f"`hcp/configuration/public/*` literals across {socc} occurrences")
    md.append(f"- **shared by both builds: {len(sset)}** · **clinic-only: "
              f"{len(cset - sset)}** · **support-only: {len(sset - cset)}**")
    md.append(f"- **self-check against HCP-CONFIG-SCHEMA.md §10**, zero requests: this "
              f"extraction returns **{len(ckeys)}** `public/*` and **{len(cdirect)}** direct "
              f"`hcp/configuration/*` literals from the clinic build, against the recorded "
              f"**15 and 6** — it is reading the same population the record describes, not a "
              f"neighbouring one. The support build's direct literals: **{len(sdirect)}**, "
              f"{'identical set to the clinic build' if sdirect == cdirect else '**DIFFERENT set**'}.")
    md.append(f"- **templated literals instantiated before request:** "
              f"{len(ctempl) + len(stempl)} occurrence(s) — "
              f"{sorted({(m, v) for _, m, v in ctempl + stempl})} — marker count from "
              f"2026-10-14-area-k-clinic-controlflow/FINDINGS.md:301 §3i (*exactly 1* route "
              f"carries a query string), the value from HCP-CONFIG-SCHEMA.md:185. "
              f"**The `((…))` marker is never sent.**")
    md.append("")
    md.append("### the 6 direct (non-`public/`) literals — recorded here, NOT requested")
    md.append("Deliberately out of scope: 4 of the 6 are POST-only or token-gated on the "
              "recorded host (`application`, `productContext`, `user` → 405; `appContext`, "
              "`access/config`, `whitelisted` → 401 at HCP-CONFIG-SCHEMA.md:162-178), and "
              "this is a GET-only, no-auth pass (AGENTS.md §8). Named here so the count is "
              "checkable and nobody re-derives them from a probe.\n")
    md.append("```")
    for k in cdirect:
        md.append(f"  hcp/configuration/{k}")
    md.append("```")
    md.append("### the 15 literals BOTH builds name — the shared set, printed in full")
    md.append("Read this list against the two empty lists below it: it contains both "
              "`cua.*` and `pow.*` keys, which is what makes \"each build names the "
              "other's product namespace\" an observation rather than an inference.\n")
    md.append("```")
    for k in sorted(sset):
        md.append(f"  {k}")
    md.append("```")
    md.append("### clinic-only literals (a clinic deployment may publish these and the support one may not)")
    md.append("```")
    for k in sorted(cset - sset):
        md.append(f"  {k}")
    md.append("```")
    md.append("### support-only literals (the reverse)")
    md.append("```")
    for k in sorted(sset - cset):
        md.append(f"  {k}")
    md.append("```")
    md.append("## The request plan, in issue order\n")
    md.append("| # | host | kind | header | path |")
    md.append("|---:|---|---|---|---|")
    for i, r in enumerate(plan, 1):
        md.append(f"| {i} | `{r['host']}` | {r['kind']} | "
                  f"`{r['header']}` | `{r['path']}` |")
    md.append("")
    md.append("## Why each candidate exists — one line per row, the reasoning the ledger carries\n")
    for i, r in enumerate(plan, 1):
        md.append(f"{i}. `{r['host']}` `{r['path']}` — {r['role']}")
    md.append("")

    json.dump({"clinic_keys": ckeys, "clinic_occurrences": cocc,
               "support_keys": skeys, "support_occurrences": socc,
               "clinic_direct": cdirect, "support_direct": sdirect,
               "templated_substitutions": [{"literal": a, "marker": b, "value": c}
                                           for a, b, c in ctempl + stempl],
               "shared": sorted(sset), "clinic_only": sorted(cset - sset),
               "support_only": sorted(sset - cset),
               "plan": plan},
              open(os.path.join(HERE, "plan.json"), "w"), indent=1)
    open(os.path.join(HERE, "plan.md"), "w").write("\n".join(md))
    sys.stderr.write(f"corpus control PASS 4 of 4 | clinic {len(ckeys)} literals "
                     f"({cocc} occ) | support {len(skeys)} literals ({socc} occ) | "
                     f"shared {len(sset)} clinic-only {len(cset-sset)} "
                     f"support-only {len(sset-cset)} | plan {len(plan)} requests\n")
    return len(plan)


def issue(ledger, runlog, hdr, scratch, assets, lockdir, delay, cap, ua):
    delay = float(delay)
    cap = int(cap)
    plan = json.load(open(os.path.join(HERE, "plan.json"), encoding="utf-8"))["plan"]
    rows = load_ledger(ledger)
    seq = len(rows)
    per_host = {}
    for r in rows:
        per_host[r["host"]] = per_host.get(r["host"], 0) + 1

    def logln(s):
        with open(runlog, "a") as f:
            f.write(f"{now()} {s}\n")

    logln(f"PLAN_BATCH2 hosts={sorted({r['host'] for r in plan})} requests={len(plan)}")
    issued = 0
    for r in plan:
        if seq >= cap:
            logln(f"CAP STOP at {seq} of {cap}")
            print(f"CAP STOP at {seq} of {cap}", file=sys.stderr)
            break
        host, path, hdrsent = r["host"], r["path"], r["header"]
        seq += 1
        per_host[host] = per_host.get(host, 0) + 1
        hseq = per_host[host]
        tag = f"k{seq:03d}-{host.replace('.', '-')}-{path.rsplit('/', 1)[-1].replace('?', '_')[:44]}"
        out = os.path.join(scratch, tag)
        tq = now()
        harg = f"-H '{hdrsent}' " if hdrsent else ""
        cmd = ("sleep %s; date -u +%%Y-%%m-%%dT%%H:%%M:%%S.%%3NZ > '%s.ts'; "
               "curl -s --compressed --max-time 120 -A '%s' %s"
               "-D '%s.h' -o '%s.b' -w '%%{http_code}' 'https://%s%s'") % (
            delay, out, ua, harg, out, out, host, path)
        p = subprocess.run(["flock", os.path.join(lockdir, f"host-{host}.lock"), "-c", cmd],
                           capture_output=True, text=True)
        code = p.stdout.strip()
        ts = open(f"{out}.ts").read().strip() if os.path.exists(f"{out}.ts") else tq
        td = now()

        def hv(n, o=out):
            if not os.path.exists(f"{o}.h"):
                return "(none)"
            v = [l.split(":", 1)[1].strip() for l in open(f"{o}.h", errors="replace")
                 if l.lower().startswith(n.lower() + ":")]
            return v[-1] if v else "(none)"

        hb = f"{out}.b"
        sz = os.path.getsize(hb) if os.path.exists(hb) else 0
        dg = hashlib.sha256(open(hb, "rb").read()).hexdigest() if os.path.exists(hb) else ""
        if sz and sz <= 100000:
            open(os.path.join(hdr, tag + ".b"), "wb").write(open(hb, "rb").read())
        raw_hdr = (open(f"{out}.h", errors="replace").read().replace("\r", "")
                   if os.path.exists(f"{out}.h") else "")
        if raw_hdr:
            open(os.path.join(hdr, tag + ".h"), "w").write(raw_hdr)
        row = {"seq": seq, "host_seq": hseq, "host": host, "tag": tag, "method": "GET",
               "path": path, "role": r["role"], "kind": r["kind"],
               "sent_headers": hdrsent or "(none)", "http_status": code,
               "curl_exit": p.returncode, "content_type": hv("content-type"),
               "content_length_hdr": hv("content-length"),
               "content_encoding": hv("content-encoding"), "vary": hv("vary"),
               "x_amz_cf_pop": hv("x-amz-cf-pop"), "server": hv("server"),
               "body_bytes": sz, "body_sha256": dg,
               "headers": " | ".join(l for l in raw_hdr.splitlines() if l),
               "t_queued": tq, "t_sent": ts, "t_done": td}
        with open(ledger, "a") as f:
            f.write(json.dumps(row) + "\n")
        logln(f"seq={seq} host_seq={hseq} host={host} tag={tag} kind={r['kind']} "
              f"status={code} ctype={row['content_type']} bytes={sz} sha256={dg[:16]} "
              f"path={path}")
        print(f"seq={seq:3d} host_seq={hseq} {code:>3} {row['content_type'][:26]:<26} "
              f"{sz:>6}  {path}")
        issued += 1
    print(f"ISSUED={issued} LEDGER={seq} CAP={cap}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--issue":
        issue(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6],
              sys.argv[7], sys.argv[8], sys.argv[9], sys.argv[10])
    else:
        build_plan()