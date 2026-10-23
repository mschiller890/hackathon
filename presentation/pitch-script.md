---
tags:
  - hackathon
---

# Pitch: 7 minut pro porotu

Stav: přepsáno v pátek 23. října večer podle `docs/review-findings-2.md` (Kritik 2) a `docs/claims-corrections.md`, potom opraveno podle `docs/review-findings-3.md` (Kritik 3) a naposledy podle `docs/review-physics.md` (fyzik, větev `cloud/pitch-fix-3`): každé číslo přesnosti je shoda s rekonstrukcí ústavu, ne přesnost polohy skutečného plazmatu. Každá mluvená věta souhlasí se souborem v `results/` a s obrazovkou po úpravách z `docs/deck-fixes.md`. Pod každým číslem přesnosti říkáme, na jakých výbojích bylo změřeno. Čas vybraného modelu je změřený (`results/ipp1-latency-shipped.md`). Na přehrání čeká jen `0,22 milimetru` (číslo z prohlížeče den předem; bez něj se říká věta bez čísla). Název `[[odezva vybraného modelu]]` je rezervovaný pro číslo, které by čekalo na další soubor; teď se nepoužívá. Pořadí snímků sedí s `repo/presentation/outline.md`; co má změnit sazeč decku, je v `docs/deck-fixes.md`. Formát tabulek se nesmí měnit, čte ho `deck/build_deck.py` (nadpisy `### Snímek N`, řádek `Hlavní věta:` a řádky `| m:ss | sek. | kdo | text | obrazovka |`).

## Jak je to postavené

* Začátek: problém, který bolí. Protažené plazma je svisle nestabilní a řízení musí znát polohu a tvar v milisekundách; úplná rekonstrukce rovnováhy trvá minuty. Dotek stěny není strašák: 44,2 procenta řádků v datech je limitovaných.
* Jádro: živá ukázka v prohlížeči. V ukázce je vybraný model na 30 odložených výbojích; obrys je z rekonstrukce ústavu, síť odhaduje jen označené body, a to říkáme nahlas před ukázkou.
* Konec: dvě rychlosti (základní síť, vybraný model) a upřímně, co model neumí. Slogan: desetiny milimetru shody s rekonstrukcí za setiny milisekundy výpočtu (0,0145 a 0,027 ms jsou setiny milisekundy).
* Dva modely, vždy pojmenované: základní síť (24 vstupů, 107 152 parametrů) a vybraný model (základní síť plus rozdíly sousedních cívek, lineární model pro proud, zvláštní síť pro bod u limiteru). Pro zašuměné vstupy se používá třetí věc, síť učená se šumem.
* Tři protokoly, nikdy je nemíchat bez štítku: 30 odložených výbojů (osa 0,13 mm), křížová validace na 119 výbojích (0,23 mm), novější čísla výbojů (0,40 mm). Základní síť má vlastní protokol: pět dělení po výbojích (osa 0,38 mm). Číslo 119 má dva významy: vývojová sada (119 výbojů, protokol křížové validace) a 119 učících výbojů v každém z pěti dělení všech 149 (křivka podle počtu výbojů, základní síť).
* Řečníci: A je první řečník (majitel týmu), B je druhý řečník (kolega).
* Porota: fyzici z ÚFP a odborníci na strojové učení. Čísla říkáme pomalu, jedno po druhém, a vždy s protokolem.
* Co čísla znamenají: síť napodobuje rekonstrukci ústavu (štítky jsou pravděpodobně výstup programu na rekonstrukci rovnováhy, program neznáme) z 24 čidel. Neměří plazma. Přesnost polohy plazmatu netvrdíme, tvrdíme jen shodu s rekonstrukcí.

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

Kamerový snímek je skrytá záloha a v časovém plánu nemá žádné vteřiny (viz Záloha: kamera). Čtení všech čísel slovy je o 25 až 50 sekund delší než prostý počet slov (Kritik 3, část 5), proto je počet slov v Lead notes počítán s čísly napsanými slovy. Z mluveného textu už jsou pryč: věta o rychlosti v ukázce, věta Zbývá napojení, věta Typický výboj sedí, věta U každého čísla řeknu, devadesát devět procent odhadů sítě (zůstává na dlaždici), řádek o 2,22 a 2,64 při učení se šumem (je v otázce 3), věta o délce výboje 150 až 200 milisekund (je v otázce 8), věta Zadání chce jednotky až desítky milisekund (je na snímku a v otázce 8), počet okamžiků 42 972 (je na dlaždici), 135 ze 149 výbojů v ukázce. Pokud je to před vystoupením o víc než 10 sekund přes, škrtá se dál v tomto pořadí: věta Platí jen pro jeden tokamak (6:11), řádek 4:01 o vybraném modelu (číslo zůstává na dlaždici), kamera (je skrytá). Věty s výhradou se nikdy nešktají: druhá věta řádku 4:10, řádky 4:29, 5:23 a 6:38. Řádky o grafické kartě a o druhém počítači jsou z mluveného textu pryč.

## Časovaný scénář

Čas je začátek řádku. Sloupec Co se říká je přesně to, co zazní. Text v závorkách se neříká. Rychlost řeči je asi 1,7 slova za sekundu, u čísel pomaleji.

### Snímek 1: Problém (0:00 až 0:38, 38 s)

Hlavní věta: Řízení potřebuje polohu a tvar plazmatu v milisekundách, úplná rekonstrukce rovnováhy trvá minuty.

Obrázek: 02-minutes-vs-ms.png (obrázek 04-wall-damage.png nepoužívat jako důkaz poškození stěny, viz docs/deck-fixes.md, snímek 1)

| Čas | Sek. | Kdo | Co se říká | Na obrazovce |
|---|---|---|---|---|
| 0:00 | 11 | A | Plazma v tokamaku se samo neudrží uprostřed komory. Protažené plazma je svisle nestabilní a bez rychlého řízení uhne ke stěně. | Snímek 1. Obrázek na celou plochu je jen ilustrace, neříkej, že jde o fotografii ani o doklad poškození stěny (docs/deck-fixes.md, snímek 1). |
| 0:11 | 10 | A | Řízení proto musí znát polohu a tvar plazmatu v řádu milisekund, tak to říká zadání. | Stále stejný obrázek. Délku výboje (150 až 200 milisekund podle organizátorů) nahlas neříkáme, je v otázce 8. |
| 0:21 | 8 | A | Úplná rekonstrukce rovnováhy se počítá po výboji a trvá minuty. Řízení potřebuje rychlý odhad. | Přepnout na obrázek 02-minutes-vs-ms.png (přesýpací hodiny proti záblesku) a dlaždice minuty a jednotky ms. |
| 0:29 | 7 | A | Naše otázka: dokáže malá neuronová síť rekonstrukci napodobit dost dobře a dost rychle? | Dole na snímku věta s otázkou (nový text je v docs/deck-fixes.md, snímek 2 decku). |
| 0:36 | 2 | A | Data představí kolega. | Pohled na B, klik na snímek 2. |

### Snímek 2: Data (0:38 až 1:06, 28 s)

Hlavní věta: 42 972 okamžiků ze 149 výbojů, 24 vstupů, 16 veličin, dělení po celých výbojích.

Obrázek: 03-coils.png

| Čas | Sek. | Kdo | Co se říká | Na obrazovce |
|---|---|---|---|---|
| 0:38 | 7 | B | Máme data ze 149 výbojů tokamaku COMPASS. | Snímek 2 (tři dlaždice 24, 16, 149; 42 972 okamžiků je na dlaždici a v hlavní větě, nahlas se neříká). Obrázek 03-coils.png je schéma, ne skutečný řez. |
| 0:45 | 14 | B | Vstup: jen 24 magnetických čidel, proudy v cívkách pole a model komory síť nedostává. Výstup: 16 veličin, poloha a tvar plazmatu, proud a údaj o limiteru. | Ukázat na obrázek. Je na něm 16 cívek, smyčky toku na něm nejsou. |
| 0:59 | 7 | B | Dělíme po celých výbojích, aby se netestovalo na tom, co model viděl. | Spodní věta snímku. |

### Snímek 3: Metoda (1:06 až 1:26, 20 s)

Hlavní věta: Základní síť o 107 152 parametrech a z ní vylepšený vybraný model; u každého čísla říkáme, na jakých výbojích bylo změřeno.

Obrázek: 06-neural-bridge.png

