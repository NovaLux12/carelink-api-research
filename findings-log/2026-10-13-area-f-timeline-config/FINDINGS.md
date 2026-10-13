# Area F — the timeline config key set, the two timeline-host keys, and the dedicated-route config escapes

Claim issue **#55**. `docs/11` area F. 2026-10-13.

**Total 24 of a 26 cap.** GET only — 24 GET, 0 POST, 0 OPTIONS, no
authentication, no token exchange, no cookie. **≥2 s between requests to the same
host**; a `sleep 2.5` ran *inside* a per-host `flock` in the parent checkout's
`.loop/`, so the delay is real and not merely intended while four workers probe
concurrently. Three hosts: `carelink.minimed.eu`, `carelink.minimed.com`,
`carelink-trials.minimed.com`.

Ledger: `results.jsonl`, **24 rows, one per request, and `wc -l` = 24 = the number
above.** `run.log` is the same 24 requests in order. `headers/` holds one header
capture per request (24 files). Response bodies are transient by design
(`AGENTS.md` §7 — no raw captures); `analyse.py` consumed them while they were in
hand and `rm -rf`'d them at the end.

---

## Verdict, first

Four deliverables, three of them positive:

| # | Deliverable | Verdict |
|---|---|---|
| 1 | `personal.patient.timeline.config` full key set | **POSITIVE — exactly two members, identical on all three deployments** |
| 2 | The bundle's two timeline-host keys | **RESOLVED — the bundle names a key the vendor does not publish, 3 of 3** |
| 3 | The three dedicated routes off EU | **POSITIVE, and it refutes the EU-only hypothesis — all three are live on `.com` and `-trials`** |
| 4 | `cell-digests.tsv` | **COMMITTED — the artefact area E's verifier round 2 asked for** |

**A negative counts and was the expected answer for #2, and it is what happened.**

---

## Deliverable 1 — `personal.patient.timeline.config`, full key set

**OBSERVED.** Read off the live bulk document on each deployment
(`/patient/v2/configuration/public`, `results.jsonl` seq 4 / 10 / 19).

| | `.eu` | `.com` | `-trials` |
|---|---|---|---|
| key present in document | **yes** | **yes** | **yes** |
| resolved type | `object` | `object` | `object` |
| member count | **2** | **2** | **2** |
| members (sorted) | `featureEnabled, host` | `featureEnabled, host` | `featureEnabled, host` |

Per-member types and digests — `timeline-keys.tsv`, `derived.json`:

| member | type | `.eu` | `.com` | `-trials` |
|---|---|---|---|---|
| `featureEnabled` | boolean | `true` | `true` | `true` |
| `host` | string | 79 chars, `https` | 76 chars, `https` | 76 chars, `https` |

⚠ **The two digest columns are two different conventions for the same member, and a
reader comparing them would conclude one is wrong.** `timeline-keys.tsv` column 8 is
`sha256(canon(member))` — the **canonical-JSON** encoding, so a string member hashes
**with its quotes** (`.com` `host` → `fbc3c350…`). `derived.json`'s
`member_shape.host.sha256` is `sha256` of the **raw string**, without quotes (same
member → `24ee5564…`). Both are correct for what they claim; neither is re-derivable
from the other, and `analyse.py` carries the distinction in a comment at the write
site. **A hash is only comparable inside one convention.**

**The member set is identical across all three deployments; the `host` value is
not.** `featureEnabled` carries the same canonical digest on all three
(`b5bea41b…`); `host` carries three distinct digests (`f81e6648…` / `24ee5564…` /
`988acbd7…`). **Digests, never values** — `AGENTS.md` §7, and the same convention
this repo's bulk-document digests already use.

This closes area V's addendum blocker. Area V recorded that the bundle reads the
object (selector `Nt`, 3 property reads) and that a template reads `.featureEnabled`
to choose between rendering the Patient-Timeline tab and not; the shape had never
been read. It is now read, and it has **two** members, not three — so "3 property
reads" over a 2-member object means at least one member is read more than once.

