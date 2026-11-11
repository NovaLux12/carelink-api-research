# Area AO — is the ADR 0002 pin guard inert on any cell the bridge could be pointed at?

**Pass of 2026-11-11.** Branch `research/lao`. Hosts: **`clcloud.minimed.com` and
`clcloud.minimed.eu` only** — the two hosts the area letter names; no other host was touched.

**12 of a 12 cap**, GET only, `sleep 2.5` inside the per-host `flock`, controls first,
**0 held back, 0 unspent, 0 retries**.

Question inherited from area AH §3, which measured the `Auth0SSOConfiguration` key on eight
tails across two hosts and found it **present on `3.6` only** — absent on `3.4`, `4.0`, `4.1`,
`4.2`, `5.0` and on both fabricated controls [source:
findings-log/2026-11-10-area-ah-discovery-4x/FINDINGS.md §3]. AH stated its own scope limit:
`3.5`, `3.7`, `3.8`, `3.9`, `3.10` were **not measured**. This pass spends its whole budget
on exactly those five tails, on two hosts.

**The answer, in one line:** `3.5`, `3.7` and `3.8` **carry** the key on all three of their
`CP[]` entries on both hosts; `3.9` and `3.10` **do not** carry it on either host. So the
guard is inert-by-key-presence on three of the five tails AH left open — including `3.5`,
`3.7` and `3.8`, which are exactly the kind of cell a pin bump would land on.

---

## 1. Accounting

| item | value |
|---|---|
| Requests | **12 of a 12 cap** (0 unspent) — derivation below |
| Method | `GET` only. No POST, no OPTIONS, no token, no cookie, no auth header, no wordlist |
| Delay | `sleep 2.5` **inside** the per-host `flock`, before the send; **≥ 2.5 s between requests to the same host** |
| Spacing, ledger clock (`t0_epoch`) | `.com` floor **2.844 s** over 6 gaps; `.eu` floor **2.577 s** over 4 gaps; **0 of 10 gaps under 2.5 s** |
| Spacing, kernel body-mtime oracle | `.com` floor **2.842 s**, `.eu` floor **2.576 s**, **0 of 10 gaps under 2.5 s**; all 12 body mtimes distinct, so that oracle is **live** on this pass |
| Failures | **0** — `curl_exit: 0` on all 12 rows, `200` on all 12, no 000, no 5xx, no timeout |
| Retries | 0 |

**Gap statistic computed the way the method requires:** rows were grouped by `host` and sorted
by `seq` *before* differencing, never zipped in file order. Totals check against
`sum(rows_per_host − 1)` = (7−1) + (5−1) = **10** gaps, and 6 + 4 = 10 were computed.

**Cap derivation (one assignment, `CAP=12` in `probe.sh`):** 1 host × 2 controls = 2, +
2 hosts × 5 question tails = 10 → **12**. There is no headroom by design: the letter's budget
is ≤ 12 and the ten cells *are* the deliverable. A cell that had failed would have been
recorded **as a failure and reported as a non-answer**, not retried, because no retry cell
existed.

---

## 2. Controls — run first, both passed, question cells spent only after

| # | cell | role | status | `CP[]` len | `Auth0SSOConfiguration` |
|---|---|---|---|---|---|
| 1 | `clcloud.minimed.com` `android/3.6` | **positive** — AH §3 measured the key present | `200` | 3 | **present on 3 of 3** |
| 2 | `clcloud.minimed.com` `android/zz-ao-absent-3141` | **absent** — fabricated tail, no convention produces it | `200` | 2 | **absent on 0 of 2** |

The absent control returned `200` rather than a `403`: consistent with area AA's finding that
the tail is **echoed, not validated** [source: findings-log/2026-10-17-area-aa-appversion-axis/FINDINGS.md §4.2],
so this control is read as *does it carry the key*, not *does the host refuse it* (OBSERVED).
The positive control's three `CP[]` key sets include `Auth0SSOConfiguration`,
`UseSSOConfiguration` and `Layer7SSOConfiguration`, which AH §3 also recorded for `3.6` on
both hosts — a re-derivation of one source, not a second one.

Both controls passed in the gate that `probe.sh` applies before any question cell
(`check_controls`, exit 0 → proceed). Had either failed the pass would have stopped at
**2 of a 12 cap** and reported that, spending nothing further.

---

## 3. The ten cells (OBSERVED)

`Auth0SSOConfiguration` presence is a **key-membership test on each `CP[]` entry**, not a
substring search of the body.

