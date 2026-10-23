# Studijní podklad pro hlasový rozhovor (ChatGPT)

Tento soubor je určený pro hlasový rozhovor s ChatGPT. Obsahuje jen souhrnné výsledky a texty z naší prezentace; žádná surová data ústavu v něm nejsou. Rozhovor je v češtině.

## Co říct ChatGPT na začátku (vlož jako první zprávu)

Jsi můj trenér před vystoupením na hackathonu. Přečti si přiložený soubor celý. Pak:
1. Nejdřív mi bez odborných slov vysvětli, o čem projekt je, jako bych byl chytrý student, který o plazmatu nic neví. Maximálně dvě minuty, pak se zeptej, jestli je to jasné.
2. Potom mě učíš po krocích podle části "Plán rozhovoru" na konci souboru. Po každém kroku mi dej jednu kontrolní otázku a čekej na mou odpověď. Opravuj mě jen podle čísel a vět v tomto souboru; když něco v souboru není, řekni "to v podkladu není" a nevymýšlej.
3. Na konci hraj porotce: nejdřív fyzika z Ústavu fyziky plazmatu, potom odborníka na strojové učení, potom učitele. Ptej se na těžké otázky z části "Zlé otázky", jednu po druhé, a po mé odpovědi řekni, co chybělo nebo bylo příliš silné.
4. Mluv pomalu, krátkými větami, česky. Čísla vždy s jednotkou a s tím, na čem se měřila.

## Pravidla, která v rozhovoru platí

* Chyba 0,13 milimetru je shoda s rekonstrukcí, kterou nám dal ústav, ne přesnost vůči skutečnému plazmatu.
* Nikdy neříkej "nikdo neviděl", "skutečný tvar", "přesnost" pro shodu s rekonstrukcí, ani že je řízení v reálném čase vyřešené.
* Když nevíme, řekni: "Tohle jsme neměřili, měřili jsme ...".
* Na otázku, zda jsme používali umělou inteligenci, se odpovídá pravdivě: ano, jako pomocníky; zadání, rozhodnutí a kontrolu čísel jsme dělali my.

## Projekt vysvětlený od nuly

Tokamak je prstenec, ve kterém magnetické pole drží velmi horký plyn, plazma. Aby se plazma nedotklo stěn, musí řídicí systém v řádu milisekund vědět, kde plazma je a jaký má tvar. Přesný výpočet tvaru z měření trvá po výboji minuty. Dostali jsme data z tokamaku COMPASS Ústavu fyziky plazmatu: 149 výbojů, asi 43 tisíc časových okamžiků, a v každém 24 magnetických měření (16 cívek a 8 smyček toku). K tomu má každý okamžik hodnoty, které spočítala rekonstrukce rovnováhy ústavu: poloha magnetické osy, bod X, dva dotykové body, bod u limiteru, protažení, trojúhelníkovost, proud plazmatem a další.

Náš úkol: naučit malou neuronovou síť, aby z 24 měření odhadla těch 16 hlavních veličin, a změřit, jak dobře a jak rychle to umí. Dělíme vždy po celých výbojích, protože sousední okamžiky jednoho výboje jsou skoro kopie. Základní síť má 107 152 parametrů. Vybraný model je základní síť plus rozdíly sousedních cívek, lineární model pro proud a zvláštní síť pro bod u limiteru.

Co ukazuje demo: prohlížeč přehrává výboj; tmavá čára je tvar z rekonstrukce ústavu, barevné body jsou odhad vybraného modelu (obrys se nepředpovídá, jen body: osa, bod X, dotykové body, bod u limiteru). Ukázkové výboje: 85 (typický, osa o čtvrt milimetru vedle) a 147 (nejhorší konec, osa o 34 milimetrů vedle na posledním snímku, ale průměr celého výboje pod milimetrem).



## Slovníček

Dvanáct pojmů, každý jednou prostou větou. Slova odpovídají snímkům v osnově.

* **Tokamak:** zařízení tvaru velkého prstence, v němž magnetické pole drží žhavé plazma, aby se nedotýkalo stěn; náš se jmenuje COMPASS.
* **Plazma:** velmi horký plyn, jehož částice jsou nabité, a proto ho lze držet magnetickým polem.
* **Bod X:** místo, kde se magnetické siločáry kříží a kde se hranice plazmatu zalamuje.
* **Dotykový bod:** místo na dně komory, kam dopadá okraj plazmatu, a proto se tam stěna nejvíc namáhá.
* **Limiter:** pevná část stěny, o kterou se plazma může opřít; chybu v jeho poloze odhadujeme nejhůř.
* **Protažení:** poměr výšky a šířky plazmatu; čím větší číslo, tím je plazma vyšší a užší.
* **Trojúhelníkovost:** míra, nakolik se průřez plazmatu podobá písmenu D a nakolik kruhu.
* **Výboj:** jeden celý pokus, od zapálení plazmatu do jeho zániku; data dělíme vždy po celých výbojích.
* **Smyčka toku:** drát kolem komory, který měří magnetický tok, a je tedy jedním z 24 vstupů modelu.
* **Cívka:** drát, který měří magnetické pole; samotných 16 cívek IPR dává skoro stejnou chybu jako všech 24 vstupů.
* **Odezva:** čas od chvíle, kdy model dostane měření, do chvíle, kdy vydá odhad; náš výpočet trvá setiny milisekundy a podle zatížení procesoru o něco víc.
* **Přeučení:** model si zapamatuje učící data místo obecné souvislosti, a proto selže na nových výbojích; proti tomu testujeme na výbojích, které neviděl.

## Čísla k zapamatování a věty, které se nesmí říct

## Tahák A: první řečník, majitel týmu, ruce na notebooku (tvoje řádky jsou tučně)

### 1. Dvanáct čísel (říkej je jednou, pomalu, s protokolem a názvem modelu; nehádej)

| Číslo | Jedn. | Co to je | Protokol | [Soubor] |
|---|---|---|---|---|
| **0,13** | mm | osa R, vybraný model, 30 odložených (0,133) | odložené | [ipp1-final.md] |
| **0,23** | mm | totéž, křížová validace, 119 výbojů (0,230) | křížová | [ipp1-final.md] |
| **0,40** | mm | totéž, test na 59 nejvyšších číslech (0,397) | novější | [ipp1-final.md] |
| **0,31** | mm | osa R, základní síť, 30 odložených (0,307) | odložené | [ipp1-final.md] |
| **4,55** | mm | bod u limiteru, vybraný model; základní síť 10,6 | odložené | [ipp1-final.md] |
| **0,035** | kA | proud, lineární model (0,0347); síť měla 1,20 | odložené | [ipp1-final.md] |
| 0,0145 | ms | ZÁKLADNÍ SÍŤ, medián, Apple M5, vytížený notebook | měření | [ipp1-latency.md] |
| 0,027 | ms | VYBRANÝ MODEL, limitované plazma, medián (0,0274) | měření | [ipp1-latency-shipped.md] |
| 2,38 | mm | osa R, vstupy zašuměné, síť učená se šumem | odložené | [ipp1-final.md] |
| 10,15 | mm | osa R, základní síť z čistých dat, vstupy zašuměné | dělení | [ipp1-robustness-findings.md] |
| **0,095 proti 0,230** | mm | osa R vybraného modelu: učící proti neviděným řádkům | křížová | [ipp1-traintest-gap.md] |
| **1,47** | mm | osa R, základní síť, 30 učících výbojů (se 119: 0,38) | dělení | [ipp1-robustness-findings.md] |

