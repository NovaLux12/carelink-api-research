#!/usr/bin/env python3
"""analyse.py — area F post-sweep derivation.

Runs INSIDE probe.sh, while the transient bodies are still on disk, and writes the
committed artefacts. This is the only moment at which cell-digests.tsv is writable
at all (area E's verifier round-2 addendum): the bodies are deleted the moment the
sweep ends, and a digest cannot be computed retrospectively.

Deliverables produced here:
  timeline-keys.tsv   the full key set of personal.patient.timeline.config, per
                      deployment, with each member's resolved jq type
  cell-digests.tsv    host key seq norm sha256(canonical(parsed value))
                      sha256(canonical(resolved bulk subtree))  — DIGESTS ONLY
  derived.json        every derived fact this pass measured, machine-readable

TWO TRAPS THIS FILE EXISTS TO AVOID
----------------------------------
1. AGENTS.md section 6 item 3 — a hash comparison over a lookup that silently
   returns null manufactures consensus. Two different values hashing to the same
   digest once looked like agreement here. So every resolve is TYPE-ASSERTED
   before it is hashed, and a resolve that returns None writes NULLRESOLVED
   rather than the digest of anything. **The NULL check is the whole live guard**,
   and it is deliberately the only one: an earlier version of this file also
   compared against the all-zero digest (e3b0c442..., sha256 of the empty string),
   advertising a belt-and-braces check that **cannot fire**, because `canon()`
   always emits at least one character for a non-None value and the NULL branch
   above has already continued. A guard that cannot fail is worse than no guard —
   it reads as protection and is not — so it was removed rather than kept as
   reassurance. This was caught in verification on 2026-10-13.

2. personal.patient.timeline.config is a LITERAL DOTTED KEY, not a nested path.
   The 69 published names are literal strings — 68 of 69 are dotted, and exactly
   one (captcha) is a real nested object. A walker that splits every name on "."
   resolves this key to nothing and would report agreement against nothing. This
   file resolves the literal key AND records what the split-walk returns, so the
   difference is on the record rather than in someone's head.

Usage: analyse.py <TMPD> <OUT>
"""
import hashlib
import json
import os
import sys

# NOTE: an EMPTY_SHA constant and an all-zero-digest guard were removed here on
# 2026-10-13. The guard sat AFTER the None check, which `continue`s, so it was
# unreachable: canon() never yields "" for a non-None value. An unreachable guard
# reads as protection and is not protection, so it is gone rather than kept.

HOSTS = [
    ("carelink.minimed.eu", "eu"),
    ("carelink.minimed.com", "com"),
    ("carelink-trials.minimed.com", "trials"),
]

CFG_KEY = "personal.patient.timeline.config"
HOST_KEY = "personal.patient.timeline.host"


def load_ledger(path):
    """seq -> ledger row. The ledger is the authority on STATUS; a body is only
    needed to hash a VALUE. A 404 with a 0-byte body is not 'unparseable' — it is
    absent, and saying so is the difference between a verdict and a shrug."""
    led = {}
    if not os.path.exists(path):
        return led
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                r = json.loads(line)
                led[r["seq"]] = r
    return led


def perkey_verdict(ledger_row):
    """What the ledger alone settles about a per-key response, with no body."""
    if ledger_row is None:
        return "NO_LEDGER_ROW"
    code = ledger_row.get("code")
    nbytes = ledger_row.get("bytes")
    if code != 200:
        return "ABSENT_HTTP_%s_%dB_NO_ENVELOPE" % (code, nbytes)
    if nbytes == 0:
        return "HTTP_200_BUT_EMPTY_BODY"
    return None


