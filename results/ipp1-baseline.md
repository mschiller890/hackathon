# Baseline IPP 1: group split by discharge, 5 folds, 60 epochs

| target | unit | ridge MAE | MLP MAE | ridge R2 | MLP R2 | MLP nRMSE |
|---|---|---|---|---|---|---|
| plasma_current | kA | 0.0346 | 1.49 | 1.000 | 0.999 | 0.027 |
| R_mag_axis | mm | 2.4 | 0.377 | 0.527 | 0.977 | 0.139 |
| Z_mag_axis | mm | 2.66 | 0.391 | 0.774 | 0.984 | 0.107 |
| elongation |  | 0.092 | 0.00569 | 0.597 | 0.998 | 0.041 |
| triangularity |  | 0.041 | 0.00284 | 0.574 | 0.997 | 0.048 |
| triangularity_upper |  | 0.0251 | 0.00297 | 0.604 | 0.993 | 0.080 |
| triangularity_lower |  | 0.0597 | 0.00368 | 0.576 | 0.998 | 0.044 |
| R_x_point | mm | 1.54 | 0.202 | 0.785 | 0.994 | 0.067 |
| Z_x_point | mm | 2.12 | 0.195 | 0.863 | 0.997 | 0.039 |
| R_strike_point_1 | mm | 2.59 | 0.265 | 0.802 | 0.995 | 0.051 |
| Z_strike_point_1 | mm | 1.43 | 0.131 | 0.763 | 0.993 | 0.067 |
| R_strike_point_2 | mm | 1.61 | 0.228 | 0.877 | 0.997 | 0.045 |
| Z_strike_point_2 | mm | 0.35 | 0.0552 | 0.900 | 0.993 | 0.068 |
| R_limiter | mm | 46.8 | 10.7 | 0.179 | 0.898 | 0.317 |
| Z_limiter | mm | 80.9 | 22.2 | 0.391 | 0.926 | 0.270 |
| is_limited |  | 0.198 | 0.0203 | 0.616 | 0.979 | 0.144 |

is_limited accuracy: ridge 0.912, MLP 0.993
Latency (MLP, CPU, one sample): median 0.015 ms, p99 0.042 ms; batch of 4096: 2.3 ms; 107,152 parameters