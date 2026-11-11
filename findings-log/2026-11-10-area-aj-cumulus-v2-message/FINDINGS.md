# Area AJ — does the cumulus-v2 base carry a `display/message` route at all? (2026-11-10)

Closes `docs/11-suggested-research-areas.md` area AJ. Claim: issue #182.

## 0. The question, and why it was open

Area C tested `pde/v{1,2,3}/display/message` and `csr/v{1,3}/display/message` — dead —
and the **v13** track's `carepartner/v13/display/message` — live, `401`. It never tested
the **v2** track's own message leaf. The cumulus-v2 spike names
`/connect/carepartner/v2` as the v2 `baseUrlCumulus` and
`GET {baseUrlCumulus}/display/message` as *the* message endpoint
[source: findings-log/cumulus-v2-spike.md] — while every recorded probe of
`display/message` had been against `v13`. In the whole committed corpus this leaf had
been requested **once**: `VERSION-AXIS.md` row 42, `.eu`, `GET` only, `403`
[source: findings-log/probe-2026-10-08/recon/VERSION-AXIS.md:156], and
`findings-log/2026-10-12-area-y-three-host-audit/host-coverage.txt:53` records that
`N=1`. **No `OPTIONS` on this leaf exists anywhere in this repository.** A `GET`-only
`403` on this host family is the no-route error, so the leaf's method axis had never
been measured — and under `docs/09` Oracle A a `GET 403` alone cannot distinguish
"absent" from "registered with a non-`GET` method".

The Instinct angle: US Instinct users report login works and data download fails; the
theory under test is that Instinct rides a cumulus-v2 transport. If the Instinct data
plane is at v2, this leaf is its front door.

## 1. Method

- **Hosts:** `clcloud.minimed.com`, `clcloud-trials.minimed.com`, `clcloud.minimed.eu` —
  the three recorded cumulus hosts, and no other.
- **18 requests, 6 cells × 3 hosts. 18 of a 18 cap.** `GET` plus **empty-body
  `OPTIONS`** only (`--request OPTIONS`, no `-d`, which is the flag that silently
  converts a "GET with body" into a POST — `docs/09` §4). No `POST`, no
  `Authorization`, no `Cookie`, no `x-api-key`, no `X-System-ID`, no token exchange, no
  wordlist, no DNS, no port scan, no dev/stage host.
- **`sleep 2.5` INSIDE the per-host `flock`** — the harness holds
  `flock` on `$REPO/.loop/host-<host>.lock`, sleeps, then sends, then releases, so the
  spacing is a property of the lock and not of the shell's timing. **Delay ≥2.5 s
  between requests to the same host.** Copied structurally
  from `findings-log/2026-11-10-area-ab-hcp-direct/probe.sh`.
- **Controls first on every host, and the absent control is a GATE, not a datapoint.**
  `probe.sh` compares the absent control's status, byte count **and** digest against
  the oracle before it issues any question cell, and aborts the sweep with exit 9 if
  they do not match. The gate fired green on all three hosts (§2), so no verdict below
  is being read against a moved oracle.
- **Candidate justification** (bounded, derived, no fuzzing):
  - `connect/carepartner/v2/display/message` — `baseUrlCumulus` + `/display/message`,
    both halves published (§0), never probed together.
  - `connect/carepartner/v2/discover/android/3.6` — the **nearby cell**. It is the one
    leaf under the same `/v2` base that is recorded as *served* on any host
    (`-trials`: `200`, 10 053 B, `sha256 1aab9bb1e721…`,
    [source: findings-log/2026-10-17-discover-3host-matrix/FINDINGS.md:143,347]). It
    costs two of the eighteen and it is what makes the result interpretable: without
    it, a no-route on the message leaf could be explained away as "the whole `/v2`
    base is unrouted on this host". With it, that explanation is excluded per host.

## 2. Controls (OBSERVED)

| # | host | method | path | status | `x-amzn-errortype` | `x-ca-err` | bytes | sha256 |
|---|---|---|---|---|---|---|---|---|
| 1 | `.com` | GET | `connect/carepartner/v13/display/message` | **401** | `UnauthorizedException` | **990** | 36 | `d551247201fc8fc2…` |
| 7 | `-trials` | GET | same | **401** | `UnauthorizedException` | **990** | 36 | `d551247201fc8fc2…` |
| 13 | `.eu` | GET | same | **401** | `UnauthorizedException` | **990** | 36 | `d551247201fc8fc2…` |
| 2 | `.com` | GET | `connect/carepartner/v2/zz-aj-absent-8713` | **403** | `MissingAuthenticationTokenException` | — | **42** | **`f249b63cb2fcb66b47e86f906c98f8fd912e82dd035b4e53d7e72fc1960cfd16`** |
| 8 | `-trials` | GET | same | **403** | `MissingAuthenticationTokenException` | — | **42** | **same** |
| 14 | `.eu` | GET | same | **403** | `MissingAuthenticationTokenException` | — | **42** | **same** |

