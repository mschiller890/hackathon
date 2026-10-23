# Latency (REQ-002)

The assignment asks for a reaction in units to tens of milliseconds. Network: 107,152 parameters, 24 inputs, 16 outputs (a freshly initialised network of the trained architecture; weights do not change the timing). Times in milliseconds.

CPU: Apple M5 (10 logical cores); GPU rows: the Apple GPU of the same chip through torch MPS. Load average (1, 5, 15 minutes) at the start [5.67, 14.52, 29.34], at the end [5.86, 14.41, 29.21]; the machine was shared and busy (a load of 8 or more in the 1 or 5 minute average on 10 cores), so the medians are somewhat pessimistic and the tails are pessimistic: not a clean benchmark. The tail columns (p99.9, max) come from 5000 calls (500 or fewer for the batch rows) on a general-purpose operating system without real-time guarantees: they show what happens on such a machine, they are not a worst-case bound. A loaded machine earlier gave p99 0.65 ms and max 21 ms for a single CPU sample (reviewer measurement, load 16), still inside a 1 to 10 ms budget at the p99.

| setting | median | p99 | p99.9 | max |
|---|---|---|---|---|
| cpu_1_thread_single_sample | 0.0145 | 0.0209 | 0.0812 | 0.148 |
| cpu_4_thread_single_sample | 0.0145 | 0.0205 | 0.0771 | 0.118 |
| cpu_batch_64 | 0.0716 | 0.1184 | 0.2445 | 0.258 |
| cpu_batch_1024 | 0.6480 | 1.0108 | 1.1172 | 1.120 |
| cpu_batch_4096 | 2.4205 | 3.2844 | 4.0918 | 4.254 |
| numpy_single_sample | 0.0125 | 0.0475 | 0.0760 | 0.087 |
| cpu_end_to_end_numpy | 0.0140 | 0.0503 | 0.0778 | 0.105 |
| mps_single_sample | 0.2681 | 0.6057 | 0.6700 | 0.709 |
| mps_single_sample_with_transfers | 0.4896 | 3.9435 | 8.1092 | 40.551 |
| mps_batch_4096 | 0.7039 | 1.0785 | 1.1767 | 1.216 |

cpu_end_to_end_numpy and mps_single_sample_with_transfers include the standardisation of the inputs, the copy to and from the GPU (the GPU row) and the de-standardisation of the outputs, which any real loop needs; the other single-sample rows time the network only. What these numbers do not cover: collecting and integrating the coil signals, and the accuracy on really noisy signals (see the robustness results).