### 2. Devět vět, které neříkej (zdroje: claims-corrections.md, review-physics.md H1 až H4, ipp1-traintest-gap.md)

| Neříkej | Řekni místo toho |
|---|---|
| Nikdo je neviděl. Zamčené. | Odložili jsme 30 výbojů před posledním výběrem modelu; náměty na úpravy vznikly na všech 149. |
| Skutečný tvar. Skutečnost. | Tvar z rekonstrukce ústavu. |
| Přesnost 0,13 milimetru. | Shoda s rekonstrukcí ústavu, osa 0,13 milimetru na odložených výbojích. |
| V reálném čase je to vyřešené. | Ověřili jsme jen výpočet sítě, ne sběr signálů ani zašuměné signály. |
| Nepřeučuje se. | Učící řádky 0,095, neviděné 0,230 milimetru. Hodnotíme jen neviděné. |
| Síť odhadne tvar, obrys. | Síť odhaduje 16 veličin (osa, bod X, dotykové body, limiter), obrys ne. |
| Model to spočítá za 0,0145 ms. | Základní síť 0,0145, vybraný model 0,027 milisekundy. Vždy s názvem modelu. |
| Plazma se dotkne stěny a poškodí ji. | Protažené plazma je svisle nestabilní a bez řízení uhne ke stěně. |
| Cívky nesou skoro všechno. | Samotných 16 cívek 0,066 proti 0,063 se všemi 24; čidlo nejmenujeme. |

### 3. Pořadí a čas

| Od | Snímek | Kdo | Sek. | Do | Musí zaznít |
|---|---|---|---|---|---|
| **0:00** | **1 Problém** | A | 38 | **0:38** | plazma uhne ke stěně; výpočet minuty, řízení ms |
| 0:38 | 2 Data | B | 28 | 1:06 | 42 972 okamžiků, 149 výbojů, 24 vstupů, 16 veličin |
| **1:06** | **3 Metoda** | A | 20 | **1:26** | základní síť 107 152 parametrů, vybraný model |
| **1:26** | **4 Výsledky** | A, B od 2:17 | 63 | **2:29** | 0,13 / 0,23 / 0,40; limiter 4,55; proud 0,035 |
| **2:29** | **Živá ukázka** | A, B od 3:31 | 80 | **3:49** | výboj 85 typický, 147 špatný; 135 ze 149 pod 1 mm |
| 3:49 | 5 Rychlost | B | 40 | 4:29 | 0,0145 základní síť, 0,027 vybraný; jen výpočet |
| **4:29** | **6 Meze** | A | 34 | **5:03** | limiter 4,55 a 8,35; osa na konci 0,9, uprostřed 0,24 |
| **5:03** | **7 Co neumí** | B, A od 5:38, B od 6:11 | 74 | **6:17** | šum 10,15 a 2,38; 1,47; 18 neobvyklých; jeden tokamak |
| **6:17** | **8 Závěr** | A, B od 6:38, oba 6:55 | 43 | **7:00** | 0,13; setiny ms; šum: osa 2,38; ještě ne do řízení |

Sedm minut je odhad z počtu slov, stopkami neměřený; při normálním tempu asi 7:24 [pitch-script.md]. Pozadu přes 10 s: škrtni větu o zadání v 4:13, pak 99 % pod 0,021 v 3:49, pak 5:19 o 2,22. Neškrtej druhou větu 4:13, 5:26 a 6:38.

### 4. Když ukázka selže (přepni do 5 s, nikdy neladíš před porotou)

* **Neotevře se:** snímek 10 (klávesa H, jen PowerPoint), tři obrázky, 45 s. Řekni: Ukázka se nespustila, ukážu obrázky.
* **Zasekne se:** mezerník, pak Cmd+R, pak obrázky. Řekni: Prohlížeč se zasekl, pokračuji obrázky.
* **Není internet:** nic, prohlížeč je jeden soubor bez sítě. (nic neříkej)
* **Notebook mrtvý:** druhý notebook (viewer/dist/index.html) nebo PDF z USB. Řekni: Přepnu na záložní počítač.
* **Selže všechno:** záznam out/viewer-demo.mp4 (60 s), A mluví přes něj. Řekni: Pustím záznam, je to stejná ukázka.

K obrázkům: výboj 85 osa 0,22 a 0,25 mm; výboj 147 osa 33,7 mm, průměr 0,85 mm [demo-facts.md].

### 5. Když se zeptají: „Tohle jsme neměřili, měřili jsme X.“ a pokračuj tím, co jsme měřili

* **A, přesnost: Tohle jsme neměřili, měřili jsme shodu s rekonstrukcí ústavu, osa 0,13 mm.**
* **A, nový tvar, čidla: Tohle jsme neměřili, měřili jsme šum organizátorů, osa 2,38 mm; čidla ne.**
* B, nasazení: Tohle jsme neměřili, měřili jsme výpočet sítě, 0,0145 a 0,027 ms; sběr signálů ne.

**A:** pravda, tvar, šum, proud, validace, konce výboje, polarita, čidla, kamera. **B:** rychlost, nasazení, COMPASS Upgrade, nejistota, zkoušené modely, 16 z 31 sloupců, 99,3 % Zdroje [ipp1-final.md, ipp1-latency-shipped.md, pitch-script.md]. Cizí otázka: „To odpoví kolega.“

<div style="page-break-before: always"></div>

## Tahák B: druhý řečník, kolega, hlídá čas (tvoje řádky jsou tučně)

### 1. Dvanáct čísel (říkej je jednou, pomalu, s protokolem a názvem modelu; nehádej)

