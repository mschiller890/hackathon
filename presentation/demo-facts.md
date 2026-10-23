# Demo facts for the pitch (live viewer on the shipped model)

Source: bladed-85, commit e50b1ee (IMPL-20), computed from `viewer/data.js` (every third row of each discharge, which is what the viewer shows). Nothing typed by hand. Regenerate and check every number with `analysis/ipp1_demo_facts.py`, which writes `results/ipp1-demo-facts.md` (all values above reproduced there, except the all-row mean 0.75 mm of discharge 147, which needs the raw data). The viewer files stay out of git.

What the viewer plays: the shipped model (`cand`) on the 30 discharges set aside before the final model choice. It predicts 16 of 31 targets, so it draws predicted POINTS (axis, X point, strike points, limiter point) over the true outline, not a predicted outline. Say aloud: "V ukázce vidíte vybraný model na třiceti odložených výbojích; obrys nepředpovídá, ukazuje body."

| Still or moment | Discharge | Where | Value |
|---|---|---|---|
| start (limited) | 85 | t 0.028 | axis error 0.22 mm, limiter point 10.0 mm |
| middle (diverted) | 85 | t 0.502 | axis 0.25 mm, X point 0.1 mm |
| rough end | 147 | last frame, t 1.000 | axis 33.7 mm, limiter point 105.5 mm; discharge mean 0.85 mm (0.75 over all rows) |
| noise switch | 85 | t 0.447 | shipped model trained on clean data 290.2 mm axis error, noise-trained 1.84 mm (discharge means 294.1 and 3.10 mm) |

Discharge 85 is the typical one: lower median of the mean axis error among the 30 (0.18 mm), 72 frames, 36 % limited rows. Replaces 123, 0, 4, 11 (those are development discharges and the old numbers came from the baseline network).

Aggregates (distance of the axis sqrt(dR^2+dZ^2) per row, mean per discharge; not the 0.133 mm R-axis MAE of the slide):
- All 30 set-aside discharges have a mean axis error below 1 mm; median 0.18 mm; worst id 14 with 0.86 mm, then 147 with 0.85 mm; none above 5 mm.
- Over all 149 discharges (set-aside plus 119 development discharges out of fold, same recipe): 135 below 1 mm, 2 above 5 mm (id 0 with 8.66 mm and id 11 with 5.29 mm, both development discharges).
- Viewer means over every third row can differ from all-row means by up to 0.1 mm for the set-aside discharges (3 mm for the roughest development ones).

Tile text: "Doba odhadu, vybraný model 0,027 ms, medián, 1 jádro, Apple M5" (limited path; diverted 0,015 ms and p99 0,093 ms in `results/ipp1-latency-shipped.md`). The red series in the noise mode is the model trained on clean data and it fails there; the label says "učený bez šumu".

Open: no predicted outline for the shipped model (see PLAN IMPL-20); the 60 s clip is not recorded yet (`viewer/record.py --clip`, about 5 minutes, discharge 85).
