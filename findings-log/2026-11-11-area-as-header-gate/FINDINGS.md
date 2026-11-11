# Area AS — the `412` is in front of **two live routes**, not an absent one: a `400` with a Bean-Validation body and a `401` at the `InvalidToken`/`AUTH` digest

**Claim:** [NovaLux12/carelink-api-research#210](https://github.com/NovaLux12/carelink-api-research/issues/210) ·
**Date:** 2026-11-11 · **Area:** AS · **Branch:** `research/as-header-gate`
**Host swept:** `carelinkhp.minimed.eu` — **one host**, the whole declared set. Three sibling lanes
held the `clcloud.*` hosts and the other three clinic hosts; this harness cannot address them.

Legend (`AGENTS.md` §2) — **OBSERVED** = seen in a live response · **PUBLISHED** = in a vendor
document served without a login · **INFERRED** = reasoned, not seen.

---

## The answer in one paragraph

**Both literals are live behind the gate, and neither answer is `404`.** With
`X-System-ID: ProWeb` present, `GET /hcp/patients/care-partner/search` answers **`400`, 237 B,
`application/json`** carrying a Spring Bean-Validation envelope that names
`searchCarePartners.arg0`/`arg2` as `must not be null` (OBSERVED), and
`GET /hcp/patients/otc-linking/allowed` answers **`401`, 48 B,
`{"error":{"type":"InvalidToken","group":"AUTH"}}`** at digest `247825a426460798` — the exact
48-byte envelope areas AB and O record on nine cells of a different subtree (OBSERVED). Both flip
back to **`412`, 0 B, no `Content-Type`** when the header is removed in the same run, so the flip is
attributable to the header and not to the host shifting under the sweep (OBSERVED). **The `412` is
therefore not an edge artefact in front of a non-existent route** — area AG's `Allow`-constant
failure does **not** recur here wearing a `412`, and the correction AQ's successor contemplated is
**not** owed. The `400` is the most informative cell in the pass: a validation envelope is generated
**after routing, after method resolution and past the `X-System-ID` gate, by the controller's own
argument binder**, which is a stronger liveness proof than a `200` would have been — it names the
handler's own method and its two parameter positions (OBSERVED for the bytes; **INFERRED** for the
mechanism, since no handler was read).

---

## 1. Request accounting — 10 of a 12 cap

| | n |
|---|---:|
| **Cap, declared before the first request** | **12** |
| Requests sent | **10** |
| `curl_exit` ≠ 0 | **0** |
| Rows in `results.jsonl` | **10** |
| Hosts contacted | **1** — `carelinkhp.minimed.eu`, the whole declared set |

The cap is a single assignment in `probe.sh` (`CAP=12`) and its itemisation *is* the cap:

```
1  CONTROL-1  pow.crm.settings WITH ProWeb        (expected 200, 96 B)
1  CONTROL-2  /hcp/patients/zz-as-absent-5531     (expected 404, 0 B, no Content-Type)
2  care-partner/search   {WITH ProWeb, WITHOUT}
2  otc-linking/allowed   {WITH ProWeb, WITHOUT}
1  depth-2 fabricated child, NO header
2  bare OPTIONS on each literal, NO header
1  OPTIONS on the certainly-absent child  ← spent from the 2 declared-unspent
2  declared unspent (1 remains)
--
10 issued of a 12 cap
```

**NO RECORDED CAP REVISION.** Nine cells were fixed before request 1; the tenth came out of the two
cells the itemisation had already reserved, and it was released only after the first nine showed why
it was load-bearing (§5). `verify.py` re-derives the row count and the unspent count from the ledger.

**Method:** `GET` only, plus **empty-body `OPTIONS`** (`AGENTS.md` §8 permits a preflight; area AB
set the precedent). No `POST`, no token, no cookie, no auth, no wordlist, and **no patient id — not
even a fabricated one**. The only header ever sent is `X-System-ID: ProWeb`, a **PUBLISHED,
non-secret** value already used by areas AB/AG/AK/AQ; it is not a credential, is printed in full,
and is **not** redacted. `verify.py` asserts the distinct `sent_headers` set is exactly
`{X-System-ID: ProWeb, (none)}`. `--compressed` and `--max-time 120` on every request.
`sleep 2.5` **inside** the per-host `flock` on `.loop/host-carelinkhp_minimed_eu.lock`, structure
copied from `findings-log/2026-11-10-area-ab-hcp-direct/probe.sh`.

## 2. Controls first, and both reproduce

Sent as **seq 1 and seq 2**, before any question cell, and `probe.sh` returns out of `all()` on the
first `cap_guard` failure so a question is never bought without them.

