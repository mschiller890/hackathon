---
tags:
  - hackathon
---

# Pitch: 7 minut pro porotu

Stav: přepsáno v pátek 23. října večer podle `docs/review-findings-2.md` (Kritik 2) a `docs/claims-corrections.md`, potom opraveno podle `docs/review-findings-3.md` (Kritik 3). Každá mluvená věta souhlasí se souborem v `results/` a s obrazovkou po úpravách z `docs/deck-fixes.md`. Pod každým číslem přesnosti říkáme, na jakých výbojích bylo změřeno. Čas vybraného modelu je změřený (`results/ipp1-latency-shipped.md`). Na přehrání čeká jen `[[chyba osy výboje 0]]` (číslo z prohlížeče den předem; bez něj se říká věta bez čísla). Název `[[odezva vybraného modelu]]` je rezervovaný pro číslo, které by čekalo na další soubor; teď se nepoužívá. Pořadí snímků sedí s `repo/presentation/outline.md`; co má změnit sazeč decku, je v `docs/deck-fixes.md`. Formát tabulek se nesmí měnit, čte ho `deck/build_deck.py` (nadpisy `### Snímek N`, řádek `Hlavní věta:` a řádky `| m:ss | sek. | kdo | text | obrazovka |`).

## Jak je to postavené

* Začátek: problém, který bolí. Plazma se dotkne stěny, výboj trvá 150 až 200 milisekund, klasický výpočet tvaru trvá minuty.
* Jádro: živá ukázka v prohlížeči tvaru. V ukázce je základní síť, ne vybraný model; říkáme to nahlas před ukázkou.
* Konec: dvě rychlosti (základní síť, vybraný model) a upřímně, co model neumí. Slogan: desetiny milimetru za setiny milisekundy (0,0145 a 0,027 ms jsou setiny milisekundy).
* Dva modely, vždy pojmenované: základní síť (24 vstupů, 107 152 parametrů) a vybraný model (základní síť plus rozdíly sousedních cívek, lineární model pro proud, zvláštní síť pro bod u limiteru). Pro zašuměné vstupy se používá třetí věc, síť učená se šumem.
* Tři protokoly, nikdy je nemíchat bez štítku: 30 odložených výbojů (osa 0,13 mm), křížová validace na 119 výbojích (0,23 mm), novější čísla výbojů (0,40 mm). Základní síť má vlastní protokol: pět dělení po výbojích (osa 0,38 mm). Číslo 119 má dva významy: vývojová sada (119 výbojů, protokol křížové validace) a 119 učících výbojů v každém z pěti dělení všech 149 (křivka podle počtu výbojů, základní síť).
* Řečníci: A je první řečník (majitel týmu), B je druhý řečník (kolega).
* Porota: fyzici z ÚFP a odborníci na strojové učení. Čísla říkáme pomalu, jedno po druhém, a vždy s protokolem.

## Časový přehled

| Čas | Sek. | Co je na obrazovce | Snímek v decku | Obrázek | Kdo |
|---|---|---|---|---|---|
| 0:00 až 0:38 | 38 | Snímek 1: Problém | 1, 2 | 04-wall-damage.png, potom 02-minutes-vs-ms.png | A |
| 0:38 až 1:06 | 28 | Snímek 2: Data | 3 | 03-coils.png | B |
| 1:06 až 1:26 | 20 | Snímek 3: Metoda | 4 (5 skrytá záloha) | 06-neural-bridge.png | A |
| 1:26 až 2:29 | 63 | Snímek 4: Výsledky | 6, 7, 8 | 05-shape-schematic.png | A a B |
| 2:29 až 3:49 | 80 | Živá ukázka, mezi snímkem 4 a 5 | 9 (10 skrytá záloha) | žádný, na obrazovce je prohlížeč tvaru (repo/viewer/index.html) | A, jedna věta B |
| 3:49 až 4:29 | 40 | Snímek 5: Rychlost, verdikt pro řízení | 11 | 02-minutes-vs-ms.png (zopakovat jako pozadí) | B |
| 4:29 až 5:03 | 34 | Snímek 6: Meze | 12 | žádný obrázek, na snímku je graf chyby osy podle času | A |
| 5:03 až 6:17 | 74 | Snímek 7: Co model neumí | 13 | žádný obrázek, na snímku jsou dva grafy (šum, počet výbojů) | B a A |
| 6:17 až 7:00 | 43 | Snímek 8: Závěr | 14 | 07-closing.png | A a B |
| celkem | 420 | 8 snímků a ukázka (kamera je skrytá záloha bez času) | | | |

Kamerový snímek je skrytá záloha a v časovém plánu nemá žádné vteřiny (viz Záloha: kamera). Podle Kritika 3 (část 5) je čtení všech čísel slovy o 25 až 50 sekund delší než prostý počet slov; proto jsou věta o rychlosti v ukázce, věta Zbývá napojení a věta Typický výboj sedí z textu pryč, věta U každého čísla řeknu (snímek 3) je pryč, řádek o učení se šumem je zkrácený a poslední věta snímku 7 je zkrácená. Tabulka počtů je v Lead notes; stopkami to dosud nikdo nezměřil. Pokud je to před vystoupením o víc než 10 sekund přes, škrtá se v tomto pořadí: řádek 0:38 zkrátit na téměř 43 tisíc okamžiků, kamera (je skrytá), věta Platí jen pro jeden tokamak. Řádky o grafické kartě a o druhém počítači jsou z mluveného textu pryč.

## Časovaný scénář

Čas je začátek řádku. Sloupec Co se říká je přesně to, co zazní. Text v závorkách se neříká. Rychlost řeči je asi 1,7 slova za sekundu, u čísel pomaleji.

### Snímek 1: Problém (0:00 až 0:38, 38 s)

Hlavní věta: Plazma se musí držet daleko od stěny během milisekund, klasický výpočet tvaru trvá minuty.

Obrázek: 04-wall-damage.png, potom 02-minutes-vs-ms.png

| Čas | Sek. | Kdo | Co se říká | Na obrazovce |
|---|---|---|---|---|
| 0:00 | 9 | A | Čeho se bojí každý, kdo provozuje tokamak: žhavé plazma se dotkne stěny a poškodí ji. | Snímek 1. Obrázek 04-wall-damage.png přes celou plochu. Je to ilustrace, neříkej, že jde o fotografii. |
| 0:09 | 12 | A | Celý výboj na tokamaku COMPASS trvá podle organizátorů jen 150 až 200 milisekund, řízení proto potřebuje tvar plazmatu v milisekundách. | Stále obrázek 04. |
| 0:21 | 7 | A | Klasický výpočet tvaru z magnetických měření ale trvá minuty. To je propast. | Přepnout na obrázek 02-minutes-vs-ms.png (přesýpací hodiny proti záblesku) a dlaždice minuty a jednotky ms. |
| 0:28 | 8 | A | Naše otázka: odhadne malá neuronová síť tvar plazmatu dost přesně a dost rychle? | Dole na snímku věta s otázkou. |
| 0:36 | 2 | A | Data představí kolega. | Pohled na B, klik na snímek 2. |

