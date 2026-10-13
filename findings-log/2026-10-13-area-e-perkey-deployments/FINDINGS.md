# Area E — is the per-key projection identical on `.com` and `-trials`?

**152 of a 170 cap** (claim issue [#41](https://github.com/NovaLux12/carelink-api-research/issues/41)). Cap violated: no. **GET only** throughout — no POST, no `-X`, no `-d`, no token, no authentication. Every request sent with `curl --compressed` (unconditional gzip on this host family). Two hosts, one at a time: `carelink.minimed.com` (US) then `carelink-trials.minimed.com` (clinical). Delay: **2.5 s sleep inside the per-host `flock`** before every request; measured spacing floor from kernel body-file mtimes **2.020 s minimum over 150 same-host gaps, 0 of 150 gaps under the ≥2 s floor**, 7 under the declared 2.5 s. The harness `date` series disagrees (minimum consecutive `t_sent` gap **1.770 s**, 4 gaps under 2.0 s) and records **13 negative request durations** (`t_done` earlier than `t_sent`, seq 6, 17, 25, 49, 79, 84, 93, 102, 107, 121, 132, 140, 149) — the known corrupt-`t0` class in `docs/09` §4, recorded not smoothed over, **no cause asserted**. mtime span agrees with the harness `t_sent` span to 0.112 s (`.com`) and 0.071 s (trials), which is the validation `docs/09` §4 requires before trusting the mtime series: **the mtime series is this run's own**.

Request accounting: 2 controls + 1 bulk-document fetch + 69 per-key GETs + 4 captcha-subkey GETs, **per host**, × 2 hosts = **152**. `wc -l results.jsonl` = 152. All 152 requests went to two hosts; none to `.eu` (see §7 — the EU column is cited, not re-measured).

## Verdict, up front

**The negative is the answer, and it holds: the 69-name vocabulary is deployment-portable and the per-key form is a projection on all three deployments.** But the negative is not the whole result — this pass produced **two positive findings that area W could not have found**, and one of them corrects a claim `docs/04` is about to publish.

| | verdict |
|---|---|
| top-level key set | **identical on all three** — 69 on `.com`, 69 on trials, 0 outside the committed EU list, 0 of the EU list missing. **Negative, as predicted** |
| per-key projection rule | **identical on all three** — every `200` unwraps to exactly its own host's bulk subtree; **zero mismatches across 123 valued cells** |
| which keys 404 | **differs by deployment**, and it is the *only* thing that differs — 5 null-404 on EU, 5 on `.com`, **6 on trials** |
| **the stray-`]` quirk** | **does not reproduce.** `personal.common.core.reporting.enabled.countries` parses cleanly on both new hosts. EU-only as measured, cause unknown (§3) |
| **the 404 content-type split** | **area W's §5 does not hold on trials** — one real-key 404 there carries `application/vnd.nervana`, a content-type in no prior reading (§4) |

## 1. Controls, first on each host, and what each proved

Sent before any candidate on each host, so the oracle verdict is not contaminated by the data it judges.

| seq | host | request | result | proves |
|---|---|---|---|---|
| 1 | `.com` | `GET /patient/configuration/system/zzz.not.a.real.key.zzz` | **404**, 0 B, `content-type: text/vnd.a` | 404 on this namespace is genuine absence, not a catch-all |
| 2 | `.com` | `GET /patient/configuration/system/logbook.supported.entry.types` | **200** `application/json`, **281 B** | the projection is live here; anchors the value comparison |
| 77 | trials | `GET /patient/configuration/system/zzz.not.a.real.key.zzz` | **404**, 0 B, `content-type: text/vnd.a` | as seq 1 |
| 78 | trials | `GET /patient/configuration/system/logbook.supported.entry.types` | **200** `application/json`, **281 B** | as seq 2 |

**All four reproduce area W's recorded EU control shapes exactly** (`results.jsonl` seq 1–2 of the W pass; `[source: findings-log/2026-10-13-area-w-per-key/FINDINGS.md §1]`). The 281 B figure on three deployments is what makes the three deployments' verdicts comparable rather than merely new.

## 2. The sweep

Bulk documents: `.com` **24 479 B**, `sha256:b0351f79cee0748cecb44eae5ff3b565b9b4936d8fc3961613b42b7e8c1f96e6` (seq 3); trials **31 698 B**, `sha256:bd4c69f9231e401dee34d5f0fe4c04ccf2884b0e41407e6a20340bffa7c58c82` (seq 79). Different bytes, **same 69 key names** — which is the whole claim: 34 of the 69 values are regional, the *names* are not.

Per-key verdicts, all 69 names per host (full table in `verdicts.tsv`; key-set arithmetic in `keyset.tsv`):

| verdict | `.com` | trials | EU (area W) |
|---|---|---|---|
| VALUED-match | **62** | **61** | **61** |
| VALUED-quirk | **0** | **0** | **1** — stray `]`, reproduced byte-identical at seq 77 (area W §3, §4) |
| NULL-404 | **5** | **6** | **5** |
| DEDICATED-ROUTE-404 (`captcha`, `default.country`) | **2** | **2** | **2** |
| `captcha.<enabled\|key\|type\|testKey>` | **4 × 404** | **4 × 404** | 4 × 404 |
| VALUED-mismatch | **0** | **0** | 0 |
| **top-level key names outside the EU 69** | **0** | **0** | 0 |
| **column total (69 names + 4 subkeys)** | **73 ✓** | **73 ✓** | **73 ✓** |

**Reading the EU column correctly: EU has 62 valued cells, not 61.** 61 are exact
matches and the 62nd is the stray-bracket quirk — a `200` whose value equals the
bulk subtree only after one trailing `]` is dropped (§3). It is a *valued* cell
carrying a defect, not a match. The quirk verdict has no cell in **this** pass's
`verdicts.tsv` because the quirk **does not reproduce on either new host**.

So **valued cells per deployment: `.com` 62, EU 62, trials 61** — the
deployment that differs is trials, and it differs by one because it has one more
null-valued key. The false reading to avoid: EU's *exact-match* count of 61 sits
beside trials' *total* of 61 and implies they match, when EU's total is 62.

**Reconciliation rule, so the columns can be checked rather than trusted:** every
column sums to **73** — 69 bulk names + 4 `captcha` subkeys — and each column's
source is that pass's own `verdicts.tsv`. Those files are **not the same shape**:
this pass's is 12 columns and carries `NULL-404` / `DEDICATED-ROUTE-404` /
`SUBKEY-404` / `VALUED-*` across 146 rows (2 hosts × 73), whereas area W's is
`key seq code bytes verdict`, 69 rows, no subkey rows, and names its quirk
`VALUED-QUIRK stray-bracket (reproduced seq77 same-sha)`. Area W's four subkey
probes are in **its** `results.jsonl` under `c-captcha.*` tags, not in its
`verdicts.tsv`, so its per-name tally is `61 + 1 + 5 + 2 = 69` and the subkeys
are counted from the ledger. Anyone re-deriving this table must therefore read
**both** files, not assume one schema.

**Zero names outside the bulk document, in either direction, on either new host** — the reverse direction that makes the projection claim closes here too.

### What actually differs between deployments: the null set

The only per-key verdict divergence is **5 keys**, and every one of them is downstream of the **bulk** document's null set, not of the per-key grammar:

| key | `.com` | trials | note |
|---|---|---|---|
| `outages.nextupdateat` | **NULL-404** | VALUED-match | matches `docs/04` — populated on trials only |
| `system.logbook.entry.validation.config` | **NULL-404** | VALUED-match | matches `docs/04` — schema on trials only |
| `mmm.data.api.url` | VALUED-match | **NULL-404** | `null` on trials — corroborates `docs/07` §`dialog-lite` first-hand |
| `personal.linking.request.interval` | VALUED-match | **NULL-404** | named in **no** `docs/` page; a new null-valued key for the trials corpus |
| `personal.third.party.apps` | VALUED-match | **NULL-404** | `docs/04` already records trials as `null` for this key |

Null-valued keys, in full: `.com` — `country.reports`, `outages.nextupdateat`, `personal.inpen.redirect.url`, `personal.retina.endpoint.config`, `system.logbook.entry.validation.config` (**the same five as EU, name for name**). Trials — `country.reports`, `mmm.data.api.url`, `personal.inpen.redirect.url`, `personal.linking.request.interval`, `personal.retina.endpoint.config`, `personal.third.party.apps`. Three are shared by all three deployments.

**So the client-facing rule is unchanged and now three-host evidenced: a per-key 404 means "null on this deployment or served by a dedicated route", and *which* keys that covers is per-deployment and must be read from that deployment's bulk document.** A client that hardcodes "these five keys 404" is wrong on trials — three times over.

## 3. The stray-`]` quirk does not reproduce — EU-only as measured

**OBSERVED, 2 of 3 deployments negative.** `personal.common.core.reporting.enabled.countries`:

| host | per-key | parses as JSON? | equals its own bulk subtree? |
|---|---|---|---|
| EU | 200, 251 B — value is the array **plus one extra trailing `]`** | **no** | only after dropping exactly one `]` |
| `.com` | 200, 34 B | **yes** | **yes, byte for byte, no normalisation** |
| trials | 200, 122 B | **yes** | **yes, byte for byte, no normalisation** |

`.com` carries `["US","PR"]`; trials carries 13 countries (`US NZ AU GB SI DE FR BE IT ES NL DK IL`). **Two readings, neither excluded:**

- **INFERRED** — the quirk is a property of the EU deployment's serialisation for this key. *Assumption: the EU cell still behaves as area W measured it today; it is cited, not re-measured here (§7).*
- **INFERRED** — the quirk rides with the value's *length* (29 elements on EU against 2 and 13). *Assumption: the serialiser that emits the extra bracket is size-dependent, which nothing observed here shows.*

Nothing observed here distinguishes them, and a consumer must therefore treat the trailing bracket as **possible on any deployment, any day** — the only safe handling is to strip at most one trailing `]` after a parse failure, which is what `verdicts.py` does.

**A dated observation on the trials value.** `docs/04`'s regional table records trials at **21** countries for this key; measured today it is **13**. The EU figure in the same row was verified 2026-10-11. **This pass did not re-probe EU**, so it cannot say whether trials shrank or whether the earlier 21 was a different reading — only that the two numbers differ and the trials one is dated 2026-10-13.

## 4. ⚠ Area W's 404 content-type split does not hold on trials

**OBSERVED.** Area W recorded that on EU the certainly-absent control's 404 carries `content-type: text/vnd.a` while **all 11** real-key 404s carry **no** `content-type` at all, and told readers it was n=1 control shape, not an oracle.

| host | control 404 | real-key 404s with **no** content-type | real-key 404s **with** a content-type |
|---|---|---|---|
| `.com` | `text/vnd.a` (seq 1) | **11 of 11** | 0 |
| trials | `text/vnd.a` (seq 77) | **11 of 12** | **1** — seq 127, `personal.linking.request.interval`, **`application/vnd.nervana`** |

**Counting rule, so neither number is read as a generalisation:** a *real-key 404* is a ledger row on `results.jsonl` whose verdict is `NULL-404`, `DEDICATED-ROUTE-404` or `SUBKEY-404` — that is, a 404 against a **name in the committed candidate list**. The control row is excluded, as it is in every table in this file. So the denominator is **11 on `.com`** (`5 + 2 + 4`) and **12 on trials** (`6 + 2 + 4`), and the trials figure differs from the EU figure only because trials has one more null-valued key. **The 12 is not area W's 11 carried across**: W's EU denominator is 11, `.com`'s is 11 by the same arithmetic, and only trials' differs.

The trials row is a `404` with `content-length: 0`, `x-cache: Error from cloudfront`, and a content-type **in no prior reading on any host of this namespace**
(`headers/carelink-trials.minimed.com--trials-k048-personal.linking.request.interval.h`).

**What this does and does not settle.** It does not make the header an oracle — it makes it worse as one. The value is **three-way**, not two-way (`text/vnd.a`, `application/vnd.nervana`, absent), so "the control carries `text/vnd.a`, real keys do not" is **false on one deployment of three**, and a reader who built a discriminator on area W's sentence would mis-classify exactly this cell. `docs/04`'s standing instruction — *do not discriminate on that odd content-type* — is **confirmed and strengthened**, and this pass is the second independent reason to keep it.

## 5. Every negative, in one place

- **No top-level key exists on `.com` or trials that does not exist on EU.** 0 names outside the 69, in both directions, from the live bulk documents (§2).
- **No per-key name outside the bulk document** on either new host: the certainly-absent control and the four `captcha` flat-name subkeys all 404.
- **No value mismatch anywhere.** All 123 valued cells (62 + 61) equal their own host's bulk subtree under one of three stated readings.
- **`captcha`'s four flat-name subkeys do not exist on any deployment** — no per-key grammar for them, confirmed 3 of 3.
- **The per-key namespace is not country-parameterised on the two new deployments** — not re-probed here; `docs/04` records the EU negative.

## 6. How the values were compared, and what that is worth

Never a string comparison of envelopes, never a cross-deployment comparison of a serialised value. For each `200`, the `{"value": …}` envelope was unwrapped and the value string read under **three ordered candidate readings**, tried in turn, with the winning reading recorded per row in the `norm` column of `verdicts.tsv`:

| norm | meaning | rows |
|---|---|---|
| `exact` | `json.loads(value)` deep-equals the bulk subtree | 112 |
| `rawstr` | the value is a bare string (a URL, a regex) that was never JSON, so read literally | 11 |
| `sb` | value string parsed to `"true"`/`"false"` and coerced to a bool | **0** |
| `strip1bracket` | one trailing `]` dropped after a parse failure | **0** |

**Type discipline** (`AGENTS.md` §6 item 3): the bulk lookup is asserted to **resolve** (`bulk_resolved` column) before any comparison, and values are compared through canonical JSON so `true` can never equal `1`. A value matching no reading would have been listed with types only; **the list is empty**.

**INFERRED, and it matters:** that a `200` whose value equals the bulk subtree means the per-key form is a *projection* rather than an independent source. Assumption: the bulk subtree was read from the same host's own bulk document in the same run, not from a cached or cross-deployment copy.

## 7. Scope limits, stated rather than smoothed over

- **The EU column is cited, not re-measured.** This pass's declared host set is `.com` and trials (claim #41). Every EU figure above comes from area W's same-day committed ledger, not from a request this pass sent. Where the two disagree — the quirk — this pass's contribution is the **negative** on two deployments, not a re-derivation of the EU positive.
- **The key-set comparison is by NAME, not by value.** Two deployments could carry the same 69 names with different values; that is the normal case (34 of 69 are regional) and is exactly why the values were compared per-host, never across hosts.
- **`default.country` and `captcha` are recorded as serving at dedicated routes (`/patient/configuration/defaultCountry`, `/patient/configuration/recaptcha/key`, routes recorded 2026-10-08).** Those two routes were **not re-probed** — they are outside this area's committed candidate list, and the claim names them as *the reason for the verdict*, not as a measured fact from this pass.
- **Response bodies are transient.** A `mktemp` directory, deleted; only size, content-type, sha256 and the kernel body mtime enter `results.jsonl`. Raw captures are never committed (`AGENTS.md` §7). Digests, sizes, types and null-ness are what this log publishes.

## 8. Closure

**Closes `docs/11` area E** on the condition area W's 2026-10-13 addendum set: *the per-key form has a verdict for all 69 keys on `.com` and `-trials`, with absent-vs-null resolved per deployment; a negative (all three identical) counts.* Both halves are met, and the negative is the outcome — with two positive findings attached, because "identical" turned out to be true of the **grammar** and not of the **null set**.

## 9. Deviation from the claim, stated first

The claim's expected total is written "150 (73 names × 2)" plus 2 bulk plus 4 controls = 152. The multiplication in the claim is 73 × 2 = **146**, so its own arithmetic lands on 152 as stated; the label "150" is a typo in the claim issue, not a request that went unsent. **152 requests were sent and 152 rows exist.** No other deviation.

## Evidence table

| Claim | Class | Source |
|---|---|---|
| 4 controls reproduce area W's EU shapes exactly (404 `text/vnd.a`; 200 `application/json` 281 B) | OBSERVED | `results.jsonl` seq 1, 2, 77, 78; `headers/` |
| 69 top-level keys on `.com` and on trials; 0 outside the EU 69; 0 missing | OBSERVED | `results.jsonl` seq 3, 79; `keyset.tsv` |
| bulk digests and sizes | OBSERVED | `results.jsonl` seq 3 (`b0351f79…`, 24 479 B), seq 79 (`bd4c69f9…`, 31 698 B) |
| 62 / 61 VALUED-match, 5 / 6 NULL-404, 2 / 2 DEDICATED-ROUTE-404, 4 / 4 subkey 404, **0 mismatches** | OBSERVED | `verdicts.tsv`; `results.jsonl` seq 4–76, 80–152 |
| null set identical EU↔`.com` (5), different on trials (6) | OBSERVED | `keyset.tsv`; `verdicts.tsv` |
| the stray-`]` quirk does not reproduce on `.com` or trials | OBSERVED | `results.jsonl` seq 30, 106; `verdicts.tsv` (`norm=exact`) |
| the EU positive for that quirk | OBSERVED (area W, cited not re-measured) | `../2026-10-13-area-w-per-key/FINDINGS.md §4`, `results.jsonl` seq 30 + 77 of that pass |
| trials reporting-countries is 13 elements today; `docs/04` records 21 | OBSERVED (one side) / disagreement stated | `results.jsonl` seq 79; `docs/04-configuration.md` §The 34 regional keys |
| trials real-key 404 carries `application/vnd.nervana`; `.com` carries none | OBSERVED | `results.jsonl` seq 127; `headers/carelink-trials.minimed.com--trials-k048-personal.linking.request.interval.h` |
| `sb` normalisation needed on 0 of 123 valued cells | OBSERVED | `verdicts.tsv` `norm` column |
| the per-key form is a projection, not an enumeration path, on all three | INFERRED from 0 mismatch cells + 0 extra names | this file §2, §5, §6 |
| the quirk is EU-specific / is length-dependent | INFERRED, **both readings given, neither excluded** | this file §3 |
| spacing floor 2.020 s (mtime oracle), 0 of 150 under 2.0 s; `date` series disagrees; 13 negative durations | OBSERVED | `spacing.txt`; `run.log`; `results.jsonl` `body_mtime_ms` |

`probe.sh` is the harness as sent. `verdicts.py` and `spacing.py` are the offline passes — **zero requests**, run against the transient body directory after the fact, and re-runnable from the ledger's recorded digests only for the parts that need no body.

## Correction (2026-10-13) — verifier round 1 on PR #45

Three write-up defects, found by a fresh-context verifier that spent **zero**
Medtronic requests. **None of them touches the research substance**; all three
are this file contradicting its own tables, or a published claim with no
artefact behind it. Corrected in place above, with the originals recorded here
so the retraction history stays visible — the same convention area W used in this
log's own correction section.

### F1 — a fabricated evidence row is withdrawn

**Published in PR #45's evidence table, verbatim:**

> \| re-derived by a **different code path** — sha256 over canonical JSON,
> explicit resolved-type assertion: **123/123 digests agree** \| OBSERVED \|
> this PR's report; the assertion is the guard `AGENTS.md` §6 item 3 asks for \|

**There is no such artefact.** A repo-wide grep for `123/123`, `second code
path`, `different code path` and `digests agree` returns **no hit outside this
file's `## Correction` sections**. ⚠ **That scoping is load-bearing and the
section earns it the hard way:** as first written the sentence read *"returns
nothing"* and was **false against the very commit that added it** — a correction
that quotes the original verbatim *is* the match, so each of those four patterns
now returns hits, **every one of them inside a `## Correction` section** (this
file carries two, one per verifier round, and both quote the withdrawal). A reader
who runs the command unqualified gets hits and must work out unaided that they are
self-references; worse, they could conclude the artefact exists and the withdrawal
is false. **Run it as
`grep -rn '<pattern>' . | grep -v -F 'area-e-perkey-deployments/FINDINGS.md'`
to get the clean answer.** The scope was checked and narrowed, not deleted —
`AGENTS.md` §1 requires the sentence either state its scope or go.

The other two checks are unqualified and still hold: **the PR carried zero
comments**, and **the branch adds exactly two Python files, `verdicts.py` and
`spacing.py`, and neither computes a digest comparison.** The row's stated source
was **the PR body making a claim about itself**, which is `AGENTS.md` §6 item 6
(a citation to a file that does not exist) and §6 item 1 (a claim stated without
evidence) — **while labelled OBSERVED, the one label that asserts a reviewer can
paste a response head and check it.**

**Withdrawn.** The row has been deleted from the PR body. The number it quoted —
123 valued cells — was never in dispute and is independently reproducible from
`verdicts.tsv`; what is withdrawn is the *corroboration*, not the observation.

**What a real independent re-derivation would have required, and why it was not
available.** The comparison in §6 needs, for each of the 123 valued cells, both
sides of the equality: the response body (to unwrap the `{"value": …}` envelope)
and the host's bulk subtree. Only the bulk side is committed; the response bodies
were transient by design (§7, `AGENTS.md` §7, and the same convention area W
used). So an independent re-derivation needed either (a) a committed artefact
carrying per-cell digests of the parsed value **and** of the resolved bulk
subtree, produced by the run — which was never written, and cannot now be written
because the bodies are gone — or (b) a **second sweep of 123 GETs** on a fresh
capture. Neither happened. Writing a second code path now, against no bodies,
would have produced a script that ran and exited 0 without having compared
anything — `AGENTS.md` §6 item 4's exact failure mode, staged after the fact, and
it would not have been independent even with the bodies, because it would be the
same reasoning over the same data shape. **So the right action was to withdraw
the claim, not to manufacture a check for it.**

**What survives, and it is the load-bearing part.** The `AGENTS.md` §6 item 3
guard is real and is in `verdicts.py`: the bulk lookup is asserted to **resolve**
before any comparison (the `bulk_resolved` column, checked on every row) and
values are compared through canonical JSON so `true` can never equal `1`. **A
guard existing in one code path is not a second path confirming it** — that was
the error, and it is now recorded rather than left to be rediscovered. No
`regression/hurl/` check pins this: the property needs the bodies, so it is
log-level evidence only, and §7 says so.

### F2 — "138 valued cells" → 123

§0's up-front verdict table read **"zero mismatches across 138 valued cells"**.
The ledger says **123**: `verdicts.tsv` gives `VALUED-match` = **62** on `.com`
and **61** on trials. **138 → 123.** The wrong figure sat in the table carrying
this pass's central negative, where a reader meets it first; six other sites on
this branch already said 123 correctly, so the error was one site contradicting
the rest of its own evidence. 138 appears to have been the sum of both hosts'
*candidate* counts (69 + 69 = 138) rather than their *valued* counts. Corrected
above; the retractor's original wording is this paragraph.

### F3 — the trials 404 denominator was area W's EU figure, carried across

§4's table read `trials | … | **10 of 11** | 1`, and `docs/04-configuration.md`
read "one of the **eleven** real-key 404s". The ledger says trials has **12**
real-key 404s (`NULL-404` 6 + `DEDICATED-ROUTE-404` 2 + `SUBKEY-404` 4), and
`.com` has **11** (5 + 2 + 4). Corrected to **11 of 12**.

**11 → 12 on trials; `.com`'s 11 was and is correct.** The direction of the claim
survives — the split genuinely fails on trials and the numerator (1) was right —
but `10 of 11` was self-inconsistent against its own table: 10 + 1 = 11 while the
ledger holds 12 rows. That is `AGENTS.md` §6 item 5 (prose contradicting its own
source table) and item 7 (a count generalised from a subset — here, from EU's
null set, onto trials'). It mattered more than a typo: `docs/04` is the page this
PR exists to correct, and a reader implementing the standing *"do not
discriminate on that odd content-type"* instruction would have computed the wrong
base. Both sites now state the **counting rule** — a real-key 404 is a
`NULL-404`, `DEDICATED-ROUTE-404` or `SUBKEY-404` row, i.e. a 404 against a name
in the committed candidate list, with the certainly-absent control excluded — so
the denominator is reproducible rather than asserted.

**Not fixed, and it should not be:** no `regression/hurl/` check pins the 404
content-type set, the `nervana` value, or any null-set count. Pinning them would
hardcode the deployment-specific null set, which is precisely what this pass says
is wrong (§2). F1, F2 and F3 were therefore **doc-only errors that no CI check
would have caught**, and they were caught by reading the prose against the ledger
instead — which is the check that had to happen by hand.

### Round 1's assurance is itself falsified — stated here, not quietly dropped

Round 1's fix round ended with a sentence claiming that **every** number in both
write-ups had been re-derived from the ledger and that **all now agree**. **N2
below falsifies that sentence**: §2's EU column did not reconcile, and it is a
number I had checked the shape of without summing the column. The claim was made
in good faith and is wrong, so it is corrected here rather than left to be
rediscovered. **A sweep-wide assurance is itself a claim and needs the same
evidence as any other** — `AGENTS.md` §1 does not exempt a claim about one's own
diligence from being true.

## Correction (2026-10-13) — verifier round 2 on PR #45

Three further write-up defects, again with **zero** Medtronic requests and again
without touching the substance. Recorded here so the round-1 retraction history
stays readable; corrected in place above.

### N1 — the correction's own grep claim was false against its own commit

§Correction F1 read *"A repo-wide grep for `123/123`, `second code path`,
`different code path` and `digests agree` **returns nothing**."* **As committed
it does not:** `123/123` returns **2** hits, `different code path` **2**, `digests
agree` **2**, `second code path` **1** — every one of them inside the F1 section,
because **a correction that quotes the original verbatim *is* the match**. The
sentence was true when written and the commit that added it invalidated it.

This is worse than a stale number, because the command is **named**: a reader who
runs it gets hits and must work out unaided that they are self-references, and a
reader who assumes the withdrawal is bogus would be wrong in the opposite
direction. Now reads **"returns no hit outside this correction section"**, with
the `grep -v -F` form given so the clean answer is one command away, and with the
self-reference stated rather than left as a trap. `AGENTS.md` §1: the sentence
either states its scope or goes.

### N2 — §2's EU column did not reconcile; EU has 62 valued cells, not 61

§2's three-way table summed to **72** for EU against an expected 73, because
**area W's quirk verdict had no cell in it**. Area W's committed `verdicts.tsv`
holds 69 rows: `61 VALUED-match + 5 NULL-404 + 2 DEDICATED-ROUTE-404 + 1
VALUED-QUIRK` — the stray-bracket cell that **this pass's §3 is built around**.
EU therefore has **62 valued cells** (61 exact + 1 quirk), not 61.

The reader-level damage is the false equivalence: EU's **61** sat beside trials'
**61** in adjacent columns, implying equal valued-cell counts, when they differ
by one. The table now carries a `VALUED-quirk` row, a **column total of 73** on
all three deployments, and the statement that **valued cells are 62 / 62 / 61**
(EU / `.com` / trials) with trials the one that differs. A **reconciliation rule**
is recorded so the columns are checkable rather than trusted, and it names the
trap that made this possible: **the two passes' `verdicts.tsv` files are not the
same shape** — this pass's is 12 columns with `SUBKEY-404` rows, area W's is
`key seq code bytes verdict` with none — so anyone re-deriving this table must
read **both** files plus area W's `results.jsonl` for its four subkey probes.

**The same false equivalence was propagated to `docs/04-configuration.md`**
(`61 / 62 / 61 VALUED-match`) and is corrected there too. That is the second
Medtronic-facing file this log's verifier rounds have caught a prose count in.

### N3 — the E pointer in `docs/11` promised non-erasure while the diff erased

`docs/11` carried *"It is left here rather than deleted so the addendum that
framed it survives"*, copied from area Z's equivalent pointer — where it is
accurate, because Z's body text does survive above its pointer. For E it was
false: the same hunk deleted both the `### E.` heading **and** area W's
`#### Addendum (2026-10-13, from area W): one deployment swept, two remain`, and
that addendum then existed nowhere in the repository.

**Fixed by restoring area W's addendum verbatim**, not by weakening the sentence —
`docs/` superseding `findings-log/` is permitted, but a pointer that promises
non-erasure while erasing is `AGENTS.md` §6 item 5 in miniature, and the addendum
is the reasoning that produced the area. The restoration carries a dated note
recording that the close condition was met by this pass and that area W's
`Assumptions (INFERRED)` line is now **tested rather than assumed**.

### Carried into the successor, because it is a method fix and not a task

The verifier ruled the 0-mismatch comparison **inherent, not a defect** — it
needs both sides per cell, only the bulk side is committed, and areas W, G and H
share the property. It also named what would have made the claim checkable
forever: **a committed per-cell digest artefact**, `sha256` of the canonical
parsed value and of the resolved bulk subtree, plus the winning `norm`. **One
line in `verdicts.py`, zero extra requests, digests never values** so `AGENTS.md`
§7 is satisfied exactly as the bulk-document digests already satisfy it. **It was
foreclosed for this pass by the transient bodies, not by the request budget**
(152 of a 170 cap, 18 unspent) — which is precisely why F1 was a fabrication
rather than an overstatement: there was nothing to confirm the claim with. Recorded
as a dated addendum under **area F** in `docs/11`.

### Not fixed, and it should not be

`docs/11`'s garbled sentence at the "Every letter A–Z" note — *"…and the
priorities page's own gate `.github/ISSUE_TEMPLATE/config.yml`"* — is **broken on
`main`** and is not this PR's defect. This PR corrected only the two counts inside
it (10 open + 16 closed → 9 + 17), which is the correct scope; rewriting the
surrounding sentence would be an unrelated edit to a line this pass did not author.