# Design direction — HISTORIEN / an eighteenth-century image index

## A replacement, not a refinement

The former site’s two-panel promotional hero, invented marketing descriptions, badges, sample prose, image-card frames, faux-library ornament, and oversized footers are discarded. This application is an **edition of a historic book**, not a modern promotional site.

## Core
Every one of Hübner’s 104 engravings, extracted cleanly from its archival photograph, is the visual unit. Art is not a thumbnail inside a graphic card. The historical ink itself provides color, texture and character. No AI-generated illustrations, altered engraved scenes or substitute page images.

## World
A rigorously typeset antiquarian catalogue meets a contemporary art-book reader. Ivory uncoated paper, deepest near-black ink, tiny functional sans navigation, and generous EB Garamond titles. A muted oxblood selection line is the sole accent. No gradients, floating cards, bevels, shadows, badges, hype copy, or decorative panels.

## Modes
- Index: Experience. One engraving per story, in original numbered order.
- Reader: Read. Engraving leads, original edition text follows. Language choice does not change the story number or the artwork.

## Typography
- EB Garamond for story headings and historical text, suitable for Cyrillic and Latin.
- Inter for controls; comfortable touch targets and active-state clarity.
- No ornamental title invented by marketing: the book’s authentic name *Biblische Historien* is the masthead.

## Structure
- **No landing page.** Root opens the visual 104-plate catalogue immediately.
- Top bar: Biblische Historien on left, one simple EN / DE / RU switch and a search control on right.
- Testament selectors are plain text, with counts 52 + 52.
- Gallery: four columns desktop, three tablet, two mobile. Engravings occupy the cell with almost no surrounding frame; original numbering and scene title below. The full historical scan is accessible separately.
- Reader: large, uncropped **engraved artwork** (not a scanned sheet) next to the edition text. One visible language choice. Quiet previous/next arrows and source links.
- Original printed folio pages live in an unobtrusive image viewer. The source citations are functional, never poetic.
- No footer slogan, marketing statistics, invented explanatory paragraphs, badges, favorites gamification, or generic callouts.

## Actual text, not simulations
- German reader can show verbatim source OCR *only if chapter boundaries are verified*; always label OCR as such and retain the 1768 photographic original.
- English is the 1765 translation where text can be verified. Russian is the Bogorodsky translation associated with the 1815 edition where verified.
- Never replace missing original English or Russian copy with summaries, new biblical retellings, or machine translation presented as historical fact.
- Wherever precise text is unavailable, show only the factual source and direct facsimile link. Never pretend that selecting a language is a complete translation if it is not.

## Colors
Paper #f4f2ec; surface #ebe8df; ink #191916; secondary #5f615b; faint rule #d3d0c7; accent #872f27.

## Spatial rules
Columns correspond to the numbered books; the sequence is readable in English and still coherent across German/Russian. The gallery’s first visible row is artwork, not an illustrated “hero.” Reader image is fully visible at all breakpoints, never cropped by CSS.

## Motion
Only the image viewer transition, restrained and reduced-motion aware. Do not animate the whole gallery into view.

## Source/provenance
Public-domain 1768 Giessen 104 engravings via Heidelberg IIIF, cropped without synthesis from the photographic originals. Keep original full page and digital source URLs for every plate, plus crop coordinates in the machine-readable provenance file.

## Reader refinement — November 2026
One persistent language control in the masthead. The story reader presents the engraving, a single navigation title, biblical reference, and the four required sections plus Latin. Original printed titles, per-chapter source details, editorial notes and alternate witnesses remain in the contextual Edition page and source data; no scan links, redundant captions or OCR disclosures interrupt the reading flow. Original German folio images remain directly visible after the text and open in the image viewer without captions or outbound links. No change to corpus content or original image assets.
