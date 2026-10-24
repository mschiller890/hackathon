# Latency of the shipped model pair (review finding H1a)

One sample, clean-input recipe `cand` of `analysis/final_evaluation.py`: the general network (112,784 parameters, 46 inputs, 16 outputs), the ridge for plasma_current and the limiter network (112,784 parameters), gated by the predicted `is_limited`. Random weights of the trained shapes (weights do not change the timing). Same protocol as `results/ipp1-latency.md`: 5000 calls after 300 warm-up calls (2000 and 200 for the GPU row), times in milliseconds.

CPU: Apple M5 (10 logical cores); the GPU row is the Apple GPU of the same chip through torch MPS. Load average (1, 5, 15 minutes) at the start [7.01, 6.47, 8.13], at the end [6.68, 6.42, 8.1]: below 8 in all windows, but other programs were running (not an isolated benchmark machine). The tail columns come from a general-purpose operating system without real-time guarantees: they show what happens on such a machine, they are not a worst-case bound.

| setting | median | p99 | p99.9 | max |
|---|---|---|---|---|
| torch_1_thread_general_net_only | 0.0143 | 0.0561 | 0.1123 | 0.134 |
| torch_1_thread_both_nets | 0.0290 | 0.1134 | 0.1985 | 0.600 |
| torch_4_thread_general_net_only | 0.0145 | 0.0691 | 0.1119 | 0.171 |
| torch_4_thread_both_nets | 0.0285 | 0.0878 | 0.1552 | 0.244 |
| numpy_end_to_end_diverted | 0.0154 | 0.0571 | 0.0880 | 0.113 |
| numpy_end_to_end_limited | 0.0274 | 0.0930 | 0.1506 | 0.196 |
| ipp1_final_predict_diverted | 0.0260 | 0.0650 | 0.1048 | 0.196 |
| ipp1_final_predict_limited | 0.0544 | 0.1883 | 0.3108 | 0.341 |
| mps_end_to_end_limited_with_transfers | 0.9837 | 2.4127 | 3.1679 | 3.296 |

`ipp1_final_predict_*` time the `predict()` closure that `analysis/final_evaluation.py` builds for the same recipe (the implementation used in the evaluation scripts: torch tensors and array copies on every call, one thread; one-epoch weights, which do not change the timing; the gate follows the network's own prediction on a real row). `numpy_end_to_end_*` is the whole per-sample path from the 24 raw inputs: 22 coil differences, standardisation, the general network, the ridge, the gate, (limited case only) the limiter network and the de-standardisation; `diverted` skips the limiter network, `limited` is the slower case and the one to quote as the bound. The `torch_*` rows time the networks only. **Included:** everything from the 24 raw numbers to the 16 outputs of the shipped pair, on one CPU core (numpy) or the GPU with its copies. **Not included:** collecting and integrating the coil signals, the noise-trained model needed for noisy inputs, the camera, and the accuracy of random weights (this is timing only).

## Reading

- **The shipped pair takes about 0.03 ms per sample on one CPU core, p99 under 0.1 ms:** numpy path from the 24 raw inputs, median 0.0154 ms when the plasma is diverted (general network only) and 0.0274 ms when
  it is limited (both networks), p99 0.057 and 0.093 ms. The baseline 24-16 network alone is 0.0145 ms (`results/ipp1-latency.md`), so the shipped pair costs about twice as much in the limited case,
  not twelve times. Both are far inside the 1 to 10 ms budget; the budget statement still covers only this computation, not the acquisition of the signals.
- The reference `predict()` of `analysis/final_evaluation.py` (torch tensors, copies on every call) needs 0.0260 ms (diverted) and 0.0544 ms (limited) in the same run, so the implementation
  matters by a factor of 1.5 to 2; a deployed loop would use the numpy path. The figure of 0.1775 ms in `results/ipp1-improve.md` (recipe `combo_diff`, another code path, "shared loaded
  machine") was **not reproduced** by the recipe of `final_evaluation.py` here; we did not rerun that script, so we do not know which part of it was slow.
- GPU: 0.98 ms per sample with the copies (0.93 to 1.06 over the runs), 35 to 65 times slower than the CPU numpy path for one sample; it is not an option for a single sample.
- **The machine was not quiet.** Load average 6.4 to 7.2 (below 8, but a browser, a video editor session and other agents were running); five runs gave the numpy limited median 0.0271 to 0.0287 ms
  and p99 0.048 to 0.096 ms, so medians are stable to about 5 % and the p99 and the maximum depend on what else runs. Quote the median and "p99 under 0.1 ms on a busy laptop"; the tails are not a bound.
- Random weights of the trained shapes: this is timing, not accuracy. The `torch_*` rows are the two networks alone (about 0.03 ms for both); `ipp1_final_predict_*` uses one-epoch weights and the gate follows its own prediction on a real row.