| Číslo | Jedn. | Co to je | Protokol | [Soubor] |
|---|---|---|---|---|
| 0,13 | mm | osa R, vybraný model, 30 odložených (0,133) | odložené | [ipp1-final.md] |
| 0,23 | mm | totéž, křížová validace, 119 výbojů (0,230) | křížová | [ipp1-final.md] |
| 0,40 | mm | totéž, test na 59 nejvyšších číslech (0,397) | novější | [ipp1-final.md] |
| 0,31 | mm | osa R, základní síť, 30 odložených (0,307) | odložené | [ipp1-final.md] |
| 4,55 | mm | bod u limiteru, vybraný model; základní síť 10,6 | odložené | [ipp1-final.md] |
| 0,035 | kA | proud, lineární model (0,0347); síť měla 1,20 | odložené | [ipp1-final.md] |
| **0,0145** | ms | ZÁKLADNÍ SÍŤ, medián, Apple M5, vytížený notebook | měření | [ipp1-latency.md] |
| **0,027** | ms | VYBRANÝ MODEL, limitované plazma, medián (0,0274) | měření | [ipp1-latency-shipped.md] |
| **2,38** | mm | osa R, vstupy zašuměné, síť učená se šumem | odložené | [ipp1-final.md] |
| **10,15** | mm | osa R, základní síť z čistých dat, vstupy zašuměné | dělení | [ipp1-robustness-findings.md] |
| 0,095 proti 0,230 | mm | osa R vybraného modelu: učící proti neviděným řádkům | křížová | [ipp1-traintest-gap.md] |
| 1,47 | mm | osa R, základní síť, 30 učících výbojů (se 119: 0,38) | dělení | [ipp1-robustness-findings.md] |

### 2. Devět vět, které neříkej (zdroje: claims-corrections.md, review-physics.md H1 až H4, ipp1-traintest-gap.md)

| Neříkej | Řekni místo toho |
|---|---|
| Nikdo je neviděl. Zamčené. | Odložili jsme 30 výbojů před posledním výběrem modelu; náměty na úpravy vznikly na všech 149. |
| Skutečný tvar. Skutečnost. | Tvar z rekonstrukce ústavu. |
| Přesnost 0,13 milimetru. | Shoda s rekonstrukcí ústavu, osa 0,13 milimetru na odložených výbojích. |
| V reálném čase je to vyřešené. | Ověřili jsme jen výpočet sítě, ne sběr signálů ani zašuměné signály. |
| Nepřeučuje se. | Učící řádky 0,095, neviděné 0,230 milimetru. Hodnotíme jen neviděné. |
| Síť odhadne tvar, obrys. | Síť odhaduje 16 veličin (osa, bod X, dotykové body, limiter), obrys ne. |
| Model to spočítá za 0,0145 ms. | Základní síť 0,0145, vybraný model 0,027 milisekundy. Vždy s názvem modelu. |
| Plazma se dotkne stěny a poškodí ji. | Protažené plazma je svisle nestabilní a bez řízení uhne ke stěně. |
| Cívky nesou skoro všechno. | Samotných 16 cívek 0,066 proti 0,063 se všemi 24; čidlo nejmenujeme. |

### 3. Pořadí a čas

| Od | Snímek | Kdo | Sek. | Do | Musí zaznít |
|---|---|---|---|---|---|
| 0:00 | 1 Problém | A | 38 | 0:38 | plazma uhne ke stěně; výpočet minuty, řízení ms |
| **0:38** | **2 Data** | B | 28 | **1:06** | 42 972 okamžiků, 149 výbojů, 24 vstupů, 16 veličin |
| 1:06 | 3 Metoda | A | 20 | 1:26 | základní síť 107 152 parametrů, vybraný model |
| **1:26** | **4 Výsledky** | A, B od 2:17 | 63 | **2:29** | 0,13 / 0,23 / 0,40; limiter 4,55; proud 0,035 |
| **2:29** | **Živá ukázka** | A, B od 3:31 | 80 | **3:49** | výboj 85 typický, 147 špatný; 135 ze 149 pod 1 mm |
| **3:49** | **5 Rychlost** | B | 40 | **4:29** | 0,0145 základní síť, 0,027 vybraný; jen výpočet |
| 4:29 | 6 Meze | A | 34 | 5:03 | limiter 4,55 a 8,35; osa na konci 0,9, uprostřed 0,24 |
| **5:03** | **7 Co neumí** | B, A od 5:38, B od 6:11 | 74 | **6:17** | šum 10,15 a 2,38; 1,47; 18 neobvyklých; jeden tokamak |
| **6:17** | **8 Závěr** | A, B od 6:38, oba 6:55 | 43 | **7:00** | 0,13; setiny ms; šum: osa 2,38; ještě ne do řízení |

Sedm minut je odhad z počtu slov, stopkami neměřený; při normálním tempu asi 7:24 [pitch-script.md]. Pozadu přes 10 s: škrtni větu o zadání v 4:13, pak 99 % pod 0,021 v 3:49, pak 5:19 o 2,22. Neškrtej druhou větu 4:13, 5:26 a 6:38.

### 4. Když ukázka selže (přepni do 5 s, nikdy neladíš před porotou)

* **Neotevře se:** snímek 10 (klávesa H, jen PowerPoint), tři obrázky, 45 s. Řekni: Ukázka se nespustila, ukážu obrázky.
* **Zasekne se:** mezerník, pak Cmd+R, pak obrázky. Řekni: Prohlížeč se zasekl, pokračuji obrázky.
* **Není internet:** nic, prohlížeč je jeden soubor bez sítě. (nic neříkej)
* **Notebook mrtvý:** druhý notebook (viewer/dist/index.html) nebo PDF z USB. Řekni: Přepnu na záložní počítač.
* **Selže všechno:** záznam out/viewer-demo.mp4 (60 s), A mluví přes něj. Řekni: Pustím záznam, je to stejná ukázka.

K obrázkům: výboj 85 osa 0,22 a 0,25 mm; výboj 147 osa 33,7 mm, průměr 0,85 mm [demo-facts.md].

### 5. Když se zeptají: „Tohle jsme neměřili, měřili jsme X.“ a pokračuj tím, co jsme měřili

* A, přesnost: Tohle jsme neměřili, měřili jsme shodu s rekonstrukcí ústavu, osa 0,13 mm.
* A, nový tvar, čidla: Tohle jsme neměřili, měřili jsme šum organizátorů, osa 2,38 mm; čidla ne.
* **B, nasazení: Tohle jsme neměřili, měřili jsme výpočet sítě, 0,0145 a 0,027 ms; sběr signálů ne.**

**A:** pravda, tvar, šum, proud, validace, konce výboje, polarita, čidla, kamera. **B:** rychlost, nasazení, COMPASS Upgrade, nejistota, zkoušené modely, 16 z 31 sloupců, 99,3 % Zdroje [ipp1-final.md, ipp1-latency-shipped.md, pitch-script.md]. Cizí otázka: „To odpoví kolega.“

## Talk, tak jak ho čteme nahlas

Stopky spusť na prvním řádku. A a B jsou dva řečníci, tučné časy říkají, kdy má řádek začít. Na konci každého snímku je cílový čas, od něj se dívej, jestli běžíte rychleji, nebo pomaleji.
Čísla čti celými slovy, jak jsou napsaná v textu. Při nejistotě řekni: "Tohle jsme neměřili."

---

