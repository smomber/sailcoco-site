#!/usr/bin/env python3
"""Extract a .docx into legal-sources/<name>.json and <name>.txt, deterministically (standard library only; no model in the loop).

usage: tools/extract_docx.py <file.docx> <name> --title "<title>" [--file-name "<original file name>"]

Run locally, once per source document; CI does not have the .docx files (they are counsel's work product, not committed). The JSON carries the document's body in order:
  {"type":"p","align":"center"?,"runs":[[text,bold,italic],...]}      one paragraph
  {"type":"ul","items":[[runs],[runs],...]}                            consecutive bulleted paragraphs
Only what the CLEAN documents use is supported; anything else (tables, numbered lists, tracked changes, hyperlinks, fields, footnotes) STOPS the extraction rather than being guessed at.
The .txt is one line per paragraph or list item. legal-sources/MANIFEST.md records each source's file name, size and SHA-256 so the extraction can be re-run and compared by anyone with the file.
"""
import hashlib
import json
import os
import sys
import zipfile
from xml.etree import ElementTree as ET

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def flag(rpr, tag):
    if rpr is None:
        return False
    el = rpr.find(W + tag)
    return el is not None and el.get(W + 'val', 'true') not in ('0', 'false', 'off')


def para_runs(p):
    runs = []
    for r in p.iter(W + 'r'):
        rpr = r.find(W + 'rPr')
        bold, italic = flag(rpr, 'b'), flag(rpr, 'i')
        txt = ''
        for ch in r:
            if ch.tag == W + 't':
                txt += ch.text or ''
            elif ch.tag in (W + 'tab', W + 'br', W + 'cr', W + 'noBreakHyphen', W + 'fldChar', W + 'instrText', W + 'footnoteReference', W + 'endnoteReference'):
                raise SystemExit('unsupported run content <%s> in paragraph %r: stop, do not guess' % (ch.tag.replace(W, ''), ''.join(x.text or '' for x in p.iter(W + 't'))[:60]))
        if txt:
            if runs and runs[-1][1] == bold and runs[-1][2] == italic:
                runs[-1][0] += txt          # adjacent runs with identical formatting are one run
            else:
                runs.append([txt, bold, italic])
    return runs


def main():
    args = sys.argv[1:]
    if len(args) < 2 or '--title' not in args:
        raise SystemExit(__doc__)
    path, name = args[0], args[1]
    title = args[args.index('--title') + 1]
    file_name = args[args.index('--file-name') + 1] if '--file-name' in args else os.path.basename(path)
    raw = open(path, 'rb').read()
    z = zipfile.ZipFile(path)
    bad = z.testzip()
    if bad:
        raise SystemExit('zip CRC failure in %s' % bad)
    root = ET.fromstring(z.read('word/document.xml'))
    doc_xml = z.read('word/document.xml').decode('utf8')
    for tag, why in (('<w:ins ', 'tracked insertion'), ('<w:del ', 'tracked deletion'), ('<w:hyperlink', 'hyperlink'), ('<w:tbl>', 'table'), ('commentReference', 'comment')):
        if tag in doc_xml:
            raise SystemExit('unsupported content in %s: %s; stop, do not guess' % (path, why))
    numbering = z.read('word/numbering.xml').decode('utf8') if 'word/numbering.xml' in z.namelist() else ''
    if '<w:numFmt w:val="decimal"' in numbering or '<w:numFmt w:val="lowerLetter"' in numbering or '<w:numFmt w:val="upperRoman"' in numbering:
        raise SystemExit('this document has numbered (not bulleted) lists; the extractor only supports bullets: stop, do not guess')
    body = root.find(W + 'body')
    blocks = []
    for el in body:
        if el.tag != W + 'p':
            if el.tag in (W + 'sectPr',):
                continue
            raise SystemExit('unsupported body element <%s>' % el.tag.replace(W, ''))
        runs = para_runs(el)
        ppr = el.find(W + 'pPr')
        numbered = ppr is not None and ppr.find(W + 'numPr') is not None
        jc = ppr.find(W + 'jc') if ppr is not None else None
        align = jc.get(W + 'val') if jc is not None else None
        if not runs:
            continue                      # an empty paragraph is spacing, not text
        if numbered:
            if blocks and blocks[-1]['type'] == 'ul':
                blocks[-1]['items'].append(runs)
            else:
                blocks.append({'type': 'ul', 'items': [runs]})
            continue
        b = {'type': 'p', 'runs': runs}
        if align == 'center':
            b['align'] = 'center'
        elif align not in (None, 'left', 'both'):
            raise SystemExit('unsupported paragraph alignment %r' % align)
        blocks.append(b)
    doc = {
        'title': title,
        'source': {'fileName': file_name, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()},
        'blocks': blocks,
    }
    out_dir = os.path.join(ROOT, 'legal-sources')
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, name + '.json'), 'w', encoding='utf-8') as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
        f.write('\n')
    lines = []
    for b in blocks:
        if b['type'] == 'p':
            lines.append(''.join(r[0] for r in b['runs']))
        else:
            lines.extend(''.join(r[0] for r in item) for item in b['items'])
    with open(os.path.join(out_dir, name + '.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    print('%s: %d blocks, %d text lines, %d bytes in, sha256 %s' % (name, len(blocks), len(lines), len(raw), doc['source']['sha256']))


if __name__ == '__main__':
    main()
