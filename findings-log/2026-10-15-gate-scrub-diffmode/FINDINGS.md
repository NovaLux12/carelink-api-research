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
`run.log` line 129). The mechanism is not asserted, it is run — and every line below is
the verbatim output of the command above it, so this block is re-runnable as written:

```
$ h=jle; printf "+/home/$h" | grep -cEi '(^|[^a-z])/[hH]ome/[a-z][a-z0-9_-]{2,}(/|\b)'
1
$ h=jle; printf "+/home/$h" | grep -cEi '^[hH]ome/'
0
# the ^ branch alone cannot skip the plus
$ h=jle; printf "+/home/$h" | grep -cEi '[^a-z]/[hH]ome/[a-z][a-z0-9_-]{2,}(/|\b)'
1
```

⚠ **Two elisions are in play here and they are not interchangeable**, which is why the
printed form is what it is. The **input** is assembled at run time (`h=jle` then
`/home/$h`) and every printed line is a **bare integer**, never the matched text. That is
deliberate: the path is split so the committed file contains no *instance* of the net it
demonstrates, because this file is `.md` and therefore in the gate's own `--all` subject
set — writing the path out whole makes the gate fire on this log, which is §3c's subject,
not a contradiction of it. The **output** is not elided at all: `grep -c` prints only the
count, so nothing needs redacting there. An earlier version of this block elided the
*input* instead (`<HOME>/jle`) and printed the matched *text*, which reversed the result —
`printf '+<HOME>/jle'` contains no `/home/` substring and reads **0**, not the **1** printed
below its own command. Verifier round 2 caught that; it is the same class as a broken
citation, a redaction that silently changes what the command means.

**Controls, shape failures rather than case.** These are the replacement for a negative
control this pass wrote in its working notes and then discarded: the intended control was a
path that fails on *case* (`/homE/`), but the gate counts with `grep -cEi` (`:126`), which
is **case-insensitive**, so `[hH]ome` accepts `homE` and the "certainly-absent" path
matched. A case-based negative control is worthless against this gate. Failing the *shape*
works:

```
$ h=j; printf "+/home/$h" | grep -cEi '(^|[^a-z])/[hH]ome/[a-z][a-z0-9_-]{2,}(/|\b)'
0
# one-char name: [a-z] then [a-z0-9_-]{2,} needs 3+
$ h=1le; printf "+/home/$h" | grep -cEi '(^|[^a-z])/[hH]ome/[a-z][a-z0-9_-]{2,}(/|\b)'
0
# digit first: the class is [a-z], not [a-z0-9]
```

And the control that isolates the leading `+` as the whole difference — the pattern is
not the problem:

```
$ h=jle; printf "/home/$h" | grep -cEi '(^|[^a-z])/[hH]ome/[a-z][a-z0-9_-]{2,}(/|\b)'
1
# the pattern matches fine without a plus: the pattern is not the problem, the leading + is
```

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

The right-hand column is `self-screen.txt`, **byte-reproducible** from the tree named in
its own first line, which records the tree the **run** read — explicitly *not* the commit
the file ships in, because a file cannot contain the hash of the commit that contains it.
That is why the transcript also carries a **digest** (`sha256` of the `--all` subject list,
plus its non-empty line count): a digest is the one key that does not move under an amend.
The harness screens a **snapshot** of this directory, so the transcript no longer depends
on stdout buffering while it is being written into, and two consecutive runs are
byte-identical.

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

**150 clean-cell rows — 5 cell types × 10 patterns × 3 modes — all read 0.** A scanner
that fires on a clean line would be reported here, not tolerated (`AGENTS.md` §6 item 2).

**Counting rule**, so the headline regenerates: every row of `cells.tsv` whose cell id
matches `NEG-*`, `DROP-*` or `CARVE-*`, which is what `check_negatives()` counts. Those are
**five** cell types, not three — **`NEG-bare`, `NEG-mid`, `NEG-plus`** are the clean-line
negatives, and **`DROP-plusplus`** (the positional `^+++` drop) and **`CARVE-AGENTS`** (the
documented machine-path example) are also required to read 0 under every pattern. So
**5 × 10 × 3 = 150**, verified against `cells.tsv` by cell id rather than by trusting the
arithmetic. ⚠ **Corrected 2026-10-15 (verifier round 2):** this line previously read *"3
clean cells × 10 patterns × 3 modes"* beside the headline **150** — and 3 × 10 × 3 is **90**.
The headline was right and the rule printed beside it was wrong, which is the wrong way
round in the one section that certifies the negatives: a reader is entitled to the
arithmetic to work. The five cell types are enumerated above and §2 already decomposed them
correctly (*"3 negatives, 1 structural cell, and 1 carve-out cell"*); only this line was
out of step. It matters beyond bookkeeping — `DROP-plusplus` and `CARVE-AGENTS` are the
two rows whose zeros mean something *other* than "the pattern declined" (§3c), so a rule
that silently excluded them would let a dropped line and a non-match look identical, which
is the same shape as the carve-out defect recorded there.

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

