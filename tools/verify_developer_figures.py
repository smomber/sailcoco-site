#!/usr/bin/env python3
"""Re-check legal-sources/developer-figures.json against the developer documents themselves (standard library only).

usage: python3 tools/verify_developer_figures.py <developer-terms.docx> <api-policy.docx>

The developer documents are not published and are not in this repository, so CI cannot run this; run it locally with the two .docx files. It confirms the size and SHA-256 recorded for each document,
then that every figure in the JSON appears in the clause it cites: the plan table (Developer Terms B3), the monthly answer limits (B4.2), the Display Licence (B7.2), the usage-based billing wording
(API Usage and Attribution Policy 7.1) and the availability sentence (B2). Exit 0 only if every check passes.
"""
import hashlib
import json
import os
import re
import sys
import zipfile
from xml.etree import ElementTree as ET

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def lines_of(path):
    """One string per paragraph; a table row becomes its cells joined by ' | '. Whitespace is normalised."""
    root = ET.fromstring(zipfile.ZipFile(path).read('word/document.xml'))
    out = []

    def text(el):
        s = ''
        for t in el.iter():
            if t.tag == W + 't':
                s += t.text or ''
            elif t.tag == W + 'tab':
                s += ' '
        return ' '.join(s.replace(' ', ' ').split())
    for el in root.find(W + 'body'):
        if el.tag == W + 'p':
            out.append(text(el))
        elif el.tag == W + 'tbl':
            for tr in el.iter(W + 'tr'):
                out.append(' | '.join(text(tc) for tc in tr.findall(W + 'tc')))
    return [x.replace('’', "'") for x in out if x]


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    fig = json.load(open(os.path.join(ROOT, 'legal-sources', 'developer-figures.json'), encoding='utf-8'))
    bad = 0

    def check(ok, msg):
        nonlocal bad
        print(('ok   ' if ok else 'FAIL ') + msg)
        bad += 0 if ok else 1

    docs = {}
    for key, path in (('developerTerms', sys.argv[1]), ('apiPolicy', sys.argv[2])):
        raw = open(path, 'rb').read()
        src = fig['sources'][key]
        check(len(raw) == src['bytes'], '%s size %d bytes (recorded %d)' % (key, len(raw), src['bytes']))
        check(hashlib.sha256(raw).hexdigest() == src['sha256'], '%s SHA-256 equals the recorded value' % key)
        docs[key] = lines_of(path)
    dt, ap = docs['developerTerms'], docs['apiPolicy']
    b42 = next((x for x in dt if x.startswith('B4.2')), '')
    b72 = next((x for x in dt if x.startswith('B7.2')), '')
    b2 = next((x for x in dt if x.startswith('Availability |')), '')
    p71 = next((x for x in ap if x.startswith('7.1')), '')
    check('Until general availability (target December 2026), paid Plans cannot be purchased' in b2, 'B2 Availability: paid plans cannot be purchased until general availability (target December 2026)')
    check(fig['availability'] == 'Available at general availability (target December 2026)', 'availability label wording')
    for p in fig['plans']:
        row = next((x for x in dt if x.startswith(p['name'] + ' |') or x.startswith(p['name'] + ' (see') or x.startswith(p['name'] + ' (S')), '')
        cells = row.split(' | ')
        check(len(cells) >= 5, 'B3 row for %s found' % p['name'])
        if len(cells) < 5:
            continue
        fee_ok = cells[1].startswith(p['monthlyFee'])
        check(fee_ok, 'B3 %s monthly fee cell %r starts with %r' % (p['name'], cells[1], p['monthlyFee']))
        check(p['dailyRequests'] in cells[3], 'B3 %s daily request cell %r contains %r' % (p['name'], cells[3], p['dailyRequests']))
        check(p['monthlyAnswers'] in cells[4], 'B3 %s monthly answer cell %r contains %r' % (p['name'], cells[4], p['monthlyAnswers']))
        if p['key'] in ('platform199', 'platform499'):
            check(cells[2].startswith('Not offered'), 'B3 %s yearly fee is "Not offered"' % p['name'])
            check(('%s: %s' % (p['name'], p['monthlyAnswers'])) in b42, 'B4.2 lists %s: %s answers' % (p['name'], p['monthlyAnswers']))
            check(('%s: %s' % (p['name'], p['dailyRequests'])) in p71, 'API policy 7.1 lists %s: %s requests per day' % (p['name'], p['dailyRequests']))
        if p['key'] == 'free':
            check('Free: 50' in b42, 'B4.2 lists Free: 50 answers')
            check('Free: 100 requests per day' in p71, 'API policy 7.1 lists Free: 100 requests per day')
        if p['note']:
            check(p['note'] in b72, 'B7.2 names the %s' % p['note'])
    check('Platform plans' in p71 or 'On a Platform plan' in p71, 'API policy 7.1 speaks of Platform plans')
    check('turn on usage-based billing with a monthly spending cap' in p71, 'API policy 7.1: usage-based billing is optional, with a monthly spending cap')
    print('\n%s' % ('ALL DEVELOPER FIGURES VERIFIED' if not bad else '%d FAILURE(S)' % bad))
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
