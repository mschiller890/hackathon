# Independent review 3: did the rewrite fix review 2? (Fri 23 Oct 2026, evening)

Reviewer: Kritik 3, a cloud session that saw only the repository at `origin/main` 1e19dec. Read: `docs/review-findings-2.md`, `presentation/pitch-script.md`, `outline.md`, `rehearsal-notes.md`, `docs/deck-fixes.md` and the `results/` files named in the task. There is no data and no Apple M5 here, so nothing was retrained or re-timed. One thing was run: `presentation/deck/build_deck.py` in a scratch copy outside git (it builds from the rewritten script; the committed `slides.pptx` was not touched). Edited: this file and one row of `docs/PLAN.md`.

**Verdict.** The rewrite fixes most of review 2 as text: the script, outline and deck-fixes now agree with each other on protocols, the two models and the unusual-shape wording. Three things are still wrong. (1) `results/ipp1-latency-shipped.md` exists on main since c00981b and says the shipped pair takes 0.027 ms, but script, outline, deck-fixes and `build_deck.py` still carry `[[latency shipped]]` and "asi 0,18 ms / dvanáctkrát"; applying deck-fixes 14.5 verbatim would replace a true closing line with a false one. (2) `slides.pptx` is still deck v3 (last commit a7fca72): every deck item is a written instruction, none is applied, and deck-fixes points at the wrong lines of `build_deck.py`. (3) The script is about 25 to 50 s too long if numbers are read out in full. None of this needs new science.

"Fixed" below means fixed in the script, outline and deck-fixes as written. "Applied to the deck: no" holds for every row.

## 1. H1 to H5, M1 to M7

