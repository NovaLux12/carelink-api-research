#!/usr/bin/env python3
"""reader.py — area D. Per-key state + per-country internal-contradiction reader.

Issues ZERO requests. Reads the response bodies this pass captured and emits,
per country: a per-key state table (ABSENT / NULL / VALUED) and a verdict list.

WHY THIS FILE LOOKS THE WAY IT DOES
-----------------------------------
Two traps this repo has already paid for are designed out here, not documented
and left to the reader:

  1. docs/09 §4 — a country sweep once used jq's `//`, which conflates "key
     absent" with "value false", because `false // x` is `x`. Every lookup here
     returns an explicit three-state verdict: ABSENT (no such key), NULL (key
     present, value JSON null), VALUED (key present, non-null value, with its
     JSON type recorded).
  2. docs/09 §5.3 — a comparison once walked a dotted path with a single
     dict.get("a.b.c"), got None, and hashed None, so two different values
     produced one digest and looked like agreement. `resolve()` here walks the
     path ONE SEGMENT AT A TIME and asserts the container type at every step.
     If a segment is not a dict, the walk returns NOT-A-MAPPING — it never
     returns None for "could not resolve", so a lookup that fails to resolve is
     visibly different from a key whose value really is null.

RULE CLASSES
------------
CONTRADICTION — two keys (or two parts of one key) in the SAME document that
                 disagree by definition. No assumption about vendor intent.
FLAG-INFERRED — a rule that rests on an assumption. Reported, counted
                 separately, and never merged into the contradiction count.

Usage:  python3 reader.py <bodies-dir> <reference-keys.json> > verdicts.jsonl
"""

import hashlib
import json
import os
import re
import sys

# ---------------------------------------------------------------------------
# Reference vocabulary: the union of top-level key names across the three
# country documents captured on disk by the 2026-10-12 published-pointers pass.
# It is the READER's vocabulary, not a claim about today's responses; any key a
# live response carries that is not in here is reported as a vocabulary delta.
# ---------------------------------------------------------------------------
def load_reference(path):
    with open(path, encoding='utf-8') as fh:
        return json.load(fh)

REF = load_reference(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  'reference-keys.json'))

ABSENT = 'ABSENT'
NULL = 'NULL'
VALUED = 'VALUED'
NOT_A_MAPPING = 'NOT-A-MAPPING'


def resolve(doc, path):
    """Resolve a dotted path one segment at a time.

    Returns (state, value, json_type). `state` is one of ABSENT / NULL /
    VALUED / NOT-A-MAPPING. A path whose intermediate segment is not an object
    returns NOT-A-MAPPING and a None value — never a silent None.
    """
    segs = path.split('.')
    cur = doc
    for i, seg in enumerate(segs):
        if not isinstance(cur, dict):
            return NOT_A_MAPPING, None, type(cur).__name__
        if seg not in cur:
            # A partially-resolvable path is absent, and the reason is recorded.
            return ABSENT, None, 'object'
        cur = cur[seg]
    if cur is None:
        return NULL, None, 'null'
    return VALUED, cur, type(cur).__name__


def state_of(doc, path):
    """Three-state verdict only, for the per-key table."""
    st, _val, _t = resolve(doc, path)
    return st


def typed(doc, path, want):
    """VALUED and of type `want`, else None. Used before any comparison, so a
    comparison is never run over an unresolved or wrongly-typed lookup."""
    st, val, jt = resolve(doc, path)
    if st != VALUED:
        return None
    if want and jt != want:
        return None
    return val


# ---------------------------------------------------------------------------
# Contradiction rules. Each takes (doc, cc) and returns a list of dicts.
# ---------------------------------------------------------------------------
def r_glucose_units(doc, cc):
    out = []
    bg = typed(doc, 'bgUnits', 'str')
    gd = typed(doc, 'glucoseUnitsDefault', 'str')
    if bg is not None and gd is not None and bg != gd:
        out.append({'rule': 'glucose-unit disagreement',
                    'keys': ['bgUnits', 'glucoseUnitsDefault'],
                    'left': bg, 'right': gd,
                    'text': 'two keys in one document naming the same '
                            'quantity disagree'})
    return out


