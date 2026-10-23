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

Věta: Použili jsme malou neuronovou síť o 107 152 parametrech, porovnali ji s lineárním modelem a každý výsledek ověřujeme pětkrát na náhodně vybraných výbojích, které síť při učení neviděla.

* Srovnání: lineární model (hřebenová regrese) proti malé neuronové síti.
* Dále: kolik vstupů opravdu potřebujeme, jak stabilní je výstup v čase, jak rychlá je odpověď, jak síť snáší šum.
* Pro čisté vstupy jsme pak zkusili vylepšený model: síť s rozdíly sousedních cívek, lineární model pro proud a zvláštní síť pro bod u limiteru.
* Kamera: malá konvoluční síť na snímcích, samotná je 6 až 8krát horší než magnetická měření na ose (1,54 mm proti 0,24 mm, jen na dvou z pěti dělení, proto srovnáváme jen uvnitř téže tabulky). Černobílý snímek nic nezmění (1,53 mm). Proud plazmatem z kamery určit nejde (chyba 18 kA).

## Snímek 4: Výsledky (45 s)

Věta: Síť trefí osu, bod X a dotykové body s průměrnou chybou 0,06 až 0,4 mm, u osy více než šestkrát lépe než lineární model; jen u proudu plazmatem je lineární model lepší.

* Osa plazmatu: průměrná chyba 0,38 mm (radiální) a 0,39 mm (svislá); lineární model 2,4 a 2,66 mm.
* Průměr skrývá chvosty: medián radiální osy je 0,153 mm, 99 % řádků je pod 3,74 mm, nejhorší řádek má 64 mm, hlavně na konci výboje. Limitované plazma je asi 2,3krát horší než divertorové.
* Bod X: 0,20 mm a 0,20 mm. Dotykové body: od 0,0552 do 0,265 mm.
* Proud plazmatem určí lineární model s chybou 0,035 kA, síť s chybou 1,49 kA, proto pro proud použijeme lineární model. Protažení: chyba sítě 0,00569.
* Zda je plazma opřeno o limiter, určí síť správně v 99,3 % případů.
* Méně vstupů: se všemi 24 vstupy je souhrnná relativní chyba 0,063, s nejlepšími 12 je 0,077, s nejlepšími 8 je 0,094.
* Samotných 16 cívek IPR dává souhrnnou chybu 0,066, samotných 8 smyček toku 0,285, tedy 4,3krát horší. Pořadí vstupů je důležitost pro naučenou síť, ne obsah informace, proto neříkáme, které čidlo je nejdůležitější.
* Vylepšený model pro čisté vstupy, závěrečný test na 30 výbojích, které se při vývoji nepoužily: chyba bodu u limiteru 4,55 mm místo 10,6 (radiálně) a 8,35 mm místo 22,5 (svisle), proud 0,035 kA místo 1,20 kA. Několik jednotlivých řádků je ale horších, takže říkáme "lepší v průměru a ve většině řádků", ne "všude".
* Obrázek: graf chyby podle počtu vstupů (soubor ipp1 inputs ve složce results).

## Živá ukázka mezi snímkem 4 a 5 (95 s)

Věta: V prohlížeči vidíte skutečný a odhadnutý tvar plazmatu vedle sebe a chybu v čase, jednu typickou a jednu špatnou ukázku.

* Posuvník času, skutečná a odhadnutá hranice, tabulka chyb. Podrobný scénář je v souboru pitch script.

## Snímek 5: Verdikt pro řízení v reálném čase (35 s)

Věta: Výpočet sítě rychlosti nebrání: medián je 0,0145 ms na procesoru Apple M5, rozpočet je 1 až 10 ms; ověřili jsme ale jen výpočet samotné sítě.

* Procesor Apple M5, jeden vzorek: medián 0,0145 ms, 99 % měření pod 0,0209 ms. Při dřívějším měření na silněji zatíženém stroji vyšel medián 0,0188 ms a 99 % měření pod 0,118 ms, takže čas závisí na zatížení.
* Celý odhad od surových čísel na vstupu po čísla na výstupu: medián 0,0140 ms. Nejvyšší hodnoty se na systému bez reálného času ojediněle objeví až v milisekundách, to není horní mez.
* Grafická karta pro jeden odhad: medián 0,27 ms, s přenosem dat 0,49 ms, pomalejší než procesor, protože model je malý.
* Neověřili jsme: sběr a integraci signálů z cívek, nejhorší dobu na systému reálného času a přesnost na skutečně zašuměných signálech. Síť naučená na čistých datech na šumu selže, síť naučená na šumu dává chybu osy 2,64 mm.
* U každého času říkáme, na jakém procesoru byl měřen.

## Snímek 6: Meze (30 s)

Věta: Nejhůř se odhaduje bod u limiteru, kde chyba dosahuje 10,7 mm a 22,2 mm, a chyby rostou hlavně na konci výboje.

