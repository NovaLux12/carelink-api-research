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

Three defects in **this pass's own tooling** are on the record rather than smoothed over —
a lost ledger batch, a `%3N` timestamp bug, and a body-in-a-status-field bug. See
`FINDINGS.md` §2. No ledger row was deleted, reordered or edited to absorb any of them.

## Requests used

- [x] GET only, except OPTIONS with an empty body to find POST-only routes, and the two pinned POSTs in `04-deep-surface.hurl` (public client_ids, asserted as 403 failures) — no other POST, no token exchange, no authentication attempted. **This pass issued no POST and no OPTIONS at all.** The 26 requests the pinned suite issued are the suite's own, under `AGENTS.md` §11, and are recorded in the ledger with `kind: gate-suite`.
- [x] Slept ≥2s between requests to the same host — `sleep 2.5` **inside** the shared per-host `flock`. **Measured `t_sent` floor 2.276 s over 57 same-host gaps, 1 sub-floor reading, no cause asserted.** The 26 gate-suite rows are excluded from that figure: their `t_sent` is a shim's pre-exec stamp, not a stamp taken inside a lock.
- [x] Stated cap respected: **87 requests of a 90 cap** — and this is the **one bounded cap revision** claim #144 allows, taken after the fact with the reason in the log head. The claim's arithmetic budgeted the sweep (≤80) and **not** the `05-public-config.check.sh` traffic `./scripts/research-gate.sh` issues on every run; the sweep landed at 61 and the gate ran twice (13 + 13). **A third run was refused** — 13 more requests for a third reading of a suite already green twice. `wc -l results.jsonl` = 87 = the accounting number.

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

**Shared-surface note.** This PR mints successor area **`AB`**, not `AA` — lane l3 minted
`AA` in PR #148 on the same day, and a two-letter id is only a namespace if allocated once.
Both branches mint exactly one area and both edit the same live count sentence in the
"Why there is no area AA" amendment: **that one line is the merge conflict the queue must
reconcile**, and the headings do not clash.

</details>

<details>
<summary>Diagrams checklist</summary>

- [x] Mermaid only (GitHub renders it natively) — none added; this pass produces tables, not topology.
- [x] Every branch is labelled — n/a, no diagram.
- [x] One diagram answers one question — n/a.

</details>