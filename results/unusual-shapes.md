# IPP 1: unusual shapes (REQ-B08)

Question: how much worse is the network on a family of shapes that was not in training? Full tables: `out/unusual_shapes.{json,md}` (not in git);
figure `unusual_shapes.png`.

Command (`HACKATHON_HOME=<your hackathon folder>`): `~/.venvs/hackathon/bin/python -I analysis/ipp1_unusual_shapes.py`
(1.5 minutes; shared MLP, 60 epochs, 2 threads).

## Design

- Each discharge is described by its median elongation and median triangularity. KMeans (k=4) on the **ranks** of the two values gives clusters of
  33 to 43 discharges. Two tail groups are added: the 23 discharges with the highest triangularity and the 23 with the lowest elongation.
- For each group: train on all other discharges, test on the group. Reference: the error on the **same discharges** from the usual random 5-fold
  split by discharge, so the factor below is caused by the unseen shape and not by the choice of discharges.
- The family split works as intended: the distance from a held-out discharge to the nearest training discharge in (elongation, triangularity)
  ranks is 0.12 to 0.28 against 0.02 to 0.05 in the random split (2.5 to 12 times larger; smallest for the high triangularity group).
- A first attempt with KMeans on raw values was dropped: one cluster held 131 of 149 discharges, so leaving it out meant training on 18 discharges and
  measured the amount of data, not the shape.

## What the 149 discharges look like

Nearly all discharges lie in one tight group (median elongation 1.75 to 1.82, triangularity 0.33 to 0.40). 18 discharges are really different
(median elongation 1.0 to 1.74, triangularity 0.02 to 0.33); they all fall into cluster 0, and they are 18 of the 23 discharges of the low elongation group. Clusters 1 to 3 are therefore subgroups
of ordinary shapes. The high triangularity group (median 0.38 against 0.36 for everything) is only the upper edge of the ordinary group and **is not
a rare shape**.

## Result (MAE on the held-out group; factor = family out divided by random fold, same discharges)

| Held out | Discharges | R axis (mm) | Z axis (mm) | elongation | limiter R (mm) |
|---|---:|---|---|---|---|
| cluster 0 (contains the 18 odd shapes) | 34 | 0.53 to 1.10 (2.1x) | 0.48 to 0.99 (2.1x) | 0.0075 to 0.0136 (1.8x) | 11.2 to 34.1 (3.0x) |
| cluster 1 | 39 | 0.43 to 0.75 (1.7x) | 0.48 to 0.76 (1.6x) | 0.0063 to 0.0081 (1.3x) | 10.3 to 11.5 (1.1x) |
| cluster 2 | 33 | 0.38 to 0.44 (1.2x) | 0.38 to 0.47 (1.2x) | 0.0056 to 0.0064 (1.1x) | 11.3 to 11.7 (1.0x) |
| cluster 3 | 43 | 0.26 to 0.50 (1.9x) | 0.29 to 0.47 (1.6x) | 0.0044 to 0.0062 (1.4x) | 11.1 to 12.5 (1.1x) |
| high triangularity (edge of the ordinary group) | 23 | 0.57 to 0.64 (1.1x) | 0.56 to 0.79 (1.4x) | 0.0078 to 0.0082 (1.0x) | 14.0 to 14.1 (1.0x) |
| low elongation (the 18 odd shapes and 5 ordinary ones) | 23 | 0.68 to 1.63 (2.4x) | 0.60 to 1.09 (1.8x) | 0.0100 to 0.0225 (2.2x) | 11.9 to 23.1 (1.9x) |

- Leaving out a family of shapes makes the error 1.0 to 3.0 times larger, typically 1.2 to 2.4 times; there is no collapse. On the group that is mostly
  the odd shapes the axis error is 1.6 mm (from 0.7 mm) and the elongation error 0.023 on a range of 0.9 to 1.9.
- `is_limited` accuracy does not change (99.0 to 99.4 % in both settings).

## Limits (say these in the talk)

- The random split is itself optimistic: discharge ids are chronological, so neighbours of every test discharge are in training
  (`docs/internal/review-findings.md`). The factors measure the loss from removing a whole family, not the total error on a new tokamak scenario.
- Only 18 discharges are truly unusual and they were never held out alone (cluster 0 and the low elongation group mix them with 16 and 5 ordinary ones),
  and the extreme elongation near 1.0 was never tested as an unseen extreme. The result says nothing about shapes outside the range of the data.
- One initialization per group, no repeated runs; with 23 to 43 discharges per group a factor of 1.1x to 1.3x is within noise.
