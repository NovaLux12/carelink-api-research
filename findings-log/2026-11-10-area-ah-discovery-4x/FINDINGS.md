# Area AH — do the `android/{4.0,4.1,4.2,5.0}` discovery cells still serve cumulus v2?

**Pass of 2026-11-10.** Claim [NovaLux12/carelink-api-research#180](https://github.com/NovaLux12/carelink-api-research/issues/180).
Branch `research/ah-discovery-4x`. Hosts swept: **`clcloud.minimed.com` and
`clcloud-trials.minimed.com` only** — the two hosts the claim names, and no other host was touched.

**16 of a 20 cap**, GET only, `sleep 2.5` inside the per-host `flock`, ≥ 2.5 s between
requests to the same host, controls first on every host. 4 requests held back and unspent.

---

## 0. The result is the inverse of the question, and the control is what establishes it

The area was posed as *"do the 4.x cells still serve cumulus v2?"*. They do return a
cumulus-v2 document — **and so does every other string I sent that the server does not
recognise.** The certainly-absent control settles it:

| what was sent | tail echoed back | tail-erased digest, `.com` | tail-erased digest, `-trials` |
|---|---|---|---|
| `zz-absent-8713` **(control, certainly absent)** | `android,zz-absent-8713` | `7ac09335c7e4…` | `9962b3db79b1…` |
| `99.99` **(control, above every string this axis has served)** | `android,99.99` | `7ac09335c7e4…` | `9962b3db79b1…` |
| `4.0` | `android,4.0` | `7ac09335c7e4…` | `9962b3db79b1…` |
| `4.1` | `android,4.1` | `7ac09335c7e4…` | `9962b3db79b1…` |
| `4.2` | `android,4.2` | `7ac09335c7e4…` | `9962b3db79b1…` |
| `5.0` | `android,5.0` | `7ac09335c7e4…` | `9962b3db79b1…` |

**OBSERVED, and not merely equal digests: after replacing the echoed tail with a fixed
marker, all six bodies on each host are `cmp`-identical — 18 104 B on `.com`, 16 368 B on
`-trials`, zero byte delta** (measured in this session over the transient bodies; the
bodies themselves are not committed, `AGENTS.md` §7).

So:

- **`baseUrlCumulus: /connect/carepartner/v2` is the DEFAULT document, not a version
  selection.** Any tail the server does not key on resolves to it.
- **The keyed tails are the exceptions, and only two were keyed in this sweep.**
- Therefore *"the 4.x cells return cumulus v2"* is true but carries **no information
  about 4.x**. It is the same sentence as *"4.x is not in the table"*.

This is a **re-derivation of a fact this repository already had and did not draw out.**
Area AA's own table records `absent-probe-871` → *"same document as `3.9`"*
[source: findings-log/2026-10-17-area-aa-appversion-axis/FINDINGS.md §4.2], and area AE's
erased digests `7ac09335c7e4` / `9962b3db79b1` are the same two values this pass got from a
fabricated tail [source: findings-log/2026-11-10-area-ae-appversion-tail/results.jsonl
seq 3, 5, 8, 12 — `erased_config_sha256`]. **Two prior passes held both halves and neither
stated the rule.** That is the finding, and it is one source: this repository
(`AGENTS.md` §2.1 — no strength word used anywhere in this document).

---

## 1. Accounting

| item | value |
|---|---|
| Requests | **16 of a 20 cap** (4 unspent) — derivation below |
| Method | `GET` only. No POST, no OPTIONS, no token, no cookie, no auth header, no wordlist |
| Delay | `sleep 2.5` **inside** the per-host `flock`, before the send; **≥ 2.5 s between requests to the same host** |
| Spacing, ledger clock | `.com` floor **2.399 s** over 6 gaps (1 under 2.5 s, **0 under 2.0 s**); `-trials` floor **2.985 s** over 6 gaps (0 under 2.5 s) |
| Spacing, kernel body-mtime oracle | `.com` floor **2.962 s**, `-trials` floor **2.986 s**, **0 gaps under 2.5 s** on either host |
| Failures | **0** — no 000, no 5xx, no timeout, `curl_exit: 0` on all 16 rows |
| Retries | 0 |

**Cap derivation (one assignment, `CAP=20` in `probe.sh`):** 2 hosts × 2 controls = 4,
+ 2 hosts × 4 claim tails = 8 (**12**), + 2 hosts × tail `3.4` for the `docs/03:164`
addendum = 2 (**14**), + 2 hosts × tail `99.99` for the fallback confirmation = 2
(**16**), + 4 held back against the failure class. **The cap was never revised.** The two
addenda were recorded in `probe.sh` with their reason *before* the requests were sent.

⚠ **Disclosed, not smoothed over:** the `t_sent` series records **two negative request
durations** (seq 4: −0.320 s, seq 5: −0.145 s) on `.com`. That is impossible for a
faithful monotonic clock and **no cause is asserted** — this is the known corrupt-`t0`
class recorded in `docs/09` §4 and in the AB and AE rows. The kernel body-mtime oracle,
which is measured from a different clock than the harness and valid only on the machine that ran the
probe, reads **0 gaps under 2.5 s on either host**, so no gap in this pass was actually
short. The one sub-2.5 s ledger gap (2.399 s) sits immediately after the two negative
durations on the same clock.

---

## 2. The keyed tails — the positive half (OBSERVED)

| tail | `n_cp` | `CP[]` regions | `baseUrlCumulus` (verbatim) | `baseUrlCareLink` (verbatim) | `baseUrlPde` (verbatim) | countries |
|---|---|---|---|---|---|---|
| `3.4` | **3** | `US, EU, CLINICAL` | `https://clcloud.minimed.com/connect/carepartner/v11` · `https://clcloud.minimed.eu/connect/carepartner/v11` · `https://clcloud-trials.minimed.com/connect/carepartner/v11` | `…/carelink.minimed.com/api/carepartner/v2` · `…/carelink.minimed.eu/api/carepartner/v2` · `…/carelink-trials.minimed.com/api/carepartner/v2` | `…/clcloud.minimed.com/connect/pde/v2` · `…/clcloud.minimed.eu/connect/pde/v2` · `…/clcloud-trials.minimed.com/connect/pde/v2` | **109** |
| `3.6` | **3** | `US, EU, CLINICAL` | `https://clcloud.minimed.com/connect/carepartner/v13` · `https://clcloud.minimed.eu/connect/carepartner/v13` · `https://clcloud-trials.minimed.com/connect/carepartner/v13` | `…/api/carepartner/v2` ×3 | `…/connect/pde/v3` ×3 | **109** |
| `4.0`,`4.1`,`4.2`,`5.0`,`zz-absent-8713`,`99.99` | **2** | `US, EU` — **no CLINICAL** | `https://clcloud.minimed.com/connect/carepartner/v2` · `https://clcloud.minimed.eu/connect/carepartner/v2` (`.com`) / `https://clcloud-trials.minimed.com/connect/carepartner/v2` ×2 (`-trials`) | `…/api/carepartner/v1` | `…/connect/pde/v1` | **99** (`.com`) / **76** (`-trials`) |

`3.4` and `3.6` are **byte-identical across both hosts** (erased digest `7ad212402d7f…` for
`3.6` on both; `4a80524eb334…` for `3.4` on both). The fallback document is **not**: 99
countries and an EU SSO entry on `.com`, 76 and a US-only entry on `-trials`.

`3.6` re-derives area AE's `7ad212402d7f…` exactly — the same one source, not a second one.

**`3.4` is not a v2 cell.** `docs/03` §3's table row reads *"3.9 – 12.0 (and ≤ 3.4) | no |
v2 | no | legacy doc"* [source: docs/03-discovery-and-versions.md:156]. Measured: `3.4`
answers cumulus **v11**, `n_cp` **3**, with a **CLINICAL** region, 109 countries, and
`baseUrlPde` **v2** — not the fallback document. `PROBE-FINDINGS §3` agreed with the
measurement (`3.3, 3.4 → v11, 3 regions`) [source:
findings-log/probe-2026-10-08/PROBE-FINDINGS.md:63], so `docs/03`'s row contradicts its own
source. Corrected in `docs/03` by this PR; the raw logs are untouched (append-only).

---

## 3. `Auth0SSOConfiguration` — the key is NOT on every version 3.4 → 5.0

Key presence was read as a key-membership test on each `CP[]` entry, not a string search of
the body. Verbatim `CP[]` key sets:

- **`3.6`** (both hosts): `SSOConfiguration`, `baseUrlAem`, `baseUrlCareLink`,
  `baseUrlCumulus`, `baseUrlPde`, `region`, **plus `Auth0SSOConfiguration` and
  `UseSSOConfiguration`**.
- **`3.4`, `4.0`, `4.1`, `4.2`, `5.0`, `zz-absent-8713`, `99.99`** (both hosts):
  `SSOConfiguration`, `baseUrlAem`, `baseUrlCareLink`, `baseUrlCumulus`, `baseUrlPde`,
  `region` — **and nothing else. No `Auth0SSOConfiguration`. No `UseSSOConfiguration`.**

So the answer to the claim's Auth0 question is **NO for all eight 4.x cells and NO for the
two 3.4 cells**.

**This refutes a load-bearing sentence in `docs/03`.** `docs/03:164-169` states the
`Auth0SSOConfiguration` key *"now exists on every version 3.4 → 5.0, including the
cumulus-v2 no-Auth0 cells, even where `UseSSOConfiguration` is absent"*, and builds a code
finding on it — that `selectAuth0ConfigUrl()`'s `?? 'Auth0SSOConfiguration'` fallback makes
the ADR 0002 pin guard **inert**, so bumping `DISCOVERY_APP_VERSION` to `android/4.0` would
*"fail later at the data call, with no named error"*.
**The key is absent on 5 of the 6
distinct version tails this pass measured — `3.4`, `4.0`, `4.1`, `4.2`, `5.0` — and present
only on `3.6`. So the `??` fallback has nothing to fall back to on those five, and the
mechanism the paragraph describes cannot run there.**

⚠ **Scope, stated exactly:** this pass measured `3.4`, `3.6` and the 4.x family. It did
**not** measure `3.5`, `3.7`, `3.8`, `3.9`, `3.10`, so **the claim is not refuted for those
tails and nothing is claimed about them here.** What is refuted is the *universal*
("every version 3.4 → 5.0") form. The ADR-guard-liveness question is handed to the
successor rather than answered: whether the guard is inert depends on which cells the
bridge could actually be pointed at, and that is now an open, bounded question.

`docs/03` is corrected with a dated blockquote by this PR; the finding is superseded, not
deleted, and `findings-log/` is not edited.

---

## 4. Withdrawal — the spike's Instinct inference, withdrawn by this pass

`findings-log/cumulus-v2-spike.md:13-17` reads:

> "Discovery cells `android/{4.0,4.1,4.2,5.0}` return cumulus **v2** + CareLink API v1 +
> PDE v1 configs with NO Auth0 and no CLINICAL region. … [INFERENCE] The cumulus-v2 shape
> may be the transport the Instinct-era "Cumulus" API rides on."

**Two of those sentences are still exactly right as observations** — the 4.x cells do return
that document, in those exact values (§2). **The INFERENCE is withdrawn, and the withdrawal
is mine and dated 2026-11-10, not a correction to the spike file.** `findings-log/` is
append-only under `AGENTS.md` §3, so the spike is superseded here and left in place.

**Why it is withdrawn:** the inference takes "4.x selects v2" as evidence of a *relationship
between 4.x and the cumulus-v2 transport*. §0 shows that relationship does not exist —
a fabricated tail and `99.99` select the same document. **A property every string has is not
evidence about any string.** The observation is real; the step from it to the Instinct track
is unsupported by it.

**What this does and does not do to the Instinct hypothesis.** It removes the spike's only
*discovery-axis* support for "Instinct rides cumulus v2". It does **not** refute the
hypothesis — the xDrip discussion report that started the spike
([NightscoutFoundation/xDrip#4318](https://github.com/NightscoutFoundation/xDrip/discussions/4318),
one source, third-party, not re-read here) is untouched by this measurement. The hypothesis
now rests on that report alone, which is where it should have been recorded.

**Also superseded, same reason:** the 2026-08-05 re-probe's conclusion *"`android/4.1` →
**legacy track** … Confirms 4.x is a distinct legacy product track (no Auth0) all the way up
to 4.1"* [source: findings-log/medtronic-carelink-2026-07-21/01-endpoint-matrix.md:92].
"Is a distinct track" is not supported: **4.x is indistinguishable from a tail the server
does not know.** Whether Medtronic has a 4.x product track is **not measured by this axis**
and this pass does not answer it.

**Not tested here:** the spike's *"no shipped store app is ≥4.x"* clause. That is a claim
about app stores, this pass touched no store, and nothing in this ledger speaks to it.

---

## 5. Verdict

**Does the spike's 4.x reading still hold?** **The observation holds; the reading does not.**

- **Holds (OBSERVED):** all four tails `4.0`, `4.1`, `4.2`, `5.0` answer `200` on both hosts,
  with `baseUrlCumulus` `/connect/carepartner/v2`, `baseUrlCareLink` `/api/carepartner/v1`,
  `baseUrlPde` `/connect/pde/v1`, `CP[]` length **2** (`US, EU`, **no CLINICAL**), 99
  countries on `.com` / 76 on `-trials`, and **no `Auth0SSOConfiguration` key**. Eight of
  eight cells reproduced the spike's field values verbatim.
- **Does not hold (OBSERVED):** the claim that these cells *show* 4.x on the cumulus-v2
  track / that 4.x is a "legacy product track". They show only that **4.x is not a keyed
  tail**, which a fabricated string also shows.
- **Refuted (OBSERVED):** `docs/03:164`'s "Auth0SSOConfiguration key on every version
  3.4 → 5.0", at the five of six measured tails where it is absent, and `docs/03:156`'s
  grouping of `3.4` with the v2 legacy cells.

---

## 6. Counting rule

Stated before the numbers, so they can be reproduced and so none is read as a
generalisation:

- **One "cell" = one `GET`** of `/connect/carepartner/v13/discover/android/<tail>` on one
  host. 16 cells measured = 8 tails × 2 hosts. Nothing is counted twice: no retries.
- **"Fallback class"** = a tail whose body, with the echoed tail replaced by a fixed marker,
  is byte-identical to that of the `zz-absent-8713` control **on the same host**. 6 tails on
  `.com` and 6 on `-trials` fall in it (`4.0`, `4.1`, `4.2`, `5.0`, `zz-absent-8713`,
  `99.99`). Comparability is **within** a host: the fallback document differs across hosts
  (99 vs 76 countries), so a cross-host digest match would be a different claim.
- **"Keyed"** = a tail not in the fallback class. **2 tails** qualified: `3.4`, `3.6`.
- **Key presence** is a membership test on each `CP[]` entry's key set, not a substring
  search of the body — a substring test would be defeated by the key appearing in the
  `SSOConfiguration` filename.

---

## 7. Files

- `probe.sh` — CAP as a single assignment, `cap_guard` reading the ledger, one JSON line per
  request, host locks under `$REPO/.loop/host-<key>.lock`, `sleep 2.5` inside the lock.
- `results.jsonl` — 16 rows, one per request.
- `run.log` — the same events plus the spacing derivation.
- `spacing.txt` — the per-host gap series from both clocks.

## 8. Successor

Minted as **area AM** in `docs/11` — which cells the ADR 0002 guard is actually inert on,
now that the `Auth0SSOConfiguration` key is known to be absent on the 4.x family and on `3.4`.
**Blocker:** a request budget, not a token. **INFERRED** labels where they belong, including
that the guard's inertness is a property of the *cell*, not of the *version range*.