### Snímek 2: Data (0:38 až 1:06, 28 s)

Hlavní věta: 42 972 okamžiků ze 149 výbojů, 24 vstupů, 16 veličin, dělení po celých výbojích.

Obrázek: 03-coils.png

| Čas | Sek. | Kdo | Co se říká | Na obrazovce |
|---|---|---|---|---|
| 0:38 | 8 | B | Máme data z tokamaku COMPASS: 42 972 okamžiků ze 149 výbojů. | Snímek 2 (tři dlaždice 24, 16, 149). Obrázek 03-coils.png je schéma, ne skutečný řez. |
| 0:46 | 12 | B | V každém okamžiku 24 měření z cívek a smyček toku a 16 veličin tvaru, které má model určit. | Ukázat na obrázek. Je na něm 16 cívek, smyčky toku na něm nejsou. |
| 0:58 | 8 | B | Dělíme vždy po celých výbojích, aby se model netestoval na tom, co už viděl. | Spodní věta snímku. |

### Snímek 3: Metoda (1:06 až 1:26, 20 s)

Hlavní věta: Základní síť o 107 152 parametrech a z ní vylepšený vybraný model; u každého čísla říkáme, na jakých výbojích bylo změřeno.

Obrázek: 06-neural-bridge.png

| Čas | Sek. | Kdo | Co se říká | Na obrazovce |
|---|---|---|---|---|
| 1:06 | 7 | A | Základní síť je malá neuronová síť o 107 152 parametrech. | Snímek 3. Obrázek 06-neural-bridge.png ukazuje princip. Teček čidel je na něm 16, skutečných vstupů je 24. |
| 1:13 | 13 | A | Vybraný model je její vylepšení: rozdíly sousedních cívek, lineární model pro proud a zvláštní síť pro bod u limiteru. | Spodní věta snímku (co je vybraný model); pod ní věta o ověření (u každého čísla je napsáno, na jakých výbojích bylo změřeno). |

### Snímek 4: Výsledky (1:26 až 2:29, 63 s)

Hlavní věta: Na 30 odložených výbojích osa 0,13 mm (0,23 mm v křížové validaci, 0,40 mm na novějších číslech); samotné cívky stačí na skoro stejnou souhrnnou chybu.

Obrázek: 05-shape-schematic.png

| Čas | Sek. | Kdo | Co se říká | Na obrazovce |
|---|---|---|---|---|
| 1:26 | 7 | A | Odhadujeme osu, bod X a dva dotykové body, kam dopadá okraj plazmatu. | Snímek 4. Obrázek 05-shape-schematic.png asi 6 sekund, pak snímek s výsledky. |
| 1:33 | 19 | A | Třicet výbojů jsme odložili před posledním výběrem modelu; náměty na úpravy ale vznikly na všech 149. Na odložených má vybraný model chybu osy 0,13 milimetru, základní síť 0,31. | Titulek a sloupce osy R. Protokol pod číslem: 30 odložených výbojů. Pod grafem je věta, že náměty na úpravy vznikly na všech 149 výbojích. |
| 1:52 | 11 | A | V křížové validaci na 119 výbojích je to 0,23, na novějších číslech výbojů 0,40. | Řádek protokolů pod grafem (119 výbojů, křížová validace; novější čísla). |
| 2:03 | 14 | A | Bod u limiteru: 4,55 milimetru proti 10,6. Proud určí lineární model s chybou 0,035 kiloampéru; síť měla 1,2. | Dlaždice 4,55 mm a 0,035 kA (lineární model). Protokol: 30 odložených výbojů. |
| 2:17 | 12 | B | Samotné cívky stačí na skoro stejnou souhrnnou chybu jako všech 24 vstupů, osm nejlepších už ne. | Graf Kolik vstupů stačí (základní síť, pět dělení po výbojích): 0,066 proti 0,063, osm nejlepších 0,094. Menší číslo je lepší. |

### Živá ukázka, mezi snímkem 4 a 5 (2:29 až 3:49, 80 s)

Hlavní věta: Skutečný a odhadnutý tvar vedle sebe; v ukázce je základní síť, ne vybraný model; jedna typická a jedna špatná ukázka.

Obrázek: žádný, na obrazovce je prohlížeč tvaru (repo/viewer/index.html)

| Čas | Sek. | Kdo | Co se říká | Na obrazovce |
|---|---|---|---|---|
| 2:29 | 13 | A | Teď naživo. Prohlížeč běží bez internetu. Vidíte základní síť, ne vybraný model, který je u osy na odložených výbojích asi dvakrát přesnější. | Cmd+Tab do prohlížeče. Okno je předem otevřené na adrese končící #d=123, rychlost 1×, zastaveno. Dlaždice v prohlížeči musí říkat základní síť. |
| 2:42 | 12 | A | Tmavá čára je skutečný tvar, oranžová odhad sítě. Výboj číslo 123 síť neviděla, nepatří ani mezi odložených třicet. | Ukázat na přepínače Skutečnost a Předpověď. Mezerník spustí přehrávání. Stav dole: validační skupina 1 z 5. |
| 2:54 | 6 | A | (ticho, výboj běží a porota se dívá) | Nech výboj proběhnout dvakrát. |
| 3:00 | 12 | A | Kroužek je osa, křížek bod X. Dole je chyba v čase, v tomto výboji roste na začátku a na konci. | Ukázat na značky a spodní graf. Před vystoupením ověřit, že graf to opravdu ukazuje. |
| 3:12 | 14 | A | Teď záměrně špatný výboj, číslo 0. Rozdíl je vidět, chyba osy je podle prohlížeče [[chyba osy výboje 0]] milimetru. | Výboj 0 z nabídky nebo adresa s #d=0. Číslo doplnit až po přehrání den předem; bez ověřeného čísla řekni jen: Rozdíl mezi čárami je vidět. |
| 3:26 | 5 | A | (ticho, špatný výboj běží) | Ukázat na místo, kde se čáry rozcházejí. |
| 3:31 | 14 | B | Takových výbojů je málo: u základní sítě má chybu osy pod milimetrem 86 procent výbojů, tedy 128 ze 149. | Protokol: základní síť, pět dělení po výbojích (results/ipp1-claim-support.md); jen tři výboje jsou přes 5 mm. |
| 3:45 | 4 | A | (ticho, přepnutí zpět) | Cmd+Tab zpět do prezentace, klik na snímek 5. Dlaždici latence v prohlížeči neukazovat ani neříkat (v prohlížeči je základní síť; číslo zazní na snímku 5). |

### Snímek 5: Rychlost, verdikt pro řízení (3:49 až 4:29, 40 s)

Hlavní věta: Základní síť 0,0145 ms, vybraný model asi 0,03 ms (0,027 u limitovaného plazmatu), obojí pod naším rozpočtem 1 až 10 ms; ověřili jsme jen výpočet samotné sítě.

Obrázek: 02-minutes-vs-ms.png (zopakovat jako pozadí)

