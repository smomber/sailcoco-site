#!/usr/bin/env python3
"""Shared helpers for the legal pages (standard library only).

The rule these helpers enforce (site publication rules of 9 Oct 2026): legal text is COPIED, never drafted or edited. A page is generated from the structured source in
legal-sources/*.json (extracted by tools/extract_docx.py from counsel's CLEAN .docx, with no model in the loop), and the only differences from the source that may ever exist are the ones
listed in legal-sources/edits.json (the publication date filled into the blank date lines, the one authorised typo fix, and the owner's own edits: exact find-and-replace inside one formatting run, or a new
paragraph after a named block). tools/check_site.py fails on any other difference.
"""
import html
import json
import os
import re
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def norm(s):
    """Whitespace-normalise: any run of whitespace (including newlines and no-break spaces) becomes one space."""
    return ' '.join(s.replace(' ', ' ').split())


def esc(s):
    """Escape &, < and > only. Quotes and other characters stay literal, exactly as the existing pages carry them (the pages are UTF-8)."""
    return html.escape(s, quote=False)


def load_json(path):
    with open(os.path.join(ROOT, path), encoding='utf-8') as f:
        return json.load(f)


def config():
    return load_json('site-config.json')


def pub_date(cfg, name=None):
    """The configured publication date for one document. The Privacy Policy has its own (counsel's round 3, 10 Oct 2026: its Effective Date and Last Updated are the date round 3 was merged); every other document uses publicationDate."""
    if name == 'privacy':
        return cfg['privacyPublicationDate']
    if name == 'terms' and 'termsPublicationDate' in cfg:
        return cfg['termsPublicationDate']
    return cfg['publicationDate']


def date_text(cfg):
    return '%s, %s' % (cfg['publicationDate']['monthDay'], cfg['publicationDate']['year'])


def block_text(block):
    """The text of one source block: a paragraph's runs joined, or (for a list) one string per item."""
    if block['type'] == 'p':
        return ''.join(r[0] for r in block['runs'])
    if block['type'] == 'ul':
        return [''.join(r[0] for r in item) for item in block['items']]
    raise ValueError('unknown block type %r' % block['type'])


def expected_lines(doc):
    """The expected text lines of a document AFTER the documented edits, in page order (list items are lines of their own). Each edit must match exactly once."""
    return [line for line in _lines(doc)]


def _lines(doc):
    for b in doc['blocks']:
        t = block_text(b)
        if isinstance(t, list):
            for x in t:
                yield x
        else:
            yield t


def apply_edits(doc, edits, cfg, name=None):
    """Return a deep copy of the document with the documented edits applied at run level. Every edit must match EXACTLY once, or this raises (a silent no-op would hide a changed source)."""
    out = json.loads(json.dumps(doc))
    month_day = pub_date(cfg, name)['monthDay']
    year = str(pub_date(cfg, name)['year'])
    counts = [0] * len(edits)

    def fix_runs(runs):
        for run in runs:
            for i, e in enumerate(edits):
                if e['kind'] == 'owner-paragraph':
                    continue  # structural: it adds a block and is handled below, after the run-level edits
                find = e['find']
                if e['kind'] == 'date':
                    if find in run[0]:
                        n = run[0].count(find)
                        counts[i] += n
                        run[0] = run[0].replace(find, month_day)
                        # the year after the blank is part of the source (", 2026"); it must be the configured year
                        if (', ' + year) not in run[0]:
                            raise ValueError('date line does not carry the configured year %s: %r' % (year, run[0]))
                else:
                    if find in run[0]:
                        counts[i] += run[0].count(find)
                        run[0] = run[0].replace(find, e['replace'])

    for b in out['blocks']:
        if b['type'] == 'p':
            fix_runs(b['runs'])
        else:
            for item in b['items']:
                fix_runs(item)
    # `owner-paragraph` (an owner-authorised new paragraph; the only edit that adds a block): `replace` becomes a NEW plain paragraph directly after the block whose last line is exactly `find`
    # (a paragraph's whole text, or a list's last item), judged after the run-level edits above. It must match exactly one block, like every other edit.
    for i, e in enumerate(edits):
        if e['kind'] != 'owner-paragraph':
            continue
        hits = [bi for bi, b in enumerate(out['blocks'])
                if (''.join(r[0] for r in b['runs']) if b['type'] == 'p' else ''.join(r[0] for r in b['items'][-1])) == e['find']]
        counts[i] = len(hits)
        if len(hits) == 1:
            out['blocks'].insert(hits[0] + 1, {'type': 'p', 'runs': [[e['replace'], False, False]]})
    for i, e in enumerate(edits):
        if counts[i] != e.get('expect', 1):
            raise ValueError('edit %d (%s) matched %d time(s), expected %d: %r' % (i, e['kind'], counts[i], e.get('expect', 1), e['find']))
    return out