**The `host` value is deliberately not published.** Its length is 79 / 76 / 76 and
it is an `https` string, but the value itself is one unauthenticated GET away and
this log does not restate it. Whether it names an API Gateway, a `carelink.*` host,
or something else is **not claimed** — that is a successor (§7).

### The trap this file existed to avoid, made a control

`personal.patient.timeline.config` is a **literal dotted key**, not a nested path:
68 of the 69 published names are literal strings and exactly one (`captcha`) is a
real nested object. `analyse.py` therefore resolves the literal key **and** records
what a split-on-`.` walk returns for the same name, so the difference is on the
record rather than in someone's head:

| | `.eu` | `.com` | `-trials` |
|---|---|---|---|
| literal key resolves | `true` (`object`) | `true` (`object`) | `true` (`object`) |
| split on `.` resolves | **`false`** (`null`) | **`false`** (`null`) | **`false`** (`null`) |

`docs/09` §5 item 3 records what happens otherwise: a walker that resolved
`dict.get("a.b.c")` got `None`, hashed it, and two genuinely different values
produced identical digests that looked like agreement. Every digest in
`cell-digests.tsv` is type-asserted before it is hashed, and a resolve that fails
writes `NULLRESOLVED` rather than the digest of `None`.

---

## Deliverable 2 — the two timeline-host keys, reconciled

Area V left this open with both readings named. **The document supports one and
rules the other out, 3 of 3.**

| question | `.eu` | `.com` | `-trials` |
|---|---|---|---|
| is `personal.patient.timeline.host` a **top-level** key in the bulk document? | **no** | **no** | **no** |
| does `personal.patient.timeline.config` carry a **`host` member**? | **yes** | **yes** | **yes** |
| does the per-key route `/patient/configuration/system/personal.patient.timeline.host` answer? | **404**, 0 B | **404**, 0 B | **404**, 0 B |

**Reading: the bundle names a stale key the document does not publish.** The
vendor publishes exactly **one** timeline host, as `…timeline.config.host`, and
there is no second top-level `personal.patient.timeline.host` on any deployment.
The "vendor publishes a second, unrecorded key" reading is **refuted** — it would
have shown as a top-level key in a 69-key document, and it is absent from all three.

**Which of the three rows is load-bearing, and why it is not the 404.** A per-key
404 alone is ambiguous on this plane: a null-valued key 404s exactly like an absent
one (`CONFIG-NAMESPACE-DEEP.md` §"Which keys do NOT answer under the per-key form").
The **bulk document** is the decisive row, and it is a direct membership test, not
a status reading. The 404 corroborates; it does not carry the claim.

**Both readings were kept open until the document was read, as area V required.**
They are not both still open.

Combined with area V's corpus finding — the bundle's constant
`personalPatientTimelineHostURL` occurs **once**, so nothing reads it — the two
halves now agree: the bundle carries a **name with no published key and no reader**.
What area V could not rule out was a second published key; this pass ruled it out.

---

## Deliverable 3 — the three dedicated routes off EU

**POSITIVE. The "EU-only" hypothesis is refuted: all three routes are live on both
non-EU deployments, returning `200 application/json`.**

| route | `.eu` (recorded 2026-10-08) | `.com` | `-trials` |
|---|---|---|---|
| `/patient/configuration/defaultCountry` | 200 `{"value": "GB"}` | **200**, 20 B | **200**, 20 B |
| `/patient/configuration/recaptcha/key` | 200 `{"value": …}` | **200**, 58 B | **200**, 58 B |
| `/patient/configuration/messages/en` | 200 `{"messages": []}` | **200**, 22 B | **200**, 22 B |

`CONFIG-NAMESPACE-DEEP.md` lines 86, 87, 90 are the `.eu` column; they are **cited,
not re-measured** — this pass did not spend requests re-deriving them.

**`.com` and `-trials` agree exactly on two routes and differ on one**, by sha256:

- `defaultCountry` — **identical** digest on both (`a8c04033…`)
- `messages/en` — **identical** digest on both (`04868b50…`)
- `recaptcha/key` — **different** digest on each (`2018cee4…` vs `a3e59c56…`)

