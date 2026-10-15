# Gate leak-scan pattern liveness behind the diff-mode `+` — area D, pool lane D

**Pass:** 2026-10-15 · **Slug:** `2026-10-15-gate-scrub-diffmode` · **Requests:**
**0 of a 0 cap** · **Methods:** none — this pass issued **no `GET`, no `OPTIONS`,
no `POST`**, to any host. **Delay:** **n/a — 0 requests were issued**, so no
inter-request spacing exists to measure and none is claimed. The floor this repo
enforces (**≥2s** between requests to the same host, `AGENTS.md` §8) is therefore
**not exercised** by this pass: no `sleep`, no host lock, no `curl`, no `hurl` ran.
Every input is a local file: `scripts/research-gate.sh`,
`scripts/scrub-patterns.txt`, and a scratch git repository built by the harness.

**No repair is attempted here.** Stripping the `+` at `research-gate.sh:108` or
rewriting the pattern both touch the gate's own machinery; `docs/09` §4 records
that altering a check in the same PR the check passed is a maintainer decision,
not a research pass's side effect. The deliverable is the measurement, the control
set, and successors.

---

## 1. The three subject-mode constructions, as read

`scripts/research-gate.sh` builds one text blob, `ADDED`, and then counts per
pattern how many of its lines match:

```
hits=$(printf '%s' "$ADDED" | grep -cEi "$pat" || true)     # :126
```

