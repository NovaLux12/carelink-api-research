# Area AR — the `/hcp/configuration/` 405 does **not** extend to a third subtree: it is scoped to `configuration`

**Claim:** [NovaLux12/carelink-api-research#212](https://github.com/NovaLux12/carelink-api-research/issues/212) ·
**Date:** 2026-11-11 · **Area:** AR · **Branch:** `research/ar-third-subtree`
**Hosts:** `carelink.medtronic.eu`, `carelink-support.medtronic.com` — and no others
**Cap:** **Total 18 of a 18 cap**, itemised before the first request, **0 recorded revisions**

Legend (`AGENTS.md` §2) — **OBSERVED** = seen in a live response · **PUBLISHED** = in a vendor
document served without a login · **INFERRED** = reasoned, not seen.

---

## The answer in one paragraph

**The constant is scoped to `/hcp/configuration/` and does not follow a handler class.** Three
subtrees were derived from the shipped clinic build — **`/hcp/user/`, `/hcp/clinics/`,
`/hcp/reports/`** — and every one of them answers an absent child with the plain `/hcp/` shape:
**`404`, 0 bytes, no `Content-Type`, at depth 1 AND depth 2, on both hosts, 6 of 6 cells**
(OBSERVED). `/hcp/configuration/<absent>` answered **`405` + `Allow: POST, OPTIONS`** on those
same two hosts in the same run, between the same locks (OBSERVED). So the `405 + Allow`
that area AG found to be a subtree constant, and area AL found invariant across four hosts, is
**a property of the `configuration` subtree alone** — three sibling subtrees that the same build
drives do not reproduce it (OBSERVED for the six cells; **INFERRED** that the selector is a mount
on that one prefix, because a mechanism is not visible to a GET).

**This closes the two-point-pattern worry on the negative side.** AR was minted because
`configuration` and `patients` are not a pattern. They are now not a pattern for a measured
reason: `configuration` is the outlier, and everything else that was tested behaves like `/hcp/`.

---

## 1. Request accounting — 18 of a 18 cap, no revision

| | n |
|---|---:|
| **Cap, declared before the first request** | **18** |
| Requests sent | **18** |
| `curl_exit` ≠ 0 | **0** |
| Rows in `results.jsonl` | **18** |
| Hosts contacted | **2** — the two I own, no others |

The cap **is** its itemisation, and `probe.sh` holds a single `CAP=18` assignment that its
`cap_guard` reads:

```
3 controls x 2 hosts                     =  6
3 derived subtrees x 2 depths x 2 hosts  = 12
                                           --
                                           18
```

`python3 verify.py` re-derives that sum from `derive.txt` and `candidates.txt` and prints
`3 controls x 2 hosts + 3 subtrees x 2 depths x 2 hosts = 18, cap is 18`.

**No cap revision was recorded, because none was needed** — a first for this run's areas, and it
is a consequence of the derivation costing zero requests (§2). The candidate list was **not**
typed into `probe.sh`: the sweep reads `candidates.txt`, which `derive.py` wrote before it ran.

**Method:** `GET` only. No `POST`, no `OPTIONS`, no token, no cookie, no patient id, no wordlist.
The only header sent is `X-System-ID: ProWeb`, and only on the one positive control per host.
`--compressed` on every request. `--max-time 120`.

**Hosts.** This lane owns `carelink.medtronic.eu` and `carelink-support.medtronic.com`. It did
**not** touch `carelink.medtronic.com` (a sibling lane's host), `carelinkhp.minimed.eu`
(§10 — do not re-run), or any `clcloud` host. Two hosts is what the claim bought, and the
close condition in `docs/11` asks for "at least two hosts", which is met.

## 2. The derivation — read out of the build, not guessed

`AGENTS.md` §8 forbids wordlists. The convention here is structural rather than lexical: every
client route in the portal build is a string literal beginning `hcp/`, so the set of **depth-1
segments** those literals use *is* the set of subtree names the build knows about. `derive.py`
never types a candidate name.

**The derivation cost 0 requests.** The clinic bundle `/main.fb5f8cb7eb60c4d5.js` was already in
this run's asset cache — fetched by area AQ — and `derive.py` verifies its sha256 against the
value area AB pinned **before extracting anything**:

```
bundle: bytes=3397615 sha256=2a7fa8e7af519c2b493caf62c00b46c5e75a357048444dbf7abff6136bfc02ba
pinned: bytes=3397615 sha256=2a7fa8e7af519c2b493caf62c00b46c5e75a357048444dbf7abff6136bfc02ba
reproduces=True
```

That is what makes the extraction defensible: a build whose digest did not reproduce would have
had no recorded route table applied to it, and `derive.py` exits `2` rather than deriving from it.

**What the build holds.** 190 string literals starting at `hcp/`, spanning **20 distinct
depth-1 segments**. Two are AR's controls, not its candidates — `configuration` (the reference
this area is testing the scope of) and `patients` (measured by area AQ in this same run). Removing
them leaves **18 surviving subtrees**:

| segment | distinct literals | | segment | distinct literals |
|---|---:|---|---|---:|
| `patients` | 38 | **excluded** — area AQ | `settings-calculator` | 4 |
| **`user`** | **34** | **candidate 1** | `access-data` | 3 |
| **`clinics`** | **32** | **candidate 2** | `fastLinking` | 3 |
| `configuration` | 21 | **excluded** — AR's control | `linkedPatient` | 3 |
| **`reports`** | **10** | **candidate 3** | `sso` | 3 |
| `insights` | 8 | not reached | `countries` | 2 |
| `dataUpload` | 6 | not reached | `registrationCheck` | 2 |
| `anonymization` | 4 | not reached | `remoteLinking` | 2 |
| `follow-up` | 4 | not reached | `locale` | 1 |
| | | | `ping` | 1 |
| | | | `v2` | 1 |

**Ranking rule, stated before the number was used:** exclude the two measured segments; order the
remainder by **distinct literal count, descending, then alphabetically**; take the top 3. The
count is a proxy for "this subtree is genuinely handled" — 34 literals is a mount, 1 may be a leaf
path that merely looks like a subtree. **The proxy is INFERRED** and it only decides *which* three
subtrees were bought; the verdict is read from the response, not from the count.

**Not reached, and explicitly so:** `insights` (8), `dataUpload` (6), `anonymization` (4),
`follow-up` (4), `settings-calculator` (4), `access-data` (3), `fastLinking` (3), `linkedPatient`
(3), `sso` (3), `countries` (2), `registrationCheck` (2), `remoteLinking` (2), `locale` (1),
`ping` (1), `v2` (1). The budget bought three. Their absent-path behaviour is **unmeasured**, and
this log does not generalise the six cells to them.

## 3. Controls first, per host — 6 of 6 reproduce

Sent **before any candidate on that host**, inside the same per-host lock.

| control | expected (recorded) | `carelink.medtronic.eu` | `carelink-support.medtronic.com` |
|---|---|---|---|
| `/hcp/configuration/public/pow.crm.settings` + `X-System-ID: ProWeb` | 200 | **200**, 96 B, `a977733a53ee0d5f…` | **200**, 97 B, `370e3bba0d28c540…` |
| `/hcp/configuration/zz-ar-absent-6293` | 405 + `Allow: POST, OPTIONS`, 0 B | **405**, 0 B, `POST, OPTIONS` | **405**, 0 B, `POST, OPTIONS` |
| `/hcp/zz-ar-absent-6293` | 404, 0 B, no `Content-Type` | **404**, 0 B, `(none)` | **404**, 0 B, `(none)` |

**6 of 6 reproduce exactly (OBSERVED).** The 96/97-byte split and both digests reproduce area A's
and lane l2's record as re-derived by area AQ §3, so these two hosts are serving the documents
this repository pins. The absent cell directly under `/hcp/` answers a real `404` with **no
`Content-Type`**, confirming again that a `404` below that prefix is a true absence and not area
AK's 5518 B fallback.

The fabricated name is **`zz-ar-absent-6293`**. `git grep -c 'zz-ar-absent-6293' -- .` at this
head returns **nothing** (exit 1, no output) — a name no tracked file carries.

## 4. The measurement — 6 of 6 cells are the `/hcp/` shape

| host | subtree | depth 1 | depth 2 | `Allow` |
|---|---|---|---|---|
| `carelink.medtronic.eu` | `/hcp/user/` | **404**, 0 B, no CT | **404**, 0 B, no CT | — |
| `carelink.medtronic.eu` | `/hcp/clinics/` | **404**, 0 B, no CT | **404**, 0 B, no CT | — |
| `carelink.medtronic.eu` | `/hcp/reports/` | **404**, 0 B, no CT | **404**, 0 B, no CT | — |
| `carelink.medtronic.eu` | `/hcp/configuration/` | **405**, 0 B, `POST, OPTIONS` | — | `POST, OPTIONS` |
| `carelink-support.medtronic.com` | `/hcp/user/` | **404**, 0 B, no CT | **404**, 0 B, no CT | — |
| `carelink-support.medtronic.com` | `/hcp/clinics/` | **404**, 0 B, no CT | **404**, 0 B, no CT | — |
| `carelink-support.medtronic.com` | `/hcp/reports/` | **404**, 0 B, no CT | **404**, 0 B, no CT | — |
| `carelink-support.medtronic.com` | `/hcp/configuration/` | **405**, 0 B, `POST, OPTIONS` | — | `POST, OPTIONS` |

Every cell is copied from `results.jsonl` by `verify.py` §4, not from this table.

**The three-way reading that `docs/11` pre-registered, applied:**

- Both depths `404` → **a discriminating subtree.** This is what all three answered, on both hosts.
- Both depths `405 + Allow` → the constant follows a handler class. **Not observed anywhere.**
- A mix → something more interesting. **Not observed**, so there is no mix to report.

**Depth was not decorative.** Depth 2 (`<subtree>/<absent>/zz`) separates a handler mounted *on*
the subtree — which would answer every child path regardless of depth — from a handler answering
only its own depth-1 children. All six depth-2 cells `404` at 0 B, so neither shape exists on
these subtrees: they are ordinary routed namespaces that answer absences the way `/hcp/` does.

**The `Allow` *value* question §The design raised.** `docs/11` noted that if a second subtree
answered `Allow: GET, POST, OPTIONS` where `configuration` answers `POST, OPTIONS`, the constant
would be per-subtree and `Allow` would still be saying something. **That question dissolves on the
negative result:** there is no `Allow` header on any of the six cells at all, so there is no value
to compare. The header does not exist outside `configuration`'s 405s, which is the strongest form
of "not a subtree constant".

## 5. What this settles, and what it does not

**Settled (OBSERVED):** on `carelink.medtronic.eu` and `carelink-support.medtronic.com`, an
absent path under `/hcp/user/`, `/hcp/clinics/` and `/hcp/reports/` answers a genuine `404` at two
depths — while an absent path under `/hcp/configuration/` on the same hosts, in the same run,
answers `405 + Allow: POST, OPTIONS`. The constant is **scoped to `configuration`**.

**Settled by consequence (OBSERVED, and this is the useful part):** a `405` recorded inside those
three subtrees **would** discriminate a registered route from an absent path, the way area AQ
showed a `405` inside `hcp/patients/` does. Area AL's reading — "any pass that reads a `405` under
`/hcp/configuration/` as *route present, wrong method* is reading a subtree constant" — is
**correct and stays correct**, and the constant is now known not to be the shape of the namespace.

**Not settled:** *why* `configuration` is the exception. That is a mechanism, it is invisible to a
GET, and it is stated as **INFERRED**: the most economical reading is that `configuration` is the
one prefix with a handler mounted directly on it whose own method filter answers before any route
resolution, while the other subtrees are resolved by the ordinary router. **No observation here
distinguishes that from a rewrite rule that special-cases the one prefix.** Area AN's finding that
the `404` and the `405` are one layer's answers sharing every header but `Allow` is consistent with
either, and consistency is not proof.

**Also not settled:** the 15 subtrees §2 did not reach; any host other than the two I own; and
whether `patients` behaves this way at depth 2 — area AQ controlled depth 1 only (§7).

## 6. Does any recorded `405 + Allow` verdict need re-reading? — No

This was the deliverable that mattered most if the answer had gone the other way, so it was
measured rather than assumed. A census over every committed `results.jsonl` under `findings-log/`
finds **38 recorded `405` rows whose path starts `/hcp/`**, and they live under exactly two
subtrees:

| subtree | rows | ledgers | status of the subtree's absent-path control |
|---|---:|---|---|
| `configuration` | 21 | AB (9), AG (6), AK (4), AR (2) | **known constant** — the 405 there carries no existence information, already recorded by AG/AL |
| `patients` | 17 | AQ (17) | **controlled at depth 1** — AQ measured a `404`, 0 B on 4 of 4 hosts, and 15 candidates `405` while 3 `404` at the same depth under the same parent |

**No recorded `405` verdict anywhere in this repository sits under a subtree with no absent-path
control.** So **no lane's work needs a correction**, and none is appended — the `## Correction`
deliverable is satisfied by a measured negative, not by a retraction.

⚠ **One boundary is stated rather than left for a reader to discover.** AQ's absent-path control
is at **depth 1**. AQ's candidate set includes nested names (`otc-linking/allowed`,
`care-partner/search`), and AR's six depth-2 cells are evidence that *these three* subtrees `404`
at depth 2 — not that `patients` does. AQ's nested `405`s are therefore controlled one level up
rather than at their own depth. AR does not retract them (the same run measured `404`s at the same
depth under the same parent, which no child-answering handler produces) but the gap is real and is
carried as a successor condition rather than smoothed over.