The `recaptcha/key` split is **consistent with** `scripts/scrub-patterns.txt`'s
recorded note that the vendor publishes three region-specific reCAPTCHA keys and
that trials carries a different three-character run again. **The key values are not
published** — that is the one thing in this namespace the gate exists for.

**`messages/en` has changed shape and this pass does not claim what it became.**
The recorded `.eu` value `{"messages": []}` is **16 bytes**; both non-EU hosts
return **22 bytes**. So the byte length differs, which is OBSERVED and derivable
from the ledger alone. What the 6 extra bytes are is **not in the ledger**, because
bodies are transient — this pass makes no claim about the content, and no reader
should infer "empty" from a 200. That is a successor (§7).

### Per-deployment 404 content-type set

**Nine 404s in this pass and not one carried a `content-type` header at all.** All
nine are `content-length: 0` with `x-cache: Error from cloudfront`
(`headers/carelink.minimed.eu--002-control-absent.h`,
`headers/carelink.minimed.eu--006-pkey-timeline-host.h`).

| host | 404s observed here | with a `content-type` |
|---|---|---|
| `.eu` | 3 | **0** |
| `.com` | 3 | **0** |
| `-trials` | 3 | **0** |

Placed beside the prior readings: area W recorded the **certainly-absent** control
`…/system/zzz.not.a.real.key.zzz` carrying `text/vnd.a` while all 11 real-key 404s
carried none; area E added one trials real-key 404 carrying
`application/vnd.nervana`. The value is three-way and remains so
(`text/vnd.a`, `application/vnd.nervana`, absent).

**INFERRED — and then falsified, in the next paragraph below. Both are kept.**
Within the *same* namespace (`/patient/configuration/system/`), an **absurd**
fabricated name (`zzz.not.a.real.key.zzz`, areas W and E) returns `text/vnd.a`,
while a **plausible-shaped** unpublished name (`personal.patient.timeline.host`,
this pass) returns **no** content-type at all. I first read that as: the
discriminator is the *plausibility of the requested name*, not area W's "control
versus real key". **Assumption stated:** the header depends on the name rather than
on some unseen property of the route state. **n = 1 per reading.**

> ⚠ **Retracted 2026-10-13 (verification). The hypothesis above is falsified by a
> cell two paragraphs above it, and it is withdrawn.**
>
> Area E's trials **seq 127**, `personal.linking.request.interval`, is a
> **real-key 404** — a 404 against a name in the committed candidate list, and that
> name is **published** in the 69-name list (`keys.txt` line 48). It carries
> **`application/vnd.nervana`**. So a *published, plausible* name produces a
> content-type, which the plausibility reading predicts it would not. **The
> hypothesis predicts the very cell it is placed beside.** `AGENTS.md` §6 item 2 is
> the shape of the mistake: a pattern in two cells that a third cell contradicts.
>
> **What survives, stated honestly: nothing about the name.** Three values exist —
> `text/vnd.a`, `application/vnd.nervana`, absent — and **no property of the
> requested name separates them**, which is the opposite of what I proposed.
>
> **What this pass does contribute, and it is coverage, not explanation: 9 of 9 of
> its own 404s carry no `content-type`, across all three deployments** — and,
> unlike areas W and E, it probed the **namespace root level** (`/patient/…/version`
> and `/patient/configuration/`), which no prior pass had. So the *root-level* 404
> shape is observed for the first time, and it is the absent-value shape.
>
> `docs/04`'s standing instruction — do not discriminate on that odd content-type —
> is confirmed again, and this pass adds a third independent reason: it now has a
> counterexample for **every** candidate rule. The correct summary is the negative
> one, and I should have written it the first time.

---

## Deliverable 4 — `cell-digests.tsv`

Committed, and it is the artefact area E's verifier round 2 asked for and could not
produce retrospectively because its bodies were gone.

```
host  key  seq  norm  sha256(canonical(parsed value))  sha256(canonical(resolved bulk subtree))
```

Six rows: the per-key projection's parsed value against its own host's resolved
bulk subtree, for both timeline names on all three deployments.