| control | expected (recorded) | OBSERVED | verdict |
|---|---|---|---|
| `GET /hcp/configuration/public/pow.crm.settings` + `X-System-ID: ProWeb` | 200, 96 B | **200, 96 B, `a977733a53ee0d5f…`, `application/octet-stream`** | reproduces area AB and AQ on this host |
| `GET /hcp/patients/zz-as-absent-5531` (no header) | 404, 0 B, no `Content-Type` | **404, 0 B, no `Content-Type`** | a header-less GET on this subtree **can** return `404` |

The second control is what makes the `412` interpretable: `404` is reachable from the identical
request shape, so a `412` on the same shape is a different answer and not the absence shape
(OBSERVED).

The fabricated names are **`zz-as-absent-5531`** and **`zz-as-depth2-5531`**.
`git grep -c 'zz-as-absent-5531\|zz-as-depth2-5531' -- .` at this head returns **0** outside this
pass's own log directory — no tracked file carried either name before the sweep.

## 3. THE PAIR — the status flips with the header, on both literals

This is the load-bearing table. Both cells of each pair are inside one run, adjacent in sequence,
2.5 s apart, same host, same method, same URL — the only difference is the header.

| # | literal | **WITH** `X-System-ID: ProWeb` | **WITHOUT** it |
|---:|---|---|---|
| seq 3 / 4 | `care-partner/search` | **`400`**, 237 B, `application/json`, `c9481609f74aa447…` | **`412`**, 0 B, no `Content-Type` |
| seq 5 / 6 | `otc-linking/allowed` | **`401`**, 48 B, `application/json`, `247825a426460798…` | **`412`**, 0 B, no `Content-Type` |

**Both re-assertions reproduce `412` exactly (OBSERVED)** — 0 bytes, no `Content-Type` — the same
shape area AQ recorded header-less on this host. So the `412` column is stable across two
independent passes and the `400`/`401` are consequences of satisfying it, not of the host changing
under the run (OBSERVED for the flip; **INFERRED** that the header alone is the sufficient cause,
because no other variable was moved).

### 3.1 What the `400` says — the body, quoted in full

```
{
  "validationErrors" : [ {
    "field" : "searchCarePartners.arg2",
    "message" : "must not be null",
    "params" : null
  }, {
    "field" : "searchCarePartners.arg0",
    "message" : "must not be null",
    "params" : null
  } ]
}
```

**`searchCarePartners` is a method name that appears in no committed file** — `git grep -c
'searchCarePartners' -- .` returns **0** at this head, and the string arrived with this response
(OBSERVED). The envelope is a Spring `MethodArgumentNotValidException`-shaped payload naming a
**handler method and two of its parameter positions** (`arg0`, `arg2`; `arg1` is not named, so the
`@Valid` parameter is not the first one). **INFERRED**, and labelled as such: that a controller ran,
bound arguments, and failed at `arg2` before reaching the body — this is the reading that explains a
`400` naming a method the client never sent, but the handler was not read and no code was
dereferenced.

**Why that matters more than a `200` would have:** a `200` would prove *a* route. This proves a route
whose handler is **typed** — it knows this request has at least three positional arguments and that
two of them are required. The `412` was gating a route the deployment actively validates
(OBSERVED for the response; **INFERRED** for the handler reading).

### 3.2 What the `401` says — AB's envelope, byte-identical, one subtree over

`{"error":{"type":"InvalidToken","group":"AUTH"}}` — **48 bytes**, sha256
`247825a426460798…`. That digest is committed **nine** times in area AB's ledger
(`/hcp/configuration/{access/config,appContext,whitelisted}` × 3 hosts, seq 9/10/14/22/23/27/35/36/40)
and again in area O's (OBSERVED, [source:
findings-log/2026-11-10-area-ab-hcp-direct/results.jsonl]). So `otc-linking/allowed` sits behind the
**same token gate**, producing the **same 48-byte AUTH envelope**, one subtree away from where that
envelope was first measured. This is a reproduction **by this repository of this repository** — one
source, so no strength word applies (`AGENTS.md` §2.1): it says the two subtrees share an envelope,
not that two producers agree.

The `401` response also carries two `Set-Cookie` headers clearing `auth_tmp_token` and
`c_token_valid_to` to empty with `Max-Age=0` — the deployment's own expiry path (OBSERVED). No cookie
was **sent**; these are `Set-Cookie` on the response.

## 4. The `412` is therefore **not** an edge artefact — AQ needs no correction

AQ's successor text named four possible outcomes and flagged `404` as *"the most interesting
possible result"*, because a `404` behind an accepted header would make the `412` an edge artefact
in front of a route that does not exist — area AG's `Allow`-constant failure wearing a different
status code.

