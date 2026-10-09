#!/usr/bin/env python3
"""A converter for exactly the Markdown subset used by legal-sources/legal.md (the approved legal page text, filed 2026-10-09 and copied here word for word).

Supported, and nothing else (anything else raises, so a changed source cannot be half-rendered): '# ', '## ' headings; paragraphs; a trailing backslash as a hard line break;
**bold**; [text](/path) links; '- ' bullets with two-space-indented '- ' sub-bullets; one pipe table with a header row and a '|---|---|' separator.
It also returns the expected TEXT lines of the page (for tools/check_site.py): the same text with the Markdown syntax removed.
"""
import re

from legal_lib import esc

LINK = re.compile(r'\[([^\]]+)\]\((/[a-z0-9/_-]*)\)')
BOLD = re.compile(r'\*\*([^*]+)\*\*')


def _plain(seg, whole):
    for bad in ('**', '[', ']'):
        if bad in seg:
            raise ValueError('unsupported or unbalanced inline markup (%r) in %r' % (bad, whole))
    return esc(seg)


def inline_html(s):
    out, last = '', 0
    tokens = sorted([(m.start(), m.end(), 'link', m) for m in LINK.finditer(s)] + [(m.start(), m.end(), 'bold', m) for m in BOLD.finditer(s)], key=lambda t: t[:2])
    for start, end, kind, m in tokens:
        if start < last:
            raise ValueError('overlapping inline markup in %r' % s)
        out += _plain(s[last:start], s)
        if kind == 'link':
            out += '<a href="%s">%s</a>' % (esc(m.group(2)), _plain(m.group(1), s))
        else:
            out += '<strong>%s</strong>' % _plain(m.group(1), s)
        last = end
    return out + _plain(s[last:], s)


def inline_text(s):
    s = LINK.sub(lambda m: m.group(1), s)
    s = BOLD.sub(lambda m: m.group(1), s)
    return s


def convert(md, date_text):
    """Return (content_html, expected_text_lines). `date_text` replaces the '[publication date]' placeholder (exactly once)."""
    if md.count('[publication date]') != 1:
        raise ValueError('the source must carry the [publication date] placeholder exactly once')
    md = md.replace('[publication date]', date_text)
    lines = md.split('\n')
    html, text = [], []
    i = 0
    while i < len(lines):
        ln = lines[i]
        if not ln.strip():
            i += 1
            continue
        if ln.startswith('# '):
            html.append('<h1>%s</h1>' % inline_html(ln[2:]))
            text.append(inline_text(ln[2:]))
            i += 1
        elif ln.startswith('## '):
            html.append('<h2>%s</h2>' % inline_html(ln[3:]))
            text.append(inline_text(ln[3:]))
            i += 1
        elif ln.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].startswith('|'):
                rows.append([c.strip() for c in lines[i].strip().strip('|').split('|')])
                i += 1
            if len(rows) < 3 or not all(re.fullmatch(r':?-{3,}:?', c) for c in rows[1]):
                raise ValueError('unsupported table')
            head, body = rows[0], rows[2:]
            html.append('<table>\n<thead><tr>' + ''.join('<th>%s</th>' % inline_html(c) for c in head) + '</tr></thead>\n<tbody>\n'
                        + '\n'.join('<tr>' + ''.join('<td>%s</td>' % inline_html(c) for c in r) + '</tr>' for r in body) + '\n</tbody>\n</table>')
            for r in [head] + body:
                text.extend(inline_text(c) for c in r)
        elif ln.startswith('- '):
            items = []                       # (level, text)
            while i < len(lines) and (lines[i].startswith('- ') or lines[i].startswith('  - ')):
                items.append((0, lines[i][2:]) if lines[i].startswith('- ') else (1, lines[i][4:]))
                i += 1
            out, open_sub = ['<ul>'], False
            for k, (lvl, t) in enumerate(items):
                nxt = items[k + 1][0] if k + 1 < len(items) else 0
                if lvl == 0:
                    out.append('<li>%s' % inline_html(t) + ('' if nxt == 1 else '</li>'))
                    if nxt == 1:
                        out.append('<ul>')
                        open_sub = True
                else:
                    out.append('<li>%s</li>' % inline_html(t))
                    if nxt == 0 and open_sub:
                        out.append('</ul></li>')
                        open_sub = False
                text.append(inline_text(t))
            out.append('</ul>')
            html.append('\n'.join(out))
        else:
            para = []
            while i < len(lines) and lines[i].strip() and not lines[i].startswith(('#', '|', '- ')):
                para.append(lines[i])
                i += 1
            parts = []
            for k, p in enumerate(para):
                hard = p.endswith('\\')
                body = p[:-1] if hard else p
                parts.append(inline_html(body) + ('<br>' if hard and k + 1 < len(para) else ''))
                if hard and k + 1 == len(para):
                    raise ValueError('a hard line break on the last line of a paragraph: %r' % p)
            html.append('<p>%s</p>' % '\n'.join(parts))
            # text: the lines of one paragraph are ONE text block (joined by a space after normalisation; the <br> becomes whitespace)
            text.append(' '.join(inline_text(p[:-1] if p.endswith('\\') else p) for p in para))
    return '\n'.join(html), text