| host | key | verdict |
|---|---|---|
| all three | `personal.patient.timeline.config` | **equal, 3 of 3** (`a96b7d57…` / `f9daee21…` / `09233608…`) |
| all three | `personal.patient.timeline.host` | **NOT COMPARED — absent, 404 0 B** |

`norm` is `envelope-fromjson`: the per-key envelope is `{"value": "…"}` with the
value serialised *into a string*, so it is unwrapped and re-parsed before hashing.
Digests differ per deployment because the `host` member differs.

**Why this closes area E's addendum clause "or the area that produced it records in
prose that its '0 mismatches' claim is log-level and non-re-derivable":** this
artefact is the re-derivable form of that claim. A verifier can re-hash both sides
from this file and confirm the equality without ever holding a body. It covers the
two timeline names, **not** area E's 123 cells — area E's bodies are gone and
inventing its digests would be worse than not having them, which is exactly what
its own log says.

---

## Method

### Controls — sent first, on every host, before any candidate

`AGENTS.md` §8 and `docs/09` §3: a status code is an oracle only once controls
pass, and they go first so the verdict is not contaminated by the data it judges.

| # | control | result, all three hosts |
|---|---|---|
| 1 | `GET /patient/configuration/system/logbook.supported.entry.types` | **200**, `application/json`, 281 B, **identical sha256 on all three** — the per-key namespace is **live** on every host, so a 404 on any sibling is interpretable |
| 2 | `GET /patient/configuration/version` | **404**, 0 B, no `content-type` — plausible-shaped name, a genuine absence |
| 3 | `GET /patient/configuration/` | **404**, 0 B, no `content-type` — the namespace root does not serve a collection |

The oracle set holds on all three hosts: 200 for present, 404 for absent, in the
same namespace, with control 1 proving liveness first.

**Control 1 is not in the claim and is the one that carries the verdicts.** Without
it, a 404 on a dedicated route would be consistent with the whole `/patient/…`
tree being absent on that deployment — which is exactly the alternative reading
deliverable 3 had to exclude. Control 2 cannot do that job: it proves 404 is
answerable, not that the namespace serves.

### Spacing — two series, and the disagreement is the finding

Both series are recorded. `results.jsonl` carries `t_queued`, `t_sent` and
`t_done`, **all UTC ISO-8601 at millisecond resolution**, plus the kernel body
mtime (`body_mtime_ms`) that `curl -o` set at write time.

| oracle | series | same-host gaps | min | gaps < 2.5 s | gaps < 2.0 s |
|---|---|---|---|---|---|
| **B — kernel body-mtime** (independent of the harness clock) | 24 | 21 | **2.542 s** | **0** | **0** |
| A — harness `t_sent` | 24 | 21 | **1.803 s** | **1** | **1** |

**The measured floor is 2.542 s, from oracle B**, and it clears both the declared
2.5 s sleep and the repo's `>=2 s` floor with no exception.

**The 1.803 s reading is reported, not rounded away.** It is the `t_sent` gap
seq 11 → 12 on `carelink.minimed.com`. **Seq 11 is the one row in 24 whose
timestamps are impossible**: its `t_done` precedes its `t_sent` by **0.740 s**, and
its body mtime precedes its `t_sent` by **0.744 s**. Every other row has a
positive duration and a positive mtime-minus-`t_sent` offset (**0.045–0.547 s**).
⚠ **Corrected 2026-10-13 (verification):** this range first read **0.125–0.547 s**,
which was taken from the four rows printed during the run rather than from all 23.
The minimum is seq 2 at **+0.045 s**; the corrected range is the one above. Harmless
to the argument's direction — every one of the 23 is positive either way — but a
number in a findings log that does not re-derive is the defect this repo keeps
paying for, and the correction is recorded rather than quietly applied.

**So the sequence the two oracles disagree on is precisely the sequence whose
`date` readings are broken.** That is `docs/09` §4's finding reproduced on a new
pass — area D's 11 of 119 negative durations, area O's "prefer the mtimes and
cross-check against `t0`". **Oracle B's series is validated, not assumed:** its span
is 75.880 s against oracle A's 75.655 s, agreeing to 225 ms, which is the
trustworthiness test `docs/09` §4 sets for the mtime series.

