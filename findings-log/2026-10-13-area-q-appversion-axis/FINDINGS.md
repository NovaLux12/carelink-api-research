# Area Q — the `appVersion` body gate: a second version axis, and what it is worth

**Pass date:** 2026-10-13 · **Method:** static read of two public third-party
source repositories at named commits, over the GitHub API · **Method words:
GET only — no POST, no OPTIONS, no token exchange, no authentication attempted.**

> **Accounting — the cap of record was restated AFTER this pass ran. Read
> `## Correction (2026-10-13)` at the foot of this file before trusting this line.**
>
> **21 of a 21 cap.** `results.jsonl` carries 21 rows; `wc -l results.jsonl` = 21,
> which is the number stated here, in both directions. **The cap that was in force
> while these 21 requests were being sent was 20** — claim issue #43 declared 20 —
> and the pass spent 21. The cap was restated to 21 by **owner authorisation on
> 2026-10-13, after the pass completed**, recorded on the public record as a dated
> addendum on issue #43. **The restatement equals the spend exactly and grants no
> slack** a later reader could spend.
>
> **⚠ `21 of a 21 cap` makes `research-checks.py` pass, and that is NOT the same as
> the evidence having supported a cap of 21.** The number the check stops objecting
> to and the number the ledger supports are the same number for different reasons:
> one is *"this pass spent 21"*, the other is *"this pass spent 21 against a cap of
> 20, and the cap was restated afterwards to match"*. The second is the true claim.
> This line is written to match the first; the Correction below carries the second,
> which is why the restatement is recorded rather than applied silently. **A reader
> who takes the accounting line at face value will conclude there was no overrun.
> There was one, of exactly one request.**
>
> **How the extra one happened, stated rather than reconciled.** `probe.sh` sent 18
> (seq 1–18). `probe-followup.sh` was then run twice: its first run sent request 19,
> and the second run re-sent request 19 and added request 20. **No row was deleted**,
> and the number above was never lowered, because a ledger that undercounts is the
> quieter and worse failure (`docs/09` §4: a check that looks like it ran is worse
> than no check). It has one further consequence, in §1b. The harness defect that
> caused it is documented in the Correction, and the committed `probe-followup.sh` is
> **left byte-faithful to what actually ran** — the Correction gives the reason, and
> what a correct implementation would read instead.
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
**`3.7` and `3.8`, and nothing else, among the `X.Y` forms the discovery axis has
actually been probed at.**

> **⚠ Scope of the window, added 2026-10-13 (verifier round 1).** "Exactly
> `{3.7, 3.8}`" is a statement about **`X.Y` forms only**, and that restriction is
> load-bearing. The author's table lists `3.7.0` and `3.8.0` as **accepted by the
> body gate**, and its prose says both `X.Y` and `X.Y.Z` forms work there — but
> **nothing establishes what those two strings do on the discovery path.** The
> discovery axis is probed in `X.Y` form only: there is **no `X.Y.Z` cell anywhere**
> in `ORACLE-PROBE-MATRIX` (which contains only `discover/android/3.6` and `…/3.8`)
> and **zero** in `VERSION-AXIS.md`. So `3.7.0` and `3.8.0` are *not excluded* from
> the window — they are **unobserved** on the axis that would put them in or out of
> it. The window is closed at exactly two values **for the forms anyone has probed**,
> and saying otherwise would over-read a table about a different axis.

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

**8.1 — The committed probe script covers only 5 of the 10 version values in the
README's own boundary table.** `src/probe-appversion.ts:24` declares
`const VERSIONS = ['3.7', '3.6.9', '3.6.1', '3.5.0', '10.0.0'];` — **5** values.
`README.md:52-53` tabulates **10**: `3.5.0`, `3.6`, `3.6.1`, `3.6.9` → 206 and
`3.7`, `3.7.0`, `3.8`, `3.8.0`, `4.0.0`, `10.0.0` → 200. The values with **no
corresponding entry in the committed `VERSIONS` array** are `3.6`, `3.7.0`, `3.8`,
`3.8.0`, `4.0.0` — and `3.8.0` is the exact value the xDrip PR merged, and `3.8` is
the exact value the client ships. **The two values that matter most operationally are
two of the five the committed script never varies.** Nothing contradicts the table;
the point is how much of it the tree can reproduce, which is **5 of 10**.