**Both controls reproduce on all three hosts.** The live control is `401` +
`x-ca-err: 990` — the request reached Medtronic's Layer7 authorizer, so the host still
routes a carepartner `display/message` leaf and the authorizer answers. The absent
control is `403` at the full 42 B digest, byte-identical on all three hosts, which is
the **"no route"** signal defined at `docs/09` §2. Per the brief: had this digest not
reproduced, the run would have been void.

**The live/absent pair is the whole oracle here, and the direction matters:** 403 with
`MissingAuthenticationTokenException` at `f249b63cb2fc…` is a **NEGATIVE — the path does
not exist.** It is *not* a live auth-gated route. `401` + `x-ca-err: 990` is the
positive. Every verdict in §3 is read through that pair.

## 3. Results — the full 18-cell matrix (OBSERVED)

Verdict rule, `docs/09` §2: `GET 403 + OPTIONS 403` → dead on every tested method;
`GET 403 + OPTIONS 200` → live, registered with a non-`GET` method (POST-only
signature); `GET 401` → live with `GET`.

| # | host | method | path | status | `x-amzn-errortype` | bytes | CORS (`ACAO` / `ACAM`) | verdict |
|---|---|---|---|---|---|---|---|---|
| 3 | `.com` | GET | `v2/display/message` | 403 | MissingAuthToken | 42 `f249b63c…` | — | no `GET` route |
| 4 | `.com` | OPTIONS | `v2/display/message` | 403 | MissingAuthToken | 42 `f249b63c…` | — | **dead** |
| 5 | `.com` | GET | `v2/discover/android/3.6` | 403 | MissingAuthToken | 42 `f249b63c…` | — | no `GET` route |
| 6 | `.com` | OPTIONS | `v2/discover/android/3.6` | 403 | MissingAuthToken | 42 `f249b63c…` | — | **dead** |
| 9 | `-trials` | GET | `v2/display/message` | 403 | MissingAuthToken | 42 `f249b63c…` | — | no `GET` route |
| **10** | **`-trials`** | **OPTIONS** | **`v2/display/message`** | **200** | *(absent)* | **0** | **`*` / `OPTIONS`** | **LIVE — non-`GET` method registered** |
| **11** | **`-trials`** | **GET** | **`v2/discover/android/3.6`** | **200** | *(absent)* | **10 053** `1aab9bb1e721…` | absent | **live, public** |
| 12 | `-trials` | OPTIONS | `v2/discover/android/3.6` | 403 | MissingAuthToken | 42 `f249b63c…` | — | no `OPTIONS` route |
| 15 | `.eu` | GET | `v2/display/message` | 403 | MissingAuthToken | 42 `f249b63c…` | — | no `GET` route |
| 16 | `.eu` | OPTIONS | `v2/display/message` | 403 | MissingAuthToken | 42 `f249b63c…` | — | **dead** |
| 17 | `.eu` | GET | `v2/discover/android/3.6` | 403 | MissingAuthToken | 42 `f249b63c…` | — | no `GET` route |
| 18 | `.eu` | OPTIONS | `v2/discover/android/3.6` | 403 | MissingAuthToken | 42 `f249b63c…` | — | **dead** |

All thirteen `403`s carry **one** digest, `f249b63cb2fcb66b47e86f906c98f8fd912e82dd035b4e53d7e72fc1960cfd16`,
42 B — the absent control, the six candidate cells on `.com`/`.eu` and the two
`-trials` no-route cells alike. **Evidence class: OBSERVED** — `results.jsonl` rows 1–18,
`headers/*.hdr` + `headers/*.body`, `run.log`.

The `-trials` `200` at seq 10 is, verbatim: `HTTP/2 200`, `content-type: application/json`,
`content-length: 0`, `access-control-allow-origin: *`,
`access-control-allow-methods: OPTIONS`,
`access-control-allow-headers: Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token`,
`x-cache: Miss from cloudfront`. The `-trials` `200` at seq 11 is
`application/json;charset=utf-8`, 10 053 B, brotli, `x-cum-signature` present,
`cache-control: no-cache, no-store` — a discovery document, and its digest
**reproduces the recorded `1aab9bb1e721…` exactly** (re-derivation of one recorded
value; [source: findings-log/2026-10-17-discover-3host-matrix/FINDINGS.md:143]).

