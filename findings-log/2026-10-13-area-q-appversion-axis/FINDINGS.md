# Area Q — the `appVersion` body gate: a second version axis, and what it is worth

**Pass date:** 2026-10-13 · **Method:** static read of two public third-party
source repositories at named commits, over the GitHub API · **Method words:
GET only — no POST, no OPTIONS, no token exchange, no authentication attempted.**

> **Accounting — read the cap line, it is not what the claim issue said.**
>
> **21 of a 20 cap.** Claim issue #43 declared 20. **This pass sent 21 HTTP
> requests** and `results.jsonl` carries 21 rows; `wc -l results.jsonl` = 21, which
> is the number stated here, in both directions.
>
> **How the extra one happened, stated rather than reconciled.** `probe.sh` sent 18
> (seq 1–18). `probe-followup.sh` was then run twice: its first run sent request 19,
> and the second run re-sent request 19 and added request 20. The duplicate is a
> harness defect — the script resets `SEQ` to 18 rather than reading the ledger's
> last row, so a re-run re-issues the first request instead of continuing. **No row
> was deleted to make the arithmetic work**, because a ledger that undercounts is
> the quieter and worse failure (`docs/09` §4: a check that looks like it ran is
> worse than no check). It has one further consequence, in §1b.
>
> **⚠ `python3 scripts/research-checks.py` fails on exactly this line, and it should.**
> Its rule is *"an accounting that exceeds its own cap fails"* — which is the correct
> rule, correctly fired by a pass that really did exceed its cap. **Do not resolve it
> by deleting the duplicate row, by lowering `N` to 20, or by restating the cap.** Any
> of those would leave the artefact and the prose disagreeing, which is the failure
> this repository exists to catch. Every other check passes: numbers, citation
> integrity, priorities sync, prompt parity, append-only, leak scan (0 hits on all
> nine `scripts/scrub-patterns.txt` patterns), and the counting rule's own self-test.
>
> **Medtronic requests: 0.** Not "none attempted because it was unnecessary" —
> **none made, deliberately.** The only way to settle a body-field gate is a POST
> carrying an `appVersion` body; `AGENTS.md` §11 forbids that outside the two
> already-pinned public-`client_id` requests and states that no automation may
> extend the exception. A GET cannot reach a body field. So the boundary values are
> **not obtainable from outside this pass by construction**, and the area's second
> close condition applies.

**Inter-request delay:** declared **2.5 s**, `sleep 2.5` issued **inside** the
per-host `flock` (a sleep outside the lock would let the pool's other workers fire
simultaneously). **Measured floor 2.765 s** — see §1b for which oracle produced it
and why the harness's own series disagrees.

---

## 0. Evidence class, because this pass needs two labels `AGENTS.md` §2 does not define

This subject is **other people's code, written against a live API**. That is not
INFERRED and it is not OBSERVED, and the difference matters more here than anywhere
else in the repo, because a medical-data client reading this page will make a
decision on it.

The two labels used below are **third-party labels, local to this pass, not repo
policy**:

- **SOURCE-OBSERVED** — read at a named `file:line`, in a named public repository,
  at a named commit, in this pass. The bytes were fetched and the line was located
  by number in code.
- **SOURCE-PUBLISHED** — that repository's README, PR body, or comment thread. What
  an author asserts, not what anyone here saw.

**Neither is ever promoted to OBSERVED.** Neither is this repo's evidence about
Medtronic; it is evidence about a client. Adding the two to `AGENTS.md` §2 is a
**maintainer decision** and remains open at `docs/11` area S — see the addendum
added there by this pass. Until it is decided, a reader of `docs/03` sees these
labels used with the third-party flag attached, exactly as the 2026-10-11 pass used
them.

---

## 1. The ledger

### 1a. What was sent