def r_carb_units(doc, cc):
    out = []
    a = typed(doc, 'carbDefaultUnit', 'str')
    b = typed(doc, 'carbohydrateUnitsDefault', 'str')
    if a is not None and b is not None and a != b:
        out.append({'rule': 'carbohydrate-unit disagreement',
                    'keys': ['carbDefaultUnit', 'carbohydrateUnitsDefault'],
                    'left': a, 'right': b,
                    'text': 'two keys in one document naming the same '
                            'quantity disagree'})
    return out


def r_exchanges_need_ratio(doc, cc):
    """EXCHANGES is a ratio: without carbExchangeRatioDefault a client cannot
    convert grams to exchanges at all, so the two keys together are incomplete."""
    out = []
    unit = typed(doc, 'carbDefaultUnit', 'str')
    if unit == 'EXCHANGES':
        st, val, jt = resolve(doc, 'carbExchangeRatioDefault')
        if st != VALUED or not isinstance(val, (int, float)):
            out.append({'rule': 'EXCHANGES without a conversion ratio',
                        'keys': ['carbDefaultUnit', 'carbExchangeRatioDefault'],
                        'left': unit,
                        'right': f'{st}:{jt}',
                        'text': 'the document selects exchange counting and '
                                'carries no numeric grams-per-exchange ratio'})
    return out


def r_default_language(doc, cc):
    out = []
    langs = typed(doc, 'languages', 'list')
    dl = typed(doc, 'defaultLanguage', 'str')
    if langs and dl is not None:
        codes = [l.get('code') for l in langs if isinstance(l, dict)]
        if dl not in codes:
            out.append({'rule': 'defaultLanguage not among languages',
                        'keys': ['defaultLanguage', 'languages[].code'],
                        'left': dl, 'right': ','.join(str(c) for c in codes),
                        'text': 'the document names a default language it does '
                                'not list'})
    return out


def r_country_names(doc, cc):
    out = []
    a = typed(doc, 'name', 'str')
    b = typed(doc, 'defaultCountryName', 'str')
    if a is not None and b is not None and a != b:
        out.append({'rule': 'name and defaultCountryName disagree',
                    'keys': ['name', 'defaultCountryName'],
                    'left': a, 'right': b,
                    'text': 'two keys in one document naming the same country '
                            'give different names'})
    return out


def r_region_media_host(doc, cc):
    """Region and media host name the same plane. Recorded invariant:
    US -> carelink.minimed.com, every other region -> carelink.minimed.eu
    (docs/04-configuration.md:371)."""
    out = []
    region = typed(doc, 'region', 'str')
    host = typed(doc, 'mediaHost', 'str')
    if region is not None and host is not None:
        want = '.com' if region == 'US' else '.eu'
        if not host.endswith(want):
            out.append({'rule': 'region and mediaHost disagree',
                        'keys': ['region', 'mediaHost'],
                        'left': region, 'right': host,
                        'text': f'region {region} but the media host is not a '
                                f'{want} host'})
    return out


def _endpoint_plane(url):
    """The host of a published endpoint URL, lowercased."""
    if not isinstance(url, str):
        return None
    m = re.match(r'^https?://([^/]+)/', url)
    return m.group(1).lower() if m else None


def r_region_cumulus_host(doc, cc):
    """Two keys in the SAME document publish the endpoint a client should talk
    to. If they name different markets, one document instructs the client to use
    two hosts.

    NOTE ON WHAT THIS DOES NOT CLAIM. A first version of this rule asserted
    that every endpoint host must match the region's TLD, and fired on US and PR
    (region US, ble endpoint clcloud.minimed.eu). That assertion is REFUTED by
    the repo's own record: `blePereodicDataEndpoint` is recorded as a CONSTANT
    at clcloud.minimed.eu across all 18 swept countries, US among them
    (docs/04-configuration.md, "Constant across all 18 countries" block — cite
    by the claim, not by a line number, because this file's own branch edits
    docs/04 and a line cite would silently rot; the underlying observation is
    findings-log/probe-2026-10-08/recon/CONFIG-NAMESPACE-DEEP.md:189). So the
    .eu value is a recorded constant, not a contradiction, and the rule as
    written would have manufactured a finding.
    What survives is the weaker and defensible statement below: the two endpoint
    keys disagree with EACH OTHER inside one document. No claim is made here
    about which of the two is right."""
    out = []
    mh = _endpoint_plane(typed(doc, 'mediaHost', 'str'))
    ble = _endpoint_plane(typed(doc, 'blePereodicDataEndpoint', 'str'))
    if mh and ble:
        mh_market = mh.rsplit('.', 1)[-1]
        ble_market = ble.rsplit('.', 1)[-1]
        if mh_market != ble_market:
            out.append({'rule': 'the two endpoint keys name different markets',
                        'keys': ['mediaHost', 'blePereodicDataEndpoint'],
                        'left': mh, 'right': ble,
                        'text': 'one document publishes two endpoints on two '
                                'different markets; which is authoritative is '
                                'NOT established here'})
    return out