| Čas | Sek. | Kdo | Co se říká | Na obrazovce |
|---|---|---|---|---|
| 3:49 | 13 | B | Základní síť: jeden odhad na procesoru Apple M5 trvá 0,0145 milisekundy, devadesát devět procent odhadů je rychlejších než 0,021 milisekundy. | Snímek 5. Velká dlaždice 0,0145 ms, dlaždice 0,0209 ms. Pod nimi: základní síť, procesor Apple M5. |
| 4:02 | 11 | B | Vybraný model má tři části a jeden odhad trvá asi 0,03 milisekundy, u limitovaného plazmatu medián 0,027. | Dlaždice vybraného modelu: 0,027 ms, limitované plazma, Apple M5, vytížený notebook (results/ipp1-latency-shipped.md, numpy, náhodné váhy stejného tvaru, jen čas). |
| 4:13 | 16 | B | Zadání chce jednotky až desítky milisekund, my počítáme s rozpočtem jedné až deseti; obojí je hluboko pod ním. Ověřili jsme jen výpočet sítě, ne sběr signálů ani zašuměné signály. | Věta pod dlaždicemi. Rozpočet 1 až 10 ms je náš, ne ze zadání. Konec snímku, pohled na A, klik na snímek 6. |

### Snímek 6: Meze (4:29 až 5:03, 34 s)

Hlavní věta: Nejhůř bod u limiteru (4,55 a 8,35 mm u vybraného modelu na 30 odložených výbojích); chyba osy roste hlavně na konci výboje.

Obrázek: žádný obrázek, na snímku je graf chyby osy podle času

| Čas | Sek. | Kdo | Co se říká | Na obrazovce |
|---|---|---|---|---|
| 4:29 | 21 | A | Bod u limiteru, nejslabší místo: vybraný model má na třiceti odložených výbojích chybu 4,55 milimetru radiálně a 8,35 svisle, v jednom procentu řádků je chyba přes 77 milimetrů radiálně a přes 92 svisle. | Snímek 6. Dlaždice 4,55 mm a 8,35 mm (vybraný model, 30 odložených výbojů); pod nimi 99 % řádků pod 77,5 a 92,2 mm (results/ipp1-final.md, sloupec p99). Nejhorší řádky mají 357 a 485 mm. |
| 4:50 | 13 | A | Chyba osy roste hlavně na konci výboje: u základní sítě v pěti dělení 0,9 milimetru proti 0,24 uprostřed. | Graf chyby osy podle desetin výboje (základní síť, pět dělení), oranžové sloupce jsou začátek a konec. Kolísání výstupu je jen v poznámce pod čarou. |

### Snímek 7: Co model neumí (5:03 až 6:17, 74 s)

Hlavní věta: Šum zhroutí síť naučenou na čistých datech, potřebuje dost výbojů, neobvyklé tvary jsme samostatně neověřili, jen jeden tokamak.

Obrázek: žádný obrázek, na snímku jsou dva grafy (šum, počet výbojů)

| Čas | Sek. | Kdo | Co se říká | Na obrazovce |
|---|---|---|---|---|
| 5:03 | 16 | B | Největší slabina je šum. Základní síť naučená na čistých datech má chybu osy 0,38 milimetru, na zašuměných datech od organizátorů ale 10,15. | Snímek 7, levý graf, první dva sloupce. Protokol: základní síť, pět dělení po výbojích. |
| 5:19 | 7 | B | Učení se šumem to srazí na 2,64, na čistých datech ale zhorší na 2,22. | Třetí sloupec; číslo 2,22 není na grafu, říkáš ho z paměti. |
| 5:26 | 12 | B | Vybraný model na šumu selže, proto bychom použili síť učenou se šumem: osa 2,38 milimetru na třiceti odložených výbojích. | Řádek pod grafem (30 odložených výbojů; proud 4,65 kA je tam také). |
| 5:38 | 18 | A | Druhá slabina: počet výbojů. Se 30 učícími výboji je chyba osy 1,47, se všemi učícími výboji, 119 v každém dělení, je 0,38, ale s pevným počtem epoch. | Pravý graf, křivka podle počtu učících výbojů (základní síť, pět dělení). |
| 5:56 | 15 | A | Třetí slabina: neobvyklé tvary. Vynechání rodiny tvarů zvedlo chybu nejvýš třikrát, ale opravdu neobvyklých výbojů je jen 18 ze 149 a samostatně jsme je neověřili. | Spodní text snímku. |
| 6:11 | 6 | B | Platí jen pro jeden tokamak. | Spodní text snímku; věta, že řízení plazmatu model sám nenahradí, je jen tam. |

### Snímek 8: Závěr (6:17 až 7:00, 43 s)

Hlavní věta: Přesnost desetiny milimetru na čistých vstupech, rychlost setiny milisekundy, a upřímně co nefunguje.

Obrázek: 07-closing.png

| Čas | Sek. | Kdo | Co se říká | Na obrazovce |
|---|---|---|---|---|
| 6:17 | 10 | A | Přesnost na čistých vstupech: osa 0,13 milimetru na odložených výbojích, asi 0,2 v křížové validaci. | Snímek 8. Obrázek 07-closing.png. Dlaždice Přesnost. |
| 6:27 | 11 | A | Rychlost: základní síť 0,0145 milisekundy, vybraný model asi 0,03, obojí hluboko pod rozpočtem. | Velké číslo 0,0145 ms vlevo a vedle něj vybraný model (0,027 ms). Pomalu. |
| 6:38 | 17 | B | Na zašuměných vstupech je osa na jednotky milimetrů, bod u limiteru na desítky, proud 4,65 kiloampéru. Pro řízení model ještě není: nezná neobvyklé tvary a šum mu vadí. | Dlaždice Přesnost (druhý řádek) a Zbývá. Zašuměné vstupy: osa 2,38 mm, bod u limiteru 25,8 a 38,9 mm, proud 4,65 kA (30 odložených výbojů, síť učená se šumem). |
| 6:55 | 5 | A+B | Desetiny milimetru za setiny milisekundy. Děkujeme. | Oba se dívají na porotu. Konec v 7:00. Věta Zbývá napojení na řídicí systém je na dlaždici Zbývá. |

## Pravidla řeči