| # | host | path (abbreviated) | role | status |
|---|---|---|---|---|
| 1 | api.github.com | `/repos/CarlosJPV/carelink-cumulus-bridge` | resolve default branch | 200 |
| 2 | api.github.com | xDrip `…/CareLinkClient.java` @ `ref=deadbeef…` | **CONTROL — certainly-absent ref** | **404** |
| 3 | api.github.com | CarlosJPV `…/src/zzz-no-such-path-area-q.ts` @ `0180b89` | **CONTROL — certainly-absent path** | **404** |
| 4 | api.github.com | xDrip `/commits/366c97a8` | resolve pinned commit | 200 |
| 5 | api.github.com | CarlosJPV `/commits/0180b89` | resolve pinned commit | 200 |
| 6 | api.github.com | xDrip `…/CareLinkClient.java` @ `366c97a8` | subject, pinned | **404** |
| 7 | api.github.com | xDrip `…/CareLinkClient.java` @ `master` | subject, head | **404** |
| 8 | api.github.com | CarlosJPV `src/carelink/cumulus.ts` @ `0180b89` | subject, pinned | 200 |
| 9 | api.github.com | CarlosJPV `src/carelink/cumulus.ts` @ `main` | subject, head | 200 |
| 10 | api.github.com | CarlosJPV `README.md` @ `0180b89` | subject, pinned | 200 |
| 11 | api.github.com | CarlosJPV `README.md` @ `main` | subject, head | 200 |
| 12 | api.github.com | CarlosJPV `src/probe-appversion.ts` @ `0180b89` | subject, pinned | 200 |
| 13 | api.github.com | CarlosJPV `src/probe-appversion.ts` @ `main` | subject, head | 200 |
| 14 | api.github.com | CarlosJPV `.gitignore` @ `0180b89` | subject, pinned | 200 |
| 15 | api.github.com | CarlosJPV `.gitignore` @ `main` | subject, head | 200 |
| 16 | api.github.com | xDrip `/pulls/4711` | author-reported table (PR) | 200 |
| 17 | api.github.com | xDrip `/issues/4711/comments` | author-reported table (comments) | 200 |
| 18 | raw.githubusercontent.com | xDrip `…/CareLinkClient.java` @ `366c97a8` | **CONTROL — cross-host byte check** | **404** |
| 19 | api.github.com | xDrip `…/dexdrip/cgm` listing @ pinned | locate the package directory | 200 |
| 19 *(again)* | api.github.com | *identical request, re-sent* | **the duplicate described in the header** | 200 |
| 20 | api.github.com | xDrip `…/cgm/carelinkfollow` listing @ pinned | locate the file | 200 |

`18` to `raw.githubusercontent.com` is the only request off `api.github.com`. **No
request went to any other host.**

### 1b. Spacing, measured two ways

Full output in [`spacing.txt`](spacing.txt); the method is in [`spacing.py`](spacing.py).

**Oracle B — kernel body-file mtimes, the series this repo says to trust.** `curl -o`
makes the kernel set each body's mtime at write time, independently of the harness's
clock. **Counting rule:** one gap per consecutive pair in ledger order per host, over
*distinct body files* — 18 measurable gaps.

- **Measured floor: 2.765 s.**
- **0 of 18 gaps under the declared 2.5 s.**
- **0 of 18 gaps under the repo's `≥2 s` floor.**
- Series validated before use: mtime span **143.895 s** against the harness's
  `t_sent` span **143.688 s**, difference **0.207 s**. The series is this run's own.

**Oracle A — the harness `t_sent` series, reported alongside and not instead.** Its
minimum is **2.014 s**, and it records **3 negative request durations** (seq 1, 9,
20: `t_done` earlier than `t_sent`, which is impossible). That is the corrupt-`t0`
class already on record in `docs/09` §4; **no cause is asserted**, and neither series
is substituted for the other.

