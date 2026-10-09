#!/usr/bin/env python3
"""CI checks for the public site (standard library only). Exit 1 on the first failing GROUP; every failure inside a group is printed.

Groups (the site publication rules of 9 Oct 2026):
  generated   terms.html and privacy.html are exactly what legal-sources/ generates (no hand edits can sit in them)
  sources     each legal-sources/<name>.txt is exactly the text of <name>.json; each source's size and SHA-256 are listed in legal-sources/MANIFEST.md
  edits       legal-sources/edits.json is exactly the authorised list (the dates, and the one ', USA' fix)
  text        each page's text equals its source text, block by block, after whitespace normalisation, with ONLY the documented edits (legal-sources/edits.json)
  dates       no blank date line is left; the pages carry the publication date from site-config.json
  legal       legal.html is the approved text word for word (block by block, and again as one blob by an independent method), carries every required contact detail, no placeholder
  banned      the old plan names and any freshness guarantee or credit appear on none of the checked pages; no registered-trademark symbol
  footer      every checked page's footer links to Terms, Privacy (and Legal once legal.html exists) and carries the trademark line exactly
  links       every local link and anchor resolves
  scripts     the checked pages load no script and no external resource (so no analytics and no cookies are possible; the consent gate has nothing to gate)
"""
import hashlib
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import legal_lib as L  # noqa: E402
import legal_md  # noqa: E402

BANNED_NAMES = ['Starter', 'Growth', 'Coastal', 'Offshore', 'Scale', 'Passenger Pass', 'Crew Pass', 'Pro Crew', 'Charter Bundle', 'Passage Pack']
BANNED_PATTERNS = [
    (re.compile(r'[Ff]reshness\s+(guarantee|credit|SLA)', re.I), 'a freshness guarantee or credit (SLA 4.4: credits are for availability only)'),
    (re.compile(r'(guarantee[sd]?|promise[sd]?)\s+(that\s+)?(the\s+)?(data|facts?|information)\s+(is|are)\s+(always\s+)?(fresh|current|up[- ]to[- ]date)', re.I), 'a data freshness guarantee'),
    (re.compile(r'[®]|&reg;|&#174;|&#xae;', re.I), 'a registered-trademark symbol (TM only, never the registered mark)'),
]

# The ONLY edits to counsel's text that may exist (site publication rules of 9 Oct 2026): the publication date in the blank date lines, and this one typo fix. A new entry in
# legal-sources/edits.json fails here until a human changes this list in the same pull request, where it is visible in review.
AUTHORISED_EDITS = {
    'terms': [('date', '______________', None)],
    'privacy': [('date', '______________', None), ('typo', 'Redwood City, California 94065. Users', 'Redwood City, California 94065, USA. Users')],
}

failures = []


def group(name, fn):
    before = len(failures)
    fn()
    print('%-9s %s' % (name, 'ok' if len(failures) == before else 'FAILED (%d)' % (len(failures) - before)))


def fail(msg):
    failures.append(msg)
    print('  FAIL', msg)


def read(path):
    with open(os.path.join(L.ROOT, path), encoding='utf-8') as f:
        return f.read()


def checked_pages():
    return L.config()['checkedPages']


def check_generated():
    r = subprocess.run([sys.executable, os.path.join(L.ROOT, 'tools', 'build_legal.py'), '--check'], capture_output=True, text=True)
    if r.returncode:
        fail('build_legal.py --check: ' + (r.stdout + r.stderr).strip().replace('\n', ' | '))


def check_sources():
    manifest = read('legal-sources/MANIFEST.md')
    for name in ('terms', 'privacy'):
        doc = L.load_json('legal-sources/%s.json' % name)
        lines = [x for x in L._lines(doc)]
        if read('legal-sources/%s.txt' % name) != '\n'.join(lines) + '\n':
            fail('legal-sources/%s.txt is not exactly the text of %s.json' % (name, name))
        src = doc['source']
        for needle in (str(src['bytes']), src['sha256']):
            if needle not in manifest:
                fail('legal-sources/MANIFEST.md does not list %s for %s' % (needle, name))