| Čas | Sek. | Kdo | Co se říká | Na obrazovce |
|---|---|---|---|---|
| 1:06 | 7 | A | Základní síť je malá neuronová síť o 107 152 parametrech. | Snímek 3. Obrázek 06-neural-bridge.png ukazuje princip. Teček čidel je na něm 16, skutečných vstupů je 24. |
| 1:13 | 13 | A | Vybraný model je její vylepšení: rozdíly sousedních cívek, lineární model pro proud a zvláštní síť pro bod u limiteru. | Spodní věta snímku (co je vybraný model); pod ní věta o ověření (u každého čísla je napsáno, na jakých výbojích bylo změřeno). |

### Snímek 4: Výsledky (1:26 až 2:29, 63 s)

Hlavní věta: Na 30 odložených výbojích se osa liší od rekonstrukce ústavu o 0,13 mm (0,23 mm v křížové validaci, 0,40 mm na novějších číslech); samotné cívky stačí na skoro stejnou souhrnnou chybu.

Obrázek: 05-shape-schematic.png

| Čas | Sek. | Kdo | Co se říká | Na obrazovce |
|---|---|---|---|---|
| 1:26 | 7 | A | Odhadujeme polohu osy, dolní bod X a dotykové body na deskách divertoru. Obrys vybraný model neodhaduje. | Snímek 4. Obrázek 05-shape-schematic.png asi 6 sekund, pak snímek s výsledky. |
| 1:33 | 23 | A | Třicet výbojů jsme odložili před posledním výběrem modelu, náměty na úpravy ale vznikly na všech 149. Na odložených se vybraný model od rekonstrukce ústavu liší v radiální poloze osy o 0,13 milimetru, základní síť o 0,31. | Titulek a sloupce osy R. Protokol pod číslem: 30 odložených výbojů. Pod grafem je věta, že náměty na úpravy vznikly na všech 149 výbojích. |
| 1:56 | 9 | A | V křížové validaci na 119 výbojích 0,23, na novějších číslech 0,40. | Řádek protokolů pod grafem (119 výbojů, křížová validace; novější čísla). |
| 2:05 | 12 | A | Proud určí lineární model s chybou 0,035 kiloampéru; síť měla 1,2. | Dlaždice 0,035 kA (lineární model; proč stačí lineární, je v otázce 4). Protokol: 30 odložených výbojů. Bod u limiteru 4,55 mm proti 10,6 je na dlaždici a zazní na snímku 6. |
| 2:17 | 12 | B | Samotné cívky stačí na skoro stejnou souhrnnou chybu jako všech 24 vstupů, osm nejlepších už ne. | Graf Kolik vstupů stačí (základní síť, pět dělení po výbojích): 0,066 proti 0,063, osm nejlepších 0,094. Menší číslo je lepší. |

### Živá ukázka, mezi snímkem 4 a 5 (2:29 až 3:49, 80 s)

Hlavní věta: Rekonstrukce ústavu a odhad vybraného modelu vedle sebe: sledujeme odhadnuté body, obrys vybraný model neodhaduje; jedna typická a jedna špatná ukázka.

Obrázek: žádný, na obrazovce je prohlížeč tvaru (repo/viewer/index.html)

| Čas | Sek. | Kdo | Co se říká | Na obrazovce |
|---|---|---|---|---|
| 2:29 | 13 | A | Teď naživo. Obrys v ukázce je z rekonstrukce ústavu, naše síť odhaduje jen označené body, na třiceti výbojích, které jsme odložili. | Cmd+Tab do prohlížeče. Okno je předem otevřené na výboji 85, rychlost 1×, zastaveno. Dlaždice říká vybraný model. |
| 2:42 | 12 | A | Tmavá čára je tvar z rekonstrukce ústavu, barevné značky jsou odhad sítě. Výboj číslo 85 je z odložených třiceti a je typický. | Ukázat na dva přepínače. V prohlížeči mají stát Rekonstrukce ústavu a Odhad sítě; dokud tam stojí Skutečnost a Předpověď, tato dvě slova nahlas neříkej (docs/deck-fixes.md, viewer). Mezerník spustí přehrávání. |
| 2:54 | 6 | A | (ticho, výboj běží a porota se dívá) | Nech výboj proběhnout dvakrát. |
| 3:00 | 12 | A | Kroužek je osa, křížek bod X. Chyba osy je tady čtvrtina milimetru, na začátku i uprostřed výboje. | Ukázat na značky a tabulku. Čísla z prohlížeče: začátek 0,22 mm, střed 0,25 mm (docs/demo-facts.md). |
| 3:12 | 14 | A | Teď nejhorší konec: výboj číslo 147, poslední snímek. Osa je vedle o třicet tři milimetrů a bod u limiteru o sto pět, ale průměr celého výboje je pod milimetrem. | Výboj 147 z nabídky, poslední snímek (t 1,0). Čísla: osa 33,7 mm, bod u limiteru asi 105 mm, průměr výboje 0,85 mm (docs/demo-facts.md). |
| 3:26 | 5 | A | (ticho, špatný výboj běží) | Ukázat na místo, kde se čáry rozcházejí. |
| 3:31 | 14 | B | Takových výbojů je málo: všech třicet odložených má průměrnou chybu osy pod milimetrem, medián asi 0,2. | Protokol: vybraný model, odložených 30 a vývojové výboje mimo učení, vzdálenost osy (docs/demo-facts.md); dva výboje nad 5 mm, obě vývojové (id 0 a 11); pod milimetrem je 135 ze 149 výbojů, nahlas se neříká. |
| 3:45 | 4 | A | (ticho, přepnutí zpět) | Cmd+Tab zpět do prezentace, klik na snímek 5. Dlaždici latence v prohlížeči neukazovat ani neříkat (číslo zazní na snímku 5). |

### Snímek 5: Rychlost, verdikt pro řízení (3:49 až 4:29, 40 s)

Hlavní věta: Základní síť 0,0145 ms, vybraný model asi 0,03 ms (0,027 u limitovaného plazmatu), obojí pod naším rozpočtem 1 až 10 ms; ověřili jsme jen výpočet samotné sítě, ne celý řetězec od čidel k řízení.

Obrázek: 02-minutes-vs-ms.png (zopakovat jako pozadí)

| Čas | Sek. | Kdo | Co se říká | Na obrazovce |
|---|---|---|---|---|
| 3:49 | 12 | B | Základní síť: jeden odhad na procesoru Apple M5 trvá 0,0145 milisekundy. | Snímek 5. Velká dlaždice 0,0145 ms, dlaždice 0,0209 ms (devadesát devět procent odhadů je rychlejších, nahlas se neříká). Pod nimi: základní síť, procesor Apple M5. |
| 4:01 | 9 | B | Vybraný model má tři části a trvá asi 0,03 milisekundy. | Dlaždice vybraného modelu: 0,027 ms, limitované plazma, Apple M5, vytížený notebook (results/ipp1-latency-shipped.md, numpy, náhodné váhy stejného tvaru, jen čas). |
| 4:10 | 19 | B | Náš rozpočet je jedna až deset milisekund, výpočet sítě je hluboko pod ním. Neověřili jsme zbytek řetězce: sběr a integraci signálů v reálném čase, jak signály vypadají v provozu, uzavřenou smyčku a systém reálného času. | Věta pod dlaždicemi. Rozpočet 1 až 10 ms je náš, ne ze zadání; že zadání chce jednotky až desítky milisekund, je na snímku a v otázce 8. Konec snímku, pohled na A, klik na snímek 6. |

### Snímek 6: Meze (4:29 až 5:03, 34 s)

Hlavní věta: Nejhůř bod u limiteru (medián chyby 0,73 mm, průměr 4,55 mm u vybraného modelu na 30 odložených výbojích, vzdálenost od stěny neměřena); chyba osy roste hlavně na konci výboje.

Obrázek: žádný obrázek, na snímku je graf chyby osy podle času

| Čas | Sek. | Kdo | Co se říká | Na obrazovce |
|---|---|---|---|---|
| 4:29 | 22 | A | Bod u limiteru je místo na stěně, kde se plazma dotkne. Medián chyby je 0,73 milimetru, průměr 4,55 táhnou řádky s jiným místem dotyku, v jednom procentu je chyba přes 77 milimetrů. Vzdálenost od stěny jsme neměřili. | Snímek 6. Dlaždice 4,55 mm a 8,35 mm (vybraný model, 30 odložených výbojů); pod nimi 99 % řádků pod 77,5 a 92,2 mm (results/ipp1-final.md, sloupec p99). Medián 0,733 mm a nejhorší řádky 357 a 485 mm jsou v tomtéž souboru. |
| 4:51 | 12 | A | Chyba osy roste hlavně na konci výboje, 0,9 milimetru proti 0,24 uprostřed, základní síť, pět dělení. Příčinu neznáme. | Graf chyby osy podle desetin výboje (základní síť, pět dělení), oranžové sloupce jsou začátek a konec. Hypotézu o slabé rekonstrukci na koncích říkáme jen v otázce 8 a jen s přívlastkem hypotéza. Kolísání výstupu je jen v poznámce pod čarou. |

