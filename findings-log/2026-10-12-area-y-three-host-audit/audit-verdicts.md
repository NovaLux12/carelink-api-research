# Area Y — per-claim audit table

Each in-scope claim resolved to its raw row(s). Host coverage is the test: a claim naming
three hosts that resolves to fewer is a defect **whether or not the fact is true**.

| # | Location | Claim (abridged) | Hosts found | Verdict |
|---|---|---|---|---|
| 1 | `03-discovery-and-versions.md:38` | “All three hosts return the **same document** — sha256 `f8488626…`” | 3 | **confirmed-by-row** — area X's tracked ledger hashes all three at `f84886265667…`, 20256 B each. Y-1 withdrawn |
| 2 | `03-discovery-and-versions.md:131` | \| `*/v13/discover/android/3.6` (all 3 hosts) \| yes \| **v13** \| yes \| patient… | 3 | **confirmed-by-row** |
| 3 | `03-discovery-and-versions.md:135` | \| `*/v12/discover/android/3.6` (all 3 hosts) \| ? (401, unreadable) \| ? \| ? \|… | 3 | **confirmed-by-row** |
| 4 | `03-discovery-and-versions.md:138` | three hosts, and `v11` on `.eu` and `-trials`. Both were already known; **no new | 3 | **confirmed-by-row** |
| 5 | `03-discovery-and-versions.md:157` | **`/connect/carepartner/v12/display/message` is live and GET-capable — 401 on all… | 3 | **confirmed-by-row** |
| 6 | `03-discovery-and-versions.md:165` | ### Confirmed on all three hosts (2026-10-12) — the claim above was under-evidenc… | 3 | **confirmed-by-row** |
| 7 | `03-discovery-and-versions.md:167` | The sentence above asserted "401 on all three hosts" on the strength of **one** r… | 3 | **confirmed-by-row** |
| 8 | `03-discovery-and-versions.md:172` | `clcloud-trials.minimed.com` — **3 of 3**, every one a request that reached Medtr… | 3 | **confirmed-by-row** |
| 9 | `03-discovery-and-versions.md:256` | **403 on GET** and **200 with CORS on OPTIONS** on all three hosts: the resource … | 3 | **confirmed-by-row** |
| 10 † | `03-discovery-and-versions.md:316` | \| `clcloud.minimed.eu` `v13/discover/android/3.6` \| US, EU, CLINICAL \| `…/conn… | 3 | **confirmed-by-row** |
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

**Identifier note.** `A1`/`A2`/`A3` are the addendum rows in **this** file. They correspond to
`FINDINGS.md`'s **Y-2**/**Y-3**/**Y-4**. `Y-1` is *not* an addendum row — it was an in-scope claim
(`docs/03:38`) and is **withdrawn**, so it no longer appears anywhere as a defect. Locations are
given by **content**, not line number: the corrections in this PR shift line numbers in the very
files they cite.

| A1 (= FINDINGS **Y-2**, second site) | `docs/08-security-findings.md`, the paragraph reading *"so the finding spans **five hosts** — recorded as reported"* | **NOT A DEFECT — reverted.** That paragraph cites `DRIFT-AND-NEW`, which has a *"Five hosts, not two"* section, and the paragraph already carries the re-verification caveat. `origin/main` restored byte-identically |
| A2 (= FINDINGS **Y-3**) | `docs/02-auth-tenants-and-flows.md`, the `subgraph POL[...]` title | five tenants inside a "compared field-by-field" subgraph | **Y-3 WITHDRAWN — no defect.** `AUTH-TENANT-FINDINGS.md` §1's three tenants *include trials*; §8's four is the JWKS-`kid` comparison, which correctly excludes it. `origin/main` restored byte-identically |
| A3 (= FINDINGS **Y-4**) | `findings-log/2026-10-12-published-pointers/.gitignore` | the discovery / country / config bodies these pages rest on | **NOT RE-DERIVABLE from a clean clone** (Y-4) — 10 tracked files in that directory, none a `docs/*.json`. Maintainer decision, recorded not fixed |

† **Claim #10 corrected after review round 1.** The line says the cell has *"no GET or OPTIONS
route … all 3 hosts"* without naming a method. Measured: the **GET** axis has **3** attributable
hosts; the **OPTIONS** axis has **2** attributable hosts plus **one unattributable row per recorded path (2)**
in the host-less `pde-csr-oracle` ledger, which carries 13 host-less rows per method in total. The table's "3" is therefore right for GET and optimistic for OPTIONS.
Restated in `docs/03` with both axes named.

**Counting rule for this table.** A line is in scope if it matches any of these **seven**
multi-host phrases, case-insensitively:

```
all three hosts | on all three | three hosts | all 3 hosts | 3 of 3 | five hosts | spans five
```

Applied to `docs/03` + `docs/06` this yields **29** lines: 12 in `docs/03`, 17 in `docs/06`.
**Verdicts: 29 confirmed-by-row, 0 corrected.**

**A1–A3 are counted separately and are NOT part of the 29.** They live in `docs/08` and `docs/02`,
outside the area's stated scope, so folding them into the in-scope total does not reproduce this
table. Two earlier drafts did exactly that — one reported "26 of 29" against a table holding a
single defect row, the next "27 confirmed, 2 corrected" — and a third reported "28 / 1" after
Y-1 was withdrawn without the prose being updated. **29 lines, 29 clean, 0 corrected** is the
only split this table supports.

No claim was marked defective on the strength of the index alone —
each was checked against the page's own cited source. **Coverage is per claim cell, not per
line**: several lines bundle more than one cell, and each cell was resolved separately.
