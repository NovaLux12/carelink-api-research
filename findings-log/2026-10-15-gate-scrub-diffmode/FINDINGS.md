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

### 3b. `machine-specific paths` — the distinction the addendum flagged, measured

`scripts/scrub-patterns.txt:47`, `(^|[^a-z])/[hH]ome/…`, fires in **4 of 4**
cells in **all three modes**, including cell C (`++/home/…` behind a `+`,
`run.log` line 129) — because `[^a-z]` accepts the plus. The dividing line is
therefore the one the addendum names: **"anchored at `^`" versus "has an
alternative accepting any non-letter"**, and the pattern file records which is
which for **none** of its ten entries. That is now measured rather than asserted
(§3, first three columns).

### 3c. Two structural cells — a zero that is not a pattern verdict

| cell | file line | `all` | `staged` | `diff` | reading |
|---|---|---:|---:|---:|---|
| `DROP-plusplus` | `++This line carries no instance of any scrub pattern.` | rendered, 0/10 | **rendered 0**, 0/10 | **rendered 0**, 0/10 | the `^+++` filter is **positional**: an added line whose *content* starts with `++` renders as `+++…`, is indistinguishable from the `+++ b/file` header, and is **dropped whole** — no pattern ever sees it |
| `CARVE-AGENTS` | the machine-path example `AGENTS.md` documents | rendered, 0/10 | rendered, 0/10 | rendered, 0/10 | the loop's only per-pattern special case, `:123-124` |

Both are recorded because a zero here and a zero in §3a are different facts. A
pattern that does not match and a line the construction deleted look identical
downstream, which is how a scan becomes a check that cannot fail.

**The carve-out is not load-bearing today, and that is measured, not assumed.**
Applied directly to the documented example with **no** carve-out, the machine-path
pattern reads **0** — because after `/home/` the pattern requires `[a-z]` and the
placeholder's next character is `<`. Over the real `--all` subject text **as of
`origin/main` = `ab28f58`** (**206 files, 43,687 non-empty lines**), the pattern
reads **0 with the carve-out and 0 without**. So `:123-124` currently excludes
nothing. (Counted by `printf '%s' "$ADDED" | grep -c '[^[:space:]]'`, over the
subject list `--all` actually builds — re-derive rather than trust the number.)

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
  removed on exit.
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