# Area J (addendum) — the three advertised Auth0 endpoints by OPTIONS (2026-10-13)

Claim issue **#34**. Addendum scope ONLY: the three advertised siblings of
`registration_endpoint`, by empty-body OPTIONS. The parent half of J (bridge
`login-errors.ts` taxonomy vs the live error surface) is out of scope and is
carried as the successor in `docs/10-open-questions.md` §1.

**23 of a 26 cap, GET and OPTIONS only, no POST anywhere.** 20 curl requests
(5 controls + 15 candidates) + 3 live hurl pin-validations. One further hurl
invocation failed parsing locally and opened no socket — zero surviving rows,
not counted (§5). Millisecond ledger timestamps throughout
(`date -u +%FT%T.%3NZ`); the spacing floor is measured from `t_sent` gaps per
host, not from rounded readings.

Declared delay **2.5 s between requests to the same host**, enforced as a
`sleep` *inside* the per-host `flock` in `probe.sh` and around each hurl
validation — outside the lock, three concurrent pool workers would fire
simultaneously on one host. `--compressed` on every curl request.

A GET sweep of these three paths would report "absent" on every tenant and be
wrong at least once: all three are POST-only by OAuth/OIDC specification
(`bc-authorize` takes an `auth_req_id`; `mfa/challenge` takes an MFA token;
`global-token-revocation` takes a connection name), and area I proved a GET-only
sweep cannot see a POST-only route. The method sent here is OPTIONS on all 20
curl rows; `Access-Control-Request-Method: POST` is a preflight *declaration*
of what a browser would send, not a POST, and no request body was sent.

**Measured spacing floor: 2.395 s from `t_sent`**, over 15 same-host curl gaps
plus 2 hurl-validation gaps — all 17 ≥ the repo's 2 s floor, 2 of the 15 curl
gaps under the declared 2.5 s (2.403 s on `minimed.eu`, 2.395 s on
`medtronic.eu`), and the second hurl gap at 2.455 s. Four rows carry NEGATIVE
durations (`t_done` earlier than `t_sent`: seq 7, 13, 18 curl and seq 22 hurl),
which is impossible, so those timestamps cannot all be faithful. Both short
curl gaps sit adjacent to a negative-duration row on the same host, which is
consistent with a corrupt `t_sent` rather than a short sleep — but that is an
INFERRED reading, and per `docs/09` §4 no cause is asserted. Recorded rather
than smoothed over; this is the sixth pass to record the class. No gap below
the floor on any host, on any reading.

## 1. Candidate list — closed and justified, no wordlist

Every path is named *inside* a discovery document this repo already holds
(`findings-log/2026-10-12-area-i-auth0-tenant-behaviour/openid/*-openid-configuration.json`,
all five tenants, identical templates):

| Probed path | Discovery key | Concretisation |
|---|---|---|
| `/bc-authorize` | `backchannel_authentication_endpoint` | exact |
| `/mfa/challenge` | `mfa_challenge_endpoint` | exact |
| `/oauth/global-token-revocation/connection/Auth0` | `global_token_revocation_endpoint` (`…/connection/{connectionName}`) | `Auth0` — the name already recorded in `docs/02-auth-tenants-and-flows.md:137` and pinned by `regression/hurl/04-deep-surface.hurl` |

Five tenants: `carelink-login-trials.minimed.com`, `carelink-login.minimed.eu`,
`carelink-login.minimed.com`, `carelink-login.medtronic.eu`,
`carelink-login.medtronic.com`. Per tenant: control first, then the three
candidates. The `{connectionName}` template means another connection name
could route where `Auth0` does not — the revocation verdict covers only the
probed name, and says so (§2).

## 2. Verdicts — one per path × tenant, on headers, never on status

| Path | All five tenants | Discriminator (OBSERVED) |
|---|---|---|
| `/bc-authorize` | **UNROUTED everywhere** | 404 `text/plain` 10 B + `x-auth0-not-found: 1`, body byte-identical to the same host's control: all 15 ten-byte bodies share one full digest `0802559db1375af3…` (5 controls + 5 `/bc-authorize` + 5 revocation; seq 1–2, 4–6, 8–10, 12–14, 16–18, 20). The advertised `backchannel_authentication_endpoint` is dangling on every tenant. |
| `/mfa/challenge` | **ROUTED everywhere** | 204, 0 B, `access-control-allow-origin: *`, `access-control-allow-methods: GET, PUT, POST, DELETE, PATCH, OPTIONS` — identical on all five (seq 3, 7, 11, 15, 19), empty-body digest `e3b0c44298fc…` × 5. The advertisement is honoured at the routing layer on every tenant, shadow tenants included. |
| `/oauth/global-token-revocation/connection/Auth0` | **UNROUTED everywhere (for this connection name)** | Same unrouted signature and the same shared digest as the controls (seq 4, 8, 12, 16, 20). Confirms the existing GET 404 pin rather than contradicting it. |