def check_edit_list():
    edits = L.load_json('legal-sources/edits.json')
    for name, want in AUTHORISED_EDITS.items():
        got = [(e['kind'], e['find'], e.get('replace')) for e in edits.get(name, [])]
        if got != want:
            fail('legal-sources/edits.json for %s is not exactly the authorised list: %r' % (name, got))
    for name in edits:
        if name not in AUTHORISED_EDITS:
            fail('legal-sources/edits.json has edits for %r, which is not an authorised document' % name)


def check_text():
    cfg = L.config()
    edits = L.load_json('legal-sources/edits.json')
    for name, out in (('terms', 'terms.html'), ('privacy', 'privacy.html')):
        doc = L.apply_edits(L.load_json('legal-sources/%s.json' % name), edits[name], cfg)
        want = [L.norm(x) for x in L._lines(doc)]
        blocks, stray = L.page_blocks(read(out))
        got = [L.norm(b) for b in blocks]
        if stray:
            fail('%s has text outside the paragraphs and list items of the content area: %s' % (out, stray[:3]))
        if len(got) != len(want):
            fail('%s has %d text blocks, the source has %d' % (out, len(got), len(want)))
        for i, (a, b) in enumerate(zip(got, want)):
            if a != b:
                j = next((k for k in range(min(len(a), len(b))) if a[k] != b[k]), min(len(a), len(b)))
                fail('%s block %d differs from the source at character %d: page %r vs source %r' % (out, i + 1, j, a[max(0, j - 30):j + 40], b[max(0, j - 30):j + 40]))
                break


def check_dates():
    cfg = L.config()
    md, yr = cfg['publicationDate']['monthDay'], str(cfg['publicationDate']['year'])
    stamp = '%s, %s' % (md, yr)
    for out, needs in (('terms.html', ['Last Updated: ' + stamp]), ('privacy.html', ['Effective Date: ' + stamp, 'Last Updated: ' + stamp])):
        t = read(out)
        if '____' in t:
            fail('%s still has a blank date line' % out)
        for n in needs:
            if n not in t:
                fail('%s does not carry %r' % (out, n))


LEGAL_REQUIRED = [
    'Data Protection Representative Limited, trading as DataRep', 'digitalrequest@datarep.com', 'datarequest@datarep.com', 'www.datarep.com/data-request',
    '77 Camden Street Lower', 'Dublin, D02 XE80, Ireland', '107-111 Fleet Street', 'Leutschenbachstrasse 95', '+353 1 919 8899', '+1 650 778 1744',
    'B20260350242', '303 Twin Dolphin Drive, Suite 600, Redwood City, California 94065, USA', 'appointed from 7 October 2026', 'Since 7 October 2026',
    'support@sailcoco.com', 'privacy@sailcoco.com', 'security@sailcoco.com', L.TRADEMARK_LINE,
]
LEGAL_FORBIDDEN = ['upon appointment', 'will be published on this page', 'PENDING-EU-REPRESENTATIVE', 'data-pending=', '[publication date]']


def strip_markdown_blob(md):
    """An independent second opinion on the legal page: the Markdown source with its syntax stripped by plain regexes (no use of tools/legal_md.py), as one whitespace-normalised string."""
    out = []
    for ln in md.split('\n'):
        if re.fullmatch(r'\|[-: |]+\|', ln.strip()):
            continue
        ln = re.sub(r'^\s*#+\s+', '', ln)
        ln = re.sub(r'^\s*-\s+', '', ln)
        ln = ln.replace('|', ' ')
        ln = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', ln)
        ln = ln.replace('**', '')
        ln = re.sub(r'\\$', '', ln)
        out.append(ln)
    return L.norm(' '.join(out))