> **Counting rule, recorded so the 10 is reproducible** (the number was wrong twice
> before this line existed — see the Correction below). **Denominator 10:** the
> table's version values are counted **per status row** — **4** on the `206` row
> (`README.md:52`) and **6** on the `200` row (`README.md:53`) — and both rows are
> counted, giving 10 distinct values. It is **not** 11: there is no eleventh value,
> and the table is **two rows, not eleven rows**. **Numerator 5:** the length of the
> `VERSIONS` array at `probe-appversion.ts:24`, and every one of its 5 entries is a
> member of the 10, so coverage is 5. Re-derive with the `extract.py` method in this
> directory: decode `bodies/10-cj-readme-pin.b`, take the **first data cell** of each
> of the two status rows, and pull the backticked values out of it. (The *second*
> cell is the result — `206 Upgrade application` / `200 OK` — and reading that cell
> instead yields **1**, not 10. That trap is real and is why this rule says *first*
> cell; it is **not** the route to the wrong denominator, because 1 cannot reach 11
> by any arithmetic. See the Correction below for the route that is claimed.)

**8.2 — The PR body and the PR comment describe different test accounts.** The PR
body says it was tested with *"a Medtronic 780G + Guardian 4 user and Medtronic InPen
+ Simplera user"*; the comment says *"a live MiniMed Go + Instinct account (EU, care
partner)"*, and `README.md:47` repeats the latter. Both are the same author's
statements about the same change, so this is **not** a disagreement — it is one author
reporting against two different setups, recorded so a reader does not read the
comment's "tested against a live MiniMed Go + Instinct account" as covering the
combined-device claim in the PR.

**8.3 — ⚠ A machine path was committed on `main`; it was true when written and is
now STALE.** While checking the repo's own hygiene I found a literal user-home path
inside a committed capture in `findings-log/2026-10-12-area-b-v12-routing/` — one
line of captured `hurl` output, outside any file this pass touched. **Recorded, not
fixed**: it is not this pass's file, and `findings-log/` is append-only. It is the
same defect class area I hit, where its own `probe.sh` carried a hard-coded home path
until a later pass found it.

