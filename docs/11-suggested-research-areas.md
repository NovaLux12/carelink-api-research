# Suggested research areas

> **Navigation** — the map: [`00-summary-the-map.md`](00-summary-the-map.md) · related: [`10-open-questions.md`](10-open-questions.md)

**Pick something up.** Every area below states what is known, what is missing, and
what would close it. Nothing here is a guess dressed up as a task — each one has a
specific blocker.

Priority is roughly: **cheapest-and-highest-value first**. Token-gated items are
grouped at the end because they need something we don't have.

---

## Already blocked on a token — don't start here

These need an authenticated response on a real account. If you have one, tell us;
everything else on this page moves.

| Area | Blocker |
|---|---|
| `deviceFamily` wire shape | one logged `monitor/data` response |
| NGP alarm-code vocabulary | an authenticated `application` config |
| `relativeOffset` clock semantics | any real payload |
| Report bodies from `commoncore` | a clinician-scoped token |
| Does a `200` carry `Access-Control-Allow-Origin`? | one authenticated cross-origin request. Every browser-visible response on `clcloud.*` today is an error (401/403) and **none carry CORS**, so callability from a browser is unproven in both directions (see [`10-open-questions.md`](10-open-questions.md) §1) |

#### Addendum (2026-10-13, from the `commoncore-trials` pass): the `commoncore` 403s are the gateway's *no-route* error, so "six endpoints on `commoncore.medtronic.{eu,com}`" is unproven

Attached to the `Report bodies from commoncore` row above, which is the claim this
actually refines. The `commoncore-trials` pass closed the `docs/10` §1 row **"is
`commoncore-trials.medtronic.com` a real host?"**; closing it produced this.

**What is known (labels and cites).** `commoncore-trials.medtronic.com` **is** a
real host: CNAME to a CloudFront distribution, a host-specific DigiCert leaf whose
SAN matches the name, a gateway-shaped `403` — three signals a parked name cannot
produce (OBSERVED, [findings-log/2026-10-13-commoncore-trials/FINDINGS.md]
§2a). The trials deployment's **config** points `nutrino.cc.broker.service.config.host`
at the **`.minimed.com`** sibling while its **CSP** allows the **`.medtronic.com`**
one, so two vendor documents name two different trials hosts (OBSERVED, same log
§3b; config value at
[findings-log/2026-10-12-published-pointers/enumeration-scrubbed.txt:217]).

**What was NOT established, and why it matters.** These hosts are AWS API Gateway
behind CloudFront, where `MissingAuthenticationTokenException` **is the
unmatched-route error** and a fabricated path returns the published response
byte-for-byte ([docs/09-methodology-and-oracles.md](09-methodology-and-oracles.md)
Oracle A — whose "**`404` is never emitted**" clause is **INFERRED by analogy from
`clcloud.*`**, that page scoping it to `clcloud.*` plus the five `execute-api`
gateways; `AWS-GATEWAYS.md` names no `commoncore` host, and this pass observed **no
`404` in either direction**).
The `commoncore-trials` pass confirmed the control directly:
`/reports-broker/v1/ocl` and `/reports-broker/v1/ocl-probe-absent` returned the
**same status, error type and body digest** (`f249b63c…`, 42 B) — six GETs,
**one** distinct body (OBSERVED, same log §2b, §5). **So `docs/07`'s "all **403**"
on the six `commoncore.medtronic.{eu,com}` endpoints is a statement about the
gateway, not evidence that six endpoints are served.** The six paths are still the
vendor's own config values; the *status* is what was being over-read. This matters
because the row above assumes a reports surface exists to authenticate against —
and on this host family that assumption is currently **unproven in both directions**.

**Adjudicated on `.com` only.** The absent-path control was run on
`commoncore.medtronic.com` (seq 4 vs 5) and **not** on `commoncore.medtronic.eu`, so
the `.{eu,com}` brace is **not** one adjudicated pair and the EU cell is
corroboration. The EU control **did** fit the budget — what spent the slot was the
pass's own unspent re-issue reserve (same log §5, §9), not the cap.

**Blocker:** a clinician-scoped token, **and** a path whose `403` means something
other than "no route". The second half is the real obstacle: it needs either a
`401`/`400`/`405` cell (the [carelink plane](00-summary-the-map.md) supplies those,
`commoncore` does not) or one authenticated request. **This is a token question, not
a request-budget question** — the `commoncore-trials` pass spent **9 of a 10 cap**
and closed the *host-existence* half plus the no-route control; it did **not** close
the route question or the EU cell, and both remain open.

**Closes when:** one authenticated `GET /reports-broker/v1/ocl` on any `commoncore`
host returns a status that is **not** `MissingAuthenticationTokenException` — which
would establish that the route exists and the family is reachable. **A negative
counts, and on the current evidence it is the likely answer**: if the authenticated
request also answers `403 MissingAuthenticationTokenException`, the six endpoints
should be **retired from `docs/07`'s prose as unserved**, which is a real result.

**Assumptions (INFERRED):** that the CloudFront distribution and its certificate
are Medtronic-operated rather than third-party-hosted — the issuer and SAN are
OBSERVED, the ownership is inferred from the vendor naming the host in its own CSP;
and that the config/CSP split on the trials deployment is deliberate rather than a
stale config entry, which **nothing observed here distinguishes**. The EU cell in
the `commoncore-trials` pass carries **no absent-path control**, so it
is corroboration rather than an adjudicated reading.

