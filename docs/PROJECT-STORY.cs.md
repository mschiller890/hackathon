# Od zadání k výsledku: příběh našeho řešení

*Hackathon CVUT ML 2026, úloha IPP 1: tvar a poloha plazmatu v tokamaku COMPASS z magnetických měření. Čas: pátek 23. října 16:00 až sobota 24. října 14:00. Tento dokument obsahuje jen souhrnné výsledky a texty, žádná surová data Ústavu fyziky plazmatu.*

## 1. Na jedné stránce

**Úloha.** Z 24 magnetických měření (16 cívek a 8 smyček toku) odhadnout 16 veličin, které popisují polohu a tvar plazmatu, tak rychle, aby se to dalo použít při řízení tokamaku. Data: 149 výbojů, 42 972 časových okamžiků.

**Co jsme udělali.** Naučili jsme malou neuronovou síť (107 152 parametrů), rozšířili ji o tři úpravy a změřili přesněji, než se obvykle měří: dělení po celých výbojích, třicet výbojů odložených před finálním výběrem, pět dělení, tři semínka, intervaly spolehlivosti přes výboje a latenci na konkrétním procesoru.

**Hlavní výsledky** (vždy shoda s rekonstrukcí rovnováhy, kterou dal ústav, ne přesnost vůči skutečnému plazmatu):

| Co | Hodnota | Protokol |
|---|---|---|
| Chyba radiální osy R, vybraný model | 0,13 mm [0,10; 0,18] | 30 odložených výbojů |
| Totéž ve vývoji | 0,23 mm | 5 dělení po výbojích, 119 výbojů |
| Totéž na novějších číslech výbojů | 0,40 mm | blokové dělení |
| Základní síť, osa R | 0,31 mm (odložené), 0,38 mm (5 dělení) | totéž |
| Bod u limiteru | 4,55 mm a 8,35 mm (základní síť 10,6 a 22,5 mm) | 30 odložených |
| Proud plazmatem | 0,035 kA (lineární model; síť měla 1,2 kA) | 30 odložených |
| Odhad jednoho vzorku | 0,0145 ms základní síť; 0,0154 až 0,0274 ms vybraný model | Apple M5, jedno jádro, vytížený stroj |
| Na zašuměných vstupech | 2,38 mm (síť učená se šumem); model učený na čistých datech selhává (190 mm) | 30 odložených, šum ze souboru organizátorů |

**Co jsme neukázali:** fyzikální přesnost vůči plazmatu, tvary mimo rozsah dat, reálný čas na skutečném řídicím systému (měřili jsme jen výpočet sítě) a dlouhodobou stabilitu bez omezení.

## 2. Zadání a pravidla

Organizátoři dali pět úloh. Dvě od Ústavu fyziky plazmatu AV ČR (IPP): rekonstrukce tvaru plazmatu z magnetických dat (IPP 1) a odhad parametrů paprsku uprchlých elektronů z infračervených obrazů (IPP 2). Tři od Datového centra Ústeckého kraje: obce, kvalita ovzduší a Labe. Tým si vybírá jednu.

Ke každé úloze patřila stejná pravidla: odevzdat Jupyter notebooky (stačí i Colab) s modely, grafy a všemi závěry a prezentaci; grafické rozhraní se nevyžaduje. U úloh IPP navíc platí, že data jsou poskytnuta jen pro tento hackathon a nesmí se zveřejnit. Z veřejné stránky akce víme, že prezentace se konají v sobotu 14:30 až 16:30 a týmy mají nejvýš 15 minut; pravidla odevzdání ani kritéria hodnocení nikde veřejně nejsou, proto jsme je dali do seznamu otázek pro organizátory.

## 3. Proč jsme vybrali IPP 1

Rozhodovalo pravidlo „co přinese body, ne co je technicky zajímavé“. Majitel týmu uvedl kritéria „prezentace a funkčnost“.

| Úloha | Co mluvilo pro | Co proti | Verdikt |
|---|---|---|---|
| **IPP 1, rovnováha** | Čistá tabulková data (43 MB), 24 vstupů a 16 cílů, každé číslo lze změřit a ověřit; zadání samo chce metriku, latenci, stabilitu a robustnost, takže body se dají doložit čísly; přímý příběh (tvar plazmatu v řádu milisekund); animaci tvaru lze ukázat | Důvěrná data; těžké cíle (limiter, X bod), nepravidelné rozdělení | **Vybráno** |
| IPP 2, uprchlé elektrony | Obrazy, zajímavý fyzikální problém | Čtyři datasety A až D, postupně těžší, generalizace mezi nimi; hodně času na síť na obrazech, riziko nedokončení; porotě těžší ukázat výsledek | Ne |
| DCUK 1, obce | Rychlý start, otevřená data | Bez rozhodné metriky, výsledek se špatně porovnává, hodnotí se hlavně interpretace | Ne |
| DCUK 2, ovzduší | Čistá časová řada | Častá úloha, malá odlišnost; důležitá korektní práce s časem a chybějícími hodnotami | Ne |
| DCUK 3, Labe | Zajímavá fyzika toku, předpověď | Riziko úniku budoucích dat, nutné počasí a stanice, těžké ověřit | Ne |