**The duplicate's cost, measured.** Because request 19 was issued twice under one
`host_tag`, it wrote one body file twice: **21 rows, 20 distinct bodies**, so the
mtime series has no measurement for the gap between them. The harness series puts
those two requests **24.280 s** apart. The `0.000 s` entry a naive body-ordered
walk produces is a **ledger artefact, not a request-spacing failure**, and
`spacing.py` walks in ledger order to surface it as such rather than hide it.

**Caveat carried forward:** git does not preserve mtimes, so oracle B is valid on the
machine that ran the probe and is **not** re-derivable from a clean clone.

---

## 2. The controls, and what they actually decided

Controls were sent **first**, before the candidates, so the verdict is not
contaminated by the data it judges. They are not ceremonial — control 3 changed the
shape of this pass's main finding.

**C1 — certainly-absent REF** (request 2), at the most plausible path in the set.
→ `404`, 162 B, body `{"message":"No commit found for the ref deadbeef…"}`,
sha256 `5428c4bed7a433…`. *Establishes:* a 404 on this host family means "did not
resolve", not "always 200".

**C2 — certainly-absent PATH** (request 3), at a **real** ref.
→ `404`, 127 B, body `{"message":"Not Found", …}`, sha256 `e45906ce02e79f16…`.
*Establishes:* the two 404 shapes are **distinguishable**, so a bare status code can
tell a bad ref from a bad path. This is what let requests 6 and 7 be read at all.

**C3 — every subject file fetched twice, pinned commit and branch head, adjudicated
by the git blob SHA.** Equal blob SHA means byte-identical content; nothing is
decided by eyeballing a diff.

| file | pinned `0180b89` | head `main` | verdict |
|---|---|---|---|
| `src/carelink/cumulus.ts` | `448c27b19d53cb87d…` | `448c27b19d53cb87d…` | **IDENTICAL** |
| `README.md` | `430874b042061c48…` | `430874b042061c48…` | **IDENTICAL** |
| `src/probe-appversion.ts` | `7156575d18f936cb…` | `7156575d18f936cb…` | **IDENTICAL** |
| `.gitignore` | `64a3160f1eba1bcf…` | `64a3160f1eba1bcf…` | **IDENTICAL** |

**Zero drift in all four.** Every `file:line` below therefore resolves *identically*
at the pinned commit and at head, so a reader who checks out either gets the same
bytes. This is the strongest single result in the pass: the 2026-10-11 pass's
citations have not rotted in the 18 days since it made them.

**C4 — cross-host byte control** (request 18). `raw.githubusercontent.com` was to
re-fetch one file and sha256-compare it against the base64 the API returned, so that
a silently empty or truncated payload could not be mistaken for agreement
(`docs/09` §5 item 3). **It could not be run, and is recorded as INCONCLUSIVE rather
than as agreement** — the file path it targeted does not exist (§3). A control that
did not execute is not a control that passed.

---

## 3. What did **not** resolve — and it is my error, not the source pass's

The xDrip half of the claim — *"xDrip sends `appVersion` in the body at
`CareLinkClient.java:664`"* — **is not verified by this pass.** Requests 6, 7 and 18
all returned `404` with the bad-path body, byte-identical to control C2
(sha256 `e45906ce02e79f16…`). Requests 19 and 20 located the truth:

At the pinned commit `366c97a8de5fe644b20910ab008da98a07391c7b`, the package
`…/dexdrip/cgm/carelinkfollow/` contains exactly three files —
`CareLinkDataProcessor.java`, `CareLinkFollowDownloader.java`,
`CareLinkFollowService.java` — and three directories, `auth/`, `client/`, `message/`.
**There is no `CareLinkClient.java` and no `CareLinkAuthenticator.java` at the
package root.** The files the source pass cites are under `client/` and `auth/`.