def check_legal():
    cfg = L.config()
    if not cfg['hasLegalPage']:
        return
    md = read('legal-sources/legal.md')
    manifest = read('legal-sources/MANIFEST.md')
    if hashlib.sha256(md.encode('utf-8')).hexdigest() not in manifest:
        fail('legal-sources/MANIFEST.md does not list the SHA-256 of legal-sources/legal.md')
    page = read('legal.html')
    _, want = legal_md.convert(md, L.date_text(cfg))
    blocks, stray = L.page_blocks(page)
    got = [L.norm(b) for b in blocks]
    want = [L.norm(x) for x in want]
    if stray:
        fail('legal.html has text outside the content blocks: %s' % stray[:3])
    if got != want:
        j = next((i for i, (a, b) in enumerate(zip(got, want)) if a != b), min(len(got), len(want)))
        fail('legal.html differs from the source at block %d: page %r vs source %r' % (j + 1, got[j:j + 1], want[j:j + 1]))
    blob_page = L.norm(' '.join(blocks))
    blob_src = strip_markdown_blob(md.replace('[publication date]', L.date_text(cfg)))
    if blob_page != blob_src:
        j = next((k for k in range(min(len(blob_page), len(blob_src))) if blob_page[k] != blob_src[k]), min(len(blob_page), len(blob_src)))
        fail('legal.html as one text blob differs from the independently stripped source at character %d: %r vs %r' % (j, blob_page[max(0, j - 30):j + 40], blob_src[max(0, j - 30):j + 40]))
    visible = re.sub(r'<[^>]+>', ' ', page)
    for need in LEGAL_REQUIRED:
        if L.norm(need) not in L.norm(visible):
            fail('legal.html lacks required text: %s' % need)
    if L.norm(visible).count('7 October 2026') < 2:
        fail('legal.html must carry 7 October 2026 for both appointments (DSA and GDPR/UK/Swiss)')
    for bad in LEGAL_FORBIDDEN:
        if bad in page:
            fail('legal.html contains forbidden text: %s' % bad)


def check_banned():
    for page in checked_pages():
        raw = read(page)
        visible = re.sub(r'<style.*?</style>', ' ', raw, flags=re.S)
        for n in BANNED_NAMES:
            if re.search(r'(?<![A-Za-z])' + re.escape(n) + r'(?![A-Za-z])', visible):
                fail('%s mentions the retired name %r' % (page, n))
        for pat, why in BANNED_PATTERNS:
            if pat.search(raw):
                fail('%s contains %s' % (page, why))


def check_footer():
    legal = L.config()['hasLegalPage']
    for page in checked_pages():
        raw = read(page)
        m = re.search(r'<footer>(.*?)</footer>', raw, re.S)
        if not m:
            fail('%s has no footer' % page)
            continue
        f = m.group(1)
        if L.TRADEMARK_LINE not in f:
            fail('%s footer lacks the trademark line %r' % (page, L.TRADEMARK_LINE))
        for href in ['terms.html', 'privacy.html'] + (['legal.html'] if legal else []):
            if 'href="%s"' % href not in f:
                fail('%s footer does not link to %s' % (page, href))


def check_links():
    pages = {p: read(p) for p in checked_pages()}
    for page, raw in pages.items():
        for href in re.findall(r'href="([^"]+)"', raw):
            if re.match(r'^(https?:|mailto:|tel:)', href):
                continue
            path, _, frag = href.partition('#')
            target = path or page
            if target.startswith('/'):
                # a clean URL as GitHub Pages serves it: /terms is terms.html (or terms/index.html)
                name = target.strip('/')
                cands = [name + '.html', name + '/index.html', name] if name else ['index.html']
                target = next((c for c in cands if os.path.isfile(os.path.join(L.ROOT, c))), None)
                if target is None:
                    fail('%s links to %s, which no file serves (looked for %s)' % (page, href, ', '.join(cands)))
                    continue
            if not os.path.exists(os.path.join(L.ROOT, target)):
                fail('%s links to %s, which does not exist' % (page, href))
                continue
            if frag and 'id="%s"' % frag not in read(target):
                fail('%s links to %s, but %s has no id="%s"' % (page, href, target, frag))


def check_scripts():
    for page in checked_pages():
        raw = read(page)
        if re.search(r'<script|<iframe|<link[^>]+rel="?stylesheet|<img[^>]+src="https?:|src="https?:|@import|url\(https?:', raw, re.I):
            fail('%s loads a script or an external resource' % page)


def main():
    for name, fn in (('generated', check_generated), ('sources', check_sources), ('edits', check_edit_list), ('text', check_text), ('dates', check_dates), ('legal', check_legal), ('banned', check_banned),
                     ('footer', check_footer), ('links', check_links), ('scripts', check_scripts)):
        group(name, fn)
    print('\n%s' % ('ALL CHECKS PASSED' if not failures else '%d CHECK FAILURE(S)' % len(failures)))
    sys.exit(1 if failures else 0)


if __name__ == '__main__':
    main()