def r_state_codes_prefix(doc, cc):
    """stateCodes is a list of <CC>-<SUBDIVISION>. Any element whose prefix is
    not the requested country is the document contradicting itself."""
    out = []
    codes = typed(doc, 'stateCodes', 'list')
    if codes:
        bad = [c for c in codes if not (isinstance(c, str) and c.startswith(cc + '-'))]
        if bad:
            out.append({'rule': 'stateCodes carry another country prefix',
                        'keys': ['stateCodes'],
                        'left': cc, 'right': ','.join(str(b) for b in bad[:5]),
                        'text': f'{len(bad)} subdivision code(s) are not '
                                f'prefixed {cc}-'})
    return out


def r_state_codes_vs_region(doc, cc):
    """Only the US half survives, and only as an asymmetry between the two
    US-region documents.

    A first version of this rule also fired on any non-US region carrying a
    subdivision list, and CA tripped it with 13 Canadian province codes
    (CA-ON, CA-QC, ...). That assertion is REFUTED by the live data: the key is
    named `stateCodes` but the values are subdivisions of whatever country was
    requested, and the prefix rule above already checks exactly that. The rule
    would have reported Canada's provinces as a vendor defect.

    What remains: US and PR both carry region "US", US carries 50 subdivision
    codes and PR carries none. That is a real asymmetry between two documents
    the same endpoint returns for the same region, and it is the only statement
    this pass makes about it — PR genuinely has no subdivisions of its own, so
    whether that is a fault or correct is NOT established."""
    out = []
    codes = typed(doc, 'stateCodes', 'list')
    region = typed(doc, 'region', 'str')
    if region == 'US' and not codes:
        st, _v, _t = resolve(doc, 'stateCodes')
        out.append({'rule': 'US region with no subdivision list',
                    'keys': ['region', 'stateCodes'],
                    'left': region, 'right': st,
                    'text': 'two documents share region US and only one '
                            'carries subdivisions; whether that is correct for '
                            'this country is NOT established'})
    return out


def r_time_fields(doc, cc):
    out = []
    tf = typed(doc, 'timeFormat', 'str')
    tu = typed(doc, 'timeUnitsDefault', 'str')
    if tf in ('HR_12', 'HR_24') and tu in ('12h', '24h'):
        if (tf == 'HR_12') != (tu == '12h'):
            out.append({'rule': 'timeFormat and timeUnitsDefault disagree',
                        'keys': ['timeFormat', 'timeUnitsDefault'],
                        'left': tf, 'right': tu,
                        'text': 'the hour clock and the hour unit disagree'})
    stf = typed(doc, 'shortTimeFormat', 'str')
    if tf in ('HR_12', 'HR_24') and stf:
        # Case-insensitive meridiem detection. Both observed spellings are in
        # the corpus: GB "h:mm a", US "h:mm A" — a case-sensitive pattern read
        # the US document as a 24-hour pattern and reported a contradiction
        # that does not exist. Found by the reader's offline self-test.
        has_meridiem = bool(re.search(r'(?i)(?<![a-z0-9])(a\.?m?\.?|p\.?m?\.?|tt)(?![a-z0-9])', stf))
        if tf == 'HR_12' and not has_meridiem:
            out.append({'rule': 'HR_12 with a pattern carrying no meridiem',
                        'keys': ['timeFormat', 'shortTimeFormat'],
                        'left': tf, 'right': stf,
                        'text': '12-hour clock, pattern carries no meridiem'})
        if tf == 'HR_24' and has_meridiem:
            out.append({'rule': 'HR_24 with a pattern carrying a meridiem',
                        'keys': ['timeFormat', 'shortTimeFormat'],
                        'left': tf, 'right': stf,
                        'text': '24-hour clock, pattern carries a meridiem'})
    return out


