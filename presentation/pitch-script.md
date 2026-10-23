---
tags:
  - hackathon
---

# Pitch: 7 minut pro porotu

Stav: hotový návrh z pátku 23. října, 17:30. Čísla jsou jen ze složky results a z popisu dat. Co chybí, je označeno DOPLNIT. Pořadí snímků, pojmy a čísla sedí s osnovou `repo/presentation/outline.md` a s decku v `repo/presentation/deck/`. Změněné jsou jen časy a místo živé ukázky, viz část Lead notes na konci.

## Jak je to postavené

* Začátek: problém, který bolí. Plazma se dotkne stěny, výboj trvá jen 150 až 200 milisekund, klasický výpočet tvaru trvá minuty.
* Jádro: živá ukázka v prohlížeči tvaru. Vedle sebe skutečný a odhadnutý tvar plazmatu přes celý výboj, a jeden špatný výboj naschvál.
* Konec: jedno číslo, 0,0145 milisekundy na jeden odhad. K němu upřímná věta, co model neumí.
* Řečníci: A je první řečník (majitel týmu), B je druhý řečník (kolega). B má kratší a čistě popisné části a otázky podnikatelů.
* Porota: fyzici z ÚFP a odborníci na strojové učení. Posuzuje se prezentace a funkčnost, proto ukázka běží živě a čísla říkáme pomalu, jedno po druhém.

## Časový přehled

| Čas | Sek. | Co je na obrazovce | Obrázek | Kdo |
|---|---|---|---|---|
| 0:00 až 0:50 | 50 | Snímek 1: Problém | 04-wall-damage.png, potom 02-minutes-vs-ms.png | A |
| 0:50 až 1:20 | 30 | Snímek 2: Data | 03-coils.png | B |
| 1:20 až 1:45 | 25 | Snímek 3: Metoda | 06-neural-bridge.png | A |
| 1:45 až 2:30 | 45 | Snímek 4: Výsledky | 05-shape-schematic.png | A a B |
| 2:30 až 4:05 | 95 | Živá ukázka, mezi snímkem 4 a 5 | žádný, na obrazovce je prohlížeč tvaru (repo/viewer/index.html) | A, jedna věta B |
| 4:05 až 4:40 | 35 | Snímek 5: Rychlost, verdikt pro řízení | 02-minutes-vs-ms.png (zopakovat jako pozadí) | B |
| 4:40 až 5:10 | 30 | Snímek 6: Meze | žádný obrázek, na snímku je graf chyby osy podle času | A |
| 5:10 až 6:10 | 60 | Snímek 7: Co model neumí | žádný obrázek, na snímku jsou dva grafy (šum, počet výbojů) | B a A |
| 6:10 až 7:00 | 50 | Snímek 8: Závěr, jedno číslo | 07-closing.png | A a B |
| celkem | 420 | 8 snímků a ukázka | | |

## Časovaný scénář

Čas je začátek řádku. Sloupec Co se říká je přesně to, co zazní. Text v závorkách se neříká. Rychlost řeči je asi 2 slova za sekundu, u čísel pomaleji.

### Snímek 1: Problém (0:00 až 0:50, 50 s)

Hlavní věta: Plazma se musí držet daleko od stěny během milisekund, klasický výpočet tvaru trvá minuty.

Obrázek: 04-wall-damage.png, potom 02-minutes-vs-ms.png

| Čas | Sek. | Kdo | Co se říká | Na obrazovce |
|---|---|---|---|---|
| 0:00 | 9 | A | Čeho se bojí každý, kdo provozuje tokamak, ukazuje tahle ilustrace: žhavé plazma se dotkne stěny a stěnu poškodí. | Snímek 1. Obrázek 04-wall-damage.png přes celou plochu. Je to ilustrace, neříkej, že jde o skutečnou fotografii. |
| 0:09 | 6 | A | Celý výboj na tokamaku COMPASS trvá jen 150 až 200 milisekund. | Stále obrázek 04. |
| 0:15 | 9 | A | Aby se to nestalo, musí řídicí systém znát polohu a tvar plazmatu v řádu jednotek až desítek milisekund. | Stále obrázek 04. |
| 0:24 | 5 | A | Klasický výpočet tvaru z magnetických měření ale trvá minuty. | Přepnout na obrázek 02-minutes-vs-ms.png (přesýpací hodiny proti záblesku) a dlaždice minuty a jednotky ms. |
| 0:29 | 4 | A | To je o několik řádů víc, než řízení unese. | Stále obrázek 02. |
| 0:33 | 5 | A | Minuty proti milisekundám. To je propast, kterou chceme překlenout. | Stále obrázek 02. |
| 0:38 | 9 | A | Naše otázka zní: dokáže malá neuronová síť odhadnout tvar plazmatu z magnetických měření dost přesně a dost rychle? | Dole na snímku věta s otázkou. |
| 0:47 | 3 | A | Data vám představí kolega. | Pohled na B, klik na snímek 2. |