### Snímek 7: Co model neumí (5:03 až 6:17, 74 s)

Hlavní věta: Odolnost vůči chybám čidel jsme zkoušeli jen na šumu a na umělém posunu; šum zhroutí síť naučenou na čistých datech, síť potřebuje dost výbojů, neobvyklé tvary jsme samostatně neověřili, jen jeden tokamak.

Obrázek: žádný obrázek, na snímku jsou dva grafy (šum, počet výbojů)

| Čas | Sek. | Kdo | Co se říká | Na obrazovce |
|---|---|---|---|---|
| 5:03 | 20 | B | Slabina je odolnost vůči chybám čidel. Zkoušeli jsme šum od organizátorů a umělý posun. Základní síť má chybu osy 0,38 milimetru na čistých datech a 10,15 na zašuměných. | Snímek 7, levý graf, první dva sloupce (třetí sloupec 2,64 se nemluví, je v otázce 3). Protokol: základní síť, pět dělení po výbojích. |
| 5:23 | 14 | B | Vybraný model na šumu selže, proto bychom použili síť učenou se šumem: osa 2,38 milimetru na třiceti odložených výbojích. | Řádek pod grafem (30 odložených výbojů; proud 4,65 kA je tam také). |
| 5:37 | 17 | A | Druhá slabina: počet výbojů. Se 30 učícími výboji je chyba osy 1,47, se všemi učícími výboji, 119 v každém dělení, je 0,38, ale s pevným počtem epoch. | Pravý graf, křivka podle počtu učících výbojů (základní síť, pět dělení). |
| 5:54 | 17 | A | Třetí slabina: neobvyklé tvary. Osmnáct nejodlišnějších výbojů jsme vynechali z učení a chyba osy je u základní sítě asi dvaapůlkrát větší, od 0,9 do 2,3 milimetru. Čtrnáct z nich je z časné části kampaně, takže se tu míchá tvar s dobou. | Spodní text snímku. |
| 6:11 | 6 | B | Platí jen pro jeden tokamak. | Spodní text snímku; věta, že řízení plazmatu model sám nenahradí, je jen tam. |

### Snímek 8: Závěr (6:17 až 7:00, 43 s)

Hlavní věta: Shoda s rekonstrukcí ústavu desetiny milimetru na čistých vstupech, rychlost výpočtu setiny milisekundy, a upřímně co nefunguje.

Obrázek: 07-closing.png

| Čas | Sek. | Kdo | Co se říká | Na obrazovce |
|---|---|---|---|---|
| 6:17 | 10 | A | Shoda s rekonstrukcí ústavu na čistých vstupech: osa 0,13 milimetru na odložených výbojích, asi 0,2 v křížové validaci. | Snímek 8. Obrázek 07-closing.png. Dlaždice Shoda s rekonstrukcí. |
| 6:27 | 11 | A | Rychlost: základní síť 0,0145 milisekundy, vybraný model asi 0,03. | Velké číslo 0,0145 ms vlevo a vedle něj vybraný model (0,027 ms). Pomalu. |
| 6:38 | 17 | B | Na zašuměných vstupech je osa na jednotky milimetrů, bod u limiteru na desítky, proud 4,65 kiloampéru. Pro řízení model ještě není: chybí řetězec od čidel a zkouška v uzavřené smyčce. | Dlaždice Shoda s rekonstrukcí (druhý řádek) a Zbývá. Zašuměné vstupy: osa 2,38 mm, bod u limiteru 25,8 a 38,9 mm, proud 4,65 kA (30 odložených výbojů, síť učená se šumem). |
| 6:55 | 5 | A+B | Na čistých vstupech desetiny milimetru shody s rekonstrukcí, setiny milisekundy výpočtu. Děkujeme. | Oba se dívají na porotu. Konec v 7:00. |

## Pravidla řeči

* Číslo řekni jednou, pomalu, a nech ho doznít. V jedné větě nejvýš dvě čísla. Pod každým číslem shody s rekonstrukcí řekni, na jakých výbojích bylo změřeno (odložených 30, křížová validace, pět dělení po výbojích). Číslo bez protokolu neříkej.
* Slova zamčená, nikdo neviděl a před finálním výběrem neříkej (porota z nich slyší výboje mimo návrh). Říkej odložené výboje, odložené před posledním výběrem modelu, a hned větu, že náměty na úpravy modelu vznikly na všech 149 výbojích (řádek 1:33, otázka N2).
* Slova pro čísla: říkej shoda s rekonstrukcí ústavu, odchylka od rekonstrukce, odhad sítě. Neříkej přesnost polohy plazmatu, skutečný tvar, skutečnost, předpověď. Neříkej, že síť měří plazma. Říkej dolní bod X, ne jen bod X, když jde o význam. Dotykový bod je místo, kde hranice plazmatu protíná desky divertoru. Šum v souboru je od organizátorů, posun je náš umělý. Směrodatná odchylka šumu, ne rozptyl.
* Slova základní síť a vybraný model nikdy nezaměňuj. Rychlost 0,0145 milisekundy patří základní síti, nikdy vybranému modelu. Vybraný model má asi 0,03 milisekundy, u limitovaného plazmatu medián 0,027, u divertorového 0,015.
* Rozpočet jedné až deseti milisekund je náš; zadání chce jednotky až desítky milisekund (to říkej v odpovědi na otázku 8, řádek 4:10 říká jen náš rozpočet). Neříkej, že rozpočet dalo zadání.
* Nečti text ze snímku. Dívej se na porotu, na obrazovku jen ukaž.
* Před začátkem: prohlížeč otevřený na výboji 85, rychlost 1×, zastaveno; výboj 147 připravený v nabídce; hlasitost a zrcadlení obrazovky vyzkoušené. Čísla z prohlížeče jsou v docs/demo-facts.md; den předem je jednou porovnat s tím, co prohlížeč ukazuje.
* Kontrolní časy: 0:38 snímek 2, 1:06 snímek 3, 1:26 snímek 4, 2:29 ukázka, 3:49 snímek 5, 4:29 snímek 6, 5:03 snímek 7, 6:17 snímek 8, 7:00 konec.
* Neznáš odpověď? Řekni: Tohle jsme neměřili. A pokračuj tím, co jsme měřili. Nikdy nehádej číslo.

## Záloha, když ukázka selže

* Po první větě ukázky (2:29) řekni: Ukázka se nespustila, ukážu uložené obrázky. Pak ukaž tři obrázky z tlačítka Uložit PNG (začátek, střed a konec, výboj 85 a 147) a řádky ukázky o osách a tabulce. Zkrať to na 45 sekund a zbytek času dorovnej tím, že vynecháš řádky se špatným výbojem. Skrytý snímek 10 se z prezentace otevře klávesou H (nebo napsat 10 a Enter); klávesa H funguje jen v PowerPointu, protože skrytý snímek 10 následuje hned po snímku 9. V Keynote ani v Google Slides klávesa H není: tam před vystoupením odkrýt snímek 10 nebo mít záložní kopii s odkrytým snímkem a vyzkoušet, jak se na něj přejde.
* Záznam hotový: `out/viewer-demo.mp4` (60 s, výboj 85, jen na počítači, mimo git). Zkopírovat ho a `viewer/dist/index.html` na druhý notebook. Plynulejší verze: `viewer/record.py --seconds 20`.
* Den před vystoupením: jednou přehrát výboje 85 a 147 a porovnat s docs/demo-facts.md. Dřívější čísla pro výboje 123, 0 a 11 pocházela ze základní sítě a nepoužívají se.

## Záloha: kamera (skrytý snímek 5 v decku)

Nepoužívá se, pokud před vystoupením nezbývá mezera aspoň 20 sekund. V časovém plánu nemá vteřiny. Pokud se použije, řekne ji B:

| Čas | Sek. | Kdo | Co se říká | Na obrazovce |
|---|---|---|---|---|
| záloha | 20 | B | Bonus: malá kamerová síť na snímcích 48 na 64 bodů, naučená na 78 výbojích, je 1,3 až 13krát horší než cívky; osa 1,79 milimetru proti 0,38, orientačně. Barva nepomáhá. Říká to něco o této malé síti, ne o kameře. | Skrytý snímek 5. Pět dělení po výbojích. |

