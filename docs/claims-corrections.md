# Claims corrections for the slides, the outline and the pitch (from the claims review, Fri 23 Oct 2026)

Source: `docs/review-findings.md` (reviewers 1 to 3). This file holds the **exact Czech replacement sentences** for the
lane that owns `presentation/` (outline, deck, pitch script, glossary). I did not edit anything in `presentation/` or
`viewer/`. The Czech is plain, without English words and without dashes. Every number below was seen in a command output
or a file in `results/` or `out/`; where my own re-measurement differs from the review, both are named.

How to use: for each fix, find the sentence in "Where", replace it with "Replacement", and keep the "Evidence" line
for the notes. The corrected wording rules for the written documents are already applied in `README.md`,
`docs/REQUIREMENTS.md`, `docs/PLAN.md`, `docs/DECISIONS.md`, `results/*.md` (notes) and `out/data-overview.md`.

## 1. Real-time verdict is conditional (high)

**Where:** `outline.md` slide 5 (main sentence, bullets "nejhorší naměřená hodnota 0,090 ms" and "Verdikt: rychlost nebude
překážkou"); `pitch-script.md` slide 5 rows 4:05 to 4:32, the closing rows 6:10 to 6:47 (one number 0,0145 ms), question 8
(Podnikatel) and the table line "one number at the end"; `deck/build_deck.py` slide 5 (title "Jeden odhad trvá setiny
milisekundy" and the verdict line); `slovnicek.md` entry "Odezva".

**Replacement, slide 5 main sentence (outline and deck):**
Výpočet sítě rychlosti nebrání: medián je 0,015 milisekundy na nezatíženém procesoru Apple M5 a 0,03 až 0,07 milisekundy na zatíženém nebo jiném procesoru, rozpočet je 1 až 10 milisekund.

**Replacement, the verdict bullet and the spoken verdict (4:32):**
Ověřili jsme jen výpočet samotné sítě. Neověřili jsme sběr a integraci signálů z cívek, nejhorší dobu na systému reálného času ani přesnost na skutečně zašuměných signálech: síť naučená na čistých datech na šumu selže, síť naučená na šumu dává chybu osy 2,6 milimetru.

**Replacement, the bullet about the worst value (outline slide 5) and the line "v 99 procentech případů do 0,029" (pitch 4:13):**
Celý odhad od surových čísel na vstupu po čísla na výstupu trvá medián 0,053 milisekundy. Na systému bez reálného času se ojediněle objeví špičky až do milisekund. Nejvyšší hodnota z 5 000 měření na nezatíženém počítači byla 0,090 milisekundy, to není horní mez.

**Replacement, the one number at the end (pitch slide 8, rows 6:14 and later):**
0,015 milisekundy. Tolik trvá výpočet sítě na nezatíženém procesoru Apple M5; k tomu patří věta, že sběr signálů a napojení na řídicí systém jsme nezkoušeli.

**Replacement, glossary entry "Odezva":**
Čas od chvíle, kdy model dostane měření, do chvíle, kdy vydá odhad; náš výpočet trvá setiny až desetiny milisekundy podle zatížení procesoru.

**Rule:** name the processor next to every latency number (RP-7: Apple M5 gave 0,015 ms, a Ryzen 5 7535HS on the Fedora
machine gave 0,032 ms). Keep "grafická karta je pro jeden odhad pomalejší než procesor" (0,24 ms).

**Evidence:** `results/ipp1-latency.md` (median 0,0145 ms, max 0,090 ms, one thread, idle machine) and its new note;
`docs/PLAN.md` RP-7 (0,032 ms, Ryzen); review reviewer 2 (0,053 ms numpy in and out, loaded run p99 0,65 ms and max 21 ms;
not re-run by me); `results/ipp1-robustness-findings.md` (2,6 mm after training with noise). `sysctl` on this Mac:
Apple M5.

## 2. Stability claim: the jitter ratio holds on clean inputs for 7 targets only (high)

**Where:** `outline.md` slide 6 bullet "Výstup mezi sousedními časy nekolísá víc než pravda (poměr kolísání je okolo 1)";
`pitch-script.md` row 5:04 ("Výstup přitom mezi sousedními časy kolísá stejně jako skutečnost") and the table line "Jitter
ratio 0.97 for R axis"; `deck/build_deck.py` line near 265 (already says "na čistých vstupech", keep and add the second
sentence).

**Replacement (one sentence, slide 6 and pitch 5:04):**
Na čistých vstupech kolísá výstup stejně jako skutečnost, poměr je 0,97 až 1,07 u sedmi veličin v tabulce. Na zašuměných vstupech kolísá výstup sítě naučené na čistých datech 8,4krát (osa R) a 3,3krát (osa Z) víc než skutečnost, po učení se šumem a posunem 1,7krát u obou os.

**Do not say:** "výstup nekolísá víc než pravda" without "na čistých vstupech", and never quote only the 0,97 of the R axis.

**Evidence:** `results/ipp1-time.md` (0,97 R axis, 1,06 Z axis, 1,07 current, 1,03 elongation, 1,05 triangularity, 1,00
X point, 1,00 strike point 1). My re-measurement with the same definition and time gap filter as `analysis/ipp1_time.py`
on `out/ipp1-predictions.csv` and `out/ipp1-predictions-noise.csv` (script `/private/tmp/claude-501/-Users-bladed-Documents-AIprogramy/9c29f15f-c38a-48af-a9cd-0090fe4aa1ea/scratchpad/jit2.py`, all rows, 5 folds): clean
inputs 0,96 to 1,07 for the 13 non limiter targets and 0,69 and 0,48 for the limiter point; noisy inputs, clean trained
network R axis 8,42 and Z axis 3,25; trained with noise and drift R axis 1,71 and Z axis 1,65. The review quoted 2,7
(R) to 4,4 (Z) without a method; I could not reproduce those figures, so use mine and say "podle `out/ipp1-predictions-noise.csv`".
The ratio is amplitude weighted and says only that the network is smooth when its input is smooth.

**Companion fix (low), error growth, slide 6 and pitch 4:55 (replace "Chyby rostou i na začátku a na konci výboje"):**
Chyby rostou hlavně na konci výboje, 1,6 až 3,7krát oproti středu: osa má na konci 0,9 milimetru, uprostřed 0,24. Na začátku roste jen chyba polohy osy (radiální 2,5krát, svislá 1,5krát), bod X a dotykové body se na začátku výboje nevyskytují.

**Evidence:** `results/ipp1-time.md` table, ratios of the last tenth and of the first tenth to the mean of 30 to 70 % computed
from it (1,56 to 3,72 at the end; R axis 2,47 and Z axis 1,54 at the start).

## 3. Plasma current: the linear model beats the network (medium, wording)

**Where:** `outline.md` slide 4 main sentence ("což je mnohem lépe než lineární model") and bullet "Proud plazmatem: chyba
1,49 kA"; `pitch-script.md` slide 4 main sentence, table line "Plasma current" and question 4 (Odborník na strojové učení);
`deck/build_deck.py` slide 4 if it prints 1,49.

**Replacement, slide 4 main sentence:**
Síť trefí osu, bod X a dotykové body s průměrnou chybou 0,06 až 0,4 mm, u osy více než šestkrát lépe než lineární model; jen u proudu plazmatem je lineární model lepší.

**Replacement, the plasma current bullet and the spoken line:**
Proud plazmatem určí lineární model s chybou 0,035 kiloampéru, síť s chybou 1,49 kiloampéru, proto pro proud použijeme lineární model.

**Optional second sentence (noisy inputs):** Na zašuměných vstupech vyšla chyba proudu 4,0 kiloampéru u lineárního modelu a 4,7 u sítě, obě učené s přidaným šumem a posunem.

**Evidence:** `results/ipp1-baseline.md` (ridge 0,0346 kA, network 1,49 kA, ratio 43); the noisy figures are from
`results/ipp1-improve.md` (summary paragraph, "4.03 against 4.70 kA"), which I read but did not re-run. The ridge for the
current is in `analysis/ipp1_improve.py` (`combo_long`), not yet in the viewer predictions or the baseline table.

## 4. Importance ranking wording (medium)

**Where:** `outline.md` slide 4 bullet "tedy cívky nesou skoro vše" and the pitch-script main sentence "cívky IPR nesou skoro
všechno" and row 2:22 ("Cívky tedy nesou skoro všechno"; "vpravo je pořadí důležitosti vstupů"); `slovnicek.md` entry "Cívka".

**Replacement, row 2:22 and the outline bullet:**
Samotných 16 cívek IPR dává souhrnnou chybu 0,066, samotných 8 smyček toku 0,285, tedy 4,3krát horší. Pořadí vstupů na obrázku je důležitost pro naučenou síť, ne obsah informace, proto neříkáme, které čidlo je nejdůležitější.

**Replacement, slide 4 main sentence tail (pitch):**
samotné cívky IPR stačí skoro na stejnou přesnost jako všech 24 vstupů (0,066 proti 0,063).

**Replacement, glossary entry "Cívka":**
Drát, který měří magnetické pole; samotných 16 cívek IPR dává skoro stejnou přesnost jako všech 24 vstupů.

**Evidence:** `results/ipp1-inputs.md` (0,063 all 24, 0,066 IPR only, 0,285 FL only, ratio 4,32) and its new note. Do not
show a ranking of "important sensors" on a slide.

## 5. The 99,9 percent sentence: variance, not information (medium)

**Where:** any slide, glossary or script line that says "pět složek nese 99,9 % informace" (`out/data-overview.md` and the
Obsidian notes are already fixed; check `outline.md` slide 2 or 3 and the pitch question about unusual shapes, which says
"dvě hlavní složky vstupů nesou 92,8 procenta rozptylu", correct as it stands).

**Replacement:**
Vstupy jsou nadbytečné co do rozptylu: pět hlavních složek nese 99,9 % rozptylu 24 měření. Pro přesnost to ale nestačí: model na těchto pěti složkách má asi 7krát větší chybu radiální polohy osy (2,6 mm místo 0,38 mm).

**Evidence:** PCA 99,925 % at five components (my script, `/private/tmp/claude-501/-Users-bladed-Documents-AIprogramy/9c29f15f-c38a-48af-a9cd-0090fe4aa1ea/scratchpad/fig_var.py`, same as `ipp1_eda.py`); I re-trained the
baseline network on 5 training-fold PCA components with the same 5 folds and 60 epochs (`/private/tmp/claude-501/-Users-bladed-Documents-AIprogramy/9c29f15f-c38a-48af-a9cd-0090fe4aa1ea/scratchpad/pca5.py`): radial axis
2,6472 mm (folds 2,38, 1,94, 3,02, 2,15, 3,74), vertical axis 0,6603 mm against 0,391. The review said "about 2,6 times
worse overall and 7 times on the R axis"; I confirmed the R axis (7,0 times) and the Z axis (1,7 times) but did not compute
an overall figure, so quote the R axis only. The figure title in `analysis/ipp1_eda.py` line 109 still says "informace";
`out/fig-ipp1-structure-variance.png` is the corrected figure used by the overview (owner of `ipp1_eda.py` should rename it).

## 6. The provided noisy file has white noise and no drift (medium)

**Where:** `outline.md` backup section ("Posun čidel je náš vlastní model, ne měřený posun skutečných čidel. Posun škodí
méně než šum stejné velikosti."), `pitch-script.md` question about noise (Odpovídá A, "Posun čidel jsme simulovali
vlastním vzorcem"), slide 7 notes; `out/brief-ipp-uloha-1.md` ("stejná data se šumem a driftem", not edited by me, it is not on my list).

**Replacement, backup and pitch answer:**
Soubor se šumem od organizátorů obsahuje jen bílý šum a žádný měřitelný posun. Šum má asi 9 procent směrodatné odchylky vstupu u smyček toku a 15 procent u cívek. Posun v čase jsme zkoušeli jen na vlastních, uměle vytvořených datech: posun se směrodatnou odchylkou sklonu 0,3 přidá k chybě osy asi 1 milimetr u sítě naučené na šumu a 4,7 milimetru u sítě naučené na čistých datech.

**Evidence:** my measurement on `equil_data.csv` against `equil_data_noisy.csv` (aggregate only): noise SD over input SD
0,153 mean for IPR (0,098 to 0,167) and 0,090 for FL (0,086 to 0,098), median 0,155; 0,309 of the within discharge SD;
mean lag 1 autocorrelation of the noise -0,005; mean correlation with time -0,0002 (mean absolute 0,0497, what white
noise gives). Drift numbers: `results/ipp1-robustness-findings.md` (2,64 to 3,77 mm and 10,4 to 15,1 mm).
"Posun škodí méně než šum stejné velikosti" is dropped: the amplitudes are not comparable.

## 7. Spreads are small only for the axis, X point and strike points (medium)

**Where:** `outline.md` slide 2 or any "rozptyly jsou drobné" line; `pitch-script.md` question 7 (Odborník na strojové učení)
"osa se v datech hýbe jen se směrodatnou odchylkou 8 milimetrů" (true for R, add the rest); glossary if it quotes spreads.

**Replacement:**
Rozptyl je malý jen u osy, bodu X a dotykových bodů, od 2,4 do 13,7 milimetru; u bodu limiteru je 90 a 153 milimetru a u proudu plazmatem 114 kiloampérů, proto chyby uvádíme v milimetrech i vůči rozptylu.

**Evidence:** my measurement on `equil_data.csv`: standard deviation R axis 8,02 mm, Z axis 13,74 mm, X point 8,06 and 12,74
mm, strike points 12,55, 5,03, 11,77 and 2,38 mm, limiter R 89,6 mm and Z 153,3 mm, plasma current 114 186 A; 98 % of the
axis values lie in a band 42,3 mm (R) and 56,4 mm (Z) wide. The limiter point has 66 (R) and 111 (Z) distinct values, a
discrete wall contact.

## 8. GroupKFold is optimistic for "a new campaign" (medium)

**Where:** `outline.md` slide 3 ("Ověření: pětkrát jiné rozdělení") and slide 4 and the limits slide; `pitch-script.md` row
1:32 ("na výbojích, které síť při učení neviděla") and question 5 (Odborník na strojové učení).

**Replacement, slide 3 and pitch 1:32:**
Každý výsledek ověřujeme pětkrát na náhodně vybraných výbojích, které síť při učení neviděla.

**Add one sentence on the limits slide (or in the answer to question 5):**
Čísla výbojů jsou zřejmě seřazena podle času, což jsme s organizátory neověřili. Když zkoušíme na souvislých blocích čísel, je chyba radiální osy asi o polovinu větší, asi 0,6 milimetru místo 0,38.

**Evidence:** review reviewer 1 (0,57 mm R, 0,69 mm Z on blocks); another worker's rerun in `/private/tmp/claude-501/-Users-bladed-Documents-AIprogramy/9c29f15f-c38a-48af-a9cd-0090fe4aa1ea/scratchpad/e1.log`
(contiguous blocks 0,557 mm R and 0,646 mm Z against 0,444 and 0,446 on random groups); baseline 0,377 and 0,391.
Quote "asi 0,6 mm" which fits all three.

**Flag, unverified sentence in the pitch (question 5):** "Architekturu jsme zvolili předem a podle testu neladili."
The review says this is only true if it is true (`ipp1-baseline-run1.md` differs from the final run, and no validation
split exists). Keep it only if the owner confirms it, otherwise write: "Nemáme zvláštní ověřovací část, proto rozdíly pod
10 až 15 procent považujeme za šum."

## 9. Headline means hide the tails (medium, from reviewers 1 to 3)

**Where:** `outline.md` slide 4 sentence "chybou 0,06 až 0,4 mm" and slide 6; `pitch-script.md` row 1:54.

**Replacement (add after the headline mean, slide 4 or 6):**
Průměrná chyba radiální osy je 0,38 milimetru, medián 0,15 milimetru, 99 procent řádků je pod 3,7 milimetru a nejhorší řádky mají chybu desítek milimetrů a více, hlavně na konci výboje. Limitované plazma je asi 2,3krát horší než divertorové.

**Evidence:** my computation on `out/ipp1-predictions.csv` against `equil_data.csv`: R axis mean 0,377, median 0,153, p95 1,21,
p99 3,74, max 64,3 mm; Z axis mean 0,391, median 0,180, p99 3,55, max 284,4 mm; limited rows 0,553 mm against divertor rows
0,237 mm on the R axis (ratio 2,33; 1,76 on the Z axis). REQ-007 stays IN PROGRESS until a per configuration table exists.

## 10. Learning curve wording (low)

**Where:** `outline.md` slide 7 bullet "od 30 výbojů se chyba osy s každým zdvojením zhruba půlí ... a nepřestala klesat";
`pitch-script.md` slide 7 if it repeats it.

**Replacement:**
S 30 výboji je chyba osy 1,47 milimetru (radiální) a 0,95 milimetru (svislá). Od 30 do 119 výbojů klesá zhruba na polovinu při zdvojnásobení, ale s pevným počtem 60 epoch, takže část zlepšení tvoří víc kroků učení.

**Evidence:** `results/ipp1-robustness-findings.md` section 2 table (1,47, 0,83, 0,38 mm R; 0,95 mm Z at 30) and its limit note.

## Outstanding items I did not change

- `presentation/` and `viewer/` (other lanes): every sentence above.
- `out/brief-ipp-uloha-1.md` ("stejná data se šumem a driftem", "order invariant loss"): not on my list.
- `analysis/ipp1_eda.py` line 109 (figure title "Kolik nezávislé informace ..."), `analysis/ipp1_time.py` (KEY lists 7 of 16 targets, NaN in
  the JSON), `analysis/ipp1_latency.py` (no `OUT.mkdir`): code, not wording.
- `out/data-overview.pdf` page 2 shows one real discharge row by row (figure `fig-ipp1-discharge.png`, RP-6, CON-001): the owner has not decided.
- Obsidian `NOW.md` header (last rewritten 14:53) and `Status-Board.md`: not on my list.
- The review's methodology items about a locked test set, a seed average, sign canonicalisation and the limiter as a
  classifier are experiments, not wording; they are recorded as qualifiers in `docs/DECISIONS.md` DEC-003.
