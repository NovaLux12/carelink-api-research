# Area Z — CORS `Origin` reflection, raw observations

Run date: 2026-10-12. Harness: [`probe.sh`](probe.sh) (unmodified, run once).
Corpus: `results.jsonl`, request ledger: [`run.log`](run.log), rendered
comparison: [`verdict.txt`](verdict.txt) (produced by [`verdict.py`](verdict.py),
which issues no requests).

This file records **only what came back off the wire**. It assigns no evidence
class, states no cause, and offers no explanation for any pattern below. Where a
value was absent, the literal `(none)` is written in place of the value — which
is what `probe.sh` writes into the ledger for that case, so the table below is
the ledger, not a re-reading of it.

---

## 1. Request accounting

- **60 of a 69 cap.** The cap is the sum of the two numbers the claim
  issue ([#17](https://github.com/NovaLux12/carelink-api-research/issues/17))
  declared: the `CAP=60` guard inside `probe.sh`, plus **9** discrete hurl
  pin-validation requests named separately there. **Used: 51 from the harness
  + 9 from hurl = 60.**
- `wc -l results.jsonl` = **60**, `seq` contiguous 1..51 from the harness and
  52-60 appended by hand for the hurl requests (§8). **Every request this pass
  made against the vendor has a row**, and the converse: `run.log` holds exactly
  **51** request lines with `seq` contiguous 1..51, no gaps and no extras.
  (`probe.sh` also prints a `DONE n=…` banner, but via `echo` to stdout rather
  than into `run.log`, so it is **not** on disk and is not cited here.)
- All 51 harness requests were **OPTIONS** (45 data) or **GET** (6 controls),
  every one with an **empty body**. The 9 hurl requests were **OPTIONS**.
- No POST, no token exchange, no authentication. No `Authorization`, no `Cookie`,
  no `x-api-key` header was sent on any request. The only header `probe.sh` ever
  adds is `Origin`.
- `probe.sh` carries a `CAP=60` guard that exits 9 before issuing a request past
  the cap, and refuses to run a second time if `results.jsonl` or `run.log`
  already exists. The harness count cannot silently double.
- The two `Origin` literals were `https://example.invalid` and
  `https://probe-two.invalid`. Both are RFC 2606 reserved, guaranteed never to
  resolve. Neither was resolved; they are recorded here only as those strings.
  The first is the literal area X used, so the two passes are comparable.

### Delay between requests

`probe.sh` sleeps **≥2.5 s between requests to the same host**, which satisfies
the repository rule of `>=2 s`. Measured from the `run.log` timestamps
(ISO-8601 with milliseconds), the gap between the start of consecutive requests
to the same host:

| Measure | Value |
|---|---|
| same-host gaps measured | 48 |
| gaps >= 2.5 s | 43 |
| gaps < 2.5 s | **5** |
| gaps < 2.0 s (the repository floor) | **0** |
| single measured minimum same-host gap | **2.042 s** (`clcloud.minimed.eu`, **seq 15 -> 16**) |
| maximum same-host gap | 3.229 s |

The five sub-2.5 s gaps, stated rather than rounded away:

| gap | between | host |
|---|---|---|
| 2.044 s | seq 4 -> 5 | `clcloud.minimed.eu` |
| 2.449 s | seq 7 -> 8 | `clcloud.minimed.eu` |
| 2.042 s | seq 15 -> 16 | `clcloud.minimed.eu` |
| 2.470 s | seq 30 -> 31 | `clcloud.minimed.com` |
| 2.449 s | seq 36 -> 37 | `clcloud-trials.minimed.com` |

**All five remain above the `>=2 s` floor; none breaches the repository rule.**
No cause for the shortfall against the harness's own 2.5 s is asserted here.
This is the third pass in a row to record a sub-2.5 s same-host gap (areas B and
X each recorded one), which is itself worth noting: the stated spacing and the
measured spacing are not the same number, and this repo should not keep writing
down the stated one as though it were measured.

---

## 2. Controls — 2 per host, 6 total, sent FIRST and bare on every host

Sent before any data cell, and deliberately **without** an `Origin`, so the
oracle is not judged by the variable it exists to test.

| seq | host | role | status | `x-amzn-errortype` | `x-ca-err` | bytes | sha256(body) |
|---|---|---|---|---|---|---|---|
| 1 | `clcloud.minimed.eu` | CONTROL-live-token-gated | 401 | `UnauthorizedException` | 990 | 36 | `d551247201fc` |
| 2 | `clcloud.minimed.eu` | CONTROL-dead-fabricated-uuid | 403 | `MissingAuthenticationTokenException` | (none) | 42 | `f249b63cb2fc` |
| 18 | `clcloud.minimed.com` | CONTROL-live-token-gated | 401 | `UnauthorizedException` | 990 | 36 | `d551247201fc` |
| 19 | `clcloud.minimed.com` | CONTROL-dead-fabricated-uuid | 403 | `MissingAuthenticationTokenException` | (none) | 42 | `f249b63cb2fc` |
| 35 | `clcloud-trials.minimed.com` | CONTROL-live-token-gated | 401 | `UnauthorizedException` | 990 | 36 | `d551247201fc` |
| 36 | `clcloud-trials.minimed.com` | CONTROL-dead-fabricated-uuid | 403 | `MissingAuthenticationTokenException` | (none) | 42 | `f249b63cb2fc` |

Both controls returned **byte-identical bodies on all three hosts**. The
dead-path body digest `f249b63cb2fc` is the no-route constant already recorded
by areas U and B. No control failed.

---

## 3. The grid — every data cell

45 cells: 3 hosts x 5 route families x 3 conditions (bare / `Origin` A /
`Origin` B). Controls excluded from this table; see §2.

| seq | host | path | sent | status | `acao` | `acam` |
|---|---|---|---|---|---|---|
| 3 | `.eu` | `v13/display/message` | none sent | 200 | `*` | `OPTIONS` |
| 4 | `.eu` | `v13/display/message` | `Origin: https://example.invalid` | 200 | `*` | `OPTIONS` |
| 5 | `.eu` | `v13/display/message` | `Origin: https://probe-two.invalid` | 200 | `*` | `OPTIONS` |
| 6 | `.eu` | `csr/v2/display/message` | none sent | 200 | `*` | `OPTIONS,POST` |
| 7 | `.eu` | `csr/v2/display/message` | `Origin: https://example.invalid` | 200 | `*` | `OPTIONS,POST` |
| 8 | `.eu` | `csr/v2/display/message` | `Origin: https://probe-two.invalid` | 200 | `*` | `OPTIONS,POST` |
| 9 | `.eu` | `display/message` | none sent | 200 | `*` | `POST,OPTIONS` |
| 10 | `.eu` | `display/message` | `Origin: https://example.invalid` | 200 | `*` | `POST,OPTIONS` |
| 11 | `.eu` | `display/message` | `Origin: https://probe-two.invalid` | 200 | `*` | `POST,OPTIONS` |
| 12 | `.eu` | `v12/display/message` | none sent | 200 | `*` | `OPTIONS` |
| 13 | `.eu` | `v12/display/message` | `Origin: https://example.invalid` | 200 | `*` | `OPTIONS` |
| 14 | `.eu` | `v12/display/message` | `Origin: https://probe-two.invalid` | 200 | `*` | `OPTIONS` |
| 15 | `.eu` | `v6/display/message` | none sent | 200 | `*` | `OPTIONS` |
| 16 | `.eu` | `v6/display/message` | `Origin: https://example.invalid` | 200 | `*` | `OPTIONS` |
| 17 | `.eu` | `v6/display/message` | `Origin: https://probe-two.invalid` | 200 | `*` | `OPTIONS` |
| 20 | `.com` | `v13/display/message` | none sent | 200 | `*` | `OPTIONS` |
| 21 | `.com` | `v13/display/message` | `Origin: https://example.invalid` | 200 | `*` | `OPTIONS` |
| 22 | `.com` | `v13/display/message` | `Origin: https://probe-two.invalid` | 200 | `*` | `OPTIONS` |
| 23 | `.com` | `csr/v2/display/message` | none sent | 200 | `*` | `OPTIONS,POST` |
| 24 | `.com` | `csr/v2/display/message` | `Origin: https://example.invalid` | 200 | `*` | `OPTIONS,POST` |
| 25 | `.com` | `csr/v2/display/message` | `Origin: https://probe-two.invalid` | 200 | `*` | `OPTIONS,POST` |
| 26 | `.com` | `display/message` | none sent | 200 | `*` | `POST,OPTIONS` |
| 27 | `.com` | `display/message` | `Origin: https://example.invalid` | 200 | `*` | `POST,OPTIONS` |
| 28 | `.com` | `display/message` | `Origin: https://probe-two.invalid` | 200 | `*` | `POST,OPTIONS` |
| 29 | `.com` | `v12/display/message` | none sent | 200 | `*` | `OPTIONS` |
| 30 | `.com` | `v12/display/message` | `Origin: https://example.invalid` | 200 | `*` | `OPTIONS` |
| 31 | `.com` | `v12/display/message` | `Origin: https://probe-two.invalid` | 200 | `*` | `OPTIONS` |
| 32 | `.com` | `v6/display/message` | none sent | 200 | `*` | `OPTIONS` |
| 33 | `.com` | `v6/display/message` | `Origin: https://example.invalid` | 200 | `*` | `OPTIONS` |
| 34 | `.com` | `v6/display/message` | `Origin: https://probe-two.invalid` | 200 | `*` | `OPTIONS` |
| 37 | `-trials` | `v13/display/message` | none sent | 200 | `*` | `OPTIONS` |
| 38 | `-trials` | `v13/display/message` | `Origin: https://example.invalid` | 200 | `*` | `OPTIONS` |
| 39 | `-trials` | `v13/display/message` | `Origin: https://probe-two.invalid` | 200 | `*` | `OPTIONS` |
| 40 | `-trials` | `csr/v2/display/message` | none sent | 200 | `*` | `OPTIONS,POST` |
| 41 | `-trials` | `csr/v2/display/message` | `Origin: https://example.invalid` | 200 | `*` | `OPTIONS,POST` |
| 42 | `-trials` | `csr/v2/display/message` | `Origin: https://probe-two.invalid` | 200 | `*` | `OPTIONS,POST` |
| 43 | `-trials` | `display/message` | none sent | 200 | `*` | `POST,OPTIONS` |
| 44 | `-trials` | `display/message` | `Origin: https://example.invalid` | 200 | `*` | `POST,OPTIONS` |
| 45 | `-trials` | `display/message` | `Origin: https://probe-two.invalid` | 200 | `*` | `POST,OPTIONS` |
| 46 | `-trials` | `v12/display/message` | none sent | 200 | `*` | `OPTIONS` |
| 47 | `-trials` | `v12/display/message` | `Origin: https://example.invalid` | 200 | `*` | `OPTIONS` |
| 48 | `-trials` | `v12/display/message` | `Origin: https://probe-two.invalid` | 200 | `*` | `OPTIONS` |
| 49 | `-trials` | `v6/display/message` | none sent | 200 | `*` | `OPTIONS` |
| 50 | `-trials` | `v6/display/message` | `Origin: https://example.invalid` | 200 | `*` | `OPTIONS` |
| 51 | `-trials` | `v6/display/message` | `Origin: https://probe-two.invalid` | 200 | `*` | `OPTIONS` |

---

## 4. `access-control-allow-origin` — the question

Every one of the 45 data cells answered `200` with `acao` = `*`.

- **distinct `acao` values across all 45 cells: one — `*`**
- per route x host, the bare, Origin-A and Origin-B values are identical
- **45/45 cells agree**
- 0 of 45 cells echoed an `Origin` value back
- no data cell was non-`200`, and no data cell lacked `acao`

`ac_family_seen` (an unanchored, case-insensitive sweep for *any*
`access-control-*` header on the wire) read
`access-control-allow-headers,access-control-allow-methods,access-control-allow-origin`
on all 45.

## 5. `access-control-allow-methods`

| path | `acam` | cells | cells agreeing |
|---|---|---|---|
| `connect/carepartner/v13/display/message` | `OPTIONS` | 9 | 9 |
| `connect/carepartner/v12/display/message` | `OPTIONS` | 9 | 9 |
| `connect/carepartner/v6/display/message` | `OPTIONS` | 9 | 9 |
| `connect/csr/v2/display/message` | `OPTIONS,POST` | 9 | 9 |
| `connect/v2/display/message` | `POST,OPTIONS` | 9 | 9 |

One value per route, unchanged across all 3 hosts and all 3 conditions. Two of
the five differ from the literal `OPTIONS`; the two that differ hold the **same
method set in a different declared order**.

## 6. The rest of the CORS family, and `vary`

Across **all 51** harness responses:

| header | present |
|---|---|
| `access-control-allow-origin` | 45 / 51 (the 6 absences are the 6 controls) |
| `access-control-allow-methods` | 45 / 51 (same 6) |
| `access-control-allow-headers` | 45 / 51 (same 6) |
| `access-control-allow-credentials` | **0 / 51** |
| `access-control-max-age` | **0 / 51** |
| `vary` | **0 / 51** |

`access-control-allow-headers`, per route, constant across 3 hosts x 3
conditions:

| path | value |
|---|---|
| `v13/display/message`, `v12/display/message`, `v6/display/message`, `csr/v2/display/message` | `Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token` |
| `connect/v2/display/message` | the same five **plus** `x-amz-apigw-id,x-amzn-requestid,x-amzn-trace-id` |

## 7. Are these the same response, or the same headers?

Stripping the per-request-volatile headers (`date`, `x-amzn-requestid`,
`x-amz-apigw-id`, `x-amz-cf-id`, `x-amz-cf-pop`, `via`, `x-cache`) and comparing
what is left:

| path | cells | distinct non-volatile heads | distinct body digests |
|---|---|---|---|
| `connect/carepartner/v13/display/message` | 9 | **1** | **1** |
| `connect/csr/v2/display/message` | 9 | **1** | **1** |
| `connect/v2/display/message` | 9 | **1** | **1** |
| `connect/carepartner/v12/display/message` | 9 | **1** | **1** |
| `connect/carepartner/v6/display/message` | 9 | **1** | **1** |

All 45 bodies are `0` bytes, `sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
(the digest of the empty string).

The full head for `connect/csr/v2/display/message`, identical in all 9 of its cells:

```
content-type: application/json
content-length: 0
access-control-allow-methods: OPTIONS,POST
access-control-allow-origin: *
access-control-allow-headers: Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token
alt-svc: h3=":443"; ma=86400
```

## 8. The hurl pin-validation requests

Nine further requests were issued by `hurl` when the new regression assertions
were executed before being committed. They are recorded as `seq` 52-60 in
`results.jsonl`, appended by hand in the same schema, because hurl does not write
the ledger. Capture and output: [`hurl-validation.txt`](hurl-validation.txt),
which records `Success ... (9 request(s))`, `Executed requests: 9`,
`Succeeded files: 1 (100.0%)`, exit 0.

**These nine rows carry only three established values each**, and the rest are
marked `(not captured by hurl --test)`:

| field | why |
|---|---|
| `http_status` `200`, `acao` `*`, `acam` `OPTIONS` | **established** — these are exactly the values the shipped assertions test, and the file executed at 100 % |
| everything else (`curl_exit`, `content_type`, the `x-amzn-*` headers, `acah`, `acac`, `acamx`, `vary`, `ctype_full`, `body_bytes`, `body_sha256`) | **not captured** — `hurl --test` does not dump response heads or bodies, and **`curl_exit` is curl-specific: curl did not make these nine requests**, so any value there would be a statement about a program that was never involved |

Those fields were **not** copied across from the harness rows, even where the
request was the same host, path and `Origin` as a harness row. A row that
describes one request must not inherit another request's evidence. No claim in
§3-§7 rests on a `seq` 52-60 row: every cell in those tables is a harness row,
`seq` 1-51.

Total vendor requests this pass: **51 (harness) + 9 (hurl) = 60**. The harness
cap was 60 and the harness issued 51; the 9 validation requests were the
separate discrete cost declared in the claim issue
([#17](https://github.com/NovaLux12/carelink-api-research/issues/17)). No
request was issued by `verdict.py`.

The nine new pinned **request blocks** are the two-origin discriminating test
(3 hosts x 2 distinct `Origin` values) and `v6`'s preflight presence (3 hosts);
under the repo's counting rule those carry **18 predicates**, 2 each — the "nine"
is a block count, the same conflation this file's own defect 10 records. The two
*exact* `allow-methods` pins added to the pre-existing `csr/v2` and bare `v2`
blocks in `04-deep-surface.hurl` were **not** re-validated here — they are
attached to request blocks that already existed, so the weekly drift sweep
exercises them at no extra request cost, and their values come from the 9-of-9
harness cells in §5.

---

## 9. Assumptions this pass did NOT test

Recorded so a reader does not over-read the grid.

1. **`Origin` was sent without `Access-Control-Request-Method`.** `probe.sh`
   sends `Origin` alone, so `Origin` is the only variable. A real browser
   preflight always carries both, so every `Origin` cell here is synthetic. The
   **`Access-Control-Request-Method` x `Origin` interaction is therefore not
   tested by this pass.**
2. **Only five route families were probed.** A route absent from §3 is not
   covered, and `probe.sh` carries no assertion that §3 is the complete set of
   preflight-bearing `clcloud.*` routes. It is a set of five paths already
   recorded on disk, not an enumeration.
3. **All 51 requests came from one network vantage point** and within one
   ~2.5-minute window. Nothing here speaks to CloudFront edge variation.
4. **No cause is established for anything in §4 or §5.** This file reports that
   the values are constant. Whether the gateway emits `*` from route
   configuration, from a stage default, or from CloudFront is not addressed by
   any request here.

---

## Correction (2026-10-12, after independent review)

A fresh-context verifier that did not watch this pass being built returned **NOT CLEAN**
twice, across two SHAs. Eight defects were raised. All are fixed; the retraction history is
kept here rather than edited away, because §1 of this file was itself corrected in place and
`findings-log/` is append-only by rule (`AGENTS.md` §3).

| # | Defect | Raised at | Disposition |
|---|---|---|---|
| 1 | `docs/11` read "20 open plus 6 closed" while the page held **19** open headings and **7** closed rows — self-refuting, in the paragraph whose own thesis is that the page's count must not disagree with its contents | `fbe5d9b` | **Fixed** to 19 and 7. Both re-derived from the page itself; the gate never reads this prose, which is why a green gate did not catch it |
| 2 | `docs/10` claimed the trials `200` on a `discover` path was "the **only** such case". Three rows qualify (36, 38, 70) | `fbe5d9b` | **Fixed.** The anomaly is `v6`-specific, not `-trials`-specific: `v11/discover/android/3.6` is `200` on all three hosts (rows 29, 37, 38) |
| 3 | **§1 of this file** claimed `run.log` ends `DONE n=51 (cap 60)`. **No such line exists** — `probe.sh` echoes that banner to stdout, never into `run.log` | `fbe5d9b` | **Fixed in place, and recorded here because that is where the retraction belongs.** §1 now states the same guarantee from what *is* on disk: `run.log` holds exactly 51 request lines, `seq` contiguous 1..51, no gaps and no extras. **The original sentence was wrong and is withdrawn** |
| 4 | The `docs/11` addendum cited `FINDINGS.md §6` for the 2-vs-12 example. Section 6 does not contain it and it appears nowhere in this file — **it is deliberately not here**, because this file is scoped to what came off the wire and that result is an offline property of the corpus | `fbe5d9b` | **Fixed.** Repointed to `docs/06` and issue #17, with the reason stated |
| 5 | `results.jsonl` rows 52–60 carried `curl_exit: 0`. **curl did not make those nine requests** — hurl did — so the field asserted a fact about a program never involved, and contradicted §8's "only three established values each" | `fbe5d9b` | **Fixed.** All 9 rows now read `(not captured by hurl --test)`, and §8's table lists `curl_exit` first among the not-captured fields |
| 6 | `docs/10` stated a counting rule and then a **figure that rule does not yield**: rule said status exactly `200`, figure said **7**. The rule yields **6**; **7** is the 2xx count, which silently adds row 28's **204** for `v10/discover/android/3.6` | `bb3127c` | **Fixed.** Rule and figure now agree at **6**, with the 2xx trap named so the next reader does not re-introduce it |
| 7 | `docs/10` said `v6` did what "its two siblings" do not — but `v11` answers `200` on all three hosts and `v12` answers `401` on all three, so no sibling version "serves nothing". As written the clause contradicted the sentence before it | `bb3127c` | **Fixed.** Restated as: for `v6` alone, `-trials` serves a document while `.eu` and `.com` serve nothing **for that same version** |
| 8 | The §1 correction (defect 3) was made by **rewriting this file in place with no Correction section**, against `AGENTS.md` §3 and against the same commit's handling of defect 2 | `bb3127c` | **This section.** The text is correct; what was missing was the trace that it had once been wrong |
| 9 | §1's minimum-gap cell read **2.042 s at seq 4 -> 5**. That gap is **2.044 s**; **2.042 s is at seq 15 -> 16** — the file's own table nine lines below said so. The value was right, the pointer wrong | `65efeff` | **Fixed.** Pointer corrected to `seq 15 -> 16`. Pre-existing since `fbe5d9b`; missed by two rounds because it sat in a cell nobody re-derived against its own table |
| 10 | The new hurl block comment called itself "**These 6 assertions** are the only ones in the suite that send an `Origin`". Under the repo's own counting rule (`static` = predicates inside `[Asserts]`) those 6 blocks carry **12 predicates**, 2 each (runtime 24 with status lines). A block count wearing the word "assertion" | `65efeff` | **Fixed.** Comment now says 6 request **blocks**, names the 12 predicates and the rule, and records 6-of-67. The substantive uniqueness claim is true and unchanged |
| 11 | `docs/06` and the `docs/11` addendum both said `area-b-v12-routing` captures **"no CORS value at all"** and that there are **four** conventions. **Both wrong**: area B carries `access_control_allow_origin` in **3** rows (`.eu` v11/v12/v13) and has a `host` column, and the pre-existing corpus uses **three** conventions. I wrote the false row *in the paragraph about querying ledgers carelessly* — from a query that read only the short key, which is the exact error the paragraph describes | `65efeff` | **Fixed, twice, in both files.** Per-ledger table replaced with one derived from the keys actually present; the wrong row and the "four" are named as retracted inline. The 2-vs-12 figures were re-derived and **hold** (2 short-key cells vs 12 across three conventions, area Z excluded) |
| 12 | `docs/10` called the split "`v6`-specific". Only **3 of 16** versions were probed on `discover/android/3.6` across all three hosts (`v6`, `v11`, `v12`); the other **13** were `.eu`-only, so a split is **undeterminable** for them, not excluded | `65efeff` | **Fixed.** Restated as "among the versions with three-host coverage", with the 13-version blind spot named and an explicit warning not to read it as "only `v6` splits" |
| 13 | The `docs/11` addendum **still said "re-parsed across all four conventions"** on the line between the sentence saying **three** and the correction note saying **three, not four**. The round-3 fix rewrote the opening and the closing and missed the middle, so the paragraph asserted three, then four, then three again | `2d36eea` | **Fixed.** The whole paragraph was rewritten as one block rather than patched again, so the retracted count has nowhere left to hide, and the per-ledger table now carries row counts summing to 17 |
| 14 | The "2 vs 12" figure carried **no unit**. Counting *rows* across the three conventions gives **17**; **12** is the count after deduplicating to (host, method, route). Not false, but a reader who counts rows gets 17 and concludes the page is wrong | `2d36eea` | **Fixed** in both `docs/06` and `docs/11`. Both now state the counting rule and name the unit. The sibling `docs/10` row already did this for its 6-vs-7 and was the model |
| 15 | **`probe.sh`'s own header comment** says the corpus stores the header "four different ways across five ledgers", and points at "FINDINGS.md §6" for the 2-vs-12 example — the same two errors as defects 11 and 4, in the harness | `2d36eea` | **NOT fixed, deliberately.** §1 above attests this harness "(unmodified, run once)", so editing it — even a comment — would falsify the attestation and edit the record of what actually ran. The false characterisation is corrected here instead: the corpus uses **three conventions across five pre-existing ledgers — two, two and one** — not the four the comment states. See [`corpus-audit.txt`](corpus-audit.txt). **This is the one place in the pass where a wrong statement is knowingly left standing**, because the alternative is rewriting history rather than annotating it |
| 16 | `docs/11` said the corpus uses "**three** conventions, **two ledgers each**". The true distribution among the five pre-existing ledgers is **2 / 2 / 1** — short keys appear in `pde-csr-cross-host` only. "Two ledgers each" is true only if area Z's own ledger is counted, and the counting rule four lines above excludes exactly that. It contradicted the paragraph's own table, its "five pre-existing files" opening and its "five-ledger corpus" rule, and it was **new in the very commit written to give the retracted count nowhere left to hide** | `5c5520b` | **Fixed, and the class fixed rather than the instance.** Corrected to "two, two and one", and every corpus-shaped figure in `docs/06` and `docs/11` is now *derived* by [`corpus-audit.py`](corpus-audit.py) — committed, exits non-zero if the shape moves, and cited from both pages — instead of asserted in prose. Five consecutive rounds found this same class; the sixth would too, so the numbers now have a source that can be re-run |
| 17 | **Round 6 was CLEAN on `c237b1f`** — no blocking defect, every figure independently re-derived from raw rows, raw `.hdr` and raw `run.log`. It raised four non-blocking points; three were in this diff and are fixed here, one was not. (a) §8 said "the nine pinned **assertions**" — verbatim defect 10, the block/assertion conflation, surviving 200 lines from where this file records having fixed it. (b) `corpus-audit.py`'s `convention()` accepted the **allow-methods** key as evidence of the full-name convention, so a ledger capturing allow-methods but never allow-origin would be misfiled — no such ledger exists, so it changed no figure, but a guard wrong only in a case that has not happened yet is not a guard. (c) `docs/10` attributed the matrix rows to **2026-07-21**; the matrix declares no date at all and its parent `VERSION-AXIS.md` is titled **2026-10-10** — a sixth instance of the class, a value asserted with no source | `c237b1f` | **Fixed (a)(b)(c).** (a) now says 9 blocks / 18 predicates. (b) `convention()` classifies on the allow-origin key alone, and `corpus-audit.txt` is byte-identical before and after — proof the latent bug never moved a figure. (c) the date is now traced to `VERSION-AXIS.md`'s title and 2026-07-21 is withdrawn inline. **(d)** round 6 also flagged `README.md`'s "12 canonical pages" vs 13 `.md` files — **pre-existing, outside this diff, deliberately not touched here** |
| 18 | Fix (c) from round 6 was **partial**: the head of the `docs/10` row was corrected and 2026-07-21 withdrawn, but ~600 characters later the same cell still read "the `discover` half rests on **2026-07-21 rows** alone" — reusing the withdrawn date as a source label, while citing `probe-2026-10-08/`. The `medtronic-carelink-2026-07-21/` directory holds no per-row `v6/discover` statuses at all, so the label pointed at something that does not contain the evidence | `8e3590d` | **Fixed.** The date label is dropped; the sentence now reads "rests on the matrix rows alone, cited below". Round 7 also caught it because the fix changed one half of a cell and left the other half — **a partial fix to a self-contradicting cell leaves the contradiction.** Swept the whole diff for the pattern afterwards: no added line now pairs a date with a load-bearing verb (`rests on`, `records`, `dated`, `re-probed since`) in the same sentence that withdraws it |

### Why the gate caught none of the three blocking `docs/` defects

Worth recording, because the next pass will assume a green gate means the prose is sound.

- The gate counts open areas by matching `^### [A-Z]. ` **headings** against the number in
  `config.yml`. Defect 1 was in **prose inside the same file**, describing the split between open
  and closed. Heading count and `config.yml` agreed throughout; only the sentence did not.
- `check_append_only()` diffs `origin/main...HEAD`. Every area-Z file is status `A` against
  `origin/main`, so an in-place rewrite of a file that has never been published is **invisible to
  it** — correctly, in my view, but it means defect 8 could not have been caught mechanically.

**No conclusion in this pass changes.** The load-bearing claim — `ACAO` constant `*`, 45 of 45,
0 echoed — was independently re-derived from the raw `headers/*.hdr` and `headers/*.body`
captures rather than from this file's own tables, in both review rounds, and held each time.
