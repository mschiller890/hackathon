# IPP 1: poloha a tvar plazmatu z magnetických měření (COMPASS)

**Úloha.** Ze 24 magnetických měření (16 cívek, 8 smyček toku) odhadnout 16 veličin plazmatu (osu, bod X, dotykové body, bod u limiteru, proud, protažení, trojúhelníkovost) dost rychle pro řízení. Klasická rekonstrukce trvá minuty.

**Co jsme vytvořili.** *Základní síť* (24 vstupů, 16 výstupů). *Vybraný model* přidává 22 rozdílů sousedních cívek, lineární model pro proud plazmatem a zvláštní síť pro bod u limiteru. Pro dodané zašuměné vstupy dodáváme jinou síť, naučenou se šumem a posunem.

**Výsledek.** Štítky jsou referenční rekonstrukce ústavu, proto každé číslo je *shoda s touto rekonstrukcí*, ne fyzikální přesnost. Střední absolutní chyba, čisté vstupy. *Odložených 30*: 30 výbojů mimo učení, vyhodnocených jednou. *Pětinásobné ověření*: 119 vývojových výbojů, vždy celé výboje v jednom dílu. Odezva: jedno jádro Apple M5 na sdíleném počítači, od 24 surových vstupů.

| Veličina | Vybraný model, odložených 30 [95% interval, výběr s opakováním po výbojích] | Základní síť, stejných 30 | Vybraný model, pětinásobné ověření |
|---|---|---|---|
| Osa R (mm) | 0,133 [0,099; 0,177] | 0,307 | 0,23 |
| Bod X R (mm) | 0,115 [0,076; 0,168] | 0,161 | 0,211 |
| Dotykové body R, 1 a 2 (mm) | 0,108 [0,077; 0,144], 0,136 [0,084; 0,205] | 0,212; 0,212 | 0,206; 0,254 |
| Bod u limiteru R, Z (mm) | 4,55 [3,30; 6,16], 8,35 [6,81; 10,2] | 10,6; 22,5 | 4,62; 11,8 |
| Proud plazmatem (kA) | 0,0347 [0,0311; 0,0382] | 1,20 | 0,0332 |
| Odezva na jeden odhad (ms) | medián 0,015 (divertorové), 0,027 (limitované); 99. percentil 0,057 a 0,093 | základní síť 0,0145 | nelze |

Zdroje: `results/ipp1-final.md`, `ipp1-latency-shipped.md`, `ipp1-latency.md`. Pořadí platí v 5 z 5 semen; bod X je jen o něco lepší (`ipp1-final-seeds.md`).

**Jiná rozdělení.** Dělení po blocích (učení na 60 nejnižších číslech výbojů, zkouška na 59 nejvyšších; čísla vypadají jako chronologická, nepotvrzeno): osa R 0,397 mm proti 0,216 mm při náhodných dílech na stejných 59 výbojích (základní síť 1,23 proti 0,448 mm), s méně učícími výboji (`ipp1-final.md`). Chyba na učících datech proti chybě na odložených, osa R vybraného modelu: 0,095 proti 0,230 mm při pětinásobném ověření (2,4krát), 0,087 proti 0,133 mm na odložených 30 (1,5krát); základní síť 1,7krát a 1,2krát; největší poměr při pětinásobném ověření je 3,8krát (dotykový bod 2 R), model tedy sedí na učící výboje lépe než na nové (`ipp1-traintest-gap.md`). Chyby jsou průměry: medián chyby osy R u základní sítě je 0,15 mm proti průměru 0,38 mm a limitovaná plazmata tvoří 92 % jejího čtverce chyby osy (`ipp1-distribution.md`).

**Co jsme neukázali.**

- Fyzikální přesnost nad rámec shody s referencí; nepoužili jsme žádné nezávislé měření.
- Tvary mimo data: skupiny s 18 neobvyklými výboji dopadly 1,0 až 3,0krát hůř, nejkrajnější tvar jsme nikdy nevynechali samotný (`ipp1-unusual-shapes.md`). Model dává 16 čísel, ne hranici plazmatu.
- Zašuměné vstupy pro model naučený na čistých datech: selže, osa R 10,15 mm proti 0,38 mm (základní síť, pětinásobné ověření; `ipp1-robustness-findings.md`). Síť naučená se šumem dává na odložených 30 chybu 2,38 mm (`ipp1-final.md`). Dodaný zašuměný soubor obsahuje jen bílý šum; výsledky o posunu jsou uměle vytvořené.
- Sběr signálů a systém reálného času: měřili jsme jen výpočet sítě; špičky nejsou horní mez.

**Doplňkové rozbory (jedna věta, soubor).**

- Množství dat: 30 učících výbojů dává osu R 1,47 mm, 119 dává 0,38 mm, při pevných 60 epochách; časový kontext: tři vzorky pomáhají na zašuměných vstupech a škodí na čistých (`ipp1-robustness-findings.md`).
- Méně vstupů: samotných 16 cívek 0,066, všech 24 vstupů 0,063, samotných 8 smyček toku 0,285 (souhrnná chyba; `ipp1-inputs.md`).
- Stabilita: chyby rostou hlavně v poslední desetině výboje (`ipp1-time.md`).
- Neshoda pěti sítí sleduje chybu, Spearman 0,46 pro osu R (`ipp1-uncertainty.md`).
- Kamerová síť: osa R 1,79 mm v barvě, 1,70 mm v šedi, proti 0,38 mm z magnetických měření (`cloud-camera-main.md`).

**Kde je co.** Sešity `notebooks/01` až `09`; souhrnná čísla a obrázky v `results/`; pravidla znění v `docs/claims-corrections.md`. Surová data jsou důvěrná a v repozitáři nejsou.