| ID | Status | What is missing (exact fix) |
|---|---|---|
| H1 shipped speed, accuracy, demo | **Partly** | (a) Measurement now exists, but nobody used it: replace every `[[latency shipped]]` and "asi 0,18" with the measured value (section 2). (b) Slogan: see section 2, X1. (c) Demo intro 2:24 "vidíte základní síť, ne vybraný model, … asi dvakrát přesnější" is fixed (0.133 against 0.307 is 2.3 times). (d) Viewer tile still unnamed: `viewer/index.html:373` says "Doba jednoho odhadu / medián, 1 jádro CPU" and `:509` "Předpověď: neuronová síť"; script and deck-fixes both say "lane U, not edited here", so nobody owns it. One-line edit plus rebuild of the gitignored `viewer/dist`: tile text "Základní síť: doba jednoho odhadu", status line "Předpověď: základní síť". |
| H2 three protocols, "nikdo neviděl" | **Mostly fixed** | Script gives 0,13 / 0,23 / 0,40 with protocols; "zamčené" and "nikdo neviděl" gone from script and outline; deck-fixes 7.1, 7.2, 7.6 put all three protocols and the "návrh na všech 149" caption on screen. Missing: the spoken line 1:37 "odložili před finálním výběrem" lets the audience hear "held out from design"; only the small print and N2 say otherwise. Add 8 words to 1:37: "…odložili před posledním výběrem modelu; náměty na úpravy ale vznikly na všech 149." Also `build_deck.py:345, 354, 357, 368` hard-code "zamčených", "nikdo neviděl", "nasazený model", "zamčená sada"; a rebuild undoes deck-fixes 7.1 to 7.3 (verified: the rebuilt notes of slide 7 still print "zamčená sada"). |
| H3 script against screen, slides 4 to 7 | **Fixed in the script**, one new error | Slide 4 (0,13 / 0,31, 4,55 / 10,6, 0,035 / 1,2), slide 5 (0,0145, 0,021), slide 7 (learning-curve wording, "pevný počet epoch") now match the screen after deck-fixes. "Cívky nesou skoro všechno" and the 0,029 / 0,24 / 0,032 lines are gone. New error on slide 6, 4:29: "v jednom procentu řádků až 78 a 92 milimetrů". 77.5 and 92.2 are the 99th percentile (`ipp1-final.md`, p99 column); the worst rows are 357 and 485 mm. "Až" reads as a maximum, so the tail is understated. Replace by "devadesát devět procent řádků je pod 78 a 92 milimetry", or drop the clause (it also saves 11 spoken words). |
| H4 slide 13 against the speaker | **Fixed**, one nit | Script 5:54 and Q2 and deck-fixes 13.5 now say one thing (factor 1.0 to 3.0, 18 of 149 never held out alone, shapes outside the data not tested). Nit: the slide 13 title "Zná jen tvary z dat a šum v měření mu vadí nejvíc" (deck v3, not touched by deck-fixes) states as a finding what the results say was not tested. Suggest "Šum v měření mu vadí nejvíc; neobvyklé tvary jsme neověřili". |
| H5 noise-free headline | **Mostly fixed** | Slide 7 line (deck-fixes 7.5), slide 14 tile (14.3) and script 5:26, 6:16 give the noisy value 2,38 mm. Missing: spoken 6:38 "Na zašuměných vstupech jsou to jednotky milimetrů" is true for the axis only; limiter point is 25,8 and 38,9 mm and current 4,65 kA (`ipp1-final.md`, `base_aug`). Say "osa na zašuměných vstupech jednotky milimetrů, bod u limiteru desítky". Slide 14 tile (14.3) should name the targets: "osa, bod X, dotykové body". |
| M1 current tile | **Fixed** | Tile and speech say "lineární model; síť měla 1,2"; Q4 states it is almost linear; the "dvakrát lépe" is limited to the axis. |
| M2 camera slide | **Fixed**, one nit | Hidden, no seconds, new title and footnote. Nit: the "1,3 až 13krát" has no baseline named in the backup line and N10 (the 13 is plasma current against the weak network; against the ridge it is several hundred times), and `results/cloud-camera-findings.md:68` and PLAN KQ-6 still say "3 to 13". Pick one range and say "než základní síť na cívkách". |
| M3 unlabelled noise numbers | **Fixed** | Every spoken noise number has its protocol; the 2,33 bar is deleted (13.1); 2,22 is a note under the chart. |
| M4 stale prepared answers | **Partly** | Q4 fixed. Q5 fixed except "rozptylem mezi dělením 0,12", which is in no file of `results/`. Q6 contradicts itself: it says LightGBM trees were tried ("stromy byly horší", correct, `ipp1-improve.md:37-40`) and then "Jiné rodiny modelů jsme nezkoušeli"; write "Kromě sítí jsme zkoušeli jen stromy pro bod u limiteru." Q8 and N5 still quote the unmeasured speed and "dvanáctkrát" (section 2). |
| M5 demo facts | **Partly** | Unverifiable "219 snímků" and "5,7 mm" removed. `[[chyba osy výboje 0]]` appears twice (3:14 and Q10) and only 3:14 has a fallback; give Q10 the same ("rozdíl mezi čárami je vidět"). The line 2:56 "v tomto výboji roste na začátku a na konci" is unchecked (script says "ověřit"); needs one replay by a person, `viewer/data.js` is not in git. The 128 of 149 (85,9 %) claim is verified in `ipp1-claim-support.md`. |
| M6 demo single point of failure | **Partly** | Key H is documented and works in PowerPoint because slide 10 (hidden) follows slide 9; it does not exist in Keynote or Google Slides, so say which tool. The 60 s recording and the second-laptop copy of `viewer/dist/index.html` are still `DOPLNIT`, so open until a person does them. |
| M7 nobody read it aloud | **Open** | Counts redone, no stopwatch reading; `rehearsal-notes.md` still `DOPLNIT`. See section 4: the script overruns if numbers are spoken in full. The close no longer promises "jedno číslo" (script), but deck v3 notes of slide 14 still say "Shrnu to jedním číslem" until rebuilt. |

