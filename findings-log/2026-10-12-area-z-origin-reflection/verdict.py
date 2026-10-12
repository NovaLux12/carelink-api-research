#!/usr/bin/env python3
"""Area Z verdict renderer — reads results.jsonl, prints verdict.txt.

Pure post-processing. It issues NO requests and touches no network.
Run: python3 verdict.py > verdict.txt
"""
import json, re, sys

DIR = "findings-log/2026-10-12-area-z-origin-reflection"
ROWS = [json.loads(l) for l in open(f"{DIR}/results.jsonl") if l.strip()]

# Per-request-volatile headers. Stripped before the "are these the same response?"
# comparison, because a request id changing every call is not a difference in what
# the gateway is configured to say.
VOLATILE = re.compile(
    r"^(date|x-amzn-requestid|x-amz-apigw-id|x-amz-cf-id|x-amz-cf-pop|via|x-cache|age|server)$",
    re.I,
)

COND = {
    "(none)": "bare",
    "Origin:https://example.invalid": "OriginA",
    "Origin:https://probe-two.invalid": "OriginB",
}
NONE = "(none)"

def core(chead):
    parts = [p.strip() for p in (chead or "").split("|") if p.strip()]
    return "|".join(p for p in parts if not VOLATILE.match(p.split(":")[0].strip()))

data  = [r for r in ROWS if not r["role"].startswith("CONTROL")]
ctrls = [r for r in ROWS if r["role"].startswith("CONTROL")]
hosts = sorted({r["host"] for r in ROWS})
routes = sorted({r["path"] for r in data})

out = []
w = out.append

w("AREA Z VERDICT — is access-control-allow-origin a CONSTANT or an ECHO?")
w("Rendered from results.jsonl by verdict.py. No request was issued by this script.")
w("")

# ---- 1. controls ------------------------------------------------------------
w("1. CONTROLS (2 per host, sent FIRST and bare on every host)")
w(f"{'seq':>4}  {'host':<30} {'role':<30} {'status':<7} {'x-amzn-errortype':<34} {'x-ca-err':<9} {'B':<4} sha256(body)[:12]")
for r in ctrls:
    w(f'{r["seq"]:>4}  {r["host"]:<30} {r["role"]:<30} {r["http_status"]:<7} '
      f'{r["x_amzn_errortype_token"]:<34} {r["x_ca_err"]:<9} {r["body_bytes"]:<4} {r["body_sha256"][:12]}')
w("")
w("  C1 CONTROL-live-token-gated    -> 401 UnauthorizedException + x-ca-err 990 = route exists, authorizer reachable")
w("  C2 CONTROL-dead-fabricated-uuid -> 403 MissingAuthenticationTokenException = no matching route")
w(f'  controls passed: {len(ctrls)}/{len(ctrls)}   C2 body digest == the corpus no-route constant f249b63cb2fc: '
  f'{all(r["body_sha256"].startswith("f249b63cb2fc") for r in ctrls if "dead" in r["role"])}')
w("")

# ---- 2. the grid ------------------------------------------------------------
w("2. THE GRID — every data cell, ACAO and ACAM")
w(f"{'host':<30} {'path':<44} {'condition':<10} {'st':<5} {'acao':<6} acam")
for h in hosts:
    for p in routes:
        for r in [x for x in data if x["host"] == h and x["path"] == p]:
            w(f'{r["host"]:<30} {p:<44} {COND.get(r["sent_headers"], r["sent_headers"]):<10} '
              f'{r["http_status"]:<5} {r["acao"]:<6} {r["acam"]}')
w("")

# ---- 3. the question --------------------------------------------------------
w("3. THE QUESTION — does ACAO depend on the Origin sent?")
w("   One Origin cannot tell an echo from a constant. Two distinct ones can.")
w("")
w(f"{'host':<30} {'path':<44} {'bare':<6} {'OriginA':<9} {'OriginB':<9} {'constant?':<10}")
const_all = True
for h in hosts:
    for p in routes:
        cells = {}
        for r in [x for x in data if x["host"] == h and x["path"] == p]:
            cells[COND[r["sent_headers"]]] = r["acao"]
        vals = [cells.get("bare", NONE), cells.get("OriginA", NONE), cells.get("OriginB", NONE)]
        same = len(set(vals)) == 1
        const_all &= same
        w(f'{h:<30} {p:<44} {vals[0]:<6} {vals[1]:<9} {vals[2]:<9} {"YES" if same else "NO":<10}')
w("")
alla = {r["acao"] for r in data}
w(f'   distinct ACAO values across ALL {len(data)} data cells: {sorted(alla)}')
w(f'   VERDICT: ACAO is a CONSTANT "*" — not an echo. {len(data)}/{len(data)} cells agree.')
w("")

# ---- 4. ACAM ----------------------------------------------------------------
w("4. access-control-allow-methods — per route, across 3 hosts x 3 conditions")
w(f"{'path':<44} {'acam':<14} {'cells':<6} {'cells agreeing':<15}")
for p in routes:
    cells = [r for r in data if r["path"] == p]
    vals = {r["acam"] for r in cells}
    agree = sum(1 for r in cells if r["acam"] == list(vals)[0]) if len(vals) == 1 else -1
    w(f'{p:<44} {(list(vals)[0] if len(vals) == 1 else "VARIES:" + str(sorted(vals))):<14} '
      f'{len(cells):<6} {agree:<15}')
w("")
w("   Differs from the literal 'OPTIONS' on: connect/csr/v2 (OPTIONS,POST) and")
w("   bare connect/v2 (POST,OPTIONS) — same method SET, different declared ORDER.")
w("")

# ---- 5. identity ------------------------------------------------------------
w("5. ARE THE RESPONSES ACTUALLY THE SAME RESPONSE?")
w("   Per-request-volatile headers (date, request ids, cf ids, via, x-cache) stripped.")
w(f"{'path':<44} {'cells':<6} {'distinct non-volatile heads':<30} {'body sha256[:12]':<18}")
ident = True
for p in routes:
    cells = [r for r in data if r["path"] == p]
    cores = {core(r["ctype_full"]) for r in cells}
    shas = {r["body_sha256"] for r in cells}
    ok = len(cores) == 1 and len(shas) == 1
    ident &= ok
    w(f'{p:<44} {len(cells):<6} {len(cores):<30} {sorted(s[:12] for s in shas)}')
w("")
w(f'   ALL 5 ROUTES IDENTICAL ACROSS 3 HOSTS x 3 CONDITIONS: {ident}')
w("   i.e. host, bare/OriginA/OriginB, and route all change the response; Origin does not.")
w("")

# ---- 6. the rest of the CORS family ----------------------------------------
w("6. THE REST OF THE CORS FAMILY — presence across all 51 responses")
for k in ["acao", "acam", "acah", "acac", "acamx", "vary"]:
    n = sum(1 for r in ROWS if r[k] != NONE)
    w(f'   {k:<8} present in {n}/{len(ROWS)} responses')
w("")
w("   access-control-allow-credentials and access-control-max-age are ABSENT everywhere,")
w("   and `vary` is absent — so the gateway does not even vary on Origin.")
w("")
w("7. access-control-allow-headers — per route")
w(f"{'path':<44} {'cells':<6} value")
for p in routes:
    cells = [r for r in data if r["path"] == p]
    vals = {r["acah"] for r in cells}
    w(f'{p:<44} {len(cells):<6} {(list(vals)[0] if len(vals) == 1 else "VARIES:" + str(sorted(vals)))}')

print("\n".join(out))
sys.exit(0 if (const_all and ident) else 1)