## 4. Verdict

**The answer is not one number. The v2 track's message leaf is routed on exactly one of
the three cumulus hosts, and it is not either US/EU patient host.**

- **`clcloud.minimed.com` — no route on any tested method.** `GET` 403 and `OPTIONS`
  403, both at the no-route digest, byte-identical to a fabricated sibling. The v2 leaf
  the spike names does **not** exist on the US patient host (OBSERVED, seq 3–4).
- **`clcloud.minimed.eu` — no route on any tested method.** Same two cells, same digest
  (OBSERVED, seq 15–16). This reproduces the single prior observation on this leaf
  (`VERSION-AXIS.md` row 42, `GET` 403) and adds the method axis it lacked.
- **`clcloud-trials.minimed.com` — `GET` is not routed, `OPTIONS` is.** `GET` 403 at
  the no-route digest; `OPTIONS` `200`, 0 B, `ACAO: *`, `ACAM: OPTIONS`. Under
  `docs/09` §2's rule this is **the signature of a route registered with a non-`GET`
  method — POST-only** (OBSERVED cells, seq 9–10; the POST reading is INFERRED, see
  §6).

**So "the v2 track has no `display/message` route" is FALSE as a global claim, and
"the v2 track's data plane is at `/connect/carepartner/v2/display/message`" is FALSE on
both patient hosts.** Two of three hosts are a clean negative; one host is a partial
positive of exactly the shape that found `csr/v2` and bare `connect/v2` in area C.

**The nearby cell is what makes the `-trials` result mean something, and the two
`-trials` asymmetries point in opposite directions.** On the same host, in the same run,
under the same `/connect/carepartner/v2` prefix:

| `-trials` cell | `GET` | `OPTIONS` |
|---|---|---|
| `v2/discover/android/3.6` | **200**, 10 053 B | **403** no route |
| `v2/display/message` | **403** no route | **200**, `ACAO: *` |

`OPTIONS` therefore is **not** blanket-`200` under this prefix on this host — if it
were, seq 12 would have returned `200` too. The `200` at seq 10 is **path-specific**
(INFERRED from those two OBSERVED cells; the assumption is that the gateway's
`OPTIONS` handling is resolved per route, which `docs/09` §2's `OPTIONS 200 → live`
rule already presupposes). That is the strongest reading available without a
fabricated-path `OPTIONS` control, which this pass did not buy — §6 states that gap
rather than papering over it.

**For the Instinct theory, this is a negative that narrows the search rather than
closing it.** The `baseUrlCumulus` the vendor publishes for a US patient account is
`https://clcloud.minimed.com/connect/carepartner/v2` (PUBLISHED — the 3.9-class legacy
discovery document, `baseUrlCumulus` extracted offline from
`findings-log/2026-10-17-area-aa-appversion-axis/headers/02-clcloud.minimed.com-v11-android-3.6.b`
and `…/05-clcloud.minimed.com-v13-android-3.9.b`), and **that base has no
`display/message` route on that host**. The only host where the v2 message leaf is
routed is `-trials`, where the v2 base is *also* the one still serving discovery
(seq 11). **INFERRED:** the v2 message plane is live only where the v2 track is itself
still served, which reads as a legacy track retained on the trials deployment rather
than as the Instinct data plane arriving on v2. The assumption is that route
registration tracks deployment configuration rather than being independent per leaf;
nothing here observes a vendor decision.

## 5. What the published documents say, and the one contradiction worth recording

The spike's row reads *"Display/messages · `GET {baseUrlCumulus}/display/message` ·
ondrej1024 carelink_client2.py:221"* [source: findings-log/cumulus-v2-spike.md:27].
The cited source, at its current head, says the opposite about the method:

```
carelink_client2.py:41  # [3] GET data (providing username, role, patientId) from "baseUrlCumulus"
carelink_client2.py:42  # POST /connect/carepartner/v11/display/message
carelink_client2.py:221      url = config["baseUrlCumulus"] + "/display/message"
carelink_client2.py:238      resp = requests.post(url=url,headers=headers,data=json.dumps(data))
```

(SOURCE-PUBLISHED — fetched 2026-11-10 from
`raw.githubusercontent.com/ondrej1024/carelink-python-client/main/carelink_client2.py`,
repo head `29051ca`, 2026-07-07. This is third-party client code, **not** a statement
about vendor behaviour, and it is not promoted to OBSERVED.)