## Verze na 30 sekund

Řízení tokamaku potřebuje znát polohu a tvar plazmatu v milisekundách, úplná rekonstrukce ale trvá minuty. Naučili jsme malou neuronovou síť, aby rekonstrukci ústavu napodobila ze 24 magnetických měření. Na 30 odložených výbojích se osa od rekonstrukce liší o 0,13 milimetru, jeden odhad trvá setiny milisekundy. Slabé je šum, bod u limiteru a jediný tokamak.

Slov: 54, s čísly počítanými dvakrát 57. Přibližně 30 sekund (odhad podle počtu slov, ne stopky).

## Verze na 60 sekund (výtah)

Řízení tokamaku potřebuje polohu a tvar plazmatu v milisekundách, úplná rekonstrukce rovnováhy trvá minuty. Naučili jsme malou neuronovou síť napodobit rekonstrukci ústavu ze 24 magnetických měření. Na 30 výbojích odložených před posledním výběrem modelu se osa vybraného modelu od rekonstrukce liší o 0,13 milimetru, základní sítě o 0,31; náměty na úpravy ale vznikly na všech 149 výbojích. Jeden odhad základní sítě trvá 0,0145 milisekundy na procesoru Apple M5, vybraný model asi 0,03. Nejsme hotovi: bod u limiteru má průměrnou chybu 4,55 milimetru, na zašuměných vstupech je osa 2,38, neobvyklé tvary jsme samostatně neověřili a chybí řetězec od čidel k řízení. Data jsou jen z jednoho tokamaku.

Slov: 106, s čísly počítanými dvakrát 116. Přibližně 60 sekund (odhad podle počtu slov, ne stopky).

## Deset zlých otázek a upřímné odpovědi

Každá odpověď říká i mez a u čísla protokol. Poznámky k zdrojům a k tomu, co ještě chybí, jsou v části Lead notes. Odpovědi 4, 5, 6 a 8 byly po kontrole Kritika 2 přepsány, protože původní znění už neplatilo (tvrdilo, že vybraný model nepoužívá lineární model pro proud, že se architektura neladila podle testu, že silnější modely se teprve zkoušejí a že rychlost 0,0145 milisekundy patří vybranému modelu). Po kontrole fyzika (`docs/review-physics.md`, větev `cloud/pitch-fix-3`) se přepsaly odpovědi 1, 2, 3, 4, 7, 8, 9 a N1, N3, N6, N8, N13 (rekonstrukce ústavu místo skutečného plazmatu, Ampérův zákon, šum a posun, celý řetězec řízení, relativní čas, konec výboje, polarita) a přibyly otázky F2, F4 a F5; všech deset nejtěžších fyzikálních otázek F1 až F10 je dohledatelných v části Příloha: deset nejtěžších fyzikálních otázek. Po kontrole Kritika 3 se opravily ještě 5 (rozptyl mezi dělením 0,12 v žádném souboru není, použit je rozptyl semen), 6 (zkoušeli jsme stromy), 8 a N5 (změřená rychlost) a 9 (věta o COMPASS Upgrade nemá zdroj v repozitáři) a 10 (náhradní věta bez čísla).

### 1. Fyzik
Otázka: Čemu říkáte pravda? Porovnáváte se skutečným plazmatem, nebo s výpočtem? Jak přesné je 0,13 milimetru? (F1)

Odpovídá A: Porovnáváme se s rekonstrukcí rovnováhy, kterou nám dal ústav, ne se skutečným plazmatem. Podle toho, co víme, takhle správné odpovědi vznikly; program a jeho nastavení neznáme. Na třiceti odložených výbojích se vybraný model od ní liší v radiální poloze osy průměrně o 0,13 milimetru, interval přes výboje je 0,10 až 0,18. Jak přesná je sama rekonstrukce, jsme neměřili a nezávislé měření polohy plazmatu jsme nepoužili. Ověřit by to šlo zkalibrovanou kamerou nebo výpočtem, kde tvar předem známe.

### 2. Fyzik
Otázka: Co když plazma bude mít nový tvar, který v datech nebyl? A co když řízení uzavře smyčku? (F9)

Odpovídá A: Nevíme. Když jsme při učení vynechali celou rodinu tvarů, byla chyba osy 1,0 až 3,0krát větší, obvykle 1,2 až 2,4krát, u základní sítě v pětinásobném dělení. Osmnáct nejodlišnějších výbojů jsme pak vynechali z učení samostatně: u základní sítě je chyba osy 0,9 až 2,3 milimetru, asi dvaapůlkrát víc než v náhodném dělení, a pěti nejnižším protažením dokonce 2,6 až 4,9 milimetru. Čtrnáct z těch osmnácti je ale z nejstarších čísel výbojů, takže se tu míchá tvar s časnou částí kampaně. O tvarech mimo rozsah dat to nic neříká. (`results/ipp1-unusual-heldout.md`) Na nejnovějších číslech výbojů, při učení na šedesáti nejnižších, je osa vybraného modelu 0,40 milimetru místo 0,22. V datech leží protažení a trojúhelníkovost na úzké křivce, tedy na jedné rodině tvarů, které stroj ve svých scénářích vytváří. Síť se naučila tuto rodinu a pro tvar mimo ni jí věřit nelze. V uzavřené smyčce řízení samo změní proudy v cívkách, a tím vstupy sítě; to jsme netestovali.

### 3. Fyzik
Otázka: Síť se na šumu zhroutí. Dá se to vůbec použít se skutečnými čidly? Je váš šum a posun realistický? (F7)

Odpovídá A: Síť naučená na čistých datech na šum nestačí: chyba osy vyskočí z 0,38 na 10,15 milimetru, u základní sítě v pěti dělení po výbojích. Při učení na zašuměných datech je to 2,64 milimetru, ale na čistých datech pak 2,22. Vybraný model naučený na čistých datech na šumu selže úplně, proto bychom pro zašuměné vstupy použili síť učenou se šumem: na odložených výbojích má osu 2,38 milimetru. Šum v souboru od organizátorů je bílý a posun v něm není. Jeho směrodatná odchylka je asi 16 procent směrodatné odchylky signálu u cívek a 9 procent u smyček toku. Poměr se mezi čidly mění jen málo, což vypadá spíš na šum přidaný úměrně signálu než na změřený; to jen usuzujeme. Zda odpovídá skutečným čidlům, nevíme. Posun jsme vyrobili sami, lineární v relativním čase výboje, kdežto skutečný posun integrátoru roste s absolutním časem. Špatnou kalibraci a výpadek čidla jsme netestovali.

### 4. Odborník na strojové učení
Otázka: Proč u proudu plazmatem vychází lineární model lépe než vaše síť? (F3)

Odpovídá A: Je to tak a vybraný model to využívá. Podle Ampérova zákona je součet částečných Rogowského cívek po celém obvodu úměrný proudu uvnitř, takže stačí lineární model. Na odložených výbojích má chybu 0,035 kiloampéru, základní síť 1,2; to je 0,03 procenta rozptylu proudu, který je 114 kiloampérů. Takto přesná shoda spíš znamená, že proud v datech je odvozen z týchž signálů, než že je změřen nezávisle; to jsme ale neověřili. Není to úspěch sítě a nepočítáme to do tvrzení, že je vybraný model lepší. Na zašuměných vstupech je chyba proudu 4,0 až 4,7 kiloampéru podle modelu, obě učené se šumem.

### 5. Odborník na strojové učení
Otázka: Je validace poctivá? Jen 149 výbojů, jedno náhodné nastavení, žádný interval spolehlivosti.

Odpovídá A: Dělíme po celých výbojích. Základní síť ověřujeme pětkrát jinak, u osy je střední chyba 0,38 milimetru. Vybraný model jsme navrhovali na křížové validaci přes všech 149 výbojů, takže odložených 30 bylo při návrhu v testovacích částech; po odložení se nic neladilo, jen jsme vybrali jednu ze čtyř variant uvnitř 119 výbojů. Odložené výboje vycházejí lépe než vývojová křížová validace, 0,13 proti 0,23 milimetru, proto uvádíme obě čísla. Interval přes výboje pro odloženou osu je 0,10 až 0,18 milimetru. Pro hlavní srovnání jsme udělali pět semen: osa R vychází 0,133 milimetru se směrodatnou odchylkou 0,006 u vybraného modelu a 0,289 s odchylkou 0,011 u základní sítě; vybraný model je lepší v pěti z pěti u všech sedmi veličin.

### 6. Odborník na strojové učení
Otázka: Proč jen jedna síť? Zkoušeli jste stromy nebo jiné architektury?

