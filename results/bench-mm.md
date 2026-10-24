# Millimetre benchmark of the shipped model, 30 set-aside discharges

Command: `python analysis/bench_mm.py --model out/model/ipp1-ipn.npz --set locked` (Apple M5, Sat 24 Oct 2026). The shipped model for clean inputs is `analysis/ipn_model.py` (measurements divided by the plasma current, `results/ipp1-ipn.md`), trained on the 119 development discharges. Earlier shipped models on the same discharges: `cand` axis R 0.133 / Z 0.172 mm; `cand` plus a separate axis network 0.063 / 0.091 mm.

```
Odchylka od rekonstrukce ústavu (absolutní hodnota |model − rekonstrukce|)
====================================================================================================
model   out/model/ipp1-ipn.npz (119 discharges (34211 rows), seed 0, 150 epochs, Huber 0.2)
sada    locked: odložené výboje (30 v results/ipp1-locked-test-ids.txt); 30 výbojů, 8761 řádků

Rozdělení odchylky v mm (proud plazmatu v kA), na řádcích, kde rekonstrukce veličinu má
----------------------------------------------------------------------------------------------------
veličina             řádků výb.     MAE  medián    RMSE     p90     p95     p99   p99.9     max
osa R                 8761   30  0.0563  0.0314   0.178   0.121   0.166   0.372    0.85    11.2
osa Z                 8761   30  0.0632  0.0357   0.287   0.125   0.177   0.391    2.17    21.4
osa 2D vzdálenost     8761   30  0.0956  0.0627   0.338   0.175   0.247    0.56    2.21    24.1
X bod R               5207   30  0.0479  0.0239   0.137  0.0919   0.133   0.515    2.07     3.3
X bod Z               5207   30  0.0529  0.0284   0.114   0.112   0.181   0.412    1.29    2.79
bod dopadu 1 R        5206   30  0.0771  0.0374   0.209   0.134   0.211   0.951    2.59    3.13
bod dopadu 1 Z        5206   30  0.0275  0.0148  0.0588  0.0558  0.0834   0.247   0.582    1.21
bod dopadu 2 R        5206   30  0.0523  0.0276   0.169   0.101   0.164   0.377    1.57    7.27
bod dopadu 2 Z        5206   30  0.0118 0.00675  0.0414  0.0223  0.0342  0.0824   0.274    2.18
bod limiteru R        3554   30    3.48   0.523    20.8    3.55    7.53    56.8     313     430
bod limiteru Z        3554   30    3.91    1.16    20.4    5.78    10.2    44.9     361     527
proud plazmatu kA     8760   30  0.0347  0.0258   0.047  0.0765  0.0982   0.143   0.185   0.398

Podíl řádků s odchylkou pod prahem (%) a 95% interval (bootstrap po výbojích, 1000×)
----------------------------------------------------------------------------------------------------
veličina              <0.1   <0.5     <1     <2     <5  MAE [95% interval]    pod 1 mm % [95% int.]
osa R                87.14  99.42  99.93  99.97  99.98  0.0563 [0.0476, 0.066] 99.93 [99.87, 99.99]
osa Z                85.61  99.30  99.74  99.89  99.97  0.0632 [0.053, 0.0753] 99.74 [99.56, 99.87]
osa 2D vzdálenost    74.64  98.72  99.68  99.89  99.97  0.0956 [0.0818, 0.111] 99.68 [99.49, 99.83]
X bod R              91.34  98.92  99.79  99.88 100.00  0.0479 [0.0353, 0.0633] 99.79 [99.43, 99.98]
X bod Z              87.90  99.29  99.83  99.98 100.00  0.0529 [0.0402, 0.0677] 99.83 [99.62, 99.96]
bod dopadu 1 R       82.89  98.23  99.04  99.71 100.00  0.0771 [0.0556, 0.102] 99.04 [97.96, 99.91]
bod dopadu 1 Z       96.25  99.75  99.98 100.00 100.00  0.0275 [0.021, 0.0348] 99.98 [99.94, 100.00]
bod dopadu 2 R       89.82  99.40  99.69  99.92  99.98  0.0523 [0.0394, 0.0679] 99.69 [99.32, 99.90]
bod dopadu 2 Z       99.25  99.92  99.96  99.98 100.00  0.0118 [0.00974, 0.0145] 99.96 [99.87, 100.00]
bod limiteru R       21.07  49.35  65.50  81.06  92.54  3.48 [2.17, 5.28]     65.50 [59.75, 70.84]
bod limiteru Z        7.34  28.93  46.06  64.88  87.51  3.91 [3.11, 4.9]      46.06 [42.70, 49.72]
proud plazmatu kA        –      –      –      –      –  0.0347 [0.0311, 0.0382] –

Konfigurace limitovaná / divertorová (model: is_limited > 0.5)
----------------------------------------------------------------------------------------------------
shoda s rekonstrukcí 99.20 % z 8761 řádků; výbojů s aspoň jedním rozdílem: 22
                            model limitovaná  model divertorová
rekonstrukce limitovaná                 3512                 42
rekonstrukce divertorová                  28               5179

10 řádků s největší odchylkou (řádek jednou, podle jeho největší odchylky polohy)
----------------------------------------------------------------------------------------------------
  #     výboj  rel. čas  veličina            odchylka mm  osa 2D mm
  1       104     0.263  bod limiteru Z              527       1.08
  2        44     0.205  bod limiteru Z              498      0.181
  3       104     0.260  bod limiteru Z              495       1.56
  4       129     0.205  bod limiteru Z              485      0.272
  5        52     0.003  bod limiteru R              430     0.0761
  6        21     0.000  bod limiteru R              384       0.26
  7       129     0.000  bod limiteru R              352      0.285
  8        88     0.011  bod limiteru R              314      0.171
  9        88     0.022  bod limiteru R              313      0.244
 10        85     0.014  bod limiteru R              296      0.345

Čísla jsou shoda s rekonstrukcí ústavu, ne odchylka od plazmatu samotného.
```
