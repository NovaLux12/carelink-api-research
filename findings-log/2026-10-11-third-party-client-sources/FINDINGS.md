# Third-party client sources — nightscout-connect, xDrip CareLinkFollow, CarlosJPV cumulus bridge

**Pass date:** 2026-10-11 · **Method:** read-only static analysis of three public
source repositories + their public PR/issue metadata · **Requests: 0 of a 0 cap.**

> **Accounting.** This pass sent **zero** HTTP requests to any Medtronic, MiniMed or
> Abbott host, so the cap is zero. Nothing was probed, nothing was authenticated, no
> credential was used or handled. The probe method space (GET / OPTIONS / POST) was
> **not** exercised — the words appear below only when describing what a *third-party
> client* does, never as a method this pass used.
>
> **Inter-request delay: none was required, because no request was made.** The
> standing floor for this project is ≥2 s of spacing between requests to the same
> host; it is vacuous at zero requests and is recorded here rather than paraphrased
> away. All findings below are derived from files in public Git repositories and from
> `gh` read-only API reads. AGENTS.md §8 probing discipline is satisfied trivially.

**A note on evidence class, because this pass creates a gap in it.** AGENTS.md §2
defines three: OBSERVED (seen in a live response), PUBLISHED (in a vendor document
served without a login), INFERRED (reasoned, not seen). A fourth kind of evidence
is in play here and none of the three fits: **a third-party client that was written
against a live API and runs in production.** It is stronger than INFERRED — someone
coded against real responses and shipped it — and weaker than OBSERVED, because we
did not see the response. The class used throughout this document is
**SOURCE-OBSERVED** (file:line + short quote in a named public repo at a named commit)
and **SOURCE-PUBLISHED** (that repo's README/PR body/commit history). Both are
weaker than a live response and are treated as corroboration, never as proof of
vendor behaviour. See §7 for the proposal to add these to AGENTS.md §2.

---

## Summary

Three independent clients were read in full. The result is a large body of
corroboration, **four contradictions with this repo's current documentation**, and
one finding that materially changes how the repo should treat open question #81.

The single most useful discovery is not a fact about Medtronic. It is the
**timestamp at which community research was upstreamed**, recorded in §6.

| Repo | Commit read | Date | Consequence for this repo |
|---|---|---|---|
| `nightscout/nightscout-connect` | `4dde1ec` | 2026-09-24 | **contradicts** `docs/05` §deviceFamily; PR #54 is dead |
| `NightscoutFoundation/xDrip` | `366c97a8` (tag `2026.10.10`) | 2026-10-10 | **corroborates** the `deviceFamily`/`medicalDeviceFamily` split |
| `CarlosJPV/carelink-cumulus-bridge` | `0180b89` | 2026-08-26 | supplies the Cumulus payload vocabulary |

---

## 1. The `deviceFamily` split — a three-way convergence

`docs/05-devices-and-vocabulary.md` records a two-hit corpus scan concluding
`deviceFamily` is *"only a localStorage patient-filter object — **not an API
field**"*. That was drawn from the **vendor's own bundles**. It is now contradicted
by three independent client implementations, which agree with each other on the
shape:

| Source | `monitor/data` field | data-payload field | Cite |
|---|---|---|---|
| `nightscout-connect` | **`deviceFamily`** | `medicalDeviceFamily` | `index.js:587` destructures `{ deviceFamily }` off the `getMonitorData()` response and routes on `deviceFamily == 'GUARDIAN'`; `:179, :194, :197` read `medicalDeviceFamily` off the data payload |
| `xDrip` | **`deviceFamily`** | `medicalDeviceFamily` | `message/MonitorData.java:5` declares `deviceFamily`; `message/RecentData.java:102` declares `medicalDeviceFamily` |
| `CarlosJPV` | `deviceFamily?: string` | `medicalDeviceFamily: string` | `src/types/carelink.ts:29-34` — both fields, in one interface |

**The finding.** Two *different* field names exist on two *different* payloads, and
all three clients agree on which goes where:

- `/patient/monitor/data` → `deviceFamily` — the **routing discriminator**, deciding
  m2m-vs-ble data leg.
- Cumulus/ble data payload → `medicalDeviceFamily` — the **reported device family**,
  values seen by these clients are `GUARDIAN`, `MINIMED`, `PARADIGM`.

**This still does not close `docs/10` #81.** Two independent reasons, both of which
must travel with the claim:

1. A destructuring default makes an absent field indistinguishable from a present
   one. `nightscout-connect` routes to the ble endpoint whenever `deviceFamily` is
   anything other than the literal `GUARDIAN` — including when it is `undefined`.
   The code is correct either way, so it does not prove the field is present.
2. **No client reports a `deviceFamily` value.** Every value observed by these three
   repos is a `medicalDeviceFamily` value. The casing of the routing field on the
   wire — the half #81 actually asked for — remains unobserved by everyone.

**Class: SOURCE-OBSERVED ×3, corroborating. Effect: `docs/05`'s "not an API field"
sentence is refuted; #81 stays open with a much narrower remaining question.**

---

## 2. The Cumulus payload vocabulary — what `/display/message` actually returns

`CarlosJPV/carelink-cumulus-bridge` is the only one of the three that implements
the API used by the MiniMed Go / Instinct sensor. Its payload handling is
source-verifiable (not just README prose).

**Structure.** `POST {baseUrlCumulus}/display/message` returns an envelope whose
data lives under **`patientData`**, not at the root
(`src/carelink/cumulus.ts:43-47`, unwrapped `:168-169`; `README.md:95`).
Independently confirmed by xDrip's DTO, which has exactly two fields —
`metadata` and `patientData` (`xDrip message/DisplayMessage.java:5-6`, unwrapped at
`CareLinkClient.java:690-694`). **Two independent confirmations.**

**Reading timestamps.** The legacy payload uses `datetime`; the Cumulus payload uses
**`timestamp`**, and carries **no timezone** — it is patient-local, with
`patientData.clientTimeZoneName` and `currentServerTime` present to reconstruct the
offset (`CarlosJPV src/carelink/cumulus.ts:53-57`, `src/server.ts:127-194`;
`README.md:96-97`). xDrip's `SensorGlucose` DTO carries **both** `datetime` and
`timestamp` with a dual-shape accessor (`xDrip message/SensorGlucose.java:17-35`).

**Ordering.** `sgs` is **not sorted** by time (`CarlosJPV src/carelink/cumulus.ts:171-176`,
`README.md:98`). Both clients sort defensively before processing
(`CarlosJPV :171-176`; `xDrip CareLinkDataProcessor.java:74-89`).

**Sentinels.** `sg: 0` is a no-reading marker (`CarlosJPV test/samples.ts:41`,
filtered at `src/server.ts:223`; xDrip filters `sg > 0` at `CareLinkDataProcessor.java:100`).
`activeInsulin.amount == -1` is a no-IOB sentinel (`CarlosJPV test/fixtures.ts:62`,
handled `src/transform/index.ts:65-67`). The second is **INFERRED** from the code and
a test name; no vendor document states it.

**Effect on `docs/10` #47 (`relativeOffset`) and #85 (timestamp semantics).** The two
open rows are about *which* timezone a timestamp is in. This pass finds that the
community has already split into **two incompatible strategies**, which means the
question is better posed as *which field wins*:

- `nightscout-connect` rewrites every timestamp's offset from the conduit's own
  `lastConduitDateTime` (`index.js:697-716`).
- `CarlosJPV` prefers `clientTimeZoneName`, and explicitly records the first strategy
  as **a bug**: `src/server.ts:165-172` — *"`lastConduitDateTime` is the last time
  the phone talked to the cloud. If the phone has been offline for hours that field
  freezes and the offset comes out skewed… real consequence: readings emitted with a
  future timestamp and xDrip+ rejecting them with 'bgreading is too far in the
  future'"*.
- xDrip shifts by a whole-hour diff computed from `lastConduitUpdateServerDateTime`
  vs `lastConduitDateTime`, bounded to <26h (`CareLinkClient.java:850-907`).

**This is a genuine, dated disagreement between three shipping clients about how to
read the same field**, and it is recorded here as a disagreement. Neither reading is
settled by this pass.

---

## 3. The `appVersion` body gate — the community finding that was upstreamed

`POST {baseUrlCumulus}/display/message` rejects old clients with
**HTTP 206 `{"message":"Upgrade application"}`**. The accepted value is a **body
field**, not a header.

The boundary, as reported by the author and corroborated independently by a xDrip
maintainer in PR #4711 (see §6):

| `appVersion` | result |
|---|---|
| `3.5.0`, `3.6`, `3.6.1`, `3.6.9` | 206 `Upgrade application` |
| `3.7`, `3.7.0`, `3.8`, `3.8.0`, `4.0.0`, `10.0.0` | 200 OK |

**Boundary: ≥ 3.7 accepted, ≤ 3.6.9 rejected.** Both `X.Y` and `X.Y.Z` parse.

**Evidence class for the boundary itself: SOURCE-PUBLISHED, author-reported.** The
boundary table is README prose and a PR comment. The repository ships the *probe
scripts* (`src/probe-appversion.ts`, `src/probe-headers.ts`) but **not their
outputs** — the result file is gitignored (`.gitignore:12`). So the *mechanism* is
source-verifiable (a body field, `src/carelink/cumulus.ts:146`) and the *boundary
values* are not independently reproducible from the tree.

**Corroborating source-verified fact:** xDrip sends `appVersion` in the body at
`CareLinkClient.java:664` (`userJson.addProperty("appVersion", "3.8.0")`), and sends
**no `os` field** — the xDrip PR author states explicitly that adding it made no
difference. This independently confirms the `os`-optional half of the finding, and
confirms it is a body field, because xDrip's is a body field too.

**Correction to our own docs.** `docs/05` and `docs/00` record the *discovery-path*
version axis (`android/3.6`–`3.8` → cumulus v13). All three clients confirm that,
and `CarlosJPV`'s `README.md:86` states the same ceiling (`3.9`+ falls back to a
legacy no-Auth0 config). **This is a second, independent axis — the body's
`appVersion` — and the two are constrained in opposite directions:** the discovery
URL must stay ≤ 3.8 while the body value has no upper bound. Our docs describe only
the first. See `docs/11` area F, added by this pass.