### Snímek 2: Data (0:50 až 1:20, 30 s)

Hlavní věta: 42 972 okamžiků ze 149 výbojů, 24 vstupů, 16 veličin, dělení po celých výbojích.

Obrázek: 03-coils.png

| Čas | Sek. | Kdo | Co se říká | Na obrazovce |
|---|---|---|---|---|
| 0:50 | 7 | B | Máme data z tokamaku COMPASS: 42 972 okamžiků ze 149 výbojů. | Snímek 2 (tři dlaždice 24, 16, 149). Obrázek 03-coils.png je schéma, ne skutečný řez. |
| 0:57 | 8 | B | V každém okamžiku máme 24 měření: 16 cívek IPR a 8 smyček toku. Obrázek je jen schéma. | Ukázat na obrázek. Je na něm 16 cívek, smyčky toku na něm nejsou. |
| 1:05 | 7 | B | Z nich má model určit 16 veličin tvaru: osu, bod X, dotykové body, protažení a další. | Dlaždice 16. |
| 1:12 | 8 | B | Dělíme vždy po celých výbojích, jinak by se model testoval na tom, co už viděl. | Spodní věta snímku. |

### Snímek 3: Metoda (1:20 až 1:45, 25 s)

Hlavní věta: Malá neuronová síť o 107 152 parametrech proti lineárnímu modelu, pět rozdělení po výbojích.

Obrázek: 06-neural-bridge.png

| Čas | Sek. | Kdo | Co se říká | Na obrazovce |
|---|---|---|---|---|
| 1:20 | 7 | A | Model je malá neuronová síť: 24 měření na vstupu, 16 veličin najednou na výstupu. | Snímek 3. Obrázek 06-neural-bridge.png ukazuje princip. Teček čidel je na něm 16, skutečných vstupů je 24. |
| 1:27 | 5 | A | Má 107 152 parametrů a porovnáváme ji s lineárním modelem. | Dlaždice 107 152. |
| 1:32 | 7 | A | Každý výsledek ověřujeme pětkrát, vždy na výbojích, které síť při učení neviděla. | Spodní věta snímku. |
| 1:39 | 6 | A | Pak měříme, kolik vstupů potřebuje, jak je rychlá a jak snáší šum. | Spodní věta snímku. |

### Snímek 4: Výsledky (1:45 až 2:30, 45 s)

Hlavní věta: Osa, bod X a dotykové body s chybou 0,06 až 0,4 mm; cívky IPR nesou skoro všechno.

Obrázek: 05-shape-schematic.png

| Čas | Sek. | Kdo | Co se říká | Na obrazovce |
|---|---|---|---|---|
| 1:45 | 9 | A | Na schématu vidíte, co odhadujeme: osu uprostřed, bod X dole a dva dotykové body, kam dopadá okraj plazmatu. | Snímek 4. Obrázek 05-shape-schematic.png asi 9 sekund (osa, bod X, dva dotykové body), pak graf chyb. |
| 1:54 | 8 | A | U osy, bodu X a dotykových bodů je průměrná chyba mezi 0,06 a 0,4 milimetru. | Graf: lineární model proti neuronové síti, šest veličin. |
| 2:02 | 6 | A | Lineární model dělá u osy chybu 2,4 milimetru, tedy více než šestkrát větší. | Ukázat na oranžové a šedé sloupce osy R. |
| 2:08 | 6 | A | Zda plazma leží na limiteru, určí síť správně v 99,3 procentech případů. | Dlaždice 99,3 %. |
| 2:14 | 8 | B | Kolik vstupů potřebujeme? Všech 24 dává souhrnnou chybu 0,063, jen nejlepších 8 dává 0,094. | Ukázat levý graf Kolik vstupů stačí z results/ipp1-inputs.png. V decku snímku 4 zatím chybí, viz Lead notes. Menší číslo je lepší. |
| 2:22 | 8 | B | Samotných 16 cívek IPR dává 0,066, samotné smyčky toku jen 0,285. Cívky tedy nesou skoro všechno. | Stejný graf, vpravo je pořadí důležitosti vstupů. |

### Živá ukázka, mezi snímkem 4 a 5 (2:30 až 4:05, 95 s)

Hlavní věta: Skutečný a odhadnutý tvar plazmatu vedle sebe, chyba v čase, jedna typická a jedna špatná ukázka.

Obrázek: žádný, na obrazovce je prohlížeč tvaru (repo/viewer/index.html)