## Snímek 1: Problém

**0:00   A**

Plazma v tokamaku se samo neudrží uprostřed komory. Protažené plazma je svisle nestabilní a bez rychlého řízení uhne ke stěně.

**0:11   A**

Řízení proto musí znát polohu a tvar plazmatu v milisekundách, tak to chce zadání.

**0:21   A**

Úplná rekonstrukce rovnováhy se počítá po výboji a trvá minuty. Řízení potřebuje rychlý odhad.

**0:29   A**

Naše otázka: dokáže malá neuronová síť rekonstrukci napodobit dost dobře a dost rychle?

**0:36   A**

Data představí kolega.

**Konec snímku: cílový čas 0:38**

---

## Snímek 2: Data

**0:38   B**

Máme data ze 149 výbojů tokamaku COMPASS.

**0:45   B**

Vstup: jen 24 magnetických čidel. Proudy v cívkách pole a model komory síť nedostává. Výstup: 16 veličin, poloha a tvar plazmatu, proud a údaj o limiteru.

**0:59   B**

Dělíme po celých výbojích, aby se netestovalo na tom, co model viděl.

**Konec snímku: cílový čas 1:06**

---

## Snímek 3: Metoda

**1:06   A**

Základní síť je malá neuronová síť o 107 152 parametrech.

**1:13   A**

Vybraný model je její vylepšení: rozdíly sousedních cívek, lineární model pro proud a zvláštní síť pro bod u limiteru.

**Konec snímku: cílový čas 1:26**

---

## Snímek 4: Výsledky

**1:26   A**

Odhadujeme polohu osy, dolní bod X a dotykové body na deskách divertoru. Obrys vybraný model neodhaduje.

**1:33   A**

Třicet výbojů jsme odložili před posledním výběrem modelu, náměty na úpravy ale vznikly na všech 149. Na odložených se vybraný model od rekonstrukce ústavu liší v radiální poloze osy o 0,13 milimetru. Základní síť o 0,31.

**1:56   A**

Křížová validace na 119 výbojích 0,23, novější čísla výbojů 0,40.

**2:05   A**

Proud určí lineární model s chybou 0,035 kiloampéru; síť měla 1,2.

**2:17   B**

Samotné cívky dají skoro stejnou souhrnnou chybu jako všech 24 vstupů, osm nejlepších už ne.

**Konec snímku: cílový čas 2:29**

---

## Živá ukázka, mezi snímkem 4 a 5

**2:29   A**

Teď naživo. Obrys v ukázce je z rekonstrukce ústavu, naše síť odhaduje jen označené body, na třiceti výbojích, které jsme odložili.

**2:42   A**

Tmavá čára je tvar z rekonstrukce ústavu, barevné značky jsou odhad sítě. Výboj číslo 85 je z odložených třiceti a je typický.

**2:54   ticho, 6 s**

*(ticho, výboj běží a porota se dívá)*

**3:00   A**

Kroužek je osa, křížek dolní bod X. Vzdálenost osy od rekonstrukce je tu čtvrt milimetru, na začátku i uprostřed.

**3:12   A**

Teď nejhorší konec: výboj číslo 147, poslední snímek. Osa se liší o třicet čtyři milimetry, bod u limiteru o víc než sto pět, ale v průměru přes celý výboj je to pod milimetrem.

**3:26   ticho, 5 s**

*(ticho, špatný výboj běží)*

**3:31   B**

Takových výbojů je málo: všech třicet odložených má průměrnou vzdálenost osy od rekonstrukce pod milimetrem, medián asi dvě desetiny.

**3:45   ticho, 4 s**

*(ticho, přepnutí zpět)*

**Konec snímku: cílový čas 3:49**

---

## Snímek 5: Rychlost, verdikt pro řízení

**3:49   B**

Základní síť: jeden odhad na procesoru Apple M5 trvá 0,0145 milisekundy.

**4:01   B**

Vybraný model má tři části, odhad asi 0,03 milisekundy.

**4:10   B**

Náš rozpočet je jedna až deset milisekund, výpočet sítě je hluboko pod ním. Neověřili jsme zbytek řetězce: sběr a integraci signálů, jejich chování v provozu, uzavřenou smyčku a systém reálného času.

**Konec snímku: cílový čas 4:29**

---

## Snímek 6: Meze

**4:29   A**

Bod u limiteru je místo na stěně, kde se plazma dotkne. Medián chyby je 0,73 milimetru. Průměr 4,55 zvedají řádky s jiným místem dotyku, v jednom procentu přes 77 milimetrů. Vzdálenost od stěny jsme neměřili.

**4:51   A**

Chyba osy roste hlavně na konci výboje, 0,9 milimetru proti 0,24 uprostřed, základní síť, pět dělení. Příčinu neznáme.

**Konec snímku: cílový čas 5:03**

---

## Snímek 7: Co model neumí

**5:03   B**

Slabé místo jsou chyby čidel. Zkoušeli jsme šum od organizátorů a umělý posun. Základní síť má chybu osy 0,38 milimetru na čistých datech a 10,15 na zašuměných.

**5:23   B**

Vybraný model na šumu selže, proto bychom použili síť učenou se šumem: chyba osy 2,38 milimetru na třiceti odložených.

**5:37   A**

Druhá slabina: počet výbojů. Při 30 učících výbojích je chyba osy 1,47, při všech 119 v každém dělení 0,38; počet epoch byl pevný.

**5:54   A**

Třetí slabina: neobvyklé tvary. Osmnáct nejodlišnějších výbojů jsme vynechali z učení a chyba osy je u základní sítě asi dvaapůlkrát větší, od 0,9 do 2,3 milimetru. Čtrnáct z nich je z časné části kampaně, takže se tu míchá tvar s dobou.

**6:11   B**

Platí jen pro jeden tokamak.

**Konec snímku: cílový čas 6:17**

---

## Snímek 8: Závěr

**6:17   A**

Na čistých vstupech se radiální osa liší od rekonstrukce ústavu o 0,13 milimetru na odložených výbojích, o 0,23 v křížové validaci.

**6:27   A**

Rychlost: základní síť 0,0145 milisekundy, vybraný model asi 0,03.

**6:38   B**

Na zašuměných vstupech: chyba osy jednotky milimetrů, bodu u limiteru desítky, proudu 4,65 kiloampéru. Pro řízení model ještě není: chybí řetězec od čidel a zkouška v uzavřené smyčce.

**6:55   A + B**

Na čistých vstupech desetiny milimetru shody s rekonstrukcí, setiny milisekundy výpočtu. Děkujeme.

**Konec snímku: cílový čas 7:00**

---

Celkem podle `presentation/timing.py`: total written 420 s (7:00); estimated 1.6 w/s -> 7:36, 1.8 w/s -> 6:47, 2.0 w/s -> 6:08.

