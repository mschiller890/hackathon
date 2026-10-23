# Poznámky ke zkoušce (předběžné)

Stav: odhad podle počtu slov, NE měření na stopkách. Přednášku zatím nikdo nečetl nahlas. Po přečtení nahlas čísla přepsat skutečnými.

## Odhad délky podle snímků

Platí časy ze souboru pitch script (rozhodnutí vedoucího, RP 11). Počty mluvených slov a slova za sekundu jsou z jeho tabulky, ne moje měření.

* Snímek 1: 96 slov v 50 s, 1,92 slova za sekundu.
* Snímek 2: 59 slov ve 30 s, 1,97.
* Snímek 3: 48 slov ve 25 s, 1,92.
* Snímek 4: 88 slov ve 45 s, 1,96.
* Živá ukázka: 165 slov v 95 s, 1,74.
* Snímek 5: 67 slov ve 35 s, 1,91.
* Snímek 6: 52 slov ve 30 s, 1,73.
* Snímek 7: 115 slov v 60 s, 1,92.
* Snímek 8: 80 slov v 50 s, 1,60.
* Celkem 770 slov ve 420 s, 1,83 slova za sekundu.

Tempo kolem 2 slov za sekundu je rychlé, zvlášť u čísel, která se čtou pomaleji. Nejtěsnější jsou snímky 2, 4 a 7. DOPLNIT: skutečný čas po přečtení se stopkami (maximum 7:00).

## Kde je text těžký na sledování

* Snímek 4 má nejvíc čísel (osa, bod X, dotykové body, proud, protažení, vstupy). Říct nahlas jen tři: osa 0,38 mm, bod X 0,20 mm, proud plazmatem 0,035 kA z lineárního modelu. Zbytek nechat na obrazovce.
* Snímek 7 míchá šum, množství dat a meze. Mluvit ve třech větách, v tomto pořadí.
* Slova IPR a FL (snímek 2) nejsou pro posluchače srozumitelná. Říkat "cívky" a "smyčky toku", viz slovníček.

## Otázky poroty (naše odhady, ne deset otázek ze skriptu)

Deset otázek poroty s odpověďmi je v souboru pitch script. Zde jsou moje doplňující odpovědi, všechny z osnovy a z results:

* Proč síť, a ne klasická rekonstrukce? Výpočet sítě trvá 0,0145 ms na procesoru Apple M5 proti minutám; průměrná chyba je pod půl milimetru u většiny veličin, ale 99 % řádků osy je pod 3,74 mm a nejhorší řádky mají desítky mm.
* Co když čidla mají šum? Na čistých datech učený model je křehký (osa 0,38 mm na 10,15 mm). Učení na šumu to srazí na 2,64 mm za cenu horších čistých dat (2,22 mm).
* Jak víte, že to funguje na nových výbojích? Dělili jsme po celých výbojích, pětkrát jinak.
* Je 149 výbojů dost? Od 30 výbojů se chyba osy s každým zdvojením zhruba půlí ale učili jsme vždy 60 epoch, takže část zlepšení tvoří víc kroků učení; víc dat by zřejmě pomohlo.
* Kde model selhává? Bod u limiteru (10,7 a 22,2 mm) a začátek a konec výboje.
  * Záloha: zkusili jsme zvláštní model pro bod u limiteru. Na čistých datech chybu půlí (10,7 na 5,7 mm radiálně, 22,2 na 11,7 mm svisle), ale na zašuměných datech selže úplně, proto ho zatím nepoužíváme. Platí, dokud vedoucí nerozhodne, který model se v talku ukáže (RP 9); osnova zůstává na základním modelu.
* Dá se to nasadit do řízení? Výpočet sítě je rychlý; sběr signálů, systém reálného času a skutečně zašuměné signály jsme neověřovali.
* Co neobvyklý tvar? Neměřeno (DOPLNIT, nebo přiznat jako mez).
* Co kamera? Samotná je 6 až 8krát horší než magnetická měření na ose (1,54 proti 0,24 mm) a proud plazmatem určit nejde. Měřeno jen na dvou z pěti dělení, kamera zůstává bonus.