---

## 4. `nightscout-connect` — PR #54 is dead, `main` is still on the broken path

Read at `4dde1ec` (2026-09-24).

**PR #54** ("replace broken SSO auth with OAuth2 PKCE + MongoDB token storage",
opened 2026-03-04) is **OPEN, `mergeable: CONFLICTING`, 0 reviews, 0 comments**,
~7 months dormant. None of `auth.js`, `oauth.js`, `token-store.js` or
`commands/login.js` exist on `main`; there is no `mongodb` dependency.

**`main` still runs the legacy cookie SSO** that Medtronic broke:
`login_url: '/patient/sso/login'` (`index.js:24`), credentials POSTed directly
(`:285-287`), tokens harvested from a `tough-cookie` jar as `auth_tmp_token` /
`c_token_valid_to` (`:38-41`), with a hardcoded placeholder submitted in the
`g-recaptcha-response` field (`:292` — a static literal, value withheld).

Two further observations that bear on how a newcomer reads that repo:

- **Refresh is implemented and deliberately disabled** — `// refresh: impl.refreshSession`
  commented out at `:772-774` with the note *"have never seen refreshSession work"*.
  Yet the README claims regression coverage for refresh (`README.md:103-105`). The
  test exercises the function directly, bypassing the machine that would call it.