**⚠ An open question this pass raised and could not close.** Its six `403`s all
carry **`access-control-allow-origin: *`** on bare `GET`s with **no `Origin` sent**.
That bears directly on the closed area X row above and on the "CORS is emitted only
on `OPTIONS`" reading — these are exactly the discriminating cells, and they cut
against it. It is **not** corrected here: correcting a closed area is a disclosure
decision. Carried by [issue #61](https://github.com/NovaLux12/carelink-api-research/issues/61)
and recorded in the pass log
[§12](https://github.com/NovaLux12/carelink-api-research/blob/main/findings-log/2026-10-13-commoncore-trials/FINDINGS.md).

---

#### Addendum (2026-10-12, from area O): 24 more non-2xx responses, still zero `200`s

Attached to the `Access-Control-Allow-Origin` row above, as area O's claim issue
specified — it is the same question one gate further in, and this pass moved it
without a token.

**What was added.** Area O probed `/patient/reports/*` on all three
`carelink.minimed.*` patient hosts. **All 24 responses carried no
`access-control-allow-origin`** — not the 6 `401`s, not the 3 `400`s, not the
nine `405`s, not the 6 `404`s (OBSERVED,
[findings-log/2026-10-12-area-o-reports-namespace/FINDINGS.md] §6d). That is
**corroboration, not continuation**: area X's "0 non-2xx responses carrying CORS
anywhere" was measured on `clcloud.*`, and this is a different host family with
a different origin stack (`Apache/2.4.62` behind CloudFront, not AWS API
Gateway).

**Why it does not discharge the row.** The row asks about a **`200`**, and this
pass produced **no `200` at all** — every cell in the namespace is a 4xx. So the
token-gated half is now *more* precisely bounded than before: for
`/patient/reports/*` on `carelink.*`, the CORS question cannot be answered from
the outside at all, on any host, by any amount of further unauthenticated
probing.

**Blocker (unchanged, restated from what this pass established):** the remaining
unknown is what a successful response carries, which needs an authenticated
cross-origin request against a route that is known to exist. Area O establishes
*which routes exist* — 6 of the 7 on each of 3 hosts — so the token-gated half
of this row now has a precise target list instead of a vague one.

**Closes when:** one authenticated cross-origin request to any of the six live
`/patient/reports/*` paths on any of the three hosts shows a `200`'s CORS
headers, **or** the row is retired as unanswerable and the unauthenticated
negative is promoted to the standing position. **A negative closes it** — and
this pass is evidence that the negative is the likely answer, so this row should
be expected to close by downgrade rather than by discovery.

**Assumptions (INFERRED):** that `connect-src`/`frame-src` in the CSP the same
responses carry implies the browser client *needs* cross-origin access to the
report hosts. The CSP is host-aware and names the vendor's own data-plane hosts
per region (§6c of the pass log), which is suggestive, but no response observed
here demonstrates an actual cross-origin call.

---

## Tier 1 — no token needed, high value

### AD. Can the committed `cluster.idx` locate converge — and what does the `minimed.eu` family interval actually contain?

**What is known, all OBSERVED, and it is one run.** The S-L1 instrument is
committed at `findings-log/2026-10-18-sl1-cluster-servedness/servedness.py` and
answers **served/unserved** for any named crawl in one ranged read. It has
classified correctly on every crawl it was pointed at: `CC-MAIN-2022-27` and
`CC-MAIN-2024-42` both **SERVED**, the absent id `CC-MAIN-9999-99` **`404
NoSuchKey`**, `CC-MAIN-2014-23` **SERVED** at **153 902 243 B**, and its CDX
`404` now sits behind a **`200`** control on that same crawl
([findings-log/2026-10-18-sl1-cluster-servedness/FINDINGS.md §5–§6]). Its
**locate** half — the banded bisection for the family interval
`[eu,minimed)`, `eu,minimeda)` — has **never once returned a verdict on live
data**: both controls came back **`UNCONVERGED`** at a 3-page budget, and the
control gate correctly withheld every family claim as a result. The only
evidence the locate machinery works at all is `selftest`, on a synthetic
keyspace, at **0 requests**.

**What is missing, and it is specific.** Nothing has ever read a `cluster.idx`
block key for `minimed.eu`. Area M named this as `offsetB` and recorded it as
**prepared and not sent** — the cap arrived first, after a verifier round
corrected the stronger reading that it was mechanically blocked
(`findings-log/2026-10-13-area-m-commoncrawl-cdx/FINDINGS.md:498-521`). So the
question *"does this crawl's index carry the `minimed.eu` family **at all**"* is
untouched, and it is **not** answerable from the CDX API: a `404` there cannot
separate *the crawler never requested a `minimed.eu` URL* from *it requested one
and the origin answered `404`* — which is exactly the ambiguity AC is chasing on
the other side of the window.

**Closes when** the locate returns a real verdict — `FAMILY_PRESENT` or
`FAMILY_ABSENT` — for **both** controls, at a budget that is declared and
measured rather than guessed, and then for `CC-MAIN-2014-23`. **A negative
counts and is the likely answer**: if `CC-MAIN-2014-23`'s index carries no
`minimed.eu` block key, that is a statement about the crawl's keyspace rather
than about one URL, and it is stronger than any CDX `404`. **`UNCONVERGED`
does not close this area** — it is what it already returned.

**Budget, and the blocker on it, both named.** The **fix is a seed, and the seed
is free**: the `cluster.idx` head read this instrument already performs returns
`Content-Range` (the file's exact total length) **and** 8 KiB of the file's first
keys. The 2026-10-19 run had both and **used neither** to seed the bisection,
which opened at a fixed `f0 = 0.85` of file size and landed deep in
`org,…`/`pl,…`. So the first step is **zero-request**: derive the initial
fraction and the page schedule from the head read already in hand, plus the
observed key distribution, and re-`selftest` it against a synthetic keyspace
large enough that a single page cannot span it. Only then does a live run need
the network: **budget it at ≥ 10 pages per crawl** — the observed window after
3 pages of 4 MiB was still **18.9%** of the file — and bill it with the same
`spacing.py` accounting. **Blocker: none** — a read of a published index, not a
vendor surface. **What does not block it is the cap**: the 2026-10-19 pass spent
6 of 15 rows on two control locates that could not converge at 3 pages each,
which was its own page-schedule choice rather than a constraint
(same log, §9).

**And the zero-request half, which can start today.** Every crawl this
repository already publishes a **classified negative** for — area M's six, area
L's 84 in-window cells, S-L2's 44 out-of-window cells — has a served/unserved
verdict obtainable in **one ranged read each**, and `classify` derives the whole
table from a committed ledger without touching the network. Applying it to those
published negatives is **zero-request once the instrument exists**, and it is the
cheap half of this area: it would tell us, for every negative this repository
publishes, whether the crawl's index was served at all — the pairing S-L1's
close condition asked for and this pass could supply for only the one crawl it
named.

**Assumptions (INFERRED):** that `cluster.idx` blocks are keyed by the full
first SURT key rather than by registrable domain (area M's standing assumption,
still labelled INFERRED and never promoted to OBSERVED); that the keyspace's
first keys are informative about where `eu,` sorts (untested — it is the thing
this area would test); and that a served `cluster.idx` implies the crawl's CDX
API is reachable (observed on one crawl, `CC-MAIN-2014-23`, and **not**
established in either direction for the rest).



### AC. After the window: what does Common Crawl hold for `minimed.eu` from 2022-06 onward, and is `/ipro/hcp/` retired or merely uncrawled?

The out-of-window census is **complete** — **0 of 44 unread**, every cell
classified under the counting rule (a `404` reads as an absence only behind a `200`
on that same crawl; a `502`/`504`/`503`/`400` is a failure and is re-issued, never
an absence) — and it returned **165 records over 27 distinct host-relative paths
and six hosts** in its 40 record cells. **Five of the 44 carry a `/ipro/hcp/`
member**, the last dated **2026-06-10**, archived **`404`**
[source: findings-log/2026-10-17-sl2-outwindow-census/FINDINGS.md §F2, §F5, §F10].

**What is known, and what is missing.** Every status in those cells is the
**archived** status of a capture — the answer the origin gave when a crawler
fetched that URL — so a `404` is consistent with retirement, a gate, and path
rewriting, and **nothing observed separates the three**. The census also produced
a pattern nobody has looked at: **`javascript-warning.html` appears in 29 of the
40 record cells**, in **five** distinct shapes, four of them nested under `/app/` at
up to `/app/assets/assets/assets/assets/javascript-warning.html`. Area L saw five
such captures on one crawl in 2026-10 and explicitly declined to interpret them.

**Closes when** the post-2022 `minimed.eu` record set is **enumerated rather than
sampled** — every path and status across the 41 out-of-window crawls from 2022-06,
under a stated completeness rule, with the nested-asset shapes either explained or
recorded as unexplained. **A negative counts**, and a negative is the likely answer:
if the nested shapes turn out to be a crawler artefact rather than a served path
structure, that is the finding. **Budget:** derivable from
`findings-log/2026-10-17-sl2-outwindow-census/budget.py` — **2.59 requests per
crawl measured**, 2.51 derived, so ~106 rows for the 41 post-window crawls — and
the crawl list must again be derived from `GET /collinfo.json`.

**Blocker:** none — a read of a published index, not a vendor surface. The real
blocker on the *interpretation* is `AGENTS.md` §7: the record bodies are outside
the tree, so **"did `carelink.minimed.eu` serve a catch-all on those nested asset
paths" cannot be settled from a Common Crawl ledger at all** — the 404s and 200s
here are indistinguishable from a SPA fallback without one bounded live probe on
the named path. **That live probe is the sharp question this area exists for**, and
it is cheap and GET-only.

**Assumptions (INFERRED):** that the 165 records enumerate what the crawler
requested rather than what exists (the API is queried by URL, so it answers about
requested paths only); that `carelink.minimed.eu` and `carelink.minimed.com` behave
alike on these asset paths (untested — the census never queried `.com`); and that
the archived status is a faithful record of the origin's answer (it is a third
party's record of a third party's fetch, and this repository has not
independently checked one).


> **Area AA is CLOSED** (2026-10-17, claim #151) — see the Closed table at the foot of
> this page and
> [findings-log/2026-10-17-area-aa-appversion-axis/FINDINGS.md]. **The area's framing
> was the wrong pair of terms, and saying so is the finding.** It asked whether the
> app-version axis is a **content gate** or an **echo**. It is **both at once**, and the
> status line alone would have returned "echo": a fabricated tail
> (`android/absent-probe-871`) answers **`200`** on both hosts, so nothing is rejected
> and nothing looks selective. The discriminator is in the bodies — erase the echoed
> `config` value and re-digest.
>
> **Per `(host, base)`, OBSERVED, 20 of 20 requests, GET only, measured same-host
> spacing floor 3.304 s:**
>
> | base | `.com` | `-trials` |
> |---|---|---|
> | `v13` | **gating** — 4 tails → **3** documents | **gating** — 4 tails → **3** documents |
> | `v6` | **no verdict** — base unrouted (`403`, no-route digest) | **not gating** — 4 tails → **1** document (n=4) |
> | `v11` | **no verdict** — one tail sent (a control) | **no verdict** — one tail sent (a control) |
>
> - **No allow-list, on either host.** All 14 `200` bodies echo the requested tail
>   exactly once into `"config"`, and a fabricated tail was served verbatim at three
>   cells. The segment is **never validated**.
> - **At `v13` the tail selects substantively**: `3.6` → `3.9` moves the advertised
>   `baseUrlCumulus` base (`v13`→`v2`), `baseUrlCareLink` (`v2`→`v1`), `CP[]` length
>   (3→2), country count (109→99 on `.com`, 109→76 on `-trials`) and the SSO config
>   file family: `oauth20_sso_carepartner_*_v6.json` on the 3.5/3.6 class, against
>   `sso_cp_us_v6.json` on `-trials` and both `sso_cp_us_v6.json` +
>   `eu_sso_cp_eu_v6.json` on `.com` for the 3.9 class. The `3.5` and
>   `3.6` documents are byte-identical **across** both hosts; the `3.9`-class document
>   is **not** — which corrects `docs/00`'s "every cell from 3.9 upward is
>   byte-identical" to *within a host*.
> - **At `-trials` `v6` the tail gates nothing** — four tails including a fabricated
>   one collapse to one document. Strongest single result in the pass, and it
>   **re-derives** the digest the 2026-10-17 matrix pass recorded there.
> - **The `v6` `403` split reads as a base-axis effect, not an app-version effect
>   (INFERRED; the refutations are OBSERVED)**, and the rows support that much: same
>   host, same tail `3.6`, base `v11` → `200`. Whether
>   `v6` is unrouted on `.com` because of the version segment or the route family is
>   **not** established and **no choice is made** between those readings.
> - **Deviation, disclosed:** claim #151 named `carelink.minimed.com` /
>   `carelink-trials.minimed.com`; the pass sent `clcloud.minimed.com` /
>   `clcloud-trials.minimed.com`, because that is the host family the route is
>   published on (`baseUrlCumulus`). **The claim's host list was wrong.** It answers
>   the area as posed — `.com`/`-trials` are the deployment designations — and does
>   **not** speak to the `carelink.*` hosts, which were not swept.
> - **Premise checked, not assumed:** the prior closed row recording "the bare
>   `connect/carepartner/` prefixes dead on both methods" probed the *prefix parents*
>   (`…/carepartner/`, `…/carepartner/v13`, `…/carepartner/v13/discover`). These cells
>   are a routed leaf four segments below. **Distinct claims, no contradiction.**
> - **No pin added**, as the area directed: a 4-cell pin in `05-public-config` costs 4
>   requests on **every PR gate** *and* 4 per weekly sweep — affordable against the
>   ~80-request sweep budget in `AGENTS.md` §11, and declined for a different reason: it
>   would not catch the change that matters. **Measure**; counting rule in the log §7.
> - **One source.** One lane, one ledger, one author — no strength word is used for
>   any of the above, including the cross-host byte-identity (`AGENTS.md` §2.1).
>
> **Carried forward as area AE**, which is the one question these cells could not
> answer.

### AE. Is the `android/<app-version>` tail a lookup table, or a threshold?

**What is known, labelled and cited.** At base `v13` on **both** cumulus hosts the
app-version tail **gates content** — four tails select **three** distinct documents,
differing in advertised `baseUrlCumulus` base, `baseUrlCareLink` version, `CP[]`
length, country count and SSO config file family (OBSERVED, 20 of 20 requests,
`[findings-log/2026-10-17-area-aa-appversion-axis/FINDINGS.md §4.2]`). The tail is
**never validated** — a fabricated tail answers `200` and lands on the `3.9`-class
document (OBSERVED, same source `§4.1`). At `-trials` base `v6` the tail gates
**nothing** — four tails, one document (OBSERVED, `§4.3`).

**What is missing, and why it matters.** **Whether the rule is a per-value lookup or
a threshold is not separable from AA's tails.** AA sent `3.5`, `3.6`, `3.9` and one
fabricated value — three of them adjacent. A boundary anywhere in `(3.5, 3.6]` or
`(3.6, 3.9]` fits those cells exactly as well as a table keyed on the string. The
difference is not cosmetic: it decides whether a client can pick a **safe** tail
without enumerating them. It is also the only question AA left open that more of the
same cells could not answer.

**Blocker:** a request budget, not a token. **≤20 requests** — `clcloud.minimed.com`
first, base `v13`, tails strictly **inside** `(3.6, 3.9)`: `3.61`, `3.65`, `3.7`,
`3.75`, `3.8`, `3.85`, `3.89` = 7 cells, plus 2 controls (`v99` absent, `v11`
served) = **9**; the `-trials` host only if the first host brackets a boundary,
**≤9** more. GET only, ≥2.5 s same-host, controls first per host.

**Closes when:** the discriminating boundary is bracketed to a specific interval on
at least one host, **or** the ladder turns up a **fourth** distinct document, which
is positive evidence for a table. **A negative counts** — if no tail in `(3.6, 3.9)`
produces a document distinct from the `3.6`-class, the boundary lies outside the
swept range (or the rule is not a threshold at all), and that is the answer. Also
carry back: whether the `3.9`-class document's **host** difference (99 countries and
an EU SSO entry on `.com` against US-only 76 on `-trials`) is a country-list
consequence or a separate axis — no prior row varies the country axis.

**Non-duplicate:** intermediate tails **do** exist in the record — `docs/03` §3
documents `3.7` and `3.8` as part of the `3.6` class — but they were measured on
`.eu` **at base `v13`** (`3.8` also appears on `-trials`, but at base `v6` — §8).
On `.com` and `-trials` the only tails ever requested at base `v13` are `3.5`,
`3.6`, `3.9` and AA's fabricated value, so no intermediate tail has been swept on
either host at that base. AA's four tails bracket nothing. **Assumptions
(INFERRED):** that the `3.6`-class
and `3.9`-class documents on `v13` remain distinct long enough for a ladder to
separate them — they were distinct on 2026-10-17; and that the response document is a
function of `(host, base, tail)` with no fourth input, which AA's cross-product is
consistent with but did not test.


### AF. Can the findings-log census be made self-deriving, so no lane restates it by hand?

**What is known, labelled and cited.** The committed-ledger census is stated by hand in
**at least three** places — the S-L4c block, the ledger-census row, and a comment in
`findings-log/2026-10-14-lane-s6-public-index/account.py` — and its population is
**derived from the tree**, so **every merge that adds a `findings-log/…/results.jsonl`
moves it**. OBSERVED: area AA's ledger moved the population 50 → 51 at `ad376d8` and
would make it 52 when #154 lands, falsifying all five derived figures one merge after
they were written (see the **S-L4c correction of 2026-10-20**, further up this page).

**What is missing, and why it matters.** Nothing catches this. `scripts/research-checks.py`
checks the assertion count, the open-area count, the prose counts and the log-cite
resolvability — it does **not** derive the ledger census, so a then-value survives CI
until a human notices. The failure mode is silent by construction: the sentence reads
correctly at the head it was written on and is wrong at the next.

**Blocker:** nothing external. **0 requests.** A static check in `scripts/research-checks.py`
that derives `git ls-files 'findings-log/*/results.jsonl' | wc -l` and fails on any docs
sentence stating a bare ledger population with no commit anchor beside it — the same
shape as the existing "N open plus M closed" check, which already fails on drift.

**Closes when:** no bare population figure survives without a commit it is true at, **or**
the census is reported only as command output and the hand-stated figures are deleted.
**A negative counts** — if the check cannot distinguish a genuinely anchored figure from
a live one, that is itself the finding and the answer.

**Non-duplicate:** no existing check derives this census. **Assumptions (INFERRED):** that
the three hand-stated sites are all this PR can see, and that no fourth exists in a
findings-log comment the census prose does not name; a `grep` for the counting command
settles it. **Labelled:** the *falsehood* is OBSERVED; the *remedy* is INFERRED until a
check exists.



> **Area V is CLOSED** (2026-10-13, claim #42) — see the Closed table at the foot of
> this page and
[findings-log/2026-10-13-area-v-pde-clients/FINDINGS.md]. **Recorded negative, with a
> sharper reason than the area expected:** no vendor web bundle contains `baseUrlPde` —
> and no `baseUrl*` key, `discover/android`, `clcloud` or `api/carepartner` is present
> either, because **no web bundle in the corpus reads the discovery document at all**.
> ⚠ **corrected 2026-10-13**: this row first published `discover` as 0 in all five
> bodies. It is **12 in each portal build**, every one a zxcvbn password-dictionary
> word — the conclusion is unchanged and the negative is stronger (17 dictionary hits
> per portal build: 12 `discover` + 5 `pde`), but the number was wrong. See
> [findings-log/2026-10-13-area-v-pde-clients/FINDINGS.md §Correction (2026-10-13) §A]. The document's consumer is
> the mobile client its own path names (`discover/android/3.6`), so "does a client follow
> it" remains **unobserved in both directions** and `docs/03` §9a's INFERRED reading
> stands unchanged. The same corpus produced a **positive on the sibling pointer**: the
> patient bundle follows `csr.cumulus.periodic.data.endpoints` and POSTs its
> `display_message`, while naming `system.gc.gz.transition.flags` and never reading it in
> the eager bundle (the lazy chunk `6746` does — see docs/04).
>
> Its reasoning is preserved below rather than deleted, and its follow-ups were filed as
> **dated addenda to areas F and K**, not as new letters — see
> [Why there is no area AA](#why-there-is-no-area-aa).

> **Area Z is CLOSED** — see the Closed table at the foot of this page and
[findings-log/2026-10-12-area-z-origin-reflection/FINDINGS.md]. `ACAO` is a constant `*`, not an
echo: **45 of 45** cells, 3 hosts × 5 route families × 3 `Origin` conditions. It is left here
rather than deleted so the reasoning survives; a closed area never leaves the page silently
([How to claim one](#how-to-claim-one), rule 5).

> **Area E is CLOSED** — see the Closed table at the foot of this page and
> [findings-log/2026-10-13-area-e-perkey-deployments/FINDINGS.md]. Its framing
> addendum from area W is **reproduced verbatim below**, not deleted, so the
> reasoning that produced the area survives; a closed area never leaves the page
> silently ([How to claim one](#how-to-claim-one), rule 5). Its successor is the
> dated addendum under **F** below.

#### Addendum (2026-10-13, from area W) — preserved: one deployment swept, two remained

> **Restored 2026-10-13 by area E.** Area E's first version of this page deleted
> this addendum along with the `### E.` heading while the pointer above promised
> the addendum would survive — a pointer promising non-erasure while erasing, which
> is `AGENTS.md` §6 item 5 in miniature. The wording below is area W's, unchanged.
> **Its close condition was met on 2026-10-13 by area E** (negative — all three
> deployments carry the same 69-name key set), so it is history rather than an open
> task. Its `Assumptions (INFERRED)` line is now **tested, not assumed**: the
> per-key grammar *is* keyed off the same flat-name form on all three deployments.

Area W swept all 69 keys plus `captcha`'s four subkeys on **EU only**
([findings-log/2026-10-13-area-w-per-key/FINDINGS.md]): 61 VALUED-match, 5
NULL-404, `captcha`/`default.country` on dedicated routes, zero names outside
the bulk document — and the complete 69-name list is now committed at
[findings-log/2026-10-13-area-w-per-key/keys.txt](../../findings-log/2026-10-13-area-w-per-key/keys.txt),
so the candidate list for the remaining two deployments is closed and needs no
re-derivation. One caveat travels with it: `personal.common.core.reporting.enabled.countries`
does **not** round-trip on EU — its per-key value carries a stray trailing `]`
(reproduced byte-identical), so a cross-deployment value comparison must parse
defensively, not string-compare. **Closes when:** the per-key form has a verdict
for all 69 keys on `.com` and `-trials`, with absent-vs-null resolved per
deployment. A negative (all three identical) counts. **Assumptions (INFERRED):**
that the per-key grammar is keyed off the same flat-name form on all three
deployments — only one has ever been swept.

### F (closed 2026-10-14) What the timeline and dialog-lite gateways actually are

**Closes on the letter's own condition — "you can name the caller and say whether a
third-party client can reach these services" — as a negative on the naming half and as
a negative on the reachability half, with the cause half explicitly left blocked.** The
addenda below are preserved in place and unedited: they are the history this verdict
rests on, and the closing addendum is at the bottom of this section.

Both are AWS API Gateway stage-wide `ANY /{proxy+}` catch-alls. `dialog-lite` 500s
on every invocation (the Lambda throws); `patient-timeline` 403s uniformly. Neither
is browser-callable — zero of 90 responses carried `Access-Control-*`.

So: how does the portal call them? **It must not be the browser.** Look for a
server-side proxy in the portal bundle, or a `m2m` / `gc` call pattern from the
patient API. The patient config names them, but a service only reachable from
Medtronic's own backend is a different piece of architecture than one a client can
call.

**Closes when:** you can name the caller and say whether a third-party client can
reach these services at all.

#### Addendum (2026-10-13, from area E): the two config-escape routes have only ever been read on one deployment

**Derived from area E's negative, which is what makes this askable.** E swept
all 69 names per-key on `.com` and `-trials` and found the projection is
byte-for-byte identical to each host's own bulk document, **0 mismatches in 123
valued cells** ([findings-log/2026-10-13-area-e-perkey-deployments/FINDINGS.md]
§2). That means a third-party client reading config unauthenticated has exactly
**three** read paths, not 69: the bulk document, plus the two keys whose per-key
form is a 404 because they live at **dedicated routes** —
`/patient/configuration/defaultCountry` and `/patient/configuration/recaptcha/key`
— plus `/patient/configuration/messages/{lang}` beside them.

**All three were recorded on `.eu` only**, by the 2026-10-08 namespace pass
([findings-log/probe-2026-10-08/recon/CONFIG-NAMESPACE-DEEP.md]). No pass has
requested either dedicated route on `.com` or `-trials`, and area E's own log says
so rather than implying it ([source:
findings-log/2026-10-13-area-e-perkey-deployments/FINDINGS.md §7]). A client that
falls back to `defaultCountry` when the per-key form 404s has **never been
observed to succeed anywhere but the EU host** — and that fallback is exactly what
the `default.country` / `captcha` verdict is for.

**What is missing:** whether the two dedicated routes are live, and return the
same envelope, on the other two deployments; and whether `messages/{lang}` is
still `{"messages":[]}` or has gained content. A **third** question fell out of
E and is the cheaper one: the trials host returned **one real-key 404 carrying
`content-type: application/vnd.nervana`** — a value in **no prior reading anywhere
in this namespace** — so the 404 content-type set is **deployment-dependent and
three-valued**, not the two-valued shape area W recorded on EU.

**Blocker:** a bounded candidate list that already exists on disk and needs no
invention — the three routes above, plus `/patient/configuration/version` and the
`/patient/configuration/` root (both already tried and 404'd on EU, so they are
**controls**, not candidates). That is 5 paths × 2 hosts + 2 controls per host =
**14 requests**, GET only, controls first per host.

**Closes when:** all three routes have a recorded verdict on `.com` and `-trials`,
and the per-deployment 404 content-type set is tabulated. **A negative counts**
and is the likely answer — that the two dedicated routes are EU-only, or that the
whole sibling namespace is identical everywhere, would both close this. The one
outcome that does *not* close it is a new key appearing under
`/patient/configuration/` on a non-EU host, which would reopen the projection
question E just retired.

**Assumptions (INFERRED):** that the `/patient/configuration/` sibling namespace
behaves the same on all three deployments — E established this for the
`/system/` subtree only, on the strength of an identical 69-name key set and
identical per-key verdicts, which is evidence about `/system/` and not about the
siblings. `application/vnd.nervana` is recorded once, on one cell, on one
deployment: that it is a deployment-level constant rather than a per-key or
per-route value is **not** established, and one observation cannot separate those
three readings.

#### Addendum (2026-10-13, verifier round 2 of area E): commit the per-cell digests, or the "0 mismatches" claim is unverifiable forever

**Derived from a failure, not from a topic.** Area E's central claim — **0 value
mismatches across 123 valued cells** — is the one number in its log that **no
reviewer can re-derive.** It passed two verifier rounds as sound and
*unverifiable*, which are not the same property: the claim needs, per cell, both
sides of the equality (the response body to unwrap the envelope, and the host's
resolved bulk subtree), the response bodies were transient by design
(`AGENTS.md` §7, no raw captures), and `verdicts.py` cannot be re-run without
them. The verdict was recorded as **inherent, not a defect** — areas W, G and H
share the same property. **But area E also published a row claiming a second code
path had confirmed it, and no such path existed** ([findings-log/2026-10-13-area-e-perkey-deployments/FINDINGS.md]
§Correction (2026-10-13), F1). **That is the honest reason it was a fabrication
rather than an overstatement: there was nothing to confirm it with.**

**What would have made it checkable, forever, at zero extra requests.** One line
in `verdicts.py`, emitting a committed `cell-digests.tsv`:

```
host  key  seq  norm  sha256(canonical(parsed value))  sha256(canonical(resolved bulk subtree))
```

Digests, **never values** — so it satisfies `AGENTS.md` §7 exactly as this repo's
bulk-document digests already do, and a verifier can re-hash both sides from the
committed file and confirm the equality without ever holding a body. **This is
one line of code and zero requests; it is not hard, which is exactly why its
absence is a finding rather than an excuse.**

**Foreclosed for area E, and the reason matters.** It cannot be added now: the
bodies are gone, so the digests cannot be computed retrospectively and inventing
them would be worse than not having them. **Foreclosed by the transient bodies,
not by the request budget** — area E used 152 of a 170 cap, so 18 requests were
unspent. The next pass over this namespace must emit it.

**Blocker:** none, zero requests, for the digest artefact alone — it is written
during a sweep, not after one. It becomes possible only while a body is in hand,
which is why it is a property of *running* a sweep rather than of a follow-up.

**Closes when:** any sweep over `/patient/configuration/` commits a per-cell
digest artefact whose two columns a stranger can re-hash, **or** the area that
produced it records in prose that its "0 mismatches" claim is **log-level and
non-re-derivable**, so no later reader mistakes it for a pinned assertion.
**A negative counts:** if the two digest columns ever disagree on a cell, that is
a positive finding about the vendor, not a harness artefact.

**Assumptions (INFERRED):** that a value digest is a sufficient equality witness
here — it is, because every compared cell's bulk side is derivable from the same
host's bulk document, which **is** re-fetchable unauthenticated in 1 request per
host, whereas the response side is not. The one case a digest cannot settle is a
hash collision, which this repo already treats as an acceptable residual for the
same reason (`docs/09` §5 item 3).

#### Addendum (2026-10-13, from the #61 CORS-method pass): the family claim rests on two
hosts, no `commoncore*` cell was ever matched, and none has ever varied `Origin`

**Why this is filed under F rather than in a letter of its own, recorded because the page has
a documented placement problem and the reason was missing.** Every letter A—Z is in use, so a
new `### ` heading would leave this page's own "N open plus M closed" sentence disagreeing
with its contents — which is the failure `docs/11`'s own addenda have already been written to repair
twice. ⚠ **Superseded 2026-10-16: the namespace continues past Z and two-letter headings now
count** — see the Amendment in "Why there is no area AA". Of the five open areas, **F is the only one whose subject is the CORS behaviour of an
AWS-API-Gateway-behind-CloudFront deployment**: its own text turns on "zero of 90 responses
carried `Access-Control-*`", which is the same question on the `clcloud.*` stage. The host
family differs and this addendum says so in every sentence that could be misread; the
**mechanism** does not, and that is what the successor is about. Filing it under a token-
gated row would have been worse: this needs no token.

**Derived from a cell nobody had run.** Before 2026-10-13 no **OPTIONS** request had ever
been sent to any `commoncore*` host, so two things were unaskable. One has an answer. **OBSERVED,
8 of 8 cells**, 2 hosts × {recorded path, certainly-absent path} × {`GET`, empty-body
`OPTIONS`}: `403` `MissingAuthenticationTokenException`, `ACAO`/`ACAM`/`ACAH` all `*`, no
`ACAC`, no `Allow`, no `Vary`, all 8 byte-identical once the per-request headers are
stripped ([findings-log/2026-10-13-cors-method/FINDINGS.md §3]). On this origin stack the CORS set is **not
method-conditional** — **and the bound is `non-2xx` only: every cell is a no-route `403`, so this says
nothing about a `2xx` on either method.** So **"emitted only on `OPTIONS`" is excluded for
this family**, and the corollary is the useful half: an `OPTIONS` response carrying `ACAO: *`
**here is not proof that a resource exists**, so `docs/09` §2's `GET 403 + OPTIONS 200` rule
needs the status beside the header, not the header alone (**no `clcloud.*` host was probed,
and `clcloud.*` emits no CORS at all on this error — `regression/hurl/04-deep-surface.hurl:182`, `:444` — so
nothing here transfers to that family**; F's own premise, that these gateways are not
browser-callable, is untouched).

**⚠ What this addendum does NOT claim, because its first version did and the log did not
support it.** Not "not path-conditional": **all 8 cells returned the same no-route envelope,
so nothing was ever matched and the path question is untested rather than answered.** The
path axis shows only that `ACAO` does not discriminate between a path a prior pass recorded
and one the gateway has never heard of ([findings-log/2026-10-13-cors-method/FINDINGS.md
§3.2]).

**What is missing, in three halves.** (a) **Breadth:** `commoncore-trials.minimed.com`
carries 1 of the six counter-examples and was **not** probed — three cells per host is 9 requests
against a cap of 8, and the full matrix is 12. That was a **trade**, not a rule: the fourth
cell per host is the only one that adds contrast, so 8 requests on 2 hosts buys a complete
square twice where 6 on 3 buys a pair and no square anywhere.
(b) **A matched cell.** No pass has yet sent a request to a `commoncore*` path that this
stage actually routes, so no claim about how the CORS set behaves on a *routed* response
here can be made at all. (c) **A dimension no pass has varied:** `Origin`. Area Z excluded
"ACAO appears only when an `Origin` header is sent" on `clcloud.*` route cells; on
`commoncore*` **no pass has ever sent one**, and this pass sent none deliberately, to match the
captures it follows. `Vary` is absent on all 8 cells — that is a caching directive and **no
emission mechanism is inferred from it**.

**Blocker:** not an idea and not a token for the two halves that are reachable — **8
requests**. (a) Four: the same square on the third host, `GET` and empty-body `OPTIONS` on
`/reports-broker/v1/ocl` and on `/reports-broker/v1/ocl-probe-absent`. **No "positive
control" is claimed here**: the first version of this addendum justified that phrase and
the verification round disproved it — on this stage the recorded path answers identically to the absent one, so
it is a second data point on the same envelope, not a control over it. (c) Four: one host,
two paths, each bare and each with `Origin: https://example.invalid` — a reserved name, so the value can
only be echoed or dropped, never dialled. `Origin` is a request header, so it adds no traffic
to a third party. (b) **Is not reachable and is not budgeted:** finding a *matched* cell needs
a `commoncore*` path this stage actually routes, and the only routes recorded there are the
token-gated report ones — already the blocked-table row *"Report bodies from `commoncore`"*. Naming that
is more useful than a request count that could not be spent.

**Closes when:** (a) the third host has a verdict on the square **and** (c) one host has a
verdict on the `Origin` axis. A verdict is the **status plus** the header set, never the
header alone, so a partial answer cannot read as a settled one. **A negative counts** on both,
and is the likely answer for (c), given the literal `*` in every cell recorded so far. (b)
closes when it joins the blocked table with a token named, or is retired as unanswerable from
outside — it does not close by another unauthenticated sweep.

**Assumptions (INFERRED):** that these two hosts are representative of the
`commoncore-trials.medtronic.com` / `commoncore.medtronic.com` family — **which is exactly
what half (a) tests, and is not assumed by this addendum's own claim**, since the claim is
stated per host. That the `*` is stage-level gateway configuration rather than a per-route
setting: it appears on a `MissingAuthenticationTokenException`, which is evidence about the
*stage*, but the mechanism remains unestablished, as `docs/09` §2 says. That half (b) is
token-blocked rather than merely unprobed: the reasoning is that the only `commoncore*` paths
on the record are report routes behind a clinician token — **INFERRED from the blocked-table row, not
measured**, and one probe of the namespace root would settle it or refute it. That an `Origin`
on a no-route error would be handled by the same code path as an `Origin` on a routed one —
**untested**, and the two are not interchangeable.

#### Addendum (2026-10-13, from swarm lane S3, issue #92): halves (a) and (c) close; half (b) stands

**What changed.** The #61 addendum above named three halves. Two were reachable
unauthenticated, and both are now closed
([findings-log/2026-10-13-s3-commoncore-origin-cors/FINDINGS.md]).
Half (a) — third host (`commoncore-trials.minimed.com`): the full square matches the
two #61 hosts byte-for-byte, same `MissingAuthenticationTokenException`,
`ACAO`/`ACAM`/`ACAH` all `*`, body digest `f249b63c…`. The no-route envelope is
stage-level on the `commoncore*` family, not host-specific. Half (c) — `Origin`
varied on every cell of one host: status, every `access-control-*` header, `Vary`,
`Allow`, and the body digest are unchanged; the gateway stamps per-request AWS
ids on every response and does not echo `Origin`, and `Vary: Origin` is absent on
all 12 cells. So `OPTIONS` + `ACAO: *` on this stage is still not proof of a
routed resource, and `*` is not an `Origin` echo
([findings-log/2026-10-13-s3-commoncore-origin-cors/FINDINGS.md §3, §4]).
Measured spacing floor 2.731 s (10 same-host gaps, 0 under 2.5 s).
12 of a 12 cap, GET + empty-body OPTIONS only, no POST.

**What is still missing.** Half (b) — a matched cell — is unchanged: it needs a
`commoncore*` path this stage actually routes, which on the record exists only
behind a clinician-scoped token, so it stays in the blocked table row
"Report bodies from `commoncore`". One probe of the namespace root would settle
it; this lane did not spend it.

**F's own count of open successor space is unchanged:** one blocked row remains,
and no new letter is minted (all A-Z are in use).

#### Addendum (2026-10-13, from area V): the shipped patient bundle names a timeline host that is not published

**Derived:** none of this was knowable before 2026-10-13 — area V re-fetched the patient
bundle and grepped it, and these four facts came out of that corpus rather than out of
the network [findings-log/2026-10-13-area-v-pde-clients/FINDINGS.md].

**OBSERVED**, patient bundle `main.6595daf83bd6d4b1.js` (3,417,255 B, sha256
`0fb4fbd4…`, captured 2026-10-13, byte-identical on `carelink.minimed.eu` and
`carelink.minimed.com`):

- **`dialog-lite` is 0 hits in all five captured bodies.** The premise that the portal
  calls it is **not supported by the corpus** — a negative, not a refutation of the
  route.
- **`patient-timeline` is 5 hits and every one is an Angular component selector, not a
  URL** — `["app-patient-timeline"]` (byte 1718181),
  `"app-patient-timeline-filter-toolbar"` (1719243), two template calls (1963408,
  1963661) and one `selectors:` array (3340159). A grep on the bare name reports an
  integration that is not there: the `docs/09` §5 false-hit class, on the one token
  this area is specifically hunting.
- The bundle **does** carry `personal.patient.timeline.config` as a quoted literal and
  reads it (selector `Nt`, exported as `bQ`, 3 property reads), and a template reads
  **`.featureEnabled`** off it to choose between rendering the Patient-Timeline tab and
  not (byte 1966110). The timeline is therefore **config-gated in shipped code**, which
  is one step closer to a caller than "it must not be the browser".
- ⚠ The bundle **also names `personal.patient.timeline.host`** — 1 occurrence, and its
  constant `personalPatientTimelineHostURL` occurs **once**, so nothing reads it. The
  **published** key is `personal.patient.timeline.config.host` (`docs/04`, an AWS API
  Gateway answering 403). `personal.patient.timeline.host` is **not** in the 69-name
  list area W committed, i.e. **the bundle names a config key the public document does
  not publish.** Which of the two is real is **not** settled here.

**Blocker:** the shape of `personal.patient.timeline.config` has never been read. This
area asks "who calls `patient-timeline`", and the caller turns out to be gated on that
object's `featureEnabled` — while the object itself is nowhere in this repo's recorded
values and only its `.host` member is named. **It costs zero requests**: the whole
public config document is already downloaded by `regression/hurl/05-public-config.check.sh`,
so one `jq` on that body enumerates the object's full key set.

**Closes when:** `personal.patient.timeline.config` has its **full key set** recorded
from the live public config on all three deployments, and the bundle's two timeline-host
keys are reconciled against it — either the bundle's key is a stale name nothing reads
(half-evidenced now: its constant has zero readers in the eager bundle) or the vendor
publishes a second, unrecorded key. **A negative counts**: "the bundle names a key the
document does not publish, and nothing reads it" is a complete answer.

**Assumptions (INFERRED):** that the patient bundle fetched from `carelink.minimed.eu`
is what the shipped patient web app loads — its asset name is taken from that host's own
entry document in the same run, but no authenticated session confirms a logged-in user
receives it. And that a lazy chunk cannot read the timeline config: **only the eager main
bundle was swept**, the 211 lazy chunks were not (see the addendum to area K).

#### Addendum (2026-10-13, from area F): the timeline config is read, the stale key is confirmed, and the dedicated routes are not EU-only

**Area F stays open** — this addendum settles four of its addenda and leaves the
letter's own question ("who calls `patient-timeline`, and can a third-party client
reach it") untouched. Claim **#55**, 24 of a 26 cap, GET only
([source: findings-log/2026-10-13-area-f-timeline-config/FINDINGS.md]).

**Three of the four addendum deliverables are answered, two of them positively.**

1. **The blocker above is gone.** `personal.patient.timeline.config` is an object of
   **exactly two members, `featureEnabled` and `host`, the same member set on all three
   deployments** (`OBSERVED`). `featureEnabled` is boolean `true` everywhere; `host` is a
   deployment-specific `https` string carrying **three distinct digests**. Its **value is
   deliberately not published**. Both facts are now **pinned** — six assertions in
   `regression/hurl/05-public-config.check.sh`, **zero extra vendor requests**, since every
   body it reads is already fetched by that suite's area-E block.
2. **The two timeline-host keys are reconciled, and the open reading is closed.**
   `personal.patient.timeline.host` is **not a top-level key in any of the three bulk
   documents** and its per-key route 404s with 0 bytes on all three (`OBSERVED`, 3 of 3).
   So the document publishes **exactly one** timeline host, as `…timeline.config.host`, and
   the bundle's second name is the **stale key**. Area V's alternative — "the vendor
   publishes a second, unrecorded key" — is **refuted**, on a membership test against the
   document rather than a status code. The per-key 404 corroborates but cannot carry the
   claim: on this plane a null-valued key 404s identically to an absent one.
3. **The EU-only hypothesis for the dedicated routes is refuted.** Area E's addendum above
   expected "the two dedicated routes are EU-only" as the likely answer. **All three answer
   `200 application/json` on `.com` and `-trials`** (`OBSERVED`): `defaultCountry` (20 B,
   byte-identical across the two), `recaptcha/key` (58 B, **different** on each — consistent
   with the three region-specific keys `scripts/scrub-patterns.txt` already records), and
   `messages/en` (22 B, byte-identical). **A third read path exists on every deployment, not
   three of one.** `messages/en` returns **22 B where the recorded `.eu` value
   `{"messages": []}` is 16 B**, so its shape has changed; the content is **not claimed**,
   because bodies are transient and no reader should infer "empty" from a 200.
4. **The per-cell digests area E could not produce retrospectively now exist.**
   `cell-digests.tsv` in the log carries `sha256(canonical(parsed value))` and
   `sha256(canonical(resolved bulk subtree))` per cell — **digests, never values**. The
   projection of `…timeline.config` equals its own host's bulk subtree **3 of 3**, which is
   the re-derivable form of area E's otherwise log-only "0 mismatches" claim. Every digest is
   **type-asserted before it is hashed**, and a resolve that returns null writes
   `NULLRESOLVED` rather than the digest of `None` — `docs/09` §5 item 3.

**Also settled, and it is a trap: this key is a literal dotted name.** Splitting
`personal.patient.timeline.config` on `.` resolves to `null` on all three deployments while
the literal key resolves to an object, so a dotted-path walker would have hashed nothing
against nothing and reported agreement (`OBSERVED`, recorded deliberately as a control).

**And a fifth, negative result about the 404 content-type set:** **9 of 9** 404s in this
pass carried **no** `content-type` header at all — and, unlike areas W and E, this pass
probed the **namespace root level**, which no prior pass had, so that shape is observed
for the first time. ⚠ **A hypothesis this addendum briefly carried is withdrawn.** It
proposed that the discriminator is *the plausibility of the requested name* (an absurd
fabricated name returns `text/vnd.a`, a plausible unpublished name returns none).
**Falsified by a cell that sits beside it**: area E's trials **seq 127**,
`personal.linking.request.interval`, is a **real-key 404** against a **published** name
(69-name list, line 48) and carries **`application/vnd.nervana`** — exactly what the
plausibility reading predicts it would not. **Three values exist and no property of the
requested name separates them.** `docs/04`'s standing instruction not to discriminate on
it is confirmed, with a third independent reason [findings-log/2026-10-13-area-f-timeline-config/FINDINGS.md
"Deliverable 3"].

**Two corrections to this page's own premises, recorded rather than smoothed over.** The
claim and the pool brief both named **`/patient/configuration/`** as the bulk document; it is
the **per-key** namespace, and the bulk document is **`/patient/v2/configuration/public`**
(`05-public-config.check.sh` fetches exactly that). Used as written, deliverable 1 would have
returned a 404 and been recorded as "the key is not published" — a false negative produced by
the brief. And this page's line 178 describes `/patient/configuration/version` and the
`/patient/configuration/` root as "already tried and 404'd on EU"; **no committed record
contains either probe** — what the 2026-10-08 pass recorded 404 is the `/patient/v2/`
siblings, a different namespace. Both controls were therefore **measured per host** instead
of inherited, which is what made them usable.

#### Successor to area F — does the published `config.host` pointer name the gateway this repo probed?

**Known, labelled.** The object's full member set is recorded and pinned
(`OBSERVED`, [source: findings-log/2026-10-13-area-f-timeline-config/FINDINGS.md "Deliverable 1"]). The
`host` member is an `https` string of **79 / 76 / 76** characters on `.eu` / `.com` /
`-trials`, with **three distinct** sha256 digests (`OBSERVED`, same source). The value itself
is **not published** here and its content is **not claimed**. Separately, this repo records the
service's host shape as `…eu-central-1…/prod/patient-timeline` (EU) and
`…us-east-1…/prod/patient-timeline` (US and trials) (`OBSERVED`,
[source: findings-log/probe-2026-10-08/CROSS-REGION-CONFIG-FINDINGS.md]), which is how
[`07-admin-portal-and-reporting.md`](../07-admin-portal-and-reporting.md) attributes the
probed `patient-timeline` gateway to this config key.

**Missing, and why it matters.** The measured lengths and the recorded region names
**disagree**: EU is **three** characters longer than the other two deployments, while
`eu-central-1` and `us-east-1` differ by **two**. So either something other than the region
string differs between the EU and US pointers, or one of the two records is wrong.

⚠ **The reason this is not checkable from the log — corrected 2026-10-13.** Area F first
wrote that the value "has never been read". **That was false, and it was false against this
repo's own record**: the 2026-10-08 pass read it and published it **ellipsised**
([source: findings-log/probe-2026-10-08/CROSS-REGION-CONFIG-FINDINGS.md] — *"Every host
below was disclosed only by the config"*). The true obstacle is narrower and worth stating
precisely: **the committed record abbreviates exactly the segment the question turns on.** The
ellipsis sits where the host's region and API-Gateway id live, and the length discrepancy is
about that segment. So the disclosure is evidenced and the *arithmetic* is not re-derivable
from what is committed — which is a different defect from an unevidenced claim, and the one
actually worth someone's request budget.

**Blocker:** the un-abbreviated string is readable only **while a response body is in hand**,
and bodies are transient by design (`AGENTS.md` §7). It cannot be recovered after a sweep, and
it is one unauthenticated GET away — so the blocker is a harness, not a token or a budget:
**3 requests, 1 per patient deployment**, plus the recorded shapes already on disk.

**Closes when:** the string is read on all three deployments and either (a) its length
accounts for the discrepancy against the recorded shape, or (b) the discrepancy is explained
and the wrong record is corrected in place with the original kept visible. **A negative
counts and is the more likely answer** — "the pointer does not name the gateway this repo
probed" would be the more consequential result, and it closes this.

**A note on the value itself, and a deliberate non-decision.** Whether the un-abbreviated
`host` value may be published is **not settled here and not pre-committed**. Area F's first
draft of this successor promised publication conditional on a scrub-list check; that has been
**removed**, because deciding in advance whether a disclosure is publishable is a disclosure
decision, and it belongs to a human holding the value — not to a research pass writing a
placeholder. **What a reader should take from this row:** the question is answerable for
**3 requests**, the answer decides nothing about the vendor's behaviour, and whether the
answer becomes public is a separate call made by a person, with the value in hand and
`scripts/scrub-patterns.txt` in front of them.

**Assumptions (INFERRED):** that the 2026-10-08 shape record and the 2026-10-13 measurement
describe the same field — the 2026-10-08 pass may have read a different deployment's value, or
abbreviated in a way that dropped a character. Nothing above assumes the value is publishable.

#### Successor to area F — what is in `/patient/configuration/messages/{lang}` now?

#### Addendum (2026-10-14, swarm lane S2, issue #91) — this successor is **CLOSED**: the array is empty and the 6 bytes are formatting

**Recorded as a shape, not prose, and deliberately without the value.** `GET /patient/configuration/messages/en` answers `200 application/json`, **22 B**, one sha256 (`04868b50…`) **byte-identical on all three** patient deployments; the envelope member list is `["messages"]` and the array length is **0** on every one (`OBSERVED`, 6 of a 6 cap, controls first per host: [source: findings-log/2026-10-14-area-s2-messages-en/FINDINGS.md]; `results.jsonl` seq 2 / 4 / 6).

**The 16-vs-22 byte delta is a formatting difference on the same empty array** — the canonical, newline-free rendering of `{"messages":[]}` is **15 B** (`sha256 5e4ce7b3…`), so the 2026-10-08 note's "16 B" was a transcription of a differently-formatted rendering of an empty array, not a different value. That is the **negative** this successor asked for, and it is worth recording precisely because it means the 2026-10-08 record was about the wrong thing.

**The `INFERRED` assumption above is now tested rather than assumed:** `22` and `16` are comparable byte counts of the same envelope, and the array was empty all along. **No customer-facing copy is published** — an empty array has none, and the pass deliberately recorded shape only.

**What this does not settle.** Nothing about *why* the endpoint is empty on all three deployments (an i18n feature flag, a decommissioned path, or a build artefact is **not** established, and no claim is made). Area F's own question — who calls `patient-timeline`, and whether a third-party client can reach it — is untouched by this row.

**Successor, derived from this pass:** the **positive control** used here (`GET /patient/v2/configuration/public`, 24 479–31 698 B, **69 top-level keys** on all three) is the cheapest liveness oracle in the patient namespace, and it is not currently pinned anywhere. A drift sweep that reads the bulk document anyway could assert the key count per deployment at **zero extra requests**. Closes when that count is pinned for all three deployments; a negative (the count already drifts) counts. **Assumptions (INFERRED):** that the 69-key figure is stable rather than build-specific — area E measured the same 69-name vocabulary across deployments on 2026-10-13, so this is corroboration of an existing claim rather than a new one, and the successor's value is the *pin*, not the count.


**Known, labelled.** The route answers `200 application/json` on `.com` and `-trials`
(**22 B**, byte-identical by sha256 across the two) and was recorded `200` returning
`{"messages": []}` (**16 B**) on `.eu` in 2026-10-08 (`OBSERVED`,
[source: findings-log/2026-10-13-area-f-timeline-config/FINDINGS.md "Deliverable 3"];
[`CONFIG-NAMESPACE-DEEP.md`](../findings-log/probe-2026-10-08/recon/CONFIG-NAMESPACE-DEEP.md)
line 90). The live value's **content is not in the ledger**, because bodies are transient.

**Missing, and why it matters.** A **6-byte** difference between a recorded empty array and
what two deployments serve today is a change in an unauthenticated, client-facing i18n
endpoint. `docs/04`'s reader currently cannot tell whether a client can rely on this route
being empty. **It is also the cheapest remaining question in area F** — the bytes are
already known, only the value is not.

**Blocker:** the value is readable only while a body is in hand. **3 requests**, 1 per
deployment, or 1 if the `.com` byte-identity with trials is trusted.

**Closes when:** the response is recorded as a **shape** (member list and array length) rather
than as prose — and if the array is non-empty, **its size and the shape of one entry, never a
translated string**, since this is customer-facing copy. **A negative counts**: "the array is
still empty and the 6 bytes are elsewhere in the envelope" closes it, and is worth recording
precisely because it would mean the recorded 2026-10-08 note is about the wrong thing.

**Assumptions (INFERRED):** that `22` and `16` are comparable byte counts of the same
envelope — the 2026-10-08 record is a transcription in prose, not a measured
`content-length`, so it may have counted a differently-formatted rendering of the same empty
array. **That assumption is the first thing to test**, and a `content-length` header settles
it without reading the body.

---

#### Addendum (2026-10-13, from `pool-f-config-host`): successor evidence for the published pointer and `messages/en`

**Derived from 6 GETs across the three patient deployments, unauthenticated, cap 6/6,
`results.jsonl` in `findings-log/2026-10-13-pool-f-config-host/`.**

- **Successor 1 (pointer naming).** `personal.patient.timeline.config` is still a
  two-member object (`featureEnabled`, `host`) with the same member set on all three
  deployments; `featureEnabled` boolean `true` everywhere. The `host` member remains
  an `https` string of **79 / 76 / 76** characters with **three distinct digests**
  (`f81e6648…` / `24ee5564…` / `988acbd7…`), **unchanged** since the
  2026-10-13 area-F pass. In-process shape classification shows it is an AWS
  API Gateway host (`.execute-api.`, 10-character gateway id, ending
  `/prod/patient-timeline`) whose region segment is `eu-central-1` on `.eu` and
  `us-east-1` on `.com` and `-trials`. The measured 3-character length delta
  (`79 − 76`) is exactly the difference between `eu-central-1` (13) and
  `us-east-1` (10), leaving no unexplained characters. So the pointer is
  **consistent with naming the gateway this repo probed**; the id segment was
  not compared (it is infrastructure, not published), so this is strong
  consistency rather than proof. **Raw `host` value not published.**

  **Correction (2026-10-14, from lane S1, issue #90).** The id segment *was*
  compared on all three deployments by hashing it while the bulk document was in
  hand, without publishing it: `bfda4356…` (`.eu`) / `30a035af…` (`.com`) /
  `f11b68e5…` (`.trials`). Each equals the SHA-256 of the 10-character
  gateway id published for the same deployment's `patient-timeline` gateway in
  [`findings-log/2026-10-12-published-pointers/enumeration-scrubbed.txt`](../findings-log/2026-10-12-published-pointers/enumeration-scrubbed.txt)
  lines 121 / 187 / 245, so the 2026-10-13 “strong consistency rather than
  proof” sentence is superseded: the pointer carries the *same gateway id* as
  the probed gateway, not merely the same shape. It still names a
  *per-deployment* gateway, not one shared id. See
  [`findings-log/2026-10-14-s1-config-host-pointer/FINDINGS.md`](../findings-log/2026-10-14-s1-config-host-pointer/FINDINGS.md)
  §Deliverable 1. Nothing here makes F's caller/reachability sub-question any
  less open.
- **Successor 2 (`messages/en`).** All three deployments answer `200`,
  `application/json`, 22 bytes, digest `04868b50…` (byte-identical). Envelope
  member list is `["messages"]`; the array length is **0** on all three. The
  16-vs-22-byte difference against the 2026-10-08 record is a formatting
  difference on the same empty array.
- Neither successor closes area F: the caller / reachability question for
  `patient-timeline` is untouched; a third-party client's ability to reach it is
  not settled by either of the above.
- F remains **open**; area count unchanged.


#### Addendum (2026-10-13, from `area-f-dedicated-routes`): independent controls-first re-derivation of the dedicated routes on `.com` and `-trials`

Area F's dedicated-route half (Deliverable 3 of the 2026-10-13 pass) stands, but the
controls behind it had not been re-issued from a clean baseline after the dispatch: both
controls turn out to reproduce byte-for-byte. This pass re-issues them, controls first per
host, on the two remaining patient hosts.

**Derived from 10 GETs (2 controls + 3 routes × 2 hosts), cap 14, `results.jsonl` in
`findings-log/2026-10-13-area-f-dedicated-routes/`.**

- **Controls.** `/patient/configuration/version` and `/patient/configuration/` (root) both
  404 with 0 bytes and no `content-type` on both hosts — the same shape the earlier pass
  recorded.
- **Routes.** All three answer `200 application/json` with the earlier digests:
  `defaultCountry` 20 B (`a8c04033…`), `recaptcha/key` 58 B (differs by host,
  `2018cee4…` com vs `a3e59c56…` trials), `messages/en` 22 B (`04868b50…`), with the
  byte-identical split preserved across `.com` and `-trials` for the first and third.
- **No `content-type` change, no new 404 shape, and no contradiction of the earlier
  record.** Area F's substantive conclusion (a third read path lives on every deployment)
  stands unamended. ⚠ **CORRECTED 2026-10-14 (area S independence audit): the word *corroborated*
  is withdrawn** — `AGENTS.md` §2.1 requires ≥2 independent sources and Area F and this pass
  are both this repository, so the count is **1**
  [findings-log/2026-10-14-pool-s-independence-audit/FINDINGS.md §3 row 29].
- `EU` is not re-probed; its record stays cited from the earlier pass.

Area F remains open: neither the caller nor the reachability question for
`patient-timeline` moves, and this pass claims no closure. Successors 1 and 2 above stand.
Area count unchanged.

#### Closing addendum (2026-10-14, pool worker F, issue #123): the caller question closes NEGATIVE, and the cause half stays blocked

**Derived from** 17 GETs across 7 hosts, **17 of a 40 cap**, GET only, ≥2.5 s same-host,
**controls first on every host**, `results.jsonl` in
`findings-log/2026-10-14-pool-f-timeline-caller/` ([FINDINGS.md](../findings-log/2026-10-14-pool-f-timeline-caller/FINDINGS.md)).
Every addendum above is preserved above, unedited.

**1. The letter's naming half: closed NEGATIVE, and structurally so.** Both **portal**
builds were re-fetched on their content-hashed asset names and both reproduce their
pinned anchors in full (`2a7fa8e7af519c2b…` 3 397 615 B; `a054555a0f22176e…`
3 410 666 B), so the corpus is the corpus. In **both** bodies these are **0**:
`patient-timeline`, `dialog-lite`, `app-patient-timeline`, `patientTimeline`, both
`personal.patient.timeline.*` spellings, `execute-api`, `prodous`, `/patient/`,
`clcloud`, `carelink.minimed` — and **each of the five 10-character gateway ids**
(`OBSERVED`). The reason is larger than the absence, and it settles the "look for a
server-side proxy in the portal bundle" half of the letter: **`personal.` is 4 hits
per build, and not one of the eight is a key of the 69-name patient document** (the
four literals are the same in each build; the byte offsets differ), while `hcp/patients` is 42 and
`hcp/configuration/public/` 15 — **neither build reads the patient configuration
document at all**, so the pointer is unreachable from that code and no proxy can exist
there to follow it. Counting **per build**, as `grep-out.txt` does: the `m2m` hit the
letter proposed is **1 in each build** (2 across both) and it falls in the **middle** of
`cum2me`, inside a leaked-password list; `baseUrl` is **2 in each build** (4 across both) and
every one is inside an embedded Pusher SDK, not a CareLink base (`OBSERVED`).

**2. The false-hit class, quantified — this is the pass's most reusable number.**
`timeline` scores **196** (66 + 126 + 4, 74 signatures) against `patient-timeline`'s
**0**, and all 196 are GSAP animation internals, Pusher SDK internals, Medtronic's own
snapshot-timelines **report** service (`hcp/reports/getSnapshotTimelinesRange`,
`TIMELINE_RANGE`), two leaked-password words, or one analytics label. Counting rule for
the census is in the log §6.5; a right-context pattern returns **189** and that figure
is a defect of the pattern, not a count.

**3. The letter's reachability half: closed NEGATIVE for GET, unauthenticated.**
The **`BLOCK 7` cells that had never run** ([`AWS-GATEWAYS.md`](../../findings-log/probe-2026-10-08/recon/AWS-GATEWAYS.md):240-242) ran: `v1/events` on
all three deployments, `logbook` on one, plus the `v1` prefix root. **All 11 of 11
`patient-timeline` cells** answer `403 MissingAuthenticationTokenException`, 42 B, one
digest `f249b63cb2fcb66b47e86f906c98f8fd912e82dd035b4e53d7e72fc1960cfd16` — which
reproduces this repo's published `f249b63cb2fc` **in full**, byte-identically, with the
certainly-absent control indistinguishable from every plausible path. Under Oracle A
that is **no matching GET route** on any of the three deployments. **Zero 404s in 17
requests** on both families, which observes the "404 is not in this vocabulary" clause
on this family directly instead of by analogy from `clcloud.*`. `dialog-lite` 500s on
all 4 cells with **one** body digest (`660f19c0…`, 36 B, **new** — the 2026-10-10 pass
recorded the size and no digest), and because the certainly-absent control is
byte-identical to the published root on both regions, **the 500 cannot discriminate the
path** — it is the catch-all's signature, exactly as recorded. Zero of 15 gateway
responses carry any `Access-Control-*`, and the header set is still the same six keys,
so this letter's "neither is browser-callable" premise is re-observed, not re-derived.

**4. What does NOT close, stated before the verdict rather than after.** **Which of the
three readings explains the `403`s — no routes deployed / routes for other verbs only /
the live stage is not `prod` — is unchanged and still blocked**, because separating them
needs an authentication attempt, which `AGENTS.md` §8 and §11 exclude. Four more cells
went into that dead end and did not move it; `docs/10` §1 carries the row and this
addendum does not supersede it. Also unchanged: *why* `dialog-lite` raises, and whether
the raw `…timeline.config.host` value is publishable — **a disclosure judgement for a
maintainer holding the value, not pre-committed here.** `docs/10` §1 gains a row for the
client question that survives this closure.

**5. One scope limit that travels with the negative.** Three builds exist and **only the
patient build has ever named the timeline at all** — and there every hit is an Angular
component selector, with `.featureEnabled` read for rendering and the gateway-host
sibling read by nothing (area V, 2026-10-13; `carelink.minimed.eu` is outside #123's
host set, so that record is **cited, not reproduced**). The negative's honest scope is
*no web caller in any of the three builds this repo has read* (**INFERRED**), which is a
claim about the corpus and not about every client the vendor ships.

**6. What was pinned, and what deliberately was not.** One `check` site in
`regression/hurl/05-public-config.check.sh`: the **EU** bulk document's
`keys | length` = 69, at **zero extra vendor requests** because that body is already
fetched at the top of the suite. `.com` and `-trials` already carried it; EU was the
missing third. **No `regression/hurl/` pin for the gateway cells** — the
`execute-api.*` hosts are in no suite, and adding them would widen the weekly drift
sweep's ~80-request vendor budget from a research pass (area M's log records the same
decision and the same reasoning). It pins the **count, not the set**.

**Measured spacing floor 2.239 s** on the millisecond `t_sent` series (**1** of 10 gaps
under the declared 2.5 s, **0** under the `>=2 s` floor) with **one negative duration**
— seq 9's `t_done` is 552 ms before its `t_sent`, the known corrupt-`t0` class of
`docs/09` §4, **no cause asserted**. The kernel body-mtime oracle puts the floor at
**2.866 s with 0 gaps under 2.5 s**, so no gap was actually short; that oracle is **not
re-derivable from a clean clone** (git does not preserve mtimes, bodies are transient),
and the load-bearing figure is the `t_sent` series, which reproduces from
`results.jsonl` alone.

#### Successor to area F — 1: the portal **lazy-chunk** corpus, the one place a caller could still be hiding

**Derived from what this session actually saw.** The two eager main bundles are now
swept clean — every service-identifying literal, including all five gateway ids, is **0**
in both, and neither build even contains the `app-patient-timeline` component selector the
patient build carries 5 times. So a caller inside a portal build, if one exists, is **not
in the eager main**. The place that leaves is the **lazy-chunk corpus of those two
builds**, which has never been swept for these tokens: area K's 211 chunks are the
**patient** corpus, and the 224 portal chunks are a different set
([area K addendum](#k-the-chunk-corpus-for-real-this-time)).

**Blocker:** **224 chunk requests**, which exceeds any single area's cap in this repo,
and the chunk corpus is not committed — so it is a **multi-pass, hash-ordered** job, not
a session. It also needs no new candidate list: the literal set already exists, gated,
in [`grep.sh`](../findings-log/2026-10-14-pool-f-timeline-caller/grep.sh).

**Closes when:** every chunk of **both** portal builds is hashed and swept with that
token list, both anchor gates and both named method gates applied per build, and the
result recorded **per build** — not as a pooled total, because the pooled form is what
let area E's per-deployment split and area W's deployment-specific 404 content-types go
unrecorded twice. **A negative (0 hits across all 224) counts** and is the likely answer.

**Assumptions (INFERRED):** that a timeline caller, if present in a portal build, lives
in a **lazy chunk** rather than in the eager main. That is **not** a general claim about
where callers live — it is forced by the fact that the eager main is now swept clean, so
this is the only place left in this corpus. **INFERRED, assumption stated:** that the two
portal builds share one chunk corpus rather than two; area A and area G recorded the
builds' eager assets and their `runtime.*`/`polyfills.*` names differ, so the chunk list
must be read from **each** build's own entry document rather than merged.

##### Result (2026-10-15, pool lane A, issue #131) — **the clinic build is closed; the support build is 16 cells and named**

**A negative, on the corpus, per build — never pooled.**

| build | cells swept | verdict |
|---|---:|---|
| **clinic `pow`** | **225 of 225** — complete | **0** on every service-identifying token: `patient-timeline`, `dialog-lite`, `app-patient-timeline`, `patientTimeline`, both `personal.patient.timeline.*` spellings, `prodous`, `/patient/`, `hcp/configuration/public/`, `execute-api`, `clcloud`, `carelink.minimed`, `baseUrl`, `m2m`, and all five gateway ids. **Area F's scoped negative is now unqualified for this build's lazy corpus.** |
| **support `cua`** | **16 of 225** — open | the same **0** on all of them, over 4 build-distinctive cells + 12 bridge cells |

Four tokens score and **all four are code, not pointers**: `Timeline` (104 clinic +
4 support) and `timeline` (44) are Angular state properties, service method names and
CSS classes (`allTimelinePeriod`, `getSnapshotTimelinesRange`, `[1,"timeline-chart"]`);
`personal.` (23 + 14) is i18n translation keys (`patient.invite.to.personal.message`) —
which is why `personal.patient.timeline.config` is **0** while the prefix scores;
`hcp/patients` (1 + 1) is one real call, `POST hcp/patients/checkPhoneNumber`, at the
**identical byte offset in both builds**. ⚠ **Every count on this line is
re-derivable from the committed ledger; every *byte offset* and quoted string is
not** — the response bodies were transient and are gone, so those reads are OBSERVED
as made and unverifiable now. The counts are what a later reader can check; the
offsets are what the pass read. [caveat applies to this paragraph's offsets and
quoted fragments; §1b carries the rule] Case-sensitivity control: in the busiest
chunk `Timeline`=84 / `timeline`=44 / `TIMELINE`=**0**. `m2m` — the token area F included
*expecting* a false hit — is **0** across all 240 chunk bodies. Both anchor gates pass
(`2a7fa8e7…` 3 397 615 B; `a054555a…` 3 410 666 B) and both method gates fire
(`hcp/configuration/public/`=15, `hcp/patients`=42 on each main bundle). 0 of 240 sweep
cells returned the 5 518 B SPA shell. **252 of a 260 cap, GET only**, measured in the log.
[source: findings-log/2026-10-15-area-f1-portal-chunks/FINDINGS.md §3, §5, §8b]

**The block's own INFERRED assumption is now answered — and the answer is "not
quite".** The two builds **do not** share one corpus and **are not two unrelated
ones**: they expose **the same 225 chunk ids**, **221** of them carrying an identical
content hash, the **4** that differ differing by **exactly five bytes** — the webpack
module id `37254` on clinic and `21981` on support, same five bytes in all four. The
4 pairs' token censuses are identical, so those 4 cells carry no content difference
between the builds. **12 of 12** sampled shared-hash cells fetched from the two
different hosts came back **byte-identical** — OBSERVED for those 12, and the
generalisation to the other 209 is **INFERRED** on one sample.
⚠ **What a reader can check, per claim:** the "exactly five bytes" rests on a body
comparison this repository does not retain (bodies are transient, `AGENTS.md` §7), so
**its exhaustiveness is not re-derivable from a clean clone**; what *is* re-derivable is
that each pair has equal `body_bytes` and different `body_sha256`, and that
`prefix + 5 + suffix` equals the body length exactly in all four. The log names every
such claim individually and ships a zero-request script for the checkable half
(§1b).
[source: findings-log/2026-10-15-area-f1-portal-chunks/FINDINGS.md §7, §8b]

**⚠ The limit that travels with this negative, and it is measured, not asserted.**
**A zero on a path-literal token list is a statement about literals, not about
reachability.** Clinic chunk `9481.6977c1a7bd7461f8.js` scores **0 on all 24 tokens**
— a count a later reader **can** re-derive from the ledger — and still calls the
config namespace twice: `getLogBookConfig(){return this.http.get($.C40)`
at byte 6 756 and `$.C40` at 6 798, with `hcp/configuration/public/` **absent** from
that body. ⚠ **Those two offsets and the quoted source are OBSERVED as read and are
not re-derivable from a clean clone** — the bodies are gone (§1b). The *scores* are
verifiable; the *offsets* are the pass's own reading of bytes this repository does
not retain. The point the offsets were read for does not depend on their exact
positions: what matters is that a chunk scoring 0 on every token makes a live call
into a namespace it does not spell.
The route literals live in the eager main bundle; the lazy chunk reaches
them through an imported constant. So `hcp/configuration/public/` = 0 in the lazy
corpus reads as *"the lazy corpus adds no new route literals"*, **not** as *"the lazy
corpus does not read the configuration namespace"* — and the same bound applies with
more force to every service-identifying token reading 0. The `carelink.medtronic.*`
and `carelink-support.medtronic.com` deployments were **not** probed: they serve the
same builds, but that is a claim about the bundles, and nothing here tested their
**chunk** URLs.
[source: findings-log/2026-10-15-area-f1-portal-chunks/FINDINGS.md §5d, §8]

**A discrepancy between this block and the claim, recorded rather than papered over.**
The block and issue #131 both name `carelinkhp.minimed.com` as the support host. **That
host is NXDOMAIN** — area A closed with "there is no `.com` `carelinkhp` variant: all
five `carelinkhp*.minimed.{eu,com}` names outside the baseline are NXDOMAIN" — and the
support build's own host is the one the pinned suite already reads. The pass used
`carelink-support.medtronic.eu` and named the swap in its log.
[source: findings-log/2026-10-12-area-a-clinic-portal-region/FINDINGS.md; `regression/hurl/05-public-config.check.sh:329–330`]

**⚠ And the denominator this repo already published for this corpus is 224 — it is
225 minus one.** `docs/10`'s config-pointer row and this page's own text (found by
`git show ab28f58:docs/11-suggested-research-areas.md | grep -nF '224 lazy chunks are mined for endpoints and field names'`,
**1 hit**, anchored to the `ab28f58` object (line 1254) so the answer cannot drift as this
page is edited) both say "224 chunks".

Run *in-tree*, the same search matches more than the target — **and the in-tree count is
deliberately not published as a number.** This paragraph itself quotes the pattern (in the
command above and in the table below), so the in-tree count is a function of the text
describing it and changes with every edit here; publishing one would be false after the
next commit, which is the very defect this passage documents. The merge-base form above is
fixed at 1; run the in-tree grep yourself if you need the current figure.

| site | what it is | how to resolve it | merge-base |
|---|---|---|---|
| this page, first command slot | self-quote #1 | `grep -nF '224 lazy chunks are mined for endpoints and field names' docs/11-suggested-research-areas.md` | — (not present at ab28f58) |
| this page, second command slot | self-quote #2 | same grep | — (not present at ab28f58) |
| the pre-existing 224 sentence | target prose (section K) | `git show ab28f58:docs/11-… \| grep -nF '224 lazy chunks are mined…'` | 1254 |

**The pattern is the
longer one on purpose, but lengthening does not make the in-tree count stable:** this page
quotes the pattern in its own command slots and its own table, so the in-tree count tracks
this text. The fix that works, and the one the table below records, is the merge-base
qualification `git show ab28f58:…`, whose result set cannot see this pass's own text. The 2026-10-08 record those came from is explicit:
the
runtime holds a **225-entry** map, it built filenames as `<id>.<hash>.js` — the **id**
form — and *"**224 fetched. One entry returned the SPA fallback**"*. The entry it lost
is the one whose id form is not the name `f.u` emits: id **2076**, which `f.u` maps to
`common` (this ledger, OBSERVED on **both** builds — `2076.<hash>.js` → 200 `text/html`
5518 B, `common.<hash>.js` → 200 `application/javascript`). This pass requested the
**emitted** names and got **225 of 225** with **0** fallbacks. **Use 225.** Which entry
the 2026-10-08 run lost is **INFERRED** — that record says "one entry" and does not name
it — and `docs/10` is not this pass's lane to correct, so it is carried as successor §1c.
[source: findings-log/2026-10-15-area-f1-portal-chunks/FINDINGS.md §8a]

#### Successor to area F — 1a: the support build's **209 unswept** chunks — the one place the negative can still be wrong

**Derived from the pass above, not from a topic.** The clinic corpus is closed; the
support corpus was swept to **16 of its 225 cells** because 225 + 225 exceeds any cap
in this repo. The remainder is not "the rest of the corpus" in the abstract — it is a
specific, enumerated set: every support-host cell for the **221 shared-hash ids** except
the **12** already drawn at stride 18, i.e. **209 cells**, all on one host.

**Blocker:** **209 requests** on `carelink-support.medtronic.eu` at 2.5 s (≈ 9 min), and
nothing else. **Zero requests to plan it and zero to resume it:** `chunk-map.tsv` is
committed, `probe.sh` reads the ledger's highest `seq` and continues at 253, and
`plan-cells.py` regenerates the cell list. **The two anchor gates do not need re-sending**
— they were sent on this build in the same ledger and passed.

**Closes when:** the remaining **209** support cells are fetched, discriminated on
content-type, and swept with the same 24 tokens — and the bridge sample grows from
**12 of 221** to **221 of 221**, which converts §6a's **INFERRED** content-identity
step into an **OBSERVED** one. **Either outcome counts:** if the 209 are byte-identical
to their clinic counterparts the support negative closes by arithmetic *and* by fetch;
if any one of them is not, this repo has a content-difference-without-contenthash case
and the support negative needs re-stating. **A negative counts.**

**Assumptions (INFERRED):** that the support host serves its 225 chunk URLs at all.
Nothing in this repository has ever fetched one — this pass fetched **16** and all 16
answered `application/javascript`. The other 209 rest on the support runtime naming
them, and a name in a document is not a served file (`AGENTS.md` §6 item 2). That is
the whole reason the remainder is a successor and not a footnote.

**Duplicate test, run and recorded** (`CONTRIBUTING-research.md:195-200`, "grep both
first"). Commands and hit counts, at head:

| where | command | hits | verdict |
|---|---|---:|---|
| `docs/10` §1 | `grep -ciE '209 cells\|209 chunk\|unswept' docs/10-open-questions.md` | **0** | not there |
| `docs/10` §1, wider | `grep -ciE 'portal .*chunk' docs/10-open-questions.md` | 4 | all incidental — lines 61 (false-hit word list), 63 (config-pointer row), 83 (CHUNK-CORPUS citation), 92 (chunk identifier in a deployment row) |
| Closed table | `awk '/^## Closed areas/,0' docs/11-suggested-research-areas.md \| grep -ciE -e '\b209\b' -e unswept` | **0** | not closed |
| this page | `grep -n '\b209\b' docs/11-suggested-research-areas.md` | **0 at `origin/main`** — every hit lands inside this pass's inserted block, none in the pre-existing text (1 in the Result paragraph above, the rest in successor 1a). The **head count is not published**: it moves with every edit above the block; run the grep yourself. It is **inherently unstable** — delete the block (or the finding) and the count returns to its pre-pass 0 — so it is recorded as a property ("every hit is inside this pass's own text"), not as a fixed number | not a duplicate of itself |

**Non-duplicate, recorded.** ⚠ One related hit **is** a real staleness and is **not**
this successor: `docs/10`'s config-pointer row still reads *"The one thing a web sweep
could still add is the portal lazy-chunk corpus (**224 chunks**, never swept for these
tokens)"*. **224 is the wrong denominator** — it is 225 minus the one entry lost to
the `f.u` id-vs-name form, and the pass that swept 224 said so and left the fallback
unexplained ([findings-log/2026-10-15-area-f1-portal-chunks/FINDINGS.md §8a]). That row
now points at a corpus this pass swept, so it needs restating; **`docs/10` is not this
pass's lane to edit** and the correction is named in §1c below.

#### Successor to area F — 1b: the `$.C40` mechanism — **how many of this repo's "0 hits" sentences are negatives over literals?**

**Derived from the demonstration in §5d, which is the transferable part.** One chunk in
the corpus just closed scores 0 on every token and makes two live calls to the
configuration namespace through an **imported webpack constant** whose literal lives in
a different file. That is a *mechanism*, not an anecdote, and it applies to any negative
in this repository that was produced by grepping for path literals: area F's two
portal bundles, area P's `system.logbook.entry.validation.config` literal (which area K
later found **has** a consumer, in lazy chunk 9481 — "no adjacent field definition" was
true and the conclusion drawn from it was not), area V's `NGP`/`guardian` dictionary
noise, this pass's own `hcp/configuration/public/` = 0.

**Blocker:** **zero requests**, and the first half needs none at all. The eager main
bundles already name their route literals (15 `hcp/configuration/public/` occurrences
per bundle); what is missing is the **reverse index** from each lazy chunk back to the
constants it reads. Countable offline from a corpus that has to be fetched once anyway,
and the 225 chunk bodies are re-fetchable from the committed `chunk-map.tsv`.

**Closes when:** every "0 hits in N chunks/bundles" sentence in `docs/` is either (a)
carries a `Content-Type` and anchor gate, **and** (b) says whether the corpus it swept
carries route **literals** or route **call sites** — and the ones that conflate the two
are corrected with the original wording preserved. **A negative (every sentence already
distinguishes them) counts.** The second half — do the `docs/` claims distinguish them —
is a counting-rule check over committed text, no requests.

**Assumptions (INFERRED):** that a lazy chunk reaches a service either by carrying a
literal, by reading an imported constant, or by assembling the URL at run time from
config — and that the third of those is rare. **The third is not tested and is not
claimed**; it is named because it is the residual that no corpus sweep of any size can
reach, and a reader deserves to know it is still there after 225 chunks read clean.

**The second half is now concrete, and it is a rule about what a corpus pass must
commit.** Verification of the pass above showed the failure this section is about: its
per-hit **byte offsets** and quoted minified source — and the exhaustiveness of its
"exactly five bytes" — are **not re-derivable from a clean clone**, because the bodies
were transient (`AGENTS.md` §7) and were written to a `mktemp -d` that no longer exists.
The *counts* are re-derivable and a stranger can check them; **the reads behind the
counts cannot be checked at all.** That is a gap between what a pass asserts and what a
later reader can verify, and it is cheap to close on the next sweep:

> **A corpus pass commits a per-cell evidence index at capture time** — the offset list
> plus a ~160-byte excerpt for every non-zero hit, and a fixed-width window around each
> distinct-pair divergence. Roughly 30 KB for this corpus, no vendor secret, and it makes
> the literal-vs-code reads and the byte-difference claims checkable from a clone.

The pass above cannot be back-filled without re-fetching 240 bodies, which would break
its closed request accounting; its log names every affected claim individually instead
([source: findings-log/2026-10-15-area-f1-portal-chunks/FINDINGS.md §8b]), and ships a
zero-request `verify-derivable.py` that machine-checks the half that *is* checkable.
**Closing this means the next corpus pass writes the index while the bodies are on disk.**

#### Successor to area F — 1c: the **224** two pages still publish for a **225**-chunk corpus

**Derived from the pass above, and it is a denominator, not a topic.** `docs/10`'s
config-pointer row and this page's own text (`git show ab28f58:docs/11-suggested-research-areas.md
| grep -nF '224 lazy chunks are mined for endpoints and field names'`, **1 hit at
merge-base `ab28f58`, line 1254** — the in-tree count is not published (this page quotes
the command, so the count tracks it; see the note above)) both say the portal lazy-chunk
corpus is **224** chunks. **The count is pinned to merge-base so this passage cannot be
counted into it.** The 2026-10-08 record
that number came from is explicit about
why:
*"holds a 225-entry webpack chunk map … so the filenames are `<id>.<hash>.js`"* and
*"**224 fetched. One entry returned the SPA fallback**"* — it built URLs in the **id**
form, and the one entry whose id form is not the name `f.u` emits is id **2076**, which
`f.u` maps to `common`. This pass re-derived both builds' `f.u`, requested the emitted
names, and got **225 of 225** with **0** fallbacks.

**Blocker:** **zero requests.** Both figures are already in committed text; the question
is which is right, and the arithmetic answers it. **Attribution of the lost entry to
2076 is INFERRED, not tested** — the 2026-10-08 record says "one entry" and does not
name it.

**Closes when:** `docs/10`'s row and this page's own "224 lazy chunks" sentence both read
**225**, with the 224 named as the id-form count and the `f.u` substitution named as the
cause; and area K's §8 successor — *"the 224-chunk clinic sweep had 'One entry returned
the SPA fallback' — never explained"* — is answered by that same sentence. **A negative
counts.**

**Assumptions (INFERRED):** that the unnamed fallback entry is id 2076 rather than a
fetch error, resting on three OBSERVED facts (the id form answers the 5 518 B shell and
the `common` form answers `application/javascript`, on **both** builds — this ledger,
seq 4/5/11/12 — plus `f.u` naming `common` for 2076 and no other id) **and** that
assumption. **Not claimed.**

#### Successor to area F — 2: the new pin's stated limit — the 69-key **count** is not the **set**

**Derived from the pin this pass added.** `regression/hurl/05-public-config.check.sh` now
asserts `keys | length` = 69 on all **three** patient deployments, which completes the
third copy the claim asked for. What it deliberately does **not** do is pin the key
**set**: a deployment that swapped one key for another would keep 69 and pass. Area E
proved the sets identical on 2026-10-13 from its own sweep, and that proof is
**log-level and not re-derivable from a clean clone**, because the response bodies were
transient by design.

**Blocker:** none for the artefact, **zero requests, for the next sweep that is reading
the bulk document anyway.** The bodies are already on disk inside
`05-public-config.check.sh` at the point the three key-count checks run, so a committed
`keys.tsv` — the **sorted key list** per deployment, which is a *vocabulary* and not a
value — can be emitted from the same parse with **no additional request** and no value
disclosure. Area E's `findings-log/2026-10-13-area-w-per-key/keys.txt` is the EU list and
it **already exists**, so the EU row needs nothing new; only `.com` and `-trials` do.

**Closes when:** the suite emits a sorted per-deployment key list alongside the count, or
the prose says plainly that the count is a count and the set claim is log-only. **Either
counts as closed.**

**Assumptions (INFERRED):** none beyond the quoted addenda — this is arithmetic about a
file this repo controls, and the only judgement is whether a *vocabulary* is publishable
when the *values* are held back, which this row does not pre-decide.

#### Addendum (2026-10-15, from pool worker F, issue #123, round 13) — successor: a `^`-anchored scrub pattern cannot work in the gate's diff path

**Derived from this pass, not from a topic**, and **it is a gate finding rather than a
research one**, which is why it is a successor and not a fix.

**What is missing.** `scripts/research-gate.sh:108` builds its **diff-mode** subject text
with a `git diff -U0 | grep '^+' | grep -v '^+++'` construction, which **keeps the
leading plus**. Every line the gate greps on that path therefore begins with `+`, so **a
`^`-anchored pattern can never reach its token.** Measured on the one anchored net in the
list:

| control placed… | `grep -cEi` against the reCAPTCHA pattern |
|---|---:|
| bare, at line start | **1** |
| mid-line | **0** |
| **at line start behind a leading `+` — diff mode** | **0** |

**Which nets, exactly.** `reCAPTCHA site keys` is the **only** `^`-anchored pattern in
`scripts/scrub-patterns.txt` — 1 anchored of 10, checked with the gate's own
`IFS='|' read` parsing. The other nine are unanchored. **CI runs bare
`./scripts/research-gate.sh` — diff mode — on every pull request**
([`research-gate.yml`](../../.github/workflows/research-gate.yml):43-44), with `--all`
running only on push to `main` (`:47`). **So the net is dead on the path every PR is
checked by and live only on the post-merge path.**

**The distinction that is easy to get wrong, recorded because it is the useful part.**
`machine-specific paths|(^|[^a-z])/[hH]ome/…` **does** fire behind a `+`, because
`[^a-z]` matches the plus. **⚠ Corrected 2026-10-15 (area D, #134): this addendum stated that as a two-way
division — anchored at `^` versus has an alternative accepting any non-letter — and it
is not a partition.** The right-hand side is satisfied by **1 of the 10** patterns; the
other eight are unanchored *and* carry no such alternative, and are live anyway. The
rule is **one-directional**: **a net is dead behind `+` iff every alternative is
`^`-anchored.** Carrying a non-letter alternative is one *sufficient* way to satisfy
that, not a necessary one. The mechanism above is unchanged and survives the correction
— it is the partition that was wrong, and all ten patterns are re-classified against the
one-directional rule in [findings-log/2026-10-15-gate-scrub-diffmode/FINDINGS.md §3b].
**The pattern list records which is which for none of its ten entries.**

**Blocker:** **both** available repairs touch the gate's own machinery — strip the `+` at
`research-gate.sh:108`, or rewrite the pattern to tolerate a leading `+` — and `docs/09`
§4 records that widening or altering a check **in the same PR the check passed** is a
maintainer decision, not a research pass's. **Neither is attempted here.**

**Closes when:** either the `+` is stripped from the diff-mode subject lines, **or**
`scripts/scrub-patterns.txt` records per pattern whether it survives a leading `+` —
**and a control exists for each of the ten that proves the answer**, because a net whose
liveness is unstated is a net whose liveness nobody notices has stopped.

**Assumptions (INFERRED):** that `:108` is the only `+`-prefixed subject path — `staged`
mode at `:104` uses the same construction and `--all` at `:106` uses `cat`, so that is a
reading of the three lines together, not of `:108` alone. Zero requests.

> ⚠ **CORRECTED 2026-10-15 (area D, #134) — both halves of the sentence above are false.**
> Read at the file: `:104` is
> `[ -f "$f" ] || continue`, a guard inside the per-file loop, **not** the `staged`
> construction, which is at **`:107`**; and `:108` is **not** the only `+`-prefixed path —
> `:107` is a second one with identical semantics, so the count is **2, not 1**. The
> `105,109` block carries exactly 2 occurrences of `grep '^+' | grep -v '^+++'` and exactly
> 1 `cat "$f"`, counted rather than read. The premise this sentence supports — *"dead on the
> path every PR is checked by"* — also **understates** it: the anchored net is dead on
> **two** paths, `diff` **and** `staged`, and is only partly live in `--all`. Correction,
> counts and the cell table: the next addendum on this page (area D, §"The correction"), and
> [findings-log/2026-10-15-gate-scrub-diffmode/FINDINGS.md §1a]. The correction is also
> appended to the log this addendum came from
> ([`FINDINGS.md`](../findings-log/2026-10-14-pool-f-timeline-caller/FINDINGS.md),
> `## Correction (2026-10-15)`), so the correction is reachable from the source as well as
> from here. **The superseded wording is retained above rather than deleted** — the same
> convention the Closed-areas L row uses.

#### Addendum (2026-10-15, area D, pool lane D, issue #134) — the measurement branch: a control cell for each of the ten

**The close condition's second branch is now met on the measurement side, and the area's
stated assumption above is corrected by the measurement rather than inherited.**

**What was measured** [source: findings-log/2026-10-15-gate-scrub-diffmode/FINDINGS.md §3].
Every verdict comes from running the gate's own bytes — the `84,94` subject selection, the
`105,109` `ADDED` construction and the whole `114,136` matching loop are `eval`'d out of
`scripts/research-gate.sh` at run time, not re-implemented — against a scratch git repo
holding synthetic lines, in **all three modes**. **45 cells × 10 patterns × 3 modes = 1350
rows.** Zero requests.

| | `--all` | `staged` | `diff` |
|---|---|---|---|
| patterns **live** (≥1 cell fires) | **10 of 10** | **9 of 10** | **9 of 10** |
| patterns **dead** (0 of 4 cells fire) | 0 | **1** | **1** |
| patterns **undecidable** | 0 | 0 | 0 |
| dead net | — | `reCAPTCHA site keys` | `reCAPTCHA site keys` |

**The correction.** The assumption recorded above was that `:108` is the only `+`-prefixed
subject path and that `staged` sits at `:104`. Both are wrong: **`:107` is a second
`+`-prefixed path** with identical semantics, and `:104` is `[ -f "$f" ] || continue`, not
a construction. Counted rather than read — the `105,109` block holds **exactly 2**
occurrences of `grep '^+' | grep -v '^+++'` and **exactly 1** `cat "$f"`
[FINDINGS.md §1a]. So the anchored net is dead on **two** paths, not one, and the area's
premise *"dead on the path every PR is checked by"* understates it.

**The finding the addendum did not have: the `$` end-anchor is the larger restriction.**
`reCAPTCHA site keys` is anchored at **both** ends, so it does not merely miss a leading
`+` — it misses **any token not alone on its line**, in `--all` mode too. Cell-for-cell: 1
of 4 in `--all` (bare at line start), **0 of 4** in `staged` and in `diff`
[FINDINGS.md §3a]. A key inside a captured response body — where a key of that shape
actually arrives — would not be caught by this net **in any mode**.

**The distinction the addendum named is now measured, not asserted — and restated, because
the phrasing it used is not a partition.**
`machine-specific paths` fires in **4 of 4** cells in **all three modes**, including behind
a leading `+`, because `[^a-z]` accepts the plus. ⚠ **Corrected 2026-10-15 (verifier round
1, F3):** the area-F addendum stated the dividing line as a two-way partition — anchored at
`^` *versus* has an alternative accepting any non-letter — and **1 of the 10** patterns
satisfies its right-hand side. The other eight are unanchored and carry no such alternative,
and are live anyway. **The rule is one-directional: a net is dead behind `+` iff every
alternative is `^`-anchored.** A non-letter alternative is one *sufficient* way to satisfy
that, not a necessary one — and that is the only correction, because the mechanism is
unchanged and was independently re-derived rather than read back. All ten patterns are
re-classified against the one-directional rule in [FINDINGS.md §3b], and the pattern file
records which is which for **none** of its ten entries.

**Two zero-means-different-things cells** are recorded so a later reader does not merge
them [FINDINGS.md §3c]: an added line whose **content** starts with `++` renders as `+++…`,
is indistinguishable from the `+++ b/file` header, and is **dropped whole** by the
`^+++` filter — no pattern ever sees it. And the loop's only per-pattern carve-out
(`:123-124`) is currently **not load-bearing**: the documented machine-path example reads
**0** with the carve-out and **0** without, and **0** either way across the real `--all`
text at `ab28f58` (206 files, 43,687 non-empty lines).

**Blocker:** the maintenance decision the area already names — strip the `+`, or record
per pattern whether it survives one, or de-anchor the one anchored net. **Not attempted
here**, for the `docs/09` §4 reason above.

**Closes when:** that decision is taken and recorded, **and** the committed control set
(`findings-log/2026-10-15-gate-scrub-diffmode/`) is re-run against it — the harness exits
non-zero if the gate's blocks move, and its mutation test fails if the measurement stops
responding to the thing it measures.

**Assumptions (INFERRED):** that `research-gate.yml:43-44` — bare
`./scripts/research-gate.sh`, i.e. diff mode — is the mode a pull request actually gets.
It is the ordinary case, but `research-gate.sh:76-82` **fails closed into `--all`** when
`origin/main` is unresolvable, and this pass observed no CI run. The verdict table is
therefore stated **per mode** and is not generalised.

> **Update, same day, after the branch was pushed.** The one CI run this PR triggered —
> `pull_request`, head `research/D-scrub-diffmode-control`, SHA `33895ee` — printed
> `--- leak scan (mode: diff) ---` as its own mode line and concluded `GATE PASS`
> [source: findings-log/2026-10-15-gate-scrub-diffmode/FINDINGS.md §4]. So for **one**
> same-repository pull request the mode is **OBSERVED**, not inferred, and the `diff`
> column above is the column that PR was actually checked by. The remaining
> INFERRED part narrows to the `push to main` event and to a **fork** pull request, and
> successor 1 below is re-scoped to exactly those.

#### Successor to the area-D addendum — 1: which mode do the *other* two events get?

**Derived from what this pass could not establish.** Every verdict above is per-mode. The
`pull_request` case is now **observed once** (`FINDINGS.md` §4), which retires half of this
row: what is left is the event CI takes when the diff is gone, and the checkout shape that
makes the gate change mode without saying so.

**Blocker:** none — zero requests. The gate prints its own mode at `:73`, and
`research-gate.yml` keeps logs.

**Closes when:** the `--- leak scan (mode: …) ---` line has been read from a real
`research-gate` run of **each** remaining shape — **`push` to `main`** (which `:47` routes
to `--all`), and a **fork** pull request or any checkout where `origin/main` does not
resolve, which is where `:76-82`'s fail-closed fallback decides the mode on its own. **A
fork PR may not be constructible without an outside contributor's consent, and if so that
counts as the answer with the reason stated.** Any other mode observed counts equally.

**Assumptions (INFERRED):** that `actions/checkout@v4` with `fetch-depth: 0`
(`research-gate.yml:15-17`) leaves `origin/main` resolvable for same-repo pull requests.
⚠ **Corrected 2026-10-15 (verifier round 2) — two axes, and only one of them moved.**
This row said "supported by one observation … which is one source". Both halves were right
and the *observation* half then went stale: a second run (`38766246282`, head `d86a21b`,
`GATE PASS`) has since printed the same `--- leak scan (mode: diff) ---` line, so **two
runs are observed (`38762357329`, `38766246282`) from one source — this repository's own
CI**. `AGENTS.md` §2.1's **independence count is unchanged at 1**: two runs of the same
workflow file, on the same event type, in this repository, are two samples of one source
(`docs/03` §3a.4), so *independently* is still unavailable. The count that was wrong was
the observation count, and saying "once" about it was `AGENTS.md` §6 item 1 — a sentence no
reader could point at. **The INFERRED boundaries are untouched by the second run:** the
`push to main` event, a fork PR, and any checkout where `origin/main` does not resolve.
Not load-bearing: the verdict does not depend on it.

#### Successor to the area-D addendum — 2: a per-pattern liveness column, and the fact that no control set can be committed

**Derived from the control set this pass committed.** Two facts fell out of building it: one
is new to the page, the other restates the addendum above.

⚠ **Partly a restatement, and said so.** The **close condition** below is not new *in shape*
— the addendum's F3 already asks for the same thing: annotate each pattern's `+`-liveness
**and** ship a control that proves the answer. It differs in strength: F3 asks for a control
for **each of the ten**, this successor for **one in ten** (a sample), and it adds the escape
hatch that fact 1 forces — the control must be assembled at run time, because a committed
instance would make the gate fire on itself. Of the two facts below, **only the first is new
to the page** — that no control set can be committed at all; the second (that the `^+++`
filter is positional) is **carried forward** from **this pass's own addendum above**, not
from F3: it is new to `main`, and it is only *not new* to a reader who has just read this
page. Restated here only to keep this successor self-contained. A maintainer reading only
`main` has seen the close condition's **shape** (F3) and neither fact; one reading this page
has seen all of it.

1. **All ten nets are self-referential**, so no control set can live in the repo as a
   fixture: an instance that matches pattern P is by construction text that P matches, and
   committing one makes the gate fire on its own control. The one literal pattern is worse —
   its only positive instance is the published value itself, which only the file the gate
   exempts at `:67` may hold. This pass therefore **assembles instances at runtime from
   fragments** and commits only counts (`cells.tsv`). The generalisable form: *a gate whose
   nets are self-referential has no testable fixture form, so "add a fixture" is not an
   available repair for any of them.*
2. **The `^+++` filter is positional** (`FINDINGS.md` §3c): a line whose content begins with
   `++` is deleted before any pattern sees it, and a scan that reports only counts cannot
   distinguish that from a pattern that did not match.

**Blocker:** none — zero requests, all local.

**Closes when:** `scripts/scrub-patterns.txt` carries a **per-pattern column** stating
whether the net survives a leading `+`, and one in ten patterns ships a committed control
that runs **without** writing an instance into a scanned file — e.g. instances derived from
the exempt pattern file at run time, which is what this pass does and which works. **A
negative counts**: if the maintainer judged per-pattern annotation unnecessary because
`:108` is simply fixed, this successor is moot and should be closed with the reason.
⚠ **The column must state the one-directional rule, not the two-way one this pass first
published.** A column whose test is *"anchored at `^` versus has an alternative accepting
any non-letter"* leaves **8 of 10** entries unclassified (verifier round 1, F3): the test
is **dead behind `+` iff every alternative is `^`-anchored**
[`FINDINGS.md` §3b], which classifies **10 of 10** with **0** disagreements. **Also here:
the `docs/09` §4 `.txt` extension-blindness row (`docs/09:206`) has counts measured at
`cd626d6` that are now stale, and it is annotated in place rather than re-derived** — its
own counting rule is `git ls-files '*.txt'` against `git ls-files '*.md' '*.yml' '*.yaml'
'*.sh' '*.hurl'` minus the two excluded files, so whoever picks it up has the command
already written down and this pass does not vouch for `31`, `126` or `1216`.

**Assumptions (INFERRED):** that a per-pattern annotation is cheaper than the alternative
of stripping the `+`. The opposite is defensible — the area records both repairs, and this
row does not argue for one.


## Tier 2 — cheap, moderate value

### P (closed 2026-10-13) Recover the request schema from the vendor's own app, statically

Half of `docs/10`'s open questions — the `markers[]` per-entry field names, the
`deviceFamily` casing, the NGP alarm vocabulary — are blocked on *one
authenticated response each*. The request side of those shapes is compiled into
the CareLink app itself, and no pass has ever decompiled it: the mobile-artifact
note is store metadata only, and the 2026-10-08 app-emulation pass worked from
the public JS bundle and third-party clients
([findings-log/medtronic-carelink-2026-07-21/09-mobile-artifacts.md];
[findings-log/probe-2026-10-08/APP-EMULATION-RESEARCH.md]).

**Blocker:** the artefact is not in the repo and no static-analysis tooling has
been run against it. Provenance of a store download is a decision to record, not
an assumption to make (the APKPure mirror is already recorded as
medium-confidence), and `docs/09`'s no-source-maps finding means the JS path
yields little.

**Closes when:** the logbook/marker entry payload and the family-matching
predicate are recovered verbatim from the app artefact with a named static
tool, written to a dated findings-log with the tool, version and evidence class
recorded — enough to answer the *shape* half of at least one token-blocked row in
`docs/10`, even though the response half stays token-gated. A negative — the
shape is not recoverable from the artefact — is equally a result.

**Assumptions (INFERRED):** that a static pass recovers schema the live surface
gates; the bridge's own notes show the app's family-matcher is five tokens wide
while the vendor ships a device it cannot match, which is the shape of a schema
that static analysis *would* settle — but no one has tried, so the recovery rate
is unknown.

> **Area Q is CLOSED — see the Closed table at the foot of this page and
> [`docs/03`](03-discovery-and-versions.md) §3a.** Closed 2026-10-13 on the area's
> **second** close condition — *recorded as community-reported-and-unverifiable, with
> the reason* — because the boundary is a **request-body** field and `AGENTS.md` §11
> permits no vendor POST beyond the two already-pinned public-`client_id` requests.
> The **mechanism** resolved in code; the **boundary values** did not and cannot be
> resolved from outside the project. **The pass spent 21 requests against a cap of
> 20** — a one-request overrun, disclosed in the log and not smoothed away. **The cap
> was restated to 21 by owner authorisation on 2026-10-13, after the pass
> completed**, so the log's accounting line now reads `21 of a 21 cap`; the declared
> 20 is kept readable beside it, in the log's `## Correction (2026-10-13)`. The
> restatement equals the spend exactly and grants no slack.
>
> **The area as written, kept verbatim so the correction stays readable.** One of the
> two claims it rests on no longer holds. **⚠ Withdrawn:** *"corroborated by a xDrip
> maintainer on PR #4711"*. Read at the artefact, PR #4711's three comments are the
> boundary table (**by the same author as the README that repeats it**), a question,
> and an approval that does not restate or retest the boundary values — so the table
> is **one source stated twice**. **Still stands:** the table is SOURCE-PUBLISHED and
> author-reported, and the *mechanism* — that `appVersion` is a **body** field — is
> SOURCE-OBSERVED at `CarlosJPV src/carelink/cumulus.ts:146` @ `0180b89`, which this
> pass read and which is byte-identical at branch head. **Not re-verified here:** the
> xDrip half, `CareLinkClient.java:664`. Original text:
>
> > **Added 2026-10-11.** `docs/00` and `docs/03` describe the **discovery-path**
> > version axis (`android/3.6`–`3.8` → Auth0 + cumulus v13). Third-party source
> > review found a **second, independent axis on the request body** that our docs do
> > not cover: `POST {baseUrlCumulus}/display/message` rejects `appVersion ≤ 3.6.9`
> > with **HTTP 206 `{"message":"Upgrade application"}`** and accepts `≥ 3.7`.
> > (SOURCE-PUBLISHED — author-reported table, corroborated by a xDrip maintainer on
> > PR #4711. The *mechanism*, that it is a **body** field, is SOURCE-OBSERVED at
> > xDrip `CareLinkClient.java:664` and `CarlosJPV src/carelink/cumulus.ts:146`.)
> >
> > The two axes are constrained in **opposite** directions: the discovery URL must
> > stay **≤ 3.8** (3.9+ falls back to a legacy no-Auth0 config), while the body
> > `appVersion` has **no upper bound**. A client can be correct on one axis and
> > broken on the other.
> >
> > **Why it's ours:** nobody publishes a two-axis compatibility matrix. Every client
> > re-derives it independently — `CarlosJPV`, xDrip and this ecosystem's own
> > `discovery.ts` each found one half.
> >
> > **Closes when:** the two axes are documented together in `docs/03` — **or**
> > recorded as community-reported-and-unverifiable, which is a legitimate close.
> >
> > **Assumptions (INFERRED):** that the body gate and the discovery axis could move
> > independently. No client dates either change, so no drift timeline is asserted.
>
> **What the pass added that the area did not ask for:** the two constraints
> **intersect in exactly `{3.7, 3.8}`** *for the `X.Y` forms the discovery axis has
> been probed at* — `3.7.0`/`3.8.0` clear the body gate but are unobserved on the
> discovery path, since no `X.Y.Z` cell was ever probed — and the one client whose
> source is readable feeds **a single constant** into both axes, correct only because
> `3.8` is in that window, so raising it to `3.9` breaks the discovery axis
> *silently*, on a path this repo already pins. That is a bridge-facing coupling and
> it is now a `docs/10` §1 row.

#### Addendum (2026-10-13, from area P): static schema recovered in part — issue #80

The successor pass re-read the hash-pinned patient bundle (`0fb4fbd4…`, 3,417,255 B) and
its 211 lazy chunks, plus both portal bundles (`2a7fa8e7…` / `a054555a…`), and moved
two of the three targets forward:

1. **Per-entry logbook payload shape (a).** Lazy chunk `k-9799-ae484032a07c9d4f-js.b`
   (176,766 B; sha256 `713cd95f…`) carries the client's submission object:
   `entryTs`, `type`, `id`, `comment`, plus `sensorInsertionInfo { sensorLocation,
   otherSensorLocation, timeCapUnscrewed }`, `removalInfo { sensorLocation,
   otherSensorLocation, removalType, removalReason, removalDescription }`,
   `physicalDisturbanceInfo`, `medicationInfo`, `adhesiveAndTapeInfo`, and a dynamic
   `attributes` bag. **Casing correction:** the wire field is **`timeCapUnscrewed`**
   (capital C); docs/10 row 46's `timecapUnscrewed` is wrong. `sensorInsertionLocation`
   is a *form-control* name; the serialized field is `sensorInsertionInfo.sensorLocation`.
2. **`deviceFamily` routing-discriminator casing (b).** The patient bundle defines a
   client-side enum `{ BLE: "BLE", BLE_X: "BLE_X", SIMPLERA: "SIMPLERA",
   SIMPLERA_X: "SIMPLERA_X", GUARDIAN: "GUARDIAN" }` (module 45559, byte 1,723,245) and
   matches `deviceFamily` with `.startsWith(...)` (byte 2,964,121). Area R's first
   observed candidate: uppercase `BLE`/`SIMPLERA`/`GUARDIAN`. Still client-side, so the
   live wire string stays token-gated (`docs/10` row 37).
3. **`system.logbook.entry.validation.config` schema (c)** stays **not recoverable**:
   bundles and all 211 chunks carry the route literal only (offsets 2,768,979 /
   2,769,017) and the patient config-key registry names it without a field set. The
   configured key now also has a name in the patient map (`yt`, `gt.logbookConfiguration`).
   Partial compensating result: NGP `lastAlarm.code` is a **number** on the wire,
   rendered zero-padded by the UI (chunk byte 76,305), which settles the representation
   half of `docs/10` row 39. The NGP alarm *vocabulary* itself (#84) stays unpublished.
   `alarmCode` occurs zero times across patient + portals + 211 chunks.

**Close position:** area P closes on this evidence. Prior negative
(`findings-log/2026-10-13-area-p-static-schema-recovery/FINDINGS.md`) is preserved as
the first pass; the successor's log is
`findings-log/2026-10-13-area-p-static-schema/FINDINGS.md`. The first pass's
disclaimer about store metadata and no mobile binary stands and is not weakened.

**Successor (attached, not a new letter):**
- Mobile side (still attached): a sourced, hash-verifiable mobile artefact or a
  clinician token, for live wire values and the validation-config field set.
- Attached to area F: if a fuller NGP alarm vocabulary is recovered, its
  patient-facing i18n shape (`messages/{lang}`).

**Assumptions (INFERRED):** the web bundle represents enough of the mobile client for
the casing/form facts above; area J is the known counter-example where build location
is not stable across builds, so deviceFamily wire strings are candidates, not
confirmed live values.


### R (closed 2026-10-14) Reconcile the `deviceFamily` correction against the client consensus

> **CLOSED 2026-10-14 — on the area's second close condition, and the close is a
> negative.** Issue [#124](https://github.com/NovaLux12/carelink-api-research/issues/124),
> **0 requests of a 0 cap**, ledger committed
> ([findings-log/2026-10-14-pool-r-devicefamily-casing/FINDINGS.md]). The value's
> casing stays **unobserved**, `docs/05` now records that with the reason, and the
> candidate set it will be matched against is reconciled under a counting rule.
> Verdict, evidence and closing issue: the Closed table below. The original area
> text is kept, unedited, under this heading; where the pass corrected it, the
> correction is in the row, not silently absorbed into the area.

**Added 2026-10-11.** `docs/05` is corrected — `deviceFamily` **is** an API field on
`/patient/monitor/data`, agreed by three independent clients at named commits. What
is still missing is the **casing of a `deviceFamily` value**, which no client reports.

**Why the correction does not close it:** a destructuring default makes an absent field
indistinguishable from a present one, so a client that *reads* `deviceFamily` proves the
author believed it existed — not that it does.

**Closes when:** one authenticated `monitor/data` response records the key-name and its
value's casing verbatim, **or** a note in `docs/05` records that the value casing stays
unobserved and why. A negative retires the question honestly instead of leaving it
apparently answered.

#### Addendum (2026-10-14, area S independence audit, issue #125): two successors about the rule, recorded here because no letter is free

Area S closed on 2026-10-14 with a **negative** — "all remaining corroborated claims
are genuinely independent" is what the area asked for, and 12 strength-word claims
were found failing and relabelled rather than a clean sweep
[findings-log/2026-10-14-pool-s-independence-audit/FINDINGS.md]. Two questions it
could not answer are attached **here** rather than to a new letter, per
[Why there is no area AA](#why-there-is-no-area-aa) below. Both are about
`AGENTS.md` §2.1, and both bear on this area, whose own premise — *"agreed by three
independent clients at named commits"* — is the §2.1 test applied at its strongest
and the one claim in `docs/` that survives at **count 3**.

**1. Does §2.1 decide the one-organisation, two-method case?**

**What is known.** §2.1's three-part test turns on *authors*, *artefacts* and
*quoting*, and the audit found its sharpest recurring shape to be **two artefacts,
one producer** — this repository reading the same byte twice. That case §2.1 does
decide. The case it does **not** decide is two measurements by the **same**
organisation that are not derived from each other: Medtronic's own status line in
one response and its own log in a later release; this repo's kernel mtime series
against its own `date` series (`docs/09` §4); area L's page accounting and area
S6's re-run of it. Each is single-author and each is non-derived.

**Why it matters.** A reader cannot tell from §2.1's text whether that is one
source or two, and the answer decides whether "corroborated" is ever available for
a **vendor's own** surface — which is most of this repo's claims.

**Blocker:** a **maintainer decision on the rule's own precedent** — §2.1 was one,
and this pass is a research pass (`docs/11:1580-1582`, `docs/09` §4).

**Closes when:** the case is either written into §2.1 with an example, or
explicitly excluded from it in the same sentence. **A negative (excluded) counts.**

**Assumptions (INFERRED):** that §2.1's wording is intended to exclude same-author
pairs entirely, which is what "different authors" says and what no example in the
repo tests.

**2. What is the audited vocabulary — §2.1's exact strings, or their inflections — and does it speak to negated and instrument-verb uses?**

**What is known, measured, in scope at `origin/main` `7d915b8`.** §2.1 lists
**exact strings**, so the automated population is smaller than what a reader counts
by eye. Outside the eleven: `corroboration` **19**, `confirmed` **43**,
`corroborates` **7**, `corroborating` **5**, `confirm` **8**, `support` **41**,
`supported` **19**, `agree` **13**, and smaller sets. Eleven of those lines carry a
real multiplicity claim; two carry the word `independent` directly — `docs/05:60`
(count **1**, fails) and `docs/05:301` (count **2**, survives). Separately, §2.1
is silent on **negated** strength words, so `docs/07:149`'s *"neither confirms nor
refutes"* — which asserts a count of **0** and so cannot overstate — reads as a
literal violation. The audit applied a scope test of its own (logged, and labelled
INFERRED) to leave instrument-verb uses alone: *"403 only ever **confirms** a
negative"*. It survived that test only because **five** other lines whose words
*are* doing multiplicity work were still edited.

**Why it matters.** A rule a reader cannot apply consistently is not a gate. The
scope test above is defensible and it is also unverifiable from the text.

**Blocker:** the same maintainer decision on §2.1's wording. This pass did **not**
widen the vocabulary — `AGENTS.md` §1 makes the rule the source for which words are
gated — and read every excluded line anyway.

**Closes when:** §2.1 states which inflections are gated, whether a negated strength
word is exempt, and whether instrument-verb uses are in or out — **or** a note
records the blind spot and declines to close it, which `docs/09` §4 already
precedent for twice.

**Assumptions (INFERRED):** that the eleven strings were meant as a vocabulary
rather than as exemplars of one; the audit read them as literal, and recorded that
reading rather than choosing the other.

**Assumptions (INFERRED):** that the routing field and the reported-family field stay
distinct. If a future payload collapses them into one, the correction's shape changes.

#### Addendum (2026-10-13, from area G): the offline half is ready — per-build model lists as casing candidates

Area G extracted the device table from **each** portal build separately and found
them identical as data (78 table codes + 9 `SKU-*`, 76 quoted name-pairs + 2
unquoted `MMT5100`/`MMT5101` aliases + 9 `SKU-*` pairs, 80-code whole-file
census — same sets in both builds), with `MMT-8600`/`8601` in module `90991`
in both (OBSERVED,
[source: findings-log/2026-10-13-area-g-device-tables/FINDINGS.md]).

**What this gives R:** the exact candidate strings whose casing a wire
`deviceFamily` value must be compared against. The portal builds carry display
names ("Guardian™ 4 system", "Simplera™ system", "MiniMed™ 780G", …) alongside
every code, so a future authenticated response can be matched three ways:
against the model code, against the display name, and against the patient map's
16 family tokens — and whichever matches names the casing convention.

**Blocker (unchanged, restated with the offline half discharged):** one
authenticated `monitor/data` response (token-gated half stays); the offline
half — G's per-build model lists — is done and needs no re-fetch unless the
builds move (re-anchor by the asset sha256 pair `2a7fa8e7…` /
`a054555a…` first).

**Closes when:** one authenticated response records the `deviceFamily` value
verbatim and it is matched against G's table entries, or `docs/05` records the
casing as unobserved with the reason. A negative (casing unobservable without a
token) counts.

**Assumptions (INFERRED):** that the routing field and reported-family field
stay distinct; that table strings are the wire vocabulary.

> ⚠ **The first of those two assumptions is REFUTED** (area S4, and area R's own
> audit). The routing field and the reported-family field are **one axis** — the
> patient client assigns `n.deviceFamily = i.medicalDeviceFamily` — so a fourth
> match axis is needed ahead of G's three: the **client's own comparison set**
> (`BLE`, `BLE_X`, `SIMPLERA`, `SIMPLERA_X`, `GUARDIAN`, `NGP`). A future
> response matching **none of the four** is itself the finding.
> [findings-log/2026-10-14-area-s4-lazy-chunk-control-flow/FINDINGS.md] §6

#### Addendum (2026-10-14, from area R, issue #124): two successors, because R closes on a negative and a negative leaves work

Attached to closed area R rather than opened under a new letter — every letter
A–Z is in use, and a two-letter heading is invisible to this page's own count
(**Why there is no area AA**, below). *(⚠ Superseded 2026-10-16: two-letter
headings now count — see the Amendment in that section. The successors above
stand.)* **0 requests of a 0 cap**;
[findings-log/2026-10-14-pool-r-devicefamily-casing/FINDINGS.md].

**1. The read-side echo casing of the recovered logbook keys.** Area P and area S4
recovered the **write** payload verbatim, and S4 settled `timeCapUnscrewed` as the
wire form against the form-control name `timecapUnscrewed`. Nothing establishes
that the **read** response echoes any of these keys, and S4 explicitly flags the
submission shape as *not* shown to be the `logbook/entries` response shape.

- **Blocker:** a clinician token. `GET hcp/patients/{patientId}/logbook/entries` is
  patient-scoped and is deliberately not requested by this project.
- **Closes when:** one such response is read with key-names-only logging, **or** a
  note records that read-side casing is unobtainable under this project's
  constraints. **A negative counts.**
- **Assumptions (INFERRED):** that the read path echoes the write schema rather
  than a divergent one — **nothing on disk shows either.**

**2. Whether the `_*` suffixes (`BLE_X`, `SIMPLERA_X`) are a transport axis, a
model axis, or a build discriminator.** The enum declares four `_X`-suffixed
variants and **no committed artefact reads the suffix** — it is declared, never
consumed. A declared-but-unread enum member is exactly the shape that rots
quietly, because the declaration looks like a specification.

- **Blocker:** a client artefact that **branches** on the suffix rather than only
  declaring it. None is on disk; the patient bundle and its lazy chunks were
  swept (area K, 211 chunks) and the enum is module `45559` of the **main**
  bundle.
- **Closes when:** one call site is found that branches on the suffix, or a note
  records the suffix as undocumented-and-unused. **A negative counts.**
- **Assumptions (INFERRED):** that the suffix carries semantics rather than being
  a build or A/B discriminator — the repo holds **no** evidence either way, and
  the client's own matcher is a `startsWith` prefix test, which is consistent
  with both readings.

##### Closed 2026-10-15 — successor 2 (issue #132): documented negative. The suffix is **declared and unread**, and *inert*, not merely unused.

**4 of a 8 cap**, `GET` only, 2.5 s apart under the shared per-host lock; **2 requests of static
analysis**; [findings-log/2026-10-15-area-r2-x-suffix/FINDINGS.md].

The row's close condition is met by its second half — *"a note records the suffix as
undocumented-and-unused"*. Measured on the digest-pinned patient bundle
(`0fb4fbd4…`, 3 417 255 B, re-fetched and re-anchored by this pass):

| | measured | source |
|---|---|---|
| consumers of enum module `45559` | **1** — the module id occurs exactly twice, and one of the two is the definition | `census.txt` §C, bundle bytes 1 723 196 / 2 962 721 |
| member reads, total | **3** | `census.txt` §D, bytes 2 964 176 / 2 964 215 / 2 964 259 |
| distinct members read | **3 of 5** — `BLE`, `SIMPLERA`, `GUARDIAN` | `census.txt` §I |
| **`BLE_X`, `SIMPLERA_X`** | **0 reads.** Each occurs twice, both inside the declaration's own key and value | `census.txt` §E |
| consumption shapes other than `<binding>.G.<member>` | **none** across 8 explicit sweeps — bracket read, `Object.values`/`keys`/`entries`, spread, pass-the-object-as-a-whole. **7 of the 8 return 0**; the 8th returns only the already-counted same-token false hit at byte 198 638 | `census.txt` §D |

The three reads are the three arms of one expression, and each is a `startsWith`
**prefix** test (`p.startsWith(o.G.BLE)`). `"BLE_X".startsWith("BLE")` is already
true, so **deleting both `_X` members would change no branch, for any input,
including their own values** (`census.txt` §J, truth table). That is stronger than
"unused": the members are **inert**, and inert is a property no authenticated
response can overturn.

**And the enumeration is closed by the module boundary, not by a token count.** A
global `\bo\.G\b` sweep finds **4** hits, one of them a different module's exported
function; that is a count, not a closure. Bounding the *importing* module instead —
webpack delimiter, module `83644`, bytes 2 962 630 – 2 965 093 — and enumerating
every use of the imported binding gives **4 identifiers: the binding itself
(`o=i(45559`) and three `o.G.<MEMBER>` reads, with no module-level `o`, no
parameter named `o`, no alias and no bare pass-on**. With module `45559` exporting
exactly one binding (`G`), the enum object cannot leave module `83644` by any
route this body contains. So "0 reads" here is a closed enumeration, not a
sampled one [source: findings-log/2026-10-15-area-r2-x-suffix/FINDINGS.md §11].

So of the three readings the row offers, two are **excluded by this corpus** and
the third is untouched by it:

- **Not a transport axis *at this call site*.** The branch's consequence is a real
  transport decision — `getUploadDeviceInfo` POSTs the CSR periodic-data endpoint
  the public config supplies as `csr.cumulus.periodic.data.endpoints.display_message`,
  else emits `of(null)` (`census.txt` §D, §K, bytes 3 373 390 / 3 373 507) — but it
  is decided on the **base** token and does not distinguish the suffixed values.
- **Not a model axis *at this call site*.** The model axis in this corpus is
  nearby and separate: `deviceModelMapping` with its `StandaloneCGM` and
  `SIMPLERACC` keys (bytes 580 904 / 2 136 000 / 2 136 604), keyed by model, none of
  them enum members.
- **Still open: whether `_X` means anything on the wire.** Values arrive from
  `POST /patient/v2/monitor/data` (byte 3 372 491), and `getDeviceFamily` can
  overwrite the response with `sessionStorage.getItem("deviceFamily")` (byte
  3 372 603). **This pass says nothing about what the server sends** and does not
  narrow the semantic-suffix vs build-discriminator choice.

> **⚠ Scope limit, in the words the row requires.** This pass swept the **eager
> main bundle only**. **"0 reads in the eager main" is a true statement; "0 reads
> anywhere" is not one that can be made.** Area K swept the 211 patient lazy chunks
> for *pointer* tokens, not for `_X` reads and not for module `45559`.

> **⚠ Correction to the line above it, which this pass measured rather than
> assumed.** The original row reads *"declares **four** `_X`-suffixed variants"*.
> The enum has **two**: `BLE_X` and `SIMPLERA_X`, out of five members. Measured
> case-sensitively, each occurs exactly twice in the corpus and both occurrences
> are the declaration's own key and value (`census.txt` §E). The sentence above is
> **left as written** rather than edited — it is the row's record of what was
> believed when the area was opened, and a correction that overwrites the belief
> leaves no evidence that the belief existed.

Three successors, none of which needs a token:

- **(a) The patient lazy corpus, for module `45559` and for `BLE_X`/`SIMPLERA_X`
  reads.** The only thing standing between this result and "0 reads anywhere".
  **Blocker:** none — the candidate list is already committed and closed
  (`findings-log/2026-10-13-area-v-pde-clients/chunks.txt`, 211 entries), so the
  sweep is bounded without enumeration. **Closes when:** either a chunk importing
  `45559` is found (which would reopen the whole row), or the 211 are swept and the
  eager-main negative is promoted to corpus-wide. **Assumptions (INFERRED):** that
  the eager main holds the only importer of a module the main itself defines —
  measured for the main, **assumed, not measured**, for the chunks.
- **(b) Add the `BLE`-shaped rows to the `docs/09` §4 trap list, with offsets.**
  `BLE` has **52** case-sensitive hits in this bundle and **3 169**
  case-insensitively — a **60.9×** multiplier — and those 52 partition as **4** in
  the enum literal + **1** member read + **47** other. Of the 47, **34 are
  substrings** of longer identifiers and **13 are standalone tokens** where `BLE`
  abbreviates Bluetooth Low Energy inside a **debug-log event catalogue** — an
  unrelated third sense of the same token.
  ⚠ **⚠ The 13 are NOT one owner's, and this successor must not record them as one.**
  They fall across **three** arrays in that catalogue, grouped by log source:
  **11** in `source:"sensor"` *"Sensor Traces"* (array 3 314 809 – 3 318 475), **1** in
  `source:"pump"` *"Pump Diagnostic Logs"* (3 318 533 – 3 320 922), **1** in
  `source:"app"` *"Mobile App Logs"* (3 320 974 – 3 322 899). A byte span quoted over
  all 13 — 3 316 707 – 3 321 247 — is **the span of the hits, not of any one
  catalogue**, and calling it "the pump's" names one of three owners. **The register
  rows must carry each hit's own group**, or no span at all [source:
  findings-log/2026-10-15-area-r2-x-suffix/FINDINGS.md §3.2].
  ⚠ **The rule is stated so it does not mis-apply:** *substring* and *standalone* are
  defined over the **47 "other"** hits. Applied to all 52 the same rule gives
  **36 / 16**, because the declaration and member-read hits are themselves standalone
  `BLE` tokens under it. Both splits are right on their own class; only the 47 answers
  "what noise is this?". ⚠ **And the byte frame is named**, because the log publishes
  two and they differ by `len("o.G.")`: a member read spans
  `len("o.G." + MEMBER)`, so building it narrower — `site..site+3`, the length of the
  token `BLE` — yields **4 + 0 + 48** and **34 + 14** instead of the published
  **4 + 1 + 47** and **34 + 13** [source:
  findings-log/2026-10-15-area-r2-x-suffix/FINDINGS.md §3.1, §3.2, §11].
  `SIMPLERACC` (byte 2 136 604) is a model-map key a substring
  grep reports as a sixth enum member, and lowercase `guardian` (9 hits) is a **human**
  guardian of a minor patient's account, not the CGM family. **Blocker:** none.
  **Closes when:** these token shapes are rows in **`docs/09` §4**, the register that
  already exists and already cites this token in §5 item 2 — so the next sweep reads
  them instead of rediscovering them. ⚠ `docs/09` §4 carries **0** occurrences of
  `BLE` today, so the rows are genuinely absent rather than duplicated. **Narrowed by
  its own duplicate test** ([source:
  findings-log/2026-10-15-area-r2-x-suffix/FINDINGS.md §10b], re-runnable as
  `dup-test.sh`, which prints the commit it counted at): the register is named rather
  than implied, and area F's equivalent rows for the `timeline` family are the
  precedent, not a second copy of this work.
- **(c) The `NGP` figure does not reproduce.** This pass measures case-sensitive
  `NGP` = **0**; the 94 case-insensitive hits are the letters `ngP` (93) or `ngp`
  (1, inside `bingpreview`) inside `numberingPlan`-class identifiers. The 2026-10-08
  note records "three apparent matches … Samsung user-agent strings" and
  `docs/05:327` / `docs/09:236` repeat the figure; the Samsung regexes are present
  but none carries `NGP`. **Blocker:** none, but **this is a `docs/05`, `docs/09`
  and `docs/10` call, not this lane's** — recorded here and in the log as a
  disagreement with both readings given, and **none of the three pages was
  edited.** (`docs/10` row 38 is **adjacent, not the same figure** — it concerns
  the bundle's `N\d\d` tokens and a Samsung *device* regex — but a human resolving
  this should see it.) **Closes when:** one pass re-derives the figure on the pinned
  build and the pages are corrected together. **Assumptions (INFERRED):** that the
  earlier figure was case-insensitive; nothing on disk states the matching mode.

> **Grep-first duplicate test, run for all three successors** against
> `docs/10` §1, **both** tables that answer "the Closed table" (`docs/10` §2 *"Searched
> and closed"* and this page's *Closed areas*, which disagree with each other) and this
> page — commands, counts and a per-hit verdict for each, plus the two things it
> surfaced that are recorded rather than acted on. **Every count is bound to the commit
> it was taken on**, and the test is re-runnable as `dup-test.sh`, which prints the SHA
> it counted at — a `docs/11` grep count can move whenever a lane edits this page, and
> four lanes edit it at once in this pool [source:
> findings-log/2026-10-15-area-r2-x-suffix/FINDINGS.md §10, `dup-test.sh`].

#### S. Two more evidence classes for third-party source material

*(retained as a `####` subsection so the closed area does not re-enter the open-area count; area S is closed.)*


Area S closed on **a negative**, not on silence. `AGENTS.md` §2.1 now states the
independence rule and SOURCE-OBSERVED / SOURCE-PUBLISHED remain corroboration
descriptors rather than ranks (option (b)); the audit this area's own addendum called
"what remains" then ran at **0 requests** and found **12** live strength-word claims
failing §2.1, all at independent count **1**, and relabelled all 12 — plus **one**
claim that went the other way, from count 1 to count 2, found by reading a PR's author
off the artefact. Verdict, evidence and closing issue:
[findings-log/2026-10-14-pool-s-independence-audit/FINDINGS.md].

**The two questions the audit could not answer are attached to open area** R
**as its 2026-10-14 addendum**, not here, because a closed area should not carry
open work.

### K (closed 2026-10-16) The chunk corpus, for real this time

**Closed 2026-10-16 — control-flow mining complete; both clinic (225) and patient
(211) lazy-chunk corpora swept clean of discovery-key tokens; `system.logbook.entry.validation.config`
recovered in lazy chunk `9481`; cross-client differential declined as not meaningful.
Verdict, evidence and closing issue: [findings-log/2026-10-16-k-chunk-corpus/FINDINGS.md](findings-log/2026-10-16-k-chunk-corpus/FINDINGS.md), issue #140.** The original area text is kept, unedited, under this heading; where the pass corrected it, the correction is in the Closed-table row, not silently absorbed into the area.

224 lazy chunks are mined for endpoints and field names. **They were never mined for
control flow** — no analysis of what the call-sites do with the 89 field names, or
what the conditional logic implies about the request shape.

`system.logbook.entry.validation.config` shows entry shapes are **state-dependent**
(picking one removal reason triggers a free-text field). Tracing how the chunks
build the logbook entry payload would recover the request schema, not just the field
names.

#### Addendum (2026-10-13, from area V): the *patient* chunk corpus is a different, unswept set of 211

**Derived and non-duplicate.** Area K's corpus is the **224** chunks of the **clinic
portal** — `CHUNK-CORPUS-FINDINGS.md` names `hp-main.js` as its measure source. The
**patient** app is a separate webpack build with its own runtime chunk map, and that map
has **211 entries**
([findings-log/2026-10-13-area-v-pde-clients/chunks.txt](../../findings-log/2026-10-13-area-v-pde-clients/chunks.txt)).
Three were sampled once in 2026-10-08 (`JSMAP-HUNT §3.3`); **none of the 211 was ever
fetched as a corpus.** So the gap is not "chunks are unmined" — it is **the patient
corpus specifically**, which K's 224 does not cover.

**The candidate list is closed, committed, and current.** `chunks.txt` was written from
the runtime bundle's own map on 2026-10-13 and **reproduces** the 2026-10-08 record: the
map still has 211 entries and the sampled hashes (`12.c22952a522974f5f`,
`985.47eb741416e9cd44`) are unchanged. URL form is `<id>.<hash>.js` at the **asset
root** (`carelink.minimed.eu`, not `/app/`) because the runtime sets `.p=""`;
`JSMAP-HUNT §5` already recorded that the `<base href="/app">` reading is wrong.

**Why it matters now.** Every bundle claim area V made — "no web bundle reads the
discovery document", "the client follows `csr.cumulus.periodic.data.endpoints` but not
`system.gc.gz.transition.flags`" — is a statement about the **eager main bundle only**,
and that limit is stated at every use. A lazy chunk is exactly where a feature-gated
call site would live, so those negatives are provisional until this set is swept.

**Blocker:** 211 GETs of the committed list from one host — a real request budget
(≈9 minutes at a 2.5 s spacing), not a token. Everything else is already done: the
list, the host, the URL form, and the token set (`baseUrl*` / `discover` / `clcloud` /
`pde` / the nine `transition.flags` leaves).

**Closes when:** all 211 carry a verdict for that token set, each hit read to
literal-vs-directive with a case-sensitivity control exactly as area V read its 13
bodies — **and a negative counts**, since "no lazy chunk carries a discovery key" is
the expected outcome and would convert area V's scoped negative into an unqualified one.

**Assumptions (INFERRED):** that the chunk ids and hashes in the runtime map still
resolve — verified today for the two sampled ids only, not for all 211; and that the
patient `main`+`runtime` pair is the entry point for those chunks, which the runtime's
own `f.u` construction implies but this pass did not trace to a loader.

#### Addendum (2026-10-13, from area K): the patient 211 are swept — a positive, and a wrong URL form in the committed list

**This is area K's own addendum above, answered on 2026-10-13 (issue #56). Area K is
NOT closed** — the clinic half of K is untouched, and the successor below is filed
against it. 215 of a 230 cap, GET only, one host, `carelink.minimed.eu`.

**The negative holds in full and is now unqualified.** All 211 chunks were fetched —
**211 distinct digests, 0 duplicates, 0 empty bodies, 2.85 MB** — and every
pointer-shaped token is **0 across all of them**: `baseUrlPde`, `/connect/pde`,
`baseUrlCumulus`/`Cms`/`Aem`/`CareLink`, `discover/android`, `clcloud`,
`api/carepartner`. **No web bundle in the whole patient corpus reads the discovery
document**, not just the eager ones (OBSERVED,
[findings-log/2026-10-13-area-k-patient-chunks/FINDINGS.md §5]).

**And the positive the area predicted, on the sibling axis.** Lazy chunk
`6746.c6795ff7e9ff468d.js` **reads `system.gc.gz.transition.flags` twice** — two
modules of that chunk, both binding **module id `4265`**, which is defined in the main
bundle at byte 91298 and whose export table maps `z2:()=>be` to a selector over
`gt.guardianCumulusPeriodicAPI` = `"system.gc.gz.transition.flags"`. The value read
flows into the URL that is then POSTed. **Area V's "the client does not follow this
subtree" is correct for the eager main bundle and refuted for the patient corpus**; the
measurement is not retracted, the corpus was the limit. **A lazy chunk was exactly
where the feature-gated call site lived** — both reads sit behind `csrEnabled`.

**A correction to a committed artefact, which is why this addendum exists at all.**
`chunks.txt` lists chunk `2076` under its **id**; the runtime's `f.u` special-cases
that one id and emits the **name** `common`. The id form answers **404** (byte-identical
to the certainly-absent control); the emitted name answers **200** /
`application/javascript` / 21,157 B. A sweep that trusted the list would have closed
on "211 cells carry a verdict" with one verdict about a file that does not exist.
**Re-derive filenames from `f.u` and diff by hash before sweeping a chunk list** —
`docs/09` §4 now carries this as a trap.

#### Addendum (2026-10-13, from area K): the clinic 224 carry the same URL-form defect — successor

**Derived.** This could not have been written before 2026-10-13: it needs today's
observation that `f.u` emits one chunk under a *different name*, and nothing in the
2026-10-08 record connects that to the anomaly it already logged.

**Known, with labels.** The clinic build's runtime carries the **same special case** —
`f.u = e => (2076===e?"common":e)+"."+{12:"cfb28faf…",40:"9cffbe…",…}` (OBSERVED,
[findings-log/probe-2026-10-08/recon/JS-API-SURFACE.md:1118]). The clinic sweep
fetched **224 of a 225-entry map** and recorded **"One entry returned the SPA
fallback"** (OBSERVED,
[findings-log/probe-2026-10-08/CHUNK-CORPUS-FINDINGS.md:13]) — **never explained since**,
in either the log or `docs/`. The 5518 B fallback is what `carelinkhp.minimed.eu`
returns for *every* unknown path, so the entry is very likely that one chunk requested
under its id. The id `2076` is **live**: the clinic app requests it
(`uploader-instructions → r.e(2076)+r.e(342)`, OBSERVED, `JS-API-SURFACE.md:1128`).

**What is missing, and why it matters.** `docs/10` §2 currently carries "negative in …
**all 224 lazy chunks**" and the `CHUNK-CORPUS` table is headed "all 224 chunks". If one
of those 224 bodies is the 5518 B SPA page rather than a chunk, the **denominator is
misstated by one, in kind**: the corpus is 223 chunks plus one HTML page. The honest
reading is that this does **not** overturn the negatives — an HTML page can only
contribute false *hits*, not false misses — so the conclusions stand while the
denominator does not. That is exactly the `docs/09` §6 item 5 shape: right number, wrong
scope, propagated.

**Blocker:** the clinic runtime's `2076` **content hash**, which `JS-API-SURFACE.md:1118`
truncates to `cfb28faf…` — it is in the same committed artefact, so **zero requests to
re-derive the map** and at most **2** to settle the cell (`/common.<hash>.js` on
`carelinkhp.minimed.eu`, with `/2076.<hash>.js` as its in-corpus negative twin). Not a
token, not a budget problem: the map is on disk.

**Closes when:** the 2026-10-08 clinic corpus is re-stated with a **body-verified**
denominator — every one of the 225 map entries either fetched as
`application/javascript` under the name `f.u` emits, or recorded as absent — **and**
the unexplained SPA-fallback entry is either identified as that chunk or shown to be
something else. The resulting "0 of N" sentence carries the **measured** N.
**A negative counts:** if `/common.<hash>.js` also 404s on the portal, then the SPA
entry has another cause and the denominator correction stands on its own.

**Assumptions (INFERRED):** that the clinic runtime's `common` chunk is the source of
the SPA-fallback entry. The assumption is that the sweep requested the map's filenames
without applying the `f.u` name substitution — the same mistake the patient list
records, but **not verified**, because the clinic sweep's per-file ledger is not
committed. Nothing observed here demonstrates it; the 5518 B page identifies the
*host family*, not the chunk.

#### Addendum (2026-10-13, pool-K clinic URL-form pass): the id form is now measured absent on the portal

Four GETs to `carelinkhp.minimed.eu` (cap 4, `sleep 2.5` inside the host lock), GET
only. `OBSERVED`: `/common.a62bb847b4ea289e.js` → 200 `application/javascript`, 20731 B,
body begins `push([[2076]` (so the emitted name is genuinely chunk 2076); the
committed-list form `/2076.a62bb847b4ea289e.js` → 200 `text/html` 5518 B,
byte-identical (`0f2c5f62…`) to a certainly-absent name and to the documented SPA
fallback; a known committed clinic chunk `/12.cfb28fafc1fe9cf5.js` returns
`application/javascript`. Oracle (positive control + absent control) confirmed on
this host family before the verdict was taken. **Result: the clinic 2076 entry is a
second instance of the URL-form defect already measured on the patient corpus — the
hash is the join key, the name moved.** `docs/09` §4's trap row stands unchanged and
is not weakened. ⚠ **CORRECTED 2026-10-14 (area S independence audit): the word *corroborated*
is withdrawn** — both that row and this pass are this repository, count **1**
[findings-log/2026-10-14-pool-s-independence-audit/FINDINGS.md §3 row 31]. **Still NOT measured:** re-fetching all 225 clinic
entries under their `f.u` names; only id 2076 is settled here, and the negatives in
the 2026-10-08 clinic corpus still rest on its uncommitted per-file ledger. K's
denominator therefore stays provisional.
[source: findings-log/2026-10-13-pool-k-clinic-url-form/FINDINGS.md]

#### Addendum (2026-10-13, from area K residual, issue #78): the denominator is now body-verified at 225

**This closes the residual.** The predecessor left the 2026-10-08 clinic sweep's "one
entry returned the SPA fallback" unexplained and the per-file ledger uncommitted.

**OBSERVED — all 225 map entries resolve as `application/javascript` under the
name `f.u` emits** (one GET per map entry, 225 distinct digests, zero duplicates,
zero empty bodies, zero 5518 B fallbacks; host `carelinkhp.minimed.eu`).
Under those names the corpus is **225** JS chunks. Measurement:
`findings-log/2026-10-13-area-k-clinic-denominator/results.jsonl` (seq 1–225),
`spacing.txt` (body-mtime floor 2.561 s, 0 of 224 gaps under 2.5 s).

**INFERRED (bounded)** — the unexplained 5518 B cell is id 2076 fetched under
its id instead of its emitted name `common.a62bb847b4ea289e.js`, reproducing the
defect measured on the patient corpus (pool K pass req 2 vs req 4). The negatives
in the 2026-10-08 record survive (an HTML shell can only add false hits, never
false misses), and the published conclusions now carry N = 225.

**Successor -> K proper (unchanged):** control-flow mining of the call-sites and
the state-dependent shape of `system.logbook.entry.validation.config`.

#### Addendum (2026-10-14, pool K control-flow pass): call sites and write payload settled

The K-proper successor above is partially advanced by the pool K lane (issue #103),
static only, 0 vendor requests. Recovered from the shipped client corpus
(patient bundle `0fb4fbd4…` and lazy chunk `k-9799-ae484032a07c9d4f-js.b`,
digest pinned):

- **Call-site request shapes** — `GET /patient/logbookEntry/filled` and the
  paginated `/patient/logbookEntry` (repeated `type` query param); `POST` and
  `PUT /patient/logbookEntry` with a verbatim body; `DELETE
  /patient/logbookEntry/{id}` with no body; `GET /patient/logbookEntry/last`.
  `addEntry`/`editEntry` pass the built object straight to `http.post`/`http.put`,
  so the wire body is exactly the constructed `result`.
  [source: `findings-log/2026-10-14-pool-k-controlflow/FINDINGS.md` §2]
- **State-dependent write payload** — `attributes` is `null` for the typed
  entries, each of which instead carries its own nested object (sensor
  insertion: `sensorLocation`, `otherSensorLocation`, `timeCapUnscrewed`;
  sensor removal: `sensorLocation`, `otherSensorLocation`, `removalType`,
  `removalReason`, `removalDescription`; …). `attributes` is populated from the
  generic form controls for untyped entries.
  [source: `findings-log/2026-10-14-pool-k-controlflow/FINDINGS.md` §3]
- **Casing corrections** (already in area P, re-anchored to the submission site):
  `timecapUnscrewed` → `timeCapUnscrewed`; `sensorInsertionLocation` is a form
  control name serialised as `sensorInsertionInfo.sensorLocation`.
- **Still token-gated:** read-side echo casing of `/patient/logbookEntry`, and
  the field set of `system.logbook.entry.validation.config`.
- **Remaining work:** `docs/10` row 46 (read-side casing + read `GET
  hcp/patients/{patientId}/logbook/entries`) stays open; the safe successor per
  issue #103 is L (positive control, 0–2 GETs).

#### Addendum (2026-10-14, issue #121): the clinic 225 are swept — and area P's negative is completed, not refuted

**Area K is NOT closed.** This is the clinic half only, and the cross-client
differential it was meant to settle is **not settled** — see the refusal below.

**231 of a 231 cap**, GET only, one host (`carelinkhp.minimed.eu`), **0 requests
to any other host** [source:
`findings-log/2026-10-14-area-k-clinic-controlflow/FINDINGS.md`].

**The corpus did not drift.** 225 of 225 cells returned `application/javascript`,
225 distinct body digests, 0 duplicates, and **0 of 225 differ** from the
sha256s recorded on 2026-10-13. The map was re-derived from the live runtime's
own `f.u` and diffed **by hash**; the `2076 === e ? "common" : e` special case was
read out of the source, and a control confirmed the id-form 404s — docs/09 trap 3
satisfied rather than assumed.

**`system.logbook.entry.validation.config` is RECOVERED — which COMPLETES area P's
negative rather than refuting it.** Area P scoped its claim to *"the reproducible,
hash-verifiable web corpus"* and stated the route literal is followed *"by the
next module; there is no adjacent field definition"*. Both halves hold: `C40` has
**zero property reads** in the eager bundle (0 of 6 logbook constants do; 111 of
188 routes do). P was **right about what it searched**; its corpus was incomplete.
Per the same rule area Z's measurement was kept after a sweep narrowed it — *a
measurement and the inference drawn from it are separate artefacts* — the correct
label here is **completion**, and the earlier "refuted" wording in this addendum
and in the commit subject is withdrawn.

The route constant is in the eager main bundle, but the **call site is in lazy
chunk `9481.6977c1a7bd7461f8`** (module 79481):
`getLogBookConfig(){return this.http.get($.C40).pipe(catchError(()=>of({})))}`
(byte 6,673), stored verbatim as `logbookConfiguration` (byte 15,295) and read
**36 times** as `selectedEntryConfiguration`. The document is an object **keyed by
entry type**, carrying `sensorLocations.options[]`/`freeText[]`, `types`,
`doseUnits.options[]`, `questions[].label`/`.children[].conditionValue`.

**Why area P could not have found it:** in the eager bundle the constant has **0**
property reads outside re-export maps (0 of 6 logbook constants do; 111 of 188
routes do). The control flow lives in a lazy chunk. **This is the same lesson area
K already taught about the patient corpus, on the other half of the corpus.**

**Semantics recovered, values token-gated.** `types` presence makes `removalReason`
required (byte 82,617); `freeText[].triggerOption` selects the conditional
validation on `removalDescription` (byte 99,642); `conditionValue` gates a child
question (`o===i.conditionValue?0:-1`, byte 101k region). The **values** inside the
document are not published and not claimed.

**⚠ A negative that is the useful part: the client cannot tell an empty config
from a failed fetch.** Its own fallback is `of({})`. So a `200` carrying `{}` would
be **equally consistent with a swallowed auth failure** and must not be recorded as
"the schema is empty". Any future sweep of that route must distinguish the two.

**The cross-client differential is NOT reported, deliberately.** S4's committed
`extract-call-sites.py` was run unmodified against the clinic corpus, and it
resolves **220 of 225** clinic call sites as unresolved versus **58 of 233**
patient sites — because the clinic routes through a constant table
(`$.C40`, `$.lwO`, …) where the patient build inlines literals. Comparing the
surviving **5** clinic shapes against the patient's **144** would be meaningless,
so it is not done. The builds were proven distinct first: **0 of 145 shared chunk
ids share a content hash**. Arithmetic stated and checked: patient
`154+20+1+58=233` and `72+49+14+9+0=144`; clinic `5+0+0+220=225` and
`2+3+0+0+0=5`.

**Disclosed rather than smoothed:** on the `t_sent` series, **30 gaps fall under
the declared 2.5 s and 5 under the repo's 2.0 s floor** (min 1.766 s). A kernel
body-mtime series was recorded alongside and shows 0 under either — **and it
cannot settle the question**, because `mtime_gap == t_sent_gap + Δlatency` with
Δlatency swinging by up to 0.895 s, which is larger than the margin under test;
in all five sub-floor cases the +0.653…+0.895 s latency swing is precisely what
lifts those mtime gaps above 2.6 s — the swing does not itself breach 2.0 s, but
the mtime series is therefore not an independent witness. **Both series are
reported and neither is the
authority; no cause is asserted.** Both figures **ARE re-derivable from a clean
clone**, because `results.jsonl` commits `body_mtime_ns` for all 231 rows; an
earlier draft of this addendum said otherwise and was wrong. `body_mtime_ns −
t_sent` spans **[−0.823, +0.356] s, spread 1.180 s** — comparable to the request
latency itself, as a write timestamp should be. ⚠ **Two earlier drafts of this
addendum claimed a constant "3600.000 s" offset here. That was false** and was
introduced by this pass's own first correction round; it is withdrawn. Gaps are
named by seq pair in the log.

**Three instrument defects the pass found in itself**, recorded because a check
that cannot fail is not evidence: a literal detector whose quote-parity flipped
after the first escape (self-test now 6/6, including an absent-token negative);
and **a `scrub-check.sh` that resolved the repo root one level too high, iterated
zero patterns, and printed `PASS`** — now exits non-zero below five parsed
patterns. It also confirms a known-published vendor API key compiled into the
bundle at main byte 3,323,593 is **not** reproduced in any artefact.

**A route-delta negative — and a correction to an earlier draft of this very
addendum.** Counting rule: a route literal is a `hcp/…` or `/hcp/…` string
appearing inside a quoted span, extracted with a **parity-free** anchor
(`"([^"]*hcp/[^"]*)"`) rather than a raw `grep` over raw bytes, because a raw
grep flips quote-parity after the first escaped quote (docs/09 §5 false-hit
class; the same defect is recorded in this pass's own `FINDINGS.md` §5.1).
Set difference is computed under `LC_ALL=C sort -u` — an unsorted `comm` warns
and returns a wrong answer without failing.

| set | count |
|---|---|
| distinct `hcp/` literals in the **eager main bundle** | **184** |
| distinct `hcp/` literals across all **225 lazy chunks** | **3** |
| **shared** | **0** |
| **chunk-only** | **3** — `hcp/countries/dialCodes`, `hcp/patients/checkPhoneNumber`, `/hcp/sso/auth/otc/send` |
| **main-only** | **184** |

**⚠ This addendum's first draft published "168 shared, 1 chunk-only, 0
main-only". That was wrong in all three figures. The verifier caught it; the
correction is kept visible rather than smoothed over.**

**⚠ The first correction's own explanation was ALSO wrong, and is corrected
here.** Round 1 attributed the error to the corpus being incomplete mid-sweep and
said a partial corpus "inflates the shared figure". Both halves are false: a
partial corpus **deflates** shared, and the real defect was the **extraction
rule**. The first draft's rule was a raw byte grep for `hcp/[A-Za-z0-9_/.-]*`,
which reproduces its own erroneous **168** exactly on the complete main bundle.
It silently misses **26** literals that the parity-free rule catches — every
`/hcp/…` leading-slash form, every `((param))` template, the `?`/`=` query
string, and the `" /hcp/linkedPatient"` space-prefixed literal `docs/07` line 65
warns about. A second, separate error compounded it: the main bundle was globbed
onto **both** sides of the set difference.

The generalisable lesson, which is the same one `docs/09` §4 trap 3 records: *a
counting rule that cannot express a form the corpus contains will report that
form as absent, and "absent" is indistinguishable from "not found".*

The substantive conclusion is **unchanged and stronger**: the lazy chunks carry
essentially no route literals of their own. They route through the constant table
in the main bundle — which is the same mechanism behind §4c's 220-unresolved
figure, and the reason the endpoint differential is not reportable. The three
chunk-only literals are not new endpoints: `docs/07` line 47 already attributes
`/hcp/sso/auth/otc/send` to a lazy chunk, and lines 47–48 name the other two as
new literals the chunks contributed.

#### Successor to area K — do the 15 `hcp/configuration/public/*` keys answer?

**Derived from what this pass saw.** The client's own route table carries **15**
keys under `hcp/configuration/public/` (eager main bundle, **module 66703** —
which begins at byte 2,759,689 and owns the export map for these constants;
offsets 2,761,878–2,769,023), and **`docs/07` publishes no per-key verdict for
any of them** —
it publishes the oracle (line 180) and one worked control pair, not which keys
exist. So "the client calls these" is OBSERVED while "these answer" is unmeasured.

**Blocker:** a bounded list already on disk, needing no invention. **19 requests**
(15 keys + positive control `personal/media/config/eu` → 401 + absent control
`zzz.this.does.not.exist.zzz` + case control `CSU.CONTROL.CODES.SETTINGS` vs
`cua.control.codes.settings`), GET only, one host, controls first.

**Closes when:** all 15 carry a verdict under `docs/07`'s own oracle, **and**
`system.logbook.entry.validation.config`'s response is recorded as a **shape**
(members and value types), never as raw content. **A negative counts** — "not
published, and here is the exact reason" closes it. **The `of({})` ambiguity above
is the trap:** a `200` carrying `{}` is not evidence of an empty schema.

**Assumptions (INFERRED):** that the 15 keys in the client's route table are the
complete public config set the clinic app uses. A client may call a subset, so a
404 on a key the client calls would be drift, not absence.

#### L. Recovery of the retired `ipro/hcp` JSF surface

#### Addendum (2026-10-15, from pool L continuation, claim #126): **the window census is complete — 0 of 84 unread — and the family has dates in 2017, 2019, 2020 and 2021**


**188 requests** of the 200 authorised in round 2 (area total **228 of a 240 cap**),
GET only, `index.commoncrawl.org` alone, **zero requests to any Medtronic host**.
**60 of 188 rows failures** (502 ×33, 504 ×24, 400 ×3 — 32%), **54 retries each
with its own row, header capture and three timestamps**; `t_sent` floor **3.536 s**
and kernel-mtime floor **4.156 s** over 187 gaps, **0 under 3.5 s and 0 under the
`>=2 s` floor on either clock**, both series committed in `spacing.txt`. Two
negative durations (`t_done` before `t_sent` — impossible, `docs/09` §4's
corrupt-`t0` class, **no cause asserted**), and both clocks agree the spacing was
honoured at those positions.

**The census is done.** `collinfo.json` publishes **128** indexes, **84** overlap
2013-05-17 → 2022-05-13, and across all three passes of this area **every one now
carries a verdict**: **65 RECORD · 10 ABSENCE · 1 INDETERMINATE** (`-2014-23`) ·
**0 FAILURE** · 8 read by an earlier pass under a row schema this area's reader
does not parse · **0 UNREAD**. `census-84.txt` carries all 128 rows with each
verdict and the pass it came from.

**Eight more crawls carry `/ipro/hcp/*` — 28 members, 2017-06-26 → 2021-09-28** —
dates the corpus previously had **nothing** for: `CC-MAIN-2017-26` (6 members, two
crawl passes of the same three paths on one day), `-2019-35` (3), `-2019-47` (3),
`-2020-45` (6, two dates eleven days apart), `-2021-17` (1),
`-2021-21` (4), `-2021-31` (2), `-2021-39` (3). **Two paths are new to every
corpus:** `/ipro/hcp/privacy.jsf` (**403**, 2021-04-20) and
`/ipro/hcp/login.jsf?bhcp=1` (**200**, 2021-05-06) — the login page captured in
its *queried* form. `CC-MAIN-2021-31` holds the area's only `/ipro/hcp/*` cells
answering **403**. **INFERRED, and labelled because nothing observed separates the
readings:** that those `403`s mark the surface closing rather than a crawler
meeting a gate. The bodies are in Common Crawl and unread; no claim about *why* is
made, and the `403` here is the archived status of a capture, not a probe result.

**This corrects the correction.** The predecessor's pass refuted a "bounded 2020
deployment" reading; **that reading failed the same way** — it read a *sparse*
sweep as a *bounded* one. The statement the completed census supports is the
**negative**, and it is a census now rather than a spread:
**`/ipro/hcp/` is absent from 65 of the 84 in-window crawls**, and from **56 of the
64** this pass read. **The family is not a 2014-and-2020 artifact**: it was being
captured in 2014, 2017, 2019 (×2), 2020 (×3), 2021 (×4) and 2022, on one host,
`carelink.minimed.eu`, across **six paths**.

**What this does not do.** The claim is still **"absent from every crawl this pass
could read"**, and **"absent from Common Crawl" stays disclaimed**: **44 of the 128
published indexes lie outside the window** — **3 entirely before it** (2008–2013) and
**41 entirely after it** (2022-06 onward), `128 − 84 = 44` — and this area has read
**one** of
them, and that one — `CC-MAIN-2022-27` — carried a member. **A member outside the
window has already refuted the window's sufficiency once.** The eight `403`
bodies are unread. `cluster.idx` is still unbuilt. **`CC-MAIN-2018-05`**, which the
first pass selected and never enqueued, is in this pass's queue and **answered: a
readable absence** — control `commoncrawl.org` **200 / 5 records** (seq 82), then
`minimed.eu` domain **404** `No Captures found for: minimed.eu` (seq 83), one
attempt each, no retry.
⚠ **CORRECTED 2026-10-17 (the out-of-window census, #146): "this area has read
exactly **one** of them" is wrong — the figure is two.** `CC-MAIN-2022-21`
(2022-05-16 → 2022-05-29) is also outside the window, and an area-L pass read it
with the same two-cell shape: control `example.com` **200 / 5 records**
(`2026-10-13-area-l-ipro-hcp` seq 26), probe `minimed.eu` **200 / 4 records**
(seq 24), **0** `/ipro/hcp/` members, enumerated at
[findings-log/2026-10-13-area-l-ipro-hcp/FINDINGS.md:374-381]. **Only one of the
two carried a member** — that half stands. The committed inventory in this area's
own log directory carried the right tag all along (`crawl-window.txt`, row
`CC-MAIN-2022-21 … no  prior-L-pass`), so **the prose contradicted a committed
file**: `docs/09` §4's *derived prose contradicting its own source table*, one
level up. Repo-wide the figure is **six** (area M and lane S6 also touched
`-2022-40`, `-2024-42`, `-2025-30`, `-2026-39`) and **38** of the 44 had never been
read by any pass — every figure named, because "this area" and "this repository"
are different populations
[source: findings-log/2026-10-17-sl2-outwindow-census/FINDINGS.md §F6].

#### Addendum (2026-10-15, from pool L #126): the census pass — two new crawls, both ends now carried by captures, and area L **closes**

**40 of a 40 cap**, GET only, **`index.commoncrawl.org` alone, zero requests to
any Medtronic host**, ≥ 3.5 s held inside `flock`, measured `t_sent` spacing
floor **4.272 s** over 39 gaps (0 under 3.5 s, 0 under the `>=2 s` floor, 0
negative durations; kernel-mtime oracle 4.035 s, 0 under 3.5 s). **15 of 40 rows
were failures** (502 ×10, 504 ×3, 400 ×2 — 38%), and **a retry is a request**:
12 rows are retries. Evidence:
[source: findings-log/2026-10-14-pool-l-ipro-hcp-census/FINDINGS.md].

**Every cell below is classified under the counting rule that governs this page:**
*a cell is readable as an absence only if some row for that crawl answered 200.*
A failure is labelled a failure and is never smoothed into an absence.

| crawl | control (seq · status) | probe (seq · status · records) | `/ipro/hcp/` | **verdict** |
|---|---|---|---|---|
| `CC-MAIN-2013-20` | 8 · 200 | 9 · 404 | 0 | **readable absence** (host scope) |
| **`CC-MAIN-2014-15`** | 12 · 200 | 15 · **200 · 4** | **4** | **record — new crawl** |
| `CC-MAIN-2014-23` | 16 · 400 · 17 · 502 · 18 · 502 · 40 · 502 | 19 · 404 | 0 | **INDETERMINATE** |
| `CC-MAIN-2015-11` | 20 · 200 | 21 · 200 · 1 | 0 | record, no ipro |
| `CC-MAIN-2016-07` | 22 · 200 | 23 · 200 · 1 | 0 | record, no ipro |
| `CC-MAIN-2017-09` | 24 · 200 | 25 · 200 · 6 | 0 | record, no ipro |
| `CC-MAIN-2019-04` | 26 · 200 | 28 · 200 · 12 | 0 | record, no ipro |
| `CC-MAIN-2020-05` | 29 · 504 · 30 · 200 | 31 · 200 · 3 | 0 | record, no ipro |
| `CC-MAIN-2020-50` | 6 · 502 · **7 · 200** | 7 · 200 · 5 | **3** | **record** (area M's anchor, reproduced) |
| `CC-MAIN-2021-04` | 10 · 200 | 11 · 404 | 0 | **readable absence** (host scope) |
| `CC-MAIN-2021-10` | 32 · 200 | 33 · 200 · 3 | 0 | record, no ipro |
| `CC-MAIN-2022-05` | 2 · 504 · **3 · 200** | 4 · 404 | 0 | **readable absence** — the disputed cell |
| **`CC-MAIN-2022-27`** | 34–36 · 502 ×3 | 39 · **200 · 9** | **1** | **record — new crawl, control failed** |

**Three results, in the order they matter.**

**1. The one contradictory cell is settled, and the disagreement was a
control-ordering artefact.** On `CC-MAIN-2022-05` the control answered **504**,
then **200 with 5 records** on retry, and the `minimed.eu` domain probe sent
immediately after returned **404** `No Captures found for: minimed.eu`. Under the
counting rule that is a **readable absence**. **Both prior readings were true of
their own ledgers and neither was true of the crawl, and neither is retracted:**
the 7crawl pass's Correction records that *its own* two re-issued controls
returned `504`, and pool-L ran a `200`-with-records control but **sent no minimed
probe** and carried its cover across to one it never asked. What moved the cell
is neither ledger alone — it is a control and a probe **on one crawl, in one pass,
in that order** (OBSERVED, seqs 2–4).

**2. `/ipro/hcp/*` reaches 2022-07-03, so the "bounded 2020 deployment" reading
is refuted.** `CC-MAIN-2022-27` holds
`carelink.minimed.eu` `/ipro/hcp/index.jsp` at **`20220703140927`**, **HTTP 200**
(OBSERVED, seq 39). The 2022 end is now carried by a **capture**, 51 days *past*
the 2022-05-13 date `ARCHIVE-URLS §3` records — and past `CC-MAIN-2022-21`, the
crawl the earlier reading rested on, whose window (2022-05-16 → 2022-05-29)
simply precedes it. The earlier reading was not wrong about that crawl; it was
not the nearest crawl that carries the family. **Caveat, stated not smoothed:**
the control gateway-failed 3× here, so this cell is a record behind no succeeded
control — which costs nothing, because a record needs no absence oracle and seq
39 is a `200` on that exact crawl.

**3. `CC-MAIN-2014-15` holds four `/ipro/hcp/login.jsf` captures, all April 2014,
all HTTP 200** — `20140417041651`, `20140423143329`, `20140424054803`,
`20140424231208` (OBSERVED, seq 15). This is the densest cell in the corpus for
this family and the only one holding repeated captures of one path on one crawl.
**INFERRED:** that repeated captures mean a live surface to a crawler — the
records are the observation, the reading is not.

**The family as the corpus now reads it — four paths · one host · five crawls ·
an observed span of 2014-03-10 → 2022-07-03** (both new ends from this pass):

| timestamp | host | path | status | crawl |
|---|---|---|---|---|
| 2014-03-10 | `carelink.minimed.eu` | `/ipro/hcp/login.jsf` | 200 | `CC-MAIN-2014-10` (prior) |
| **2014-04-17 → 04-24 (×4)** | `carelink.minimed.eu` | `/ipro/hcp/login.jsf` | **200** | **`CC-MAIN-2014-15`** |
| 2020-05-27 (×3) | `carelink.minimed.eu` | `index.jsp`, `login.jsf`, `main/home.jsf` | 302 / 200 / 302 | `CC-MAIN-2020-24` (prior) |
| 2020-12-02 (×3) | `carelink.minimed.eu` | `/`, `login.jsf`, `main/home.jsf` | 302 / 200 / 302 | `CC-MAIN-2020-50` (prior, reproduced seq 7) |
| **2022-07-03** | `carelink.minimed.eu` | `/ipro/hcp/index.jsp` | **200** | **`CC-MAIN-2022-27`** |

**The 2013 end stays an absence and stays an absence.** `CC-MAIN-2013-20` and
`-2013-48` are readable absences, the host-scope cells on `-2013-20` and
`-2021-04` are now readable absences too (each behind its own control), and
nothing observed contradicts them. **That discharges
`2026-10-13-area-l-early-crawl-reissue/FINDINGS.md:107-111`** — the third time
the same shape has been run is this time the run that promoted it.

**⚠ The standing INFERRED is unchanged and this pass makes it more load-bearing,
not less.** That `/ipro/hcp/*` names **one** surface over time is **still not
demonstrated**. The 2022 member is a **`.jsp`** and the 2014 members are
**`.jsf`**; the 2020-05 member is a `.jsp` sitting on the same host as the `.jsf`
members, so the shape does not split the family — but one path prefix across
eight years and two server-side technologies (JSF and JSP), on a host that also
serves the patient
portal, is exactly what two corpora agreeing on a string does not establish.
**Assumption:** a shared path prefix implies a shared deployment.

**A third distinct failure shape joins 502/504/503 on this API:** a Python **400**
carrying `ConnectionResetError` (seq 16) *and* one carrying `RemoteDisconnected`
(seq 38), on two different crawls, in one run. `CC-MAIN-2014-23` took **four**
control rows across two control hosts and never produced a `200`, so its `404`
carries no absence weight — **the cell is indeterminate, and that is the finding,
not a gap to be written around.**

**⚠ This pass retracted its own crawl-window count — and the first explanation of
that retraction was itself half wrong.** The published number was **87** where the
answer is **84**, reproducing
`2026-10-13-area-l-ipro-hcp/FINDINGS.md:313-317` exactly. The buggy comparison
made **two opposite mistakes**, because `-` is `0x2D` and sorts below both `0`
(`0x30`) and `2` (`0x32`): it **dropped 2** — the `to` test fails for every 2013
crawl — and it **wrongly included 5**, because the `from` test *passes* for every
post-window 2022 crawl (`'2022-06-24…' <= '20220513'` is true), pulling in
`CC-MAIN-2022-21`, `-2022-27`, `-2022-33`, `-2022-40` and `-2022-49`.
84 − 2 + 5 = 87. **So the rule is restated more weakly and more usefully:
comparing `YYYY-MM-DD` on both sides also gives 84 — full timestamp precision is
not required, and what is forbidden is comparing two different string shapes.**
`AGENTS.md` §6 item 3, caught by re-derivation, and this count is published twice
on this page. No probe, control, cell or verdict was affected; only the
denominator moved, and it moved **toward** the prior figure.

**Why the area closes.** Its close condition was *"the `/ipro/hcp/*` family is
enumerated with a host and a date per member, and the `carelink.minimed.eu` anchor
is either confirmed across the 2013 and 2022 ends or explicitly shown to be a
single-period deployment"* — plus, in claim #126, that every cell is classified as
record / count-absence / **failure** / indeterminate. Both hold: every member has a
host and a date, the 2022 end is now a capture rather than an absence, and all 13
cells are classified with failures labelled as failures. **A negative counts, and
it counted here**: in **7 of the 9** crawls this pass **first read**, `/ipro/hcp/`
did not appear at all — the two exceptions being `CC-MAIN-2014-15` (4 members)
and `CC-MAIN-2022-27` (1 member). **The denominator is stated because two are
defensible:** over all 9 first-read crawls it is **7 of 9**; over the **8
classified cells** it is **6 of 8**, since a `404` behind no control cannot carry
an absence in either direction. Both are given, and they differ by exactly the one
indeterminate cell.

**What closure does not mean.** This is **not** "absent from Common Crawl."
`collinfo.json` publishes **128** crawl indexes, **84** overlap the
2013-05-17 → 2022-05-13 window, **12** had been read by a prior area-L pass, so
**72** were unread when this pass started. This pass first-read **9** of them —
**8 inside the window** and 1 outside it (`CC-MAIN-2022-27`, window
2022-06-24 → 2022-07-07, read precisely because the 2022-end question needed the
crawl *after* the window) — leaving **64 unread in window**. A tenth selection,
`CC-MAIN-2018-05`, was **never queued**: it appears in no `q-*.tsv`, no ledger row
and no header. What the cap actually blocked was the **retry of seq 40**, the
last control attempt, which answered `502` and was re-issued by a loop that found
the cap exhausted. The claim is **"absent from every crawl this pass could
read"**, and the hole in the broader claim stays open and stated.

#### Successors to area L (dated, in place — this page cannot mint a letter)

**S-L1 — CLOSED 2026-10-19 (claim #152). The instrument exists, and the target's
`404` is now a served-and-empty answer rather than an unreadable cell.** The
instrument is `findings-log/2026-10-18-sl1-cluster-servedness/servedness.py`,
committed under its log directory with three subcommands (`pass`, `classify`,
`selftest`) and usable on any named crawl. **The verdict on `CC-MAIN-2014-23`,
OBSERVED on two hosts and in this order:** the crawl is in `collinfo.json`
(**128** published crawls; its window **2014-07-09 → 2014-08-02**, fields
asserted `str`-typed before use); its `cluster.idx` is **SERVED**, `206` with
`Content-Range: bytes 0-8191/153 902 243`; the CDX API answers **`200`** with
**1 785 B** of `google.com` records on that same crawl; and the `minimed.eu`
query then answers **`404`** + `{"message": "No Captures found for: minimed.eu"}`
— the documented absence shape. **The cell retires on the SERVED side: this is
"the index is served and the family is not in it", not "the crawl was
unservable"**, and the two are not interchangeable — `AGENTS.md` §7 records that
`index.commoncrawl.org` TLS-drops from some hosts, so an unreachable host is a
statement about *this box*, never about a crawl. **15 requests of a 15 cap**,
GET only, `data.commoncrawl.org` (11) and `index.commoncrawl.org` (4) only,
**0 to any Medtronic host**, measured `t_sent` floor **3.537 s** over 11
checkable gaps (**0 under 3.5 s, 0 under `AGENTS.md` §8's 2 s floor**), **0
retries spent**, `E[N]` **1.00** for this run — against the **1.25–1.65 span across
the five populations `budget.py` prints** for this API (1.649227 / 1.515625 /
1.421005 / 1.373269 / 1.254848), not a single figure; and **not** a second
population for that model, since **11 of the 15** rows went to the **bulk**
path — 10 of the 13 instrumented, plus the disclosed pre-instrument probe — and
none of them failed
[source: findings-log/2026-10-18-sl1-cluster-servedness/FINDINGS.md §1, §6].

**The locate half did not converge, and that is the recorded negative.** The
`eu,minimed)`-family locate inside `cluster.idx` returned **`UNCONVERGED`** for
both controls at a 3-page budget, so **the control gate did not pass and the
instrument published no family-presence or family-absence verdict for any
crawl** — including the target, whose locate was never run. The bisection
narrowed `CC-MAIN-2022-27` to a **28 991 795 B** window (**18.9% of its
153 702 643 B** file, ≈ 7 further 4 MiB pages) without bracketing the interval;
its `f0 = 0.85` prior landed deep in `org,…`/`pl,…`, which is the wrong place
for a keyspace that is **not uniform over TLDs** (INFERRED, from the three
observed pages). **`UNCONVERGED` is not a negative and was not read as one**
(same log, §5d, §8).

**What S-L1's close condition asked, item by item.** *"served/unserved from
`cluster.idx` for every crawl named"* — **met**: one ranged read per crawl
answers `206` or `404`, and it classified correctly on both controls
(`CC-MAIN-2022-27` and `CC-MAIN-2024-42` both SERVED) against the absent-id
oracle (`CC-MAIN-9999-99` → `404 NoSuchKey`), which is what makes a `206`
readable as a statement about a crawl. *"every crawl a pass names in a negative
carries that verdict alongside its CDX verdict"* — **met for the target**, the
only crawl this pass names a negative for. *"a named crawl that cannot be read
is recorded unservable rather than left as a hole"* — **the branch did not
trigger**: every crawl named was served. ⚠ **And the condition's literal wording
is one this pass argues against**, so its satisfaction is vacuous rather than
demonstrated: S-L1's block says a crawl that cannot be read is recorded
**unservable**, while `FINDINGS.md` §4 argues that `unservable` is the *wrong*
label for exactly that case — a TLS drop is a statement about **this box**, and
the instrument therefore records **`UNREAD-FROM-THIS-HOST`**, which explicitly
**does not discharge** an indeterminate cell. **The condition should be reworded
to name that label**, and until it is, "did not trigger" is all that can be
claimed — the area is not closed on having satisfied it.

⚠ **Correction to this block's own text, on the record.** It named
`CC-MAIN-2024-22` as the readable-absence control. **That crawl's own cited
ledger contradicts it**: its S-L2 row 45 is a **`200`** for `minimed.eu`
carrying **13 records**, not a `404`. `CC-MAIN-2024-22` is a second
`carelink.minimed.eu` member, i.e. a **positive-adjacent** crawl. The
documented `404 No Captures found` is **`CC-MAIN-2024-42`**
(`findings-log/2026-10-13-area-m-commoncrawl-cdx/FINDINGS.md:349`, behind its
row-25 `200`). The 2026-10-19 pass used `CC-MAIN-2024-42`; claim #152's
descriptor was wrong and is corrected here rather than left standing in a
citation someone will re-read.

**Two buckets, and the instrument refuses to merge them.** `classify` prints
**connection-level failures** (`000`, 5xx, TLS drop, timeout, non-documented 4xx
— a statement about this host, this moment) **separately from served answers**
(`206` on the bulk path; `200`/`301`/`302`/`404` on the CDX API, where `404` is
the documented absence shape) — asserted in code and by `selftest`, which runs
both predicates over every status this API has been recorded producing. A crawl
whose every row failed at connection level is recorded **UNREAD-FROM-THIS-HOST**,
which **does not discharge** any standing indeterminate cell. This pass: **15
attempts, 15 served, 0 connection-level failures**
(same log, §4).


**Blocker:** none — a read of a published index, not a vendor surface.
**Closes when** every crawl a pass names in a negative carries a served/unserved
verdict from `cluster.idx` *as well as* from the CDX API, and a named crawl that
cannot be read is recorded as unservable rather than left as a hole.
`CC-MAIN-2014-23` is the named target: **four control rows, two control hosts, no
`200`** (OBSERVED, this pass seqs 16–18, 40).
**Assumptions (INFERRED):** that `cluster.idx` availability and CDX-API
availability are independent signals, and that a served index with an empty result
is distinguishable from an unserved one. Neither is demonstrated.

**S-L2 — the window census is COMPLETE; what remains is the window itself.**
**0 of the 84 in-window crawls are unread** after the 2026-10-15 continuation, so
this successor is no longer "read more crawls". Same two-cell shape
(per-crawl positive control, then `minimed.eu` `matchType=domain`, `output=json`,
**no `limit`**) was the right one and it worked **188 requests against a
predicted 211** — the corrected per-crawl cost below, budgeted conservatively.
**What is left** *(as S-L2 read it before 2026-10-17 — **superseded in full by the
closure immediately below**, and kept as written so the reasoning survives; both of
its facts are now measured and one of them is wrong, see the correction at the end
of this block)*: **44 of the 128 published indexes lie outside
2013-05-17 → 2022-05-13** — **3 entirely before** (2008–2013) and **41 entirely
after** (2022-06 onward) — this area has read exactly **one** of them, and that
one carried a member. **Blocker:** budget, and the fact that the window is a choice
inherited from `ARCHIVE-URLS`'s two dates. **Closes when** either that
justification is re-examined, or those 44 crawls are read too. **A member outside
the window is the valuable cell** — one has already been found. (per-crawl positive control, then `minimed.eu` `matchType=domain`,
`output=json`, **no `limit`**), continuing with the **64** unread in-window
crawls, in dated batches, against `data.commoncrawl.org` only if a second lock is
held. The crawl list is derived from `GET /collinfo.json`, never guessed.

#### ⚠ CLOSED 2026-10-17 by [`findings-log/2026-10-17-sl2-outwindow-census/`](../../findings-log/2026-10-17-sl2-outwindow-census/FINDINGS.md) — **both** halves of S-L2's close condition are met, and the justification does not survive

**114 of a 170 cap**, GET only, **`index.commoncrawl.org` alone, zero requests to
any Medtronic host**, ≥ 3.5 s inside `flock` (`t_sent` floor **3.339 s** over 113
gaps, with **one** gap under the declared delay — which is a corrupt `t_sent`
rather than a short delay: the kernel-mtime oracle puts the floor at **3.992 s**
with **0 of 113** under). **All 44 out-of-window crawls now carry a classified
cell: 40 RECORD · 4 readable ABSENCE · 0 indeterminate · 0 unservable-candidate**,
so the census is complete on **both** sides of the window — **0 of 84 in-window
unread, 0 of 44 out-of-window unread.** **24 of 114 rows were failures**
(502 ×12, 504 ×9, 400 ×3 — **21.1%**), every one labelled a failure and re-issued,
and **23 rows are retries**, each a request with its own row and header capture.

**The census itself reproduces, derived in code.** `GET /collinfo.json` (seq 1,
`200`, 35 226 B) yields **128** indexes; the window count is **84** and the
out-of-window count **44 = 41 after + 3 before**. **This is S-L3's close
condition, satisfied as a by-product of the method the sweep needed anyway:**
comparing `YYYY-MM-DD` on both sides gives **84**, full ISO-8601 gives **84**, and
the area-L dashless-bound variant is re-run and printed as its own **negative
control at 87** — `-` is `0x2D` and sorts below both `0` and `2`.

**The valuable cell: four more out-of-window members, and the family outlives the
window by four years.** All five out-of-window members are on one host,
`carelink.minimed.eu`, and **the four new ones had never been read by any pass in
this repository**:

| crawl | capture timestamp | path | archived status |
|---|---|---|---|
| `CC-MAIN-2022-27` | 2022-07-03 14:09:27 | `/ipro/hcp/index.jsp` | **200** |
| `CC-MAIN-2024-22` | **2024-05-23 08:39:53** | `/ipro/hcp/index.jsp` | **404** |
| `CC-MAIN-2024-26` | **2024-06-24 09:36:38** | `/ipro/hcp/index.jsp` | **404** |
| `CC-MAIN-2026-17` | **2026-04-14 09:26:05** | `/ipro/hcp/privacy.jsf` | **404** |
| `CC-MAIN-2026-25` | **2026-06-10 02:55:55** | `/ipro/hcp/index.jsp` | **404** |

**So the window's inherited justification does not survive, and it fails
asymmetrically.** Its upper bound is `ARCHIVE-URLS` §3's *"last archived
2022-05-13"* for `ipro/hcp/*.jsf`; the last member in the whole published corpus
is dated **2026-06-10** — **4 years and 1 month** past it — and it is a **`.jsp`**
member, so that bound was never on the family at all. Its **lower** bound survives
and is *generous*: the **three** crawls entirely before the window are all readable
absences, and the earliest member is still **2014-03-10**, inside the window. The
window is **loose at the start and four years short at the end.**

**What is now measured, in place of the window:** `/ipro/hcp/` is present in **5 of
the 44** out-of-window crawls and **12 of the 84** in-window, with an observed span
of **2014-03-10 → 2026-06-10** and no member anywhere else — **17 of the 128**
published indexes whole-corpus. **The in-window `12` is re-derived, not inherited**,
and it is **two higher than the figure this page inherited**: `census-84.txt:168`
publishes `11` while its own header at `:161` declares the tally IN-WINDOW-only, and
its list includes `CC-MAIN-2022-27`, which `:119` marks `in_window=no` — the defect
successor **S-L4a** already names, left unreconciled until this pass. The area's own
committed reader (`read-area-l.py census`, which parses the three row schemas its
predecessor could not) re-derives **12 in-window** and **39 in-window member
records**, against `census-84.txt`'s **10** and **35**; the whole difference is two
of the eight `older-schema` crawls, `CC-MAIN-2014-10` (**1** member) and
`CC-MAIN-2020-24` (**3**). **Both figures stand, both are published, and `12` is a
floor** — the reader says so in its own output
[source: findings-log/2026-10-17-sl2-outwindow-census/FINDINGS.md §F3c]. **Not claimed:** that the surface is
retired. Every status above is the **archived** status of a capture — not a live
answer, and no body was fetched; a `404` is equally consistent with long
retirement, a gate, and path rewriting, and **nothing observed separates the
three**. INFERRED, and labelled because area L drew the same line for the
in-window `403`s.

**Four corrections to `docs/`, applied in place rather than left standing.** (1)
*"This area has read exactly **one**"* of the out-of-window crawls is **two**:
`CC-MAIN-2022-21` was read too, with a `200` control and a `200` probe carrying
**0** members — only one of the two carried a member. Repo-wide the figure is
**six** and **38 of the 44** had never been read by any pass. The committed
`crawl-window.txt` tagged it correctly all along, so the prose had contradicted a
committed file. (2) This block's own *"exactly one"*, same defect, same fix.
(3) A **third site reached only on verification** — the same sentence, live in
**`docs/10` §1**, which the first pass did not touch; a reader of `docs/10` was
still getting the wrong count, uncorrected and unlabelled. Three sites, all
corrected in place with their correction attached; none deleted.
(4) And the in-window member figure this block published as inherited — **10** — is
**12**, re-derived; see the paragraph above and the log's §F3c. **Four edits, not
two:** the count of corrections a page claims is itself a figure, and this one was
understated.

**What this pass narrows and does not close.** The three pre-window crawls are
**served** — the CDX API answers `200` on the **2008–2009** and **2009–2010**
indexes, which are *older than* `CC-MAIN-2014-23`. So **"the API does not serve
crawls that old"** is now **falsified**, and that cell needs a different answer.
**S-L1 stays open and is not closed here:** this pass did not test that crawl, and
its condition — served/unserved from `cluster.idx` *as well as* from the CDX API —
is untouched. The follow-on this pass *can* name is minted as **AC**.
**Budget 3.3 requests per crawl — not 2 — and take the figure from
`budget.py`, not from prose.** *Counting rule: every `results.jsonl` row whose
crawl is one of the nine first-read crawls, ÷ 9.*

| | figure | how |
|---|---|---|
| **measured** | **3.22** | 29 rows on the nine ÷ 9 crawls |
| **derived** | **3.30** | row failure rate on those 29 rows `p = 13/29 = 0.448`; `probe.sh` sends `N = min(Geom(p), MAXRETRY+1) = min(Geom(p),3)`, so `E[N] = 1 + p + p² = 1.649`; two queries per crawl → **3.30** |

**⚠ The expectation formula this successor used to carry was wrong, and the error
inverted the sentence attached to it.** It read
`(1−p)(1+p+p²) + 3p³`, which expands to **`1 + 2p³`** — an expectation that
*falls* as the failure rate rises. The inner polynomial must be `1 + 2p + 3p²`;
`(1−p)(1+2p+3p²) + 3p³` is the same value, `1 + p + p²`. The published
consequence — "the measured figure exceeds the derived one" — was **backwards**:
under the corrected algebra the derived **3.30 exceeds the measured 3.22** by
2.4%. **Three figures are withdrawn from this successor in turn: "roughly 1.6"
(no derivation at all), "2.4–3.2" (a wrong floor, since 2.4 came from the broken
formula), and the sentence explaining why the measured number was the higher one.**
What survives is the arithmetic above, computed in `budget.py` so it cannot drift
from the prose again. **Checked against a large sample — and the check does NOT have one direction.**
⚠ **CORRECTED 2026-10-15 (verifier round 4): an earlier version of this cell said the
continuation came in "11% below the prediction, the correct direction for a budget"
and that "the model is conservative". Both were wrong, and they were wrong by
conflating two different quantities.** ⚠ **CORRECTED AGAIN 2026-10-15 (verifier round
5): the two percentages in the row below shared one cell and **two different
denominators** — 2.4% was on `measured`, 3.4% on `derived` — and **no denominator
was stated anywhere**, while `budget.py` printed **3.3%**, so the page named the
script as its authority and disagreed with it by 0.1 pp. **The denominator is now
stated once and used throughout: `measured`,** which is `budget.py`'s choice, so
page and script cannot differ again. (The other denominator would give 2.3% and
3.4%; both are correct arithmetic on different bases and only one is published.)

**POPULATION RULES, named in every row** — round 3's finding was that *a published
figure whose population is not named is a typed number wearing a script's name*,
and two rows below were both saying "predecessor" for **two different row sets**:

| id | population | rows |
|---|---|---|
| **S-L2** | every predecessor-ledger row whose crawl is one of the **nine** that pass **first-read**; the 3 re-probed prior-read crawls and the 1 anchor reproduction excluded | 29 over 9 crawls |
| **P-WHOLE** | **every** row in the predecessor ledger, including the inventory fetch and the re-probed cells | 40 over 13 crawls |
| **THIS** | every row in the continuation ledger | 188 over 64 crawls |

| quantity | population | comparison |
|---|---|---|
| **requests per crawl** — measured `rows ÷ crawls` vs derived `2(1+p+p²)` | **S-L2**: **3.2222** vs **3.2985** → measured **BELOW by 2.4%** · **THIS**: **2.9375** vs **2.8420** → measured **ABOVE by 3.3%** | **the sign flips between populations** |
| **mean attempts per query** — `rows ÷ logical queries` vs `E[N]` | **S-L2**: 29 ÷ 19 = **1.5263** vs **1.6492** → observed **BELOW** · **P-WHOLE**: 40 ÷ 28 = **1.4286** vs **1.5156** → observed **BELOW** · **THIS**: 188 ÷ 129 = **1.4574** (**1.46** rounded) vs **1.4210** → observed **ABOVE** | **flips at THIS** |
| **budget headroom** — rows spent vs rows predicted | **THIS**: **188** vs `64 × 3.2985 = 211.1` → **10.9% under budget** | *a third thing, and not the comparison the sentence named* |

**No direction is claimed.** The model is conservative only near the failure rate
it was fitted on; at this pass's lower rate it is slightly optimistic. A single
population cannot license a claim about the error's sign, and both signs are now
published.

**And two figures this cell used to carry are retracted here, by name, because the
table above replaced their sentence without saying so.** At `4c585cd` the cell
published *"the observed mean attempts per query (**1.43** predecessor, **1.45**
continuation)"*. **1.43 was right** for P-WHOLE (`40 ÷ 28 = 1.4286`). **1.45 was
wrong twice** — the continuation's figure is **1.4574**, which is **ABOVE** the
model's 1.4210, not below it, and it rounds to **1.46**. **The corrected pair is
published above**, with each population named; **1.43 and 1.45 are superseded and
neither is silently dropped** (`AGENTS.md` §5 — corrections are preserved, not
smoothed over). **Assumption (INFERRED):** that `p`, measured as the *marginal* row
failure rate, is the per-attempt failure probability a query actually faces — the
divergences above are recorded rather than reconciled, because reconciling them
needs a per-attempt conditional rate this pass did not measure.
**Blocker:** budget, against an API that fails 28–41% of its queries.
**Closes when** every in-window crawl carries a classified cell, or the sweep stops
with the remainder named. **A negative (no `/ipro/hcp/` anywhere else) counts** —
and so does a positive, which is what this pass found twice.
**Assumptions (INFERRED):** that a `/ipro/hcp/` record in one crawl predicts
nothing about the next; nothing here tests that, and the two 2020 crawls holding
records with four empty crawls between them is consistent with either reading.

**S-L4 — one reader for the area's ledgers.** Three passes of this area wrote
**three row schemas** — free-text `role` values in the 2026-10-13 passes,
`ipro_hcp_urls` / `ipro_hcp_members` in one of them, `ipro_hcp` in the two newer —
so **8 of the 84 in-window crawls cannot be re-derived by any script in the tree**
and `census-84.txt` labels them `older-schema` rather than reading them by eye.
This is `docs/11`'s area-Y defect — *the corpus is two sources, not one* — arriving
as a **schema change** rather than a missing file. **Blocker:** none, zero
requests. **Closes when** one script reads every area-L ledger and produces the
census with no manual reading, and the corpus is two sources in the sense that
addendum means. **Assumptions (INFERRED):** that the three schemas carry the same
facts — the free-text roles look like the same queries under other names, but that
is a reading of strings, not a demonstrated equivalence.

**✅ CLOSED 2026-10-15 by [`findings-log/2026-10-15-area-l4-ledger-reader/`](../../findings-log/2026-10-15-area-l4-ledger-reader/FINDINGS.md)
— 0 of a 0 cap, GET/OPTIONS/POST all 0, entirely offline.** `read-area-l.py`
resolves every area-L ledger with **one code path that never reads `role`**: a
row's cell is decided by **what it queried** (the `url=` in `path`, common to
every schema), not by what its author called it. **The three schema names above
are not wrong — they are a count of member-field shapes, and
`read-area-l.py schemas` measures exactly that and returns 3** (rule K2). What the
committed reader could not survive is the **population**, not the shape count:
`2026-10-14-pool-s7-l7crawl` has **no `role` key on any of its 19 rows** (a
`crawl` field instead, and `"200 (curl)"` as a status *string* — so a
`== "200"` test finds **0 of 19** rows), and `2026-10-14-pool-l-crawlcontrol`
carries **no data cell at all**, all 20 of its rows being controls. Both are
area-L work by their own `**Area:**` lines. **⚠ An earlier version of this entry
published "the schema count is five, not three". That aggregate is withdrawn** —
no counting rule produced it; it added a row-schema property to a
query-derivation property. Distinct row key-sets across the population are **10**,
member fields **3**, and the two component facts above stand with their own
numbers (`AGENTS.md` §6 item 7). **Population: 8 ledgers, 380 rows**, counted by
a recorded two-step rule before any row was read — and **`derive.py:169-170` was
reading 6**, missing those two, so **39 rows — 10.3% of the population
(39 ÷ 380) — were not in the corpus the census came from**. `older-schema` is now
emitted **0 times**: all **8 of 8** resolve to a named `ledger seq`, and
**7 → RECORD, 1 → ABSENCE** (`CC-MAIN-2013-48`, behind a `200`).

**⚠ The label had already cost two cells, and this is the finding, not the
cleanup.** The `older-schema` verdict is a bail-out in the committed reader
(`derive.py:182-185`), which called anything without one of three literal `role`
strings `older-schema`; but **`CC-MAIN-2020-24` carries 3 `/ipro/hcp/*` members**
(`2026-10-13-area-l-ipro-hcp` seq 34, `FINDINGS.md:549`, `:265-267`) and
**`CC-MAIN-2014-10` carries 1** (`2026-10-13-area-l-7crawl-reissue` seq 21-22,
`FINDINGS.md:55`) — while `census-84.txt:36` and `:102` score both `older-schema`
with **0** members and omit both from its member tally at `:168`. **Both values
stand.** Re-derived vs committed: RECORD **72** vs **65**, ABSENCE **11** vs
**10**, older-schema **0** vs **8**, in-window members **39** vs **35**, crawls
carrying a member **12** vs **10** in-window (**13** vs **11** counting the one
out-of-window crawl `census-84.txt:168` itself lists). 72+11+1+0 = 84, so the
re-derived tally leaves none unassigned. **The repo already contradicted itself
without any new evidence:** this page's own family table lists both crawls' members
in its two `(prior)` rows — `CC-MAIN-2014-10` / `/ipro/hcp/login.jsf`, and
`CC-MAIN-2020-24` / `index.jsp`, `login.jsf`, `main/home.jsf` — findable with
`grep -rn 'CC-MAIN-2014-10.*(prior)\|CC-MAIN-2020-24.*(prior)' docs/`, **by
content and deliberately with no line number, because this page moves as other
passes land. One of that recipe's rows is this very sentence, which quotes it, so
**no count is printed beside it** — a figure here would be a then-value that moves
every time this page is edited.** ⚠ **Two corrections to this sentence, both recorded because each
replaced one broken citation with another — the failure `AGENTS.md` §6 item 6
names, and the one this pass's own §8a-6 row 4 was written to stop.** It once read
**"lines 1736 and 1738 above"**, stale on the commit it shipped in (those lines are
two successor bullets); the rows are now named above instead. And the replacement
recipe first read **`grep -n '…' docs/` without `-r`**, which GNU grep rejects —
`grep: docs/: Is a directory`, exit 2, no rows — so the fix for a stale pointer
published a pointer that **did not execute**. **The `-r` is load-bearing; the
recipe is quoted with it, and it is re-run verbatim before this page ships.** A
citation that cannot be executed is worse than a wrong line number, because the
wrong number at least fails visibly. **⚠ Every member figure in this sentence — 39 vs 35, 12 vs 10, 13
vs 11, and each crawl's own count — is a LOWER BOUND, not an exact total.** The
evidence is two sentences below and it governs every number printed here; it is
stated here rather than only there because a limit separated from its figure by
other prose reads as an exact figure (`AGENTS.md` §2).

**Assumptions (INFERRED) — the equivalence is NOT closed, and this is the honest
answer.** Measured field by field: all three member shapes normalise to the same
record for **count, path and host**, but **`ipro_hcp_urls` (89 rows) carries no
timestamp and no HTTP status at all** — the `2014-03-10` and `200` the prose
gives for `CC-MAIN-2014-10` live in that pass's `FINDINGS.md`, not its ledger.
**And the five resolved zeros rest on an internal-consistency argument inside
one pass's ledger** (the same field, populated on a sibling crawl, empty on
these) — the bodies that would demonstrate them are outside the tree by
`AGENTS.md` §7. A reader that normalised free text into a schema would have
assumed the equivalence it was asked to test; this one measures the gap instead.
**The defect closes; the assumption stays INFERRED.**

**⚠ `CC-MAIN-2013-48`'s member count is NOT DERIVABLE, not 0.** Its only
member-bearing data row is a **502**
(`2026-10-14-area-l-ipro-early-crawl-supplement` seq 3), and an empty list on a
failed query carries no information — `census-84.txt:20` says a 502 is a FAILURE,
never an absence. The reader now takes member counts **only from `200` rows** and
prints every data row that could not supply one. **No headline number moves
either way** (the cell was `0`, and a not-derivable cell is not carried in the
member tally): RECORD 72, ABSENCE 11, 39 in-window members all stand.

**And every member count published above is a LOWER BOUND, not an exact total.**
A reader cannot distinguish "this crawl holds 3 members" from "this crawl holds at
least 3, and the pass read one page". **Two of the three candidate mechanisms are
measured and excluded, and one is not** — and both measurements are now computed by
a committed script under a stated rule, because a version of this paragraph carried a
count no script produced:

| mechanism | status | measurement — `python3 …/kib-detector.py` |
|---|---|---|
| `limit=` tail truncation | **excluded for 73 of 74** member-source rows | cell **B** (one per crawl, what the reader counts): 74 rows, **68** carry no `limit=`, **6** carry one, and only **1 reached it** — `CC-MAIN-2020-50`, `pool-l-ipro-hcp-census` seq 7, records 5, limit 5. **Carrying a limit and reaching it are different predicates**, and only the second can cut a tail |
| whole-KiB truncation | **excluded** | **0 candidates across 193** successful `200`s. "Successful" means the reader's own `status_of(row) == 200`; the other two obvious rules give **0** (`raw == 200`) and **183** (`raw == "200"`, missing the 10 `"200 (curl)"` rows), which is why the rule is stated beside the number |
| **completeness of the record set** | **NOT MEASUREDABLE OFFLINE** | `docs/10` §1 anticipates it — *"clean for this test is not the same as complete"* — and the bodies are excluded by `AGENTS.md` §7 |

**No upper bound on any crawl's members is claimed anywhere above, and every figure
here is ≥ its stated member count, not =.**

**Successors from this pass:**

**S-L4a — the member tally is mis-scoped, and the fix is a page this pass does
not own.** `census-84.txt:168` publishes **11** crawls carrying a member while
every tally above it is scoped "IN-WINDOW crawls only" (`:161`), and its list
contains `CC-MAIN-2022-27`, which `:119` itself marks `no`. **Blocker:** the
correction belongs in `census-84.txt` and in this area's prose, both outside the
claiming lane. **Closes when** the member tally states its window basis, or
`CC-MAIN-2022-27` is named as the single out-of-window entry.
**Assumptions (INFERRED):** that "crawls carrying a member" was *meant* to be
in-window — the header does not say, and both framings are published rather than
one being chosen.

**S-L4b — every member count is a FLOOR, not an exact total, and the five zeros
need a ledger field that distinguishes "computed, found none" from "not
computed".** **Blocker:** the bodies are outside the tree by `AGENTS.md` §7, so
"does a committed `200` row's member list enumerate every member in that crawl"
is undemonstrable offline. **Closes when** either the bodies are made available
under a disclosure decision, or every ledger row carries the distinction — a
`shape` field as `ipro-hcp` already has, or an explicit `members_computed`.
**Zero requests** for the second route. **Assumptions (INFERRED):** that a boolean
in the ledger is sufficient for the second route; nothing in the tree says a later
pass would populate it.

**S-L4c — one reader for the other committed ledgers.** ⚠ **The heading's "**36**"
is withdrawn (2026-10-19): no counting rule was stated with it and none reproduces
it. The population it means is now named by a command — `git ls-files
'findings-log/*/results.jsonl'` → **50** committed ledgers, of which **8** are
area L's own and appear in this pass's `manifest.tsv`, so the "other" population is
**42**. **That changes what this open successor asks for, and it is recorded here
rather than applied silently: the figure it was scoped against was wrong, and the
scope is now the 42.** Nothing else in the row changes — the blocker, the
`cors-method` half-ledger note, the closer and the zero-request budget all stand. **Blocker, weakened
from "none":** the population contains at least one ledger that is **not
machine-readable** — `2026-10-13-cors-method/results.jsonl` is **16 of its 24 rows
malformed JSON**, on `main` too (commit `8b7b7e9`) — so a reader that must span
it has to decide what a half-ledger counts as. Recorded, **not fixed**: it is
pre-existing and outside this claim. Otherwise zero requests; apply the same
count-then-read method to every `results.jsonl`.
**Closes when** every committed ledger resolves under the same query-derived cell
rule, or each non-resolving ledger is named with its schema and its reason.

> ⚑ **Correction (2026-10-20) — the census figures above are anchored, not live.**
> The `50` and `42` in this block were measured at **`5f37668`**, and they are correct
> *there*. They are **not** correct at any head that adds a ledger, because
> `findings-log/2026-10-17-area-aa-appversion-axis/results.jsonl` — committed by area
> AA, PR #155 — makes the population **51** at **`ad376d8`**. Rather than bump the
> numbers (which would be false again the moment PR #154 merges, adding
> `findings-log/2026-10-18-sl1-cluster-servedness/results.jsonl`), both readings are
> published with the commit each belongs to:
>
> | reading | at `5f37668` (measured) | at `ad376d8` (after AA's merge) |
> |---|---|---|
> | committed ledgers | 50 | 51 |
> | excluding the 8 area-L ledgers | 42 | 43 |
> | refused by the reader | 18 | 19 |
> | `findings-log/` top-level entries | 65 | 66 |
>
> **Counting rule**, unchanged and re-derivable at whatever head you hold:
> `git ls-files 'findings-log/*/results.jsonl'` — population = one such file; an item
> = one such file; a pass = exit 0; fail-closed = non-zero with a named reason.
> **The 19th refusal is area AA's own ledger, refused by design**: its schema carries
> no `http_status`, so it is a *known member* of the population, not an unexplained
> gap. **Two figures survive by coincidence and are not evidence the census is
> stable**: `66 − 51 = 15` still holds, and "not one traceback" still holds across all
> 51 (every exit ∈ {0, 2}).
>
> **The durable property, which is why this is anchored rather than restated:**
> **every merge that adds a `findings-log` ledger moves this census**, so any
> unanchored figure about it is false by construction one merge later. Carried to
> successor **AF** below.
**A negative counts.** **Assumptions (INFERRED):** that the other passes' schemas
are independent of area L's — different passes, different days, and nothing in the
tree asserts the schema set is closed. **Measured here and worth carrying into
that pass:** area L's own population was **not** the 6 its name rule most
obviously suggests but **8**, so expect the slug rule and the `**Area:**` line to
disagree, and report both.

**S-L4d — "absent from 65 of the 84" reconciles with neither reading, and the
sentence is in three places.** The **area-L addendum above** (this area's prose),
this page's **Closed-area row `L`**, and **`docs/10-open-questions.md` §1** all
publish it, while the same rows publish `65 RECORD · 10 ABSENCE · 1
INDETERMINATE` — so the `docs/10` row **contradicts itself inside one table row**.
Under the committed census the absent count is **19** (84 − 65); under this pass's
re-derivation it is **12** (84 − 72). **65 is neither** — it is the census's RECORD
cell read into the absent slot. **Find all three with
`grep -rn 'absent from 65 of the 84' docs/`** — deliberately no line numbers here,
because this page moves as other passes land and a pointer into it went stale
before. (⚠ an earlier version of this successor pointed at `:2170`, which does
**not** contain the sentence — it is the area-F dedicated-routes addendum. The
finding was right; the pointer was wrong.) **Blocker:** all three are out of this
pass's lane (`docs/10` §1, this area's prose, this page's Closed table).
**Closes when** one reading is chosen on stated grounds and the other two retired
with their arithmetic shown, or the sentence is re-derived from a named verdict
rule. **Zero requests.** **Assumptions (INFERRED):** that "absent from X of 84"
means *no member found* rather than *no `200`-bearing probe* — the two coincide
only if RECORD and member-carrying are the same set, and this pass's own
re-derivation shows they are not (**12** crawls carry members; **72** answered
`200`). **Stated because this pass hunted this exact class twice and missed a
third instance on the same page.**

**S-L4e — `account.py` is handed on broken, and this successor exists so it is not.**
`docs/10` §1's own successor tells the next pass to run that tool over **"every other
committed CC ledger"**. Run exactly that way, it **crashes on a member of this very
population**: `2026-10-13-area-l-ipro-hcp` seqs 1–4 carry a **null `t_sent`**, and
`account.py`'s `spacing()` called `strptime(None)` → `TypeError`. This pass did not
fix it — another lane owns that file — and **that is why this successor exists**:
recording the crash as observed is not enough while the row naming the tool still
points the next pass straight at it. **Blocker: none — the closer is a maintainer
decision, and
the earlier wording here ("the fix belongs to the lane that owns `account.py`") named
neither an owner nor a route, so it described the crash without stopping anything.**
`account.py` is a committed analysis script, not a live surface; the next pass that
runs it is whoever reads `docs/10`. **Closes when** EITHER the tool tolerates an
absent `t_sent` — the spacing oracle needs only the rows that have one, so skipping
them is sufficient and correct, not a loosening — OR the `docs/10` §1 successor is
reworded to name the ledgers it can read, which costs nothing and is the smaller
change. **Zero requests either way.** **Assumptions (INFERRED):** that the null is
a malformed row rather than a deliberately blank field — 4 of that ledger's 44 rows,
all at seqs 1–4, and nothing in the tree says which. **Not fixed here.**
⚠ **Three clauses of the entry above are superseded — *"This pass did not fix it —
another lane owns that file"*, the `account.py:109` line number (which this change
invalidated, since `account.py` is a file this correction edits; the call is named by
function instead), and *"**Not fixed here**"* — and this successor is CLOSED
2026-10-17: the
first branch of its own closer was taken, not the cheaper reword.** `account.py` now
tolerates an absent `t_sent`: `parse()` returns `None` for a non-string rather than
letting `strptime(None)` raise `TypeError`, `spacing()` skips the two pairs touching
a row that carries no timestamp **and prints how many it skipped**, and the
inverted-row test reads both keys with `.get()`. **All eight area-L ledgers open
under `python3 findings-log/2026-10-14-lane-s6-public-index/account.py <ledger>`,
run from the repo root** — the ledger path is root-relative, so the bare
`python3 account.py <ledger>` form resolves against the script's own directory and
exits 2. A second crash fell out of the same verification — a 0-row ledger raised
`IndexError`; it now says in words that such a ledger records a pass that sent
nothing. ⚠ **Two claims this paragraph carried are withdrawn.** **"The newest
committed CC ledger in the repository"** is deleted rather than reworded
(`AGENTS.md` §1): it is false at this head, and it had no committed ordering behind
it — `2026-10-15-pool-l-ipro-census-cont` is CC-bearing and carries the same date as
the 0-row ledger, so "newest" named nothing. And **"all eight"** is the area-L
population, a proper subset of what `docs/10` §1's successor actually asks for
(*"every other committed CC ledger"*): run over the population
`git ls-files 'findings-log/*/results.jsonl'` names — **50** committed ledgers —
this tool reads **32** and fails closed with a named reason on **18**, **not one
traceback**. Before this pass, over those same 50, **24** read and **26** died with
an unhandled `KeyError` or `TypeError`. **A ledger this tool cannot read is a gap in
the record, not a negative result**, and it now says so and exits 2 rather than
raising.

> ⚑ **Correction (2026-10-20) — same census, anchored.** The `50`, the `18 refused`
> and the `65` in this row were measured at **`5f37668`** and are correct there. Area
> AA's ledger (PR #155) makes them **51 / 19 / 66** at **`ad376d8`**, and PR #154 adds a
> 52nd. Both readings and the counting rule are published at the
> **S-L4c correction above**; they
> are not restated here, because a second copy is a second thing to falsify. The
> `32 read` figure is **unaffected** — the AA ledger is one of the refusals, not one of
> the reads. **Do not bump these numbers in place**: a per-head figure here is false by
> construction one merge later. (S-L4c is a bolded paragraph opener, not a heading, so
> this cross-reference is plain text on purpose — there is no anchor to link to.)

⚑ **Correction (2026-10-19). The two sentences this replaces — "the population is
named by a command rather than a glob on purpose: a glob in this tree expands to
paths that do not exist" — are withdrawn.** What was measured: the withdrawn figure
**65** is the count of `findings-log/` **top-level entries — passes, not ledger
paths** (`git ls-tree <sha> --name-only findings-log/ | wc -l` → **65**), where
there are **50** committed ledgers. The **15** difference is exactly the
tracked entries that hold no `results.jsonl` — **14 directories and one tracked
file**, `findings-log/cumulus-v2-spike.md`, which is a `.md` file, not a pass
directory; e.g. `findings-log/2026-10-11-third-party-client-sources/` is a tracked
directory that carries no ledger. **A glob and `git ls-files` name the same 50 files
here, so the counting rule is published as a command to make the population explicit
rather than to correct a glob that was not wrong.** **The census figures did not move because the
enumeration changed — they moved because `account.py` was fixed.** The counting rule
is unchanged and is the command: `git ls-files 'findings-log/*/results.jsonl'` → **50**. **Skipping the rows was the right
fix, not a loosening:** the spacing oracle needs only the rows that carry a
timestamp, and a gap measured *across* a row with none would be a guess. **The
INFERRED assumption above is untouched** — a null may still be a malformed row; the
tool no longer has to assume either way to answer. [source: findings-log/2026-10-15-area-l4-ledger-reader/FINDINGS.md §Correction (2026-10-17) — correction issue #139's eight findings, re-derived at this head]
[source: findings-log/2026-10-15-area-l4-ledger-reader/FINDINGS.md §1, §2b, §6, §7, §7a, §7b, §8a and the correction sections that follow it, §8b, §8c]

⚠ **The other seven of #139's eight findings were already fixed when PR #135
merged** (`aa401b7`, 2026-10-15), by that pass's own **seven** further commits, self-labelled rounds **3–9** — **counted by the filtered command**, `git log --oneline aa401b7^1..aa401b7 | grep -cE '^(24b9601|227a95c|bfc8f55|741cca1|228519f|d88a879|f83137d)'` → **7**, because the **unfiltered** `git log` this sentence first cited prints **12** lines beside a stated seven — a stale
pointer withdrawn, a policy made fatal, an unstated counting rule shipped in
`kib-detector.py`, a reader sentence corrected to the predicate it means, and a
rounding rule that now produces its own figure. **Re-derived at this head rather
than taken from the issue's wording**, with one live instance of the pointer class
found on this page and fixed above. **None of the measurements moved**, and none was
restated. [source: findings-log/2026-10-15-area-l4-ledger-reader/FINDINGS.md §Correction (2026-10-17)]

⚑ **What this correction pass closed, and why it mints no successor.**
**S-L4e is CLOSED above** — the only one of the five S-L4 rows this pass could close,
and it closed by taking its own first branch (fix the tool) rather than the cheaper
one (reword the successor). **No successor area is minted, and the reason is on this
page rather than only in the log: S-L4a, S-L4b and S-L4c are already open rows on
this page and remain claimable, so minting them again would fail
`CONTRIBUTING-research.md` step 7's *Non-duplicate* bar — a new row for work this page
already schedules is a duplicate row, not a successor.** A fourth candidate was
considered and failed the same bar: re-running #139's eight findings as a probe
area. It is **Derived** (the dispositions above give the commands), and it could be
made **Bounded** and **Labelled**, but it is **not Non-duplicate** — it is this
pass's own correction, already executed, and it would ask a next pass to re-probe a
corpus with no host contact to gain. **Bounded** is the bar that also stops a
candidate with no cap: a correction pass that minted a probe successor would have to
name a request budget, and none is derivable from anything on this page. **S-L4d** is
unchanged by this pass and remains open. [source: findings-log/2026-10-15-area-l4-ledger-reader/FINDINGS.md §Correction (2026-10-17) — third pass of this date]

**S-L3 — the census denominator needs a check, because this pass shipped a wrong
one and only a re-derivation caught it.** A one-command verifier for the
crawl-window count, run against `collinfo.json` with the comparison asserted on
its resolved type rather than on a string's byte order — the same lesson
`AGENTS.md` §6 item 3 records for a hash over a `None` lookup.
**Blocker:** none, zero requests.
**Closes when** the window count is derived by code that cannot silently drop a
boundary year, and the count in prose names the rule it was measured under.
**Assumptions (INFERRED):** that a reusable check is worth more here than the
number it checks.

[source: findings-log/2026-10-14-pool-l-ipro-hcp-census/FINDINGS.md]

---

## How to claim one

1. Open an issue using the **Claim a research area** form (labels
   `research-area,claimed`). State the area id and title from this page —
   if it is not on this page, it is not claimable here.
2. Say what you will probe, the request cap, and what "closed" means for that area.
3. When you have a result — positive **or negative** — open a PR with the finding
   and, if it pins something that must not rot, a regression entry.
4. **Negative results are first-class.** This repo's #84 was closed by proving
   something doesn't exist across 73 paths, 28 key names, and four corpora. That is
   a good contribution.
5. **Your PR must leave this page fuller than it found it.** Close the area into
   the Closed table with its evidence, and add at least one successor area with a
   blocker and a definition of done — minting the next free id (`AA`, `AB`, … now
   that `A`–`Z` is spent) — see
   [`CONTRIBUTING-research.md`](../CONTRIBUTING-research.md) step 7 for the
   template and the quality bar. A weekly job files an issue if this page drops
   below three open areas.

### Why there is no area AA
#### Addendum (2026-10-12, from area Y): the corpus is two sources, not one

Found while building area Y's index, and **the correction the rest of this page depends on** —
see [Why there is no area AA](#why-there-is-no-area-aa). Zero requests.

**`results.jsonl` is not the whole corpus.** Host evidence also lives in
`findings-log/probe-2026-10-08/recon/ORACLE-PROBE-MATRIX.md`, the repo's own "one-request-per-row
log". Area Y read the machine-readable ledgers first and found
`connect/carepartner/v6/display/message` `GET` on **zero** hosts — which would have marked a
correctly-evidenced three-host claim **false**. The matrix carries all three.

Two more traps in reading it: the `namespace` column **already includes `connect/`** (prefixing it
again yields `connect/connect/…`), and some rows carry the version in the path tail while others
leave it to the `ver` column. And the index's `--coverage` lookup originally returned **before**
the matrix was merged, so it answered from a smaller corpus than the report printed beside it —
**the same "check that cannot fail" shape this page already warns about**.

**Blocker:** none, zero requests. `audit-index.py` (in the area Y log) merges both sources and
emits both readings where a matrix row is ambiguous, so a claim can never be marked unevidenced
because a parser guessed.
**Closes when:** the two sources are documented as the corpus on this page, and any host-coverage
query reads both.
**Assumptions (INFERRED):** that `results.jsonl` + `ORACLE-PROBE-MATRIX` is sufficient. Other
markdown logs (`VERSION-AXIS.md`, `AWS-GATEWAYS.md`) carry host evidence too; no claim was marked
defective on the index alone.


⚠ **Superseded 2026-10-16 — the namespace now continues past `Z`; see the 2026-10-16
Amendment in this subsection. Kept as written:**

> **Every letter A–Z is now in use** — 0 open plus 26 closed — and the priorities page's own gate
> `.github/ISSUE_TEMPLATE/config.yml`. A two-letter heading therefore fails that count in two ways
> at once: it is invisible to the pattern, and the page's stated count would then disagree with its
> own contents. This was already recorded for the sub-declared-gap question in
> [`docs/09`](09-methodology-and-oracles.md) §4; area Z hit the same wall.

⚠ **Disclosed 2026-10-15 (area R): the Closed table below physically holds 26
rows while the arbiter's pattern measures 25, and the difference is the `S6`
row** — a closed area that fails this page's own rule in exactly the way the rule
two lines above describes. The number is not wrong; it is measured on a stated
pattern, and the pattern cannot see `S6` — ⚠ **both figures are as of 2026-10-15** and move
as rows land (K's row arrived 2026-10-16); re-derive rather than copy. Both figures are given
rather than one
being quietly chosen (`AGENTS.md` §2). Neither is adjusted here: the `S6` row
stays, the counting rule stays, and widening the pattern is a maintainer decision
that `docs/09` §4 already rules out of a research pass — "changing the gate's own
pattern in the same PR the gate passed is not a research pass's side effect". The
residual is a known one-cell divergence, not a hidden one.

> ⚠ **Corrected 2026-10-13 by area M.** This read *"9 open plus 17 closed"*. **The
> words are not mine — `git diff origin/main...HEAD -- docs/ | grep -c 'Every letter A'`
> is 0 — but the values are mine to maintain, because closing area M is what broke
> them.** Measured across the three revisions:
>
> | revision | sentence read | actual | `config.yml` |
> |---|---|---|---|
> | `3166c3a` (this branch's base) | 10 open plus 16 closed | **10 / 16** ✓ | 10 |
> | `cd626d6` (area E merged) | 9 open plus 17 closed | **9 / 17** ✓ | 9 |
> | HEAD (area M closed) | 9 open plus 17 closed | **8 / 18** ✗ | 8 |
>
> So this was **not** a stale sentence I inherited — area E had it right, and my
> own closure took closed 17→18 and open 9→8 while `config.yml` moved 9→8. **8 + 18
> = 26 = A–Z**, both figures re-derived from this page, and `config.yml` agrees.
>
> **This is the third time this exact sentence has been wrong.** Area Z fixed it at
> `fbe5d9b` (from "20 open plus 6 closed" to 19 and 7) and recorded why a green gate
> missed it: `research-checks.py` compares `config.yml` against the **heading** count
> (`^### [A-Z]. `), and **nothing anywhere compares this prose against either number**.
> That blind spot is unchanged, so this will drift again on the next closure unless a
> check is added. **Not added here**: extending the gate's own patterns in the same PR
> the gate passed is a maintainer decision, for the reason `docs/09` §4 already records
> about its count-pattern defect. Recorded as the successor instead.

⚠ **Superseded 2026-10-16 — minting is restored; see the Amendment immediately below. Kept as
written:**

> **So a pass that discovers a successor cannot mint a letter.** The options are: attach it to an
> existing open area as a dated addendum (what area Z did — see area Y), or record it in
> [`docs/10`](10-open-questions.md) §1 as an open question rather than a claimable area. **Neither
> is as good as a real area, and the honest reading is that this repository has exhausted its
> area namespace.** Extending the gate's area pattern to `AA`-style headings is a maintainer
> decision, not a side effect of a research pass — same reasoning as the gate's own pattern in
> [`docs/09`](09-methodology-and-oracles.md) §4.

#### Amendment (2026-10-16, maintainer): the namespace continues past Z — successors mint as `AA`, `AB`, …

**The maintainer decision the paragraphs above deferred has been taken.** **4 open plus 27 closed**
stand today (`AC`, `AD`, `AE`, `AF` — `AD` minted 2026-10-19 by lane sl1 and merged
against the `AE`/`AF` mints; counted from the `^### [A-Z]{1,2}.` headings, not
inherited); the next bounded successor that clears the step 7 quality bar is minted as a
**two-letter area** (`AA`, `AB`, …) instead of being parked as an addendum or a `docs/10` §1 row.
**`AA` was the first such mint** (2026-10-17, [issue #145](https://github.com/NovaLux12/carelink-api-research/issues/145)):
the `android/<app-version>` axis on the two cumulus `.com`/`-trials` hosts — which
had **not** been swept on that axis at base `v13` (⚠ corrected on closing AA, which
this PR did: `.com` had never had the tail varied at any base, and `-trials` only at
`v6` with two tails — see `docs/03` §3b's "What was already swept").
**`AF` was the third** (minted 2026-10-20, by the PR that closed AA, on the `origin/main`
sync — the census anchor below). **`AE` was the second** (minted 2026-10-19 by that same PR, under
[claim #151](https://github.com/NovaLux12/carelink-api-research/issues/151) — the
same claim issue AA was closed under), and is the question AA's cells could not
answer — whether that tail is a lookup table or a threshold.

- The area-counting patterns are widened to `^### [A-Z]{1,2}\.` wherever they live —
  [`scripts/research-checks.py`](../scripts/research-checks.py),
  [`scripts/research-loop.sh`](../scripts/research-loop.sh), and
  [`.github/workflows/priorities-alarm.yml`](../.github/workflows/priorities-alarm.yml) alike.
- The `N + M = 26` invariant is **retired**: every live "N open plus M closed" sentence must merely
  **agree with the page** — heading count, Closed-table rows, and
  [`.github/ISSUE_TEMPLATE/config.yml`](../.github/ISSUE_TEMPLATE/config.yml) — at whatever total.
  The count sentence in this amendment is **live**: `scripts/research-checks.py` parses every
  non-blockquoted "N open plus M closed" and fails on drift, so a minting pass updates it here.
- `S6` stays outside the count exactly as the disclosure above states — it never matched the
  single-letter pattern and does not match the two-letter one, so the physical-row count and the
  measured count keep being given side by side.

This restores what the paragraphs above lost: a bounded successor is a **claimable area** again,
and [`CONTRIBUTING-research.md`](../CONTRIBUTING-research.md) step 7 is the rule that says so.

#### Addendum (2026-10-14, from issue #102): dedicated-route envelopes on `.com` and `-trials` — byte-identical, language-independent

**Derived from 14 GETs across two patient deployments, cap 14/14, controls first,**
`findings-log/2026-10-14-area-f-dedicated-routes-succession/FINDINGS.md`.

- **All three dedicated routes answer `200 application/json` on both**
  `carelink.minimed.com` and `carelink-trials.minimed.com` (controls:
  `/patient/configuration/version` and `/patient/configuration/` both `404` with
  an empty body on both hosts — 4 of 14).
- **Envelopes.** `defaultCountry` → `{"value": <2-char>}` (20 B, same digest
  on both hosts); `recaptcha/key` → `{"value": <40-char>}` (58 B, **different**
  digest per host, consistent with the per-host reCAPTCHA keys already on
  record); `messages/{en,fr,de}` → `{"messages": []}` (22 B, **identical
  digest across both hosts and all three languages**). No language-dependent
  content was observed; the empty array is not an `en`-only artefact.
- **A negative.** No additional 404 shape was produced by this pass — the two
  controls 404 with no `content-type` on both hosts only — so the three-valued
  404 content-type set stays as area E recorded it; this pass does not extend
  it. No regression pin moved.

**Successor (per issue #102):** a pinned cell-digest artefact in any future
per-key sweep (0 requests), so the "0 mismatches" line becomes re-hashable.
**Assumptions (INFERRED):** none beyond the quoted addendum claims.

## Closed areas

Dated, with the verdict and the evidence. An area leaves this table only by
being superseded — never silently. Letters are not reused.

| Area | Closed | Verdict | Evidence | Closed by |
|---|---|---|---|---|
| C — extend the oracle set to `pde/v3` and `csr` | 2026-10-11 | **Negative on 10 cells, positive on 2.** PDE `v1/v2/v3` `display/message` and `pde/v3/discover/android/3.6` dead on GET **and** OPTIONS (no route on any tested method); `csr/v1`/`v3` and the bare `connect/carepartner/` prefixes dead on both; `connect/csr/v2/display/message` and `connect/v2/display/message` **live, POST-only** — in no prior note. 30 of a 30 request cap, GET+OPTIONS only | [findings-log/2026-10-11-pde-csr-oracle/FINDINGS.md] | #2 |
| N — do the two new POST-only routes exist on the other two cumulus hosts | 2026-10-12 | **Positive, and no region split.** Both `connect/csr/v2/display/message` and bare `connect/v2/display/message` are live and POST-only on `clcloud.minimed.com` and `clcloud-trials.minimed.com` as well as `.eu` — every cell byte-identical including CORS header ordering, controls first on each host. 16 of a 16 cap, GET+OPTIONS only. The pass also produced a **methodology correction**: `access-control-allow-methods` is not a register of a route's methods (`v13/display/message` advertises `OPTIONS` and is GET-capable on all three hosts) | [findings-log/2026-10-12-csr-cross-host/FINDINGS.md] | #8 |
| U — are the `csr/v1`, `csr/v3` and PDE cells dead on `.com`/`-trials` too, or only on `.eu`? | 2026-10-12 | **Negative, 3 hosts wide.** All six cells dead on **both** methods on both remaining hosts — 24 of 24 cells `403 MissingAuthenticationTokenException`, controls first on each host, 32 of a 32 cap. All 28 no-route bodies byte-identical (42 B, `sha256:f249b63cb2fc`), and that digest matches the `.eu` capture, so the router's no-route response is one artefact shared by three hosts. `docs/00`'s "Not re-probed on `.com`/`-trials`" caveat is **discharged**; nothing flipped to live | [findings-log/2026-10-12-pde-csr-cross-host/FINDINGS.md] | #11 |
| T — does any published document point a client at `csr/v2`? | 2026-10-12 | **Positive, and the premise was wrong.** The public config names `csr/v2` in **two** keys on **all three** deployments (`…csrDisplayMessageUrl` and `csr.cumulus.periodic.data.endpoints.display_message`, same URL), with `useCumulusUrls` already `true`; `baseUrlCsr` does not exist, so the route is addressed from **config, not discovery**. 10 of a 12 cap, GET only. Also found the **`system.gc.gz.transition.flags` switchboard** (absent from every prior key list), the **only** unroutable published base URL (`baseUrlPde`), and two corrections (`personal.data.csv.export.enable` is an object not a boolean; the document is 68 flat dotted keys + 1 nested `captcha`). **The premise had already been refuted on disk** by [findings-log/probe-2026-10-08/recon/ARCHIVE-URLS.md](https://github.com/NovaLux12/carelink-api-research/blob/main/findings-log/probe-2026-10-08/recon/ARCHIVE-URLS.md) §1 line 99 and never reached `docs/` | [findings-log/2026-10-12-published-pointers/FINDINGS.md] | #10 |
| B — the `v12/display/message` routing picture | 2026-10-12 | **Positive on the audit target, and the premise needed no correction.** `v12/display/message` is `401` + `UnauthorizedException` + `x-ca-err: 990` on **all three** hosts, 3 of 3 — but `docs/03` §6 and `docs/06` had asserted "401 on all three hosts" on **one** raw row (`.eu` only, duplicated across two files), so the claim is now *confirmed and evidenced* rather than restated. All 8 controls passed, controls first per host. **`v12` does not differ from `v13` on preflight**: `OPTIONS v{11,12,13}/display/message` all `200` + CORS, and `x-ca-err: 990` is identical across `v11`/`v12`/`v13`. **The gateway does not add CORS uniformly:** `discover/android/3.6` returns `401` with zero `Access-Control-*` at every version, same host and session — but this is **an observation, not a cause**: across all 101 captured heads every CORS-carrying response is a `200`, so "per-route configuration" is **not established** and became successor X. 17 of a 24 cap, ****23 of 24** including hurl validation of the new pins**, GET+OPTIONS only, measured spacing floor **2.033 s** (13 of 14 same-host gaps ≥2.5 s; the one short gap is **arithmetically impossible if both timestamps are faithful** — which assumes a monotonic clock, and `docs/09` declines to assert that cause — and is recorded as a provenance problem, not smoothed over. The 42 B no-route digest `f249b63cb2fc` reproduces the area U artefact ⚠ **CORRECTED 2026-10-14 (area S independence audit): the word *independently* is withdrawn** — area B and area U are both this repository, so the independent count is **1**, however genuinely surprising the digest match [findings-log/2026-10-14-pool-s-independence-audit/FINDINGS.md §3 row 35]. ⚠ **Its CORS corpus premise was superseded by area X the same day** — the 10 CORS-less `200`s are not all on "a different host surface"; four are `clcloud.*` discovery documents. The observation stands; the inference did not ([findings-log/2026-10-12-area-b-v12-routing/FINDINGS.md] §Correction) | [findings-log/2026-10-12-area-b-v12-routing/FINDINGS.md] | #4 |
| X — why the two `clcloud.*` route families differ in their CORS headers | 2026-10-12 | **Negative on the separating cell the area named, and a correction to the confound it rested on.** The area said no separating cell existed; **one was already in the corpus.** Of the 10 captured `200` heads with no `access-control-allow-origin`, **4 are on `clcloud.*`**, not on "a different host surface" — so on `clcloud.*` a `200` carrying no preflight *does* exist, and status was never standing in for CORS presence. Re-derived live on all three hosts: **25 of a 26 cap**, GET + empty-body OPTIONS only, controls first per host, **all 7 controls passed**; **9 further `200`-without-CORS responses, every one a `GET` of a discovery payload**; **0 non-2xx responses carrying CORS on `clcloud.*` (counter-examples on `commoncore*`: six 403 captures, PR #59/#65)**; and sending `Origin` changed **none** of the **6** paired bare/`Origin` cells (6 route×method pairs, controls excluded), which **excludes** the "ACAO only when an `Origin` is present" mechanism. **It does not exclude area B's reading (b)** — "the route demands a token on `OPTIONS`" — nor reading (a), nor "emitted only on `OPTIONS`": a first draft of this row claimed (b) was refuted, and that was withdrawn, because the reason assumed a configured route would carry `ACAO` on its own `200` `GET`, which is the thing in dispute. **The cause is not established and this row does not establish it** — all three readings fit 25 rows, and separating them needs a CORS-configured `clcloud.*` route that also answers `200` on `GET`, of which **none is recorded on any host**. The four archive heads are **gitignored**, so the 24/14/10 split is not re-derivable from a clean clone. Measured spacing floor **2.291 s** (20 of 21 same-host gaps ≥2.5 s; the one short gap is **arithmetically impossible if both timestamps are faithful** (it assumes a monotonic clock, which `docs/09` declines to assume elsewhere) and is recorded as a provenance problem, **not smoothed over** — the second such gap in two passes). The separating cell is now **pinned** on the public `200` `GET`, at zero extra requests per drift sweep | [findings-log/2026-10-12-area-x-cors-separation/FINDINGS.md] | #15 |
| Z — does any `clcloud.*` route reflect `Origin`, or is `ACAO` a fixed `*`? | 2026-10-12 | **Negative, as predicted: `ACAO` is a CONSTANT `*`, never an echo.** Each preflight route's `OPTIONS` was sent under **three** conditions — bare, `Origin: https://example.invalid`, `Origin: https://probe-two.invalid` — on all three cumulus hosts, because **one `Origin` cannot distinguish an echo from a constant** and that is exactly why the archive (and area X's single-`Origin` pass) could not answer it. **45 of 45 data cells returned `ACAO: *`; 0 echoed; 1 distinct value.** All 6 controls passed **first on every host** (live `401` + `x-ca-err: 990`; dead `403` at the corpus no-route digest `f249b63cb2fc`, byte-identical on all three). `ACAM` is a **per-route constant**, 9 of 9 cells each across 3 hosts × 3 conditions, and **does** differ from the literal `OPTIONS` on two routes — `csr/v2` → `OPTIONS,POST`, bare `v2` → `POST,OPTIONS`, the same method set in a **different declared order**. `ACAC`, `access-control-max-age` and **`vary`** absent on all 51 responses. 60 of a 69 cap (51 harness + 9 hurl pin-validation), GET+OPTIONS only, measured minimum same-host gap **2.042 s** with **5 of 48** gaps under the declared 2.5 s — **none below the `>=2 s` floor**, the third pass in a row to record one (running count in `docs/09` §4). **No cause established.** **Positive side-finding:** `v6/display/message` — the vendor's own published `blePereodicDataEndpoint` — answers `200` + `ACAO: *` on **all three** hosts, closing a gap where it had only a `.eu` yes/no `CORS` flag and **two hosts never `OPTIONS`-probed**. ⚠ **The area's own premise was corrected before probing**: it asserted `ACAO` on all three hosts for `csr/v2`, bare `v2` and `v6`, and that was evidenced for **none** of the three — area Y's defect class. See the "corpus is two sources, not one" note under **Why there is no area AA** | [findings-log/2026-10-12-area-z-origin-reflection/FINDINGS.md] | #17 |
| Y — how many "all three hosts" claims rest on a single row? | 2026-10-12 | **All 29 in-scope claims confirmed by row — the negative result, and it closes the audit.** Every multi-host claim in the area's stated scope (**`docs/03` + `docs/06`**, 29 lines) resolves to a row per host. The `clcloud.*` route claims are three-host evidenced because areas B, X, N, U and Z each swept all three hosts on 2026-10-12. **Four candidate findings — none of them in scope, and two of them withdrawn**, and they are the more useful half of the record: **Y-1 WITHDRAWN** — `docs/03:38`'s "all three hosts return the same document" was alleged to be two-host evidenced on the strength of one pass's ledger, and **area X's tracked ledger refutes that**: all three hosts at 20256 B, one digest. **`docs/03:38`** and `01-discovery-pin.hurl` are unchanged from main — `docs/03` does carry **one** other edit from this pass, the claim-#10 method-axis correction, which is unrelated to Y-1. **Y-2 corrected** — `docs/08:37` claimed five hosts while citing `SECURITY-FINDINGS §S3`, which says **"at least twice"**, and labelled it OBSERVED from a file that forbids that label. **Y-3 WITHDRAWN** — `docs/02` was alleged to over-claim a five-tenant comparison; `AUTH-TENANT-FINDINGS §1`'s three tenants *include* trials, and `docs/02` is unchanged. **Y-4** the 2026-10-12 captures are gitignored, so some pages are not re-derivable from a clean clone — recorded, not fixed. **0 requests, 0 cap.** **The lesson the record carries:** two of the four candidate findings (Y-1 and Y-3) were produced by reading **one file as the corpus** — the exact defect area Z's addendum names, written by the pass immediately before this one. It took **three verification rounds** to repair the arithmetic built on the false premise before anyone checked the premise. `audit-index.py --selftest` now asserts its two views read one corpus | [findings-log/2026-10-12-area-y-three-host-audit/FINDINGS.md] | #19 |
| O — is `/patient/reports/*` on `carelink.*` the reports surface for every region? | 2026-10-12 | **Positive, and the area's split does not exist.** All seven recorded paths answer on **all three** patient deployments — `carelink.minimed.eu`, `carelink.minimed.com`, `carelink-trials.minimed.com` — and the responses are **byte-identical across hosts** (one body digest per path, three hosts). 21 of 21 cells reproduce their recorded code: `supported` / `snapshotTimelinesRange` **401**, `generateReport` / `favoriteReports` / `snapshotTimelinesForCalendar` **405**, `reportStatus` **400**, `report` **404**. **24 of a 30 cap**, GET only, controls first on every host, **all 6 passed** — the certainly-absent path `404`s on each host, so the status oracle is sound here (unlike the `clcloud.*` family, where it is uniform and useless) and the `404` is a true absence. **The negative the area anticipated did not occur.** **Two INFERRED premises are now confirmed rather than carried:** the three deployments share the namespace, and the status code is a usable discriminator. **A provenance correction:** the "live, gated 401/405" this area inherited cited a 2026-10-10 sweep whose committed artefact **disclaims itself** — *"a reconstruction from the agent's report"*, evidence *"not reproduced"*, *"re-verify before treating any row as OBSERVED"* ([`DRIFT-AND-NEW-2026-10-10.md:9`](https://github.com/NovaLux12/carelink-api-research/blob/main/findings-log/probe-2026-10-08/recon/DRIFT-AND-NEW-2026-10-10.md)); the bundle inventory it produced names **none** of the camelCase paths; the only committed file naming `snapshotTimelinesRange` is the **archive** table, whose header says the codes are "as archived, **not** as measured live today" (2020-09-29→2021-03-31). So there was no live probe behind "live" — this pass is the first, and it reproduced the archived codes exactly. **Side-findings:** **`Allow: POST, OPTIONS` on all nine `405`s and on nothing else** — 9 of 24 responses, correlating exactly with the POST-only routes. This is a **scoping clarification** of `docs/09` §4's "no `clcloud.*` response carried `Allow`", not a correction of it: that row was already scoped to `clcloud.*` and to "this host family", so a `carelink.*` response carrying the header does not falsify it — it confirms the observation is **family-specific**, and a reader must not generalise it. (`docs/06:27,28,32` already records `Allow` — and its absence — on other patient routes.) Also a **host-aware CSP** that names **`commoncore-trials.medtronic.com`, a host in no prior note**. **⚠ The pass BREACHED the `>=2 s` delay floor** — 21 of 21 same-host gaps fell below it because a declared `DELAY=2.5` was never actually called; not re-run, because a clean re-run would exceed the 30 cap. Its first report of **min −0.538 s** was measured from `run.log` and **understated the breach**: the body-file mtimes give the true **min +0.092 s / max +0.387 s**, and show **no overlap**. It also added **two** backwards-clock-step occurrences (seq 9→10, seq 20→21), not one. Disclosed in full in the log §1a | [findings-log/2026-10-12-area-o-reports-namespace/FINDINGS.md] | #24 |
| D — the 18-country sweep, completed | 2026-10-12 | **Both close conditions met: the sweep is complete AND the contradictions are enumerated.** **118** country codes requested — the offline-derived union of the codes the vendor's own three published config documents enumerate — **117** country documents served, every key given an ABSENT / NULL / VALUED verdict, **33/34/35 keys** by country, **no key outside the 35-key vocabulary**, no report-vocabulary delta. **51 internal contradictions across 10 classes**, the headline being that the recorded two-country `bgUnits` vs `glucoseUnitsDefault` anomaly is **30 of 117** documents (BE reproduces; **CH no longer contradicts**; **IT and ES have drifted into it** since 2026-10-08), so `docs/04` is corrected in place with the original claim left readable. Also: three keys recorded as `null` are **absent** (41 of 117 for `cpMobileAppAvailable`, 115 for `stateCodes`) — `docs/04:377` had been contradicting the repo's own pinned assertion; **`ID` is enumerated by all three configs and refused by the endpoint**; KZ and PR publish a postal regex that rejects the document's own example. **119 of a 130 cap**, GET only, controls first. **Spacing floor 2.575 s with 0 of 118 gaps under the declared 2.5 s and 0 under the `>=2 s` floor** — measured from body-file mtimes, which the kernel sets at write time and which are therefore independent of the harness's own clock (**counting rule: consecutive pairs in `run.log` request order, 119 bodies, 118 gaps**; mtime span 304.9 s equals the harness span, confirming the series is the run's own). The harness `date` series disagrees with it (**1.642 s, 14 gaps under 2.5 s, 8 under 2 s**) because that pass recorded **11 negative request durations**, which is impossible, so those timestamps cannot all be faithful; **no cause asserted**. **Caveat on reuse: git does not preserve mtimes, so this oracle is valid only on the machine that ran the probe** — see [`docs/09`](09-methodology-and-oracles.md) §4. Three defects found in the reader itself are recorded, two of which would have manufactured findings | [findings-log/2026-10-12-area-d-country-sweep/FINDINGS.md] | #22 |
| A — is `carelinkhp` really the clinician portal for every region? | 2026-10-12 | **Negative on the area's premise, and it corrected two published claims.** There is **no `.com` `carelinkhp` variant**: all five `carelinkhp*.minimed.{eu,com}` names outside the baseline are **NXDOMAIN**, including `carelinkhp-prod.minimed.eu` — the only one the corpus had named and never probed. The portal is on **five hosts, two TLDs, two builds**, and the split is **product role** (clinic `pow` vs support `cua`), **not region**: every `.eu`/`.com` pair serves the same build. **Two refutations:** `carelink.medtronic.eu` **is** a portal deployment serving the byte-identical clinic bundle (3,397,615 B, sha256 `2a7fa8e7af519c2b`) — `docs/01:69` and `docs/10` §2 called it a false positive, which was caused by a document-path probe on a host family where **the catch-all *is* the entry document**; and `carelink-support.medtronic.com` serves the **support** build, not "the same document" as `docs/07:24`, `docs/01:68` and SECURITY-FINDINGS §S3 had it. A third correction: `docs/08`'s `sha256 f637c8d0…` is the **entry document**, not `main.759cddab23085086.js` (which is `a054555a0f22176e…`). **20 of a 20 cap**, GET only, controls first per host, 8 DNS lookups recorded outside the cap, measured minimum consecutive same-host gap **2 s over 15 gaps**: all 15 ≥ the repo's 2 s floor, **0 below it**, 11 of 15 ≥ the declared 2.5 s, 4 below it. `run.log` cannot distinguish truncation from a clock step from a post-hoc edit, so **no cause is asserted** for those 4 (`docs/09` §4). Cross-checked with area O's body-mtime oracle, offline and zero-request, over the **10 of 15** gaps whose bodies are committed: **0 corrupt-`t0` signatures, minimum 2.637 s, and all 4 short readings measure ≥ 2.5 s at sub-second resolution** — so no gap in this pass was actually short. That is OBSERVED for this pass only, it is **not re-derivable from a clean clone** (git does not preserve mtimes), and it does **not** answer the open question, which concerns areas B, X and Z. This pass contributes **1 pass / 4 occurrences** to that row's `n`, reconciled by the merge queue, not here | [findings-log/2026-10-12-area-a-clinic-portal-region/FINDINGS.md] | #21 |
| I — Auth0 tenant behavioural differences | 2026-10-12 | **Negative on the difference the area hunted; positive on one it did not name; and it corrected two `kid` strings already published.** The estate is **five** tenants, not four — reconciling "three" (`AUTH-TENANT` §1, a policy axis) against "four" (`docs/11`/`docs/10`, a key-material axis) was part of the pass, and **neither number was an error**: they counted two different sets over the same five hosts, and the union revealed that **`carelink-login.minimed.com` was in nobody's policy comparison** and **`-trials` was in nobody's key set**. **The negative, in its strongest form:** substituting each tenant's own hostname out of its discovery document leaves **one digest across all five** (`sha256:0c0db635f5e9b08b…`, 2640 B) — the same *bytes*, not merely the same fields; **30 field names, 0 absent from any document**, and exactly **12 of 30** differing raw, every one a URL containing that tenant's hostname. That **corrects** `AUTH-TENANT` §1: `registration_endpoint` is **not** a separate difference, it differs only by hostname like the other eleven. **The positive:** `x-ratelimit-limit` is **500 on both `.eu` tenants and 100 on the other three** — 10 observations, 2 per tenant, constant within a tenant, and invisible in byte-identical documents (INFERRED as tenant configuration, on the stated assumption Auth0 treats it as static). **Also:** `registration_endpoint` is advertised by all five and **404 to GET on all five** (`/oidc/register` → 404 `application/json`, 60 B, one digest `f006bbd60894…` across five hosts) — ⚠ **this pass's `registration_endpoint` headline was REFUTED and is RETRACTED**: a verifier showed the endpoint is **live and POST-only**, which a GET-only sweep cannot see, and the pass's own supplementary OPTIONS run then confirmed it on **3 of 5** tenants (`204` + `allow-methods: POST` against a per-tenant `404` + `x-auth0-not-found: 1` control); the trials tenant's key set is fetched for the first time (2 further disjoint kids → **10 keys, 0 shared**, discharging `docs/02` §9's "Unknown"); and **two corpus transcription defects settled against the corpus** — `AUTH-TENANT` §8's `medtronic.com` kid (`…_lLOJ`) is wrong in favour of `RECON-SUBDOMAINS`' (`…_lOOJ`), which **resolves `docs/02` §8's unresolved disagreement against the very spelling it recommended**, and `minimed.com`'s second kid is the live string **minus one `Q`** (a *deletion*, so no second reading existed to compare — invisible to §8's method by construction). **19 of a 20 cap** (17 curl + 2 hurl), **GET only**, plus an owner-authorised **supplementary budget of 14 of which 13 were used** (10 OPTIONS probes + 3 diagnostics) — **32 requests total, no POST anywhere**; controls first per host, **both certainly-absent controls returned 404** (`x-auth0-not-found: 1`, one digest across two hosts) so the oracle held and **no stop condition fired**; measured spacing floor **2.000 s**, which this ledger's **1-second timestamps cannot resolve** against the declared 2.5 s — a lower bound, not a measurement, recorded rather than smoothed over (4th pass in a row). New pins on the trials tenant validated live. Successor: the three remaining advertised endpoints, added under area J **and rewritten on 2026-10-12 to use empty-body OPTIONS rather than GET**, since all three are POST-only by specification and a GET-only successor would have repeated this pass's error three more times | [findings-log/2026-10-12-area-i-auth0-tenant-behaviour/FINDINGS.md] | #23 |
| G — cross-check the three model tables against each other | 2026-10-13 | **Negative: both builds' device tables are identical as data.** The clinic `pow` asset (`main.fb5f8cb7eb60c4d5.js`, 3,397,615 B, sha256 `2a7fa8e7af519c2b`) and the support `cua` asset (`main.759cddab23085086.js`, 3,410,666 B, sha256 `a054555a0f22176e`) were fetched separately and extracted separately, offline: identical code sets (78 table codes + 9 `SKU-*`), identical display-name pairs (76 quoted + 2 unquoted `MMT5100`/`MMT5101` + 9 `SKU-*`), identical whole-file census (80 `MMT-*`, same set), identical module-`90991` `["MMT-8600","MMT-8601"]` array, identical answers on 23 patient-map spot checks — so G's premise is unchanged and the reconciliation stays three-way. **Side-finding:** `MMT-8200`/`8201` ("Guardian™ 4 system") and `MMT-8400`/`8401` ("Simplera™ system") are present in **both** builds' tables, so the patient map is the only compared source lacking them. **6 of a 12 cap**, GET only, controls first per host (fabricated asset → per-build 5518 B fallback; root anchors build digests, both reproducing area A), spacing floor **2.595 s**, 4/4 gaps ≥ 2.5 s | [findings-log/2026-10-13-area-g-device-tables/FINDINGS.md] | #32 |
| J — `login-errors.ts` against the live error surface (addendum: the three advertised Auth0 endpoints) | 2026-10-13 | **One routed, two dangling — uniform across all five tenants, no shadow split.** `/mfa/challenge` answers the preflight `204` + `ACAO: *` + exact `allow-methods: GET, PUT, POST, DELETE, PATCH, OPTIONS` on all five (the path with no probe result in any source was live); `/bc-authorize` and `/oauth/global-token-revocation/connection/Auth0` are unrouted on all five — preflight byte-identical to per-host one-character-different controls (one 10 B digest `0802559db137…` across 15 bodies). POST-only-ness of `/mfa/challenge` is INFERRED from specification, not established — no POST sent, and the six-method list is a second live instance of `docs/09` §4's allow-methods trap. Revocation verdict scoped to the `Auth0` connection name. ⚠ **Correction history preserved:** this addendum was written 2026-10-12 as a GET sweep on area I's then-claim that `registration_endpoint` was absent everywhere; a verifier refuted the premise (the endpoint is live and POST-only) and the addendum was rewritten to empty-body OPTIONS before probing — the original wording is retained in the area-I log, not here. **23 of a 26 cap** (20 curl + 3 live hurl pin-validations), GET + empty-body OPTIONS only, controls first per host, all 5 passed, measured `t_sent` floor **2.395 s** (all gaps ≥ 2 s floor; 2 under the declared 2.5 s and 4 negative durations recorded with no cause asserted). EU cells pinned (exact allow-methods, not contains); counts re-measured 193→199 static, 401→413 execute. Successor: the parent half (bridge `login-errors.ts` taxonomy vs provoked errors) as a new `docs/10` §1 row | [findings-log/2026-10-13-area-j-advertised-endpoints/FINDINGS.md] | #34 |
| H — the `reportFileNamingSupportedPumpModels` list, entry by entry | 2026-10-13 | **Positive with residue: 214 entries classified, 86 rows matched, 128 not.** The list lives in the **patient** public config (`personal.common.core.report.generation.reportFileNamingSupportedPumpModels`, 69-key document, re-derived live) — not HCP-only as the area premise had it. In code: wire code 129 · display name 71 · bare number 10 · placeholder 4; 82 wire codes matched by family, 47 unmatched by prefix group; placeholders 4/4 matched (all INSTINCT values); bare numbers and display names 0 matched; normalization changes nothing. Anomalies: `MMT-9015` ×2, `Precision Xtra® / Xceed™` ×2, one trailing-space entry matching the map's own padding exactly, ten `MMT-`+bare pairs. Correction attached in `docs/05`: `MMT-8200/8201/8400/8401` are in **both** report lists and **neither** family table. **5 of a 6 cap**, GET only; 3 hp-namespace requests voided by a harness header defect and disclosed as wasted — the close rests on the patient document alone | [findings-log/2026-10-13-area-h-report-naming/FINDINGS.md] | #33 |
| V — given that `baseUrlPde` names a dead namespace, does any vendor client follow it? | 2026-10-13 | **Negative, and the reason is sharper than the area expected.** No vendor **web** bundle contains `baseUrlPde` or `/connect/pde` — and no `baseUrl*` key, `discover/android`, `clcloud` or `api/carepartner` is present either, because **no web bundle in the corpus reads the discovery document at all**. ⚠ **corrected 2026-10-13**: the bare `discover` token **is** present — **12 in each portal build**, every one a zxcvbn password-dictionary word at identical bytes, so the portal builds carry **17 dictionary hits each** (12 `discover` + 5 `pde`) and none is a pointer; this row first published `discover` as 0 [findings-log/2026-10-13-area-v-pde-clients/FINDINGS.md §Correction (2026-10-13) §A]; the two `baseUrl` hits in the patient bundle are `this.baseUrl = getBaseCmsUrl()`, a CMS media base. Every `pde` hit is accounted for: **5 per portal build, all zxcvbn password-dictionary substrings** (`dropdead`, `helpdesk`, `herpderp`, `topdevice`, `hampden`); **0 case-sensitive in the patient bundle**, whose 25 insensitive hits are 7 unrelated identifiers. **INFERRED, and stated as the limit not the finding:** the consumer is the *mobile* client the document's own path names (`discover/android/3.6`), so “does a client follow it” stays **unobserved in both directions** and `docs/03` §9a's reading is unchanged. **Positive on the sibling pointer:** the patient bundle **follows** `csr.cumulus.periodic.data.endpoints` — 1 genuine read, `display_message` destructured and **POSTed** with `{patientId, role, username}` — while naming `system.gc.gz.transition.flags`, exporting its selector as `z2` and reading `.z2` **0 times in the file**; all nine of its leaves are 0 hits everywhere. Also: **56 of 69** published config keys appear as quoted literals in the patient bundle (raw-substring counting would have said `captcha` 152 times, not 5); patient `.eu`/`.com` are byte-identical; both portal digests reproduce areas A and G; the patient build and its **211-chunk map reproduce the 2026-10-08 record**, so it has not bumped. **13 of a 24 cap**, GET only, 8 controls first per host, measured `t_sent` floor **2.566 s** (9 gaps, 0 under 2.5 s) cross-checked by kernel body-mtimes at **2.599 s** — ⚠ **the mtime figure is not re-derivable from the committed ledger**, because `results.jsonl`'s `body_mtime_epoch` came from `stat -c%Y` (whole seconds) and git does not preserve mtimes; the `2.599 s` is re-stat'ed from bodies still on disk by `spacing.sh`, so the load-bearing floor is the millisecond `t_sent` series, which reproduces from `results.jsonl` alone. Spans agree to 15 ms and no negative durations were recorded. Successors: dated addenda to **area F** (timeline-host key named by the bundle but not published) and **area K** (the 211 patient chunks are not K's 224 portal chunks) | [findings-log/2026-10-13-area-v-pde-clients/FINDINGS.md] | #42 |
| W — is the per-key projection a complete enumeration path for the 69-key document? | 2026-10-13 | **Negative, and it closes the area: the key sets are identical on EU.** All 69 bulk names probed per-key plus `captcha`'s four flat-name subkeys — **61 VALUED-match**, 5 NULL-404 (every null-valued key), `captcha`/`default.country` 404 via their dedicated routes, **zero names outside the bulk document**. The per-key form is a projection, not an enumeration path — the `docs/04` framing is retired, not extended. **77 of an 84 cap**, GET only, controls first, measured spacing floor **2.574 s** by kernel body-mtimes (0 of 76 gaps under 2.5 s); the harness `date` series shows 3 sub-floor gaps with 3 negative durations, the known corrupt-`t0` class (`docs/09` §4), no cause asserted. **Side-findings:** `personal.common.core.reporting.enabled.countries` does **not** round-trip — its value carries a stray trailing `]` (reproduced byte-identical on re-issue); real-key 404s carry **no `content-type`** while the certainly-absent control carries `text/vnd.a`; the 35 country keys and 69 bulk keys are **disjoint vocabularies**; and the complete 69-name list is committed (`keys.txt`) for the first time. Successor: dated addendum to area E (remaining two deployments) | [findings-log/2026-10-13-area-w-per-key/FINDINGS.md] | #31 |
| M — is Common Crawl's zero on the API surface real, or was it the method? | 2026-10-13 | **Partially refuted, and the correction is to the METHOD.** Re-derived through the **CDX index API** instead of computed byte offsets, across **six named crawls with dates**, **all four controls first**, both absence oracles established behind their own positive controls. **Refuted:** CC holds **24 records for `minimed.eu` across 5 of the 6 crawls** (8 / 6 / 5 / 2 / 3 in 2018-39 / 2020-50 / 2022-40 / 2025-30 / 2026-39, incl. `/ipro/hcp/login.jsf` **200** on `carelink.minimed.eu` @2020-12-02), and **`medtronic.eu` is non-empty in all 6** — against `COMMONCRAWL §1`'s own table recording `eu,medtronic)` = 0 blocks in the two crawls it used. **Confirmed, for a different reason:** **no captured path in any of the six begins `/patient/` or `/connect/`**, and `clcloud.minimed.eu` / `carelinkhp.minimed.eu` hold **zero**, established by *enumerating* the successful domain responses rather than by their own failed host queries. **So "essentially zero coverage of the API surface" stands; "not one record for any `carelink*` host" does not**, and "in either of two crawls" was a budget artefact — `CC-MAIN-2024-42` really is zero (404 `No Captures found`) and the other five are not. **Offset method, corrected at the mechanism:** of the three byte ranges `COMMONCRAWL §1` records, **one reproduces exactly at both ends, one starts exactly on its bound but overshoots its recorded end into `com,medtryck)`**, and one could not be fetched at all (`503 SlowDown` ×2) — the *opposite* defect from the recorded "alphabetical neighbours" one — and **the first pass's ranges are not re-derivable, because the record names no offsets**. **Side-findings:** the API **failed 17 of 61 (28%)** — 502 / 504 / 400 / 503 — so **one query never settles a zero**. ⚠ **CORRECTED 2026-10-13 (verifier round 1): this row originally read "with **0** failures against known-covered hosts". That was false — `seq 50`/`53` asked for a host `seq 42` had proven covered 32.6 s earlier and both failed.** Under the counting rule in `failclass.py` (only a **record-form** query names a host, so classify by what the ledger knew *before* the row was sent) the 17 split **2 covered / 0 absent / 13 indeterminate / 2 n/a**: **a gateway error on a host whose coverage was never established carries no information in either direction and must be re-issued, and coverage is not a shield either.** `index.commoncrawl.org` answered **200** here on 2026-10-13 (128 crawls published), recorded as an observation about *this host at this time* and **not generalised**. **61 of a 64 cap** (60 under the claim, **1** under owner authorisation for the overshoot re-read; **3 recorded as unspent**), GET only, **zero requests to any Medtronic host**, measured same-host floor **2.873 s** by kernel body-mtimes, cross-checked at **2.736 s** from `t_sent` (0 gaps under 2.5 s on either oracle). **No `regression/hurl/` pin** — those suites are vendor surfaces and `AGENTS.md` §11 bars one research pass from widening the gate's budget; the rot-prone half is pinned as `docs/09` §4 traps instead. Successor: dated addendum to area L | [findings-log/2026-10-13-area-m-commoncrawl-cdx/FINDINGS.md] | #44 |
| S — two more evidence classes for third-party source material | 2026-10-14 | **Closed on a negative, and the negative found 12.** `AGENTS.md` §2.1 now states the independence rule (added 2026-10-14 by issue #105) and SOURCE-OBSERVED / SOURCE-PUBLISHED remain **corroboration descriptors, not ranks** — option (b) of the area's own close condition. Close condition (a) was already met. What the addendum called "what remains" was the **audit**, and it then ran at **0 requests, 0 of a 0 cap**. **Population counted before it was read:** every occurrence of the eleven phrases `AGENTS.md` §2.1 names, across `docs/*.md` + `README.md` — **68 occurrences on 49 matching lines**, plus **14 on 7** in `AGENTS.md` counted separately as rule text; **6 of the 14 in-scope files carry zero**. ⚠ **The first pattern had no left word boundary and matched `disagrees with` ⊃ `agrees with` — the opposite word — in 3 places**; the superseded count 71/52 is kept beside the corrected one. **Result: 12 live strength-word claims failed §2.1, all at independent count 1, and all 12 were relabelled** (`README.md:50`; `docs/03:241` ×2, `:400`; `docs/05:331`; `docs/09:194`; `docs/10:45`, `:64`; `docs/11:720`, `:1006`, `:1183`, `:1496`, `:1627`). **The recurring shape was one and it is the failure the rule was written for: two artefacts, one producer** — areas O and E on a **byte-identical** CSP line, areas B and U on one no-route digest, five Common Crawl queries by one observer, two read sites inside **one** client chunk. **Three claims survive, each on a count that is real:** `docs/10:37` (**3** — three named clients at three commits), `README.md:340` (**≥2**, enumerated on the line), and `docs/03` §3a.4 **newly, at 2**. **One claim moved from count 1 to count 2 and only reading the artefact could find it:** area Q read PR #4711's three *comments* and correctly found the boundary table to be one source stated twice, but never read the PR's *author* — `bodies/16-xd-pr4711.b` records `user.login: m0rt4l1n`, a **second person** whose body reports testing on 780G+Guardian 4 and InPen+Simplera and never quotes `CarlosJPV`. So "`3.8.0` is accepted by the body gate" now clears §2.1; **where the boundary sits stays at count 1.** **Stated as a limit, not a claim of completeness:** `docs/`, `README.md` and `findings-log/` are covered; `CONTRIBUTING-research.md`, `SECURITY.md`, `regression/`, `scripts/`, `.github/` and `PR.md` are **not audited**; inside `findings-log/` (append-only, §3) **4 claims FAIL and are flagged unedited**, including the 12-entry-type vocabulary called *"double-sourced … two independent surfaces"*, which is **Medtronic twice** and so count **1**. §2.1's own text has **two gaps** this pass recorded rather than resolved — negated strength words, and its exact-string vocabulary missing `corroborates`/`corroborating`/`corroboration`/`confirmed`. **Nothing was pinned and nothing was added to the gate**: a §2.1 check is a maintainer decision (`docs/09` §4, and the note above on extending the gate's own patterns in the PR the gate passed). **A negative counts, and this is one** — a sweep that found 12 and fixed 12, not a sweep that found none | [findings-log/2026-10-14-pool-s-independence-audit/FINDINGS.md §0–§6] | #125 |
| S6 — Common Crawl public host/path inventory, and is a domain result set complete? | 2026-10-14 | **The completeness half is answered and it is a negative: this API truncates, so a large Common Crawl record count is a LOWER BOUND whenever its byte count is an exact multiple of 1024.** ⚠ Scoped deliberately: the detector has been run over **this lane's ledger only**. Whether other passes' committed counts are floors is **unmeasured** — `docs/10` row 65 carries that as the open successor. An earlier draft of this row said "every large count in this repo", which the row it points at contradicts. The **identical** query — `CC-MAIN-2026-39-index?url=medtronic.com&matchType=domain&fl=url` — answered **5 108 records at exactly 655 360 B (640.0 KiB)** and, **18.8 min later**, **10 942 records at exactly 1 228 800 B (1200.0 KiB)**. The second is a strict superset of the first (every host the first carried, plus 22 more, each sorting earlier in SURT order than every one of the 13 still unreached). A published crawl index does not change between two queries 18.8 min apart, so **at least one was cut short**. ⚠ **but it is NOT a SURT-ordered prefix and that claim is withdrawn**: its furthest host is `www.medtronic.com` at rank 36 of 37 while **12 of the 13 unreached hosts sort before it** — under the canonical SURT key, in which the apex sorts before its subdomains; the numerals are **not** convention-invariant and `FINDINGS.md` §2 states the rule. The conclusion rests only on the byte-identical query returning different counts at two 1024 boundaries; **what produced that ordering is not established**. **Detector (OBSERVED): a record response whose byte count is an exact multiple of 1024 was truncated** — exactly 3 of the ledger's 29 successful answers sit on a whole-KiB boundary (32.0 / 640.0 / 1200.0 KiB) and all three fail to run to completion (for the 32.0 KiB cell that is INFERRED from `pages: 3`, not observed); the other 26 sit on none, and the small ones reproduce byte-for-byte (412 B, 35 226 B, 19 301 B each appear twice, identical). One arithmetic test now audits any committed CC row. **A count in THIS LANE'S OWN ledger is a floor, not a correction to the corpus:** `CC-MAIN-2022-40 / medtronic.com` = **203 records (seq 74)** was **never published** — `git grep '203 records'` at `origin/main` returns **0 hits**, area M's published figure for that cell is `blocks: 14`, and seq 74 belongs to this lane's own earlier attempt, which lands in this same PR. An earlier draft of this row called it "area M's" and "a published figure"; both were wrong and are corrected here. Only **two** re-issues (seq 149, 151) touched that cell; seq 150 re-issued a different one. All three answered **504**, so the ceiling there is **unconfirmed** and the figure stands as a floor. **Method correction to this row's own successor premise:** the field-width invariance test is **not** a truncation detector here — a *narrower* `fl` returns *fewer* records, the opposite of a ceiling; it corroborates only where the response completes (`2015-48 / medtronic.eu`: 132 records at both 19 301 B and 49 350 B, a 2.56× size spread, medium reproduced byte-for-byte). **Mechanism and bound of the ceiling: NOT established** — a proxy cap, a server emit-budget and a client read-cutoff all fit; no cause asserted. **Host inventory:** the 11 522-record `medtronic.com` set on `CC-MAIN-2026-39` (37 hosts, byte count not on a KiB boundary) carries **five host names absent from every tracked file at `origin/main`** — `synchromed2battery.` (label reads as the retired *SyncMed 2* line — **INFERRED, no repo source;** `git grep -i synchromed origin/main` is 0 hits), `e-thoth.`, `oab.`, `bakkeninvitation.`, `kappasigmasnlist.` — which are **candidates for a DNS-only pass, not assets** (counting rule: `git grep -il <name> origin/main` over **all** tracked files, not a subset of extensions — 0 files each; the wording is "absent at main", not "nowhere": at this head all five appear in **2 files each** — `FINDINGS.md` and `results.jsonl` — and **none** in this row, which uses abbreviated forms): presence in a crawl index means a crawler *encountered the name*, not that it resolves or is operated. **Path prefixes:** `/connect/` absent from `medtronic.com` on 2022-40 is **anchored** — that cell is proven non-empty (203 records, seq 74). ⚠ **This is a NEW negative, not a reproduction of area M's claim**: area M's `/patient/` + `/connect/` finding is scoped to **`minimed.eu`** ("across **every** capture recovered for `minimed.eu`"), while this sweep covered only `medtronic.eu` and `medtronic.com` and has **no `minimed.eu` cell**. Area M never enumerated a path on either `medtronic.*` host either — its only record-form queries there are `limit=5` controls. The two pass over different hosts, so this reproduces **none** of area M's cells. The second `/connect/` absence, `medtronic.com` on 2013-48, is **UNANCHORED**; an earlier draft of this row called it anchored on the 112 records of seq 65, which is `medtronic.eu`, not `medtronic.com`. `/ipro/` and `/hcp/` absent from `medtronic.eu` on 2013-48 are anchored, on seq 65. **25 of 30 path-prefix cells answered 502/504 and are unmeasured, not negative**. Three of the five answers are **anchored** (a record-form query on the same cell returned 200). Two are **UNANCHORED** and must not be cited as absences: `2026-39 / medtronic.eu` `/oauth2/` (seq 118) and `2013-48 / medtronic.com` `/connect/` (seq 139) — for the latter the only domain query on that cell is seq 66, which answered 504. Sequences 65 and 66 are the whole of this lane's coverage of **those two cells** — one per host group, not two on `medtronic.com`. **151 of a 400 cap**, GET only, **zero requests to any Medtronic host**, controls first and all three passed (covered host → 5 records, RFC 2606 `.invalid` → 404 true zero), measured same-host floor **2.941 s** (`t_sent`) / **3.123 s** (kernel body-mtime oracle — **not re-derivable from a clean clone**: git does not preserve mtimes and the raw bodies live outside the repository; the `t_sent` figure is the one that reproduces from `results.jsonl` alone), 0 of 74 gaps under 2.5 s, no overlap, **`curl_exit` was hardcoded to 0 on all 151 rows and is not a measurement** — see `FINDINGS.md` §7. **Disclosed defects in the earlier attempt on this claim:** **30 requests wasted** on `\&`-escaped ampersands (all 30 answered 400 `{"message":"output=json\ not supported"}`) and **5 rows recording `t_done` before `t_sent`**, cause not established; both are confined to seq ≤ 28 and this pass's own 75 rows are clean on every check. **No `regression/hurl/` pin** — the suites are vendor surfaces and `AGENTS.md` §11 bars one research pass from widening the gate's budget; the rot-prone half is the whole-KiB test, which is pure arithmetic over a committed ledger | [findings-log/2026-10-14-lane-s6-public-index/FINDINGS.md] | #95 |
| E — is the per-key projection identical on `.com` and `-trials`? | 2026-10-13 | **Negative on the key set, and that is the answer: the 69-name vocabulary is deployment-portable.** All 69 names plus `captcha`'s four flat-name subkeys swept on both remaining patient hosts — **69 top-level keys on each, 0 outside the committed EU list, 0 of the EU list missing**, and **0 value mismatches across 123 valued cells** (62 `.com` + 61 trials VALUED-match), so the per-key form is a projection on all three deployments and the `docs/04` framing is retired rather than extended. **What is *not* identical is which keys 404** — and it is downstream of the bulk null set, not the grammar: EU and `.com` share the same five null-valued keys name for name, trials has six, adding `mmm.data.api.url`, `personal.linking.request.interval` (in no `docs/` page) and `personal.third.party.apps`. **Two positive findings area W could not have had.** (1) **The stray-`]` quirk does not reproduce** — `personal.common.core.reporting.enabled.countries` parses cleanly on `.com` (2 countries) and trials (13), matching their bulk subtrees exactly; the defect is EU-only as measured, and *EU-specific* and *length-dependent* are both left standing because nothing observed separates them. (2) **⚠ Area W's 404 content-type split does not hold on trials** — one real-key 404 there carries `application/vnd.nervana`, a value in no prior reading, so the header is three-valued and deployment-dependent and "the control carries `text/vnd.a` and real keys do not" is false on one deployment of three; `docs/04`'s standing "do not discriminate on it" is confirmed and strengthened. **152 of a 170 cap**, GET only, **all 4 controls first per host** reproducing W's shapes exactly (404 `text/vnd.a`; 200 `application/json` 281 B), measured spacing floor **2.020 s** by kernel body-mtimes (0 of 150 gaps under the ≥2 s floor); the harness `date` series shows 4 sub-floor gaps and **13 negative durations**, the known corrupt-`t0` class, no cause asserted. Successor: dated addendum to area F — the two dedicated-route escapes were read on `.eu` only | [findings-log/2026-10-13-area-e-perkey-deployments/FINDINGS.md] | #41 |
| Q — the `appVersion` body gate — a second version axis our docs do not describe | 2026-10-13 | **Closed on the area's second close condition: recorded as community-reported-and-unverifiable, with the reason.** The two axes are now documented together in `docs/03` §3a. **Mechanism confirmed in code**: `appVersion` is a **body** field, at `CarlosJPV/carelink-cumulus-bridge src/carelink/cumulus.ts:146` @ `0180b89` (SOURCE-OBSERVED). **Boundary values not confirmed and not confirmable here** — a body field needs a POST, `AGENTS.md` §11 permits no vendor POST beyond the two already-pinned public-`client_id` requests, and the author's probe *outputs* are gitignored (`.gitignore:12` resolves exactly), so **no pin is possible either** — the claim is unpinned by necessity, loudly. **The finding the area did not ask for:** for the `X.Y` forms the discovery axis has been probed at, the two constraints **intersect in exactly `{3.7, 3.8}`** (`3.7.0`/`3.8.0` clear the body gate but are **unobserved** on the discovery path — no `X.Y.Z` cell was ever probed), and the readable client feeds **one constant** (`'3.8'`, `cumulus.ts:31`) into **both** axes — correct only because `3.8` is in that window, so raising it to `3.9` satisfies the body gate forever and breaks the discovery axis silently. **Zero drift**: all four subject files byte-identical between pinned commit and branch head (blob SHAs), so every `file:line` resolves identically in either revision. **⚠ Correction:** the area's *"corroborated by a xDrip maintainer on PR #4711"* is **withdrawn** — that PR's three comments are the table (**by the same author as the README that repeats it**), a question, and an approval that does not retest it, so it is **one source stated twice**. **21 requests against a cap of 20** — the overrun is **one** request, because `probe-followup.sh` sets `SEQ=18` rather than reading the ledger and was run twice, re-issuing request 19; **no ledger row was deleted to hide it**. **The cap was restated to 21 by owner authorisation on 2026-10-13, after the pass**, so the log's accounting line reads `21 of a 21 cap` with the declared 20 kept readable in its `## Correction (2026-10-13)`. 0 requests to any Medtronic host, by design. Spacing floor **2.765 s** (kernel body-mtime oracle, 18 measurable gaps, 0 under 2.5 s; harness series disagrees at 2.014 s with 3 impossible negative durations — no cause asserted). **Not verified:** the xDrip `CareLinkClient.java:664` half — the file is not at the package root, and that is **this pass's path-reconstruction error**, not a broken citation. Successor: dated addendum to area S (what *independently corroborated* requires) | [findings-log/2026-10-13-area-q-appversion-axis/FINDINGS.md] | #43 |
| L — recovery of the retired `ipro/hcp` JSF surface, and the census under it | 2026-10-15 | ⚠ **SUPERSEDED IN PART by the 2026-10-15 continuation below — the first pass's "negative seven times" counted 9 first-read crawls; the completed census reads "absent from 65 of the 84", and the family has dates in 2017, 2019, 2020 and 2021 that this row predates.** First pass alone: **Positive twice, negative seven times, and the 2022 end is now a capture rather than an absence — which refutes the "bounded 2020 deployment" reading this area carried.** **40 of a 40 cap**, GET only, **`index.commoncrawl.org` alone, zero requests to any Medtronic host**, ≥ 3.5 s inside `flock`, measured `t_sent` floor **4.272 s** over 39 gaps (0 under 3.5 s, 0 under the `>=2 s` floor, 0 negative durations; kernel-mtime oracle 4.035 s). **13 crawls, every cell classified** under the counting rule — a cell reads as an absence only if some row for that crawl answered `200`, and a failure is labelled a failure: **9 records / 3 readable absences / 1 indeterminate**, with **15 of 40 rows failures** (502 ×10, 504 ×3, 400 ×2 — 38%) and **12 retries, each a request and each with a row**. **New:** `CC-MAIN-2014-15` holds **four** `/ipro/hcp/login.jsf` captures, all April 2014, all **200** (2014-04-17 / 04-23 / 04-24 ×2) — the densest cell in the corpus and the only one with repeated captures of one path on one crawl; `CC-MAIN-2022-27` holds `/ipro/hcp/index.jsp` @ **2022-07-03** **200**, **past** the 2022-05-13 archive end and past `CC-MAIN-2022-21` (window 2022-05-16 → 2022-05-29), the crawl the old reading rested on. **The disputed `CC-MAIN-2022-05` cell is settled:** control 504 → **200 / 5 records** → `minimed.eu` **404** immediately after, in one pass — a readable absence; **both prior readings stand unretracted** (the 7crawl Correction records that *its own* re-issued controls 504'd; #104 ran a control but sent no probe). Host-scope cells on `-2013-20` and `-2021-04` promoted to readable absences, discharging `early-crawl-reissue:107-111`. **The negative:** in **7 of the 9** crawls **first read** it did not appear at all — **8 of 9 would be wrong**, because two of the eight classified cells *do* carry members; over classified cells only it is **6 of 8**, the indeterminate cell being the whole difference. **`CC-MAIN-2014-23` is indeterminate** — four control rows, two control hosts, no `200` — and a third failure shape joins 502/504/503: a Python `400` carrying `ConnectionResetError` **and** one carrying `RemoteDisconnected`. **⚠ This pass retracted its own denominator, and its first explanation of that retraction was half wrong:** comparing dashed timestamps against a dashless bound made **two opposite** errors — `-` `0x2D` sorts below both `0` `0x30` and `2` `0x32`, so it dropped the 2 crawls of 2013 *and* wrongly included all 5 post-window 2022 crawls, 84 − 2 + 5 = **87** where the answer is **84**, reproducing `area-l-ipro-hcp:313-317` exactly. Comparing `YYYY-MM-DD` on both sides gives the same 84, so full timestamp precision is not required and what is forbidden is comparing two different string shapes. `AGENTS.md` §6 item 3, caught only by re-derivation; no probe, cell or verdict was affected. **`CC-MAIN-2022-27` is outside the window** (2022-06-24 → 2022-07-07): 9 crawls first-read, **8 in window** — and it is *precisely because* it sits after the window that no in-window 2022 crawl had carried the family. **Not claimed:** "absent from Common Crawl" — **64 of the 84** in-window crawls remain unread. A tenth selection, `CC-MAIN-2018-05`, was **never queued** (no `q-*.tsv` line, no row, no header); what the cap blocked was the **retry of seq 40**, whose `502` wanted a re-issue. Successors S-L1 (`cluster.idx` served-ness), S-L2 (the remaining census) and S-L3 (a denominator check) are dated addenda above | [findings-log/2026-10-14-pool-l-ipro-hcp-census/FINDINGS.md] | #126 |
| P — recover the request schema from the vendor's own app, statically | 2026-10-13 | **Partial positive, asks (a) and (b); documented negative on the validation-config field set.** Static pass over the hash-pinned patient bundle `0fb4fbd4…` (3,417,255 B), both portal bundles (`2a7fa8e7…` / `a054555a…`) and its 211 lazy chunks, **0 requests**: (a) per-entry logbook submission payload recovered in lazy chunk `k-9799-ae484032a07c9d4f-js.b` — `entryTs`, `type`, `id`, `comment`, `sensorInsertionInfo { sensorLocation, otherSensorLocation, timeCapUnscrewed }`, `removalInfo { sensorLocation, otherSensorLocation, removalType, removalReason, removalDescription }`, plus `physicalDisturbanceInfo`, `medicationInfo`, `adhesiveAndTapeInfo`, dynamic `attributes`; **casing correction `timecapUnscrewed` → `timeCapUnscrewed`**, and `sensorInsertionLocation` is a form-control, serialized as `sensorInsertionInfo.sensorLocation`. (b) `deviceFamily` routing-discriminator casing = client enum `{ BLE, BLE_X, SIMPLERA, SIMPLERA_X, GUARDIAN }` (bundle module 45559 / byte 1,723,245, compared at byte 2,964,121) — candidates for area R, still client-side. (c) **negative**: `system.logbook.entry.validation.config` occurs only as a route literal (offsets 2,768,979 / 2,769,017) and once in the patient config-key registry (`D.logbookConfiguration`, offset 2,190,314; selector `yt` at 96,883), with no field set. `alarmCode` occurs 0 times in patient + portals + 211 chunks. Compensating: NGP `lastAlarm.code` is a **number** on the wire (chunk byte 76,314 / 87,560), settling the shape half of `docs/10` row 39. Prior negative `findings-log/2026-10-13-area-p-static-schema-recovery/FINDINGS.md` preserved as pass 1 | [findings-log/2026-10-13-area-p-static-schema/FINDINGS.md] | #80 |
| F — what the timeline and dialog-lite gateways actually are | 2026-10-14 | **Closed NEGATIVE on the letter's own condition — no caller named, because none exists in the corpus, and no third-party client can reach either service by GET.** The caller half is a **structural** negative, not an absence of evidence: both portal builds were re-fetched on their content-hashed asset names and **reproduce their pinned anchors in full** (`2a7fa8e7af519c2b…` 3 397 615 B; `a054555a0f22176e…` 3 410 666 B), and in **both** bodies `patient-timeline`, `dialog-lite`, `app-patient-timeline`, `patientTimeline`, both `personal.patient.timeline.*` spellings, `execute-api`, `prodous`, `/patient/`, `clcloud`, `carelink.minimed` and **all five 10-character gateway ids** are **0** — while **`personal.` is 4 hits and not one is a key of the 69-name patient document** (`hcp/patients` 42, `hcp/configuration/public/` 15). **Neither build reads the patient configuration document at all**, so the pointer is unreachable from that code and no server-side proxy can exist there to follow it; that also settles the letter's "look for a proxy in the portal bundle" reading. **The `BLOCK 7` cells that had never run ran and are negative: 11 of 11 `patient-timeline` cells answer `403` `MissingAuthenticationTokenException`, 42 B, one digest `f249b63cb2fcb66b47e86f906c98f8fd912e82dd035b4e53d7e72fc1960cfd16` — which reproduces this repo's published `f249b63cb2fc` IN FULL — with the certainly-absent control byte-identical to every plausible path on all three deployments, so under Oracle A there is **no matching GET route**. Zero 404s in 17 requests, so that clause is observed on this family directly rather than by analogy from `clcloud.*`. `dialog-lite` 500s on all 4 cells with one body digest (`660f19c0…`, 36 B, **new** — the 2026-10-10 pass recorded the size and no digest) and the certainly-absent control is byte-identical to the published root on **both** regions, so **the 500 cannot discriminate the path**: it is the catch-all's signature. Zero of 15 gateway responses carry `Access-Control-*` and the header set is still the same six keys, so "neither is browser-callable" is **re-observed, not re-derived**. **Most reusable number:** `timeline` scores **196** (66+126+4, 74 signatures) against `patient-timeline`'s **0**, and all 196 are GSAP / Pusher internals, Medtronic's own snapshot-timelines **report** service, two leaked-password words, or one analytics label — `docs/09` §5's false-positive class quantified on the exact token this area hunts; a right-context census pattern returns **189** and that figure is a defect of the pattern, not a count. Counting **per build**, as `grep-out.txt` does: the `m2m` hit the letter proposed is **1 in each build** (2 across both) and falls in the **middle** of `cum2me`, inside a leaked-password list; `baseUrl` is **2 in each build** (4 across both), every one an embedded Pusher SDK. **17 of a 40 cap**, GET only, 7 hosts, ≥2.5 s same-host, **controls first on every host**, no POST, no token exchange, no authentication. Spacing floor **2.239 s** on the `t_sent` series (1 of 10 gaps under 2.5 s, **0** under the ≥2 s floor) with **one negative duration** (seq 9, −552 ms — the known corrupt-`t0` class, **no cause asserted**); the kernel body-mtime oracle reads **2.866 s with 0 sub-2.5 s gaps**, so no gap was actually short, and that oracle is **not re-derivable from a clean clone**. ⚠ **NOT closed, and this row does not claim it:** the **three readings of the 403s** (no routes / other verbs only / the live stage is not `prod`) need an authentication attempt, excluded by `AGENTS.md` §8/§11 — four more cells went into that dead end and did not move it, and `docs/10` §1 carries the row unchanged. Also unchanged: *why* `dialog-lite` raises, and whether the raw `…timeline.config.host` value is publishable — **a disclosure judgement for a maintainer holding the value, not pre-committed here**. **Scope limit:** three builds exist and only the **patient** build has ever named the timeline at all (there every hit is an Angular component selector; area V, cited not reproduced, since `carelink.minimed.eu` is outside the claim's host set), so the negative's scope is *no web caller in any of the three builds this repo has read* (**INFERRED**, a corpus claim, not a claim about every client). **Pinned:** the EU `keys | length` = 69 assertion, **zero extra vendor requests**, completing the third copy. **Not pinned:** the gateway cells — the `execute-api.*` hosts are in no suite and adding them would widen the drift sweep's vendor budget from a research pass. Successors: the **portal lazy-chunk corpus** (224 chunks, never swept for these tokens) and the new pin's stated limit (**count ≠ set**) | [findings-log/2026-10-14-pool-f-timeline-caller/FINDINGS.md] | #123 |
| R — reconcile the `deviceFamily` correction against the client consensus | 2026-10-14 | **Negative, on the area's second close condition: the value's casing stays UNOBSERVED, and `docs/05` now says so with the reason.** **0 requests of a 0 cap** — no vendor host was touched and no request of any kind was made, because a zero-request pass cannot have an oracle and this one did not manufacture one. Three findings, and the second is the one that mattered: (1) **The reconciled candidate set is 21 strings under a counting rule stated before the number** (three admitted sources hold 27 between them; the difference of **6** is duplicate **occurrences** across **5** distinct shared tokens — `SIMPLERA` is in all three sources — and the sum is printed beside the union so it cannot be mistaken for it). Every member is *extracted from a committed artefact at a named `file:line`*, so the denominator is re-derivable from a clean clone and an anchor that stops resolving exits non-zero. ⚠ **Unpinned, stated rather than left to be discovered:** the suite guards only the **map axis** — `regression/hurl/05-public-config.check.sh` pins `family count is 16`, which this pass independently re-derived — while **nothing pins the union 21, the sum 27, or the `S-CLIENT-DTO` exclusion**. A pin was considered and declined: a new `check` site moves the static count and every site that states it, and `docs/09` §4 records that widening a gate pattern in the same PR the gate passed is a maintainer decision. The gap is the re-derivation script, not a pin. (2) **One of the three candidate vocabularies the area inherited fails the provenance bar the pass sets for itself** — the third-party set `GUARDIAN`/`NGP`/`CGM`/`CC` is recorded at `findings-log/probe-2026-10-08/APP-EMULATION-RESEARCH.md:384-385`, inside a section headed at **`:349`** — *"Round 3 — the full `RecentData` payload schema (from xDrip's message classes)"* — which names **no `file:line` and no named commit**, so `CGM` and `CC` are **not admitted** and the union is **21, not 23**; the repair is one cite, since the 2026-10-11 pass read xDrip at `366c97a8`. (3) **The three vocabularies are not one vocabulary with disagreements** — the 16 map tokens are a *published identifier axis*, the client's 5 enum + `NGP` a *prefix-matched routing classification*, and the third-party four a *product-role DTO enum*; measured overlaps are `{SIMPLERA}`, **none**, and `{GUARDIAN}` respectively, so under the client's five `startsWith` tests `CGM`/`CC` match nothing and under the third-party four `BLE`/`SIMPLERA` match nothing (INFERRED, assumptions stated). **The audit re-counted every surviving `deviceFamily` claim against `AGENTS.md` §2.1 and one was deleted outright**: `docs/05`'s "appears as a call-site field name in the lazy-chunk corpus — independent corroboration of the field name" rested on a source that records that token as **0** across the 224 chunks in its own measure table, attributes its real evidence to a different artefact with no `file:line` and no digest, and whose 224 chunk bodies are **not committed** (independent count **0** — `AGENTS.md` §1 deletes the claim, §2.1 deletes the word). Two more re-labelled: `docs/05`'s "the vendor's bundles do not contain" is **false** (the patient lazy chunk carries `medicalDeviceFamily` at byte 83,893), and `docs/10` row 37's `(GUARDIAN, MINIMED, PARADIGM)` loses **`MINIMED`/`PARADIGM`** — ⚠ **corrected 2026-10-15: the count published as their evidence was false.** The row claimed they had one uncited log line plus the row quoting it; `git grep -w` at base `7d915b8` shows **three** files carrying each token as a claimed value and a **fourth** carrying `PARADIGM` as an era label — and moves from OBSERVED to **SOURCE-OBSERVED**, since no client read here is a live response. `GUARDIAN` survives, sourceable twice. **What would change the verdict:** one authenticated `GET /patient/monitor/data`, key-names-only, value verbatim, matched against four axes (client comparison set, model code, display name, 16 map tokens); **a value matching none of the four is itself the finding**. Two successors filed under the area: read-side echo casing, and whether the `_X` suffixes mean anything | [findings-log/2026-10-14-pool-r-devicefamily-casing/FINDINGS.md] | #124 |
| K — The chunk corpus, for real this time | 2026-10-16 | **Negative on nothing, positive on completion.** Control-flow mining complete: both clinic (225) and patient (211) lazy-chunk corpora swept clean of discovery-key tokens (`baseUrlPde`, `/connect/pde`, `discover/android`, `clcloud`, `api/carepartner`, `system.gc.gz.transition.flags` leaves all 0); `system.logbook.entry.validation.config` recovered in lazy chunk `9481.6977c1a7bd7461f8` (module 79481), structure recorded as `types`/`sensorLocations.options`/`freeText`/`doseUnits.options`/`questions` with values token-gated; cross-client differential declined as not meaningful (5 clinic vs 144 patient unresolved call-site shapes, compared across constant-table vs inlined-routing builds). 0 of a 0 cap — closing on existing committed evidence from issues #56, #78, #103, #121. Successor: the 15 `hcp/configuration/public/*` keys, filed as a docs/10 §1 open question (no new letter can be minted — A–Z all in use). | [findings-log/2026-10-16-k-chunk-corpus/FINDINGS.md] | #140 |
| AA — does the `android/<app-version>` axis gate anything on `.com` and `-trials`, or only on `.eu`? | 2026-10-17 | **Positive, on both hosts, and the area's gate-versus-echo framing is withdrawn as the wrong pair of terms.** The tail is **both** echoed and selective at once. **OBSERVED, 20 of 20 requests, GET only, measured same-host floor 3.304 s** (9 gaps/host, 0 under 2.5 s, controls first per host, `v99` absent -> 403 at `f249b63cb2fc…` and `v11` served -> 200 on both). **No allow-list anywhere**: all 14 `200` bodies echo the requested tail exactly once into `"config"`, and a fabricated tail `android/absent-probe-871` was served verbatim at 3 cells — never 400/404. **At base `v13` on both `.com` and `-trials` the tail gates**: 4 tails select **3** documents, and `3.6`->`3.9` moves advertised `baseUrlCumulus` base (`v13`->`v2`), `baseUrlCareLink` (`v2`->`v1`), `CP[]` length (3->2), country count (109->99 on `.com`, 109->76 on `-trials`) and the SSO config file family: `oauth20_sso_carepartner_*_v6.json` on the 3.5/3.6 class, against `sso_cp_us_v6.json` on `-trials` and both `sso_cp_us_v6.json` + `eu_sso_cp_eu_v6.json` on `.com` for the 3.9 class. The `3.5`/`3.6` documents are byte-identical **across** both hosts; the `3.9`-class document is not, which corrects `docs/00`'s "every cell from 3.9 upward is byte-identical" to *within a host*. **At `-trials` base `v6` the tail gates nothing** — 4 tails including the fabricated one collapse to **one** canonical digest (n=4), re-deriving the digest the 2026-10-17 matrix pass recorded there. **The `v6` 403 split reads as a base-axis effect, not an app-version effect (INFERRED; the refutations are OBSERVED)** — same host, same tail `3.6`, base `v11` -> 200 — but whether `v6` is unrouted on `.com` because of the version segment or the route family is **not established and no choice is made**. **Deviation, disclosed:** claim #151 named `carelink.minimed.com`/`carelink-trials.minimed.com`; the pass sent `clcloud.*`, the host family the route is published on — **the claim's host list was wrong**; it answers the area as posed and does **not** speak to `carelink.*`. **Premise checked:** the closed row on "bare `connect/carepartner/` prefixes dead" probed *prefix parents*, not this routed leaf — **no contradiction**. **No pin added** — a 4-cell pin in `05-public-config` costs 4 requests on **every PR gate** *and* 4 per weekly sweep, and it would not catch the change that matters (the `3.6`-class document departing). **Measure**; counting rule in the log §7. **One source** — no strength word used (`§2.1`). Lookup-vs-threshold **not separable** from 4 tails; carried to **AE** | [findings-log/2026-10-17-area-aa-appversion-axis/FINDINGS.md] | #155 |
| S-L1 — the `cluster.idx`-level "is this crawl served at all" instrument, and the verdict on `CC-MAIN-2014-23` | 2026-10-19 | **Closed on its close condition, and the target retired on the SERVED side.** The instrument is committed (`servedness.py`, `pass`/`classify`/`selftest`) and answers served/unserved for any named crawl in **one ranged read**, classified correctly on both controls (`CC-MAIN-2022-27` and `CC-MAIN-2024-42` both **SERVED**) against the absent-id oracle (`CC-MAIN-9999-99` → `404 NoSuchKey`). **`CC-MAIN-2014-23` is SERVED** — `206`, `Content-Range: bytes 0-8191/153 902 243` — and its `minimed.eu` `404` now sits behind a **`200`** control **on that same crawl** (**1 785 B** of `google.com` records), so the standing **indeterminate cell retires as served-but-empty, NOT as "unservable"**; `AGENTS.md` §7 records `index.commoncrawl.org` TLS-dropping from some hosts, so a connection-level failure is a statement about *this box* and discharges nothing. **15 of a 15 cap**, GET only, `data.commoncrawl.org` (11) + `index.commoncrawl.org` (4), **0 to any Medtronic host**, `t_sent` floor **3.537 s** (0 gaps under 3.5 s), **0 retries** at `E[N]` 1.00. **The locate half is the recorded negative: `UNCONVERGED` on both controls** at a 3-page budget, so the control gate withheld every family verdict and the target's locate never ran — `UNCONVERGED` is not a negative. ⚠ **Corrects claim #152's own descriptor**: the readable-absence control is **`CC-MAIN-2024-42`** (area M row 25 `200` / row 45 `404`), **not** `CC-MAIN-2024-22`, whose S-L2 row 45 is a **`200`** with 13 records — a positive-adjacent crawl. Successor: **AD**, the locate with a seed derived from the head read (**0 requests** once the instrument exists). | [findings-log/2026-10-18-sl1-cluster-servedness/FINDINGS.md] | #152 |


---

> **Consumer note.** Findings here are consumed by
> [NovaLux12/carelink-bridge](https://github.com/NovaLux12/carelink-bridge), which
> feeds this repo's regression suite, which the bridge runs before a release.
> If something here moves a value the bridge pins, it reaches their release
> checklist — file it here with the `downstream-bridge` label and name
> the constant. Bridge bugs (login, upload, crash) belong in
> [their bug tracker](https://github.com/NovaLux12/carelink-bridge/issues/new?template=bug.yml).