## 7. Delay accounting — two clocks, both published, and clock B proven live

`probe.sh` takes the `sleep 2.5` **inside** the per-host `flock`, one lock file per host, copied
from area AB's structure — a declared floor of `≥ 2.5 s` spacing between requests to the same host. Two clocks were kept, and — per trap 5 — clock B is published **only
because its liveness was proved**: 18 bodies, **18 distinct mtimes**, so it is a request-time clock
and not one build timestamp.

```
clock A — t_sent (re-derivable from results.jsonl)
  gaps 16   min 2.060 s   median 2.609 s   max 3.546 s
  under 2.5 s : 1  (seq 11->12, 2.060 s)
  under 2.0 s : 0
  impossible negative DURATIONS (t_done < t_sent): seq 11, -0.477 s

clock B — kernel body mtimes (NOT re-derivable from a clean clone)
  bodies stat-able 18 of 18   DISTINCT mtimes 18 of 18   -> LIVE
  gaps 16   min 2.590 s   median 2.626 s   max 2.823 s
  under 2.5 s : none          FLOOR ON THIS CLOCK: 2.590 s
```

Gap count checked against the grouping rule rather than eyeballed: group by host, sort by `seq`,
then zip — `sum(rows_per_host - 1)` = `8 + 8` = **16**, and both clocks produce **16**.