## 2. The new measurement and what it breaks

`results/ipp1-latency-shipped.md` (one sample, Apple M5, load average 6.4 to 7.2 on 10 cores, random weights of the trained shapes): numpy path from the 24 raw inputs, median **0.0154 ms** diverted and **0.0274 ms** limited, p99 0.057 and 0.093 ms; the evaluation code `ipp1_final.predict()` with torch copies 0.026 and 0.054 ms. The file says itself that the shipped pair is about twice the baseline, "not twelve times", and that 0.1775 ms in `ipp1-improve.md` was not reproduced.

**X1. Stale or contradicted lines (all say 0,18 or "dvanáctkrát" or wait for a placeholder):** script rows 4:05, 6:26, Hlavní věta of snímek 5, Q8, N5, Lead notes (rows "Latency, selected model", "Still pending", H1 row); `outline.md` lines 11, 75, 107, 110; `docs/deck-fixes.md` header, 11.2, 14.1, 14.5 and the last section; `build_deck.py:428-430` (prints "asi 0,18 ms" and cites `ipp1-improve.md` as source on slide 11); PLAN row "Latency of the shipped model" (line 57) and KQ-9(c) still open.

Proposed replacements (Czech, from the file):
- 4:05: "Vybraný model má tři části a jeden odhad trvá asi 0,03 milisekundy, u limitovaného plazmatu medián 0,027."
- 6:26: "Rychlost: základní síť 0,0145 milisekundy, vybraný model asi 0,03, obojí hluboko pod rozpočtem."
- N5: "Vybraný model trvá 0,027 milisekundy u limitovaného plazmatu a 0,015 u divertorového, asi dvakrát víc než základní síť. Dřívější odhad 0,18 se při měření na stejném postupu nepotvrdil."
- Deck 11.2 and 14.1 tile: "0,027 ms / vybraný model, limitované plazma, Apple M5, vytížený notebook"; footnote "numpy, náhodné váhy stejného tvaru, jen čas".
- **Slogan: keep "Desetiny milimetru za setiny milisekundy"** (deck v3 slide 14 already says it). 0,0145 and 0,027 are hundredths of a millisecond. The review-2 change to "desetiny milisekundy" (deck-fixes 14.5, script 6:56, outline line 110, Lead notes) was built on the 0,18 guess and now understates speed and disagrees with the tiles. Drop deck-fixes 14.5; make the 30 s version consistent ("setiny", not "setiny až desetiny").
- Caveats a physicist can still raise, to put in the notes: timing used random weights and a numpy re-implementation; no file checks that it reproduces the trained network's predictions (a 100-row comparison with `predict()` would close that); the noise-trained network needed for noisy inputs was not timed (it has the baseline size); machine was not idle.

## 3. New inconsistencies between script, outline, deck-fixes and the deck

1. **X2. Wrong line numbers in deck-fixes 0.3.** It names `build_deck.py` lines 256/264, 299, 320/330, 356; those lines are unrelated code. The `notes_text` split calls are at lines **262** (`end="0:24"`), **272** (`start="0:24"`), **336** (`end="1:54"`), **346** (`start="1:54"`, `end="2:14"`), **374** (`start="2:14"`). The values it asks for are right (0:24 to 0:21, 1:54 to 1:37, 2:14 stays). Without the 1:54 edit the rebuilt notes of slides 6, 7, 8 hold 30, 14 and 10 s of rows (checked in the scratch build); the 1:30 row belongs to slide 6 only.
2. **X3. "119" means two things.** 1:49 uses 119 for the development set (cross-validation 0,23); 5:38 "se všemi 119 je 0,38" means the 119 training discharges inside each of the five folds on all 149 (`ipp1-robustness-findings.md`, learning curve). Four minutes apart. Say at 5:38 "se všemi učícími výboji, 119 v každém dělení".
3. **X4. The "1 až 10 ms" budget is ours, not the assignment's.** `REQUIREMENTS.md` REQ-002 and `ipp1-latency.md` quote the assignment as "units to tens of milliseconds"; "budget 1 to 10 ms" is the team's verdict text. Deck-fixes 14.2 puts both in adjacent sentences. Speak "zadání chce jednotky až desítky milisekund; počítáme s rozpočtem jedné až deseti".
4. **X5. Source footers on deck notes.** `add_sources` strings in `build_deck.py` (lines 368, 430) print "zamčená sada" and "ipp1-improve.md (0,18 ms nasazeného receptu)" into the speaker notes; deck-fixes does not list them.
5. **X6.** Deck slide 14 tile "Přesný" is replaced by "Přesnost" in deck-fixes 14.3 but `build_deck.py:499` still builds "Přesný"; same class as X5.
6. Script and outline agree with each other on protocols, numbers, the camera slide and the cut order. I found no other disagreement.

