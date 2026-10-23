# Deck fixes for `presentation/deck/slides.pptx`

For the colleague who owns the deck. Source: `docs/review-findings-2.md` (Kritik 2), `docs/review-findings-3.md` (Kritik 3), `docs/review-physics.md` (the physicist, section 16 below) and the pitch script `presentation/pitch-script.md` as corrected after review 3. Nothing here edits the deck for you; each item says the slide, what to change, and the exact Czech text. Slide numbers are the deck's 14 screens. State of the deck: `slides.pptx` and `deck/build_deck.py` (deck v4, commit 32717a7) already carry most items of review 2; what is still wrong in `build_deck.py` after review 3 is listed with line numbers in section 15, and the lines of `outline.md` and `rehearsal-notes.md` in the last section, For lane K. The shipped model is now measured (`results/ipp1-latency-shipped.md`): every former `[[odezva vybraného modelu]]` and "asi 0,18 ms" below is replaced by the measured numbers. The name `[[odezva vybraného modelu]]` is reserved for a number that would wait for another file and is not used.

Vocabulary to use on every slide: **základní síť** (24 vstupů, 107 152 parametrů), **vybraný model** (základní síť + rozdíly sousedních cívek + lineární model pro proud + zvláštní síť pro bod u limiteru), **odložené výboje** (30 výbojů odložených před posledním výběrem modelu; náměty na úpravy vznikly na všech 149). Never "nasazený model", "zamčené", "nikdo neviděl".

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
"Základní síť: 5 různých rozdělení po výbojích. Vybraný model: navíc 30 výbojů odložených před posledním výběrem modelu."

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
"Průměrná chyba v mm na 30 výbojích odložených před posledním výběrem modelu, oproti rekonstrukci ústavu. Náměty na úpravy modelu vznikly na všech 149 výbojích."

7.3 Chart series "nasazený model" is renamed "vybraný model". Series "základní síť" stays. Values unchanged (0,307 / 0,321 / 0,161 / 0,212 and 0,133 / 0,172 / 0,115 / 0,108).

7.4 Tiles:
* "0,13 mm" / "průměrná odchylka radiální osy, 30 odložených výbojů"
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

9.1 Superseded by the viewer facts of `docs/demo-facts.md` and by section 16.5. The old second line ("V ukázce je základní síť ... Výboje 123 a 0") is wrong now: the viewer plays the selected model on the 30 set-aside discharges and shows points, not an outline. Use the texts of 16.5.

9.2 Add to the speaker notes: "Klávesa H: skrytý snímek 10 se stopkami (jen PowerPoint)." (0.4)

## 10. Slide 10 (hidden, stills)

Stays hidden. Add the caption under the three pictures: "Obrázky z prohlížeče, výboj 85 a 147, vybraný model, odložené výboje. Tmavá čára je rekonstrukce ústavu." (the old caption "Základní síť, výboj 123" is stale, `docs/demo-facts.md`) (The viewer tile also has to say "základní síť" instead of the latency of an unnamed model; that is the viewer owner's job, not the deck's.)

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
"Vynechání rodiny tvarů: chyba osy 1,0 až 3,0krát větší. 18 nejodlišnějších výbojů vynecháno z učení: chyba osy asi 2,5krát větší (0,9 až 2,3 mm, základní síť); 14 z nich je z časné části kampaně. Tvary mimo rozsah dat jsme neověřili. Jen jeden tokamak, řízení model sám nenahradí."
Delete "bez zhroucení; osa u nejodlišnějších tvarů 1,6 mm místo 0,7 mm". (H4)

13.6 Slide title: unchanged, KQ-19 answered by the Lead (keep "Šum mu vadí nejvíc; tvary mimo rozsah dat jsme neověřili"); the footnote of 16.8 carries the physicist's point that noise is a synthetic stress test.

## 14. Slide 14 (Závěr) (H1, H5, M7)

14.1 Big number tile: "0,0145 ms" with the label "Jeden odhad základní sítě, procesor Apple M5". Next to it a second, smaller number: "0,027 ms" / "vybraný model, limitované plazma" (measured, not "odhad").