def runs_html(runs):
    out = ''
    for text, bold, italic in runs:
        t = esc(text)
        if bold and italic:
            t = '<strong><em>' + t + '</em></strong>'
        elif bold:
            t = '<strong>' + t + '</strong>'
        elif italic:
            t = '<em>' + t + '</em>'
        out += t
    return out


def blocks_html(doc):
    parts = []
    for b in doc['blocks']:
        if b['type'] == 'p':
            style = ' style="text-align:center"' if b.get('align') == 'center' else ''
            parts.append('<p%s>%s</p>' % (style, runs_html(b['runs'])))
        else:
            parts.append('<ul>\n' + '\n'.join('<li>%s</li>' % runs_html(item) for item in b['items']) + '\n</ul>')
    return '\n'.join(parts)


# ---------------------------------------------------------------- page template (the existing pages' look: inline CSS, header, content, footer)

CSS = (
    ":root{--cream:#F7EBD7;--foam:#FDF6EA;--cocoa:#4A2E1D;--cocoa-l:#6B4A33;--ocean:#1C8095;--brass:#B98A2F;--gold:#D4AF37;--green:#4A7C43}\n"
    "*{box-sizing:border-box}body{margin:0;font-family:Georgia,'Times New Roman',serif;background:var(--cream);color:var(--cocoa);line-height:1.65}\n"
    ".wrap{max-width:820px;margin:0 auto;padding:28px 22px 60px}\n"
    "header.site{background:var(--cocoa);color:var(--cream);padding:14px 0}\n"
    "header.site .wrap{padding:0 22px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px}\n"
    ".brand{font-size:1.25rem;font-weight:bold;letter-spacing:.5px;color:var(--cream);text-decoration:none}\n"
    ".brand span{color:var(--gold)}\n"
    "nav a{color:var(--cream);text-decoration:none;margin-left:18px;font-size:.95rem;opacity:.9}\n"
    "nav a:hover{opacity:1;text-decoration:underline}\n"
    "h1{color:var(--cocoa);font-size:1.7rem;margin:26px 0 4px}\n"
    "h2{color:var(--ocean);font-size:1.15rem;margin-top:28px}\n"
    ".meta{color:var(--cocoa-l);font-style:italic;margin-bottom:18px}\n"
    ".legal p{font-size:.98rem}.legal strong{color:var(--cocoa)}.legal ul{padding-left:1.4rem}.legal li{margin:.25rem 0}\n"
    ".legal a{color:var(--ocean)}\n"
    ".legal table{border-collapse:collapse;width:100%;margin:.4rem 0 1rem;font-size:.98rem}\n"
    ".legal th,.legal td{text-align:left;vertical-align:top;padding:.4rem 1.4rem .4rem 0;border-bottom:1px solid rgba(74,46,29,.18)}\n"
    ".legal th{color:var(--cocoa);font-size:.9rem}\n"
    ".avail{display:inline-block;background:#EFF7F4;border:1px solid var(--green);color:var(--green);border-radius:999px;padding:2px 12px;font-size:.82rem;font-weight:bold}\n"
    ".plans-wrap{overflow-x:auto;margin:.4rem 0 1rem}.plans-wrap table{margin:0}.legal table.plans td,.legal table.plans th{padding-right:1rem}\n"
    "@media(max-width:640px){.plans-wrap{overflow:visible}.legal table.plans,.legal table.plans tbody,.legal table.plans tr,.legal table.plans td{display:block;width:100%}.legal table.plans thead{display:none}.legal table.plans tr{padding:.7rem 0;border-bottom:1px solid rgba(74,46,29,.18)}.legal table.plans td{border:0;padding:.15rem 0}.legal table.plans td[data-th]:before{content:attr(data-th) \": \";font-weight:bold;color:var(--cocoa-l)}}\n"
    "footer{border-top:2px solid var(--brass);margin-top:48px;padding:18px 22px;text-align:center;font-size:.85rem;color:var(--cocoa-l)}\n"
    "footer a{color:var(--ocean)}"
)