Odpovídá B: Zkoušeli jsme víc: širší a hlubší sítě, jinou ztrátovou funkci, rozdíly sousedních cívek, soubory tří sítí i stromy pro bod u limiteru. Nejvíc pomohla zvláštní síť pro bod u limiteru a lineární model pro proud; chyba bodu u limiteru klesla na polovinu, 4,55 proti 10,6 milimetru na odložených výbojích. Stromy byly horší než zvláštní síť. Zlepšení platí v pěti z pěti semen, u bodu X radiálně je jen o něco lepší. Kromě sítí jsme zkoušeli jen stromy pro bod u limiteru. Nemáme zvláštní ověřovací část, proto rozdíly pod 10 až 15 procent považujeme za šum.

### 7. Fyzik
Otázka: Chyba 0,13 milimetru zní skvěle, ale hodnoty se skoro nehýbou. Co to znamená?

Odpovídá A: Správně, ale jen u osy, bodu X a dotykových bodů: jejich směrodatná odchylka je od 2,4 do 13,7 milimetru, u radiální osy asi 8. U bodu limiteru je 90 a 153 milimetrů a u proudu plazmatem 114 kiloampérů. Proto uvádíme chyby v milimetrech i vztažené ke směrodatné odchylce: u osy je to 0,139 u základní sítě a 0,68 u lineárního modelu, v pěti dělení po výbojích.

### 8. Podnikatel
Otázka: Co to znamená v praxi? Dá se to nasadit do řízení? Co kromě času sítě musí řízení zvládnout? (F10)

Odpovídá B: Zatím ne. Změřili jsme jen výpočet sítě, na jednom jádru procesoru Apple M5, na vytíženém notebooku: základní síť 0,0145 milisekundy, vybraný model 0,027 u limitovaného plazmatu a 0,015 u divertorového. Zadání chce jednotky až desítky milisekund, my počítáme s rozpočtem jedné až deseti a obojí je hluboko pod ním. Celý výboj trvá podle organizátorů 150 až 200 milisekund, ale čas v souboru je relativní a skutečný odstup řádků neznáme. Na systému bez reálného času se ojediněle objeví špičky, dřívější měření dalo 99 procent pod 0,65 milisekundy a největší 21. Neměřili jsme sběr a integraci signálů, zda signály za provozu vypadají jako data, uzavřenou smyčku, výpadek čidla ani nejhorší dobu na systému reálného času. Řízení polohy navíc potřebuje rychlost změny polohy, a tu jsme neměřili. Jsou to také dva modely, pro čisté a pro zašuměné vstupy, a přepínání mezi nimi jsme netestovali. Bez toho bych to do řízení nedal.

### 9. Podnikatel
Otázka: Komu to pomůže a co dál? Dá se to použít na COMPASS Upgrade?

Odpovídá B: Náš model je naučený jen na COMPASSu. Na jiném stroji se mění geometrie, čidla i cívky, takže by se musel učit znovu, ne jen doladit. U základní sítě je s 30 učícími výboji chyba osy 1,47 milimetru; kolik výbojů potřebuje nový stroj, nevíme.

### 10. Podnikatel
Otázka: Proč věřit modelu, který neříká, jak si je jistý? Co když se plete?

Odpovídá B: Síť sama vydá jen číslo. Zkusili jsme pět sítí s různým náhodným začátkem, základní síť v pěti dělení po výbojích: na deseti procentech řádků, kde se nejvíc rozcházejí, je chyba 8krát větší než na zbytku a ty řádky nesou 47 procent celé chyby. Je to použitelné varování, ne pravděpodobnost chyby, a netestovali jsme ho na neobvyklých tvarech ani na zašuměném vstupu. Slabá místa známe: bod u limiteru, začátek a konec výboje a šum. V prohlížeči jste viděli špatný výboj, rozdíl mezi čárami byl vidět. (Číslo říkej jen po ověření: odchylka osy 0,22 milimetru. Bez ověřeného čísla neříkej žádné.)

## Příloha: dalších třináct otázek od Kritika 2

Kritik 2 sepsal třináct nových otázek; prvních deset je hlavní sada, N11 až N13 jsou krátké doplňky. Číslo N odpovídá pořadí v `docs/review-findings-2.md` (část Ten new hostile questions).

### N1. Fyzik
Otázka: Vaše nejlepší číslo je pro signály bez šumu. Skutečné sondy šum mají. Jak přesní jste na nich?

Odpovídá A: Na souboru se šumem od organizátorů dává model, který bychom použili, učený se šumem a posunem, na 30 odložených výbojích osu 2,38 milimetru, bod u limiteru 25,8 a 38,9 milimetru a proud 4,65 kiloampéru. Vybraný model naučený na čistých datech tam selže (osa 190 milimetrů). Zda šum v souboru odpovídá skutečným čidlům, nevíme: je bílý, jeho směrodatná odchylka je asi 16 procent směrodatné odchylky signálu u cívek. Podrobněji v otázce 3.

### N2. Odborník na strojové učení
Otázka: Navrhovali jste model s pohledem na testovací výboje?

Odpovídá A: Částečně. Třicet odložených výbojů jsme vylosovali po návrhu receptu, ale návrhové pokusy běžely na křížové validaci přes všech 149 výbojů, takže těch 30 bylo při návrhu v testovacích částech. Na odložených 30 se pak nic nepřeučovalo; jen poslední volba ze čtyř variant se udělala uvnitř 119 vývojových výbojů. Odložené výboje vycházejí lépe než vývojové, osa 0,133 proti 0,230 milimetru, proto uvádíme obě čísla.

### N3. Odborník na strojové učení
Otázka: Je odložená sada reprezentativní? Co je to opačný směr proudu? (F6)

Odpovídá A: Ne zcela. V celém souboru má kladné znaménko proudu 16 ze 149 výbojů, 7,4 procenta řádků, ostatní záporné. Konvenci znaménka a vztah ke směru toroidálního pole neznáme, nevíme tedy, zda jde o opačnou polaritu stroje. Mezi odloženými jsou takové jen 2 z 30 výbojů, 591 z 8 761 řádků, a na nich je chyba osy u vybraného modelu 0,454 milimetru proti 0,110 na ostatních. Signály se při obrácení znaménka zrcadlí: střední rozdíl mezi skupinami je 2,00 směrodatné odchylky vstupu a po vynásobení znaménkem součtu cívek 0,13. Sjednocení znaménka zlepší kladné výboje o 64 procent a zhorší většinu o 20, proto ho nepoužíváme. Dva výboje jsou málo na spolehlivý závěr.

### N4. Odborník na strojové učení
Otázka: Vylepšený model, kolik z toho je skutečné?

Odpovídá A: Pět semen: vybraný model je lepší v pěti z pěti u všech sedmi veličin, zisk u osy, dotykového bodu a bodu u limiteru je 42 až 60 procent. U bodu X radiálně je zisk jen 21 procent, nejbližší semeno 0,96, říkáme jen o něco lepší. Střední kvadratická chyba bodu X radiálně a druhého dotykového bodu je horší (0,454 proti 0,305 a 0,638 proti 0,401 milimetru) a nejhorší jednotlivý řádek šesti veličin je větší.

### N5. Fyzik
Otázka: Jakou rychlost uvádíte, tu vybraného modelu?

Odpovídá B: Číslo 0,0145 milisekundy patří základní síti. Vybraný model trvá 0,027 milisekundy u limitovaného plazmatu a 0,015 u divertorového, asi dvakrát víc než základní síť. Dřívější odhad 0,18 se při měření na stejném postupu nepotvrdil. Obojí je hluboko pod naším rozpočtem jedné až deseti milisekund; ani jedno nezahrnuje sběr dat.

### N6. Fyzik
Otázka: Pro řízení rozhodují náhlé zániky a start výboje. Jak jste tam dobří? (F8)

Odpovídá A: Nejhůř na koncích. V posledních 2 procentech výboje je u vybraného modelu na odložených výbojích radiální chyba osy 0,578 milimetru proti 0,114 uprostřed, svislá 1,33 proti 0,14. U základní sítě v pěti dělení má nejhorší jednotlivý řádek svislou chybu 284 milimetrů při směrodatné odchylce svislé osy 13,7. Příčinu neznáme: může to být síť, ale i rekonstrukce, která je při malém proudu a rychlých změnách nejhůř určená; to je jen hypotéza. Zda data obsahují zánik plazmatu, jsme nevyhodnotili. Výboje mají 17 až 439 řádků.

### N7. Odborník na strojové učení
Otázka: Model, který musí vědět, zda jsou vstupy zašuměné, není model. Co dodáte?

