# Deck fixes for `presentation/deck/slides.pptx`

For the colleague who owns the deck. Source: `docs/review-findings-2.md` (Kritik 2), `docs/review-findings-3.md` (Kritik 3) and the pitch script `presentation/pitch-script.md` as corrected after review 3. Nothing here edits the deck for you; each item says the slide, what to change, and the exact Czech text. Slide numbers are the deck's 14 screens. State of the deck: `slides.pptx` and `deck/build_deck.py` (deck v4, commit 32717a7) already carry most items of review 2; what is still wrong in `build_deck.py` after review 3 is listed with line numbers in section 15, and the lines of `outline.md` and `rehearsal-notes.md` in the last section, For lane K. The shipped model is now measured (`results/ipp1-latency-shipped.md`): every former `[[odezva vybraného modelu]]` and "asi 0,18 ms" below is replaced by the measured numbers. The name `[[odezva vybraného modelu]]` is reserved for a number that would wait for another file and is not used.

Vocabulary to use on every slide: **základní síť** (24 vstupů, 107 152 parametrů), **vybraný model** (základní síť + rozdíly sousedních cívek + lineární model pro proud + zvláštní síť pro bod u limiteru), **odložené výboje** (30 výbojů odložených před finálním výběrem). Never "nasazený model", "zamčené", "nikdo neviděl".

## 0. Whole deck

0.1 **Counters.** On every slide delete the footer counter ("1 / 8", "2 / 8", "3 / 8" twice, "4 / 8" three times, "5 / 8", "6 / 8", "7 / 8", "8 / 8"). The audience sees 14 screens in 7 minutes. (L2)

0.2 **Search and replace.** "zamčených" or "zamčené" becomes "odložených"; "nasazený model" becomes "vybraný model" (chart legend on slide 7, footnote on slide 11); delete "nikdo neviděl" wherever it stands (slide 7 caption). Delete the phrase "nasazujeme", use "použijeme". (H2, L4)

0.3 **Speaker notes.** The notes of every slide are the "Co se říká" rows of the matching section of `presentation/pitch-script.md` (section list in its table "Časový přehled", column "Snímek v decku"); `deck/build_deck.py` copies them automatically. Its `notes_text` calls split a section where a screen changes, by the start time of a script row. In the current file (32717a7) they are:
* line 291 `end="0:21"` and line 299 `start="0:21"` (slide 1, the picture changes at the row "Klasický výpočet", 0:21): correct, no change;
* line 363 `end="1:37"` and line 372 `start="1:37"` (slide 4, screen a to screen b): with the corrected timing the row "Třicet výbojů jsme odložili" starts at **1:33**, so both become `1:33` (the 1:37 of the first correction round is obsolete);
* line 372 `end="2:14"` and line 409 `start="2:14"` (slide 4, screen b to the inputs screen): the row "Samotné cívky stačí" now starts at **2:17**, so both become `2:17`.
The earlier text of this item named lines 256/264, 299, 320/330, 356; those were wrong (review 3, X2). Without the 1:33 and 2:17 edits the notes of the three slides 6, 7 and 8 would hold the wrong rows (the 1:26 row belongs to slide 6 only; check the heads "Snímek 4b: N s z 63 s" after a rebuild: expected 4a 7 s, 4b 44 s, 4c 12 s). The camera screen is a hidden backup and has no seconds (comment at the camera slide).
Also check `build_deck.py` text for the strings in section 15 below; the script has its own copies.

0.4 **Hidden slides.** Slide 5 (camera) is hidden (new, see 5). Slide 10 (stills) stays hidden and gets a note in the speaker view of slide 9: "Záloha: klávesa H otevře skrytý snímek 10 (jen v PowerPointu; v Keynote a Google Slides klávesa H není, tam snímek odkrýt předem)." (M6)

0.5 **Gloss of jargon.** Where the terms appear, add one short line, small print: "p99: 99 % odhadů je rychlejších" (slide 11), "Souhrnná relativní chyba: průměr přes 13 veličin bez bodu u limiteru, chyba vztažená k rozptylu veličiny; menší je lepší" (slide 8), "Křížová validace: 5krát jiné rozdělení výbojů na učení a test" (slide 4). (L4)

## 1. Slides 1 and 2 (Problém, Minuty proti milisekundám)

No text change. Only the notes (0.3).

## 2. Slide 3 (Data)