def _date_order(pattern):
    """Return the day/month token order of a date pattern, or None.
    'dd/MM/yyyy' and 'DD/MM/YYYY' -> 'DM'; 'MM-dd-yyyy' -> 'MD'.
    Casing matters only for M/m: uppercase M is the month, lowercase m is
    minutes, so "MM/dd/yyyy hh:mm" must not read its minutes as a month."""
    if not isinstance(pattern, str):
        return None
    order = []
    for t in re.findall(r'[dD]{1,4}|[mM]{1,4}', pattern):
        if t[0] in 'dD':
            order.append('D')
        elif t[0] == 'M':
            order.append('M')
        # lowercase m is minutes: contributes nothing to date order
    seq = [c for c in order if c in ('D', 'M')]
    if len(seq) < 2:
        return None
    return ''.join(seq)


def r_date_fields(doc, cc):
    """shortDateFormat and reportDateFormat.shortDatePattern are two spellings
    of the same date in one document. If they order day and month differently a
    client that reads one and renders the other shows the wrong date."""
    out = []
    s = typed(doc, 'shortDateFormat', 'str')
    st, rep, jt = resolve(doc, 'reportDateFormat.shortDatePattern')
    if s is not None and st == VALUED and isinstance(rep, str):
        so, ro = _date_order(s), _date_order(rep)
        if so and ro and so != ro:
            out.append({'rule': 'day/month order differs between the two date fields',
                        'keys': ['shortDateFormat',
                                 'reportDateFormat.shortDatePattern'],
                        'left': s, 'right': rep,
                        'text': f'token order {so} vs {ro}'})
    if s is not None and jt == 'str':
        sep = typed(doc, 'reportDateFormat.dateSeparator', 'str')
        if sep and sep not in s:
            out.append({'rule': 'date separator differs between the two date fields',
                        'keys': ['shortDateFormat',
                                 'reportDateFormat.dateSeparator'],
                        'left': s, 'right': sep,
                        'text': 'the separator the document publishes is not '
                                'the one its own short format uses'})
    return out


def r_mfa_shape(doc, cc):
    out = []
    st, mfa, jt = resolve(doc, 'mfa')
    if st == VALUED and isinstance(mfa, dict):
        if 'status' not in mfa:
            out.append({'rule': 'mfa block with no status',
                        'keys': ['mfa.status'],
                        'left': 'ABSENT',
                        'right': ','.join(sorted(mfa)),
                        'text': 'the document describes MFA without saying '
                                'whether it is required'})
        for k, v in mfa.items():
            if k != 'status' and not isinstance(v, (int, float, str, bool, type(None))):
                out.append({'rule': 'unexpected mfa value type',
                            'keys': [f'mfa.{k}'],
                            'left': type(v).__name__, 'right': k,
                            'text': 'a scalar mfa field is not scalar'})
    return out


def _parse_shape_date(value):
    """Split a date-shaped string into (order, sep, parts). order is 'DMY' or
    'MDY' from the first two components' size — no, sizes are ambiguous; the
    order is decided by which component exceeds 12. Returns (order|None, sep,
    ints)."""
    if not isinstance(value, str):
        return None, None, None
    m = re.match(r'^\s*(\d{1,4})\s*([^\d\s])\s*(\d{1,2})\s*([^\d\s])\s*(\d{1,4})\s*$', value)
    if not m:
        return None, None, None
    a, sep1, b, sep2, c = m.groups()
    sep = sep1 if sep1 == sep2 else None
    ai, bi, ci = int(a), int(b), int(c)
    # A 4-digit leading component is a year first: Y-M-D.
    if len(a) == 4:
        return 'YMD', sep, (ai, bi, ci)
    if len(c) == 4 or (len(c) == 2 and len(a) == 4):
        if bi > 12 and ai <= 12:
            return 'MDY', sep, (ai, bi, ci)
        return 'DMY', sep, (ai, bi, ci)
    if bi > 12 and ai <= 12:
        return 'MDY', sep, (ai, bi, ci)
    return 'DMY', sep, (ai, bi, ci)


