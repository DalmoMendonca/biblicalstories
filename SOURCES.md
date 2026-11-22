# Source inventory and editorial integrity

## One-to-one illustrated edition: 1768 (primary artwork)

**Johann Hübner.** *Zweymal zwey und funfzig auserlesene Biblische Historien*, Giessen: Johann Christoph Schröder, 1768. Universitätsbibliothek Heidelberg, digital item `huebner1768`.

- [Browse facsimile](https://digi.ub.uni-heidelberg.de/diglit/huebner1768)
- [IIIF Presentation API manifest](https://digi.ub.uni-heidelberg.de/diglit/iiif/huebner1768/manifest.json)
- The manifest has 567 canvases and precisely 104 individually labelled engravings, **Tafel 1…52 twice** in the Old / New Testament sequence.
- Each image stored at `public/art/<three-digit-id>.webp`, with a 600px thumbnail in `public/art/thumb/`.
- `public/data/archive.json` is an unambiguous machine-readable provenance ledger for every image. It records original IIIF JPEG URI, source-page link, archival label and original German folio references.
- The original Heidelberg scan contains archival marks and facsimile page borders. We do not remove or “restore” marks for false antiquarian authenticity.
- Reproductions are of public-domain eighteenth-century artwork; archive attribution is retained for scholarly ethics.

## German witness: Zürich, c. 1775

**Johann Hübner.** Zürich: Bürklische Druckerei, circa 1775. Zentralbibliothek Zürich, AWZ 727. DOI [10.3931/e-rara-85573](https://doi.org/10.3931/e-rara-85573).

- [Zürich IIIF facsimile](https://www.e-rara.ch/i3f/v20/24283792/manifest): 632 digital pages.
- [Uncorrected machine-readable German OCR](https://www.e-rara.ch/zuz/download/ftpack/plain/24283792), retained in `public/data/german-ocr.txt`. It is visibly noisy Fraktur OCR and **not a proofread historical edition**.
- Public Domain Mark on the digitized edition. Do not mix this version's OCR into 1768 story pages without visible version identification and human validation.

## Russian: 1815, outstanding primary source

**Сто четыре Священные Истории, выбранные из Ветхого и Нового Завета, в пользу юношества**. Johann Hübner, translated from an edition revised by Johann Gottfried Fleck by Vasily Bogorodsky. St Petersburg: I. Baikov's printing house, 1815.

- Edition documented with **35 illustrated leaves plus a separate frontispiece**, making 36.
- Scholarly and museum research associates copies of this edition with Dostoevsky's family reading. Survival does not establish that a complete digitized set is obtainable.
- Do **not** identify the German 1768 plates as the illustrations used by Dostoevsky; physical similarities require plate-by-plate comparison and provenance.
- The complete verified 1815 text/plates have not yet been transcribed or acquired for this repository.

## English: 1765, outstanding per-story transcription

A German/French/English parallel version of Hübner's Histories was published in Hamburg in 1765.

- [Google Books bibliographic/facsimile record](https://books.google.com/books?id=5elUAAAAcAAJ)
- An English edition exists; a checked, complete 104-story extracted transcription has **not** yet been incorporated. Do not present AI translation as if it were a historical publication.

## Story labels
`src/catalog.js` contains three-language **modern editorial navigation labels**, based on the known historic narrative order and biblical subject matter. The labels are not original chapter headings or historical transcriptions and must not be quoted as such.

## Restoration and audit
Run `python3 scripts/harvest.py` to re-acquire all archival assets using the two original manifests. Run `npm run check` and `python3 scripts/build.py` to confirm completeness and generate the static deployment. GitHub Actions preserves this process, with a positive assertion on image count and order. The site refuses to render an incomplete archive rather than quietly showing unrelated artwork.

## Future text authentication
An original-text milestone is complete only when:
1. all 104 text segments are accounted for in the stated edition;
2. beginnings and ends checked against facsimile, including questions, moral lessons, and devotional thoughts;
3. every passage has bibliographic source and page reference;
4. uncertain OCR recognized as uncertain, not silently “corrected” by generation;
5. translations and changes between editions remain distinguished.
