# Jury simulation: three jurors and a ranking guess

Written Fri 23 Oct 2026 about 20:40 CEST by a cloud session (branch `cloud/jury-sim`, from `origin/main` fc41e7a). Nothing was re-run and nothing in
the deck, script or results was edited; there is no data and no Apple M5 here. Every remark below quotes a line or names a file.

## 0. How to read this

**What was read.** `README.md`, `presentation/pitch-script.md` (the spoken text), `presentation/outline.md`, `docs/deck-fixes.md`,
`docs/deck-visual-qa.md`, `docs/demo-facts.md`, `results/ipp1-final.md`, `docs/hackathon-rules.md`, `docs/REHEARSAL.md`, `docs/SUBMISSION.md`,
`docs/REQUIREMENTS.md`, `results/ipp1-traintest-gap.md`, the first and last markdown cell of each of the eight notebooks, and the deck itself
(`presentation/deck/slides.pptx`, rendered to PDF with LibreOffice and read with python-pptx). `docs/HANDOUT.md` does not exist, so there is no
leave-behind sheet for the jury.

**Limits of this simulation.** One model plays three roles, so the jurors are not truly independent: I wrote each sheet separately, using only what
that juror would plausibly see or know (J3 sees the talk, the slides and the demo; J1 and J2 may also open notebooks and `results/`). I did not hear
the talk, nobody has timed it, I have not seen the viewer run, and I have not seen the deck in PowerPoint on a projector. The jury's real criteria
are unknown (`docs/hackathon-rules.md`: "Judging criteria and weights | An expert committee judges after the presentations. Criteria and weights:
UNKNOWN"). The other teams are unknown, so no score below is calibrated against them.

**"Use of the time"** is read as both things: how well the 22 hours were spent (breadth and depth delivered) and how well the talk slot is used.

**Facts about the event that shape the scores** (`docs/hackathon-rules.md`, KSI FJFI page): "Secondary-school students, teams of 2 to 4, basic
programming, Python recommended"; "At most 15 minutes per team"; "Room for presentations / projector / how a demo laptop connects | UNKNOWN";
prizes 25,000, 15,000 and 10,000 CZK. The 7 minutes are the owner's choice: `docs/SUBMISSION.md` says "The 7 minutes and the video come from the owner
(Assignment note), not from the organizers' text (OQ-002)". This team has two speakers and an enormous amount of material for a student event.

## 1. Scores (1 to 10)

| Criterion | J1 plasma physicist (IPP) | J2 ML researcher | J3 teacher / organiser | Mean |
|---|---:|---:|---:|---:|
| Understanding of the task | 7 | 8 | 6 | 7.0 |
| Technical quality | 7 | 8 | 6 | 7.0 |
| Honesty about limits | 9 | 9 | 7 | 8.3 |
| Functionality / demo | 7 | 6 | 7 | 6.7 |
| Presentation clarity | 6 | 6 | 4 | 5.3 |
| Use of the time | 8 | 8 | 6 | 7.3 |
| **Overall** | **7** | **8** | **6** | **7.0** |

The spread is the story: the two expert jurors reward depth and honesty, the juror who values students, clarity and teamwork scores it six, mostly
because of the talk and not the work. A mean of 7 is not a winning score by itself; whether it wins depends on rivals nobody can see.

## 2. J1: plasma physicist from the Institute of Plasma Physics

Knows COMPASS, has seen the classical reconstruction (EFIT++ or similar), possibly set the task. Listens for physics, for what the truth is, for
what is new.

**Liked.**
- The opening is physically correct and short: pitch row 0:00 "Protažené plazma je svisle nestabilní a bez rychlého řízení uhne ke stěně." A
  student team that says this has read the introduction.
- The truth is named for what it is, aloud: row 6:17 "Shoda s rekonstrukcí ústavu na čistých vstupech" and Q1 "Chyba 0,13 milimetru na odložených výbojích je tedy chyba proti ní, ne proti
  skutečnému plazmatu." Most teams will say "accuracy against the true shape".
- The team noticed the plasma current is "téměř přesně lineární funkce 24 vstupů" (Q4) and shipped a ridge for it (0,035 kA against 1,20): a physicist
  sees Ampère's law in that and approves that it is not sold as a neural-network success.
- The failure discharge 147 is shown on purpose: row 3:12 "Osa je vedle o třicet tři milimetrů a bod u limiteru o sto pět".
- Real-time verdict is not oversold: slide 11 "Neověřeno: sběr signálů, nejhorší doba, zašuměné signály"; README "Not verified: acquisition and integration of the coil signals, the worst case on a real-time system".

**Bothered.**
- **0,13 mm is below what the measurement can support, and the screen never says what it is compared with.** I checked the text of every deck
  slide: none contains "rekonstruk" or "ústav". Slide 7 title "Na 30 odložených výbojích: osa 0,13 mm", tile "průměrná chyba osy"; slide 14
  "Přesnost osa 0,13 mm". Only the speaker (and the notes) say "proti rekonstrukci". A physicist reading the slide alone reads it as error against the
  plasma. And the team says itself it did not measure how accurate the reconstruction is (Q1).
- **The headline is the most favourable of three protocols.** `results/ipp1-final.md`: 0,133 on the 30 set aside, 0,230 in development cross validation,
  0,397 when trained on the 60 lowest ids and tested on the 59 highest ("ids are chronological"); the baseline goes from 0,448 to 1,23. The talk gives all three, which is
  good, but the title and the close use 0,13. README admits "these 30 are not 'never seen'". For a new campaign the number that matters is closer to 0,40.
- **No prior work is mentioned.** `docs/hackathon-rules.md` lists Windsor et al., "Real-time electronic neural networks for ITER-like multiparameter
  equilibrium reconstruction and control in COMPASS-D" as "good prior-art line for a slide". My grep of `presentation/pitch-script.md` and `outline.md` for
  Windsor, EFIT, "předchozí", "literatur" finds nothing. Slide 2 reads "Otázka: odhadne malá neuronová síť tvar plazmatu ... dost přesně a dost rychle?" as if
  nobody had asked it on this very machine.
- **The "shape" is four points.** README and `docs/demo-facts.md`: it "predicts 16 of 31 targets, so it draws predicted POINTS ... not a predicted outline". The pitch says so
  honestly ("Celý obrys neodhadujeme"), but the title of the work is "tvar plazmatu".
- Noise: the provided file has "bílý šum a žádný měřitelný posun" (Q3), so drift, the thing that really hurts integrated Rogowski coils, was tested only on
  self-made data. The talk says that, but 2,38 mm on white noise says little about a real campaign.
- Speed numbers are for "náhodné váhy stejného tvaru, jen čas" on a busy laptop (slide 11 tile 3, `results/ipp1-latency-shipped.md`), not the trained
  noise network and not a real-time system. Honest and still soft.

**Three questions.**
1. "Jak přesná je samotná rekonstrukce, se kterou se porovnáváte? Co když je vaše síť přesnější v tom, že kopíruje její chyby?" (answer exists: Q1, but it ends in "jsme neměřili".)
2. "Co se stane s kalibrací cívek v další kampani, nebo když vypadne cívka?" (N9: "Netestovali jsme".)
3. "Zkoušeli jste to na výbojích s jiným scénářem než v datech, nebo na startu a zániku, kde řízení potřebuje odhad nejvíc?" (N6: "Nejhůř na koncích"; sudden disruptions are "nejsou v datech".)

**What would move J1 by 2 points.** On screen, next to every error: "proti rekonstrukci ústavu"; one line of prior art; and the range "0,13 až 0,40 mm podle
protokolu" instead of the single best number. J1 would then score understanding and honesty 9 and the overall 8 to 9.

## 3. J2: machine learning researcher

Cares about the protocol, leakage, baselines, variance, whether the claim is supported.

**Liked.**
- Grouped splits and a held-out set, said early: row 0:58 "Dělíme vždy po celých výbojích, aby se model netestoval na tom, co už viděl."
- The contamination of the 30 is confessed, not hidden: row 1:33 "náměty na úpravy ale vznikly na všech 149" and N2 "těch 30 bylo při návrhu v testovacích částech".
  Very few student teams will do this.
- Variance is addressed: `results/ipp1-final-seeds.md` as quoted in Q5, "osa R vychází 0,133 milimetru se směrodatnou odchylkou 0,006", better in five of five seeds, plus a bootstrap interval.
- It reports where the "better" model is worse: pitch N4 "Střední kvadratická chyba bodu X radiálně ... je horší (0,454 proti 0,305)".
- Negative results are kept: the cloud search was tested and not shipped (`results/ipp1-search-dev.md`: "Verdict: do not ship"), the camera is "1,3 až 13krát horší".
- The train against held-out gap is measured (`results/ipp1-traintest-gap.md`, shipped model R axis 0,095 train, 0,230 held out, a factor 2,4).

**Bothered.**
- **Three models and three protocols in 7 minutes.** `pitch-script.md` line 15: "základní síť ... vybraný model ... Pro zašuměné vstupy se používá třetí věc". The jury has to hold a 3 by 3 table in
  its head. Row 5:19 "Učení se šumem to srazí na 2,64, na čistých datech ale zhorší na 2,22" is then a fourth cell.
- **The model that wins on clean data fails on noise, and the model for noise loses on clean data.** The talk says so (N7: "Jeden vítěz neexistuje"), and deployment would need to know
  which input it gets ("přepínání ... jsme netestovali"). The honest result is also an incomplete product.
- **Baselines are thin.** Ridge and the team's own MLP. Trees were tried only for the limiter point (Q6: "jen stromy pro bod u limiteru"). No kNN, boosted trees on all targets, or Gaussian process. A reviewer asks
  whether 107 152 parameters are the right size at all for 149 discharges.
- **One seed for most numbers, 30 held-out discharges (2 with reversed polarity).** The pitch's own Q5 question says "jedno náhodné nastavení". Fine as disclosed; it limits every claim below about 10 to 15 percent.
- **The notebooks barely contain models.** Notebook 09 conclusion: "The notebook trains nothing: it recomputes all metrics from the cached predictions"; notebooks 07 and 08 open with "This notebook is **data free**" and parse
  `results/*.md`. Only `02` trains. `docs/REQUIREMENTS.md` REQ-005 asks for "Jupyter notebooks ... with the models and graphs". The models are in `analysis/*.py`, which a juror opening the
  notebooks will not know. README also still says "Five Jupyter notebooks" for a folder of eight (01 to 05, 07, 08, 09; there is no 06).
- **Nothing says what each team member did or whether tools helped.** (See J3; J2 asks the same for a different reason: reproducibility and who understands the code.)

**Three questions.**
1. "Proč 30 výbojů z 149 a proč s nimi nejsou slabé výsledky v pěti semenech u bodu X?" ending in: "Který z čísel 0,13, 0,23, 0,40 byste dal do abstraktu?"
2. "Zkoušeli jste něco jiného než plně propojenou síť, třeba gradientní stromy na všechny veličiny? Jak velká je síť vzhledem ke 149 výbojům a není přeučená?"
   (Gap table exists: 2,4 to 3,8 times on development, not in the script.)
3. "Co by se změnilo, kdybyste podle času rozdělili po 20 výbojích a ne po 60, a proč jsou čísla výbojů chronologická, když jste to s organizátory neověřili?"

**What would move J2 by 2 points.** One slide or one backup slide that puts the single honest table on screen (shipped model, three protocols, one row each) instead of
three sentences in a spoken pass; one sentence on why a small network and not trees; notebook 09 containing the training call of the shipped model, or one sentence that the models live in
`analysis/`. J2 would then give technical quality 9 and the overall 9.

## 4. J3: teacher / organiser (the event is for students)

Values clarity, teamwork, a demo that works, whether the students understood what they did. Cannot verify most of the numbers; judges the room.

**Liked.**
- The first 38 seconds work for a layperson: a picture of wall damage, "Plazma se musí držet daleko od stěny během milisekund, klasický výpočet tvaru trvá minuty" (slide 1 and 2, hourglass picture).
- A live viewer with a true and a predicted shape is exactly what a school jury likes to see; it runs offline ("Prohlížeč běží bez internetu") and is a polished tool (`presentation/assets/viewer-middle-divertor.png`).
- The team says what is not finished. "Pro řízení model ještě není" (row 6:38) is something a teacher respects.
- Both team members speak and the slides are consistent in style (dark theme, one idea per slide on 1, 2, 6, 9).

**Bothered.**
- **Too many numbers to follow.** In the spoken column I count 52 tokens that contain a digit in 7 minutes (my count), slide 4 and slide 7 eleven each, with the sentence rate the script itself estimates as
  "about 25 s over" at a normal pace (Lead notes: "730 words ... 7:24 at a normal pace, 7:01 only at 1.8 words per second"; `presentation/timing.py`: 8:15 at 1.6 words per second, 7:20 at 1.8). No one has timed it ("no stopwatch reading exists (M7)").
  A room of students and teachers cannot retain "0,13, 0,23, 0,40, 0,307, 4,55, 10,6, 0,035, 1,2".
- **Slide text is small.** After the visual QA fixes the deck still has text under 18 pt on most screens (python-pptx: slide 4 38 of 48 words, slide 12 37 of 50, slide 13 37 of 49; smallest 13 pt). From the back of a classroom
  the tile captions are unreadable; only the big numbers are.
- **The talk is 7 minutes in a 15 minute slot.** `docs/hackathon-rules.md`: "At most 15 minutes per team". The jury may feel the team was too hurried and too dense for a time it did not have to compress to; or it may be a deliberate rule from the assignment, which no file shows.
- **The demo's first 40 seconds look like nothing happens.** On a typical discharge the model's four marks sit on the true ones (`viewer-middle-divertor.png`: error 0,25 mm, window ±1 mm). The one clear moment is the bad end (discharge 147), which is rough and
  gets only 14 seconds. A layperson sees "two overlapping dots" first.
- **Teamwork is not visible.** Speaker split in the script: A 263 s (15 s silent), B 152 s, together 5 s. B has the data, speed and noise slides; A answers 16 of the 23 prepared questions (counted from "Odpovídá A/B" lines). Nothing in
  `pitch-script.md`, `outline.md` or `REHEARSAL.md` mentions how the team worked; my grep for "Claude", "agent", "umělá inteligence" returns no hit. Whether AI tools were allowed is an unanswered question for the organisers
  (`docs/hackathon-rules.md` question 7: "May teams use external pretrained models, online AI tools and internet during the event?"). In a school event this is the first question after the numbers.
- Jargon survives: "p99", "souhrnná relativní chyba", "křížová validace", "limitované plazma" (glossed only in small print).

**Three questions.**
1. "Kdo z vás co udělal a kdo z vás tomu rozumí? Pomáhal vám při tom nějaký nástroj, jaký, a jak jste jeho výsledky kontrolovali?"
2. "Proč jste mluvili jen sedm minut, když jste mohli patnáct, a co byste ještě ukázali?"
3. "Co byste řekli žákovi, který vidí tokamak poprvé: k čemu to je a proč je to těžké?" (the opening slides answer this; the closing does not repeat it.)

**What would move J3 by 2 points.** One plain sentence on who did what and how tools were used (and a prepared answer); two or three numbers instead of fifty; a visible moment in the demo that a layperson understands in
five seconds (the failing end first, then the typical discharge). J3 would then give clarity 6 to 7 and the overall 8.

## 5. Synthesis

### 5.1 Where they agree and disagree

- All three: the work is deeper and more honest than a school hackathon entry would normally be. J1 and J2 call honesty the best asset, J3 does not penalise it but cannot weigh it.
- All three: the talk carries too many numbers (J3 hardest) and the screen does not hold the claim by itself (J1: no "vůči rekonstrukci"; J2: protocols spoken, not shown; J3: text size).
- They disagree on what to forgive. J1 and J2 forgive density because the numbers are traceable; J3 does not, and J3's vote is probably not decisive, but J3 is the juror who judges the talk as a student event.

### 5.2 Expected rank

**Top 10 percent on content, "top 10 percent, podium plausible but not safe" overall.** Reasons, none of them a probability:

- The event is for secondary-school students with "basic programming" in 22 hours (`docs/hackathon-rules.md`). A usual entry on this task loads the file, fits a model, shows error plots, and maybe a small interface. This entry has every
  required item and every bonus with a number in `results/` (`docs/REQUIREMENTS.md`: REQ-003, 004, B01 to B07 `DONE`; REQ-B08 `IN PROGRESS`), a held-out set, seeds, an intervals check, a latency study, a noise study and a viewer.
- Anyone on the committee who knows the task sees at once that this is far beyond a baseline. The honesty on limits is rare at any level.
- Why not "certainly top 3": (a) the criteria are unknown and one of them may be "understandable to students" or "teamwork", where this talk scores lowest; (b) teams on the other COMPASS task, or a cleaner story with a demo a jury grasps in 30 seconds,
  are invisible to me; (c) the two speakers and the density risk hurting the first impression that a committee deliberating from memory after 16:30 will keep; (d) the unanswered authorship question can cost trust.
- What would put it in the **top third** instead: the talk overruns or is cut off before the close, the demo fails without an immediate backup, or a juror's authorship question is answered badly.
- What would make it **middle**: only if the criteria are mainly presentation to a lay audience and the talk is delivered as written. I consider that unlikely but not excluded.

### 5.3 The five changes with the biggest expected gain per hour, possible before Sat 10:00

Ordered by my judgement of gain per hour (estimates of effort are mine; no measurement). All of them are presentation or rehearsal items, so none breaks the results freeze (Sat 01:00); the first two are cheap.

1. **Put the evidence label and the range on the screen (about 30 min, lane K `build_deck.py`).** Slide 7 title: keep one number but add the compared thing and the range, for example the line "proti rekonstrukci ústavu; podle protokolu 0,13 až 0,40 mm". Same on slide 14
   ("Přesnost ... proti rekonstrukci ústavu"). Add one line on slide 4 or in the spoken row 1:06: earlier neural networks for equilibrium reconstruction on COMPASS-D exist (title-level source in `docs/hackathon-rules.md`; do not claim more than the title). Gain: J1 +1 to +2 on understanding and honesty, J2 stops reading the title as cherry picking.
2. **Say who did what and how tools were used, in 15 to 20 seconds, and prepare the answer (about 20 minutes, Lead and the two speakers).** Ask the organisers at the first opportunity whether AI tools are allowed (rules question 7) before choosing the wording; then write one plain sentence for slide 8 or the opening and one 15 second answer to J3's question 1.
   Also swap one hard answer from A to B so B visibly owns part of Q&A (B has 4 of 10 hard questions and 3 of 13 supplementary). Gain: J3 teamwork and J2 trust; this is the question most likely to be asked and has no answer in any prepared file.
3. **Two stopwatch runs and a cut list, with the real slot confirmed (about 90 minutes with both speakers).** Run it aloud twice, write the times into `presentation/rehearsal-notes.md` (the open DOPLNIT), cut to a version that ends at 6:15 at 1.7 words per second so a slower pace
   still finishes. Candidates from the script's own cut order plus one more: the 5:19 row (2,22, "13 words" saved), the p99 clause at 3:49, the 4:13 sentence about the assignment's units; and say the three protocols as one sentence ("od 0,13 do 0,40 milimetru podle protokolu") instead of rows 1:33 and 1:52 (about 30 s,
   five numbers fewer). Ask organisers (OQ-002) whether the slot really is 7 minutes or 15; if 15, use the spare time for a longer demo, not for more numbers. Gain: removes the most probable loss (see 5.4 item 1).
4. **Make the fallback real (about 45 minutes, owner).** Record the 60 s clip, export the PDF of the deck (both listed as missing), copy `viewer/dist/index.html` to a second device, bring HDMI and USB-C adapters, unhide slide 10 before the talk (the "klávesa H" fallback works only in PowerPoint; the owner uses a Mac with Cmd+Tab), and ask the
   organisers how a laptop connects (unknown). Reorder the demo so the first thing the room sees is the bad end of discharge 147 (14 s) and then the typical discharge; a layperson then knows what "good" looks like. Gain: turns the demo from single point of failure to a nuisance, and gives J3 a moment he understands.
5. **Clean up the self-contradictions in what the team will say and rehearse from (about 40 minutes, Lead).** See section 6: N11 in the script says the other columns "nepředpovídali jsme je" while `docs/bonus-gaps.md` says they are predicted; `docs/REHEARSAL.md` still scripts discharge 123 and "Vidíte základní síť"; the script says the 60 s clip is done while three
   other files say it is not; `presentation/assets/failure-gallery.md` uses the banned word "zamčená sada". Add the train against held-out gap (factor 2,4 to 3,8) as one prepared answer. Gain: no contradiction on stage when a question lands on a stale answer.

A sixth item that I would do only if time remains: a one-page leave-behind sheet (the five headline numbers with their protocols, the limits in one box, the three-models picture). The committee decides after the last team; the deck PDF does not exist yet and the repository is private (`docs/SUBMISSION.md` OQ-S2).
Number it 6 because the gain is real but the risk to a hurried hour is low only if items 1 to 5 are done.

### 5.4 The three things that could lose the most points

Ranked by my guess of probability times damage (judgement, not measurement).

1. **Talking too long, or too densely.** Evidence: the script's own estimate "at a normal pace it is about 25 s over"; `presentation/timing.py` "1.6 w/s -> 8:15, 1.8 w/s -> 7:20"; no stopwatch run exists; the close (slide 8, 6:17 to 7:00) carries the only take-home sentence ("desetiny milimetru za setiny milisekundy")
   and is the first thing to be rushed or cut by a moderator. Nerves speed up some speakers and slow others, and numbers are read slower than words. A cut-off on the closing slide costs J3's clarity score and every juror's memory of the message; density alone costs J3 more.
2. **A trust break.** Three ways, any of which a juror can trigger in one question: (a) the headline "0,13 mm" read as error against the plasma, because no slide says what it is compared with and the best of three protocols is in the title; (b) "Who wrote this, did the students understand it?", no prepared answer,
   and B owning the least Q&A; (c) a stale prepared answer contradicting a file (N11, the clip, the demo discharge). The team's honesty is its best asset, and an inconsistency found by the jury turns "honest" into "careless".
3. **Demo failure.** Single laptop, a local 11 MB HTML with IPP data that must not go online (`docs/PLAN.md` IMPL-10), projector connection unknown, the fallback hidden slide depends on a key that exists only in PowerPoint, and the 60 s clip is documented as both done and not done.
   The demo is 80 of the 420 seconds and sits in the middle; if the stills and the clip work, recovery should cost on the order of 20 to 45 seconds (the script's own "Zkrať to na 45 sekund"), if they do not it costs the whole slot and the thread of the talk (my judgement).

## 6. Contradictions found while reading (for the Lead; not edited here)

| # | What | Where (quoted) |
|---|---|---|
| 1 | N11 answer claims the other 15 columns were not predicted | `presentation/pitch-script.md` N11: "ostatní jsou doplňkové a nepředpovídali jsme je"; `docs/REHEARSAL.md` N11 and `docs/bonus-gaps.md` section 0 item 2: "They are predicted" |
| 2 | 60 s fallback clip: done or not | `pitch-script.md` backup: "Záznam hotový: `out/viewer-demo.mp4` (60 s ...)"; `docs/demo-facts.md`: "the 60 s clip is not recorded yet"; `docs/REHEARSAL.md`: "Missing today: the 60 s clip (only the 15 s ... exists)" |
| 3 | Rehearsal sheet scripts the old demo | `docs/REHEARSAL.md` section 1: "Vidíte základní síť, ne vybraný model" and discharge 123, 0; `pitch-script.md` rows 2:29 to 3:45: discharge 85 and 147, selected model (`docs/deck-fixes.md` "For lane K" also lists REHEARSAL Q6, Q9 as stale) |
| 4 | Banned word in a jury-facing file | `presentation/assets/failure-gallery.md`: "výboj 147 (zamčená sada 30 výbojů)"; `docs/deck-fixes.md` 0.2 and `pitch-script.md` rules ban "zamčené" |
| 5 | Notebook count | `README.md` structure table: "Five Jupyter notebooks"; the folder has eight (01 to 05, 07, 08, 09); `docs/SUBMISSION.md` plans "5 `.ipynb`"; `analysis/make_submission.py` copies all `*.ipynb` |
| 6 | Time budget | `docs/hackathon-rules.md` "At most 15 minutes per team" against the 7 minutes of `docs/SUBMISSION.md` "come from the owner" |

## 7. What I could not judge

- The viewer running live, PowerPoint rendering, the real pace of A and B, the sound of the Czech numbers aloud, the committee's real criteria, the other teams, whether AI tools are allowed.
- Whether a hidden test set or an automatic metric exists. If the committee scores model accuracy on its own held-out discharges, content decides and the talk matters less; if it does not, the talk decides. Question 4 on the list of things to ask the organisers (`docs/hackathon-rules.md`) is the one whose answer would change this document most.
