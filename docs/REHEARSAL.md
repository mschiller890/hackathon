# Rehearsal sheet: live demo, drill questions, G5 checklist

For the owner (A, first speaker, hands on the laptop) and the colleague (B). Print at 9 pt. Speaker lines are Czech (from `presentation/pitch-script.md`);
the rest is English. Numbers only from `results/`, source named per row. State of `main` at 1c6d046, Fri 23 Oct evening.

## 1. Demo run sheet (slot 2:29 to 3:49, 80 s, between slide 4 and slide 5)

**Before the slot:** Chrome only (`viewer/README.md`). Tab 1 `viewer/dist/index.html#d=85`, speed 1x, stopped; tab 2 `...#d=147`; deck on slide 4; Wi-Fi and notifications off.

| Time | Click / key (A unless noted) | Say (Czech) |
|---|---|---|
| 2:24 | Cmd+Tab to Chrome, tab 1 | "Teď naživo. Prohlížeč běží bez internetu. V ukázce vidíte vybraný model na třiceti odložených výbojích; obrys neodhaduje, ukazuje body." |
| 2:37 | Point to chips *Skutečnost* and *Předpověď*; press **Space** | "Tmavá čára je referenční tvar z rekonstrukce ústavu, body jsou odhad vybraného modelu. Výboj číslo 85 patří mezi odložených třicet." |
| 2:49 | Nothing; let it run twice (if it stops, Space) | (ticho, 7 s) |
| 2:56 | Point to the circle (axis), the cross (X point), the error chart below | "Kroužek je osa, křížek bod X. Dole je chyba v čase, v tomto výboji roste na začátku a na konci." Rehearsal check: if the chart does not show it, say only the first sentence. |
| 3:14 | Click tab 2 (`#d=147`), **Space** | "Teď záměrně špatný výboj, číslo 147. Na konci je osa vedle o třicet čtyři milimetrů, průměr celého výboje je pod milimetrem." (numbers: `results/ipp1-demo-facts.md`) |
| 3:28 | Point to where the two lines part | (ticho, 6 s) |
| 3:34 | B speaks, no click | "Takových výbojů je málo: u základní sítě má chybu osy pod milimetrem 86 procent výbojů, tedy 128 ze 149." (`results/ipp1-claim-support.md`) |

Hard rule: slide 5 is on screen at 3:52. Over time: drop 3:28 and 3:34 first, then 3:08.

| If | Do (5 s at most, then switch; never debug on stage) | Say |
|---|---|---|
| The viewer does not open / blank page | Deck, hidden **slide 10** (key **H**, or `10` + Enter): stills of discharge 85 | "Ukázka se nespustila, ukážu uložené obrázky." 45 s, skip the bad-discharge rows |
| The viewer freezes mid-run | Space; then Cmd+R (the address restores the discharge, not the position); still frozen: stills | Keep going, apologise once |
| The laptop has no network | Nothing: one file, data inlined, no external URL (`PLAN.md` IMPL-10, tested with DNS blocked) | none |
| Laptop dead / no video out | Second device, or the PDF on the USB stick | One sentence, continue |
| Everything fails | 60 s clip, A talks over it | "Pustím záznam, je to stejná ukázka." |

Backup order: (1) stills in hidden slide 10 (`presentation/assets/viewer-*.png`); (2) 60 s clip (discharge 85); (3) PDF of the deck.
**Missing today:** the 60 s clip (only the 15 s `out/viewer-demo.mp4` exists, outside git) and the PDF (`docs/SUBMISSION.md`). `viewer/dist/index.html` (11 MB, IPP data, gitignored, CON-001) goes to the second device by USB or AirDrop only.

## 2. Drill sheet (23 questions; ★ = the five most dangerous)

Unknown? "Tohle jsme neměřili." and continue with what was measured. Never guess; say the protocol with every number.

**IPP physicist**

