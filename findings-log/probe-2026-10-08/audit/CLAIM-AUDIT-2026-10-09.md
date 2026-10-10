# Claim audit of the facts the PR publishes (2026-10-09)

Independent re-verification, same session, same UA, low rate. The point is that
four review rounds all trusted the research notes; this pass re-probed the
load-bearing claims directly.

## Verified correct (re-probed, match the docs)

| Claim | Re-probe |
|---|---|
| discovery doc is global, byte-identical across `clcloud.minimed.{eu,com}` and `clcloud-trials.minimed.com` | sha256 identical, 1 distinct value; `f8488626…` unchanged |
| `certificates[]` is 8 entries carrying ONE cert for 8 hostnames | 8 entries, 1 distinct cert, same 8 hosts |
| `x-cum-signature` is 344 base64 chars, deterministic, decodes to 256 bytes | 344 chars, identical across 2 requests, 256 bytes |
| metadata endpoints only on `carelink.*`; `connect/data` on both | `users/me` carelink=401 clcloud=403; `monitor/data` carelink=401 clcloud=403; `connect/data` carelink=401 clcloud=**401** |
| `display/message` is clcloud-only, POST=401 / GET=403 | POST=401, GET=403, carelink host=404 |
| `/patient/countries/settings?countryCode=GB` is 200 unauthenticated | 200 |
| `/patient/configuration/system/personal.cp.m2m.enabled` is 200 unauth on carelink, 403 on clcloud | 200 / 403 |

## ❌ FOUND WRONG — `pde/v3` status is 403, not 401

**This one is wrong in the branch and is a correction-of-a-correction.**

- The original live probe in this session returned **403**
  `{"message":"Missing Authentication Token"}` for `/connect/pde/v3/monitor/data`.
- `PROBE-FINDINGS.md` then recorded it as **401**.
- Review round 3 found the ARCHITECTURE doc said 403, checked it against
  PROBE-FINDINGS.md (which said 401), and "corrected" ARCHITECTURE from
  403 (right) to **401 (wrong)**.
- It was then marked VERIFIED in round 4 — because all four rounds trusted the
  notes rather than re-probing.

**Re-probed twice just now: HTTP 403, body `{"message":"Missing Authentication
Token"}`, identical both times.**

The distinction matters for the doc's purpose: on `clcloud.*`, **403 with that
body is the gateway-level rejection** (the host does not route the path to a
CareLink-app auth check), whereas **401 `{"error":{"type":"InvalidToken"}}` is
the app-level rejection** the bridge's own endpoints give. `/patient/users/me`
on clcloud behaves identically to `pde/v3` — both 403 with the same body.

**Fix:** `docs/ARCHITECTURE.md:316` → `**403**`, and the explanatory paragraph
must say the 403 is gateway-level so nobody reads it as "exists and needs a
CareLink token". Also correct `PROBE-FINDINGS.md`, and record in ADR/CHANGELOG
that this was a correction of a correction.

## Method note

This is the failure mode the whole review chain exists to catch: a claim
propagates from probe output → notes → doc → reviewer, and each hop trusts the
previous one. Re-probe the numbers, don't re-read the notes.

## Second batch — all verified correct

| Claim | Re-probe |
|---|---|
| OAuth `redirect_uri` is strictly allowlisted | attacker redirect → **403** |
| PKCE `S256` accepted | 302 |
| PKCE **`plain` accepted** (the S2 weakness) | 302 |
| PKCE **omitted entirely accepted** | 302 |
| `device_code` rejected for both tenants | 403 `unauthorized_client`, "Grant type … not allowed for the client" — identical on eu and com |
| `cpMobileAppAvailable` true only for AU | AU=true; GB/US/DE/FR absent → flag present-but-false; IE/NL/NZ absent |
| `defaultDevice` = `GM` everywhere probed | GM in all 8 |
| GB `bgUnits` = `MMOL_L`, `region` = `OUS` | MMOL_L / OUS — confirms the mmol/L path and the region-naming note |
| `blePereodicDataEndpoint` handed out by country settings | `https://clcloud.minimed.eu/connect/carepartner/v6/display/message`, identical for GB and US |

So the ONLY wrong published fact found is the PDE status code. Everything else
the four review rounds trusted (and everything they "corrected") holds.

## Third batch — a doc-clarity finding (NG-note), not a code defect

Country-settings `bgUnits` is **not** consistent with real-world units:
AU/GB/IE/NL/NZ → `MMOL_L`; **US → `MG_DL` with `region: US`**; but
**DE and FR → `MG_DL` with `region: OUS`** (re-probed with `language=de`
for DE, so it is not a language artifact).

Germany and France are mmol/L countries, so a reader would reasonably infer
that country-settings `bgUnits` reflects the account's unit. It does not —
it is a per-country config preference.

**The bridge is unaffected**, which is the important part: `transform/index.ts`
reads the unit from the **data payload** (`data.bgUnits`/`bgunits`), never from
country settings, so the P0.1 mmol/L safety conversion keys off what CareLink
actually sends. Verified: `src/transform/index.ts:21-22` reads
`data.bgunits ?? data.bgUnits`.

**Doc finding:** `docs/ARCHITECTURE.md:378` says "(GB also reports
`bgUnits: MMOL_L`)" in the region-naming table. True as stated, but it sits
where a reader is learning the region field and invites the inference that this
field tracks the account unit. Suggested qualification: note that
country-settings `bgUnits` is a per-country display preference and that the
account's real unit comes from the data payload.
