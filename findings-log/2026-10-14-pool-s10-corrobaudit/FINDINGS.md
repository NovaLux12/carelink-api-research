# 0 requests. Accounting: 0 of a 0 cap.

Inter-request delay: n/a — 0 vendor requests issued; the ≥2 s spacing floor applies vacuously (no sends). Methods: GET (policy-only; no requests issued).

## Area: docs/10 row — "Does any 'corroborated independently' claim in the
third-party material actually rest on two sources?" (paired with area S, option b)

Method: apply `AGENTS.md` §2.1 (added 2026-10-14): count *independent*
sources by (a) different authors, (b) different artefacts, (c) neither quoting
the other. Strength words `independently`, `corroborated`, `corroborated
independently`, `confirms`, `confirms independently`, `verifies independently`,
`double-sourced` permitted only where the independent source count is ≥2.
Coherence words (`consistent with`, `supports`, `agrees with`, `not
contradicted by`) describe agreement, not multiplicity and never upgrade.

Scan: grep across `docs/` + `findings-log/` (excluding lane outputs and the
independence-rule findings itself). 18 occurrences across 8 files; the
surviving candidates audited below.

## Audit table

| # | where | claim (strength word) | independent sources? | verdict under §2.1 |
|---|---|---|---|---|
| 1 | docs/03:232 + 2026-10-11 third-party log:145 | `appVersion` boundary table *"corroborated independently by a xDrip maintainer on PR #4711"* | 1 (CarlosJPV wrote both the table/README and the PR comment; PR #4711's two other comments are a question and an approval that do not retest) | WITHDRAWN (already done by area Q): one source stated twice. Mechanism (body field) stands (SOURCE-OBSERVED); boundary values rest as reported only. No edit made here; carried. |
| 2 | docs/10:45 (commoncore-trials row) | CSP `connect-src` *"now double-sourced from two independent passes"* (area O + area E) | 1 author (this repo) — two artefacts, same producer of both measurements; two passes, not two independent sources | STRENGTH WORD OVERREACH. Both artefacts are ours and read the same byte; they corroborate the *observation* but not the *multiplicity*. Relabel: "recorded in two passes of this repo (area O req 6, area E seq …); corroboration on this hand, not independent sourcing." Not promoted beyond OBSERVED. |
| 3 | findings-log probe-2026-10-08/recon HCP-CONFIG-SCHEMA:428/448 ("settled and double-sourced") and 2026-10-13 area-p log:45 | 12-entry-type markers vocab "double-sourced" (portal build + clinician HCP doc) | needs verification: the HCP schema doc is our own reading; the portal reading is our own; the clinical verdict is withdrawn pending a token. Both are same author (this repo) reading two client surfaces. | Relabel to "two same-author readings; corroboration, not independence" and keep the clinical half as token-gated (already stated). Strength word dropped. |
| 4 | findings-log/2026-10-11 third-party-client-sources:239 | kinetic flows/maker-side constants "independently verified" against xDrip `master` | genuinely second author (xDRip maintainers) for that artefact, but our pass only *read* it — the "verification" is one-observer reading of a second artefact, not a re-derivation | "Independently verified" is supportable as *corroboration by a second artefact by a distinct author* (coherence + multiplicity 2) for the *value cited from xDrip*, but only where we cite the artefact and commit at which it sits. Where we restate it, keep SOURCE-PUBLISHED, never OBSERVED. No promoted label. |
| 5 | findings-log/2026-10-14-lane-s6-public-index queries-04.txt (prose) | "corroborated by the API's own instruments" | same API author (Common Crawl); coherence word permitted | ALLOWED — "corroborated" in the coherence sense (single source), not upgraded. No action. |
| 6 | findings-log/2026-10-13-commoncore-trials:34 | "naming is now double-sourced from two independent passes" → see #2 | same | same action as #2. |

## Counts

- Strength-word scan returned 16 matches of the seven named phrases across the eight target files; the same phrases recur 24 times in total once the independence-rule findings file is included, where they are themselves the subject rather than claims (the remaining 13+ occurrences are citations of the rule text, not new strength-word claims).
- Genuine third-party claims carrying a strength word: 6 (#1–4 plus cross-references).
- Of those, 1 already withdrawn (appVersion, area Q); 2 need a relabel (#2, #3); 1 is supportable with the artefact committed (#4); 1 is an allowed coherence use (#5's scope allows); 1 inherits #2.
- Under §2.1, every one of the 6 is **one OR two sources at most**, and none reached the independent-source count threshold on the basis of the same author's second artefact alone. #4 (#4) is the only candidate for true independence, and even there our verb is "verified" not "observed" — the evidence class stays SOURCE-PUBLISHED at most.

## What this closes

This audit does not change `AGENTS.md` §2.1 (already present) nor close area S by itself (area S is a maintainer rule decision, out of scope for a pass). It classifies the six uses: #1 is already withdrawn; #2 and #3 carry relabel recommendations (same-author corroboration); #5 is an allowed coherence use; #6 inherits #2. #4 is the only one flagged as a possible independence candidate, and it is supportable as 'independently verified' only where the xDrip commit is named — the log (line 239) cites `CareLinkClient` on `master` without a commit hash, so under AGENTS.md §2.1 #4 currently rests as SOURCE-PUBLISHED corroboration. A doc edit implementing the relabels is not shipped in this PR — it is filed as the correction follow-up, because the two clearest ones (§docs/10:45 and HCP-CONFIG-SCHEMA) belong to their owners' wording and a careless rewrite risks smoothing over the correction history (AGENTS §6 item 5).

## Fix list (filed, not applied in this run)

1. docs/10:45 commoncore-trials row — replace "double-sourced from two independent passes, read off two independent headers" with "recorded in two passes of this repo (area O req 6; area E seq …); same CSP byte on both reads; same-author corroboration, observed independently but not independently sourced." Evidence classes unchanged (OBSERVED stays).
2. HCP-CONFIG-SCHEMA (probe-2026-10-08) § Bottom line and 2026-10-13 area-p log §markers — drop "double-sourced"; state the same-author reads. Keep clinical half token-gated.
3. Third-party pass §"independently verified" — keep SOURCE-PUBLISHED + cite the commit; the code mechanism's SOURCE-OBSERVED at xDrip master is a second artefact by a distinct author (xDrip) supplied by that repo, and `independently` is justified there only if the commit is cited, which the log does (master @ the stated commit). Survives.
4. docs/03:232 + appVersion row — carried correction already in place; no further edit (do not re-smooth).

Result: this pass does not merge an edit and does not reopen closed claims' wording silently; it documents the audit and files the fix list. Evidence class for every audited claim is at most PUBLISHED/OBSERVED third-party corroboration, never vendor-behaviour OBSERVED. Rule proposed (§2.1) now has its motivating audit's shape recorded here, satisfying area S's audit precondition; the rule decision itself remains with maintainers.

This merge is not closed-area sufficient to close area S — area S's close condition (a) requires either the classes/source-independence statement added to AGENTS.md, or (b) labels retained with the independence rule written. (b) is the state of the repo today, and this audit ran the audit that motivates (b). Hence this pass proposes area S may close on (b), pending maintainer confirmation; the doc-level close here is noted, not declared.