Sečteno z řádků: 7:00, slov ve všech řádcích 629.

## Zlé otázky a odpovědi (porotce se ptá, ty hodnotíš)

### Q1 – ptá se: IPP fyzik

**Otázka:** Čemu říkáte pravda?

**Krátká odpověď:** Porovnáváme se správnými odpověďmi od ústavu, což je numerická rekonstrukce rovnováhy. Chyba 0,13 milimetru je proti ní, ne proti skutečnému plazmatu. Přesnost těch odpovědí jsme neměřili.

**Úplná odpověď:** Porovnáváme se s rekonstrukcí rovnováhy, kterou nám dal ústav, ne se skutečným plazmatem. Podle toho, co víme, takto vznikly cílové hodnoty; program a nastavení neznáme. Na třiceti odložených výbojích se vybraný model od ní liší v radiální poloze osy průměrně o 0,13 milimetru, interval přes výboje je 0,10 až 0,18. Jak přesná je sama rekonstrukce, jsme neměřili a nezávislé měření polohy plazmatu jsme nepoužili. Ověřit by to šlo zkalibrovanou kamerou nebo výpočtem, kde tvar předem známe.

*Zdroj: ipp1-final.md, docs/review-physics.md §5 (F1)*

### Q2 – ptá se: IPP fyzik (nebezpečná)

**Otázka:** Co když bude tvar nový?

**Krátká odpověď:** Nevíme. Vynechání celé rodiny tvarů zvedlo chybu nejvýš třikrát. Opravdu neobvyklých výbojů je jen 18 ze 149 a samostatně jsme je nevynechali. Mimo rozsah dat tomu věřit nelze.

**Úplná odpověď:** Nevíme. Když jsme při učení vynechali celou rodinu tvarů, byla chyba osy 1,0 až 3,0krát větší, obvykle 1,2 až 2,4krát, základní síť, pět dělení po výbojích. Osmnáct nejodlišnějších výbojů jsme pak vynechali z učení samostatně: u základní sítě je chyba osy 0,9 až 2,3 milimetru, asi dvaapůlkrát víc než v náhodném dělení, a pěti nejnižším protažením dokonce 2,6 až 4,9 milimetru. Čtrnáct z těch osmnácti je ale z nejstarších čísel výbojů, takže se tu míchá tvar s časnou částí kampaně. O tvarech mimo rozsah dat to nic neříká. (results/ipp1-unusual-heldout.md) Na nejnovějších číslech výbojů, při učení na šedesáti nejnižších, je osa vybraného modelu 0,40 milimetru místo 0,22. V datech leží protažení a trojúhelníkovost na úzké křivce, tedy na jedné rodině tvarů, které stroj ve svých scénářích vytváří. Síť se naučila tuto rodinu a pro tvar mimo ni jí věřit nelze. V uzavřené smyčce řízení samo změní proudy v cívkách, a tím vstupy sítě; to jsme netestovali.

*Zdroj: ipp1-unusual-shapes.md, docs/review-physics.md §5 (F9)*

### Q3 – ptá se: IPP fyzik (nebezpečná)

**Otázka:** Na šumu se síť zhroutí; jak přesní jste na skutečných čidlech?

**Krátká odpověď:** Síť naučená na čistých datech má na šumu osu 10,15 milimetru. Síť učená se šumem má na 30 odložených výbojích osu 2,38. Zda šum v souboru odpovídá skutečným čidlům, nevíme.

**Úplná odpověď:** Síť naučená na čistých datech na šum nestačí: chyba osy vyskočí z 0,38 na 10,15 milimetru, základní síť, pět dělení po výbojích. Při učení na zašuměných datech je to 2,64 milimetru, ale na čistých datech pak 2,22. Vybraný model naučený na čistých datech na šumu selže úplně, proto bychom pro zašuměné vstupy použili síť učenou se šumem: na odložených má chybu osy 2,38 milimetru. Šum v souboru od organizátorů je bílý a posun v něm není. Jeho směrodatná odchylka je asi 16 procent směrodatné odchylky signálu u cívek a 9 procent u smyček toku. Poměr se mezi čidly mění jen málo, což vypadá spíš na šum přidaný úměrně signálu než na změřený; to jen usuzujeme. Zda odpovídá skutečným čidlům, nevíme. Posun jsme vyrobili sami, lineární v relativním čase výboje, kdežto skutečný posun integrátoru roste s absolutním časem. Špatnou kalibraci a výpadek čidla jsme netestovali.

*Zdroj: ipp1-robustness-findings.md, ipp1-final.md, ipp1-data-checks.md, docs/review-physics.md §5 (F7)*

### Q7 – ptá se: IPP fyzik

**Otázka:** Hodnoty se skoro nehýbou.

**Krátká odpověď:** Správně, u osy a bodu X je rozptyl jen 2,4 až 13,7 milimetru. Proto uvádíme i chybu vztaženou k rozptylu: u osy 0,139 u základní sítě, pět dělení po výbojích.

**Úplná odpověď:** Správně, ale jen u osy, bodu X a dotykových bodů: jejich směrodatná odchylka je od 2,4 do 13,7 milimetru, u radiální osy asi 8. Pro bod u limiteru je to 90 a 153 milimetrů, pro proud 114 kiloampérů. Proto uvádíme chyby v milimetrech i vztažené ke směrodatné odchylce: u osy je to 0,139 u základní sítě a 0,68 u lineárního modelu, pět dělení po výbojích.

*Zdroj: ipp1-baseline.md, ipp1-data-checks.md*

### N5 – ptá se: IPP fyzik (nebezpečná)

**Otázka:** Jakou rychlost uvádíte, vybraného modelu?

**Krátká odpověď:** 0,0145 milisekundy patří základní síti. Vybraný model od 24 čísel po výstup: u divertorového plazmatu medián 0,015, u limitovaného 0,027 milisekundy, devadesát devět procent pod 0,1, na vytíženém notebooku. Obojí pod rozpočtem 1 až 10.

**Úplná odpověď:** Číslo 0,0145 milisekundy patří základní síti. Vybraný model: 0,027 milisekundy u limitovaného plazmatu a 0,015 u divertorového, asi dvakrát víc než základní síť. Dřívější odhad 0,18 se při stejném měření nepotvrdil. Obojí je hluboko pod naším rozpočtem jedné až deseti milisekund; ani jedno nezahrnuje sběr dat.

*Zdroj: ipp1-latency-shipped.md, ipp1-latency.md*

### N6 – ptá se: IPP fyzik

**Otázka:** Jak jste na zánicích a startu?

**Krátká odpověď:** Nejhůř na koncích: u vybraného modelu na odložených výbojích je v posledních dvou procentech radiální chyba osy 0,58 milimetru proti 0,11 uprostřed. Zda data obsahují zánik plazmatu, jsme nevyhodnotili.

