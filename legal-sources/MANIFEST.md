# Legal sources: what the pages are generated from

Legal text on this site is **copied from counsel's documents, never drafted or edited here** (site publication rules of 9 Oct 2026). Each page is generated from a structured source in this
directory, and `python3 tools/check_site.py` (run by CI on every pull request and every push to `main`) fails if a page differs from its source by anything other than the edits listed in
`edits.json`.

| Page | Source document (counsel, round 2, final "CLEAN" version) | Bytes | SHA-256 |
|---|---|---|---|
| `terms.html` | CLEAN 01 SailCoCo LLC - Terms of Service v4.docx | 40289 | `0d4742fa16de0aa3acd69e0eed9f1b7dfc25eb70886d2ef24cc4012f740e392e` |
| `privacy.html` | CLEAN 02 SailCoCo LLC - Privacy Policy v5.docx | 31803 | `20d96149e04695758178f5138887b750a37ecd714c1ae85ae3cc4141746f7403` |

## Text supplied directly (not extracted from a .docx)

| Page | Source | Bytes | SHA-256 |
|---|---|---|---|
| `legal.html` | `legal-sources/legal.md`, a byte-for-byte copy of the approved text (filed 2026-10-09), rendered word for word by `tools/legal_md.py`; the only change is the publication date filled into `Last updated:` | 2854 | `13dc3d45b13f83f76f22d1b8472e0c5dcdf3f75440cfaa15dd52262cb1fb72d6` |

## Developer figures (the documents are not published)

The developer plan figures on `developers.html` come from `developer-figures.json`. The developer documents themselves are not published and are not in this repository; their size and SHA-256 are recorded here so anyone holding the files can re-check, and `python3 tools/verify_developer_figures.py <developer-terms.docx> <api-policy.docx>` re-reads every figure from the clause it cites (run locally; CI does not have the files).

| Document | Bytes | SHA-256 |
|---|---|---|
| Developer Terms (order form), final version | 50633 | `16647ad8c11f104f3d9214acaa7bfc8b676e58bb1b38b3c2ab7d55be2f42cfe7` |
| API Usage and Attribution Policy, final version | 22980 | `6092f288f074858aa6247fba1003580fabaf3ed6cad756ec2288cb220b754e6c` |

## How the sources were made

`tools/extract_docx.py` reads the `.docx` body (`word/document.xml`) and writes `<name>.json` (paragraphs and bulleted lists, with bold and italic runs) and `<name>.txt` (one line per paragraph or
list item). It uses only the Python standard library, involves no model, and stops instead of guessing when it meets anything it does not support (tables, numbered lists, tracked changes,
hyperlinks, fields, footnotes, comments). The `.docx` files themselves are not committed. To re-check an extraction, run the same command on the file with the SHA-256 above and compare:

```
python3 tools/extract_docx.py "<file>.docx" terms --title "Terms of Service v4"
git diff --stat legal-sources/
```

## The only edits allowed (`edits.json`)

1. **The publication date** is filled into the blank date lines of the Terms (`Last Updated`) and the Privacy Policy (`Effective Date`, `Last Updated`). The date is `site-config.json`'s
   `publicationDate`: the day the pull request is merged.
2. **Privacy section 15**: `, USA` is added after `California 94065` in the postal address, to match every other document (the one typo fix that was authorised).

Everything else, every heading, number, list and sentence, is the document's own text. Header and footer text inside the `.docx` (page numbers and the like) is not part of the body and is not published.
