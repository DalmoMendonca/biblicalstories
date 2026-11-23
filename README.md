# Biblische Historien — Johann Hübner

**Live illustrated edition:** https://biblicalstories.dalmo.ai

An open-access reader for Johann Hübner's *Zweymal zwey und fünfzig auserlesene Biblische Historien*, first published in 1714.

## Contents

- **104 original eighteenth-century engravings**, one per history, 52 Old Testament and 52 New Testament. The artworks are from the Giessen **1768** printing digitized by Heidelberg University Library.
- **Per-sheet perspective correction:** the original photographed leaves remain under `public/art/`. `scripts/crop_plates.py` detects the engraved frame on each scan and applies a four-corner rectification, preserving genuine engraved pixels without generative alteration. The 104 corrected images and thumbnails are in `public/engravings/`, with per-image geometry in `public/data/crop-provenance.json`.
- **324 locally archived German page facsimiles** from the same 1768 printing in `public/folios/`.
- **312 unverified machine-generated drafts are archived**, not authenticated historical transcriptions. The reader does **not** render those corrupted texts as finished editions. It links to the historical English and Russian sources and opens the genuine German page facsimiles for each story.

## Textual provenance — essential

The three available texts are **not three independently verified historical editions**:

| Language | Actual text supplied | Verification |
|---|---|---|
| German | Automated Fraktur OCR of the Giessen 1768 **original German printed pages** | **Uncorrected**; may include recognition errors, running headers, and two-column ordering artifacts |
| English | Modern machine translation from the above German OCR | **Not** the historical 1765 English translation; not proofread |
| Russian | Modern machine translation from the above German OCR | **Not** the Bogorodsky 1815/1825 historical Russian translation; not proofread |

Every chapter preserves source-page references and a link to the scanned original. Mechanical completeness validation confirms 104 × 3 **draft** records; verified historical transcription coverage is currently **zero** for each language. The reader hides those drafts rather than suggesting they are readable originals. The historical 1765 English and 1815 Russian editions remain future scholarly transcription witnesses. The separate 35+1 illustrations of the Dostoevsky-related Russian edition are not conflated with our German plate series.

## Run locally

```bash
git clone https://github.com/DalmoMendonca/biblicalstories.git
cd biblicalstories
npm run check
python3 scripts/check_texts.py
npm run build
python3 -m http.server 8123 --directory dist
```

Open http://localhost:8123. All publication images and all 312 texts are committed to GitHub; the deployed site does not depend on runtime requests to Heidelberg or external translation services.

## Deploy

[Netlify: 104biblicalstories](https://app.netlify.com/projects/104biblicalstories) is connected to the GitHub `main` branch, publishing automatically to **https://biblicalstories.dalmo.ai**. `netlify.toml` defines the static `dist` build.

## Historical sources

- [Giessen 1768, Heidelberg University Library](https://digi.ub.uni-heidelberg.de/diglit/huebner1768) — original plates and original-text page facsimiles used in this app.
- [Zürich ca. 1775, Zentralbibliothek Zürich](https://www.e-rara.ch/zuz/doi/10.3931/e-rara-85573) — alternative illustrated public-domain printing and uncorrected OCR for comparison, not silently substituted for Giessen.
- [St Petersburg 1815 Russian edition](https://search.rsl.ru) — Vasily Bogorodsky translation, edition related to Dostoevsky; historically documented 35 plates and a frontispiece, complete digital plates not yet obtained.
- [1825 Russian Old Testament](https://kp.rusneb.ru/item/material/5fcf8bb3991f3b91423439b5) — later Russian source facsimile.
- [1765 German–French–English parallel edition](https://books.google.com/books?id=5elUAAAAcAAJ) — historical English translation bibliographic record.

See [SOURCES.md](./SOURCES.md) for image, facsimile and text provenance details.
