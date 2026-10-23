# Osnova prezentace: tvar plazmatu z magnetických měření

Celkem 7 minut (420 sekund), 8 snímků. U každého snímku je čas a jedna věta, kterou musí říct.
Čísla pocházejí jen ze složky results. Kde číslo ještě neexistuje, stojí DOPLNIT.
Zdroje čísel: soubory ipp1 baseline, ipp1 inputs, ipp1 time a ipp1 latency ve složce results.

## Snímek 1: Problém (50 s)

Věta: Plazma v tokamaku COMPASS se musí držet daleko od stěny během milisekund, ale klasický výpočet jeho tvaru trvá minuty.

* Zadání žádá reakci v řádu jednotek až desítek milisekund (podle zadání úlohy).
* Klasická rekonstrukce rovnováhy trvá minuty, tedy o několik řádů déle.
* Naše otázka: dokáže malý model odhadnout tvar plazmatu z magnetických měření dost přesně a dost rychle?

## Snímek 2: Data (30 s)

Věta: Máme 42 972 řádků z 149 výbojů, na každém řádku 24 magnetických měření a 16 hledaných veličin popisujících tvar.

* Vstupy: 24 magnetických čidel, dvě skupiny: 16 cívek IPR a 8 smyček toku FL.
* Výstupy: poloha osy, bod X, dotykové body na divertoru, protažení, trojúhelníkovost, proud plazmatem, bod u limiteru.
* Data jsou důvěrná, proto na snímku nejsou žádné surové hodnoty, jen souhrny.
* Dělíme po celých výbojích, nikdy po řádcích, jinak by se model učil na tom, co testuje.

## Snímek 3: Metoda (25 s)

Věta: Použili jsme malou neuronovou síť o 107 152 parametrech a porovnali ji s lineárním modelem.

* Srovnání: lineární model (hřebenová regrese) proti malé neuronové síti.
* Ověření: pětkrát jiné rozdělení výbojů na učení a test.
* Dále: kolik vstupů opravdu potřebujeme, jak stabilní je výstup v čase, jak rychlá je odpověď.
* Kamerový model: DOPLNIT (zatím neměřeno).

## Snímek 4: Výsledky (45 s)

Věta: Na náhodně vybraných nových výbojích síť trefí osu, bod X a dotykové body s chybou 0,06 až 0,4 mm, což je mnohem lépe než lineární model; jen pro proud plazmatem je lepší lineární model.

* Osa plazmatu: chyba 0,38 mm (radiální) a 0,39 mm (svislá); lineární model 2,4 a 2,66 mm.
* Bod X: 0,20 mm a 0,20 mm. Dotykové body: od 0,0552 do 0,265 mm.
* Proud plazmatem: lineární model 0,035 kA, síť 1,49 kA, takže pro proud je lepší lineární model. Protažení: chyba sítě 0,00569.
* Zda je plazma opřeno o limiter, určí síť správně v 99,3 % případů.
* Méně vstupů: se všemi 24 vstupy je souhrnná relativní chyba 0,063, s nejlepšími 12 je 0,077, s nejlepšími 8 je 0,094.
* Samotné cívky IPR (16 vstupů) dávají 0,066, samotné smyčky toku (8 vstupů) jen 0,285, tedy cívky stačí téměř samy. Pořadí vstupů je důležitost pro naučenou síť, ne obsah informace.
* Obrázek: graf chyby podle počtu vstupů (soubor ipp1 inputs ve složce results).

## Živá ukázka mezi snímkem 4 a 5 (95 s)

Věta: V prohlížeči vidíte skutečný a odhadnutý tvar plazmatu vedle sebe a chybu v čase, jednu typickou a jednu špatnou ukázku.

* Posuvník času, skutečná a odhadnutá hranice, tabulka chyb. Podrobný scénář je v souboru pitch script.

## Snímek 5: Verdikt pro řízení v reálném čase (35 s)

Věta: Výpočet sítě trvá asi 0,0145 ms na procesoru, tedy mnohonásobně méně než jednotky milisekund, které zadání žádá, ale sběr signálů a běh na systému reálného času jsme neověřovali.