**Úplná odpověď:** Nejhůř jsme na koncích. V posledních dvou procentech výboje je u vybraného modelu radiální chyba osy 0,578 milimetru proti 0,114 uprostřed, svislá 1,33 proti 0,14, v prvních dvou procentech 0,538. U základní sítě v pěti dělení nese posledních 2 procenta řádků 77,9 procenta čtverce chyby svislé osy a největší chyba jednoho řádku je 284 milimetru, přitom rozptyl svislé osy je 13,7. Příčinu neznáme: může to být síť, ale i rekonstrukce, která je při malém proudu a rychlých změnách nejhůř určená. Zda data obsahují zánik plazmatu, jsme nevyhodnotili.

*Zdroj: ipp1-final.md, docs/review-physics.md §5 (F8)*

### N8 – ptá se: IPP fyzik

**Otázka:** Proč nezprůměrovat řádky?

**Krátká odpověď:** Zkusili jsme tři: na šumu klesla chyba osy z 2,64 na 2,33, na čistých vstupech se zhoršila z 0,38 na 0,57 milimetru. Delší okna jsme nezkoušeli.

**Úplná odpověď:** Zkusili jsme tři po sobě jdoucí řádky: na zašuměných vstupech klesla chyba osy z 2,64 na 2,33 milimetru, na čistých vstupech byla horší, z 0,38 na 0,57. Delší okna jsme nezkoušeli. Okno je počet řádků, ne milisekundy: čas v souboru je relativní a skutečný odstup řádků neznáme.

*Zdroj: ipp1-robustness-findings.md*

### N9 – ptá se: IPP fyzik

**Otázka:** Přežije se výpadek cívky?

**Krátká odpověď:** Netestovali jsme. Samotných 16 cívek dává souhrnnou chybu 0,066 proti 0,063 se všemi 24 vstupy. Žádné čidlo nejmenujeme, pořadí není stabilní.

**Úplná odpověď:** Netestovali jsme. Jediný důkaz: samotných 16 cívek dává souhrnnou chybu 0,066 proti 0,063 se všemi 24 vstupy, samotných 8 smyček toku 0,285, vše základní síť, pět dělení po výbojích. Pořadí vstupů není stabilní (shoda tří způsobů je od minus 0,14 do 0,40), proto žádné čidlo nejmenujeme; cívka IPR13 přežila vyřazování v každém dělení.

*Zdroj: ipp1-inputs.md, ipp1-inputs-controls.md*

### N11 – ptá se: IPP fyzik

**Otázka:** Zadání má 17 parametrů, vy 16.

**Krátká odpověď:** Vybraný model odhaduje 16 hlavních sloupců z 31 v souboru. Ostatních patnáct sloupců jsou doplňkové veličiny pro obrys; ty odhaduje jen základní síť, vybraný model je neodhaduje.

*Zdroj: ipp1-data.md*

### Q4 – ptá se: ML

**Otázka:** Proč je u proudu lineární model lepší?

**Krátká odpověď:** Je, a vybraný model ho používá: 0,035 kiloampéru proti 1,2 u sítě. Proud je skoro lineární funkce vstupů, není to úspěch sítě a nepočítáme to do zisku.

**Úplná odpověď:** Je to tak a vybraný model to využívá. Podle Ampérova zákona je součet částečných Rogowského cívek po celém obvodu úměrný proudu uvnitř, takže stačí lineární model. Na odložených výbojích má chybu 0,035 kiloampéru, základní síť 1,2; to je 0,03 procenta rozptylu proudu, který je 114 kiloampérů. Takto přesná shoda spíš znamená, že proud v datech je odvozen z týchž signálů, než že je změřen nezávisle; to jsme ale neověřili. Není to úspěch sítě a nepočítáme to do tvrzení, že je vybraný model lepší. Na zašuměných vstupech je chyba proudu 4,0 až 4,7 kiloampéru podle modelu, oba učené se šumem.

*Zdroj: ipp1-final.md, ipp1-baseline.md, docs/review-physics.md §5 (F3)*

### Q5 – ptá se: ML (nebezpečná)

**Otázka:** Je validace poctivá? Ladili jste na testu?

**Krátká odpověď:** Částečně. Návrh běžel na křížové validaci přes všech 149 výbojů, takže odložených 30 v ní bylo. Po odložení se nepřeučovalo. Proto obě čísla: 0,13 odložené, 0,23 vývojové.

**Úplná odpověď:** Dělíme po celých výbojích. Základní síť ověřujeme pětkrát jinak, průměrná chyba osy je 0,38 milimetru. Vybraný model jsme navrhovali na křížové validaci přes všech 149 výbojů, takže odložených 30 bylo při návrhu v testovacích částech; po odložení se nic neladilo, jen jsme vybrali jednu ze čtyř variant uvnitř 119 výbojů. Odložené výboje vycházejí lépe než vývojová křížová validace, 0,13 proti 0,23 milimetru, proto uvádíme obě čísla. Interval přes výboje pro odloženou osu je 0,10 až 0,18 milimetru. Pro hlavní srovnání jsme udělali pět semen: osa R vychází 0,133 milimetru se směrodatnou odchylkou 0,006 u vybraného modelu a 0,289 s odchylkou 0,011 u základní sítě; vybraný model je lepší v pěti z pěti u všech sedmi veličin.

*Zdroj: ipp1-final.md, ipp1-improve.md*

### Q6 – ptá se: ML

**Otázka:** Zkoušeli jste jiné modely?

**Krátká odpověď:** Širší a hlubší sítě, jinou ztrátu, rozdíly cívek, soubory sítí i stromy. Nejvíc pomohla zvláštní síť pro limiter: 4,55 proti 10,6 milimetru. Rozdíly pod asi 20 procent bereme jako šum, pokud interval přes výboje nevylučuje 1.

**Úplná odpověď:** Zkoušeli jsme víc: širší a hlubší sítě, jinou ztrátovou funkci, rozdíly sousedních cívek, soubory tří sítí i stromy pro bod u limiteru. Nejvíc pomohla zvláštní síť pro bod u limiteru a lineární model pro proud; chyba bodu u limiteru klesla na polovinu, 4,55 proti 10,6 milimetru na odložených výbojích. Stromy byly horší než zvláštní síť. Zlepšení platí v pěti z pěti semen, u bodu X radiálně je jen o něco lepší. Kromě sítí jsme zkoušeli jen stromy pro bod u limiteru. Nemáme zvláštní ověřovací část, proto rozdíly pod asi 20 procent, pokud interval přes výboje nevylučuje 1 považujeme za šum.

*Zdroj: ipp1-improve.md, ipp1-final.md*

### N3 – ptá se: ML

**Otázka:** Je odložená sada reprezentativní?