**That is not what happened.** Neither literal answers `404`; the answers are `400` and `401`, both
with bodies, both generated above the routing layer (OBSERVED). Three consequences, each stated
against its own evidence:

1. **The `412` discriminates presence on this subtree — now in both directions.** AQ established
   this from a header-less `404` on the same host in the same run. This pass adds the other
   direction: satisfying the gate produces route-specific answers on both literals (OBSERVED).
2. **AQ's §7 sentence "what these two answer *with* the header present is unmeasured" is now
   measured**, and its `412`-column verdict — *routed, header-gated* — **stands unretracted**. No
   `## Correction` is appended to AQ's `FINDINGS.md`, because nothing in it was wrong; what it
   lacked is now supplied here and cited from docs/11.
3. **Area AG's failure shape does not generalise to this subtree's gate.** AG showed `Allow` on
   `/hcp/configuration/` is emitted identically for a path that cannot exist. Here the *gate* is in
   front of two paths that demonstrably **do** exist (OBSERVED). The two mechanisms are different
   layers, and neither bounds the other (**INFERRED**: no mechanism was read for either).

**What is NOT established, and is the one thing that would change the picture:** that these are
*the same* handler generation as the routes AQ probed `405` on. The `405` routes advertise
`Allow: POST, OPTIONS`; these two advertise `Allow: HEAD, GET, OPTIONS` on `OPTIONS` (§5) and accept
a `GET` far enough to validate arguments. So `care-partner/search` and `otc-linking/allowed` are
**`GET`-capable routes**, unlike the other seventeen — which means AQ's uniform `405 + Allow: POST,
OPTIONS` column and these two were never the same handler class, and reading the `412` as "the same
routes, one gate earlier" would be wrong.

## 5. The `OPTIONS` column, and the control that keeps it honest

Both literals answered an empty-body, **header-less** `OPTIONS` with **`200`, 18 B,
`Allow: HEAD, GET, OPTIONS`**, and **one** body digest `0f06a4c8d34690d4…` (OBSERVED). Two facts
follow, and the second is the reason the tenth request was spent:

- The gate **does not precede method resolution** on these two: a header-less request for a method
  they *do* register is answered `200`, while the same header-less request for `GET` is `412`
  (OBSERVED). **INFERRED**: the `412` is keyed on `GET` reaching the gated handler, not on the path
  alone — but only two methods were tried, so this is a two-point observation, not a rule.
- **`Allow: HEAD, GET, OPTIONS`** is a *different* value from the `Allow: POST, OPTIONS` that all 17
  `405` routes in area AQ carry — so `Allow` here **varies per route**, unlike area AG's
  `/hcp/configuration/` constant (OBSERVED).

**The control (seq 10):** the certainly-absent child answered `OPTIONS` **`404`, 0 B, no
`Allow`** (OBSERVED). So the `200 + Allow` is **not** a subtree constant: a route that does not
exist does not produce it, and the OPTIONS column is therefore evidence here rather than noise. This
is exactly the control area AP had to buy on `clcloud-trials` for the `403` line, and it lands the
other way: on this subtree `OPTIONS` resolves **per route** (OBSERVED), as `docs/09` §2's
`GET 405/412 + OPTIONS 200 → live, non-GET-registered` rule presupposes.

**A trap this does NOT fall into:** the `OPTIONS 200` and the `GET 400/401` are on *different*
headers and *different* methods. Reading `OPTIONS 200` as "the route is public" or `GET 400` as "the
route is broken" both invert the evidence. The only reading the cells support is: the path is routed,
the handler is `GET`-capable, the `GET` is behind `X-System-ID`, and one of the two is also behind a
token (OBSERVED).

## 6. The absence shape, at both depths

| cell | OBSERVED |
|---|---|
| `GET /hcp/patients/zz-as-absent-5531` (depth 1, no header) | **`404`, 0 B, no `Content-Type`** |
| `GET /hcp/patients/zz-as-absent-5531/zz-as-depth2-5531` (depth 2, no header) | **`404`, 0 B, no `Content-Type`** |
| `OPTIONS /hcp/patients/zz-as-absent-5531` (no header) | **`404`, 0 B, no `Allow`** |

So a fabricated name one and two segments below `/hcp/patients/` answers the absence shape on both
methods, which is what makes a `412` at those depths a **presence** answer rather than a depth
artefact (OBSERVED). AQ measured the depth-1 `GET` on 4 of 4 hosts; the depth-2 `GET` and both
`OPTIONS` cells are new here and are this host only.

## 7. Headers

| header | value | cells |
|---|---|---|
| `Server` | `Apache/2.4.62 (Red Hat Enterprise Linux) OpenSSL/3.5.5` | 10 of 10 |
| `access-control-allow-headers` | `X-System-ID, Content-Type, authorization` | 10 of 10, one value |
| `access-control-allow-methods` | (absent) | 10 of 10 |
| `access-control-allow-origin` | (absent) | 10 of 10 |
| `Allow` | only on the two `OPTIONS 200`s: `HEAD, GET, OPTIONS` | 2 of 10 |
| `x-cache` | `Error from cloudfront` on the two gated `GET`s | 2 of 2 |
| `via` | one CloudFront POP (`LHR5-P7`) | 10 of 10 |

`ACAM` and `ACAO` absent on every row repeats areas AB/AG/AQ on this family, so `Allow` is the only
method signal available here (OBSERVED). The `x-cache: Error from cloudfront` on both gated `GET`s
and on neither `OPTIONS` is recorded and **not interpreted** — two cells, no control for it, and
CloudFront emits it for a range of origin responses.

## 8. Delay accounting — two clocks, both live, no rule breached

Both clocks are published; `python3 verify.py` re-derives each at zero requests.

```
clock A — t_sent (re-derivable from results.jsonl)
  gaps 9   min 2.455 s   median 2.622 s   max 37.963 s
  under 2.5 s : seq 7->8 (2.455 s)
  under 2.0 s : none
  impossible negative DURATIONS (t_done < t_sent): none