Three things these verdicts are NOT:

- `/mfa/challenge` is **not** established as POST-only. The preflight answers
  204 with a six-method allow-list — unlike `/oidc/register`'s bare `POST`
  (area I §3). That it takes an MFA token by POST is INFERRED from the OAuth
  specification, on the assumption Auth0 implements the standard
  `mfa/challenge` contract; no POST was sent, so no method claim beyond
  "routed" is OBSERVED. Per `docs/09` §4, `allow-methods` is CORS
  configuration, not a method register — and this six-method list on a
  challenge endpoint is a second live instance of why.
- The revocation negative covers **only** the `Auth0` connection name. A tenant
  whose connection is named otherwise would answer a different path, which was
  not probed and is not claimed about.
- No shadow-tenant split was found here, unlike `/oidc/register` (3 × 204 vs
  2 × CORS-refused). All three paths answer identically across the
  patient/shadow line — `/mfa/challenge` routed on all five, the other two
  unrouted on all five. The per-host controls are what make "identically" a
  finding rather than an assumption.

## 3. Controls, and what each one proved

| # | seq | Request | Result | What it proved |
|---|---|---|---|---|
| C1–C5 | 1, 5, 9, 13, 17 | `/bc-authorizex` (OPTIONS, same preflight headers) on each of the five tenants, sent *first* on its host | 404 `text/plain` 10 B, `x-auth0-not-found: 1`, one digest `0802559db137…` across all five | The front door marks an unrouted path identically on every tenant, and each tenant's mark was established before that tenant's candidates were read. A routed verdict is therefore falsifiable per host rather than assumed. |
| V1–V3 | 21–23 | the three committed hurl pins, run live via `hurl 8.0.1 --test` (a different client from the curl probe) | exit 0 × 3 | The pin text committed to `regression/hurl/02-sso-oidc.hurl` holds on the wire, not just in the ledger. Ledger rows carry status + timestamps; bodies/headers were not re-captured by hurl and the rows say so rather than carrying values from the curl cells. |

All five curl controls passed. **No stop condition fired.** The `Origin` sent
(`https://example.invalid`) is a fixed non-routable placeholder, so no
preflight can look like a real referrer.

## 4. Every negative result, stated

- `/bc-authorize` unrouted on **all five** tenants — byte-identical to each
  host's certainly-absent control (§2). The strongest negative in this pass:
  candidate == control, not merely "also 404".
- `/oauth/global-token-revocation/connection/Auth0` unrouted on **all five**
  tenants, same byte-identity. Scoped to the `Auth0` name (§2).
- `x-auth0-not-found` appears on 15 of 20 curl responses and on **no** routed
  cell — the oracle holds for a second pass running.
- No `access-control-*` header on any of the 15 unrouted cells; `ACAO: *` on
  all 5 routed cells.
- `docs/02` §1's lumped claim — "`/bc-authorize`, `/oidc/register`,
  `/oauth/global-token-revocation/connection/Auth0` — all advertised, all 404,
  absent" — is now wrong in the interesting direction for one of the three:
  `/mfa/challenge` was never in that sentence (it sat two lines below as
  "Unknown — no probe result in any source") and it is **routed**, while the
  other two are confirmed unrouted by the correct method. `docs/02` is
  corrected in place with this paragraph cited, not silently rewritten.

## 5. Discipline notes — two harness defects, both caught before the push

