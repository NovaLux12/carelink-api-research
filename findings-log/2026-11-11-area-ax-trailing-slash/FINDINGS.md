# Area AX — is the trailing-slash sensitivity general, or specific to `/hcp`?

**Claim:** NovaLux12/carelink-api-research#211
**Date:** 2026-11-11
**Host:** `carelink.medtronic.com` **only** — one of the five hosts this repository probes, and the
only one this lane owned (three sibling lanes held the `clcloud` hosts, `carelinkhp` and the other
clinic hosts).
**Cap:** 10 requests. **Sent: 10.** One recorded revision, made before the 10th request (§1a).
**Delay:** `sleep 2.5` **inside** the per-host `flock` on `.loop/host-carelink_medtronic_com.lock`
— i.e. ≥ 2.5 s between requests to this host, measured on two clocks in §6.
**Methods:** GET only. No POST, no OPTIONS, no token, no cookie, no auth, no wordlist.

**The question, and it is one question:**

> Area AN measured that `/hcp` (bare) answers `200` + the deployment's own entry document while
> `/hcp/` (slashed) answers a real `404` (0 B, no `Content-Type`), with no `DirectorySlash` `301`
> anywhere. Area AK's `200` at `/app/` was measured **with** the slash. **Is bare `/app` the same
> handler, a different one, or an absence — and is slashed-ness a general property of this
> deployment's prefix selection, or is it `/hcp`-specific?**

---

## 0. Verdict, in one paragraph, with the labels it needs