Odpovídá A: Dva modely: vybraný pro čisté vstupy a síť učenou se šumem pro zašuměné. Jeden vítěz neexistuje: modely učené se šumem jsou na čistých datech horší, osa 1,56 proti 0,307 milimetru u základní sítě. Přepínání podle druhu vstupu je předpoklad nasazení, který jsme netestovali.

### N8. Fyzik
Otázka: Šum je nezávislý v každém řádku. Proč nezprůměrovat několik vzorků?

Odpovídá A: Zkusili jsme tři po sobě jdoucí řádky: na zašuměných vstupech klesla chyba osy z 2,64 na 2,33 milimetru, na čistých vstupech byla horší, z 0,38 na 0,57. Delší okna jsme nezkoušeli. Okno je počet řádků, ne milisekundy: čas v souboru je relativní a skutečný odstup řádků neznáme.

### N9. Fyzik
Otázka: Přežije se výpadek cívky?

Odpovídá A: Netestovali jsme. Jediný důkaz: samotných 16 cívek dává souhrnnou chybu 0,066 proti 0,063 se všemi 24 vstupy, samotných 8 smyček toku 0,285, vše u základní sítě v pěti dělení po výbojích. Pořadí vstupů není stabilní (shoda tří způsobů je od minus 0,14 do 0,40), proto žádné jedno čidlo nepojmenováváme; cívka IPR13 přežila vyřazování ve všech pěti dělení.

### N10. Odborník na strojové učení
Otázka: Kamerový model je špatný. Je kamera k ničemu?

Odpovídá A: Je to malá síť na snímcích 48 na 64 bodů, 12 epoch, každý osmý snímek, 78 ze 149 výbojů. Je 1,3 až 13krát horší než cívky a při spojení s cívkami nic nepřidá (1,21 proti 0,24 milimetru na dvou dělení). To ukazuje, že tato síť obrazy dobře nevyužívá, ne že kamera nenese informaci.

### N11. Fyzik
Otázka: Zadání mluví o 17 parametrech, vy uvádíte 16.

Odpovídá B: Vybraný model odhaduje 16 hlavních sloupců z 31 v souboru. Ostatních patnáct jsou doplňkové veličiny pro obrys; ty odhaduje jen základní síť a čísla pro ně zatím nezveřejňujeme (oprava podle `docs/bonus-gaps.md`, stejně jako v `docs/REHEARSAL.md`).

### N12. Odborník na strojové učení
Otázka: A jak si model vede na nejnovějších výbojích?

Odpovídá A: Čísla výbojů zřejmě sledují čas, což jsme s organizátory neověřili. Když učíme na 60 nejnižších číslech a testujeme na 59 nejvyšších, je chyba osy vybraného modelu 0,397 milimetru (při náhodném dělení 0,216), základní sítě 1,23 (0,448). Část rozdílu vysvětluje menší učící sada.

### N13. Podnikatel
Otázka: Proč věřit shodě 99,3 procenta pro limitované a divertorové plazma?

Odpovídá B: Základní síť má 0,993 v pěti dělení, vybraný model 0,9916 a základní síť 0,9892 na odložených výbojích. Chyby základní sítě v pěti dělení se dělí zhruba rovným dílem mezi obě konfigurace, 49 a 51 procent čtverce chyby. Příznak je tvrdé rozhodnutí na spojitém přechodu, takže chyby čekáme právě tam, ale na přechodu jsme je zvlášť nevyhodnotili. Chyby bodu X a dotykových bodů jsme počítali jen na řádcích, kde tyto body podle rekonstrukce jsou; v provozu by je řídil odhadnutý příznak a jeho chyby na přechodu jsme nezměřili.

### N14. Porotce nebo organizátor: Kdo to dělal a jak jste používali nástroje s umělou inteligencí?

Odpovídá B: Pracovali jsme ve dvou. Kód, analýzy a texty jsme psali s pomocí nástrojů s umělou inteligencí, hlavně modelů Claude a GPT, které pracovaly jako pomocníci. Zadání, rozhodnutí a kontrolu každého čísla v repozitáři jsme dělali my. U každého výsledku je zapsán protokol a soubor, aby se dal ověřit. *(Znění potvrdí majitel před vystoupením; otázku na pravidla ke používání AI mají organizátoři v seznamu otázek, číslo 12. Nikdy neříkat, že AI nebyla použita.)*

### N15. Fyzik: Co je nejslabší místo a zkoušeli jste ho zlepšit?

Odpovídá B: Nejslabší je bod, kde plazma dosedá na limiter: chyba 4,55 a 8,35 milimetru na třiceti odložených výbojích. Zkusili jsme vyměnit jen jeho síť za reziduální z našeho hledání. Ve vývoji snížila chybu o 39 procent, na odložených výbojích o 28 a 34 procent, tedy z 4,55 na 3,26 a z 8,35 na 5,55 milimetru, ostatní výstupy zůstaly stejné. Jako hlavní model ji nepoužíváme: její nastavení vzešlo z hledání, které vidělo všechny výboje, je asi třikrát pomalejší (0,087 proti 0,029 milisekundy) a pravidlo pro rychlost jsme museli upravit dodatečně, což je v protokolu vyznačeno. (`results/ipp1-limiter-swap.md`)

## Příloha: deset nejtěžších fyzikálních otázek

Zdroj: `docs/review-physics.md`, část 5 (otázky F1 až F10). Sedm z nich je totéž co otázky výše, proto jsou sloučené a odpověď je tam; tři nové (F2, F4, F5) jsou níže. Čísla jsou jen ze složky `results/`, kde odpověď neví, řekne Neměřili jsme.

| F | Téma | Kde je odpověď |
|---|---|---|
| F1 | Porovnáváte se s plazmatem, nebo s výpočtem? Jak přesné je 0,13 mm? | otázka 1 |
| F2 | Rekonstrukce potřebuje proudy v cívkách a model komory, vy máte 24 čidel | F2 níže |
| F3 | Proč je proud lineární? | otázka 4 |
| F4 | Co znamená chyba bodu u limiteru 4,55 mm? | F4 níže |
| F5 | Jak dobrá je rychlost změny polohy? | F5 níže |
| F6 | Co je opačný směr proudu? | N3 |
| F7 | Je šum a posun realistický? | otázka 3 (a N1) |
| F8 | Zánik plazmatu, začátek a konec výboje | N6 |
| F9 | Nový scénář, uzavřená smyčka | otázka 2 |
| F10 | Co kromě času sítě musí řízení zvládnout? | otázka 8 |

### F2. Fyzik
Otázka: Rekonstrukce potřebuje proudy v cívkách pole a model komory. Vy máte jen 24 čidel. Jak je to možné?

Odpovídá A: Nevíme, co všechno rekonstrukce použila. Naše síť dostává jen těch 24 čidel. To, že to funguje, ukazuje, že v těchto 149 výbojích jsou ostatní veličiny téměř určeny čidly, tedy že výboje patří do úzké rodiny scénářů. Prvních pět hlavních složek nese 99,93 procenta rozptylu vstupů, ale základní síť jen s pěti složkami má v pěti dělení chybu osy 2,63 milimetru místo 0,41. Spíš se tedy naučila rodinu tvarů, které tento stroj vytváří, než že by řešila celou úlohu.

### F4. Fyzik
Otázka: Co znamená chyba bodu u limiteru 4,55 milimetru?

Odpovídá A: Bod u limiteru je místo na stěně, kde se plazma dotkne, ne spojitá veličina. Většinou ho trefíme, medián radiální chyby je 0,73 milimetru. Průměr táhnou řádky, kde síť vybere jiné místo dotyku: v jednom procentu řádků je chyba přes 77 milimetrů, nejhorší řádek má 357. Vzdálenost plazmatu od stěny, na které řízení záleží, jsme neměřili.

### F5. Fyzik
Otázka: Pro svislou stabilizaci potřebuji rychlost změny polohy. Jak dobrá je?

Odpovídá B: Rychlost změny jsme neměřili. Máme jen krok chyby mezi sousedními řádky. U základní sítě na čistých vstupech je ve svislé ose 1,46 milimetru, zatímco skutečná osa se mezi řádky posune o 2,53; v radiální ose je to 0,45 proti 2,5. Na zašuměných vstupech je krok chyby sítě naučené na čistých datech 8,4krát větší než pohyb osy v radiálním směru a 3,1krát ve svislém, po učení se šumem 1,7 a 1,4krát. Výstup tedy kolísá víc, než se plazma hýbe, a rychlost z něj brát nelze. Časový odstup řádků neznáme.

