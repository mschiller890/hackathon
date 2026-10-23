# Osnova prezentace: tvar plazmatu z magnetických měření

Celkem 7 minut (420 sekund), 8 snímků a živá ukázka. U každého snímku je čas a jedna věta, kterou musí říct. Časy a mluvený text jsou v souboru pitch script, tady jsou věty a podklady. Úpravy obrazovky jsou v `docs/deck-fixes.md`.
Čísla pocházejí jen ze složky results. Kde číslo ještě neexistuje, stojí v dvojitých hranatých závorkách, například `[[latency shipped]]`.
Zdroje čísel: soubory ipp1 final, ipp1 baseline, ipp1 inputs, ipp1 time a ipp1 latency ve složce results.

Pravidla pro všechna čísla:

* Dva modely se nezaměňují. Základní síť: 24 vstupů, 107 152 parametrů. Vybraný model: základní síť plus rozdíly sousedních cívek, lineární model pro proud a zvláštní síť pro bod u limiteru. Pro zašuměné vstupy se používá síť učená se šumem.
* Pod každým číslem přesnosti stojí protokol: 30 odložených výbojů (osa 0,133 mm), křížová validace na 119 výbojích (0,230 mm), novější čísla výbojů (0,397 mm), u základní sítě pět dělení po výbojích (0,377 mm).
* Každá rychlost má model a procesor: základní síť 0,0145 ms, Apple M5; vybraný model `[[latency shipped]]`, do změření asi 0,18 ms (odhad z podobného postupu na vytíženém počítači).
* Slova zamčená a nikdo neviděl se nepoužívají. Říká se odložené výboje (odložené před finálním výběrem).

## Snímek 1: Problém (38 s)

Věta: Plazma v tokamaku COMPASS se musí držet daleko od stěny během milisekund, ale klasický výpočet jeho tvaru trvá minuty.

* Zadání žádá reakci v řádu jednotek až desítek milisekund (podle zadání úlohy).
* Klasická rekonstrukce rovnováhy trvá minuty, tedy o několik řádů déle.
* Celý výboj na tokamaku COMPASS trvá podle organizátorů asi 150 až 200 ms (údaj organizátorů, neměřili jsme ho).
* Naše otázka: dokáže malý model odhadnout tvar plazmatu z magnetických měření dost přesně a dost rychle?

## Snímek 2: Data (28 s)

Věta: Máme 42 972 řádků ze 149 výbojů, na každém řádku 24 magnetických měření a 16 hlavních veličin popisujících tvar (soubor jich obsahuje 31).

* Vstupy: 24 magnetických čidel, dvě skupiny: 16 cívek IPR a 8 smyček toku FL.
* Výstupy: poloha osy, bod X, dotykové body na divertoru, protažení, trojúhelníkovost, proud plazmatem, bod u limiteru.
* Data jsou důvěrná, proto na snímku nejsou žádné surové hodnoty, jen souhrny.
* Dělíme po celých výbojích, nikdy po řádcích, jinak by se model učil na tom, co testuje.

## Snímek 3: Metoda (24 s)

Věta: Základní síť má 107 152 parametrů; vybraný model je její vylepšení; u každého čísla říkáme, na jakých výbojích bylo změřeno.

* Srovnání: lineární model (hřebenová regrese) proti malé neuronové síti (základní síť).
* Vybraný model pro čisté vstupy: síť s rozdíly sousedních cívek, lineární model pro proud a zvláštní síť pro bod u limiteru.
* Ověření: základní síť pětkrát jinak po výbojích; vybraný model navíc na 30 výbojích odložených před finálním výběrem (8 761 řádků). Náměty na úpravy modelu vznikly na křížové validaci přes všech 149 výbojů, odložených 30 bylo při návrhu v testovacích částech; po odložení se nic neladilo, jen se vybírala jedna ze čtyř variant uvnitř 119 výbojů.
* Dále: kolik vstupů opravdu potřebujeme, jak stabilní je výstup v čase, jak rychlá je odpověď, jak síť snáší šum.
* Kamera je skrytá záloha bez času, viz konec osnovy.

## Snímek 4: Výsledky (54 s)

