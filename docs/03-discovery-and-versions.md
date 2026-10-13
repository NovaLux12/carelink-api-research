# Discovery and versions

The discovery document, the `carepartner` version axis, and which cells are actually
live. This is the page that pins `android/3.6` —
[the constant `NovaLux12/carelink-bridge`](https://github.com/NovaLux12/carelink-bridge/blob/main/src/discovery.ts)
uses, governed by [its ADR 0002](https://github.com/NovaLux12/carelink-bridge/blob/main/docs/adr/0002-discovery-app-version-pin.md).
Extends
[`00-summary-the-map.md`](00-summary-the-map.md) and agrees with it; the
endpoint-by-endpoint patient-API tables are in
[`06-patient-api-surface.md`](06-patient-api-surface.md), the probing method in
[`09-methodology-and-oracles.md`](09-methodology-and-oracles.md).

**Dated 2026-10-10.**

Legend — **OBSERVED** = seen in a live response · **PUBLISHED** = in a vendor document
served without a login (live, or recovered from a public web archive) · **INFERRED** =
reasoned, not seen.

> **Navigation** — the map: [`00-summary-the-map.md`](00-summary-the-map.md) · ← prev:
> [`02-auth-tenants-and-flows.md`](02-auth-tenants-and-flows.md) · → next:
> [`04-configuration.md`](04-configuration.md) · related:
> [`06-patient-api-surface.md`](06-patient-api-surface.md) ·
> [`09-methodology-and-oracles.md`](09-methodology-and-oracles.md)

Citations are `[source: findings-log/<file> §n]`; `PROBE-FINDINGS` =
`findings-log/probe-2026-10-08/PROBE-FINDINGS.md` and `VERSION-AXIS`, `ARCHIVE-URLS`,
`CONFIG-NAMESPACE`, `CONFIG-NAMESPACE-DEEP` are `…/probe-2026-10-08/recon/<name>.md`.

---

## 1. The discovery document

```
GET https://clcloud.{minimed.eu, minimed.com, clcloud-trials.minimed.com}/connect/carepartner/v13/discover/android/3.6
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

`certificates[]` is always exactly **8 entries** and **identical between the v13 and v11
documents**, so it is **not a tenant discriminator** — only a cert-rotation tripwire
[source: work/METHOD-FACTS.md; VERSION-AXIS §4].

## 2. Two independent axes

The URL `/connect/carepartner/{basePath}/discover/android/{version}` varies on two
orthogonal things [source: PROBE-FINDINGS deep §2]:

- **Base path = which deployment/tenant.** `v13` → the patient API. `v11` → a **trials
  deployment** — all three regions return the trials tenant (`carelink-trials` /
  `clcloud-trials`), so "v11" does not mean "older API", it is a different tenant. `v10`
  → 204 (exists, empty). `v12` → 401. `v14/v15/v16/v20` → 403.
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

Probing an `android/X.Y` cell past 3.8 does not give a new API — it re-derives one of two
known documents. Ten further cells (3.11, 3.12, 4.9, 5.1, 6.1, 7.0, 8.0, 9.0, 11.0, 12.0)
all returned 200, all legacy: no `Auth0SSOConfiguration`, `baseUrlCumulus` at
`/connect/carepartner/v2`, `CP[]` with only `US,EU` — no CLINICAL at all. After
normalising, every legacy cell from 3.11 to 12.0 is **byte-identical** except the echoed
request string `"config": "android,3.11"` vs `"config": "android,12.0"`
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
|---|---|---|---|---|
| `*/v13/discover/android/3.6` (all 3 hosts) | yes | **v13** | yes | patient doc — what the bridge uses |
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

### Confirmed on all three hosts (2026-10-12) — the claim above was under-evidenced, not wrong

The sentence above asserted "401 on all three hosts" on the strength of **one** raw row
(`ORACLE-PROBE-MATRIX` row 52, `clcloud.minimed.eu` only) — the failure mode in
`AGENTS.md` §6 item 1. A 2026-10-12 pass probed the two missing hosts and **confirmed the
claim**: `GET v12/display/message` returns `401` + `x-amzn-errortype: UnauthorizedException`
+ `x-ca-err: 990` on `clcloud.minimed.eu`, `clcloud.minimed.com` and
`clcloud-trials.minimed.com` — **3 of 3**, every one a request that reached Medtronic's
Layer7 authorizer, so the route exists and is token-gated (OBSERVED,
[source: findings-log/2026-10-12-area-b-v12-routing/FINDINGS.md §Finding 1]). There is **no
region split** on this cell. The claim is now 3-host evidenced and pinned in
`regression/hurl/04-deep-surface.hurl`.

**`v12` carries a CORS preflight, exactly like `v11` and `v13`.** `OPTIONS
v{11,12,13}/display/message` all return `200` with `access-control-allow-origin: *` and
`access-control-allow-methods: OPTIONS`, on `.eu` (OBSERVED, same source §Finding 2). This
settles the area's open question: `v12` does **not** differ from `v13` on preflight
presence.

**But the gateway does not add CORS uniformly.** On the same host, in the same session,
`OPTIONS v{11,12,13}/discover/android/3.6` returns **`401`** + `x-ca-err: 990` with **no
`Access-Control-*` header at all**, while `…/display/message` one path-family away returns
`200` + CORS. So "the gateway adds CORS to `clcloud.*`" is **false as a rule** (OBSERVED, a
3 × 2 on `.eu`, same source §Finding 3).

**This is an observation, not a cause** — and as of 2026-10-12 the *reason* it could not be
turned into a cause is itself corrected. The earlier version of this paragraph rested on a
corpus count plus the assertion that every `200` carrying no CORS lived on "a different host
surface". That assertion was **false**: of the ten captured `200` heads with no
`access-control-allow-origin`, **four are on `clcloud.*`** — the discovery documents fetched
by [findings-log/2026-10-12-published-pointers/probe.sh:81-84] — four heads across **three**
cumulus hosts, **two of them on `clcloud.minimed.com`**, so this is 4 cells on 3 hosts and not one
per host. So on
`clcloud.*` **a `200` that carries no preflight exists**, and "carries a preflight" and
"answers `200`" are **not** the same observation. Area X re-derived it live: **9 further
`200`-without-CORS responses — every one a `GET` of a discovery payload, across all three
hosts — and still zero non-2xx responses anywhere in the corpus carrying CORS**
([source: findings-log/2026-10-12-area-x-cors-separation/FINDINGS.md §4]).

**⚠ But the false premise does not select between the two readings this page offered, and
this paragraph previously claimed that it did. That claim is withdrawn.** An earlier draft
argued reading (b) — the route "demands a token on `OPTIONS`" — was *refuted*, because a
CORS-configured route would carry `ACAO` on its own `200` `GET`. **That argument assumes the
thing in dispute**: if `ACAO` is emitted only on `OPTIONS` responses regardless of route, a
configured route's `GET` carries nothing either and the cell is *uninformative* rather than
evidence against. **Reading (b) is not excluded, reading (a) is not excluded, and neither is
"emitted only on `OPTIONS`".** The cause is not established and this page does not establish it.

**What this pass did exclude**, which no earlier pass could test because no earlier pass sent
an `Origin` header to `clcloud.*` at all: **the mechanism "`ACAO` appears only when an `Origin`
is sent" is dead.** Across the **6** route×method pairs where both a bare and an
`Origin`-bearing request were sent — controls excluded, they are not part of the comparison —
status and the full `access-control-*` set were **identical in all 6**; 0 changed.

Separating the three surviving readings needs a `clcloud.*` route that is both
CORS-configured and returns `200` on `GET`; **no such route is recorded on any of the three
hosts** — every GET-public cumulus route is a discovery document whose `OPTIONS` answers
`401`. Successor area in [`11-suggested-research-areas.md`](11-suggested-research-areas.md).

**None of the above makes `v12` browser-callable.** The `401` itself carries no
`Access-Control-*` header, which is the recorded `MissingAllowOriginHeader` failure — still
open in [`10-open-questions.md`](10-open-questions.md) §1, and untouched by this pass.

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

**Update 2026-10-11 (area C):** that caveat is discharged on `clcloud.minimed.eu`.
GET **and** OPTIONS both return 403 `MissingAuthenticationTokenException` on every PDE
cell, so PDE has **no route on any tested method**. The same pass found `csr/v2` and
bare `connect/v2` **live and POST-only**
[findings-log/2026-10-11-pde-csr-oracle/FINDINGS.md].

**Update 2026-10-12 (area N):** **no region split.** Both POST-only routes are live on
`clcloud.minimed.com` and `clcloud-trials.minimed.com` as well, byte-identical,
16 of a 16 cap with controls run first on each host
[findings-log/2026-10-12-csr-cross-host/FINDINGS.md]. PDE was **not** re-probed on those
two hosts — dead on `.eu` is not evidence of dead elsewhere, and that is a named
successor area rather than an assumption.

**Update 2026-10-12 (area U):** that caveat is **discharged**. The same six cells —
`pde/v{1,2,3}/display/message`, `pde/v3/discover/android/3.6`, `csr/v1`, `csr/v3` —
are **dead on both methods on both remaining hosts**: 24 of 24 cells
`403 MissingAuthenticationTokenException`, no CORS, controls run first on each host,
32 of a 32 cap. All 28 no-route bodies in the pass are byte-identical (42 B,
`sha256:f249b63cb2fc`), and that digest is **also** the `.eu` no-route digest recorded
by Area C — so the router's no-route response is one artefact shared by all three
hosts, not three lookalikes [findings-log/2026-10-12-pde-csr-cross-host/FINDINGS.md].

### 9a. ⚠ The published PDE base URL cannot answer, anywhere it is published

**OBSERVED**, and this is the load-bearing consequence of the three preceding updates.

`baseUrlPde` is the **only** base URL in the discovery document whose target has no
route. Every region of every document read on 2026-10-12 publishes one:

| document | regions | `baseUrlPde` | the route it names |
|---|---|---|---|
| `clcloud.minimed.eu` `v13/discover/android/3.6` | US, EU, CLINICAL | `…/connect/pde/v3` | **no GET or OPTIONS route**, either recorded path. GET: **3** attributable hosts. OPTIONS: **2** attributable hosts, plus one unattributable row per recorded path (2) in a ledger that has no `host` column — so "all 3 hosts" held for the GET axis only (area Y) |
| `clcloud.minimed.com` `v13/discover/android/3.6` | US, EU, CLINICAL | `…/connect/pde/v3` | **no route, any method, any host** |
| `clcloud.minimed.com` `v11/discover/android/3.6` (legacy) | US, EU | `…/connect/pde/v1` | **no route, any method, any host** |
| `clcloud-trials.minimed.com` `v6/discover/android/3.6` (legacy) | US, EU | `…/connect/pde/v1` | **no route, any method, any host** |

**A dead route behind a published base URL is a different fact from "the vendor has a
dead route."** The discovery document exists so that a client can resolve its
endpoints from the vendor's own published configuration — that is its entire purpose,
and it is the mechanism this repo's consumer uses. A key that is always present and
never resolvable is a trap published by the vendor's own contract surface, and it is
pinned on both sides: `01-discovery-pin.hurl` asserts the promise, `04-deep-surface.hurl`
asserts the route is absent.

**INFERRED — and this is the one inference in this section, so its assumption is
stated:** that this is a **retired service left in the document** rather than a
deliberate "ignore this key" contract. The reasoning: the same document's
`baseUrlCumulus` is load-bearing, so a published base URL is meant to be used, and a
uniformly dead one is more consistent with an oversight than with a contract. **The
assumption is that publishing a base URL implies intending it to be called, and
nothing observed here settles that** — the namespace 403s *before any application code
runs*, so a client can never reach the point of deciding to ignore it, and no
client-side evidence of intent exists to be gathered. Both readings are given rather
than one picked [findings-log/2026-10-12-published-pointers/FINDINGS.md §2b].

### 9b. ⚠ The discovery document publishes **no** CSR base URL — and it does not need to

**OBSERVED.** `baseUrlCsr` does not exist in any region of any of the four discovery
documents; the discovery document is not where `csr/v2` is addressed (Pinned as a
negative assertion in `01-discovery-pin.hurl`.)

That is **not** the same as "`csr/v2` is unaddressable". The **public config** names it,
in two independent keys, on all three deployments:

| key | value (EU) |
|---|---|
| `system.gc.gz.transition.flags.displayMessage.csrDisplayMessageUrl` | `https://clcloud.minimed.eu/connect/csr/v2/display/message` |
| `csr.cumulus.periodic.data.endpoints.display_message` | `https://clcloud.minimed.eu/connect/csr/v2/display/message` |

Both carry the same URL, and the host is always the deployment's own sibling. So the
two planes are addressed by **different documents**: `baseUrlPde` from discovery, and
`csr/v2` from config. "No key of that name exists" was never the question — see
[`docs/04`](04-configuration.md) §The published pointer set, which also records that the
**bare** `/connect/v2` is named by no published document at all, making the asymmetry
between the two POST-only routes durable [findings-log/2026-10-12-published-pointers/FINDINGS.md §1, §4].

> **⚠ Correction to a claim this repository made about itself.** `docs/11` area T was
> opened on the premise that no `/connect/csr/v2` string was recorded anywhere — and it
> already was, on 2026-10-08, with its value, in
> `findings-log/probe-2026-10-08/recon/ARCHIVE-URLS.md` §1 line 99. It never reached
> `docs/`, and a derived note (`docs/04`, key listed with no value) then let a successor
> area assert a negative its own log contradicted. **The finding was never lost; it was
> lost between the log and the docs.** Grepping this repo's own logs before writing an
> area costs nothing and would have caught it.

### 9c. ⚠ No vendor *web* bundle in the corpus reads the discovery document at all

**Added 2026-10-13** (area V, #42). §9a concludes that nothing on the live surface can
say whether a client intends to use `baseUrlPde`. Area V asked the follow-up — can the
vendor's **own shipped bundles** say it — and the honest answer is that **this corpus
does not contain that client**, so the negative below is a statement about a
*document*, not about a *decision*.

**OBSERVED**, 2026-10-13: four `main.*.js` bundles and one `runtime.*.js` re-fetched
and grepped exhaustively [source: findings-log/2026-10-13-area-v-pde-clients/FINDINGS.md]:

| token | patient `.eu` | patient `.com` | clinic portal | support portal | patient runtime |
|---|---|---|---|---|---|
| `baseUrlPde` | 0 | 0 | 0 | 0 | 0 |
| `/connect/pde` | 0 | 0 | 0 | 0 | 0 |
| `pde` (case-sensitive) | **0** | **0** | 5 | 5 | 0 |
| `baseUrlCumulus` / `baseUrlCms` / `baseUrlAem` / `baseUrlCareLink` | 0 | 0 | 0 | 0 | 0 |
| `discover` / `discover/android` | 0 | 0 | 0 | 0 | 0 |
| `clcloud` / `api/carepartner` | 0 | 0 | 0 | 0 | 0 |

**Every hit is accounted for.** The 5 case-sensitive `pde` hits in each portal build
are substrings of **zxcvbn password-dictionary entries** — `dropdead`, `helpdesk`,
`herpderp`, `topdevice`, `hampden` at bytes 269182, 293243, 325138, 326919, 535085,
identically in both builds. They are literals in a password-strength wordlist, **not
directives**: the same false-hit class `docs/09` §5 records for `ngp`/`guardian` in
this very bundle. The patient bundle's 25 case-**insensitive** hits are seven
unrelated identifiers (`propDecorators`, `removeStylesOnCompDestroy`,
`isDesktopDevice`, `WPDesktop`, `mapDeviceModelName`, `getGroupDelayControl`,
`LoopDetected`). The only `baseUrl` token in the patient bundle is `this.baseUrl`,
assigned from `getBaseCmsUrl()` and used to fetch a CMS media file — a different
`baseUrl`, not a published pointer.

**So the negative is not "no client calls `baseUrlPde`"; it is "no web bundle here
reads the discovery document at all."** That is the finding, and it is **OBSERVED**.

**INFERRED — and this is the load-bearing limit, so its assumption is stated:** the
consumer of this document is a **mobile** client, because the document's own path
names it — `discover/android/3.6`. No mobile artefact is served by any host probed, so
**whether any client follows `baseUrlPde` remains unobserved in both directions**, and
§9a's INFERRED reading is **unchanged and still unresolved**: this pass produced no
evidence about intent either way.

**Corpus and its boundaries, so the negative is not over-read.** Four eager main
bundles across three hosts — the patient bundle `main.6595daf83bd6d4b1.js`
(3,417,255 B, sha256 `0fb4fbd4…`, **byte-identical on `carelink.minimed.eu` and
`carelink.minimed.com`**) plus the two portal builds, whose digests reproduce areas A
and G exactly. The **211 lazy chunks are not in this corpus**; their current inventory
is committed at
[findings-log/2026-10-13-area-v-pde-clients/chunks.txt](../findings-log/2026-10-13-area-v-pde-clients/chunks.txt)
and reproduces the 2026-10-08 record — the patient build **has not bumped in five
days**, so the stale-capture worry the area was filed with turned out to be the
opposite of the risk: it was superseded by an *identical* build, not by a changed one.

**What the same corpus did settle**, on the neighbouring axis: the patient bundle
**does** follow `csr.cumulus.periodic.data.endpoints` and POSTs its `display_message`
field, while naming `system.gc.gz.transition.flags` and never reading it — see
[`docs/04`](04-configuration.md) §Which of the two identical CSR pointers the shipped
client actually follows. **The contrast is the point**: a published pointer a shipped
client acts on, and one it names but ignores, are now separated by evidence.
`baseUrlPde` sits outside that distinction entirely — no web bundle names it, because
none of them reads this document.

### 10. Post-2026-10-10 version-axis work

`recon/VERSION-AXIS.md` (2026-10-10) is the pass behind §2–§8: 70 requests, hard cap
reached, GET+OPTIONS only, unauthenticated, controls run **first** so the oracle verdict
is not contaminated by the data it judges [source: VERSION-AXIS preamble]. The **v2 tree
also has a data plane**:
`/patient/v2/monitor/data` → **405** (exists, POST-only) and `/patient/v2/users/me` → **401**
(exists, token-gated) — 405 rather than 404 is the same "exists, POST-only" signature
used elsewhere; not previously recorded [source: CONFIG-NAMESPACE-DEEP TARGET 1]. Live
drift 2026-10-09 → 2026-10-10: the country lists grew
(`personal.common.core.reporting.enabled.countries` 17 → 29) and the config document
grew 20420 B → 20586 B with the same 69-key set — a rollout is in progress
[source: CONFIG-NAMESPACE-DEEP "NEW items"]. Note also that only **6** archived
`discover` captures exist, all in one 6-week window (2026-02-24 → 2026-03-08), with **no
archived `v13` discover URL at all** — so the archives neither confirm nor refute the
`android/3.6` → cumulus `v13` mapping [source: ARCHIVE-URLS §3, §8].
`recon/DRIFT-AND-NEW-2026-10-10.md` **does not exist** in this repo; nothing in it is
cited and no claim here depends on it.
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
| Which of `{11, 12, 13}` returns what the bridge wants, with a real token | blocked on credentials |
| Whether the `android/3.6` pin survives the next rotation | guarded only by the ADR text and the discovery test — the runtime guard is inert (§3) |

**Verification lessons applied here:** re-probe the numbers rather than re-reading notes,
and never hash a lookup that can silently return `null` — both are written up in
[`09-methodology-and-oracles.md`](09-methodology-and-oracles.md) [source:
CLAIM-AUDIT-2026-10-09.md; CROSS-REGION-CONFIG-FINDINGS.md].
