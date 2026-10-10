# November validation runbook — what to run the day a CareLink token exists

**Trigger:** `npm run login` succeeds on a real account (patient or care-partner).
**Prereqs:** merged `main` + this branch's research notes. A token with data —
a fresh account with no pump paired answers less (see tier 0).
**Budget:** keep it to one session. Every command below is read-only except
`npm run login` itself, which writes only `logindata.json` (0600, gitignored).

## Tier 0 — is there data at all? (5 minutes)

```bash
npm run doctor          # pre-flight: env, CareLink reachable, token valid
npm start               # one fetch cycle, then Ctrl+C
```

- If `doctor` fails on the token: stop, the Auth0 surface moved — re-probe
  discovery first (`research/probe-2026-10-08/hurl/run.sh`).
- If fetch succeeds but uploads zero entries: check `deviceFamily` in the
  debug log before anything else — see Tier 1.

## Tier 1 — the #81 vocabulary question (highest value, 10 minutes)

Log the raw values (temporarily, verbose on):

```
deviceFamily, medicalDeviceFamily, deviceModel, sensorModel
```

from ONE `GET /patient/monitor/data` response and ONE
`POST /connect/carepartner/v13/display/message` response.

**Decision tree:**
- Value is `BLE_*` → current matcher correct, #81 closes as-is.
- Value is `GUARDIAN` / `NGP` / `CGM` / `CC` → #81's widening is REQUIRED;
  implement, test, and re-verify the Flex rows still hold.
- Value is `Minimed Flex` / `MMT-806x` → #91's fix covers it; confirm live.
- Value is something else entirely → log it verbatim in #81 and widen.

Whatever it is, paste the verbatim strings into #81. Do not paraphrase —
the matcher depends on exact spellings.

## Tier 2 — the #74 host question (10 minutes)

With a valid token, request `connect/data` from BOTH hosts and compare bodies:

```
GET https://carelink.minimed.eu/patient/connect/data?cpSerialNumber=NONE&msgType=last24hours&requestTime=<now>
GET https://clcloud.minimed.eu/patient/connect/data?cpSerialNumber=NONE&msgType=last24hours&requestTime=<now>
```

- Both return data → the dual-host fallback is belt-and-braces; keep.
- Only clcloud returns data → the xDrip claim holds; consider making clcloud
  the FIRST candidate for EU accounts.
- Only carelink returns data → the fallback is harmless dead code; keep anyway
  (costs one request only on empty-body answers).

## Tier 3 — the #84 alarm wire form (5 minutes)

Read `lastAlarm.code` from a live payload and check its JSON type:

- Number → current code correct; #84 becomes defence-in-depth only.
- String (`"N24"`-style) → implement the coercion in #84 now, with the NGP
  critical set (`N24, N35, N40, N47, N48, N50, N55, N131` → stop_using_pump).

## Tier 4 — the #76 reports surface (20 minutes)

```bash
GET hcp/configuration/public/logbook.supported.entry.types      # with bearer
GET hcp/configuration/public/cua.control.codes.settings        # with bearer
```

- 200 with a schema → pull both into `test/samples.ts` as sanitised fixtures;
  they are the treatments + NGP-code schemas the ROADMAP defers.
- `access.not.allowed` → the account lacks clinic scope; try the
  `reports-broker generateReport` with type `LOGBOOK` instead.
- Then: `generateReport` → poll `reportStatus` → fetch `reportCsv`. Capture
  the shape even if the content is empty.

## Tier 5 — re-run the regression suite (5 minutes)

```bash
research/probe-2026-10-08/hurl/run.sh
```

Exit 0 = the public surface has not drifted since 2026-10-08. Any failure is
a finding: diff the response against the pinned assertions before touching code.

## Aftermath

- Sanitise everything before it touches the repo: no usernames, no serials, no
  timestamps that identify the account. Fixtures carry structure, never identity.
- Update each issue with the verdict (confirmed / refuted / still open).
- If `android/3.6` no longer resolves Auth0: that is a P0, ahead of all of the
  above — the pin, the guard, and ADR 0002 all need same-day work.
