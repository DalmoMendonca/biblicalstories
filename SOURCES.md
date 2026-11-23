# Source inventory and editorial integrity

## One-to-one illustrated edition: 1768 (primary artwork)

**Johann Hübner.** *Zweymal zwey und funfzig auserlesene Biblische Historien*, Giessen: Johann Christoph Schröder, 1768. Universitätsbibliothek Heidelberg, digital item `huebner1768`.

- [Browse facsimile](https://digi.ub.uni-heidelberg.de/diglit/huebner1768)
- [IIIF Presentation API manifest](https://digi.ub.uni-heidelberg.de/diglit/iiif/huebner1768/manifest.json)
- The manifest has 567 canvases and precisely 104 individually labelled engravings, **Tafel 1…52 twice** in the Old / New Testament sequence.
- Unaltered photographic scans are stored at `public/art/<three-digit-id>.webp`. **The app displays only the engraved image**: exact spatial crops at `public/engravings/<three-digit-id>.webp` and `public/engravings/thumb/`, with pixel coordinates, original dimensions, and per-plate provenance in `public/data/crop-provenance.json`. Crop generation is reproducible with `scripts/crop_plates.py`.
- `public/data/archive.json` is an unambiguous machine-readable provenance ledger for every image. It records original IIIF JPEG URI, source-page link, archival label and original German folio references.
- The original Heidelberg scans contain paper margins, caption cartouches, and archival marks; these are retained intact in the source facsimiles and only **excluded by spatial cropping** from the displayed artwork. No drawing, retouching, or generative alterations are performed. Heidelberg's final plate was mislabelled in the manifest: `Tafel 52` at canvas 551 points to blank verso. The correct engraved recto is canvas 550 labelled `dz`; `scripts/harvest.py` fixes this and rejects blank crops.
- Reproductions are of public-domain eighteenth-century artwork; archive attribution is retained for scholarly ethics.

## Verified publication status (November 2026)

- **104/104** illustration crops have been individually perspective-normalized. The final pass used 99 automatically estimated four-corner engraving frames and five earlier four-edge perspective transforms. Each crop's geometry and method are recorded in `public/data/crop-provenance.json`. Manual inspection also identified and removed residual printed-caption bands from plates 8, 12, and 94.
- **104/104** chapter-level JSON records are present in `public/texts/`, yielding **312** nonempty German/English/Russian text fields. Automated validation checks alignment, distinctness, length, source attribution, and the uncorrected/modern-translation labels.
- **Live site:** https://biblicalstories.dalmo.ai. A production-domain smoke test successfully requested all 104 text records, tested their three languages, and retrieved original plate crops. Chromium desktop/mobile tests confirmed language selection and text rendering for samples including chapters 3, 71, 87 and 104.
- **Important limitation:** the mechanical completion tests do not make Fraktur OCR or machine translation proofread or certify the 1765 and 1815 historic translations. Those historical editions and the original Russian engraving set remain independent scholarly work.

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
- The [digitized Russian 1825 Old Testament](https://kp.rusneb.ru/item/material/5fcf8bb3991f3b91423439b5) and [New Testament](https://kp.rusneb.ru/item/material/sto-chetyre-svyashchennyya-istorii-pyatdesyat-dve-svyashchennyya-istorii-iz-novago-zaveta--ch2) are accessible public digital facsimiles of a later edition. The app links to the correct book for each Testament, not falsely to the 1815 witness.

## English: 1765, outstanding per-story transcription

A German/French/English parallel version of Hübner's Histories was published in Hamburg in 1765.

- [Google Books bibliographic/facsimile record](https://books.google.com/books?id=5elUAAAAcAAJ)
- An English edition exists; a checked, complete 104-story extracted transcription has **not** yet been incorporated. Do not present AI translation as if it were a historical publication.

## Story labels
`src/catalog.js` contains three-language **modern editorial navigation labels**, based on the known historic narrative order and biblical subject matter. The labels are not original chapter headings or historical transcriptions and must not be quoted as such.

## Restoration and audit
Run `python3 scripts/harvest.py` to re-acquire all archival assets using the two original manifests, then `python3 scripts/crop_plates.py` to reproduce the artwork-only crops. Run `npm run check` and `python3 scripts/build.py` to confirm completeness and generate the static deployment. GitHub Actions preserves this process, with a positive assertion on image count and order. The site refuses to render an incomplete archive rather than quietly showing unrelated artwork.

## Future text authentication
An original-text milestone is complete only when:
1. all 104 text segments are accounted for in the stated edition;
2. beginnings and ends checked against facsimile, including questions, moral lessons, and devotional thoughts;
3. every passage has bibliographic source and page reference;
4. uncertain OCR recognized as uncertain, not silently “corrected” by generation;
5. translations and changes between editions remain distinguished.

## Full-text production pipeline (2026)

The application can serve one chapter-level JSON for each of 104 stories. The text generator is `scripts/produce_texts.py`, launched by `.github/workflows/produce-texts.yml`:

- **German** (`de`): an **uncorrected transcription by Fraktur-specific OCR of the actual 1768 Giessen pages** in `public/folios/`. A transcription error is *not* a historical variant. This is not yet a proofread critical text.
- **English** (`en`): a new **machine translation of the German OCR transcription**, not the published 1765 English edition. Labelled `modern-machine-translation-of-1768-ocr` in every JSON record.
- **Russian** (`ru`): a new **machine translation of the German OCR transcription**, not Bogorodsky's historical 1815 translation, nor the 1825 Russian printed witness. Same source/quality distinction as English.

Original full German folios are preserved as independently inspectable source images. Each generated German text record keeps the original page URLs and `editorial.proofread:false`. The special case of chapter 69 (New Testament XVII), where the Heidelberg numbering attaches no text leaves immediately to its engraving, uses adjacent source folios with an explicit collation warning. Machine translation can magnify OCR errors; those outputs must not be represented as historic original translations or quoted as verified literary sources.

The generator checks every language for nonempty content and the production build refuses a partial import (1–103 of 104 JSON files). The generated `public/data/text-coverage.json` records actual coverage rather than promising completeness before verification.