Two of this pass's own INFERRED claims are now **OBSERVED**, on **two runs of one
source**. The `gate` job printed, as its own mode line:

```
--- leak scan (mode: diff) ---
```

| run | event | head SHA | verdict | created |
|---|---|---|---|---|
| `38762357329` | `pull_request` | `33895ee` | `GATE PASS` | 2026-10-15T15:40:12Z |
| `38766246282` | `pull_request` | `d86a21b` | `GATE PASS` | round 2, same day |

Both runs are the `research-gate` workflow in **this** repository, on a same-repository
`pull_request`, on this branch. Each concluded `GATE PASS` — the second re-ran `85 passed,
0 failed` on the 05 suite, all ten leak patterns `ok`, citations resolve, `CHECKS PASS`,
`0 mermaid problem(s)`, and the numbers check re-asserted `217` and `431`.

⚠ **CORRECTED 2026-10-15 (verifier round 2). This section previously read "OBSERVED,
once", and `once` has become a false statement of fact.** Two runs have happened; a reader
— or a later agent grepping for "observed once" to decide whether re-checking is warranted
— was being told the observation had not recurred. That is `AGENTS.md` §6 item 1: a sentence
that cannot be pointed at. **The instinct to soften `once` because "the count went up" was
the wrong reflex**, and the correction is worth stating because the two axes are different
and only one of them moved:

- **`AGENTS.md` §2.1's independence count is unchanged at 1.** §2.1 identifies a source by
  **the person or organisation** that produced the measurement. Two runs of the *same
  workflow file* on the *same event type* in *this repository* are two samples of one
  source, not two sources — the `docs/03` §3a.4 precedent, one artefact plus a PR comment
  on it. The word *independently* remains unavailable, and no strength word is used below.
- **The observation count is 2.** This is an evidence-class fact, not an independence fact,
  and it is the one that was wrong.

**Two axes, stated separately so neither is read off the other: two runs observed
(`38762357329`, `38766246282`), one source — this repository's own CI.**

What this does **not** establish is unchanged by the second run: the `push to main` event,
which `research-gate.yml:47` routes to `--all`; a **fork** pull request, where `:76-82`'s
fail-closed fallback is the interesting case; or any checkout in which `origin/main` does
not resolve. Two same-repo runs of one event type leave all three exactly where they were.
§6 carries the full list of what is still open, and `docs/11`'s successor 1 is re-scoped to
precisely those three.

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
  `FAIL` flag at **0** in both modes and **0** hits on any file here. The one
  un-elided copy of the rendered subject lines lives in the harness's scratch
  directory, created by `mktemp -d` and removed on exit. ⚠ **This was nearly false,
  and the near-miss is the point:** writing the F4 fix put a real machine path on a
  comment line of this pass's own harness, which is a `.sh` file and therefore in
  both subject sets, and `--screen` went red on the harness itself. Round 2 added a
  second instance of the same mistake — printing `$REPO` whole put an absolute home
  path into the transcript. The committed artefacts are clean because the instances
  are assembled from fragments at runtime and never appear whole in a committed
  line — see §3b, §3c and §7a.