* Číslo řekni jednou, pomalu, a nech ho doznít. V jedné větě nejvýš dvě čísla. Pod každým číslem přesnosti řekni, na jakých výbojích bylo změřeno (odložených 30, křížová validace, pět dělení po výbojích). Číslo bez protokolu neříkej.
* Slova zamčená, nikdo neviděl a před finálním výběrem neříkej (porota z nich slyší výboje mimo návrh). Říkej odložené výboje, odložené před posledním výběrem modelu, a hned větu, že náměty na úpravy modelu vznikly na všech 149 výbojích (řádek 1:37, otázka N2).
* Slova základní síť a vybraný model nikdy nezaměňuj. Rychlost 0,0145 milisekundy patří základní síti, nikdy vybranému modelu. Vybraný model má asi 0,03 milisekundy, u limitovaného plazmatu medián 0,027, u divertorového 0,015.
* Rozpočet jedné až deseti milisekund je náš; zadání chce jednotky až desítky milisekund. Neříkej, že rozpočet dalo zadání.
* Nečti text ze snímku. Dívej se na porotu, na obrazovku jen ukaž.
* Před začátkem: prohlížeč otevřený na výboji 123, rychlost 1×, zastaveno; druhá záložka nebo adresa s #d=0 připravená; hlasitost a zrcadlení obrazovky vyzkoušené. Den předem přehrát výboje 123 a 0 a zapsat sem čísla, která prohlížeč ukazuje (viz Záloha ukázky).
* Kontrolní časy: 0:38 snímek 2, 1:06 snímek 3, 1:26 snímek 4, 2:29 ukázka, 3:49 snímek 5, 4:29 snímek 6, 5:03 snímek 7, 6:17 snímek 8, 7:00 konec.
* Neznáš odpověď? Řekni: Tohle jsme neměřili. A pokračuj tím, co jsme měřili. Nikdy nehádej číslo.

## Záloha, když ukázka selže

* Po první větě ukázky (2:29) řekni: Ukázka se nespustila, ukážu uložené obrázky. Pak ukaž tři obrázky z tlačítka Uložit PNG (začátek, střed a konec výboje 123) a řádky ukázky o osách a tabulce. Zkrať to na 45 sekund a zbytek času dorovnej tím, že vynecháš řádky se špatným výbojem. Skrytý snímek 10 se z prezentace otevře klávesou H (nebo napsat 10 a Enter); klávesa H funguje jen v PowerPointu, protože skrytý snímek 10 následuje hned po snímku 9. V Keynote ani v Google Slides klávesa H není: tam před vystoupením odkrýt snímek 10 nebo mít záložní kopii s odkrytým snímkem a vyzkoušet, jak se na něj přejde.
* DOPLNIT: nahrát 60 sekund záznamu obrazovky z prohlížeče (výboj 123 a výboj 4 s přepínačem šumu) a uložit vedle prezentace; zkopírovat prohlížeč `viewer/dist/index.html` na druhý notebook. Zatím neexistuje.
* Den před vystoupením: přehrát výboje 123 a 0 a zapsat, co prohlížeč ukazuje (počet snímků, chyba osy na konci výboje). Dřívější poznámky o 219 snímcích a o chybě 5,7 mm výboje 0 nejdou z repozitáře ověřit (prohlížeč ukazuje jen 146 snímků, každý druhý řádek) a nepoužívají se.

## Záloha: kamera (skrytý snímek 5 v decku)

Nepoužívá se, pokud před vystoupením nezbývá mezera aspoň 20 sekund. V časovém plánu nemá vteřiny. Pokud se použije, řekne ji B:

| Čas | Sek. | Kdo | Co se říká | Na obrazovce |
|---|---|---|---|---|
| záloha | 20 | B | Bonus: malá kamerová síť na snímcích 48 na 64 bodů, naučená na 78 výbojích, je 1,3 až 13krát horší než cívky; osa 1,79 milimetru proti 0,38, orientačně. Barva nepomáhá. Říká to něco o této malé síti, ne o kameře. | Skrytý snímek 5. Pět dělení po výbojích. |

## Verze na 30 sekund

Řídicí systém tokamaku potřebuje znát tvar plazmatu v milisekundách, klasický výpočet ale trvá minuty. Naučili jsme malou neuronovou síť, která tvar odhadne ze 24 magnetických měření. Na 30 odložených výbojích má osa chybu 0,13 milimetru, jeden odhad trvá setiny milisekundy. Slabé je šum, bod u limiteru a jediný tokamak.

Slov: 49, s čísly počítanými dvakrát 52. Přibližně 30 sekund (odhad podle počtu slov, ne stopky).

## Verze na 60 sekund (výtah)

Když se plazma dotkne stěny, poškodí ji. Řídicí systém proto potřebuje tvar plazmatu v milisekundách, klasický výpočet trvá minuty. Naučili jsme malou neuronovou síť odhadnout tvar ze 24 magnetických měření na 149 výbojích. Na 30 výbojích odložených před posledním výběrem modelu má vybraný model chybu osy 0,13 milimetru, základní síť 0,31; náměty na úpravy ale vznikly na všech 149 výbojích. Jeden odhad základní sítě trvá 0,0145 milisekundy na procesoru Apple M5, vybraný model asi 0,03. Nejsme hotovi: bod u limiteru má chybu 4,55 milimetru, na zašuměných vstupech je osa 2,38 a neobvyklé tvary jsme samostatně neověřili. Data jsou jen z jednoho tokamaku.

Slov: 102, s čísly počítanými dvakrát 113. Přibližně 60 sekund (odhad podle počtu slov, ne stopky).

## Deset zlých otázek a upřímné odpovědi

Každá odpověď říká i mez a u čísla protokol. Poznámky k zdrojům a k tomu, co ještě chybí, jsou v části Lead notes. Odpovědi 4, 5, 6 a 8 byly po kontrole Kritika 2 přepsány, protože původní znění už neplatilo (tvrdilo, že vybraný model nepoužívá lineární model pro proud, že se architektura neladila podle testu, že silnější modely se teprve zkoušejí a že rychlost 0,0145 milisekundy patří vybranému modelu). Po kontrole Kritika 3 se opravily ještě 5 (rozptyl mezi dělením 0,12 v žádném souboru není, použit je rozptyl semen), 6 (zkoušeli jsme stromy), 8 a N5 (změřená rychlost) a 9 (věta o COMPASS Upgrade nemá zdroj v repozitáři) a 10 (náhradní věta bez čísla).

### 1. Fyzik
Otázka: Čemu říkáte pravda? Porovnáváte se skutečným plazmatem, nebo s výpočtem?

Odpovídá A: Porovnáváme se správnými odpověďmi, které dodal ústav. Podle zadání vznikají numerickou rekonstrukcí rovnováhy, takže se síť učí tuto rekonstrukci napodobit. Chyba 0,13 milimetru na odložených výbojích je tedy chyba proti ní, ne proti skutečnému plazmatu. Jak přesné jsou správné odpovědi samy o sobě, jsme neměřili.

### 2. Fyzik
Otázka: Co když plazma bude mít nový tvar, který v datech nebyl?

Odpovídá A: Nevíme. Když jsme při učení vynechali celou rodinu tvarů, byla chyba osy 1,0 až 3,0krát větší, obvykle 1,2 až 2,4krát, bez zhroucení, u základní sítě v pětinásobném dělení. Opravdu neobvyklých výbojů je ale jen 18 ze 149 a samostatně jsme je nikdy nevynechali, takže o tvarech mimo rozsah dat ten výsledek nic neříká. V datech leží protažení a trojúhelníkovost na jedné úzké křivce, tedy na jedné rodině tvarů. Pro tvar mimo ni jí věřit nelze.

### 3. Fyzik
Otázka: Síť se na šumu zhroutí. Dá se to vůbec použít se skutečnými čidly?