def r_mfa_from_date(doc, cc):
    """`mfa.fromDate` is a date inside a document that publishes its own date
    format in two places. TIER 2, not tier 1: a fixed wire serialisation is a
    benign reading and is not excluded here — the point recorded is that the
    document does not say which format the value is in, and a client that uses
    the document's own format can mis-read it."""
    out = []
    val = typed(doc, 'mfa.fromDate', 'str')
    if val is None:
        return out
    order, sep, parts = _parse_shape_date(val)
    if order is None:
        out.append({'rule': 'mfa.fromDate is not a recognisable date',
                    'class': 'FLAG-INFERRED',
                    'keys': ['mfa.fromDate'],
                    'left': val, 'right': 'unrecognised shape',
                    'text': 'flagged'})
        return out
    want = _date_order(typed(doc, 'shortDateFormat', 'str'))
    want_order = {'DM': 'DMY', 'MD': 'MDY'}.get(want)
    if want_order and order != want_order:
        out.append({'rule': 'mfa.fromDate ordered against the document date format',
                    'keys': ['mfa.fromDate', 'shortDateFormat'],
                    'left': val, 'right': typed(doc, 'shortDateFormat', 'str'),
                    'text': f'the value reads as {order}, the document formats '
                            f'dates as {want_order}'})
    dsep = typed(doc, 'reportDateFormat.dateSeparator', 'str')
    if dsep and sep and sep != dsep:
        out.append({'rule': 'mfa.fromDate separator against the document date format',
                    'keys': ['mfa.fromDate', 'reportDateFormat.dateSeparator'],
                    'left': val, 'right': dsep,
                    'text': 'the value uses a separator the document does not '
                            'publish'})
    if order == 'DMY' and parts[1] > 12:
        out.append({'rule': 'mfa.fromDate month out of range under its own reading',
                    'keys': ['mfa.fromDate', 'shortDateFormat'],
                    'left': val, 'right': typed(doc, 'shortDateFormat', 'str'),
                    'text': f'the second component is {parts[1]}, which is not '
                            f'a month'})
    return out


def r_mfa_zero_grace(doc, cc):
    """INFERRED rule, reported as a flag and never counted as a contradiction:
    a REQUIRED factor with a zero-day grace period leaves no window in which the
    account can be used without it. Recorded only as an observation."""
    out = []
    status = typed(doc, 'mfa.status', 'str')
    grace = typed(doc, 'mfa.gracePeriod', 'int')
    if status == 'REQUIRED' and grace == 0:
        out.append({'rule': 'MFA REQUIRED with gracePeriod 0',
                    'keys': ['mfa.status', 'mfa.gracePeriod'],
                    'left': status, 'right': grace,
                    'text': 'required factor, zero-day grace — flagged, rule '
                            'is an assumption'})
    return out


def r_reports_shape(doc, cc):
    out = []
    reports = typed(doc, 'supportedReports', 'list')
    if reports is None:
        return out
    seen = {}
    for i, r in enumerate(reports):
        if not isinstance(r, dict):
            out.append({'rule': 'supportedReports entry is not an object',
                        'keys': [f'supportedReports[{i}]'],
                        'left': type(r).__name__, 'right': str(r)[:40],
                        'text': 'every entry is expected to be an object'})
            continue
        name = r.get('report')
        seen.setdefault(name, []).append(i)
        only = r.get('onlyFor')
        notf = r.get('notFor')
        for k, v in (('onlyFor', only), ('notFor', notf)):
            if not isinstance(v, list):
                out.append({'rule': 'supportedReports field is not a list',
                            'keys': [f'supportedReports[{i}].{k}'],
                            'left': type(v).__name__, 'right': str(v)[:40],
                            'text': f'{k} is not an array'})
        if isinstance(only, list) and isinstance(notf, list):
            both = sorted(set(map(str, only)) & set(map(str, notf)))
            if both:
                out.append({'rule': 'report both required and forbidden',
                            'keys': [f'supportedReports[{i}].onlyFor',
                                     f'supportedReports[{i}].notFor'],
                            'left': ','.join(both), 'right': name,
                            'text': 'the same country is in onlyFor and notFor '
                                    'for one report'})
    for name, idxs in seen.items():
        if len(idxs) > 1:
            out.append({'rule': 'duplicate report entry',
                        'keys': ['supportedReports'],
                        'left': f'{name} x{len(idxs)}',
                        'right': ','.join(str(i) for i in idxs),
                        'text': 'the same report name appears twice'})
    return out