clock B — kernel body mtimes (NOT re-derivable from a clean clone)
  bodies stat-able 10 of 10,  10 DISTINCT values
  gaps 9   min 2.589 s   max 37.991 s
  under 2.5 s : none        FLOOR ON THIS CLOCK: 2.589 s
  each mtime inside its own [t_sent, t_done] window: 9 of 10
```

**Clock B is proved to be a live second clock, not one repeated value** — all ten mtimes are
distinct, which is the check area AJ's harness failed (all 18 of its bodies shared one mtime, 43 ms
apart, and the mtime oracle was dead there). Nine of the ten fall strictly inside their own request
window; the tenth is `seq 7`, **85 ms before its own `t_sent`**, and it is published rather than
dropped because suppressing it would be the exact defect `docs/09` §4 records.

**The one sub-2.5 s reading is clock A only: `seq 7→8`, 2.455 s (OBSERVED).** Clock B over the same
row reads **2.589 s** — above the rule. This harness has **no corrupt-`t0` row** to blame (zero
negative durations), so the two clocks disagree on a clean series, and the honest statement is the
one the repo's rule already supports: **the sleep is `2.5` and the observed same-host floor is
2.455 s on the `t_sent` clock and 2.589 s on the kernel clock; no delay rule is claimed breached and
no clean `t_sent` floor is claimed either.** The 2.455 s gap sits exactly at the boundary of
`date`-call overhead around a `sleep 2.5`, and calling it a breach would overstate 45 ms of
scheduler jitter as a methodological failure (**INFERRED**).

The 37.96 s max is the deliberate between-batch pause: the nine-cell batch completed, the reserve
cell was released, and `probe.sh reserve` was invoked separately. It is a between-batches gap, not a
within-batch spacing defect (OBSERVED from the two commands' timestamps).

**Gap count checked against the row count, not carried:** one host, 10 rows →
`sum(rows_per_host − 1) = 9` = the published gap count of 9. `verify.py` prints both and asserts
equality.

## 9. What this does not establish

- **Nothing about any patient.** No token, no cookie, no auth, no patient id — fabricated or
  otherwise. A `400` naming `arg2` and a `401` clearing a cookie are statements about the edge and
  the argument binder; **not one byte of a patient record was read**, and no search was executed.
- **Not the other three clinic hosts, and not the `clcloud.*` hosts.** One host, deliberately —
  sibling lanes held the rest. Whether `care-partner/search` answers `400` on
  `carelink.medtronic.com` is **unmeasured** (successor **AY**).
- **Not a `POST`, and so not the routes' accepted method.** `Allow: HEAD, GET, OPTIONS` is what the
  deployment advertises to an `OPTIONS`; area AG established that `Allow` is not a method register in
  general. What is established is that it is **not a constant** here (§5) and that `GET` reaches the
  handler (§3).
- **Not the `400`'s validator or the `401`'s authorizer by mechanism.** Both readings are
  **INFERRED**; no handler, filter or configuration was read.
- **Not a disclosure.** Every cell is an unauthenticated `GET` or an empty-body `OPTIONS` against a
  public host, and every byte quoted is an error envelope the deployment serves to any anonymous
  caller who sends the one published header.