## 4. Spoken numbers that are not in `results/`

| Spoken | Where | Status |
|---|---|---|
| 1 až 10 milisekund (rozpočet) | 4:13, 6:26, Q8, N5 | Not in `results/`; team verdict, `docs/REQUIREMENTS.md:42`, `README.md:25`. Assignment wording is "jednotky až desítky ms" (`ipp1-latency.md:3`). See X4. |
| 0,6 milisekundy mezi řádky | Q8, N8 | In no file of the repository except review text; organizers' Data-Brief. It is flagged "orientační" in the answer; keep or drop. |
| rozptyl mezi dělením 0,12 | Q5 | No file contains it (searched `ipp1-baseline.md/json`, `ipp1-inputs.md`, `ipp1-final-seeds.md`, `ipp1-robustness-findings.md`). The only per-seed spread found: R axis candidate 0.133 (SD 0.006), baseline 0.289 (SD 0.011) in `ipp1-final-seeds.md`. Cut or use those. |
| "Ústav připravuje COMPASS Upgrade a chce využít strojové učení" | Q9 | No source in the repository. Either cite the organizers' text or cut. |
| asi 0,18 ms | 4:05 fallback, 6:26, Q8, N5 | Contradicted by `ipp1-latency-shipped.md` (0.0274 limited). Section 2. |
| "asi 0,2" (close) | 6:16 | 0.230 in `ipp1-final.md`; rounding, fine. |
| "dvakrát přesnější" | 2:24 | Derived: 0.307 / 0.133 = 2.3 (`ipp1-final.md`); fine. |
| 86 procent, 78 a 92, třikrát | 3:34, 4:29, 5:54 | Roundings of 85.9 % (`ipp1-claim-support.md`), p99 77.5 and 92.2 (`ipp1-final.md`), 3.0 (`ipp1-unusual-shapes.md`). The 78/92 wording is the problem, not the number (H3). |

Everything else I traced is in `results/` with the printed value: 42 972 / 149 / 24 / 16 of 31 (`ipp1-data.md`), 150 až 200 ms (`ipp1-data.md:14`, marked "not measured by us"), 107 152 and 0,0145 / 0,0209 (`ipp1-latency.md`), 0,133 / 0,307, 4,55 / 10,6, 8,35, 0,035 / 1,20, 2,38, 0,454, 0,578 / 0,114, 99,16 % (`ipp1-final.md`), 0,063 / 0,066 / 0,094 / 0,285 (`ipp1-inputs.md`), 0,38 / 10,15 / 2,64 / 2,22 and 1,47 / 0,38 (`ipp1-robustness-findings.md`), 0,9 / 0,24 (`ipp1-time.md`), 16 % and 9 % noise (0.158 and 0.090, `ipp1-data-checks.md`), 8,1 times and 47 % (`ipp1-uncertainty.md`), 18 of 149 and factor 1.0 to 3.0 (`ipp1-unusual-shapes.md`). Demo discharges 0, 4, 11, 123 are not in `ipp1-locked-test-ids.txt` (checked).