## Lead notes (English, for the team, not spoken)

### Words and seconds per section

| Section | Start | End | Seconds | Words (space split) | Words, numerals counted twice | Words, numbers written out | Silent seconds | Rate (numerals twice) | Rate (written out) |
|---|---|---|---|---|---|---|---|---|---|
| Snímek 1: Problém | 0:00 | 0:38 | 38 | 65 | 65 | 65 | 0 | 1.71 | 1.71 |
| Snímek 2: Data | 0:38 | 1:06 | 28 | 45 | 48 | 46 | 0 | 1.71 | 1.64 |
| Snímek 3: Metoda | 1:06 | 1:26 | 20 | 29 | 31 | 31 | 0 | 1.55 | 1.55 |
| Snímek 4: Výsledky | 1:26 | 2:29 | 63 | 90 | 99 | 110 | 0 | 1.57 | 1.75 |
| Živá ukázka, mezi snímkem 4 a 5 | 2:29 | 3:49 | 80 | 104 | 107 | 108 | 15 | 1.65 | 1.66 |
| Snímek 5: Rychlost, verdikt pro řízení | 3:49 | 4:29 | 40 | 56 | 59 | 65 | 0 | 1.48 | 1.62 |
| Snímek 6: Meze | 4:29 | 5:03 | 34 | 55 | 60 | 66 | 0 | 1.76 | 1.94 |
| Snímek 7: Co model neumí | 5:03 | 6:17 | 74 | 104 | 113 | 121 | 0 | 1.53 | 1.64 |
| Snímek 8: Závěr | 6:17 | 7:00 | 43 | 66 | 71 | 82 | 0 | 1.65 | 1.91 |
| Total | 0:00 | 7:00 | 420 | 614 | 653 | 694 | 15 | 1.61 | 1.71 |

Counting (same method as before, small parser of the five-column rows that `build_deck.py` reads, silent "ticho" rows left out): words split on spaces; a token with a digit counts twice; "numbers written out" counts the Czech words a speaker really says (rough rule: "0,0145" is 6 words, "4,55" is 4, "119" is 2). The jury hears every digit, so the last column is the honest planning figure. The counting script reproduces the previous version's 727 written-out words (the old table said 730), so the numbers are comparable. The Lead's edits H1 to H3 (commit 2fb3f86) had raised the count to 789, 7:33 at 1.8 words per second; this pass brought it to 694 by cutting the sentences listed in the paragraph under the overview table.

Time estimate from the written-out count (694 words, 405 s of speech plus 15 s of silence in the demo): at 1.6 words per second 7:28, at 1.7 words per second 7:03, at 1.8 words per second 6:40. **So the script fits 7:00 at about 1.7 words per second and is about 28 s over at the slow end (1.6).** Sections above 1.85 words per second (written out) are slide 6 (1.94) and slide 8 (1.91); slide 4 is 1.84 after the cuts. This is an estimate; no stopwatch reading exists: read the whole script aloud once and write the real times into `rehearsal-notes.md`.

If the stopwatch says over, cut in this order (written-out words saved): the sentence "Platí jen pro jeden tokamak" at 6:11 (5; the slide text keeps it), row 4:01 on the selected model (13, the tile keeps 0,027), the camera (hidden, no seconds). Already cut in this pass: the length of the discharge 150 to 200 ms at 0:09 (it is in Q8), the 42 972 at 0:38, the p99 clause at 3:49, "Zadání chce jednotky až desítky milisekund" at 4:10 (slide and Q8), the 2,64 and 2,22 row at 5:19 (Q3), the 135 of 149 at 3:31, and the Ampère sentence at 2:04 (Q4). Do not cut the caveat lines: the second sentence of 4:10, 4:29 (last sentence), 5:23 and 6:38.

### What changed, finding by finding

