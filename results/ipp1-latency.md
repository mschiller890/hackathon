# Latency (REQ-002)

The assignment asks for a reaction in units to tens of milliseconds. Network: 107,152 parameters, 24 inputs, 16 outputs. Times in milliseconds.

| setting | median | p99 | p99.9 | max |
|---|---|---|---|---|
| cpu_1_thread_single_sample | 0.0145 | 0.0288 | 0.0699 | 0.090 |
| cpu_4_thread_single_sample | 0.0146 | 0.0350 | 0.0653 | 0.077 |
| cpu_batch_64 | 0.0660 | 0.0748 | 0.1010 | 0.113 |
| cpu_batch_1024 | 0.4983 | 0.8707 | 1.1088 | 1.140 |
| cpu_batch_4096 | 1.6775 | 2.5467 | 2.9509 | 3.127 |
| numpy_single_sample | 0.0129 | 0.0324 | 0.0541 | 0.083 |
| mps_single_sample | 0.2405 | 0.4640 | 0.6916 | 0.716 |
| mps_batch_4096 | 0.6849 | 1.6529 | 2.0111 | 2.056 |