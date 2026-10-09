#!/usr/bin/env python3
"""Build terms.html, privacy.html and (once hasLegalPage is true) legal.html from legal-sources/*.json (see tools/legal_lib.py for the rule: copied, never drafted).

usage: python3 tools/build_legal.py            write the pages
       python3 tools/build_legal.py --check    exit 1 if a committed page differs from what the sources generate (CI runs this)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import legal_lib as L  # noqa: E402
import legal_md  # noqa: E402

DOCS = {
    'terms': {'out': 'terms.html', 'title': 'Terms of Service — SailCoCo'},
    'privacy': {'out': 'privacy.html', 'title': 'Privacy Policy — SailCoCo'},
}


def build():
    cfg = L.config()
    edits = L.load_json('legal-sources/edits.json')
    pages = {}
    for name, d in DOCS.items():
        doc = L.load_json('legal-sources/%s.json' % name)
        edited = L.apply_edits(doc, edits[name], cfg)
        pages[d['out']] = L.page_html(d['title'], L.blocks_html(edited), cfg['hasLegalPage'])
    if cfg['hasLegalPage']:
        md = open(os.path.join(L.ROOT, 'legal-sources', 'legal.md'), encoding='utf-8').read()
        content, _ = legal_md.convert(md, L.date_text(cfg))
        pages['legal.html'] = L.page_html('Legal information \u2014 SailCoCo', content, True)
    return pages


def main():
    check = '--check' in sys.argv
    pages = build()
    bad = 0
    for out, text in pages.items():
        path = os.path.join(L.ROOT, out)
        if check:
            have = open(path, encoding='utf-8').read() if os.path.exists(path) else None
            if have != text:
                print('FAIL %s differs from what legal-sources/ generates (run python3 tools/build_legal.py)' % out)
                bad += 1
            else:
                print('ok   %s is exactly what legal-sources/ generates (%d bytes)' % (out, len(text.encode('utf-8'))))
        else:
            with open(path, 'w', encoding='utf-8', newline='\n') as f:
                f.write(text)
            print('wrote %s (%d bytes)' % (out, len(text.encode('utf-8'))))
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