`ADDED` is assembled per subject file at `:101-112`, and the three modes reach it
three different ways (**OBSERVED**, read at the lines quoted, and asserted by the
harness's own extraction guards):

| mode | line | construction | leading `+`? |
|---|---|---|---|
| `all` | `research-gate.sh:106` | `cat "$f"` | **no** |
| `staged` | `research-gate.sh:107` | `git diff --cached -U0 -- "$f" \| grep '^+' \| grep -v '^+++'` | **yes** |
| `diff` | `research-gate.sh:108` | `git diff -U0 "$BASE" -- "$f" \| grep '^+' \| grep -v '^+++'` | **yes** |

The harness counts the two shapes directly rather than reading them into prose:
the `105,109` block contains **exactly 2** occurrences of `grep '^+' | grep -v
'^+++'` and **exactly 1** occurrence of `cat "$f"` (`run.log` self-test, lines
3-4). If the gate changes shape, those guards fail and the harness exits non-zero
rather than publishing verdicts for a construct it is no longer reading.

### 1a. Correction to the addendum's stated assumption

`docs/11`'s addendum recorded, as **INFERRED**: *"that `:108` is the only
`+`-prefixed subject path — `staged` mode at `:104` uses the same construction"*.
Re-derived, **two** things in that sentence are wrong (**OBSERVED**):

1. **`:104` is not the `staged` construction.** `:104` reads `[ -f "$f" ] ||
   continue` — a guard inside the per-file loop. The `staged` construction is at
   **`:107`**.
2. **`:108` is not the only `+`-prefixed path.** `:107` is a second one, with
   identical semantics. The count is 2, not 1.

The correction matters to the verdict, not just to the citation: the area's
premise was *"dead on the path every PR is checked by, live only on the
post-merge path"*. The measurement below shows the anchored net is dead on **two**
paths, `diff` **and** `staged`, and live in `--all` mode only under a further
restriction the addendum did not state.

---

## 2. Method

`scrub-diffmode-control.sh`, beside this file, **evals the gate's own bytes**:
the `66,67` exclusions, the `84,94` subject-selection `case`, the `105,109`
`ADDED` `case`, and the whole `114,136` matching loop are read out of
`scripts/research-gate.sh` at run time and evaluated. Nothing in the matching path
is re-implemented, so the harness cannot drift into measuring a different program
than the one CI runs. The harness's own `note()` is replaced with a recorder
(pattern name + hit count) because the gate's version formats prose for a human;
everything that *decides* a hit is the gate's.

**Corpus:** one scratch git repo, one synthetic `.md` file, one line per cell,
`git add`ed so that one working-tree state serves all three modes:

- **A** — the token alone on the line (at line start)
- **B** — the token mid-line, uniform wrapper (`zz <token> zz`)
- **B2** — the token mid-line, a **realistic** embedding for that pattern (a JSON
  field, a query string, an HTTP request line — see the script's `wrap_of`)
- **C** — the token at line start behind a leading `+` (the file line is `+<token>`)

**Why `B2` exists:** a bare token is the easiest cell in the matrix. It says
nothing about the line a real finding would arrive in, and for this area it is
exactly the cell that would have exposed a second defect (see §4).

**Cell count:** 4 placements × 10 patterns = 40 instance cells, plus 3 negatives
(clean bare / mid-line / behind `+`), 1 structural cell, and 1 carve-out cell =
 **45 cells × 10 patterns × 3 modes = 1350 rows** (`cells.tsv`).

**Instances are assembled at runtime from fragments and are elided from every
committed artefact.** All ten nets are self-referential — an instance that
matches pattern P is by construction text that P matches — so committing an
instance as a fixture would make the gate fire on its own control set. The one
pattern that is a bare literal (`vendor API key literal`) has its instance read at
runtime from the pattern file the gate itself exempts at `:67`, and written
nowhere.

### 2a. The harness asserts its own parsing, and can fail

`AGENTS.md` §6 item 2 governs this whole area, so the self-test is part of the
artefact (`run.log`, self-test block; `--self-test` runs it alone and exits 0):

- **extraction guards** — each `sed`-ed block must still carry its signatures:
  6 in the matching loop (`IFS='|' read`, both `[ -z … ] && continue`, the
  `grep -cEi`, the `-gt 0` test, the carve-out `grep -v`); the `ls-files`
  pathspec and the extension filter in the subject block; both `case … esac`
  shapes.
- **pattern count asserted at 10**, not assumed — the area-K precedent is a
  `scrub-check.sh` that printed `PASS` while iterating zero patterns.
- **every pattern name resolves to an instance and a wrapper**, or a cell is
  silently lost; and no name contains the gate's ` — ` hit separator, so the
  recorder's parse is unambiguous.
- **quote parity** on the fragment joiner (3 cells).
- **the construction is proven live before it is measured** — a sentinel line must
  render as exactly `+SENTINEL token here`, or the diff-mode verdicts below would
  be measuring nothing.
- **mutation test** — strip both anchors from the one anchored pattern in the
  scratch copy and assert its diff-mode hits move **0 → 1**, then restore and
  assert the baseline returns. A harness that cannot fail is not evidence.
- **vacuity guard** — every mode must produce non-zero rows, non-zero rendered
  lines *and* non-zero hits, or the run fails. This is not decorative: the first
  working version of this harness ran the gate's bare `git` commands in the
  repository instead of the scratch repo, which yields an empty subject list and
  a **1350-row matrix of zeros that reads exactly like ten dead nets**. The guard
  exists because that failure mode is silent and plausible.
- ⚠ **the fail-closed block, run in both directions** (added 2026-10-15, round 2).
  `--screen` originally `eval`'d the subject block, the `ADDED` block and the
  matching loop, but **not** `research-gate.sh:76-82` — so a checkout where
  `origin/main` does not resolve produced an empty subject list, a zero for every
  pattern, and **exit 0**. It is now `eval`'d like the rest, and asserted
  behaviourally rather than by signature: in a throwaway repo with no
  `origin/main` the block must move `diff` → `all` and set `BASE=HEAD`; after
  `git update-ref refs/remotes/origin/main` it must leave `MODE=diff` alone. Both
  directions are checked, because a block that always fired would satisfy the
  first one alone. See §7 F5.

---

## 3. Results — per-pattern verdict

Each verdict is **measured**, against **one mode**, with each firing cell named.
`cells` = 4 instance cells; `rendered` = cells whose subject text produced at
least one line (a cell the gate dropped is not a verdict); `firing` = cells
scanning ≥1.

| pattern (`scripts/scrub-patterns.txt`) | line | `^`-anchored | `^` in an alternation | `[^a-z]`-style non-letter alternative | `--all` | `staged` | `diff` |
|---|---:|---|---|---|---|---|---|
| `vendor API key literal` | `:14` | no | no | no | **live** 4/4 | **live** 4/4 | **live** 4/4 |
| `reports-broker key fragments` | `:15` | no | no | no | **live** 4/4 | **live** 4/4 | **live** 4/4 |
| `reCAPTCHA site keys` | `:28` | **yes** | no | no | **live 1/4** (cell A only) | **DEAD** 0/4 | **DEAD** 0/4 |
| `AWS VPC endpoint service name` | `:44` | no | no | no | **live** 4/4 | **live** 4/4 | **live** 4/4 |
| `internal Grafana/K8s/GitLab/DB/Prometheus host` | `:45` | no | no | no | **live** 4/4 | **live** 4/4 | **live** 4/4 |
| `internal .corp host` | `:46` | no | no | no | **live** 4/4 | **live** 4/4 | **live** 4/4 |
| `machine-specific paths` | `:47` | no | **yes** | **yes** | **live** 4/4 | **live** 4/4 | **live** 4/4 |
| `live jsession values` | `:48` | no | no | no | **live** 4/4 | **live** 4/4 | **live** 4/4 |
| `live sessionData values` | `:49` | no | no | no | **live** 4/4 | **live** 4/4 | **live** 4/4 |
| `credential prefixes` | `:57` | no | no | no | **live** 4/4 | **live** 4/4 | **live** 4/4 |

**Totals: `diff` mode — 9 live, 1 dead, 0 undecidable, 0 nets dead in every mode.**
`staged` is identical, cell for cell. `--all` mode — 10 live, but one of them
live in a single placement.

The first three columns are **string properties of the pattern file, derived by
`classify()` in the harness** and printed by it (`run.log`, classification
block). They are reported beside the verdict and not merged into it, because a
string property is not a liveness result — that is `AGENTS.md` §6 item 2 in the
form this repo keeps re-learning.

### 3a. The one dead net, cell by cell

`reCAPTCHA site keys`, `scripts/scrub-patterns.txt:28`, pattern
`^6L…$` (both ends anchored). Raw counts (`cells.tsv`, `run.log` lines 110-113):

| cell | file line | `--all` subject text | `staged` / `diff` subject text | `--all` | `staged` | `diff` |
|---|---|---|---|---:|---:|---:|
| A | `<token>` | `<token>` | `+<token>` | **1** | 0 | 0 |
| B | `zz <token> zz` | `zz <token> zz` | `+zz <token> zz` | 0 | 0 | 0 |
| B2 | `"site_key": "<token>"` | `"site_key": "<token>"` | `+"site_key": "<token>"` | 0 | 0 | 0 |
| C | `+<token>` | `+<token>` | `++<token>` | 0 | 0 | 0 |

**Two independent restrictions, and the second is bigger than the first.**

1. The leading `+` defeats it in both `+`-prefixed modes — cells A and C read 0
   there and 1/0 in `--all`.
2. **The trailing `$` defeats it in every mode whenever the token is not alone on
   the line** — cell B2, a key inside a JSON string, reads **0 in `--all` mode
   too**. So even on the post-merge path, where `--all` scans whole files, the net
   only fires on a key that sits on a line by itself. A vendor key inside any
   captured response body — which is where a key of this shape actually arrives —
   would not be caught by this net in **any** mode.

`AGENTS.md` §2 requires that both be stated rather than blended: the addendum's
claim (dead in diff mode) is confirmed and extended; the `$` restriction is new
here and is a property of the pattern, not of the gate.

### 3b. `machine-specific paths` — the mechanism, and the rule restated

`scripts/scrub-patterns.txt:47`, `(^|[^a-z])/[hH]ome/…`, fires in **4 of 4**
cells in **all three modes**, including cell C (`++/home/…` behind a `+`,
`run.log` line 129). The mechanism is not asserted, it is shown:

```
# the home segment is written <HOME> below: a committed instance of THIS net makes
# the gate fire on this very file, which is §3c's point, not a contradiction of it.
# substitute any /home/<lowercase-name> shape to reproduce.
$ printf '+<HOME>/jle' | grep -oEi '(^|[^a-z])/[hH]ome/[a-z][a-z0-9_-]{2,}(/|)'
+<HOME>/jle                 # [^a-z] consumed the '+'
$ printf '+<HOME>/jle' | grep -cE '^[hH]ome/'
0                            # the ^ branch alone cannot skip the plus
$ printf '+<HOME>/jle' | grep -cEi '[^a-z]/[hH]ome/[a-z][a-z0-9_-]{2,}(/|)'
1                            # [^a-z] alone is sufficient
```

⚠ **A negative control in this pass's own working notes failed, and it is why the rule
below is stated one-directionally.** The intended control was a path that cannot match
because the case is wrong (`/homE/`), but the gate counts with `grep -cEi` (`:126`), which
is **case-insensitive**, so `[hH]ome` accepts `homE` and the "certainly-absent" path
matched. A case-based negative control is worthless against this gate. It was a scratch
control, it reached no committed table, and **no number in §3 rests on it** — but it is
recorded here because the corrected rule is the thing that would have caught it: applied to
the *pattern*, "dead behind `+` iff every alternative is `^`-anchored" predicts nothing
about case at all, so it never offered the false inference in the first place. The
committed controls that do stand are the four cells per pattern plus three clean cells
(§3, §3d), and the gate's own fail-closed behaviour is now exercised by a behavioural
self-test rather than a string one (§2a).

#### The rule, in the form that actually classifies all ten

**A net is dead behind `+` iff every alternative is `^`-anchored.**

⚠ **CORRECTED 2026-10-15 (verifier round 1, F3).** This pass, and the addendum it was
answering, stated the dividing line as a **two-way partition** — *anchored at `^` versus
has an alternative accepting any non-letter* — and that is **not a partition of the ten**:
the right-hand side is satisfied by **exactly 1 of 10**. The other eight are unanchored
*and* carry no non-letter alternative, and are live anyway, so the stated rule classifies
**2 of 10** and leaves the rest unclassified. Carrying a non-letter alternative is one
**sufficient** way to be live behind `+`, not a necessary one — being unanchored is
sufficient on its own and needs no alternation at all. The rule above is the
necessary-and-sufficient form, it is one-directional, and **all ten classify against it**:

| pattern | line | every alternative `^`-anchored? | predicted | measured `diff` |
|---|---:|---|---|---|
| `vendor API key literal` | `:14` | no — bare literal, no anchor | live | **live 4/4** |
| `reports-broker key fragments` | `:15` | no — alternation, neither branch anchored | live | **live 4/4** |
| `reCAPTCHA site keys` | `:28` | **yes** — the sole pattern is `^…$` | **dead** | **DEAD 0/4** |
| `AWS VPC endpoint service name` | `:44` | no | live | **live 4/4** |
| `internal Grafana/K8s/GitLab/DB/Prometheus host` | `:45` | no — alternation, neither branch anchored | live | **live 4/4** |
| `internal .corp host` | `:46` | no | live | **live 4/4** |
| `machine-specific paths` | `:47` | no — one branch is `^`, the other `[^a-z]` | live | **live 4/4** |
| `live jsession values` | `:48` | no | live | **live 4/4** |
| `live sessionData values` | `:49` | no | live | **live 4/4** |
| `credential prefixes` | `:57` | no — alternation, none anchored | live | **live 4/4** |

**10 of 10 predicted, 10 of 10 measured, 0 disagreements.** That is the test the earlier
two-way phrasing could not pass, and it is the point of restating it: a rule that leaves
eight of ten unclassified cannot be used to annotate the pattern file, which is exactly
what successor 2's close condition asks for.

**Why the two-way phrasing looked right, in one sentence.** The area's evidence for it
was two examples read as two sides — the reCAPTCHA pattern is the net that *died* behind
`+`, and `machine-specific paths` is the net that *survived* — when in fact they are one
rule seen from opposite ends, so the two read as a dichotomy that the other eight patterns
silently do not belong to.

The pattern file records which is which for **none** of its ten entries.

### 3c. Two structural cells — a zero that is not a pattern verdict

| cell | file line | `all` | `staged` | `diff` | reading |
|---|---|---:|---:|---:|---|
| `DROP-plusplus` | `++This line carries no instance of any scrub pattern.` | rendered, 0/10 | **rendered 0**, 0/10 | **rendered 0**, 0/10 | the `^+++` filter is **positional**: an added line whose *content* starts with `++` renders as `+++…`, is indistinguishable from the `+++ b/file` header, and is **dropped whole** — no pattern ever sees it |
| `CARVE-AGENTS` | the machine-path example `AGENTS.md` documents | rendered, 0/10 | rendered, 0/10 | rendered, 0/10 | the loop's only per-pattern special case, `:123-124` |

Both are recorded because a zero here and a zero in §3a are different facts. A
pattern that does not match and a line the construction deleted look identical
downstream, which is how a scan becomes a check that cannot fail.

**The carve-out is not load-bearing at `ab28f58`, and that is measured, not assumed —
and "not load-bearing" is a claim about the hit count, not about the text.**

⚠ **CORRECTED 2026-10-15 (verifier round 1, F4).** This pass wrote *"So `:123-124`
currently excludes nothing."* That was wrong, and it was wrong in the direction that
matters for a future reader: the filter is not a no-op. Measured over the real `--all`
subject text **as of `origin/main` = `ab28f58`** (**206 files, 43,687 non-empty lines**),
it drops **4 lines** — `grep -cF '/home/<user>'` reads **4**, and total lines fall
**51,971 → 51,967** across the `grep -v`. What is unchanged is the **hit count**: the
pattern reads **0 without the carve-out and 0 with it**, because after `/home/` it demands
`[a-z]` and the placeholder's next character is `<`. So the accurate statement is
**"excludes 4 lines, and none of them would have matched anyway"** — not "excludes
nothing". Verifier round 1 re-derived all four numbers independently and they agree.

**Two different claims, kept apart, because "not load-bearing" and "disabled" are not
the same and only the first is this pass's:**

| | at `ab28f58` | on this branch, mid-round-2 | **as committed (this PR)** |
|---|---:|---:|---:|
| lines the carve-out drops | **4** | **10** | **11** |
| lines carrying the documented example | **4** | **10** | **11** |
| hits **without** the carve-out | **0** | **1** | **0** |
| hits **with** the carve-out (gate `:124`) | **0** | **0** | **0** |
| verdict | **not load-bearing** | **load-bearing** | **not load-bearing** |

The right-hand column is `self-screen.txt`, regenerated at the commit this file ships in
and byte-reproducible: the harness now screens a **snapshot** of this directory, so the
transcript no longer depends on stdout buffering while it is being written into.

⚠ **The middle column was measured, not constructed.** Writing the F4 fix, this pass
put both the documented example and a real machine path on **one comment line** of its own
harness — a `.sh` file, therefore in both the `all` and `diff` subject sets. `grep -v
'/home/<user>'` is **line-granular**, so it removed that line whole and suppressed a
**genuine** match; `--screen` went red on the harness itself. The comment has been rewritten
to name neither path and the harness now takes the instance from `INST_HOMEPATH`, which is
assembled from fragments at runtime (§2). Two findings come out of that accident and both
are load-bearing for this log:

1. **The carve-out is a line-granular suppressor, not a pattern-level one.** It cannot
   distinguish a line that documents the example from a line that *commits* the leak; if
   both appear on one line, the leak is dropped. That is a latent defect of `:123-124`, not
   a property of today's text, and it is why "not load-bearing at `ab28f58`" must never be
   restated as "safe to keep".
2. **It is an independent confirmation of successor 2** (§6, and `docs/11` successor 2):
   all ten nets are self-referential, so a control set cannot live in the repo as a
   fixture. This pass found that out by *committing* an instance and watching the gate fire
   on its own control — the failure mode, observed rather than reasoned.

**Positive control, kept visible so the verdict above is never read as "disabled":** a
real machine path must fire, and must survive the carve-out. It does —
`grep -cEi` reads **1** with the carve-out **not** applied and **1** with it applied, on
`cd <machine path>/projects` (`self-screen.txt`, last two lines of the carve-out block).
`:123-124` drops the documented example and nothing else.

### 3d. Negatives

**150 clean-cell rows — 3 clean cells × 10 patterns × 3 modes — all read 0.** A
scanner that fires on a clean line would be reported here, not tolerated
(`AGENTS.md` §6 item 2).

---

## 4. Observed in CI after the branch was pushed (2026-10-15)

This section is appended after the fact; §1-§3 above are unchanged. What this
commit also changed in the file, stated rather than left for a reviewer to find:
the former "What this does **not** establish" was renumbered §4 → §6, its three
bullets were folded into §6, and one accounting bullet in §5 was corrected to say
CI ran the gate on the pushed branch. No measurement, cell, count or verdict
moved. The file is new on this branch and unmerged, so nothing published was
rewritten — but `check_append_only` cannot see this either way: it handles `D` and
`M` and an `A` file rewritten in place on its own branch reports `A`
(`docs/09` §4, the append-only-guard row).

One of §4's own INFERRED claims is now **OBSERVED, once**. The `gate` job of
run `38762357329` — event **`pull_request`**, head `research/D-scrub-diffmode-control`,
SHA `33895ee` — printed, as its third line of output:

```
--- leak scan (mode: diff) ---
```

So for **one same-repository pull request**, CI did select **diff mode**, and the
ten nets in §3's `diff` column are the nets that PR was actually checked by. The
run concluded `GATE PASS` (`85 passed, 0 failed` on the 05 suite, all ten leak
patterns `ok`, citations resolve, `CHECKS PASS`, `0 mermaid problem(s)`).

What this does **not** establish: the `push to main` event, which `research-gate.yml:47`
routes to `--all`; a **fork** pull request, where `:76-82`'s fail-closed fallback
is the interesting case; or any checkout in which `origin/main` does not resolve.
One observation is one source (this repository's own CI log, one run) and is not
corroboration of the general claim. §6 carries the full list of what is still open.

---

## 5. Accounting

- **Requests: 0 of a 0 cap.** `results.jsonl` has **0 rows**, matching the cap
  line above. Methods: none — the literal words `GET` / `OPTIONS` / `POST` appear
  in this file only in that statement.
- **Delay:** 0 requests, so no spacing exists to state; the repo's ≥2s floor is
  not exercised and no delay is claimed.
- **Files:** `FINDINGS.md` (this file), `scrub-diffmode-control.sh` (the probe
  record — the thing that produced every number here), `run.log` (full
  transcript), `cells.tsv` (1350 rows: mode · cell · pattern · hits ·
  rendered_lines), `verdicts.tsv` (the derived per-pattern table), `self-screen.txt` (the `--screen`
  transcript), `results.jsonl` (empty).
- **Committed artefacts contain no instance text and no absolute home path.**
  `--screen` runs the gate's own loop over every file in this directory across
  **all** extensions — `self-screen.txt` is its output, and it reports the loop's
  `FAIL` flag at **0** in both modes over the branch diff (3 subject files) and
  **0** hits on any file here. The one un-elided copy of the rendered subject
  lines lives in the harness's scratch directory, created by `mktemp -d` and
  removed on exit. ⚠ **This was nearly false, and the near-miss is the point:** writing
  the F4 fix put a real machine path on a comment line of this pass's own harness,
  which is a `.sh` file and therefore in both subject sets, and `--screen` went red
  on the harness itself. The committed artefacts are clean because the instances are
  assembled from fragments at runtime and never appear whole in a committed line —
  see §3c and §7a.
- **The 05 vendor suite was not run locally.** The pool serialises suites. The
  static portion of the gate this pass depends on — the leak scan, both subject
  modes — was run verbatim via `--screen`: the branch diff reads **3** subject
  files and the `--all` list **206** files at `ab28f58`, with the loop's own
  `FAIL` flag at **0**. CI then ran the real gate on the pushed branch and it
  concluded `GATE PASS` (§4).

---

## 6. What this does **not** establish

- **The `push to main` event, a fork pull request, or any checkout where
  `origin/main` does not resolve.** §4 observed **one** same-repository
  `pull_request` run and one run is one source.
- **Whether the `--all` path would have caught a real key.** §3a shows the
  anchored net would not, for a key not alone on a line. That is a statement about
  the pattern, measured on synthetic lines; it is not a statement that a key is or
  is not currently committed anywhere.
- **Anything about the vendor's surface.** This pass touched no vendor host.

---

## 7. Corrections from verifier round 1 (2026-10-15)

An independent verifier returned **NOT CLEAN** on `076c040` with six findings, **none
of which moved a measured number** — all citation, wording and harness-honesty defects.
§1–§3 and §5–§6 above are unchanged except where a correction is cited in place. This
section is the single place every round-2 change is recorded, and the file's renumbering
is disclosed here rather than left for a reviewer to find. **Section numbers 1–6 are
unchanged; §7 is new.** Nothing was inserted above §6.

Each finding is a *disagreement with wording or structure*, not a disagreement with a
measurement. What the verifier did **not** overturn, and what therefore stands: the
`9 live / 1 dead / 0 undecidable` table, `staged` cell-for-cell, the 150 clean-cell
rows, the vacuity guard at both layers, all ten classifications, the `reCAPTCHA`
`--all` 1-of-4 cell, the 206 / 43,687 / 0 / 0 carve-out measurement, and the observed
CI fact — **all independently re-derived rather than read back**, by a second corpus
sharing no code with this harness, which landed on the same numbers (their matrix
550 rows / 46 non-zero against this pass's 450 / 37, same structure).

| # | finding | where it now lives | nature |
|---|---|---|---|
| F1 | the `:104` / `:108` correction was not carried to the first place a reader meets it | `docs/11`, in-place `⚠ CORRECTED` blockquote directly under the false sentence; §1a | disagreement |
| F2 | the originating area-F log carried the false sentence with no correction appended | `findings-log/2026-10-14-pool-f-timeline-caller/FINDINGS.md`, new `## Correction (2026-10-15)` section | absence of the sanctioned mechanism |
| F3 | the liveness rule was stated as a two-way partition that classifies 2 of 10 | §3b restated one-directionally, all ten re-classified; `docs/11` §3b and the area-F addendum | disagreement on framing |
| F4 | "the carve-out currently excludes nothing" — it excludes 4 lines | §3c, with the two-column measurement and the positive control | disagreement on wording |
| F5 | `--screen` exited 0 having scanned nothing from a foreign cwd | `scrub-diffmode-control.sh` `screen()`, plus a behavioural self-test and an end-to-end regression | absence of a guard |
| F6 | `self-screen.txt` recorded a line count matching no commit and named no commit | `--screen` now prints repo, HEAD and dirty-file count, so the transcript names its tree; regenerated | absence of provenance |
| F7 | `docs/09:206`'s stale `.txt` counts were recorded only in another document | one inline sentence at `docs/09:206`; this log does **not** re-derive the row's numbers | absence of a pointer |

### 7a. F5 and F6 — the harness defect that was not disclosed

Two of the three harness defects are now fixed and asserted. The third was found by the
verifier and is disclosed here in the same spirit as the first two:

- **`--screen` had no cwd guard and no vacuity guard.** The gate's loop reads
  `scripts/scrub-patterns.txt` by **relative** path (`gate:136`), and `screen()` had no
  `cd` of its own, so from any directory but the repo root the loop iterated nothing,
  every pattern read 0, and the mode printed `ok no pattern fired` and **exited 0**.
  It also `eval`'d every block *except* the fail-closed block, so a missing
  `origin/main` produced the same green by a second route. `screen()` now enters `$REPO`
  and asserts it arrived, asserts the relative pattern path and the absolute parsed copy
  are the same file, refuses to report a clean scan over **zero** patterns, an **empty**
  subject list, or a **partial** loop (it compares the number of recorded verdicts
  against the number of parsed patterns), and prints the tree it read. The
  regression is asserted end-to-end in `--self-test`: `--screen` is invoked from a
  scratch directory and must not report `subject files: 0`.
- **`self-screen.txt` named no commit.** Its `--all` subject-line count read **44,619**,
  which matched **neither** `33895ee` (**44,621**) nor `076c040` (**44,652**) — it was a
  transcript of an intermediate working tree. No prose cited it, and the file's four
  substantive assertions still held, but a transcript a reader cannot re-derive is not
  evidence. `--screen` now prints `repo …, HEAD <sha>, dirty <n> file(s)` as its first
  line, and the file has been regenerated from the final commit.

### 7b. The grep-first duplicate test (`CONTRIBUTING-research.md:199`)

Both successors were checked against `docs/10` §1, the `docs/11` Closed table and
`docs/11` itself **before** publication, and the commands and results are recorded here
rather than asserted. **Neither successor is a duplicate; neither was narrowed.**

```
$ grep -nEi "mode: diff|leak scan|fail.closed|fork (PR|pull request)|push to main" \
      docs/10-open-questions.md
  exit=1 — no match
$ grep -nEi "mode: diff|leak scan|fail.closed|fork (PR|pull request)|push to main" \
      docs/09-methodology-and-oracles.md
  docs/09:206 — the `.txt` extension blind spot. Adjacent subject (which FILES the gate
  reads), not the same one (which PATTERNS fire). This is F7's target, not a duplicate.
$ grep -nE "leak scan|scrub pattern|scrub-patterns|research-gate\.sh" \
      docs/10-open-questions.md
  docs/10:50 — a row that CITES scrub-patterns.txt as a source for three reCAPTCHA keys.
  A use of the file, not an open question about the gate.
$ grep -nEi "per-pattern|survives a leading|liveness column|no control set|self-referential net" \
      docs/10-open-questions.md docs/09-methodology-and-oracles.md
  exit=1 — no match
$ grep -c "#### Successor to the area-D addendum" docs/11-suggested-research-areas.md
  2   (successors 1 and 2, both this pass)
$ grep -n "^#### Successor to" docs/11-suggested-research-areas.md
  564, 618, 822, 852   (area F — untouched, different area)
  995, 1017            (area D — this pass)
  1710                 (area K)
```

**Against the quality bar (`CONTRIBUTING-research.md:195-200`):**

| Test | Successor 1 — the other two events' mode | Successor 2 — per-pattern liveness column |
|---|---|---|
| **Derived** | Passes. It retires half of itself on the strength of §4's one observation and names the exact line to read. It could not have been written before §4 existed | Passes. Both facts came out of building the control set this pass committed; neither was recorded anywhere |
| **Bounded** | Passes. Zero requests, no vendor host, and the close condition is checkable by a stranger reading one log line | Passes. Same; and a negative counts, stated in the row |
| **Non-duplicate** | Passes, per the greps above | Passes, per the greps above |
| **Labelled** | Passes. The one observation is OBSERVED from **one** source, explicitly not corroboration (§4); the `push to main` and fork shapes stay INFERRED | Passes. The `^+++` drop is measured on synthetic lines and labelled as such (§3c) |

### 7c. What was **not** changed, and why

- **No repair to the gate.** `research-gate.sh`, `scrub-patterns.txt`,
  `research-checks.py`, `measure_assertions.py`, `run.sh` and `research-gate.yml` are
  byte-identical to `ab28f58`. Stripping the `+`, de-anchoring the reCAPTCHA net and
  widening the extension filter are all maintainer decisions (`docs/09` §4).
- **No pin added**, so the static assertion count stays **217** and the runtime count
  **431**. A `check` site would move every site that states it.
- **`docs/09:206`'s counts are not re-derived.** F7 adds a pointer and nothing else;
  the row is `docs/09` §4's to maintain and its owner is named there. **This pass does
  not vouch for `31`, for `126`, or for `1216`** — those were measured at `cd626d6` on
  2026-10-13 and the row itself says the counts move as passes land.
- **The four `Successor to area F` blocks, the Closed table and `README.md` are
  untouched.**
