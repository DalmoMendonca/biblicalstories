# Biblische Historien — Johann Hübner

An illustrated, open-access edition of Johann Hübner's *Zweymal zwey und fünfzig auserlesene Biblische Historien* (1714), presenting archival engravings, facsimile sources, and a multilingual scholarly reading interface.

## Editorial policy

- Every reproduced historical image is attributed to the edition that supplies it.
- German, Russian, and English texts are versioned **separately**; no text is presented as a verified historical transcription unless it has been checked against its source.
- The 1815 Russian illustration set associated with Dostoevsky is distinct from German plates until a match is demonstrated.
- Machine OCR is labeled and never silently passed off as proofread copy.


## Experience

The rebuilt application presents **104 individually cropped eighteenth-century engravings** as the art, not full-page photographs. View the complete 52+52 plate index, filter by Testament, search, switch English/German/Russian navigation without losing the current story, and examine the original German text on the 324 archived 1768 book folios. The visual design is an editorial index without promotional hero, image cards, artificial copy, or decorative ornaments.

The **complete historical English (1765)** and **Russian (1815)** story transcriptions are still outstanding editorial work, and so are the distinct 35+1 Russian engraved illustrations. An **1825 Russian edition** with digitized Old and New Testament volumes is linked as a later original-language witness. These are transparently represented as source gaps, rather than filled by invented text or AI drawings.

## Reproduce locally

```bash
git clone https://github.com/DalmoMendonca/biblicalstories.git
cd biblicalstories
npm run check
npm run build
python3 -m http.server 8123 --directory dist
```

Open http://localhost:8123. The source images and original German folios are versioned in the repository; reading images does not require a live library image server. Re-import source facsimiles with `python3 scripts/harvest.py` and regenerate all individual illustrations with `python3 scripts/crop_plates.py` (Pillow required). Crop coordinates and per-image provenance live in `public/data/crop-provenance.json`.

## Netlify publication

The reserved Netlify project is [biblicalstories-ytdf](https://app.netlify.com/projects/biblicalstories-ytdf) (the short name biblicalstories was already taken).

To turn on continuous deployment, connect the GitHub repository `DalmoMendonca/biblicalstories` to that existing Netlify project, with production branch `main`. The checked-in `netlify.toml` already specifies the static build and `dist` output directory. No secret environment variables or paid services are required.

## Primary sources

- [Zürich ca. 1775, Zentralbibliothek Zürich](https://www.e-rara.ch/zuz/doi/10.3931/e-rara-85573) — [IIIF manifest](https://www.e-rara.ch/i3f/v20/24283792/manifest) and [uncorrected OCR](https://www.e-rara.ch/zuz/download/ftpack/plain/24283792), Public Domain Mark.
- [Giessen 1768, Heidelberg University Library](https://digi.ub.uni-heidelberg.de/diglit/huebner1768) — 104 accompanying engravings in historical edition.
- [Russian illustrated edition, St Petersburg 1815](https://search.rsl.ru) — Vasily Bogorodsky translation; its original image plates remain unverified. The [1825 Old Testament](https://kp.rusneb.ru/item/material/5fcf8bb3991f3b91423439b5) and [1825 New Testament](https://kp.rusneb.ru/item/material/sto-chetyre-svyashchennyya-istorii-pyatdesyat-dve-svyashchennyya-istorii-iz-novago-zaveta--ch2) have digitized historic book scans.
- [1765 trilingual historical edition](https://books.google.com/books?id=5elUAAAAcAAJ) — German, French, English, complete digitization under investigation.

The project uses a static-first frontend with progressive enhancement. See `SOURCES.md` for source-by-source evidence, provenance, and outstanding textual research.