The single sub-2.5 s gap on clock A is `seq 11→12`, and `seq 11` is the row whose own `t_done`
precedes its `t_sent` — arithmetically impossible, so at least one stamp on it is corrupt. Under
the counting rule `docs/09` §4 already sets, a short gap measured off a provably corrupt series is
an artefact of that corruption and is not evidence of underspacing; the kernel clock reads **0 of
16 gaps under 2.5 s, floor 2.590 s** (OBSERVED). **No delay rule is claimed breached**, and no
cause is asserted for the corrupt stamp — it is the known `corrupt-t0` class.

## 8. Re-running this pass

`probe.sh sweep` re-issues all 18 requests and appends to `results.jsonl`. `derive.py` needs the
clinic bundle at argv[1]; `.loop/` is gitignored so **the bundle is not committed** and this
derivation is not re-runnable from a clean clone — `derive.txt` records its byte count and sha256
so the figures stay auditable without it, and `probe.sh` does not need it (it reads the committed
`candidates.txt`). `verify.py` needs `$AR_SCRATCH` (default
`<repo>/.loop/ar-scratch`) for clock B; with the scratch dir gone it reports clock B **not live**
and claims one clock, which is the correct degradation rather than a silent failure.

## 9. Successor — **AY**

Minted as **AY** in `docs/11` at this head (`origin/main` was at `73d2df0`; `AY` was free there and
still free at commit time). Two halves, because the ledger's own answer splits:

- **(a) the mechanism** — is the `configuration` exception a mounted handler whose own method
  filter answers before route resolution, or a rewrite that special-cases that one prefix? Area AN
  showed the `404` and the `405` share every header but `Allow`, which is consistent with **either**
  reading (**INFERRED**, not proof). This half may be **undecidable from outside** — the deployment
  configuration is not served publicly and not in the bundles — and saying so is the close
  condition, not a failure.
- **(b) the `patients` depth-2 control** — AQ controlled depth 1 only (§6, ⚠). Four cells, GET only,
  on hosts this lane already owns.

**One assumption of AR's own is now falsified and is recorded as such:** `docs/11`'s AR block
asserted (INFERRED) that "a subtree boundary is a property of how Apache mounts a handler, so a
third mounted subtree should reproduce the shape." Three mounted sibling subtrees did **not**
reproduce it. The assumption is not retracted from the page — the Closed row quotes it — but no
later pass should rest on it.

## 10. What AR records as a limit rather than as a defect

`derive.py` reads a bundle that is **not committed**, so the derivation is not re-runnable from a
clean clone. That is disclosed in the script's own docstring and in `derive.txt` (byte count and
sha256 beside every figure), and it is why the digest check runs **before** extraction. A reader
who wants to re-derive it must re-fetch `/main.fb5f8cb7eb60c4d5.js` and confirm the sha256 first;
if it has moved, the derivation does **not** apply and `derive.py` exits `2`.