14.2 Line "Klasický výpočet trvá minuty. Zadání chce jednotky až desítky milisekund." stays; add after it: "Obě sítě jsou pod naším rozpočtem 1 až 10 ms (měřen jen výpočet sítě)." (X4: say "našim", the budget is ours.)

14.3 Superseded by 16.9: the tile head "Přesnost" becomes "Shoda s rekonstrukcí" (the numbers are an agreement with the institute's reconstruction, not an accuracy of the plasma position).

14.4 Superseded by 16.9 (the tile Zbývá names the whole chain from the sensors).

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
| 563 to 564 | `"... Zadání chce jednotky až desítky milisekund. Obojí je pod rozpočtem 1 až 10 ms."` | `"... Obě sítě jsou pod naším rozpočtem 1 až 10 ms (měřen jen výpočet sítě)."` (X4) |
| 566 to 567 | `"desetiny milimetru na čistých vstupech, jednotky milimetrů na zašuměných (osa ... mm a ... mm, 30 odložených výbojů)"` | text of 14.3 above (targets named) |
| 574 | `"Desetiny milimetru za desetiny milisekundy."` | `"Desetiny milimetru za setiny milisekundy."` (X1) |
| 577 | `add_sources(... "results/ipp1-latency.json (0,0145 ms, Apple M5)" ...)` | add `"results/ipp1-latency-shipped.md (0,027 ms)"` |
| 508 | `"Zná jen tvary z dat a šum v měření mu vadí nejvíc"` | `"Šum v měření mu vadí nejvíc; neobvyklé tvary jsme neověřili"` (13.6) |
| 436 | `"\nZáloha: klávesa H otevře skrytý snímek s uloženými obrázky."` | `"\nZáloha: klávesa H otevře skrytý snímek s uloženými obrázky (jen PowerPoint; v Keynote a Google Slides odkrýt snímek předem)."` (M6) |
| 363, 372, 372, 409 | `end="1:37"`, `start="1:37"`, `end="2:14"`, `start="2:14"` | `1:33`, `1:33`, `2:17`, `2:17` (item 0.3) |
| 362, 371, 435 (comments) | "1:30 to 1:37", "1:37 to 2:14", "2:24 to 3:52" | "1:26 to 1:33", "1:33 to 2:17", "2:29 to 3:49" |

After the edits rebuild and check, in the speaker notes: no `0,18`, no `zamčen`, no `[[odezva vybraného modelu]]`, slide 14 closing line "setiny", slide 11 third tile "0,027 ms", the heads of the three notes of slide 4 add to 63 s.

## 16. Physics review pass (`docs/review-physics.md`, branch `cloud/pitch-fix-3`)

The deck is not edited here. Strings and line numbers are those of `presentation/deck/build_deck.py` on main at commit 2fb3f86 (check with `grep -n` on the quoted old text). The rule behind all of it: the numbers are an agreement of the network with the institute's reconstruction (the labels are probably the output of a reconstruction code, not confirmed), never "přesnost polohy plazmatu" and never "skutečný".

16.1 **Slide 1 (lines 291 to 297).** The picture 04-wall-damage.png (melting metal) says that wall contact is the danger, while 44,2 % of all rows are limited. Replace the background by 02-minutes-vs-ms.png or by a neutral cross section; if the picture stays, the caption "Ilustrace, ne fotografie." is not enough, so also change line 294 "Plazma se musí udržet dál od stěny" to "Plazma se samo neudrží uprostřed komory". Line 295 (150 až 200 milisekund podle organizátorů) stays on the screen; it is no longer spoken.

16.2 **Slide 2 (line 306 to 307).** The question "odhadne malá neuronová síť tvar plazmatu z magnetických měření dost přesně a dost rychle?" becomes "dokáže malá neuronová síť rekonstrukci polohy a tvaru plazmatu napodobit dost dobře a dost rychle?" (the pitch row 0:29 says the same).

16.3 **Slide 3 Data (line 314).** Tile "hledaných veličin tvaru: osa, bod X, dotykové body, protažení" becomes "veličin polohy a tvaru: osa, dolní bod X, dotykové body, bod u limiteru, protažení, trojúhelníkovost, proud, údaj o limiteru" (the 16 include the current and a flag). Add one line under the tiles, small print: "Vstup: jen magnetická čidla. Proudy v cívkách pole a model komory síť nedostává." (H6, spoken at 0:45).

16.4 **Slide 6 Co odhadujeme (line 364 onward).** Add the line "Vybraný model odhaduje jen body (osa, dolní bod X, dotykové body, bod u limiteru), obrys ne." (H2; the 15 supplementary columns are predicted by the basic network only and their numbers are not published, `docs/bonus-gaps.md`).

16.5 **Slide 7 and slide 9 (lines 372, 376, 384, 442).**
* line 372 title: "Na 30 odložených výbojích se osa liší od rekonstrukce o 0,13 mm"
* line 376 tile text: "průměrná odchylka radiální osy od rekonstrukce ústavu, 30 odložených výbojů"
* line 384 caption: "Průměrná chyba v mm (odchylka od rekonstrukce ústavu) na 30 výbojích odložených před posledním výběrem modelu. Náměty na úpravy modelu vznikly na všech 149 výbojích." (also 3.1)
* line 442 (live demo slide): "Skutečný tvar plazmatu a odhadnuté body, chyba v čase" becomes "Rekonstrukce ústavu a odhad sítě: odhadnuté body, odchylka v čase"; the second line (443) stays, add "Obrys je z rekonstrukce ústavu."

16.6 **Slide 11 (line 473 to 474).** "sběr signálů z cívek, nejhorší doba na systému reálného času a přesnost na skutečně zašuměných signálech." becomes "sběr a integraci signálů z cívek, chování signálů v provozu, uzavřenou smyčku, nejhorší dobu na systému reálného času, rychlost změny polohy a chování na skutečně zašuměných signálech." (H4). Add to the grey line (line 476) "Čas řádků v souboru je relativní; skutečný odstup řádků neznáme."

16.7 **Slide 12 (lines 483 to 506).**
* tile 4,55 mm (line 485): text becomes "bod u limiteru radiálně (vybraný model, 30 odložených výbojů): medián 0,73 mm, 99 % řádků pod 77,5 mm" (M5); the tile 8,35 mm keeps its text
* add a footnote line: "Vzdálenost plazmatu od stěny, na které řízení záleží, jsme neměřili. Bod u limiteru je místo dotyku na stěně, ne spojitá veličina."
* line 504 "Kolísání výstupu proti skutečnosti" becomes "Kolísání výstupu proti rekonstrukci ústavu"
* line 490 chart caption keeps "Chyba polohy osy"; add "Příčina růstu na konci výboje není známa." (M6)

16.8 **Slide 13 (lines 513 to 557).**
* title (line 513): unchanged. The Lead answered KQ-19: keep "Šum mu vadí nejvíc; tvary mimo rozsah dat jsme neověřili" (it is the more exact one). Item 13.6 and the first title proposal of this pass are withdrawn.
* line 525 text under the left chart: add "Šum je ze souboru organizátorů, posun jsme vyrobili sami. Skutečné chyby čidel (kalibrace, výpadek, posun integrátoru) jsme netestovali." (H5)
* line 554 footnote: keep, and after "řízení model sám nenahradí" add nothing else.

16.9 **Slide 14 (lines 568 to 585).**
* tile head "Přesnost" (line 571) becomes "Shoda s rekonstrukcí"; its body begins "čisté vstupy, shoda s rekonstrukcí ústavu: radiální osa 0,13 mm, bod X a dotykové body desetiny milimetru, bod u limiteru 4,55 a 8,35 mm. Zašuměné vstupy: ..." (the rest unchanged)
* tile "Zbývá" (line 575): "celý řetězec od čidel k řízení a zkouška v uzavřené smyčce, bod u limiteru, neobvyklé tvary (samostatně neověřeny), skutečné chyby čidel"
* line 574 closing line: "Desetiny milimetru shody s rekonstrukcí za setiny milisekundy."
* line 585 source "results/ipp1-final.md (přesnost)" becomes "results/ipp1-final.md (shoda s rekonstrukcí)"

16.10 **Speaker notes.** Rebuild after the edits (the notes are copied from `pitch-script.md`; the row times of this pass are 0:11, 0:29 (slide 1), 0:45, 0:59 (slide 2), 1:56 and 2:05 (slide 4), 4:01 and 4:10 (slide 5), 4:51 (slide 6), 5:23, 5:37, 5:54 (slide 7); the boundaries used by `notes_text` stay 0:21, 1:33 and 2:17, so the heads of slide 4 are still 7 s, 44 s, 12 s).

16.11 **Viewer (outside this list, for its owner).** Toggle labels "Skutečnost" and "Předpověď" become "Rekonstrukce ústavu" and "Odhad sítě"; the legend that says "obrys model nepředpovídá" becomes "obrys model neodhaduje, ukazuje jen označené body"; `docs/viewer-qa.md` still says "Předpověď". Until it is changed the speaker does not say those two words (pitch row 2:42).

16.12 **Pictures.** `presentation/assets/prompts.md` holds the prompt of the melting-wall picture; the physicist asks to drop it (H3). Not edited here.

## Questions for the organizers

Ready to send, not sent. Czech, one message, numbered so that they can answer by number. Nobody has seen the organizers' task text or their notebook in this repository, so every question below is a point where the talk currently says "nevíme".

> Dobrý den, pracujeme na úloze IPP 1 a rádi bychom v sobotní prezentaci neřekli nic, co neplatí. Prosíme o krátké odpovědi na tyto otázky (stačí číslo a odpověď):
>
> 1. Jak vznikly sloupce, které odhadujeme (osa, bod X, dotykové body, bod u limiteru, protažení, trojúhelníkovost, proud)? Je to výstup rekonstrukce rovnováhy (jaký program, jaké vstupy: proudy v cívkách pole, model komory) a jakou nejistotu mají? Smíme říct, že se síť učí napodobit tuto rekonstrukci?
> 2. Je sloupec time relativní (0 až 1)? Jaké jsou skutečné časy řádků a odstup řádků a proč mají výboje 17 až 439 řádků, když celý výboj trvá 150 až 200 milisekund? Smíme tu délku výboje v prezentaci říct?
> 3. Jaká je konvence znaménka proudu plazmatem? Šestnáct ze 149 výbojů má kladný proud. Je to jiná kampaň, nebo obrácené toroidální pole?
> 4. Jaké jsou přesné vzorce pro elongation, triangularity, triangularity_upper a triangularity_lower a pro krajní body, když je plazma limitované a když je divertorové? Proč elongation klesá až k 0,9 a na kterých řádcích?
> 5. Obsahují data výboje, které skončily zánikem plazmatu, nebo jsou v souboru jen výboje, pro které rekonstrukce proběhla?
> 6. Soubor se šumem: jak byl vytvořen (šum úměrný směrodatné odchylce každého kanálu?) a proč má směrodatnou odchylku 16 procent u cívek a 9 procent u smyček toku? Jsou signály integrované a opravené o posun už ve sběru dat, nebo až dodatečně?
> 7. Jak souvisí číslo výboje s časem? Je výboj s číslem 0 nejstarší?
> 8. Které sloupce jsou těch 17 parametrů ze zadání? My odhadujeme 16 z 31.
> 9. Z čeho plyne požadavek na odezvu jednotky až desítky milisekund? Jaká je perioda smyčky svislé stabilizace na COMPASSu a co kromě polohy a tvaru řízení potřebuje (rychlost změny polohy, vzdálenost plazmatu od stěny)?
> 10. Potvrdí kolegové z ÚFP dvě věty z našeho úvodu: protažené plazma je svisle nestabilní a bez rychlého řízení uhne ke stěně; úplná rekonstrukce rovnováhy se počítá po výboji a trvá minuty?
> 11. Je ve vašem zadání doslova napsáno, že správné odpovědi vznikají numerickou rekonstrukcí rovnováhy, a smíme to takto citovat?
>
> 12. Smíme při práci používat nástroje s umělou inteligencí a máte nějaké pravidlo, jak to uvést v odevzdání nebo v prezentaci? Pokud ano, jak to chcete uvést?
>
> Děkujeme.

Internal, not for the organizers: until questions 1, 2 and 11 are answered the talk says "podle toho, co víme" and never quotes the assignment on the origin of the labels; the answer to 2 also decides whether OQ-005 (real time axis) is opened in `docs/REQUIREMENTS.md` (not edited here); the answers to 3 and 5 change Q&A N3 and N6.

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

### Physics review pass (branch `cloud/pitch-fix-3`, `docs/review-physics.md`)

Line numbers are those of `presentation/outline.md` and `presentation/slovnicek.md` after the merge of main c2b5bba (check with `grep -n` on the quoted text). Already applied on main and therefore not listed again: the slide 4 sentence (line 44), the slide 8 sentence (line 103), the slogan (line 109) and the placeholder `[[chyba osy výboje 0]]` (lines 4 and 125). The pitch script is already changed; the row times of its slides 1, 2, 4, 5, 6 and 7 moved (see 16.10), no section length changed (still 420 s: 38 + 28 + 20 + 63 + 80 + 40 + 34 + 74 + 43). Wording rule for every line: the model reproduces the institute's reconstruction from 24 signals; do not write "přesnost polohy plazmatu", "skutečný", "skutečnost", "předpověď".

`presentation/outline.md`:
* line 16 (sentence of slide 1): "Plazma v tokamaku COMPASS se musí držet daleko od stěny během milisekund, ale klasický výpočet jeho tvaru trvá minuty." becomes "Řízení potřebuje polohu a tvar plazmatu v milisekundách, úplná rekonstrukce rovnováhy se počítá po výboji a trvá minuty."
* line 18: add after it the bullet "Protažené plazma je svisle nestabilní a bez rychlého řízení uhne ke stěně (ÚFP má potvrdit, otázka 10 pro organizátory). Dotek stěny není strašák: 44,2 % řádků je limitovaných."
* line 20 ("Celý výboj ... 150 až 200 ms"): append "; nahlas se neříká. Čas v souboru je relativní a skutečný odstup řádků neznáme, proto se neříká ani 0,6 ms (439 řádků krát 0,6 ms by bylo 263 ms)."
* line 21: "dokáže malý model odhadnout tvar plazmatu z magnetických měření dost přesně a dost rychle?" becomes "dokáže malá neuronová síť napodobit rekonstrukci polohy a tvaru plazmatu z magnetických měření dost dobře a dost rychle?"
* line 25 (sentence of slide 2): "16 hlavních veličin popisujících tvar" becomes "16 hlavních veličin: poloha a tvar plazmatu, proud a údaj o limiteru"; after line 27 add the bullet "Síť nedostává proudy v cívkách pole ani model komory; nevíme, co všechno použila rekonstrukce."
* line 28: "bod X" becomes "dolní bod X" (v datech je vždy dolní, žádný horní bod X ani dvojitý nulový bod).
* line 47 (current): add "Proud je podle Ampérova zákona lineární funkce signálů cívek; tak přesná shoda znamená, že štítek je zřejmě odvozen z týchž signálů (neověřeno)."
* line 53: replace "chyby jsou posuny o pár řádků na přechodu" by "chyby se dělí rovným dílem mezi obě konfigurace (49 a 51 % čtverce chyby); kde v čase leží, jsme nevyhodnotili"
* line 61 and 63 (demo): "skutečné a odhadnuté body" becomes "body z rekonstrukce ústavu a odhadnuté body"; "Vybraný model nepředpovídá celý obrys" becomes "Vybraný model neodhaduje celý obrys"
* line 76 (not verified, slide 5): add "uzavřenou smyčku, chování signálů v provozu, rychlost změny polohy; čas řádků je relativní"
* line 83 to 85 (slide 6): add "Bod u limiteru je místo dotyku na stěně; medián radiální chyby 0,733 mm, průměr 4,55 mm táhnou řádky s jiným místem dotyku, nejhorší řádky 357 a 485 mm; vzdálenost plazmatu od stěny jsme neměřili." and after the sentence on the end of the discharge add "Příčinu neznáme; hypotéza (neověřeno): na koncích je malý proud a rychlé změny, takže je i rekonstrukce nejhůř určená."
* line 94 to 95 (slide 7, noise): add "Šum v souboru je od organizátorů (bílý, směrodatná odchylka 16 % směrodatné odchylky signálu u cívek, 9 % u smyček toku; rozsah poměru 0,086 až 0,167 vypadá na šum úměrný signálu, neověřeno); posun jsme vyrobili sami, lineární v relativním čase; kalibraci a výpadek čidla jsme netestovali."
* line 105: "Přesnost: osa 0,13 mm" becomes "Shoda s rekonstrukcí: osa 0,13 mm"
* line 108: "Zbývá napojení na řídicí systém, víc výbojů a odolnost proti šumu." becomes "Zbývá celý řetězec od čidel k řízení, zkouška v uzavřené smyčce, víc výbojů a odolnost proti skutečným chybám čidel."
* line 113 (součet času): the order of cuts becomes the one in the Lead notes of the pitch script (6:11 Platí jen pro jeden tokamak; 4:01; camera); already cut: the length of the discharge, 42 972, p99 clause, "Zadání chce jednotky", 2,64 and 2,22, 135 of 149, the Ampère sentence.
* line 130 (Do zálohy): the line "Učení na zašuměných datech zhorší čistá data ..." stays; add to line 134 "Posun, který zkoušíme, je lineární v relativním čase výboje; skutečný posun integrátoru roste s absolutním časem."
* new line in "Do zálohy": "Deset nejtěžších fyzikálních otázek F1 až F10 je v pitch scriptu (část Příloha: deset nejtěžších fyzikálních otázek)."

`presentation/slovnicek.md` (line 3 says "Dvanáct pojmů"; with the new entry it is "Třináct pojmů"):
* line 7 (Bod X): "místo, kde se magnetické siločáry kříží a kde se hranice plazmatu zalamuje." becomes "místo, kde je poloidální magnetické pole nulové a kde se kříží hranice plazmatu, neboli separatrix; v našich datech je vždy dolní."
* line 8 (Dotykový bod): "místo na dně komory, kam dopadá okraj plazmatu, a proto se tam stěna nejvíc namáhá." becomes "místo, kde hranice plazmatu protíná desky divertoru; tam dopadá nejvíc tepla."
* line 9 (Limiter): "pevná část stěny, o kterou se plazma může opřít; chybu v jeho poloze odhadujeme nejhůř." becomes "pevná část stěny, o kterou se plazma může opřít; bod u limiteru je místo na stěně, kde se plazma dotkne, a jeho polohu odhadujeme nejhůř."
* line 13 (Smyčka toku): "drát kolem komory, který měří magnetický tok, a je tedy jedním z 24 vstupů modelu." becomes "závit, jehož napětí po integraci dává magnetický tok jím obepnutý; je jedním z 24 vstupů modelu."
* line 14 (Cívka): "drát, který měří magnetické pole; samotných 16 cívek IPR dává skoro stejnou přesnost jako všech 24 vstupů." becomes "Cívka IPR: integrovaná částečná Rogowského cívka, měří integrál magnetického pole podél úseku stěny komory; samotných 16 cívek IPR dává skoro stejnou souhrnnou chybu jako všech 24 vstupů."
* line 15 (Odezva): "náš výpočet trvá setiny milisekundy a podle zatížení procesoru o něco víc." becomes "náš výpočet sítě trvá setiny milisekundy a podle zatížení procesoru o něco víc; sběr signálů a řízení do toho nepatří."
* new entry after Tokamak: "**Rekonstrukce rovnováhy:** výpočet polohy a tvaru plazmatu z magnetických měření, který se dělá po výboji a trvá minuty; z ní pocházejí správné odpovědi, které se síť učí napodobit a se kterými ji porovnáváme. Nejde o měření plazmatu."
* the wording "Odhad" instead of "předpověď" everywhere in both files.

Open on lane K's side, not a wording change: the definitions of elongation and the three triangularities, and the convention of the extreme points when the plasma is limited, are not written in the repository (review M8). Copy them from the organizers' notebook into the glossary when the answer to question 4 arrives.