No text change. Only the notes.

## 3. Slide 4 (Metoda)

3.1 Replace the bottom line "Ověření: 5 různých rozdělení výbojů; chyby vždy na výbojích, které model neviděl." with:
"Základní síť: 5 různých rozdělení po výbojích. Vybraný model: navíc 30 výbojů odložených před finálním výběrem."

3.2 Add one line under the three tiles (small print):
"Vybraný model = základní síť + rozdíly sousedních cívek + lineární model pro proud + zvláštní síť pro bod u limiteru."

3.3 Add the gloss for the křížová validace from 0.5. Keep the footnote "Ilustrace principu; skutečných vstupů je 24, ne 16."

## 5. Slide 5 (kamera, BONUS)

5.1 **Hide the slide** (slide show, Hide Slide). No seconds in the timed plan. (M2)

5.2 New title: "Malá kamerová síť (snímky 48×64) je 1,3 až 13krát horší než cívky"

5.3 Tile "14 kA" with text "chyba proudu plazmatem: kamera ho neurčí" becomes: "14 kA" / "chyba proudu plazmatem: tato síť ho neurčí".

5.4 Footnote "Srovnání je jen orientační: kamera má snímky jen ze 78 výbojů." becomes: "Srovnání je jen orientační: snímky jen ze 78 výbojů, 12 epoch, každý osmý snímek. Platí pro tuto malou síť, ne pro kameru jako takovou."

5.5 Chart caption stays ("Průměrná chyba v mm, 5 dělení po výbojích"). Tile "1,79 mm" text stays ("osa R barevně, šedá 1,70 mm: barva nepomáhá").

## 6. Slide 6 (Co odhadujeme)

No text change. Only the notes.

## 7. Slide 7 (Na 30 zamčených výbojích: osa 0,13 mm) (H2, H3, H5, M1, M3, L4)

7.1 Title: "Na 30 odložených výbojích: osa 0,13 mm"
Second line under the title (smaller): "v křížové validaci na 119 výbojích 0,23 mm, na novějších číslech výbojů 0,40 mm"

7.2 Chart caption "Průměrná chyba v mm na 30 výbojích, které při vývoji nikdo neviděl" becomes:
"Průměrná chyba v mm na 30 výbojích odložených před finálním výběrem. Náměty na úpravy modelu vznikly na všech 149 výbojích."

7.3 Chart series "nasazený model" is renamed "vybraný model". Series "základní síť" stays. Values unchanged (0,307 / 0,321 / 0,161 / 0,212 and 0,133 / 0,172 / 0,115 / 0,108).

7.4 Tiles:
* "0,13 mm" / "průměrná chyba polohy osy, 30 odložených výbojů"
* "4,55 mm" / "bod u limiteru radiálně, dříve 10,6 mm (30 odložených výbojů)"
* "0,035 kA" / "proud plazmatem: lineární model; síť to neuměla (1,2 kA)" (do not count this tile into "dvakrát lépe")

7.5 Footnote at the bottom (8 pt) is replaced by two lines:
"Několik jednotlivých řádků je horších: nejhorší řádek bodu X 10,1 mm proti 2,76 mm."
"Čisté vstupy: osa 0,13 mm, proud 0,035 kA. Zašuměné vstupy (soubor organizátorů): jiný model, učený se šumem: osa 2,38 mm, proud 4,65 kA, bod u limiteru 25,8 a 38,9 mm (30 odložených výbojů)."

7.6 New line of three protocols (small print, under the chart): "Osa R, vybraný model: 30 odložených výbojů 0,13 mm | křížová validace na 119 výbojích 0,23 mm | novější čísla výbojů 0,40 mm (učení na 60 nejnižších číslech)."

## 8. Slide 8 (Kolik vstupů stačí) (L3, L5, M3)

8.1 Keep the title "Kolik vstupů stačí". Add a sentence under it:
"Samotné cívky stačí na skoro stejnou souhrnnou chybu (0,066 proti 0,063); osm nejlepších už ne (0,094)."

8.2 Chart caption "Souhrnná relativní chyba podle počtu vstupů (menší je lepší)" becomes: "Souhrnná relativní chyba podle počtu vstupů (menší je lepší), základní síť, 5 dělení po výbojích". Add the y axis title "souhrnná relativní chyba (bez jednotky)".

