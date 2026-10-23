# Čti nahlas: sedm minut

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