Věta: Na 30 odložených výbojích určí vybraný model osu s chybou 0,13 mm (základní síť 0,31), v křížové validaci na 119 výbojích 0,23 mm a na novějších číslech výbojů 0,40 mm.

* Protokol 1, 30 odložených výbojů, vybraný model proti základní síti, průměrná chyba: radiální osa 0,133 mm proti 0,307 mm (bootstrapový interval 0,099 až 0,177 mm), svislá osa 0,172 mm proti 0,321 mm, bod u limiteru 4,55 mm proti 10,6 mm (radiálně) a 8,35 mm proti 22,5 mm (svisle).
* Proud plazmatem: lineární model 0,035 kA, základní síť 1,20 kA. Je to lineární model, který žádné semeno nemá; síť to neuměla. Nepočítáme to do tvrzení, že je vybraný model lepší.
* Protokol 2, křížová validace na 119 vývojových výbojích: radiální osa 0,230 mm u vybraného modelu (základní síť 0,479 mm). Odložených 30 vychází lépe: je asi o 35 % lehčí (souhrnná relativní chyba vybraného modelu 0,059 proti 0,091, u základní sítě 0,080 proti 0,123) a má jen 2 výboje s opačným směrem proudu (6,7 % řádků proti 10,7 %).
* Protokol 3, novější čísla výbojů (učení na 60 nejnižších, test na 59 nejvyšších, čísla zřejmě sledují čas, neověřeno): radiální osa 0,397 mm u vybraného modelu (0,216 mm při náhodném dělení), 1,23 mm u základní sítě (0,448 mm); část rozdílu vysvětluje menší učící sada.
* Vybraný model je lepší u všech sedmi veličin v každém z pěti semen: zisk u osy, dotykového bodu a bodu u limiteru je 42 až 60 %, několikrát víc než rozdíl mezi semeny. Bod X (radiálně) je jen o něco lepší, 0,115 mm proti 0,161 mm.
* Poctivě k chvostům: model je lepší v průměru a ve většině řádků, ale několik jednotlivých řádků je horších, například střední kvadratická chyba radiálního bodu X je 0,454 mm proti 0,305 mm.
* Základní síť, pět dělení po výbojích: osa 0,38 mm a 0,39 mm, lineární model 2,4 a 2,66 mm, tedy u osy více než šestkrát hůř. Průměr skrývá chvosty: medián radiální osy je 0,153 mm, 99 % řádků je pod 3,74 mm, nejhorší řádek má 64 mm, hlavně na konci výboje. Limitované plazma je asi 2,3krát horší než divertorové.
* Zda je plazma opřeno o limiter, určí základní síť správně v 99,3 % případů (pět dělení), vybraný model v 99,16 % na 30 odložených výbojích; chyby jsou posuny o pár řádků na přechodu.
* Pro zašuměné vstupy vybraný model nepoužijeme: na šumu selže (osa 190 mm). Tam nasadíme síť učenou se šumem a posunem, viz snímek 7.
* Méně vstupů (základní síť, pět dělení): se všemi 24 vstupy je souhrnná relativní chyba 0,063, s nejlepšími 12 je 0,077, s nejlepšími 8 je 0,094 (osa R 0,904 mm proti 0,377 mm).
* Samotných 16 cívek IPR dává souhrnnou chybu 0,066, samotných 8 smyček toku 0,285, tedy 4,3krát horší. Mluví se takto: samotné cívky stačí na skoro stejnou souhrnnou chybu, osm nejlepších už ne. Žádné jedno čidlo není samo nezbytné: pořadí podle tří způsobů se téměř neshodují. Neříkáme, která čidla jsou důležitá, říkáme jen výsledek po rodinách.
* Obrázek: graf chyby podle počtu vstupů (soubor ipp1 inputs ve složce results).

## Živá ukázka mezi snímkem 4 a 5 (88 s)

Věta: V prohlížeči vidíte skutečný a odhadnutý tvar plazmatu vedle sebe a chybu v čase, jednu typickou a jednu špatnou ukázku; v ukázce je základní síť, ne vybraný model.

