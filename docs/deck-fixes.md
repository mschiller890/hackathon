# Deck fixes for `presentation/deck/slides.pptx`

For the colleague who owns the deck. Source: `docs/review-findings-2.md` (Kritik 2) and the rewritten `presentation/pitch-script.md`. Nothing here edits the deck for you; each item says the slide, what to change, and the exact Czech text. Slide numbers are the deck's 14 screens (the footer counter is wrong, see item 0.1). Items marked **[[odezva vybraného modelu]]** wait for one measurement (finding H1a: time of the shipped model pair on an idle machine, owner: a local terminal, file `results/ipp1-latency-shipped.md`); leave the placeholder text in until the number exists, then replace it with the measured median, p99 and the CPU name. Until then use the fallback written next to it.

Vocabulary to use on every slide: **základní síť** (24 vstupů, 107 152 parametrů), **vybraný model** (základní síť + rozdíly sousedních cívek + lineární model pro proud + zvláštní síť pro bod u limiteru), **odložené výboje** (30 výbojů odložených před finálním výběrem). Never "nasazený model", "zamčené", "nikdo neviděl".

## 0. Whole deck

0.1 **Counters.** On every slide delete the footer counter ("1 / 8", "2 / 8", "3 / 8" twice, "4 / 8" three times, "5 / 8", "6 / 8", "7 / 8", "8 / 8"). The audience sees 14 screens in 7 minutes. (L2)

0.2 **Search and replace.** "zamčených" or "zamčené" becomes "odložených"; "nasazený model" becomes "vybraný model" (chart legend on slide 7, footnote on slide 11); delete "nikdo neviděl" wherever it stands (slide 7 caption). Delete the phrase "nasazujeme", use "použijeme". (H2, L4)

0.3 **Speaker notes.** Notes of the old deck still carry "cívky IPR nesou skoro všechno" (slide 7 or 6), "rychlost nebude překážkou" (slide 11), "do 0,029", "0,24 ms", "na druhém počítači 0,032" and "Křivka ještě neklesla na dno". Replace the notes of every slide with the "Co se říká" cells of the matching section in `presentation/pitch-script.md` (the script's section list is in its table "Časový přehled", column "Snímek v decku"). If you rebuild with `deck/build_deck.py` the notes follow the script automatically, but three split times in the file must change because the new rows start at other times:
* line 256 and 264: `end="0:24"` and `start="0:24"` become `0:21` (the picture changes at the row "Klasický výpočet", now at 0:21);
* line 320 and 330: `end="1:54"` and `start="1:54"` become `1:37`;
* line 330 and 356: `end="2:14"` and `start="2:14"` stay (the inputs row now starts at 2:14);
* line 299 comment: the camera screen is a hidden backup and has no seconds.
Also check `build_deck.py` text for the strings in items 7, 11, 12, 13 and 14 below; the script has its own copies.

0.4 **Hidden slides.** Slide 5 (camera) is hidden (new, see 5). Slide 10 (stills) stays hidden and gets a note in the speaker view of slide 9: "Záloha: klávesa H otevře skrytý snímek 10." (M6)

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

9.2 Add to the speaker notes: "Klávesa H: skrytý snímek 10 se stopkami." (0.4)

## 10. Slide 10 (hidden, stills)

Stays hidden. Add the caption under the three pictures: "Základní síť, výboj 123, mimo učení. Obrázky z prohlížeče." (The viewer tile also has to say "základní síť" instead of the latency of an unnamed model; that is the viewer owner's job, not the deck's.)

## 11. Slide 11 (Výpočet sítě rychlosti nebrání) (H1, H3, M7)

11.1 Tile text under "0,0145 ms": "medián jednoho odhadu základní sítě, procesor Apple M5" (was "medián jednoho odhadu na procesoru").
Tile text under "0,0209 ms": "99 % odhadů základní sítě je rychlejších" (keep the p99 gloss, 0.5).

11.2 **Add a third tile** next to them:
* with the measurement: "[[odezva vybraného modelu]] ms" / "vybraný model (3 části), procesor [[CPU]], klidný počítač"
* fallback until it exists: "asi 0,18 ms" / "vybraný model, zatím odhad z podobného postupu na vytíženém počítači, neměřeno"

11.3 Footnote: keep "Rozpočet je 1 až 10 ms." and "Celý odhad základní sítě od čísel na vstupu po čísla na výstupu: medián 0,0140 ms." **Delete** the sentence "Grafická karta je pro jeden odhad pomalejší (0,27 ms, s přenosem dat 0,49 ms)." (time cut) and the sentence "Nasazený model se třemi částmi je pomalejší, asi 0,18 ms (podobný recept, zatížený počítač)." (replaced by 11.2). Keep "Neověřeno: sběr signálů z cívek, nejhorší doba na systému reálného času a přesnost na skutečně zašuměných signálech." and add: "Přepínání mezi modelem pro čisté a pro zašuměné vstupy netestováno. Na systému bez reálného času se ojediněle objeví špičky."

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

## 14. Slide 14 (Závěr) (H1, H5, M7)

14.1 Big number tile: "0,0145 ms" with the label "Jeden odhad základní sítě, procesor Apple M5". Next to it a second, smaller number: "[[odezva vybraného modelu]] ms" / "vybraný model" (fallback until measured: "asi 0,18 ms, odhad").

14.2 Line "Klasický výpočet trvá minuty. Zadání chce jednotky až desítky milisekund." stays; add after it: "Obojí je pod rozpočtem 1 až 10 ms."

14.3 Tile "Přesný / desetiny milimetru na ose, bodu X a dotykových bodech" becomes:
"Přesnost" / "desetiny milimetru na čistých vstupech, jednotky milimetrů na zašuměných (osa 0,13 mm a 2,38 mm, 30 odložených výbojů)"

14.4 Tile "Zbývá" becomes: "Zbývá" / "bod u limiteru, neobvyklé tvary (samostatně neověřeny), odolnost proti šumu, napojení na řízení"

14.5 Closing line "Desetiny milimetru za setiny milisekundy." becomes "Desetiny milimetru za desetiny milisekundy." (until the measured time of the shipped model says otherwise; then ask the Lead which of the two to keep).

14.6 The background picture (sunset) has no label: add the small print "Ilustrace." as on slide 1. (L6)

## What waits for a measurement

Only the placeholders **[[odezva vybraného modelu]]** (items 11.2, 14.1 and the script rows of slides 5 and 8) and `[[CPU]]`. Everything else here is final and checked against `results/` (numbers and files are listed in the Lead notes at the end of `presentation/pitch-script.md`). The viewer (`viewer/`) is outside this list: its latency tile should say "základní síť" (H1d).
