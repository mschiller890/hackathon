#!/usr/bin/env python
"""Two numbers that the pitch cites but results/ did not hold (found by analysis/check_claims.py, gate G2).

1. The share of the variance of the 24 inputs carried by the leading principal components (standardized inputs).
2. The share of discharges whose out-of-fold axis error is below 1 mm or above 5 mm. The axis error of a row is the distance
   sqrt(dR^2 + dZ^2) between the true and the predicted magnetic axis; a discharge is judged by the mean of its rows.
   Predictions: out/ipp1-predictions.csv (analysis/ipp1_oof.py, the baseline network, 5 folds by discharge).

Run: HACKATHON_HOME=... ~/.venvs/hackathon/bin/python -I analysis/ipp1_claim_support.py     Writes results/ipp1-claim-support.md
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ipp1_common import DATA, OUT, ROOT, load


def main():
    df, x, _, groups, _ = load()
    ratio = PCA().fit((x - x.mean(0)) / x.std(0)).explained_variance_ratio_
    pred = pd.read_csv(OUT / "ipp1-predictions.csv")
    truth = pd.read_csv(DATA / "equil_data.csv")
    # The prediction file rounds the time column, so rows are matched by position after checking they are the same rows.
    assert len(pred) == len(truth) and (pred.discharge.values == truth.discharge.values).all()
    assert np.abs(pred.time.values - truth.time.values).max() < 1e-6
    dist = np.hypot(pred.R_mag_axis_pred - truth.R_mag_axis, pred.Z_mag_axis_pred - truth.Z_mag_axis) * 1000
    per = dist.groupby(truth.discharge).mean()
    lines = ["# Numbers cited by the pitch that were missing from results/", "",
             "Made by `analysis/ipp1_claim_support.py` (gate G2, `docs/claims-audit.md`).", "",
             "## Variance of the 24 inputs in principal components (inputs standardized, all 42,972 rows)", "",
             "| components | share of the variance |", "|---:|---:|"]
    lines += [f"| {k} | {100 * ratio[:k].sum():.2f} % |" for k in (1, 2, 5)]
    lines += ["", "That is variance, not information: the share says how redundant the inputs are, not how much of the shape they determine.", "",
              "## Axis error per discharge (out-of-fold predictions of the baseline network, 149 discharges)", "",
              "Row error = distance between the true and the predicted magnetic axis. Discharge error = mean over its rows.", "",
              "| measure | value |", "|---|---:|",
              f"| discharges with mean axis error below 1 mm | {int((per < 1).sum())} of {len(per)} ({100 * (per < 1).mean():.1f} %) |",
              f"| discharges with mean axis error above 5 mm | {int((per > 5).sum())} of {len(per)} |",
              f"| median over discharges of the mean axis error | {per.median():.2f} mm |",
              f"| median radial axis error over all rows | {np.median(np.abs(pred.R_mag_axis_pred - truth.R_mag_axis)) * 1000:.3f} mm |",
              "", "Out-of-fold means every discharge was predicted by a network that did not train on it; folds are random by discharge, so this is the optimistic split "
              "(`results/ipp1-final.md` has the blocked one)."]
    (ROOT / "repo/results/ipp1-claim-support.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