* Posuvník času, skutečná a odhadnutá hranice, tabulka chyb. Podrobný scénář je v souboru pitch script.
* Prohlížeč přehrává předpovědi základní sítě mimo učení (validační skupina 1 z 5); výboje 123, 0, 4 a 11 nepatří mezi odložených 30. Dlaždice latence v prohlížeči má říkat základní síť, 0,0145 ms.
* Před ukázkou se nahlas řekne, že vybraný model je na odložených výbojích u osy asi dvakrát přesnější.
* Čísla z prohlížeče (chyba osy výboje 0, tvar chyby výboje 123) se zapíšou den předem po přehrání; do té doby jsou `[[chyba osy výboje 0]]`.
* Podíl výbojů: 128 ze 149 (85,9 %) má průměrnou chybu osy pod 1 mm, 3 přes 5 mm (základní síť, pět dělení).

## Snímek 5: Verdikt pro řízení v reálném čase (37 s)

Věta: Výpočet sítě rychlosti nebrání: základní síť 0,0145 ms na procesoru Apple M5, vybraný model asi `[[latency shipped]]` ms, rozpočet je 1 až 10 ms; ověřili jsme ale jen výpočet samotné sítě.

* Základní síť, procesor Apple M5, jeden vzorek: medián 0,0145 ms, 99 % měření pod 0,0209 ms. Stroj byl sdílený a vytížený, takže čas závisí na zatížení; na jiném procesoru (AMD Ryzen 5 7535HS) vyšlo 0,032 ms.
* Celý odhad základní sítě od surových čísel na vstupu po čísla na výstupu: medián 0,0140 ms, 99 % měření pod 0,0503 ms. Nejvyšší hodnoty se na systému bez reálného času ojediněle objeví až v milisekundách, to není horní mez.
* Vybraný model (síť s rozdíly cívek, lineární model pro proud a síť pro bod u limiteru) trvá jeden odhad `[[latency shipped]]` ms na klidném stroji; do změření je odhad 0,1775 ms z podobného postupu na vytíženém stroji, asi dvanáctkrát víc než základní síť. Pořád je to hluboko pod rozpočtem 1 až 10 ms.
* Grafická karta a druhý počítač se nahlas neříkají (škrtnuto kvůli času): grafická karta 0,27 ms, s přenosem dat 0,49 ms, pomalejší než procesor, protože model je malý.
* Neověřili jsme: sběr a integraci signálů z cívek, nejhorší dobu na systému reálného času a přesnost na skutečně zašuměných signálech. Přepínání mezi modelem pro čisté a pro zašuměné vstupy jsme netestovali.
* U každého času říkáme, na jakém modelu a procesoru byl měřen.

## Snímek 6: Meze (31 s)

Věta: Nejhůř se odhaduje bod u limiteru (vybraný model 4,55 a 8,35 mm na 30 odložených výbojích) a chyby rostou hlavně na konci výboje.

* Limitované plazma tvoří 44 % řádků, ale 92 % čtverce chyby radiální osy (základní síť, pět dělení). Bod u limiteru je v prvních 2 % výboje 52,6 mm, uprostřed výboje 8,28 mm.
* Bod u limiteru, vybraný model, 30 odložených výbojů: radiálně 4,55 mm, svisle 8,35 mm, v jednom procentu řádků až 77,5 a 92,2 mm. Základní síť: 10,7 a 22,2 mm v pěti dělení.
* Chyby rostou hlavně na konci výboje, 1,6 až 3,7krát oproti středu: u základní sítě má osa na konci 0,9 mm, uprostřed 0,24 mm (graf pod dlaždicemi je základní síť, dlaždice jsou vybraný model). U vybraného modelu na odložených výbojích: poslední 2 % výboje 0,578 mm, střed 0,114 mm. Na začátku roste jen chyba polohy osy (radiální 2,5krát, svislá 1,5krát).
* Kolísání (jen poznámka pod čarou, nahlas se neříká): na čistých vstupech 0,96 až 1,07 u 13 veličin (u sedmi veličin tabulky 0,97 až 1,07). Na zašuměných vstupech kolísá výstup sítě naučené na čistých datech 8,4krát (osa R) a 3,3krát (osa Z) víc než skutečnost, po učení se šumem a posunem 1,7krát a 1,65krát. Nikdy neříkáme jen 0,97.
* Čísla výbojů jsou zřejmě seřazena podle času, což jsme s organizátory neověřili. Na souvislých blocích čísel je chyba základní sítě 1,5 až 2,9krát větší (osa R 1,23 mm místo 0,448 mm), z části i proto, že je méně učících výbojů.
* S menším počtem vstupů přesnost klesá: se 4 vstupy je souhrnná chyba 0,204.