| Čas | Sek. | Kdo | Co se říká | Na obrazovce |
|---|---|---|---|---|
| 2:30 | 11 | A | Teď to uvidíte naživo. Přepínám do prohlížeče tvaru. Běží bez připojení k internetu a ukazuje jen tvar plazmatu, surová měření cívek ne. | Cmd+Tab do prohlížeče. Okno je předem otevřené na adrese končící #d=123, rychlost 1×, zastaveno. |
| 2:41 | 8 | A | Vlevo je řez plazmatem. Tmavá čára je skutečný tvar, oranžová přerušovaná čára je odhad sítě. | Ukázat na přepínače Skutečnost a Předpověď nahoře. |
| 2:49 | 7 | A | Pouštím výboj číslo 123, který síť při učení neviděla. Obě čáry se téměř překrývají. | Mezerník spustí přehrávání. Stav dole: validační skupina 1 z 5. |
| 2:56 | 7 | A | (ticho, výboj běží a porota se dívá) | Nech výboj proběhnout dvakrát. |
| 3:03 | 6 | A | Kroužek je osa, křížek je bod X a trojúhelníky jsou dotykové body. | Ukázat na značky v řezu. |
| 3:09 | 7 | A | Vpravo je tabulka: skutečná a odhadnutá hodnota každé veličiny a jejich rozdíl. | Pravý panel, sloupce Skutečnost, Předpověď, Δ. |
| 3:16 | 8 | A | Dole je chyba v čase. V průměru přes všechny výboje roste na začátku a na konci. | Spodní graf, veličina Poloha magnetické osy. |
| 3:24 | 9 | A | Každý snímek je jeden odhad sítě. Jeden takový odhad trvá 0,0145 milisekundy. Přehráváme ho zpomaleně, aby bylo něco vidět. | Prohlížeč latenci nezobrazuje, číslo říkáš z paměti. Je na snímku 5. |
| 3:33 | 4 | A | A teď záměrně jeden z nejhorších výbojů, číslo 0. | V nabídce Výboj zvolit první položku (Výboj 0) nebo otevřít adresu s #d=0. Spustit přehrávání. |
| 3:37 | 7 | A | Chyba osy je v něm podle prohlížeče 5,7 milimetru a rozdíl mezi čárami je vidět. | V panelu vlevo Chyba polohy osy. Ověřit při zkoušce, že je rozdíl opravdu vidět. |
| 3:44 | 6 | A | (ticho, špatný výboj běží) | Ukázat na místo, kde se čáry rozcházejí. |
| 3:50 | 9 | B | Takových výbojů je málo: 85 procent výbojů má chybu osy pod milimetrem, jen tři ze 149 přes 5 milimetrů. | Čísla jsou spočtená z dat prohlížeče (chyba osy za výboj). Před vystoupením ověřit. |
| 3:59 | 6 | A | Shrnutí: typický výboj sedí, chybují jen vzácné výjimky. Vracíme se ke snímkům. | Cmd+Tab zpět do prezentace, klik na snímek 5. |

### Snímek 5: Rychlost, verdikt pro řízení (4:05 až 4:40, 35 s)

Hlavní věta: Jeden odhad trvá 0,0145 ms na procesoru, rychlost nebude překážkou.

Obrázek: 02-minutes-vs-ms.png (zopakovat jako pozadí)

| Čas | Sek. | Kdo | Co se říká | Na obrazovce |
|---|---|---|---|---|
| 4:05 | 8 | B | Jak je to rychlé? Jeden odhad na procesoru trvá 0,0145 milisekundy, to je medián. | Snímek 5. Velká dlaždice 0,0145 ms. Obrázek 02-minutes-vs-ms.png jako pozadí. |
| 4:13 | 7 | B | Nejhorší naměřený případ je 0,09 milisekundy, tedy více než desetkrát méně než jedna milisekunda. | Dlaždice 0,090 ms. |
| 4:20 | 6 | B | Na druhém počítači vyšlo 0,032 milisekundy, pořád hluboko pod limitem. | Malý text pod dlaždicemi. |
| 4:26 | 6 | B | Grafická karta je pro jeden odhad pomalejší, 0,24 milisekundy, protože síť je malá. | Řádek o grafické kartě. |
| 4:32 | 8 | B | Verdikt: rychlost nebude překážkou. Změřili jsme jen odhad samotné sítě, napojení na řídicí systém jsme nezkoušeli. | Konec snímku. Pohled na A, klik na snímek 6. |

### Snímek 6: Meze (4:40 až 5:10, 30 s)

Hlavní věta: Nejhůř bod u limiteru, 10,7 a 22,2 mm; chyby rostou na začátku a na konci výboje.

Obrázek: žádný obrázek, na snímku je graf chyby osy podle času

