# Discovery and versions

The discovery document, the `carepartner` version axis, and which cells are actually
live. This is the page that pins `android/3.6`. Extends
[`00-summary-the-map.md`](00-summary-the-map.md) and agrees with it; the
endpoint-by-endpoint patient-API tables are in
[`06-patient-api-surface.md`](06-patient-api-surface.md), the probing method in
[`09-methodology-and-oracles.md`](09-methodology-and-oracles.md).

Legend — **OBSERVED** = seen in a live response during this research ·
**PUBLISHED** = in a vendor document served without a login (live, or recovered from
a public web archive) · **INFERRED** = reasoned, not seen. Citations are
`[source: findings-log/<file> §n]`; `PROBE-FINDINGS` =
`findings-log/probe-2026-10-08/PROBE-FINDINGS.md` and `VERSION-AXIS`, `ARCHIVE-URLS`,
`CONFIG-NAMESPACE`, `CONFIG-NAMESPACE-DEEP` are `…/probe-2026-10-08/recon/<name>.md`.

---

## 1. The discovery document

```
GET https://clcloud.{minimed.eu, minimed.com, clcloud-trials.minimed.com}
        /connect/carepartner/v13/discover/android/3.6
→ 200 application/json, 20256 B, unauthenticated, no x-api-key required
```

**OBSERVED** and hash-verified. All three hosts return the **same document** — sha256
`f8488626…`, md5 `403220ced1a7837372b777fa97ecbb2b` — re-verified byte-identical to
the on-disk capture `disc-eu.json` [source: PROBE-FINDINGS §3; VERSION-AXIS §3a;
CONFIG-NAMESPACE TARGET 1; audit/CLAIM-AUDIT-2026-10-09.md].

It carries `CP[]` in the order **`US, EU, CLINICAL`** and, per region, the keys
`SSOConfiguration`, `Layer7SSOConfiguration`, `Auth0SSOConfiguration`,
`UseSSOConfiguration`, `baseUrlCms`, `baseUrlCareLink`, `baseUrlCumulus`,
`baseUrlPde`, `baseUrlAem`. The CLINICAL entry, verbatim [source: CONFIG-NAMESPACE]:
`SSOConfiguration`/`Layer7SSOConfiguration` = `…carelink-trials.minimed.com/configs/v1/oauth20_sso_carepartner_us_v6.json`;
`Auth0SSOConfiguration` = `…/configs/v1/carepartner_auth0_cl_sso_config_v1.json`;
`UseSSOConfiguration` = `Auth0SSOConfiguration`; `baseUrlCareLink` = `…carelink-trials.minimed.com/api/carepartner/v2`;
`baseUrlCumulus` = `…clcloud-trials.minimed.com/connect/carepartner/v13`; `baseUrlPde` =
`…clcloud-trials.minimed.com/connect/pde/v3`; `baseUrlCms` = `…carelink-content.medtronic.com/carepartner`.
So the trials deployment **splits planes exactly like US and EU** — `carelink-trials`
for the app/API plane, `clcloud-trials` for cumulus + PDE — an answer obtained from
data already on disk at zero request cost [source: AUTH-TENANT §6].

Signed, and the bridge does not check the signature: every discovery response carries a
deterministic **344-char base64 `x-cum-signature`** (decodes to 256 bytes) **only** on
`/connect/carepartner/*/discover/*` — not on `/patient/*`, not on `countries/settings` —
and it **differs between `.eu` and `.com` even though the documents are byte-identical**,
so the signing key or binding is host/region specific. `git grep x-cum-signature` finds
nothing in `src/` or `test/` [source: SECURITY-FINDINGS S4; CLAIM-AUDIT-2026-10-09.md].

`certificates[]` is always exactly **8 entries** and is **identical between the v13
(patient) and v11 (trials) documents** (same sha256), so it is **not a tenant
discriminator** — only a "did Medtronic rotate their pinned roots" tripwire
[source: work/METHOD-FACTS.md; VERSION-AXIS §4].

## 2. Two independent axes

The URL `/connect/carepartner/{basePath}/discover/android/{version}` varies on two
orthogonal things [source: PROBE-FINDINGS deep §2]:

- **Base path = which deployment/tenant.** `v13` → the patient API. `v11` → a
  **trials deployment** — all three regions are returned the trials tenant
  (`carelink-trials` / `clcloud-trials`), so "v11" does not mean "older API", it is a
  different tenant. `v10` → 204 (exists, empty). `v12` → 401. `v14/v15/v16/v20` → 403.
- **App version = which cumulus the returned document references.**

| base version | status | verdict |
|---|---|---|
| v1 – v9, v14 – v16 | 403 | **no route** — dead |
| v10 | 204 | live, empty — exists, returns nothing |
| v11 | 200 | live, public — **trials-tenant** doc (see §7) |
| v12 | 401 | live, token-gated — body unreadable unauthenticated |
| v13 | 200 | live, public — **the patient API** doc |