## Snímek 7: Co model neumí (76 s)

Věta: Model je křehký vůči šumu, potřebuje dost výbojů, neobvyklé tvary jsme samostatně neověřili a platí jen pro jeden tokamak.

* Šum, základní síť, pět dělení po výbojích: osa má chybu 0,38 mm na čistých datech, ale 10,15 mm na datech s šumem; učení na zašuměných datech to srazí na 2,64 mm, na čistých datech pak 2,22 mm. Pozor na tři různé protokoly: 2,64 a 2,22 jsou pět dělení, 2,38 mm (osa) a 4,65 kA (proud) je síť učená se šumem na 30 odložených výbojích, 2,99 mm je vývojová křížová validace.
* Vybraný model pro čisté vstupy na šumu selže úplně (osa 190 mm), proto pro zašuměné vstupy použijeme síť učenou se šumem: osa 2,38 mm (osmnáctkrát víc než 0,133 mm na čistých vstupech), bod u limiteru 25,8 a 38,9 mm, proud 4,65 kA (lineární část druhého modelu učeného se šumem má 4,03 kA, jako jeden recept to spuštěno nebylo).
* Množství dat, základní síť: s 30 učícími výboji je chyba osy 1,47 mm (radiální) a 0,95 mm (svislá), se všemi 119 je 0,38 mm. Od 30 do 119 výbojů klesá zhruba na polovinu při zdvojnásobení, ale s pevným počtem 60 epoch, takže část zlepšení tvoří víc kroků učení.
* Neobvyklý tvar: když při učení vynecháme celou rodinu tvarů, chyba je 1,0 až 3,0krát větší, obvykle 1,2 až 2,4krát. Opravdu neobvyklých je ale jen 18 výbojů ze 149 a nikdy nebyly vynechány samostatně, takže o tvarech mimo rozsah dat výsledek nic neříká; rozdíly 1,1 až 1,3krát jsou v šumu měření.
* Kamera (skrytá záloha): model naučený na nepohnutých snímcích je křehký, posun o 4 pixely ztrojnásobí chybu osy (z 1,54 na 4,95 mm); kamera a magnetická měření dohromady magnetickou síť nepřekonaly (1,21 mm proti 0,24 mm). Měřeno jen na dvou z pěti dělení.
* Ověřeno jen na jednom tokamaku a jen vůči rekonstrukci, kterou dodal ústav. Model odhaduje jen tvar a řízení plazmatu samo nenahrazuje.

## Snímek 8: Závěr (44 s)

Věta: Přesnost na čistých vstupech je desetiny milimetru, rychlost výpočtu desetiny milisekundy, ale model ještě není připraven pro řízení.

* Přesnost: osa 0,13 mm na 30 odložených výbojích, asi 0,2 mm v křížové validaci (0,40 mm na novějších číslech); na zašuměných vstupech jednotky milimetrů (2,38 mm).
* Rychlost: základní síť 0,0145 ms (procesor Apple M5), vybraný model asi `[[latency shipped]]` ms; obojí hluboko pod rozpočtem 1 až 10 ms. Výpočet sítě, ne celý řídicí systém.
* Upřímně: slabý bod u limiteru, neobvyklé tvary jsme samostatně neověřili a šum mu vadí, pokud se na něj neučí.
* Sběr signálů a napojení na řídicí systém jsme nezkoušeli. Zbývá napojení na řídicí systém, víc výbojů a odolnost proti šumu.
* Slogan: desetiny milimetru za desetiny milisekundy (do změření vybraného modelu; pak podle měření).

## Součet času

