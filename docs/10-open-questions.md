# Open questions

Everything not yet known, with what would settle it — and, just as important,
what was **searched and closed** versus what is merely unknown. This project has
both, and the difference matters: a closed question should never be re-run, an
open one should not be guessed at. Extends
[`00-summary-the-map.md`](00-summary-the-map.md).

Legend — **OBSERVED** = seen in a live response · **PUBLISHED** = in a vendor
document served without a login · **INFERRED** = reasoned, not seen.

Citations are `[source: findings-log/<file> §n]`; inside tables the bare
filename is the same file: `PROBE-FINDINGS` =
`findings-log/probe-2026-10-08/PROBE-FINDINGS.md`, `METHOD-FACTS` =
`findings-log/probe-2026-10-08/work/METHOD-FACTS.md`, `VALIDATION-RUNBOOK` =
`findings-log/probe-2026-10-08/work/VALIDATION-RUNBOOK.md`, `VERSION-AXIS` =
`findings-log/probe-2026-10-08/recon/VERSION-AXIS.md`, `HCP-SCHEMA` =
`findings-log/probe-2026-10-08/recon/HCP-CONFIG-SCHEMA.md`, `CROSS-REGION` =
`findings-log/probe-2026-10-08/CROSS-REGION-CONFIG-FINDINGS.md`, `AUTH-TENANT` =
`findings-log/probe-2026-10-08/AUTH-TENANT-FINDINGS.md`, `AWS-GATEWAYS` =
`findings-log/probe-2026-10-08/recon/AWS-GATEWAYS.md`, `RECON-SUBDOMAINS` =
`findings-log/probe-2026-10-08/recon/RECON-SUBDOMAINS.md`, `COMMONCRAWL` =
`findings-log/probe-2026-10-08/recon/cc/COMMONCRAWL-URLS.md`, `PUBLIC-CONFIG` =
`findings-log/probe-2026-10-08/PUBLIC-CONFIG-FINDINGS.md`, `CONFIG-NS` =
`findings-log/probe-2026-10-08/recon/CONFIG-NAMESPACE.md`, `CONFIG-DEEP` =
`findings-log/probe-2026-10-08/recon/CONFIG-NAMESPACE-DEEP.md`, `PATIENT-VOCAB` =
`findings-log/probe-2026-10-08/recov/PATIENT-APP-VOCABULARY.md`, `GAPS-0721` =
`findings-log/medtronic-carelink-2026-07-21/03-data-model-and-gaps.md`,
`SECURITY-FINDINGS` = `findings-log/probe-2026-10-08/SECURITY-FINDINGS.md`,
`CLAIM-AUDIT` = `findings-log/probe-2026-10-08/audit/CLAIM-AUDIT-2026-10-09.md`,
`DRIFT-AND-NEW` = `findings-log/probe-2026-10-08/recon/DRIFT-AND-NEW-2026-10-10.md`.

## 1. Open questions

