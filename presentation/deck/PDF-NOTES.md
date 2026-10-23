# Deck PDF export, notes

Exported Fri 23 Oct 2026 by a cloud session (branch `cloud/deck-pdf`, no raw data, nothing edited).
Source: `presentation/deck/slides.pptx` as on main 5a9a2d9 (last change to the file: 2809b2d).

## What was done

- LibreOffice 24.2.7.2 was already installed (`soffice --version`).
- `slides.pdf`: `soffice --headless --convert-to pdf --outdir out presentation/deck/slides.pptx`.
  LibreOffice skips hidden slides by default: **12 pages** (screens 5 and 10 left out).
- `slides-all.pdf`: the same with the filter option
  `--convert-to 'pdf:impress_pdf_Export:{"ExportHiddenSlides":{"type":"boolean","value":"true"}}'`:
  **14 pages**, in deck order. `pdfinfo`: 960 x 540 pt (16:9, 13.33 x 7.5 in), text stays selectable.
- The pptx has 14 slides; `python-pptx` shows `show="0"` on slide 5 (bonus: camera) and slide 10 (backup: stored
  viewer images). Page 5 and 10 of `slides-all.pdf` are exactly those; `slides.pdf` is `slides-all.pdf` without them.
- Speaker notes are not in the PDFs (LibreOffice default); they stay in the pptx.
- Every page rendered with `pdftoppm -r 85 -png` and looked at one by one.

## Fonts

`pdffonts` lists only two embedded fonts: LiberationSans and LiberationSans-Bold.
The deck asks for Arial (190 uses, charts included), and for the theme default Calibri, which no run uses.
Arial became Liberation Sans, which is metric compatible with Arial, so line breaks and box fits do not move.
Carlito (the Calibri substitute) is installed but was not needed. Czech diacritics (ě š č ř ž ý á í é ů ť ň) render
on every page. The PDF is therefore Liberation Sans, not Arial: the letter shapes differ slightly from Arial.

## Overflow check

No text runs out of its tile, card or the page on any of the 14 pages. Tightest cases, all inside: page 6 right
label "dva dotykové body, kam dopadá okraj" ends about 47 px (of 1133) from the right edge; page 12 note text and
page 14 tile text fill their cards but stay in. No autofit is used in the pptx, so no renderer shrinks text.

## Where LibreOffice may differ from PowerPoint

1. **Charts (pages 5, 7, 8, 12, 13 twice).** Rendered from the XML as written. All value axes carry a bare
   `<c:delete/>`, which means "deleted" in OOXML, so no y-axis numbers or ticks show in either program; the numbers
   are the data labels. LibreOffice and PowerPoint should agree here, but PowerPoint draws gridlines, label
   positions and bar gap slightly differently. Compare the label placement on page 8 (labels 0,143 and 0,157 sit
   close together) and page 13 right chart (labels 1,47 and 0,83).
2. **Page 13 right chart, x axis (`chart6`) is a log axis with tick label size `sz="100"` = 1 pt.** The x tick
   labels are therefore invisible, in the PDF and probably in PowerPoint. The slide gives the number of learning
   discharges in brackets in the data labels and says "logarithmická osa", but the axis itself has no readable
   scale. That is a deck issue, not a rendering one (the owner of `build_deck.py` decides).
3. **Picture backgrounds.** Full bleed images (pages 1, 2, 9, 14) and the dark rectangle behind the schematic on
   page 6 are plain pictures with a text overlay; the page 6 picture shows as a slightly lighter box on the dark
   slide. Same in PowerPoint if the PNG is the same.
4. **Shadows and rounded cards.** Soft text shadows and card shadows are drawn by LibreOffice, close to
   PowerPoint's. Page 3 and 4 card shadows are the most visible.
5. No animations, transitions, video or embedded objects exist in the pptx, so nothing is lost in the PDF.
   The live demo screen (page 9 of `slides-all.pdf`) is a title only; the viewer runs separately.

## Wording still open in the deck (not changed here)

The export is the pptx as it is. PLAN row IMPL-34 (TODO) is not applied yet: page 9 of `slides-all.pdf` still says
"Skutečný tvar plazmatu a odhadnuté body", page 14 still says "Přesnost osy". **Re-export after IMPL-34 and after any
other deck edit**; the commands above give the same files in under a minute.

## What the owner must check in PowerPoint or Keynote before this is the official export

1. Open `slides.pptx` and export a PDF yourself (File, Export as PDF, "hidden slides" off for the 12 page file).
   Compare page count (12 and 14) and flip through next to `slides-all.pdf`.
2. If Arial is not on the machine (Keynote on a bare system), confirm the font is Arial and not a fallback.
3. Charts: bar and label positions on pages 7, 8, 12 and 13; the missing log axis labels on page 13 (note 2).
4. Hidden slides: confirm in the slide sorter that exactly screens 5 and 10 are hidden, and decide which file is
   the submission (12 pages for the talk, 14 for the archive).
5. The page 6 picture box and the full bleed pictures on pages 1, 2, 9, 14 look the same as on screen.
6. File sizes are 4.5 MB (12 pages) and 5.1 MB (14 pages), mostly the embedded pictures; check the submission
   size limit if there is one (OQ-S in `docs/SUBMISSION.md`).
7. Confidentiality was not judged here (no data in this mirror). Page 10 of `slides-all.pdf` and the viewer
   pictures may show real discharge values; audit item H-1 and decision D-RP6 in `docs/` stay the owner's to settle
   before the PDF leaves the team.
