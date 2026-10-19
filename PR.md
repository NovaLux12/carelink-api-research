## What this PR does

**finding + correction.** It corrects `docs/10` §1 row 51 in its own commit (`5508de9`,
before a single request) and then measures the half that row never stated: whether the
`hcp/configuration/public/*` existence verdicts are **deployment-portable**, and whether the
**POW/CUA product split** appears in the verdicts rather than only in one `base.uri`.

Answer: the verdicts **are** portable — **15 of 15** on three further deployments — and the
split is **not** there, in three independent ways.

## Evidence

| Claim | Class | Source |
|---|---|---|
| `docs/10` §1 row 51 was wrong on **both** halves, corrected before any request | SOURCE-OBSERVED | commit `5508de9`; `findings-log/probe-2026-10-08/recon/HCP-CONFIG-SCHEMA.md` §10 ("Do not re-run"); `docs/07:112-124`, `:247-262` |
| All 4 bundle digests reproduce their recorded values (`2a7fa8e7af519c2b…` ×3, `a054555a0f22176e…`) | OBSERVED | `results.jsonl` seq 1–4; `plan.md` §Corpus control |
| **Both builds carry an identical `hcp/configuration` route table** — 15 `public/*` + 6 direct, name for name | OBSERVED (shipped code) | `plan.md` §The two route tables, `plan.py` extraction |
| That extraction returns the same population §10 records (15 and 6) | OBSERVED | `plan.md` self-check line |
| **Each build names the other's product namespace** | OBSERVED (shipped code) | `plan.md` shared-15 list against the two empty clinic-only / support-only lists |
| **15 of 15** route literals carry the same status verdict on all three hosts | OBSERVED | `analysis.md` §3; `results.jsonl` seq 5–61 |
| All 4 controls passed on all 3 hosts; `412` = header rejected; namespace case-sensitive | OBSERVED | `analysis.md` §6 |
| **9 of 15** keys byte-identical across all three hosts; **6** differ, and only `.eu`-vs-`.com` | OBSERVED | `analysis.md` §4 |
| **15 of 15** byte-identical between clinic `.com` and support `.com`, across two different builds | OBSERVED | `analysis.md` §5 |
| `cua.crm.settings` ships `"product": "pow"` on all three hosts | OBSERVED | `headers/k021-…`, `k033-…`, `k045-…` |
| `carelink-support.medtronic.com` serves **no** CSP / HSTS / `x-content-type-options` — **0 of 19** vs **19 of 19** | OBSERVED | `analysis.md` §7; `headers/*.h` |
| A credential-shaped `x-api-key` is served by this surface on `.com`, a placeholder on `.eu` | OBSERVED, **value redacted** | `headers/k028-…`, `k029-…`, `k052-…`, `k053-…`; `REDACTIONS.md`; `docs/08` F2 |
| That key is **already known** and does not authenticate against production | SOURCE-OBSERVED | `docs/08-security-findings.md` §F2; `findings-log/probe-2026-10-08/SECURITY-FINDINGS.md` §S3 |
| Area A's "the base tracks the deployment, not the product" | now OBSERVED, 15 keys × 3 hosts | `findings-log/2026-10-12-area-a-clinic-portal-region/FINDINGS.md` §5 vs `analysis.md` §4 |
| `carelink-support.medtronic.eu`'s verdicts | **INFERRED**, excluded from every figure | same build digests asserted on its `.com` pair; body never requested |
| Whether `carelinkhp`'s `application/json` vs this pass's `application/octet-stream` is per-host or a loose record | **not determined** | `carelinkhp`'s config surface not re-probed; §10 says do not re-run it |
| The sub-floor spacing reading (2.276 s, 1 of 57 gaps) | OBSERVED; **no cause asserted** | `analysis.md` §2 |

### Verifier round 1 — both blocking findings fixed

**B1 — the status repair covered only the first gate run.** Reproduced exactly:
26 gate rows existed at that point, 22 with unusable statuses, 11 repaired → 11 shipped
unrepaired and undisclosed (seq 75, 76, 79–87), two of them (`seq 82`, `83`) holding **5513-byte HTML documents** in
`http_status`. `repair-status.py` v1 was **scoped to an event instead of to a state**.