def r_postal(doc, cc):
    """The document publishes both an example format and a regular expression
    meant to validate it. If the expression rejects the document's own example,
    a client that validates against it rejects every address it is shown."""
    out = []
    fmts = typed(doc, 'postal.postalFormat', 'list')
    st, rx, jt = resolve(doc, 'postal.regExpStr')
    if not fmts or st != VALUED or not isinstance(rx, str):
        return out
    for ex in fmts:
        if not isinstance(ex, str):
            continue
        try:
            hit = re.search(rx, ex) is not None
        except re.error as e:
            out.append({'rule': 'postal.regExpStr does not compile',
                        'keys': ['postal.regExpStr'],
                        'left': 're.error', 'right': str(e)[:60],
                        'text': 'the published pattern is not a valid regex'})
            break
        if not hit:
            out.append({'rule': 'postal format rejected by its own regex',
                        'keys': ['postal.postalFormat', 'postal.regExpStr'],
                        'left': ex, 'right': f'{len(rx)}-char expression',
                        'text': 'an example the document itself publishes does '
                                'not match the expression published beside it'})
    return out


def _locale_norm(code):
    """Normalise a language code for comparison: lowercase, and drop a script
    subtag, so ZH-HANT and zh compare equal. The corpus contains both spellings
    in the same document (HK, MO, TW: defaultLanguage ZH-HANT, paths /zh/), and
    an earlier version of this rule reported that as 15 contradictions when it
    is a naming convention, not a vendor fault."""
    if not isinstance(code, str):
        return None
    return code.strip().lower().split('-')[0]


def r_pathdocs_locale(doc, cc):
    """The strongest internal statement this document supports about its own
    legal-document paths: every locale segment in `pathDocs` must name a
    language the document's OWN `languages` array lists.

    An earlier version asserted the weaker and wrong thing — that every path
    must use `defaultLanguage`. That is refuted by 16 countries whose
    defaultLanguage is a local language and whose FAQ is served in English,
    which is an ordinary fallback, not a contradiction. The rule below does not
    care which language a document is in; it only cares whether the path names
    a language the document says the country has."""
    out = []
    pd = typed(doc, 'pathDocs', 'dict')
    langs = typed(doc, 'languages', 'list')
    if not pd or not langs:
        return out
    listed = {_locale_norm(l.get('code')) for l in langs if isinstance(l, dict)}
    listed.discard(None)
    bad = {}
    for k, v in pd.items():
        if not isinstance(v, str):
            continue
        m = re.search(r'/media/([^/]+)/', v)
        if not m:
            continue
        loc = _locale_norm(m.group(1))
        if loc and loc not in listed:
            bad.setdefault(loc, []).append(k)
    for loc, keys in sorted(bad.items()):
        out.append({'rule': 'legal-document path names a language the document does not list',
                    'keys': ['pathDocs', 'languages'],
                    'left': loc,
                    'right': ','.join(sorted(keys)[:4]),
                    'text': f'pathDocs serves /{loc}/ while `languages` lists '
                            f'{sorted(x for x in listed if x)} — no reading of '
                            f'this document makes {loc} one of its languages'})
    return out


DAYS = ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su']


def _expand_days(spec):
    """Expand a techDays value to a set of day codes. Accepts 'Mo-Su',
    'Mo-Fr' and comma lists. Returns None when a token is not a day code, so a
    vocabulary this reader does not know is reported as unknown rather than as
    a contradiction — a range like 'Mo-Su' covers Saturday by being a range,
    and an earlier version of this rule read it as a missing day."""
    if not isinstance(spec, str):
        return None
    out = set()
    for part in re.split(r'[,\s]+', spec.strip()):
        if not part:
            continue
        if '-' in part:
            a, _, b = part.partition('-')
            if a in DAYS and b in DAYS:
                ia, ib = DAYS.index(a), DAYS.index(b)
                if ia <= ib:
                    out.update(DAYS[ia:ib + 1])
                    continue
                out.update(DAYS[ia:] + DAYS[:ib + 1])
                continue
            return None
        if part in DAYS:
            out.add(part)
            continue
        return None
    return out or None


def r_tech_247(doc, cc):
    """techHours promising 24/7 while techDays lists fewer than seven days is
    the document contradicting itself: a client that honours the days list
    shows support as unavailable on the days the same document says it is
    available."""
    out = []
    th = typed(doc, 'techHours', 'str')
    td = typed(doc, 'techDays', 'str')
    if isinstance(th, str) and th.startswith('24/7'):
        days = _expand_days(td)
        if days is not None and len(days) < 7:
            out.append({'rule': '24/7 hours on a days list that omits a day',
                        'class': 'CONTRADICTION',
                        'keys': ['techHours', 'techDays'],
                        'left': th, 'right': td,
                        'text': f'the document promises 24/7 and its days list '
                                f'expands to {len(days)} day(s)'})
    return out