* Procesor, jeden vzorek: medián 0,0145 ms, 99 % měření pod 0,0288 ms (měřeno na počítači vedoucího týmu; na jiném procesoru vychází čas vyšší, proto u čísla vždy říkáme, na jakém počítači bylo měřeno).
* Grafická karta Apple, jeden vzorek: medián 0,2405 ms, pomalejší než procesor, protože model je malý.
* Verdikt: výpočet sítě není překážkou. Neověřeno: sběr signálů z čidel, běh na systému reálného času a přesnost na skutečně zašuměných signálech (síť učená na čistých datech na šumu selže, viz snímek 7).

## Snímek 6: Meze (30 s)

Věta: Nejhůř se odhaduje bod u limiteru, kde chyba dosahuje 10,7 mm a 22,2 mm, a na konci výboje chyby rostou u všech veličin.

* Bod u limiteru: radiální chyba 10,7 mm, svislá 22,2 mm, řádově hůř než ostatní veličiny.
* Na konci výboje chyby rostou u všech sledovaných veličin, například osa 0,9 mm proti 0,24 mm uprostřed. Na začátku roste jen chyba polohy osy.
* Na čistých vstupech kolísá výstup mezi sousedními časy stejně jako pravda (poměr 0,97 až 1,07 u sedmi veličin; bod u limiteru mezi nimi není).
* S menším počtem vstupů přesnost klesá: se 4 vstupy je souhrnná chyba 0,204.

## Snímek 7: Co model neumí (60 s)

Věta: Model je křehký vůči šumu, potřebuje dost výbojů a nezná neobvyklý tvar ani řízení plazmatu.

* Šum: osa má chybu 0,38 mm na čistých datech, ale 10,15 mm na datech s šumem; učení na zašuměných datech to srazí na 2,64 mm.
* Množství dat: od 30 výbojů se chyba osy s každým zdvojením zhruba půlí (1,47; 0,83; 0,38 mm) ale učili jsme vždy 60 epoch, takže část zlepšení tvoří víc kroků učení.
* Neobvyklý tvar, který poruší vztahy mezi veličinami: DOPLNIT (zatím neměřeno).
* Ověřeno jen na jednom tokamaku. Model odhaduje jen tvar a řízení plazmatu samo nenahrazuje.

## Snímek 8: Závěr, jedno číslo (50 s)

Věta: Jeden odhad tvaru plazmatu trvá 0,0145 ms na procesoru a chyba osy je desetiny milimetru, ale model ještě není připraven pro řízení.

* Velké číslo 0,0145 ms, vedle něj desetiny milimetru u osy, bodu X a dotykových bodů.
* Upřímně: slabý bod u limiteru, nezná neobvyklé tvary a šum mu vadí, pokud se na něj neučí.
* Zbývá ověřit napojení na řídicí systém, získat víc výbojů a přidat odolnost proti šumu.

## Součet času

Podle rozhodnutí vedoucího (RP 11) platí časy ze souboru pitch script: 50 + 30 + 25 + 45 + 95 (ukázka) + 35 + 30 + 60 + 50 = 420 sekund, tedy 7 minut.

## Chybějící čísla (DOPLNIT)

* Výsledky kamerového modelu a srovnání s magnetickým.
* Chování pro neobvyklý tvar.
* Kdo potvrdí napojení na řídicí systém.

## Do zálohy: dotazy poroty (neříká se nahlas)

* Posun čidel je náš vlastní model, ne měřený posun skutečných čidel. Posun čidel se směrodatnou odchylkou sklonu 0,3 přidá k chybě osy asi 1 mm (model učený na šumu).
* Učení na zašuměných datech zhorší čistá data: chyba osy 2,22 mm místo 0,38 mm.
* Tři po sobě jdoucí časy zlepšují zašuměný vstup (osa 2,64 na 2,33 mm), ale na čistém vstupu osu zhoršují (0,38 na 0,57 mm).
* Naměřeno pro jednu inicializaci a jednu realizaci šumu na každé rozdělení, rozdíly pár procent nejsou prokázané.