| # | Question | 15 s answer (Czech) | Source in `results/` |
|---|---|---|---|
| Q1 | Čemu říkáte pravda? | "Porovnáváme se správnými odpověďmi od ústavu, což je numerická rekonstrukce rovnováhy. Chyba 0,13 milimetru je proti ní, ne proti skutečnému plazmatu. Přesnost těch odpovědí jsme neměřili." | `ipp1-final.md` |
| Q2 ★ | Co když bude tvar nový? | "Nevíme. Vynechání celé rodiny tvarů zvedlo chybu nejvýš třikrát. Opravdu neobvyklých výbojů je jen 18 ze 149 a samostatně jsme je nevynechali. Mimo rozsah dat tomu věřit nelze." | `ipp1-unusual-shapes.md` |
| Q3 · N1 ★ | Na šumu se síť zhroutí; jak přesní jste na skutečných čidlech? | "Síť naučená na čistých datech má na šumu osu 10,15 milimetru. Síť učená se šumem má na 30 odložených výbojích osu 2,38. Zda šum v souboru odpovídá skutečným čidlům, nevíme." | `ipp1-robustness-findings.md`, `ipp1-final.md`, `ipp1-data-checks.md` |
| Q7 | Hodnoty se skoro nehýbou. | "Správně, u osy a bodu X je rozptyl jen 2,4 až 13,7 milimetru. Proto uvádíme i chybu vztaženou k rozptylu: u osy 0,139 u základní sítě, pět dělení po výbojích." | `ipp1-baseline.md`, `ipp1-data-checks.md` |
| N5 ★ | Jakou rychlost uvádíte, vybraného modelu? | "0,0145 milisekundy patří základní síti. Vybraný model od 24 čísel po výstup: u divertorového plazmatu medián 0,015, u limitovaného 0,027 milisekundy, devadesát devět procent pod 0,1, na vytíženém notebooku. Obojí pod rozpočtem 1 až 10." | `ipp1-latency-shipped.md`, `ipp1-latency.md` |
| N6 | Jak jste na zánicích a startu? | "Nejhůř na koncích: u vybraného modelu na odložených výbojích je v posledních dvou procentech radiální chyba osy 0,58 milimetru proti 0,11 uprostřed. Zda data obsahují zánik plazmatu, jsme nevyhodnotili." | `ipp1-final.md` |
| N8 | Proč nezprůměrovat řádky? | "Zkusili jsme tři: na šumu klesla chyba osy z 2,64 na 2,33, na čistých vstupech se zhoršila z 0,38 na 0,57 milimetru. Delší okna jsme nezkoušeli." | `ipp1-robustness-findings.md` |
| N9 | Přežije se výpadek cívky? | "Netestovali jsme. Samotných 16 cívek dává souhrnnou chybu 0,066 proti 0,063 se všemi 24 vstupy. Žádné čidlo nejmenujeme, pořadí není stabilní." | `ipp1-inputs.md`, `ipp1-inputs-controls.md` |
| N11 | Zadání má 17 parametrů, vy 16. | "Vybraný model odhaduje 16 hlavních sloupců z 31 v souboru. Ostatních patnáct sloupců jsou doplňkové veličiny pro obrys; ty odhaduje jen základní síť, vybraný model je neodhaduje." | `ipp1-data.md` |

**ML person**

| # | Question | 15 s answer (Czech) | Source in `results/` |
|---|---|---|---|
| Q4 | Proč je u proudu lineární model lepší? | "Je, a vybraný model ho používá: 0,035 kiloampéru proti 1,2 u sítě. Proud je skoro lineární funkce vstupů, není to úspěch sítě a nepočítáme to do zisku." | `ipp1-final.md`, `ipp1-baseline.md` |
| Q5 · N2 ★ | Je validace poctivá? Ladili jste na testu? | "Částečně. Návrh běžel na křížové validaci přes všech 149 výbojů, takže odložených 30 v ní bylo. Po odložení se nepřeučovalo. Proto obě čísla: 0,13 odložené, 0,23 vývojové." | `ipp1-final.md`, `ipp1-improve.md` |
| Q6 | Zkoušeli jste jiné modely? | "Širší a hlubší sítě, jinou ztrátu, rozdíly cívek, soubory sítí i stromy. Nejvíc pomohla zvláštní síť pro limiter: 4,55 proti 10,6 milimetru. Rozdíly pod asi 20 procent bereme jako šum, pokud interval přes výboje nevylučuje 1." | `ipp1-improve.md`, `ipp1-final.md` |
| N3 | Je odložená sada reprezentativní? | "Ne zcela. Jen 2 z 30 odložených výbojů mají kladný proud a tam je u vybraného modelu osa 0,45 milimetru proti 0,11 na ostatních. Konvenci znaménka neznáme, nevíme tedy, zda jde o opačnou polaritu stroje. Interval osy je 0,10 až 0,18." | `ipp1-final.md` |
| N4 | Kolik z vylepšení je skutečné? | "Pět semen: vybraný model je lepší v pěti z pěti u všech sedmi veličin, osa o 42 až 60 procent. U bodu X jen o 21, tam říkáme o něco lepší." | `ipp1-final-seeds.md` |
| N7 | Model, který musí znát druh vstupu? | "Dodáváme dva: vybraný pro čisté vstupy, síť učenou se šumem pro zašuměné. Jeden vítěz není, učená se šumem je na čistých horší, 1,56 proti 0,31. Přepínání jsme netestovali." | `ipp1-final.md` |
| N10 | Je kamera k ničemu? | "Je to malá síť na snímcích 48 na 64 z 78 výbojů, 1,3 až 13krát horší než cívky. Ukazuje to na tuto síť, ne že kamera nenese informaci." | `cloud-camera-main.md`, `cloud-camera-findings.md` |
| N12 | A na nejnovějších výbojích? | "Učení na 60 nejnižších číslech, test na 59 nejvyšších: osa 0,40 milimetru, při náhodném dělení 0,22. Že čísla sledují čas, jsme neověřili." | `ipp1-final.md` |