| host | tail | status | bytes | `CP[]` len | regions | `Auth0SSOConfiguration` | `UseSSOConfiguration` | `baseUrlCumulus` | countries |
|---|---|---|---|---|---|---|---|---|---|
| `.com` | `3.5` | 200 | 20 256 | 3 | `US, EU, CLINICAL` | **present 3/3** | present 3/3 | `v11` ×3 | 109 |
| `.com` | `3.7` | 200 | 20 256 | 3 | `US, EU, CLINICAL` | **present 3/3** | present 3/3 | `v13` ×3 | 109 |
| `.com` | `3.8` | 200 | 20 256 | 3 | `US, EU, CLINICAL` | **present 3/3** | present 3/3 | `v13` ×3 | 109 |
| `.com` | `3.9` | 200 | 18 105 | 2 | `US, EU` | **absent 0/2** | absent 0/2 | `v2` ×2 | 99 |
| `.com` | `3.10` | 200 | 18 106 | 2 | `US, EU` | **absent 0/2** | absent 0/2 | `v2` ×2 | 99 |
| `.eu` | `3.5` | 200 | 20 256 | 3 | `US, EU, CLINICAL` | **present 3/3** | present 3/3 | `v11` ×3 | 109 |
| `.eu` | `3.7` | 200 | 20 256 | 3 | `US, EU, CLINICAL` | **present 3/3** | present 3/3 | `v13` ×3 | 109 |
| `.eu` | `3.8` | 200 | 20 256 | 3 | `US, EU, CLINICAL` | **present 3/3** | present 3/3 | `v13` ×3 | 109 |
| `.eu` | `3.9` | 200 | 18 105 | 2 | `US, EU` | **absent 0/2** | absent 0/2 | `v2` ×2 | 99 |
| `.eu` | `3.10` | 200 | 18 106 | 2 | `US, EU` | **absent 0/2** | absent 0/2 | `v2` ×2 | 99 |

**Verdict per tail, stated with the population in the sentence:** the
`Auth0SSOConfiguration` key appears on `3.5`, `3.7` and `3.8` and does **not** appear in the
`CP[]` entries of `3.9` or `3.10` — across the five tails measured on two hosts, ten cells in
total, one observation each. No such key appears on `3.9` or `3.10` in any of the ten cells
this pass read.

**Cross-host identity (OBSERVED, a `cmp` of the transient bodies).** For all five tails the
`.com` and `.eu` bodies are **byte-identical after the echoed tail is replaced with a fixed
marker**, so the ten cells are five documents seen twice. That agrees with area AA's
finding that the `3.5`/`3.6`-class documents are identical across hosts while the legacy
class is not [source: findings-log/2026-10-17-area-aa-appversion-axis/FINDINGS.md §4.2] —
⚠ but note this pass measured `.eu`, not `-trials`, so it says nothing about the
host-specificity AA measured and restates none of its 99-vs-76 country split.

**Class membership, by tail-erased body digest** (marker `<TAIL>`; computed at send time on
the transient body, no body committed, `AGENTS.md` §7):

| tail | tail-erased `sha256` (first 12) | class |
|---|---|---|
| `3.6` (control), `3.7`, `3.8` | `7850cce693d1` | one document — the current-generation one |
| `3.5` | `31b22e731f89` | one document — the `v11` one, distinct from both neighbours |
| `3.9`, `3.10`, and the absent control | `1b196aff22cd` | the **fallback** document |

That the three `v13` tails collapse to one digest and `3.9`/`3.10` collapse onto the
**fabricated-tail** digest is a re-derivation of area AE's recorded result (`3.7`, `3.8`
re-derive the `3.6` document; `3.9` onward is the legacy/fallback class) [source:
findings-log/2026-11-10-area-ae-appversion-tail/FINDINGS.md §2] — one source, not a second
independent one. ⚠ The digest *strings* here are not comparable to AH's `7ad212402d7f…` /
`7ac09335c7e4…`, which were produced with a different erasure convention; the **equality
within this pass** is what is claimed, and the class assignment agrees with AE's.

---

## 4. The finding beyond the five cells: the `??` branch never fires on any cell measured

The selector is

```js
const key = cpEntry.UseSSOConfiguration ?? 'Auth0SSOConfiguration'
```

`??` returns its right operand only when the left is `null` or `undefined`. So the fallback
is reachable on a `CP[]` entry **only where `UseSSOConfiguration` is absent while
`Auth0SSOConfiguration` is present** — and on every one of the ten cells this pass measured,
the two keys appear together or not at all. In all 12 rows (10 question + 2 controls) the
`has_UseSSOConfiguration_key` array is **element-wise equal** to
`has_Auth0SSOConfiguration_key`. Where the key is present, `UseSSOConfiguration` is present
*and its value is the literal string* `Auth0SSOConfiguration` (OBSERVED, all 9 present
entries), so the expression resolves on the left operand.

The same element-wise equality holds on **all 16 rows** of area AH's ledger, re-checked here
from that committed file [source: findings-log/2026-11-10-area-ah-discovery-4x/results.jsonl
seq 1–16] — `3.6`, `3.4`, `4.0`, `4.1`, `4.2`, `5.0`, `zz-absent-8713` and `99.99` on two hosts.

