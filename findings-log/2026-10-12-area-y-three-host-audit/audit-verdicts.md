# Area Y — per-claim audit table

Each in-scope claim resolved to its raw row(s). Host coverage is the test: a claim naming
three hosts that resolves to fewer is a defect **whether or not the fact is true**.

| # | Location | Claim (abridged) | Hosts found | Verdict |
|---|---|---|---|---|
| 1 | `03-discovery-and-versions.md:38` | **OBSERVED** and hash-verified. All three hosts return the **same document** — sh… | — | **DEFECT Y-1** — 2-host evidenced, claims 3 |
| 2 | `03-discovery-and-versions.md:131` | \| `*/v13/discover/android/3.6` (all 3 hosts) \| yes \| **v13** \| yes \| patient… | 3 | **confirmed-by-row** |
| 3 | `03-discovery-and-versions.md:135` | \| `*/v12/discover/android/3.6` (all 3 hosts) \| ? (401, unreadable) \| ? \| ? \|… | 3 | **confirmed-by-row** |
| 4 | `03-discovery-and-versions.md:138` | three hosts, and `v11` on `.eu` and `-trials`. Both were already known; **no new | 3 | **confirmed-by-row** |
| 5 | `03-discovery-and-versions.md:157` | **`/connect/carepartner/v12/display/message` is live and GET-capable — 401 on all… | 3 | **confirmed-by-row** |
| 6 | `03-discovery-and-versions.md:165` | ### Confirmed on all three hosts (2026-10-12) — the claim above was under-evidenc… | 3 | **confirmed-by-row** |
| 7 | `03-discovery-and-versions.md:167` | The sentence above asserted "401 on all three hosts" on the strength of **one** r… | 3 | **confirmed-by-row** |
| 8 | `03-discovery-and-versions.md:172` | `clcloud-trials.minimed.com` — **3 of 3**, every one a request that reached Medtr… | 3 | **confirmed-by-row** |
| 9 | `03-discovery-and-versions.md:256` | **403 on GET** and **200 with CORS on OPTIONS** on all three hosts: the resource … | 3 | **confirmed-by-row** |
| 10 | `03-discovery-and-versions.md:316` | \| `clcloud.minimed.eu` `v13/discover/android/3.6` \| US, EU, CLINICAL \| `…/conn… | 3 | **confirmed-by-row** |
| 11 | `03-discovery-and-versions.md:347` | in two independent keys, on all three deployments: | 3 | **confirmed-by-row** |
| 12 | `03-discovery-and-versions.md:400` | \| What `*/v12/discover/android/*` returns \| token-gated on all three hosts — 40… | 3 | **confirmed-by-row** |
| 13 | `06-patient-api-surface.md:126` | `display/message` at v6/v11/v13 is byte-identical on all three hosts (v6 403, v11… | 3 | **confirmed-by-row** |
| 14 | `06-patient-api-surface.md:127` | v13 401); `v12/discover` is 401 on all three. **There is no region split on the d… | 3 | **confirmed-by-row** |
| 15 | `06-patient-api-surface.md:134` | `UnauthorizedException` + `x-ca-err: 990` on all three**, so this page's "same sh… | 3 | **confirmed-by-row** |
| 16 | `06-patient-api-surface.md:135` | three hosts" claim is now 3-host evidenced instead of resting on the single `.eu`… | 3 | **confirmed-by-row** |
| 17 | `06-patient-api-surface.md:155` | Area X re-derived the cell live on all three hosts: **9 `200`-without-CORS respon… | 3 | **confirmed-by-row** |
| 18 | `06-patient-api-surface.md:174` | recorded on any of the three hosts**. Successor area in | 3 | **confirmed-by-row** |
| 19 | `06-patient-api-surface.md:190` | \| All 6 controls passed, **first on every host**: `401` + `UnauthorizedException… | 3 | **confirmed-by-row** |
| 20 | `06-patient-api-surface.md:208` | and `v6/display/message` return `200` + **`ACAO` on all three hosts**. **`ACAO` o… | 3 | **confirmed-by-row** |
| 21 | `06-patient-api-surface.md:217` | `200` + `ACAO: *` + `ACAM: OPTIONS` on all three hosts**, 9 of 9 cells, which als… | 3 | **confirmed-by-row** |
| 22 | `06-patient-api-surface.md:234` | host**. That is why `docs/11` §Z's "`ACAO` on all three hosts" was unsourced for … | 3 | **confirmed-by-row** |
| 23 | `06-patient-api-surface.md:322` | ### ⚠ Not region-split — confirmed on all three cumulus hosts (2026-10-12) | 3 | **confirmed-by-row** |
| 24 | `06-patient-api-surface.md:354` | \| `connect/csr/v2/display/message` \| the **public config**, twice — `system.gc.… | 3 | **confirmed-by-row** |
| 25 | `06-patient-api-surface.md:357` | Both are live and POST-only on all three hosts. Only one is *addressable*, becaus… | 3 | **confirmed-by-row** |
| 26 | `06-patient-api-surface.md:379` | `OPTIONS` → 200, `allow-origin: *`, `allow-methods: OPTIONS` — on all three | 3 | **confirmed-by-row** |
| 27 | `06-patient-api-surface.md:397` | explicitly — `GET …/v13/display/message` → 401 + `x-ca-err == "990"` on all three | 3 | **confirmed-by-row** |
| 28 | `06-patient-api-surface.md:467` | `/api/schema`, `/api/v1/schema`, `/graphql`, `/graphiql`) was probed on three hosts: | 3 | **confirmed-by-row** |
| 29 | `06-patient-api-surface.md:487` | \| v12 \| **live** — same shape as v11/v13, re-evidenced 2026-10-12 as **401 + `x… | 3 | **confirmed-by-row** |

### Added by dated addendum (outside the area's stated `docs/03` + `docs/06` scope)

| # | Location | Claim | Verdict |
|---|---|---|---|
| A1 | `docs/08-security-findings.md:91` | "the finding spans **five hosts**" | **DEFECT Y-2** — the same claim as `:37`; inherits both defects |
| A2 | `docs/02-auth-tenants-and-flows.md:41` (mermaid) | five tenants inside a "compared field-by-field" subgraph | **RESTATEMENT Y-3** — the comparison covered **four of five**; stated correctly in the prose, at risk in the diagram |
| A3 | `findings-log/2026-10-12-published-pointers/.gitignore` | the discovery / country / config bodies these pages rest on | **NOT RE-DERIVABLE from a clean clone** (Y-4) — maintainer decision, recorded not fixed |

**Counting rule for this table.** A line is in scope if it matches the seven multi-host phrases
above. In-scope total: **29** lines across `docs/03` + `docs/06`. Verdicts: **26 confirmed-by-row,
3 not evidenced as written.** No claim was marked defective on the strength of the index alone —
each was checked against the page's own cited source. **Coverage is per claim cell, not per
line**: several lines bundle more than one cell, and each cell was resolved separately.
