# Hübner · 104 Biblische Historien

<!-- impeccable:product-schema 1 -->

## Platform
web

## Product
Open-access visual critical edition of Johann Hübner’s 104 biblical histories: 52 Old Testament, 52 New Testament. Scholarly provenance is essential. The book is not a generic Bible storytelling product.

## Primary user task
Look at all 104 ORIGINAL historical engravings without page scan distractions; open a story and read the historically attested full text in German, English, or Russian, where the actual edition has been obtained.

## Nonnegotiable requirements
1. Use individually cropped original engraved illustrations—not full-page photo scans—for the primary interface.
2. One original engraved scene per story, correctly mapped; preserve the unmodified source image and the crop geometry.
3. No made-up marketing microcopy, invented source text, AI illustration, decorative fluff, or scriptural paraphrase passing as Hübner’s original.
4. English / German / Russian language switches retain the story and change content only where an actual edition’s words are available.
5. Never mix Russian 1815 plates with German 1768 artwork under a false attribution.
6. Mobile and desktop must be complete and readable, without external rendering dependencies for artwork.

## Source availability
The Giessen 1768 German 104 plates and 324 original text-folio scans have been archived locally; the end-of-book plate 52 indexing error is being corrected. The Zürich circa-1775 German edition offers uncorrected whole-book OCR, not a proofread 1768 transcription. The historical English 1765 version exists but 104 source-checked chapter transcriptions are not yet in the repository. The illustrated 1815 Bogorodsky Russian text is bibliographically known, but its 35+1 plates and full text are not yet in the repository.

## Stack
Static HTML, CSS and JS; original images cropped using Pillow and versioned in GitHub; bundled build via scripts/build.py, deployable on Netlify.
