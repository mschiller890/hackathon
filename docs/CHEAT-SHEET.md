# Tahák, dvě strany A4 (pátek 23. října večer; čísla z `results/`, soubor v hranaté závorce)

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