| Question | Current best guess (class) | Exactly what would settle it | Issue |
|---|---|---|---|
| Which field carries `deviceFamily`, and in what casing | **The field name is settled; the value's casing is not.** `/patient/monitor/data` carries **`deviceFamily`** (routing discriminator) and the Cumulus/ble payload carries **`medicalDeviceFamily`** (reported family) — agreed independently by three clients at named commits (`nightscout-connect` `index.js:587`; xDrip `MonitorData.java:5` + `RecentData.java:102`; `CarlosJPV` `types/carelink.ts:29-34`). **Every observed value so far is a `medicalDeviceFamily` value** (`GUARDIAN`, `MINIMED`, `PARADIGM`); no client reports a `deviceFamily` value, so its wire casing is still unobserved. Note `docs/05` previously recorded `deviceFamily` as "not an API field" — **that was wrong and is corrected in place** (OBSERVED, third-party source; INFERRED for the wire value) [findings-log/2026-10-11-third-party-client-sources/FINDINGS.md §1, §5.1] | **One authenticated `GET /patient/monitor/data` response**, logged key-names-only; paste verbatim strings, do not paraphrase [VALIDATION-RUNBOOK Tier 1] | #81 |
| The NGP alarm-code vocabulary | **Not published on any unauthenticated surface** — 28 key names probed, all 404, under case-sensitivity and 401-vs-404 controls; the patient bundle's `N\d\d` tokens minify to Angular internals and a Samsung device regex, so #84 is explicitly **not claimed answered** by the 2026-10-10 pass (OBSERVED negatives) [HCP-SCHEMA §7; DRIFT-AND-NEW §Not chased] | An authenticated `POST hcp/configuration/application` (clinician token; returns a large `appConfig` blob) or a real device/pump report [HCP-SCHEMA §7] | #84 |
| Whether the alarm wire form is numeric or string (`lastAlarm.code`) | Unknown; the community alarm table is paradigm + NGP-era (INFERRED, 2015 gist) [GAPS-0721 P0.2] | Read `lastAlarm.code`'s JSON type from one live payload [VALIDATION-RUNBOOK Tier 3] | #84 |
| Report bodies — and from which host | Plausibly richer than `/patient/monitor/data` (INFERRED) [SECURITY-FINDINGS §reports]; the surface is wider than recorded: `/patient/reports/*` is live on `carelink.*`, gated 401/405, and `commoncore`'s 502 is an origin-side DNS failure, not absence [DRIFT-AND-NEW §2–3] | An authenticated request with a real token, per host; `commoncore` is **never archived in any crawl**, so archives cannot help [AUTH-TENANT §9 standing blind spot] | #76 |
| Which host actually returns `connect/data` with a token | Both hosts answer 401 unauthenticated; the **method** question is closed (bridge's GET/POST usage is correct), only the **host** is open (OBSERVED) [METHOD-FACTS §Conclusion for #74; CLAIM-AUDIT batch 1] | Request `connect/data` from **both** `carelink.*` and `clcloud.*` with a valid token and compare bodies [VALIDATION-RUNBOOK Tier 2] | #74 |
| Which of cumulus `v11`/`v12`/`v13` returns the data the bridge wants | All three are live; the bridge's `BLE_API_VERSIONS = [13, 11, 6, 5]` contains a permanently dead `v5` and omits a live `v12` — behaviour unchanged today because v13 answers first (OBSERVED) [VERSION-AXIS §6, §7] | Blocked on a token — route existence is settled, data is not [PROBE-FINDINGS §7] | not numbered in any source |
| The `v12/discover` document's contents | Exists, 401 on all three hosts (OBSERVED) [VERSION-AXIS §3a] | Blocked on a token | not numbered in any source |
| Whether either US/trials reports-broker key is live | Unknown — **deliberately not tested**: it needs an authenticated call to a production medical-data service, outside a read-only pass [CROSS-REGION §SECURITY] | An authenticated call with a real token, by someone authorised to make one | not numbered in any source |
| The `markers[]` per-entry payload schema | The 12-entry-type vocabulary is settled and double-sourced; the per-entry field names (`removalType`, `removalReason`, `sensorInsertionLocation`, `timecapUnscrewed`, …) are call-site fields, not config (OBSERVED) [HCP-SCHEMA §8; CHUNK-CORPUS] | `GET hcp/patients/{patientId}/logbook/entries` with a clinician token — patient-scoped, deliberately not requested [HCP-SCHEMA §8] | #76 |
| Would any host accept a token minted by a shadow Auth0 tenant | Should not — four tenants, completely disjoint JWKS kids; if anything accepts it, the bug is a loose `kid`/`aud` verifier, not a key leak (INFERRED from OBSERVED key sets) [AUTH-TENANT §8] | Blocked on a token; COMMONCRAWL §4e's prose says **12 candidate issuer hostnames (8 archive-only, keys unknown)**, but its own list names **7** new hosts, which makes 11 — the section disagrees with itself and the two readings are both given here rather than one picked (OBSERVED disagreement). 4 with known key material either way [COMMONCRAWL §4e] | not numbered in any source |
| `relativeOffset` semantics for pump-offset rounding | Unknown; DST transitions are the known failure mode of the current 15-minute rounding (INFERRED) [GAPS-0721 P0.3; docs/00-summary-the-map.md] | Blocked on a real token | not numbered in any source |
| Timestamp semantics generally | **Three shipping clients disagree, and the disagreement is now documented.** (a) `nightscout-connect` rewrites every timestamp's offset from the conduit's own `lastConduitDateTime` (`index.js:697-716`); (b) `CarlosJPV` prefers `patientData.clientTimeZoneName` and **explicitly records (a) as a bug** — an offline phone freezes that field and skews the offset, producing future-dated readings that xDrip+ rejects with *"bgreading is too far in the future"* (`src/server.ts:165-172`); (c) xDrip shifts by a whole-hour diff from `lastConduitUpdateServerDateTime − lastConduitDateTime`, bounded to <26h (`CareLinkClient.java:850-907`). All three are SOURCE-OBSERVED. The question is better posed as **which field wins** (OBSERVED disagreement, third-party sources) [findings-log/2026-10-11-third-party-client-sources/FINDINGS.md §2] | Blocked on a token — route existence is settled, semantics are not | #85 |
| The retina service's real host | Composed at runtime from three server-supplied config fields; the static host is not in any artefact (OBSERVED) [AUTH-TENANT §7] | An authenticated fetch of the portal config | not numbered in any source |
| The Instinct-era Cumulus-v2 data plane's audience/scope | Assume a distinct audience/scope until disproven on real hardware (INFERRED) [findings-log/cumulus-v2-spike.md §Expected auth] | A captured token from a real device, probed before assuming parity | not numbered in any source |
| Refresh-token lifetime (`personal.session.timeout = 30`) | Published value 30 — semantics unverified (OBSERVED value, INFERRED meaning) [PUBLIC-CONFIG] | A token lifetime observation in November | not numbered in any source |
| Why `dialog-lite`'s backend raises on every invocation | Most likely a broken/misconfigured deployment; "cannot be settled from outside" (INFERRED) [AWS-GATEWAYS §6] | Nothing available from outside — blocked | not numbered in any source |
| Which of three readings explains `patient-timeline`'s no-route 403s (no routes deployed / write-only routes / live stage isn't `prod`) | All three are consistent with the evidence and cannot be separated with GET-only probing (OBSERVED) [AWS-GATEWAYS §6] | The single separating test is an authentication attempt — **excluded by this project's constraints**; recommended first follow-up only with explicit sign-off | not numbered in any source |