| Čas | Sek. | Kdo | Co se říká | Na obrazovce |
|---|---|---|---|---|
| 4:40 | 10 | A | Teď poctivě slabá místa. Nejhůř určujeme bod u limiteru: chyba je 10,7 milimetru radiálně a 22,2 milimetru svisle. | Snímek 6. Dlaždice 10,7 mm a 22,2 mm. |
| 4:50 | 5 | A | To je řádově horší než u ostatních veličin. | Stejné dlaždice. |
| 4:55 | 9 | A | Chyby rostou i na začátku a na konci výboje: osa má na konci 0,9 milimetru, uprostřed 0,24. | Graf chyby osy podle desetin výboje, oranžové sloupce jsou začátek a konec. |
| 5:04 | 6 | A | Výstup přitom mezi sousedními časy kolísá stejně jako skutečnost. | Spodní řádek snímku (poměr kolísání 0,97). |

### Snímek 7: Co model neumí (5:10 až 6:10, 60 s)

Hlavní věta: Šum zhroutí síť naučenou na čistých datech, potřebuje dost výbojů, neobvyklý tvar neznáme, jen jeden tokamak.

Obrázek: žádný obrázek, na snímku jsou dva grafy (šum, počet výbojů)

| Čas | Sek. | Kdo | Co se říká | Na obrazovce |
|---|---|---|---|---|
| 5:10 | 9 | B | Největší slabina je šum. Síť naučená na čistých datech má na čistých datech chybu osy 0,38 milimetru. | Snímek 7, levý graf, první sloupec. |
| 5:19 | 8 | B | Na datech se šumem od organizátorů je chyba 10,15 milimetru, tedy 27krát větší. | Druhý sloupec je oranžový. |
| 5:27 | 12 | B | Když se síť učí rovnou na zašuměných datech, chyba klesne na 2,64 milimetru. Zaplatíme za to horším výsledkem na čistých datech: 2,22 milimetru. | Třetí a čtvrtý sloupec. Číslo 2,22 není na grafu, říkáš ho z paměti. |
| 5:39 | 13 | A | Druhá slabina: počet výbojů. Se 6 výboji je chyba osy 7,3 milimetru, s 30 výboji 1,47 a se všemi 119 učícími výboji 0,38. Křivka ještě neklesla na dno. | Pravý graf, křivka podle počtu učících výbojů. |
| 5:52 | 9 | A | Třetí slabina: neobvyklý tvar plazmatu mimo naučené vztahy jsme zatím neměřili. Nevíme, jak by se síť zachovala. | Spodní text snímku: neobvyklý tvar, DOPLNIT, zatím neměřeno. |
| 6:01 | 9 | B | Všechno platí jen pro jeden tokamak a 149 výbojů. Model odhaduje tvar a řízení plazmatu sám nenahradí. | Spodní text snímku. |

### Snímek 8: Závěr, jedno číslo (6:10 až 7:00, 50 s)

Hlavní věta: 0,0145 ms na jeden odhad, desetiny milimetru, a upřímně co nefunguje.

Obrázek: 07-closing.png

| Čas | Sek. | Kdo | Co se říká | Na obrazovce |
|---|---|---|---|---|
| 6:10 | 4 | A | Shrnu to jedním číslem. | Snímek 8. Obrázek 07-closing.png. Doporučená změna snímku: velké číslo 0,0145 ms vlevo místo rámečku živé ukázky. |
| 6:14 | 8 | A | 0,0145 milisekundy. Tolik trvá jeden odhad tvaru plazmatu na procesoru obyčejného počítače. | Nech číslo chvíli viset. Pomalu. |
| 6:22 | 7 | A | Klasický výpočet trvá minuty. Zadání chce jednotky až desítky milisekund. | Stále snímek 8. |
| 6:29 | 6 | B | Přesnost: desetiny milimetru u osy, bodu X a dotykových bodů. | Dlaždice Přesný. |
| 6:35 | 12 | B | Pro řízení tokamaku ale model ještě není. Je slabý u bodu limiteru, nezná neobvyklé tvary a šum mu vadí, pokud se na něj neučí. | Dlaždice Zbývá. |
| 6:47 | 8 | A | Zbývá ověřit napojení na řídicí systém, získat víc výbojů a přidat odolnost proti šumu. | Stále snímek 8. |
| 6:55 | 5 | A+B | Desetiny milimetru za setiny milisekundy. Děkujeme. | Oba se dívají na porotu. Konec v 7:00. |

## Pravidla řeči