Odpovídá A: Síť naučená na čistých datech na šum nestačí: chyba osy vyskočí z 0,38 na 10,15 milimetru, u základní sítě v pěti dělení po výbojích. Při učení na zašuměných datech je to 2,64 milimetru, ale na čistých datech pak 2,22. Vybraný model naučený na čistých datech na šumu selže úplně, proto bychom pro zašuměné vstupy použili síť učenou se šumem: na odložených výbojích má osu 2,38 milimetru. Soubor se šumem od organizátorů obsahuje jen bílý šum a žádný měřitelný posun, šum má asi 16 procent rozptylu signálu u cívek a 9 procent u smyček toku. Posun v čase jsme zkoušeli jen na vlastních, uměle vytvořených datech. Zda šum v souboru odpovídá skutečným čidlům, nevíme. Použitelné je to jen s učením na šumu a s ověřením na zařízení.

### 4. Odborník na strojové učení
Otázka: Proč u proudu plazmatem vychází lineární model lépe než vaše síť?

Odpovídá A: Je to tak a vybraný model to využívá: pro proud používá lineární model. Na odložených výbojích má chybu 0,035 kiloampéru, základní síť 1,2. Proud je téměř přesně lineární funkce 24 vstupů, proto lineární model stačí; není to úspěch sítě a nepočítáme to do tvrzení, že je vybraný model lepší. Na zašuměných vstupech je chyba proudu 4,0 až 4,7 kiloampéru podle modelu, obě učené se šumem.

### 5. Odborník na strojové učení
Otázka: Je validace poctivá? Jen 149 výbojů, jedno náhodné nastavení, žádný interval spolehlivosti.

Odpovídá A: Dělíme po celých výbojích. Základní síť ověřujeme pětkrát jinak, u osy je střední chyba 0,38 milimetru. Vybraný model jsme navrhovali na křížové validaci přes všech 149 výbojů, takže odložených 30 bylo při návrhu v testovacích částech; po odložení se nic neladilo, jen jsme vybrali jednu ze čtyř variant uvnitř 119 výbojů. Odložené výboje vycházejí lépe než vývojová křížová validace, 0,13 proti 0,23 milimetru, proto uvádíme obě čísla. Bootstrapový interval odložené osy je 0,10 až 0,18 milimetru. Pro hlavní srovnání jsme udělali pět semen: osa R vychází 0,133 milimetru se směrodatnou odchylkou 0,006 u vybraného modelu a 0,289 s odchylkou 0,011 u základní sítě; vybraný model je lepší v pěti z pěti u všech sedmi veličin.

### 6. Odborník na strojové učení
Otázka: Proč jen jedna síť? Zkoušeli jste stromy nebo jiné architektury?

Odpovídá B: Zkoušeli jsme víc: širší a hlubší sítě, jinou ztrátovou funkci, rozdíly sousedních cívek, soubory tří sítí i stromy pro bod u limiteru. Nejvíc pomohla zvláštní síť pro bod u limiteru a lineární model pro proud; chyba bodu u limiteru klesla na polovinu, 4,55 proti 10,6 milimetru na odložených výbojích. Stromy byly horší než zvláštní síť. Zlepšení platí v pěti z pěti semen, u bodu X radiálně je jen o něco lepší. Kromě sítí jsme zkoušeli jen stromy pro bod u limiteru. Nemáme zvláštní ověřovací část, proto rozdíly pod 10 až 15 procent považujeme za šum.

### 7. Fyzik
Otázka: Chyba 0,13 milimetru zní skvěle, ale hodnoty se skoro nehýbou. Co to znamená?

Odpovídá A: Správně, ale jen u osy, bodu X a dotykových bodů: jejich rozptyl je od 2,4 do 13,7 milimetru. U bodu limiteru je 90 a 153 milimetru a u proudu plazmatem 114 kiloampérů. Proto uvádíme chyby v milimetrech i vztažené k rozptylu: u osy je to 0,139 u základní sítě a 0,68 u lineárního modelu, v pěti dělení po výbojích.

### 8. Podnikatel
Otázka: Co to znamená v praxi? Dá se to nasadit do řízení?

Odpovídá B: Zatím ne. Změřili jsme jen samotný odhad na jednom jádru procesoru Apple M5, na vytíženém notebooku: základní síť 0,0145 milisekundy, vybraný model 0,027 u limitovaného plazmatu a 0,015 u divertorového. Zadání chce jednotky až desítky milisekund, my počítáme s rozpočtem jedné až deseti a obojí je hluboko pod ním. Na systému bez reálného času se ojediněle objeví špičky až do milisekund. Mezi dvěma řádky dat uplyne asi 0,6 milisekundy, to je orientační údaj. Sběr signálů, napojení na řídicí systém, nejhorší dobu a skutečně zašuměné signály jsme nezkoušeli. Navíc jsou to dva různé modely, pro čisté a pro zašuměné vstupy, a přepínání mezi nimi jsme netestovali. Bez toho bych to do řízení nedal.

### 9. Podnikatel
Otázka: Komu to pomůže a co dál? Dá se to použít na COMPASS Upgrade?

Odpovídá B: Náš model je naučený jen na COMPASSu a na jiném zařízení by se musel učit znovu. U základní sítě je s 30 učícími výboji chyba osy 1,47 milimetru; kolik výbojů potřebuje nový stroj, nevíme.

### 10. Podnikatel
Otázka: Proč věřit modelu, který neříká, jak si je jistý? Co když se plete?

Odpovídá B: Síť sama vydá jen číslo. Zkusili jsme pět sítí s různým náhodným začátkem, základní síť v pěti dělení po výbojích: na deseti procentech řádků, kde se nejvíc rozcházejí, je chyba 8krát větší než na zbytku a ty řádky nesou 47 procent celé chyby. Je to použitelné varování, ne pravděpodobnost chyby, a netestovali jsme ho na neobvyklých tvarech ani na zašuměném vstupu. Slabá místa známe: bod u limiteru, začátek a konec výboje a šum. V prohlížeči jste viděli špatný výboj, rozdíl mezi čárami byl vidět. (Číslo říkej jen po ověření: chyba osy [[chyba osy výboje 0]] milimetru. Bez ověřeného čísla neříkej žádné.)

## Příloha: dalších třináct otázek od Kritika 2

Kritik 2 sepsal třináct nových otázek; prvních deset je hlavní sada, N11 až N13 jsou krátké doplňky. Číslo N odpovídá pořadí v `docs/review-findings-2.md` (část Ten new hostile questions).

### N1. Fyzik
Otázka: Vaše nejlepší číslo je pro signály bez šumu. Skutečné sondy šum mají. Jak přesní jste na nich?

Odpovídá A: Na souboru se šumem od organizátorů dává model, který bychom použili, učený se šumem a posunem, na 30 odložených výbojích osu 2,38 milimetru, bod u limiteru 25,8 a 38,9 milimetru a proud 4,65 kiloampéru. Vybraný model naučený na čistých datech tam selže (osa 190 milimetrů). Zda šum v souboru odpovídá skutečným čidlům, nevíme: je bílý, asi 16 procent rozptylu signálu u cívek.

### N2. Odborník na strojové učení
Otázka: Navrhovali jste model s pohledem na testovací výboje?