- **The 05 vendor suite was not run locally.** The pool serialises suites. The
  static portion of the gate this pass depends on — the leak scan, both subject
  modes — was run verbatim via `--screen`, with the loop's own `FAIL` flag at **0**.
  CI then ran the real gate on the pushed branch and it concluded `GATE PASS` (§4).

  ⚠ **CORRECTED 2026-10-15 (verifier round 2): every number in the bullet above is now
  anchored to the commit it was measured at, because one sentence was carrying two numbers
  from two different trees and read as though both belonged to the nearer one.** The rule
  applied is the one lane B was given in the same round: **re-anchor each number to its own
  commit, per number**, never to the tree the paragraph happens to be sitting in.

  | figure | value | measured at | counting rule |
  |---|---:|---|---|
  | branch-diff subject files | **3** | `ab28f58..076c040` | `git diff --name-only --diff-filter=ACM` ∩ the gate's extension filter, minus the two excluded files |
  | branch-diff subject files | **5** | `ab28f58..d86a21b` | as above; the two added are `docs/09` (F7) and `pool-f/FINDINGS.md` (F2) |
  | `--all` subject files | **206** | **`ab28f58`** | `git ls-tree -r --name-only` ∩ extension filter, minus the two excluded files — **this is the tree the §3c carve-out measurement was taken on** |
  | `--all` subject files | **208** | `076c040` and `d86a21b` | as above; +2 are this pass's own `FINDINGS.md` and harness |
  | non-empty lines in the `--all` text | **43,687** | **`ab28f58`** | `grep -c '[^[:space:]]'` over the subject set above |

  The original read *"the branch diff reads **3** subject files and the `--all` list **206**
  files at `ab28f58`"*, where the trailing `at ab28f58` reads as scoping **both** clauses.
  It scopes only the second. At `ab28f58` the branch diff is **0** subject files — that
  commit *is* the base — and the diff figure of **3** was true only of `ab28f58..076c040`.
  **No verdict moves:** both figures are inventory, and §3's tables are measured against the
  scratch repo, not against either tree.

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
- **`self-screen.txt` named no commit, and naming one was not the fix.** Round 1: its
  `--all` subject-line count read **44,619**, matching **neither** `33895ee` (**44,621**)
  nor `076c040` (**44,652**) — a transcript of an intermediate tree. Round 1 "fixed" that
  by printing `HEAD <sha>, dirty <n> file(s)` as line 1, and **round 2 caught that as
  finding 5**: the file then read `HEAD 076c040…`, `dirty 6 file(s)` while §3c claimed it
  was *"regenerated at the commit this file ships in"* — **a file cannot carry the hash of
  the commit that contains it**, so that sentence was unsatisfiable and the bytes
  contradicted it. The fix is not a commit hash, it is a key that survives an amend: line 1
  now says **"the tree this RUN read, NOT the commit this transcript ships in"**, and the
  re-derivable key is the **sha256 of the `--all` subject list plus its non-empty line
  count**, printed on its own line. Anyone checking out any later commit re-runs `--screen`
  and gets the same digest if and only if nothing the gate reads moved.

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

---

## 8. Corrections from verifier round 2 (2026-10-15)

A second independent verifier returned **NOT CLEAN** on `d86a21b`: **three blocking**
findings, three non-blocking. **No measured number moved again**, and the verifier's own
re-derivations matched every figure this log publishes — the `9 / 1 / 0` table rebuilt from
`cells.tsv` by an independent implementation, `staged` identical cell-for-cell, `reCAPTCHA`
firing on cell A only in `--all`, the 150 clean rows, the vacuity triple
**450/450/37** and **440/440/36**, the carve-out's **206 / 43 687 / 4 / 4 / 0 / 0 / 1**, the
one-directional rule at **10 predicted / 10 measured / 0** on the ten line numbers §3b
claims, and F7's **326 / 208 / 3 418** at both commits. §1–§7 stand except where a
correction is cited in place. **Section numbers 1–7 are unchanged; §8 is new.**

| # | finding | where it now lives | nature |
|---|---|---|---|
| 1 | `docs/11:942` — a bare `findings-log/…` link target with no `../`, which resolves to `docs/findings-log/…` | fixed; whole-repo sweep run, §8a | **dead link, `AGENTS.md` §6 item 6** |
| 2 | the F5 regression test **passed on the F5 defect** | three positive assertions; **both mutants committed**, §8b | test could not fail |
| 3 | the §3b mechanism demo did not reproduce as printed | re-run and re-printed, every output line a bare integer, §8c | elision changed the result |
| 4 | §3d's counting rule does not regenerate its own count (3×10×3=90, not 150) | counting rule restated and enumerated, §3d | arithmetic wrong, headline right |
| 5 | `self-screen.txt` line 1 named a commit the file cannot ship in | line 1 relabelled; digest is the key, §8d | provenance unsatisfiable |
| 6 | two stale figures in §5 carried each other's commit | per-number anchor table, §5 | scoping |
| — | ruling: `once` is a false statement of fact, the independence count is not | §4 and `docs/11` successor 1, §8e | false statement (`AGENTS.md` §6 item 1) |

### 8a. Finding 1 — the link sweep, and the instances I did **not** fix