* Číslo řekni jednou, pomalu, a nech ho doznít. V jedné větě nejvýš dvě čísla.
* Nečti text ze snímku. Dívej se na porotu, na obrazovku jen ukaž.
* Před začátkem: prohlížeč otevřený na výboji 123, rychlost 1×, zastaveno; druhá záložka nebo adresa s #d=0 připravená; hlasitost a zrcadlení obrazovky vyzkoušené.
* Kontrolní časy: 0:50 snímek 2, 1:20 snímek 3, 1:45 snímek 4, 2:30 ukázka, 4:05 snímek 5, 4:40 snímek 6, 5:10 snímek 7, 6:10 snímek 8, 7:00 konec.
* Když se zpozdíš o víc než 10 sekund: vynech řádek o grafické kartě (snímek 5) a poslední větu snímku 3. Když ukázka nejede: viz Záloha.
* Neznáš odpověď? Řekni: Tohle jsme neměřili. A pokračuj tím, co jsme měřili. Nikdy nehádej číslo.

## Záloha, když ukázka selže

* Po první větě ukázky (2:41) řekni: Ukázka se nespustila, ukážu uložené obrázky. Pak ukaž tři obrázky z tlačítka Uložit PNG (začátek, střed a konec výboje 123) a řádky ukázky o osách a tabulce. Zkrať to na 45 sekund a zbytek času dorovnej tím, že vynecháš řádky se špatným výbojem.
* DOPLNIT: nahrát 60 sekund záznamu obrazovky z prohlížeče (výboj 123 a výboj 0) a uložit vedle prezentace. Zatím neexistuje.

## Verze na 30 sekund

Plazma v tokamaku se musí držet daleko od stěny. Řídicí systém proto potřebuje znát jeho tvar v řádu milisekund, ale klasický výpočet trvá minuty. My jsme natrénovali malou neuronovou síť, která tvar odhadne ze 24 magnetických měření. Chyba osy je 0,38 milimetru a jeden odhad trvá 0,0145 milisekundy. Slabé místo je šum v měření a bod u limiteru. Data jsou jen z jednoho tokamaku.

Slov: 64. Přibližně 30 sekund.

## Verze na 60 sekund (výtah)

Tokamak drží žhavé plazma magnetickým polem. Když se plazma dotkne stěny, může ji poškodit. Proto musí řídicí systém znát tvar plazmatu v řádu jednotek až desítek milisekund, ale klasický výpočet z magnetických měření trvá minuty. Vzali jsme data ze 149 výbojů tokamaku COMPASS a naučili malou neuronovou síť odhadnout tvar ze 24 měření. Testovali jsme vždy na výbojích, které síť při učení neviděla. Osa plazmatu vyjde s chybou 0,38 milimetru, bod X s chybou 0,2 milimetru a jeden odhad trvá 0,0145 milisekundy. V prohlížeči vidíte skutečný a odhadnutý tvar vedle sebe. Nejsme hotovi: bod u limiteru má chybu 10,7 a 22,2 milimetru, šum v měření zvedne chybu osy na 10,15 milimetru a neobvyklý tvar jsme neměřili. Data jsou jen z jednoho tokamaku.

Slov: 122. Přibližně 58 sekund.

## Deset zlých otázek a upřímné odpovědi

Každá odpověď říká i mez. Poznámky k zdrojům a k tomu, co ještě chybí, jsou v části Lead notes.

### 1. Fyzik
Otázka: Čemu říkáte pravda? Porovnáváte se skutečným plazmatem, nebo s výpočtem?

Odpovídá A: Porovnáváme se správnými odpověďmi, které dodal ústav. Podle zadání je lze získat numerickou rekonstrukcí rovnováhy, takže se síť učí tuto rekonstrukci napodobit. Chyba 0,38 milimetru je tedy chyba proti ní, ne proti skutečnému plazmatu. Jak přesné jsou správné odpovědi samy o sobě, jsme neměřili.

### 2. Fyzik
Otázka: Co když plazma bude mít nový tvar, který v datech nebyl?

Odpovídá A: Nevíme, tuto zkoušku jsme zatím neměřili. V datech leží protažení a trojúhelníkovost na jedné úzké křivce, tedy na jedné rodině tvarů, a dvě hlavní složky vstupů nesou 92,8 procenta rozptylu. Síť se učila jen na této rodině. Pro tvar mimo ni jí věřit nelze.

### 3. Fyzik
Otázka: Síť se na šumu zhroutí. Dá se to vůbec použít se skutečnými čidly?

Odpovídá A: Síť naučená na čistých datech na šum nestačí: chyba osy vyskočí z 0,38 na 10,15 milimetru. Při učení na zašuměných datech je to 2,64 milimetru, ale na čistých datech pak 2,22. Posun čidel jsme simulovali vlastním vzorcem, ne měřeným posunem skutečných čidel. Použitelné je to tedy jen s učením na šumu a s ověřením na zařízení.