8.3 Data labels: delete the labels "0,265" and "0,204" or move them above the points (they overlap the line). Keep the footnote "Pořadí důležitosti platí pro naučenou síť, neříká, kolik informace vstup nese."

## 9. Slide 9 (Živá ukázka)

9.1 Subtitle "Skutečný a odhadnutý tvar plazmatu vedle sebe, chyba v čase" gets a second line: "V ukázce je základní síť, ne vybraný model. Výboje 123 a 0 síť při učení neviděla."

9.2 Add to the speaker notes: "Klávesa H: skrytý snímek 10 se stopkami (jen PowerPoint)." (0.4)

## 10. Slide 10 (hidden, stills)

Stays hidden. Add the caption under the three pictures: "Základní síť, výboj 123, mimo učení. Obrázky z prohlížeče." (The viewer tile also has to say "základní síť" instead of the latency of an unnamed model; that is the viewer owner's job, not the deck's.)

## 11. Slide 11 (Výpočet sítě rychlosti nebrání) (H1, H3, M7)

11.1 Tile text under "0,0145 ms": "medián jednoho odhadu základní sítě, procesor Apple M5" (was "medián jednoho odhadu na procesoru").
Tile text under "0,0209 ms": "99 % odhadů základní sítě je rychlejších" (keep the p99 gloss, 0.5).

11.2 **Third tile** next to them (measured, `results/ipp1-latency-shipped.md`, row `numpy_end_to_end_limited`): "0,027 ms" / "vybraný model, limitované plazma, procesor Apple M5, vytížený notebook". Footnote under the tiles: "Vybraný model: numpy, náhodné váhy stejného tvaru, jen čas; divertorové plazma 0,015 ms, p99 pod 0,1 ms." The old fallback "asi 0,18 ms ... neměřeno" is deleted; it was not reproduced (review 3, X1).