**The sensitivity is `/hcp`-SPECIFIC. It is not a general property of this deployment's prefix
selection, and the negative is the finding.** Bare `/app` and slashed `/app/` return the
**byte-identical** entry document — `200`, 5518 B, `0f2c5f62…`, `cmp`-equal (OBSERVED, §4 rows 5/6)
— so `/app` is **one handler that is slash-insensitive**, not two surfaces and not an absence
(OBSERVED for the bytes; INFERRED for "one handler", since byte identity cannot exclude two
configurations that emit identical bytes, though nothing observed suggests two). Bare
`/hcp/configuration` and slashed `/hcp/configuration/` **also agree** — both `404`, 0 B, no
`Content-Type` (OBSERVED, rows 7/8) — so bare-ness selects nothing there either. `/hcp` remains the
**only** prefix on this host where the bare form and the slashed form disagree (OBSERVED, rows 2/9:
`/hcp` → `200` fallback, `/hcp/` → `404` from area AN, reproduced in-run at row 9), and the apex pair
`/` versus `//` is **identical** (OBSERVED, rows 3/4, `0f2c5f62…` both). **A probing client that
omits the slash therefore gets a `200` that says nothing about existence at *every* prefix measured
here — but for two different reasons**, and the difference matters: at `/app` the `200` is the real
answer (the fallback is the handler), while at `/hcp` it is not. **INFERRED, and labelled because it
is not observable by GET:** the `/hcp` asymmetry is a property of a rule keyed on the literal string
`/hcp/` (area AN §6's reading, which this pass does not extend and did not test), **not** a
deployment-wide trailing-slash convention — the three other prefixes measured here do not share it.

**One thing this pass found that no area had recorded: the `/hcp/configuration/` 405 does NOT reach
the subtree root.** `/hcp/configuration/` answers **`404`, 0 B, no `Content-Type`** (OBSERVED, row 8)
while `/hcp/configuration/<absent>` answers **`405` + `Allow: POST, OPTIONS`** in the same run
(OBSERVED, row 10). So the 405 constant area AG/AL recorded is scoped to paths **one segment below**
the subtree root, and a `404` at the prefix root is a discriminating answer (INFERRED: that scoping is
what the two cells show; the mechanism is not observable by GET).

---

## 1. Request accounting — 10 of a 10 cap, no failures, one recorded revision

| | n |
|---|---|
| **Cap, declared before the first request** | **10** |
| Requests sent in total | **10** |
| Rows in `results.jsonl` | **10** |
| Failures (`000`/5xx/timeout) | **0** |
| Retries | **0** |
| Hosts contacted | **1** — `carelink.medtronic.com`, the whole declared host set |
| Requests to any other host | **0** |

The cap was itemised **before the first request**, in `probe.sh`'s header, as
**2 controls + 2 (pair A) + 2 (pair B) + 2 (apex) + 1 (anchor) + 1 unspent = 10**.

### 1a. The recorded revision — the 10th request, declared before it was sent

The unspent request bought **one** cell: `GET /hcp/configuration/zz-ax-absent-8147`. The revision is
written into `probe.sh`'s header **before** the request, and the reason is a **defect of this
design, not a new question**: the PAIR-B slashed reference was mis-set. Area AG and area AL measured
`/hcp/configuration/<CHILD>` (`…/zz-ag-absent-8713`, `…/zz-ak-absent-4713`) — **never the prefix root
`/hcp/configuration/`** — so the slashed half of pair B had **no recorded reference at all**, and the
`405` the design quoted for it belonged to a different path shape. The cell was sent **last**, after
every pre-registered cell, so it cannot have influenced the pre-registered reading. It returned
`405` + `Allow: POST, OPTIONS` (row 10), which is the genuine AG/AL anchor, in-run, one segment under
the pair.

### 1b. A harness defect, recorded rather than back-filled

**Row 10's ledger row was reconstructed from the retained `.h`/`.b` artefacts, not written by the
harness.** The request was sent exactly once and the response was captured to disk; the inline
`python3 <<PY` that writes the ledger row then died with a nested-quote `SyntaxError` (exit non-zero,
`rows=9` printed). The artefacts were read back and the row written from them
(`harness_note` on the row says so). **What that costs:** the row's `t_sent` is reconstructed from
the `sleep 2.5` and the body's kernel mtime (12:12:23.800770239), **not** from a live harness
timestamp — so clock A's last gap is a reconstruction, and clock B (§6) is the load-bearing measurement
for that interval. **No request was repeated and no row was invented.**

---

## 2. Controls first — 2 of 2 pass, and the oracle is shown to discriminate before any pair is read

Every control was sent **before** any pair cell, and `probe.sh` **aborts** on mismatch rather than
proceeding.

| # | Control | Expected | Measured | Verdict |
|---|---|---|---|---|
| 1 | `/hcp/configuration/public/pow.crm.settings` + `X-System-ID: ProWeb` | `200` / 97 B / `370e3bba0d28…` | `200` / 97 B / `370e3bba0d28c540` | **PASS** — area AB/AK's value reproduced |
| 2 | `/hcp/zz-ax-absent-8147` | `404` / 0 B / no `Content-Type` | `404` / 0 B / `(none)` | **PASS** — area AK row 3's envelope reproduced |

**The oracle is not merely plausible — the two controls differ in status, size and
`Content-Type`, so a `200` and a `404` are distinguishable on this host in this run.** The
fabricated name is `zz-ax-absent-8147`: `git grep -c 'zz-ax-absent'` returns **0 hits** (grep exit 1)
at this head, so it is a name in no repository file, and it reuses neither area AG's
`zz-ag-absent-8713` nor area AK's `zz-ak-absent-4713`.

---

## 3. The pre-registered outcome table — written into `probe.sh` BEFORE the first cell

The full table is in `probe.sh`'s header. Its discriminating entries, and how each cell scored:

| Cell | Outcome that would have been read | Scored? |
|---|---|---|
| `/app` vs `/app/` | A1 same digest → one slash-insensitive handler **/ A2 slashed 200 + bare 404 → AN's pattern generalises / A3 bare 200 different digest → second fallback / A5 bare 200 fallback + slashed 404 → strongest generalisation | **A1** |
| `/hcp/configuration` vs `/hcp/configuration/` | B1 bare 200 + slashed 405 → bare escapes the handler, exactly as `/hcp` / B2 both 405 → slash-insensitive / B4 bare 404 + slashed 405 → third behaviour | **B6 (not pre-registered — see §3a)** |
| `/` vs `//` | X1 same digest → apex slash-count-insensitive / X2 `//` 404 → the fallback keys on a literal string too / X3 400/414 → request-line rejection, says nothing | **X1** |
| `/hcp` anchor | H1 `200` / 5518 B / `0f2c5f62…` → AN reproduces in-run | **H1** |

### 3a. The one outcome the table did not enumerate, and why that is a design defect

**PAIR B scored B6, which was not in the table** — both forms `404` with the same envelope. It was
not enumerated because the table's slashed reference was the `405` that had been measured one
segment deeper (§1a). **B6 is recorded in `probe.sh` as a post-hoc label, explicitly marked
"ADDED AFTER THE CELL"**, so a reader can see it was not a pre-registration. The reading is
unambiguous only because row 10 supplies the genuine `405` anchor **in the same run, one segment
under the same subtree**: the two `404`s are statements about the **prefix root**, not about the
subtree having gone away.

---

## 4. The matrix — 10 of 10 cells, every one a verdict

Digest is the sha256 of the decompressed body.

| # | Path | Status | `Content-Type` | Bytes | sha256 | Verdict |
|---|---|---|---|---|---|---|
| 1 | `/hcp/configuration/public/pow.crm.settings` | 200 | `application/octet-stream` | 97 | `370e3bba…` | control — PASS |
| 2 | `/hcp/zz-ax-absent-8147` | **404** | **(none)** | 0 | — | control — PASS |
| 3 | **`/`** | **200** | `text/html; charset=UTF-8` | **5518** | `0f2c5f62…` | apex anchor — entry document |
| 4 | **`//`** | **200** | `text/html; charset=UTF-8` | **5518** | `0f2c5f62…` | **X1 — apex is slash-count-INSENSITIVE** |
| 5 | **`/app`** | **200** | `text/html; charset=UTF-8` | **5518** | `0f2c5f62…` | **A1 — same handler as `/app/`** |
| 6 | **`/app/`** | **200** | `text/html; charset=UTF-8` | **5518** | `0f2c5f62…` | AK row 5 reproduced in full |
| 7 | **`/hcp/configuration`** | **404** | **(none)** | 0 | — | **B6 — bare form is NOT in the fallback** |
| 8 | **`/hcp/configuration/`** | **404** | **(none)** | 0 | — | **B6 — and the slashed root is not in the 405 handler either** |
| 9 | **`/hcp`** | **200** | `text/html; charset=UTF-8` | **5518** | `0f2c5f62…` | **H1 — area AN reproduces in-run** |
| 10 | `/hcp/configuration/zz-ax-absent-8147` | **405** | **(none)** | 0 | — `Allow: POST, OPTIONS` | **AG/AL anchor, one segment down** |

**`cmp`-confirmed byte identity, not eyeballed:** rows 3, 4, 5, 6 and 9 are **all** the digest
`0f2c5f6257a6fc6af22e4b31309264df4c148e08016c196e1048bdc19a87e32d` at 5518 B — one document,
five paths, two of them doubled-slash and one of them un-slashed.

**`0f2c5f62…` is exactly the digest area AN recorded on this host** (row 2 of AN's matrix) and
exactly area AK's `.com` `/app/` digest (AK row 5). So both anchors this pass needed reproduce
**in full**, not by prefix.

**Full digests:**

```
370e3bba0d28c540b1c347b5492fa3e8b0d4c176d53aa4fe0f4b11e65ac8cb44   control 1, 97 B
0f2c5f6257a6fc6af22e4b31309264df4c148e08016c196e1048bdc19a87e32d   rows 3/4/5/6/9, 5518 B
```

---

## 5. What the pairs mean, and what they do not

**PAIR A — `/app` vs `/app/`: slash-INSENSITIVE (OBSERVED).** Same status, same 5518 bytes, same
digest, `cmp`-equal. Under the pre-registered table this is **A1**: one handler, and the
`/hcp` sensitivity does **not** generalise to `/app`. **INFERRED:** "one handler" is the reading the
bytes support; byte identity cannot exclude two configurations emitting identical bytes, and nothing
observed suggests two, so the weaker statement that is certain is *`/app` and `/app/` are
indistinguishable to a GET*.

**PAIR B — `/hcp/configuration` vs `/hcp/configuration/`: also slash-INSENSITIVE, and both `404`
(OBSERVED).** This is **B6**, the outcome §3a describes. Two consequences, both OBSERVED:

- **The bare form does not escape into the fallback.** This is the one place a generalisation of
  AN's pattern would have shown up most clearly, and it does not: `/hcp/configuration` is a real
  `404`, not `200`. **So bare-ness is not the variable — `/hcp` is.**
- **The 405 constant is scoped BELOW the subtree root.** The prefix root `404`s (row 8) while one
  segment under it `405`s with `Allow: POST, OPTIONS` (row 10), in the same run on the same host.
  Area AL's statement that the 405 is *"a property of the handler"* is not contradicted — it is
  **narrowed**: the handler does not answer its own root. **INFERRED:** so a `404` **is**
  discriminating at this subtree's root, and any future pass reading a `404` on `/hcp/configuration/…`
  should read it as absence-one-level-deeper, not as the subtree being gone.

**APEX — `/` vs `//`: slash-count-INSENSITIVE (OBSERVED).** `--path-as-is` sent `//` to the wire as
`//`; the answer is the same `200` / 5518 B / `0f2c5f62…`. Under the table this is **X1**, and it is
consistent with area AN's finding that the `/hcp/` selector runs on the **normalised** path: Apache's
`merge_slashes` collapses the doubled leading slash before anything selects (INFERRED as to the
mechanism; OBSERVED that the two paths are indistinguishable).

**The `/hcp` anchor reproduced in-run (OBSERVED, row 9).** `200` / 5518 B / `0f2c5f62…`, exactly
area AN's cell 2 on this host. So the asymmetry this pass generalises *from* is live, on this host,
in this run — not a cross-pass recollection.

---

## 6. Spacing — two clocks, both live, neither breached

`python3 verify.py <scratch>` re-derives both. The kernel-mtime clock is **not** re-derivable from a
clean clone (git does not preserve mtimes); it is reported as a point-in-time measurement.

```
== clock A: t_sent ==
rows 10  same-host gaps 9   (expected sum(rows_per_host - 1) = 9 on ONE host)
min 2.568 s   max 81.316 s   mean 11.555 s
under the declared 2.5 s: 0
under the repository 2.0 s floor: 0
impossible durations (t_done < t_sent): 0

== clock B: kernel body mtimes (NOT re-derivable from a clone) ==
bodies stat-able 10 of 10; same-host gaps 9
min 2.799 s   max 82.053 s   mean 11.624 s
under the declared 2.5 s: 0
under the repository 2.0 s floor: 0
distinct mtimes: 10 of 10 — second clock is LIVE
```

**The gap count is checked against the population, not carried:** one host, ten rows, so
`sum(rows_per_host - 1) = 9` and both clocks report **9**. The 81 s maxima are the interval between
rows 9 and 10, which spans two tool invocations and is therefore a **pause**, not a measurement of
the harness — no gap is under either the declared 2.5 s or the repository's 2.0 s floor on either
clock. **The second clock is proven live rather than assumed: 10 distinct request-time mtimes out of
10 bodies** — which is the trap that cost area AJ its mtime oracle (all 18 bodies sharing one
mtime), and it does not apply here.

---

## 7. Verdict

**OBSERVED, 10 of 10 cells of a 10 cap, 2 of 2 controls first, 0 failures, 0 retries, no delay rule
breached on either clock:**

- **The trailing-slash sensitivity is `/hcp`-SPECIFIC.** Bare `/app` and slashed `/app/` are the
  **same** `200` / 5518 B / `0f2c5f62…` (rows 5/6, `cmp`-equal); bare and slashed
  `/hcp/configuration` are the **same** `404` / 0 B / no `Content-Type` (rows 7/8); `/` and `//` are
  the **same** `200` / 5518 B / `0f2c5f62…` (rows 3/4). `/hcp` is the **only** prefix measured here
  whose two forms disagree (row 9 `200` vs area AN's `/hcp/` `404`, which this pass did not re-buy).
- **A negative is a first-class answer and this is one.** The generalisation AX was minted to test
  **does not hold**: slashed-ness is not a deployment-wide property, so the repository's every
  recorded `/prefix/` verdict does **not** acquire an unmeasured counterpart. The rule area AN found
  is narrower than a general convention (OBSERVED for the four prefixes; **INFERRED** that the
  selector keys on the literal string `/hcp/`, which is AN §6's reading and not re-tested here).
- **The `/hcp/configuration/` 405 does not reach the subtree root** (OBSERVED, rows 8 vs 10). Area
  AL's handler-level constant is **narrowed, not contradicted**: it is a property of the handler
  one segment below the root. **INFERRED:** therefore a `404` at this subtree's prefix root is
  discriminating rather than a constant.
- **The apex survives a doubled leading slash** (OBSERVED, row 4), consistent with the
  **normalised-path** selection area AN measured under `/hcp/` (INFERRED as to `merge_slashes`).

**Not claimed:** that `/hcp`'s asymmetry holds or fails on the other three clinic hosts — this pass
bought **one** host by design, and AX's own stated assumption (that a single host establishes a
general property) is **not** satisfied by one host, which is successor **BB**. Also not claimed:
that no other prefix anywhere on this family is asymmetric — four prefixes were measured, not a
census. And no mechanism is offered for any of it: **every causal reading above is INFERRED and says
so in its sentence**, because area AN §6 established that the pipeline behind a bare-prefix `200` is
not observable by GET.

**Not a disclosure.** An SPA serving its own entry document at unmatched paths, and an API subtree
answering `404` at its root, are ordinary configuration. The finding is a **documentation** fact:
a client that omits a trailing slash cannot read existence from the status code at any prefix
measured here, and at `/hcp` specifically it reads a false positive.

## 8. Successor

Minted in `docs/11` as **BB**: *does the `/hcp`-only result hold on the other three clinic hosts —
is `/app` slash-insensitive there too, and is `/hcp` the only asymmetric prefix on each?*
**Blocker:** none — GET only, no token, no cookie, no auth, no wordlist; a budget question.
**Closes when** each of `carelink.medtronic.eu`, `carelink-support.medtronic.com` and
`carelinkhp.minimed.eu` is asked the same four pair cells beside its own two controls, and every
pair's verdict is recorded — **≤ 18 requests**. **A negative counts:** if `/hcp` is the only
asymmetric prefix on all three, this pass's `/hcp`-specific result is a property of the deployment
family rather than of one host, which is a stronger finding than this one. **Assumptions
(INFERRED):** that a second and third host behave as `carelink.medtronic.com` does, which the
`0f2c5f62…` digest's appearance on `.eu` and `carelinkhp` in area AN makes plausible and does **not**
establish; and that `carelinkhp.minimed.eu` — the documented baseline — is safe to re-probe for pair
cells, which area AL's precedent says it is (it was read, not re-probed, there).