### 4. Odborník na strojové učení
Otázka: Proč u proudu plazmatem vychází lineární model lépe než vaše síť?

Odpovídá A: Je to tak. Proud plazmatem určí lineární model s chybou 0,0346 kiloampéru, síť s chybou 1,49. Proud pravděpodobně souvisí s měřením téměř lineárně. Proto netvrdíme, že je síť lepší všude. Pro proud bychom měli použít lineární model, v číslech, která ukazujeme, použit není.

### 5. Odborník na strojové učení
Otázka: Je validace poctivá? Jen 149 výbojů, jedno náhodné nastavení, žádný interval spolehlivosti.

Odpovídá A: Dělíme po celých výbojích a pětkrát jinak, test je vždy na výbojích, které síť neviděla. Architekturu jsme zvolili předem a podle testu neladili. Mezi pěti rozděleními je rozptyl: u osy 0,38 milimetru s odchylkou 0,12. Každé rozdělení jsme trénovali jednou, takže rozdíly několika procent mezi variantami nejsou prokázané.

### 6. Odborník na strojové učení
Otázka: Proč jen jedna síť? Zkoušeli jste stromy nebo jiné architektury?

Odpovídá B: V číslech máme jen lineární model a tuto síť. Silnější modely, hlavně pro bod u limiteru, se teprve zkoušejí a výsledek zatím nemáme. Síť je záměrně malá, aby byla rychlá. Zda by větší model zlepšil bod u limiteru, nevíme.

### 7. Fyzik
Otázka: Chyba 0,38 milimetru zní skvěle, ale hodnoty se skoro nehýbou. Co to znamená?

Odpovídá A: Správně, osa se v datech hýbe jen se směrodatnou odchylkou 8 milimetrů. Proto uvádíme chyby v milimetrech i vztažené k rozptylu: u osy je to 0,139 u sítě a 0,68 u lineárního modelu.

### 8. Podnikatel
Otázka: Co to znamená v praxi? Dá se to nasadit do řízení?

Odpovídá B: Zatím ne. Změřili jsme jen samotný odhad: 0,0145 milisekundy na procesoru obyčejného počítače, nejhůř 0,09. Mezi dvěma řádky dat uplyne asi 0,6 milisekundy, takže by odhad stíhal. Přenos měření, napojení na řídicí systém a chování ve smyčce jsme ale nezkoušeli. Bez toho a bez odolnosti proti šumu bych to do řízení nedal.

### 9. Podnikatel
Otázka: Komu to pomůže a co dál? Dá se to použít na COMPASS Upgrade?

Odpovídá B: Ústav připravuje nástupce COMPASS Upgrade a chce využít strojové učení při návrhu i provozu. Náš model je naučený jen na COMPASSu a na jiném zařízení by se musel učit znovu. Z křivky učení víme, že s 30 výboji je chyba osy 1,47 milimetru. Kolik výbojů potřebuje nový stroj, nevíme.

### 10. Podnikatel
Otázka: Proč věřit modelu, který neříká, jak si je jistý? Co když se plete?

Odpovídá B: Nemáme odhad nejistoty, síť vydá jen číslo. Slabá místa známe: bod u limiteru, začátek a konec výboje a šum. V prohlížeči jste viděli výboj s chybou osy 5,7 milimetru. Pro řízení by bylo nutné přidat kontrolu, zda je odhad věrohodný. To jsme nedělali.

## Lead notes (English, for the team, not spoken)

### Words and seconds per section

| Section | Start | End | Seconds | Spoken words | Words per second |
|---|---|---|---|---|---|
| Snímek 1: Problém | 0:00 | 0:50 | 50 | 96 | 1.92 |
| Snímek 2: Data | 0:50 | 1:20 | 30 | 59 | 1.97 |
| Snímek 3: Metoda | 1:20 | 1:45 | 25 | 48 | 1.92 |
| Snímek 4: Výsledky | 1:45 | 2:30 | 45 | 88 | 1.96 |
| Živá ukázka, mezi snímkem 4 a 5 | 2:30 | 4:05 | 95 | 165 | 1.74 |
| Snímek 5: Rychlost, verdikt pro řízení | 4:05 | 4:40 | 35 | 67 | 1.91 |
| Snímek 6: Meze | 4:40 | 5:10 | 30 | 52 | 1.73 |
| Snímek 7: Co model neumí | 5:10 | 6:10 | 60 | 115 | 1.92 |
| Snímek 8: Závěr, jedno číslo | 6:10 | 7:00 | 50 | 80 | 1.60 |
| Total | 0:00 | 7:00 | 420 | 770 | 1.83 |
| 30 second version | | | 30 | 64 | 2.13 |
| 60 second version | | | 60 | 122 | 2.03 |

