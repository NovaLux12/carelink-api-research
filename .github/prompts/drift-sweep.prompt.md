---
name: drift-sweep
description: Re-run the pinned assertion suite and report any drift as a correction-ready finding
argument-hint: [optional: one suite name]
---

You are running the drift sweep on
https://github.com/NovaLux12/carelink-api-research. The pinned assertions are
how this repo notices that the vendor surface moved. (A scheduled job does this
weekly; this prompt is the manual version, or the pass to run when it files a
drift issue.)

Read first: AGENTS.md · CONTRIBUTING-research.md ·
docs/09-methodology-and-oracles.md · regression/hurl/ in full, including
05-public-config.check.sh's header.

1. `cd regression/hurl && DELAY_MS=2000 ./run.sh` — read the exit code and the
   full output, not just the summary line. Exit 0 = no drift.
2. For every failure, capture: suite, assertion label, expected, actual, and the
   response head that produced the actual.
3. **Establish whether the failure is drift or a broken assertion.** Re-probe the
   failing cell with controls. A suite that fails because of a proxy, a gzip
   mishandling, or a wrong expected value is not vendor drift; on
   `carelink.minimed.eu` gzip is sent unconditionally and hurl only decodes what
   it asked for, which is why the config suite is a shell script.
4. Write the result as a correction-ready finding: raw pass →
   `findings-log/<date>-drift-sweep/`; synthesised → the affected `docs/` page,
   citing the log; and if a pinned value changed, **update the assertion and the
   prose in the same change**. The suite has caught a wrong prose hash before by
   being right when the note was wrong.
5. If nothing drifted, say so, with the exit code and the date. A clean sweep is
   a result.
6. **If the drift moved a value
   [NovaLux12/carelink-bridge](https://github.com/NovaLux12/carelink-bridge)
   pins, the finding is not finished until the consumer knows.** Label the issue
   `downstream-bridge`, name the pinned constant that moved (discovery
   app-version pin, `BLE_API_VERSIONS`, device family vocabulary, error-class
   taxonomy), and say that the bridge runs this suite before a release — so drift
   here can reach their release checklist. Do not close a `downstream-bridge`
   issue until a bridge issue or PR is linked.

Stop when every failing assertion is either explained as drift (with evidence)
or explained as an artefact of the harness (with the control that proves it). Do
not open a PR that changes a claim the suite pins without updating the suite.

Final output: the `run.sh` exit code and timestamp · a table of assertion |
expected | actual | verdict (drift | harness artefact | unknown) · what would
settle anything unknown · paths created or changed · the
`./scripts/research-gate.sh` exit code.