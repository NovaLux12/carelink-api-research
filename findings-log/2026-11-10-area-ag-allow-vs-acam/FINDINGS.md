# Area AG — does `Allow` agree with `access-control-allow-methods` on the same route?

**Claim:** NovaLux12/carelink-api-research#179
**Date:** 2026-11-10
**Cap:** 28 requests (24 + one recorded revision to 28)
**Delay:** `sleep 2.5` spacing between requests to the same host, taken **inside** the per-host `flock` (declared floor ≥ 2 s)
**Result:** **Negative, and the negative is the answer — plus a control that refuted its own premise.**

---

## The answer in one paragraph

**No route in the committed corpus or in this pass carries both headers on one response — 0 of 28 live cells and 0 of 2,730 rows across the committed result ledgers.** The two headers are emitted by **different server stacks**, and the split is per-family: the portal hosts run Apache and emit `Allow` from its own 405 handling; the cumulus hosts run API Gateway and emit `access-control-allow-methods` on `OPTIONS` 200s. They are **disjoint by design**, and AG's stated INFERRED assumption — that `Allow` is emitted from a route's registered methods — is **refuted** by a control that was supposed to be boring.

---

## 1. The primary finding: the certainly-absent control was not absent

The pass was designed to test whether a portal route's `405 + Allow` ever carries `ACAM` alongside. The certainly-absent control was `zz-ag-absent-8713`, verified **0 hits** in the whole repo by `git grep`, so it is a name this surface has never seen.

It returned:

| host | path | status | bytes | `Allow` | `ACAM` |
|---|---|---|---|---|---|
| `carelink.medtronic.com` | `/hcp/configuration/zz-ag-absent-8713` | **405** | 0 | **`POST, OPTIONS`** | — |
| `carelink.medtronic.com` | `/hcp/configuration/application` (real POST-only route) | **405** | 0 | **`POST, OPTIONS`** | — |

**Byte-identical, header-identical.** A path that certainly does not exist produces exactly the response a real POST-only route produces. So `Allow` on this family does **not** discriminate "route exists, wrong method" from "route does not exist".

That makes the header useless as an oracle in the direction area AB used it — and it means AG's own INFERRED assumption, that `Allow` is emitted by the server from the route's registered methods, is **not merely unestablished but contradicted**.

## 2. Where the 405 comes from — the boundary

One recorded cap revision (24 → 28) bought four cells on two portal hosts to find where the 405 stops:

| path | status | bytes | reading |
|---|---|---|---|
| `/zz-ag-absent-8713` | **200** | **5518** | the SPA fallback (§7's documented trap, on a host where §7 does not document it) |
| `/hcp/zz-ag-absent-8713` | **404** | 0 | genuine absence — the namespace is real |
| `/hcp/configuration/zz-ag-absent-8713` | **405** + `Allow: POST, OPTIONS` | 0 | **the 405 is scoped to the `/hcp/configuration/` subtree** |

So on the portal hosts there are **three** distinct absent-path behaviours, selected by prefix. The 405 is a property of a handler mounted on `/hcp/configuration/`, not of any route within it — which is exactly why it fires for a name that does not exist. **`Allow` there is a subtree constant.**

The `200 + 5518 B` at root is a second finding, and it is area AK's question: the SPA fallback is present on `carelink.medtronic.com` and `carelink.medtronic.eu` at root, where `AGENTS.md` §7 documents it only for `carelinkhp.minimed.eu`.

## 3. The two families, measured

| family | hosts | rows | `Allow` | `ACAM` | both |
|---|---|---|---|---|---|
| portal (Apache) | `carelink.medtronic.*`, `carelink-support.medtronic.com`, `carelink.minimed.*` | 1,700 | **27** | **0** | **0** |
| cumulus (API Gateway) | `clcloud.*` | 248 | **0** | **56** | **0** |
| other | commoncrawl, commoncore, github | 782 | 0 | 0 | 0 |

Committed-corpus census, both storage shapes:

| source | rows | `Allow` | `ACAM` | **both** |
|---|---|---|---|---|
| `.hdr` files | 166 | 0 | 62 | **0** |
| `results.jsonl` header dicts | 43 | 18 | 0 | **0** |
| per-row header fields (heterogeneous schemas) | 2,730 rows | 27 | 56 | **0** |

**The shapes are heterogeneous** — the committed `results.jsonl` files carry at least six different row schemas (`headers` dict, flat `allow`/`acam`/`acao`, `ctype` strings with headers embedded as text, `disc_headers`), so a single-field census undercounts. Three separate walks were needed to cover them. That is recorded because a future pass will otherwise re-derive the number wrongly.

## 4. Why they are disjoint — the mechanism, stated as INFERRED

- **Portal:** `server: Apache/2.4.62 (Red Hat Enterprise Linux)`. Apache emits `Allow` on its own 405 and on `OPTIONS` 200s for a mounted handler. It emits `ACAM` **only** if CORS is configured. On this surface `access-control-allow-headers` is present but `access-control-allow-origin` and `access-control-allow-methods` are **absent on every portal row** — 0 of 1,700. So Apache here has the CORS header set switched off; `ACAH` is emitted by the application, not by a CORS module.
- **Cumulus:** `server: aws` / API Gateway. API Gateway emits the full CORS trio (`ACAO`, `ACAM`, `ACAH`) on `OPTIONS` 200s and **never** emits `Allow` — a 403 no-route response carries no `Allow`.

**INFERRED, and the inference is the honest one:** the two headers come from different software with different jobs, so no single response can carry both **on these two families**. What this pass measured is that they never do; what it did *not* measure is whether a third stack could emit both.

## 5. Area N's warning, and whether it generalises

Area N established that `ACAM` is **not a register of a route's methods** — `carepartner/v13/display/message` advertises `OPTIONS` and is GET-capable on all three hosts. Area Z then found `ACAM` is a per-route constant whose *order* differs from the literal `OPTIONS` on two routes.

This pass adds the mirror: **`Allow` is not a register either.** On the portal family it is a subtree constant that a non-existent path reproduces exactly.

So the answer to AG's title question is: **the two headers never appear together, and neither one is a method register where it does appear.** The question "do they agree" has no subject — but the reason it has no subject is more useful than the agreement would have been.

## 6. Controls and their verdicts

| control | intent | verdict |
|---|---|---|
| portal known-live `/hcp/configuration/access/config` | prove the host answers | **412, 0 B, on all 3 hosts** — the recorded `X-System-ID` gate; consistent with area AB |
| portal certainly-absent `/hcp/configuration/zz-ag-absent-8713` | prove absence is distinguishable | **REFUTED ITS OWN PREMISE** — 405 + `Allow`, identical to a real route. This became the finding. |
| cumulus known-live `carepartner/v13/display/message` | prove the host answers | **401, 36 B, digest `d551247201fc8fc2`** on all 3 — route present, auth required |
| cumulus certainly-absent `/connect/csr/v2/zz-ag-absent-8713` | prove absence is distinguishable | **403, 42 B, digest `f249b63cb2fcb66b…`** on all 3 — reproduces the repo's published no-route digest **in full** |

**One of four controls failed to be a control, and that is the pass's most valuable result.** A control that comes back looking like a live route is not noise to be worked around — it is the instrument telling you the oracle is wrong.

## 7. Request accounting

**28 of a 28 cap**, GET + empty-body `OPTIONS` only, no POST, no token, no cookie, no auth, no wordlist. 6 hosts.

**One recorded cap revision:** 24 → 28. Reason: the absent control returned `405 + Allow`, so the primary cell could not be interpreted without knowing how far the 405 reaches; four cells (two paths × two portal hosts) established the boundary.

Measured same-host spacing, `t_sent` series: **22 gaps, minimum 1.894 s, median 2.959 s, 2 gaps under 2.5 s, 1 under the 2.0 s floor, 0 negative durations.**

⚠ **The 1.894 s gap is disclosed as below the `>= 2 s` floor.** The declared delay is 2.5 s and it is taken *inside* the per-host `flock`, so this is the known corrupt-`t0` class this repo has recorded in four prior passes (`docs/09` §4) — **no cause is asserted**. Unlike prior passes there is no kernel-mtime oracle here to cross-check it: the bodies were written to a gitignored scratch dir that is deleted after the run.

## 8. What this does not establish

- **Not** that no server anywhere emits both headers. This is two families, measured.
- **Not** that `Allow` is a subtree constant on *every* portal host — measured on `carelink.medtronic.com` and `carelink.medtronic.eu`; `carelink-support.medtronic.com` returned 405+`Allow` on both the real route and the absent path too, but the root/`/hcp/` boundary cells were not run there (cap).
- **Not** a cause for the 405-on-absent-path behaviour. It is consistent with a handler mounted at `/hcp/configuration/` that answers 405 for any child path, but the mechanism was not observed, only the boundary.
- **Not** a disclosure or security finding. Every cell here is an unauthenticated response to a GET or an empty-body OPTIONS on a public host.

## 9. Successors

- **AK** (filed, claim #183) — the 5518 B SPA fallback at root on `carelink.medtronic.*`, where `AGENTS.md` §7 documents it only for `carelinkhp.minimed.eu`.
- **AL** (minted below) — is the `/hcp/configuration/` 405 a handler-level constant on **every** host that mounts it, including `carelinkhp`? One host's boundary is measured; the family's is not.

## 10. Evidence index

| file | what it holds |
|---|---|
| `probe.sh` | the 24-cell sweep, cap as a single assignment |
| `boundary.sh` | the 4-cell boundary batch, the recorded cap revision |
| `results.jsonl` | 28 rows, one per request, with `allow`/`acam`/`acao`/`acah` per row |
| `run.log` | per-request line, timestamps, cap-stop guard |