Words are counted by splitting on spaces (a number such as 42 972 counts as two words and is read longer, so numeric lines run slower than the count says). Rehearse once with a stopwatch; the pace to hit is about 2 words per second.

### What differs from outline.md, and why

* Slide order and the content of every slide are unchanged (1 problem, 2 data, 3 method, 4 results, 5 real time, 6 limits, 7 cannot do, 8 close).
* The outline puts the demo on slide 8 for 30 s. The owner's rule is problem, live demo in the core, one number at the end, so the live demo is a 95 s window between slide 4 and slide 5 (centre of the talk, 2:30 to 4:05), and slide 8 becomes the close with the one number. Request for lane K: in the deck, replace the empty panel on slide 8 (live demo placeholder) with the big number 0,0145 ms, or with a still of the viewer as the fallback.
* Seconds per slide (outline to script): 1 problem 50 to 50, 2 data 50 to 30, 3 method 50 to 25, 4 results 80 to 45, demo 0 to 95, 5 real time 50 to 35, 6 limits 50 to 30, 7 cannot do 60 to 60, 8 close 30 to 50. Total 420 both ways. Speaker notes in the deck still carry the outline seconds and need the new ones.
* The one number at the end is 0,0145 ms (median, one sample, CPU). Opening and closing both use the minutes against milliseconds contrast.

### Problems found while writing (decide before the talk)

1. The viewer shows no latency readout. The task asked for the shape over a discharge together with the latency; the script says the number aloud at 3:24 and shows it on slide 5. A latency box in the viewer is DOPLNIT (lane U).
1b. Slide 4 of the deck has no fewer inputs figure, but speaker B says the inputs numbers there (0,063, 0,094, 0,066, 0,285). Add results/ipp1-inputs.png (left panel, Czech labels, only the legend says IPR only and FL only) or three small tiles to slide 4.
2. Plasma current: the linear model beats the network by a factor of 43 (0.0346 kA against 1.49 kA, R2 0.99999983, results/ipp1-baseline.json). The outline lists 1,49 kA as the current error; the spoken script avoids that figure and answers it in question 4. Consider using ridge for the current in the final numbers.
3. The viewer status bar says the wall outline is not loaded (D.wall is null), so the cross section has no tokamak wall. Nothing in the spoken text claims a wall.
4. The viewer shows true target values of one discharge row by row. PLAN.md RP-6 left open whether a single discharge trace may be shown in a public talk; the jury includes IPP, the data owner, but a published video would be public. Owner decides. The spoken text says only that raw coil measurements are not shown, which is true of the viewer.
5. The images are illustrations (assets/prompts.md): 03-coils shows 16 coils and 06-neural-bridge 16 sensor dots, the real input is 24; 04 and 02 are drawings, not photos. The script says so in the stage directions.
6. The assignment text speaks of 17 parameters; the file has 16 main target columns and the deck says 16. A physicist may ask; answer: the 16 main columns, the rest are supplementary columns we did not predict.
7. Latency machines: 0.0145 ms is the lead's Mac (CPU model not recorded, DOPLNIT), 0.032 ms is the colleague's AMD Ryzen 5 7535HS (docs/PLAN.md RP-7). The spoken text says 'procesor obyčejného počítače' and names no CPU. PLAN RP-7 asks to name the CPU next to every figure.
8. Not used in the spoken text because they are not measured yet: camera model and its comparison with the magnetic one (DOPLNIT), unusual shapes (DOPLNIT), improved model for the limiter point (workflow improve-model and the cloud search are still running; answer 6 must be updated when they report).
9. Demo rehearsal checks: that the two lines are visibly apart on discharge 0 (error 5.73 mm over a window about 550 mm wide); that the chart under the cross section on discharge 123 matches the sentence about the ends (the script says 'v průměru přes všechny výboje' to stay true either way); that the 2:41 fallback works.

### Notes per hostile question (sources and what is still open)