**Krátká odpověď:** Ne zcela. Jen 2 z 30 odložených výbojů mají kladný proud a tam je u vybraného modelu osa 0,45 milimetru proti 0,11 na ostatních. Konvenci znaménka neznáme, nevíme tedy, zda jde o opačnou polaritu stroje. Interval osy je 0,10 až 0,18.

**Úplná odpověď:** V souboru má šestnáct ze 149 výbojů kladné znaménko proudu, 7,4 procenta řádků. Konvenci znaménka a vztah ke směru toroidálního pole neznáme. Signály se při obrácení znaménka zrcadlí: střední rozdíl mezi skupinami je 2,00 směrodatné odchylky vstupu a po vynásobení znaménkem součtu cívek IPR 0,13. Ten součet je v podstatě Rogowského cívka po celém obvodu, proto se jeho znaménko shoduje se znaménkem proudu na všech řádcích vývojové i odložené sady. Chyba osy na kladných výbojích je 1,73 proti 0,269 milimetru (základní síť, pět dělení) a u vybraného modelu na dvou odložených výbojích 0,454 proti 0,110. Je to 591 řádků, na jistý závěr málo. Sjednocení znaménka zlepší výboje s kladným proudem o 64 procent a zhorší většinu o 20, proto ho zatím nepoužíváme, rozhodnutí je otevřené (KQ-11).

*Zdroj: ipp1-final.md, docs/review-physics.md §5 (F6)*

### N4 – ptá se: ML

**Otázka:** Kolik z vylepšení je skutečné?

**Krátká odpověď:** Pět semen: vybraný model je lepší v pěti z pěti u všech sedmi veličin, osa o 42 až 60 procent. U bodu X jen o 21, tam říkáme o něco lepší.

**Úplná odpověď:** Pět semen: vybraný model je lepší v pěti z pěti u všech sedmi veličin, zisk u osy, dotykového bodu a bodu u limiteru je 42 až 60 procent. U bodu X radiálně je zisk jen 21 procent, nejbližší semeno 0,96, říkáme jen o něco lepší. Střední kvadratická chyba bodu X radiálně a druhého dotykového bodu je horší (0,454 proti 0,305 a 0,638 proti 0,401 milimetru) a nejhorší jednotlivý řádek šesti veličin je větší.

*Zdroj: ipp1-final-seeds.md*

### N7 – ptá se: ML

**Otázka:** Model, který musí znát druh vstupu?

**Krátká odpověď:** Dodáváme dva: vybraný pro čisté vstupy, síť učenou se šumem pro zašuměné. Jeden vítěz není, učená se šumem je na čistých horší, 1,56 proti 0,31. Přepínání jsme netestovali.

**Úplná odpověď:** Dva modely: vybraný pro čisté vstupy a síť učenou se šumem pro zašuměné. Jeden vítěz neexistuje: modely učené se šumem jsou na čistých datech horší, osa 1,56 proti 0,307 milimetru u základní sítě. Přepínání podle druhu vstupu je předpoklad nasazení, který jsme netestovali.

*Zdroj: ipp1-final.md*

### N10 – ptá se: ML

**Otázka:** Je kamera k ničemu?

**Krátká odpověď:** Je to malá síť na snímcích 48 na 64 z 78 výbojů, 1,3 až 13krát horší než cívky. Ukazuje to na tuto síť, ne že kamera nenese informaci.

**Úplná odpověď:** Je to malá síť na snímcích 48 na 64 bodů, 12 epoch, každý osmý snímek, 78 ze 149 výbojů. Je 1,3 až 13krát horší než cívky a při spojení s cívkami nic nepřidá (1,21 proti 0,24 milimetru, dvě dělení). To ukazuje, že tato síť obrazy dobře nevyužívá, ne že kamera nenese informaci.

*Zdroj: cloud-camera-main.md, cloud-camera-findings.md*

### N12 – ptá se: ML

**Otázka:** A na nejnovějších výbojích?

**Krátká odpověď:** Učení na 60 nejnižších číslech, test na 59 nejvyšších: osa 0,40 milimetru, při náhodném dělení 0,22. Že čísla sledují čas, jsme neověřili.

**Úplná odpověď:** Čísla výbojů zřejmě sledují čas, což jsme s organizátory neověřili. Když učíme na 60 nejnižších číslech a testujeme na 59 nejvyšších, je chyba osy vybraného modelu 0,397 milimetru (při náhodném dělení 0,216), základní sítě 1,23 (0,448). Část rozdílu vysvětluje menší učící sada.

*Zdroj: ipp1-final.md*

### Q8 – ptá se: organizátor (nebezpečná)

**Otázka:** Dá se to nasadit do řízení?

**Krátká odpověď:** Zatím ne. Změřili jsme jen výpočet sítě. Sběr signálů, napojení, nejhorší dobu a skutečně zašuměné signály ne. A jsou to dva modely, přepínání jsme netestovali.

**Úplná odpověď:** Zatím ne. Změřili jsme jen výpočet sítě, na jednom jádru procesoru Apple M5, na vytíženém notebooku: základní síť 0,0145 milisekundy, vybraný model 0,027 u limitovaného plazmatu a 0,015 u divertorového. Zadání chce jednotky až desítky milisekund, náš rozpočet jedna až deset milisekund, obojí je hluboko pod ním. Celý výboj trvá podle organizátorů 150 až 200 milisekund, ale čas v souboru je relativní a skutečný odstup řádků neznáme. Na běžném systému se ojediněle objeví špičky: dřívější měření dalo 99 procent pod 0,65 milisekundy, největší 21 milisekund. Neměřili jsme sběr a integraci signálů, chování signálů za provozu, uzavřenou smyčku, výpadek čidla ani nejhorší dobu na systému reálného času. Řízení polohy navíc potřebuje rychlost změny polohy, a tu jsme neměřili. Jsou to také dva modely, pro čisté a pro zašuměné vstupy, a přepínání mezi nimi jsme netestovali. Bez toho bych to do řízení nedal.

*Zdroj: ipp1-latency-shipped.md, ipp1-final.md, docs/review-physics.md §5 (F10)*

### Q9 – ptá se: organizátor

**Otázka:** Pomůže to COMPASS Upgrade?

**Krátká odpověď:** Model je naučený jen na COMPASSu, na jiném stroji by se učil znovu. Se 30 učícími výboji je osa 1,47 milimetru; kolik výbojů potřebuje nový stroj, nevíme.

**Úplná odpověď:** Náš model je naučený jen na COMPASSu. Na jiném stroji se mění geometrie, čidla i cívky, takže by se musel učit znovu, ne jen doladit. U základní sítě je s 30 učícími výboji chyba osy 1,47 milimetru; kolik výbojů potřebuje nový stroj, nevíme.

*Zdroj: ipp1-robustness-findings.md*

### Q10 – ptá se: organizátor

**Otázka:** Co když se plete a neřekne to?

**Krátká odpověď:** Pět sítí s různým začátkem: na deseti procentech nejnejistějších řádků je chyba 8krát větší a nesou 47 procent celé chyby. Je to varování, ne pravděpodobnost.