**Organizer / business**

| # | Question | 15 s answer (Czech) | Source in `results/` |
|---|---|---|---|
| Q8 ★ | Dá se to nasadit do řízení? | "Zatím ne. Změřili jsme jen výpočet sítě. Sběr signálů, napojení, nejhorší dobu a skutečně zašuměné signály ne. A jsou to dva modely, přepínání jsme netestovali." | `ipp1-latency-shipped.md`, `ipp1-final.md` |
| Q9 | Pomůže to COMPASS Upgrade? | "Model je naučený jen na COMPASSu, na jiném stroji by se učil znovu. Se 30 učícími výboji je osa 1,47 milimetru; kolik výbojů potřebuje nový stroj, nevíme." | `ipp1-robustness-findings.md` |
| Q10 | Co když se plete a neřekne to? | "Pět sítí s různým začátkem: na deseti procentech nejnejistějších řádků je chyba 8krát větší a nesou 47 procent celé chyby. Je to varování, ne pravděpodobnost." | `ipp1-uncertainty.md` |
| N13 | Proč věřit 99,3 procenta? | "Základní síť má 0,993 v pěti dělení, vybraný model 0,9916 na odložených výbojích. Zda jsou chyby u přechodu mezi konfiguracemi, jsme zvlášť nevyhodnotili." | `ipp1-baseline.md`, `ipp1-final.md`, `ipp1-distribution.md` |

Ids: Q1 to Q10 from `pitch-script.md`; N1 to N13 from `docs/review-findings-2.md` (it lists 13, not 10). Q3 and N1, Q5 and N2 share one answer.

**Wording fixed with the Lead's decisions (23 Oct, after the physics rewrite of the pitch)**
1. Slogan: "Desetiny milimetru shody s rekonstrukcí, setiny milisekundy výpočtu." Measured: selected model 0,027 ms limited and 0,015 ms diverted, basic network 0,0145 ms (`results/ipp1-latency-shipped.md`, `results/ipp1-latency.md`). Say "vybraný model" for the viewer tile; the old 0,1775 ms estimate is not used.
2. Reference wording: say "referenční tvar" or "rekonstrukce ústavu", not "skutečný tvar". Q1 keeps "skutečné plazma" only as the contrast ("ne proti skutečnému plazmatu").
3. Demo discharges are 85 (typical, set-aside) and 147 (rough end); the median of the mean axis error over the set-aside discharges is "asi 0,2 mm" (0,19 mm, `results/ipp1-demo-facts.md`). The old discharges 123 and 0, the "5,7 mm" and "219 frames" are not used.

## 3. G5 checklist (Sat 09:00, owner and colleague; tick with evidence, name the person for each line)

- [ ] **Second device:** `viewer/dist/index.html` (copied by USB) in a clean Chrome profile; discharge 85 plays, the *Šum měření* chip works.
- [ ] **`file://` open** on the presentation laptop (double click and typed path), `#d=85` and `#d=147`; default browser is Chrome.
- [ ] **Fonts offline:** Wi-Fi off, page plays; viewer uses the system font stack, deck uses Arial; Czech diacritics checked on all 14 slides on both devices.
- [ ] **Battery:** on mains, sleep and screensaver off, Do Not Disturb on, other apps closed; spare charger and video adapter in the bag.
- [ ] **Screen share:** mirror at 1920x1080 and 1366x768; viewer legible from the back (toolbar not clipped, magnifier tiles visible).
- [ ] **Timer:** stopwatch on a phone; checkpoints 0:38, 1:06, 1:26, 2:29, 3:49, 4:29, 5:03, 6:17, 7:00. One timed run, real times into `presentation/rehearsal-notes.md` (7:00 is only a word count today).
- [ ] **Backup video present:** 60 s clip plays on the second device and from the USB stick (today only the 15 s clip exists).
- [ ] **Hidden slide 10** opens with H and shows the stills captioned "Základní síť"; **PDF of the deck** on the USB stick and both devices.
- [ ] Axis error of discharge 0 written into row 3:14; `git ls-files` shows no `data.js` or `dist/` (CON-001).
