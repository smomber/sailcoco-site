#!/usr/bin/env python3
"""CI checks for the public site (standard library only). Exit 1 on the first failing GROUP; every failure inside a group is printed.

Groups (the site publication rules of 9 Oct 2026):
  generated   terms.html and privacy.html are exactly what legal-sources/ generates (no hand edits can sit in them)
  sources     each legal-sources/<name>.txt is exactly the text of <name>.json; each source's size and SHA-256 are listed in legal-sources/MANIFEST.md
  edits       legal-sources/edits.json is exactly the authorised list (the dates, and the one ', USA' fix)
  text        each page's text equals its source text, block by block, after whitespace normalisation, with ONLY the documented edits (legal-sources/edits.json)
  dates       no blank date line is left; the pages carry the publication date from site-config.json
  legal       legal.html is the approved text word for word (block by block, and again as one blob by an independent method), carries every required contact detail, no placeholder
  figures     index.html and developers.html: every element carrying data-src is checked against its source (a Terms clause AS PUBLISHED, that is counsel's text with the authorised edits applied, matched as whole
              words and figures so that "$9" is not found inside "$99"; the developer figures table, the legal page text, or the dated coverage counts in
              legal-sources/coverage-figures.json), and any money or number-with-unit in the pricing, refund and hero regions or on the developers page that has no data-src fails; on the home page a count of
              facts or countries, or a percentage, that has no data-src fails
  labels      every consumer plan says "Available at launch" and every developer plan the general-availability wording; no button, form or input on any page; no buy or checkout link
  claims      EVERY page in the repository except counsel's Terms and Privacy Policy: no "#1" or "number one"; no "compliant"; no "verified" unless the same block carries the approved qualifier ("Sources checked by
              SailCoCo on [date]. Not a government approval."); no "real-time", "continuously monitored", "always up to date" or "guarantee"; no "we answer ... within" service promise (it must say "we aim to")
  banned      EVERY page in the repository (discovered, not listed): no retired plan name (whole word, any case, in the text a visitor reads), no freshness guarantee or credit, no registered-trademark symbol,
              no "copilot" or "co-pilot" in any case anywhere in a page's markup (the retired tagline word, title and meta tags included; the tagline is "Your Sailing Compliance CoCaptain");
              and, on every page except counsel's Terms and Privacy Policy, no introductory-price, first-year or step-up wording and no "Refund & Cancellation Policy" summary
              plus, on the home page (every consumer plan is annual only, Terms 5.1): no monthly or weekly price or billing period (the developer plans on developers.html are monthly and are not affected), and no
              "% off", "save %", was/now or struck-through price (launch prices are shown as launch price and standard price);
              and, on every page including the Terms, no "lifetime" (Founding Crew is three years)
  footer      every checked page's footer links to Terms, Privacy (and Legal once legal.html exists) and carries the trademark line exactly
  links       every local link and anchor resolves
  scripts     the checked pages load no script and no external resource (so no analytics and no cookies are possible; the consent gate has nothing to gate)
"""
import hashlib
import os
import re
import subprocess
import sys
from html.parser import HTMLParser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import legal_lib as L  # noqa: E402
import legal_md  # noqa: E402

BANNED_NAMES = ['Starter', 'Growth', 'Coastal', 'Offshore', 'Scale', 'Passenger Pass', 'Crew Pass', 'Pro Crew', 'Charter Bundle', 'Passage Pack']
BANNED_PATTERNS = [
    (re.compile(r'[Ff]reshness\s+(guarantee|credit|SLA)', re.I), 'a freshness guarantee or credit (SLA 4.4: credits are for availability only)'),
    (re.compile(r'(guarantee[sd]?|promise[sd]?)\s+(that\s+)?(the\s+)?(data|facts?|information)\s+(is|are)\s+(always\s+)?(fresh|current|up[- ]to[- ]date)', re.I), 'a data freshness guarantee'),
    (re.compile(r'[®]|&reg;|&#174;|&#xae;', re.I), 'a registered-trademark symbol (TM only, never the registered mark)'),
    (re.compile(r'co-?pilot', re.I), 'the retired tagline word "Copilot" (the tagline is "Your Sailing Compliance CoCaptain")'),
    (re.compile(r'\blife[- ]?time\b', re.I), 'the word "lifetime" (Founding Crew is a $150 one-time purchase of the Skipper Plan for three years; nothing is sold as "lifetime")'),
]