def r_tech_clock_shape(doc, cc):
    """FLAG-INFERRED, not a contradiction: an assumption about parsers, not
    about the document. Recorded because the repo already carries one parser
    break here — NL's dotted clock, in
    findings-log/probe-2026-10-08/recon/CONFIG-NAMESPACE-DEEP.md:239. It is NOT
    in docs/04: an earlier version of this docstring cited docs/04:238 for it,
    which was already wrong at the base commit — that line reads "itemised in any
    source". docs/04:419 summarises techHours without the dotted-clock detail."""
    out = []
    th = typed(doc, 'techHours', 'str')
    if isinstance(th, str) and not th.startswith('24/7'):
        if not re.match(r'^\d{1,2}[:.]\d{2}\s*[ap]\.?m?\.?\s*-\s*\d{1,2}[:.]\d{2}\s*[ap]\.?m?\.?$',
                        th, re.I):
            out.append({'rule': 'techHours clock shape',
                        'class': 'FLAG-INFERRED',
                        'keys': ['techHours'],
                        'left': th, 'right': 'H:MM - H:MM, no trailing token',
                        'text': 'flagged: a strict clock parser rejects this '
                                'shape — the rule is an assumption about '
                                'parsers, not a claim about the vendor'})
    return out


RULES = [
    ('glucose-unit disagreement', r_glucose_units),
    ('carbohydrate-unit disagreement', r_carb_units),
    ('EXCHANGES without a conversion ratio', r_exchanges_need_ratio),
    ('defaultLanguage not among languages', r_default_language),
    ('name and defaultCountryName disagree', r_country_names),
    ('region and mediaHost disagree', r_region_media_host),
    ('endpoint host does not match the region', r_region_cumulus_host),
    ('stateCodes carry another country prefix', r_state_codes_prefix),
    ('subdivision list on a non-US region', r_state_codes_vs_region),
    ('timeFormat and timeUnitsDefault disagree', r_time_fields),
    ('day/month order differs between the two date fields', r_date_fields),
    ('mfa block with no status', r_mfa_shape),
    ('mfa.fromDate against the document date format', r_mfa_from_date),
    ('report both required and forbidden', r_reports_shape),
    ('postal format rejected by its own regex', r_postal),
    ('legal-document path names a language the document does not list',
     r_pathdocs_locale),
    ('24/7 hours on a days list that omits a day', r_tech_247),
    ('MFA REQUIRED with gracePeriod 0', r_mfa_zero_grace),
    ('techHours clock shape', r_tech_clock_shape),
]

# TIER 1 — the two sides draw from the SAME closed vocabulary, so no benign
# reading exists: MMOL_L and MG_DL are two members of one enum and a single
# document selects both. This is the shape that makes a client output a wrong
# number. TIER 2 — mechanically identical (two keys, two different values) but a
# benign reading is available and is NOT excluded: `name` and
# `defaultCountryName` are plausibly the English and the localised name, so
# their differing is an observation, not a demonstrated fault.
TIER2_RULES = {
    'name and defaultCountryName disagree',
    'mfa.fromDate ordered against the document date format',
    'mfa.fromDate separator against the document date format',
    'mfa.fromDate month out of range under its own reading',
}

VOCAB_REPORTS = {
    'ADHERENCE', 'ASSESSMENT_AND_PROGRESS', 'BOLUS_WIZARD_FOOD_BOLUS',
    'DAILY_DETAILS', 'DASHBOARD', 'DEVICE_SETTINGS', 'EPISODE_SUMMARY',
    'LOGBOOK', 'OVERVIEW', 'WEEKLY_REVIEW', 'INSULIN_ASSESSMENT',
}


