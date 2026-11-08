# Area AF — can the findings-log census be made self-deriving?

**Answer: yes, and it now is.** `scripts/research-checks.py` derives the
committed-ledger population and fails on any prose figure that no commit it is
true at anchors to.

**0 of a 0 cap. 0 requests. Methods: GET (the family the census's counting rule
would name — nothing was sent; this pass is static analysis over the working tree
only, no vendor host was contacted, so the family is recorded as unused).**
No inter-request delay is stated because no request was made — a static pass has no
spacing to measure, so the floor is **0 s apart** over zero requests; the accounting
is `0 of a 0 cap` by construction, not by restraint.

## What was wrong

The census population is **derived from the tree** — one item is one
`findings-log/*/results.jsonl`. It was nonetheless **stated by hand** in three
places, so every merge adding a ledger falsified all of them at once, silently:

| site | figure | state |
|---|---|---|
| `docs/11` S-L4c block (~3082) | 50 committed ledgers | anchored (50 at `5f37668`, 51 at `ad376d8`) |
| `docs/11` ledger-census row (~3197) | 50 committed ledgers | anchored, cross-referenced to S-L4c |
| `docs/11` correction (~3220) | 50 committed ledgers | **bare — no commit anchor** |
| `findings-log/2026-10-14-lane-s6-public-index/account.py:60-65` | 50 / 51 / 52 | anchor comment; append-only, not editable |

Measured at this head **`6600700`**: **53** committed ledgers.
The derivation is `git ls-files 'findings-log/*/results.jsonl'` → **53 at `6600700`**. The three doc
figures were written against a population of 50 and nothing derived them.

## The check (`check_ledger_census`)

1. Derives the population two ways: `git ls-files -- 'findings-log/*/results.jsonl'`
   at the working tree, and `git ls-tree -r <rev> -- findings-log/` filtered to
   that basename at any commit. Fails closed if the derivation yields 0.
2. Matches live prose claims of the form "N committed ledgers" / "N committed
   `results.jsonl` files" in `README.md` and `docs/*.md`, after stripping
   markdown emphasis (the figures are written `**50**`) and skipping table rows
   and blockquotes (quoted history is evidence, not a claim).
3. Requires a commit anchor in the paragraph — **including a correction
   blockquote directly beneath it**, which is the house form.
4. **Verifies the anchor against the tree** rather than trusting it: the anchor
   must resolve to a commit *and* that commit's tree must really have held N
   ledgers. This is what makes it self-deriving rather than footnoted — a
   mis-transcribed reading (the withdrawn S-L4c "36") fails too.

Fails on docs/; **warns only** in `findings-log/`, because that tree is
append-only under `AGENTS.md` §3 — a stale figure in `account.py`'s comment
cannot be rewritten in place and must be superseded by a dated correction. A
check that failed there would trap a lane between two rules.

## Demonstrations (all run in this worktree)

- **Passes on the tree** after the one doc fix. The population was **53** at
  `6600700` (the base this lane started from) and is **54** at this lane's own head,
  because this lane's `results.jsonl` is itself one more committed ledger — which is
  the drift this check exists to catch, arriving through the very commit that adds
  the check. Both figures are stated with the commit they are true at, per the rule
  the check enforces:
  ```
  $ git ls-tree -r --name-only 6600700 -- findings-log/ | grep -c results.jsonl
  53
  $ git ls-files -- 'findings-log/*/results.jsonl' | wc -l    # at this lane's head
  54
  ```
- **Fails on a planted bare figure**: planting a bare population sentence with no
  anchor in `docs/` fails with *"states N committed ledgers with no resolving
  commit anchor beside it"* and the run exits 1. Demonstrated and restored with
  `git checkout` — the working tree was left clean, confirmed by `git status`.
- **Fails on a mis-anchored figure**: the anchor is checked against the tree, so
  a figure whose anchor held a different count fails as a mis-transcription.
- Non-vacuity was verified separately: before the matcher was fixed, a naive
  pattern matched **0** live doc claims — the emphasis-stripping is what makes
  the check see the three real sites rather than pass on an empty match.

## Verification boundary

This check catches *unstated provenance*, not *falsehood*: a figure anchored to
a commit that genuinely held it is accepted even though it is stale at head —
which is correct, because that is the form the repo's own corrections use. What
it no longer permits is a figure with **no** commit it is true at.

**Closes:** every bare population figure in `docs/` now carries an anchor, and
the checker keeps it that way. **Zero requests.** No new successor minted: the
append-only site in `account.py` is superseded by this log, which is the
correction form §3 allows.