**Úplná odpověď:** Síť sama vydá jen číslo. Zkusili jsme pět sítí s různým náhodným začátkem, základní síť, pět dělení po výbojích: na deseti procentech řádků, kde se nejvíc rozcházejí, je chyba 8krát větší než na zbytku. Ty řádky nesou 47 procent celé chyby. Je to použitelné varování, ne pravděpodobnost chyby, a netestovali jsme ho na neobvyklých tvarech ani na zašuměném vstupu. Slabá místa známe: bod u limiteru, začátek a konec výboje a šum. V prohlížeči jste viděli špatný výboj, rozdíl mezi čárami byl vidět. (Číslo říkej jen po ověření: odchylka osy 0,22 milimetru. Bez ověřeného čísla neříkej žádné.)

*Zdroj: ipp1-uncertainty.md*

### N13 – ptá se: organizátor

**Otázka:** Proč věřit 99,3 procenta?

**Krátká odpověď:** Základní síť má 0,993 v pěti dělení, vybraný model 0,9916 na odložených výbojích. Zda jsou chyby u přechodu mezi konfiguracemi, jsme zvlášť nevyhodnotili.

**Úplná odpověď:** Základní síť má 0,993, pět dělení po výbojích; na odložených vybraný model 0,9916, základní síť 0,9892. Chyby základní sítě v pěti dělení se dělí zhruba rovným dílem mezi obě konfigurace, 49 a 51 procent čtverce chyby. Příznak je tvrdé rozhodnutí na spojitém přechodu, takže chyby čekáme právě tam, ale na přechodu jsme je zvlášť nevyhodnotili. Chyby bodu X a dotykových bodů jsme počítali jen na řádcích, kde tyto body podle rekonstrukce jsou; v provozu by je řídil odhadnutý příznak a jeho chyby na přechodu jsme nezměřili.

*Zdroj: ipp1-baseline.md, ipp1-final.md, ipp1-distribution.md*

### N14 – ptá se: IPP fyzik

**Otázka:** Rekonstrukce potřebuje proudy v cívkách pole a model komory. Vy máte jen 24 čidel. Jak je to možné?

**Krátká odpověď:** Nevíme, co všechno rekonstrukce použila. Naše síť dostává jen těch 24 čidel. To, že to funguje, ukazuje, že v těchto 149 výbojích jsou ostatní veličiny téměř určeny čidly, tedy že výboje patří do úzké rodiny scénářů.

**Úplná odpověď:** Nevíme, co všechno rekonstrukce použila. Jako vstup máme jen těch 24 čidel. To, že to funguje, ukazuje, že v těchto 149 výbojích jsou ostatní veličiny téměř určeny čidly, tedy že výboje patří do úzké rodiny scénářů. Prvních pět hlavních složek nese 99,93 procenta rozptylu vstupů, ale síť jen s pěti složkami má chybu osy 2,63 milimetru místo 0,41. Dvanáct čidel vybraných pivotovanou QR dává souhrnnou chybu 0,065, vybraných podle důležitosti pro síť 0,077, proti 0,063 se všemi 24 (corrected by Lead pass 23 Oct), ale tam se síť učila znovu na podmnožině; výpadek čidla za běhu jsme netestovali. Když jsme při učení vynechali celou rodinu tvarů, byla chyba osy 1,0 až 3,0krát větší.

*Zdroj: presentation/pitch-script.md, docs/review-physics.md §5 (F2)*

### F4 – ptá se: IPP fyzik

**Otázka:** Co znamená chyba bodu u limiteru 4,55 milimetru?

**Krátká odpověď:** Bod u limiteru je místo na stěně, kde se plazma dotkne, ne spojitá veličina. Většinou ho trefíme, medián radiální chyby je 0,73 milimetru.

**Úplná odpověď:** Bod u limiteru je místo na stěně, kde se plazma dotkne, ne spojitá veličina. Většinou ho trefíme, medián radiální chyby je 0,73 milimetru. Průměr táhnou řádky, kde síť vybere jiné místo dotyku: v jednom procentu řádků je chyba přes 77 milimetrů (corrected by Lead pass 23 Oct), nejhorší řádek má 357. Vzdálenost plazmatu od stěny, na které řízení záleží, jsme neměřili.

*Zdroj: docs/review-physics.md §5*

### F5 – ptá se: IPP fyzik

**Otázka:** Pro svislou stabilizaci potřebuji rychlost změny polohy. Jak dobrá je?

**Krátká odpověď:** Rychlost změny jsme neměřili. Máme jen krok chyby mezi sousedními řádky. U základní sítě na čistých vstupech je ve svislé ose 1,46 milimetru, zatímco skutečná osa se mezi řádky posune o 2,53 milimetru, v radiální ose 0,45 proti 2,5.

**Úplná odpověď:** Rychlost změny jsme neměřili. Máme jen krok chyby mezi sousedními řádky. U základní sítě na čistých vstupech je ve svislé ose 1,46 milimetru, zatímco skutečná osa se mezi řádky posune o 2,53 milimetru, v radiální ose 0,45 proti 2,5. Na zašuměných vstupech je krok chyby základní sítě naučené na čistých datech 8,4krát větší než skutečný pohyb osy v radiálním směru a 3,1krát ve svislém; po učení se šumem 1,7 a 1,4krát. Tedy výstup kolísá víc, než se plazma hýbe, a rychlost z něj vzít nejde. Časový odstup řádků neznáme.

*Zdroj: docs/review-physics.md §5*




## Plán rozhovoru (pro ChatGPT: vést mě podle něj)

1. Úvod bez odborných slov (2 minuty) a otázka: "Řekni vlastními slovy, co síť dělá a proč to někdo chce."
2. Pojmy ze slovníčku: osm pojmů, ke každému jedna otázka (tokamak, plazma, bod X, dotykový bod, limiter, protažení, výboj, odezva).
3. Čísla: projdi tabulku čísel; pak se ptej na čísla v náhodném pořadí: "Kolik je chyba osy na odložených výbojích a jaký je to protokol?" Chci slyšet číslo, jednotku i protokol.
4. Co neumíme a co jsme neměřili: nové tvary, zašuměné vstupy u modelu učeného na čistých datech, reálný čas na skutečném systému, fyzikální přesnost vůči plazmatu.
5. Přečtu nahlas celý talk (7 minut); ty hlídáš, jestli neřeknu větu ze seznamu zakázaných, a po každém slajdu řekneš jednu věc, která zněla špatně.
6. Zlé otázky: hraješ tři porotce a ptáš se; já odpovídám; ty hodnotíš odpověď 1 až 5 a říkáš přesně, co zlepšit.
7. Na závěr: tři věty, které si mám odnést, a tři věci, ve kterých jsem nejistý.

