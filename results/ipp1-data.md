# Data facts used on the slides (IPP task 1, magnetic file `equil_data.csv`)

Measured with `analysis/ipp1_eda.py` (numbers in `out/ipp1-eda.json`, aggregate only).

| Fact | Value | Source |
|---|---|---|
| Rows (one row is one time instant of one discharge) | 42,972 | measured |
| Columns | 57 (24 inputs, 2 index columns `time` and `discharge`, 31 targets) | measured |
| Discharges | 149 | measured |
| Rows per discharge | 17 to 439, median 293 | measured |
| Inputs | 24: 16 coils `IPR01` to `IPR16`, 8 flux loops `FL01` to `FL08` | measured |
| Targets reported in the headline tables | 16 (the main targets of the assignment, including `is_limited`); the file holds 31 | assignment text and measured |
| Share of limited rows | 44.2 % | measured |
| Duration of a discharge, about 150 to 200 ms | **not measured by us**: stated by the organizers in their data notebook (`uloha-1-ekvilibrium-nacteni-dat.ipynb`, "typický výboj trvá 150 až 200 ms") and in the introductory presentation | organizers |