def analyse(cc, body_path):
    raw = open(body_path, 'rb').read()
    sha = hashlib.sha256(raw).hexdigest()
    try:
        doc = json.loads(raw.decode('utf-8'))
    except Exception as e:
        return {'cc': cc, 'parse': f'FAIL: {e}', 'body_sha256': sha,
                'body_bytes': len(raw)}
    if not isinstance(doc, dict):
        return {'cc': cc, 'parse': f'not an object ({type(doc).__name__})',
                'body_sha256': sha, 'body_bytes': len(raw)}

    keys = sorted(doc)
    key_states = {}
    for k in REF:
        key_states[k] = state_of(doc, k)
    extra = [k for k in keys if k not in REF]

    found, flagged = [], []
    for name, fn in RULES:
        for hit in fn(doc, cc):
            # The class is a property of the HIT, not of the rule name. An
            # earlier version of this file registered the same function twice
            # under two names and counted its FLAG findings as contradictions;
            # the offline self-test caught it.
            if hit.get('class') == 'FLAG-INFERRED':
                flagged.append(hit)
                continue
            hit.setdefault('class', 'CONTRADICTION')
            # Tier is keyed on the HIT's own rule name, not the registry name:
            # one registered rule can emit several distinct findings and only
            # some of them are tier 2. Keying on the registry name put the
            # mfa.fromDate findings in tier 1 when TIER2_RULES says otherwise.
            hit.setdefault('tier', 2 if hit['rule'] in TIER2_RULES else 1)
            found.append(hit)

    rep_names = [r.get('report') for r in (typed(doc, 'supportedReports', 'list') or [])
                 if isinstance(r, dict)]
    vocab_delta = sorted({r for r in rep_names if r not in VOCAB_REPORTS})

    # Structural completeness of the five nested blocks, so an absent block is
    # never reported as an empty one.
    nested = {}
    for b in ('mfa', 'pathDocs', 'reportDateFormat', 'postal', 'numberFormat',
              'languages', 'stateCodes', 'supportedReports'):
        st, v, jt = resolve(doc, b)
        nested[b] = {'state': st, 'type': jt,
                     'n': (len(v) if st == VALUED and isinstance(v, (list, dict)) else None)}

    return {'cc': cc, 'parse': 'OK', 'body_sha256': sha, 'body_bytes': len(raw),
            'key_count': len(keys), 'key_states': key_states,
            'keys_not_in_reference': extra, 'nested': nested,
            'contradictions': found, 'flags': flagged,
            'report_vocabulary_delta': vocab_delta,
            'report_count': len(rep_names)}


def main():
    """Shipped invocation: `python3 reader.py bodies`.

    The country code is derived from the filename by stripping the `cc-` PREFIX
    as well as the `.json` suffix. An earlier version stripped 5 characters
    (`name[:-5]`) and so produced `cc-CA` from `cc-CA.json`; `r_state_codes_prefix`
    then tested codes against the literal prefix `cc-CA-`, which nothing matches,
    emitting two spurious tier-1 findings for CA and US — re-running the shipped
    reader gave 53 tier-1 against the 51 in the committed `verdicts.jsonl`.

    The committed artefact was never wrong: `report.py` passes the code from
    `run.log`, not from the filename. The defect was that the shipped entry point
    could not reproduce it, which fails AGENTS.md §10's re-run bar. Found by
    re-running the shipped command, which is why it is checked below.

    ROW ORDER matters and is taken from `run.log` when it is present, because
    that is the order `report.py` used to write `verdicts.jsonl` — the order the
    controls come first. Sorting the filenames instead sorts `cc-AD` ahead of
    `cc-GB`, which reorders every row and makes the output differ from the
    committed artefact byte-for-byte even when every record is identical.
    """
    bodies, out = sys.argv[1], sys.stdout
    runlog = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'run.log')
    order = []
    if os.path.exists(runlog):
        with open(runlog, encoding='utf-8') as fh:
            for line in fh:
                if line.startswith('#') or not line.strip():
                    continue
                parts = line.rstrip('\n').split('\t')
                if len(parts) >= 2:
                    order.append(parts[1])
    names = [f'cc-{cc}.json' for cc in order]
    names += [n for n in sorted(os.listdir(bodies))
              if n.endswith('.json') and n not in names]
    for name in names:
        if not name.endswith('.json'):
            continue
        path = os.path.join(bodies, name)
        if not os.path.exists(path):
            continue
        base = name[:-len('.json')]
        cc = base[len('cc-'):] if base.startswith('cc-') else base
        rec = analyse(cc, path)
        out.write(json.dumps(rec, sort_keys=True) + '\n')


if __name__ == '__main__':
    main()