Every markdown link in `docs/` and `README.md` was resolved from the file's own directory.
**Seven are broken**, in two shapes: a missing `../` (resolves to `docs/findings-log/…`) and
an over-supplied `../../` (resolves to `../findings-log/…`). Only one is mine. The broken
shape is written here as a bare link **target** rather than as a rendered link, so that this
paragraph cannot itself become the defect it describes: the offending sequence — an opening
square bracket, a closing parenthesis, then a bare relative path — still reads as a link to
a Markdown renderer and to any future link checker, even inside an inline code span. The two
shapes are therefore named by their **prefixes** rather than quoted whole.

| location | target | resolves to | mine? | action |
|---|---|---|:---:|---|
| `docs/11:942` | `findings-log/2026-10-14-pool-f-timeline-caller/FINDINGS.md` | `docs/findings-log/…` | ✅ | **fixed** → `../findings-log/…` |
| `docs/05:188` | `findings-log/2026-10-13-area-h-report-naming/FINDINGS.md` | `docs/findings-log/…` | — | **reported, not fixed** |
| `docs/09:204` | `findings-log/2026-10-13-cors-method/spacing.txt` | `docs/findings-log/…` | — | **reported, not fixed** |
| `docs/11:198` | `../../findings-log/probe-2026-10-08/recon/AWS-GATEWAYS.md` | `../findings-log/…` | — | **reported, not fixed** |
| `docs/11:770` | `../../findings-log/probe-2026-10-08/recon/AWS-GATEWAYS.md` | `../findings-log/…` | — | **reported, not fixed** |
| `docs/11:1435` | `../../findings-log/2026-10-13-area-v-pde-clients/chunks.txt` | `../findings-log/…` | — | **reported, not fixed** |
| `docs/11:1435` | `../../findings-log/…` (second target on the line) | `../findings-log/…` | — | **reported, not fixed** |

⚠ **The six I did not fix are outside this lane, and that is a decision, not an
oversight.** `docs/05`, `docs/07`, `docs/09` outside `:206`, and `docs/11` outside this
addendum block belong to other passes; the round-2 brief scoped me to the addendum block,
the one `docs/09:206` sentence, this log directory and the appended `pool-f` correction, and
`AGENTS.md` §1 makes an edit to a page another lane owns a claim this pass cannot source.
They are recorded here with the exact fix so the owner has it. **Three of the six are the
over-`../../` shape, which the round-2 brief did not ask about and which the same sweep
found** — the class is the same defect in the opposite direction, and it is in `docs/11`
at three lines inside the same file I was editing.

**Why no check would have caught any of them:** `check_findings_log_cites`
(`research-checks.py:277`) reads `findings-log/**/*.md` as *sources* and `findings-log/`
only as valid *targets*. A `docs/` page is a source and never a target, so **a link inside
`docs/` is structurally invisible to the gate** — the same blind spot `docs/09` §4 records
for a raw pass's internal cites. A check for it is a maintainer decision (widening a check
in the PR the check passed), and it is **not** proposed here as done.

### 8b. Finding 2 — the regression test that could not fail, and the mutants that prove it now can

Round 2 fixed F5 and shipped a regression test for it **in the same commit**. The test
asserted two *strings*: the output contains `HEAD `, and it does not contain
`subject files: 0`. It never read the exit code, and `*"HEAD "*` matches the failure text
**`HEAD UNRESOLVED`**. Deleting only the `cd "$REPO"` line — the round-2 pre-flight left
intact — made `--screen` exit **1** while the test printed `ok` and `SELF-TEST PASS`. The
sentinel it grepped for had become **unreachable the moment the fix landed**, because the
new pre-flight returns before `subject files:` is ever printed: the assertion was shadowed
by the fix it was written alongside.

The replacement asserts three **positive** claims, so no early return can satisfy them:
`rc = 0`; `subject files: [1-9]` in **both** mode blocks, pinned to the mode-block pattern
so the carve-out block's own `subject files:` line cannot make a missing mode look present;
and that the run never reached the pre-flight guard. **Both mutants are committed**
(`mutants-round2.log`), built in scratch copies — the real worktree is never modified:

| mutant | change | `--screen` from a foreign cwd | `--self-test` |
|---|---|---|---|
| baseline | none | exit **0**, both modes non-zero | **PASS** (13 assertions) |
| **A** | delete **only** `cd "$REPO"` | exit **1**, pre-trip | **FAIL — 3 assertions, exit 1** |
| **B** | delete `cd "$REPO"` **and** the pre-flight guards (the true round-1 shape) | exit **1**, `subject files: 0` in both modes | **FAIL — 2 assertions, exit 1** |