# The ONLY edits to counsel's text that may exist (site publication rules of 9 Oct 2026): the publication date in the blank date lines, and this one typo fix. A new entry in
# legal-sources/edits.json fails here until a human changes this list in the same pull request, where it is visible in review.
AUTHORISED_EDITS = {
    'terms': [
        ('date', '______________', None),
        ('owner', 'The Company will register the agent with the U.S. Copyright Office.', "The Company has registered the agent with the U.S. Copyright Office (registration number DMCA-1082554). The agent's full contact details are on the Legal information page at sailcoco.com/legal."),
        ('owner', 'Free tier: no charge.', 'Free tier: no charge. The Free tier includes one Free Compliance Card per person: a Compliance Card for one place, at no charge. The Company will not charge for a Free Compliance Card.'),
        ('owner', 'but only if the account is a Free tier account.', 'but only if the account is a Free tier account, and the Company does not close an account that holds a Free Compliance Card for inactivity.'),
        ('owner', 'means the business subscription described in Section 5, priced per boat, that lets one Charter Operator pay for access for its fleet and invite crew and guests.', 'means the subscription described in Section 5 for two or more boats, priced per boat per year, that lets one Charter Operator pay for access for its fleet and invite crew and guests.'),
        ('owner', "Consumer plans are annual only. They are the Free tier at no charge and the Skipper Plan at $99 per year for one boat, plus $29 per year for each additional boat on the same account. The Skipper Plan includes the features for delivery skippers and paid crew. The Fleet Plan is the one business plan. It is priced per boat in the Charter Operator's fleet at $9 per boat per month, or $8 per boat per month from 25 boats and $7 per boat per month from 100 boats, and it bills monthly. Where a Charter Operator buys the Fleet Plan through supported charter booking software, the price may instead be $2 per boat per charter-week, as shown at the point of sale.", 'All plans are annual only, and no monthly price is offered. They are the Free tier at no charge, the Skipper Plan at $99 per year for one boat, and the Fleet Plan for two or more boats. The Skipper Plan includes the features for delivery skippers and paid crew. The Fleet Plan is priced per boat per year at $89 per boat from 2 boats, $79 per boat from 10 boats, $69 per boat from 25 boats, and $59 per boat from 100 boats, and the number of boats on the account sets the price for every boat.'),
        ('owner', 'Annual plans renew once per year on the renewal date, and the Fleet Plan renews each month on the renewal date.', 'Each Subscription renews once per year on the renewal date.'),
        ('owner', 'Skipper Plan: $99 per year for one boat, plus $29 per year for each additional boat. Includes the features for delivery skippers and paid crew.', 'Skipper Plan: $99 per year for one boat. Includes the features for delivery skippers and paid crew.'),
        ('owner', 'Fleet Plan: $9 per boat per month ($8 from 25 boats, $7 from 100 boats), billed monthly, or $2 per boat per charter-week when bought through supported charter booking software.', 'Fleet Plan: for two or more boats, billed yearly per boat: $89 per boat from 2 boats, $79 from 10 boats, $69 from 25 boats, $59 from 100 boats; the number of boats on the account sets the price for every boat.'),
        ('owner', 'Schedule A lists the current plans.', 'Schedule A lists the current plans. Schedule A also lists the launch prices that apply during the launch period.'),
        ('owner-paragraph', 'Founding Crew: $150 one-time for the Skipper Plan for one boat for three years from purchase, limited to 1,000 seats, sold during a limited promotional window while seats remain, no auto-renewal, no card kept on file.', 'Launch prices. During the launch period, the Company offers each plan at a launch price 30% below its standard price: the Skipper Plan at $69 per year; and the Fleet Plan at $62 per boat per year from 2 boats, $55 from 10 boats, $48 from 25 boats and $41 from 100 boats. A Subscription bought at a launch price renews at that launch price for as long as it stays active without a break, including boats added to a Fleet Plan later, and for that Subscription the standard price in Section 5.2 means its launch price. The Company will announce the end of the launch period on the Service at least 30 days in advance, and the launch period ends no later than six months after paid plans are first offered for sale. Purchases after the launch period ends are at the standard prices.'),
        ('owner', 'with an owner side and a renter side,', 'with an owner side and an operator side (for the person who takes the boat out, such as a renter, charterer or skipper),'),
        ('owner', 'A Charter Operator may also show the renter side of a Compliance Card', 'A Charter Operator may also show the operator side of a Compliance Card'),
        ('owner', 'The Service offers one One-Time Purchase, Founding Crew, which does not auto-renew and for which the Company keeps no card on file. Founding Crew is a $299 one-time purchase for a lifetime Skipper Plan for one boat, limited to 150 seats and sold during a limited promotional window while seats remain. Founding Crew does not renew and ends on its own terms without a further charge.', 'The Service offers one One-Time Purchase, Founding Crew, which does not auto-renew and for which the Company keeps no card on file. Founding Crew is a $150 one-time purchase of the Skipper Plan for one boat for three years from the date of purchase, limited to 1,000 seats and sold during a limited promotional window while seats remain. Founding Crew does not renew and ends after three years without a further charge. The Company emails a reminder at least 30 days before it ends.'),
        ('owner', 'Meaning of Lifetime for Founding Crew.', 'Founding Crew Term.'),
        ('owner', '"Lifetime" for a Founding Crew purchase means for as long as the Company offers the Skipper Plan, or any successor or renamed tier that provides substantially similar access, and not the lifetime of the purchaser. If the Company discontinues the Service, or discontinues the Skipper Plan without offering a successor tier, Founding Crew access ends at that time, and the Company will give at least 60 days advance notice by email before it does so. If the Company discontinues the Service within 24 months after a Founding Crew purchase, the Company refunds a share of the $299 price in proportion to the time left in that 24-month period, and no refund is owed for a discontinuation after 24 months. A Founding Crew purchase carries no cash value except for any refund stated here and is not transferable.', 'A Founding Crew purchase gives access to the Skipper Plan, or any successor or renamed tier that provides substantially similar access, for three years from the date of purchase. If the Company discontinues the Service, or discontinues the Skipper Plan without offering a successor tier, before those three years end, Founding Crew access ends at that time, the Company gives at least 60 days advance notice by email, and it refunds a share of the price paid in proportion to the time left in the three years. A Founding Crew purchase carries no cash value except for any refund stated here and is not transferable.'),
        ('owner', 'Founding Crew: $299 one-time for a lifetime Skipper Plan for one boat, limited to 150 seats, sold during a limited promotional window while seats remain, no auto-renewal, no card kept on file.', 'Founding Crew: $150 one-time for the Skipper Plan for one boat for three years from purchase, limited to 1,000 seats, sold during a limited promotional window while seats remain, no auto-renewal, no card kept on file.'),
    ],
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


CORE_PAGES = ['index.html', 'terms.html', 'privacy.html', 'legal.html', 'developers.html']
COUNSEL_PAGES = ['terms.html', 'privacy.html']  # counsel's own text: it may use words (such as "introductory") that marketing pages must not


def checked_pages():
    """EVERY HTML page in the repository, found by walking it (no hand-kept list), so a new page cannot slip past banned, footer, links, scripts or labels."""
    out = []
    for d, dirs, files in os.walk(L.ROOT):
        dirs[:] = sorted(x for x in dirs if x not in ('.git', '.github', 'node_modules', '__pycache__'))
        for f in sorted(files):
            if f.endswith('.html'):
                out.append(os.path.relpath(os.path.join(d, f), L.ROOT))
    return sorted(out)


class _Visible(HTMLParser):
    """The text a visitor (or a search engine) reads: text nodes outside <style> and <script>, the <title>, and the content of <meta name="description">. Markup, attribute values such as
    the viewport tag's "initial-scale=1", and CSS are not text."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.skip = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in ('style', 'script'):
            self.skip += 1
        if tag == 'meta':
            a = dict(attrs)
            if (a.get('name') or '').lower() == 'description' and a.get('content'):
                self.parts.append(a['content'])
        for k, v in attrs:
            if k in ('alt', 'title') and v:
                self.parts.append(v)

    def handle_endtag(self, tag):
        if tag in ('style', 'script') and self.skip:
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def visible_text(raw):
    p = _Visible()
    p.feed(raw)
    p.close()
    return L.norm(' '.join(p.parts))


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
    figs = L.load_json('legal-sources/developer-figures.json')
    for key, src in figs['sources'].items():
        for needle in (str(src['bytes']), src['sha256']):
            if needle not in manifest:
                fail('legal-sources/MANIFEST.md does not list %s for the developer source %s' % (needle, key))


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
        doc = L.apply_edits(L.load_json('legal-sources/%s.json' % name), edits[name], cfg, name)
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
    if 'privacyPublicationDate' not in cfg:
        fail('site-config.json has no privacyPublicationDate (the Privacy Policy carries its own date since counsel\'s round 3)')
        return
    tdate = L.pub_date(cfg, 'terms')
    stamp = '%s, %s' % (tdate['monthDay'], tdate['year'])
    pstamp = '%s, %s' % (cfg['privacyPublicationDate']['monthDay'], cfg['privacyPublicationDate']['year'])
    for out, needs in (('terms.html', ['Last Updated: ' + stamp]), ('privacy.html', ['Effective Date: ' + pstamp, 'Last Updated: ' + pstamp])):
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


INTRO_WORDING = [
    (re.compile(r'\bintroductory\b', re.I), 'introductory-price wording (the Terms list no introductory price)'),
    (re.compile(r'\bfirst[- ]year\b', re.I), 'first-year price wording'),
    (re.compile(r'\bsteps?\s+up\b', re.I), 'a price step-up promise'),
    (re.compile(r'Refund\s*(?:&|&amp;|and)\s*Cancellation\s+Policy', re.I), 'the old "Refund & Cancellation Policy" summary (cancellation and refunds are the Terms, Section 5)'),
]
# The home page is the consumer page: every consumer plan is annual only (Terms 5.1: "no monthly price is offered"). developers.html is not checked here: the Platform plans are billed monthly (Developer Terms).
CONSUMER_PAGES = ['index.html']
CONSUMER_ALLOWED_PHRASE = 'no monthly price is offered'  # the Terms' own sentence (5.1), which the home page quotes under data-src; the `figures` group proves it is in the Terms
CONSUMER_WORDING = [
    (re.compile(r'\bmonthly\b|\b(?:per|each|every|a)\s+month\b|\bweekly\b|\b(?:per|each|every|a)\s+week\b|\bcharter[- ]?week\b', re.I), 'a monthly or weekly price or billing period (every consumer plan is annual only: Terms 5.1)'),
    # Launch prices (Terms Schedule A) are shown as "Launch price ... · standard price ... after the launch period", never as a discount against a price nobody has paid.
    (re.compile(r'\b\d+\s?%\s?(?:off|discount)\b|\bsave\s+(?:up\s+to\s+)?\d+\s?%|\b(?:was|now)\s+(?:US)?\$\s?\d', re.I), 'a "% off", "save %" or was/now price display (launch prices are shown as launch price and standard price, never as a discount)'),
]
CONSUMER_RAW_BANNED = [
    (re.compile(r'<(?:s|del|strike)\b|line-through', re.I), 'a struck-through price (<s>, <del>, <strike> or text-decoration: line-through)'),
]


def check_banned():
    pages = checked_pages()
    for core in CORE_PAGES:
        if core not in pages:
            fail('%s is missing from the repository (the page discovery found only %s)' % (core, pages))
    for page in pages:
        raw = read(page)
        visible = visible_text(raw)
        for n in BANNED_NAMES:  # case-insensitive, whole word, on what a visitor reads: "scale" in prose fails; the viewport tag's "initial-scale=1" is markup, not text
            if re.search(r'(?<![A-Za-z])' + re.escape(n) + r'(?![A-Za-z])', visible, re.I):
                fail('%s mentions the retired name %r' % (page, n))
        if page not in COUNSEL_PAGES:
            for pat, why in INTRO_WORDING:
                if pat.search(visible):
                    fail('%s contains %s' % (page, why))
        if page in CONSUMER_PAGES:
            consumer_text = visible.replace(CONSUMER_ALLOWED_PHRASE, ' ')
            for pat, why in CONSUMER_WORDING:
                if pat.search(consumer_text):
                    fail('%s contains %s' % (page, why))
            for pat, why in CONSUMER_RAW_BANNED:
                if pat.search(raw):
                    fail('%s contains %s' % (page, why))
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
            if 'href="%s"' % href not in f and 'href="/%s"' % href[:-len('.html')] not in f:  # the file name, or the root-relative clean URL a page shown at any address (404.html) must use
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


# ---------------------------------------------------------------- commercial pages: every figure traced to its source, availability labels, nothing to buy

import developers_page  # noqa: E402

COMMERCIAL_PAGES = ['index.html', 'developers.html']
VOID_TAGS = {'br', 'hr', 'img', 'input', 'meta', 'link', 'area', 'base', 'col', 'embed', 'source', 'track', 'wbr'}
CONSUMER_LABEL = 'Available at launch'


class _Tagged(HTMLParser):
    """Collects every element that carries data-src (its tag, source and text) and every data-label element (its kind and text)."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.items = []
        self.labels = []

    def handle_starttag(self, tag, attrs):
        if tag in VOID_TAGS:
            return
        a = dict(attrs)
        recs = []
        if 'data-src' in a:
            r = {'tag': tag, 'src': a['data-src'], 'text': []}
            self.items.append(r)
            recs.append(r)
        if 'data-label' in a:
            r = {'kind': a['data-label'], 'text': []}
            self.labels.append(r)
            recs.append(r)
        self.stack.append((tag, recs))

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                return

    def handle_data(self, data):
        for _, recs in self.stack:
            for r in recs:
                r['text'].append(data)


def tagged(page):
    p = _Tagged()
    p.feed(read(page))
    p.close()
    for r in p.items + p.labels:
        r['text'] = L.norm(''.join(r['text']))
    return p.items, p.labels


def in_clause(text, clause):
    """True when `text` occurs in `clause` (any case) as whole words and figures: "$9" is not found inside "$99", nor "25" inside "250", nor "boat" inside "boats"."""
    return re.search(r'(?<![\w$.,])' + re.escape(text) + r'(?!\w)', clause, re.I) is not None


def terms_clause(cid):
    # The clauses a page's figures are checked against are the Terms AS PUBLISHED: counsel's source with the authorised edits (legal-sources/edits.json, itself pinned to AUTHORISED_EDITS above) applied,
    # one line per paragraph or list item, exactly the lines the 'text' group proves terms.html carries. Reading counsel's raw terms.txt would make it impossible for a page to state a price an owner edit changed.
    doc = L.apply_edits(L.load_json('legal-sources/terms.json'), L.load_json('legal-sources/edits.json')['terms'], L.config(), 'terms')
    lines = list(L._lines(doc))
    if cid == 'ScheduleA':
        i = next((k for k, l in enumerate(lines) if l.startswith('Schedule A.')), None)
        j = next((k for k, l in enumerate(lines) if l.startswith('Schedule B.')), None)
        return L.norm(' '.join(lines[i:j])) if i is not None and j is not None else None
    for l in lines:
        if l.startswith(cid + ' '):
            return L.norm(l)
    return None


def dev_value(fig, ref):
    parts = ref.split('.')
    if ref == 'sourcesLine':
        return fig.get('sourcesLine')
    if parts[0] == 'billing' and len(parts) == 2:
        return fig['billing'].get(parts[1])
    plan = next((p for p in fig['plans'] if p['key'] == parts[0]), None)
    return plan.get(parts[1]) if plan and len(parts) == 2 else None


COV_REFS = ['publishedFacts', 'publishedFactsAsOf', 'countries', 'countriesAsOf']


def cov_value(cov, ref):
    key, as_of = (ref[:-len('AsOf')], True) if ref.endswith('AsOf') else (ref, False)
    f = cov['figures'].get(key)
    if f is None or ref not in COV_REFS:
        return None
    return f['asOfText'] if as_of else f['text']


UNSOURCED = re.compile(r'(?:US)?\$\s?\d[\d,.]*|\b\d[\d,]*\s+(?:requests|answers|seats|boats|days|months|countries|users)\b', re.I)


def check_figures():
    fig = L.load_json('legal-sources/developer-figures.json')
    cov = L.load_json('legal-sources/coverage-figures.json')
    legal_sentence = developers_page.developer_documents_sentence(L.config())
    for page in COMMERCIAL_PAGES:
        items, _ = tagged(page)
        if not items:
            fail('%s has no data-src element at all: its figures are not traced to a source' % page)
        got = sorted(i['src'].partition(':')[2] for i in items if i['src'].startswith('cov:'))
        if page == 'index.html' and got != sorted(COV_REFS):
            fail('index.html: the coverage counts must each appear exactly once as data-src="cov:..." (want %s, found %s)' % (sorted(COV_REFS), got))
        if page != 'index.html' and got:
            fail('%s carries coverage counts (%s): only the home page states them' % (page, got))
        for it in items:
            kind, _, ref = it['src'].partition(':')
            text = it['text']
            if kind == 'terms':
                cl = terms_clause(ref)
                if cl is None:
                    fail('%s: data-src %r names a clause that does not exist in the Terms' % (page, it['src']))
                elif not in_clause(text, cl):
                    fail('%s: %r is not in Terms clause %s (data-src="%s")' % (page, text[:90], ref, it['src']))
            elif kind == 'dev':
                want = dev_value(fig, ref)
                if want is None:
                    fail('%s: data-src %r names a figure that is not in legal-sources/developer-figures.json' % (page, it['src']))
                elif text != L.norm(want):
                    fail('%s: %r differs from developer-figures.json %s = %r' % (page, text[:90], ref, want))
            elif kind == 'cov':
                want = cov_value(cov, ref)
                if want is None:
                    fail('%s: data-src %r names a coverage figure that is not in legal-sources/coverage-figures.json' % (page, it['src']))
                elif text != L.norm(want):
                    fail('%s: %r differs from coverage-figures.json %s = %r' % (page, text[:90], ref, want))
            elif kind == 'legal':
                if ref != 'developer-documents' or text != L.norm(legal_sentence):
                    fail('%s: the quoted legal-page sentence differs from legal-sources/legal.md (%r)' % (page, text[:90]))
            else:
                fail('%s: unknown data-src kind in %r' % (page, it['src']))
        # a figure with no source: strip every sourced element, then look for money and numbers with units in the pricing, refund and hero regions (index.html) or the whole page (developers.html)
        raw = read(page)
        if page == 'index.html':
            regions = [m.group(0) for m in re.finditer(r'<section id="pricing".*?</section>', raw, re.S)] + re.findall(r'<div class="badge">.*?</div>', raw, re.S)
            if len(regions) != 2:
                fail('index.html: expected the pricing section and the hero badge, found %d regions' % len(regions))
        else:
            regions = [re.search(r'<div class="wrap legal">.*?</div>', raw, re.S).group(0)]
        for reg in regions:
            for _ in range(3):
                reg = re.sub(r'<(\w+)[^>]*\sdata-src="[^"]*"[^>]*>.*?</\1>', ' ', reg, flags=re.S)
            visible = L.norm(re.sub(r'<[^>]+>', ' ', reg))
            for m in UNSOURCED.finditer(visible):
                fail('%s: the figure %r has no data-src (every figure must come from one cited source): ...%s...' % (page, m.group(0), visible[max(0, m.start() - 40):m.end() + 30]))
        if page == 'index.html':
            check_coverage_text(raw, cov)


COVERAGE_UNSOURCED = re.compile(r'\b\d[\d,.]*\s+(?:[A-Za-z-]+\s+)?(?:facts?|countries|territories|jurisdictions)\b|\b\d+(?:\.\d+)?\s?%', re.I)


def check_coverage_text(raw, cov):
    """The home page's coverage counts: the exact labels, each beside its own as-of date, and no other count of facts or countries, and no percentage, anywhere on the page without a source."""
    pf, ct = cov['figures']['publishedFacts'], cov['figures']['countries']
    visible = visible_text(raw)
    for want in ('%s %s as of %s' % (pf['text'], pf['label'], pf['asOfText']), '%s %s as of the %s' % (ct['text'], ct['label'], ct['asOfText'])):
        if want not in visible:
            fail('index.html: the coverage sentence %r is not on the page (every count carries its label and its own as-of date)' % want)
    rest = raw
    for _ in range(3):
        rest = re.sub(r'<(\w+)[^>]*\sdata-src="[^"]*"[^>]*>.*?</\1>', ' ', rest, flags=re.S)
    text = visible_text(rest)
    for m in COVERAGE_UNSOURCED.finditer(text):
        fail('index.html: the count %r has no data-src (the only coverage numbers allowed are the two in coverage-figures.json): ...%s...' % (m.group(0), text[max(0, m.start() - 40):m.end() + 30]))


def check_labels():
    fig = L.load_json('legal-sources/developer-figures.json')
    items, labels = tagged('index.html')
    consumer = [x for x in labels if x['kind'] == 'consumer']
    raw = read('index.html')
    cards = len(re.findall(r'<div class="plan[ "]', raw)) + len(re.findall(r'<div class="onetime"', raw))
    if len(consumer) != cards or cards != 4:
        fail('index.html: %d consumer plan blocks and %d availability labels (want 4 and 4: Free, Skipper, Fleet, Founding Crew)' % (cards, len(consumer)))
    for x in consumer:
        if x['text'] != CONSUMER_LABEL:
            fail('index.html: a consumer plan label reads %r, not %r' % (x['text'], CONSUMER_LABEL))
    _, dlabels = tagged('developers.html')
    dev = [x for x in dlabels if x['kind'] == 'developer']
    if len(dev) != len(fig['plans']):
        fail('developers.html: %d developer availability labels for %d plans' % (len(dev), len(fig['plans'])))
    for x in dev:
        if x['text'] != fig['availability']:
            fail('developers.html: a developer plan label reads %r, not %r' % (x['text'], fig['availability']))
    # nothing to buy: no button, form or input anywhere, no buy or checkout link on the commercial pages
    for page in checked_pages():
        r = read(page)
        if re.search(r'<(button|form|input|select|textarea)\b', r, re.I):
            fail('%s has a button, form or input (nothing can be bought or submitted on this site)' % page)
    for page in COMMERCIAL_PAGES:
        for m in re.finditer(r'<a\b[^>]*href="([^"]*)"[^>]*>(.*?)</a>', read(page), re.S | re.I):
            href, label = m.group(1), L.norm(re.sub(r'<[^>]+>', ' ', m.group(2)))
            if re.search(r'\b(buy|purchase|checkout|subscribe|order now|add to cart|sign up|start free trial|get started)\b', label, re.I) or re.search(r'stripe|checkout|/buy|/pay\b|/cart', href, re.I):
                fail('%s has a link that offers something for sale: %r -> %s' % (page, label[:60], href))


# ---------------------------------------------------------------- claims: marketing copy may not promise more than the product can show (site publication rules of 9 Oct 2026)

CLAIM_PATTERNS = [
    (re.compile(r'(?<![\w&])#\s?1(?![\w;])|\bnumber[ -]one\b|\bno\.\s?1\b', re.I), '"#1" or "number one" (an unsubstantiated superlative)'),
    (re.compile(r'\bcompliant\b', re.I), '"compliant" (no claim may say that a boat or a person is compliant)'),
    (re.compile(r'\breal[- ]?time\b', re.I), '"real-time" (a freshness claim)'),
    (re.compile(r'\bcontinuous(?:ly)?\s+monitor(?:ed|ing)?\b', re.I), '"continuously monitored" (a freshness claim)'),
    (re.compile(r'\balways\s+up[- ]to[- ]date\b', re.I), '"always up to date" (a freshness claim)'),
    (re.compile(r'\bguarantee[sd]?\b', re.I), '"guarantee" (no outcome is promised)'),
    (re.compile(r'\bwe\s+(?:answer|reply|respond)\b[^.]{0,60}\bwithin\b', re.I), 'a service promise ("we answer ... within"): say "we aim to"'),
]
VERIFIED = re.compile(r'\bverified\b', re.I)
VERIFIED_QUALIFIER = ('Sources checked by SailCoCo on', 'Not a government approval.')
BLOCK_TAGS = {'p', 'div', 'li', 'ul', 'ol', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'section', 'header', 'footer', 'nav', 'table', 'tr', 'td', 'th', 'blockquote', 'br', 'hr', 'title', 'body', 'main', 'article', 'aside'}


class _Blocks(HTMLParser):
    """The visible text of a page cut into blocks at block-level tags (so the qualifier must sit in the same paragraph, list item or heading as the word it qualifies). The title and the meta
    description are blocks of their own, as are alt and title attributes."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.skip = 0
        self.cur = []
        self.blocks = []

    def flush(self):
        t = L.norm(' '.join(self.cur))
        if t:
            self.blocks.append(t)
        self.cur = []

    def handle_starttag(self, tag, attrs):
        if tag in ('style', 'script'):
            self.skip += 1
        if tag in BLOCK_TAGS:
            self.flush()
        a = dict(attrs)
        if tag == 'meta' and (a.get('name') or '').lower() == 'description' and a.get('content'):
            self.blocks.append(L.norm(a['content']))
        for k in ('alt', 'title'):
            if a.get(k):
                self.blocks.append(L.norm(a[k]))

    def handle_endtag(self, tag):
        if tag in ('style', 'script') and self.skip:
            self.skip -= 1
        if tag in BLOCK_TAGS:
            self.flush()

    def handle_data(self, data):
        if not self.skip:
            self.cur.append(data)


def visible_blocks(raw):
    p = _Blocks()
    p.feed(raw)
    p.close()
    p.flush()
    return p.blocks


def check_claims():
    for page in checked_pages():
        if page in COUNSEL_PAGES:  # counsel's own text is exempt
            continue
        for block in visible_blocks(read(page)):
            for pat, why in CLAIM_PATTERNS:
                m = pat.search(block)
                if m:
                    fail('%s makes a claim the site does not make: %s: ...%s...' % (page, why, block[max(0, m.start() - 50):m.end() + 40]))
            m = VERIFIED.search(block)
            if m and not all(q in block for q in VERIFIED_QUALIFIER):
                fail('%s uses "verified" without the approved qualifier ("Sources checked by SailCoCo on [date]. Not a government approval.") in the same block; say "sourced and dated": ...%s...' % (page, block[max(0, m.start() - 50):m.end() + 40]))


def main():
    for name, fn in (('generated', check_generated), ('sources', check_sources), ('edits', check_edit_list), ('text', check_text), ('dates', check_dates), ('legal', check_legal), ('figures', check_figures), ('labels', check_labels), ('banned', check_banned), ('claims', check_claims),
                     ('footer', check_footer), ('links', check_links), ('scripts', check_scripts)):
        group(name, fn)
    print('\n%s' % ('ALL CHECKS PASSED' if not failures else '%d CHECK FAILURE(S)' % len(failures)))
    sys.exit(1 if failures else 0)


if __name__ == '__main__':
    main()