- **The README instructs username/password setup** (`:373-382`) — the exact path PR
  #54 declares unusable — and records no Medtronic breakage anywhere.

**Corroboration of our own record, not new:** `minimed-connect-to-nightscout#47`
("CareLink Recaptcha EU", opened 2023-09-28, still open) is the primary public record
of the SSO→CAPTCHA break that `docs/` already carries.

**Provenance note.** PR #54's body credits the OAuth2 PKCE flow to
`nightscout/carelink-bridge`, *"which already implements this successfully in
production"*. **SOURCE-PUBLISHED.** This is a third-party claim about a fork, not a
vendor fact, and is recorded as such.

---

## 5. Contradictions and corrections this pass forces

Recorded per AGENTS.md §6 — corrections stay visible.

**5.1 — `docs/05-devices-and-vocabulary.md:152` is wrong.**
*"only a localStorage patient-filter object — **not an API field**"* — refuted by
three independent clients (§1). The scan was of the vendor's own bundles and found
nothing there, which was a true statement about those bundles and a false inference
about the wire. **This is the fourth instance in this repo of a corpus scan being
read as a statement about the API.** Corrected in place with a preserved note.

**5.2 — `docs/10` §2 does not list this pass's negative.** No `deviceFamily` *value*
is reported by any of the three clients. Recorded so the row does not get closed on
the strength of §1.

**5.3 — a contradiction *inside* a source, recorded rather than smoothed.**
`CarlosJPV`'s own repository disagrees with itself on whether `os` is required:
`README.md:77-80` retracts the requirement explicitly, while `DEPLOY.md:104-105`
still states it is required and `src/probe-appversion.ts:81` still carries the stale
intent comment. **If that repository is ever cited, cite its `README.md`, not its
`DEPLOY.md`.** This is recorded because our own repo has a documented history of
derived prose contradicting its source (§6, the MG_DL case) — the failure mode is
common enough to be worth naming in a third-party source.