So the spike's `GET` is **the spike's error, not the client's**: that client `POST`s, its
own header comment says `POST`, and its worked example is the `v11` base. The spike's
own table is also the only place in this repo where this leaf is attributed a `GET`
method, and the live cells do not support it on any host (`GET` is 403 everywhere).
**This does not change the pass's verdict** — the cells were probed on both methods, so a
wrong `GET` in the spike could not have hidden a route — but a reader following the spike
to build an integration would send `GET` to a leaf that has no `GET` route on **any**
host, and would read the 403 as an auth problem. Correcting the method in the spike's
row is recorded here rather than edited into that file (`findings-log/` is append-only).

## 6. Limits — what this does NOT prove

1. **The `OPTIONS`-on-a-certainly-absent-path control was not run inside this subtree.**
   Area C ran one, but on a different base path (`OPTIONS connect/carepartner/v13/3f8a1c2e-…`
   → 403, no CORS) and a different host (`.eu`) — [source: findings-log/2026-10-11-pde-csr-oracle/FINDINGS.md:42].
   The in-run substitute is the `-trials` pair in §4: `OPTIONS` 403 on a *sibling* leaf
   one path-family away, which excludes a subtree-wide blanket `200`. That is weaker
   than a fabricated-path control and it is the first job of successor **AM**.
2. **"POST-only" means "registered with a non-`GET` method, almost certainly POST".**
   It does not mean "POST returns data". `docs/09` §2 and area N both warn that
   `access-control-allow-methods` is **not** a register of a route's methods — seq 10
   advertises `ACAM: OPTIONS` on a leaf whose `GET` is unrouted, which is the same
   header shape `carepartner/v13/display/message` carries while being GET-capable
   [source: findings-log/2026-10-12-csr-cross-host/FINDINGS.md]. So the POST half rests
   on `GET` 403 + `OPTIONS` 200 agreeing with the method inference, **not** on the
   header. The body behind it is token-gated and unobserved.
3. **No route existence beyond the two methods tested.** A method other than `GET` and
   `OPTIONS` (a `PUT`, a `DELETE`) is untested by construction — `AGENTS.md` §8 and §11
   forbid it, and it would not change the answer anyone needs.
4. **One day, one run.** The `-trials` 200 was seen once. It is not pinned (§7) and no
   second observation exists.
5. **`v2` is a substring shared with `csr/v2`.** `connect/v2/display/message` (bare,
   pre-`carepartner`) is a **different** leaf, recorded live POST-only on all three
   hosts by areas C and N. Nothing here re-probes or contradicts that; the two must not
   be conflated in any later citation.

## 7. Pinning — deliberately not done

The tempting pin is `GET connect/carepartner/v2/display/message → 403` at the no-route
digest, on the two patient hosts. **Not added**, for a reason that is about this repo's
own budget rather than about the claim: `clcloud.*` hosts cost two requests per cell per
PR gate **and** per weekly drift sweep, and the change that matters for the Instinct
question — the `-trials` `OPTIONS` 200 appearing or disappearing — is on a host whose
drift would not fail a `GET`-403 pin on `.com`/`.eu` at all. A pin that cannot fire on
the finding it accompanies is the one-directional pin defect area N's §3 recorded; it
should not be repeated here. Recorded as a decision, not an omission.

## 8. Requests and spacing

**18 of a 18 cap**, zero unspent, zero failures (`curl_exit: 0` on all 18), zero
retries. `GET` + empty-body `OPTIONS` only, no `POST`, no token, no cookie, no auth
header of any kind.

⚠ **Corrected 2026-11-10 after verification: the kernel-mtime oracle is DEAD on this
pass, and the figure originally published here (2.611 s floor, 0 under 2.5 s) was an
artefact of it.**

The `t_sent` series reads **2.022 s floor over 15 gaps, 1 gap under 2.5 s, and 1
negative duration** (`seq 14`, `.eu`, `t_done - t_sent = -0.531 s`) — the known
corrupt-`t0` signature recorded in five prior passes, and no cause is asserted.

The mtime cross-check that earlier passes used to rescue such a series **cannot be
applied here**, and the reason is mechanical: every committed body file carries the
**same** mtime (`1794355484.4125…`, a 43 ms spread across all 18), because they were
written by the same checkout/copy step rather than by curl at request time. A series
whose spread is 43 ms cannot measure a 2.5 s spacing rule. **So this pass has one
clock, not two, and that clock contains a negative duration and a sub-floor gap.**

What is claimed: the delay was slept inside the per-host `flock` as declared. What is
**not** claimed: a clean spacing floor. `1.894 s`-class readings on a series that also
reports an impossible negative are exactly what `docs/09` §4 says to publish rather
than reconcile.