**This is my defect and it is stated as one.** The 2026-10-11 pass recorded **bare
filenames**, never full paths — `CareLinkClient.java:664`, not a package path. I
reconstructed the path by concatenating a filename onto the `sparse-checkout` line
from that pass's reproduction section, and got it wrong. **That is not evidence that
the source pass's citation is broken.** What it is evidence for is a real and
narrower claim: *the filename alone does not resolve against the package path a
reader is most likely to try*, which is worth recording because this repo's own
citation rule (`AGENTS.md` §6 item 6) is about cites that resolve, and a cite that
needs a search to locate is one that can go stale unnoticed.

**What I therefore do not claim, stated plainly:** I did not read
`CareLinkClient.java` at any revision, so I assert **nothing** about what is on its
line 664, and the xDrip body-field half of the claim is carried forward as
**SOURCE-OBSERVED at the 2026-10-11 pass's citation, not re-verified here.** The
`message/` subdirectory the pass also cites does exist, which is consistent with its
other citations but does not confirm any of them.

---

## 4. What did resolve: the mechanism, in code

The CarlosJPV half is fully verifiable, and the area's load-bearing mechanism
resolves exactly where the source pass said it would.

**The `appVersion` field is a body field.** `src/carelink/cumulus.ts:143-148`, read
in code at `0180b89` and confirmed byte-identical at `main`:

```
142:    const url = `${this.urls.baseUrlCumulus}/display/message`;
143:    const body: Record<string, string> = {
144:      username,
145:      role,
146:      appVersion: APP_VERSION,     <-- the cite the source pass gave
147:      os: 'android',
148:    };
151:    const resp = await this.http.post<CumulusResponse>(url, body, ...);
```

`cumulus.ts:146` resolves to exactly `appVersion: APP_VERSION,` — **the citation is
exact.** The mechanism is SOURCE-OBSERVED: `appVersion` is a key of a JSON object
passed as the POST body, not a header. The file's own comment at `:131-135` records
the author's basis, and dates it: *"CLAVE DEL ASUNTO (descubierto por
experimentación, 25-08-2026): sin `appVersion` y `os` en el BODY, el servidor
responde HTTP 206 … No son cabeceras"*.

**`.gitignore:12` resolves exactly**, as `cumulus-response*.json`, with
`cumulus-hit.json` at `:13`, under the comment at `:9-10` explaining that the
response files carry personal and health data and must never be pushed. So the
2026-10-11 pass's statement — *the probe **scripts** are committed, their **outputs**
are not* — is confirmed in code, and the boundary values are **not reproducible from
the tree**.

---

## 5. The finding: one constant, two axes, and a two-value window

This is what the pass actually produced, and it is not in the source pass.

The area's premise is that the two axes are *"constrained in opposite directions …
so a client can be correct on one axis and broken on the other."* **That premise
holds**, on the author's own reading of both constraints
[source: `CarlosJPV/carelink-cumulus-bridge` `README.md:86-89` @ `0180b89`,
SOURCE-PUBLISHED]:

| axis | constraint | cite |
|---|---|---|
| discovery path `/discover/android/<ver>` | `3.5` → Cumulus **v11**; `3.6`–`3.8` → **v13**; **`3.9`+ → legacy config, `/connect/carepartner/v2`, no Auth0** | `README.md:86` |
| body `appVersion` | **≥ 3.7, no upper bound** | `README.md:87` |

The intersection — the version strings that satisfy **both** — is therefore
**`3.7` and `3.8`, and nothing else.**

**And the one client whose source is readable uses a single constant for both
axes.** `cumulus.ts:31` declares `const APP_VERSION = '3.8';` — three characters,
read in code, not by eye — and that one constant is used in **three** places:

```
 31: const APP_VERSION = '3.8';
 34:   `https://clcloud.minimed.eu/connect/carepartner/v13/discover/android/${APP_VERSION}`   <- axis 1
 36:   `https://clcloud.minimed.com/connect/carepartner/v13/discover/android/${APP_VERSION}`   <- axis 1