`v10`'s 204 carries a distinctive `x-amzn-trace-id` with a `Lineage=` field and a
security-header set (`strict-transport-security`, `x-frame-options: sameorigin`,
`content-security-policy: default-src 'self'`, `x-permitted-cross-domain-policies: none`)
that no other cell carries [source: VERSION-AXIS §3a].

## 3. The version axis serves exactly two documents

Probing an `android/X.Y` cell past 3.8 does not give a new API — it re-derives one
of two known documents. Ten further cells (3.11, 3.12, 4.9, 5.1, 6.1, 7.0, 8.0, 9.0,
11.0, 12.0) all returned 200, all legacy: no `Auth0SSOConfiguration`, `baseUrlCumulus`
at `/connect/carepartner/v2`, `CP[]` with only `US,EU` — no CLINICAL at all. After
normalising, every legacy cell from 3.11 to 12.0 is **byte-identical** except the
echoed request string `"config": "android,3.11"` vs `"config": "android,12.0"`
[source: PROBE-FINDINGS §7].

**⚠ Superseded, stated as such rather than dropped:** the earlier note "the enum is
open-ended (10.0 still 200)" is **superseded**. There is no undiscovered Auth0+v13
fallback; 3.6/3.7/3.8 remain the only cells on the track the bridge uses
[source: PROBE-FINDINGS §7; docs/00-summary-the-map.md].

| Cells | Auth0 | cumulus | CLINICAL | Document |
|---|---|---|---|---|
| 3.6, 3.7, 3.8 | yes | **v13** | yes | auth0 doc — what the bridge uses |
| 3.5 | yes | **v11** | yes | auth0 doc, wrong cumulus |
| 3.9 – 12.0 (and ≤ 3.4) | no | v2 | no | legacy doc |

`android/3.5` is a **near miss**: it selects the Auth0 config but points at cumulus
**v11**, so it is still not a usable fallback. The pin stays `android/3.6`
[source: PROBE-FINDINGS §3 and §7].

**Code finding — the ADR 0002 pin guard no longer holds.** `selectAuth0ConfigUrl()` does
`const key = cpEntry.UseSSOConfiguration ?? 'Auth0SSOConfiguration'`, and the
`Auth0SSOConfiguration` **key now exists on every version 3.4 → 5.0**, including the
cumulus-v2 no-Auth0 cells, even where `UseSSOConfiguration` is absent. So bumping
`DISCOVERY_APP_VERSION` to `android/4.0` would **not** throw
`NoAuth0SSOConfigurationError` — it would resolve the same Auth0 config URL and fail
later at the data call, with no named error. The runtime guard the ADR relies on is
currently inert; the pin is protected only by the ADR text and the discovery test.
Suggested fix, **not applied** (a repo change): gate on `baseUrlCumulus` containing `/v13`
too [source: PROBE-FINDINGS §3].

## 4. The Auth0 + cumulus-v13 cell matrix

| Cell | Auth0 | cumulus | CLINICAL | Document |
|---|---|---|---|---|| `*/v13/discover/android/3.6` (all 3 hosts) | yes | **v13** | yes | patient doc — what the bridge uses |
| `.eu` and `-trials` `v11/discover/android/3.6` | yes — the **clinical** config `carepartner_auth0_cl_sso_config_v1.json`, for all three regions | **v13** | yes | trials-tenant doc, Auth0 track |
| `.com` `v11/discover/android/3.6` | **no** | **v2** | **no** | legacy doc — see §7 |
| `-trials` `v6/discover/android/{3.6,3.8}` | **no** | **v2** | **no** | legacy doc — see §8 |
| `*/v12/discover/android/3.6` (all 3 hosts) | ? (401, unreadable) | ? | ? | token-gated — **worth a token** |

**Only two cells give a cumulus-v13 base and survive a code path** — `v13` on all
three hosts, and `v11` on `.eu` and `-trials`. Both were already known; **no new
v13 cell exists** [source: VERSION-AXIS §3c].

Status code alone carries no signal here: a fabricated path, a random UUID and a dead
version all return the same 403. The **response headers** are a perfect, unambiguous
oracle, because this family is AWS API Gateway fronted by CloudFront —
`x-amzn-errortype: MissingAuthenticationTokenException` (403) = **no matching route**,
i.e. **dead**; `UnauthorizedException` **plus `x-ca-err: 990`** (401) = the request
reached a backend authorizer inside Medtronic's Layer7 stack, i.e. **live and
token-gated**; no errortype (200/204) = fully public. Controls fire on every axis: all
7 fabricated controls returned `MissingAuthenticationTokenException` with no CORS
headers (**zero false negatives**) and all 13 `UnauthorizedException` responses were on
`v11`/`v12`/`v13` of `display/message` and `discover` (**zero false positives**).
`access-control-allow-origin: *` on an **OPTIONS** request is the cleanest liveness test
for a resource with no GET method, and **latency is not an oracle** — the host dominates,
not the version [source: VERSION-AXIS §1; docs/00-summary-the-map.md].