> **⚠ Corrected 2026-10-13 (verifier round 1): the CONCLUSION above is right, the
> REASON was wrong.** I wrote that the capture *"does not fail the gate, which scans
> the diff rather than the tree"*. That is not the mechanism. **All three gate modes
> select their subjects by file extension** — `git ls-files '*.md' '*.yml' '*.yaml'
> '*.sh' '*.hurl'` in `--all`, and the same `\.(md|yml|yaml|sh|hurl)$` filter in
> `--staged` and diff mode. **A `.txt` capture is excluded by extension in every
> mode**, so `--all` would not have read it either. **The three filter lines
> (`scripts/research-gate.sh:86`, `:89`, `:92`) are all blamed to `6ed0a8d4`,
> 2026-10-11 16:32** — a file's later last-touch does not date a line, and
> `2457a59` (2026-10-12 19:25) added **zero** filter lines. Either way the filter
> predates this pass, so nothing about it is a consequence of
> anything here. The same distinction is what `docs/09`'s neighbouring row already
> recorded for the assertion counts — the check sees only what its own filter
> selects, and a value it cannot select is a value it is not evidence about.
>
> **And the finding is now stale, which is the record working rather than breaking.**
> `8a4ac41` ("correction: redact a machine path from area B's hurl-validation
> capture", 2026-10-13 11:27) redacted it on `main` **32 minutes after this pass
> committed** (10:55). The finding was **true when written** and is not true now.
> The sentence above is left in place unedited because that timeline is the
> evidence: the gap existed, a pass noticed it from outside its own scope, and it
> was fixed within the hour. **What is stale is the phrasing "is committed on
> `main`" — the value is no longer there.**

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

---

## Correction (2026-10-13) — the cap was restated from 20 to 21, after the pass

**The accounting line at the top of this file now reads `21 of a 21 cap`. The cap that
was in force while the requests were being sent was 20.** Both numbers are recorded
here because a cap that changes with no trace is a claim about this pass's budget
that the ledger cannot support — and because the restatement happened *after* the
spend, not before it.

| | |
|---|---|
| Cap declared in claim issue #43, before any request was sent | **20** |
| Requests actually sent, and rows in `results.jsonl` | **21** |
| Overrun | **1 request** |
| Cap of record now | **21** — restated by **owner authorisation on 2026-10-13, after the pass completed** |

**The overrun, in full.** `probe.sh` sent 18 requests (seq 1–18). `probe-followup.sh`
was then run **twice**: its first run sent request 19, and its second run **re-sent
request 19** and added request 20. Twenty-one HTTP requests left this machine, and
`results.jsonl` carries twenty-one rows. **No row was deleted**, and the number in
the accounting line was never lowered, to make any check pass.

**The harness defect, named.** `probe-followup.sh` sets `SEQ=18` at the top of each
invocation instead of reading the last `seq` already in the ledger, so a second run
**re-issued request 19** — the first request of the follow-up phase — rather than
continuing past it. It re-issued exactly that one request.

**Why the committed `probe-followup.sh` was not fixed.** It is the record of the run,
and it is left **byte-faithful to what executed** — `SEQ=18` and all. A harness
rewritten after the fact is a different and worse artefact than a harness with a
documented defect: the first implies the run went differently, the second admits that
it did not. **What a correct implementation would do, stated instead of shipped:**
derive the starting `seq` from the ledger (or from a run-marker line in `run.log`)
and begin one past it, so a re-run appends rather than re-issuing. A fixed harness,
if one is wanted for the next pass, belongs in a successor area or a note in
`docs/09` — not beside a capture it would contradict.

**The authorisation is on the public record**, as a dated addendum on issue #43, so
this restatement is not a private edit to a log.

**⚠ The tension, kept visible rather than smoothed over.** `21 of a 21 cap` is
precisely what makes `research-checks.py` pass — its rule is *"an accounting that
exceeds its own cap fails"*, and once the cap is restated the accounting no longer
exceeds it. **That is not the same as the evidence having supported a cap of 21.** The
two numbers are equal by coincidence of restatement, not because the pass fitted
inside a 21-request budget. Anyone reading the accounting line alone would conclude
there was no overrun; that conclusion would be wrong. The original 20 therefore stays
in this file, beside the restatement that supersedes it, and the restatement is
labelled as post-hoc in every place it appears.

---

## Correction (2026-10-13, verifier round 1) — §8.1 said "6 of the README's own 11 table rows"; it is 5 of 10

**Verdict: CONTRADICTS, on one count, at three sites. The finding beneath it stands.**

The original §8.1 heading, kept verbatim so the correction is auditable:

> **8.1 — The committed probe script does not cover 6 of the README's own 11 table
> rows.** … `README.md:52-53` tabulates **eleven**: … the point is how much of it the
> tree can reproduce, which is 5 of 11.

**Three defects in that one passage**, and they are the recurring classes in
`AGENTS.md` §6 items 1, 5 and 7 rather than three separate slips:

1. **The denominator was wrong: 11, not 10.** The table is **two status rows**, not
   eleven rows. Counting the version values per row gives **4** on the `206` row
   (`README.md:52`) and **6** on the `200` row (`README.md:53`) = **10**.
2. **The heading's numerator contradicted its own body.** The heading said `6`; two
   lines below the body correctly said *"two of the **five** the committed script
   never varies"* and then *also* said `5 of 11`. The body's `5` was right; the
   heading's `6` was not supported by anything.
3. **The file contradicted itself 29 lines earlier.** `§7`'s table row already called
   it *"the **10**-row boundary table"*. The same file carried both numbers.

**The counting rule is now recorded in §8.1** so the 10 is reproducible, including the
specific trap that produced the first wrong value: the table row's **second** cell is
the *result* (`206 Upgrade application` / `200 OK`), and reading that cell instead of
the first yields 1 — which is how `11` first became reachable.

**The substantive point is unchanged and is what makes the finding worth keeping.**
The committed `VERSIONS` array covers 5 of the 10, and the five it never varies are
`3.6`, `3.7.0`, `3.8`, `3.8.0`, `4.0.0` — of which **`3.8` and `3.8.0` are the exact
values the client ships and the xDrip PR merged**. A wrong count here was a wrong
count about how much of a third party's boundary table is reproducible from their
tree; it was not a wrong count about Medtronic. Corrected at all four sites: this
file's §8.1 heading, its body, and `docs/03-discovery-and-versions.md` §3a.1, which is
where it had propagated into canonical prose.

**Also corrected here, same round: §8.3's mechanism.** It claimed the committed
machine path *"does not fail the gate, which scans the diff rather than the tree."*
The conclusion held; the reason did not. **All three gate modes select subjects by
extension** — `git ls-files '*.md' '*.yml' '*.yaml' '*.sh' '*.hurl'` for `--all`, and
the same `\.(md|yml|yaml|sh|hurl)$` filter for `--staged` and diff mode — so a `.txt`
capture is excluded in **every** mode and `--all` would not have read it either. That
filter predates this pass (the three filter lines are blamed to `6ed0a8d4`,
2026-10-11 16:32), so nothing here caused it.
The same point is what `docs/09`'s neighbouring row already recorded for the
assertion counts: a check sees only what its own filter selects.

**And §8.3 is now STALE, which is the record working.** `8a4ac41` redacted that
capture on `main` at 2026-10-13 11:27, **32 minutes after** this pass committed
(10:55). The finding was **true when written** and is not true now. The original
sentence is left in place because the timeline is the evidence: the gap existed, a
pass found it from outside its own scope, and it was fixed within the hour. **What
no longer holds is the phrase "is committed on `main`".**

**Not changed: the `{3.7, 3.8}` window is still true**, but its scope is now stated
where it is claimed — see §5, which records that the window is closed at two values
**for the `X.Y` forms the discovery axis was probed at**, and that `3.7.0`/`3.8.0`
are **unobserved** on the discovery path (no `X.Y.Z` cell exists anywhere) rather
than excluded from it. That is a wording scope correction, not a retraction: the
verifier recorded it as prose reaching past its evidence, and the evidence itself
never moved.

---

## Correction (2026-10-13, verifier round 2) — three one-line items; the substance is unchanged

**Verdict: CONTRADICTS on three items, each a one-line edit.** The count itself was
**not** re-litigated: round 2 re-derived `5 of 10` from both captures by a different
route and **confirmed the counting rule reproduces**. All three items below are
wording, sourcing or scope — the same defect class round 1 caught, one level down.

**1. The window qualifier was not applied everywhere, and the front door was the
miss.** Round 1's fix scoped `{3.7, 3.8}` at four sites. **`README.md` was a fifth
and was not among them** — the commit message said "everywhere it appears", which was
false, and `git log -S` shows that paragraph was **added by this same pass** at
`432adf6`. The fix touched `docs/00`, `docs/03`, `docs/11` and this file, and missed
the file a newcomer reads first. It now carries the same `X.Y`-forms qualifier, with
`3.7.0`/`3.8.0` marked **unobserved** on the discovery path. **Five sites, not four.**

**2. A causal clause with nothing to point at. Deleted as asserted, relabelled as
INFERRED.** The counting rule said the second-cell trap *"yields 1, which is how this
number was got wrong the first time."* **The trap is real and does yield exactly 1 —
but 1 cannot reach 11 by any arithmetic**, so the clause pointed at nothing, and
`AGENTS.md` §1 says a sentence with no line to point at gets deleted rather than
hedged. The trap is kept, because it is verified and it is why the rule says *first*
cell. The **route** is now INFERRED and the assumption is stated:

> **INFERRED — how the wrong denominator arose.** The most likely route is the one
> visible in the preserved original itself: it read *"`README.md:52-53` tabulates
> **eleven**"* and then **listed ten values on the same line** — self-refuting on its
> face, with the wrong count in front of the reader and the right list immediately
> after. **Assumption:** that the number came from reading the prose label rather than
> counting the list. Nothing in the tree establishes how the sentence was actually
> written, and no counter is recorded. This is a hypothesis about a past edit, offered
> because it is checkable against the preserved text — not a finding.

**3. A line wearing a file's date. The filter's date is now the line's.** §8.3 said
the extension filter *"was last touched 2026-10-12 19:25"*. `2457a59` at that
timestamp **touched the file**, and added **zero** filter lines; `git blame` puts
`scripts/research-gate.sh:86`, `:89` and `:92` all at **`6ed0a8d4`, 2026-10-11
16:32**. The conclusion — *the filter predates this pass, nothing here caused it* —
holds on either date, so only the attribution moves. A file's last-touch wearing a
line's name is `AGENTS.md` §6 item 2, and the number was the *file's* throughout.
Corrected at both places it appeared: §8.3 and the round-1 Correction above.

**Also recorded, and not changed: the round-1 commit message overstates what was
corrected.** It claims *"Corrected at all four sites: the 8.1 heading, its body, the
section 7 row, and docs/03 section 3a.1."* **`FINDINGS.md`'s §7 "10-row boundary
table" row was always correct and was not changed** — the correction text in the file
says so honestly; only the message implied otherwise. **The pushed message is not
amended.** Rewriting a pushed commit rewrites history a reviewer may already have
read, for no change to any file; the accurate account is this paragraph and the
commit that carries it.

**Not re-litigated, per round 2's own confirmations:** `5 of 10` re-derived from both
captures by a different route; the second-cell trap yielding 1; the original `6 of 11`
character-identical and self-refuting; §8.3's extension filter confirmed at source;
the 32-minute staleness interval; zero `X.Y.Z` cells repo-wide; `unobserved` **not**
converted to `excluded`; the `rows` → `values` noun correction; the retraction, the
cap restatement, the byte-faithful `probe-followup.sh`, `config.yml` = 7, 209/423 at
all four sites, and nothing added to `regression/hurl/`.

**Method note for the next worker, from the verifier's near-miss:** this repo's local
`main` is **shared across worktrees and goes stale** — here it sat at `77b2c8e` while
`origin/main` was `5b72995`, **9 commits behind**. Diffing against it reported a
`3+/2−` change to `docs/09` that does not exist, i.e. **a manufactured false
contradiction**. `git fetch origin` and diff against **`origin/main`**, never a local
`main`. `docs/09` is byte-identical to `origin/main` on this branch, and its
`:162` historical `147` is untouched.