TRADEMARK_LINE = 'SailCoCo and the SailCoCo flag logo are trademarks of SailCoCo LLC.'


# The address of each page as a root-relative clean URL (what GitHub Pages and the site's own server both serve); used for a page that can be shown at ANY address, such as 404.html, whose
# relative links would otherwise resolve against whatever path was asked for.
ROOT_LINKS = {'index.html': '/', 'index.html#pricing': '/#pricing', 'developers.html': '/developers', 'terms.html': '/terms', 'privacy.html': '/privacy', 'legal.html': '/legal'}


def _links(html, root):
    if not root:
        return html
    for rel, clean in ROOT_LINKS.items():
        html = html.replace('href="%s"' % rel, 'href="%s"' % clean)
    return html


def footer_html(with_legal, root=False):
    links = ['<a href="terms.html">Terms of Service</a>', '<a href="privacy.html">Privacy Policy</a>']
    if with_legal:
        links.append('<a href="legal.html">Legal information</a>')
    links.append('<a href="terms.html">Cancellation and refunds (Terms of Service, Section 5)</a>')
    return _links('<footer>SailCoCo LLC · Redwood City, California · <a href="mailto:support@sailcoco.com">support@sailcoco.com</a><br>\n'
                  + ' · '.join(links) + '<br>\n' + TRADEMARK_LINE + '</footer>', root)


def nav_html(with_legal, root=False):
    items = ['<a href="index.html">Home</a>', '<a href="index.html#pricing">Pricing</a>', '<a href="developers.html">Developers</a>', '<a href="terms.html">Terms</a>', '<a href="privacy.html">Privacy</a>']
    if with_legal:
        items.append('<a href="legal.html">Legal</a>')
    return _links('<nav>' + ' '.join(items) + '</nav>', root)


def page_html(title, content_html, with_legal, head_extra='', root=False):
    return ('<!DOCTYPE html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">%s\n'
            '<title>%s</title><style>\n%s\n</style></head><body>\n'
            '<header class="site"><div class="wrap"><a class="brand" href="%s">Sail<span>CoCo</span></a>\n%s</div></header>\n'
            '<div class="wrap legal">%s\n</div>\n%s\n</body></html>\n') % (head_extra, esc(title), CSS, '/' if root else 'index.html', nav_html(with_legal, root), content_html, footer_html(with_legal, root))


# ---------------------------------------------------------------- reading a page back (for the checks): the text of the content area, block by block

class _Blocks(HTMLParser):
    """Collects the visible text of every <p> and <li> inside <div class="wrap legal">, one string per element, in document order. Nothing else may sit in that div."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_legal = 0
        self.depth_div = 0
        self.cur = None
        self.blocks = []
        self.stray = []

    BLOCKS = ('p', 'li', 'h1', 'h2', 'h3', 'td', 'th')

    def _flush(self):
        if self.cur is not None:
            self.blocks.append(''.join(self.cur))
            self.cur = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'div':
            if self.in_legal:
                self.in_legal += 1
            elif a.get('class') == 'wrap legal':
                self.in_legal = 1
            return
        if not self.in_legal:
            return
        if tag in self.BLOCKS:
            if self.cur is not None:
                if tag == 'li':
                    self._flush()          # a nested list item: the outer item's own text so far is one block, the nested items follow
                else:
                    self.stray.append('nested block <%s> inside another block' % tag)
                    self._flush()
            self.cur = []
        elif tag == 'br' and self.cur is not None:
            self.cur.append('\n')

    def handle_endtag(self, tag):
        if tag == 'div' and self.in_legal:
            self.in_legal -= 1
            return
        if self.in_legal and tag in self.BLOCKS:
            self._flush()

    def handle_data(self, data):
        if not self.in_legal:
            return
        if self.cur is not None:
            self.cur.append(data)
        elif data.strip():
            self.stray.append(data.strip()[:60])


def page_blocks(html_text):
    p = _Blocks()
    p.feed(html_text)
    p.close()
    return p.blocks, p.stray
