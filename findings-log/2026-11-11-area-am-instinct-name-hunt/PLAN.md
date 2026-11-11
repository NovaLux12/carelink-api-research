# AM — itemised request plan, written BEFORE the first request

Cap **16**. GET only. `sleep 2.5` inside the per-host `flock`. Three hosts, all in this lane's set:
`carelink.minimed.com`, `carelink.minimed.eu`, `carelink-trials.minimed.com`.

## Hosts this lane does NOT touch, and therefore corpora it cannot fetch

| corpus | served from | verdict |
|---|---|---|
| the two portal builds (`main.fb5f8cb7eb60c4d5.js`, `main.759cddab23085086.js`) | `carelinkhp.minimed.eu`, `carelink-support.medtronic.{eu,com}`, `carelink.medtronic.{com,eu}` — the HCP/portal host family | **out of scope by lane assignment.** One probe tests whether the *name* also answers on a patient host (seq 8/10/12) — that is inside this lane's host set and costs nothing if it 404s |
| the HCP `pow.common.core.report.generation` copy | `carelink.medtronic.*` / `carelinkhp.*` | **not probed.** Three bodies are already committed from 2026-10-17 (`findings-log/2026-10-17-hcp-config-deployments/headers/k0{24,36,48}-*report.generation.b`) and are scanned offline at zero requests |
| the 211 patient lazy chunks | `carelink.minimed.eu/<chunk>.<hash>.js` | **not swept.** 211 GETs against a 16 cap is 13× the budget; the route, the emitted-name defect (`2076`→`common`) and the list are committed (`findings-log/2026-10-13-area-k-patient-chunks/chunks-swept.txt`), so this is a *budget* blocker, not a method blocker. Named as successor AM.1 |

## The 16, in send order

| seq | host | path | role |
|---|---|---|---|
| 1 | `carelink.minimed.com` | `/patient/configuration/system/zzz.not.a.real.key.zzz` | absent control — must be 404, 0 B, `text/vnd.a` |
| 2 | `carelink.minimed.com` | `/patient/configuration/system/logbook.supported.entry.types` | live control — must be 200, 281 B |
| 3 | `carelink.minimed.eu` | the same two | controls |
| 4 | `carelink.minimed.eu` | the same two | controls |
| 5 | `carelink-trials.minimed.com` | the same two | controls |
| 6 | `carelink-trials.minimed.com` | the same two | controls |
| 7 | `carelink.minimed.com` | `/main.6595daf83bd6d4b1.js` | patient eager bundle — the one bundle in this lane's hosts that carries `mapDeviceModelName`. Pinned 3,417,255 B sha256 `0fb4fbd4…` |
| 8 | `carelink.minimed.com` | `/main.fb5f8cb7eb60c4d5.js` | does the **clinic** build's content-hashed name answer on a patient host? Pinned (elsewhere) 3,397,615 B `2a7fa8e7…` |
| 9 | `carelink.minimed.eu` | `/main.6595daf83bd6d4b1.js` | as 7 |
| 10 | `carelink.minimed.eu` | `/main.fb5f8cb7eb60c4d5.js` | as 8 |
| 11 | `carelink-trials.minimed.com` | `/main.6595daf83bd6d4b1.js` | as 7 |
| 12 | `carelink-trials.minimed.com` | `/main.fb5f8cb7eb60c4d5.js` | as 8 |
| 13–16 | — | — | **unspent reserve**: a patient bundle whose digest moves gets re-fetched under its *re-derived* name only if the runtime map is readable; otherwise the reserve stays unspent and the cap is reported honestly |

No POST, no token, no cookie, no auth, no wordlist. The two asset names are recorded strings
(area G, area V), not candidates: this is a re-fetch on a content-hashed name, which is exactly
what "re-fetch on the content-hashed asset name" means.

**Method, and why:** every corpus named here is either a whole document or a whole bundle, so the
scan is local, at zero further requests. A per-SKU GET cannot answer this question — no sub-key
grammar for `/patient/configuration/system/<key>.<SKU>` exists in this repository, and inventing
one is wordlist fuzzing (`findings-log/2026-11-10-area-ai-instinct-sku-tail/FINDINGS.md` §Method).

---

## Recorded revision 1 — the one revision this pass is allowed, written after 12 requests and BEFORE requests 13–16

**What changed, and why.** Requests 1–12 are spent: 6 controls (all PASS) and 6 asset fetches.
The patient eager bundle — fetched and scanned locally at zero further requests — contains a
**key-addressable name route this repository has never probed**:

```
getDeviceModelMapping(V){return this.http.get(`patient/configuration/system/model-mapping/${V}`)}
```

at byte offset **3374392** of the `.com` body (seq 7), called at byte **2165828** as
`D.getDeviceModelMapping(y.code)` where `y` is the country store (`setAndEmitCountryByCode(Ve.country)`,
byte 2166531). The only two mentions of `model-mapping` anywhere in this repository before this
pass are a **call-site inventory row**, not a verdict:
`findings-log/2026-10-14-area-s4-lazy-chunk-control-flow/pairs.tsv:63` and
`findings-log/2026-10-14-area-k-clinic-controlflow/differential.json:319` — both list the route
as *seen in source*, neither ever sent it.

This is the one shape area AI's limit left open: a route that is **key-addressable by country**
and returns a mapping document, in the same namespace as the two documents that carry the family
map. It is a name source, so it is worth the reserve.

**The four, in send order** (this is the whole extension of the plan; the list is not widened again):

| seq | host | path | role |
|---|---|---|---|
| 13 | `carelink.minimed.com` | `/patient/configuration/system/model-mapping/US` | the largest deployment, the `INSTINCT` home market |
| 14 | `carelink.minimed.eu` | `/patient/configuration/system/model-mapping/US` | same code, second deployment — portability of the route itself |
| 15 | `carelink.minimed.eu` | `/patient/configuration/system/model-mapping/GB` | the UK — a market area D measured with its own published key set |
| 16 | `carelink.minimed.eu` | `/patient/configuration/system/model-mapping/DE` | the EU deployment's largest market |

**Candidate justification, recorded:** three ISO-3166 alpha-2 codes taken from
`findings-log/2026-10-12-area-d-country-sweep/candidates.txt`, which derived them offline from
published config documents (118 codes, provenance per code). Not a wordlist: the codes are the
argument the bundle itself passes (`y.code`), and `US`/`GB`/`DE` are the three whose published
key sets area D measured widest.

**No new controls are owed for this batch.** All four paths are in the *same* namespace as
control 1 (`/patient/configuration/system/zzz.not.a.real.key.zzz`), which returned 404 / 0 B /
`text/vnd.a` on all three hosts in seq 1, 3, 5 — so a 404 on `model-mapping/<CC>` reads as an
absence on this namespace, and a 200 is a document. That is the control doing its job, not a
control skipped.

**If this batch returns 404 on all four**, the cap is fully spent at 16 and the honest statement is
that the route is registered in the bundle and not served unauthenticated on this namespace — a
different fact from "the key families have no names", and both get said.