## 2. Searched and closed — do not re-run these

Each of these was an open question that a pass answered with evidence. The
search is closed; where a *value* remains unknown (e.g. the NGP vocabulary
itself) it appears in the open table above instead, not here.

| Closed question | Verdict | Evidence |
|---|---|---|
| Is the `device_code` grant usable for headless login? | **Rejected server-side** for both client_ids — 403 `unauthorized_client`; grant advertised but not enabled | [PROBE-FINDINGS deep §1; CLAIM-AUDIT batch 2] |
| Which CLINICAL base URLs does the trials tenant use? | `clcloud-trials.minimed.com` for Cumulus **and** PDE; `carelink-trials.minimed.com` for the app/API — **answered from data already on disk, zero requests** | [CONFIG-NS TARGET 1] |
| What does the `_vN` suffix in `oauth20_sso_carepartner_*_vN.json` mean? | A **certificate-rollover counter**, not an API version — v5 and v6 are functionally identical, one pinned-cert roll apart | [CONFIG-NS TARGET 3] |
| Is the NGP alarm vocabulary published unauthenticated? | **Firm negative** — 28 key names across both rounds, all 404, under case-sensitivity and 401-vs-404 controls; negative in the patient config, the clinic bundle, all 224 lazy chunks, and the patient bundle | [HCP-SCHEMA §7; PATIENT-VOCAB; JSMAP-HUNT] |
| Does `/patient/v2/configuration/` have siblings? | **Closed namespace** — six derived candidates 404; `/public` is the only member | [CROSS-REGION; CONFIG-DEEP TARGET 1] |
| Is there a fourth patient deployment? | **No** — every recorded `*trials*` host (16) is `.com`; no `.eu` counterpart. Answered from recorded evidence with zero DNS/requests | [CONFIG-DEEP TARGET 5] |
| Are `*.minimed.*` / `*.medtronic.eu` worth re-enumerating? | **Saturated** — 213 + 385 + 129 names collected, 0 new; cert-SAN recursion gained nothing (all single-SAN) | [RECON-SUBDOMAINS §0.3, §4.6, §8] |
| Do source maps exist on any portal bundle? | **Definitively absent** — exhaustive offline grep + 62 live `.map` probes across four hosts, plus header checks | [JSMAP-HUNT; CHUNK-CORPUS] |
| Is there a published OpenAPI/Swagger document? | **No** — 11 conventional paths × 3 hosts: Apache 404, the 403 auth wall, and the SPA fallback respectively | [CHUNK-CORPUS §OpenAPI] |
| Is `hcp/configuration/public/*` fully mapped? | **Yes — do not re-run.** 13 keys return JSON, 1 is token-gated, 1 is `{}`; every other bundle-known name is 404 | [HCP-SCHEMA §10] |
| Is `certificates[]` a tenant discriminator (issue #77)? | **No** — always exactly 8 entries, identical between v13 and v11 documents; a change-detector on it is only a cert-rotation tripwire | [METHOD-FACTS §Conclusion for #77] |
| What are `baseUrlCms` / `baseUrlAem`? | A private S3 bucket (403 AccessDenied) and an Akamai-gated marketing dam — both closed, neither on the data path | [CONFIG-NS TARGET 4] |
| Is the legacy Layer7 auth edge alive? | **Unambiguously dead** — both `mdtlogin*` hosts resolve but refuse TCP :443; pinned leaf certs expired 2026-03-06 (US/CL) and 2025-11-19 (EU) | [CONFIG-NS §Is it stale; AUTH-TENANT §6] |
| Does `/connect/session/status` exist? | Advertised in the legacy config; **genuinely absent** on the Auth0 host (404 on GET and POST) — dead config there | [AUTH-TENANT §5; PROBE-FINDINGS deep §5] |
| Is the discovery version enum open-ended? | **Superseded** — the axis serves exactly two documents past 3.8; no undiscovered Auth0+v13 fallback exists | [PROBE-FINDINGS §7; docs/00-summary-the-map.md] |
| Does Common Crawl cover the API surface? | **Essentially zero** — not one record for any `carelink*`/`clcloud*`/`carelinkhp*` host in either of two crawls; Wayback is the only usable archive | [COMMONCRAWL §0–§1] |
| Is `carelink.medtronic.eu` a second portal deployment? | **No — false positive.** It serves the 5518-byte SPA fallback, md5-identical to the `carelinkhp` trap page (gzipped on the wire) | [CONFIG-DEEP TARGET 5; docs/00-summary-the-map.md correction] |
| Is `pde/v3` status 401 or 403? | **403**, re-probed twice — the earlier 401 was a note error that propagated through three review rounds before being caught | [CLAIM-AUDIT §FOUND WRONG] |
| What is the family-map hash? | **`8ce419a22fd3`** — the prose note's `215e6671de09` was wrong; the pinned regression assertion had been right throughout | [DRIFT-AND-NEW §Documented defect] |
| Any new hosts since 2026-10-09? | **One**, `mdtshare2.medtronic.com`, and it is NXDOMAIN — the space was already covered | [DRIFT-AND-NEW §Clean negatives] |
| Whether any `/connect/pde/v3` route exists at all | **No route on any tested method.** GET 403 + OPTIONS 403 with `MissingAuthenticationTokenException` across `pde/v{1,2,3}/display/message`, `pde/v3/discover/android/3.6`, `csr/v1`, `csr/v3` and the bare `connect/carepartner/` prefixes — supersedes the VERSION-AXIS §5 caveat for PDE. The same pass found `csr/v2` and bare `connect/v2` **live, POST-only** [findings-log/2026-10-11-pde-csr-oracle/FINDINGS.md] |
| Did the vendor mass-rotate certificates? | **No** — no certificate issued on or after 2026-10-08 in any of the four CT zones; `clcloud-trials` still on its 2026-04-13 cert, so the 2026-10-28 expiry watch stays open | [DRIFT-AND-NEW §Clean negatives] |

## 3. Unknown — not in any source

Stated as such rather than guessed at:

- Why `clcloud.medtronic.com` gateway-gates the discovery document while
  `clcloud.medtronic.eu` serves it open — recorded, **not diagnosed**
  [RECON-SUBDOMAINS §4.3].
- Whether any dev/stage host behaves differently from prod — deliberately never
  probed; passively enumerated only by policy [PROBE-FINDINGS §1].
- The true origins behind CloudFront (`144.15.x.x`) — they refuse the public TLS
  handshake and were left alone [PROBE-FINDINGS deep §7].
- The argument name `/patient/countries/account/types` wants — the endpoint
  exists (400 `arg0 must not be null`) but guessing argument names was out of
  scope [CONFIG-DEEP TARGET 4].
- The `n…z` tail of the `medtronic.com` Wayback sweep and a dedicated
  `carelink-clinical-*` deep sweep — not attempted for want of request budget
  (19 requests unused) [COMMONCRAWL §7].