## 6. `v12/display/message` — a live version nobody had probed

**`/connect/carepartner/v12/display/message` is live and GET-capable — 401 on all three
hosts.** Prior notes only ever probed `display/message` at v6/v11/v13, so the live GET
set is **`{11, 12, 13}`**, not `{11, 13}`. Our fork's `BLE_API_VERSIONS = [13, 11, 6,
5]` therefore contains a permanently dead `v5` (no route at all, not auth-gated) and
omits a live `v12` — neither changes behaviour today (v13 is tried first and is live),
but v5 should not be in a fallback list and v12 is a free extra candidate
[source: VERSION-AXIS §3b, §6, §7; docs/00-summary-the-map.md].

## 7. `v11/discover` is host-dependent — and that contradicts an earlier claim

PROBE-FINDINGS §3 states "the hostname does not select the region — the doc is global
and carries all three `CP` entries". That was derived from **v13 only**, and it still
holds for v13. **It does not hold for v11** [source: VERSION-AXIS §4]:

| host | `v11/discover/android/3.6` | size | content |
|---|---|---|---|
| `clcloud.minimed.eu` | 200 | **20345 B** | trials tenant: all three regions → `carelink-trials`/`clcloud-trials`, `baseUrlCumulus` = `…/v13`, `baseUrlPde` = `…/pde/v3`, Auth0 config = the **clinical** config, regions `US,EU,CLINICAL` |
| `clcloud-trials.minimed.com` | 200 | **20345 B** | byte-identical to the `.eu` doc (same sha `94b739dda478`) |
| `clcloud.minimed.com` | 200 | **18105 B** | **a different document**: legacy — `SSOConfiguration` only, no Auth0, `baseUrlCumulus` = `…/v2`, `baseUrlPde` = `…/pde/v1`, `baseUrlCareLink` = `/api/carepartner/v1`, **no `baseUrlCms`**, **no `baseUrlAem`**, regions `US,EU` only |

So `buildDiscoveryUrl(isUS)`'s eu/com split is **not** purely cosmetic after all — for
`v11` it selects between two structurally different documents; it stays cosmetic for
v13. `supportedCountries` differs between the two; `certificates[]` does not
[source: VERSION-AXIS §4].

## 8. `v6` — trials-only for discovery, POST-only for data

`/connect/carepartner/v6/discover/android/{3.6,3.8}` is **200 only on
`clcloud-trials.minimed.com`** (10053 B, `x-cum-signature` present) and **403 — no route
— on both patient hosts**. The trials doc is the legacy doc, names a **fourth**
SSO-config filename variant
`https://carelink-trials.minimed.com/configs/v1/sso_cp_us_v6.json`, points every region
at `carelink-trials` hosts, and is **app-version-collapsed** (`android/3.8`
byte-identical to `android/3.6` except the echoed `"config":"android,3.8"`)
[source: VERSION-AXIS §4]. Separately, `v6/display/message` — the exact URL the
vendor's own country-settings config hands out as `blePereodicDataEndpoint` — returns
**403 on GET** and **200 with CORS on OPTIONS** on all three hosts: the resource exists,
the **GET method is not defined**, it is POST-only, matching `work/METHOD-FACTS.md`'s
"POST → 401" and now proven independently from the OPTIONS axis rather than inferred
[source: VERSION-AXIS §1].

## 9. PDE, `csr`, bare cumulus — refined, with a caveat

All six probed paths returned **403 `MissingAuthenticationTokenException`**, 42 B, no
CORS, no `x-cum-signature` — the **router's no-route** response, byte-identical to a
random UUID: `/connect/pde/v3/{display/message,discover/android/3.6}`,
`/connect/pde/v1/display/message`, `/connect/pde/v2/display/message`,
`/connect/csr/v2/display/message`, and the pre-`carepartner` `/connect/v2/display/message`
[source: VERSION-AXIS §5].

**⚠ Correction preserved.** PROBE-FINDINGS §5 recorded `pde/v3` as **401**; the live
probe returned **403** and two re-probes returned 403 with the identical body. The 403
is a **gateway-level** rejection — on `clcloud.*` it means the host does not route the
path to a CareLink-app auth check at all — and is distinct from the
`401 {"error":{"type":"InvalidToken"}}` the bridge's own endpoints return. **The wrong
number originated in `PROBE-FINDINGS.md` §5 and propagated downstream from there**,
including into a published document that was "corrected" from 403 to 401 off the back
of it [source: PROBE-FINDINGS §5; CLAIM-AUDIT-2026-10-09.md].