11.3 Footnote: replace "Rozpočet je 1 až 10 ms." by "Zadání chce jednotky až desítky milisekund; náš rozpočet je 1 až 10 ms." (X4: the 1 to 10 ms is the team's verdict, not the assignment). Keep "Celý odhad základní sítě od čísel na vstupu po čísla na výstupu: medián 0,0140 ms." **Delete** the sentence "Grafická karta je pro jeden odhad pomalejší (0,27 ms, s přenosem dat 0,49 ms)." (time cut) and the sentence "Nasazený model se třemi částmi je pomalejší, asi 0,18 ms (podobný recept, zatížený počítač)." (replaced by 11.2). Keep "Neověřeno: sběr signálů z cívek, nejhorší doba na systému reálného času a přesnost na skutečně zašuměných signálech." and add: "Přepínání mezi modelem pro čisté a pro zašuměné vstupy netestováno. Na systému bez reálného času se ojediněle objeví špičky."

11.4 Title stays "Výpočet sítě rychlosti nebrání". Do not add "nebude překážkou".

## 12. Slide 12 (Nejslabší je bod u limiteru a konec výboje) (H3, L1, M3)

12.1 Tiles:
* "4,55 mm" / "bod u limiteru radiálně (vybraný model, 30 odložených výbojů), 99 % řádků pod 77,5 mm"
* "8,35 mm" / "bod u limiteru svisle (vybraný model, 30 odložených výbojů), 99 % řádků pod 92,2 mm"

12.2 Chart caption: "Chyba polohy osy (mm) podle času výboje. Graf: základní síť, 5 dělení po výbojích. Dlaždice nahoře: vybraný model."

12.3 Footnote line 1: "Kolísání výstupu proti skutečnosti, základní síť: na čistých vstupech 0,96 až 1,07 (13 veličin), na zašuměných 8,4krát (osa R) a 3,3krát (osa Z), po učení se šumem 1,7 a 1,65krát." (was "1,7 a 1,6krát")
Line 2: "Na souvislých blocích čísel výbojů je chyba základní sítě 1,5 až 2,9krát větší než na náhodně vybraných." (add "základní sítě")

## 13. Slide 13 (Zná jen tvary z dat a šum v měření mu vadí nejvíc) (H4, M3, L3)

13.1 Left chart: **delete the fourth column** "se šumem a třemi časy" (2,33); it is not spoken. Keep the other three columns (0,38 / 10,15 / 2,64). Add a fourth, spoken-only value 2,22 as a note below the chart: "Učeno se šumem, test bez šumu: 2,22 mm."

13.2 Left chart title: "Chyba polohy osy (mm) při šumu v měření; základní síť, 5 dělení po výbojích"

13.3 Under the left chart add: "Na 30 odložených výbojích: síť učená se šumem, zašuměné vstupy: osa 2,38 mm, proud 4,65 kA. Vybraný model na zašuměných vstupech selže (osa 190 mm)."

13.4 Right chart title: "Chyba osy (mm) podle počtu učících výbojů; základní síť, 5 dělení, vždy 60 epoch". The x axis is categorical (6, 12, 30, 60, 119 equally spaced): switch to a log axis or scatter with the real values so that the spacing is true. (L3)

13.5 Footnote at the bottom is **replaced** by:
"Vynechání celé rodiny tvarů: chyba 1,0 až 3,0krát větší. Skutečně neobvyklých výbojů je jen 18 ze 149 a samostatně nikdy vynechány nebyly; tvary mimo rozsah dat jsme neověřili. Jen jeden tokamak, řízení model sám nenahradí."
Delete "bez zhroucení; osa u nejodlišnějších tvarů 1,6 mm místo 0,7 mm". (H4)

13.6 Slide title "Zná jen tvary z dat a šum v měření mu vadí nejvíc" states as a finding what the results say was not tested. New title: "Šum v měření mu vadí nejvíc; neobvyklé tvary jsme neověřili" (review 3, H4 nit).

## 14. Slide 14 (Závěr) (H1, H5, M7)

14.1 Big number tile: "0,0145 ms" with the label "Jeden odhad základní sítě, procesor Apple M5". Next to it a second, smaller number: "0,027 ms" / "vybraný model, limitované plazma" (measured, not "odhad").

14.2 Line "Klasický výpočet trvá minuty. Zadání chce jednotky až desítky milisekund." stays; add after it: "Obojí je pod naším rozpočtem 1 až 10 ms." (X4: say "našim", the budget is ours.)

14.3 Tile "Přesný / desetiny milimetru na ose, bodu X a dotykových bodech" becomes:
"Přesnost" / "čisté vstupy: osa, bod X a dotykové body desetiny milimetru (osa 0,13 mm), bod u limiteru 4,55 a 8,35 mm. Zašuměné vstupy: osa 2,38 mm, bod u limiteru 25,8 a 38,9 mm, proud 4,65 kA (30 odložených výbojů)." (H5 and review 3: the tile must name the targets; the limiter point is not "desetiny".)

14.4 Tile "Zbývá" becomes: "Zbývá" / "bod u limiteru, neobvyklé tvary (samostatně neověřeny), odolnost proti šumu, napojení na řízení"

14.5 **Dropped** (review 3, X1). The closing line stays "Desetiny milimetru za setiny milisekundy." because 0,0145 and 0,027 ms are hundredths of a millisecond; "desetiny milisekundy" was built on the 0,18 guess and contradicts the tiles. `build_deck.py` line 574 prints the withdrawn wording, see section 15.

14.6 The background picture (sunset) has no label: add the small print "Ilustrace." as on slide 1. (L6)

## 15. Strings in `deck/build_deck.py` that must change (X1, X4, X5, X6, M6; line numbers of commit 32717a7, checked by `grep -n`)

The strings of review 3 for X5 and X6 (the old lines 368, 430 and 499 with "zamčená sada", "ipp1-improve.md (0,18 ms nasazeného receptu)" and "Přesný") are fixed in deck v4: `grep -n "zamčen\|nikdo nevid\|nasazen\|Přesný" build_deck.py` finds nothing now. What is left:

| Line | Now | Change to |
|---|---|---|
| 74 to 75, 284 to 286 | `j["shipped_latency"] = None` and the tile `("asi 0,18 ms", "vybraný model, zatím odhad z podobného postupu na vytíženém počítači, neměřeno")` | drop the fallback; fixed tile `("0,027 ms", "vybraný model, limitované plazma, procesor Apple M5, vytížený notebook")`; the comments naming `[[odezva vybraného modelu]]` go (lines 74 and 284) |
| 465 | `"Rozpočet je 1 až 10 ms. "` | `"Zadání chce jednotky až desítky ms; náš rozpočet je 1 až 10 ms. "` (X4) |
| 466 to 471 (gloss line) | `p99: 99 % odhadů je rychlejších. Na systému bez reálného času se ojediněle objeví špičky.` | add `Vybraný model: numpy, náhodné váhy stejného tvaru, jen čas; divertorové plazma 0,015 ms.` |
| 473 to 475 | `"results/ipp1-latency-shipped.md (vybraný model)" if shipped else "results/ipp1-improve.md (asi 0,18 ms, podobný postup, neměřeno)"` | only `"results/ipp1-latency-shipped.md (vybraný model, numpy, 0,027 ms limitované, 0,015 ms divertorové)"` |
| 561 to 562 | `("  vybraný model" + ("" if shipped else ", odhad"), 18, MUTED, False)` | `("  vybraný model, limitované plazma", 18, MUTED, False)` |
| 563 to 564 | `"... Zadání chce jednotky až desítky milisekund. Obojí je pod rozpočtem 1 až 10 ms."` | `"... Obojí je pod naším rozpočtem 1 až 10 ms."` (X4) |
| 566 to 567 | `"desetiny milimetru na čistých vstupech, jednotky milimetrů na zašuměných (osa ... mm a ... mm, 30 odložených výbojů)"` | text of 14.3 above (targets named) |
| 574 | `"Desetiny milimetru za desetiny milisekundy."` | `"Desetiny milimetru za setiny milisekundy."` (X1) |
| 577 | `add_sources(... "results/ipp1-latency.json (0,0145 ms, Apple M5)" ...)` | add `"results/ipp1-latency-shipped.md (0,027 ms)"` |
| 508 | `"Zná jen tvary z dat a šum v měření mu vadí nejvíc"` | `"Šum v měření mu vadí nejvíc; neobvyklé tvary jsme neověřili"` (13.6) |
| 436 | `"\nZáloha: klávesa H otevře skrytý snímek s uloženými obrázky."` | `"\nZáloha: klávesa H otevře skrytý snímek s uloženými obrázky (jen PowerPoint; v Keynote a Google Slides odkrýt snímek předem)."` (M6) |
| 363, 372, 372, 409 | `end="1:37"`, `start="1:37"`, `end="2:14"`, `start="2:14"` | `1:33`, `1:33`, `2:17`, `2:17` (item 0.3) |
| 362, 371, 435 (comments) | "1:30 to 1:37", "1:37 to 2:14", "2:24 to 3:52" | "1:26 to 1:33", "1:33 to 2:17", "2:29 to 3:49" |

After the edits rebuild and check, in the speaker notes: no `0,18`, no `zamčen`, no `[[odezva vybraného modelu]]`, slide 14 closing line "setiny", slide 11 third tile "0,027 ms", the heads of the three notes of slide 4 add to 63 s.

## What waits

Nothing waits for a measurement any more. Two things still need a person: the number `[[chyba osy výboje 0]]` (replay discharge 0 in the viewer; until then the script says only "rozdíl mezi čárami je vidět") and a stopwatch reading of the whole talk (the written-out word count says about 7:24 at a normal pace, see the Lead notes of the pitch script). The viewer (`viewer/`) is outside this list: its latency tile should say "základní síť" (H1d); the tile text is in `viewer/index.html` (review 3 gives lines 373 and 509).

## For lane K

Lines the colleague must change in the files he owns (the script is already corrected; the lines below still carry the old text; the checks are `grep -n` on the strings named). Times of the corrected script: slide 3 is 20 s (1:06 to 1:26), slide 4 63 s (1:26 to 2:29), demo 80 s (2:29 to 3:49), slide 5 40 s (3:49 to 4:29), slide 6 34 s (4:29 to 5:03), slide 7 74 s (5:03 to 6:17), slide 8 43 s (6:17 to 7:00).

`presentation/outline.md` (line numbers of this commit):
* line 4: the example `[[odezva vybraného modelu]]` of a missing number: use `[[chyba osy výboje 0]]` as the example.
* line 11 (every speed has a model and a processor): "vybraný model `[[odezva vybraného modelu]]`, do změření asi 0,18 ms (odhad z podobného postupu na vytíženém počítači)" becomes "vybraný model asi 0,03 ms, medián 0,027 ms u limitovaného a 0,015 ms u divertorového plazmatu (`results/ipp1-latency-shipped.md`, vytížený notebook, náhodné váhy, jen čas)".
* line 12 and line 38: "odložené před finálním výběrem" becomes "odložené před posledním výběrem modelu; náměty na úpravy ale vznikly na všech 149" (H2: the audience hears "finálním" as held out from design).
* headings, seconds: line 32 "(24 s)" to 20 s, line 42 "(54 s)" to 63 s, line 59 "(88 s)" to 80 s, line 69 "(37 s)" to 40 s, line 80 "(31 s)" to 34 s, line 91 "(76 s)" to 74 s, line 102 "(44 s)" to 43 s; line 112 "Součet času" becomes 38 + 28 + 20 + 63 + 80 + 40 + 34 + 74 + 43 = 420 and its list of cuts becomes the order in the Lead notes of the pitch script (the sentences on the demo speed, "Zbývá napojení" and "Typický výboj sedí" are already cut).
* line 64 (demo): "Dlaždice latence v prohlížeči má říkat základní síť, 0,0145 ms" stays as a check on the viewer, but the sentence is no longer spoken (script row 3:08 cut).
* line 71 (main sentence of slide 5): `[[odezva vybraného modelu]]` becomes "0,03 (0,027 u limitovaného plazmatu)" and "rozpočet je 1 až 10 ms" becomes "náš rozpočet je 1 až 10 ms (zadání chce jednotky až desítky ms)".
* line 75 (bullet on the selected model, slide 5): delete "`[[odezva vybraného modelu]]` ms na klidném stroji; do změření je odhad 0,1775 ms ... asi dvanáctkrát víc než základní síť" and write "0,027 ms u limitovaného plazmatu, 0,015 ms u divertorového, asi dvakrát víc než základní síť; dřívější odhad 0,18 ms se při měření nepotvrdil".
* line 85 (slide 6): "v jednom procentu řádků až 77,5 a 92,2 mm" becomes "v jednom procentu řádků je chyba přes 77,5 a 92,2 mm (p99; nejhorší řádky 357 a 485 mm)".
* line 97 (slide 7, amount of data): add "119 je dvakrát jiné číslo: vývojová sada pro křížovou validaci a 119 učících výbojů v každém z pěti dělení všech 149".
* line 104 (main sentence of slide 8): "rychlost výpočtu desetiny milisekundy" becomes "rychlost výpočtu setiny milisekundy".
* line 106 (slide 8, accuracy): add "bod u limiteru 25,8 a 38,9 mm, proud 4,65 kA" after "(2,38 mm)".
* line 107 (slide 8, speed): `[[odezva vybraného modelu]]` becomes "asi 0,03 (0,027 limitované plazma)" and "rozpočtem 1 až 10 ms" becomes "naším rozpočtem 1 až 10 ms".
* line 110 (slogan): "Slogan: desetiny milimetru za setiny milisekundy." (delete "do změření vybraného modelu; pak podle měření").
* lines 124 to 128 (Chybějící čísla): delete the bullet at line 126 (`[[odezva vybraného modelu]]`).

`presentation/rehearsal-notes.md`:
* the list "Snímek 1: 38 s ..." and "Živá ukázka: 88 s, z toho 13 s ticho" and "Snímek 5: 37 s ...": new seconds as above; silence 15 s (6 + 5 + 4).
* "Celkem 420 s při 1,68 slova za sekundu (čísla dvakrát), 1,55 podle prostého počtu" becomes "420 s; 612 slov, 666 s čísly dvakrát (1,64 slova za sekundu), 730 slov, když se čísla čtou slovy (1,80 za sekundu); při 1,7 slova za sekundu asi 7:24".
* "Nejtěsnější je snímek 5 (1,73) a snímek 1 a 6 (1,71)" becomes "Nejtěsnější je snímek 5 (2,05 slova za sekundu, čísla slovy), potom 6 (1,88), 7 (1,84) a 4 (1,81)".
* the order of cuts "věta o rychlosti ukázky, věta Zbývá napojení, kamera, poslední věta snímku 7" becomes the order in the Lead notes of the pitch script (the first two are already cut).
* "Rychlost 0,0145 ms patří vždy základní síti" stays; add "Vybraný model 0,03 ms (0,027 limitované)".
* "DOPLNIT: skutečný čas po přečtení se stopkami" stays open.

`docs/REHEARSAL.md` (not mine, for whoever owns it): the answers Q6 ("rozdíly pod 15 až 20 procent") and Q9 (COMPASS Upgrade) carry the old text; Q5 and Q8 should follow the script. 