**No cause is asserted for the broken row.** `docs/09` §4 already records that a
backwards clock step is not established and that a post-hoc edit to the log would
produce the same arithmetic, so neither candidate is excluded. What is established
is that **the requests were spaced correctly and the `date` readings moved**, and
that the two independent series agree on this only for seq 11.

`docs/09` §4's trap row carries an occurrence count (n = 4 passes, 23
occurrences as of area D). **This pass adds one more: sixth pass, 24 occurrences,
minimum 1.803 s** — the smallest sub-declared gap recorded in this repo so far.
Zero requests needed; it is re-derivable from `results.jsonl` alone.

### Candidates — every one derived from an observed convention

No wordlist, no fuzzing. Each path traces to a recorded convention:

| path | convention it derives from |
|---|---|
| `/patient/v2/configuration/public` | the bulk document `05-public-config.check.sh` already pins; area E already fetches it per host |
| `/patient/configuration/system/<flat.name>` | the per-key projection grammar, `CONFIG-NAMESPACE-DEEP.md` §TARGET, swept 69×3 by areas W and E |
| `/patient/configuration/system/<name>` with `name` = the bundle's literal | the same grammar, applied to the exact string area V recorded in the bundle |
| `/patient/configuration/defaultCountry`, `/recaptcha/key`, `/messages/{lang}` | three routes already recorded 200 on `.eu` (`CONFIG-NAMESPACE-DEEP.md` lines 86, 87, 90) and in `ARCHIVE-URLS.md` lines 315–317 |
| `/patient/configuration/version`, `/patient/configuration/` | the claim's named controls |

### What was NOT pinned, and why

Six assertions were added to `regression/hurl/05-public-config.check.sh`: the exact
member set of `personal.patient.timeline.config` on each of the three deployments,
and the absence of a top-level `personal.patient.timeline.host` on each. **Six
static assertions added, 210 → 216 static, 424 → 430 execute**, re-measured with
`scripts/measure_assertions.py` on this branch; **the merge queue must re-measure
on top of `origin/main`**, because the count is global and three other workers are
adding pins in the same pool.

**They cost zero additional vendor requests** — every body they read is already
fetched by the area E block, which is the only reason they live in `05` rather than
in a new suite.

**The three dedicated routes are deliberately not pinned**, and this is a decision
rather than an oversight. Pinning them means fetching them on every gate run: 6
more vendor requests on top of the 10 `05` already makes, a 60% increase to the
per-PR gate budget, for three routes that were unpinned from 2026-10-08 until now.
`AGENTS.md` §5 asks for a pin when a claim "should never silently rot", and a route
that stops answering would. The cost is real and the brief asks for few pins, so
the trade is recorded here rather than made silently: **a reader who wants these
three rot-proof pays 6 requests per gate run.** Their current verdicts are in
`results.jsonl`, and the suite's own budget is the deciding constraint.

---

## Correction (2026-10-13, verification round) — four defects in this pass, and one of them was mine alone

Every measurement in this log was re-derived by a fresh-context verifier and held.
These four were **not** measurement errors; they are wording, provenance and
artefact-reproducibility defects, and they are appended here rather than edited into
place. `AGENTS.md` §3: the retraction history *is* the evidence.