- **The ledger writer interpolated a header block into a Python string
  literal.** Every captured `ctype_full` contains `etag: W/"…"` — the double
  quote ended the literal, so all 20 rows threw `SyntaxError` and
  `results.jsonl` was never written, while `run.log`, `headers/` and `bodies/`
  were complete. The run's vendor traffic (20 requests, all inside the cap)
  was valid; only the ledger assembly was broken. Fixed by passing
  `ctype_full` via a file and every other field via `argv`
  (`probe.sh`, commented at the fix), then rebuilding `results.jsonl` OFFLINE
  from `run.log` + `headers/` + `bodies/` + `ts/` with a script that asserts
  each row's status, byte count and sha256 against the captured files — zero
  new requests, and re-running the probe to "get a clean ledger" would have
  spent 20 more requests against a 26 cap for no new evidence. `ts/` (the
  intermediate timestamp files) is deleted, not committed; `run.log` carries
  all three timestamps per line.
- **The same bug zeroed `host_seq`.** It was derived by counting rows in the
  file the writer never wrote, so every row read `host_seq=1`. Recomputed
  per host in file order during the rebuild (1–4 per host for the curl phase,
  5–7 for the EU hurl validations). The spacing analysis in this file uses the
  corrected values.
- **One hurl invocation failed parsing and opened no socket.** `[Headers]` is
  not a request section in hurl 8.0.1 — request headers are literal lines —
  so the first validation attempt exited 2 on a local parse error
  (`run.log`, trailing comment). The same defect was in the three pins just
  appended to `02-sso-oidc.hurl`; fixed there before any live run, counts
  re-measured (193→199 static, 401→413 execute). Like area I's four
  `hurl_exit=1` rows, the failed attempt is recorded, not tidied away — and
  like those, it is not counted toward the cap because it never touched the
  vendor.
- **GET only, except OPTIONS with an empty body** to find POST-only routes
  (`PULL_REQUEST_TEMPLATE.md`), per `docs/09:64-71`. No `-d`, no `-X POST`,
  no token exchange, no authentication. `grep -c 'POST ' probe.sh` hits only
  the preflight declaration header and comments.
- **Nothing secret was found or published.** All committed bodies are 0 or 10
  bytes of vendor error text (`bodies/.gitignore` carve-out lists the
  contents). No JWKS, no key material, no session value — `set-cookie: did`
  values appear in committed response *headers* exactly as area I committed
  them (opaque Cloudflare/Auth0 device cookies, not credentials), and the
  gate's leak scan passes on the diff.

## 6. What is now pinned

Three OPTIONS entries appended to `regression/hurl/02-sso-oidc.hurl` (EU
patient-tenant cells as canaries; the full 3×5 matrix lives in
`results.jsonl`): `/mfa/challenge` → 204 + exact
`access-control-allow-methods: GET, PUT, POST, DELETE, PATCH, OPTIONS` +
`ACAO: *`; `/bc-authorize` and
`/oauth/global-token-revocation/connection/Auth0` → 404 +
`x-auth0-not-found: 1` + `text/plain`. All three validated live via hurl
(seq 21–23, exit 0 × 3) through a different client from the probe.

Assertion counts re-measured with the one counting rule
(`scripts/measure_assertions.py`): **193 → 199 static, 401 → 413 execute per
run**. Both counts updated at every site — `README.md` ×2, `docs/09` — and
re-grepped by hand.

## 7. Request accounting

20 curl (seq 1–20) + 3 hurl validations (seq 21–23) = **23 of a 26 cap**,
3 unspent. Per-host `t_sent` gaps: trials 3.028/3.022/2.886; minimed.eu
2.778/2.936/2.403 (+327.707 idle to the validation phase, 2.742/2.455);
minimed.com 3.106/2.84/2.88; medtronic.eu 2.395/2.698/2.748; medtronic.com
3.373/2.524/2.822. Floor 2.395 s, all gaps ≥ 2 s, four negative durations
recorded with no cause asserted (top of file).

## Correction (2026-10-13) — verifier round 1 on PR #38

1. `docs/02` left a stale sentence standing: the open-questions table kept "`/mfa/challenge` … no probe result in any source" as current beside this pass's 5/5 routed result. Fixed in `docs/02-auth-tenants-and-flows.md` (row now "Partially answered 2026-10-13", old wording retained inside it); the email-scope Unknown stands.
2. Evidence-class label, applied here rather than by rewriting the record: the sentences stating all three paths are POST-only by OAuth/OIDC specification (§0 above, `probe.sh` method comment) are **INFERRED** — reasoned from the specification and from area I's retracted GET-only error, with the assumption stated there. No POST was sent by this pass, so the method set beyond "routed" is unobserved. Assumption: the specification's method requirements describe these deployments.