**5.4 — an unverified claim flagged rather than adopted.** `CarlosJPV`
`src/probe-appversion.ts:2` asserts an xDrip PR (#4711) sends `appVersion` in the
body. **This was independently verified** against xDrip `master` at
`CareLinkClient.java:664`, so the claim stands — but note it was verified *after*
being flagged, not assumed.

---

## 6. The finding that matters most: research was upstreamed within 34 minutes

This is the highest-value item in the pass and it is a fact about the ecosystem, not
about Medtronic.

| Time (UTC, 2026-08-25) | Event |
|---|---|
| **15:04:33** | `CarlosJPV/carelink-cumulus-bridge` repository created |
| **15:38:40** | xDrip commit `1f9c66d61` — *"fix(carelink): update appVersion to 3.8.0"* |

The xDrip commit changes **exactly** what the new repository documents: discovery
`android/3.6 → android/3.8` and body `appVersion "3.6.0" → "3.8.0"`. The
`appVersion` boundary table appears as a comment on xDrip PR #4711 by the same
author, and a xDrip maintainer approved it.

**Inference, stated as such:** the claim *"xDrip+ has not implemented it"* was true
at the moment of writing and stopped being true within the hour. **The community
research was upstreamed.** Class: SOURCE-OBSERVED (two commit timestamps +
a diff whose content matches the README) → INFERRED (that this was the causal route).

**Why it belongs in this repo.** It is direct evidence for the proposition that
independent reverse-engineering of one undocumented API converges, and that the
convergence is fastest when one person does the experiment and publishes the method.
It is also the clearest available argument that the **method** — the committed probe
scripts in `src/probe-appversion.ts` / `src/probe-headers.ts` — is the durable
artefact, more than any single result.

---

## 7. Proposal: two more evidence classes

`AGENTS.md` §2 lists three. This pass needed a fourth and used two more. Proposed
additions, for a maintainer decision rather than actioned here:

- **SOURCE-OBSERVED** — read at file:line in a named public repo at a named commit.
- **SOURCE-PUBLISHED** — that repo's README, PR body, or commit history.

Both are **corroboration, never proof of vendor behaviour**, and must never be
promoted to OBSERVED. Rationale: without them this pass's evidence has no honest
label, and unlabelled evidence is how it silently becomes OBSERVED — which is the
one failure this repo exists to prevent (AGENTS.md §1, §6 item 1).

**Not actioned in this pass** because it changes the repo's stated rules, which is a
maintainer's call. Left in `docs/11` as area P.

---

## 8. What this pass did **not** establish

- **Any vendor behaviour.** Nothing was probed. Every statement about Medtronic's
  servers here is third-party-reported and is labelled as such.
- **`deviceFamily`'s wire casing** — the actual #81 question. Still token-gated.
- **The `appVersion` boundary values** from source — author-reported only.
- **Any US-region behaviour** in the Cumulus path. `CarlosJPV` states his testing
  was EU-only; xDrip's discovery URL is EU-hardcoded for all regions
  (`CareLinkAuthenticator.java:78`).
- **Whether `UseSSOConfiguration` replaced `Auth0SSOConfiguration`**, or when. The
  two-key indirection is visible (`CarlosJPV src/login.ts:94`) with no dates
  anywhere in any of the three repos.
- **The `lastAlarm` shape.** `CarlosJPV` declares an alarm object
  (`types/carelink.ts:20-27`) and **never reads it**; no sample value exists in the
  repo. Field names may be inferred, not observed. `docs/10` #84 is **not** moved by
  this pass.
- **The `metadata` envelope's values.** Declared, never read, never sampled.

---

## Reproducing this pass

All four artefacts are public and were read at the commits named above:

```bash
git clone --depth 1 https://github.com/CarlosJPV/carelink-cumulus-bridge.git
git clone --depth 1 --filter=blob:none --sparse https://github.com/NightscoutFoundation/xDrip.git
cd xDrip && git sparse-checkout set app/src/main/java/com/eveningoutpost/dexdrip/cgm/carelinkfollow
git clone --depth 1 https://github.com/nightscout/nightscout-connect.git
gh pr view 54 --repo nightscout/nightscout-connect        # state: OPEN, mergeable: CONFLICTING
gh pr view 4711 --repo NightscoutFoundation/xDrip          # the appVersion discussion
```

No credentials, tokens or personal data were read, handled, or recorded at any point
in this pass. The only literal resembling a secret encountered — a hardcoded
placeholder in a reCAPTCHA field — is described by location only and its value is
withheld.