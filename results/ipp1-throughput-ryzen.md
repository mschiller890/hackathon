# Throughput of the trained baseline network in bulk (Ryzen 5 7535HS)

Network: ipp1_common.fit_mlp, group fold 0, seed 0, 60 epochs (trained in 8 s), 24 inputs, 16 outputs. Fast pass: scaling folded into the first and last layer, preallocated buffers, torch 2.14.1+cu130, 6 threads (batch 1: one thread), cores [0, 2, 4, 6, 8, 10], load average 6.56 at the end.

Check on all 8591 held-out time steps: axis R mean absolute error 0.387 mm with the fast pass, 0.387 mm with fit_mlp's predict(); largest difference between the two 0.000119 mm.

| batch | weights + one batch | median time per batch | estimates per second |
|---:|---:|---:|---:|
| 1 | 0.43 MB | 24.4 µs | 38,925 |
| 256 | 1.12 MB | 210.4 µs | 1,137,419 |
| 512 | 1.82 MB | 318.7 µs | 1,537,891 |
| 1024 | 3.21 MB | 553.6 µs | 1,728,545 |
| 2048 | 6.00 MB | 1086.3 µs | 1,793,573 |
| 4096 | 11.57 MB | 2214.0 µs | 1,790,729 |
| 8192 | 22.71 MB | 5315.6 µs | 1,492,796 |

Reading: the rate is held-out time steps processed divided by the wall clock over 3 s, with the held-out set repeated. It is bulk throughput, not the latency a controller sees: a batch of n rows waits for n time steps to arrive. Batch 1 is the one-at-a-time case. Above about 4096 rows the batch no longer fits the 16 MB L3 of this CPU and the rate drops. Machine load and frequency scaling are not controlled.

Repeatability (written by hand, Fri 23 Oct, last run finished by 22:20): four runs of this script on the same machine. Two gave the table above
within about 5 % (best 1.88 and 1.79 million estimates per second). In the other two, while other programs were busy (load
average up to 6.7), batches of 512 to 4096 rows stalled at 57 to 64 ms instead of about 1 ms, so the rate fell to 17 000 to
450 000 per second for those batch sizes. With all 6 cores taken by the 6 threads, one core lent to another program holds up
the whole batch. Bulk throughput on a shared machine is therefore not guaranteed; the single-row case (batch 1) did not stall.