Na IPP 1 rozhodlo, že se *správnost dá změřit* a porotce z IPP pozná kvalitu hned. Kdyby kritéria byla jiná (například srozumitelnost pro studenty), úloha pořád drží díky příběhu a animaci.

## 4. Jak to probíhalo: časová osa

| Čas | Co se stalo |
|---|---|
| Pá 16:00 | Start. Přečtena zadání, vybrána IPP 1. Stažena data (37 MB), vytvořen přehled dat v PDF. |
| Pá 16:20 až 18:00 | Základní model: rozdělení po výbojích, ridge a síť, metriky po parametrech, latence (kontrolní bod CP1). |
| Pá 18:10 | **První nezávislá kritika.** Našla pět zásadních chyb (viz část 6). Pitch přepsán. |
| Pá 18:00 až 22:00 | Povinné analýzy: stabilita v čase, méně vstupů, šum a drift, množství dat. Notebooky 01 až 05. Zamčená testovací sada (30 výbojů). |
| Pá 19:00 až 22:00 | Práce se rozdělila mezi více pomocníků (lokální terminály, cloudové sessions, kolega s vlastním Claudem). Další kritiky a opravy. |
| Pá 22:00 | Brána G1: čísla z cloudu proti našim. Kamera potvrzena s výhradami. |
| Pá večer | Prohlížeč předpovědí, galerie selhání, simulace poroty, fyzikální kritika, jazyková korektura. |
| So 01:00 | Zmrazení výsledků. |
| So 02:30 | CP3: čistý běh všech notebooků. |
| So 10:00 | Zmrazení funkcí. |
| So 12:00 až 13:00 | Odevzdání. |

## 5. Metoda a proč právě tato

**Dělení po celých výbojích.** Sousední okamžiky jednoho výboje jsou skoro kopie. Dělení po řádcích by všechna čísla nafouklo. Proto pětinásobné dělení po výbojích a navíc třicet výbojů odložených před finálním výběrem.

**Síť s maskovanou ztrátou.** Některé cíle existují jen v divertorové konfiguraci (bod X, dotykové body) a jiné jen při limitování. Ztráta se počítá jen tam, kde cíl existuje.

**Lineární model pro proud.** Proud plazmatu je skoro přesně lineární v signálech cívek (Ampérův zákon); lineární model dává 0,035 kA, síť 1,2 kA. Vybrali jsme to, co funguje, ne to, co je modernější.

**Zvláštní síť pro limiter.** Bod u limiteru je nespojitý (diskrétní dotyk se stěnou). Síť s příznakem „je limitováno“ pro něj zlepšila chybu na polovinu.

**Proč ne stromy ani větší sítě.** Zkusili jsme boosting a širší a hlubší sítě. Stromy byly horší a větší sítě nepřinesly zlepšení, které by přežilo rozptyl mezi semínky.

**Proč ne kamera jako první.** Kamera je volitelná, data jsou 876 MB, a úloha ji sama označuje za těžší. Šla až po magnetické části a výsledek je na skrytém slajdu.

**Rychlost.** Měříme jen výpočet sítě (setiny milisekundy). Příjem signálů, nejhorší případ na řídicím systému a přesnost na skutečně zašuměných signálech jsme neověřili, a proto verdikt zní podmíněně.

## 6. Problémy a jak jsme je vyřešili

**Z první kritiky (pá 18:10):**

1. *Chyběla zamčená testovací sada.* Všechna čísla byla z křížové validace. Přidali jsme 30 výbojů odložených před finálním výběrem a přehodnotili protokoly.
2. *Nepodmíněné tvrzení o reálném čase.* Změněno na podmíněný verdikt s výčtem toho, co není změřeno.
3. *Nepravdivé tvrzení o stabilitě.* Poměr kolísání 0,97 až 1,07 platí jen na čistých vstupech a jen pro několik veličin; na zašuměných je 8,4 a 3,3krát horší.
4. *Pořadí důležitosti vstupů je pořadí pro natrénovanou síť, ne informační obsah.* Doplnili jsme kontroly: samotné cívky IPR 0,066, samotné smyčky toku 0,285, všech 24 vstupů 0,063.
5. *Zastaralé stavy v dokumentech.* Zavedli jsme jedno místo pravdy (plán úkolů) a skriptovou kontrolu čísel.

**Z dalších kol:**

