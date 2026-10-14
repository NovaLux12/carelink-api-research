# Area S6 — Common Crawl public host/path inventory, and the byte ceiling that was silently flooring every count

**Date:** 2026-10-14 · **Claim issue:** [#95](https://github.com/NovaLux12/carelink-api-research/issues/95)
**Area:** `docs/10` open questions — the truncation/completeness row (area L's `INFERRED` line) and area M's host inventory gap.
**Scope:** `index.commoncrawl.org` CDX index API only. `data.commoncrawl.org` was allowed by the probe and **never used** — 0 requests.

---

## Accounting

| item | value |
|---|---|
| **Requests sent** | **151 of a 400 cap** — 76 from the earlier attempt on this claim, 75 from this pass. Every number in this document is recomputed from `results.jsonl` by `account.py`; none is typed by hand. |
| Method | **GET only.** Every one of the 151 rows carries `"method": "GET"`. No POST, no OPTIONS, no authentication, no token exchange. |
| Hosts contacted | **`index.commoncrawl.org` only.** No other host appears in any row. |
| **Requests to any Medtronic host** | **0.** No vendor DNS, no vendor TLS, no vendor HTTP. This is what makes the pass safe to run beside other workers. |
| Declared delay | **≥ 2.5 s per host**, `sleep` **inside** `flock .loop/host-index.commoncrawl.org.lock`. Raised to 7–15 s for later rounds via `S6_DELAY` — see §7. |
| **Measured same-host gap floor, this pass** | **2.941 s** (harness `t_sent`), **3.123 s** (kernel body-mtime oracle — **not re-derivable from a clean clone**: git does not preserve mtimes and the raw bodies live outside the repository; the `t_sent` figure is the one that reproduces from `results.jsonl` alone). **0 of 74 gaps below the declared 2.5 s.** Both figures are for **seq 77–151 only**; `account.py` prints this pass and the whole ledger separately, because they differ — the whole-ledger floor is **2.376 s** with 3 sub-floor gaps, all in the earlier attempt. The whole-ledger kernel figure (**2.916 s**) carries the same **not re-derivable from a clean clone** caveat as the 3.123 s one above. |
| Ledger | `results.jsonl`, **151 rows, 151 unique `host_tag`s**, one row per request, `t_queued`/`t_sent`/`t_done` at millisecond UTC ISO-8601. ⚠ **`curl_exit` was hardcoded to 0 on every row and is not a measurement** — see §7. |
| Bodies committed | **none.** Each body was reduced in code (`derive.py`) to bytes + sha256 + record count + the **distinct hostnames** it mentions. Raw bodies are written under `$S6_SCRATCH`, **outside the repository** — see §8. |

`account.py` prints `151 of a 400 cap`; `wc -l results.jsonl` is 151. Both agree.

> **On the 400s.** 32 rows answered **HTTP 400**. **30** of them carry the earlier attempt's escaped-ampersand fault and are described in §7; the other two are this pass's `page=1` oracle, a different query shape with a different body digest. All 32 are kept in the ledger and in the accounting above rather than deleted, because `findings-log/` is append-only and the wasted requests are part of the record.

---

## 1. Controls — sent first, and read before any candidate

The findings below are claims about **counts**, so no count was read until the instrument had returned both a known-positive and a known-zero.

| # | seq | query | answer | verdict |
|---|---|---|---|---|
| **reachability** | 77 | `GET /collinfo.json` | **200**, 35 226 B, **128 crawl indexes** published, newest `CC-MAIN-2026-39` | passed |
| **A — covered host** | 78 | `url=example.com&matchType=domain&limit=5` on `CC-MAIN-2026-39` | **200**, **5 records**, 2 hosts | passed |
| **B — true zero** | 79 | `url=s6ctlabsent987notarealhost.invalid&matchType=domain&limit=5` | **404** `{"message": "No Captures found for: …"}` | passed |

**OBSERVED.** Control B's target is under the RFC 2606 reserved `.invalid` TLD and cannot resolve, so its 404 is a real absence rather than a miss. Control A returned 5 records on the same crawl, so the API was demonstrably serving records at that moment.

**The control pair also fixes the shape of an absence on this API** (OBSERVED, seq 79): a true zero is **`404` + `{"message": "No Captures found for: …"}`**. Every negative in §6 was read against that shape and its `body_sha256` differs from a gateway page's.

**Reproduction of the control, 19.9 min apart** (OBSERVED: seq 1 `t_sent` 23:39:30.617Z → seq 77 23:59:22.885Z): seq 1 and seq 77 are both 35 226 B; seq 2 and seq 78 are both 412 B. Byte-identical. The instrument is reproducible at small sizes — which §4 turns out to be the property that makes the large sizes meaningful.

---

## 2. HEADLINE — this API truncates record responses, and the truncation is detectable from the byte count alone

**OBSERVED.** Two *identical* requests against the same cell, **18.8 min apart** (seq 102 `t_sent` 00:05:04.956Z → seq 145 `t_sent` 00:23:51.277Z, both read off the committed ledger). ⚠ An earlier draft of this line called 18.8 min "the largest gap between these two rows", which is false under every reading: the largest adjacent gap in the ledger is 10.8 min, the largest span between any two rows is 55.9 min, and the largest of the three reproduction spans quoted in this document is 20.5 min. **The 18.8 min figure is correct; only the superlative was not.**:

| seq | `fl=` | records | bytes | KiB | whole-KiB? | hosts reached |
|---|---|---|---|---|---|---|
| 102 | `url` | 5 108 | 655 360 | 640.0 | **YES** | 2 |
| 145 | `url` | 10 942 | 1 228 800 | 1200.0 | **YES** | 24 |
| 68 | `url,timestamp,status,mimetype` | 11 522 | 1 864 922 | 1821.2 | no | 37 |

A published Common Crawl crawl index does not change between two queries 18.8 minutes apart. **Therefore at least one of seq 102 and seq 145 was cut short**, and the only thing that differs between the two requests is nothing — same URL, same crawl, same `matchType`, same `fl`.

**What the host sets do and do not show** (OBSERVED, and this replaces a stronger claim an earlier draft of this section made):

- seq 145's host set is a **strict superset** of seq 102's — every host seq 102 carried, plus 22 more.
- **Every** host seq 145 added sorts **earlier** in SURT order than **every** host it still did not reach. That relation holds with **0 violating pairs** across the 22 × 13 comparison.
- ⚠ **But the response is NOT a SURT-ordered prefix, and the earlier claim that it was is withdrawn.** *(Ordering rule, recorded because the numerals depend on it: SURT key = `",".join(reversed(labels))`, so the apex sorts **before** its subdomains. Under the also-common `+ "/"` recipe the apex sorts last, the ranks below become 35 and 37, the furthest-reached host becomes the apex itself at rank 37, and the count of unreached hosts sorting before it becomes **13**, not 12. ⚠ An earlier draft of this note claimed the "12" was invariant to the ordering choice; it is not. **Only the qualitative relation is — some hosts sort before the furthest one reached — and that strengthens the refutation under either convention.** The numerals 12, 36 and 1 are stated under the canonical key only.)* Ordering the 37 hosts of seq 68 by that key, seq 145's furthest-reached host is `www.medtronic.com` at **rank 36 of 37**, while **12 of the 13 unreached hosts sort strictly before it** — `mix.`, `myprofile.`, `news.`, `newsroom.`, `oab.`, `professional.`, `signin.`, `surveys.`, `synchromed2battery.`, `www.perfusion.`, `www.ptm.`, `www.stmeded.`. Only `wwwp.` sorts after it. So the response **skipped 12 hosts and then continued past them**, which is not what a cut-at-the-boundary prefix looks like. seq 102 fails the same test (its 2 hosts are ranks 1 and 36). **What produced this ordering is not established and no mechanism is asserted.**

**The conclusion does not rest on the ordering story.** It rests on the two facts that survive independently: the queries are byte-identical, and they returned different record counts (5 108 vs 10 942) at byte counts that are both exact multiples of 1024.

**The detector.** Across the whole ledger, of the **29** successful `200` answers, **exactly three have a byte count that is an exact multiple of 1024** — and all three are the ones that do not run to completion:

| seq | bytes | KiB | cell | what it reached |
|---|---|---|---|---|
| 74 | 32 768 | 32.0 | `CC-MAIN-2022-40` / `medtronic.com` | **INFERRED, not OBSERVED** — see below |
| 102 | 655 360 | 640.0 | `CC-MAIN-2026-39` / `medtronic.com` | 2 of 37 hosts |
| 145 | 1 228 800 | 1200.0 | `CC-MAIN-2026-39` / `medtronic.com` | 24 of 37 hosts |

> ⚠ **For seq 74 "stopped part-way" is INFERRED, not OBSERVED, and an earlier draft of this paragraph stated it flatly inside an OBSERVED sentence.** Seq 74's response carries exactly **one** distinct host (`medtronic.com`), and the full 2022-40 host set was never observed — every re-issue answered 504. The inference comes from `showNumPages` on that cell reporting **`pages: 3`**, the only cell in the ledger where it is not 1. In its favour, seq 83's body digest is **byte-identical** to area M's committed seq 46, whose `blocks = 14` is published in area M's `FINDINGS.md` §3b — so the count is traceable to the corpus even though the numeral `3` itself lives only in the withheld body.

The other 26 are on no boundary at all (e.g. 1 864 922, 49 350, 19 301, 41, 40).

**The counting rule for that detector lives in code, not in this paragraph.** `account.py` computes it and prints it as the `WHOLE-KiB TRUNCATION DETECTOR` block, so the claim is re-derivable from the committed ledger by running one command rather than by trusting the sentence above (`AGENTS.md` §6 item 7 — a count generalised without a recorded counting rule is how 44 became 93).

> **A Common Crawl record response whose byte count is an exact multiple of 1024 was cut short. A response whose byte count is not, ran to completion.**
>
> This is a *correlation over 29 observations with 3 positives*, not a proven mechanism. The mechanism is **not established** and no cause is asserted — a proxy byte ceiling, a server-side emit-budget, and a client-side read cutoff all fit, and nothing measured here separates them.

**Why it matters, and what it invalidates.** Counts from this API are only trustworthy when corroborated. **The threshold itself is not established**, and this pass cannot bound it: the smallest truncating response observed is **32 768 B** and the largest response that ran to completion is **1 864 922 B**, but there is **no observation between 19 301 B and 32 768 B**, so nothing here says where inside that span the behaviour changes. An earlier draft of this section asserted a "~1 800 B" threshold; that number had no derivation anywhere in this lane and is **withdrawn**. What a reader can actually do is apply the test to every response rather than trust a size — one `body_bytes % 1024 == 0` per committed row.

**Corroboration from a second instrument** (OBSERVED, `showNumPages`):

| seq | cell | `pages` | `blocks` |
|---|---|---|---|
| 83 | `CC-MAIN-2022-40` / `medtronic.com` | **3** | 14 |
| 88 | `CC-MAIN-2026-39` / `medtronic.com` | 1 | 5 |
| 93 | `CC-MAIN-2015-48` / `medtronic.eu` | 1 | 1 |

`CC-MAIN-2022-40 / medtronic.com` is **the only cell in the ledger where `pages` is not 1**, and it is **the cell whose response is exactly 32 KiB**. `docs/10` records that `pages`/`pageSize` is not a record count and under-reports by ≥400×, so `pages: 3` does not mean "3 × 5 = 15 records". What it does support is directional: the API itself says this cell spans more than one page, which is what a truncated response looks like from underneath.

---

## 3. A count in this lane's own ledger is a floor, not a measurement

**OBSERVED.** `CC-MAIN-2022-40 / medtronic.com` was recorded at **203 records** (seq 74) by the earlier attempt on this claim. Its response was **exactly 32 768 bytes = 32.0 KiB**.

By §2's detector that response was cut short. **203 is therefore a lower bound and must not be read as the size of the set.** It is also the only cell reporting `pages: 3`.

> ⚠ **This is a self-correction inside this PR, NOT a correction to the corpus — and an earlier draft of this section got that wrong.** It was headed "CORRECTION — a *published* count" and attributed the 203 figure to area M. It is not area M's. Seq 74 sits at `seq ≤ 76`, i.e. in **this lane's own earlier attempt**, which lands in this same diff. At `origin/main` (`b528a0f`) **area M never issued a record-form query for that cell at all**: its only two attempts were `showNumPages` calls — area M seq 32, which answered **504**, and area M seq 46, which answered **200** with sha `cb7e934a…`. The figure area M's `FINDINGS.md` §3b publishes for that cell is therefore **`blocks: 14`** — not a record count. `git grep '203 records'` across `docs/` and `findings-log/` at `b528a0f` returns **0 hits**. **No published document in this repo carries 203, and `docs/10`'s area-M row never did.**

That makes this a weaker claim than it first read, and the weaker claim is the true one: it corrects a number **inside this branch's own ledger**, not one in the record.

**Three attempts were made to convert the floor into a demonstration, and all three failed** (OBSERVED): **seq 149 and seq 151** re-issued the 2022-40 cell with a narrower field set and **seq 150** re-issued the *medium* `CC-MAIN-2026-39 / medtronic.com` query — a **different cell**, so only two of the three touched the cell in question. All three answered **504** (an earlier draft wrote "502/504/504"; there is no 502 among them). A gateway failure carries no information in either direction, so **the ceiling on this cell is unconfirmed** and it stays a floor. Recorded as failed rather than quietly dropped.

**What would settle it** (one request): re-issue `CC-MAIN-2022-40-index?url=medtronic.com&matchType=domain&fl=url`. Narrow records are strictly smaller than medium records, so under any byte ceiling a narrow query must return **at least** as many records. More than 203 demonstrates the floor; exactly 203 leaves the ceiling unconfirmed on this cell.

---

## 4. The field-width invariance test — valid, but only where the response completes

`fl=` selects which fields each record carries. It cannot change which records **match**. So for one fixed `(crawl, url)` pair, issuing the same query at three field widths should give three equal counts unless a ceiling intervenes — and on the one cell where this ran to completion only **two** of the three widths came back, the narrow one (seq 104) answering 504 — narrower records are smaller, so more of them fit under any ceiling.

**Demonstrated on a cell that completes** (OBSERVED, `CC-MAIN-2015-48 / medtronic.eu`):

| seq | `fl=` | records | bytes | whole-KiB? |
|---|---|---|---|---|
| 61 | `url,timestamp,status,mimetype` | **132** | 19 301 | no |
| 105 | `url,timestamp,status,mimetype` | **132** | 19 301 | no |
| 92 | `url,timestamp,status,mimetype,digest,filename,offset,length` | **132** | 49 350 | no |
| 104 | `url` (narrow) | — | — | **504** — gateway failure, carries no information |

**Two** widths across three issues, a **2.56× spread in response size, one record count**, and the medium query reproduced **byte-for-byte** across two issues **20.5 min apart** (seq 61 `t_sent` 23:45:38.258Z → seq 105 00:06:07.713Z). No ceiling at this size.

**⚠ The test does not work where truncation bites, and this pass demonstrated why.** On `CC-MAIN-2026-39 / medtronic.com` the *narrower* field set returned **fewer** records than the wider one (5 108 and 10 942 vs 11 522) — the opposite of what a ceiling predicts. Width-invariance is therefore **not** usable as a truncation detector on this API on its own, and a first draft of this section treated it as one. The whole-KiB test in §2 is the detector; the width test is corroboration, and only on a cell that completes.

---

## 5. Host inventory — five `medtronic.com` host names the repo does not carry

**OBSERVED** (seq 68, `CC-MAIN-2026-39` / `medtronic.com`, 11 522 records, 1 864 922 B, **37 distinct hosts**, byte count not on a KiB boundary so not a truncation candidate).

Of the 37, these five **appear in no file in this repository as it stood before this branch**.

> **Counting rule** (it is in code terms rather than prose, per `AGENTS.md` §6 item 7): `git grep -il <name> $(git rev-parse origin/main)` over **all** tracked files — not a subset of extensions. An earlier check of this claim used `grep --include='*.md' --include='*.hurl' --include='*.sh'`, which would have hidden a match in a `.tsv` or `.json`; the five were re-checked with `git grep` over every tracked file at `origin/main` (`b528a0f`) and all five return **0 files**. The wording is "as it stood before this branch" and not "in no file", because at this branch's own head **all five** appear in **2 files each** — this document and `results.jsonl` (`distinct_hosts`) — under a literal FQDN grep. `docs/11` carries them in abbreviated form (`synchromed2battery.`), which a FQDN grep does not match.

| host | why it is interesting |
|---|---|
| `synchromed2battery.medtronic.com` | **INFERRED, and weakly:** the label reads as naming the *SyncMed 2* pump line, which is retired. **No source in this repo supports that** — `git grep -i 'syncmed' origin/main` returns **0 hits**. What is OBSERVED is only that the name carries the `battery` token and appears in the newest published crawl. Treat the product reading as a guess. |
| `e-thoth.medtronic.com` | Unexplained single-word label; no repo context. |
| `oab.medtronic.com` | Three-letter label; no repo context. |
| `bakkeninvitation.medtronic.com` | Reads as a one-off campaign/micro-site, not a product surface. |
| `kappasigmasnlist.medtronic.com` | Reads as a generated list artefact; no repo context. |

Also present and **already in the corpus at `origin/main`**, listed here so the new list is not mistaken for a complete novelty claim: `americas.connect.medtronic.com` (a `connect.`-namespace host — `findings-log/probe-2026-10-08/recon/cc/COMMONCRAWL-URLS.md` **§7 item 5**, line 408, records it as a Wayback recursion artefact; **§4c** of that file is about `connect.medtronic.com`'s REST surface and never mentions it) and `diabetesresoursesportal.medtronic.com` (already in `RECON-SUBDOMAINS.md:318`, and notable only because the vendor misspells *resources* in the hostname). Both return **1 file** at `origin/main` under the counting rule above.

> **⚠ Scope limit, stated because it is the limit of the instrument.** Presence in a crawl index means a Common Crawl crawler **encountered the name** during 2026-09-04 → 2026-09-17. It does **not** mean the host resolves today, that it is operated by Medtronic, or that it is part of any deployment this repo probes. Per `AGENTS.md` §7, `*.carelink.*` and `*.clcloud.*` are wildcard parking DNS and ~50 collected names in this corpus are known false positives; nothing here was resolved, because resolving them would mean contacting vendor infrastructure, which is **0 requests** by design. These five names are **candidates for a future DNS-only check**, not assets.

---

## 6. Path-prefix inventory — three anchored negatives, two unanchored

`matchType=prefix` asks for paths beginning with a given prefix. The candidate list is bounded and derived from repo artefacts (`AGENTS.md` §8): `/patient/` and `/connect/` are the two prefixes area M already named; `/ipro/`, `/hcp/` and `/oauth2/` come from this lane's brief and the path vocabulary in `docs/06`/`docs/07`. Two host groups, three crawls — 30 queries, listed in full in `queries-07-path-prefix.txt`.

**The instrument was degraded during this round: 25 of 30 answered 502/504.** A gateway failure is not an absence, so **25 cells are unmeasured**, not negative.

The five that answered, all `404` true-zero (`{"message": "No Captures found for: …"}`, seq 118/129/136/137/139). "Anchored" means a **record-form query naming the same (crawl, host) cell** returned `200` with records:

| seq | crawl / host | prefix | anchored? |
|---|---|---|---|
| 129 | 2022-40 / `medtronic.com` | `/connect/` | **yes** — seq 74, same cell, 203 records |
| 136 | 2013-48 / `medtronic.eu` | `/ipro/` | **yes** — seq 65, same cell, 112 records |
| 137 | 2013-48 / `medtronic.eu` | `/hcp/` | **yes** — seq 65, same cell, 112 records |
| 118 | 2026-39 / `medtronic.eu` | `/oauth2/` | **❌ NO** — no row has ever returned a positive for this cell |
| 139 | 2013-48 / `medtronic.com` | `/connect/` | **❌ NO** — see below |
| — | 2026-39 / `medtronic.com` | `/connect/`, `/patient/` | **unmeasured** — seq 119, 120 answered 504 |

> ⚠ **An earlier draft of this table labelled seq 139 "yes — same cell holds 112 records (seq 65)". That was wrong, and it is the exact error this repo's §6 item 4 warns about: a verification that reads back the wrong target and looks like it applied.** **Seq 65 is `url=medtronic.eu`**, not `medtronic.com` — its 112 records belong to the *other* host group. The only record-form query in the entire ledger for `2013-48 / medtronic.com` is **seq 66, which answered 504**. So seq 139's `/connect/` absence is **exactly as unanchored as the `/oauth2/` one**, and the prose below it ("each of those absences sits inside a cell proven non-empty") was false for one of its two claims.

**What survives, precisely:**
- **Anchored (3):** `/connect/` absent from `medtronic.com` on 2022-40 (seq 129); `/ipro/` and `/hcp/` absent from `medtronic.eu` on 2013-48 (seq 136, 137). Each sits inside a cell proven non-empty.
- **Unanchored (2):** `/oauth2/` on `2026-39 / medtronic.eu` (seq 118) and `/connect/` on `2013-48 / medtronic.com` (seq 139). Both must not be cited as absences. The queries that would anchor them — seq 144 (`2026-39 / medtronic.eu`) and a re-issue of the `2013-48 / medtronic.com` domain cell — answered **504**.

Anchoring queries that failed: seq 144; seq 146, 147, 148 on the adjacent `/connect/` and `/patient/` cells. **All 504.**

⚠ **This sweep is on a DIFFERENT namespace from area M's claim, and reproduces NONE of its cells.** Area M's statement is verbatim: *"Across **every** capture recovered for `minimed.eu` in **all six** crawls, **not one path begins `/patient/` or `/connect/`"* — scoped to **`minimed.eu`**. This pass swept only `medtronic.eu` and `medtronic.com`; it has **no `minimed.eu` cell at all**. Area M never enumerated a path on either `medtronic.*` host either — its only record-form queries there are **controls** (`limit=5`, plus absent-host controls), the rest being `showNumPages` block counts. So what this section establishes is a **new negative on a namespace its predecessor did not read**: `/connect/` absent from `medtronic.com` on 2022-40, `/ipro/` and `/hcp/` absent from `medtronic.eu` on 2013-48. It is **neither a reproduction nor a refutation** of area M's `minimed.eu` claim, and adds nothing against it — the two pass over different hosts.

---

## 7. Methods — delay, spacing, and two oracles

**Delay enforcement.** `sleep 2.5` runs **inside** `flock .loop/host-index.commoncrawl.org.lock`. A sleep outside the lock lets other workers queue and then fire together inside one window, which is worse than no lock.

**Measured spacing, this pass** (OBSERVED, recomputed by `account.py`):

- harness `t_sent` series, minimum **2.941 s**, **0 of 74 gaps below 2.5 s**;
- kernel body-mtime oracle, minimum **3.123 s** — **not re-derivable from a clean clone**: git does not preserve mtimes and the raw bodies live outside the repository; the `t_sent` figure is the one that reproduces from `results.jsonl` alone;
- **0 overlapping request intervals**; `host_seq` strictly increasing.
- ⚠ **`curl_exit` is 0 on all 151 rows by construction, not by measurement** — `record.py` hardcoded it. Exactly **1 of 151** stderr files is non-empty (`s6cmp-2026-39-medtronic-com-numpages.err`, seq 88: `curl: (18) transfer closed with outstanding read data remaining`), and that body is a complete 40 B JSON document, so no published figure is affected. An earlier draft of this section asserted "`curl_exit` 0 on every row" as an **integrity property**; that was false — a constant that cannot fail is not a check, which is the defect `derive.py`'s own docstring names. `record.py` and `probe.sh` now capture curl's real `$?`; the 151 existing rows predate that and their column carries no information.

**Delay was raised mid-pass.** `run.log` records the per-invocation delay in order: **2.5, 2.5, 2.5, 8, 10, 7, 12, 15, 15** — the first three invocations ran at the declared 2.5 s, then it was raised, not monotonically. Inter-round pauses (`t_done` → `t_sent`, ledger-measured) were **639.2, 306.1, 246.4 and 322.2 s**. because the API degraded sharply: **81 of 151 answers were 502/504**, and at a fixed 2.5 s the informational yield collapsed across rounds. (An earlier draft cited "8 of 15" and "0 of 8"; those two figures were not reproducible under any counting rule stated here and are withdrawn. The reproducible statement is the one above: 81 of 151 answers carried no information, and per-round yields are read off the ledger's own `queries-0*.txt` ranges — seq 80–94, 95–105, 106–113, 114–143.) Raising the delay is the honest fix; retrying faster is what gets a caller throttled. Every raised-delay row is in the ledger with its real `t_sent`.

**Two spacing oracles, reported together on purpose.** `account.py` prints both and does not prefer either. The harness series is what the probe *claims*; the kernel series is the mtime of the body file, which `curl` wrote, so it cannot be an assertion the harness makes about itself. `docs/09` §4's rule is that where they disagree, the harness series is the suspect.

**Defects in the earlier attempt on this claim — disclosed, not smoothed over:**

1. **30 requests wasted on a malformed query.** `queries-02-inventory.txt` wrote `\&` between parameters, which reached the API as a format named `json\`. **30** rows answered **HTTP 400** with body `{"message":"output=json\ not supported"}` — seq **4–30 and 32–34**, one sha256 (`280bf6d3…`). (An earlier draft said 31 and cited the range "seq 4–34"; seq 31 is a **502**, so the range holds 30 rows, not 31. Counted from the ledger, not from the range.) The later per-crawl files used bare `&` and worked. **Cost: 30 of the 400 cap, and 30 rows in the ledger that measure nothing.** Kept, not deleted.
2. **Five rows record `t_done` before `t_sent`** (seq 4, 5, 21, 27, 28), which is impossible under the script's own documented order (sleep → `date` → curl → `date`). **Cause not established.** A plausible mechanism — the script being edited while `bash` was still reading it, since `bash` reads scripts incrementally — is **INFERRED and unverified**, and is not offered as an explanation.
3. **Three harness gaps below the declared 2.5 s** (seq 5→6 at 2.484 s, 21→22 at 2.376 s, 28→29 at 2.390 s). The kernel oracle puts the minimum at **2.916 s** and shows **no overlap**, so the requests were not actually closer than the declared delay — but the harness series disagrees with the oracle and the disagreement is recorded rather than resolved in the harness's favour.

All three defects are confined to `seq ≤ 28`, i.e. to the earlier attempt. **This pass's own 75 rows are clean on every one of these checks.**

**Fixes made before this pass sent anything**, in `probe.sh`:
- the ledger row is now appended **inside** the flock, so a row cannot carry another request's timestamps (defect 2's mechanism);
- tags are asserted **unique against the existing ledger** before a request is sent, and a duplicate aborts rather than silently overwriting;
- the row writer is a separate file (`record.py`) rather than a heredoc inside the `flock -c` string — the first attempt inlined it, one unescaped `"` in the Python made the whole critical section exit 127, and the request was correctly refused with no row written;
- `derive.py --selftest` passes, so the host-only projection that keeps response text out of the repository is falsifiable.

---

## 8. Response-handling policy

`AGENTS.md` §7: Common Crawl captures carry `jsessionid_*` values in URL paths and pre-Auth0 authorize URLs whose `sessionData` is a plaintext-base64 JWS. **No response body is committed anywhere in this directory.** Each body is reduced, in code, to byte count + sha256 + record count + the **distinct hostnames** it mentions. A hostname is the leftmost label of a URL and cannot carry a path, a query string or a session parameter. Raw bodies and timestamp scratch are written under `$S6_SCRATCH`, **outside the repository** (default `${TMPDIR:-/tmp}/carelink-s6-lane-scratch`), because two genuine CC responses here are 1.86 MB and 1.2 MB and the gate's hygiene check globs `findings-log/` for anything over 1 MiB. The committed artefacts in this directory are `probe.sh`, `record.py`, `derive.py`, `account.py`, the query files, `run.log`, `headers/`, `results.jsonl` and this document.

Bodies were read locally during the pass to derive facts — the byte counts and the `showNumPages`/`page=1` bodies quoted above — and **no body text is reproduced in this document beyond the four shortest API status sentences** (`No Captures found for:`, `Page 1 invalid:`, `output=json\ not supported`, and the `{"pages":…}` counters), none of which is a capture.

---

## 9. What is NOT established

- **The mechanism of the ceiling.** A proxy byte cap, a server emit-budget and a client read-cutoff all fit the observations. Nothing measured here separates them. **No cause asserted.**
- **Whether the ceiling is a fixed constant.** Three different boundaries were observed — 32.0, 640.0 and 1200.0 KiB — so **it is not a fixed size**. What sets it is unknown.
- **`CC-MAIN-2022-40 / medtronic.com` beyond "≥203".** Two re-issues of this cell (seq 149, 151) plus one of a different cell (seq 150); **all three answered 504**, and there is no 502 among them.
- **The `2026-39 / medtronic.eu` `/oauth2/` absence.** Unanchored; the anchoring query answered 504.
- **25 of the 30 path-prefix cells.** Gateway failures, not absences.
- **Whether any of the five §5 host names resolves.** Zero vendor requests by design.
- **Whether the 11 522-record `medtronic.com` set is itself complete.** Its byte count is not on a KiB boundary, which is the detector passing — but the detector is a correlation over 29 observations, not a proof, and `pages: 1` + `Last Page = 0` are the API's accounting of a set that is being cut off *below* the layer those oracles observe.

## 10. Successors

1. **Re-issue the two cells that would settle this** (1–2 requests): `CC-MAIN-2022-40/medtronic.com` and `CC-MAIN-2026-39/medtronic.com`, at a long delay, when the API is healthy. Both are in `queries-09`/`queries-10` and need no new query text.
2. **Audit every committed CC row in this repo with the whole-KiB test.** `account.py` now takes a ledger path (`python3 account.py <ledger>`) and **area M has been done: 38 `200`s, 0 whole-KiB, largest response 35 226 B — none of area M's counts is a floor by this test**, which retracts this log's own earlier speculation that area M's larger cells were probably affected. **The detector is the whole reason, and no size argument is used**: area M's largest response (35 226 B) is in fact **larger** than this lane's smallest truncation (32 768 B), so a size threshold cannot be what makes it safe, and §2 records that the threshold is not established in any case. One observation in its favour, offered as a separate fact and **not** as the argument: area M's largest response is 34.4 KiB against this lane's largest (1 821.2 KiB), so area M never worked with a response anywhere near the two larger observed boundaries (640.0 and 1 200.0 KiB). ⚠ It **did** cross the smallest one, at 32.0 KiB. The three byte-identical `200` pairs in this ledger are 412 B (seq 2/78), 35 226 B (seq 1/77) and 19 301 B (seq 61/105). **Area L's ledger and any other CC ledger remain unaudited.** OBSERVED, 0 requests.
3. **A DNS-only pass over the five §5 host names**, which is vendor traffic and therefore **outside this lane's zero-request scope**.

---

## Files in this directory

| file | what it is |
|---|---|
| `FINDINGS.md` | this document |
| `probe.sh` | the probe. GET-only, host allowlist, per-host `flock`, ≥2.5 s inside the lock, cap 400, duplicate-tag refusal |
| `record.py` | appends one ledger row, called **inside** the lock |
| `derive.py` | reduces a body to host-only facts; `--selftest` is falsifiable |
| `account.py` | recomputes every number in this document from `results.jsonl` |
| `results.jsonl` | 151 rows, one per request |
| `run.log` | per-request log line with the three timestamps |
| `queries-0*.txt` | every query sent, with the reasoning for the candidate lists |
| `headers/` | response headers (no bodies) |
| `bodies/`, `ts/` | **not in this directory and not in the repository.** Raw response text and timestamp scratch live under `$S6_SCRATCH` (default `${TMPDIR:-/tmp}/carelink-s6-lane-scratch`), because two genuine CC responses in this pass are **1.86 MB** and **1.2 MB** and the gate's hygiene check globs `findings-log/` for anything over 1 MiB. `probe.sh`, `record.py` and `account.py` all take the location from `S6_SCRATCH`. **Consequence, stated because it is a real limit:** the kernel body-mtime spacing oracle is **not re-derivable from a clean clone** — git does not preserve mtimes (the same caveat area D records), so the load-bearing spacing figure is the millisecond `t_sent` series, which reproduces from `results.jsonl` alone. |