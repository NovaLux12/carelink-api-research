# Fresh drift sweep — 2026-10-10

**Pass type:** targeted drift check against the 2026-10-08/09 baseline, plus the
three things that baseline explicitly flagged for re-checking.

**Budget:** 119 requests accounted for in the deliverable in `research/` of the
originating repo. GET-only, unauthenticated, ≥2s per host.

> **Provenance:** this file is a **reconstruction from the agent's report**, because
> the agent's own file was never written to disk. The findings below are as the agent
> reported them; the command-level evidence table is **not reproduced here** and
> lives in the originating workspace until it is re-derived. Re-verify before
> treating any row as OBSERVED.

---

## Drift — two things moved

### Real drift: the EU reporting-country rollout

The EU public config grew by **300 bytes and 24 leaf keys in one day**.

`personal.common.core.reporting.enabled.countries` went **17 → 29**:

```
+ AU HR CZ EG GE IL PL RO RS SK SI AE
```

`personal.inpen.supported.countries.enabledPerCountry` expanded in **perfect
lockstep**. `.com` and `-trials` configs were byte-identical to their baseline
copies — so this is an EU-side rollout, not a global refresh.

**Why it matters:** a client that cached "these countries have reporting" is now
wrong for 12 countries, silently. This is now pinned by a drift guard in
`regression/hurl/05-public-config.check.sh`.

### Documented defect: an unreproducible pinned hash

`CROSS-REGION-CONFIG-FINDINGS.md` gave
`personal.device.family.to.model.mapping` the hash `215e6671de09`. It actually
hashes to **`8ce419a22fd3`** — on every baseline artefact on disk *and* on the live
body.

The regression suite asserted the correct value throughout and passed. So the
pinned assertion was right and the hand-written note was wrong — which is how it
surfaced. Corrected in place with the correction attached.

**The transferable lesson:** values quoted in prose notes are not evidence. The
pinned assertion is. This is the same failure class as the source-map edit in
`CHUNK-CORPUS-FINDINGS.md` — a claim never re-derived from its artefact.

---

## Held (re-verified, no change)

| Claim | Result |
|---|---|
| Discovery document byte-identical | md5 `403220ced1a7…` unchanged |
| `x-cum-signature` for `clcloud.minimed.eu/v13/3.6` | still `640e0f934d2cc9bb`, matching the 10-08 capture |
| Four Auth0 tenants, eight disjoint JWKS kids | unchanged |
| `cpMobileAppAvailable` true only for AU | unchanged |
| `defaultDevice` = `GM` everywhere | unchanged |
| `personal.cp.m2m.enabled` = `{"value":"true"}` | unchanged |
| `lhpro.max = 4292967295` (vendor bug) | **still present** — issue #97 unresolved upstream |

---

## What is genuinely new

### 1. Five hosts, not two — the leaked bundle replicates wider

`carelink-support.medtronic.eu` serves the same 5518-byte SPA document shape but a
**different build**: `main.759cddab23085086.js`, sha256 `f637c8d0…`.

It carries the **identical hardcoded `x-api-key` material** and the same
`dev.commoncore.medtronic.eu` build-config bug as the analysed bundle — confirmed
by boolean comparison, values not reproduced.

**Consequence:** the S3 finding now spans **five** hosts. A remediation
conversation naming only `carelinkhp` fixes a fraction of it.

### 2. A second application nobody had found

`carelink-support.minimed.eu` and `carelink.minimed.eu` serve a **completely
different Angular app** — the **patient-facing client** — with **70 `/patient/*`
endpoints that appear nowhere in the 183-path clinician map.**

This resolves PROBE-FINDINGS §6's open question by naming a **third** API shape:
`/patient/v2/monitor/data` (live, **405 = POST-only**). Neither the bridge's bare
`/patient/*` nor the discovery doc's `/api/carepartner/v2/*`.

It also names `/patient/reports/*` on `carelink.*` — **not** on
`commoncore.medtronic.*` — and uses **MTCaptcha alongside Google reCAPTCHA**.

> **⚠ This supersedes a note that would otherwise have misdirected work:** the
> reports namespace behind issue #76 was mapped only to `commoncore.medtronic.{eu,com}`
> and recorded as unreachable. It is **live on the patient host**, gated 401/405
> rather than 403.

### 3. `commoncore` is a DNS failure, not an absence

`commoncore.medtronic.{eu,com}` still don't serve at root — but the reason was never
recorded: CloudFront returns **502 "wasn't able to resolve the origin domain
name."** An origin-side DNS failure.

`/reports-broker/v1/ocl` still returns the 403 `MissingAuthenticationTokenException`.

### 4. Two more unauthenticated public-data endpoints

- **`/patient/countries`** — 117 countries with dial codes. Byte-identical on EU and
  `.com`; differently-ordered on trials.
- **`/patient/languages`**

---

## Clean negatives, and the checks that prove them

- **No new hosts.** The `%.medtronic.com` CT corpus that previously returned a
  150-byte page is now **4003 certs / 1117 names**. Diffing against every on-disk
  baseline list yields exactly one new name — `mdtshare2.medtronic.com` —
  which is **NXDOMAIN**. The space was already covered.
- **No certificate issued on or after 2026-10-08 in any of the four CT zones.**
  Newest per zone: `minimed.eu` 09-18, `minimed.com` 09-29, `medtronic.eu` 10-01,
  `medtronic.com` 2021-10-01 (**that index is five years stale** — treat its
  negatives with care). So no cert-mass-rotation.
- **`clcloud-trials.minimed.com` still on its 2026-04-13 cert**, the one flagged for
  2026-10-28 expiry. Renewal watch remains open.
- Of nine unprobed hosts, all NXDOMAIN except `www.carelink.minimed.eu` (live CNAME,
  SNI rejected by CloudFront) and `www.carelink.minimed.com` (resolves to the
  internal `144.15.206.46`, same as the rest of its class).

---

## Not chased, on purpose

The `N\d\d` tokens in the patient bundle minify to Angular internals and a Samsung
device regex. **Issue #84 stays open and is explicitly not claimed answered** by this
pass.