**Caveat:** a 403 on GET does not prove the resource is unregistered — `v6` proves it.
PDE v3 could equally be a POST-only route, and OPTIONS was not run on the PDE namespace
(the 70-request cap was exhausted). **PDE v3 needs an OPTIONS probe (≲6 requests, ~12 s)
before "does not exist" can be said**; until then the honest phrasing is **"no GET
route", not "absent"** [source: VERSION-AXIS §5].

### 10. Post-2026-10-10 version-axis work

`recon/VERSION-AXIS.md` (2026-10-10) is the pass behind §2–§8: 70 requests, hard cap
reached, GET+OPTIONS only, unauthenticated, and the fabricated-path controls ran
**first** so the oracle verdict is not contaminated by the data it judges
[source: VERSION-AXIS preamble]. The **v2 tree also has a data plane**:
`/patient/v2/monitor/data` → **405** (exists, POST-only) and `/patient/v2/users/me` → **401**
(exists, token-gated) — 405 rather than 404 is the same "exists, POST-only" signature
used elsewhere; not previously recorded [source: CONFIG-NAMESPACE-DEEP TARGET 1]. Live
drift 2026-10-09 → 2026-10-10: the country lists grew
(`personal.common.core.reporting.enabled.countries` 17 → 26) and the config document
grew 20420 B → 20586 B with the same 69-key set — a rollout is in progress
[source: CONFIG-NAMESPACE-DEEP "NEW items"].

One archive limit worth knowing: only **6** archived `discover` captures exist, all
inside a single 6-week window (2026-02-24 → 2026-03-08), and there is **no archived
`v13` discover URL at all** — so the archives neither confirm nor refute that
`android/3.6` → cumulus `v13` is the live generation [source: ARCHIVE-URLS §3, §8].
Finally, `recon/DRIFT-AND-NEW-2026-10-10.md` **does not exist** in this repo; nothing
in it is cited and no claim here depends on it.
## 11. Unresolved disagreements between sources

| Disagreement | Both readings | Canonical page takes ||---|---|---|
| `v6/display/message` on GET | `APP-EMULATION-RESEARCH.md` §1 records **401 for all three of v6/v11/v13** ("All three versions live"); `VERSION-AXIS.md` §1/§3b and `work/METHOD-FACTS.md` (as corrected) record **v6 = 403 on GET, 200 on OPTIONS — POST-only** | the POST-only reading, which `00-summary-the-map.md` and `06-patient-api-surface.md` both state. `APP-EMULATION §1` is **not** marked retracted in its own file, so both are given |
| `work/METHOD-FACTS.md`'s own table | records "Unauth GET = 403" for `{v6,v11,v13}`; direct GET returns **401 for v11 and v13**, only v6 is 403 — almost certainly the `curl -d`/forced-POST artifact that file warns about two paragraphs earlier | v11/v13 = 401; that file's actual conclusion — the bridge POSTs, and that is correct — is unaffected. Full treatment in `docs/09-methodology-and-oracles.md` |
| Consolidated row "3.9–12.0 **(and ≤3.4)** → cumulus **v2**" | the full 23-cell matrix in the **same file** records **3.1 → v6** and **3.2/3.3/3.4 → v11**, so "≤3.4" is not uniformly v2 | the row groups by *document family* (the legacy doc), not by cumulus version. Read it as "legacy document"; take cumulus versions from the full matrix |
| The trials legacy SSO filename | `VERSION-AXIS §4` names `sso_cp_us_v6.json` for the trials `v6/discover` doc; `CONFIG-NAMESPACE.md` TARGET 1 shows `oauth20_sso_carepartner_us_v6.json` for the CLINICAL block of the patient doc | both recorded — two different discovery documents, so it may not be a contradiction, but **no source reconciles them** |

## 12. What we still do not know

| Question | Status |
|---|---|
| What `*/v12/discover/android/*` returns | token-gated on all three hosts — 401, body unreadable. **The most valuable unread cell** |
| Whether PDE v3 has any route at all | needs an OPTIONS probe; "no GET route" is the honest phrasing |
| Which of `{11, 12, 13}` returns the data the bridge wants, with a real token | blocked on credentials |
| Whether the `android/3.6` pin survives the next rotation | guarded only by the ADR text and the discovery test — the runtime guard is inert (§3) |

**Verification lessons applied here.** Re-probe the numbers, don't re-read the notes — the
`pde/v3` error survived four review rounds because each trusted the previous document. And
a hash over a lookup that can silently return `null` manufactures consensus. Both are
written up in [`09-methodology-and-oracles.md`](09-methodology-and-oracles.md)
[source: CLAIM-AUDIT-2026-10-09.md; CROSS-REGION-CONFIG-FINDINGS.md].
