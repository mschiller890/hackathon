# Cloud model search, IPP 1 magnetic part

Produced by `analysis/cloud_search.py` and `analysis/cloud_search_report.py`. Protocol of the baseline: 5 folds by whole discharge (same test folds as `results/ipp1-baseline.md`), masked loss, errors from `ipp1_common.score`. **Summary relative error** = mean over folds of the mean nRMSE (RMSE / spread) of the 13 targets without the limiter point, as in `results/ipp1-inputs.md`. Hyperparameters of every model were chosen only on an inner split by discharge of the training part of each fold (objective: summary error + 0.2 x mean limiter nRMSE); the test fold was never used for tuning. Latency: one sample, one CPU thread, whole pipeline from the 24 raw numbers (Intel(R) Xeon(R) Processor @ 2.10GHz); ensembles and hybrids are the sum of their parts run one after the other (a fused batched network would be faster).

**Status: PARTIAL.** Not yet in this file: model evaluation on the test folds, latency, noisy-data runs, limiter specialist. Tables below show only what has run so far.



## Pareto table (mean of 5 folds; sorted by summary error)

| model | summary rel. error | folds better than baseline | R_limiter MAE (mm) | Z_limiter MAE (mm) | R_mag_axis MAE (mm) | is_limited acc. | parameters | latency (ms / sample) | Pareto |
|---|---|---|---|---|---|---|---|---|---|

Recommendation rule: the lowest summary error among models with median latency <= 0.1 ms (ten times below the 1 ms budget): **none**; lowest Z_limiter error among them: **none**. Figure: `results/cloud-search-pareto.png`.

## Error per target (MAE, mean of 5 folds)

(not run)

Figure: `results/cloud-search-targets.png`.

## Limiter point: specialist and gate

(not run)

(not run)

## What the search found

| family | folds | trials per fold | search time (CPU-min, 1 thread each) | best inner objective per fold |
|---|---|---|---|---|
| nn | 4 | 49 | 192 | 0.0814, 0.0923, 0.1026, 0.0861 |

Best inner-validation objective reached with each choice (lower is better; mean over the folds that tried it):

| choice | value | best objective | trials (all folds) |
|---|---|---|---|
| arch | resmlp | 0.0906 | 164 |
| arch | mlp | 0.1459 | 24 |
| feat | diff | 0.0906 | 107 |
| feat | pca16 | 0.1188 | 20 |
| feat | pca24 | 0.1275 | 38 |
| feat | raw | 0.1347 | 23 |
| loss | huber | 0.0965 | 121 |
| loss | mse | 0.1051 | 67 |
| sched | cosine | 0.0965 | 114 |
| sched | onecycle | 0.1042 | 53 |
| sched | constant | 0.1438 | 21 |
| act | gelu | 0.1071 | 31 |
| act | relu | 0.1089 | 60 |
| act | mish | 0.1149 | 42 |
| act | silu | 0.1341 | 39 |
| act | tanh | 0.1572 | 16 |
| width | 256 | 0.1019 | 36 |
| width | 128 | 0.1062 | 69 |
| width | 384 | 0.1120 | 27 |
| width | 192 | 0.1141 | 31 |
| width | 64 | 0.1382 | 25 |
| depth | 3 | 0.0927 | 75 |
| depth | 2 | 0.0988 | 45 |
| depth | 4 | 0.1217 | 47 |
| depth | 1 | 0.1250 | 21 |
| batch | 512 | 0.0988 | 56 |
| batch | 256 | 0.0994 | 58 |
| batch | 1024 | 0.1204 | 74 |

Figure: `results/cloud-search-search.png`.

## Noisy data (`equil_data_noisy.csv`)

(not run)

Figure: `results/cloud-search-noisy.png`.