Mutant A is the case that used to pass. **One honest limit:** the third assertion
(*"never reaches the pre-flight guard"*) is descriptive and does not fire on mutant B,
because mutant B **deleted** that guard — mutant B is caught by the other two. The test as
a whole discriminates both; no single assertion is claimed to catch both.

### 8c. Finding 3 — an elision that silently changed the result

§3b printed a shell transcript whose *input* was elided (`<HOME>/jle`) and whose *output*
was the matched text. The elision is required — the path is an instance of the net the
block demonstrates, and this file is `.md`, so it is in the gate's own subject set — but it
**destroys the substring the demonstration needs**: `printf '+<HOME>/jle'` contains no
`/home/`, reads **0**, and a reader running the committed command got the **opposite** of
the printed answer in a block whose only function is to be re-run.

The fix moves the elision to where it costs nothing: **the input is assembled at run time
(`h=jle` then `/home/$h`) and every printed line is a bare integer from `grep -c`**, so
nothing needs redacting in the output at all. All six printed integers are verbatim output
of the six commands above them, re-run for this revision; §3b also states *why* the two
elisions are not interchangeable, so the next person does not trade one for the other.
§3b additionally replaces this pass's discarded case-based negative control — `grep -cEi`
is case-insensitive, so a `/homE/` "certainly-absent" path **matches** — with two
**shape**-failure controls that do read 0.

### 8d. Findings 5 and 6 — provenance, and per-number anchoring

Finding 5 is the same root as F6 and my round-1 "fix" made it worse by asserting something
unsatisfiable; the correction is in §3c and §7a and is summarised there. **A committed
transcript cannot name the commit that contains it**, so line 1 now labels what it actually
is — *the tree this run read* — and the **sha256 of the `--all` subject list plus its
non-empty line count** is the re-derivable key, because a digest does not move under an
amend.

Finding 6 is §5's per-number anchor table: **3** diff subjects at `ab28f58..076c040`, **5**
at `ab28f58..d86a21b`, **206** `--all` subjects at `ab28f58` (the carve-out tree), **208** at
`076c040` and `d86a21b`, **43,687** non-empty lines at `ab28f58`. The original sentence put
both numbers under one trailing `at ab28f58`; at `ab28f58` the branch diff is **0**. No
verdict moves — both figures are inventory, and §3's tables are measured against the scratch
repo.

### 8e. The ruling on `once` — two axes, recorded at both sites

§4 said **"OBSERVED, once"**. Verifier round 2 ruled that the reasoning behind keeping it
was right and the wording wrong, and the ruling is adopted here and at `docs/11` successor 1.
§2.1 governs **sources**: two runs of the same workflow file, on the same event type, in
this repository, are two samples of one source — the `docs/03` §3a.4 precedent — so **the
independence count is unchanged at 1** and *independently* remains unavailable. But `once`
was an **evidence-class** statement, and it had become **false**: two runs have happened
(`38762357329` at `33895ee`, `38766246282` at `d86a21b`), and a reader — or a later agent
grepping for "observed once" to decide whether re-checking is warranted — was being told
otherwise. `AGENTS.md` §6 item 1. **Both sites now state the two axes separately**: two runs
observed, one source.

### 8f. Verified this round, not inherited

Round 2's verifier explicitly did **not** execute these, so they were run here and the
results are recorded rather than assumed:

- `python3 scripts/research-checks.py` → **CHECKS PASS**, exit 0, including
  `findings-log append-only ok`.
- `python3 scripts/measure_assertions.py --self-test` → **self-test passed (16 shapes)**,
  exit 0. `python3 scripts/measure_assertions.py` → **217 431**, exit 0 — **both counts
  unmoved**, no pin added.
- **The grep-first duplicate test and the quality bar** (`CONTRIBUTING-research.md:195-200`)
  were **re-run**, not re-read: all three targets (`docs/10` §1, the Closed table, `docs/11`
  itself) return no duplicate for either successor, and the bar is applied to each in §7b's
  table. Round 2's verifier read that transcript and called the conclusions "likely right"
  while running none of the greps; they are run and their exit codes are in §7b.
- `--self-test`, the full harness run, `--screen` twice for reproducibility, and **both
  mutants** (§8b) — all re-run for this revision.