* Bod u limiteru: radiální chyba 10,7 mm, svislá 22,2 mm, řádově hůř než ostatní veličiny.
* Chyby rostou hlavně na konci výboje, 1,6 až 3,7krát oproti středu: osa má na konci 0,9 mm, uprostřed 0,24 mm. Na začátku roste jen chyba polohy osy (radiální 2,5krát, svislá 1,5krát), bod X a dotykové body se na začátku výboje nevyskytují.
* Na čistých vstupech kolísá výstup stejně jako skutečnost, poměr je 0,97 až 1,07 u sedmi veličin. Na zašuměných vstupech kolísá výstup sítě naučené na čistých datech 8,4krát (osa R) a 3,3krát (osa Z) víc než skutečnost, po učení se šumem a posunem 1,7krát (osa R) a 1,65krát (osa Z). Nikdy neříkáme jen 0,97.
* Čísla výbojů jsou zřejmě seřazena podle času, což jsme s organizátory neověřili. Když zkoušíme na souvislých blocích čísel, je chyba 1,5 až 2,9krát větší (osa R 1,23 mm místo 0,448 mm), z části i proto, že je méně učících výbojů.
* S menším počtem vstupů přesnost klesá: se 4 vstupy je souhrnná chyba 0,204.

## Snímek 7: Co model neumí (60 s)

Věta: Model je křehký vůči šumu, potřebuje dost výbojů a nezná neobvyklý tvar ani řízení plazmatu.

* Šum: osa má chybu 0,38 mm na čistých datech, ale 10,15 mm na datech s šumem; učení na zašuměných datech to srazí na 2,64 mm. Vylepšený model pro čisté vstupy na šumu selže úplně, proto pro zašuměné vstupy použijeme síť učenou se šumem.
* Množství dat: s 30 výboji je chyba osy 1,47 mm (radiální) a 0,95 mm (svislá). Od 30 do 119 výbojů klesá zhruba na polovinu při zdvojnásobení, ale s pevným počtem 60 epoch, takže část zlepšení tvoří víc kroků učení.
* Neobvyklý tvar, který poruší vztahy mezi veličinami: DOPLNIT (zatím neměřeno).
* Kamera: model naučený na nepohnutých snímcích je křehký, posun o 4 pixely ztrojnásobí chybu osy (z 1,54 na 4,95 mm); učení s posuny a otočením to srovná na asi 2 mm za cenu horší přesnosti na nepohnutých snímcích. Kamera a magnetická měření dohromady magnetickou síť nepřekonaly (1,21 mm proti 0,24 mm). Měřeno jen na dvou z pěti dělení.
* Ověřeno jen na jednom tokamaku. Model odhaduje jen tvar a řízení plazmatu samo nenahrazuje.

## Snímek 8: Závěr, jedno číslo (50 s)

Věta: Výpočet sítě trvá 0,0145 ms na procesoru Apple M5 a chyba osy je desetiny milimetru, ale model ještě není připraven pro řízení.

* Velké číslo 0,0145 ms (výpočet sítě na procesoru Apple M5, ne celý řídicí systém), vedle něj desetiny milimetru u osy, bodu X a dotykových bodů.
* Upřímně: slabý bod u limiteru, nezná neobvyklé tvary a šum mu vadí, pokud se na něj neučí.
* Sběr signálů a napojení na řídicí systém jsme nezkoušeli. Zbývá ověřit napojení na řídicí systém, získat víc výbojů a přidat odolnost proti šumu.

## Součet času

Podle rozhodnutí vedoucího (RP 11) platí časy ze souboru pitch script: 50 + 30 + 25 + 45 + 95 (ukázka) + 35 + 30 + 60 + 50 = 420 sekund, tedy 7 minut.

## Chybějící čísla (DOPLNIT)

* Kamera: zbylá tři dělení z pěti a nezávislý kamerový model z cloudu.
* Údaj, že výboj trvá 150 až 200 ms, není ve složce results.
* Chování pro neobvyklý tvar.

## Do zálohy: dotazy poroty (neříká se nahlas)

* Soubor se šumem od organizátorů obsahuje jen bílý šum a žádný měřitelný posun. Posun v čase jsme zkoušeli jen na vlastních, uměle vytvořených datech: posun se směrodatnou odchylkou sklonu 0,3 přidá k chybě osy asi 1 mm u sítě naučené na šumu.
* Učení na zašuměných datech zhorší čistá data: chyba osy 2,22 mm místo 0,38 mm.
* Tři po sobě jdoucí časy zlepšují zašuměný vstup (osa 2,64 na 2,33 mm), ale na čistém vstupu osu zhoršují (0,38 na 0,57 mm).
* Naměřeno pro jednu inicializaci a jednu realizaci šumu na každé rozdělení, rozdíly pár procent nejsou prokázané.
* Rozptyl veličin je malý jen u osy, bodu X a dotykových bodů, od 2,4 do 13,7 mm; u bodu limiteru je 90 a 153 mm, proto chyby uvádíme v mm i vůči rozptylu. Čísla pro rozptyl a pro rozdělení po souvislých blocích pocházejí z kontroly mimo složku results, takže je před použitím na snímku DOPLNIT do results.
* Pozor, neříkat: "pět složek nese 99,9 % informace". Správně je rozptyl, ne informace; model na pěti složkách má radiální chybu osy 2,6 mm místo 0,38 mm (z kontroly mimo složku results, DOPLNIT do results).