Odpovídá A: Částečně. Třicet odložených výbojů jsme vylosovali po návrhu receptu, ale návrhové pokusy běžely na křížové validaci přes všech 149 výbojů, takže těch 30 bylo při návrhu v testovacích částech. Na odložených 30 se pak nic nepřeučovalo; jen poslední volba ze čtyř variant se udělala uvnitř 119 vývojových výbojů. Odložené výboje vycházejí lépe než vývojové, osa 0,133 proti 0,230 milimetru, proto uvádíme obě čísla.

### N3. Odborník na strojové učení
Otázka: Je odložená sada reprezentativní?

Odpovídá A: Ne zcela. Jen 2 z 30 výbojů, tedy 591 z 8 761 řádků, 6,7 procenta, mají opačný směr proudu, a na nich je chyba osy u vybraného modelu 0,454 milimetru, čtyřikrát víc než na zbytku. Bootstrapový interval chyby osy je 0,10 až 0,18 milimetru. Je to málo, abychom řekli něco spolehlivého o opačné polaritě.

### N4. Odborník na strojové učení
Otázka: Vylepšený model, kolik z toho je skutečné?

Odpovídá A: Pět semen: vybraný model je lepší v pěti z pěti u všech sedmi veličin, zisk u osy, dotykového bodu a bodu u limiteru je 42 až 60 procent. U bodu X radiálně je zisk jen 21 procent, nejbližší semeno 0,96, říkáme jen o něco lepší. Střední kvadratická chyba bodu X radiálně a druhého dotykového bodu je horší (0,454 proti 0,305 a 0,638 proti 0,401 milimetru) a nejhorší jednotlivý řádek šesti veličin je větší.

### N5. Fyzik
Otázka: Jakou rychlost uvádíte, tu vybraného modelu?

Odpovídá B: Číslo 0,0145 milisekundy patří základní síti. Vybraný model trvá 0,027 milisekundy u limitovaného plazmatu a 0,015 u divertorového, asi dvakrát víc než základní síť. Dřívější odhad 0,18 se při měření na stejném postupu nepotvrdil. Obojí je hluboko pod naším rozpočtem jedné až deseti milisekund; ani jedno nezahrnuje sběr dat.

### N6. Fyzik
Otázka: Pro řízení rozhodují náhlé zániky a start výboje. Jak jste tam dobří?

Odpovídá A: Nejhůř na koncích. V posledních 2 procentech výboje je u vybraného modelu na odložených výbojích radiální chyba osy 0,578 milimetru proti 0,114 uprostřed, svislá 1,33 proti 0,14; v prvních 2 procentech 0,538. V křížové validaci základní sítě nesou poslední 2 procenta řádků 27 procent chyby radiální osy. Náhlé zániky jako takové nejsou v datech ani v našich zkouškách.

### N7. Odborník na strojové učení
Otázka: Model, který musí vědět, zda jsou vstupy zašuměné, není model. Co dodáte?

Odpovídá A: Dva modely: vybraný pro čisté vstupy a síť učenou se šumem pro zašuměné. Jeden vítěz neexistuje: modely učené se šumem jsou na čistých datech horší, osa 1,56 proti 0,307 milimetru u základní sítě. Přepínání podle druhu vstupu je předpoklad nasazení, který jsme netestovali.

### N8. Fyzik
Otázka: Šum je nezávislý v každém řádku a řádky jsou od sebe 0,6 milisekundy. Proč nezprůměrovat několik vzorků?

Odpovídá A: Zkusili jsme tři po sobě jdoucí řádky: na zašuměných vstupech klesla chyba osy z 2,64 na 2,33 milimetru, na čistých vstupech byla horší, z 0,38 na 0,57. Delší okna jsme nezkoušeli; odstup 0,6 milisekundy je orientační.

### N9. Fyzik
Otázka: Přežije se výpadek cívky?

Odpovídá A: Netestovali jsme. Jediný důkaz: samotných 16 cívek dává souhrnnou chybu 0,066 proti 0,063 se všemi 24 vstupy, samotných 8 smyček toku 0,285, vše u základní sítě v pěti dělení po výbojích. Pořadí vstupů není stabilní (shoda tří způsobů je od minus 0,14 do 0,40), proto žádné jedno čidlo nepojmenováváme; cívka IPR13 přežila vyřazování ve všech pěti dělení.

### N10. Odborník na strojové učení
Otázka: Kamerový model je špatný. Je kamera k ničemu?

Odpovídá A: Je to malá síť na snímcích 48 na 64 bodů, 12 epoch, každý osmý snímek, 78 ze 149 výbojů. Je 1,3 až 13krát horší než cívky a při spojení s cívkami nic nepřidá (1,21 proti 0,24 milimetru na dvou dělení). To ukazuje, že tato síť obrazy dobře nevyužívá, ne že kamera nenese informaci.

### N11. Fyzik
Otázka: Zadání mluví o 17 parametrech, vy uvádíte 16.

Odpovídá B: Předpovídáme 16 hlavních sloupců z 31 v souboru; ostatní jsou doplňkové a nepředpovídali jsme je.

### N12. Odborník na strojové učení
Otázka: A jak si model vede na nejnovějších výbojích?

Odpovídá A: Čísla výbojů zřejmě sledují čas, což jsme s organizátory neověřili. Když učíme na 60 nejnižších číslech a testujeme na 59 nejvyšších, je chyba osy vybraného modelu 0,397 milimetru (při náhodném dělení 0,216), základní sítě 1,23 (0,448). Část rozdílu vysvětluje menší učící sada.

### N13. Podnikatel
Otázka: Proč věřit přesnosti 99,3 procenta pro limitované a divertorové plazma?

Odpovídá B: Základní síť má 0,993 v pěti dělení, vybraný model 0,9916 a základní síť 0,9892 na odložených výbojích. Chyby jsou posuny o pár řádků na přechodu a rozložené rovnoměrně mezi obě konfigurace.

## Lead notes (English, for the team, not spoken)

### Words and seconds per section

| Section | Start | End | Seconds | Words (space split) | Words, numerals counted twice | Words, numbers written out | Silent seconds | Rate (numerals twice) | Rate (written out) |
|---|---|---|---|---|---|---|---|---|---|
| Snímek 1: Problém | 0:00 | 0:38 | 38 | 63 | 65 | 67 | 0 | 1.71 | 1.76 |
| Snímek 2: Data | 0:38 | 1:06 | 28 | 43 | 48 | 49 | 0 | 1.71 | 1.75 |
| Snímek 3: Metoda | 1:06 | 1:26 | 20 | 29 | 31 | 33 | 0 | 1.55 | 1.65 |
| Snímek 4: Výsledky | 1:26 | 2:29 | 63 | 88 | 99 | 114 | 0 | 1.57 | 1.81 |
| Živá ukázka, mezi snímkem 4 a 5 | 2:29 | 3:49 | 80 | 98 | 105 | 108 | 15 | 1.62 | 1.66 |
| Snímek 5: Rychlost, verdikt pro řízení | 3:49 | 4:29 | 40 | 66 | 71 | 82 | 0 | 1.77 | 2.05 |
| Snímek 6: Meze | 4:29 | 5:03 | 34 | 51 | 57 | 64 | 0 | 1.68 | 1.88 |
| Snímek 7: Co model neumí | 5:03 | 6:17 | 74 | 112 | 123 | 136 | 0 | 1.66 | 1.84 |
| Snímek 8: Závěr | 6:17 | 7:00 | 43 | 62 | 67 | 77 | 0 | 1.56 | 1.79 |
| Total | 0:00 | 7:00 | 420 | 612 | 666 | 730 | 15 | 1.64 | 1.80 |