**1. A false first-read claim, in three places.** This log's framing, `docs/04` and
`docs/11` said the `host` value had **never been read**. **False, against this repo's
own record:** the 2026-10-08 pass read it and published it ellipsised
([source: findings-log/probe-2026-10-08/CROSS-REGION-CONFIG-FINDINGS.md] — *"Every
host below was disclosed only by the config"*), which is how `docs/07` and the key table
at `docs/04` already name this key as the disclosing one. **What was genuinely new is
the SHAPE** — the member set, `featureEnabled`'s type and value, the per-deployment
digests and lengths — and that claim (`FINDINGS.md` "Deliverable 1", *"the shape had
never been read"*) **stands**. The three overstatements are narrowed to the shape, and
the successor's stated reason is replaced: the obstacle is not an unread value, it is
that **the committed record abbreviates exactly the segment the question turns on**.
**I overstated novelty by generalising a true statement about one thing (the shape)
into a false statement about another (the value).**

**2. An INFERRED hypothesis that the repo's own record falsifies.** I proposed that
the 404 `content-type` discriminator is *the plausibility of the requested name*.
Falsified by area E's trials seq 127, `personal.linking.request.interval` — a
**published, plausible** name carrying `application/vnd.nervana`. **The hypothesis
predicted the very cell it was placed beside.** Withdrawn above, with the retraction
kept visible, and restated honestly: three values exist and **no property of the
requested name separates them**. Aggravating and separately fixed: my `docs/10`
rewrite **dropped the word "real-key"** from the retained sentence about that cell —
and that word is precisely what made the cell falsifying. **A faithful paraphrase
deleted the evidence that refuted my own claim.** `AGENTS.md` §6 item 5, committed by
a synthesis step.

**3. A number that did not re-derive.** The other rows' mtime-minus-`t_sent` offsets
read **0.125–0.547 s**; the correct range is **0.045–0.547 s** (seq 2). Taken from the
four rows printed during the run instead of all 23. Fixed in this log and in
`docs/09` §4, both sites, with the retraction visible.

**4. The committed artefact did not match its committed generator.**
`timeline-keys.tsv`'s column 8 read `member_canonical_sha256` while `analyse.py` wrote
`host_member_sha256` — I renamed the header after the run and did not change the
generator, so **re-running the committed generator could not reproduce the committed
file.** In a commit whose stated purpose is *"two columns a stranger can re-hash"*
this is the defect that mattered most. The generator now writes the name the artefact
carries, which is also the accurate one (the column covers every member row, not only
`host`). Separately, `derived.json` published
`host_member_equals_top_level_key = false`, written as a **literal** at `analyse.py:289`
and computing nothing — it read as a measurement. **No claim cited it**; deleted from
both files with the reasoning recorded at the write site.

**Non-blocking, also fixed:** (5) the two digest conventions are now stated in one
sentence instead of two files disagreeing silently; (6) the all-zero-digest guard is
**removed**, because the NULL check above it `continue`s first and `canon()` never
yields `""` — it was unreachable, and the docstring advertised it as live; (7) both
"this pin can fail" claims are now **settled offline and committed** as
`pins-selftest.sh`, which proves a third member breaks the member-set pin, publishing
the stale key breaks the absent-key pin, and neither a superstring nor a prefix
satisfies the `^$` anchor — **zero vendor requests**, jq only; (8) the site the gate's
`(\d+) pinned assertions` pattern cannot see is recorded as such in the PR.

**A disclosure pre-commitment was withdrawn on request.** The successor originally
promised to publish the un-abbreviated `host` value if it matched the recorded shape,
gated on a scrub-list check. That is a disclosure decision taken in advance, and it is
not a research pass's to make. **It is removed;** the successor now states the question
and its 3-request cost and leaves publication to a human holding the value.

---

## Correction (2026-10-13) — the pool brief and claim #55 name the wrong document, and their control premise is unsupported

**The brief is wrong about the path, and the repository is right.** BRIEF.md and
claim #55 both say the timeline config's key set comes out of
**`/patient/configuration/`**. That path is the **per-key** namespace, not the bulk
document. The bulk document is **`/patient/v2/configuration/public`** —
`regression/hurl/05-public-config.check.sh:31` fetches exactly that URL, and
`CONFIG-NAMESPACE-DEEP.md` states the per-key form is a *projection of* it. Had the
brief's path been used, deliverable 1 would have returned a 404 and been recorded
as "the key is not published" — a false negative produced entirely by the brief.
The per-host control I sent as #3 was that very path, which is how the error would
have surfaced anyway.

**The claim's control premise is not in any committed record.** Claim #55 and
`docs/11` line 178 both describe `/patient/configuration/version` and the
`/patient/configuration/` root as "already tried and 404'd on EU". **They appear
only in those three places** — the two docs pages and the pool brief. No
`findings-log/` entry records either probe. What the 2026-10-08 pass recorded as
404 is the **`/patient/v2/configuration/`** siblings (`system`, `defaultCountry`,
`version`, `messages/en`, `recaptcha/key`), which is a **different namespace**
(`CONFIG-NAMESPACE-DEEP.md` §TARGET 1).

So the premise was not wrong so much as **unverifiable** — and this is
`AGENTS.md` §6 item 6, a citation to something that is not there. **Consequence for
the method:** this pass does not inherit the premise. Both controls were **measured
per host** and are recorded in `results.jsonl`, which makes the 404 interpretable
from this pass's own evidence rather than from another pass's prose. The original
wording stays above and stays readable.

**Three further deviations from the claim, stated rather than smoothed over:**

1. **I added control 1**, a positive control the claim did not name, and it is the
   control the verdicts rest on (§Method).
2. **I did not re-probe the three dedicated routes on `.eu`.** All three are
   already recorded 200 (`CONFIG-NAMESPACE-DEEP.md` lines 86, 87, 90), so `.eu` got
   6 requests and the other two hosts got 9 each — **24, not the 26 the cap
   allowed.** The cap is a ceiling, not a target.
3. **`analyse.py` mislabelled three rows, and the committed artefacts were
   corrected.** The run emitted `PER_KEY_BODY_UNPARSEABLE_OR_MISSING` for the three
   `personal.patient.timeline.host` cells, because a 404's 0-byte body does not
   `json.load`. That reports a harness limitation as though it were a vendor fact,
   and it would have left the deliverable-2 table's most load-bearing row
   unexplained. The committed `cell-digests.tsv` and `derived.json` carry the
   ledger-derived verdict **`ABSENT_HTTP_404_0B_NO_ENVELOPE`** with the real
   request numbers (seq 6, 12, 21), and `analyse.py` now reads status from
   `results.jsonl` first so a re-run cannot repeat the mistake. **The digests were
   not retyped** — the correction was applied by script over the run's own output.
   Original wording is retained here.

---

## Evidence table

| Claim | Class | Source |
|---|---|---|
| `personal.patient.timeline.config` resolves to an object of exactly 2 members, `featureEnabled` + `host`, on all three deployments | OBSERVED | `findings-log/2026-10-13-area-f-timeline-config/derived.json` (per-host `resolved_type`, `members_sorted`); `timeline-keys.tsv` rows 2–7 |
| `featureEnabled` is boolean `true` on all three, one shared canonical digest | OBSERVED | `derived.json` → `deliverable_1.*.member_shape.featureEnabled` |
| `host` is an `https` string, 79 / 76 / 76 chars, three distinct digests — **values not published** | OBSERVED | `derived.json` → `member_shape.host` (`length`, `sha256`) |
| `personal.patient.timeline.host` is **not** a top-level key in any of the three bulk documents | OBSERVED | `derived.json` → `deliverable_2.*.bundle_named_key_present_in_bulk` (false ×3); `results.jsonl` seq 4 / 10 / 19 (69-key docs) |
| its per-key route 404s with 0 B on all three | OBSERVED | `results.jsonl` seq 6, 12, 21; `headers/carelink.minimed.eu--006-pkey-timeline-host.h` |
| the document publishes exactly one timeline host, as `…timeline.config.host` — area V's "second unrecorded key" reading is refuted 3 of 3 | OBSERVED | `derived.json` → `deliverable_2.*.published_config_carries_host_member` (true ×3) + `bundle_named_key_present_in_bulk` (false ×3) |
| all three dedicated routes answer 200 `application/json` on `.com` and `-trials` | OBSERVED | `results.jsonl` seq 13–15, 22–24; `derived.json` → `deliverable_3_dedicated_routes` |
| `defaultCountry` and `messages/en` are byte-identical across `.com` / `-trials`; `recaptcha/key` differs | OBSERVED | `derived.json` → `deliverable_3_dedicated_routes` sha256 fields |
| `messages/en` is 22 B where the recorded `.eu` value `{"messages": []}` is 16 B; **content not claimed** | OBSERVED (length) / not claimed (content) | `results.jsonl` seq 15, 24 (`bytes`); `findings-log/probe-2026-10-08/recon/CONFIG-NAMESPACE-DEEP.md` line 90 |
| 9 of 9 404s in this pass carried **no** `content-type`; all 0 B, `x-cache: Error from cloudfront` | OBSERVED | `results.jsonl` seq 2, 3, 6, 8, 9, 12, 17, 18, 21 (`content_type` empty); `headers/carelink.minimed.eu--002-control-absent.h` |
| an absurd fabricated name returns `text/vnd.a` while a plausible unpublished name returns none, same namespace, same host | OBSERVED (both cells); the **INFERRED rule drawn from them is withdrawn** | `results.jsonl` seq 6 vs `findings-log/2026-10-13-area-w-per-key/FINDINGS.md` line 95–100 and `findings-log/2026-10-13-area-e-perkey-deployments/FINDINGS.md` §4 |
| the falsifying cell: trials seq 127, `personal.linking.request.interval` — a **published** name — carries `application/vnd.nervana`, so **no property of the requested name separates the three values** | OBSERVED | `findings-log/2026-10-13-area-e-perkey-deployments/FINDINGS.md` §4 (`keys.txt` line 48 for the name being published) |
| the namespace **root**-level 404 shape (`/patient/…/version`, `/patient/configuration/`) was never probed before this pass; all 3 hosts return 404 with no `content-type` | OBSERVED | `results.jsonl` seq 2, 3, 8, 9, 17, 18 |
| the other rows' mtime-minus-`t_sent` offsets are **0.045–0.547 s** (23 rows) | OBSERVED | `results.jsonl` `body_mtime_ms` (first published 0.125–0.547 s — retracted, see the verification-round correction) |
| both AREA F pins discriminate: a third member and a published stale key each break them; `^$` survives a superstring and a prefix | OBSERVED, **re-runnable, 0 requests** | `pins-selftest.sh` (jq only, fixtures built from the committed 69-name list) |
| the per-key projection of `…timeline.config` equals its own host's bulk subtree, 3 of 3 | OBSERVED | `cell-digests.tsv` rows 1, 3, 5 |
| split-on-`.` resolves `…timeline.config` to `null` while the literal key resolves to an object, 3 of 3 | OBSERVED | `derived.json` → `split_walk_control` |
| measured spacing floor **2.542 s** from kernel body-mtimes; 0 of 21 gaps under 2.5 s | OBSERVED | `results.jsonl` `body_mtime_ms`; `run.log` |
| harness `t_sent` shows one 1.803 s gap (seq 11→12) and seq 11 has a **negative** duration of −0.740 s | OBSERVED | `results.jsonl` seq 11 `t_sent`/`t_done`/`body_mtime_ms` |
| the two series disagree only on the row whose `date` readings are impossible; no cause asserted | INFERRED | `docs/09-methodology-and-oracles.md` §4; `run.log` |
| the `.eu` column of deliverable 3 is cited, not re-measured | OBSERVED (that it is a citation) | `findings-log/probe-2026-10-08/recon/CONFIG-NAMESPACE-DEEP.md` lines 86, 87, 90 |

## Files

`FINDINGS.md` · `probe.sh` (harness as sent) · `analyse.py` (post-sweep derivation,
run while bodies were in hand) · `pins-selftest.sh` (proves the six AREA F pins can
fail — jq only, **zero vendor requests**) · `results.jsonl` (24 rows) · `run.log` ·
`headers/` (24 captures) · `cell-digests.tsv` · `timeline-keys.tsv` · `derived.json`

**Artefact / generator consistency, after the verification round.** `timeline-keys.tsv`
and `cell-digests.tsv` are both written by `analyse.py`, and both now match their
generator's column headers exactly. **They are still not byte-reproducible from a
re-run**, and could not be: the bodies are deleted when the sweep ends
(`AGENTS.md` §7), so a re-run re-derives them from a fresh fetch, and the per-cell
digests are a property of what the vendor served on the day. `pins-selftest.sh` **is**
byte-reproducible offline and is the part of the generator a stranger can verify
without the network.