## 5. Length against 7:00

Rows of the table "Co se říká" only (parser: the same five-column rows `build_deck.py` reads), 407 s of speech plus 13 s of silence = 420 s.

| Count | Words | Rate over 407 s | Time at 1.6 / 1.7 / 1.8 words per second (plus 13 s silence) |
|---|---|---|---|
| Space split (Lead notes: 630) | 630 | 1.55 | 6:47 / 6:23 / 6:03 |
| Digit tokens counted twice (Lead notes: 683) | 683 | 1.68 | 7:20 / 6:55 / 6:32 |
| Numbers written out in Czech (my rough rule: "0,0145" = 6 words, "42 972" = 6, "4,55" = 4) | about 733 | 1.80 | 7:51 / 7:24 / 7:00 |

I agree with the Lead's 630 and 683. The honest planning figure is the third row, because the jury hears every digit: **7:00 only at the fast end, 7:25 at a normal pace.** The three placeholders will add about 4 words each. Denser than 2.0 words per second after writing numbers out: 0:38 (2.25), 3:08 (2.33), 3:52 (2.23), 5:16 (2.1), 1:06, 1:37, 1:49, 2:00 (2.0 to 2.07).

**Cut first, in this order (about 55 written-out words, 30 s):**
1. 3:08 "Jeden odhad základní sítě trvá 0,0145 …" (6 s, 14 words): the same number is on the next slide and the viewer tile is not yet labelled.
2. 3:48 "Typický výboj sedí, chybují jen vzácné výjimky." (4 s, 7): 21 of 149 discharges are above 1 mm; "vzácné" is soft.
3. 6:53 "Zbývá napojení na řídicí systém." (3 s, 5): 6:38 already says it.
4. 4:29 the clause "v jednom procentu řádků až 78 a 92 milimetrů" (11 words): wrong wording anyway (H3).
5. 6:09 "Platí jen pro jeden tokamak …" (7 s, 11): move to the slide 7 print (deck-fixes 13.5 already has it).
6. 5:16 shorten to "Učení se šumem to srazí na 2,64, na čistých datech ale zhorší na 2,22." (about 6 words saved).
Then, if still over: the 0:38 row, say "téměř 43 tisíc okamžiků" (saves 4 words, the slide has the exact number). The 13 s of silence in the demo is also a buffer; do not go below about 5 s each. The first, last and middle caveat lines (4:13 second sentence, 5:26, 6:38) are what the jury will trust; do not cut them.

## 6. Would a mixed IPP and ML jury find a claim overstated now?

Yes, five, all cheap to fix:
1. **"Odložené" sounds like held out from design.** The ML juror will ask at once; fix is the 8 words in H2.
2. **"Až 78 a 92 milimetrů"** understates the limiter tail (worst rows 357 and 485 mm). A physicist reading `ipp1-final.md` will see it.
3. **"Desetiny milimetru" in the close** without the target list. It is true for the axis, X point and strike points on clean inputs; the limiter point is 4,55 to 8,35 mm and the noisy axis 2,38 mm. Name the targets (H5).
4. **"Výpočet sítě rychlosti nebrání"** is acceptable because the same sentence says only the network compute was checked, but only once the speed is the measured one and the budget is attributed correctly (X4).
5. **Slide 13 title** asserts "zná jen tvary z dat", which was not tested (H4 nit).

Not overstated any more: the 0,13 headline (three protocols and the 149 admission on screen), current 0,035 kA (labelled linear model), noise (2,38 mm, limiter and current on the slide), unusual shapes, camera (hidden, "this small network").

## 7. Not covered

No retraining, no timing, no viewer run (only `viewer/index.html` source read), no check that the rebuilt deck renders (notes only, no images). `slides.pptx` was read as committed (v3) and the scratch rebuild was discarded. The cloud camera numbers (gate G1) and anything changed after this review are not covered.