Counting (script `analysis`-free, a small parser of the same five-column rows that `build_deck.py` reads, silent "ticho" rows left out): words split on spaces; a token with a digit counts twice; "numbers written out" counts the Czech words a speaker really says (rough rule: "0,0145" is 6 words, "4,55" is 4, "119" is 2). The jury hears every digit, so the last column is the honest planning figure. Review 3 (part 5) gave the same method and 630 / 683 / about 733 for the version before this fix.

Time estimate from the written-out count (730 words, 405 s of speech plus 15 s of silence in the demo): at 1.6 words per second 7:51, at 1.7 words per second 7:24, at 1.8 words per second 7:01. **So the script still fits 7:00 only at the fast end; at a normal pace it is about 25 s over.** The fixes of review 3 added words (the 8 words of H2, the budget sentence, the noisy limiter and current, the 119 clarification) and removed about as many (the three cuts of review 3, the shorter 5:19 row, the speed sentence and the "Typický výboj sedí" sentence in the demo); the net change is about zero. Section rates above 1.85 words per second (written out) are slide 5 (2.05, the tightest), slide 6 (1.88), slide 7 (1.84), slide 4 (1.81). This is an estimate; no stopwatch reading exists (M7): read the whole script aloud once and write the real times into `rehearsal-notes.md`.

If the stopwatch says over, cut in this order (written-out words saved, from the table above): 0:38 row "téměř 43 tisíc okamžiků" (about 2), the 4:13 sentence "Zadání chce jednotky až desítky milisekund" (about 8, keep "rozpočet jedné až deseti" and say it is ours), the p99 clause in 3:49 "devadesát devět procent odhadů je rychlejších než 0,021 milisekundy" (about 11, the tile keeps it), the 5:19 row on 2,22 (about 13, the number stays in N7 and Q3), camera (hidden, no seconds). Do not cut the caveat lines 4:13 (second sentence), 5:26 and 6:38.

### What changed, finding by finding

| Finding | Fix in this file |
|---|---|
| H1 shipped model, speed and demo | Two latencies, always named: basic network 0,0145 ms (Apple M5), selected model about 0,03 ms, median 0,027 ms limited and 0,015 ms diverted (`results/ipp1-latency-shipped.md`, review 3 X1; the old 0,18 ms is gone). The slogan stays "desetiny milimetru za setiny milisekundy" (review 3 X1; the review 2 change to "desetiny" is withdrawn). The demo no longer says the viewer latency (row 3:08 cut); before the demo the speaker says the viewer shows the basic network. The viewer tile must say "základní síť" (lane U, not edited here). |
| H2 favourable protocol, "nikdo neviděl" | Slide 4 gives three protocols (30 set aside 0,13; cross-validation on 119 0,23; newer ids 0,40). "Zamčené" and "nikdo neviděl" are gone. Review 3: the spoken line 1:33 said "před finálním výběrem" and the audience hears "held out from design"; now it says "před posledním výběrem modelu; náměty na úpravy ale vznikly na všech 149". Design on all 149 discharges is also answered in N2. |
| H3 script against screen, slides 4 to 7 | Rows rewritten to the numbers on the screen: 0,133 / 0,307, 4,55 / 10,6, 0,035 / 1,2 (slide 4); two speeds (slide 5); 4,55 and 8,35, chart marked as basic network (slide 6; review 3: 77,5 and 92,2 are the p99 of `ipp1-final.md` (rows 128 and 129), so the clause says "v jednom procentu řádků je chyba přes 77 a přes 92", not "až 78 a 92", which read as a maximum; the worst rows are 357 and 485 mm and stay on the screen); learning-curve wording of `claims-corrections.md` section 10 (slide 7). "Cívky nesou skoro všechno", "rychlost nebude překážkou", 0,029, 0,24 ms and 0,032 ms are removed. |
| H4 slide 13 against the speaker | One sentence for both: leaving out a family raised the error at most threefold; the 18 really unusual discharges were never held out alone. |
| H5 noise-free headline | Slide 7 gives the noisy value (axis 2,38 mm, `base_aug`, 30 set aside) and the close (6:38, review 3) says axis units of millimetres, limiter point tens of millimetres, plasma current 4,65 kA, all on noisy inputs (`base_aug`, 30 set aside: 2,38, 25,8 and 38,9 mm, 4,65 kA); 4,03 kA (ridge of `cand_aug`) was not run as one recipe and is not spoken. |
| M1 current tile | Spoken as "lineární model; síť měla 1,2"; not counted as a gain of the network. |
| M2 camera | Hidden backup, no seconds, 20 s line, title 1,3 až 13krát, "malá síť" wording. |
| M3 labelled noise numbers | Protocol said with every number; the 2,33 bar is not spoken and is deleted from the slide (deck-fixes). |
| M4 stale answers | Q4, Q5, Q6, Q8 rewritten, plus Q2, Q3, Q7, Q10 refreshed; N2, N4, N7 give the sources. Review 3: Q5 uses the seed spread of `ipp1-final-seeds.md` (0,133 SD 0,006 and 0,289 SD 0,011) instead of "0,12" (in no file); Q6 says trees were tried for the limiter point (`ipp1-improve.md:37-40`) and the noise line is "10 až 15 procent" (`ipp1-inputs-controls.md`); Q8 and N5 give the measured speed; Q9 lost the COMPASS Upgrade sentence (no source in the repository). |
| M5 demo facts | Frame count and "5,7 mm" removed; the discharge 0 number is `[[chyba osy výboje 0]]` until replayed; 3:00 now says what the chart shows for one discharge (still unchecked, to be verified in the rehearsal); Q10 has the same fallback as 3:12 (review 3). 128 of 149 (85,9 percent) is verified in `results/ipp1-claim-support.md`. |
| M6 demo single point of failure | Backup section now says: key H opens the hidden slide and works in PowerPoint only (review 3), record the 60 s clip, copy the viewer to the second laptop. Still to do by a person. |
| M7 nobody read it aloud | Recounted after review 3 (table above): written-out count 730 words, 7:24 at a normal pace, 7:01 only at 1.8 words per second. Cut already: demo speed sentence, "Typický výboj sedí", "Zbývá napojení", "U každého čísla řeknu". Emergency cuts in the section above. GPU and second computer lines are gone. No stopwatch reading yet. |
| X1 stale latency lines (review 3) | 4:02, 6:27, the main sentence of slide 5, Q8, N5, Lead notes: measured numbers; slogan "setiny"; the 30 s version says "setiny milisekundy". `[[odezva vybraného modelu]]` is gone from this file. |
| X3 two meanings of 119 | 5:38 says "se všemi učícími výboji, 119 v každém dělení"; the file header explains both meanings. |
| X4 budget attribution | 4:13 and Q8 say "zadání chce jednotky až desítky milisekund, my počítáme s rozpočtem jedné až deseti"; the speech rules say the budget is ours. |
| L1 jitter | Not spoken any more; the footnote on slide 12 keeps "0,96 až 1,07 (13 veličin), na čistých vstupech" and "1,7 a 1,65krát". |
| L4 jargon | "zamčených" gone; "p99" is said as "devadesát devět procent odhadů je rychlejších"; "vybraný model" is explained on slide 3. |
| L5 how many inputs | "Samotné cívky stačí na skoro stejnou souhrnnou chybu, osm nejlepších už ne." |