## Request accounting, restated

**18 of a 18 cap**, GET only, **0** failures, **0** retries, **0** cap revisions, **2** hosts,
**6 of 6** controls first, fabricated name `zz-ar-absent-6293` at **0** `git grep` hits.

## Correction (2026-11-11) — the sub-2.5 s gap was attributed to the wrong pair

A verifier found this. The page said the single sub-2.5 s gap on clock A was `seq 9→10`; it is
`seq 11→12`, and `verify.py` has always printed the correct pair (`pairs under 2.5 s: [(2.06,
'11->12')]`). Only the prose was wrong.

`seq 11` is also the one row with an impossible negative duration (−0.477 s), which is what made
the mislabelling tempting: the corrupt row is **adjacent** to the short gap but is not one of its
endpoints. A row number and a value that sit near each other in a list are not the same claim.

**No verdict moves**: the floor (2.060 s), the gap count (16), the median (2.609 s), the max
(3.546 s) and clock B's "0 of 16 under 2.5 s" are all unchanged and all reproduce from the ledger.

⚠ **A correction to this correction.** My first pass at this section also "corrected" the median
from 2.609 to 2.621. That was wrong, and it was wrong in the exact way this repository keeps
relearning: I took `gaps[n//2]` on an even-length list instead of the mean of the two middle
values. `statistics.median` returns **2.609** — mean of 2.597 and 2.621 — and the original figure
was right. Reverted. A repair that introduces a defect in the act of fixing one is worse than the
defect, because it arrives with the authority of a correction.