| Question | Asker | Answers | Note |
|---|---|---|---|
| 1 | Fyzik | A | DOPLNIT: jak správné odpovědi vznikly (zeptat se ÚFP). Zdroj: zadání, část Detailnější popis. |
| 2 | Fyzik | A | DOPLNIT: měření neobvyklého tvaru. Zdroj: Data-Brief. |
| 3 | Fyzik | A | Zdroj: results/ipp1-robustness-findings.md, tabulka 1. |
| 4 | Odborník na strojové učení | A | DOPLNIT: rozhodnout, zda se do finálních čísel pro proud dá lineární model. Zdroj: results/ipp1-baseline.md. |
| 5 | Odborník na strojové učení | A | Vedoucí týmu potvrdí, že základní model nebyl laděn podle testu (DEC-003). Zdroj: ipp1-learning_curve.md, ipp1-robustness-findings.md. |
| 6 | Odborník na strojové učení | B | DOPLNIT: výsledek hledání modelů (improve a cloud search). Odpověď aktualizovat před vystoupením. |
| 7 | Fyzik | A | Zdroj: Data-Brief (8 mm), results/ipp1-baseline.json (nRMSE). |
| 8 | Podnikatel | B | DOPLNIT: kdo potvrdí napojení na řídicí systém. 0,6 ms je orientační (Data-Brief). |
| 9 | Podnikatel | B | Zdroj: úvodní prezentace ÚFP (snímek 7), results/ipp1-robustness-findings.md, tabulka 2. |
| 10 | Podnikatel | B | Zdroj: results/ipp1-baseline.md, ipp1-time.md, prohlížeč. |

### Numbers used and where they come from

| Number in the script | Value | Source |
|---|---|---|
| Discharge length | 150 to 200 ms | Data-Brief.md |
| Classical reconstruction | minutes | outline.md slide 1, IPP intro slide 10 (out/ipp-uvodni-prezentace.txt) |
| Required reaction | units to tens of ms | Assignment.md, out/ipp-uloha1.txt |
| Rows, discharges | 42 972, 149 | Data-Brief.md, docs/DECISIONS.md DEC-003 |
| Inputs and targets | 24 (16 IPR + 8 FL), 16 main targets | Data-Brief.md, outline.md |
| Network size | 107 152 parameters, 256-256-128 | results/ipp1-baseline.md, ipp1-latency.md |
| Axis error R and Z | 0.377 and 0.391 mm (script: 0,38) | results/ipp1-baseline.md |
| X point error | 0.202 and 0.195 mm (script: 0,2) | results/ipp1-baseline.md |
| Range axis, X, strike | 0.0552 to 0.391 mm (script: 0,06 to 0,4) | results/ipp1-baseline.md |
| Linear model axis R | 2.4 mm (about 6.4 times the network, derived) | results/ipp1-baseline.md |
| is_limited accuracy | 99.3 % | results/ipp1-baseline.md |
| Fewer inputs | all 24: 0.063; top 8: 0.094; IPR only 0.066; FL only 0.285 | results/ipp1-inputs.md |
| Latency CPU | median 0.0145, max 0.090, GPU single 0.2405 ms | results/ipp1-latency.md |
| Latency second machine | 0.032 ms | docs/PLAN.md RP-7, outline.md |
| Limiter point | 10.7 mm and 22.2 mm | results/ipp1-baseline.md |
| Axis error end against middle | 0.9 mm (last tenth) against 0.24 mm | results/ipp1-time.md |
| Jitter ratio | 0.97 for R axis | results/ipp1-time.md |
| Noise | 0.38, 10.15, 2.64, 2.22 mm; 27 times (derived) | results/ipp1-robustness-findings.md, table 1 |
| Learning curve | 6: 7.3, 30: 1.47, 119: 0.38 mm | results/ipp1-robustness-findings.md, table 2 |
| Plasma current linear model | 0.0346 kA against 1.49 kA | results/ipp1-baseline.md |
| Spread of the axis | 8 mm standard deviation; nRMSE 0.139 and 0.68 | Data-Brief.md, results/ipp1-baseline.json |
| Fold spread of the axis | 0.12 mm | out/ipp1-learning_curve.md (fold SD 0.1162) |
| Input variance in 2 components | 92.8 % | Data-Brief.md |
| Row spacing | about 0.6 ms | Data-Brief.md (approximate) |
| Viewer: discharge 123 and 0 | 123: 0.44 mm, 219 frames, validation group 1; 0: 5.73 mm, 167 frames | repo/viewer/data.js (summary fields only), computed 17:30 |
| Viewer: share of discharges | 85 % under 1 mm, 3 of 149 over 5 mm, median 0.43 mm | repo/viewer/data.js, computed by me; the viewer metric is the distance in R and Z, not the per coordinate MAE of the tables |

All numbers were read from the files at 17:30 on 23 Oct. If the improve-model or the cloud search changes the baseline, update slide 4, 6, 8 and answers 5 and 6 and rerun the checks.

### Open DOPLNIT

* Neobvyklý tvar plazmatu, výsledek měření (slide 7, answer 2).
* Kdo potvrdí napojení na řídicí systém (answer 8).
* Výsledek kamerového modelu (not in the script; add one sentence to slide 8 if it arrives).
* Latency box in the viewer; 60 s screen recording as a fallback; CPU model of the lead's Mac.
* Decision whether ridge is used for the plasma current; whether the baseline was tuned on test folds (answer 5, DEC-003).
