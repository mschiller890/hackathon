# Poznámky ke zkoušce (předběžné)

Stav: odhad podle počtu slov, NE měření na stopkách. Přednášku zatím nikdo nečetl nahlas. Počítáno 130 slov za minutu,
slova z odrážek v osnově (osnova je zhuštěná, mluvený text bude delší). Po přečtení nahlas čísla přepsat skutečnými.

## Odhad délky podle snímků

* Snímek 1: 58 slov, asi 27 s z 50 s. Rezerva velká.
* Snímek 2: 78 slov, asi 36 s z 50 s.
* Snímek 3: 54 slov, asi 25 s z 50 s.
* Snímek 4: 124 slov, asi 57 s z 80 s.
* Snímek 5: 81 slov, asi 37 s z 50 s.
* Snímek 6: 83 slov, asi 38 s z 50 s.
* Snímek 7: 85 slov, asi 39 s z 60 s.
* Snímek 8: 40 slov, asi 18 s z 30 s.

Odrážky samy vycházejí kolem 5 minut, zbytek je prostor na plynulou řeč a přechody. Riziko je spíš opačné než přetečení:
mluvit rychleji, než se vejde. DOPLNIT: skutečný čas po přečtení se stopkami (maximum 7:00).

## Kde je text těžký na sledování

* Snímek 4 má nejvíc čísel (osa, bod X, dotykové body, proud, protažení, vstupy). Říct nahlas jen tři: osa 0,38 mm, bod X 0,20 mm, 99,3 % u limiteru. Zbytek nechat na obrazovce.
* Snímek 7 míchá šum, množství dat a meze. Mluvit ve třech větách, v tomto pořadí.
* Slova IPR a FL (snímek 2) nejsou pro posluchače srozumitelná. Říkat "cívky" a "smyčky toku", viz slovníček.

## Otázky poroty (naše odhady, ne deset otázek ze skriptu)

DOPLNIT: deset otázek z pitch skriptu, až bude existovat. Do té doby připravené odpovědi, všechny z osnovy a z results:

* Proč síť, a ne klasická rekonstrukce? Odezva 0,0145 ms na procesoru proti minutám; přesnost je pod půl milimetru u většiny veličin.
* Co když čidla mají šum? Na čistých datech učený model je křehký (osa 0,38 mm na 10,15 mm). Učení na šumu to srazí na 2,64 mm za cenu horších čistých dat (2,22 mm).
* Jak víte, že to funguje na nových výbojích? Dělili jsme po celých výbojích, pětkrát jinak.
* Je 149 výbojů dost? Od 30 výbojů se chyba osy s každým zdvojením zhruba půlí a nepřestala klesat, víc dat by pomohlo.
* Kde model selhává? Bod u limiteru (10,7 a 22,2 mm) a začátek a konec výboje.
* Dá se to nasadit do řízení? Rychlost to nevylučuje; napojení na skutečný řídicí systém jsme neověřovali.
* Co neobvyklý tvar? Neměřeno (DOPLNIT, nebo přiznat jako mez).
* Co kamera? DOPLNIT, dokud nejsou výsledky.
