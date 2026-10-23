# Osnova prezentace: tvar plazmatu z magnetických měření

Celkem 7 minut (420 sekund), 8 snímků. U každého snímku je čas a jedna věta, kterou musí říct.
Čísla pocházejí jen ze složky results. Kde číslo ještě neexistuje, stojí DOPLNIT.
Zdroje čísel: soubory ipp1 baseline, ipp1 inputs, ipp1 time a ipp1 latency ve složce results.

## Snímek 1: Problém (50 s)

Věta: Plazma v tokamaku COMPASS se musí držet daleko od stěny během milisekund, ale klasický výpočet jeho tvaru trvá minuty.

* Zadání žádá reakci v řádu jednotek až desítek milisekund (podle zadání úlohy).
* Klasická rekonstrukce rovnováhy trvá minuty, tedy o několik řádů déle.
* Naše otázka: dokáže malý model odhadnout tvar plazmatu z magnetických měření dost přesně a dost rychle?

## Snímek 2: Data (50 s)

Věta: Máme 42 972 řádků z 149 výbojů, na každém řádku 24 magnetických měření a 16 hledaných veličin popisujících tvar.

* Vstupy: 24 magnetických čidel, dvě skupiny: 16 cívek IPR a 8 smyček toku FL.
* Výstupy: poloha osy, bod X, dotykové body na divertoru, protažení, trojúhelníkovost, proud plazmatem, bod u limiteru.
* Data jsou důvěrná, proto na snímku nejsou žádné surové hodnoty, jen souhrny.
* Dělíme po celých výbojích, nikdy po řádcích, jinak by se model učil na tom, co testuje.

## Snímek 3: Metoda (50 s)

Věta: Použili jsme malou neuronovou síť o 107 152 parametrech a porovnali ji s lineárním modelem.

* Srovnání: lineární model (hřebenová regrese) proti malé neuronové síti.
* Ověření: pětkrát jiné rozdělení výbojů na učení a test.
* Dále: kolik vstupů opravdu potřebujeme, jak stabilní je výstup v čase, jak rychlá je odpověď.
* Kamerový model: DOPLNIT (zatím neměřeno).

## Snímek 4: Výsledky (80 s)

Věta: Síť trefí osu, bod X a dotykové body s chybou 0,06 až 0,4 mm, což je mnohem lépe než lineární model.

* Osa plazmatu: chyba 0,377 mm (radiální) a 0,391 mm (svislá); lineární model 2,4 a 2,66 mm.
* Bod X: 0,202 mm a 0,195 mm. Dotykové body: od 0,0552 do 0,265 mm.
* Proud plazmatem: chyba 1,49 kA. Protažení: 0,00569.
* Zda je plazma opřeno o limiter, určí síť správně v 99,3 % případů.
* Méně vstupů: se všemi 24 vstupy je souhrnná relativní chyba 0,063, s nejlepšími 12 je 0,077, s nejlepšími 8 je 0,094.
* Samotné cívky IPR (16 vstupů) dávají 0,066, samotné smyčky toku (8 vstupů) jen 0,285, tedy cívky nesou skoro vše.
* Obrázek: graf chyby podle počtu vstupů (soubor ipp1 inputs ve složce results).

## Snímek 5: Verdikt pro řízení v reálném čase (50 s)

Věta: Jeden odhad trvá 0,0145 ms na procesoru, tedy mnohonásobně méně než jednotky milisekund, které zadání žádá.

* Procesor, jeden vzorek: medián 0,0145 ms, nejhorší naměřená hodnota 0,090 ms (měřeno na počítači vedoucího týmu; na druhém počítači při opakování vyšlo 0,032 ms, což je pořád hluboko pod jednou milisekundou).
* Grafická karta Apple, jeden vzorek: medián 0,2405 ms, pomalejší než procesor, protože model je malý.
* Verdikt: rychlost nebude překážkou. Zbývá ověřit napojení na skutečný řídicí systém a spolehlivost výstupu: DOPLNIT, kdo to potvrdí.

## Snímek 6: Meze (50 s)

Věta: Nejhůř se odhaduje bod u limiteru, kde chyba dosahuje 10,7 mm a 22,2 mm, a na začátku a konci výboje chyby rostou.

* Bod u limiteru: radiální chyba 10,7 mm, svislá 22,2 mm, řádově hůř než ostatní veličiny.
* Na začátku a na konci výboje chyby rostou, například osa na konci výboje 0,9 mm proti 0,24 mm uprostřed.
* Výstup mezi sousedními časy nekolísá víc než pravda (poměr kolísání je okolo 1).
* S menším počtem vstupů přesnost klesá: se 4 vstupy je souhrnná chyba 0,204.

## Snímek 7: Co model neumí (60 s)

Věta: Model je křehký vůči šumu, potřebuje dost výbojů a nezná neobvyklý tvar ani řízení plazmatu.

* Šum: osa má chybu 0,38 mm na čistých datech, ale 10,15 mm na datech s šumem; učení na zašuměných datech to srazí na 2,64 mm.
* Množství dat: od 30 výbojů se chyba osy s každým zdvojením zhruba půlí (1,47; 0,83; 0,38 mm) a nepřestala klesat.
* Neobvyklý tvar, který poruší vztahy mezi veličinami: DOPLNIT (zatím neměřeno).
* Ověřeno jen na jednom tokamaku. Model odhaduje jen tvar a řízení plazmatu samo nenahrazuje.

## Snímek 8: Ukázka a závěr (30 s)

Věta: V prohlížeči vidíte skutečný a odhadnutý tvar plazmatu vedle sebe a chybu v čase.

* Krátká ukázka prohlížeče tvaru: posuvník času, skutečná a odhadnutá hranice.
* Závěrečná věta: rychlý model je přesný na většině veličin; zbývá ověřit odolnost a slabá místa.

## Součet času

50 + 50 + 50 + 80 + 50 + 50 + 60 + 30 = 420 sekund, tedy 7 minut.

## Chybějící čísla (DOPLNIT)

* Výsledky kamerového modelu a srovnání s magnetickým.
* Chování pro neobvyklý tvar.
* Kdo potvrdí napojení na řídicí systém.

## Do zálohy: dotazy poroty (neříká se nahlas)

* Posun čidel je náš vlastní model, ne měřený posun skutečných čidel. Posun škodí méně než šum stejné velikosti.
* Učení na zašuměných datech zhorší čistá data: chyba osy 2,22 mm místo 0,38 mm.
* Tři po sobě jdoucí časy zlepšují zašuměný vstup (osa 2,64 na 2,33 mm), ale na čistém vstupu osu zhoršují (0,38 na 0,57 mm).
* Naměřeno pro jednu inicializaci a jednu realizaci šumu na každé rozdělení, rozdíly pár procent nejsou prokázané.