**Derived from the ledgers rather than asserted:** this pass holds 31 `CP[]` entries across
its 12 rows; area AH's ledger holds 36 across its 16, and **67 entries** is their sum. Of
those, **21 entries in this pass carry the key** (3 on `3.6`, 3 each on `3.5`/`3.7`/`3.8` on
each of two hosts) and **not one** of them is missing `UseSSOConfiguration`, nor holds any
value other than the literal string `Auth0SSOConfiguration` there.

**So the state the `??` fallback exists to handle — `UseSSOConfiguration` absent with
`Auth0SSOConfiguration` present — appears in 0 of the 67 `CP[]` entries this pass and area AH
measured between them**, over 28 observations of 27 distinct (host, tail) cells on three hosts.
**INFERRED:** that the `??` right operand is therefore dead on those cells, reasoned from the
operator's own semantics and from key membership, not from executing the client.

This is narrower than, and separate from, the inertness question. **Key presence** decides
whether `selectAuth0ConfigUrl()` can resolve *something*; the `??` branch decides *which name*
it resolves. This pass measured both, and they give different populations: the key is on
`3.5`/`3.7`/`3.8` (and `3.6`), absent on `3.9`/`3.10` (and `3.4`/4.x/`5.0`), while the
`??` **branch** is reachable on neither group.

---

## 5. What this does and does not settle — (a) and (b) kept apart

The area letter splits the question in two, and the split is the load-bearing part of the
close condition.

**(a) Key presence — ANSWERED, for the five tails that were open.** `3.5`, `3.7`, `3.8`
present; `3.9`, `3.10` absent; both hosts agree on every tail. Combined with AH, the
`Auth0SSOConfiguration` key is present on exactly **`3.5`, `3.6`, `3.7`, `3.8`** among the
14 distinct tail strings the two passes measured — 11 version tails plus `99.99`,
`zz-absent-8713` and `zz-ao-absent-3141` — and absent on `3.4`, `3.9`, `3.10`, `4.0`, `4.1`,
`4.2`, `5.0` and on all three non-version strings.

**(b) The guard's runtime behaviour — NOT ANSWERED, and this pass did not try.** Whether a
client pinned to one of these cells raises `NoAuth0SSOConfigurationError` **by name**, or
fails later at the data call, is a property of `selectAuth0ConfigUrl()`'s caller in
`carelink-bridge`. **This repository does not run that client, and no GET can observe it.**
The statement this pass supports is only: *on the cells where the key is present the selector
has a name to resolve, and on the cells where it is absent it does not.* **INFERRED:** that a
client on `3.9` or `3.10` would reach a keyless entry, which follows from key absence and the
selector's shape but was not executed anywhere.

**One sentence, as the close condition requires:** **the guard's *runtime* inertness is not
established by this pass** — key presence on `3.5`/`3.7`/`3.8` is a necessary condition for
the failure mode `docs/03` described, and it is now known to hold there, but necessity is not
sufficiency and no client was run.

**Effect on the ADR 0002 paragraph.** `docs/03`'s claim that the key *"now exists on every
version 3.4 → 5.0"* was already refuted by AH and stays refuted; this pass neither restores
nor widens it, and the 14 tails measured between the two passes are still not "every version
3.4 → 5.0". What this pass adds is the band AH withheld: the key **is** present on the three
near neighbours of the pin — `3.5`, `3.7`, `3.8` — on both hosts, so the *key-absence* half of
the failure mode cannot be what protects a bump to any of those three, whereas a bump to
`3.9` or `3.10` would land on an entry carrying no such key (OBSERVED for presence; the
consequence is INFERRED).

---

## 6. No pin added

The tempting pin (five cells × one host) would cost **5 requests on every PR gate** and 5 per
weekly sweep, to guard a **key-membership boolean** on a document whose content no suite
asserts, and it would fire on the change that does not matter (a document re-render) while
staying silent on the change that does (which tails the bridge is pointed at — a client-side
constant this repo cannot read). `docs/09` §4's rule that widening a gate is a maintainer
decision applies. The re-derivation is `probe.sh` plus this ledger, at zero future requests.

---

## 7. Bibliography of this pass's evidence

- `results.jsonl` — 12 rows, one per request, with `t0_epoch`, `t_sent`, `t_done`,
  `http_status`, `curl_exit`, `body_sha256`, and the bounded projection
  (`cp_key_sets`, key-presence booleans, `regions`, the three `baseUrl*` values, country count).
- `probe.sh` — the harness, the single `CAP=12` assignment, the two controls and the
  `check_controls` gate that must exit 0 before a question cell is spent.
- `run.log` — per-request timestamped line.

External cites used above: area AH §3 and its ledger (the question; the 16-row
co-occurrence check), area AE §2 (class assignment), area AA §4.2 (echo-not-validation and
the cross-host identity of the `3.5`/`3.6` class).