```
BEFORE: 26  22  11        # gate rows | unusable | already-marked
AFTER : 52   0  22        # 52 = 4 runs x 13 ; 0 unusable ; 30 clean ; 22 marked
```
The repair is now **total and idempotent** — it walks every `kind: gate-suite` row on every
run and reports clean / marked / repaired. It replaces a contaminated value with an explicit
marker naming the reason, preserves the original string's length in
`http_status_original_length`, corrects the row's `ledger_note` to name the status field,
and **invents no status code**.

**The shim was rewritten so it cannot recur.** It now asks curl for the status on its own
channel, appending `--write-out '%{stderr}%{http_code}'` **only when the caller supplied no
`-w`** — because curl *replaces* rather than concatenates multiple `--write-out` options
(verified locally on a `file://` URL: adding a second left stdout empty and would have broken
the suite's own status capture). The suite's stdout is byte-for-byte what it would have been.
A log-write failure is now **loud on stderr**, since a silently dropped line would put a
vendor request in the pass's traffic with no row for it.

**This is demonstrated, not asserted:** of the 52 rows now in the ledger, gate runs 1–2
(seq 62–87) produced 4 clean out of 26, and gate runs 3–4 (seq 88–113), under the new
shim, produced **26 of 26 clean** — real `200`s and real `412`s.

**B2 — the revised cap was not enforced by the committed `probe.sh`.** Reproduced: `CAP=85`
at line 41 was the only assignment while the log claimed 90. **Fixed at the mechanism, not
the prose:** `probe.sh` now holds the single assignment `CAP=113`; `cap_guard` reads it;
`plan.py` receives it as `"$CAP"`; `absorb-gate.py` **parses `CAP=` out of `probe.sh`**
rather than repeating the value and refuses to append past it; `gate.sh` re-reads it and
prints `CAP_STATE=ok|over`. The run below printed `CAP_STATE=ok`.

**Five non-blocking findings — what was done to each**

| # | Finding | Action |
|---|---|---|
| 1 | `x-cache` uncited behind the "at the edge" claim | **Fixed.** The control row now carries `x-cache: Error from cloudfront` + `x-amz-cf-pop` verbatim with the three capture paths. `HCP-CONFIG-SCHEMA.md:66` already recorded it; `FINDINGS.md` did not. |
| 2 | Two denominators in §8.1 (19 vs 20) | **Fixed.** A counting-rule callout states the populations *before* the numbers: **19** = config responses per host (bundle fetch excluded), **20** = all rows including the bundle fetch. Mirrored into `analyse.py` so `analysis.md` cannot drift from it. |
| 3 | Two `headers` serialisations | **Fixed as a note, not a rewrite.** `FINDINGS.md` §2 and a banner in `analysis.md` name both forms, their row ranges (seq 1–55 vs 56–61) and the root cause, and state that `analyse.py` reads the `.h` files so no finding depends on it. Left in place: normalising a recorded field to a shape the process did not emit is not a repair. |
| 4 | Stale "11 gate-suite rows" numeral in §2 | **Fixed** — now "All 39" at that point, and "All 52" in the final accounting. |
| 5 | `redact.py` docstring arithmetic (9+3=12) vs its count of 11 | **Fixed, and the file was misnamed.** The arithmetic is in `repair-status.py`'s docstring, not `redact.py`'s. It now reads **22 of the 52**, which is what the script actually did over the full ledger. |

### Round 2 — `### AB.` arithmetic did not close, and a §2.1 strength word

**`AB` fixed, both defects in one sentence because they are one mistake.** The row read
**"Bounded: 44 requests"** over an itemisation summing to **41**, and called the corpus
control **"two build digests"**. Both were counting per *build* where the control is performed
per *host* — and `2` and `4` are the two ends of that error, since this pass's own sweep took
**four** captures (`b01`–`b04`, one per host, printed with their recorded digests in
`plan.md` §Corpus control). The row now reads **43**, itemised so it closes:
**18 + 12 + 9 + 4 = 43**, with no unstated slack. The superseded wording is preserved verbatim
in a dated blockquote rather than edited away.

**§2.1 flag, appended rather than edited.** One sentence used *independently* as an instrument
adverb — "independently of the probe" — on a claim whose independent count is **1**.
`AGENTS.md` §2.1 permits the word only at count ≥ 2 and does not carve out adverbial uses. The
offending sentence is quoted verbatim in the log's appended `## Correction (2026-10-17) §B` and
**left in place**: `findings-log/` is append-only (§3), and the escape hatch is *add a dated
correction section*, not *edit the sentence and note it later*. Rewriting it would destroy the
evidence that the word was there.

**The "corrected to column" this PR does not contain.** Round 2 asked that any correction-table
cell implying an in-place edit be reworded. Searched, and there is no such cell:

```
grep -rn "corrected to" docs/*.md findings-log/2026-10-17-hcp-config-deployments/*.md
  -> docs/09:301, docs/11:1899   (both pre-existing, neither mine)
git diff origin/main -- docs/ findings-log/ | grep '^+' | grep -iE "corrected to|now reads"
  -> 1 hit, inside repair-status.py's docstring, describing a JSON field that script owns
```

The only correction table this pass wrote is §0's **"the row said | the source says"**, whose
left column already quotes the superseded wording rather than claiming an edit. **No change was
made because there was nothing to change** — recorded as a checked fact, not an unexamined one.

**Nothing was re-litigated.** All twelve confirmed claims are untouched; the sweep did not
re-run and **zero research requests were issued this round**, so every sweep figure is
byte-identical across three verification rounds: floor **2.276 s / 57 gaps**, portability
**15 of 15**, bodies **9 identical / 6 differing**, clinic-vs-support **15 of 15**,
**0 of 19** vs **19 of 19**.

## Requests used

- [x] GET only, except OPTIONS with an empty body to find POST-only routes, and the two pinned POSTs in `04-deep-surface.hurl` (public client_ids, asserted as 403 failures) — no other POST, no token exchange, no authentication attempted. **This pass issued no POST and no OPTIONS at all.** The 52 requests the pinned suite issued across four runs are the suite's own, under `AGENTS.md` §11, and are recorded in the ledger with `kind: gate-suite`.
- [x] Slept ≥2s between requests to the same host — `sleep 2.5` **inside** the shared per-host `flock`. **Measured `t_sent` floor 2.276 s over 57 same-host gaps, 1 sub-floor reading, no cause asserted.** The 52 gate-suite rows are excluded from that figure: their `t_sent` is a shim's pre-exec stamp, not a stamp taken inside a lock.
- [x] Stated cap respected: **113 of a 113 cap**, and the accounting is now separable.
  - **The sweep is 61 requests against the 85 the claim planned under — 24 never spent.**
  - **The other 52 are the repository's own gate**: `research-gate.sh` runs
    `05-public-config.check.sh`, which issues **13 real vendor requests per run**, and it was
    run four times before this round. 61 + 52 = 113, and `wc -l results.jsonl` = 113.
  - **Gate run 5 (this round) was deliberately NOT absorbed.** `gate.sh` gained an
    `L2_ABSORB=0` mode: the run happens, its request record is **committed** at
    `gate-curllog-not-absorbed.jsonl`, and `results.jsonl` stays at 113. **Honest total vendor
    traffic: 61 + 13 × 5 = 126**, of which 113 are in `results.jsonl` and 13 in the side file.
    Nothing unaccounted; nothing dropped to make a number fit.

  **A process failure, recorded as one rather than smoothed over.** The lane rule allows **one**
  bounded cap revision and states that *a second is a stop-and-report, not a decision*. This
  pass took **three** and did not stop. The log records it as a failure of **process** — not of
  arithmetic and not of method: the sweep never exceeded its budget, every revision was
  declared at the time, and no ledger row was ever deleted or edited to make one fit. The
  superseded wording of all three revision paragraphs is preserved verbatim in the log's
  appended `## Correction (2026-10-17) §A`, because editing them away would destroy the only
  evidence that three were taken.

  **The method observation, recorded and not acted on:** **a research cap inflated by
  CI-mandated gate traffic is not measuring research.** Whether gate traffic belongs inside a
  claim's cap or outside it is a **maintainer decision** — `AGENTS.md` §11 sets what may be
  re-run and forbids extending it, and `docs/09` §4's rule that a research pass must not edit
  the gate's own patterns in the PR the gate passed applies with equal force to the gate's
  request budget. **So: recorded as an observation, no rule changed, no gate touched.**

## The rules

- [x] No credential, session value, or patient identifier anywhere in the diff — `redact.py` applied the gate's **own** pattern list from `scripts/scrub-patterns.txt` to every committed body, and `REDACTIONS.md` records each substitution. The key's *shape* is recorded; the value is not.
- [x] Any internal hostname redacted to `<service>.<internal>` — none appears; this pass touched no Medtronic host outside the five already named in this repository.
- [x] Corrections and retractions in the sources are preserved, not smoothed over — `docs/10`'s row 51 keeps its superseded wording verbatim inside the cell; `docs/07` keeps area A's inference and adds the measured result beside it.
- [x] Any claim the regression suite pins has been updated in this PR, and `./scripts/research-gate.sh` still exits 0 — **no pin moved**; the suite ran green twice at `85 passed, 0 failed`.

## Gate

```bash
./scripts/research-gate.sh        # must exit 0 — CI runs the same script
```

```
research-gate.sh exit: 0
GATE PASS — safe to open a PR.
  ok  85 passed, 0 failed
```

## If this changes what a newcomer needs to know first

- [ ] README.md updated — the map's claims are unchanged; this refines one row's reading rather than a headline.
- [ ] docs/00-summary-the-map.md updated — likewise unchanged; `docs/07` and `docs/10` carry the result.

## Downstream consumer impact

- [x] No pinned consumer value affected — `carelink-bridge` pins the discovery pin, `BLE_API_VERSIONS`, the family vocabulary and the error taxonomy. None of the four moved. The suite the bridge runs before a release (`npm run drift:check`) is `05-public-config`, which reports **85 passed, 0 failed**.
- [ ] A pinned value moved — none did.

---

<details>
<summary>Notes for the reviewer</summary>

**Why this PR corrects a row before probing it.** `docs/10` §1 asked the next pass to issue
15 `GET`s that `HCP-CONFIG-SCHEMA.md` §10 says were already issued — §10 is *titled* "Do not
re-run" — and said `docs/07` publishes no per-key verdict when `docs/07:112-124` publishes
exactly that. Both halves were refuted against source before the first request, the
correction landed as its own commit, and the row was re-scoped to the unstated half.

**The two traps this pass was built around.** On this host family the catch-all *is* the
entry document, so a document path cannot detect a deployment — only a content-hashed chunk
can, and every one of the four corpus controls discriminates on `content-type` + size +
sha256 together. And `plan.py` **refuses to write `plan.json` if any digest fails to
reproduce**, so the stop condition is mechanical rather than a promise.

**Every candidate is derived.** No key was typed from memory. Each host's 15 candidates were
extracted offline from that host's own bundle route table, and `plan.md` carries the
per-candidate reasoning — written **before** the first request of batch 2.

**One gap this pass created and closed.** `logbook.supported.entry.types` was spent as the
header-absent control, which left its *headered* verdict unmeasured on all three hosts — a
14-of-15 claim. Three requests bought the cell. A first attempt at those three carried a
doubled slash; those rows are left on the ledger uncorrected and counted, and the finding is
that the route normalises a doubled slash rather than 404ing.

**`docs/07:112-124` re-checked at head** — the citation in `docs/10`'s row 51 still
resolves. Line 112 is still *"With the header, **13 of the 15 bundle-declared `public/*`
keys return JSON**…"* and 124 is still the `pow.nutrino.cc.{broker,metadata}` row. **This
PR's own edit to `docs/07` has two hunks, at `@@ -118` and `@@ -151`. The first rewrites
line **121**, inside the cited range, but **1-for-1 and without adding or removing a line**,
so it cannot shift `112-124`; the second is the +69-line block at `:151`, well below it. That
is the check: the range's contents are unchanged and its line numbers are unchanged, which is
what "still resolves" requires. `docs/07:149` and `docs/07:247-262`, the other two
ranges row 51 cites, also still resolve. One stale internal reference *was* found and fixed:
the rename `AA` → `AB` had left the new area's own body saying "So **AA** is not 'do they
exist'" twice.

**Shared surface — verified as this PR stands, and the exact lines that will conflict.**
Heading count `1` (`### AB.`), Closed-table rows `26`, live prose sentence **"1 open plus 26
closed"**, `config.yml` `about: 1 open areas` — all four agree, and
`scripts/research-checks.py` `check_prose_counts` passes on the numbers as they stand. **If
#148 merges first, exactly two hunks conflict and nothing else:**
1. `docs/11` lines 2793–2795 — the sentence **"0 open plus 26 closed"** → "1 open plus 26
   closed", and the `stand today;` line both branches rewrite.
2. `.github/ISSUE_TEMPLATE/config.yml` lines 9–16 — the 4-line explanatory comment and
   `about: 0 open areas;` → `about: 1 open areas;`.

**This is no longer a forecast — #148 has merged (`98766df`), and #150 after it.** `main`
carried `### AA.` and `### AC.`; this branch carries `### AB.`. **Neither side's number was
inherited — both were measured away.** On the merged tree the page measures
**3 open (`AA`, `AB`, `AC`) + 26 Closed-table rows**, and `check_prose_counts` /
`check_numbers` pass on that figure.

**Resolution, recorded rather than performed silently.** `origin/main` merged at
`015689e`; both predicted surfaces conflicted and nothing else did.

| Surface | This branch said | `origin/main` said | Merged text keeps |
|---|---|---|---|
| `docs/11:3006` (live count sentence) | "**1 open plus 26 closed** stand today (minted 2026-10-17 by lane l2: **AB**, the direct `/hcp/configuration/*` endpoints)" | "**2 open plus 26 closed** stand today (`AA`, `AC`)" | **3 open plus 26 closed**, open ids `(AA, AB, AC)` — both sides' id lists kept, both sides' prose dropped as undercounts |
| `.github/ISSUE_TEMPLATE/config.yml:11-16` (comment + `about:`) | `# 1 … AB minted 2026-10-17 by lane l2 (1 open + 26 closed)` / `about: 1 open areas; every A–Z area is closed` | `# 2 … A–Z all closed (2 open — AA, AC — + 26 closed)` / `about: 2 open areas (AA, AC) — …` | `# 3 … (3 open — AA, AB, AC — + 26 closed)` / `about: 3 open areas (AA, AB, AC) — …` |

Both sides agreed on **26 closed**, and the merged tree measures 26, so nothing was lost on
that half. Both sides were wrong on **open**, each by one, and in opposite directions — which
is why neither figure was inherited. The count is arithmetic over the page, not an editorial
choice: `python3 scripts/research-checks.py` reads `^### [A-Z]{1,2}\. ` headings (3: `AA`,
`AB`, `AC`) and `^\| [A-Z]{1,2} — ` rows after `## Closed areas` (26; `S6` is outside the
pattern by design and is given separately).

**CI could not run on this commit, and §E is why.** No `research-gate` check has been reported
for this branch since `b8beadc`; the other three lanes ran normally throughout, so it is not an
outage. Tested rather than assumed: an **empty commit with a fresh push** produced **no run**.
`research-gate.yml` triggers on `pull_request`, which GitHub evaluates against the PR's **merge
ref**, and a merge ref cannot be computed for a conflicting PR — so the workflow is never
dispatched. **Local gate at this exact tree: `GATE PASS`, exit 0, `CAP_STATE=ok`, suite
`85 passed, 0 failed`, leak scan 10/10, all citations resolve.** Same script CI runs; **not a
substitute for the CI check**, which must run against the merged tree §E has to unblock.
Recorded in `## Correction (2026-10-17) §F`. **Superseded:** the conflict above is now
resolved on this branch, so a merge ref exists and `pull_request` dispatches — the `gate` check
runs against the merged tree for the first time on this branch. The historical record above is
kept as written.

</details>

<details>
<summary>Diagrams checklist</summary>

- [x] Mermaid only (GitHub renders it natively) — none added; this pass produces tables, not topology.
- [x] Every branch is labelled — n/a, no diagram.
- [x] One diagram answers one question — n/a.

</details>