### Numbers used and where they come from

| Number in the script | Value | Source |
|---|---|---|
| Discharge length | 150 to 200 ms | organizers (Data-Brief), not measured by us |
| Rows, discharges, inputs, targets | 42 972, 149, 24, 16 of 31 | `results/ipp1-data.md` |
| Network size | 107 152 parameters | `results/ipp1-latency.md` |
| Set aside 30 discharges, selected model against basic network | axis R 0,133 / 0,307; Z 0,172 / 0,321; limiter 4,55 / 10,6 and 8,35 / 22,5; plasma current 0,0347 / 1,20; p99 limiter 77,5 and 92,2 | `results/ipp1-final.md` |
| Bootstrap interval of axis R (selected model, 30 set aside) | 0,099 to 0,177 | `results/ipp1-final.md` |
| Cross-validation on 119, selected model | axis R 0,230 | `results/ipp1-final.md`, development table |
| Newer ids (train 60 lowest, test 59 highest) | axis R 0,397 (selected), 1,23 against 0,448 on random folds (basic) | `results/ipp1-final.md`, "Random group folds are optimistic" |
| Basic network, 5 folds | axis R 0,377, Z 0,391; nRMSE 0,139 and 0,68; linear 2,4 mm; plasma current 1,49 against 0,0346 kA | `results/ipp1-baseline.md` |
| Inputs | 24: 0,063; top 8: 0,094; coils only 0,066; loops only 0,285 | `results/ipp1-inputs.md` |
| Latency, basic network, Apple M5 | median 0,0145; p99 0,0209 ms | `results/ipp1-latency.md` (machine was shared and busy) |
| Latency, selected model, Apple M5, one CPU core, busy laptop (load 6,4 to 7,2) | numpy path from the 24 raw inputs: median 0,0154 ms diverted and 0,0274 ms limited, p99 0,057 and 0,093 ms; torch `predict()` 0,026 and 0,054 ms | `results/ipp1-latency-shipped.md` (random weights of the trained shapes, timing only; the 0,1775 ms of `ipp1-improve.md` was not reproduced) |
| Timing budget | assignment: units to tens of ms; our budget 1 to 10 ms (team verdict, not in the assignment) | `results/ipp1-latency.md:3`, `docs/REQUIREMENTS.md` REQ-002 |
| Seed spread, R axis, 30 set aside, 5 seeds | selected 0,133 (SD 0,006); basic network 0,289 (SD 0,011); better in 5 of 5 | `results/ipp1-final-seeds.md` |
| Basic network, error end against middle | 0,9 against 0,24 mm | `results/ipp1-time.md` |
| Jitter (footnote only) | 0,96 to 1,07 clean (13 targets); 8,4 and 3,3 noisy; 1,7 and 1,65 after training with noise | `results/ipp1-time.md`, `claims-corrections.md` section 2 |
| Noise, basic network, 5 folds | 0,38 clean; 10,15 on noisy; 2,64 trained with noise; 2,22 clean after training with noise; 2,33 with three rows (not spoken) | `results/ipp1-robustness-findings.md` |
| Noisy inputs, 30 set aside, `base_aug` | axis 2,38; limiter 25,8 and 38,9; current 4,65 kA (4,03 kA ridge of `cand_aug`); `cand` plain: axis 190 | `results/ipp1-final.md` |
| 27 times, 18 times | 10,15 / 0,38 = 26,7 (dropped from the speech); 2,38 / 0,133 = 17,9 (dropped from the speech) | derived; kept for the Q and A |
| Learning curve | 30 discharges 1,47; 119 discharges 0,38 | `results/ipp1-robustness-findings.md` |
| Unusual shapes | factor 1,0 to 3,0 (typically 1,2 to 2,4); 18 of 149 really unusual | `results/ipp1-unusual-shapes.md` |
| Discharges below 1 mm / above 5 mm | 128 of 149 (85,9 percent) / 3 | `results/ipp1-claim-support.md` |
| Uncertainty | 10 percent most uncertain rows: 8,1 times the error, 47 percent of it | `results/ipp1-uncertainty.md` |
| Polarity, ends | 2 of 30 reversed (591 rows), axis R 0,454; last 2 percent axis R 0,578 against 0,114 in the middle, Z 1,33 against 0,14 | `results/ipp1-final.md` |
| Noise structure | white, no drift; SD over signal 0,158 (coils), 0,090 (loops) | `results/ipp1-data-checks.md` |
| Spreads | 2,4 to 13,7 mm; limiter 89,6 and 153,3 mm; current 114,2 kA | `results/ipp1-data-checks.md` |
| Camera | 5 folds, 78 discharges, 48x64; axis R 1,79 (grey 1,70) against 0,377; 1,3 to 13 times; fused 1,21 against 0,24 on 2 folds | `results/cloud-camera-main.md`, `results/cloud-camera-findings.md`, `results/ipp1-camera-local-findings.md` |

The demo discharges 0, 4, 11 and 123 are not among the 30 set aside (`results/ipp1-locked-test-ids.txt`).

### Still pending (needs a person or a machine)

* Latency of the selected model: done (`results/ipp1-latency-shipped.md`, busy laptop, random weights, numpy). Caveats a physicist can raise, not closed: no file checks that the numpy path reproduces the trained network (a 100-row comparison with `predict()` would close it); the noise-trained network needed for noisy inputs was not timed (it has the size of the basic network); the machine was not idle. `[[odezva vybraného modelu]]` is reserved and unused.
* `[[chyba osy výboje 0]]` and the sentence "v tomto výboji roste na začátku a na konci": replay discharges 123 and 0 in the viewer, write down the numbers the viewer shows.
* One timed read-aloud with a stopwatch; update `rehearsal-notes.md`.
* The 60 s screen recording and the copy of the viewer on the second laptop (M6).
* `build_deck.py` has hard-coded split times for speaker notes (`0:21`, `1:37`, `2:14`); with the timing of this file the last two become `1:33` and `2:17`, see `docs/deck-fixes.md` item 0.3 and the section For lane K.
* Any change of the shipped recipe after 21:30 Friday invalidates the 0,13 and 0,23 numbers.