146:     appVersion: APP_VERSION,                                                            <- axis 2
```

**So this client is not running two axes at all — it is running one constant across
two axes, and it is correct only because `3.8` happens to lie in the two-value
window.** The failure mode is specific and it is silent: a maintainer who bumps that
constant to `3.9` to "modernise" satisfies axis 2 forever (no upper bound) and
breaks axis 1 immediately, landing on the legacy no-Auth0 config that
`docs/03` §3 already records as the reason the `android/3.6` pin exists. **Nothing
errors.** The client would keep getting 200s on a different, older API.

This is derived, and the assumption is stated: it assumes the two constraints hold
over the ranges the author reports, which is SOURCE-PUBLISHED and **not** verified
here (§6). It does **not** assume anything about how Medtronic implements the gate.

---

## 6. What this pass could not establish, and why

**The boundary values are community-reported and unverifiable from outside this
project.** Not "unverified" — *unverifiable under this project's own rules*:

- The gate is a **request-body** field. `AGENTS.md` §11 permits no POST to a vendor
  host outside the two already-pinned public-`client_id` requests, and states that
  no automation may extend that exception. A GET cannot carry a body.
- The author commits the probe **script** (`src/probe-appversion.ts`) but gitignores
  its **outputs** (§4). The measurements are not in the tree, so the tree cannot
  reproduce them.
- No vendor-published document names `appVersion` or a minimum version. Checked
  **offline, zero requests**, against the committed config/discovery corpus: the
  string `appVersion` appears in no config, discovery or archive capture in
  `findings-log/`. There is nothing to pin.

**So the area's second close condition is the one that applies**: recorded as
community-reported-and-unverifiable, with the reason. Both halves are labelled, and
a reader can tell which is which.

---

## 7. ⚠ Correction — a corroboration claim the artefact does not support

The 2026-10-11 pass records the boundary table as *"author-reported and corroborated
independently by a xDrip maintainer in PR #4711"*, and `docs/11` area Q carried the
same wording: *"author-reported table, corroborated by a xDrip maintainer on PR
#4711."*

**Read at the artefact, that is not what the PR contains.** The full comment thread
on xDrip PR #4711 is **three comments** (request 17):

| # | author | when | content |
|---|---|---|---|
| 1 | `CarlosJPV` | 2026-08-25T17:06:27Z | **the 10-row boundary table** — 3.5.0/3.6/3.6.1/3.6.9 → 206; 3.7/3.7.0/3.8/3.8.0/4.0.0/10.0.0 → 200; plus the no-`os` control |
| 2 | `jamorham` | 2026-08-26T09:45:05Z | `@benceszasz does this look okay to you?` |
| 3 | `benceszasz` | 2026-08-26T20:17:09Z | *"yes, everything seems to be fine! … nice work!"* |

**The table is `CarlosJPV`'s, and `CarlosJPV` is also the author of the README that
repeats it.** The maintainer comment approves the PR; it does not restate, retest, or
comment on the boundary values. So the table is **one source stated twice**, not two
independent sources.

**What survives and what does not — both recorded, neither deleted:**

- **Still true:** the table is SOURCE-PUBLISHED, author-reported. The *mechanism*
  (body field, not header) is independently verifiable in code at
  `cumulus.ts:146` (§4). The PR body independently confirms the value xDrip moved
  from — *"updates the advertised app version from `3.6.0` to `3.8.0`"* — and that
  PR **merged** 2026-08-29T11:59:05Z, which is upstream corroboration that `3.8.0`
  works, though not of where the boundary sits.
- **Not supported:** the word *independently*. Remove it and keep the claim, or keep
  the word and accept a strength the evidence does not carry. **This pass's choice
  is the former**, and the original wording stays readable in the 2026-10-11 log.

This is `AGENTS.md` §6 item 5 in the shape it warns about — derived prose
("corroborated independently") reaching further than the table it was derived from —
and it was found by reading the artefact, which is the only way it is findable.

---

## 8. Side findings

**8.1 — The committed probe script does not cover 6 of the README's own 11 table
rows.** `src/probe-appversion.ts:24` declares
`const VERSIONS = ['3.7', '3.6.9', '3.6.1', '3.5.0', '10.0.0'];` — **five** values.
`README.md:52-53` tabulates **eleven**: `3.5.0`, `3.6`, `3.6.1`, `3.6.9` → 206 and
`3.7`, `3.7.0`, `3.8`, `3.8.0`, `4.0.0`, `10.0.0` → 200. The rows with **no
corresponding entry in the committed `VERSIONS` array** are `3.6`, `3.7.0`, `3.8`,
`3.8.0`, `4.0.0` — and `3.8.0` is the exact value the xDrip PR merged, and `3.8` is
the exact value the client ships. **The two rows that matter most operationally are
two of the five the committed script never varies.** Nothing contradicts the table;
the point is how much of it the tree can reproduce, which is 5 of 11.

**8.2 — The PR body and the PR comment describe different test accounts.** The PR
body says it was tested with *"a Medtronic 780G + Guardian 4 user and Medtronic InPen
+ Simplera user"*; the comment says *"a live MiniMed Go + Instinct account (EU, care
partner)"*, and `README.md:47` repeats the latter. Both are the same author's
statements about the same change, so this is **not** a disagreement — it is one author
reporting against two different setups, recorded so a reader does not read the
comment's "tested against a live MiniMed Go + Instinct account" as covering the
combined-device claim in the PR.

**8.3 — A machine path is committed on `main`.** While checking the repo's own
hygiene I found a literal user-home path inside a committed capture in
`findings-log/2026-10-12-area-b-v12-routing/` — one line of captured `hurl` output,
outside any file this pass touched. It does not fail the gate, which scans the diff
rather than the tree. **Recorded, not fixed**: it is not this pass's file, and
`findings-log/` is append-only. It is the same defect class area I hit, where its own
`probe.sh` carried a hard-coded home path until a later pass found it.

**8.4 — No pin is possible for this area, and that is a result.** Step 4 of
`CONTRIBUTING` asks for pins for values someone will rely on. The value here is the
minimum accepted `appVersion`, and §6 sets out why no GET-only assertion could ever
test it. **An unpinned claim of this kind is exactly what rots quietly in this
repo**, so the pin is refused *loudly* rather than omitted silently: the claim is
carried into `docs/03` with its third-party label and its unverifiability attached.

---

## 9. Reproducing this pass

Unauthenticated, GET only, from a clean checkout — 21 requests, two hosts:

```bash
bash findings-log/2026-10-13-area-q-appversion-axis/probe.sh              # 18 requests
bash findings-log/2026-10-13-area-q-appversion-axis/probe-followup.sh     # re-sends 19, adds 20
python3 findings-log/2026-10-13-area-q-appversion-axis/extract.py         # 0 requests
python3 findings-log/2026-10-13-area-q-appversion-axis/spacing.py         # 0 requests
```

⚠ **`probe-followup.sh` resets `SEQ` to 18 instead of reading the ledger's last row.
Run it once.** That defect is what produced the 21st row (§ header); it is recorded
rather than patched in place, because editing the harness after the fact would make
the record disagree with the artefact. Everything downstream — `extract.py`,
`spacing.py` — is offline and re-derivable from `bodies/` alone.

The two subject commits:

- `CarlosJPV/carelink-cumulus-bridge` @ **`0180b890ff81feb2f7d186d8bf0de4d10c850375`** (2026-08-26T16:14:58Z)
- `NightscoutFoundation/xDrip` @ **`366c97a8de5fe644b20910ab008da98a07391c7b`** (2026-10-10T17:31:04Z)

Both were resolved through the API in this pass (requests 4 and 5) and both match
the abbreviated SHAs the 2026-10-11 pass recorded.

No credential, token, session value or patient identifier was read, sent, handled or
recorded at any point. The GitHub API calls carried **no `Authorization` header**.