| Finding | Fix in this file |
|---|---|
| H1 shipped model, speed and demo | Two latencies, always named: basic network 0,0145 ms (Apple M5), selected model about 0,03 ms, median 0,027 ms limited and 0,015 ms diverted (`results/ipp1-latency-shipped.md`, review 3 X1; the old 0,18 ms is gone). The slogan stays "desetiny milimetru za setiny milisekundy" (review 3 X1; the review 2 change to "desetiny" is withdrawn). The demo no longer says the viewer latency (row 3:08 cut). (Superseded by `docs/demo-facts.md`: the viewer now plays the selected model; the 2:29 row says so.) |
| H2 favourable protocol, "nikdo neviděl" | Slide 4 gives three protocols (30 set aside 0,13; cross-validation on 119 0,23; newer ids 0,40). "Zamčené" and "nikdo neviděl" are gone. Review 3: the spoken line 1:33 said "před finálním výběrem" and the audience hears "held out from design"; now it says "před posledním výběrem modelu; náměty na úpravy ale vznikly na všech 149". Design on all 149 discharges is also answered in N2. |
| H3 script against screen, slides 4 to 7 | Rows rewritten to the numbers on the screen: 0,133 / 0,307, 4,55 / 10,6, 0,035 / 1,2 (slide 4); two speeds (slide 5); 4,55 and 8,35, chart marked as basic network (slide 6; review 3: 77,5 and 92,2 are the p99 of `ipp1-final.md` (rows 128 and 129), so the clause says "v jednom procentu řádků je chyba přes 77 a přes 92", not "až 78 a 92", which read as a maximum; the worst rows are 357 and 485 mm and stay on the screen); learning-curve wording of `claims-corrections.md` section 10 (slide 7). "Cívky nesou skoro všechno", "rychlost nebude překážkou", 0,029, 0,24 ms and 0,032 ms are removed. |
| H4 slide 13 against the speaker | One sentence for both: leaving out a family raised the error at most threefold; the 18 really unusual discharges were never held out alone. |
| H5 noise-free headline | Slide 7 gives the noisy value (axis 2,38 mm, `base_aug`, 30 set aside) and the close (6:38, review 3) says axis units of millimetres, limiter point tens of millimetres, plasma current 4,65 kA, all on noisy inputs (`base_aug`, 30 set aside: 2,38, 25,8 and 38,9 mm, 4,65 kA); 4,03 kA (ridge of `cand_aug`) was not run as one recipe and is not spoken. |
| M1 current tile | Spoken as "lineární model; síť měla 1,2"; not counted as a gain of the network. |
| M2 camera | Hidden backup, no seconds, 20 s line, title 1,3 až 13krát, "malá síť" wording. |
| M3 labelled noise numbers | Protocol said with every number; the 2,33 bar is not spoken and is deleted from the slide (deck-fixes). |
| M4 stale answers | Q4, Q5, Q6, Q8 rewritten, plus Q2, Q3, Q7, Q10 refreshed; N2, N4, N7 give the sources. Review 3: Q5 uses the seed spread of `ipp1-final-seeds.md` (0,133 SD 0,006 and 0,289 SD 0,011) instead of "0,12" (in no file); Q6 says trees were tried for the limiter point (`ipp1-improve.md:37-40`) and the noise line is "10 až 15 procent" (`ipp1-inputs-controls.md`); Q8 and N5 give the measured speed; Q9 lost the COMPASS Upgrade sentence (no source in the repository). |
| M5 demo facts | Frame count and "5,7 mm" removed; the demo numbers now come from `docs/demo-facts.md`; 3:00 now says what the chart shows for one discharge (still unchecked, to be verified in the rehearsal); Q10 has the same fallback as 3:12 (review 3). 128 of 149 (85,9 percent) is verified in `results/ipp1-claim-support.md`. |
| M6 demo single point of failure | Backup section now says: key H opens the hidden slide and works in PowerPoint only (review 3), record the 60 s clip, copy the viewer to the second laptop. Still to do by a person. |
| M7 nobody read it aloud | Recounted after review 3 (table above): written-out count 730 words, 7:24 at a normal pace, 7:01 only at 1.8 words per second. Cut already: demo speed sentence, "Typický výboj sedí", "Zbývá napojení", "U každého čísla řeknu". Emergency cuts in the section above. GPU and second computer lines are gone. No stopwatch reading yet. |
| X1 stale latency lines (review 3) | 4:02, 6:27, the main sentence of slide 5, Q8, N5, Lead notes: measured numbers; slogan "setiny"; the 30 s version says "setiny milisekundy". `[[odezva vybraného modelu]]` is gone from this file. |
| X3 two meanings of 119 | 5:38 says "se všemi učícími výboji, 119 v každém dělení"; the file header explains both meanings. |
| X4 budget attribution | 4:13 and Q8 say "zadání chce jednotky až desítky milisekund, my počítáme s rozpočtem jedné až deseti"; the speech rules say the budget is ours. |
| L1 jitter | Not spoken any more; the footnote on slide 12 keeps "0,96 až 1,07 (13 veličin), na čistých vstupech" and "1,7 a 1,65krát". |
| L4 jargon | "zamčených" gone; "p99" is said as "devadesát devět procent odhadů je rychlejších"; "vybraný model" is explained on slide 3. |
| L5 how many inputs | "Samotné cívky stačí na skoro stejnou souhrnnou chybu, osm nejlepších už ne." |
| Physics review H1 (labels are the institute's reconstruction) | H1 spoken replacements were already in; this pass finished the leftovers: header, "Jak je to postavené", slogan, speech rules (no "přesnost", "skutečný", "předpověď"), Q1 now says "podle toho, co víme" (the sentence "podle zadání" is not in any file), screen column of 2:42 (viewer toggles to be renamed, deck-fixes), slide 8 main sentence and tile, 30 and 60 second versions. Remaining old words only in the jury's own questions (Q1, N1, N4). |
| Physics review H2 (points, not a boundary) | 1:26 says axis, lower X point, strike points on the divertor plates and "Celý obrys neodhadujeme"; 2:29 says outline is the institute's reconstruction; main sentence of the demo; N11 follows `docs/REHEARSAL.md` (the 15 supplementary columns are predicted by the basic network only). Glossary line for Dotykový bod: lane K (deck-fixes). |
| Physics review H3 (opening) | Already applied by the Lead. This pass cut the 150 to 200 ms sentence from the stage (the time column is relative and 439 rows at 0,6 ms would be 263 ms, M3; it stays in Q8 as the organizers' statement), kept the instability claim (ÚFP to confirm, deck-fixes questions) and shortened the question so slide 1 fits 38 s. Picture 04-wall-damage.png: deck-fixes slide 1. |
| Physics review H4 (real time) | 4:10 now lists what is not tested: acquisition and integration, how the signals look in operation, closed loop, real-time system; Q8 adds the derivative, the relative time and the 0,65 and 21 ms spikes; slide 8 says the chain from the sensors and a closed loop test are missing. |
| Physics review H5 (noise) | 5:03 says the weakness is robustness to sensor faults, that the noise is the organizers' and the drift is ours; Q3 gives the standard deviation wording (not "rozptyl"), says the ratio hints at proportional noise (inference) and that real integrator drift grows with absolute time; calibration error and a dead sensor were not tested. |
| Physics review H6 (what the inputs lack) | Slide 2 says the net gets no coil currents and no vessel model; Q2 says the net learned the family of shapes; new F2 gives the 99,93 percent against 2,63 mm and "nevíme, co rekonstrukce použila". |
| Physics review H7 (unsupported claims) | N13 (errors not placed at the transition, only the 49 and 51 percent split), N6 (disruptions not evaluated), Q8 (0,6 ms removed), Q9 (no source needed: the sentence about the institute's plans is no longer in the file). |
| Physics review M1, M2 | Q4 gives Ampère and says the current is probably derived from the same signals (inference, not verified); N3 gives the sign convention as unknown, 16 of 149 discharges, 2 of 30 set aside. The Ampère sentence was cut from the stage at 2:04 for time. |
| Physics review M3 | "0,6 ms" is gone from Q8 and N8; windows are rows, not milliseconds. The question for the organizers is in deck-fixes. |
| Physics review M4, M5, M6, M7 | N13 and Q&A: errors on X and strike points are scored on the true flag; 4:29 says what the limiter point is, median 0,73, mean 4,55 pulled by other contact points, the 1 percent tail, and that the distance from the wall was not measured; 4:51 says the cause is unknown (the hypothesis about the weaker reconstruction at the ends is only in N6); F5 gives the error step and says the derivative was not measured. |
| Physics review M8, M9, L1 to L6 | Glossary lines and the formulas of kappa and delta: deck-fixes, For lane K and the questions for the organizers. "Odhad" instead of "předpověď" in N11 and the speech rules. L3 in Q9, L4 in Q7 (axis standard deviation about 8 mm), L5 in Q1, L6: "neshoda pěti sítí" stays in Q10. L2 ("nejstarší výboje") needs the organizers' answer on the discharge ids; the 3:31 line stays as measured. |

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
| Axis spread | R 8,02 mm, Z 13,74 mm (standard deviation over rows) | `results/ipp1-data-checks.md` |
| Plasma current and Ampère | ridge R2 0,9999998; 0,0347 kA against 1,20 kA; 0,0347 over 114,2 kA = 0,03 percent | `results/ipp1-baseline.json`, `results/ipp1-final.md`, `results/ipp1-data-checks.md` |
| Five principal components | 99,93 percent of the input variance; axis R 2,63 mm against 0,41 | `results/ipp1-claim-support.md`, `results/ipp1-data-checks.md` |
| Limiter point R, 30 set aside, selected model | MAE 4,55; median 0,733; p95 17,2; p99 77,5; max 357 mm. Z: 8,35; 2,96; p99 92,2; max 485 | `results/ipp1-final.md` (rows 128 and 129) |
| Error step (derivative proxy), basic network | clean: R 0,451 against truth step 2,5 mm, Z 1,46 against 2,53; noisy plain network ratio 8,40 (R) and 3,14 (Z); noise-trained 1,74 and 1,39 | `results/ipp1-time.md` |
| Polarity | 16 of 149 discharges positive (7,4 percent of rows); 2 of 30 set aside (591 of 8 761 rows); axis R 0,454 (positive) against 0,11 (negative); canonicalisation +64 percent for positive, 20 percent worse for negative; mean gap 2,00 to 0,13 SD | `results/ipp1-distribution.md`, `results/ipp1-final.md`, `results/ipp1-signcanon.md` |
| Worst single row, basic network, five folds | Z axis 284 mm against a spread of 13,7 mm | `results/ipp1-distribution.md`, `results/ipp1-data-checks.md` |
| Discharge length in rows | 17 to 439, median 293 | `results/ipp1-data.md` |
| Latency spikes, earlier loaded run | p99 0,65 ms, max 21 ms (single CPU sample, load 16) | `results/ipp1-latency.md` |
| Share of errors split by configuration (`is_limited`) | 49,3 percent of the squared error on limited rows, 50,7 percent on diverted | `results/ipp1-distribution.md` |
| Camera | 5 folds, 78 discharges, 48x64; axis R 1,79 (grey 1,70) against 0,377; 1,3 to 13 times; fused 1,21 against 0,24 on 2 folds | `results/cloud-camera-main.md`, `results/cloud-camera-findings.md`, `results/ipp1-camera-local-findings.md` |

The demo now plays the selected model on the 30 set-aside discharges (viewer e50b1ee); typical discharge 85, rough end discharge 147; numbers in `docs/demo-facts.md`. Discharges 0, 11 and 123 belong to the development set.

### Still pending (needs a person or a machine)

* Latency of the selected model: done (`results/ipp1-latency-shipped.md`, busy laptop, random weights, numpy). Caveats a physicist can raise, not closed: no file checks that the numpy path reproduces the trained network (a 100-row comparison with `predict()` would close it); the noise-trained network needed for noisy inputs was not timed (it has the size of the basic network); the machine was not idle. `[[odezva vybraného modelu]]` is reserved and unused.
* Demo numbers: done, taken from the viewer by bladed-85 (`docs/demo-facts.md`); one human replay of discharges 85 and 147 the day before is still advised.
* One timed read-aloud with a stopwatch; update `rehearsal-notes.md`.
* The 60 s screen recording and the copy of the viewer on the second laptop (M6).
* `build_deck.py` has hard-coded split times for speaker notes (`0:21`, `1:37`, `2:14`); with the timing of this file the last two become `1:33` and `2:17`, see `docs/deck-fixes.md` item 0.3 and the section For lane K.
* Any change of the shipped recipe after 21:30 Friday invalidates the 0,13 and 0,23 numbers.
* Physics wording that needs a person: the viewer toggles Skutečnost and Předpověď must become Rekonstrukce ústavu and Odhad sítě (viewer owner, `docs/deck-fixes.md`); ÚFP should confirm the vertical instability sentence at 0:00; the replies of the organizers to the list in `docs/deck-fixes.md` (labels, sign, time axis, formulas, disruptions) decide whether Q1, N3 and N6 can say more. The answers F1 to F10 are written from `results/` only and say Neměřili jsme where no file measured.
* Timing: 694 written-out words, 7:03 at 1,7 words per second, 7:28 at 1,6. One stopwatch reading is still missing.