Podle rozhodnutí vedoucího (RP 11) platí časy ze souboru pitch script, přepočtené po kontrole Kritika 2: 38 + 28 + 24 + 54 + 88 (ukázka) + 37 + 31 + 76 + 44 = 420 sekund, tedy 7 minut. Kamerový snímek je skrytá záloha bez času. Při zpoždění se škrtá: věta o rychlosti ukázky, věta Zbývá napojení, kamera, poslední věta snímku 7.

## Záloha: kamera (skrytý snímek, 20 s jen když je mezera)

Věta: Malá kamerová síť (snímky 48 na 64 bodů) je 1,3 až 13krát horší než cívky.

* Pět dělení po výbojích, 78 výbojů, 12 epoch, každý osmý snímek (`results/cloud-camera-findings.md`). Radiální osa 1,79 mm (šedě 1,70 mm) proti 0,377 mm u cívek, srovnání je orientační, protože jsou to jiné řádky. Nejblíž je u bodu u limiteru (1,3krát horší v relativní chybě), nejdál u proudu plazmatem (13krát horší než základní síť; vůči lineárnímu modelu mnohem víc). Barva nepomáhá.
* Říká to něco o této malé síti, ne o tom, že kamera nenese informaci.
* Místní kontrola kamery na dvou z pěti dělení se shodne: na ose je 6 až 8krát horší než magnetická měření (1,54 mm proti 0,24 mm na stejných řádcích) a proud plazmatem určit nejde (chyba 18 kA).

## Chybějící čísla (DOPLNIT)

* `[[latency shipped]]`: čas vybraného modelu na klidném stroji (místní terminál, `results/ipp1-latency-shipped.md`).
* `[[chyba osy výboje 0]]`: číslo z přehrání v prohlížeči.
* Kamera: srovnání na stejných řádcích a zbylé běhy z cloudu (čísla z cloudu zatím neprošla kontrolou vedoucího).

## Do zálohy: dotazy poroty (neříká se nahlas)

* Posun v čase jsme zkoušeli jen na vlastních, uměle vytvořených datech: posun se směrodatnou odchylkou sklonu 0,3 přidá k chybě osy asi 1 mm u sítě naučené na šumu.
* Učení na zašuměných datech zhorší čistá data: chyba osy 2,22 mm místo 0,38 mm (základní síť, pět dělení).
* Tři po sobě jdoucí časy zlepšují zašuměný vstup (osa 2,64 na 2,33 mm), ale na čistém vstupu osu zhoršují (0,38 na 0,57 mm). Sloupec 2,33 se nemluví a z grafu se maže.
* Naměřeno pro jednu inicializaci a jednu realizaci šumu na každé rozdělení, rozdíly pár procent nejsou prokázané; u hlavního srovnání pět semen.
* Rozptyl veličin je malý jen u osy, bodu X a dotykových bodů, směrodatná odchylka od 2,4 do 13,7 mm; u bodu limiteru je 89,6 a 153,3 mm a u proudu plazmatem 114 kA, proto chyby uvádíme v mm i vůči rozptylu. 98 % hodnot osy leží v pásu širokém 42,3 mm (radiálně) a 56,4 mm (svisle).
* Soubor se šumem od organizátorů obsahuje bílý šum bez měřitelného posunu: šum má asi 0,158 směrodatné odchylky signálu u cívek a 0,090 u smyček toku. Veškerý posun, který zkoušíme, je umělý.
* Pozor, neříkat: "pět složek nese 99,9 % informace". Správně je rozptyl, ne informace: síť, která vidí jen prvních pět hlavních složek, má radiální chybu osy 2,63 mm místo 0,41 mm (asi 6,5krát horší).
* Model ví, kdy se mýlí: pět sítí s různým zrnem náhodných čísel se nejvíc rozcházejí na 10 % řádků, které nesou 47 % celkové chyby, a chyba na nich je 8,1krát větší než na zbytku. Netestovali jsme, zda se rozcházejí i na neobvyklých tvarech nebo na zašuměném vstupu, a řádky jednoho výboje jsou téměř kopie, takže jde o pořadí, ne o pravděpodobnost chyby.
* Deset zlých otázek a třináct dalších od Kritika 2 s odpověďmi je v souboru pitch script.
