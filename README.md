# Tvar a poloha plazmatu z magnetických měření (tokamak COMPASS, úloha IPP 1)

CVUT ML Hackathon 2026. Malá neuronová síť odhadne z **24 magnetických měření** (16 cívek IPR a 8 magnetických smyček FL) **16 čísel**, která popisují polohu a tvar plazmatu, a to za zlomek milisekundy. Klasický výpočet rovnováhy trvá minuty, my potřebujeme jednotky milisekund.

Všechny chyby v tomto textu jsou **shoda s rekonstrukcí Ústavu fyziky plazmatu (ÚFP)**, ne přesnost vůči skutečnému plazmatu: rekonstrukce je naše „správná odpověď“.

## Obsah

1. [Výsledky v kostce](#1-výsledky-v-kostce)
2. [Jak to funguje](#2-jak-to-funguje)
3. [Spuštění: jeden soubor](#3-spuštění-jeden-soubor)
4. [Jak použít natrénovaný model](#4-jak-použít-natrénovaný-model)
5. [Co je v repozitáři](#5-co-je-v-repozitáři)
6. [Odpovědi na cíle zadání](#6-odpovědi-na-cíle-zadání)
7. [Problémy, které jsme měli, a jak jsme je řešili](#7-problémy-které-jsme-měli-a-jak-jsme-je-řešili)
8. [Omezení a výhrady](#8-omezení-a-výhrady)
9. [Důvěrnost dat](#9-důvěrnost-dat)

---

## 1. Výsledky v kostce

**Data:** 149 výbojů, 42 972 časových okamžiků. Na začátku jsme **30 výbojů odložili** (nahodile, seed 20261024, seznam v `results/ipp1-locked-test-ids.txt`) a model se na nich neučí. Zbylých 119 výbojů (34 211 řádků) je vývojová sada. Dělíme vždy po celých výbojích, ne po řádcích, protože řádky jednoho výboje jsou téměř kopie.

### Čistá měření: 30 odložených výbojů (8 761 řádků)

| Veličina | Průměrná chyba | Podíl okamžiků s chybou pod 1 mm |
|---|---:|---:|
| osa plazmatu R | **0,056 mm** [0,048; 0,066] | 99,93 % |
| osa plazmatu Z | **0,065 mm** [0,054; 0,078] | 99,71 % |
| bod X, R / Z | 0,047 / 0,053 mm | 99,8 / 99,8 % |
| dotykový bod 1, R / Z | 0,074 / 0,028 mm | |
| dotykový bod 2, R / Z | 0,052 / 0,012 mm | |
| bod limiteru, R / Z | 2,85 / 4,49 mm | |
| proud plazmatem | 0,034 kA | |
| shoda limiterová / divertorová konfigurace | 99,2 % okamžiků | |

(Hranaté závorky jsou 95% intervaly, bootstrap po výbojích. Celá tabulka s mediánem, p99 a nejhorším řádkem je v `results/bench-mm.md`.)

**Celková přesnost** = 100 × (1 − průměr přes 16 veličin z RMSE / rozptyl reference). 100 % by byla přesná kopie rekonstrukce.

| Model | Celková přesnost, 30 odložených výbojů |
|---|---:|
| základní síť (24 → 256 → 256 → 128 → 16, 107 152 vah) | 91,97 % |
| předchozí vybraný model (`cand`) | 94,12 % |
| **nasazený model (dělení proudem)** | **95,83 %** |

Jednotlivé veličiny jsou na 97 až 100 %. Průměr stahuje hlavně **bod limiteru** (asi 80 až 90 %) a příznak „limiterová / divertorová“ (83,4 % jako regresní veličina, ale 99,2 % jako rozhodnutí: je to 0/1, RMSE ho nadhodnocuje). Grafy: `results/ipp1-accuracy-overall-cs.png`, `...-outputs-cs.png`, `...-ladder-cs.png`.

### Zašuměná měření

Model učený na čistých datech se na šumu **zhroutí** (osa Z řádově stovky mm). Proto je tu druhý model, učený se šumem a driftem, který se dívá na posledních 5 okamžiků výboje:

| Zašuměný soubor ÚFP, 30 odložených výbojů | Osa R | Osa Z | Celková přesnost |
|---|---:|---:|---:|
| zašuměný model (poslední 4 vzorky + aktuální) | **1,85 mm** | **1,25 mm** | 78,1 % |
| model učený jen na čistých datech | 36 mm | 281 mm | selže |

### Jak jsme se k tomu dostali (vývojová sada, 5 dělení po výbojích, jedno semínko)

| Krok | Celková přesnost |
|---|---:|
| základní síť s rozdíly sousedních cívek | 90,46 % |
| užší Huberova ztráta (0,2 místo 0,5) | 91,02 % |
| **dělení všech měření odhadem proudu plazmatem** | **95,24 %** |
| + druhé diference mezi sousedními cívkami | 95,53 % |

Dělení proudem snížilo chybu přibližně na polovinu u všech veličin najednou. Důvod je fyzikální a popsaný v kapitole 2.

### Rychlost

Jeden odhad přes `predict.py` (jen numpy, jedno jádro) trvá medián **0,065 ms** na procesoru AMD Ryzen 5 7535HS (kolega naměřil 0,051 ms na Apple M5). V dávkách po 2048 řádcích je to asi 230 tisíc odhadů za sekundu. Zadání chce odezvu v jednotkách až desítkách milisekund, tedy jsme zhruba stokrát pod limitem. Změřený je jen **výpočet sítě**, ne sběr signálů ani skutečný řídicí systém.

Pozor: živé demo (`mini_pipeline.py`) ukazuje kolem 1 milionu odhadů za sekundu, ale měří **svůj vlastní model v torchi na 6 vláknech**, ne exportovaný model v numpy. Čísla spolu nesouvisí.

---

## 2. Jak to funguje

**Vstup:** 24 čísel v jednom časovém okamžiku (16 cívek IPR01 až IPR16, 8 smyček FL01 až FL08). **Výstup:** 16 čísel: proud plazmatem, poloha osy (R, Z), elongace, trojúhelníkovitost (celková, horní, dolní), bod X (R, Z), dva dotykové body (R, Z), bod limiteru (R, Z) a příznak limiterové konfigurace.

### Základní síť

Plně propojená síť 24 → 256 → 256 → 128 → 16 (aktivace SiLU), 107 152 vah. Učí se po 60 epochách (AdamW, jednocyklový plán učení). Některé veličiny existují jen v jedné konfiguraci (bod X a dotykové body jen v divertorové, bod limiteru jen v limiterové), proto je ztráta **maskovaná**: chybějící cíl nepřispívá žádnou chybou. Základ je v `analysis/ipp1_common.py`.

### Nasazený model čistých dat (`analysis/ipn_model.py`)

1. **Dělení proudem plazmatem.** Pole cívek je úměrné proudům, takže tvar plazmatu závisí na **poměrech** měření k proudu, ne na jejich velikosti. Proud známe ze vstupu samotného (lineární ridge ze 24 měření, chyba 0,03 kA). Každé měření se vydělí odhadem proudu (se znaménkem, takže obrácená polarita dopadne stejně) a proud je jeden z dalších vstupů. Konec výboje, kde je proud poloviční, byl dřív nejhorší místo.
2. **Rozdíly a druhé diference sousedních cívek a smyček** (uvnitř jednoho řádku, ne mezi časy): celkem 67 vstupů.
3. **Dvě sítě.** Obecná síť odpovídá na všech 16 veličin. Limiterová síť se učí jen na limiterových řádcích a rozhodne, na které straně komory (nahoře nebo dole) bod dotyku leží a kde na ní. **Bod limiteru je průměr odpovědi obecné sítě a limiterové sítě.**
4. **Proud plazmatem** je přímo ridge, ne síť (lineární model je u proudu asi 40krát přesnější než síť: 0,035 kA proti 1,5 kA).
5. **Ztráta:** Huberova s delta 0,2 na standardizovaných cílech.

### Zašuměný model (`analysis/noisy_model.py`)

Základní síť, kterou vidí **posledních 5 okamžiků téhož výboje** naskládaných vedle sebe (120 vstupů). Učí se na čistých řádcích plus jedné kopii s přidaným šumem a driftem. Drift je lineární v čase, pro každý výboj a cívku jiný (`naměřeno(t) = správně(t) + šum + koeficient * t`). Průměrování přes okno zmenšuje šum.

### Dva modely, ručně volené

`predict.py` bere čistý model, nebo se zašuměným přepínačem `--noisy` zašuměný. **Automatický výběr v hlavní větvi není.** Model sám nepozná, jaká data dostal.

---

## 3. Spuštění: jeden soubor

```
python3.12 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
python run.py            # asi 3 minuty: živé učení, test na neviděných výbojích, export modelů
python run.py --full     # asi 10 minut: všechny analýzy a všech deset notebooků znovu spočítaných
python run.py --check    # jen zkontroluje balíčky a data
```

**Data** jsou přímo v repozitáři ve složce `data/` (`equil_data.csv` a `equil_data_noisy.csv`), takže se nic nenastavuje: `run.py` i všechny skripty a notebooky je najdou samy a vše nové (modely, mezivýsledky) ukládají do složky `out/` v repozitáři (je v `.gitignore`). Proměnná **`HACKATHON_HOME`** je volitelná: ukazuje-li na jinou složku, která má `data/` s těmito dvěma soubory (nebo původní strukturu `data/raw/ipp1-magnetic/uloha_1-magneticka_data/`), použije se ta. **Repozitář musí zůstat soukromý** (kapitola 9).

Co `python run.py` udělá, krok za krokem:

| Krok | Co se děje |
|---|---|
| 1. Balíčky | zkontroluje, že jsou nainstalované numpy, pandas, scikit-learn, torch a další |
| 2. Data | najde CSV soubory |
| 3. Živé demo | síť se učí epocha po epoše (graf ztráty a chyby osy, přesnost v procentech), pak odhaduje neviděný výboj okamžik po okamžiku a nakonec běží plnou rychlostí. Výpis ukazuje i řádky dat, **nenahrávat a neposílat** |
| 4. Export | `noisy_model.py` natrénuje zašuměný model (`ipp1-noisy.npz`), `ipn_model.py --live` natrénuje nasazený čistý model (`ipp1-ipn.npz`) se živým grafem. Vše do `out/model/` |
| 5. První odhad | odhadne prvních 5 řádků jednoho vývojového výboje s exportovaným modelem |
| 6. Šum | změří osu obou modelů na zašuměném souboru, 30 odložených výbojů |

Model se v kroku 4 učí **jen na 119 vývojových výbojích**, takže odložených 30 slouží opravdu jako neviděná data.

---

## 4. Jak použít natrénovaný model

Váhy jsou odvozené z důvěrných dat, proto nejsou v gitu. Po `python run.py` leží v `out/model/` (nebo v `model/` vedle `analysis/` v odevzdaném balíčku).

```
python predict.py vstup.csv                      # čistý model
python predict.py vstup.csv --noisy              # zašuměný model, potřebuje sloupce discharge a time
python predict.py vstup.csv --model cesta.npz    # libovolný exportovaný model
python predict.py vstup.csv --out odhady.csv --all
```

**Formát vstupu:** CSV se záhlavím a sloupci `IPR01 … IPR16`, `FL01 … FL08` (v jednotkách datového souboru, v libovolném pořadí). Další sloupce (např. `discharge`, `time`) se předají do výstupu. **Výstup:** 16 odhadů na řádek v mm a kA, plus `is_limited_flag` (1 = limiterové plazma). Buňky, které se v dané konfiguraci nevyskytují (bod X při limiteru a naopak), jsou prázdné, `--all` vypíše všechno. Program vypíše, který model načetl, a upozorní na proud pod 10 kA (tam model nemá co dělat). `predict.py` používá jen numpy.

**Zašuměný režim** potřebuje řádky téhož výboje v časovém pořadí se stejným krokem vzorkování jako při učení (odhad vidí posledních 5 řádků).

### Další nástroje

| Příkaz | K čemu |
|---|---|
| `python analysis/bench_mm.py --model out/model/ipp1-ipn.npz --set locked` | odchylky v mm po veličinách (průměr, medián, p99, nejhorší řádek, podíl pod prahem, intervaly) |
| `python analysis/plot_accuracy.py --lang cs` | grafy přesnosti v procentech (česky nebo anglicky) |
| `python analysis/ipn_model.py [--all]` | natrénuje nasazený model; `--all` na všech 149 výbojích |
| `python analysis/make_all.py [--notebooks]` | všechny analýzy v pořadí závislostí |

---

## 5. Co je v repozitáři

| Soubor / složka | Obsah |
|---|---|
| `run.py` | **jediný soubor, který spustí všechno** (kapitola 3) |
| `predict.py` | použití modelu na vlastním CSV (kapitola 4) |
| `analysis/` | skripty: `ipp1_common.py` (načtení dat, síť, skórování), `ipp1_final.py` (receptury a odložené výboje), `ipn_model.py` (nasazený model), `noisy_model.py` (zašuměný model), `mini_pipeline.py` (živé demo), `bench_mm.py`, `plot_accuracy.py`, `make_all.py`, analýzy (`ipp1_eda.py`, `ipp1_baseline.py`, `ipp1_oof*.py`, `ipp1_time.py`, `ipp1_inputs.py`, `ipp1_latency.py`, `ipp1_data_checks.py`) a syntetický test (`synth_equilibrium.py`, `synth_validation.py`) |
| `notebooks/01 … 10` | **všechny závěry**, s uloženými výstupy (jdou číst bez spuštění): 01 data, 02 základní modely, 03 vstupy a důležitost, 04 stabilita v čase, 05 odezva, 06 kamera, 07 nerovnoměrné rozdělení a neobvyklé tvary, 08 šum, drift a množství dat, 09 nasazený model na odložených výbojích, 10 syntetický test se známou pravdou |
| `data/` | **důvěrná data ÚFP** (`equil_data.csv`, `equil_data_noisy.csv`, 42 972 řádků každý). Repozitář je soukromý, kapitola 9 |
| `results/` | agregované výsledky a grafy, které notebooky čtou (žádná surová data) |
| `slides.pdf`, `slides.pptx` | prezentace |
| `requirements.txt` | balíčky a verze, se kterými čísla vznikla |

Nejdůležitější soubory v `results/`: `bench-mm.md` (chyby v mm), `ipp1-ipn.md` (nasazený model, co se zkoušelo a nepomohlo), `ipp1-final.md` (výběr receptur na odložených výbojích), `ipp1-noise-window.md` (zašuměný model), `ipp1-accuracy-*.png` (grafy přesnosti).

---

## 6. Odpovědi na cíle zadání

**Magnetický model (lehčí úloha).** Hotový, kapitola 1: osa 0,06 mm, celková přesnost 95,8 % na neviděných výbojích.

**Je model použitelný v reálném čase?** Výpočet sítě trvá asi 0,05 až 0,07 ms (jedno jádro), tedy zhruba stokrát méně než limit jednotek milisekund. Podmíněně: neověřili jsme **sběr signálů z cívek, nejhorší dobu na systému reálného času ani přesnost na skutečně zašuměných signálech**. Na běžném počítači se občas objeví špičky (nejhorší volání z 3 000 trvalo 0,28 ms), takže horní mez netvrdíme. Grafická karta se pro jeden odhad nevyplatí (je pomalejší než procesor). Notebook 05.

**Přesnost po jednotlivých veličinách.** Tabulka v kapitole 1 a `results/bench-mm.md`. Slabina je **bod limiteru** (3 554 limiterových řádků, málo dat) a **konec výboje**.

**Stabilita v čase** (notebook 04, `results/ipp1-time.md`). Na čistých vstupech kolísá výstup mezi sousedními okamžiky stejně jako skutečnost (poměr 0,97 až 1,07 u sedmi veličin). Chyby rostou hlavně **na konci výboje**: osa má v posledním desetině asi 0,9 mm, uprostřed 0,24 mm (základní síť). Na zašuměných vstupech kolísá výstup čistého modelu 8,4krát víc (osa R), po učení se šumem asi 1,7krát.

**Méně vstupů** (notebook 03, `results/ipp1-inputs.md`). Samotné cívky IPR (16) stačí skoro na stejnou chybu jako všech 24 (0,066 proti 0,063), osm nejlepších už ne (0,094), samotné smyčky FL jsou slabé (0,285). Žebříček důležitosti vstupů je popis natrénované sítě, **ne informační obsah senzoru**: vstupy jsou kolineární, takže se po vyřazení jednoho sítí dobře nahradí.

**Bonusy.**

| Téma | Zjištění |
|---|---|
| Model z kamery | malá konvoluční síť na šedých snímcích 96×128 (78 výbojů, 115 872 snímků): osa R **1,59 mm**, Z 1,99 mm. Magnetický model na týchž snímcích 0,41 / 0,42 mm. Kamera je tedy horší |
| Spojení kamery a cívek | v našem testu **nepomohlo proti samotným cívkám**: kamera sama 1,79 / 2,48 mm (osa R / Z), cívky samy 0,59 / 0,50 mm, spojení 1,54 / 1,13 mm. Spojení je tedy lepší než kamera sama, ale horší než cívky (`results/cloud-camera-multimodal.md`) |
| Černobílá kamera | **žádný rozdíl**: osa R 1,70 mm šedá proti 1,79 mm barevná (`results/cloud-camera-main.md`) |
| Citlivost na posun kamery | o 1 pixel nebo 1 stupeň: bez augmentace chyby stoupnou 1,3krát, s náhodným posunem a otočením při učení zůstanou beze změny (poměr 0,99). 1 pixel a 1 stupeň je ale málo, nenahrazuje skutečně posunutou kameru |
| Množství dat (notebook 08) | z 30 výbojů je chyba osy R 1,47 mm, ze 60 výbojů 0,83 mm, ze 119 výbojů 0,38 mm (základní síť, pevných 60 epoch, takže část zlepšení je víc kroků učení). Limiter se zlepšuje nejpomaleji |
| Čas jako kontext | více vzorků za sebou **na čistých datech škodí** (osa 0,38 → 0,57 mm), **na šumu pomáhá** (chyba 0,2891 → 0,2187), proto jen zašuměný model vidí okno |
| Šum a drift | čistý model na šumu selže, model učený se šumem a driftem dává osu R 1,85 mm. Drift je náš syntetický model (v zadaném souboru je jen bílý šum) |
| Neobvyklý tvar | 18 nejodlišnějších výbojů vynecháno z učení: chyba osy asi 2,5krát větší (ale 14 z nich jsou rané výboje). Nový tvar mimo rozsah dat to netestuje |
| Syntetický test | na simulovaném plazmatu se známou pravdou (Solovʹevovy rovnováhy, notebook 10) najde stejný postup osu na 0,73 / 0,60 mm: **metoda umí najít známé plazma** |

---

## 7. Problémy, které jsme měli, a jak jsme je řešili

| Problém | Co se stalo | Řešení | Výsledek |
|---|---|---|---|
| **Proud plazmatem** | síť určila proud s chybou 1,5 kA | lineární ridge přímo ze vstupu | 0,035 kA, asi 40krát lépe |
| **Veličiny v různých konfiguracích** | bod X, dotykové body a limiter existují jen v části řádků | maskovaná ztráta: chybějící cíl nepřispívá | všech 16 veličin v jedné síti |
| **Pořadí dotykových bodů** | zadání varuje, že se v řádcích může měnit | ověřeno: v datech je `R_strike_point_1` vždy menší než `R_strike_point_2` (0 % řádků opačně, všech 137 výbojů) | žádná úprava není potřeba |
| **Čas ve sloupci `time`** | je normovaný 0 až 1 v každém výboji | nepoužit jako vstup (zadání říká, že tyto sloupce se k učení nemají používat) | model nezná „konec výboje“ |
| **Největší chyba na konci výboje** | proud tam klesá na polovinu a signály jsou slabé | **dělení všech měření odhadem proudu** (fyzika: tvar závisí na poměrech) | chyba přibližně na polovinu u všech veličin, osa 0,38 → 0,056 mm |
| **Bod limiteru: převrácená strana** | síť mezi nahoře a dole zprůměruje a občas se splete o stovky mm (až 485 mm) | limiterová síť, která nejdřív rozhodne stranu, a **průměr** s obecnou sítí | Z limiteru z 8,4 na 4,5 mm. Samotná síť po stranách vycházela **hůř** než průměr |
| **Zašuměná data** | čistý model se zhroutí (osa Z stovky mm) | druhý model učený se šumem a driftem, s oknem 5 vzorků, ručně volený `--noisy` | osa R 1,85 mm, Z 1,25 mm |
| **Jeden model pro čistá i zašuměná data** | zkoušeli jsme jednu síť s příznakem šumu | na čistých datech vycházela o polovinu horší | zůstaly dva modely |
| **Rychlost živého dema pod 800 000 odhadů za sekundu** | první rychlá cesta alokovala v každém volání nová pole ve float64 | float32, předalokované bufery po 2048 řádcích, operace na místě, torch na 6 vláknech, standardizace sloučená do vah | z asi 100 až 400 tisíc na zhruba 1 milion za sekundu |
| **Demo a exportovaný model měří různé věci** | demo ukazuje 1 milion za sekundu, `predict.py` jen asi 230 tisíc | rozdíl je v tom, že demo je jedna síť v torchi, export je numpy | popsáno v kapitole 1, ne zamlčeno |
| **Test není nezávislý** | odložených 30 výbojů jsme použili při výběru dřívějších receptur | uvedeno u každého čísla, ladění nového receptu běželo jen na vývojové sadě | čísla na odložených výbojích berte jako odhad, ne jako úplně čistý test |
| **Šum mezi běhy** | seed mění výsledek o 8 až 19 % | rozdíly pod asi 5 až 10 % nepovažujeme za prokázané, uvádíme jedno semínko a intervaly po výbojích | poctivější závěry |
| **Metrika příznaku `is_limited`** | RMSE ho u binární veličiny nadhodnocuje: 84,8 % v průměru, ale 99,2 % správných rozhodnutí | uvádíme obojí | celková přesnost je tím asi o bod nižší, než by byla se správným měřením úspěšnosti rozhodnutí |
| **Žebříček důležitosti vstupů** | vstupy jsou kolineární | nepíšeme „důležité senzory“, jen popis sítě | notebook 03 |
| **Chyby v nástrojích** | `python -I` skrýval nainstalované balíčky (analýzy padaly), notebook 05 spadl na stroji bez Apple GPU | `-I` odstraněno, notebook počítá bez GPU | `python run.py --full` doběhne na běžném PC |
| **Opakovatelnost** | trénování není bit po bitu stejné (vlákna) | poslední číslice kolísají | popsáno v `results/ipp1-ipn.md` |

Co jsme zkoušeli a nezlepšilo to výsledek (podrobně `results/ipp1-ipn.md`): širší síť, delší učení, weight decay, velikost dávky, GELU, šum na vstupu, předchozí vzorky jako další vstup (horší na čistých datech), změna proudu za krok, kvadratická ztráta pro limiter.

---

## 8. Omezení a výhrady

* **Shoda s rekonstrukcí, ne s plazmatem.** Nevíme, jak přesná je sama reference, zvlášť při rychlém zániku plazmatu.
* **Limiter je slabé místo.** Asi 1 až 2 % limiterových řádků je mimo o víc než 32 mm, nejhorší řádky o stovky mm (v datech má bod dotyku jen asi 111 různých poloh). Největší jednotlivá chyba mimo limiter je 19,6 mm (osa Z, jeden řádek na konci výboje).
* **Zašuměný model je slabší** (78 % celkově, osa 1,85 / 1,25 mm) a otestovaný jen na bílém šumu zadaného souboru. Drift je jen naše simulace.
* **Reálný čas jsme neověřili** (sběr signálů, nejhorší doba na systému reálného času).
* **Neobvyklé tvary:** model je naučený na tvarech z dat, na úplně nový tvar nemáme test.
* **Kamera:** malá síť na 78 výbojích, slabší než cívky; snímky jednoho výboje jsou téměř kopie, takže nezávislých vzorků je málo.
* **Jedno semínko** u většiny porovnání.
* **Slidy** nemusí mít poslední čísla; poslední čísla jsou v `results/bench-mm.md` a `results/ipp1-ipn.md`.

## 9. Důvěrnost dat

Data poskytl ÚFP AV ČR jen pro účely tohoto hackathonu a **není dovoleno je zveřejnit ani zpřístupnit nikomu mimo účastníky hackatonu**.

* Obě datová CSV (`data/equil_data.csv`, `data/equil_data_noisy.csv`, dohromady asi 87 MB) **jsou v tomto repozitáři**, aby šlo všechno spustit hned po naklonování. Proto musí zůstat **soukromý** a přístup mají mít **jen účastníci hackathonu** (teď dva přispěvatelé). **Nikdy ho nezveřejňujte, nevytvářejte z něj veřejný fork ani balíček a nekopírujte `data/` jinam.** Soubory zůstávají navždy v historii gitu, i kdyby se později smazaly.
* Natrénované váhy modelů jsou z dat odvozené, proto se do gitu nedávají (`out/` a `model/` jsou v `.gitignore`) a organizátorům se předávají zvlášť.
* Živé demo vypisuje do terminálu řádky dat: ukazujte ho v místnosti, ale **nenahrávejte ho a nepřeposílejte**.