6. *Hlavní číslo bylo nejpříznivější ze tří protokolů.* Odložená sada je o 35 % lehčí než vývojová. Dnes uvádíme všechna tři čísla s protokoly: 0,13, 0,23 a 0,40 mm.
7. *Rychlost 0,0145 ms patřila základní síti, ne vybranému modelu.* Změřili jsme vybraný model: 0,0154 až 0,0274 ms.
8. *Ukázka přehrávala základní síť, slajd tvrdil číslo vybraného modelu.* Prohlížeč přepnut na vybraný model na odložených výbojích a popisky přejmenovány.
9. *Všechny chyby jsou vůči referenční rekonstrukci, ne vůči plazmatu* (fyzikální kritika). Přejmenovali jsme „skutečný tvar“ a „přesnost“ na „rekonstrukce ústavu“ a „shoda“ a přidali simulovaný test se známou pravdou.
10. *Soubor „zašuměná data“ má jen bílý šum, žádný drift.* Experimenty s driftem jsou simulované a tak je i označujeme.
11. *Obrácená polarita proudu* (7 % řádků, 78 % kvadratické chyby osy). Kanonizace znaménka je kompromis (−64 % na vzácné skupině, +20 % na hlavní), proto jsme ji nenasadili.
12. *Cloudové hledání vidělo i odložených 30 výbojů.* Jeho čísla jako test nepoužíváme, jen jako nápad. Zbytková síť pro limiter zlepšila limiter o 39 % ve vývoji, na odložených o 28 až 34 %, ale nenasazujeme ji jako hlavní model.
13. *Přeučení.* Chyba na učených výbojích 0,095 mm proti 0,230 mm na nových, odstup 2,4krát. Říkáme to otevřeně a netvrdíme, že se síť nepřeučuje.
14. *Čtyři notebooky chyběly, jeden padal na čistém klonu.* Dopsány a opraveny, kontrolní skript hlídá chybějící výstupy a zakázaná slova, čistý běh devíti notebooků trvá 9 minut.

## 7. Proč tento postup místo jiných

**Přísnost místo okázalosti.** Mohli jsme ukázat jedno krásné číslo (0,13 mm) a velkou kameru. Zvolili jsme postup, kdy každé číslo má protokol a soubor a každá věta prošla kritikou. Fyzik z IPP pozná přísnost hned a ML odborník pozná, že protokol drží.

**Víc nezávislých čtenářů místo jednoho autora.** Texty a čísla psaly stroje a lidé, proto jsme zavedli nezávislé čtenáře: ML kritika, kritika prezentace, hygienický audit, fyzik, simulace poroty, jazyková korektura, tabulka shody čísel. Každý z nich našel něco, co ostatní ne.

**Cloud pro práci bez dat, lokální terminály pro práci s daty.** Data IPP jsou důvěrná a nesmí do cloudu. Proto cloud dělal jen kritiky, texty, rešerši a notebooky čtoucí z výsledků; výpočty a notebooky s daty běžely na počítači s daty.

**Zamčená sada a předem napsaná pravidla.** Odložených 30 výbojů používáme jednou. Když jsme se rozhodovali o nasazení nových modelů, napsali jsme pravidlo předem a až potom měřili. Když jsme pravidlo museli upravit (latence), je to vyznačeno jako dodatečné.

**Poctivost před hezkým číslem.** U každé slabiny stojí, co jsme neměřili. To je záměr: porota z IPP pozná přehnané tvrzení a ztrátu důvěry.

## 8. Jak vypadá výsledek

* **Notebooky 01 až 09** s uloženými výstupy a závěry (data, základní modely, vstupy a důležitost, stabilita v čase, latence, kamera, rozdělení a neobvyklé tvary, šum a množství dat, vybraný model na odložených výbojích).
* **Prezentace do 7 minut** se živou ukázkou prohlížeče, který přehrává výboj s tvarem z rekonstrukce ústavu a odhadnutými body, chybou v čase a latencí.
* **Samostatný model** (`predict.py`): z CSV s 24 sloupci vypíše 16 hodnot na řádek, 4 až 25 mikrosekund na řádek, bez torche.
* **Jednostránkové shrnutí** pro porotu, galerie selhání, taháky pro oba řečníky, karty na trénink odpovědí a skripty pro opakovatelnost (`make_all.py`, kontrola čísel, kontrola notebooků).

## 9. Čeho si ceníme a co nevíme

* Naše síla je rozsah ověření a poctivost o limitech. Slabiny: jediný tokamak, jen shoda s referenční rekonstrukcí, malá kamerová síť, simulovaný drift.
* Nevíme, podle čeho porota hodnotí. Pokud rozhodují srozumitelnost pro studenty a týmová práce, bude talk s hustými čísly slabší; proto je cílem jasná hlavní věta a živá ukázka.
* O použití umělé inteligence: tým pracoval s agenty (Claude a GPT) jako pomocníky; zadání, rozhodnutí a kontrolu čísel dělali lidé. Pravidla akce na to jsme se zeptali organizátorů.

## 10. Co by se dělalo dál

Ověřit fyzikální přesnost nezávislým měřením nebo simulací se známou pravdou, otestovat tvary mimo rozsah dat, změřit celou řídicí smyčku včetně příjmu signálů, zkusit kombinaci magnetických dat a kamery s větší sítí a vyhodnotit nový model pro limiter na dalších výbojích.
