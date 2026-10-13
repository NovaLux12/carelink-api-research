# Area E — is the per-key projection identical on `.com` and `-trials`?

**152 of a 170 cap** (claim issue [#41](https://github.com/NovaLux12/carelink-api-research/issues/41)). Cap violated: no. **GET only** throughout — no POST, no `-X`, no `-d`, no token, no authentication. Every request sent with `curl --compressed` (unconditional gzip on this host family). Two hosts, one at a time: `carelink.minimed.com` (US) then `carelink-trials.minimed.com` (clinical). Delay: **2.5 s sleep inside the per-host `flock`** before every request; measured spacing floor from kernel body-file mtimes **2.020 s minimum over 150 same-host gaps, 0 of 150 gaps under the ≥2 s floor**, 7 under the declared 2.5 s. The harness `date` series disagrees (minimum consecutive `t_sent` gap **1.770 s**, 4 gaps under 2.0 s) and records **13 negative request durations** (`t_done` earlier than `t_sent`, seq 6, 17, 25, 49, 79, 84, 93, 102, 107, 121, 132, 140, 149) — the known corrupt-`t0` class in `docs/09` §4, recorded not smoothed over, **no cause asserted**. mtime span agrees with the harness `t_sent` span to 0.112 s (`.com`) and 0.071 s (trials), which is the validation `docs/09` §4 requires before trusting the mtime series: **the mtime series is this run's own**.

Request accounting: 2 controls + 1 bulk-document fetch + 69 per-key GETs + 4 captcha-subkey GETs, **per host**, × 2 hosts = **152**. `wc -l results.jsonl` = 152. All 152 requests went to two hosts; none to `.eu` (see §7 — the EU column is cited, not re-measured).

## Verdict, up front

**The negative is the answer, and it holds: the 69-name vocabulary is deployment-portable and the per-key form is a projection on all three deployments.** But the negative is not the whole result — this pass produced **two positive findings that area W could not have found**, and one of them corrects a claim `docs/04` is about to publish.

| | verdict |
|---|---|
| top-level key set | **identical on all three** — 69 on `.com`, 69 on trials, 0 outside the committed EU list, 0 of the EU list missing. **Negative, as predicted** |
| per-key projection rule | **identical on all three** — every `200` unwraps to exactly its own host's bulk subtree; **zero mismatches across 138 valued cells** |
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
| VALUED-match | **62** | **61** | 61 |
| NULL-404 | **5** | **6** | 5 |
| DEDICATED-ROUTE-404 (`captcha`, `default.country`) | **2** | **2** | 2 |
| `captcha.<enabled\|key\|type\|testKey>` | **4 × 404** | **4 × 404** | 4 × 404 |
| VALUED-mismatch | **0** | **0** | 0 |
| **top-level key names outside the EU 69** | **0** | **0** | 0 |

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
| trials | `text/vnd.a` (seq 77) | **10 of 11** | **1** — seq 127, `personal.linking.request.interval`, **`application/vnd.nervana`** |

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