def canon(obj):
    """Canonical JSON: sorted keys, no insignificant whitespace."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha(obj):
    return hashlib.sha256(canon(obj).encode("utf-8")).hexdigest()


def load(path):
    """Load a JSON body, or None if it is absent / unparseable. Never raises."""
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return None


def jtype(v):
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "boolean"
    if isinstance(v, dict):
        return "object"
    if isinstance(v, list):
        return "array"
    if isinstance(v, str):
        return "string"
    if isinstance(v, (int, float)):
        return "number"
    return type(v).__name__


def split_walk(doc, dotted):
    """The WRONG resolution method, run deliberately so its answer is on record.

    Returns (resolved, type). For a literal dotted key this resolves to None.
    """
    cur = doc
    for seg in dotted.split("."):
        if not isinstance(cur, dict) or seg not in cur:
            return None, "null"
        cur = cur[seg]
    return cur, jtype(cur)


def main():
    tmpd, out = sys.argv[1], sys.argv[2]
    LEDGER = load_ledger(os.path.join(out, "results.jsonl"))

    derived = {
        "deliverable_1_timeline_config_key_set": {},
        "deliverable_2_two_timeline_host_keys": {},
        "deliverable_3_dedicated_routes": {},
        "deliverable_4_cell_digests": [],
        "split_walk_control": {},
    }

    # Column 8 is sha256 of canon(member) -- the CANONICAL-JSON encoding, so a
    # string member hashes with its quotes. derived.json's member_shape.sha256 for a
    # string is sha256 of the RAW string, without quotes. Two conventions, two files,
    # one sentence apart; stated here because a reader comparing the two digests
    # would otherwise conclude one of them is wrong.
    keyrows = ["host\tshort\tkey\tpresent\tresolved_type\tmember\tmember_type\tmember_canonical_sha256"]
    drows = ["host\tkey\tseq\tnorm\tsha256_canonical_parsed_value\tsha256_canonical_resolved_bulk_subtree\tequality"]
    routes = []

    for host, short in HOSTS:
        bulk = load(os.path.join(tmpd, "bulk-%s.json" % host))
        if bulk is None:
            derived["deliverable_1_timeline_config_key_set"][host] = {"bulk_document": "UNPARSEABLE_OR_MISSING"}
            continue

        # ---- DELIVERABLE 1 + 2, read off the bulk document ------------------
        present = isinstance(bulk, dict) and CFG_KEY in bulk
        val = bulk.get(CFG_KEY) if isinstance(bulk, dict) else None
        vtype = jtype(val)

        entry = {
            "key_present": present,
            "resolved_type": vtype,
            "top_level_key_count": len(bulk),
            "member_count": (len(val) if isinstance(val, dict) else None),
        }

        # TRAP 2 control — what the split-walk returns for the same name.
        sw_val, sw_type = split_walk(bulk, CFG_KEY)
        derived["split_walk_control"][host] = {
            "dotted_name": CFG_KEY,
            "literal_key_resolves": present,
            "literal_key_type": vtype,
            "split_on_dot_resolves": sw_val is not None,
            "split_on_dot_type": sw_type,
            "note": "68 of the 69 published names are LITERAL dotted strings; "
                    "only `captcha` is a real nested object. Splitting on '.' "
                    "resolves nothing here.",
        }

        if present and isinstance(val, dict):
            members = sorted(val.keys())
            entry["members_sorted"] = members
            entry["members_joined"] = ",".join(members)
            entry["member_types"] = {m: jtype(val[m]) for m in members}
            # Shape of each member, NEVER a raw credential-shaped value.
            for m in members:
                mv = val[m]
                if isinstance(mv, str):
                    entry.setdefault("member_shape", {})[m] = {
                        "type": "string",
                        "length": len(mv),
                        "sha256": hashlib.sha256(mv.encode("utf-8")).hexdigest(),
                        "is_https": mv.startswith("https://"),
                        "scheme": mv.split(":", 1)[0] if ":" in mv else None,
                    }
                else:
                    entry.setdefault("member_shape", {})[m] = {
                        "type": jtype(mv),
                        "value": mv if not isinstance(mv, (dict, list)) else None,
                        "sha256": sha(mv),
                    }
        derived["deliverable_1_timeline_config_key_set"][host] = entry

        # The second timeline-host key. Two separate questions:
        #  (a) is there a top-level key literally named personal.patient.timeline.host?
        #  (b) does personal.patient.timeline.config carry a `host` member?
        cfg_has_host_member = isinstance(val, dict) and "host" in val
        derived["deliverable_2_two_timeline_host_keys"][host] = {
            "bundle_named_top_level_key": HOST_KEY,
            "bundle_named_key_present_in_bulk": isinstance(bulk, dict) and HOST_KEY in bulk,
            "published_config_carries_host_member": cfg_has_host_member,
            "published_key_present_in_bulk": present,
            # A former key, host_member_equals_top_level_key, was written here as a
            # literal False and removed on 2026-10-13: it compared nothing and read
            # like a measurement. The two questions it implied are already answered
            # by the two keys above -- the bundle-named key is absent from the
            # document, and the document publishes its host as a member of the
            # config object. No claim cited it.
        }

        for m in (members if present and isinstance(val, dict) else []):
            keyrows.append(
                "\t".join([host, short, CFG_KEY, str(present).lower(), vtype, m,
                           jtype(val[m]),
                           hashlib.sha256(canon(val[m]).encode("utf-8")).hexdigest()])
            )

        # ---- DELIVERABLE 4 — the per-cell digests ---------------------------
        for kind, tagname in (("pkey-cfg", "005-pkey-timeline-config"),
                              ("pkey-host", "006-pkey-timeline-host")):
            name = CFG_KEY if kind == "pkey-cfg" else HOST_KEY
            # The ledger row for THIS host's per-key request, matched by tag.
            lrow = None
            for r in LEDGER.values():
                if r.get("tag") == tagname and r.get("host") == host:
                    lrow = r
                    break
            lseq = lrow["seq"] if lrow else ""
            # STATUS comes from the ledger first, and needs no body at all. A
            # 0-byte 404 has no envelope to unwrap; calling it 'unparseable'
            # would report a harness limitation as if it were a vendor fact.
            stat = perkey_verdict(lrow)
            pk = load(os.path.join(tmpd, "%s-%s.json" % (kind, host)))
            if pk is None:
                derived["deliverable_4_cell_digests"].append(
                    {"host": host, "key": name, "seq": lseq, "verdict": stat or
                     "PER_KEY_BODY_UNPARSEABLE_OR_MISSING",
                     "http_code": lrow.get("code") if lrow else None,
                     "bytes": lrow.get("bytes") if lrow else None})
                drows.append("\t".join([host, name, str(lseq), "no-body-to-unwrap",
                                         "ABSENT" if stat else "UNPARSEABLE", "", "NOT_COMPARED"]))
                continue
            # The per-key envelope is {"value": "<the value, serialised as a STRING>"}
            # for objects/arrays. Assert the envelope shape before trusting .value.
            if not (isinstance(pk, dict) and "value" in pk):
                derived["deliverable_4_cell_digests"].append(
                    {"host": host, "key": name, "verdict": "ENVELOPE_SHAPE_UNEXPECTED",
                     "members": sorted(pk.keys()) if isinstance(pk, dict) else None})
                drows.append("\t".join([host, name, "", "unexpected-envelope", "", "", "NOT_COMPARED"]))
                continue
            raw = pk["value"]
            norm = "identity"
            parsed = raw
            if isinstance(raw, str):
                try:
                    parsed = json.loads(raw)
                    norm = "envelope-fromjson"
                except Exception:
                    parsed = raw
                    norm = "identity"
            # TYPE ASSERTION BEFORE HASHING — the whole point of docs/09 section 5 item 3.
            parsed_type = jtype(parsed)
            bulk_side = bulk.get(name) if isinstance(bulk, dict) else None
            bulk_type = jtype(bulk_side)
            if parsed is None or bulk_side is None:
                drows.append("\t".join([host, name, str(lseq), norm, "NULLRESOLVED", "NULLRESOLVED", "NOT_COMPARED"]))
                derived["deliverable_4_cell_digests"].append(
                    {"host": host, "key": name, "verdict": "NULLRESOLVED",
                     "parsed_type": parsed_type, "bulk_type": bulk_type,
                     "note": "a resolve returned null; hashing it would manufacture consensus"})
                continue
            d_parsed = sha(parsed)
            d_bulk = sha(bulk_side)
            eq = (d_parsed == d_bulk)
            drows.append("\t".join([host, name, str(lseq), norm, d_parsed, d_bulk, str(eq).lower()]))
            rec = {"host": host, "key": name, "norm": norm, "parsed_type": parsed_type,
                   "bulk_type": bulk_type, "sha256_parsed": d_parsed, "sha256_bulk": d_bulk,
                   "equal": eq}
            if isinstance(parsed, dict):
                rec["members_sorted"] = sorted(parsed.keys())
            derived["deliverable_4_cell_digests"].append(rec)

    # ---- DELIVERABLE 3 — the dedicated routes -------------------------------
    # Verdicts are read from results.jsonl (the ledger), not re-requested.
    led = os.path.join(out, "results.jsonl")
    with open(led, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if "dedicated" in r["tag"] or "control" in r["tag"]:
                routes.append({
                    "seq": r["seq"], "host": r["host"], "tag": r["tag"],
                    "url": r["url"].replace("https://" + r["host"], ""),
                    "code": r["code"], "content_type": r["content_type"],
                    "bytes": r["bytes"], "sha256": r["sha256"],
                })
    derived["deliverable_3_dedicated_routes"] = routes

    with open(os.path.join(out, "timeline-keys.tsv"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(keyrows) + "\n")
    with open(os.path.join(out, "cell-digests.tsv"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(drows) + "\n")
    with open(os.path.join(out, "derived.json"), "w", encoding="utf-8") as fh:
        json.dump(derived, fh, indent=2, sort_keys=True)
        fh.write("\n")

    print("--- derived ---")
    print(json.dumps(derived["deliverable_1_timeline_config_key_set"], indent=2, sort_keys=True))
    print(json.dumps(derived["deliverable_2_two_timeline_host_keys"], indent=2, sort_keys=True))
    print(json.dumps(derived["split_walk_control"], indent=2, sort_keys=True))
    print(json.dumps(derived["deliverable_4_cell_digests"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()