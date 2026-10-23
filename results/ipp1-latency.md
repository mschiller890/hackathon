# Latency (REQ-002)

The assignment asks for a reaction in units to tens of milliseconds. Network: 107,152 parameters, 24 inputs, 16 outputs (a freshly initialised network of the trained architecture; weights do not change the timing). Times in milliseconds.

CPU: Apple M5 (10 logical cores); GPU rows: the Apple GPU of the same chip through torch MPS. Load average (1, 5, 15 minutes) at the start [7.67, 32.55, 40.73], at the end [8.43, 31.9, 40.4]; the machine was shared and busy (a load of 8 or more in the 1 or 5 minute average on 10 cores), so the medians are somewhat pessimistic and the tails are pessimistic: not a clean benchmark. The tail columns (p99.9, max) come from 5000 calls (500 or fewer for the batch rows) on a general-purpose operating system without real-time guarantees: they show what happens on such a machine, they are not a worst-case bound. A loaded machine earlier gave p99 0.65 ms and max 21 ms for a single CPU sample (reviewer measurement, load 16), still inside a 1 to 10 ms budget at the p99.

| setting | median | p99 | p99.9 | max |
|---|---|---|---|---|
| cpu_1_thread_single_sample | 0.0188 | 0.1182 | 0.2682 | 0.757 |
| cpu_4_thread_single_sample | 0.0190 | 0.1122 | 0.4189 | 23.915 |
| cpu_batch_64 | 0.1041 | 0.6172 | 1.8506 | 2.581 |
| cpu_batch_1024 | 1.0719 | 4.2759 | 8.8110 | 11.666 |
| cpu_batch_4096 | 3.2654 | 8.6860 | 27.2692 | 31.275 |
| numpy_single_sample | 0.0195 | 0.0897 | 0.4317 | 2.589 |
| cpu_end_to_end_numpy | 0.0208 | 0.1020 | 0.2865 | 5.993 |
| mps_single_sample | 0.4394 | 3.1691 | 5.8625 | 10.187 |
| mps_single_sample_with_transfers | 0.6911 | 4.0435 | 8.2595 | 16.191 |
| mps_batch_4096 | 1.2824 | 6.1678 | 9.4209 | 10.516 |

cpu_end_to_end_numpy and mps_single_sample_with_transfers include the standardisation of the inputs, the copy to and from the GPU (the GPU row) and the de-standardisation of the outputs, which any real loop needs; the other single-sample rows time the network only. What these numbers do not cover: collecting and integrating the coil signals, and the accuracy on really noisy signals (see the robustness results).
